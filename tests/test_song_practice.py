"""song_practice.py 단위 테스트(이슈 #31). 가짜 인식 함수와 임시 폴더만 쓴다(곡·가사·모델 없음; 글은 의미 없는 w1, w2 …).
실행: python -m unittest tests.test_song_practice -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import song_practice  # noqa: E402


def fake_segments(n_words_each=(6, 6)):
    segs, t, k = [], 0.0, 1
    for n in n_words_each:
        ws = []
        for _ in range(n):
            ws.append({"word": f"w{k}", "start": round(t, 2), "end": round(t + 0.4, 2), "prob": 0.9})
            t += 0.5
            k += 1
        segs.append({"start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(w["word"] for w in ws), "avg_logprob": -0.3,
                     "no_speech_prob": 0.01, "compression_ratio": 1.2, "words": ws})
        t += 1.0
    return segs


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name, "work"); self.work.mkdir()
        self.out = Path(self.tmp.name, "out")
        (self.work / "c01_mix.wav").write_bytes(b"RIFF")                         # 존재만 확인하므로 내용은 필요 없다
        (self.work / "clips.csv").write_text("clip_id,song_file,start,duration\nc01,secret.wma,61,20\n", encoding="utf-8")
        self.calls = []

        def rec(path, language, **kw):
            self.calls.append((path, language, kw))
            return fake_segments(), 12.34
        self.rec = rec

    def prepare(self, **kw):
        return song_practice.prepare_lines("c01", work_dir=self.work, out_dir=self.out, recognize=self.rec, **kw)


class Prepare(Base):
    def test_calls_recognizer_with_song_settings_and_saves_lines(self):
        doc = self.prepare()
        path, lang, kw = self.calls[0]
        self.assertEqual(path, str(self.work / "c01_mix.wav"))                    # 변환 배열이 아니라 파일 경로 그대로
        self.assertEqual((lang, kw["model_size"], kw["vad_filter"], kw["word_timestamps"]), ("en", "medium", False, True))
        self.assertEqual(len(doc["lines"]), 2)
        saved = json.loads((self.out / "c01" / "lines.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["lines"][0]["stt_text"], saved["lines"][0]["text"])
        self.assertEqual((saved["lines"][0]["status"], saved["lines"][0]["edited"]), ("candidate", False))
        self.assertEqual((saved["start"], saved["duration"]), (61.0, 20.0))

    def test_song_file_name_is_not_saved(self):
        self.prepare()
        self.assertNotIn("secret", (self.out / "c01" / "lines.json").read_text(encoding="utf-8"))

    def test_missing_clip_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            song_practice.prepare_lines("c99", work_dir=self.work, out_dir=self.out, recognize=self.rec)

    def test_does_not_overwrite_existing_and_keeps_previous_on_overwrite(self):
        self.prepare()
        song_practice.apply_edits("c01", {1: "my fixed line"}, out_dir=self.out)
        with self.assertRaises(FileExistsError):                                   # 고친 가사를 지킨다
            self.prepare()
        self.assertEqual(song_practice.load_lines("c01", self.out)["lines"][0]["text"], "my fixed line")
        self.prepare(overwrite=True)
        prev = json.loads((self.out / "c01" / "lines.prev.json").read_text(encoding="utf-8"))
        self.assertEqual(prev["lines"][0]["text"], "my fixed line")                # 옛 파일이 남는다
        self.assertEqual(song_practice.load_lines("c01", self.out)["lines"][0]["status"], "candidate")

    def test_split_arguments_are_passed_to_line_rules(self):
        doc = self.prepare(min_words=1, min_sec=0.1, max_words=4, max_sec=99)       # 6단어 구간이 4단어 한도에 걸려 쪼개짐
        self.assertGreater(len(doc["lines"]), 2)


class Edits(Base):
    def setUp(self):
        super().setUp()
        self.prepare()

    def test_edit_marks_edited_and_confirmed_and_keeps_original(self):
        orig = song_practice.load_lines("c01", self.out)["lines"][0]["stt_text"]
        doc = song_practice.apply_edits("c01", {1: "  corrected words  "}, out_dir=self.out)
        ln = doc["lines"][0]
        self.assertEqual((ln["text"], ln["stt_text"], ln["edited"], ln["status"]), ("corrected words", orig, True, "confirmed"))

    def test_same_text_is_confirmed_but_not_edited(self):
        same = song_practice.load_lines("c01", self.out)["lines"][0]["stt_text"]
        ln = song_practice.apply_edits("c01", {1: same}, out_dir=self.out)["lines"][0]
        self.assertEqual((ln["edited"], ln["status"]), (False, "confirmed"))

    def test_confirm_and_drop(self):
        doc = song_practice.apply_edits("c01", confirm=[1], drop=[2], out_dir=self.out)
        self.assertEqual([l["status"] for l in doc["lines"]], ["confirmed", "dropped"])
        self.assertEqual([l["no"] for l in song_practice.confirmed_lines("c01", self.out)], [1])
        self.assertEqual(song_practice.status_summary("c01", self.out), {"candidate": 0, "confirmed": 1, "dropped": 1, "edited": 0, "suspect": 0})

    def test_unknown_line_or_empty_text_raises_and_nothing_is_saved(self):
        with self.assertRaises(ValueError):
            song_practice.apply_edits("c01", {1: "ok", 9: "x"}, out_dir=self.out)
        with self.assertRaises(ValueError):
            song_practice.apply_edits("c01", {1: "   "}, out_dir=self.out)
        self.assertEqual(song_practice.load_lines("c01", self.out)["lines"][0]["status"], "candidate")    # 일부만 반영되지 않음

    def test_load_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            song_practice.load_lines("c77", self.out)

    def test_confirmed_lines_do_not_include_dropped_or_candidates(self):
        song_practice.apply_edits("c01", {2: "line two"}, out_dir=self.out)
        got = song_practice.confirmed_lines("c01", self.out)
        self.assertEqual([(l["no"], l["text"]) for l in got], [(2, "line two")])


if __name__ == "__main__":
    unittest.main()
