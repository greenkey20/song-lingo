"""화면 코드가 부르는 설명 키가 app/explain.py의 TEXTS에 모두 있는지, 안 쓰는 글이 남지 않았는지 확인한다(이슈 #56).
explain.py는 streamlit을 import하므로(voice-ai 환경에는 없음) 소스 글자만 읽어 검사한다."""
import ast
import re
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"


def defined_keys():
    tree = ast.parse((APP / "explain.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "TEXTS":
            return {k.value for k in node.value.keys}
    raise AssertionError("TEXTS를 찾지 못함")


def used_keys():
    keys = set()
    for p in list(APP.glob("*.py")) + list((APP / "views").glob("*.py")):
        if p.name != "explain.py":
            keys |= set(re.findall(r'explain\.show\("([a-z_]+)"', p.read_text(encoding="utf-8")))
    return keys


class ExplainKeys(unittest.TestCase):
    def test_every_used_key_has_text(self):
        self.assertEqual(used_keys() - defined_keys(), set())

    def test_no_unused_text(self):
        self.assertEqual(defined_keys() - used_keys(), set())


if __name__ == "__main__":
    unittest.main()
