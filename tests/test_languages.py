"""languages.py 단위 테스트(소리·모델·네트워크 없음)."""
import unittest

import languages as L


class Tables(unittest.TestCase):
    def test_names_and_locales(self):
        self.assertEqual((L.name("ja"), L.name("xx")), ("일본어", "xx"))
        self.assertEqual((L.azure_locale("fr"), L.azure_locale("xx"), L.azure_locale("xx", "ko-KR")), ("fr-FR", "en-US", "ko-KR"))

    def test_spaces(self):
        self.assertFalse(L.uses_spaces("ja"))
        self.assertFalse(L.uses_spaces("zh"))
        self.assertTrue(L.uses_spaces("en") and L.uses_spaces("ko") and L.uses_spaces("fr"))

    def test_common_list_has_the_three_target_languages_first_in_use(self):
        for c in ("en", "ja", "fr"):
            self.assertIn(c, L.COMMON)


class TextDetect(unittest.TestCase):
    def test_kana_is_japanese(self):
        r = L.detect_text_language("君が好き")                       # 한자 + 히라가나
        self.assertEqual((r["languages"], r["primary"], r["assumed"]), (["ja"], "ja", False))

    def test_latin_is_assumed_english(self):
        r = L.detect_text_language("I wanna stay with you")
        self.assertEqual((r["languages"], r["primary"], r["assumed"]), (["en"], "en", True))
        self.assertTrue(L.detect_text_language("Où est la gare ?")["assumed"])      # 프랑스어도 라틴 문자라 영어로 "가정"만 한다

    def test_mixed_japanese_and_english(self):
        r = L.detect_text_language("まだ終わらない tonight")
        self.assertEqual((r["languages"], r["primary"], r["assumed"]), (["ja", "en"], "ja", False))

    def test_primary_is_the_language_with_more_letters(self):
        r = L.detect_text_language("I wanna stay with you まだ")           # 영어가 대부분인 줄은 가나 두 글자 때문에 일본어가 되지 않는다
        self.assertEqual((r["primary"], r["languages"]), ("en", ["en", "ja"]))
        r = L.detect_text_language("今夜は Moonlight の下で踊ろう")        # 가나·한자가 영어 단어보다 많거나 비슷하면 일본어
        self.assertEqual(r["primary"], "ja")

    def test_equal_letters_prefer_non_latin(self):
        self.assertEqual(L.detect_text_language("ab あい")["primary"], "ja")        # 일본어 2글자 = 라틴 2글자 → 동률이면 라틴이 아닌 쪽
        self.assertEqual(L.detect_text_language("まだ tonight")["primary"], "en")   # 라틴 7글자가 가나 2글자보다 많으면 영어

    def test_lines_are_detected_separately(self):
        got = L.detect_lines_language(["君が好き", "I wanna stay with you", "Où est la gare ?"])
        self.assertEqual([g["primary"] for g in got], ["ja", "en", "en"])
        self.assertEqual([g["assumed"] for g in got], [False, True, True])

    def test_hangul_cyrillic(self):
        self.assertEqual(L.detect_text_language("안녕하세요 hello")["primary"], "ko")
        self.assertEqual(L.detect_text_language("Привет")["languages"], ["ru"])

    def test_han_only_is_unknown(self):
        r = L.detect_text_language("今日")
        self.assertEqual((r["languages"], r["primary"]), ([], None))   # 일본어인지 중국어인지 구분 불가

    def test_empty_and_symbols(self):
        self.assertEqual(L.detect_text_language("")["primary"], None)
        self.assertEqual(L.detect_text_language("123 !?")["languages"], [])


