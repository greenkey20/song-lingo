"""web_practice.py 단위 테스트(합성 입력, API 호출 없음)."""
import tempfile
import unittest
from pathlib import Path

import scoring
import web_practice as wp

SENTENCES = [{"id": "3", "lang": "en", "sentence": "We'll sing together until the morning comes.", "meaning_ko": ""}]


class Lyrics(unittest.TestCase):
    def test_split_lyrics(self):
        self.assertEqual(wp.split_lyrics("  a b \n\n c\r\n   \nd"), ["a b", "c", "d"])
        self.assertEqual(wp.split_lyrics(""), [])

    def test_example_lyrics_by_id(self):
        sents = [{"id": "1", "sentence": "One."}, {"id": "2", "sentence": "Two."}, {"id": "9", "sentence": "Nine."}]
        self.assertEqual(wp.example_lyrics(("2", "1", "7"), sents), "Two.\nOne.")

    def test_make_prep(self):
        self.assertIsNone(wp.make_prep(" hi there ")["error"])
        self.assertEqual(wp.make_prep(" hi there ")["text"], "hi there")
        self.assertIsNotNone(wp.make_prep("   ")["error"])

    def test_tts_target_matches_sentences_csv_after_normalize(self):
        path, _ = wp.tts_target("we'll sing together until the morning comes", SENTENCES)
        self.assertEqual(path.name, "s03.wav")                 # 예시 문장과 같으면 그 캐시 파일을 쓴다(과금 없음)
        path2, _ = wp.tts_target("some other line", SENTENCES)
        self.assertTrue(path2.name.startswith("custom_"))

    def test_make_tts_uses_cache_path(self):
        # 파일이 이미 있으면 tts_wav가 API를 부르지 않는다. 가짜 wav를 캐시 경로에 두고 확인한다.
        with tempfile.TemporaryDirectory() as d:
            import tts
            old = tts.CACHE_DIR
            tts.CACHE_DIR = Path(d)
            try:
                p = tts.CACHE_DIR / "s03.wav"
                p.write_bytes(b"RIFF....WAVE")                 # 헤더가 wav가 아니어도 fix_wav_header는 건드리지 않는다
                before = tts.calls
                self.assertEqual(wp.make_tts("We'll sing together until the morning comes.", SENTENCES), p)
                self.assertEqual(tts.calls, before)
            finally:
                tts.CACHE_DIR = old


class Rendering(unittest.TestCase):
    def setUp(self):
        # 설계 시안과 같은 예: 따라읽기에서 will→are, sing→seeing
        self.score = scoring.evaluate("We'll sing together until the morning comes.",
                                      "We are seeing together until the morning comes.")

    def test_numbers_match_scoring(self):
        card = wp.result_card_html(self.score)
        self.assertIn("25.0%", card)                           # WER 2/8
        self.assertIn("15.8%", card)                           # CER 6/38
        self.assertIn("8단어 중 2개", card)
        self.assertIn("2 · 0 · 0", card)

    def test_word_cells_kinds(self):
        ops = [("일치", "a", "a"), ("치환", "b", "x"), ("삭제", "c", None), ("삽입", None, "d")]
        self.assertEqual([c["kind"] for c in wp.word_cells(ops)], ["same", "sub", "del", "ins"])

    def test_diff_html_marks_wrong_words_and_escapes(self):
        out = wp.diff_html([("일치", "a", "a"), ("치환", "b", "<script>")])
        self.assertIn("바뀜", out)
        self.assertIn("sl-wrong", out)
        self.assertNotIn("<script>", out)                      # 사용자가 적은 글은 HTML로 해석되지 않는다
        self.assertIn("&lt;script&gt;", out)

    def test_diff_html_uses_underline_not_only_color(self):
        out = wp.diff_html(self.score["main"]["ops"])
        self.assertIn("sl-und", out)

    def test_quality_chips(self):
        good = {"metrics": {"rms_dbfs": -25.0, "peak": 0.5, "silent_ratio": 0.1, "clip_ratio": 0.0}}
        bad = {"metrics": {"rms_dbfs": -70.0, "peak": 0.001, "silent_ratio": 0.9, "clip_ratio": 0.05}}
        self.assertTrue(all(ok for _t, ok in wp.quality_chips(good)))
        self.assertFalse(any(ok for _t, ok in wp.quality_chips(bad)))

    def test_pct_can_exceed_100(self):
        self.assertEqual(wp.pct(1.5), "150.0%")


if __name__ == "__main__":
    unittest.main()
