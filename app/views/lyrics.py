"""내 문장 페이지: 연습할 문장이나 가사를 쓰거나 붙여 넣고 → **언어 알아보기** → 줄마다 "○○어로 보여요. 맞나요?"(네/아니오/모르겠어요) 확인 → 표준 발음·따라읽기·받아쓰기·채점.
검토 문서 16.10·16.14. (메뉴 이름은 11-05에 "가사 입력"에서 "내 문장"으로 바꿨다. 파일 이름은 그대로 `lyrics.py`, 주소는 `/text`.)

흐름은 "내 노래"와 같다: 입력 → 언어 알아보기(제안) → 사용자 확인 → 그 선택에 따라 표준 발음과 연습.
- 언어 제안은 `languages.suggest_line_language`(문자 체계 + 라틴 문자 줄은 낱말 점수)이고 **줄마다** 따로 한다. 제안은 틀릴 수 있어 사용자가 확인한다.
- 답: 네 → 제안한 언어 / 아니오 → 사용자가 고른 언어들(여러 개 가능, 첫 번째가 주 언어) / 모르겠어요 → 제안한 언어를 쓰되 "추정"으로 표시.
- 계산은 languages.py·web_practice.py·practice.py가 하고 이 파일은 화면 배치만 한다. 문장은 세션에만 있고 저장하지 않는다.
- 표준 발음(OpenAI TTS)은 줄의 언어를 확인한 뒤 **버튼을 눌러야** 만들어진다(새 문장은 과금, 예시 문장·이미 만든 문장은 캐시라 무료). TTS는 글의 언어를 따라 읽으므로 언어를 따로 넘기지 않는다.
"""
import streamlit as st

import languages
import web_practice as wp
import explain
from ui_practice import meaning_box, notes_box, practice_panel

CONF = {"high": "확신 높음", "medium": "확신 보통", "low": "확신 낮음", "none": ""}
SOURCE = {"script": "문자 체계로 본 것", "words": "자주 쓰는 낱말로 본 것", "none": ""}

st.title("내 문장")
st.caption("연습할 문장이나 가사를 한 줄에 하나씩 쓰거나 붙여 넣어요. 이 화면에만 있고 저장하지 않아요. 어떤 언어인지 몰라도 돼요.")

if "lyrics" not in st.session_state:
    st.session_state["lyrics"] = ""


def load_example():
    """예시 묶음을 입력칸에 넣는다(버튼의 on_click: 입력 위젯이 만들어지기 전에 값을 바꿀 수 있다)."""
    st.session_state["lyrics"] = wp.example_set(st.session_state["lyr_example"])


# ---------- 1. 입력 (맨 위) ----------
text = st.text_area("문장", key="lyrics", height=150, label_visibility="collapsed",
                    placeholder="연습할 문장이나 가사를 한 줄에 하나씩 적거나 붙여 넣으세요. (영어, 일본어, 프랑스어 …)")
e1, e2, e3 = st.columns([1.3, 1.3, 3], vertical_alignment="center")
e1.selectbox("예시 묶음", wp.EXAMPLE_NAMES, key="lyr_example", label_visibility="collapsed")
e2.button("예시 문장 불러오기", on_click=load_example)
e3.caption("직접 쓴 문장이에요. 영어는 표준 발음이 이미 있어 과금되지 않고, 다른 언어는 처음 만들 때 과금돼요(작음).")

lines = wp.split_lyrics(text)
if not lines:
    st.stop()
keys = [f"{abs(hash(ln)) % 10**8}" for ln in lines]          # 줄 내용으로 만든 열쇠: 줄을 고치면 그 줄의 답은 사라진다

# ---------- 2. 언어 알아보기 ----------
st.subheader("언어 확인")
explain.show("lyr_lang")
det_for = st.session_state.get("lyr_det_for")
if st.button("언어 알아보기", key="lyr_det_btn"):
    st.session_state["lyr_det"] = {k: languages.suggest_line_language(ln) for k, ln in zip(keys, lines)}
    st.session_state["lyr_det_for"] = True
dets = st.session_state.get("lyr_det", {})
if not any(k in dets for k in keys):
    st.caption("먼저 '언어 알아보기'를 눌러 주세요. 줄마다 언어를 짐작해서 보여 드리고, 맞는지 확인받아요.")
    st.stop()


def confirm_all():
    """'모두 맞아요': 제안이 있는 모든 줄의 답을 '네'로."""
    for k in keys:
        if dets.get(k, {}).get("primary"):
            st.session_state[f"lyr_ans_{k}"] = "네"


