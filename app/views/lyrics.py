"""내 문장 페이지: 연습할 문장이나 가사를 쓰거나 붙여 넣고 → **언어 알아보기** → 줄마다 "○○어로 보여요. 맞나요?"(네/아니오/모르겠어요) 확인 → 표준 발음·따라읽기·받아쓰기·채점.
검토 문서 16.10·16.14. (메뉴 이름은 11-05에 "가사 입력"에서 "내 문장"으로 바꿨다. 파일 이름은 그대로 `lyrics.py`, 주소는 `/text`.)

흐름은 "내 노래"와 같다: 입력 → 언어 알아보기(제안) → 사용자 확인 → 그 선택에 따라 표준 발음과 연습.
- 언어 제안은 `languages.suggest_line_language`(문자 체계 + 라틴 문자 줄은 낱말 점수)이고 **줄마다** 따로 한다. 제안은 틀릴 수 있어 사용자가 확인한다.
- 답: 네 → 제안한 언어 / 아니오 → 사용자가 고른 언어들(여러 개 가능, 첫 번째가 주 언어) / 모르겠어요 → 제안한 언어를 쓰되 "추정"으로 표시.
- 계산은 languages.py·web_practice.py·practice.py가 하고 이 파일은 화면 배치만 한다. 문장은 세션에만 있고 저장하지 않는다.
- 표준 발음(OpenAI TTS)은 줄의 언어를 확인한 뒤 **버튼을 눌러야** 만들어진다(새 문장은 과금, 예시 문장·이미 만든 문장은 캐시라 무료). TTS는 글의 언어를 따라읽으므로 언어를 따로 넘기지 않는다.
- **문장 묶음**(이슈 #75): 입력창 하나의 내용 전체가 한 묶음이다. 입력을 고치는 동안은 같은 묶음이 자동 저장으로 갱신되고(`persist.autosave_texts`), "새 묶음으로 시작"을 눌러야
  새 묶음이 만들어진다. 선택 상자·불러오기·삭제는 위쪽, 제목 입력칸은 입력창 아래. 줄마다의 위젯 열쇠는 `web_practice.line_keys`(반복된 줄도 겹치지 않게).

수업과의 관계: [수업에 없음] 이 파일 전체(Streamlit 화면 배치). 점수 계산·소리 처리는 수업과 자습 노트북에서 온 루트 모듈이 하고 여기서는 부르기만 한다.
"""
import streamlit as st

import languages
import web_practice as wp
import auth_gate
import explain
import persist
from ui_practice import meaning_group, notes_box, practice_panel

CONF = {"high": "확신 높음", "medium": "확신 보통", "low": "확신 낮음", "none": ""}
SOURCE = {"script": "문자 체계로 본 것", "words": "자주 쓰는 낱말로 본 것", "none": ""}

st.title("내 문장")
st.caption("연습할 문장이나 가사를 한 줄에 하나씩 쓰거나 붙여 넣어요. 어떤 언어인지 몰라도 돼요. "
           + ("로그인하면 입력한 내용이 **묶음**으로 서버에 저장돼서(최대 50개) 다음에 골라서 이어 쓸 수 있어요(저장을 끄면 저장하지 않아요)." if auth_gate.is_user()
              else "게스트로는 이 화면에만 있고 저장되지 않아요."))

if "lyrics" not in st.session_state:
    st.session_state["lyrics"] = ""


def _clear_answers():
    """줄마다 확인한 언어 답과 '언어 알아보기' 결과를 비운다(다른 묶음을 불러오거나 새로 시작할 때 이전 묶음의 답이 남지 않게)."""
    for k in [k for k in st.session_state if str(k).startswith(("lyr_ans_", "lyr_pick_"))]:
        del st.session_state[k]
    for k in ("lyr_det", "lyr_det_for"):
        st.session_state.pop(k, None)


