"""내 노래 페이지: 곡 업로드 → 파형에서 구간 고르기 → **언어 확인** → 가사 인식 → (선택) 줄 확인·수정 → 줄마다 듣기·연습. 검토 문서 16.10·16.14.
인식된 가사는 **확정 없이 바로 연습**할 수 있다(자동 변환 + 선택적 검수, 방식 C: 검토 문서 16.14). 고치면 저장하고, 연습에서 뺄 줄만 뺀다.

계산과 파일 처리는 web_song.py가 하고 이 파일은 화면(위젯 배치)만 한다. 곡은 세션 작업 폴더(임시)에만 저장된다.
[수업에 없음] `st.session_state`: 화면이 다시 실행돼도 값을 기억하는 저장소. `st.cache_data`: 같은 입력이면 결과를 다시 계산하지 않는 캐시.
`st.audio(start_time, end_time)`: 파일 하나에서 일부 구간만 재생(줄마다 파일을 따로 만들지 않아도 됨).
"""
import hashlib

import streamlit as st

import languages
import separate
import theme
import visualisation
import web_practice as wp
import web_song
import explain
from ui_practice import meaning_box, notes_box, practice_panel

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

# ---------- 1. 입력: 음원 파일 업로드 또는 주변 음악 녹음 (이슈 #51) ----------
# 두 입력은 (이름, bytes) 하나로 합쳐 아래의 같은 흐름(작업 폴더 → 구간 → 언어 확인 → 인식 → 연습)에 넣는다.
# 탭 대신 segmented_control을 쓴다: 한 번에 한 입력만 그려서 st.stop()으로 흐름을 끊어도 다른 쪽 코드가 같이 실행되지 않는다.
MODE_FILE, MODE_REC = "음원 파일 업로드", "주변 음악 녹음"
mode = st.segmented_control("입력 방식", [MODE_FILE, MODE_REC], default=MODE_FILE, key="song_mode") or MODE_FILE
if st.session_state.get("song_mode_prev", mode) != mode and "ws" in st.session_state:
    reset_song()                                          # 입력 방식을 바꾸면 이전 입력의 작업 폴더를 지운다
st.session_state["song_mode_prev"] = mode
is_rec = mode == MODE_REC
explain.show("song_input")

if is_rec:
    st.caption("스피커로 노래를 틀어 두고, 마이크가 그 소리를 듣도록 녹음하세요(10~30초 정도가 좋아요). "
               "녹음이 길수록 인식에 오래 걸려요. 마이크는 이 주소(localhost)나 HTTPS에서만 동작해요.")
    rec = st.audio_input("눌러서 녹음 시작, 다시 눌러서 끝내기", key="ambient_rec")
    source = None if rec is None else ("recording.wav", rec.getvalue())
else:
    uploaded = st.file_uploader("음악 파일", type=["mp3", "wav", "m4a", "flac", "ogg", "wma"], key="uploader")
    source = None if uploaded is None else (uploaded.name, uploaded.getvalue())
if source is None:
    if "ws" in st.session_state:
        reset_song()                                      # 업로드 칸의 X(또는 녹음 지우기)로 비우면 폴더도 지운다
    st.stop()

src_name, data = source
digest = hashlib.sha1(data).hexdigest()
if st.session_state.get("song_digest") != digest:
    reset_song()
    ws = web_song.new_workspace()
    st.session_state.update(ws=ws, song_digest=digest, song_path=web_song.save_upload(ws, src_name, data), gen=0)
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

