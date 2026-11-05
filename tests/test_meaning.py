"""meaning.py 단위 테스트(가짜 OpenAI 클라이언트, 네트워크 없음)."""
import tempfile
import unittest
from types import SimpleNamespace

import meaning
import web_practice as wp


def fake_client(answer="아침 햇살이 방을 채워요.\n(두 번째 줄은 버림)"):
    calls = []

    def create(**kw):
        calls.append(kw)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=answer))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))), calls


class Translate(unittest.TestCase):
    def test_translate_caches_and_keeps_first_line(self):
        with tempfile.TemporaryDirectory() as d:
            client, calls = fake_client()
            self.assertEqual(meaning.translate_ko("朝の光", "ja", client=client, cache_dir=d), "아침 햇살이 방을 채워요.")
            self.assertEqual(meaning.translate_ko("朝の光", "ja", client=client, cache_dir=d), "아침 햇살이 방을 채워요.")
            self.assertEqual(len(calls), 1)                                     # 같은 문장은 캐시라 한 번만 부른다
            self.assertEqual(meaning.cached("朝の光", "ja", d), "아침 햇살이 방을 채워요.")
            self.assertIsNone(meaning.cached("朝の光", "en", d))                  # 언어가 다르면 다른 캐시
            self.assertEqual(calls[0]["model"], meaning.MODEL)

    def test_empty_text_and_empty_answer(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                meaning.translate_ko("  ", "ja", client=fake_client()[0], cache_dir=d)
            with self.assertRaises(RuntimeError):
                meaning.translate_ko("x", "ja", client=fake_client("")[0], cache_dir=d)

    def test_lookup_prefers_written_example_then_cache(self):
        with tempfile.TemporaryDirectory() as d:
            ex = {"A": "직접 쓴 뜻"}
            self.assertEqual(meaning.lookup("A", "ja", ex, d), ("직접 쓴 뜻", "직접 작성"))
            self.assertEqual(meaning.lookup("B", "ja", ex, d), (None, None))
            meaning.translate_ko("B", "ja", client=fake_client("번역")[0], cache_dir=d)
            self.assertEqual(meaning.lookup("B", "ja", ex, d), ("번역", "AI 번역"))


class ExampleMeanings(unittest.TestCase):
    def test_every_example_sentence_has_a_meaning(self):
        m = wp.example_meanings()
        for name in ("일본어", "프랑스어", "일본어+영어 섞인 예"):
            for t in wp.EXAMPLE_SETS[name]:
                self.assertTrue(m.get(t), t)
        for t in wp.example_set("영어").splitlines():
            self.assertTrue(m.get(t), t)                                        # 영어는 sentences.csv의 meaning_ko


if __name__ == "__main__":
    unittest.main()
