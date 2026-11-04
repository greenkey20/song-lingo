"""song-lingo 웹 앱의 시작점: 사이드바 메뉴(페이지 3개)를 정하고 선택된 페이지를 실행한다. 검토 문서 16.10.

메뉴: 가사 입력 / 내 노래 / 기록. 각 페이지의 화면 코드는 app/views/*.py, 계산·파일 처리는 프로젝트 루트의 모듈(web_song.py 등)에 있다.
[수업에 없음] Streamlit: 파이썬 파일이 위에서 아래로 실행되면서 화면이 만들어지는 웹 앱 도구(검토 문서 16.4).
`st.navigation`·`st.Page`: 페이지 파일마다 주소와 메뉴 항목을 만들어 주는 Streamlit의 다중 페이지 기능.

실행(프로젝트 루트에서): ~/venvs/song-lingo-app/bin/python -m streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# 프로젝트 모듈(audio.py, stt.py …)은 프로젝트 루트에 있고 이 파일은 app/ 안에 있으므로 루트를 import 경로에 넣는다.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))      # app/ui_practice.py 같은 화면 부품을 import하려고
load_dotenv(ROOT / ".env")                  # OPENAI_API_KEY, (선택) SONGLINGO_SEPARATE_PYTHON을 읽는다. 값은 화면에 보이지 않는다

st.set_page_config(page_title="song lingo", page_icon="🎵", layout="wide")

pages = [
    st.Page("views/lyrics.py", title="가사 입력", icon=":material/edit_note:", default=True),
    st.Page("views/song.py", title="내 노래", icon=":material/library_music:"),
    st.Page("views/history.py", title="기록", icon=":material/show_chart:"),
]
st.navigation(pages).run()