def restore_text_set(set_id):
    """'불러오기' 버튼의 on_click: 저장된 묶음의 글·제목·줄마다 확인한 언어를 입력칸과 언어 확인 단계에 되살리고 그 묶음을 '지금 묶음'으로 한다
    (콜백은 위젯이 만들어지기 전에 실행됨). 이후 자동 저장은 이 묶음을 갱신한다."""
    saved = persist.saved_text(set_id) if set_id is not None else None
    if not saved:
        st.toast("묶음을 불러오지 못했어요.", icon="⚠️")
        return
    entries = saved.get("lines") or []
    _clear_answers()
    st.session_state["lyrics"] = "\n".join(e["text"] for e in entries)
    st.session_state["lyr_title"] = saved.get("title") or ""
    dets = {}
    for e, k in zip(entries, wp.line_keys([e["text"] for e in entries])):      # 아래 keys와 같은 공식(같은 글이 반복되면 열쇠에 번호가 붙는다)
        ln = e["text"]
        sug = languages.suggest_line_language(ln)
        dets[k] = sug
        langs = e.get("languages") or []
        if langs:
            if sug["primary"] and sug["primary"] == langs[0]:
                st.session_state[f"lyr_ans_{k}"] = "네"
            else:
                st.session_state[f"lyr_ans_{k}"] = "아니오"
                st.session_state[f"lyr_pick_{k}"] = [c for c in langs if c in languages.COMMON]
    st.session_state["lyr_det"] = dets
    st.session_state["lyr_det_for"] = True
    st.session_state["lyr_confirm_del"] = False
    persist.use_text(set_id)


def new_text_set():
    """'새 묶음으로 시작' 버튼의 on_click: 입력칸·제목·언어 답을 비우고 지금 묶음과의 연결을 끊는다(다음 입력의 첫 저장이 새 묶음이 된다)."""
    _clear_answers()
    st.session_state["lyrics"] = ""
    st.session_state["lyr_title"] = ""
    st.session_state["lyr_confirm_del"] = False
    persist.start_new_text()


def ask_delete():
    """'이 묶음 삭제' 버튼의 on_click: 삭제 확인 단계를 켠다(실수로 지우지 않게 두 번 누르게 함)."""
    st.session_state["lyr_confirm_del"] = True


def cancel_delete():
    """'취소' 버튼의 on_click: 삭제 확인 단계를 끈다."""
    st.session_state["lyr_confirm_del"] = False


def do_delete(set_id):
    """'삭제하기' 버튼의 on_click: 묶음을 지우고(줄은 함께, 연습 기록은 남음) 입력칸을 비운다."""
    if persist.delete_text_set(set_id):
        new_text_set()
        st.session_state["lyr_set_pick"] = None
        st.toast("묶음을 삭제했어요.")
    else:
        st.session_state["lyr_confirm_del"] = False


def load_example():
    """예시 묶음을 입력칸에 넣는다(버튼의 on_click: 입력 위젯이 만들어지기 전에 값을 바꿀 수 있다)."""
    st.session_state["lyrics"] = wp.example_set(st.session_state["lyr_example"])


# ---------- 0. 저장된 묶음 (로그인한 사용자) ----------
# 묶음 하나 = 입력창 하나의 내용 전체. 입력을 고치는 동안은 같은 묶음이 자동 저장으로 갱신되고, "새 묶음으로 시작"을 눌러야 새 묶음이 만들어진다.
if auth_gate.is_user():
    sets = persist.text_sets()
    by_id = {x["id"]: x for x in sets}
    cur = st.session_state.get("text_id")
    with st.container(border=True):
        if sets:
            pick = st.selectbox("저장된 묶음", list(by_id), index=None, format_func=lambda i: wp.text_set_label(by_id[i]), key="lyr_set_pick",
                                placeholder=f"저장된 묶음 {len(sets)}개 · 골라서 불러오기")
            b1, b2 = st.columns(2)
            b1.button("불러오기", type="primary", key="lyr_set_load", on_click=restore_text_set, args=(pick,), disabled=pick is None, width="stretch")
            b2.button("새 묶음으로 시작", key="lyr_set_new", on_click=new_text_set, width="stretch")
        else:
            st.caption("저장된 묶음이 아직 없어요. 아래에 입력하면 첫 묶음으로 자동 저장돼요(저장을 켜 둔 경우).")
        if cur in by_id:
            st.caption(f"지금 묶음: {wp.text_set_label(by_id[cur])}")
            if st.session_state.get("lyr_confirm_del"):
                st.warning(f"이 묶음({by_id[cur]['n_lines']}줄)을 삭제할까요? 연습 기록은 남아요.")
                d1, d2 = st.columns(2)
                d1.button("삭제하기", type="primary", key="lyr_del_yes", on_click=do_delete, args=(cur,), width="stretch")
                d2.button("취소", key="lyr_del_no", on_click=cancel_delete, width="stretch")
            else:
                st.button("이 묶음 삭제", key="lyr_del_ask", on_click=ask_delete)
        elif sets:
            st.caption("지금은 저장되지 않은 새 입력이에요. 입력하면 새 묶음으로 저장돼요.")

