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


class Unify(unittest.TestCase):
    """영어 표기 통일 규칙(이슈 #3, 검토 문서 13.4): 정답과 인식 결과 양쪽에 같은 규칙을 적용한다."""

    def test_contractions_expand(self):
        n = scoring.normalize
        self.assertEqual(n("We're, I'm, they've, you'll."), "we are i am they have you will")
        self.assertEqual(n("Don't isn't wouldn't"), "do not is not would not")
        self.assertEqual(n("I can't, he cannot, they won't"), "i can not he can not they will not")
        self.assertEqual(n("I'm gonna wanna gotta"), "i am going to want to got to")

    def test_ambiguous_contractions_are_kept(self):
        # 's는 is/has/소유격, 'd는 would/had라서 펼치지 않는다.
        self.assertEqual(scoring.normalize("It's Tom's; he'd go"), "it's tom's he'd go")

    def test_number_words_become_digits(self):
        n = scoring.normalize
        self.assertEqual(n("zero one nineteen twenty forty ninety"), "0 1 19 20 40 90")
        self.assertEqual(n("Twenty-one and ninety-nine"), "21 and 99")     # 하이픈 숫자는 구두점 제거 전에 처리
        self.assertEqual(n("20 stars"), "20 stars")                        # 이미 숫자면 그대로

    def test_spaced_compound_is_a_known_limit(self):
        self.assertEqual(scoring.normalize("twenty one"), "20 1")          # 단어 사이는 합치지 않는다(알려진 한계)

    def test_unify_false_is_strict(self):
        n = lambda t: scoring.normalize(t, unify=False)
        self.assertEqual(n("We're twenty"), "we're twenty")
        self.assertEqual(n("twenty-one"), "twentyone")                     # 예전 동작 그대로

    def test_other_languages_untouched(self):
        self.assertEqual(scoring.normalize("L'amour n'est pas", "fr"), "l'amour n'est pas")
        self.assertEqual(scoring.normalize("you're", "ja"), "you're")

    def test_sentence_7_example(self):
        # 11-03 녹음 30건에서 문장 7이 3번 모두 이렇게 인식됐다(검토 문서 13.4).
        ref, hyp = "We're going to count twenty stars above the quiet valley.", "We are going to count 20 stars above the quiet valley."
        self.assertEqual(scoring.wer(ref, hyp)["rate"], 0.0)
        strict = scoring.wer(ref, hyp, unify=False)
        self.assertEqual((strict["S"], strict["D"], strict["I"], strict["N"]), (2, 0, 1, 10))   # we're→we, +are, twenty→20 = 0.3
        self.assertAlmostEqual(strict["rate"], 0.3)

    def test_same_rule_on_both_sides_never_hurts_identical_text(self):
        for t in ["I can't stop", "twenty-one stars", "It's Tom's", "Gonna go"]:
            self.assertEqual(scoring.wer(t, t)["rate"], 0.0)


class TieBreak(unittest.TestCase):
    """거리가 같은 경로가 여러 개일 때 비슷한 토큰끼리 짝지어 표시한다(오류율은 그대로)."""

    def diff(self, ref, hyp, **kw):
        return scoring.format_diff(scoring.wer(ref, hyp, **kw)["ops"])

    def test_similar_words_are_paired(self):
        self.assertEqual(self.diff("I want to explore the universe", "i want to explor universe"),
                         "i want to [explore→explor] [-the-] universe")
        # 짝짓기 규칙 자체는 표기 통일(#3)과 무관하므로 unify=False(엄격)로 확인한다.
        self.assertEqual(self.diff("I want to explore the universe", "I wanna explore the universe", unify=False),
                         "i [want→wanna] [-to-] explore the universe")

    def test_contraction_pairs_with_first_word(self):
        self.assertEqual(self.diff("We'll sing together", "We are seeing together", unify=False),
                         "[we'll→we] [+are+] [sing→seeing] together")

    def test_unified_contraction_is_two_substitutions(self):
        # 같은 예시를 기본 규칙(축약형 펼침)으로 보면 we'll → we will이 되어 we는 일치로 남는다.
        self.assertEqual(self.diff("We'll sing together", "We are seeing together"),
                         "we [will→are] [sing→seeing] together")

    def test_rate_and_reconstruction_unchanged(self):
        rng = random.Random(7)
        vocab = "a b c the then want wanna to explore explor".split()
        for _ in range(300):
            ref = [rng.choice(vocab) for _ in range(rng.randint(1, 7))]
            hyp = [rng.choice(vocab) for _ in range(rng.randint(0, 7))]
            r = scoring.score(ref, hyp)
            self.assertEqual([o[1] for o in r["ops"] if o[1] is not None], ref)
            self.assertEqual([o[2] for o in r["ops"] if o[2] is not None], hyp)
            self.assertEqual(r["distance"], scoring.edit_matrix(ref, hyp)[-1][-1])

class LanguageRules(unittest.TestCase):
    """이슈 #50: 언어별 정규화·주 지표."""

    def test_no_space_languages_use_cer_as_main(self):
        for lang in ("ja", "zh"):
            r = scoring.evaluate("今日は 晴れ", "今日は晴れ", lang)
            self.assertEqual(r["main"], r["cer"])
            self.assertEqual(r["cer"]["rate"], 0.0)                      # 공백 차이는 오류가 아님
        self.assertEqual(scoring.evaluate("a b", "a b", "en")["main"]["N"], 2)   # 영어는 단어 기준

    def test_lowercase_for_cased_scripts_only(self):
        self.assertEqual(scoring.normalize("¿Dónde ESTÁ?", "es"), "dónde está")    # 스페인어·독일어·스웨덴어 등도 소문자화
        self.assertEqual(scoring.normalize("ЗДРАВСТВУЙТЕ", "ru"), "здравствуйте")
        self.assertEqual(scoring.normalize("안녕 Hello", "ko"), "안녕 hello")        # 한·일·중 글자는 그대로, 섞인 영어는 소문자
        self.assertEqual(scoring.normalize("まだ終わらない Tonight", "ja"), "まだ終わらないtonight")   # 일본어 줄에 섞인 영어 단어도 소문자로 맞춘다

    def test_french_accents_kept_by_default(self):
        self.assertNotEqual(scoring.wer("été", "ete", "fr")["rate"], 0.0)          # 엄격(기본): é와 e는 다른 글자
        self.assertEqual(scoring.wer("été", "ete", "fr", strip_accents=True)["rate"], 0.0)



class JapaneseKana(unittest.TestCase):
    def test_katakana_is_folded_to_hiragana(self):
        self.assertEqual(scoring.normalize("コーヒー", "ja"), "こーひー")
        self.assertEqual(scoring.cer("こーひー", "コーヒー", "ja")["rate"], 0.0)       # 같은 소리를 다른 문자로 적은 것은 오류가 아님
        self.assertEqual(scoring.normalize("コーヒー", "ja", fold_kana=False), "コーヒー")
        self.assertEqual(scoring.normalize("コーヒー", "en"), "コーヒー")               # 일본어에서만

    def test_wer_of_japanese_is_one_token(self):
        r = scoring.wer("朝の光が部屋を満たしている", "朝の光が部屋を満たす", "ja")
        self.assertEqual(r["N"], 1)                                                    # 공백이 없어 문장 전체가 단어 1개 → WER은 0 또는 1뿐
        self.assertEqual(r["rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
