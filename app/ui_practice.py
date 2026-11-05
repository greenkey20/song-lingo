"""따라읽기·받아쓰기 화면 부품: 가사 입력 페이지와 내 노래 페이지가 같이 쓴다(검토 문서 16.10).

`practice_panel(text, key, tts_path)` 하나가 탭(따라읽기 / 받아쓰기) → 녹음 또는 입력 → 채점하기·건너뛰기 → 결과(카드·단어 대조)를 그린다.
계산은 practice.py(채점 순서)·web_practice.py(화면용 조각)가 하고 이 파일은 위젯 배치와 결과 보관(session_state)만 한다.
[수업에 없음] `st.audio_input`: 브라우저 마이크로 녹음해 wav 파일 객체를 돌려주는 Streamlit 위젯. `unsafe_allow_html`: HTML 조각을 그대로 그리는 옵션
(사용자 글은 web_practice에서 escape해서 넣는다).
"""
import matplotlib.pyplot as plt
import streamlit as st

import practice
import practice_log
import visualisation
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


def _sound_figs(tts_path, recording):
    """표준 발음과 내 녹음의 소리 모양 그림 4개를 만든다: {"wave","fft","stft","logmel"} 또는 {"error": 안내}. 채점 직후 한 번만 만들어 보관한다.
    그림 계산이 실패해도 채점 결과는 그대로 보여 주려고 예외를 안내 문구로 바꾼다."""
    try:
        figs = visualisation.plot_sound_panels(wp.normalized_sounds(tts_path, recording))
    except Exception as e:
        return {"error": f"소리 모양 그림을 만들지 못했어요 ({type(e).__name__})"}
    for f in figs.values():
        plt.close(f)             # pyplot의 열린 그림 목록에서 빼 메모리를 아낀다(st.pyplot은 닫힌 그림도 그린다)
    return figs


def _span_figure(prep, res):
    """틀린 구간 표시 한 장을 만든다: {"blocks","text","fig"} 또는 {"blocks": 0} 또는 {"error": 안내}. 채점 직후 한 번만 만든다(인식이 두 번 더 돌아 몇 초 걸림).
    노트북 practice.ipynb의 '틀린 구간을 소리 그림 위에 표시하기'(show_error_spans)와 같은 경로다."""
    try:
        sp = wp.error_spans(prep, res)
        if not sp["blocks"]:
            return {"blocks": 0}
        fig = visualisation.plot_error_spans(
            sp["sounds"], sp["loc"]["blocks"],
            "같은 번호 [k]는 같은 덩어리 (참고 정보, 평가 아님; 구간은 Whisper 단어 시간의 추정값)")
        plt.close(fig)
        return {"blocks": sp["blocks"], "text": sp["text"], "fig": fig}
    except Exception as e:
        return {"error": f"틀린 구간을 표시하지 못했어요 ({type(e).__name__})"}


def _show_error_spans(sp):
    """따라읽기 결과 아래 '틀린 구간 표시'. 위 단어 대조에서 보라로 표시된 틀린 단어가 소리의 어디인지 같은 번호 [k]로 보여 준다."""
    st.markdown("**틀린 구간 표시** · 참고용 · 평가 아님")
    if not sp:
        st.caption("표준 발음이 있어야 틀린 구간을 소리 위에 표시할 수 있어요.")
    elif "error" in sp:
        st.caption(sp["error"])
    elif not sp["blocks"]:
        st.caption("인식 결과가 기준 문장과 같아서 표시할 틀린 구간이 없어요.")
    else:
        st.pyplot(sp["fig"], clear_figure=False)
        st.code(sp["text"], language=None)
        st.caption("왼쪽은 표준 발음, 오른쪽은 내 녹음이에요. 같은 번호 [k]는 같은 덩어리이고, 단어 하나가 비었으면 점선 한 줄로 표시해요. "
                   "구간은 Whisper가 추정한 단어 시간이라 정확한 정렬이 아니에요(원인을 알려 주지는 않아요).")


