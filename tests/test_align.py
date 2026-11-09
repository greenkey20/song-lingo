"""align.py: 틀린 부분을 시간 구간으로 바꾸는 규칙(API·모델 없이)."""
import unittest

import align
import scoring


def words(spec):
    return [{"word": w, "start": s, "end": e, "prob": 0.9} for w, s, e in spec]


TTS = words([("We'll", 0.0, 0.66), ("sing", 0.66, 0.84), ("together", 0.84, 1.3), ("until", 1.3, 1.8),
             ("the", 1.8, 2.06), ("morning", 2.06, 2.34), ("comes.", 2.34, 2.84)])
MINE = words([("We", 0.9, 1.59), ("are", 1.59, 1.75), ("seeing", 1.75, 1.97), ("together", 1.97, 2.63),
              ("until", 2.63, 3.11), ("the", 3.11, 3.37), ("morning", 3.37, 3.69), ("comes.", 3.69, 4.29)])
REF = "We'll sing together until the morning comes."


class Blocks(unittest.TestCase):
    def test_runs_of_errors_become_one_block(self):
        ops = scoring.wer(REF, "We are seeing together until the morning comes.")["ops"]
        # 축약형을 펼치므로 we'll → we will, 틀린 칸은 will·sing ↔ are·seeing 둘이다(we는 일치).
        self.assertEqual(align.error_blocks(ops), [{"ref": (1, 3), "hyp": (1, 3)}])

    def test_no_error_no_block(self):
        self.assertEqual(align.error_blocks(scoring.wer("a b", "a b")["ops"]), [])

    def test_deletion_and_insertion_blocks_have_one_empty_side(self):
        d = align.error_blocks(scoring.wer("a b c", "a c")["ops"])
        i = align.error_blocks(scoring.wer("a c", "a b c")["ops"])
        self.assertEqual(d, [{"ref": (1, 2), "hyp": (1, 1)}])
        self.assertEqual(i, [{"ref": (1, 1), "hyp": (1, 2)}])


class Locate(unittest.TestCase):
    def test_spans_of_the_sing_example(self):
        r = align.locate_errors(REF, MINE, TTS)
        self.assertEqual(len(r["blocks"]), 1)
        b = r["blocks"][0]
        # "We'll"은 we·will 두 토큰이 같은 단어 시간(0.0~0.66)을 나눠 쓴다. 인식 쪽은 일치한 "We"(0.9~1.59)가 빠져 are·seeing만 남는다.
        self.assertEqual(b["tts_span"], (0.0, 0.84))
        self.assertEqual(b["hyp_span"], (1.59, 1.97))
        self.assertEqual(b["ref_words"], ["will", "sing"])
        self.assertEqual(b["hyp_words"], ["are", "seeing"])

    def test_deleted_word_is_a_point_in_my_recording(self):
        mine = words([("We'll", 0.0, 0.6), ("together", 0.6, 1.2)])
        tts = words([("We'll", 0.0, 0.66), ("sing", 0.66, 0.84), ("together", 0.84, 1.3)])
        b = align.locate_errors("We'll sing together", mine, tts)["blocks"][0]
        self.assertEqual(b["tts_span"], (0.66, 0.84))
        self.assertEqual(b["hyp_span"], (0.6, 0.6))

    def test_punctuation_only_word_is_dropped(self):
        self.assertEqual([t["token"] for t in align.word_tokens(words([("Hi", 0, 1), ("...", 1, 2)]))], ["hi"])


class WordSpans(unittest.TestCase):
    def spans(self, ref, mine, tts):
        loc = align.locate_errors(ref, mine, tts)
        return align.word_spans(ref, loc["hyp_tokens"], loc["tts_tokens"])

    def test_one_item_per_reference_token_in_order(self):
        sp = self.spans(REF, MINE, TTS)
        self.assertEqual([x["token"] for x in sp], ["we", "will", "sing", "together", "until", "the", "morning", "comes"])

    def test_matching_words_get_both_spans_and_are_same(self):
        sp = self.spans(REF, MINE, TTS)
        together = sp[3]
        self.assertEqual(together["tts_span"], (0.84, 1.3))
        self.assertEqual(together["hyp_span"], (1.97, 2.63))
        self.assertTrue(together["tts_same"] and together["hyp_same"])

    def test_substitution_has_a_span_but_is_not_same(self):
        sp = self.spans(REF, MINE, TTS)
        sing = sp[2]                                           # sing ↔ seeing
        self.assertEqual(sing["hyp_span"], (1.75, 1.97))
        self.assertFalse(sing["hyp_same"])
        self.assertTrue(sing["tts_same"])

    def test_contraction_tokens_split_the_word_time_evenly(self):
        sp = self.spans(REF, MINE, TTS)
        # TTS의 "We'll"은 0.0~0.66 한 단어 → we(0.0~0.33)·will(0.33~0.66)로 나뉘어 같은 곡선이 두 칸에 중복되지 않는다.
        self.assertEqual(sp[0]["tts_span"], (0.0, 0.33))
        self.assertAlmostEqual(sp[1]["tts_span"][0], 0.33)
        self.assertAlmostEqual(sp[1]["tts_span"][1], 0.66)

    def test_split_only_runs_with_identical_spans(self):
        toks = [{"token": "a", "start": 0.0, "end": 0.4, "prob": 1}, {"token": "b", "start": 0.4, "end": 0.8, "prob": 1}]
        self.assertEqual([(t["start"], t["end"]) for t in align._split_shared_spans(toks)], [(0.0, 0.4), (0.4, 0.8)])

    def test_deletion_has_no_span_on_my_side(self):
        mine = words([("we", 0.1, 0.3), ("sing", 0.3, 0.6)])
        tts = words([("we", 0.0, 0.2), ("will", 0.2, 0.4), ("sing", 0.4, 0.8)])
        loc = align.locate_errors("we will sing", mine, tts)
        sp = align.word_spans("we will sing", loc["hyp_tokens"], loc["tts_tokens"])
        self.assertIsNone(sp[1]["hyp_span"])
        self.assertIsNone(sp[1]["hyp_same"])
        self.assertEqual(sp[1]["tts_span"], (0.2, 0.4))

    def test_empty_reference_gives_empty_list(self):
        self.assertEqual(align.word_spans("", [], []), [])


if __name__ == "__main__":
    unittest.main()