if is_rec:
    # 주변 음악 녹음은 **녹음 전체를 구간으로** 쓴다(슬라이더·파형 없음). 상태 점검은 안내일 뿐이라 경고가 있어도 계속할 수 있다.
    try:
        info = web_song.recording_info(data)
    except Exception as e:
        st.error(f"녹음을 읽을 수 없어요 ({type(e).__name__}). 다시 녹음해 보세요.")
        st.stop()
    for w in info["warnings"]:
        st.warning(w)
    if info["long"]:
        st.info(f"{web_song.format_hms(info['seconds'])} 길이예요. 길수록 언어 확인·인식이 오래 걸려요(제한은 없어요).")
    if st.button("이 녹음으로 정하기 (들어 보기)", type="primary", key="cut_rec_btn"):
        with st.spinner("녹음을 준비하는 중…"):
            web_song.cut(ws, st.session_state["song_path"], 0.0, ov["seconds"])
        st.session_state["cut"] = (0.0, ov["seconds"])
        st.session_state["gen"] += 1
    start, duration = 0.0, ov["seconds"]
else:
    # ---------- 2. 구간 고르기 ----------
    st.subheader("구간 고르기")
    explain.show("song_cut")
    duration = st.segmented_control("구간 길이", [f"{d}초" for d in web_song.DURATIONS], default="15초", key="dur")
    duration = int((duration or "15초").rstrip("초"))
    total = int(ov["seconds"])
    if total < duration + 1:
        st.warning("곡이 선택한 길이보다 짧아요. 더 짧은 길이를 고르세요.")
        st.stop()
    # 슬라이더의 범위를 **곡 전체(0~총 길이)** 로 둔다: 파형의 가로축도 곡 전체라서 슬라이더 위치와 파형 위치가 맞는다(이전에는 0~(총 길이−구간 길이)여서 어긋났다).
    # 시작 위치가 곡 끝에서 구간 길이만큼 남기지 못하면 곡 끝에 맞춘다.
    start_raw = st.slider("시작 위치(초)", 0, total, min(60, total - duration), key="start")
    start = min(start_raw, total - duration)
    if start != start_raw:
        st.caption(f"곡 끝을 넘지 않도록 시작 위치를 {start}초로 맞췄어요.")
    fig = visualisation.plot_song_selection(ov["mins"], ov["maxs"], ov["seconds"], start, duration)
    st.pyplot(fig, clear_figure=True)
    st.markdown(f"**선택한 구간** `{web_song.clip_range_label(start, duration)}` · {duration}초")
    # 미리 듣기: 올린 원본 파일을 그대로 브라우저 플레이어에 주고 재생 구간만 [시작, 시작+길이]로 지정한다(자르지 않아도 되어 슬라이더를 옮길 때마다 바로 들어 볼 수 있다).
    # WMA 같은 형식은 브라우저가 재생하지 못해 '이 구간으로 정하기'로 자른 wav로만 들을 수 있다.
    _MIME = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".ogg": "audio/ogg", ".flac": "audio/flac"}
    _suffix = "." + src_name.rsplit(".", 1)[-1].lower() if "." in src_name else ""
    if _suffix in _MIME:
        st.audio(data, format=_MIME[_suffix], start_time=int(start), end_time=int(start + duration))
        st.caption("초록 띠 구간을 바로 들어 볼 수 있어요. 시작 위치를 옮기면 재생 구간이 바뀌어요(재생 버튼을 다시 눌러 주세요).")
    else:
        st.caption(f"{_suffix or '이'} 형식은 브라우저에서 미리 들을 수 없어요. '이 구간으로 정하기'를 누르면 잘라서 들어 볼 수 있어요.")
    with st.expander("파형은 무엇인가요? · 수업과의 연결"):
        st.markdown(
            "소리는 **1초에 수만 번 잰 소리 세기의 숫자 나열**이에요(수업 01·02: 샘플링 레이트, 진폭). 곡 한 곡은 수백만 개라 하나하나 그릴 수 없어서, "
            "**600칸으로 나눠 칸마다 가장 작은 값과 가장 큰 값**만 이어 그린 윤곽이에요. 두꺼운 곳이 소리가 큰 구간이에요. "
            "선택한 구간은 02 실습 7처럼 `axvspan`으로 띠를 칠했어요. 구간을 자르고 인식하기 전에 모델이 읽는 것은 이 숫자들이고, "
            "음성 인식(Whisper)은 안에서 16 kHz 모노로 바꿔 읽어요(수업 07).")

    if st.button("이 구간으로 정하기 (자르고 들어 보기)", type="primary", key="cut_btn"):
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
st.markdown("**선택한 구간 듣기**")
st.audio(mix_path, format="audio/wav")
st.caption("가사가 들리는 부분이 맞는지 들어 보세요. 반주만 나오면 위에서 시작 위치를 바꾸고 다시 '이 구간으로 정하기'를 누르세요.")

