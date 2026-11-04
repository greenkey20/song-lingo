"""tts.fix_wav_header·fix_wav_headers·tts_wav의 헤더 수리 단위 테스트(이슈 #31 뒤, 검토 문서 16.9). 합성 wav만 쓴다(가사·API 없음).
실행: python -m unittest tests.test_tts_wav -v"""
import hashlib
import os
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tts  # noqa: E402

UNKNOWN = 0xFFFFFFFF


def make_wav(path, seconds=1.0, sr=24000, unknown_sizes=True, extra_chunk_before_data=False, trailing_byte=False):
    """모노 PCM16 wav를 직접 바이트로 만든다. unknown_sizes=True면 RIFF·data 크기 칸을 0xFFFFFFFF로 둔다(스트리밍 저장 흉내)."""
    pcm = b"".join(struct.pack("<h", (i % 100) * 100) for i in range(int(sr * seconds)))
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, 1, sr, sr * 2, 2, 16)
    extra = struct.pack("<4sI", b"LIST", 4) + b"INFO" if extra_chunk_before_data else b""
    body = b"WAVE" + fmt + extra
    data_chunk = struct.pack("<4sI", b"data", UNKNOWN if unknown_sizes else len(pcm)) + pcm + (b"\x01" if trailing_byte else b"")
    riff = struct.pack("<4sI", b"RIFF", UNKNOWN if unknown_sizes else 4 + len(fmt) + len(extra) + len(data_chunk))
    Path(path).write_bytes(riff + body + data_chunk)
    return len(pcm) // 2


def duration(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


class FixHeader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)

    def test_unknown_sizes_are_fixed_and_duration_becomes_correct(self):
        p = self.d / "a.wav"
        make_wav(p, 2.75)
        self.assertGreater(duration(p), 10000)                    # 고치기 전: 터무니없이 긴 길이로 읽힘(문제 재현)
        self.assertEqual(tts.fix_wav_header(p), "fixed")
        self.assertAlmostEqual(duration(p), 2.75, places=2)       # 고친 뒤: 실제 길이

    def test_second_call_changes_nothing(self):
        p = self.d / "a.wav"
        make_wav(p)
        tts.fix_wav_header(p)
        before = hashlib.sha1(p.read_bytes()).hexdigest()
        self.assertEqual(tts.fix_wav_header(p), "ok")
        self.assertEqual(hashlib.sha1(p.read_bytes()).hexdigest(), before)

    def test_already_correct_file_is_not_touched(self):
        p = self.d / "good.wav"
        make_wav(p, unknown_sizes=False)
        before = p.read_bytes()
        self.assertEqual(tts.fix_wav_header(p), "ok")
        self.assertEqual(p.read_bytes(), before)

    def test_only_unknown_field_is_rewritten(self):
        p = self.d / "half.wav"
        make_wav(p, 1.0, unknown_sizes=False)
        b = bytearray(p.read_bytes())
        struct.pack_into("<I", b, 4, UNKNOWN)                      # RIFF 칸만 "모름", data 칸은 정상
        data_size_before = bytes(b[40:44])
        p.write_bytes(bytes(b))
        self.assertEqual(tts.fix_wav_header(p), "fixed")
        after = p.read_bytes()
        self.assertEqual(after[40:44], data_size_before)           # 정상이던 data 칸은 그대로
        self.assertEqual(struct.unpack_from("<I", after, 4)[0], len(after) - 8)

    def test_extra_chunk_before_data_and_partial_last_frame(self):
        p = self.d / "x.wav"
        make_wav(p, 1.0, extra_chunk_before_data=True, trailing_byte=True)    # data 앞에 LIST 칸, 끝에 반쪽 프레임 1바이트
        self.assertEqual(tts.fix_wav_header(p), "fixed")
        self.assertAlmostEqual(duration(p), 1.0, places=3)         # 반쪽 프레임은 길이에서 뺀다

    def test_non_wav_and_broken_files_are_left_alone(self):
        for name, content in (("t.wav", b"not a wav at all"), ("short.wav", b"RIFF"), ("nofmt.wav", b"RIFF" + struct.pack("<I", UNKNOWN) + b"WAVE" + b"data" + struct.pack("<I", UNKNOWN) + b"xx")):
            p = self.d / name
            p.write_bytes(content)
            self.assertEqual(tts.fix_wav_header(p), "skipped", name)
            self.assertEqual(p.read_bytes(), content)

    def test_unknown_size_non_data_chunk_is_skipped(self):
        p = self.d / "weird.wav"
        fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, 1, 24000, 48000, 2, 16)
        content = b"RIFF" + struct.pack("<I", UNKNOWN) + b"WAVE" + struct.pack("<4sI", b"LIST", UNKNOWN) + fmt
        p.write_bytes(content)
        self.assertEqual(tts.fix_wav_header(p), "skipped")
        self.assertEqual(p.read_bytes(), content)

    def test_no_temp_file_is_left_behind(self):
        p = self.d / "a.wav"
        make_wav(p)
        tts.fix_wav_header(p)
        self.assertEqual(sorted(x.name for x in self.d.iterdir()), ["a.wav"])


class Folder(unittest.TestCase):
    def test_counts_per_status(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            make_wav(d / "a.wav"); make_wav(d / "b.wav"); make_wav(d / "good.wav", unknown_sizes=False); (d / "bad.wav").write_bytes(b"xx")
            self.assertEqual(tts.fix_wav_headers(d), {"fixed": 2, "ok": 1, "skipped": 1})
            self.assertEqual(tts.fix_wav_headers(d), {"fixed": 0, "ok": 3, "skipped": 1})     # 다시 해도 같다


class TtsWav(unittest.TestCase):
    """tts_wav가 저장 직후와 캐시 적중 때 헤더를 고치는지(가짜 클라이언트: 스트리밍처럼 길이 모름 wav를 씀)."""

    class FakeResponse:
        def __init__(self, outer): self.outer = outer
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream_to_file(self, path): make_wav(path, 1.5)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        outer = self
        outer.n_calls = 0

        class Streaming:
            def create(self, **kw):
                outer.n_calls += 1
                return TtsWav.FakeResponse(outer)

        class Client:
            class audio:
                class speech:
                    with_streaming_response = Streaming()
        self.orig = tts._get_client
        tts._get_client = lambda: Client()
        self.addCleanup(lambda: setattr(tts, "_get_client", self.orig))
        self.calls0 = tts.calls

    def test_new_file_has_correct_header_after_streaming_save(self):
        p = Path(self.tmp.name) / "n.wav"
        tts.tts_wav("hello", p)
        self.assertEqual((self.n_calls, tts.calls - self.calls0), (1, 1))
        self.assertAlmostEqual(duration(p), 1.5, places=2)

    def test_cache_hit_repairs_old_file_without_calling_api(self):
        p = Path(self.tmp.name) / "old.wav"
        make_wav(p, 2.0)                                           # 예전에 저장된, 헤더가 잘못된 캐시 파일
        tts.tts_wav("hello", p)
        self.assertEqual((self.n_calls, tts.calls - self.calls0), (0, 0))      # API 호출·과금 없음
        self.assertAlmostEqual(duration(p), 2.0, places=2)


if __name__ == "__main__":
    unittest.main()
