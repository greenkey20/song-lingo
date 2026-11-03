"""clip_compare.py 단위 테스트. 실행: python -m unittest tests.test_clip_compare -v
모델도 곡도 쓰지 않는다: 빈 wav 파일과 가짜 인식 함수, 임의로 만든 문장만 쓴다."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import clip_compare  # noqa: E402

REF = "alpha bravo charlie delta"


def make_clip(work, cid, truth=REF, mix=True, vocals=True):
    work = Path(work)
    (work / "truth").mkdir(parents=True, exist_ok=True)
    if mix:
        (work / f"{cid}_mix.wav").touch()
    if vocals:
        (work / f"{cid}_vocals.wav").touch()
    if truth is not None:
        (work / "truth" / f"{cid}.txt").write_text(truth, encoding="utf-8")


CALLS = []     # 가짜 인식 함수가 받은 temperature 인자를 기록한다(None이면 인자를 아예 안 받은 것)


def fake_recognize(path, language="en", model_size=None, vad_filter=False, **kw):
    """mix는 한 단어 틀리게, vocals는 정확히, base 크기는 mix도 정확히 돌려주는 가짜. temperature=0.0이면 mix도 정확히."""
    CALLS.append(kw.get("temperature", "안 줌"))
    if "_vocals" in Path(path).name or model_size == "base" or kw.get("temperature") == 0.0:
        return REF, 0.5
    return "alpha bravo charlie echo", 0.4


class Files(unittest.TestCase):
    def test_truth_joins_lines_and_available_reports_missing(self):
        with tempfile.TemporaryDirectory() as d:
            make_clip(d, "c01", truth="alpha bravo\n  charlie   delta\n")
            make_clip(d, "c02", truth=None)                     # 정답 없음
            make_clip(d, "c03", vocals=False)                   # 보컬 없음
            make_clip(d, "c04", truth="  \n")                   # 정답 파일은 있지만 비어 있음
            self.assertEqual(clip_compare.load_truth("c01", d), REF)
            ok, missing = clip_compare.available_clips(d)
            self.assertEqual(ok, ["c01"])
            self.assertEqual(missing, {"c02": ["정답"], "c03": ["vocals"], "c04": ["정답(비어 있음)"]})


class Compare(unittest.TestCase):
    def run_compare(self, d, **kw):
        make_clip(d, "c01")
        make_clip(d, "c02")
        return clip_compare.compare(["c01", "c02"], work_dir=d, recognize=fake_recognize, **kw)

    def test_grid_size_and_scores(self):
        with tempfile.TemporaryDirectory() as d:
            m, t = self.run_compare(d, sizes=("tiny", "base"), vads=(False, True))
            self.assertEqual(len(m), 2 * 2 * 2 * 2)             # 구간2 × 소리2 × 크기2 × VAD2
            tiny_mix = m[(m["size"] == "tiny") & (m["source"] == "mix") & (m["clip"] == "c01")].iloc[0]
            self.assertEqual((tiny_mix["S"], tiny_mix["D"], tiny_mix["I"], tiny_mix["N"]), (1, 0, 0, 4))
            self.assertAlmostEqual(tiny_mix["WER"], 0.25)
            self.assertEqual(float(m[(m["source"] == "vocals")]["WER"].max()), 0.0)

    def test_metrics_have_no_lyrics_but_texts_do(self):
        with tempfile.TemporaryDirectory() as d:
            m, t = self.run_compare(d, sizes=("tiny",))
            self.assertNotIn("hyp", m.columns)
            self.assertNotIn("ref", m.columns)
            self.assertEqual(set(t.columns), {"clip", "source", "size", "vad", "temp", "run", "ref", "hyp"})
            self.assertEqual(len(m), len(t))

    def test_summary_micro_and_pivot(self):
        with tempfile.TemporaryDirectory() as d:
            m, _ = self.run_compare(d, sizes=("tiny", "base"))
            s = clip_compare.summarize(m)
            row = s[(s["size"] == "tiny") & (s["source"] == "mix")].iloc[0]
            self.assertEqual((row["clips"], row["errors"], row["N"]), (2, 2, 8))
            self.assertAlmostEqual(row["micro_WER"], 0.25)
            self.assertAlmostEqual(s[(s["size"] == "base") & (s["source"] == "mix")].iloc[0]["micro_WER"], 0.0)
            p = clip_compare.pivot_wer(m)
            self.assertEqual(list(p.index), ["c01", "c02"])
            self.assertIn("tiny/VAD끔/기본/mix", p.columns)


class TemperatureAndRepeats(unittest.TestCase):
    def test_temperature_is_passed_only_when_set_and_labeled(self):
        with tempfile.TemporaryDirectory() as d:
            make_clip(d, "c01")
            CALLS.clear()
            m, _ = clip_compare.compare(["c01"], sizes=("tiny",), work_dir=d, recognize=fake_recognize, temperatures=(None, 0.0))
            self.assertEqual(sorted(set(CALLS), key=str), [0.0, "안 줌"])         # None은 인자를 넘기지 않음, 0.0은 넘김
            self.assertEqual(set(m["temp"]), {"기본", "T0.0"})
            mix = m[(m["source"] == "mix")].set_index("temp")["WER"]
            self.assertAlmostEqual(mix["기본"], 0.25); self.assertAlmostEqual(mix["T0.0"], 0.0)

    def test_repeats_give_run_column_and_range(self):
        outputs = iter(["alpha bravo charlie delta", "alpha bravo charlie echo", "alpha bravo charlie delta"])   # mix만 흔들림

        def flaky(path, language="en", model_size=None, vad_filter=False, **kw):
            if "_vocals" in Path(path).name:
                return REF, 0.1
            return next(outputs), 0.1

        with tempfile.TemporaryDirectory() as d:
            make_clip(d, "c01")
            m, _ = clip_compare.compare(["c01"], sizes=("tiny",), work_dir=d, recognize=flaky, repeats=3)
            self.assertEqual(sorted(set(m["run"])), [1, 2, 3])
            row = clip_compare.summarize(m).query("source == 'mix'").iloc[0]
            self.assertEqual(row["runs"], 3)
            self.assertAlmostEqual(row["micro_min"], 0.0); self.assertAlmostEqual(row["micro_max"], 0.25)
            self.assertAlmostEqual(row["micro_WER"], 0.25 / 3)                    # 세 번 중 한 번만 1/4 틀림


class Sources(unittest.TestCase):
    def test_sources_subset_halves_runs_and_validates(self):
        with tempfile.TemporaryDirectory() as d:
            make_clip(d, "c01")
            m, t = clip_compare.compare(["c01"], sizes=("tiny",), work_dir=d, recognize=fake_recognize, sources=("vocals",))
            self.assertEqual(set(m["source"]), {"vocals"})
            self.assertEqual(len(m), 1)
            with self.assertRaises(ValueError):
                clip_compare.compare(["c01"], work_dir=d, recognize=fake_recognize, sources=("music",))
            with self.assertRaises(ValueError):
                clip_compare.compare(["c01"], work_dir=d, recognize=fake_recognize, sources=())


class Progress(unittest.TestCase):
    def test_progress_called_once_per_condition_group(self):
        msgs = []
        with tempfile.TemporaryDirectory() as d:
            make_clip(d, "c01"); make_clip(d, "c02")
            clip_compare.compare(["c01", "c02"], sizes=("tiny", "base"), vads=(False, True), work_dir=d,
                                 recognize=fake_recognize, sources=("vocals",), progress=msgs.append)
        self.assertEqual(len(msgs), 4)                         # 크기 2 × VAD 2 조건
        self.assertTrue(msgs[-1].startswith("[8/8]"))          # 구간 2 × 소리 1 × 4조건 = 8번
        self.assertIn("tiny VAD끔", msgs[0])


class Stt(unittest.TestCase):
    """stt.recognize가 temperature를 transcribe에 올바르게 넘기는지(모델 없이 가짜 모델로)."""

    def test_recognize_passes_temperature_only_when_given(self):
        import stt

        class Seg:
            text = " hi"

        class FakeModel:
            def __init__(self): self.kw = None
            def transcribe(self, path, **kw):
                self.kw = kw
                return iter([Seg()]), None

        fake = FakeModel()
        orig = stt.load_model
        stt.load_model = lambda size=None: fake
        try:
            stt.recognize("x.wav")
            self.assertNotIn("temperature", fake.kw)                       # 안 주면 기본 동작 그대로
            stt.recognize("x.wav", temperature=0.0)
            self.assertEqual(fake.kw["temperature"], 0.0)
            text, _ = stt.recognize("x.wav", vad_filter=True, temperature=0.0)
            self.assertEqual((text, fake.kw["vad_filter"]), ("hi", True))
        finally:
            stt.load_model = orig


if __name__ == "__main__":
    unittest.main()
