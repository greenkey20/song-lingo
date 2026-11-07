"""meaning.py 단위 테스트(가짜 OpenAI 클라이언트, 네트워크 없음)."""
import json
import tempfile
import time
import unittest
from types import SimpleNamespace

import meaning
import web_practice as wp
from tests.fake_store import FakeStore, install


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


class SharedDb(unittest.TestCase):
    """공유 DB 캐시(이슈 #69): 가짜 저장소로 DB → 파일 → OpenAI 순서, 파일→DB 채우기, DB 장애 때의 동작을 확인한다."""

    def setUp(self):
        self.store = FakeStore()
        self.restore = install(self.store)
        meaning.enable_db(True)

    def tearDown(self):
        meaning.enable_db(False)                                    # 다른 테스트에 영향이 없게(모듈 전역)
        self.restore()

    def test_new_translation_goes_to_db_and_is_found_without_the_file_or_api(self):
        with tempfile.TemporaryDirectory() as d:
            client, calls = fake_client()
            meaning.translate_ko("朝の光", "ja", client=client, cache_dir=d)
            key = meaning._key("朝の光", "ja")
            self.assertEqual(self.store.meanings[(key, "translation_ko", 1)], "아침 햇살이 방을 채워요.")
        # 파일 캐시가 없어도(다른 서버·폴더) DB에서 찾는다: OpenAI를 다시 부르지 않는다
        with tempfile.TemporaryDirectory() as empty:
            client2, calls2 = fake_client("호출되면 안 됨")
            self.assertEqual(meaning.translate_ko("朝の光", "ja", client=client2, cache_dir=empty), "아침 햇살이 방을 채워요.")
            self.assertEqual(calls2, [])
            self.assertEqual(meaning.lookup("朝の光", "ja", cache_dir=empty), ("아침 햇살이 방을 채워요.", "AI 번역"))

    def test_file_only_entries_are_copied_to_db_on_read(self):
        with tempfile.TemporaryDirectory() as d:
            (__import__("pathlib").Path(d) / f"{meaning._key('Hello', 'en')}.txt").write_text("안녕", encoding="utf-8")
            self.assertEqual(meaning.cached("Hello", "en", d), "안녕")
        self.assertEqual(self.store.meanings[(meaning._key("Hello", "en"), "translation_ko", 1)], "안녕")

    def test_notes_roundtrip_through_db(self):
        with tempfile.TemporaryDirectory() as d:
            client, calls = fake_client(json.dumps(NOTES, ensure_ascii=False))
            n = meaning.explain_sentence("The room is bright.", "en", client=client, cache_dir=d)
        self.assertIn((meaning._key("The room is bright.", "en"), "notes", 2), self.store.meanings)
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(meaning.cached_notes("The room is bright.", "en", empty), n)     # 파일이 없어도 DB에서

    def test_broken_db_content_is_ignored(self):
        key = meaning._key("x", "en")
        self.store.meanings[(key, "notes", 2)] = {"words": "not a list"}
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(meaning.cached_notes("x", "en", d))

    def test_db_failure_falls_back_to_files_and_skips_db_for_a_while(self):
        def boom(*a, **k):
            raise RuntimeError("DB down")
        self.store.connect = boom
        install(self.store)
        with tempfile.TemporaryDirectory() as d:
            client, calls = fake_client()
            self.assertEqual(meaning.translate_ko("朝の光", "ja", client=client, cache_dir=d), "아침 햇살이 방을 채워요.")   # 번역은 멈추지 않는다
            self.assertEqual(meaning.cached("朝の光", "ja", d), "아침 햇살이 방을 채워요.")                                  # 파일 캐시
            self.assertGreater(meaning._DB["down_until"], time.monotonic())                                              # 잠시 DB를 건너뜀

    def test_db_is_off_by_default_so_unit_tests_only_use_files(self):
        meaning.enable_db(False)
        with tempfile.TemporaryDirectory() as d:
            meaning.translate_ko("朝の光", "ja", client=fake_client()[0], cache_dir=d)
        self.assertEqual(self.store.meanings, {})

    def test_import_cache_to_db_counts_and_is_idempotent(self):
        import storage
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            Path(d, "aaaa111122223333.txt").write_text("뜻", encoding="utf-8")
            Path(d, "bbbb111122223333.txt").write_text("  ", encoding="utf-8")                  # 빈 파일
            Path(d, "cccc111122223333.notes2.json").write_text(json.dumps(NOTES, ensure_ascii=False), encoding="utf-8")
            Path(d, "dddd111122223333.notes2.json").write_text("{broken", encoding="utf-8")
            first = meaning.import_cache_to_db(self.store, d)
            self.assertEqual(first, {"translation_ko": 1, "notes": 1, "skipped": 0, "bad": 2})
            self.assertEqual(meaning.import_cache_to_db(self.store, d), {"translation_ko": 0, "notes": 0, "skipped": 2, "bad": 2})   # 다시 해도 중복 없음
        self.assertEqual(self.store.meanings[("aaaa111122223333", "translation_ko", 1)], "뜻")


if __name__ == "__main__":
    unittest.main()
