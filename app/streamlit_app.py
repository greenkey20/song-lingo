"""song-lingo 웹 앱의 시작점: 사이드바 메뉴(페이지 3개)를 정하고 선택된 페이지를 실행한다. 검토 문서 16.10.

메뉴: 내 문장 / 내 노래 / 기록(11-05에 "가사 입력"에서 "내 문장"으로 이름을 바꿈). 각 페이지의 화면 코드는 app/views/*.py, 계산·파일 처리는 프로젝트 루트의 모듈(web_song.py 등)에 있다.
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

# 주소: 내 문장 /text, 내 노래 /song, 기록 /history. Streamlit은 **기본 페이지의 주소를 항상 "/"로 고정**하고 url_path를 무시하므로,
# 주소가 "/"일 때는 메뉴에 보이지 않는 기본 페이지가 내 문장으로 보낸다(visibility="hidden", 이슈 #50 후속).
text_page = st.Page("views/lyrics.py", title="내 문장", icon=":material/edit_note:", url_path="text")
song_page = st.Page("views/song.py", title="내 노래", icon=":material/library_music:", url_path="song")
history_page = st.Page("views/history.py", title="기록", icon=":material/show_chart:", url_path="history")


def _home():
    st.switch_page(text_page)


home_page = st.Page(_home, title="시작", default=True, visibility="hidden")

# 로고(A안 "Beam": 빔 안의 여러 언어 + sOng·lingO의 O가 음표 머리). 원본은 시안 PNG에서 잘라 배경을 투명하게 만든 app/assets/logo.png
st.logo(str(Path(__file__).resolve().parent / "assets" / "logo.png"), size="large")
# st.logo의 size는 small(1.25rem)·medium(1.5rem)·large(2rem) 높이뿐이라 large(약 32px)가 한계여서 사이드바 너비(기본 약 21rem)의 절반도 안 된다.
# 로고를 더 키우려면 CSS로 높이를 덮어써야 한다(아래: 5.5rem ≈ 88px, 가로 세로 비율 742:287이라 너비 약 228px ≈ 사이드바의 2/3).
# **Streamlit 내부 요소 이름(data-testid)에 기대므로 Streamlit을 올리면 깨질 수 있다.** 그때는 이 블록만 지우면 기본 크기로 돌아간다.
LOGO_HEIGHT = "5.5rem"
st.html(f"""<style>
[data-testid="stSidebarHeader"] {{ height: auto; padding: 1rem 1rem 0.5rem 1rem; }}
[data-testid="stLogo"] {{ height: {LOGO_HEIGHT} !important; max-width: 100%; width: auto; }}
</style>""")
st.navigation([home_page, text_page, song_page, history_page]).run()