# ---------- 3. 언어 확인 → 가사 인식 ----------
st.subheader("언어 확인")
explain.show("song_lang")
g = st.session_state["gen"]
det_key = f"lang_det_{g}"
if st.button("언어 알아보기", key=f"det_btn_{g}"):
    with st.spinner("언어를 알아보는 중… (서버를 켠 뒤 처음 한 번은 medium 모델을 읽느라 몇십 초 더 걸려요)"):
        try:
            st.session_state[det_key] = web_song.detect_clip_language(ws)
        except Exception as e:
            st.session_state[det_key] = {"error": f"언어를 알아내지 못했어요 ({type(e).__name__}: {e})"}
sug = st.session_state.get(det_key)
answer, chosen, mixed_mode = "unknown", [], "primary"
if sug and "error" in sug:
    st.warning(sug["error"])
elif sug and sug["top"]:
    code, share = sug["top"]
    st.markdown(f"**{languages.name(code)}**로 파악돼요 ({share:.0%}). 맞나요?")
    if sug["mixed"]:
        st.caption(f"{languages.name(sug['mixed'])}도 섞여 있을 수 있어요.")
    ans = st.radio("맞나요?", ["네", "아니오", "모르겠어요"], horizontal=True, key=f"lang_ans_{g}", label_visibility="collapsed")
    if ans == "네":
        answer, chosen = "yes", [code]
    elif ans == "아니오":
        answer = "no"
        chosen = st.multiselect("실제 언어 (여러 개 가능, 첫 번째가 주 언어예요)", list(languages.COMMON), format_func=languages.name, key=f"lang_pick_{g}")
        if len(chosen) > 1:
            st.caption(f"섞인 가사는 첫 번째 언어({languages.name(chosen[0])})를 주 언어로 인식해요. "
                       "(Whisper의 구간별 재감지는 30초 단위라 10~20초 구간에서는 효과가 없어요.)")
    else:
        st.caption("자동으로 인식하고, 인식된 가사를 보고 고칠 수 있어요.")
elif sug:
    st.warning("언어를 짐작하지 못했어요. 아래에서 직접 골라 주세요.")
    answer = "no"
    chosen = st.multiselect("실제 언어 (여러 개 가능)", list(languages.COMMON), format_func=languages.name, key=f"lang_pick_{g}")
else:
    st.caption("먼저 '언어 알아보기'를 눌러 주세요. 언어가 틀리면 인식 전체가 틀려서, 인식 전에 한 번 확인해요.")
opts = languages.stt_options(answer, chosen, mixed=mixed_mode)
rec_langs = opts["languages"] or ([sug["top"][0]] if sug and sug.get("top") else [])   # '모르겠어요'여도 제안된 언어를 줄의 언어로 기록

st.subheader("가사 인식")
explain.show("song_recog")
doc = web_song.load_doc(ws)
if st.button("가사 인식하기" if doc is None else "다시 인식하기(고친 가사는 사라져요)", key="recog_btn", disabled=sug is None):
    with st.spinner("인식하는 중… (medium 모델, CPU에서 20초 구간에 약 20~60초. 서버를 켠 뒤 처음 한 번은 모델을 읽느라 더 걸려요)"):
        try:
            web_song.recognize_lines(ws, language=opts["language"], multilingual=opts["multilingual"], languages=rec_langs)
            st.session_state["gen"] += 1
        except Exception as e:
            st.error(f"인식하지 못했어요 ({type(e).__name__}: {e})")
    st.rerun()
