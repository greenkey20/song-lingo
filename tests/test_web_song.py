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


if __name__ == "__main__":
    unittest.main()
