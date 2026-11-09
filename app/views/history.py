"""기록 페이지: 연습한 줄 표시, 문장별 WER 변화, 최근 시도 표. 검토 문서 16.10·16.16.

기록의 출처는 세 가지다.
- **로그인한 사용자**(서버 DB 모드): 내 `practices`(문장 글과 인식문까지 저장되어 있어서 다시 열어도 문장이 보인다). 이슈 #52.
- **게스트**(서버 DB 모드): 이번 세션에서 한 연습만(저장되지 않음, 공유 CSV는 쓰지 않는다).
- **저장소 설정이 없을 때**(내 컴퓨터 개발): 기록 CSV(practice_log.py). CSV에는 문장 글이 없고 key만 있어서, 글은 sentences.csv(예시 문장)나
  이번 세션에서 연습한 글(session_state)에서 key로 찾고 못 찾으면 key를 그대로 보여 준다.

주의: 표에는 점수(WER·CER·S/D/I)만 나오고 **인식문(`practices.hyp_text`)은 아직 화면에 없다**(DB에는 저장돼 있음, 개선 후보).

수업과의 관계: [수업에 없음] 이 파일 전체(Streamlit 화면). 그래프는 `st.line_chart`, 표는 pandas `DataFrame`(수업 1~7강에는 없음, 자습 노트북 WER·CER과는 점수 정의가 같음).
"""
import io

import pandas as pd
import streamlit as st

import auth_gate
import explain
import practice_log as pl
import storage
import tts
import web_practice as wp

st.title("기록")
explain.show("history")
db_text = {}
if auth_gate.is_user():                                           # 로그인한 사용자: 내 시도(서버 DB)
    try:
        with storage.connect() as conn:
            practices_db = storage.list_practices(conn, st.session_state["uid"], limit=2000)
    except Exception:
        practices_db = []
        st.warning("서버에서 기록을 불러오지 못했어요. 잠시 뒤에 다시 열어 보세요.")
    rows = [r for r in (pl.row_from_practice(a) for a in reversed(practices_db)) if r]       # 오래된 것부터
    db_text = {a["key"]: a["ref_text"] for a in practices_db if a.get("ref_text")}
elif storage.enabled():                                           # 게스트: 이번 세션의 연습만
    rows = list(st.session_state.get("session_rows", []))
    st.caption("게스트로 이용 중이라 기록이 저장되지 않아요. 이번 세션에서 한 연습만 보여요. 로그인하면 기록이 서버에 저장돼요.")
else:                                                             # 저장소 설정이 없는 개발 환경: 기록 CSV
    rows = pl.read_all()
if not rows:
    st.info("아직 기록이 없어요. '내 문장'이나 '내 노래'에서 채점하면 여기에 쌓여요.")
    st.stop()

sample_text = {f"s{int(s['id']):02d}": s["sentence"] for s in tts.load_sentences()}
session_text = {**st.session_state.get("log_texts", {}), **db_text}
source_name = {"sample": "예시", "lyrics": "가사 입력", "song": "내 노래"}


def label(key):
    """key → 화면에 보일 문장(글을 못 찾으면 '문장 <key>')."""
    return sample_text.get(key) or session_text.get(key) or f"문장 {key}"


# ---------- 연습한 줄 ----------
lyrics_lines = wp.split_lyrics(st.session_state.get("lyrics", ""))
if lyrics_lines:
    done = pl.practiced_keys(rows)
    marks = [("●" if pl.sentence_key(t) in done else "○") + f" {i}줄" for i, t in enumerate(lyrics_lines, 1)]
    st.subheader(f"이번 가사 · {sum(m[0] == '●' for m in marks)}/{len(marks)}줄")
    st.markdown("  ".join(f"`{m}`" for m in marks))
    st.caption("● 한 번 이상 연습한 줄, ○ 아직 안 한 줄이에요.")

# ---------- WER 변화 ----------
st.subheader("오류율 변화")
pairs = list(dict.fromkeys((r["key"], r["mode"]) for r in rows))
choice = st.selectbox("문장 · 방법", pairs, index=len(pairs) - 1, format_func=lambda p: f"{label(p[0])} · {pl.MODES[p[1]]}")
att = pl.attempts(rows, *choice)
chart = pd.DataFrame({"단어 오류율 WER (%)": [round(r["wer"] * 100, 1) for r in att]}, index=range(1, len(att) + 1))
chart.index.name = "시도"
st.line_chart(chart, y_label="WER (%) · 낮을수록 좋아요", x_label="시도")
step = pl.step_percent(att[-1]["n_words"])
st.caption(f"{att[-1]['n_words']}단어 문장이라 단어 하나가 달라질 때마다 {step:.1f}%씩 움직여요. "
           "문장마다 길이가 달라서 서로 다른 문장의 오류율은 한 선에 섞지 않아요." if step else "")

# ---------- 최근 시도 ----------
st.subheader("최근 시도")
recent = list(reversed(rows[-20:]))
table = pd.DataFrame({
    "시각": [r["ts"][5:16] for r in recent],
    "방법": [pl.MODES[r["mode"]] for r in recent],
    "출처": [source_name.get(r["source"], r["source"]) for r in recent],
    "문장": [label(r["key"]) for r in recent],
    "WER": [wp.pct(r["wer"]) for r in recent],
    "CER": [wp.pct(r["cer"]) for r in recent],
    "바뀜·빠짐·더해짐": [f"{r['S']}·{r['D']}·{r['I']}" for r in recent],
})
st.dataframe(table, hide_index=True, width="stretch")

buf = io.StringIO()
pd.DataFrame(rows).to_csv(buf, index=False)
st.download_button("기록 CSV 내려받기", buf.getvalue(), file_name="practice_log.csv", mime="text/csv")
st.caption("내려받은 CSV에는 문장 글이 없고 점수와 설정만 있어요." if not auth_gate.is_user() else "내려받은 CSV에는 문장 글 없이 점수와 설정만 들어 있어요(내 기록은 서버에 문장과 함께 저장돼 있어요).")