if doc is None:
    st.stop()
if doc.get("languages"):
    st.caption("인식에 쓴 언어: " + " + ".join(languages.name(c) for c in doc["languages"]) + (" (구간마다 재감지)" if doc["stt"].get("multilingual") else ""))

# ---------- 4. 줄 확인·수정 (선택) ----------
lines = doc["lines"]
gen = st.session_state["gen"]
st.subheader("줄 확인·수정 (선택)")
st.caption("인식된 가사가 맞으면 **그대로 연습해도 돼요.** 틀린 곳이 보이거나 점수가 이상하면 고쳐서 저장하세요. "
           "인식이 틀리면 기준 문장도 틀려서 점수가 틀린 기준으로 매겨질 수 있어요.")
mark = {"confirmed": "✓", "dropped": "✕", "candidate": "·"}
no = st.segmented_control("줄", [l["no"] for l in lines], default=lines[0]["no"], key=f"line_{gen}",
                          format_func=lambda n: f"{n}줄 {mark[next(l['status'] for l in lines if l['no'] == n)]}")
ln = next(l for l in lines if l["no"] == (no or lines[0]["no"]))
if doc["lines"] and any(l["low_confidence"] for l in lines):
    st.caption("⚠ 이 구간은 인식이 불안정할 수 있어요(신뢰 지표가 낮음). 특히 꼼꼼히 들어 보세요.")
if ln["too_long"]:
    st.caption("이 줄은 길어요(6초·14단어 초과). 나눠서 연습하고 싶다면 가사를 줄이거나 빼세요.")

text = st.text_input("가사 (고치면 아래에 저장 버튼이 나와요)", value=ln["text"], key=f"txt_{gen}_{ln['no']}")
changed = text.strip() != ln["text"]
c1, c2, c3 = st.columns([2, 1, 3], vertical_alignment="center")
if changed and c1.button("고친 가사 저장", type="primary", key=f"ok_{gen}_{ln['no']}"):
    if text.strip():
        web_song.confirm_line(ws, ln["no"], text)
        st.rerun()
    else:
        st.warning("가사가 비어 있어요. 빼려면 '연습에서 빼기'를 누르세요.")
if c2.button("연습에서 빼기", key=f"drop_{gen}_{ln['no']}"):
    web_song.drop_line(ws, ln["no"])
    st.rerun()
c3.caption({"confirmed": "고쳐서 저장함", "dropped": "연습에서 뺌", "candidate": "자동 인식 그대로"}[ln["status"]]
           + (" · 원문과 달라요" if ln["edited"] else ""))

# ---------- 5. 듣기 ----------
st.subheader("듣기")
explain.show("song_listen")
line_lang = ln.get("lang") or (doc.get("languages") or ["en"])[0]       # 이슈 #50 이전에 만든 줄 데이터는 언어 칸이 없어 영어
meaning_box(ln["text"], line_lang, f"song_{gen}_{ln['no']}")             # 들을 문장의 한글 뜻
notes_box(ln["text"], line_lang, f"song_{gen}_{ln['no']}")               # 표현 설명(버튼)
if line_lang == "ja" and wp.reading_caption(ln["text"]):
    st.caption(wp.reading_caption(ln["text"]))                          # 한자·가타카나의 히라가나 읽기와 로마자
sources = ["원본 음악", "보컬만", "표준 발음"]
src = st.segmented_control("들을 소리", sources, default="원본 음악", key="listen_src")
a, b = web_song.line_range(ln, clip_seconds)
vs = web_song.vocals_status(ws)
if vs["state"] == "running" and src != "보컬만":
    st.caption(f"보컬 분리가 뒤에서 진행 중이에요({int(vs['elapsed'])}초 경과). '보컬만'을 고르면 상태를 볼 수 있어요.")


