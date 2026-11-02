"""model_compare.py 단위 테스트. 실행: python -m unittest tests.test_model_compare -v
Whisper 모델과 OpenAI API를 부르지 않고, stt를 가짜 함수로 바꿔 '모델 × 녹음' 순서와 결과 모양만 확인한다."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import model_compare  # noqa: E402

SENTENCES = [{"id": "1", "lang": "en", "sentence": "I want to explore the universe.",
              "meaning_ko": "나는 우주를 탐험하고 싶어.", "source": "직접 작성", "license": "직접 작성(본인)"}]


class CompareModels(unittest.TestCase):
    """model_compare.compare_models: stt를 가짜로 바꿔 '모델 × 녹음' 순서와 결과 모양만 확인한다(모델·API 없음)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        for take in (1, 2):
            (self.dir / f"s01_take{take}.wav").write_bytes(b"x")   # 인식을 가짜로 바꾸므로 내용은 상관없다

    @staticmethod
    def fake_recognize(path, lang="en", model_size=None, vad_filter=False):
        # 작은 모델은 "to"를 빠뜨리고, 큰 모델은 맞게 인식한다고 가정한 가짜 결과
        return {"tiny": "I want explore the universe.", "small": "I want to explore the universe."}[model_size], 0.5

    def run_compare(self, ids, sizes, takes=(1,)):
        with mock.patch("stt.load_model") as load, mock.patch("stt.recognize", side_effect=self.fake_recognize):
            out = model_compare.compare_models(ids, sizes, takes=takes, sentences=SENTENCES, rec_dir=self.dir)
        return out, load

    def test_one_row_per_model_and_recording(self):
        out, load = self.run_compare([1], ["tiny", "small"], takes=[1, 2])
        self.assertEqual(len(out["rows"]), 4)                                       # 2 모델 × 2 회차
        self.assertEqual([c.args[0] for c in load.call_args_list], ["tiny", "small"])   # 모델은 크기마다 한 번 읽는다
        tiny = [r for r in out["rows"] if r["model"] == "tiny"]
        self.assertTrue(all((r["D"], r["N"]) == (1, 6) and "[-to-]" in r["diff"] for r in tiny))
        self.assertAlmostEqual(tiny[0]["wer"], 1 / 6)
        small = [r for r in out["rows"] if r["model"] == "small"]
        self.assertTrue(all(r["wer"] == 0.0 for r in small))
        self.assertEqual({r["file"] for r in out["rows"]}, {"s01_take1.wav", "s01_take2.wav"})   # 경로가 아니라 이름만
        self.assertEqual(set(out["load_sec"]), {"tiny", "small"})
        self.assertEqual(out["settings"]["device"], "cpu")

    def test_missing_sentence_or_recording_is_reported_not_fatal(self):
        out, _ = self.run_compare([1, 2], ["small"], takes=[1, 3])
        self.assertEqual(len(out["rows"]), 1)                                       # s01_take1만 처리
        self.assertEqual(len(out["missing"]), 2)                                    # 2번 문장 없음, take3 녹음 없음
        self.assertTrue(any("sentences.csv에 없음" in m for m in out["missing"]))
        self.assertTrue(any("take3" in m for m in out["missing"]))

    def test_default_size_and_nothing_found(self):
        with mock.patch("stt.load_model"), mock.patch("stt.recognize", return_value=("hello", 0.1)) as rec:
            out = model_compare.compare_models([1], None, sentences=SENTENCES, rec_dir=self.dir)
        self.assertEqual(out["rows"][0]["model"], "tiny")                           # sizes를 안 주면 기본 크기
        self.assertEqual(rec.call_args.kwargs["model_size"], "tiny")
        empty, _ = self.run_compare([9], ["tiny"])
        self.assertEqual((empty["rows"], len(empty["missing"])), ([], 1))


class CompareVad(unittest.TestCase):
    """vad_filters: 끔/켬을 변수로 비교하는지, 기본값이 기존(끔)과 같은지."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / "s01_take1.wav").write_bytes(b"x")

    def run_compare(self, **kw):
        # VAD를 켜면 "to"를 맞게 인식하는 가짜 모델(small에서 VAD가 결과를 바꾼 사례를 흉내)
        def fake(path, lang="en", model_size=None, vad_filter=False):
            return ("I want to explore the universe." if vad_filter else "I want explore the universe."), 0.1
        with mock.patch("stt.load_model"), mock.patch("stt.recognize", side_effect=fake) as rec:
            out = model_compare.compare_models([1], ["small"], sentences=SENTENCES, rec_dir=self.dir, **kw)
        return out, rec

    def test_default_is_vad_off_only(self):
        out, rec = self.run_compare()
        self.assertEqual([(r["vad"], r["D"]) for r in out["rows"]], [(False, 1)])
        self.assertIs(rec.call_args.kwargs["vad_filter"], False)

    def test_both_settings_give_one_row_each(self):
        out, rec = self.run_compare(vad_filters=(False, True))
        self.assertEqual([(r["model"], r["vad"], r["wer"] == 0.0) for r in out["rows"]],
                         [("small", False, False), ("small", True, True)])     # 끔은 틀리고 켬은 맞는 가짜 결과
        self.assertEqual([c.kwargs["vad_filter"] for c in rec.call_args_list], [False, True])

    def test_single_bool_is_accepted(self):
        out, _ = self.run_compare(vad_filters=True)
        self.assertEqual([r["vad"] for r in out["rows"]], [True])


class CompareModelsRobustness(unittest.TestCase):
    """모델 하나를 읽지 못해도 나머지를 계속하는지, release=True가 모델을 내리는지(모델·API 없이 가짜로 확인)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / "s01_take1.wav").write_bytes(b"x")

    def run_compare(self, sizes, **kw):
        def fake_load(size):
            if size == "bad":
                raise OSError("내려받기 실패")
            return mock.Mock()
        with mock.patch("stt.load_model", side_effect=fake_load), \
             mock.patch("stt.recognize", return_value=("I want to explore the universe.", 0.1)), \
             mock.patch("stt.loaded_models", return_value=("tiny",)), \
             mock.patch("stt.unload_models") as unload:
            out = model_compare.compare_models([1], sizes, sentences=SENTENCES, rec_dir=self.dir, **kw)
        return out, unload

    def test_failed_model_is_skipped_and_reported(self):
        out, _ = self.run_compare(["tiny", "bad", "small"])
        self.assertEqual([r["model"] for r in out["rows"]], ["tiny", "small"])      # bad만 빠지고 계속
        self.assertEqual(list(out["errors"]), ["bad"])
        self.assertIn("OSError", out["errors"]["bad"])
        self.assertEqual(set(out["load_sec"]), {"tiny", "small"})                   # 읽지 못한 크기는 시간 기록 없음

    def test_release_unloads_only_models_it_loaded(self):
        out, unload = self.run_compare(["tiny", "small"], release=True)
        unload.assert_called_once_with("small")             # tiny는 비교 전에 이미 읽혀 있었으므로 남긴다
        self.assertEqual(out["errors"], {})

    def test_no_release_by_default(self):
        _, unload = self.run_compare(["tiny", "small"])
        unload.assert_not_called()


if __name__ == "__main__":
    unittest.main()
