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


def fake_recognize(path, language="en", model_size=None, vad_filter=False):
    """mix는 한 단어 틀리게, vocals는 정확히, base 크기는 mix도 정확히 돌려주는 가짜."""
    if "_vocals" in Path(path).name or model_size == "base":
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
            self.assertEqual(set(t.columns), {"clip", "source", "size", "vad", "ref", "hyp"})
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
            self.assertIn("tiny/VAD끔/mix", p.columns)


if __name__ == "__main__":
    unittest.main()
