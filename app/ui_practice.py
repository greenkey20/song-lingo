"""따라읽기·받아쓰기 화면 부품: 가사 입력 페이지와 내 노래 페이지가 같이 쓴다(검토 문서 16.10).

`practice_panel(text, key, tts_path)` 하나가 탭(따라읽기 / 받아쓰기) → 녹음 또는 입력 → 채점하기·건너뛰기 → 결과(카드·단어 대조)를 그린다.
계산은 practice.py(채점 순서)·web_practice.py(화면용 조각)가 하고 이 파일은 위젯 배치와 결과 보관(session_state)만 한다.
[수업에 없음] `st.audio_input`: 브라우저 마이크로 녹음해 wav 파일 객체를 돌려주는 Streamlit 위젯. `unsafe_allow_html`: HTML 조각을 그대로 그리는 옵션
(사용자 글은 web_practice에서 escape해서 넣는다).
"""
import streamlit as st

import practice
import practice_log
import web_practice as wp


def _log(source, text, mode, res):
    """채점이 성공했으면 기록 CSV에 한 줄 남긴다(문장 글은 저장하지 않음). 화면에 보여 줄 글은 이번 세션 메모리에만 key로 묻어 둔다.
    기록 실패가 연습을 막지 않게 오류는 안내만 한다."""
    try:
        rec = practice_log.make_record(source, text, mode, res)
        if rec is None:
            return
        if rec["key"].startswith("s") and not rec["key"].startswith("h_"):
            rec["source"] = "sample"                      # sentences.csv의 예시 문장
        practice_log.append(rec)
        st.session_state.setdefault("log_texts", {})[rec["key"]] = text
    except Exception as e:
        st.caption(f"기록을 저장하지 못했어요 ({type(e).__name__})")


def _result_html(res, prep):
    """채점 결과를 화면 HTML로(결과 카드 + 입력 상태 칩 + 단어 대조)."""
    score = res["score"]
    parts = [wp.result_card_html(score)]
    if res.get("quality"):
        parts.append(f'<div style="margin:-4px 0 8px">{wp.chips_html(wp.quality_chips(res["quality"]))}</div>')
    return "".join(parts)


def _show_result(res, prep, mode):
    if res["error"]:
        st.warning(res["error"])
        return
    st.markdown(_result_html(res, prep), unsafe_allow_html=True)
    if res.get("quality") and res["quality"]["warnings"]:
        for w in res["quality"]["warnings"]:
            st.caption("⚠ " + w)           # 경고는 안내일 뿐, 채점은 그대로 진행했다
    st.markdown("**단어 대조** · 위는 기준 문장, 아래는 " + ("인식한 내 녹음" if mode == "read" else "내가 적은 글") +
                " · 보라 물결 밑줄은 다른 단어", help="낮을수록 좋은 오류율이고, 틀린 단어는 색과 밑줄·이름표로 표시해요.")
    st.markdown(wp.diff_html(res["score"]["main"]["ops"]), unsafe_allow_html=True)
    if mode == "read":
        st.caption(f"인식한 문장: {res['hyp']}  ·  인식 {res['seconds']:.1f}초")


def practice_panel(text, key, tts_path=None, meaning_ko="", source="lyrics"):
    """문장 text 하나의 따라읽기·받아쓰기를 그린다. key는 페이지 안에서 겹치지 않는 문자열(문장·줄마다 다르게).

    source: 기록의 출처 표시("lyrics" 가사 입력 / "song" 내 노래; 예시 문장이면 자동으로 "sample").
    tts_path: 표준 발음 음성 파일(있으면 결과 아래 '다시 듣기'에 쓴다). 받아쓰기는 정답을 숨겨야 하므로 이 함수는 받아쓰기 탭에서
    채점하기 전에는 text를 보여 주지 않는다(따라읽기 탭에서는 읽을 문장을 보여 준다)."""
    prep = wp.make_prep(text, tts_path=tts_path, meaning_ko=meaning_ko)
    if prep["error"]:
        st.info("연습할 문장을 먼저 정하세요.")
        return
    nonce = st.session_state.get(f"{key}_nonce", 0)          # 건너뛰기로 입력·결과를 비울 때 올린다
    st.markdown(wp.css(), unsafe_allow_html=True)
    tab_read, tab_dict = st.tabs(["🎤 따라읽기", "⌨ 받아쓰기"])

    with tab_read:
        st.markdown(f"### {prep['text']}")
        if meaning_ko:
            st.caption(meaning_ko)
        rec = st.audio_input("눌러서 녹음 시작, 다시 눌러서 끝내기", key=f"{key}_rec_{nonce}")
        c1, c2 = st.columns([1, 1])
        if c1.button("채점하기", type="primary", key=f"{key}_read_go_{nonce}", disabled=rec is None):
            with st.spinner("인식하고 채점하는 중…"):
                try:
                    st.session_state[f"{key}_read"] = practice.read(prep, rec.getvalue())
                    _log(source, prep["text"], "read", st.session_state[f"{key}_read"])
                except Exception as e:
                    st.session_state[f"{key}_read"] = {"error": f"채점하지 못했어요 ({type(e).__name__}: {e})"}
        if c2.button("건너뛰기", key=f"{key}_read_skip_{nonce}"):
            st.session_state[f"{key}_nonce"] = nonce + 1
            st.session_state.pop(f"{key}_read", None)
            st.rerun()
        res = st.session_state.get(f"{key}_read")
        if res:
            _show_result(res, prep, "read")
            if rec is not None or tts_path:
                st.markdown("**다시 듣기**")
                if tts_path:
                    st.caption("표준 발음")
                    st.audio(tts_path, format="audio/wav")
                if rec is not None:
                    st.caption("내 녹음")
                    st.audio(rec)
        st.caption("점수는 발음 점수가 아니라 문장 인식 일치도예요. 주변 소리가 크면 오류율이 올라갈 수 있어요.")

    with tab_dict:
        st.caption("소리를 들으면서 들은 문장을 적어 보세요. 재생은 몇 번이든 괜찮고, 대소문자와 문장부호는 채점할 때 정리돼요.")
        ans = st.text_area("들은 문장 적기", key=f"{key}_ans_{nonce}", height=100)
        c1, c2 = st.columns([1, 1])
        if c1.button("채점하기", type="primary", key=f"{key}_dict_go_{nonce}"):
            st.session_state[f"{key}_dict"] = practice.dictation(prep, ans)
            _log(source, prep["text"], "dictation", st.session_state[f"{key}_dict"])
        if c2.button("건너뛰기", key=f"{key}_dict_skip_{nonce}"):
            st.session_state[f"{key}_nonce"] = nonce + 1
            st.session_state.pop(f"{key}_dict", None)
            st.rerun()
        res = st.session_state.get(f"{key}_dict")
        if res:
            _show_result(res, prep, "dictation")
            if not res["error"]:
                st.markdown(f"**기준 문장** (채점 뒤에 공개)  \n{prep['text']}")