def _show_sound_shapes(figs, has_tts):
    """따라읽기 결과 아래 '소리 모양 비교' 칸(2×2). 참고용이며 점수가 아님을 함께 알린다."""
    st.markdown("**소리 모양 비교** · 참고용 · 평가 아님")
    if not has_tts:
        st.caption("표준 발음이 있으면 내 녹음과 모양을 비교할 수 있어요. 가사 입력에서 '표준 발음 만들기'를 먼저 눌러 보세요.")
        return
    if not figs or "error" in figs:
        st.caption((figs or {}).get("error", "그림이 없어요."))
        return
    cells = [("wave", "파형", "시간에 따른 소리 크기(진폭)와 타이밍"),
             ("fft", "FFT", "소리 전체의 주파수별 크기(시간 정보 없음)"),
             ("stft", "STFT", "시간에 따른 주파수(dB), 밝을수록 센 소리"),
             ("logmel", "Log-Mel", "사람 귀에 가까운 주파수 눈금(dB)")]
    for row in (cells[:2], cells[2:]):
        cols = st.columns(2)
        for col, (key, title, desc) in zip(cols, row):
            with col:
                st.markdown(f"**{title}** <small>{desc}</small>", unsafe_allow_html=True)
                st.pyplot(figs[key], clear_figure=False)
    st.caption("목소리와 마이크가 달라서 모양이 다를 수 있어요. 점수는 위의 오류율이에요. 두 소리의 최대 음량은 같게 맞춰 그렸어요.")
    with st.expander("그림 읽는 법 · 수업에서 배운 것과의 연결"):
        st.markdown(SOUND_SHAPE_GUIDE)


# 소리 모양 그림을 읽는 법. 017_sound 수업의 어느 부분인지 함께 적는다(발표·복습용).
SOUND_SHAPE_GUIDE = """
**소리는 숫자의 나열이에요.** 마이크는 1초에 16,000번 소리의 세기를 재서(샘플링, 16 kHz) 숫자로 기록해요. 아래 그림은 모두 그 숫자를 다르게 바라본 거예요. *(수업 01·02)*

| 그림 | 보는 것 | 읽는 법 | 수업 |
|---|---|---|---|
| **파형** | 시간 → 진폭 | 가로는 시간, 세로는 소리의 세기. 말한 구간과 쉰 구간, 읽는 속도가 보여요 | 01 소리가 숫자가 되는 과정, 02 WAV |
| **FFT** | 주파수 → 크기 | `rfft`로 소리 전체를 사인파들의 합으로 쪼개요. 낮은 쪽의 큰 봉우리가 목소리의 높이와 배음이에요. **언제**인지는 알 수 없어요 | 03 실습 1~3 |
| **STFT** | 시간 × 주파수 → 파워 | 32 ms 창을 8 ms씩 옮기며 FFT를 반복해요. 가로줄 무늬는 모음, 위쪽의 흐린 부분은 `s`·`sh` 같은 자음이에요 | 03 STFT, lesson04 1교시 |
| **Log-Mel** | 시간 × Mel 칸 → 로그 파워 | STFT를 사람 귀의 눈금(Mel) 40칸으로 묶고 로그를 취해요. 음성 인식 모델의 입력 모양이에요 | lesson04 2·3교시 |

**비교하는 요령**: 표준 발음(TTS)과 내 녹음에서 같은 단어가 같은 위치에 오는지 보세요. 틀린 단어는 파형이 비거나 STFT의 무늬가 달라져요.
**주의**: 목소리·마이크·방이 다르면 모양이 달라요. 이 그림은 *참고용*이고 점수는 아니에요(점수는 위의 오류율).
"""


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
            with st.spinner("인식하고 채점하는 중… (틀린 구간을 찾느라 몇 초 더 걸려요)"):
                try:
                    st.session_state[f"{key}_read"] = practice.read(prep, rec.getvalue())
                    _log(source, prep["text"], "read", st.session_state[f"{key}_read"])
                    ok = tts_path and not st.session_state[f"{key}_read"]["error"]
                    st.session_state[f"{key}_figs"] = _sound_figs(tts_path, rec.getvalue()) if ok else None
                    wrong = ok and st.session_state[f"{key}_read"]["score"]["main"]["distance"] > 0
                    st.session_state[f"{key}_spans"] = _span_figure(prep, st.session_state[f"{key}_read"]) if wrong else (
                        {"blocks": 0} if ok else None)
                except Exception as e:
                    st.session_state[f"{key}_read"] = {"error": f"채점하지 못했어요 ({type(e).__name__}: {e})"}
        if c2.button("건너뛰기", key=f"{key}_read_skip_{nonce}"):
            st.session_state[f"{key}_nonce"] = nonce + 1
            st.session_state.pop(f"{key}_read", None)
            st.session_state.pop(f"{key}_figs", None)
            st.session_state.pop(f"{key}_spans", None)
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
            if not res["error"]:
                _show_error_spans(st.session_state.get(f"{key}_spans"))
                _show_sound_shapes(st.session_state.get(f"{key}_figs"), bool(tts_path))
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
