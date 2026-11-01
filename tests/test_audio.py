"""audio.py 단위 테스트. 실행: python -m unittest tests.test_audio -v
합성 신호(사인파)만 쓴다: 개인 녹음 파일은 저장소에 없으므로 테스트가 만들어 낸 임시 파일을 쓴다."""
import os
import sys
import tempfile
import unittest

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import audio  # noqa: E402


def sine(seconds, sr, freq=440.0, amp=0.5):
    return (amp * np.sin(2 * np.pi * freq * np.arange(int(seconds * sr)) / sr)).astype(np.float32)


def write_wav(path, x, sr):
    """float 파형(-1~1) → PCM16 wav. x가 2차원이면 (샘플, 채널)."""
    wavfile.write(path, sr, np.round(x * 32767).astype(np.int16))


def encode_with_av(path, x, src_sr, codec, rate):
    """모노 float 파형을 PyAV로 압축 파일(webm/opus, m4a/aac)로 저장한다. 브라우저 녹음 형식을 흉내 내는 용도."""
    import av
    with av.open(path, "w") as out:
        stream = out.add_stream(codec, rate=rate)
        stream.layout = "mono"
        frame = av.AudioFrame.from_ndarray(x[None, :], format="flt", layout="mono")
        frame.sample_rate = src_sr
        rs = av.AudioResampler(format=stream.codec_context.format.name, layout="mono", rate=rate)
        for f in list(rs.resample(frame)) + list(rs.resample(None)):
            for pkt in stream.encode(f):
                out.mux(pkt)
        for pkt in stream.encode(None):
            out.mux(pkt)


class WavInput(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def test_48k_mono_becomes_16k(self):
        write_wav(self.path("a.wav"), sine(2, 48000), 48000)
        x, sr, ch = audio.load_audio(self.path("a.wav"))
        self.assertEqual((sr, ch, x.dtype), (48000, 1, np.float32))
        self.assertEqual(len(x), 32000)               # 2초 × 16000
        self.assertAlmostEqual(float(np.abs(x[2000:-2000]).max()), 0.5, delta=0.02)   # 가장자리 울림 제외

    def test_44k_gives_integer_ratio_length(self):
        write_wav(self.path("a.wav"), sine(1, 44100), 44100)
        x, sr, _ = audio.load_audio(self.path("a.wav"))
        self.assertEqual(sr, 44100)
        self.assertAlmostEqual(len(x), 16000, delta=2)

    def test_stereo_is_averaged_to_mono(self):
        left, right = sine(1, 16000, amp=0.6), np.zeros(16000, np.float32)
        write_wav(self.path("s.wav"), np.stack([left, right], axis=1), 16000)
        x, sr, ch = audio.load_audio(self.path("s.wav"))
        self.assertEqual((sr, ch, len(x)), (16000, 2, 16000))
        self.assertAlmostEqual(float(np.abs(x).max()), 0.3, delta=0.01)   # (0.6 + 0) / 2

    def test_16k_input_is_unchanged(self):
        src = sine(1, 16000)
        write_wav(self.path("a.wav"), src, 16000)
        x, _, _ = audio.load_audio(self.path("a.wav"))
        np.testing.assert_allclose(x, src, atol=1e-4)

    def test_empty_wav_raises(self):
        wavfile.write(self.path("e.wav"), 16000, np.zeros(0, np.int16))
        with self.assertRaises(ValueError):
            audio.load_audio(self.path("e.wav"))


class CompressedInput(unittest.TestCase):
    """브라우저 녹음 형식. 가운데 구간의 진폭과 전체 길이만 본다(압축 파일은 앞뒤 가장자리 값이 원본과 다를 수 있다)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def check(self, name, codec, rate, expect_sr):
        path = os.path.join(self.tmp.name, name)
        encode_with_av(path, sine(2, 48000), 48000, codec, rate)
        x, sr, ch = audio.load_audio(path)
        self.assertEqual((sr, ch), (expect_sr, 1))
        self.assertAlmostEqual(len(x) / 16000, 2.0, delta=0.1)
        mid = x[len(x) // 10: -len(x) // 10]
        self.assertAlmostEqual(float(np.abs(mid).max()), 0.5, delta=0.05)

    def test_webm_opus(self):      # Chrome의 MediaRecorder 형식(48 kHz)
        self.check("a.webm", "libopus", 48000, 48000)

    def test_m4a_aac(self):        # Safari의 MediaRecorder 형식(mp4/aac, 44.1 kHz)과 같은 코덱
        self.check("a.m4a", "aac", 44100, 44100)

    def test_not_audio_raises(self):
        path = os.path.join(self.tmp.name, "x.webm")
        with open(path, "wb") as f:
            f.write(b"this is not audio")
        with self.assertRaises(Exception):
            audio.load_audio(path)


if __name__ == "__main__":
    unittest.main()
