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



class Sounds(unittest.TestCase):
    def test_normalized_sounds_from_path_and_bytes(self):
        import numpy as np
        import recorder
        with tempfile.TemporaryDirectory() as d:
            t = np.arange(16000) / 16000
            quiet = (0.05 * np.sin(2 * np.pi * 440 * t)).astype("float32")
            loud = (0.8 * np.sin(2 * np.pi * 660 * t)).astype("float32")
            a, b = Path(d) / "a.wav", Path(d) / "b.wav"
            recorder.save_wav(a, np.stack([quiet, quiet], 1), 16000)
            recorder.save_wav(b, np.stack([loud, loud], 1), 16000)
            out = wp.normalized_sounds(a, b.read_bytes())                  # 둘째는 bytes(웹 녹음)
            self.assertEqual([n for n, _ in out], ["표준 발음", "내 녹음"])
            for _n, x in out:
                self.assertAlmostEqual(float(abs(x).max()), 0.9, places=2)   # 소리 크기 차이는 지워져 둘 다 0.9
            silent = Path(d) / "s.wav"
            recorder.save_wav(silent, np.zeros((16000, 2), dtype="float32"), 16000)
            self.assertEqual(float(abs(wp.normalized_sounds(silent, silent)[0][1]).max()), 0.0)   # 무음은 0으로 나눠 깨지지 않는다



class ErrorSpans(unittest.TestCase):
    PREP = {"error": None, "text": "we will sing", "lang": "en", "tts_path": "x.wav"}

    def test_requires_tts_and_result(self):
        with self.assertRaises(ValueError):
            wp.error_spans({**self.PREP, "tts_path": None}, {"recording": b"x"})
        with self.assertRaises(ValueError):
            wp.error_spans(self.PREP, {"error": "녹음 없음"})

    def test_no_blocks_means_nothing_to_mark(self):
        fake = lambda prep, res: {"loc": {"blocks": [], "result": None}, "sounds": []}
        out = wp.error_spans(self.PREP, {"recording": b"x"}, locate=fake)
        self.assertEqual(out["blocks"], 0)

    def test_blocks_become_text_and_sounds(self):
        loc = {"result": {"rate": 0.5}, "blocks": [{"ref_words": ["will"], "hyp_words": ["are"], "tts_span": (0.3, 0.6), "hyp_span": (0.4, 0.8)}]}
        fake = lambda prep, res: {"loc": loc, "sounds": ["s"]}
        out = wp.error_spans(self.PREP, {"recording": b"x"}, locate=fake)
        self.assertEqual(out["blocks"], 1)
        self.assertIn("0.30~0.60", out["text"])           # TTS 쪽 구간이 글에 들어간다
        self.assertEqual(out["sounds"], ["s"])



class AzureHtml(unittest.TestCase):
    RES = {"scores": {"accuracy": 91.0, "fluency": 99.0, "completeness": 100.0, "prosody": None, "pronunciation": 93.3},
           "words": [
               {"word": "want", "accuracy": 100.0, "level": "good", "error_type": "None", "phonemes": []},
               {"word": "explore", "accuracy": 68.0, "level": "fair", "error_type": "None",
                "phonemes": [{"phoneme": "ɛ", "accuracy": 47.0, "heard": "ə"}, {"phoneme": "k", "accuracy": 90.0, "heard": None}]},
               {"word": "the<b>", "accuracy": 40.0, "level": "poor", "error_type": "Mispronunciation", "phonemes": []},
               {"word": "universe", "accuracy": 95.0, "level": "good", "error_type": "Omission", "phonemes": []}]}

    def test_cards_show_scores_and_missing_prosody(self):
        out = wp.azure_cards_html(self.RES)
        self.assertIn("<b>91</b>", out)
        self.assertIn("sl-az-na", out)                           # 운율 점수 없음 → 해당 없음 카드
        self.assertEqual(out.count("sl-az-card"), 5)             # 카드 5개(운율은 점수가 없어도 카드는 있다)

    def test_words_mark_weak_with_underline_and_label(self):
        out = wp.azure_words_html(self.RES)
        self.assertIn("발음", out)                                # Mispronunciation → 이름표
        self.assertIn("빠짐", out)                                # 점수가 높아도 Omission이면 약한 단어
        self.assertEqual(out.count("sl-und"), 2)                  # 밑줄: the<b>(poor), universe(오류 종류)
        self.assertIn("sl-fair", out)                             # 보통(fair)은 연하게
        self.assertNotIn("<b>", out.replace("&lt;b&gt;", ""))     # 단어 글은 escape된다

    def test_phoneme_lines_for_low_words_only(self):
        lines = wp.phoneme_lines(self.RES)
        self.assertEqual(lines, ["explore: ɛ 47 (ə로 들림) · k 90"])   # fair 단어만 음소가 있고, 들린 음소가 다를 때만 표시

    def test_locale_mapping(self):
        self.assertEqual((wp.LOCALES["en"], wp.LOCALES["ja"], wp.LOCALES["fr"]), ("en-US", "ja-JP", "fr-FR"))


if __name__ == "__main__":
    unittest.main()
