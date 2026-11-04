"""웹 앱의 따라읽기·받아쓰기 부품이 쓰는 계산·글 만들기(화면 코드는 app/ui_practice.py). 검토 문서 16.10.

여기서 하는 일: ① 가사 글을 줄로 나누기 ② practice.py가 받는 prep(dict) 만들기 ③ 표준 발음 음성(TTS)의 캐시 상태 확인과 만들기
④ 채점 결과(scoring.evaluate)를 화면용 HTML 조각(결과 카드·단어 대조·입력 상태 칩)으로 바꾸기.
채점·인식은 practice.py·scoring.py·stt.py가 하고, 이 모듈은 **그 결과를 화면용으로 바꾸기만** 한다(계산을 새로 하지 않는다).

수업과의 관계
- [수업에 없음] 이 모듈 전체. HTML 조각은 Streamlit의 `st.markdown(..., unsafe_allow_html=True)`로 그린다. 사용자가 적은 글이 들어가므로
  모든 글자를 `html.escape`로 바꿔 넣는다(HTML 태그로 해석되는 것을 막는 기본 안전장치).
"""
import html

import scoring
import theme
import tts

EXAMPLE_IDS = ("1", "2", "3", "6")        # "예시 문장 불러오기"에 쓰는 sentences.csv의 문장 번호(이미 TTS 캐시가 있음)


def split_lyrics(text):
    """가사 글을 줄 목록으로 나눈다(앞뒤 공백을 지우고 빈 줄은 뺀다)."""
    return [ln.strip() for ln in str(text).splitlines() if ln.strip()]


def example_lyrics(ids=EXAMPLE_IDS, sentences=None):
    """sentences.csv의 예시 문장들을 한 줄에 하나씩 이은 글을 돌려준다."""
    sentences = tts.load_sentences() if sentences is None else sentences
    by_id = {s["id"]: s["sentence"] for s in sentences}
    return "\n".join(by_id[i] for i in ids if i in by_id)


def make_prep(text, lang="en", tts_path=None, meaning_ko=""):
    """practice.read·dictation에 넘길 prep을 만든다. TTS를 부르지 않는다(practice.prepare는 문장마다 TTS를 만들어 과금될 수 있어서)."""
    prep = {"error": None, "row": None, "id": "직접 입력", "text": str(text).strip(), "lang": lang,
            "meaning_ko": meaning_ko, "tts_path": tts_path, "tts_new": False}
    if not prep["text"]:
        prep["error"] = "문장이 비어 있습니다."
    return prep


def tts_target(text, sentences=None):
    """문장 text의 표준 발음 음성 캐시 경로와 이미 있는지를 (경로, 있음)으로 돌려준다.

    sentences.csv의 문장과 (정규화해서) 같으면 그 문장의 캐시 파일(s01.wav 등)을 쓴다. 그래서 예시 문장은 과금 없이 재생된다."""
    sentences = tts.load_sentences() if sentences is None else sentences
    key = scoring.normalize(text, unify=False)
    for s in sentences:
        if scoring.normalize(s["sentence"], unify=False) == key:
            _row, path = tts.lookup_sentence(s["id"], sentences)
            return path, path.exists()
    _row, path = tts.lookup_sentence(text, sentences)
    return path, path.exists()


def make_tts(text, sentences=None):
    """표준 발음 음성을 준비한다. 캐시에 있으면 API를 부르지 않는다(없으면 OpenAI TTS 호출 = 과금). 파일 경로를 돌려준다."""
    path, _cached = tts_target(text, sentences)
    return tts.tts_wav(str(text).strip(), path)


# ---------- 채점 결과 → 화면용 조각 ----------
def word_cells(ops):
    """scoring의 ops([(종류, 정답, 인식), …])를 단어 대조용 칸 목록 [{"ref", "hyp", "kind"}]으로 바꾼다.
    kind: same(일치) / sub(바뀜) / del(빠짐) / ins(더해짐). 빠진 칸의 hyp와 더해진 칸의 ref는 빈 글."""
    kinds = {"일치": "same", "치환": "sub", "삭제": "del", "삽입": "ins"}
    return [{"ref": a or "", "hyp": b or "", "kind": kinds[k]} for k, a, b in ops]


_LABEL = {"sub": "바뀜", "del": "빠짐", "ins": "더해짐"}


def diff_html(ops):
    """단어 대조 HTML: 위 줄은 기준(정답), 아래 줄은 인식(또는 내가 적은 글). 틀린 칸은 보라 + 물결 밑줄 + 이름표(바뀜·빠짐·더해짐).
    색만으로 구분하지 않으려고 밑줄과 이름표를 함께 쓴다(검토 문서 16.9의 결정)."""
    cells = []
    for c in word_cells(ops):
        ref, hyp = html.escape(c["ref"]) or "—", html.escape(c["hyp"]) or "—"
        if c["kind"] == "same":
            cells.append(f'<span class="sl-cell"><span>{ref}</span><span>{hyp}</span></span>')
        else:
            cells.append(f'<span class="sl-cell sl-wrong"><span>{ref}</span><span class="sl-und">{hyp}</span>'
                         f'<small>{_LABEL[c["kind"]]}</small></span>')
    return f'<div class="sl-diff">{"".join(cells)}</div>'


