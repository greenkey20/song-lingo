"""quality.py 단위 테스트. 실행: python -m unittest tests.test_quality -v
합성 신호만 쓴다. 경고 기준은 '초안'이라, 기준값을 바꾸면 이 테스트의 숫자도 함께 확인한다."""
import os
import sys
import tempfile
import unittest

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import quality  # noqa: E402

SR = 16000


def tone(freq, seconds, amp):
    return (amp * np.sin(2 * np.pi * freq * np.arange(int(SR * seconds)) / SR)).astype(np.float32)


def speech_like():
    """말하는 구간(1.5초)과 무음(1.5초)이 섞인 3초: 정상 녹음 흉내."""
    return np.concatenate([np.zeros(SR // 2, np.float32), tone(300, 1.5, 0.3), np.zeros(SR, np.float32)])


def has(result, word):
    return any(word in w for w in result["warnings"])


class Cases(unittest.TestCase):
    def test_normal_recording_has_no_warning(self):
        r = quality.analyze(speech_like(), SR)
        self.assertTrue(r["ok"], r["warnings"])
        self.assertAlmostEqual(r["metrics"]["silent_ratio"], 0.5, delta=0.1)

    def test_too_quiet(self):
        r = quality.analyze(speech_like() * 0.005, SR)       # 0.3 → 0.0015: 최대 진폭 0.05 미만
        self.assertTrue(has(r, "너무 작습니다"))

    def test_silence_only_is_too_quiet(self):
        r = quality.analyze(np.zeros(SR * 2, np.float32), SR)
        self.assertFalse(r["ok"])
        self.assertTrue(has(r, "너무 작습니다"))

    def test_clipping(self):
        r = quality.analyze(np.clip(speech_like() * 6, -1, 1), SR)   # 0.3 × 6 = 1.8 → ±1로 잘림
        self.assertTrue(has(r, "잘렸을 수"))
        self.assertGreater(r["metrics"]["clip_ratio"], quality.MAX_CLIP_RATIO)

    def test_mostly_silent(self):
        x = np.concatenate([tone(300, 0.2, 0.5), np.zeros(SR * 5, np.float32)])   # 말소리 0.2초, 나머지 5초 무음
        r = quality.analyze(x, SR)
        self.assertTrue(has(r, "대부분이 무음"))
        self.assertFalse(has(r, "너무 작습니다"))             # 말하는 부분의 크기는 충분하다

    def test_too_short_and_empty(self):
        self.assertTrue(has(quality.analyze(tone(300, 0.2, 0.3), SR), "너무 짧습니다"))
        r = quality.analyze(np.zeros((0, 1), np.float32), SR)  # 빈 파형: 오류 없이 경고만
        self.assertFalse(r["ok"])
        self.assertTrue(has(r, "너무 짧습니다"))

    def test_clipping_in_one_stereo_channel_is_counted(self):
        left, right = np.clip(speech_like() * 6, -1, 1), speech_like()
        r = quality.analyze(np.stack([left, right], axis=1), SR)
        self.assertGreater(r["metrics"]["clip_ratio"], 0)


class Info(unittest.TestCase):
    def test_leading_silence(self):
        x = np.concatenate([np.zeros(SR, np.float32), tone(300, 1.5, 0.3)])
        self.assertAlmostEqual(quality.analyze(x, SR)["info"]["leading_silence_sec"], 1.0, delta=0.1)

    def test_low_frequency_ratio(self):
        low = quality.analyze(tone(50, 2, 0.3), SR)["info"]["low_freq_ratio"]
        mid = quality.analyze(tone(1000, 2, 0.3), SR)["info"]["low_freq_ratio"]
        self.assertGreater(low, 0.9)
        self.assertLess(mid, 0.01)

    def test_report_text(self):
        good = quality.format_report(quality.analyze(speech_like(), SR))
        bad = quality.format_report(quality.analyze(speech_like() * 0.005, SR))
        self.assertIn("이상 없음", good)
        self.assertIn("⚠", bad)


class FromFile(unittest.TestCase):
    def test_resampling_ringing_is_not_reported_as_clipping(self):
        """원본의 최대가 0.95인 사각파는 16 kHz로 바꾸면 1을 넘는다(울림). 원본 기준으로 재므로 클리핑이 아니다."""
        sr = 48000
        square = (0.95 * np.sign(np.sin(2 * np.pi * 200 * np.arange(sr * 2) / sr))).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "square.wav")
            wavfile.write(path, sr, np.round(square * 32767).astype(np.int16))
            r = quality.check_file(path)
        self.assertEqual(r["metrics"]["clip_ratio"], 0.0)
        self.assertAlmostEqual(r["metrics"]["peak"], 0.95, delta=0.01)
        self.assertFalse(has(r, "잘렸을 수"))


if __name__ == "__main__":
    unittest.main()
