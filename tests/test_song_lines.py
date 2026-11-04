"""song_lines.py 단위 테스트(이슈 #31). 합성 구간만 쓴다(가사 없음: 의미 없는 단어 w1, w2 …). 실행: python -m unittest tests.test_song_lines -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import song_lines  # noqa: E402


def words(start, n, dur=0.4, gap=0.1, first=1):
    """n개의 단어(w1, w2 …)를 start부터 dur초씩, 사이 쉼 gap초로 만든다."""
    out, t = [], start
    for k in range(n):
        out.append({"word": f"w{first + k}", "start": round(t, 3), "end": round(t + dur, 3), "prob": 0.9})
        t += dur + gap
    return out


def seg(start, n, dur=0.4, gap=0.1, first=1, with_words=True, **kw):
    ws = words(start, n, dur, gap, first)
    s = {"start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(w["word"] for w in ws),
         "avg_logprob": -0.3, "no_speech_prob": 0.01, "compression_ratio": 1.2, "words": ws if with_words else None}
    s.update(kw)
    return s


class Basic(unittest.TestCase):
    def test_empty_and_blank_text_segments(self):
        self.assertEqual(song_lines.split_into_lines([]), [])
        self.assertEqual(song_lines.split_into_lines([dict(seg(0, 4), text="  ")]), [])

    def test_normal_segment_is_one_line_with_same_times(self):
        lines = song_lines.split_into_lines([seg(1.0, 6)])
        self.assertEqual(len(lines), 1)
        self.assertEqual((lines[0]["no"], lines[0]["source"], lines[0]["n_words"]), (1, "segment", 6))
        self.assertEqual(lines[0]["start"], 1.0)
        self.assertFalse(lines[0]["low_confidence"] or lines[0]["too_long"])

    def test_lines_are_numbered_in_order_and_do_not_overlap(self):
        lines = song_lines.split_into_lines([seg(0, 6), seg(5, 6, first=7), seg(10, 6, first=13)])
        self.assertEqual([l["no"] for l in lines], [1, 2, 3])
        for a, b in zip(lines, lines[1:]):
            self.assertLessEqual(a["end"], b["start"])


class Split(unittest.TestCase):
    def test_long_segment_splits_at_the_biggest_pause(self):
        a, b = words(0, 8), words(8.0, 8, first=9)       # 앞 8단어 + 3초 쉼 + 뒤 8단어(총 16단어, 약 11초)
        long_seg = {"start": a[0]["start"], "end": b[-1]["end"], "text": " ".join(w["word"] for w in a + b),
                    "avg_logprob": -0.3, "no_speech_prob": 0.01, "compression_ratio": 1.2, "words": a + b}
        lines = song_lines.split_into_lines([long_seg], max_sec=7.0, max_words=16, min_sec=1.0, min_words=2)
        self.assertEqual(len(lines), 2)
        self.assertEqual([l["source"] for l in lines], ["split", "split"])
        self.assertEqual(lines[0]["text"].split()[-1], "w8")      # 큰 쉼 바로 앞에서 끊김
        self.assertEqual(lines[1]["text"].split()[0], "w9")
        self.assertEqual(" ".join(l["text"] for l in lines), long_seg["text"])    # 단어를 잃거나 순서가 바뀌지 않음

    def test_split_repeats_until_every_piece_is_short_enough(self):
        lines = song_lines.split_into_lines([seg(0, 30, dur=0.4, gap=0.1)], max_sec=7.0, max_words=16, min_sec=1.0, min_words=2)
        self.assertGreaterEqual(len(lines), 2)
        for l in lines:
            self.assertFalse(l["too_long"])
            self.assertLessEqual(l["end"] - l["start"], 7.0)
        self.assertEqual(sum(l["n_words"] for l in lines), 30)

    def test_long_segment_without_word_times_is_kept_and_flagged(self):
        lines = song_lines.split_into_lines([seg(0, 30, with_words=False)], max_sec=7.0, max_words=16)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0]["too_long"])


class Merge(unittest.TestCase):
    def test_short_neighbors_with_small_gap_are_merged(self):
        s1, s2 = seg(0, 1), seg(1.0, 1, first=2)           # 단어 하나씩, 쉼 약 0.6초
        lines = song_lines.split_into_lines([s1, s2], min_sec=1.2, min_words=3, max_merge_gap=1.5)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["source"], "merged")
        self.assertEqual(lines[0]["text"], "w1 w2")
        self.assertEqual(lines[0]["segment_ids"], [0, 1])

    def test_short_line_far_from_neighbors_stays(self):
        lines = song_lines.split_into_lines([seg(0, 6), seg(20, 1, first=7)], min_sec=1.2, min_words=3, max_merge_gap=1.5)
        self.assertEqual(len(lines), 2)

    def test_merge_prefers_the_closer_neighbor(self):
        a, mid, c = seg(0, 6), seg(5.0, 1, first=7), seg(9.0, 6, first=8)
        lines = song_lines.split_into_lines([a, mid, c], min_sec=1.2, min_words=3, max_merge_gap=3.0)
        self.assertEqual(len(lines), 2)
        self.assertIn("w7", lines[0]["text"].split())       # 가까운 앞 줄과 합쳐짐(앞 줄 끝~시작 쉼이 더 짧음)

    def test_merge_is_skipped_when_result_would_be_too_long(self):
        lines = song_lines.split_into_lines([seg(0, 16), seg(8.0, 1, first=17)], max_words=16, min_sec=1.2, min_words=3, max_merge_gap=3.0)
        self.assertEqual(len(lines), 2)


class LowConfidence(unittest.TestCase):
    def test_flags_repetition_and_low_logprob(self):
        for kw in ({"compression_ratio": 2.0}, {"avg_logprob": -0.7}):
            lines = song_lines.split_into_lines([seg(0, 6, **kw)])
            self.assertTrue(lines[0]["low_confidence"], kw)

    def test_no_speech_prob_is_not_used(self):
        # 완벽히 인식된 구간에서도 높게 나와 좋은 클립과 나쁜 클립을 가르지 못해서 기준에서 뺐다(작업 기록 문서 C2)
        self.assertFalse(song_lines.split_into_lines([seg(0, 6, no_speech_prob=0.9)])[0]["low_confidence"])

    def test_normal_segment_is_not_flagged(self):
        self.assertFalse(song_lines.split_into_lines([seg(0, 6)])[0]["low_confidence"])

    def test_threshold_values_are_the_observed_ones(self):
        self.assertEqual((song_lines.LOW_LOGPROB, song_lines.LOW_COMPRESSION), (-0.6, 1.8))


if __name__ == "__main__":
    unittest.main()
