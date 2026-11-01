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
        self.assertEqual(align.error_blocks(ops), [{"ref": (0, 2), "hyp": (0, 3)}])

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
        self.assertEqual(b["tts_span"], (0.0, 0.84))
        self.assertEqual(b["hyp_span"], (0.9, 1.97))
        self.assertEqual(b["ref_words"], ["we'll", "sing"])
        self.assertEqual(b["hyp_words"], ["we", "are", "seeing"])

    def test_deleted_word_is_a_point_in_my_recording(self):
        mine = words([("We'll", 0.0, 0.6), ("together", 0.6, 1.2)])
        tts = words([("We'll", 0.0, 0.66), ("sing", 0.66, 0.84), ("together", 0.84, 1.3)])
        b = align.locate_errors("We'll sing together", mine, tts)["blocks"][0]
        self.assertEqual(b["tts_span"], (0.66, 0.84))
        self.assertEqual(b["hyp_span"], (0.6, 0.6))

    def test_punctuation_only_word_is_dropped(self):
        self.assertEqual([t["token"] for t in align.word_tokens(words([("Hi", 0, 1), ("...", 1, 2)]))], ["hi"])


if __name__ == "__main__":
    unittest.main()
