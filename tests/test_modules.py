"""tts.py·stt.py의 API·모델 없이 확인할 수 있는 부분(조회, 파일 찾기, 캐시 적중)."""
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import stt
import tts

SENTENCES = [{"id": "1", "lang": "en", "sentence": "Hello there.", "meaning_ko": "안녕."}]


class Lookup(unittest.TestCase):
    def test_csv_id(self):
        row, path = tts.lookup_sentence(1, SENTENCES)
        self.assertEqual(row["sentence"], "Hello there.")
        self.assertEqual(path, tts.CACHE_DIR / "s01.wav")

    def test_free_text_is_hashed_and_stable(self):
        row, p1 = tts.lookup_sentence("  Where the river meets the sea. ", SENTENCES)
        _, p2 = tts.lookup_sentence("Where the river meets the sea.", SENTENCES)
        self.assertEqual(row["id"], "직접 입력")
        self.assertEqual(p1, p2)
        self.assertTrue(p1.name.startswith("custom_"))

    def test_cache_hit_makes_no_api_call(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.wav"
            p.write_bytes(b"x")
            before = tts.calls
            self.assertEqual(tts.tts_wav("anything", p), p)
            self.assertEqual(tts.calls, before)


class FindRecording(unittest.TestCase):
    def test_any_extension_and_missing(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s02_take1.m4a").write_bytes(b"x")
            self.assertEqual(stt.find_recording(2, rec_dir=d).name, "s02_take1.m4a")
            self.assertIsNone(stt.find_recording(3, rec_dir=d))


class ModelSizes(unittest.TestCase):
    """stt.py의 모델 크기 바꾸기. faster_whisper를 가짜로 바꿔서 모델을 내려받지 않고 '어떤 인자로 읽는가'만 확인한다."""

    def setUp(self):
        stt.unload_models()
        self.addCleanup(stt.unload_models)
        self.created = []                  # (크기, 생성 인자) 기록
        outer = self

        class FakeModel:
            def __init__(self, size, **kw):
                outer.created.append((size, kw))
                self.size, self.kw = size, {}

            def transcribe(self, path, **kw):
                self.kw = kw               # 인식을 부를 때 넘긴 인자(language, beam_size …)
                return [types.SimpleNamespace(text=f" hello from {self.size} ")], None

        patcher = mock.patch.dict(sys.modules, {"faster_whisper": types.SimpleNamespace(WhisperModel=FakeModel)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_default_is_tiny_cpu_int8_and_loaded_once(self):
        m1, m2 = stt.load_model(), stt.load_model("tiny")
        self.assertIs(m1, m2)                                  # 같은 크기는 한 번만 읽는다
        self.assertEqual(len(self.created), 1)
        size, kw = self.created[0]
        self.assertEqual((size, kw["device"], kw["compute_type"], kw["download_root"]), ("tiny", "cpu", "int8", "models"))

    def test_each_size_is_a_separate_model(self):
        tiny, small = stt.load_model("tiny"), stt.load_model("small")
        self.assertIsNot(tiny, small)
        self.assertEqual([c[0] for c in self.created], ["tiny", "small"])

    def test_recognize_uses_requested_size_and_default_stays_tiny(self):
        text, _ = stt.recognize("x.wav", "en", model_size="small")
        self.assertEqual(text, "hello from small")
        kw = stt.load_model("small").kw
        self.assertEqual((kw["language"], kw["beam_size"]), ("en", 1))
        text, _ = stt.recognize("x.wav")                       # 기존 호출 방식: 크기를 안 주면 tiny
        self.assertEqual(text, "hello from tiny")

    def test_recognize_words_passes_size(self):
        class W:
            word, start, end, probability = " hi ", 0.0, 0.5, 0.9
        with mock.patch.object(stt, "load_model") as load:
            load.return_value.transcribe.return_value = ([types.SimpleNamespace(words=[W])], None)
            text, words, _ = stt.recognize_words("x.wav", "en", model_size="base")
        load.assert_called_once_with("base")
        self.assertEqual((text, words[0]["word"]), ("hi", "hi"))

    def test_vad_defaults_keep_old_behaviour_and_can_be_overridden(self):
        """recognize는 기본 VAD 끔(7강과 같음), recognize_words는 기본 켬. 인자로 둘 다 바꿀 수 있다."""
        stt.recognize("x.wav")
        self.assertIs(stt.load_model().kw["vad_filter"], False)
        stt.recognize("x.wav", vad_filter=True)
        self.assertIs(stt.load_model().kw["vad_filter"], True)

        class W:
            word, start, end, probability = " hi ", 0.0, 0.5, 0.9
        with mock.patch.object(stt, "load_model") as load:
            load.return_value.transcribe.return_value = ([types.SimpleNamespace(words=[W])], None)
            stt.recognize_words("x.wav")
            self.assertIs(load.return_value.transcribe.call_args.kwargs["vad_filter"], True)
            stt.recognize_words("x.wav", vad_filter=False)
            kw = load.return_value.transcribe.call_args.kwargs
            self.assertIs(kw["vad_filter"], False)
            self.assertIs(kw["word_timestamps"], True)          # VAD를 꺼도 단어 시간은 그대로 요청한다

    def test_unload_models_forces_reload(self):
        stt.load_model()
        stt.unload_models()
        stt.load_model()
        self.assertEqual(len(self.created), 2)

    def test_unload_one_size_and_loaded_models(self):
        stt.load_model("tiny")
        stt.load_model("small")
        self.assertEqual(stt.loaded_models(), ("tiny", "small"))
        stt.unload_models("small")                            # 크기를 주면 그 모델만 내린다
        self.assertEqual(stt.loaded_models(), ("tiny",))
        stt.unload_models("never_loaded")                     # 읽은 적 없는 크기를 내려도 오류가 아니다
        stt.unload_models()
        self.assertEqual(stt.loaded_models(), ())

    def test_settings_report(self):
        self.assertEqual(stt.settings(), {"model": "tiny", "device": "cpu", "compute_type": "int8", "beam_size": 1})
        self.assertEqual(stt.settings("small")["model"], "small")


class AvailableModels(unittest.TestCase):
    """stt.available_models: models/ 폴더 구조(Hugging Face 캐시)를 가짜로 만들어 '내려받아 둔 모델'을 찾는지 확인한다."""

    def make_model(self, root, name, with_bin=True):
        snap = Path(root) / f"models--Systran--faster-whisper-{name}" / "snapshots" / "abc123"
        snap.mkdir(parents=True)
        (snap / "config.json").write_text("{}")
        if with_bin:
            (snap / "model.bin").write_bytes(b"x")

    def test_finds_downloaded_models_in_size_order(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("large-v3", "small", "tiny", "base.en"):
                self.make_model(d, name)
            self.make_model(d, "base", with_bin=False)          # 받다 만 폴더(model.bin 없음)는 제외
            (Path(d) / "models--other--thing").mkdir()           # 다른 저장소의 폴더는 무시
            self.assertEqual(stt.available_models(download_root=d), ["tiny", "base.en", "small", "large-v3"])

    def test_include_adds_not_downloaded_sizes_without_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_model(d, "tiny")
            self.assertEqual(stt.available_models(include=("tiny", "base", "small"), download_root=d), ["tiny", "base", "small"])

    def test_missing_folder_gives_empty_list(self):
        self.assertEqual(stt.available_models(download_root="no_such_models_dir_for_test"), [])

    def test_unknown_names_go_last_alphabetically(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("zeta", "tiny", "alpha"):
                self.make_model(d, name)
            self.assertEqual(stt.available_models(download_root=d), ["tiny", "alpha", "zeta"])


if __name__ == "__main__":
    unittest.main()
