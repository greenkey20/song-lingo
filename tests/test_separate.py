"""separate.py 단위 테스트. 실행: python -m unittest tests.test_separate -v
곡도 Demucs 모델도 쓰지 않는다: 합성 사인파로 만든 임시 wav와 가짜 분리 함수만 쓴다(느리고 모델 다운로드가 필요하므로)."""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import separate  # noqa: E402


def write_sine(path, seconds, sr, channels=2, freq=440.0):
    t = np.arange(int(seconds * sr)) / sr
    x = (0.5 * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    x = np.stack([x] * channels, axis=1) if channels > 1 else x
    wavfile.write(path, sr, x)


class FakeModel:
    sources = ["drums", "bass", "other", "vocals"]


def fake_apply(model, wav, device="cpu", split=True, overlap=0.25, progress=False):
    """입력 소리를 네 갈래로 나눈 척한다: vocals는 입력의 절반, 나머지는 입력의 1/6씩."""
    import torch
    parts = [wav / 6, wav / 6, wav / 6, wav / 2]
    return torch.stack(parts, dim=1)          # (배치, 소리 수, 채널, 샘플)


class Songs(unittest.TestCase):
    def test_list_songs_sorted_and_filters_non_audio(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "en").mkdir()
            for n in ["b.wma", "a.mp3", ".DS_Store", "notes.txt", "C.WAV"]:
                Path(d, "en", n).touch()
            self.assertEqual([p.name for p in separate.list_songs("en", d)], ["C.WAV", "a.mp3", "b.wma"])   # 이름순(대문자 먼저)
            with self.assertRaises(FileNotFoundError):
                separate.list_songs("fr", d)


class Clip(unittest.TestCase):
    def test_slice_length_and_resample_to_44100_stereo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "s.wav"); write_sine(p, 5.0, 32000)       # 32 kHz 스테레오 5초
            c = separate.load_clip(p, start=1.0, duration=2.0)
            self.assertEqual(c.shape[0], 2)
            self.assertAlmostEqual(c.shape[1] / 44100, 2.0, places=2)
            self.assertEqual(c.dtype, np.float32)
            self.assertGreater(float(np.abs(c).max()), 0.4)       # 소리가 사라지지 않았다

    def test_mono_is_duplicated_to_stereo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "m.wav"); write_sine(p, 2.0, 44100, channels=1)
            c = separate.load_clip(p, 0.0, 1.0)
            self.assertEqual(c.shape, (2, 44100))
            self.assertTrue(np.array_equal(c[0], c[1]))

    def test_short_song_gives_what_exists_and_start_beyond_end_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "s.wav"); write_sine(p, 1.0, 44100)
            self.assertAlmostEqual(separate.load_clip(p, 0.5, 20.0).shape[1] / 44100, 0.5, places=2)
            with self.assertRaises(ValueError):
                separate.load_clip(p, 5.0, 1.0)
            with self.assertRaises(ValueError):
                separate.load_clip(p, -1.0, 1.0)


class Separation(unittest.TestCase):
    def test_returns_vocals_source_with_original_scale(self):
        t = np.arange(44100) / 44100
        clip = np.stack([0.4 * np.sin(2 * np.pi * 440 * t)] * 2).astype(np.float32)
        v = separate.separate_vocals(clip, model=FakeModel(), apply_fn=fake_apply)
        self.assertEqual(v.shape, clip.shape)
        # 가짜 분리에서 vocals = 입력의 절반이므로, 정규화했다가 되돌려도 크기가 절반이어야 한다(정규화 왕복이 맞는지)
        self.assertTrue(np.allclose(v, clip / 2, atol=1e-5))

    def test_silence_skips_model(self):
        def boom(*a, **k):
            raise AssertionError("무음에는 모델을 돌리면 안 된다")
        v = separate.separate_vocals(np.zeros((2, 1000), dtype=np.float32), model=FakeModel(), apply_fn=boom)
        self.assertEqual(v.shape, (2, 1000))
        self.assertEqual(float(np.abs(v).max()), 0.0)

    def test_wrong_shape_or_sr_raises(self):
        with self.assertRaises(ValueError):
            separate.separate_vocals(np.zeros(100, dtype=np.float32), model=FakeModel(), apply_fn=fake_apply)
        with self.assertRaises(ValueError):
            separate.separate_vocals(np.zeros((2, 100), dtype=np.float32), sr=16000, model=FakeModel(), apply_fn=fake_apply)


