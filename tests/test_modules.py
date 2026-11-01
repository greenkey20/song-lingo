"""tts.py·stt.py의 API·모델 없이 확인할 수 있는 부분(조회, 파일 찾기, 캐시 적중)."""
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
