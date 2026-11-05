"""meaning.py 단위 테스트(가짜 OpenAI 클라이언트, 네트워크 없음)."""
import json
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


NOTES = {"words": [{"word": "bright", "ipa": "/braɪt/", "meaning": "밝은"}], "expressions": [{"expression": "light up", "meaning": "환하게 하다"}],
         "grammar": "현재진행형은 be + -ing 입니다.", "examples": [{"sentence": "The room is bright.", "meaning": "방이 밝아요."},
                                                                    {"sentence": "Light up the room.", "meaning": "방을 밝혀 줘."},
                                                                    {"sentence": "세 번째", "meaning": "버려짐"}]}


class Notes(unittest.TestCase):
    """표현 설명(이슈 #58): 가짜 클라이언트로 JSON 정리·캐시·오류를 확인한다(예문은 직접 쓴 문장)."""

    def test_explain_cleans_caches_and_limits_examples(self):
        with tempfile.TemporaryDirectory() as d:
            client, calls = fake_client(json.dumps(NOTES, ensure_ascii=False))
            n = meaning.explain_sentence("The room is bright.", "en", client=client, cache_dir=d)
            self.assertEqual(len(n["examples"]), 2)                            # 예문은 최대 2개
            self.assertEqual(calls[0]["response_format"], {"type": "json_object"})
            meaning.explain_sentence("The room is bright.", "en", client=client, cache_dir=d)
            self.assertEqual(len(calls), 1)                                   # 캐시 적중이면 다시 부르지 않는다
            self.assertEqual(meaning.cached_notes("The room is bright.", "en", d), n)

    def test_bad_json_and_empty_and_blank_text(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                meaning.explain_sentence("x", "en", client=fake_client("not json")[0], cache_dir=d)
            with self.assertRaises(ValueError):
                meaning.explain_sentence("x", "en", client=fake_client("{}")[0], cache_dir=d)
            with self.assertRaises(ValueError):
                meaning.explain_sentence("  ", "en", client=fake_client(json.dumps(NOTES))[0], cache_dir=d)
            self.assertIsNone(meaning.cached_notes("x", "en", d))             # 실패한 응답은 캐시되지 않는다

    def test_broken_cache_is_ignored_and_markdown_has_sections(self):
        with tempfile.TemporaryDirectory() as d:
            (__import__("pathlib").Path(d) / f"{meaning._key('x', 'en')}.notes2.json").write_text("{broken", encoding="utf-8")
            self.assertIsNone(meaning.cached_notes("x", "en", d))
        md = meaning.notes_markdown(meaning._clean_notes(NOTES))
        for head in ("**단어**", "**표현·숙어**", "**문법 포인트**", "**예문**"):
            self.assertIn(head, md)
        self.assertIn("**bright** /braɪt/ — 밝은", md)                          # 발음 기호는 슬래시 한 겹
        self.assertNotIn("<", md)                                            # HTML을 만들지 않는다


if __name__ == "__main__":
    unittest.main()