st.button("제안이 있는 줄은 모두 맞아요", on_click=confirm_all, key="lyr_all")
answers = {}
for n, (ln, k) in enumerate(zip(lines, keys), 1):
    sug = dets.get(k) or languages.suggest_line_language(ln)
    with st.container(border=True):
        st.markdown(f"**{n}번째 줄** · {ln}")
        if sug["primary"]:
            names = " + ".join(languages.name(c) for c in sug["languages"])
            extra = "".join(f" · {x}" for x in (SOURCE[sug["source"]], CONF[sug["confidence"]]) if x)
            st.markdown(f"**{names}**로 보여요{extra}. 맞나요?")
            if sug["source"] == "words" and sug["confidence"] == "low":
                st.caption("낱말이 적어서 확실하지 않아요. 영어일 수도 있고 다른 라틴 문자 언어(프랑스어·스페인어 …)일 수도 있어요.")
            if len(sug["languages"]) > 1:
                st.caption(f"{names}가 섞여 있어요. 글자(음절)가 더 많은 {languages.name(sug['primary'])}를 주 언어로 인식하고 채점해요.")
        else:
            st.markdown("언어를 짐작하지 못했어요(한자만 있는 글 등). 직접 골라 주세요.")
        ans = st.radio("맞나요?", ["네", "아니오", "모르겠어요"], index=None, horizontal=True, key=f"lyr_ans_{k}",
                       label_visibility="collapsed")
        langs, note = None, ""
        if ans == "네" and sug["primary"]:
            langs = [sug["primary"]]
        elif ans == "아니오" or (ans == "네" and not sug["primary"]):
            picked = st.multiselect("실제 언어 (여러 개 가능, 첫 번째가 주 언어예요)", list(languages.COMMON), format_func=languages.name,
                                    key=f"lyr_pick_{k}")
            langs = picked or None
        elif ans == "모르겠어요":
            if sug["primary"]:
                langs, note = [sug["primary"]], "제안한 언어로 추정해서 진행해요."
            else:
                st.caption("짐작도 못 했어요. 언어를 골라 주세요.")
                langs = st.multiselect("언어", list(languages.COMMON), format_func=languages.name, key=f"lyr_pick_{k}") or None
        if langs:
            answers[n] = {"line": ln, "key": k, "languages": langs, "lang": langs[0]}
            if note:
                st.caption(note)

if not answers:
    st.info("줄마다 언어를 확인하면 아래에서 표준 발음을 만들고 연습할 수 있어요.")
    st.stop()

# ---------- 3. 확인한 줄 고르기 ----------
st.subheader("연습할 줄")
ready = sorted(answers)
no = st.segmented_control("연습할 줄", ready, default=ready[0], key="lyr_line",
                          format_func=lambda n: f"{n}번째 줄 · {languages.name(answers[n]['lang'])}")
a = answers[no if no in answers else ready[0]]
no, line, lang = (no if no in answers else ready[0]), a["line"], a["lang"]
meaning_box(line, lang, f"lyr_{a['key']}")                    # 고른 줄의 한글 뜻(예시는 직접 쓴 뜻, 그 밖에는 버튼으로 AI 번역)
notes_box(line, lang, f"lyr_{a['key']}")                      # 표현 설명(버튼, 단어·표현·문법·예문)
if lang == "ja":
    rc = wp.reading_caption(line)                               # 한자·가타카나를 히라가나 읽기와 로마자로
    if rc:
        st.caption(rc)
if not languages.uses_spaces(lang):
    st.caption("공백 없이 쓰는 언어라서 점수는 단어가 아니라 **글자 오류율(CER)** 이 중심이에요. 한자·가타카나는 히라가나 읽기로 바꿔 비교해요.")

# ---------- 4. 듣기 ----------
st.subheader("듣기")
explain.show("lyr_tts")
path, cached = wp.tts_target(line)
if cached:
    st.audio(path, format="audio/wav")
    st.caption("표준 발음(TTS)이에요. 또박또박 읽는 기계 음성이라 실제 노래·대화와 다를 수 있어요.")
else:
    st.caption("이 줄의 표준 발음은 아직 없어요. 만들면 OpenAI TTS를 한 번 불러서 **과금**돼요(같은 문장은 다시 만들지 않아요).")
    if st.button("표준 발음 만들기", key=f"mk_{a['key']}"):
        with st.spinner("음성을 만드는 중…"):
            try:
                wp.make_tts(line)
            except Exception as e:
                st.error(f"만들지 못했어요 ({type(e).__name__}: {e})")
        st.rerun()

# 확인한 모든 줄의 표준 발음을 한꺼번에 만들기(이미 있는 줄은 건너뜀)
todo = [x["line"] for x in answers.values() if not wp.tts_target(x["line"])[1]]
if todo:
    chars = sum(len(t) for t in todo)
    st.caption(f"확인한 {len(answers)}줄 중 표준 발음이 아직 없는 {len(todo)}줄({chars}글자)을 한꺼번에 만들 수도 있어요(OpenAI TTS **과금**, 같은 문장은 다시 만들지 않아요).")
    if st.button(f"모든 줄의 표준 발음 만들기 ({len(todo)}줄)", key="lyr_tts_all"):
        with st.spinner("음성을 만드는 중… (줄마다 몇 초씩 걸려요)"):
            try:
                for t in todo:
                    wp.make_tts(t)
            except Exception as e:
                st.error(f"만들지 못했어요 ({type(e).__name__}: {e})")
        st.rerun()

# ---------- 5. 연습 ----------
st.subheader("연습")
practice_panel(line, key=f"lyr_{no}_{lang}_{a['key']}", tts_path=path if cached else None, lang=lang)
