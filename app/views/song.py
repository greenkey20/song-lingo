"""내 노래 페이지: 곡 업로드 → 파형에서 구간 고르기 → 가사 인식 → 줄 확인·수정 → 줄마다 듣기. 검토 문서 16.10.

계산과 파일 처리는 web_song.py가 하고 이 파일은 화면(위젯 배치)만 한다. 곡은 세션 작업 폴더(임시)에만 저장된다.
[수업에 없음] `st.session_state`: 화면이 다시 실행돼도 값을 기억하는 저장소. `st.cache_data`: 같은 입력이면 결과를 다시 계산하지 않는 캐시.
`st.audio(start_time, end_time)`: 파일 하나에서 일부 구간만 재생(줄마다 파일을 따로 만들지 않아도 됨).
"""
import hashlib

import streamlit as st

import separate
import theme
import visualisation
import web_song
from ui_practice import practice_panel

st.title("내 노래")
st.caption("올린 곡은 이 세션의 임시 폴더에만 저장돼요(저장소에는 올라가지 않아요). 1시간이 지나거나 '곡 지우기'를 누르면 지워져요.")


@st.cache_data(show_spinner="곡을 읽는 중…", max_entries=2)
def overview(data: bytes, digest: str):
    """업로드한 곡을 한 번만 디코딩해 파형 윤곽과 길이를 돌려준다(digest는 캐시 열쇠일 뿐)."""
    return web_song.song_overview(data)


def reset_song():
    """작업 폴더를 지우고 이 페이지의 상태를 비운다."""
    ws = st.session_state.pop("ws", None)
    if ws:
        web_song.delete_workspace(ws)
    for k in ("song_path", "song_digest", "cut", "gen"):
        st.session_state.pop(k, None)


if "swept" not in st.session_state:                      # 세션당 한 번, 오래된 작업 폴더 정리
    web_song.cleanup_old_workspaces()
    st.session_state["swept"] = True

# ---------- 1. 업로드 ----------
uploaded = st.file_uploader("음악 파일", type=["mp3", "wav", "m4a", "flac", "ogg", "wma"], key="uploader")
if uploaded is None:
    if "ws" in st.session_state:
        reset_song()                                      # 업로드 칸의 X로 지우면 폴더도 지운다
    st.stop()

data = uploaded.getvalue()
digest = hashlib.sha1(data).hexdigest()
if st.session_state.get("song_digest") != digest:
    reset_song()
    ws = web_song.new_workspace()
    st.session_state.update(ws=ws, song_digest=digest, song_path=web_song.save_upload(ws, uploaded.name, data), gen=0)
ws = st.session_state["ws"]

try:
    ov = overview(data, digest)
except Exception as e:                                    # 읽을 수 없는 파일: 가사는 없으므로 오류 이름만 보여 준다
    st.error(f"이 파일을 읽을 수 없어요 ({type(e).__name__}). 다른 파일로 해 보세요.")
    st.stop()

head, clear = st.columns([5, 1], vertical_alignment="center")
head.write(f"길이 {web_song.format_hms(ov['seconds'])}")
if clear.button("곡 지우기", key="clear"):
    reset_song()
    st.rerun()

# ---------- 2. 구간 고르기 ----------
st.subheader("구간 고르기")
duration = st.segmented_control("구간 길이", [f"{d}초" for d in web_song.DURATIONS], default="15초", key="dur")
duration = int((duration or "15초").rstrip("초"))
max_start = int(ov["seconds"]) - duration
if max_start < 1:
    st.warning("곡이 선택한 길이보다 짧아요. 더 짧은 길이를 고르세요.")
    st.stop()
start = st.slider("시작 위치(초)", 0, max_start, min(60, max_start), key="start")
fig = visualisation.plot_song_selection(ov["mins"], ov["maxs"], ov["seconds"], start, duration)
st.pyplot(fig, clear_figure=True)
st.markdown(f"**선택한 구간** `{web_song.clip_range_label(start, duration)}` · {duration}초")
with st.expander("파형은 무엇인가요? · 수업과의 연결"):
    st.markdown(
        "소리는 **1초에 수만 번 잰 소리 세기의 숫자 나열**이에요(수업 01·02: 샘플링 레이트, 진폭). 곡 한 곡은 수백만 개라 하나하나 그릴 수 없어서, "
        "**600칸으로 나눠 칸마다 가장 작은 값과 가장 큰 값**만 이어 그린 윤곽이에요. 두꺼운 곳이 소리가 큰 구간이에요. "
        "선택한 구간은 02 실습 7처럼 `axvspan`으로 띠를 칠했어요. 구간을 자르고 인식하기 전에 모델이 읽는 것은 이 숫자들이고, "
        "음성 인식(Whisper)은 안에서 16 kHz 모노로 바꿔 읽어요(수업 07).")

if st.button("이 구간으로 정하기", type="primary", key="cut_btn"):
    with st.spinner("구간을 자르는 중…"):
        web_song.cut(ws, st.session_state["song_path"], start, duration)
    st.session_state["cut"] = (start, duration)
    st.session_state["gen"] += 1

cut = st.session_state.get("cut")
if cut is None:
    st.stop()
if cut != (start, duration):
    st.caption(f"지금 정해 둔 구간은 {web_song.clip_range_label(*cut)}예요. 위에서 바꿨다면 '이 구간으로 정하기'를 다시 누르세요.")
