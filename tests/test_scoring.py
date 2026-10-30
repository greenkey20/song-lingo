"""scoring.py 단위 테스트. 실행: python -m unittest discover -s tests -v
손계산 5유형(일치 / 치환만 / 삭제만 / 삽입으로 WER>1 / 정규화 필요) + 경계 사례."""
import os
import random
import sys
import unicodedata
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scoring  # noqa: E402


class HandCalculated(unittest.TestCase):
    def test_1_identical(self):
        r = scoring.wer("the cat sat", "the cat sat")
        self.assertEqual((r["S"], r["D"], r["I"], r["rate"]), (0, 0, 0, 0.0))

    def test_2_substitution_only(self):
        r = scoring.wer("the cat sat", "the cat sit")
        self.assertEqual((r["S"], r["D"], r["I"], r["N"]), (1, 0, 0, 3))
        self.assertAlmostEqual(r["rate"], 1 / 3)

    def test_3_deletion_only(self):
        r = scoring.wer("i love you", "i you")
        self.assertEqual((r["S"], r["D"], r["I"]), (0, 1, 0))
        self.assertAlmostEqual(r["rate"], 1 / 3)

    def test_4_insertions_wer_over_one(self):
        r = scoring.wer("hello", "hello hello hello")
        self.assertEqual((r["S"], r["D"], r["I"], r["N"]), (0, 0, 2, 1))
        self.assertEqual(r["rate"], 2.0)

    def test_5_normalization_needed(self):
        self.assertEqual(scoring.wer("Hello, World!", "hello world")["rate"], 0.0)
        r = scoring.wer("the cat sat on the mat", "the cat sit on mat")
        self.assertEqual((r["S"], r["D"], r["I"], r["N"]), (1, 1, 0, 6))


class CerAndLanguages(unittest.TestCase):
    def test_cer_english(self):
        r = scoring.cer("the cat sat on the mat", "the cat sit on mat")
        self.assertEqual((r["distance"], r["N"]), (4, 17))

    def test_cer_korean_particle(self):
        r = scoring.cer("오늘 날씨가 좋아요", "오늘 날씨 좋아요", lang="ko")
        self.assertEqual((r["distance"], r["N"]), (1, 8))

    def test_japanese_punctuation_removed(self):
        r = scoring.cer("今日は天気がいいです。", "今日は天気がいいです", lang="ja")
        self.assertEqual(r["rate"], 0.0)

    def test_nfc_nfd_same(self):
        nfc = "café au lait"
        nfd = unicodedata.normalize("NFD", nfc)
        self.assertNotEqual(nfc, nfd)
        self.assertEqual(scoring.wer(nfc, nfd, lang="fr")["rate"], 0.0)

    def test_french_accent_policy(self):
        self.assertGreater(scoring.wer("Où est la gare ?", "ou est la gare", lang="fr")["rate"], 0)
        self.assertEqual(scoring.wer("Où est la gare ?", "ou est la gare", lang="fr",
                                     strip_accents=True)["rate"], 0.0)


class Boundaries(unittest.TestCase):
    def test_empty_reference_raises(self):
        with self.assertRaises(ValueError):
            scoring.wer("", "anything")

    def test_empty_hypothesis_is_all_deletions(self):
        r = scoring.wer("one two", "")
        self.assertEqual((r["S"], r["D"], r["I"], r["rate"]), (0, 2, 0, 1.0))

    def test_sum_equals_distance_random(self):
        random.seed(0)
        for _ in range(500):
            a = [random.choice("abc") for _ in range(random.randint(1, 8))]
            b = [random.choice("abc") for _ in range(random.randint(0, 8))]
            r = scoring.score(a, b)          # score() 안에서도 S+D+I == distance 를 검산함
            self.assertEqual(r["S"] + r["D"] + r["I"], r["distance"])

    def test_format_diff(self):
        r = scoring.wer("the cat sat on the mat", "the cat sit on mat")
        self.assertEqual(scoring.format_diff(r["ops"]), "the cat [sat→sit] on [-the-] mat")


if __name__ == "__main__":
    unittest.main()