class Process(unittest.TestCase):
    def test_saves_files_manifest_and_protects_existing(self):
        with tempfile.TemporaryDirectory() as d:
            song = Path(d, "s.wav"); write_sine(song, 3.0, 44100)
            work = Path(d, "work")
            sep = lambda clip: clip / 2                                    # 가짜 분리
            r = separate.process_clip(song, 0.5, 1.0, "c01", work_dir=work, separate=sep)
            sr_m, mix = wavfile.read(r["mix"]); sr_v, voc = wavfile.read(r["vocals"])
            self.assertEqual((sr_m, sr_v, mix.shape, voc.dtype), (44100, 44100, (44100, 2), np.int16))
            self.assertLess(np.abs(voc.astype(int)).max(), np.abs(mix.astype(int)).max())
            with open(work / "clips.csv", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows, [{"clip_id": "c01", "song_file": "s.wav", "start": "0.5", "duration": "1.0"}])
            with self.assertRaises(FileExistsError):
                separate.process_clip(song, 0.5, 1.0, "c01", work_dir=work, separate=sep)
            separate.process_clip(song, 1.0, 1.0, "c01", work_dir=work, separate=sep, overwrite=True)
            with open(work / "clips.csv", newline="", encoding="utf-8") as f:
                self.assertEqual([r["start"] for r in csv.DictReader(f)], ["1.0"])    # 같은 id는 한 줄만 남는다


class CutThenSeparate(unittest.TestCase):
    """자르기(cut_clip)와 분리(separate_clip)를 따로 부르는 흐름."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.song = self.d / "s.wav"
        write_sine(self.song, 4.0, 44100)
        self.work = self.d / "work"
        self.half = lambda clip: clip / 2                         # 가짜 분리

    def tearDown(self):
        self.tmp.cleanup()

    def test_cut_only_makes_mix_and_manifest_but_no_vocals(self):
        r = separate.cut_clip(self.song, 1.0, 2.0, "c01", work_dir=self.work)
        self.assertAlmostEqual(r["seconds"], 2.0, places=2)
        self.assertTrue((self.work / "c01_mix.wav").exists())
        self.assertFalse((self.work / "c01_vocals.wav").exists())
        self.assertEqual(separate.manifest_row("c01", self.work)["start"], "1.0")
        with self.assertRaises(FileExistsError):
            separate.cut_clip(self.song, 1.0, 2.0, "c01", work_dir=self.work)

    def test_separate_clip_reads_saved_mix_and_requires_cut_first(self):
        with self.assertRaises(FileNotFoundError):
            separate.separate_clip("c01", work_dir=self.work, separate=self.half)
        separate.cut_clip(self.song, 0.5, 1.0, "c01", work_dir=self.work)
        r = separate.separate_clip("c01", work_dir=self.work, separate=self.half)
        _, mix = wavfile.read(self.work / "c01_mix.wav"); _, voc = wavfile.read(r["vocals"])
        self.assertEqual(voc.shape, mix.shape)
        self.assertLess(np.abs(voc.astype(int)).max(), np.abs(mix.astype(int)).max())
        with self.assertRaises(FileExistsError):
            separate.separate_clip("c01", work_dir=self.work, separate=self.half)
        separate.separate_clip("c01", work_dir=self.work, separate=self.half, overwrite=True)

    def test_recut_removes_stale_vocals_and_is_cut_current_detects_change(self):
        separate.cut_clip(self.song, 0.5, 1.0, "c01", work_dir=self.work)
        separate.separate_clip("c01", work_dir=self.work, separate=self.half)
        self.assertTrue(separate.is_cut_current(self.song, 0.5, 1.0, "c01", self.work))
        self.assertFalse(separate.is_cut_current(self.song, 1.5, 1.0, "c01", self.work))     # start가 바뀜
        self.assertFalse(separate.is_cut_current(self.song, 0.5, 1.0, "c99", self.work))     # 아직 안 자름
        separate.cut_clip(self.song, 1.5, 1.0, "c01", work_dir=self.work, overwrite=True)
        self.assertFalse((self.work / "c01_vocals.wav").exists())                            # 옛 보컬은 지워짐
        self.assertTrue(separate.is_cut_current(self.song, 1.5, 1.0, "c01", self.work))


if __name__ == "__main__":
    unittest.main()
