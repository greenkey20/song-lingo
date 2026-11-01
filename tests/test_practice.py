"""practice.py·report.py 단위 테스트. 실행: python -m unittest tests.test_practice -v
OpenAI API와 Whisper를 부르지 않고, tts·stt를 가짜 함수로 바꿔서 '순서와 결과 모양'만 확인한다."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import practice  # noqa: E402
import report  # noqa: E402
import scoring  # noqa: E402
import tts  # noqa: E402

SENTENCES = [{"id": "1", "lang": "en", "sentence": "I want to explore the universe.",
              "meaning_ko": "나는 우주를 탐험하고 싶어.", "source": "직접 작성", "license": "직접 작성(본인)"}]


def write_tone(path, seconds=2.0, amp=0.3, sr=16000):
    x = amp * np.sin(2 * np.pi * 300 * np.arange(int(sr * seconds)) / sr)
    wavfile.write(path, sr, np.round(x * 32767).astype(np.int16))


class Evaluate(unittest.TestCase):
    def test_main_is_wer_except_japanese(self):
        en = scoring.evaluate("the cat sat", "the cat sit")
        self.assertIs(en["main"], en["wer"])
        self.assertAlmostEqual(en["wer"]["rate"], 1 / 3)
        ja = scoring.evaluate("今日は天気", "今日は天", lang="ja")
        self.assertIs(ja["main"], ja["cer"])


class Flow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def fake_tts(self, new):
        """tts_wav를 가짜로: 파일을 만들어 돌려주고, new=True면 호출 횟수(tts.calls)를 1 올린다."""
        def fake(text, path):
            write_tone(self.dir / "tts.wav")
            if new:
                tts.calls += 1
            return self.dir / "tts.wav"
        return mock.patch("tts.tts_wav", side_effect=fake)

    def test_prepare_reports_cache_or_new(self):
        with self.fake_tts(new=False):
            self.assertFalse(practice.prepare(1, SENTENCES)["tts_new"])
        with self.fake_tts(new=True):
            self.assertTrue(practice.prepare(1, SENTENCES)["tts_new"])

    def test_prepare_custom_sentence_and_empty(self):
        with self.fake_tts(new=True):
            custom = practice.prepare("Where the river meets the sea.", SENTENCES)
        self.assertEqual(custom["id"], "직접 입력")
        empty = practice.prepare("   ", SENTENCES)
        self.assertEqual(empty["error"], "문장이 비어 있습니다.")

    def test_read_runs_quality_then_stt_then_score(self):
        rec = self.dir / "rec.wav"
        write_tone(rec)
        with self.fake_tts(new=False):
            prep = practice.prepare(1, SENTENCES)
        with mock.patch("stt.recognize", return_value=("I want explore the universe.", 1.2)) as rec_mock:
            res = practice.read(prep, rec)
        rec_mock.assert_called_once()
        self.assertIsNone(res["error"])
        self.assertTrue(res["quality"]["ok"])                    # 정상 크기의 소리라 경고 없음
        self.assertEqual((res["score"]["wer"]["S"], res["score"]["wer"]["D"]), (0, 1))   # "to"가 빠짐
        text = report.result(prep, res)
        self.assertIn("녹음 상태: 이상 없음", text)
        self.assertIn("[-to-]", text)
        self.assertIn("발음 점수가 아니라", text)

    def test_read_warns_but_still_recognizes_quiet_recording(self):
        rec = self.dir / "quiet.wav"
        write_tone(rec, amp=0.001)
        with self.fake_tts(new=False):
            prep = practice.prepare(1, SENTENCES)
        with mock.patch("stt.recognize", return_value=("hello", 1.0)):
            res = practice.read(prep, rec)
        self.assertFalse(res["quality"]["ok"])                   # 경고는 안내일 뿐
        self.assertIsNotNone(res["score"])                       # 인식과 채점은 그대로 진행
        self.assertIn("너무 작습니다", report.result(prep, res))

    def test_read_without_recording_returns_error(self):
        with self.fake_tts(new=False):
            prep = practice.prepare(1, SENTENCES)
        res = practice.read(prep, self.dir / "none.wav")
        self.assertIn("녹음이 없습니다", res["error"])
        self.assertEqual(report.result(prep, res), res["error"])

    def test_dictation_scores_and_reveals_meaning(self):
        with self.fake_tts(new=False):
            prep = practice.prepare(1, SENTENCES)
        res = practice.dictation(prep, "I want to explor univers")
        self.assertEqual((res["score"]["wer"]["S"], res["score"]["wer"]["D"]), (2, 1))
        text = report.result(prep, res)
        self.assertIn("내가 적은 글", text)
        self.assertIn("뜻  : 나는 우주를 탐험하고 싶어.", text)
        self.assertEqual(practice.dictation(prep, "  ")["error"], "입력이 비어 있어 채점하지 않습니다.")


class Header(unittest.TestCase):
    PREP = {"id": "3", "text": "We'll sing.", "meaning_ko": "노래할 거야.", "tts_new": False}

    def test_read_shows_sentence_dictation_hides_it(self):
        self.assertIn("문장: We'll sing.", report.header(self.PREP, "read"))
        self.assertNotIn("We'll sing.", report.header(self.PREP, "dictation"))

    def test_custom_sentence_warning_and_tts_status(self):
        prep = dict(self.PREP, id="직접 입력", tts_new=True)
        self.assertIn("상업 노래의 가사는 넣지 않습니다", report.header(prep, "dictation"))
        self.assertIn("새로 만듦(API 1회)", report.tts_status(prep))
        self.assertIn("캐시 사용(API 0회)", report.tts_status(self.PREP))


if __name__ == "__main__":
    unittest.main()
