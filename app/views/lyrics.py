"""가사 입력 페이지: 가사를 직접 쓰거나 붙여 넣고, 줄을 골라 표준 발음을 듣고, 따라읽기·받아쓰기·채점을 한다. 검토 문서 16.10.

계산은 web_practice.py·practice.py가 하고 이 파일은 화면 배치만 한다. 가사는 세션에만 있고 저장하지 않는다.
표준 발음(OpenAI TTS)은 **버튼을 눌러야** 만들어진다(새 문장은 과금, 예시 문장·이미 만든 문장은 캐시라 무료).
"""
import streamlit as st

import web_practice as wp
from ui_practice import practice_panel

st.title("가사 입력")
st.caption("직접 쓰거나 붙여 넣은 가사를 한 줄씩 연습해요. 가사는 이 화면에만 있고 저장하지 않아요.")

if "lyrics" not in st.session_state:
    st.session_state["lyrics"] = ""
c1, c2 = st.columns([1, 4], vertical_alignment="center")
if c1.button("예시 문장 불러오기"):
    st.session_state["lyrics"] = wp.example_lyrics()
c2.caption("직접 쓴 예시 문장 4개를 넣어요(표준 발음이 이미 있어 과금되지 않아요).")
text = st.text_area("가사", key="lyrics", height=140, placeholder="연습할 영어 가사를 한 줄에 하나씩 적거나 붙여 넣으세요.")

lines = wp.split_lyrics(text)
if not lines:
    st.stop()

no = st.segmented_control("연습할 줄", list(range(1, len(lines) + 1)), default=1, key="lyr_line",
                          format_func=lambda n: f"{n}번째 줄")
line = lines[(no or 1) - 1]

# ---------- 듣기 ----------
st.subheader("듣기")
path, cached = wp.tts_target(line)
if cached:
    st.audio(path, format="audio/wav")
    st.caption("표준 발음(TTS)이에요. 또박또박 읽는 기계 음성이라 실제 노래·대화와 다를 수 있어요.")
else:
    st.caption("이 줄의 표준 발음은 아직 없어요. 만들면 OpenAI TTS를 한 번 불러서 **과금**돼요(같은 문장은 다시 만들지 않아요).")
    if st.button("표준 발음 만들기", key=f"mk_{no}"):
        with st.spinner("음성을 만드는 중…"):
            try:
                wp.make_tts(line)
            except Exception as e:
                st.error(f"만들지 못했어요 ({type(e).__name__}: {e})")
        st.rerun()

st.subheader("연습")
practice_panel(line, key=f"lyr_{no}_{abs(hash(line)) % 10**8}", tts_path=path if cached else None)
