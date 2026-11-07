"""practice_log.py 단위 테스트(임시 파일, 가사 없음)."""
import tempfile
import unittest
from pathlib import Path

import practice
import practice_log as pl
import scoring

SENTS = [{"id": "3", "lang": "en", "sentence": "We'll sing together until the morning comes.", "meaning_ko": ""}]


def _res(ref, hyp):
    return {"mode": "dictation", "error": None, "hyp": hyp, "score": scoring.evaluate(ref, hyp)}


class Time(unittest.TestCase):
    def test_record_time_is_seoul_regardless_of_server_timezone(self):
        rec = pl.make_record("lyrics", "Hello there.", "dictation", _res("Hello there.", "hello there"), SENTS, now=0)
        self.assertEqual(rec["ts"], "1970-01-01 09:00:00")                       # 에포크 0 = UTC 00:00 = 서울 09:00


class Log(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sub" / "log.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def test_key_for_sample_and_custom(self):
        self.assertEqual(pl.sentence_key("we'll sing together until the morning comes", SENTS), "s03")
        k = pl.sentence_key("Some other line!", SENTS)
        self.assertTrue(k.startswith("h_") and len(k) == 12)
        self.assertEqual(k, pl.sentence_key("some other  line", SENTS))      # 정규화 뒤 같으면 같은 key

    def test_record_has_numbers_and_no_text(self):
        ref = "We'll sing together until the morning comes."
        rec = pl.make_record("lyrics", ref, "dictation", _res(ref, "We will sing together until morning come."), SENTS, now=0)
        self.assertEqual((rec["wer"], rec["S"], rec["D"], rec["I"], rec["n_words"]), (0.25, 1, 1, 0, 8))
        self.assertNotIn("together", " ".join(str(v) for v in rec.values()))     # 문장 글이 기록에 없다
        self.assertEqual(rec["stt"], "")                                          # 받아쓰기는 STT 설정 없음

    def test_error_result_not_recorded(self):
        self.assertIsNone(pl.make_record("lyrics", "a b", "read", {"error": "녹음 없음", "score": None}))
        self.assertIsNone(pl.append(None, self.path))
        self.assertFalse(self.path.exists())

    def test_append_read_roundtrip_and_header_once(self):
        ref = "We'll sing together until the morning comes."
        for hyp in ("We'll sing together until the morning comes.", "We will sing together until morning come."):
            pl.append(pl.make_record("sample", ref, "dictation", _res(ref, hyp), SENTS), self.path)
        rows = pl.read_all(self.path)
        self.assertEqual([r["wer"] for r in rows], [0.0, 0.25])
        self.assertEqual(self.path.read_text(encoding="utf-8").count("ts,source"), 1)    # 머리글은 한 번만
        self.assertEqual(len(pl.attempts(rows, "s03", "dictation")), 2)
        self.assertEqual(pl.attempts(rows, "s03", "read"), [])
        self.assertEqual(pl.practiced_keys(rows, "sample"), {"s03"})
        self.assertEqual(pl.practiced_keys(rows, "song"), set())

    def test_read_all_missing_and_corrupt(self):
        self.assertEqual(pl.read_all(self.path), [])
        self.path.parent.mkdir(parents=True)
        self.path.write_text(",".join(pl.FIELDS) + "\n2026-11-05,lyrics,s01,read,abc,0,0,0,0,1,1,,True\n", encoding="utf-8")
        self.assertEqual(pl.read_all(self.path), [])                               # 숫자가 깨진 줄은 건너뜀

    def test_step_percent(self):
        self.assertEqual(pl.step_percent(8), 12.5)
        self.assertIsNone(pl.step_percent(0))


if __name__ == "__main__":
    unittest.main()
