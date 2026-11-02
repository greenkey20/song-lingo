"""recorder.py + scripts/record_takes.py 단위 테스트. 실행: python -m unittest tests.test_recorder -v
마이크 대신 가짜 sounddevice를 쓰고, 파일은 임시 폴더에만 만든다."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import recorder  # noqa: E402
import record_takes  # noqa: E402


class FakeStream:
    def __init__(self, owner, callback, blocksize=480):
        self.owner, self.callback, self.blocksize = owner, callback, blocksize

    def start(self):
        # 마이크가 440 Hz 소리를 4조각 보내 준 것처럼 callback을 직접 부른다.
        for i in range(4):
            t = (np.arange(self.blocksize) + i * self.blocksize) / self.owner.sr
            block = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)[:, None].repeat(self.owner.channels, axis=1)
            self.callback(block, self.blocksize, None, None)

    def stop(self):
        pass

    def close(self):
        pass


class FakeSD:
    def __init__(self, max_in=2, sr=48000):
        self.max_in, self.sr, self.channels, self.played = max_in, sr, None, None

    def query_devices(self, device=None, kind=None):
        return {"name": "Fake Mic", "max_input_channels": self.max_in, "default_samplerate": float(self.sr)}

    def InputStream(self, samplerate, channels, dtype, device, callback):
        self.channels = channels
        return FakeStream(self, callback)

    def play(self, x, sr):
        self.played = (x, sr)

    def wait(self):
        pass


class Names(unittest.TestCase):
    def test_path_two_digits(self):
        self.assertEqual(recorder.recording_path(1, 2, "d").as_posix(), "d/s01_take2.wav")
        self.assertEqual(recorder.recording_path("10", 3, "d").name, "s10_take3.wav")

    def test_next_take_fills_gap_and_status(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ["s01_take1.wav", "s01_take3.wav", "s02_take1.wav", "s01_take2.m4a", "memo.wav"]:
                Path(d, name).touch()
            self.assertEqual(recorder.existing_takes(1, d), [1, 3])
            self.assertEqual(recorder.next_take(1, d), 2)
            self.assertEqual(recorder.next_take(5, d), 1)
            have, missing = recorder.take_status([1, 2], 3, d)
            self.assertEqual(have, {1: [1, 3], 2: [1]})
            self.assertEqual(missing, [(1, 2), (2, 2), (2, 3)])

    def test_order_round_vs_sentence(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "s01_take1.wav").touch()          # 문장 1은 1회차만 있음
            _, rnd = recorder.take_status([1, 2, 3], 2, d)                      # 기본 = round
            _, snt = recorder.take_status([1, 2, 3], 2, d, order="sentence")
            self.assertEqual(rnd, [(2, 1), (3, 1), (1, 2), (2, 2), (3, 2)])     # 1회차 먼저(1번은 건너뜀) → 2회차
            self.assertEqual(snt, [(1, 2), (2, 1), (2, 2), (3, 1), (3, 2)])
            with self.assertRaises(ValueError):
                recorder.take_status([1], 2, d, order="x")


class Saving(unittest.TestCase):
    def test_mono_becomes_stereo_int16_same_channels(self):
        y = recorder.to_stereo_int16(np.array([0.0, 0.5, -0.5], dtype=np.float32))
        self.assertEqual(y.shape, (3, 2))
        self.assertEqual(y.dtype, np.int16)
        self.assertTrue(np.array_equal(y[:, 0], y[:, 1]))

    def test_clip_does_not_wrap(self):
        y = recorder.to_stereo_int16(np.array([2.0, -2.0], dtype=np.float32))
        self.assertEqual(y[:, 0].tolist(), [32767, -32767])

    def test_save_wav_format_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = recorder.recording_path(1, 1, Path(d) / "sub")      # 폴더가 없어도 만들어야 한다
            recorder.save_wav(p, np.zeros(480, dtype=np.float32), 48000)
            sr, x = wavfile.read(p)
            self.assertEqual((sr, x.shape, x.dtype), (48000, (480, 2), np.int16))
            with self.assertRaises(FileExistsError):
                recorder.save_wav(p, np.zeros(10), 48000)
            recorder.save_wav(p, np.zeros(10), 48000, overwrite=True)
            self.assertEqual(wavfile.read(p)[1].shape, (10, 2))


class Mic(unittest.TestCase):
    def test_record_and_stop(self):
        sd = FakeSD()
        rec = recorder.Recorder(sd=sd)
        self.assertEqual((rec.sr, rec.channels, rec.device_name), (48000, 2, "Fake Mic"))
        rec.start()
        self.assertTrue(rec.recording)
        self.assertGreater(rec.level(), 0.3)
        x = rec.stop()
        self.assertEqual(x.shape, (1920, 2))
        self.assertFalse(rec.recording)
        with self.assertRaises(RuntimeError):
            rec.stop()

    def test_mono_device_falls_back_to_one_channel(self):
        rec = recorder.Recorder(sd=FakeSD(max_in=1))
        self.assertEqual(rec.channels, 1)
        rec.start()
        self.assertEqual(rec.stop().shape, (1920, 1))

    def test_max_seconds_caps_buffer(self):
        rec = recorder.Recorder(sd=FakeSD(), max_seconds=0.02)   # 960 샘플 = 2조각
        rec.start()
        self.assertLess(len(rec.stop()), 1920)

    def test_double_start_raises(self):
        rec = recorder.Recorder(sd=FakeSD())
        rec.start()
        with self.assertRaises(RuntimeError):
            rec.start()


class Session(unittest.TestCase):
    ROWS = [{"id": "1", "sentence": "Hello there.", "meaning_ko": "안녕."},
            {"id": "2", "sentence": "Good night.", "meaning_ko": "잘 자."}]

    def run_session(self, answers, root, todo, redo=False):
        it = iter(answers)
        rec = recorder.Recorder(sd=FakeSD())
        return record_takes.session(self.ROWS, todo, rec, root, ask=lambda prompt: next(it), redo=redo)

    def test_records_in_order_and_saves_files(self):
        with tempfile.TemporaryDirectory() as d:
            # 건마다: 시작(Enter) → 끝(Enter) → 다음(Enter)
            n = self.run_session([""] * 6, d, [(1, 1), (2, 1)])
            self.assertEqual(n, 2)
            self.assertEqual(sorted(p.name for p in Path(d).glob("*.wav")), ["s01_take1.wav", "s02_take1.wav"])

    def test_redo_overwrites_same_take_then_quit_stops(self):
        with tempfile.TemporaryDirectory() as d:
            # 1건 녹음 → r(다시) → 같은 건 재녹음 → 다음 → 두 번째 건에서 q
            n = self.run_session(["", "", "r", "", "", "", "q"], d, [(1, 1), (2, 1)])
            self.assertEqual(n, 1)
            self.assertEqual([p.name for p in Path(d).glob("*.wav")], ["s01_take1.wav"])

    def test_skip_and_existing_file_not_touched_without_redo(self):
        with tempfile.TemporaryDirectory() as d:
            n = self.run_session(["s"], d, [(1, 1)])
            self.assertEqual(n, 0)
            self.assertEqual(list(Path(d).glob("*.wav")), [])


if __name__ == "__main__":
    unittest.main()
