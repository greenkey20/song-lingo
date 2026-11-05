"""stt.recognize_segments 단위 테스트(이슈 #31). 모델 없이 가짜 모델로 구간 객체 → dict 변환과 인자 전달을 확인한다.
실행: python -m unittest tests.test_stt_segments -v"""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stt  # noqa: E402


class W:
    def __init__(self, word, start, end, p): self.word, self.start, self.end, self.probability = word, start, end, p


class Seg:
    def __init__(self, start, end, text, words=None):
        self.start, self.end, self.text = start, end, text
        self.avg_logprob, self.no_speech_prob, self.compression_ratio = -0.4, 0.02, 1.3
        self.words = words


class FakeModel:
    def __init__(self, segs): self.segs, self.kw, self.audio = segs, None, None

    def transcribe(self, audio, **kw):
        self.audio, self.kw = audio, kw
        return iter(self.segs), None


class Segments(unittest.TestCase):
    def setUp(self):
        self.orig = stt.load_model
        self.addCleanup(lambda: setattr(stt, "load_model", self.orig))

    def use(self, segs):
        self.fake = FakeModel(segs)
        stt.load_model = lambda size=None: self.fake

    def test_returns_times_text_and_confidence_for_each_segment(self):
        self.use([Seg(0.0, 3.2, " first line "), Seg(3.2, 7.5, "second")])
        segs, sec = stt.recognize_segments("clip.wav")
        self.assertEqual([(s["start"], s["end"], s["text"]) for s in segs], [(0.0, 3.2, "first line"), (3.2, 7.5, "second")])
        self.assertEqual((segs[0]["avg_logprob"], segs[0]["no_speech_prob"], segs[0]["compression_ratio"]), (-0.4, 0.02, 1.3))
        self.assertIsNone(segs[0]["words"])                   # 단어 시간을 안 요청하면 None
        self.assertGreaterEqual(sec, 0.0)

    def test_song_defaults_vad_off_and_word_timestamps_only_when_asked(self):
        self.use([Seg(0, 1, "a")])
        stt.recognize_segments("clip.wav")
        self.assertIs(self.fake.kw["vad_filter"], False)      # 노래는 VAD 끔이 기본
        self.assertIs(self.fake.kw["word_timestamps"], False)
        self.assertNotIn("temperature", self.fake.kw)         # 안 주면 기본 동작 그대로
        stt.recognize_segments("clip.wav", word_timestamps=True, temperature=0.0)
        self.assertIs(self.fake.kw["word_timestamps"], True)
        self.assertEqual(self.fake.kw["temperature"], 0.0)

    def test_words_are_included_when_requested(self):
        self.use([Seg(0, 2, "hello there", words=[W(" hello", 0.1, 0.8, 0.9), W(" there", 0.9, 1.6, 0.8)])])
        segs, _ = stt.recognize_segments("clip.wav", word_timestamps=True)
        self.assertEqual([w["word"] for w in segs[0]["words"]], ["hello", "there"])
        self.assertEqual(segs[0]["words"][1]["start"], 0.9)

    def test_passes_path_and_bytes_like_recognize(self):
        self.use([Seg(0, 1, "a")])
        stt.recognize_segments("clip.wav")
        self.assertEqual(self.fake.audio, "clip.wav")         # 경로는 그대로(변환 배열이 아님)
        stt.recognize_segments(b"RIFF....WAVE")
        self.assertIsInstance(self.fake.audio, io.BytesIO)

    def test_no_segments_gives_empty_list(self):
        self.use([])
        self.assertEqual(stt.recognize_segments("silence.wav")[0], [])

class Multilingual(unittest.TestCase):
    def setUp(self):
        self.orig = stt.load_model
        self.addCleanup(lambda: setattr(stt, "load_model", self.orig))
        self.fake = FakeModel([Seg(0.0, 1.0, "x")])
        stt.load_model = lambda size=None: self.fake

    def test_multilingual_flag_is_passed_only_when_true(self):
        stt.recognize_segments(b"", language=None)                       # 기본: transcribe에 multilingual을 넘기지 않아 기존 동작 그대로
        self.assertNotIn("multilingual", self.fake.kw)
        stt.recognize_segments(b"", language=None, multilingual=True)
        self.assertTrue(self.fake.kw["multilingual"])
        self.assertIsNone(self.fake.kw["language"])                      # 자동 감지

    def test_language_is_passed_through(self):
        stt.recognize_segments(b"", language="ja")
        self.assertEqual(self.fake.kw["language"], "ja")


class DetectLanguage(unittest.TestCase):
    def setUp(self):
        self.orig = stt.load_model
        self.addCleanup(lambda: setattr(stt, "load_model", self.orig))

    def test_returns_code_prob_and_all_probs_as_floats(self):
        import numpy as np

        class M:
            def detect_language(self, x):
                self.n = len(x)
                return "ja", np.float32(0.9), [("ja", np.float32(0.9)), ("en", np.float32(0.05))]
        m = M()
        stt.load_model = lambda size=None: m
        sr = 16000
        import recorder
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            wav = recorder.save_wav(Path(d) / "x.wav", np.zeros((sr, 2), dtype="float32") + 0.1, sr)
            code, prob, probs = stt.detect_language(wav)
        self.assertEqual((code, type(prob)), ("ja", float))
        self.assertEqual(probs, [("ja", 0.8999999761581421), ("en", 0.05000000074505806)])
        self.assertEqual(m.n, sr)                                        # 16 kHz 모노 1초가 모델에 들어감

    def test_too_short_sound_is_rejected(self):
        import numpy as np
        import recorder
        import tempfile
        from pathlib import Path
        stt.load_model = lambda size=None: None
        with tempfile.TemporaryDirectory() as d:
            wav = recorder.save_wav(Path(d) / "x.wav", np.zeros((100, 2), dtype="float32"), 16000)
            with self.assertRaises(ValueError):
                stt.detect_language(wav)


if __name__ == "__main__":
    unittest.main()