class ProbsSuggestion(unittest.TestCase):
    PROBS = [("br", 0.40), ("fr", 0.25), ("en", 0.05), ("ja", 0.01), ("cy", 0.20)]

    def test_restricted_to_candidates(self):
        ranked = L.suggest_from_probs(self.PROBS, candidates=("en", "ja", "fr"))
        self.assertEqual(ranked[0][0], "fr")                           # br(브르타뉴어)가 1등이어도 후보 밖이라 제외
        self.assertAlmostEqual(sum(p for _c, p in ranked), 1.0)        # 후보 안의 비율이라 합이 1
        self.assertEqual([c for c, _p in ranked], ["fr", "en", "ja"])

    def test_no_candidate_mass(self):
        self.assertEqual(L.suggest_from_probs([("br", 1.0)], candidates=("en",)), [])

    def test_mixed_hint(self):
        self.assertEqual(L.mixed_hint([("ja", 0.6), ("en", 0.35), ("fr", 0.05)]), "en")
        self.assertIsNone(L.mixed_hint([("ja", 0.9), ("en", 0.08)]))
        self.assertIsNone(L.mixed_hint([("ja", 1.0)]))


class SttOptions(unittest.TestCase):
    def test_yes_and_single_no_fix_the_language(self):
        for ans in ("yes", "no"):
            o = L.stt_options(ans, ["ja"])
            self.assertEqual((o["language"], o["multilingual"], o["primary"]), ("ja", False, "ja"))

    def test_unknown_or_empty_is_auto(self):
        for o in (L.stt_options("unknown", ["ja"]), L.stt_options("no", [])):
            self.assertEqual((o["language"], o["multilingual"], o["languages"]), (None, False, []))

    def test_multiple_languages_primary_or_auto(self):
        p = L.stt_options("no", ["ja", "en"])
        self.assertEqual((p["language"], p["multilingual"], p["languages"]), ("ja", False, ["ja", "en"]))
        a = L.stt_options("no", ["ja", "en"], mixed="auto")
        self.assertEqual((a["language"], a["multilingual"], a["primary"]), (None, True, "ja"))

    def test_duplicates_removed_and_bad_answer(self):
        self.assertEqual(L.stt_options("no", ["ja", "ja"])["languages"], ["ja"])
        with self.assertRaises(ValueError):
            L.stt_options("maybe", ["ja"])


class LatinDetect(unittest.TestCase):
    """이슈 #50: 라틴 문자 줄의 언어를 낱말·글자 점수로 제안(직접 만든 가벼운 규칙)."""

    def test_french_example_sentences(self):
        for t in ("Je voudrais un café, s'il vous plaît.", "Où est la gare, s'il vous plaît ?",
                  "Nous allons chanter ensemble ce soir.", "Il fait beau aujourd'hui, allons nous promener."):
            self.assertEqual(L.detect_latin_language(t)["top"], "fr", t)

    def test_english_spanish_german_swedish(self):
        self.assertEqual(L.detect_latin_language("I want to explore the universe.")["top"], "en")
        self.assertEqual(L.detect_latin_language("¿Dónde está la biblioteca?")["top"], "es")
        self.assertEqual(L.detect_latin_language("Ich habe keine Zeit und du bist nicht hier.")["top"], "de")
        self.assertEqual(L.detect_latin_language("Jag är inte hemma och du har det.")["top"], "sv")

    def test_short_text_falls_back_to_english_with_low_confidence(self):
        r = L.detect_latin_language("tonight")
        self.assertEqual((r["top"], r["confidence"]), ("en", "low"))

    def test_confidence_high_needs_clear_margin(self):
        self.assertEqual(L.detect_latin_language("Où est la gare, s'il vous plaît ?")["confidence"], "high")

    def test_suggest_line_language_combines_script_and_words(self):
        self.assertEqual(L.suggest_line_language("君が好き")["primary"], "ja")
        self.assertEqual(L.suggest_line_language("君が好き")["source"], "script")
        fr = L.suggest_line_language("Nous allons chanter ensemble ce soir.")
        self.assertEqual((fr["primary"], fr["source"]), ("fr", "words"))
        mixed = L.suggest_line_language("甘い Coffee 苦い Memory")
        self.assertEqual((mixed["primary"], mixed["confidence"]), ("ja", "medium"))     # 일본어가 주, 영어도 섞임 → 보통
        self.assertEqual(L.suggest_line_language("今日")["confidence"], "none")
        self.assertIsNone(L.suggest_line_language("123")["primary"])


if __name__ == "__main__":
    unittest.main()