def pct(rate):
    """오류율(0.25) → '25.0%'. 1을 넘어도 그대로 보여 준다(WER은 1을 넘을 수 있음)."""
    return f"{rate * 100:.1f}%"


def result_card_html(score):
    """채점 결과 카드 HTML(짙은 초록 바탕에 라임 숫자). score는 scoring.evaluate의 결과.
    '일치율'이 아니라 오류율과 바뀜·빠짐·더해짐 개수로 보여 준다(WER은 1을 넘을 수 있어서)."""
    w, c = score["wer"], score["cer"]
    main = score["main"]
    return (
        '<div class="sl-result">'
        '<div class="sl-result-head">채점 결과 <small>발음 점수가 아니라 문장 인식 오류율이에요</small></div>'
        '<div class="sl-result-grid">'
        f'<div><span>단어 오류율 · WER</span><b>{pct(w["rate"])}</b><small>{w["N"]}단어 중 {w["distance"]}개가 달라요</small></div>'
        f'<div><span>글자 오류율 · CER</span><b>{pct(c["rate"])}</b><small>{c["N"]}글자 중 {c["distance"]}개 (공백 제외)</small></div>'
        f'<div><span>오류 종류</span><b>{main["S"]} · {main["D"]} · {main["I"]}</b><small>바뀜 · 빠짐 · 더해짐</small></div>'
        '</div>'
        '<p>둘 다 오류율이라 낮을수록 좋아요. We\'ll과 We will은 같은 것으로 봐요.</p>'
        '</div>')


def quality_chips(quality):
    """녹음 입력 상태(quality.analyze의 결과)를 [(글, 괜찮은가)] 칩 목록으로 바꾼다: 음량 · 무음 · 클리핑."""
    m = quality["metrics"]
    from quality import MAX_CLIP_RATIO, MAX_SILENT_RATIO, MIN_PEAK, MIN_RMS_DBFS
    loud_ok = m.get("rms_dbfs", -99) >= MIN_RMS_DBFS and m.get("peak", 0) >= MIN_PEAK
    return [("음량 적정" if loud_ok else "소리가 작음", loud_ok),
            ("무음 구간 적음" if m.get("silent_ratio", 0) < MAX_SILENT_RATIO else "대부분 무음", m.get("silent_ratio", 0) < MAX_SILENT_RATIO),
            ("클리핑 없음" if m.get("clip_ratio", 0) < MAX_CLIP_RATIO else "소리가 잘림", m.get("clip_ratio", 0) < MAX_CLIP_RATIO)]


def chips_html(chips):
    return "".join(f'<span class="sl-chip {"ok" if ok else "warn"}">{"✓" if ok else "!"} {html.escape(t)}</span>' for t, ok in chips)


def css():
    """결과 카드·단어 대조·칩의 스타일(`<style>` 블록). 색은 theme.py의 브랜드 색을 쓴다."""
    return f"""<style>
.sl-result {{ background:{theme.FOREST}; color:#fff; border-radius:20px; padding:20px 24px; margin:12px 0; }}
.sl-result-head {{ font-weight:800; font-size:1.1rem; margin-bottom:12px; }}
.sl-result-head small {{ font-weight:400; opacity:.75; margin-left:8px; font-size:.8rem; }}
.sl-result-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
.sl-result-grid > div {{ background:rgba(255,255,255,.07); border-radius:14px; padding:12px 16px; }}
.sl-result-grid span {{ display:block; font-size:.78rem; opacity:.8; }}
.sl-result-grid b {{ display:block; font-size:2rem; color:{theme.LIME}; line-height:1.3; }}
.sl-result-grid small {{ opacity:.7; }}
.sl-result p {{ margin:12px 0 0; font-size:.82rem; opacity:.8; }}
.sl-diff {{ display:flex; flex-wrap:wrap; gap:6px; margin:8px 0; }}
.sl-cell {{ display:inline-flex; flex-direction:column; align-items:center; padding:4px 8px; border-radius:10px; font-size:1.05rem; }}
.sl-wrong {{ background:#ece9fb; color:#4a3bb0; }}
.sl-und {{ text-decoration:underline wavy {theme.PURPLE}; text-underline-offset:4px; font-weight:700; }}
.sl-cell small {{ font-size:.65rem; font-weight:700; color:{theme.PURPLE}; }}
.sl-chip {{ display:inline-block; border-radius:999px; padding:2px 10px; margin:0 6px 4px 0; font-size:.8rem;
  background:rgba(255,255,255,.1); color:#fff; border:1px solid rgba(255,255,255,.25); }}
.sl-chip.warn {{ background:{theme.LIME}; color:{theme.FOREST}; border-color:{theme.LIME}; font-weight:700; }}
</style>"""