# ---------- 1. 입력 (맨 위) ----------
text = st.text_area("문장", key="lyrics", height=150, label_visibility="collapsed",
                    placeholder="연습할 문장이나 가사를 한 줄에 하나씩 적거나 붙여 넣으세요. (영어, 일본어, 프랑스어 …)")
if auth_gate.is_user():
    st.text_input("제목 (선택)", key="lyr_title", max_chars=60, placeholder="제목 (선택): 비우면 첫 줄과 저장 시각으로 보여 드려요")
e1, e2, e3 = st.columns([1.3, 1.3, 3], vertical_alignment="center")
e1.selectbox("예시 묶음", wp.EXAMPLE_NAMES, key="lyr_example", label_visibility="collapsed")
e2.button("예시 문장 불러오기", on_click=load_example)
e3.caption("직접 쓴 문장이에요. 영어는 표준 발음이 이미 있어 과금되지 않고, 다른 언어는 처음 만들 때 과금돼요(작음).")

lines = wp.split_lyrics(text)
if not lines:
    st.stop()
keys = wp.line_keys(lines)          # 줄 내용으로 만든 열쇠: 줄을 고치면 그 줄의 답은 사라진다. 같은 글이 반복돼도(후렴) 열쇠가 겹치지 않는다

# ---------- 2. 언어 알아보기 ----------
st.subheader("언어 확인")
explain.show("lyr_lang")
det_for = st.session_state.get("lyr_det_for")
if st.button("언어 알아보기", type="primary", key="lyr_det_btn"):
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


st.button("제안이 있는 줄은 모두 맞아요", type="primary", on_click=confirm_all, key="lyr_all")
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

persist.autosave_texts([{"text": ln, "languages": answers[n]["languages"] if n in answers else None,
                         "lang": answers[n]["lang"] if n in answers else None} for n, ln in enumerate(lines, 1)],
                       title=st.session_state.get("lyr_title"))      # 로그인+저장 켬일 때만. 지금 묶음을 갱신하고, 묶음이 없으면 새로 만든다
if st.session_state.pop("text_rerun", False):
    st.rerun()                                                              # 저장했거나 상한에 처음 걸렸을 때: 최신 묶음 목록으로 화면을 다시 그린다(무한 반복 아님: 다음 실행에서는 저장할 것이 없다)
if st.session_state.get("text_limit"):
    st.warning("저장된 묶음이 50개예요. 새 묶음은 저장되지 않아요. 위에서 오래된 묶음을 삭제하면 다시 저장돼요(연습은 계속 할 수 있어요).")
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
meaning_group(line, lang, f"lyr_{a['key']}")                  # 한글 뜻(예시는 직접 쓴 뜻, 그 밖에는 버튼으로 AI 번역) + 일본어면 읽기·로마자
if not languages.uses_spaces(lang):
    st.caption("공백 없이 쓰는 언어라서 점수는 단어가 아니라 **글자 오류율(CER)** 이 중심이에요. 한자·가타카나는 히라가나 읽기로 바꿔 비교해요.")
notes_box(line, lang, f"lyr_{a['key']}")                      # 표현 설명(버튼, 단어·발음 기호·표현·문법·예문): '듣기' 바로 위
explain.show("meaning")                                        # 한글 뜻·표현 설명 버튼이 무엇을 보내고 어디에 저장하는지

# ---------- 4. 듣기 ----------
st.subheader("듣기")
explain.show("lyr_tts")
path, cached = wp.tts_target(line)
if cached:
    st.audio(path, format="audio/wav")
    st.caption("표준 발음(TTS)이에요. 또박또박 읽는 기계 음성이라 실제 노래·대화와 다를 수 있어요.")
else:
    st.caption("이 줄의 표준 발음은 아직 없어요. 만들면 OpenAI TTS를 한 번 불러서 **과금**돼요(같은 문장은 다시 만들지 않아요).")
    if st.button("표준 발음 만들기", type="primary", key=f"mk_{a['key']}"):
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
practice_panel(line, key=f"lyr_{no}_{lang}_{a['key']}", tts_path=path if cached else None, lang=lang, line_no=no)
