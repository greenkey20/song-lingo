"""stt.recognize·recognize_words가 경로·bytes·배열 입력을 올바르게 transcribe에 넘기는지(이슈 #37).
모델은 쓰지 않는다: transcribe가 받은 첫 인자만 기록하는 가짜 모델을 끼운다. 실행: python -m unittest tests.test_stt_input -v"""
import io
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stt  # noqa: E402


class Seg:
    text = " hi"
    words = []


class FakeModel:
    """transcribe가 받은 소리(첫 인자)를 기록한다. 재료로 내용을 읽어 두어 BytesIO가 닫혀도 확인할 수 있게 한다."""
    def __init__(self):
        self.audio = None
        self.content = None

    def transcribe(self, audio, **kw):
        self.audio = audio
        self.content = audio.getvalue() if isinstance(audio, io.BytesIO) else None
        return iter([Seg()]), None


class InputTypes(unittest.TestCase):
    def setUp(self):
        self.fake = FakeModel()
        self.orig = stt.load_model
        stt.load_model = lambda size=None: self.fake
        self.addCleanup(lambda: setattr(stt, "load_model", self.orig))

    def test_path_str_and_pathlike_are_passed_as_str(self):
        from pathlib import Path
        stt.recognize("a.wav")
        self.assertEqual(self.fake.audio, "a.wav")
        stt.recognize(Path("data") / "b.wav")
        self.assertEqual(self.fake.audio, str(Path("data") / "b.wav"))

    def test_bytes_and_file_objects_become_bytesio_with_same_content(self):
        data = b"RIFF....WAVEdata"
        for src in (data, bytearray(data), io.BytesIO(data)):
            stt.recognize(src)
            self.assertIsInstance(self.fake.audio, io.BytesIO)
            self.assertEqual(self.fake.content, data)

    def test_float32_mono_array_is_passed_through(self):
        x = np.zeros(16000, dtype=np.float32)
        stt.recognize(x)
        self.assertIs(self.fake.audio, x)                   # 복사하지 않고 그대로

    def test_other_dtype_array_is_converted_to_float32(self):
        stt.recognize(np.zeros(16000, dtype=np.float64))
        self.assertEqual(self.fake.audio.dtype, np.float32)

    def test_non_mono_or_empty_array_is_rejected(self):
        with self.assertRaises(ValueError):
            stt.recognize(np.zeros((16000, 2), dtype=np.float32))     # 스테레오를 16 kHz 모노로 믿고 넘기면 엉뚱한 결과가 나온다
        with self.assertRaises(ValueError):
            stt.recognize(np.zeros(0, dtype=np.float32))

    def test_unsupported_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            stt.recognize(123)

    def test_recognize_words_accepts_same_inputs(self):
        x = np.zeros(16000, dtype=np.float32)
        stt.recognize_words(x)
        self.assertIs(self.fake.audio, x)
        stt.recognize_words(b"abc")
        self.assertIsInstance(self.fake.audio, io.BytesIO)


if __name__ == "__main__":
    unittest.main()
