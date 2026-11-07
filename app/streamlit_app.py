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

st.set_page_config(page_title="song lingo", page_icon=str(Path(__file__).resolve().parent / "assets" / "icon.png"), layout="wide")   # 브라우저 탭 아이콘(정사각형 아이콘 PNG)

# 아이폰 "홈 화면에 추가" 아이콘: iOS는 <head>의 apple-touch-icon 링크를 읽는데 Streamlit은 이 태그를 넣어 주지 않는다. 그래서 JS로 head에 넣는다
# (파일은 app/static/, 서버 설정 enableStaticServing). iOS가 추가 순간의 DOM을 읽는지는 아이폰에서 확인해야 한다 [미확인]. 이미 추가한 아이콘은 지우고 다시 추가해야 바뀐다.
st.html("""<script>
if (!document.querySelector('link[rel="apple-touch-icon"]')) {
  var l = document.createElement('link'); l.rel = 'apple-touch-icon'; l.href = '/app/static/apple-touch-icon.png';
  document.head.appendChild(l);
}
</script>""", unsafe_allow_javascript=True)

# 접근 제한과 사용자 확인(이슈 #52): 아이디·비밀번호 로그인(가입에는 초대 코드 = SONGLINGO_PASSWORD), 로그인 유지, 게스트. 저장소(DB) 설정이 없으면
# 예전처럼 비밀번호만 묻는다. 이 파일은 사용자가 어느 주소로 들어와도 맨 먼저 실행되므로 run()이 st.stop()으로 여기서 멈추면 모든 페이지가 가려진다.
# 판단은 account.py·auth.py·access.py, 저장은 storage.py, 화면은 app/auth_gate.py.
import auth_gate  # noqa: E402  (sys.path 설정 뒤에 import)
auth_gate.run()

# 주소: 내 문장 /text, 내 노래 /song, 기록 /history. Streamlit은 **기본 페이지의 주소를 항상 "/"로 고정**하고 url_path를 무시하므로,
# 주소가 "/"일 때는 메뉴에 보이지 않는 기본 페이지가 내 문장으로 보낸다(visibility="hidden", 이슈 #50 후속).
text_page = st.Page("views/lyrics.py", title="내 문장", icon=":material/edit_note:", url_path="text")
song_page = st.Page("views/song.py", title="내 노래", icon=":material/library_music:", url_path="song")
history_page = st.Page("views/history.py", title="기록", icon=":material/show_chart:", url_path="history")


def _home():
    st.switch_page(text_page)


home_page = st.Page(_home, title="시작", default=True, visibility="hidden")

# 로고(A안 "Beam": 빔 안의 여러 언어 + sOng·lingO의 O가 음표 머리). 벡터 SVG(글자는 윤곽선, 배경 투명)라 크게 키워도 선명하다.
# icon.svg는 정사각형 아이콘(파비콘·슬라이드용), logo.png·icon.png는 같은 그림의 PNG 보관본이다.
_ASSETS = Path(__file__).resolve().parent / "assets"
st.logo(str(_ASSETS / "logo.svg"), icon_image=str(_ASSETS / "icon.svg"), size="large")
# st.logo의 size는 small(1.25rem)·medium(1.5rem)·large(2rem) 높이뿐이라 large(약 32px)가 한계여서 사이드바 너비(기본 약 21rem)의 절반도 안 된다.
# 로고를 더 키우려면 CSS로 높이를 덮어써야 한다(아래: 5.5rem ≈ 88px, 가로:세로 비율 약 2.7:1이라 너비 약 237px ≈ 사이드바의 2/3).
# **사이드바 로고의 data-testid는 stLogo가 아니라 stSidebarLogo다(처음에 stLogo로 써서 CSS가 적용되지 않아 계속 작았음, 11-06). Streamlit 내부 요소 이름에 기대므로 Streamlit을 올리면 깨질 수 있다.** 그때는 이 블록만 지우면 기본 크기로 돌아간다.
LOGO_HEIGHT = "5.5rem"
st.html(f"""<style>
[data-testid="stSidebarHeader"] {{ height: auto; padding: 1rem 1rem 0.5rem 1rem; }}
[data-testid="stSidebarLogo"], [data-testid="stSidebar"] img.stLogo {{ height: {LOGO_HEIGHT} !important; max-width: 100%; width: auto; }}
</style>""")
import explain  # noqa: E402  (sys.path 설정 뒤에 import)
st.html(explain.CSS)      # "어떻게 동작하나요?" 상자를 라임색으로(부가 요소 구분)
auth_gate.sidebar()      # 사이드바 아래쪽: 누구로 쓰는지·저장 켜기/끄기·로그아웃·계정 삭제
st.navigation([home_page, text_page, song_page, history_page]).run()
