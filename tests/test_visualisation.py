"""visualisation.py 단위 테스트. 실행: python -m unittest tests.test_visualisation -v
합성 신호(사인파)만 쓴다."""
import os
import sys
import unittest

import matplotlib
matplotlib.use("Agg")                       # 화면 없이 그리기(테스트용)
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import visualisation as vis  # noqa: E402

SR = 16000


def sine(freq, seconds=1.0, amp=0.5):
    return (amp * np.sin(2 * np.pi * freq * np.arange(int(SR * seconds)) / SR)).astype(np.float32)


class StftPower(unittest.TestCase):
    def test_shape_matches_formula(self):
        hz, times, power = vis.stft_power(sine(1000), SR)
        frames = 1 + (SR - vis.FRAME_LENGTH) // vis.HOP_LENGTH       # 앞뒤를 채우지 않는 설정의 프레임 수
        self.assertEqual(power.shape, (vis.FRAME_LENGTH // 2 + 1, frames))
        self.assertEqual((len(hz), len(times)), power.shape)

    def test_peak_is_at_sine_frequency(self):
        hz, _, power = vis.stft_power(sine(1000), SR)                # 1 kHz는 31.25 Hz 간격의 32번째 칸
        self.assertAlmostEqual(float(hz[power.mean(axis=1).argmax()]), 1000.0, delta=1.0)

    def test_silence_has_zero_power(self):
        _, _, power = vis.stft_power(np.zeros(SR, np.float32), SR)
        self.assertEqual(float(power.max()), 0.0)


class ToDb(unittest.TestCase):
    def test_known_values(self):
        self.assertAlmostEqual(float(vis.to_db(1.0)), 0.0)
        self.assertAlmostEqual(float(vis.to_db(100.0)), 20.0)
        self.assertAlmostEqual(float(vis.to_db(0.0)), -100.0)        # 바닥값 1e-10 → -100 dB


class Mel(unittest.TestCase):
    def test_filters_are_triangles(self):
        hz, _, power = vis.stft_power(sine(1000), SR)
        _, filters = vis.apply_mel_filters(hz, power, SR)
        self.assertEqual(filters.shape, (vis.N_MELS, len(hz)))
        self.assertTrue((filters >= 0).all() and (filters <= 1 + 1e-9).all())
        self.assertTrue((filters.sum(axis=1) > 0).all())             # 필터가 하나도 비어 있지 않다

    def test_logmel_shape_and_silence_floor(self):
        f = vis.logmel(np.zeros(SR, np.float32), SR)
        self.assertEqual(f["log_mel"].shape, (vis.N_MELS, f["power"].shape[1]))
        self.assertAlmostEqual(float(f["log_mel"].max()), -100.0)

    def test_higher_tone_lands_in_higher_mel_bin(self):
        low = vis.logmel(sine(300), SR)["log_mel"].mean(axis=1).argmax()
        high = vis.logmel(sine(3000), SR)["log_mel"].mean(axis=1).argmax()
        self.assertLess(low, high)


class Plots(unittest.TestCase):
    """그림 함수는 '오류 없이 그려지고 구성이 맞는가'만 확인한다(모양의 좋고 나쁨은 눈으로 본다)."""

    def tearDown(self):
        plt.close("all")

    def test_sound_pair_makes_3x2_grid_plus_colorbars(self):
        fig = vis.plot_sound_pair([("a", sine(440)), ("b", sine(880, 1.5))], "제목")
        self.assertEqual(len(fig.axes), 6 + 2)          # 그림 6칸 + 색 막대 2개
        self.assertEqual(fig._suptitle.get_text(), "제목")

    def test_error_spans_marks_each_block_on_every_row(self):
        toks = [{"token": "a", "start": 0.1, "end": 0.4, "prob": 1.0}, {"token": "b", "start": 0.5, "end": 0.9, "prob": 1.0}]
        blocks = [{"tts_span": (0.1, 0.4), "hyp_span": (0.5, 0.9)}]          # 구간이 있는 덩어리
        sounds = [("TTS", sine(440), toks, "tts_span"), ("내 녹음", sine(440), toks, "hyp_span")]
        fig = vis.plot_error_spans(sounds, blocks, "제목")
        self.assertEqual(len(fig.axes), 9)              # 3x3 격자(오른쪽 열은 색 막대와 빈 칸)
        labels = [t.get_text() for ax in fig.axes for t in ax.texts]
        self.assertEqual(labels.count("[1]"), 2)        # 두 소리의 스펙트로그램에 같은 번호가 하나씩

    def test_error_spans_point_block_does_not_crash(self):
        toks = [{"token": "a", "start": 0.1, "end": 0.4, "prob": 1.0}]
        blocks = [{"tts_span": (0.4, 0.4), "hyp_span": (0.4, 0.4)}]          # 삭제·삽입: 길이 0인 한 점
        vis.plot_error_spans([("TTS", sine(440), toks, "tts_span"), ("내 녹음", sine(440), toks, "hyp_span")], blocks, "t")


class SoundPanels(unittest.TestCase):
    def test_fft_spectrum_peak_and_axis(self):
        # 03 실습: 440 Hz 사인파 → rfft의 가장 큰 칸이 440 Hz, 칸 간격은 sr/길이, 마지막 칸은 sr/2
        x = sine(440, 1.0)
        hz, amp = vis.fft_spectrum(x, SR)
        self.assertEqual(len(hz), len(x) // 2 + 1)
        self.assertAlmostEqual(hz[int(np.argmax(amp))], 440, delta=2)
        self.assertAlmostEqual(hz[1] - hz[0], SR / len(x))
        self.assertAlmostEqual(hz[-1], SR / 2)

    def test_fft_spectrum_normalised_by_length(self):
        # 길이가 달라도 같은 소리면 크기가 비슷해야 한다(÷샘플 수 보정, 03 셀 9)
        a = vis.fft_spectrum(sine(440, 1.0), SR, use_window=False)[1].max()
        b = vis.fft_spectrum(sine(440, 2.0), SR, use_window=False)[1].max()
        self.assertAlmostEqual(a, b, delta=0.01)
        self.assertAlmostEqual(a, 0.25, delta=0.01)             # 진폭 0.5인 사인파 → 크기 = 진폭/2

    def test_fft_spectrum_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            vis.fft_spectrum(np.zeros(1), SR)

    def test_panels_reject_too_short_sound(self):
        with self.assertRaises(ValueError):
            vis.plot_sound_panels([("표준 발음", sine(440, 1.0)), ("내 녹음", np.zeros(100, dtype=np.float32))], SR)

    def test_panels_make_four_figures_with_shared_axes(self):
        figs = vis.plot_sound_panels([("표준 발음", sine(440, 1.0)), ("내 녹음", sine(440, 0.6))], SR)
        try:
            self.assertEqual(set(figs), {"wave", "fft", "stft", "logmel"})
            wave_axes = [a for a in figs["wave"].axes]
            self.assertEqual(len(wave_axes), 2)                            # 이름별로 나란히
            self.assertEqual(wave_axes[0].get_xlim(), wave_axes[1].get_xlim())   # 같은 시간축(긴 쪽 기준)
            self.assertEqual(len(figs["fft"].axes[0].lines), 2)            # 한 그림에 두 소리를 겹쳐 그림
            self.assertEqual(len(figs["stft"].axes), 3)                    # 두 칸 + 색 막대
        finally:
            for f in figs.values():
                plt.close(f)


if __name__ == "__main__":
    unittest.main()
