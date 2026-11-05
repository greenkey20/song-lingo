"""japanese.py 단위 테스트(pykakasi가 없으면 건너뜀)."""
import unittest

import japanese


@unittest.skipUnless(japanese.available(), "pykakasi 없음")
class Reading(unittest.TestCase):
    def test_kanji_and_katakana_become_hiragana(self):
        self.assertEqual(japanese.reading("朝の光が部屋を満たしている。"), "あさのひかりがへやをみたしている。")
        self.assertEqual(japanese.reading("コーヒー"), "こーひー")

    def test_latin_words_are_kept(self):
        self.assertEqual(japanese.reading("甘い Coffee 苦い Memory"), "あまい Coffee にがい Memory")

    def test_romaji_for_every_script(self):
        self.assertEqual(japanese.romaji("コーヒー"), "koohii")                       # 가타카나
        self.assertEqual(japanese.romaji("あさ"), "asa")                              # 히라가나
        self.assertIn("asa no hikari", japanese.romaji("朝の光"))                     # 한자(읽기를 거쳐 로마자)
        self.assertEqual(japanese.readings("朝")[0], "あさ")

    def test_same_sound_different_script_matches_after_reading(self):
        import scoring
        a, b = japanese.reading("コーヒーをのむ"), japanese.reading("こーひーを飲む")
        self.assertEqual(scoring.cer(a, b, "ja")["rate"], 0.0)                       # 표기가 달라도 읽기가 같으면 오류 0

    def test_empty(self):
        self.assertEqual(japanese.reading(""), "")
        self.assertEqual(japanese.romaji(""), "")


class WithoutLibrary(unittest.TestCase):
    def test_functions_degrade_gracefully(self):
        orig = japanese.available
        japanese.available = lambda: False
        try:
            self.assertEqual(japanese.reading("朝"), "朝")                            # 변환 없이 원문
            self.assertEqual(japanese.romaji("朝"), "")
        finally:
            japanese.available = orig


if __name__ == "__main__":
    unittest.main()
