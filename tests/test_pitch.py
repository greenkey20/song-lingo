"""pitch.py 단위 테스트. 실행: python -m unittest tests.test_pitch -v
정답 주파수를 아는 합성 신호만 쓴다(실제 목소리는 정답을 몰라 알고리즘 검증이 안 된다). 허용 오차 ±10%는 이 모듈의 회귀 기준이며
pYIN의 보편적 정확도 보증이 아니다. librosa(numba)의 첫 호출은 컴파일 때문에 몇 초 걸릴 수 있다."""
import io
import os
import sys
import unittest
from unittest import mock

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pitch  # noqa: E402

SR = 16000


def tone(freq, seconds, amp=0.5):
    return (amp * np.sin(2 * np.pi * freq * np.arange(int(SR * seconds)) / SR)).astype(np.float32)


def wav_bytes(x):
    """float32 파형 → 16 kHz 모노 PCM16 WAV bytes(웹에서 오는 녹음 bytes와 같은 형태)."""
    buf = io.BytesIO()
    wavfile.write(buf, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    return buf.getvalue()


class SineWaves(unittest.TestCase):
    def test_known_frequencies(self):
        for hz in (120, 200, 250):
            with self.subTest(hz=hz):
                out = pitch.analyze_f0(wav_bytes(tone(hz, 3.0)))
                self.assertEqual(out["status"], "ok")
                self.assertAlmostEqual(out["median_hz"] / hz, 1.0, delta=0.10)
                self.assertLess(out["range_semitones"], 1.0)         # 일정한 음이라 P10~P90 폭이 거의 0

    def test_arrays_have_same_length_and_20ms_hop(self):
        out = pitch.analyze_f0(wav_bytes(tone(200, 2.0)))
        n = len(out["f0"])
        for k in ("times", "voiced_flag", "voiced_probs", "valid"):
            self.assertEqual(len(out[k]), n)
        self.assertAlmostEqual(float(out["times"][1] - out["times"][0]), 0.02, places=6)      # hop 320 / 16000

    def test_accepts_bytes_and_file_object(self):
        data = wav_bytes(tone(200, 1.0))
        a = pitch.analyze_f0(data)["median_hz"]
        b = pitch.analyze_f0(io.BytesIO(data))["median_hz"]
        self.assertAlmostEqual(a, b, places=6)


class NotVoiced(unittest.TestCase):
    def test_silence_is_not_zero_hz(self):
        out = pitch.analyze_f0(wav_bytes(np.zeros(SR * 3, np.float32)))
        self.assertEqual(out["status"], "insufficient_voicing")
        self.assertEqual(int(out["valid"].sum()), 0)
        self.assertFalse(np.any(out["f0"] == 0))                     # 무음을 0 Hz로 바꾸지 않는다(NaN)
        self.assertIsNone(out["median_hz"])

    def test_too_short(self):
        out = pitch.analyze_f0(wav_bytes(tone(200, 0.05)))
        self.assertEqual(out["status"], "too_short")
        self.assertIsNone(out["f0"])

    def test_silence_part_of_a_recording_is_nan(self):
        x = np.concatenate([np.zeros(SR, np.float32), tone(200, 1.5), np.zeros(SR, np.float32)])
        out = pitch.analyze_f0(wav_bytes(x))
        self.assertEqual(out["status"], "ok")
        head = out["times"] < 0.8                                    # 앞 무음 구간(0~1초)의 안쪽
        self.assertTrue(np.all(~out["valid"][head]))
        self.assertTrue(np.all(np.isnan(out["f0"][head])))
        mid = (out["times"] > 1.2) & (out["times"] < 2.3)
        self.assertGreater(out["valid"][mid].mean(), 0.8)

    def test_librosa_missing_returns_unavailable(self):
        with mock.patch.dict(sys.modules, {"librosa": None}):          # None이면 import가 ImportError
            out = pitch.analyze_f0(wav_bytes(tone(200, 1.0)))
        self.assertEqual(out["status"], "unavailable")


class FundamentalVsLoudestPartial(unittest.TestCase):
    def test_f0_is_not_the_loudest_peak(self):
        """150 Hz 기본음에 2배음(300 Hz)이 더 센 소리: FFT의 가장 큰 봉우리는 300 Hz지만 F0는 150 Hz다(검토 문서 16.18)."""
        x = tone(150, 2.0, 0.2) + tone(300, 2.0, 0.4)
        spectrum = np.abs(np.fft.rfft(x))
        self.assertAlmostEqual(np.fft.rfftfreq(len(x), 1 / SR)[int(np.argmax(spectrum))], 300, delta=2)
        out = pitch.analyze_f0(wav_bytes(x))
        self.assertEqual(out["status"], "ok")
        self.assertAlmostEqual(out["median_hz"] / 150, 1.0, delta=0.10)


class RelativeSemitones(unittest.TestCase):
    def test_median_is_zero_and_octave_is_twelve(self):
        f0 = np.array([100.0, 100.0, 100.0, 200.0, 50.0])
        rel = pitch.relative_semitones(f0, np.ones(5, bool), median_hz=100.0)
        np.testing.assert_allclose(rel, [0, 0, 0, 12, -12], atol=1e-9)

    def test_default_median_from_valid_frames_only(self):
        f0 = np.array([np.nan, 100.0, 200.0, 400.0, np.nan])
        valid = pitch.valid_mask(f0)
        rel = pitch.relative_semitones(f0, valid)
        self.assertTrue(np.isnan(rel[0]) and np.isnan(rel[4]))        # 무성음은 NaN 그대로
        np.testing.assert_allclose(rel[1:4], [-12, 0, 12], atol=1e-9)  # 중앙값 200 기준

    def test_no_valid_frames_gives_all_nan(self):
        rel = pitch.relative_semitones(np.array([np.nan, np.nan]), np.zeros(2, bool))
        self.assertTrue(np.all(np.isnan(rel)))

    def test_valid_mask_excludes_nan_inf_zero_negative(self):
        f0 = np.array([np.nan, np.inf, 0.0, -5.0, 120.0])
        np.testing.assert_array_equal(pitch.valid_mask(f0), [False, False, False, False, True])
        np.testing.assert_array_equal(pitch.valid_mask(f0, [True] * 4 + [False]), [False] * 5)       # voiced_flag가 거짓이면 제외


class JumpRatio(unittest.TestCase):
    def test_counts_only_adjacent_valid_pairs(self):
        rel = np.array([0.0, 0.5, 12.0, np.nan, 12.2, 12.4])
        valid = np.array([True, True, True, False, True, True])
        # 이웃 쌍: (0→0.5) 안 튐, (0.5→12) 튐, (12.2→12.4) 안 튐 → 1/3. 무성음을 낀 쌍은 세지 않는다.
        self.assertAlmostEqual(pitch.jump_ratio(rel, valid), 1 / 3)

    def test_none_when_no_pairs(self):
        self.assertIsNone(pitch.jump_ratio(np.array([0.0, np.nan, 1.0]), np.array([True, False, True])))


class EdgeChange(unittest.TestCase):
    def test_rising_end_is_positive(self):
        f0 = np.concatenate([np.full(30, 150.0), np.full(30, 300.0)])
        e = pitch.edge_change(f0, np.ones(60, bool))
        self.assertAlmostEqual(e["start_hz"], 150.0)
        self.assertAlmostEqual(e["end_hz"], 300.0)
        self.assertAlmostEqual(e["change_semitones"], 12.0, places=6)

    def test_flat_is_zero_and_falling_is_negative(self):
        self.assertAlmostEqual(pitch.edge_change(np.full(60, 200.0), np.ones(60, bool))["change_semitones"], 0.0)
        self.assertLess(pitch.edge_change(np.linspace(300, 150, 60), np.ones(60, bool))["change_semitones"], 0)

    def test_none_when_too_few_voiced_frames(self):
        self.assertIsNone(pitch.edge_change(np.full(12, 200.0), np.ones(12, bool)))       # 12개의 1/3 = 4개 < 5

    def test_unvoiced_frames_are_ignored(self):
        f0 = np.full(90, np.nan)
        f0[10:40], f0[60:90] = 150.0, 300.0
        e = pitch.edge_change(f0, pitch.valid_mask(f0))
        self.assertAlmostEqual(e["change_semitones"], 12.0, places=6)

    def test_pyin_rising_tone_end_to_end(self):
        x = np.concatenate([tone(150, 1.5), tone(300, 1.5)])
        out = pitch.analyze_f0(wav_bytes(x))
        self.assertEqual(out["status"], "ok")
        self.assertAlmostEqual(out["edge"]["change_semitones"], 12.0, delta=1.0)


class WarmUp(unittest.TestCase):
    def test_returns_true_and_never_raises(self):
        self.assertTrue(pitch.warm_up())
        with mock.patch.dict(sys.modules, {"librosa": None}):
            self.assertFalse(pitch.warm_up())                          # librosa가 없어도 예외 없이 False

    def test_analyze_waveform_matches_analyze_f0(self):
        x = tone(200, 1.0)
        a = pitch.analyze_waveform(x)["median_hz"]
        b = pitch.analyze_f0(wav_bytes(x))["median_hz"]
        self.assertAlmostEqual(a, b, delta=2.0)                         # PCM16 양자화 차이만큼만 다르다


class ToWordAxis(unittest.TestCase):
    TIMES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    VALUES = [1, 2, np.nan, 4, 5, 6]

    def test_worked_example_from_the_docstring(self):
        x, y = pitch.to_word_axis(self.TIMES, self.VALUES, [(0.0, 0.2), None, (0.3, 0.5)])
        np.testing.assert_allclose(x, [0, 0.5, 1, np.nan, 2, 2.5, 3, np.nan], equal_nan=True)
        np.testing.assert_allclose(y, [1, 2, np.nan, np.nan, 4, 5, 6, np.nan], equal_nan=True)

    def test_same_word_lands_in_same_cell_even_if_speeds_differ(self):
        """같은 단어(i=1)를 빠르게(0.1초)·느리게(0.4초) 말해도 x는 모두 1~2 사이에서 같은 비율에 놓인다."""
        fast_t, slow_t = np.linspace(1.0, 1.1, 5), np.linspace(2.0, 2.4, 5)
        xf, _ = pitch.to_word_axis(fast_t, np.zeros(5), [None, (1.0, 1.1)])
        xs, _ = pitch.to_word_axis(slow_t, np.zeros(5), [None, (2.0, 2.4)])
        np.testing.assert_allclose(xf[:5], xs[:5])
        self.assertTrue(np.all((xf[:5] >= 1) & (xf[:5] <= 2)))

    def test_unvoiced_frames_stay_nan_inside_a_word(self):
        x, y = pitch.to_word_axis([0.0, 0.1, 0.2], [1.0, np.nan, 3.0], [(0.0, 0.2)])
        self.assertTrue(np.isnan(y[1]))                          # 단어 안의 무성음은 0으로 채우지 않고 선이 끊긴다

    def test_words_are_separated_by_nan(self):
        x, y = pitch.to_word_axis([0.0, 0.1, 0.2, 0.3], [1, 2, 3, 4], [(0.0, 0.1), (0.2, 0.3)])
        self.assertEqual(int(np.isnan(x).sum()), 2)               # 단어마다 끝에 구분 NaN 하나

    def test_too_short_or_missing_spans_are_skipped(self):
        x, y = pitch.to_word_axis([0.0, 0.01, 0.02], [1, 2, 3], [(0.0, 0.02), None])
        self.assertEqual((len(x), len(y)), (0, 0))               # 0.02초 < 0.03초 → 그리지 않음

    def test_integrates_with_relative_semitones(self):
        f0 = np.array([100.0, 100.0, 200.0, 200.0])
        rel = pitch.relative_semitones(f0, np.ones(4, bool), median_hz=100.0)
        _, y = pitch.to_word_axis([0.0, 0.1, 0.2, 0.3], rel, [(0.0, 0.1), (0.2, 0.3)])
        np.testing.assert_allclose(y, [0, 0, np.nan, 12, 12, np.nan], atol=1e-9, equal_nan=True)


if __name__ == "__main__":
    unittest.main()