mix_path, voc_path = separate.clip_paths(web_song.CLIP_ID, web_song.work_dir(ws))
clip_seconds = float(cut[1])

# ---------- 3. 가사 인식 ----------
st.subheader("가사 인식")
doc = web_song.load_doc(ws)
if st.button("가사 인식하기" if doc is None else "다시 인식하기(고친 가사는 사라져요)", key="recog_btn"):
    with st.spinner("인식하는 중… (medium 모델, CPU에서 20초 구간에 약 20~60초, 처음에는 모델을 읽느라 더 걸려요)"):
        try:
            web_song.recognize_lines(ws)
            st.session_state["gen"] += 1
        except Exception as e:
            st.error(f"인식하지 못했어요 ({type(e).__name__}: {e})")
    st.rerun()
if doc is None:
    st.stop()

# ---------- 4. 줄 확인·수정 ----------
lines = doc["lines"]
gen = st.session_state["gen"]
st.subheader("줄 확인·수정")
st.caption("인식 결과는 틀릴 수 있어요. 소리를 들으면서 가사를 고치고 '이 가사로 확정'을 누르세요. 확정한 줄만 연습에 쓰여요.")
mark = {"confirmed": "✓", "dropped": "✕", "candidate": "·"}
no = st.segmented_control("줄", [l["no"] for l in lines], default=lines[0]["no"], key=f"line_{gen}",
                          format_func=lambda n: f"{n}줄 {mark[next(l['status'] for l in lines if l['no'] == n)]}")
ln = next(l for l in lines if l["no"] == (no or lines[0]["no"]))
if doc["lines"] and any(l["low_confidence"] for l in lines):
    st.caption("⚠ 이 구간은 인식이 불안정할 수 있어요(신뢰 지표가 낮음). 특히 꼼꼼히 들어 보세요.")
if ln["too_long"]:
    st.caption("이 줄은 길어요(6초·14단어 초과). 나눠서 연습하고 싶다면 가사를 줄이거나 빼세요.")

text = st.text_input("가사", value=ln["text"], key=f"txt_{gen}_{ln['no']}")
c1, c2, c3 = st.columns([2, 1, 3], vertical_alignment="center")
if c1.button("이 가사로 확정", type="primary", key=f"ok_{gen}_{ln['no']}"):
    if text.strip():
        web_song.confirm_line(ws, ln["no"], text)
        st.rerun()
    else:
        st.warning("가사가 비어 있어요. 빼려면 '연습에서 빼기'를 누르세요.")
if c2.button("연습에서 빼기", key=f"drop_{gen}_{ln['no']}"):
    web_song.drop_line(ws, ln["no"])
    st.rerun()
c3.caption({"confirmed": "확정됨", "dropped": "연습에서 뺌", "candidate": "아직 확인 안 함"}[ln["status"]]
           + (" · 고쳤어요" if ln["edited"] else ""))

# ---------- 5. 듣기 ----------
st.subheader("듣기")
sources = ["원본 음악", "보컬만", "표준 발음"]
src = st.segmented_control("들을 소리", sources, default="원본 음악", key="listen_src")
a, b = web_song.line_range(ln, clip_seconds)
if src == "보컬만":
    if voc_path.exists():
        st.audio(voc_path, format="audio/wav", start_time=a, end_time=b)
        st.caption("반주를 뺀 소리예요. 원어민이 실제로 어떻게 발음하는지 들어 보세요.")
    elif st.button("보컬만 만들기 (CPU에서 약 1~2분)", key="voc_btn"):
        with st.spinner("보컬을 분리하는 중…"):
            try:
                web_song.make_vocals(ws)
            except Exception as e:
                st.error(f"분리하지 못했어요 ({type(e).__name__}: {e})")
        st.rerun()
    else:
        st.caption("보컬만 듣기는 구간마다 한 번 만들어야 해요.")
elif src == "표준 발음":
    if ln.get("tts_path") and ln.get("tts_text") == ln["text"]:
        st.audio(ln["tts_path"], format="audio/wav")
        st.caption("TTS가 읽는 또박또박한 발음이에요(기계 음성).")
    else:
        plan = web_song.tts_summary(ws)
        if plan["n_lines"] == 0:
            st.caption("먼저 줄을 확정하세요. 확정한 줄만 표준 발음을 만들어요.")
        else:
            st.caption(f"확정한 {plan['n_lines']}줄 중 새로 만들 것 {plan['n_api_calls']}개({plan['chars']}글자, OpenAI TTS **과금**), 이미 있는 것 {plan['n_cached']}개.")
            if st.button("표준 발음 만들기", key="tts_btn"):
                with st.spinner("음성을 만드는 중…"):
                    try:
                        web_song.make_tts(ws)
                    except Exception as e:
                        st.error(f"만들지 못했어요 ({type(e).__name__}: {e})")
                st.rerun()
else:
    st.audio(mix_path, format="audio/wav", start_time=a, end_time=b)
    st.caption("원곡의 이 줄 부분이에요(앞뒤 0.1초 여유).")

# ---------- 6. 연습 ----------
st.subheader("연습")
if ln["status"] != "confirmed":
    st.caption("가사를 확인하고 '이 가사로 확정'을 누르면 이 줄을 연습할 수 있어요.")
else:
    tts_ok = ln.get("tts_path") and ln.get("tts_text") == ln["text"]
    practice_panel(ln["text"], key=f"song_{gen}_{ln['no']}", tts_path=ln["tts_path"] if tts_ok else None, source="song")
