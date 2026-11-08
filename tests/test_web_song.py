"""web_song.py 단위 테스트: 합성 신호·가짜 인식 함수만 쓴다(곡·가사·API 없음)."""
import os
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

import recorder
import separate
import web_song

SR = 44100


def _tone(seconds, sr=SR, freq=440.0):
    t = np.arange(int(seconds * sr)) / sr
    return (0.3 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class Pure(unittest.TestCase):
    def test_format_hms(self):
        self.assertEqual(web_song.format_hms(0), "00:00:00")
        self.assertEqual(web_song.format_hms(65), "00:01:05")
        self.assertEqual(web_song.format_hms(3725.4), "01:02:05")
        self.assertEqual(web_song.format_hms(-3), "00:00:00")

    def test_clip_range_label(self):
        self.assertEqual(web_song.clip_range_label(65, 15), "00:01:05 ~ 00:01:20")

    def test_peaks_shape_and_values(self):
        x = np.concatenate([np.full(500, 0.5), np.full(500, -0.25)]).astype(np.float32)
        mins, maxs = web_song.waveform_peaks(x, 2)
        self.assertEqual(len(mins), 2)
        np.testing.assert_allclose(maxs, [0.5, -0.25])
        np.testing.assert_allclose(mins, [0.5, -0.25])

    def test_peaks_stereo_and_few_samples(self):
        x = np.zeros((10, 2), dtype=np.float32)
        mins, _ = web_song.waveform_peaks(x, 600)
        self.assertEqual(len(mins), 10)              # 샘플이 칸보다 적으면 있는 만큼
        with self.assertRaises(ValueError):
            web_song.waveform_peaks(np.array([]))

    def test_line_range_clamped(self):
        self.assertEqual(web_song.line_range({"start": 0.05, "end": 14.95}, 15.0), (0.0, 15.0))
        a, b = web_song.line_range({"start": 3.0, "end": 5.0}, 15.0)
        self.assertAlmostEqual(a, 2.9)
        self.assertAlmostEqual(b, 5.1)


class RecordingInfo(unittest.TestCase):
    """주변 음악 녹음 점검(이슈 #51): 합성 신호로 길이·경고·긴 녹음 표시를 확인한다."""

    @staticmethod
    def _wav(seconds, amp=0.3, sr=16000):
        t = np.arange(int(seconds * sr)) / sr
        x = (amp * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
        import io
        buf = io.BytesIO()
        import wave
        with wave.open(buf, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((x * 32767).astype("<i2").tobytes())
        return buf.getvalue()

    def test_normal(self):
        r = web_song.recording_info(self._wav(12))
        self.assertAlmostEqual(r["seconds"], 12, delta=0.1)
        self.assertTrue(r["ok"])
        self.assertFalse(r["long"])

    def test_long_is_only_flagged(self):
        r = web_song.recording_info(self._wav(web_song.LONG_RECORDING_S + 5))
        self.assertTrue(r["long"])             # 제한이 아니라 안내용 표시

    def test_silent_warns(self):
        r = web_song.recording_info(self._wav(5, amp=0.0))
        self.assertFalse(r["ok"])
        self.assertTrue(r["warnings"])

    def test_unreadable_raises(self):
        with self.assertRaises(Exception):
            web_song.recording_info(b"not audio")


class Workspace(unittest.TestCase):
    def test_cleanup_and_delete(self):
        with tempfile.TemporaryDirectory() as base:
            old = web_song.new_workspace(base)
            new = web_song.new_workspace(base)
            other = Path(base) / "keep_me"
            other.mkdir()
            past = time.time() - 7200
            os.utime(old, (past, past))
            self.assertEqual(web_song.cleanup_old_workspaces(base, max_age_s=3600), 1)
            self.assertFalse(old.exists())
            self.assertTrue(new.exists() and other.exists())      # 새 폴더와 우리 것이 아닌 폴더는 남는다
            web_song.delete_workspace(new)
            self.assertFalse(new.exists())
            with self.assertRaises(ValueError):
                web_song.delete_workspace(other)                 # 접두어가 다르면 지우지 않는다
            self.assertTrue(other.exists())

    def test_save_upload_ignores_original_name(self):
        with tempfile.TemporaryDirectory() as base:
            ws = web_song.new_workspace(base)
            p = web_song.save_upload(ws, "../../evil name.MP3", b"abc")
            self.assertEqual(p, ws / "song.mp3")
            self.assertEqual(p.read_bytes(), b"abc")


class Flow(unittest.TestCase):
    """합성 wav '곡'으로 업로드 → 윤곽 → 구간 → 줄 → 확정 → 보컬 흐름을 가짜 인식·분리로 확인한다."""

    def setUp(self):
        self.base = tempfile.TemporaryDirectory()
        self.ws = web_song.new_workspace(self.base.name)
        src = Path(self.base.name) / "src.wav"
        recorder.save_wav(src, np.stack([_tone(30), _tone(30)], axis=1), SR)
        self.song = web_song.save_upload(self.ws, "x.wav", src.read_bytes())

    def tearDown(self):
        self.base.cleanup()

    @staticmethod
    def fake_recognize(path, language, model_size=None, vad_filter=False, word_timestamps=False):
        seg = {"start": 0.5, "end": 3.0, "text": "hello there", "avg_logprob": -0.3, "no_speech_prob": 0.01,
               "compression_ratio": 1.2, "words": [{"word": "hello", "start": 0.5, "end": 1.5, "prob": 0.9},
                                                    {"word": "there", "start": 1.6, "end": 3.0, "prob": 0.9}]}
        return [seg], 0.1

    def test_overview(self):
        ov = web_song.song_overview(self.song.read_bytes(), 100)
        self.assertAlmostEqual(ov["seconds"], 30.0, places=1)
        self.assertEqual(len(ov["mins"]), 100)

    def test_cut_recognize_edit_vocals(self):
        out = web_song.cut(self.ws, self.song, 5, 10)
        self.assertAlmostEqual(out["seconds"], 10.0, places=2)
        doc = web_song.recognize_lines(self.ws, recognize=self.fake_recognize)
        self.assertEqual(doc["lines"][0]["stt_text"], "hello there")
        web_song.confirm_line(self.ws, 1, "hello, there!")
        self.assertTrue(web_song.load_doc(self.ws)["lines"][0]["edited"])
        calls = []
        voc = web_song.make_vocals(self.ws, separate_fn=lambda clip: calls.append(1) or clip)
        self.assertTrue(voc.exists())
        web_song.make_vocals(self.ws, separate_fn=lambda clip: calls.append(1) or clip)
        self.assertEqual(len(calls), 1)                           # 이미 있으면 다시 분리하지 않는다
        summary = web_song.tts_summary(self.ws)
        self.assertEqual(summary["n_lines"], 1)
        self.assertFalse(summary["done"])                         # 계획만, 호출 없음

    def test_recut_removes_stale_lines_and_vocals(self):
        web_song.cut(self.ws, self.song, 5, 10)
        web_song.recognize_lines(self.ws, recognize=self.fake_recognize)
        web_song.make_vocals(self.ws, separate_fn=lambda clip: clip)
        web_song.cut(self.ws, self.song, 12, 10)
        self.assertIsNone(web_song.load_doc(self.ws))
        _mix, voc = separate.clip_paths(web_song.CLIP_ID, web_song.work_dir(self.ws))
        self.assertFalse(voc.exists())

class Language(unittest.TestCase):
    """이슈 #50: 구간 언어 제안과 언어가 인식 호출·줄 데이터로 전달되는지(가짜 감지·인식 함수)."""

    def setUp(self):
        self.base = tempfile.TemporaryDirectory()
        self.ws = web_song.new_workspace(self.base.name)
        src = Path(self.base.name) / "src.wav"
        recorder.save_wav(src, np.stack([_tone(30), _tone(30)], axis=1), SR)
        self.song = web_song.save_upload(self.ws, "x.wav", src.read_bytes())
        web_song.cut(self.ws, self.song, 5, 10)
        self.calls = []

    def tearDown(self):
        self.base.cleanup()

    def fake_recognize(self, path, language, model_size=None, vad_filter=False, word_timestamps=False, **kw):
        self.calls.append({"language": language, **kw})
        seg = {"start": 0.5, "end": 3.0, "text": "きみがすき", "avg_logprob": -0.3, "no_speech_prob": 0.01, "compression_ratio": 1.2,
               "words": [{"word": "きみ", "start": 0.5, "end": 1.5, "prob": 0.9}, {"word": "が", "start": 1.5, "end": 2.0, "prob": 0.9},
                         {"word": "すき", "start": 2.0, "end": 3.0, "prob": 0.9}]}
        return [seg], 0.1

    def test_detect_restricts_to_supported_languages(self):
        probs = [("br", 0.5), ("fr", 0.3), ("en", 0.15), ("ja", 0.05)]
        out = web_song.detect_clip_language(self.ws, detect=lambda path, size: ("br", 0.5, probs))
        self.assertEqual(out["top"][0], "fr")                           # 브르타뉴어(br)는 후보 밖이라 빠지고 프랑스어가 1등
        self.assertEqual(out["raw_top"], ("br", 0.5))
        self.assertEqual(out["mixed"], "en")                            # 2등 영어가 후보 안의 비율 25% 이상이라 "섞였을 수 있음"

    def test_single_language_is_passed_and_recorded(self):
        doc = web_song.recognize_lines(self.ws, recognize=self.fake_recognize, language="ja", languages=["ja"])
        self.assertEqual(self.calls[0], {"language": "ja"})             # multilingual은 켤 때만 넘김
        self.assertEqual(doc["languages"], ["ja"])
        self.assertEqual(doc["lines"][0]["lang"], "ja")

    def test_no_space_language_joins_words_without_spaces_when_split(self):
        doc = web_song.recognize_lines(self.ws, recognize=self.fake_recognize, language="ja", languages=["ja"])
        self.assertNotIn(" ", doc["lines"][0]["text"])                   # 일본어 줄에는 공백이 끼지 않는다

    def test_auto_and_multilingual(self):
        doc = web_song.recognize_lines(self.ws, recognize=self.fake_recognize, language=None, multilingual=True, languages=["ja", "en"])
        self.assertEqual(self.calls[0], {"language": None, "multilingual": True})
        self.assertEqual(doc["languages"], ["ja", "en"])
        self.assertEqual(doc["lines"][0]["lang"], "ja")                  # 자동이면 목록의 첫 언어를 줄의 주 언어로
        self.assertTrue(doc["stt"]["multilingual"])

    def test_default_language_is_english_as_before(self):
        web_song.recognize_lines(self.ws, recognize=self.fake_recognize)
        self.assertEqual(self.calls[0]["language"], "en")



class BackgroundVocals(unittest.TestCase):
    """보컬 분리를 화면을 막지 않고 시작·조회(가짜 작업 스크립트로, torch·demucs 없이)."""

    def setUp(self):
        self.base = tempfile.TemporaryDirectory()
        self.ws = web_song.new_workspace(self.base.name)
        src = Path(self.base.name) / "src.wav"
        recorder.save_wav(src, np.stack([_tone(12), _tone(12)], axis=1), SR)
        self.song = web_song.save_upload(self.ws, "x.wav", src.read_bytes())
        web_song.cut(self.ws, self.song, 1, 10)

    def tearDown(self):
        web_song._stop_job(self.ws)
        self.base.cleanup()

    def _worker(self, body):
        p = Path(self.base.name) / "worker.py"
        p.write_text(body, encoding="utf-8")
        return p

    def test_none_then_running_then_done_without_blocking(self):
        import sys
        import time
        self.assertEqual(web_song.vocals_status(self.ws)["state"], "none")
        w = self._worker("import sys, time, pathlib\ntime.sleep(0.6)\n"
                         "pathlib.Path(sys.argv[2], sys.argv[1] + '_vocals.wav').write_bytes(b'x')\n")
        t0 = time.time()
        self.assertEqual(web_song.start_vocals(self.ws, python=sys.executable, worker=w), "running")
        self.assertLess(time.time() - t0, 0.5)                                  # 시작만 하고 바로 돌아온다(기다리지 않음)
        st = web_song.vocals_status(self.ws)
        self.assertEqual(st["state"], "running")
        self.assertEqual(web_song.start_vocals(self.ws, python=sys.executable, worker=w), "running")   # 중복 시작 안 함
        self.assertEqual(len(web_song._JOBS), 1)
        for _ in range(40):
            if web_song.vocals_status(self.ws)["state"] == "done":
                break
            time.sleep(0.1)
        self.assertEqual(web_song.vocals_status(self.ws)["state"], "done")
        self.assertEqual(web_song.start_vocals(self.ws, python=sys.executable, worker=w), "done")      # 이미 있으면 다시 안 만듦

    def test_failure_is_reported_with_error_tail(self):
        import sys
        import time
        w = self._worker("import sys\nprint('ModuleNotFoundError: demucs', file=sys.stderr)\nsys.exit(1)\n")
        web_song.start_vocals(self.ws, python=sys.executable, worker=w)
        st = {"state": "running"}
        for _ in range(40):
            st = web_song.vocals_status(self.ws)
            if st["state"] != "running":
                break
            time.sleep(0.1)
        self.assertEqual(st["state"], "error")
        self.assertIn("ModuleNotFoundError", st["error"])

    def test_recut_stops_the_old_job(self):
        import sys
        w = self._worker("import time\ntime.sleep(30)\n")
        web_song.start_vocals(self.ws, python=sys.executable, worker=w)
        proc = web_song._JOBS[str(self.ws)]["proc"]
        web_song.cut(self.ws, self.song, 2, 10)                                  # 구간을 바꾸면 옛 분리는 멈춘다
        proc.wait(timeout=5)
        self.assertIsNotNone(proc.poll())
        self.assertEqual(web_song.vocals_status(self.ws)["state"], "none")

class SaveRestore(unittest.TestCase):
    """곡 기록을 저장용 dict로 만들고(song_snapshot), 같은 파일을 다시 올렸을 때 구간·가사를 복원(restore_song)하는지 시험한다(이슈 #52)."""

    def setUp(self):
        self.base = tempfile.TemporaryDirectory()
        src = Path(self.base.name) / "src.wav"
        recorder.save_wav(src, np.stack([_tone(30), _tone(30)], axis=1), SR)
        self.data = src.read_bytes()

    def tearDown(self):
        self.base.cleanup()

    def workspace(self):
        ws = web_song.new_workspace(self.base.name)
        return ws, web_song.save_upload(ws, "x.wav", self.data)

    def test_snapshot_without_doc_has_empty_lines_and_clip_info(self):
        ws, song = self.workspace()
        snap = web_song.song_snapshot(ws, "곡.wav", 30.0, "file", (5, 10))
        self.assertEqual(snap["doc"], {"lines": []})
        self.assertEqual((snap["clip_start_sec"], snap["clip_duration_sec"], snap["input_type"], snap["languages"]), (5.0, 10.0, "file", []))
        self.assertEqual(web_song.song_snapshot(ws, "곡", 30, "file", None)["clip_start_sec"], None)

    def test_roundtrip_restores_clip_and_lines_in_a_new_workspace(self):
        ws, song = self.workspace()
        web_song.cut(ws, song, 5, 10)
        doc = {"lines": [{"no": 1, "start": 0.5, "end": 3.0, "text": "hello there", "stt_text": "hello there", "status": "candidate", "lang": "en"}],
               "languages": ["en"], "stt": {"model": "medium"}}
        from song_practice import save_doc
        save_doc(web_song.CLIP_ID, doc, web_song.practice_dir(ws))
        snap = web_song.song_snapshot(ws, "곡.wav", 30.0, "file", (5, 10))
        self.assertEqual(snap["doc"]["lines"][0]["text"], "hello there")
        self.assertEqual(snap["languages"], ["en"])
        # 브라우저를 닫았다 연 것처럼 새 작업 폴더에서 같은 파일을 다시 올림
        ws2, song2 = self.workspace()
        self.assertIsNone(web_song.load_doc(ws2))
        cut_info = web_song.restore_song(ws2, song2, snap)
        self.assertEqual(cut_info, (5.0, 10.0))
        self.assertEqual(web_song.load_doc(ws2)["lines"][0]["text"], "hello there")
        mix, _ = separate.clip_paths(web_song.CLIP_ID, web_song.work_dir(ws2))
        self.assertTrue(mix.exists())                                     # 구간을 다시 잘랐다(음원은 저장하지 않았으니 새로 올린 파일에서)

    def test_restore_without_clip_info_or_lines_is_harmless(self):
        ws, song = self.workspace()
        row = {"clip_start_sec": None, "clip_duration_sec": None, "doc": {"lines": []}}
        self.assertIsNone(web_song.restore_song(ws, song, row))
        self.assertIsNone(web_song.load_doc(ws))



class ListenContext(unittest.TestCase):
    """줄 듣기의 '앞뒤 5초도 함께 듣기'(이슈 #12): line_range의 pad가 구간 안으로 잘리는지."""
    LINE = {"start": 8.0, "end": 11.0}

    def test_default_pad_is_tenth_of_a_second_and_context_pad_is_five(self):
        self.assertEqual(web_song.line_range(self.LINE, 30), (7.9, 11.1))
        self.assertEqual(web_song.line_range(self.LINE, 30, pad=web_song.CONTEXT_PAD), (3.0, 16.0))

    def test_context_is_clamped_to_the_clip(self):
        self.assertEqual(web_song.line_range({"start": 1.0, "end": 3.0}, 8, pad=5.0), (0.0, 8.0))     # 처음·끝을 넘지 않는다
        self.assertEqual(web_song.line_range({"start": 27.0, "end": 29.5}, 30, pad=5.0), (22.0, 30.0))


class ClipLabels(unittest.TestCase):
    """저장된 구간 목록의 글(이슈 #73): 좁은 화면에서 잘려도 구분되도록 알아볼 단서를 앞에 둔다."""
    from datetime import datetime, timezone
    REC = {"id": 1, "input_type": "record", "song_title": "recording.wav", "clip_start_sec": 0.0, "clip_duration_sec": 20.0, "n_lines": 8,
           "first_text": "w1 w2 w3 w4 w5 w6 w7 w8 w9 w10 w11 w12 w13 w14 w15", "languages": ["en"], "created_at": datetime(2026, 11, 7, 19, 12, tzinfo=timezone.utc)}
    FILE = dict(REC, id=2, input_type="file", song_title="my song.mp3", clip_start_sec=65.0, clip_duration_sec=15.0, first_text="hello", languages=["en", "ja"])

    def test_recording_title_is_save_time_in_seoul_not_recording_wav(self):
        self.assertEqual(web_song.clip_title(self.REC), "🎙 녹음 11-08 04:12")              # 19:12 UTC = 04:12 서울
        self.assertEqual(web_song.clip_title(self.FILE), "my song.mp3")
        self.assertNotIn("recording.wav", web_song.clip_label(self.REC, with_title=True))

    def test_label_puts_distinguishing_parts_first_and_shortens_preview(self):
        lab = web_song.clip_label(self.REC, with_title=True)
        self.assertTrue(lab.startswith("🎙 녹음 11-08 04:12 · “w1 w2 w3 w4 w5 w6…”") or lab.startswith("🎙 녹음 11-08 04:12 · “"))
        self.assertIn("…”", lab)                                                         # 긴 첫 줄은 줄여서
        self.assertTrue(lab.endswith("8줄"))
        self.assertEqual(web_song.clip_label(self.FILE), "“hello” · 00:01:05 ~ 00:01:20 · 8줄")   # 같은 파일 안에서는 제목 생략
        self.assertEqual(web_song.clip_label(dict(self.FILE, first_text=None, n_lines=2)), "00:01:05 ~ 00:01:20 · 2줄")

    def test_detail_has_title_range_lines_languages_and_time(self):
        d = web_song.clip_detail(self.FILE)
        for part in ("my song.mp3", "00:01:05 ~ 00:01:20", "(15초)", "8줄", "영어 + 일본어", "저장 11-08 04:12"):
            self.assertIn(part, d)


if __name__ == "__main__":
    unittest.main()
