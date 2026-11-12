"""내 노래의 `lines_section`이 인식된 줄이 하나도 없을 때 죽지 않고 안내만 하는지 Streamlit AppTest로 시험한다(커밋 cc3df41의 회귀 시험).
예전에는 `lines[0]["no"]`에서 IndexError가 났다. song.py는 import하면 페이지 전체가 실행되므로, **함수 하나만 소스에서 뽑아** 작은 스크립트에서 부른다.
streamlit이 있는 앱 전용 환경에서만 돈다: ~/venvs/song-lingo-app/bin/python -m unittest tests.test_song_empty_lines_apptest (voice-ai에서는 건너뜀)."""
import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except Exception:                                    # voice-ai 환경에는 streamlit이 없다
    AppTest = None

SONG = str(Path(__file__).resolve().parent.parent / "app" / "views" / "song.py")

SCRIPT = f'''
import ast
import streamlit as st

tree = ast.parse(open({SONG!r}, encoding="utf-8").read())
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "lines_section")
ns = {{"st": st}}
exec(compile(ast.Module([fn], []), {SONG!r}, "exec"), ns)
st.session_state.setdefault("gen", 0)
ns["lines_section"](None, {{"lines": []}}, 20, None, None, True)
st.write("끝까지 실행됨")
'''


class EmptyLines(unittest.TestCase):
    @unittest.skipIf(AppTest is None, "streamlit이 없는 환경이라 건너뜁니다")
    def test_no_lines_shows_warning_instead_of_crashing(self):
        at = AppTest.from_string(SCRIPT, default_timeout=30).run()
        self.assertEqual(len(at.exception), 0, [e.value for e in at.exception])           # IndexError가 없어야 한다
        self.assertEqual(len(at.warning), 1)
        self.assertIn("인식된 가사가 없어요", at.warning[0].value)
        self.assertEqual(len(at.subheader), 0)                                             # 줄 확인·수정 화면은 그리지 않는다

    def test_source_has_guard_before_first_line_access(self):
        """함수 맨 앞의 빈 목록 검사가 `lines[0]` 사용보다 먼저 있어야 한다(AppTest를 못 돌리는 환경에서도 도는 간단한 점검)."""
        src = Path(SONG).read_text(encoding="utf-8")
        body = src[src.index("def lines_section"):]
        self.assertLess(body.index("if not lines"), body.index("lines[0]"))


if __name__ == "__main__":
    unittest.main()