@st.fragment(run_every="3s")
def vocal_watch():
    """보컬 분리 진행 상태를 3초마다 확인한다. 끝나면(성공·실패) 화면 전체를 다시 그려 결과를 보여 준다."""
    cur = web_song.vocals_status(ws)
    if cur["state"] == "running":
        st.info(f"보컬을 분리하는 중이에요 · {int(cur['elapsed'])}초 경과 (보통 1~3분). 화면은 막히지 않아요. 다른 소리를 들어도 되고 끝나면 자동으로 바뀌어요.")
    else:
        st.rerun()


if src == "보컬만":
    if vs["state"] == "done":
        st.audio(voc_path, format="audio/wav", start_time=a, end_time=b)
        st.caption("반주를 뺀 소리예요. 원어민이 실제로 어떻게 발음하는지 들어 보세요.")
    elif vs["state"] == "running":
        vocal_watch()
    else:
        if vs["state"] == "error":
            st.error(vs["error"])
        st.caption("보컬만 듣기는 **이 구간 전체에 대해 한 번만** 만들면 돼요(줄마다 만드는 게 아니에요). 만든 뒤에는 줄마다 해당 부분만 재생해요. "
                   "만드는 동안에도 다른 화면을 쓸 수 있어요.")
        if st.button("보컬만 만들기 (이 구간 전체, 보통 1~3분)" if vs["state"] != "error" else "다시 만들기", key="voc_btn"):
            web_song.start_vocals(ws)
            st.rerun()
elif src == "표준 발음":
    if ln.get("tts_path") and ln.get("tts_text") == ln["text"]:
        st.audio(ln["tts_path"], format="audio/wav")
        st.caption("TTS가 읽는 또박또박한 발음이에요(기계 음성).")
    elif ln["status"] == "dropped":
        st.caption("연습에서 뺀 줄이에요.")
    else:
        plan = web_song.tts_summary(ws, only={ln["no"]})
        st.caption(f"이 줄의 표준 발음은 아직 없어요. 만들면 OpenAI TTS를 부르고({plan['chars']}글자) **과금**돼요"
                   + (" (같은 문장이 이미 있어 무료예요)." if plan["n_api_calls"] == 0 else "."))
        if st.button("이 줄의 표준 발음 만들기", key=f"tts_btn_{ln['no']}"):
            with st.spinner("음성을 만드는 중…"):
                try:
                    web_song.make_tts(ws, only={ln["no"]})
                except Exception as e:
                    st.error(f"만들지 못했어요 ({type(e).__name__}: {e})")
            st.rerun()
    all_plan = web_song.tts_summary(ws)
    if all_plan["n_lines"] and all_plan["n_api_calls"]:
        st.caption(f"전체 {all_plan['n_lines']}줄 중 아직 없는 {all_plan['n_api_calls']}줄({all_plan['chars']}글자)을 한꺼번에 만들 수도 있어요(OpenAI TTS **과금**).")
        if st.button(f"모든 줄의 표준 발음 만들기 ({all_plan['n_api_calls']}줄)", key="tts_all_btn"):
            with st.spinner("음성을 만드는 중… (줄마다 몇 초씩 걸려요)"):
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
if ln["status"] == "dropped":
    st.caption("연습에서 뺀 줄이에요. 다시 쓰려면 곡 구간을 다시 인식해 주세요.")
else:
    tts_ok = ln.get("tts_path") and ln.get("tts_text") == ln["text"]
    st.caption(f"이 줄의 언어: {languages.name(line_lang)}" + ("" if languages.uses_spaces(line_lang) else " · 글자 오류율(CER) 중심으로 채점해요"))
    practice_panel(ln["text"], key=f"song_{gen}_{ln['no']}", tts_path=ln["tts_path"] if tts_ok else None, source="song", lang=line_lang)
