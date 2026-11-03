"""song-lingo 웹 앱의 시작점(빈 앱, 이슈 #36). 화면은 이후 단계(UI 골격)에서 채운다.

지금은 두 가지만 한다: ① 앱 전용 환경에서 프로젝트 모듈이 import되는지 확인 ② 환경 정보(파이썬·패키지 버전) 표시.
[수업에 없음] Streamlit: 파이썬 파일 하나가 위에서 아래로 실행되면서 화면이 만들어지는 웹 앱 도구(검토 문서 16.4).

실행(프로젝트 루트에서): ~/venvs/song-lingo-app/bin/python -m streamlit run app/streamlit_app.py
"""
import importlib.metadata as md
import platform
import sys
from pathlib import Path

import streamlit as st

# 프로젝트 모듈(audio.py, stt.py …)은 프로젝트 루트에 있고 이 파일은 app/ 안에 있으므로 루트를 import 경로에 넣는다.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODULES = ["audio", "stt", "tts", "quality", "scoring", "report", "practice", "align", "visualisation", "theme"]
PACKAGES = ["streamlit", "numpy", "scipy", "matplotlib", "faster-whisper", "av", "openai", "python-dotenv"]


def check_imports():
    """프로젝트 모듈을 하나씩 import해 {이름: 오류 문자열 또는 None}을 돌려준다(하나가 실패해도 나머지는 계속)."""
    import importlib
    out = {}
    for name in MODULES:
        try:
            importlib.import_module(name)
            out[name] = None
        except Exception as e:      # 환경 점검용이므로 어떤 오류든 화면에 보여 준다
            out[name] = f"{type(e).__name__}: {e}"
    return out


st.set_page_config(page_title="song-lingo", page_icon="🎵")
st.title("song-lingo")
st.caption("외국어 노래 문장 연습 도우미 — 앱 환경 점검 화면(빈 앱)")

st.subheader("프로젝트 모듈 import")
results = check_imports()
for name, err in results.items():
    st.write(("✅ " if err is None else "❌ ") + f"`{name}`" + ("" if err is None else f" — {err}"))

st.subheader("환경")
st.write(f"Python {platform.python_version()} · `{Path(sys.executable).parent.parent.name}`")   # 환경 폴더 이름만(전체 경로에는 사용자 이름이 들어감)
versions = {}
for pkg in PACKAGES:
    try:
        versions[pkg] = md.version(pkg)
    except md.PackageNotFoundError:
        versions[pkg] = "설치 안 됨"
st.table({"패키지": list(versions), "버전": list(versions.values())})
