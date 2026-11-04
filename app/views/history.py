"""기록 페이지: 연습한 줄 표시, 문장별 WER 변화, 최근 시도 표. 기록 CSV(practice_log.py)를 읽는다. 검토 문서 16.10.

기록에는 문장 글이 없고 key만 있다(가사 저작물 보호). 글은 sentences.csv(예시 문장)나 이번 세션에서 연습한 글(session_state)에서 key로 찾고,
못 찾으면 key를 그대로 보여 준다(예: 서버를 다시 띄운 뒤의 가사 줄).
"""
import io

import pandas as pd
import streamlit as st

import practice_log as pl
import tts
import web_practice as wp

st.title("기록")
rows = pl.read_all()
if not rows:
    st.info("아직 기록이 없어요. '가사 입력'이나 '내 노래'에서 채점하면 여기에 쌓여요.")
    st.stop()

sample_text = {f"s{int(s['id']):02d}": s["sentence"] for s in tts.load_sentences()}
session_text = st.session_state.get("log_texts", {})
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
st.caption("기록 파일에는 문장 글이 없고 점수와 설정만 있어요.")
