"""웹 앱의 따라읽기·받아쓰기 부품이 쓰는 계산·글 만들기(화면 코드는 app/ui_practice.py). 검토 문서 16.10.

여기서 하는 일: ① 가사 글을 줄로 나누기 ② practice.py가 받는 prep(dict) 만들기 ③ 표준 발음 음성(TTS)의 캐시 상태 확인과 만들기
④ 채점 결과(scoring.evaluate)를 화면용 HTML 조각(결과 카드·단어 대조·입력 상태 칩)으로 바꾸기.
채점·인식은 practice.py·scoring.py·stt.py가 하고, 이 모듈은 **그 결과를 화면용으로 바꾸기만** 한다(계산을 새로 하지 않는다).

수업과의 관계
- [수업에 없음] 이 모듈 전체. HTML 조각은 Streamlit의 `st.markdown(..., unsafe_allow_html=True)`로 그린다. 사용자가 적은 글이 들어가므로
  모든 글자를 `html.escape`로 바꿔 넣는다(HTML 태그로 해석되는 것을 막는 기본 안전장치).
"""
import html

import numpy as np

import audio
import japanese
import languages
import practice
import report
import scoring
import theme
import tts

EXAMPLE_IDS = ("1", "2", "3", "6")

# 언어별 예시 묶음(내 문장의 "예시 문장 불러오기", 이슈 #50). **모두 이 프로젝트에서 직접 쓴 문장**이다(출처·라이선스: 직접 작성(본인)).
# 영어는 sentences.csv의 문장 4개(표준 발음 캐시가 있어 과금 없음), 나머지는 새 문장이라 표준 발음을 처음 만들 때 OpenAI TTS 과금이 있다.
# 상업 노래의 가사는 코드·예시에 넣지 않는다(CLAUDE.md Privacy): 섞인 예도 일본어와 영어가 한 줄에 섞이는 **모양**만 보여 주는 직접 쓴 문장이다.
EXAMPLE_SETS = {
    "영어": None,                                           # example_lyrics()의 sentences.csv 문장
    "일본어": ["朝の光が部屋を満たしている。", "明日の天気を教えてください。", "駅までの道を教えてもらえますか。", "一緒に歌えば、きっと楽しいよ。"],
    "프랑스어": ["Je voudrais un café, s'il vous plaît.", "Où est la gare, s'il vous plaît ?",
              "Nous allons chanter ensemble ce soir.", "Il fait beau aujourd'hui, allons nous promener."],
    "일본어+영어 섞인 예": ["今夜は Moonlight の下で踊ろう", "Hold my hand 少しだけ待って", "甘い Coffee 苦い Memory", "Just smile ねえ、笑って"],
}
EXAMPLE_NAMES = list(EXAMPLE_SETS)

# 일본어·프랑스어·섞인 예의 한글 뜻(직접 씀). 영어 예시의 뜻은 sentences.csv의 meaning_ko를 쓴다(example_meanings).
_MEANINGS_KO = {
    "朝の光が部屋を満たしている。": "아침 햇살이 방을 가득 채우고 있어요.", "明日の天気を教えてください。": "내일 날씨를 알려 주세요.",
    "駅までの道を教えてもらえますか。": "역까지 가는 길을 알려 주시겠어요?", "一緒に歌えば、きっと楽しいよ。": "함께 노래하면 분명 즐거울 거예요.",
    "Je voudrais un café, s'il vous plaît.": "커피 한 잔 주세요.", "Où est la gare, s'il vous plaît ?": "기차역이 어디예요?",
    "Nous allons chanter ensemble ce soir.": "우리는 오늘 저녁에 함께 노래할 거예요.",
    "Il fait beau aujourd'hui, allons nous promener.": "오늘은 날씨가 좋아요, 산책하러 가요.",
    "今夜は Moonlight の下で踊ろう": "오늘 밤은 달빛 아래에서 춤추자.", "Hold my hand 少しだけ待って": "내 손을 잡아, 잠깐만 기다려 줘.",
    "甘い Coffee 苦い Memory": "달콤한 커피, 쓴 기억.", "Just smile ねえ、笑って": "그냥 웃어 봐, 있잖아, 웃어 줘.",
}


def example_meanings(sentences=None):
    """예시 문장(글) → 한글 뜻. 영어는 sentences.csv의 meaning_ko, 나머지는 직접 쓴 뜻."""
    sentences = tts.load_sentences() if sentences is None else sentences
    out = {s["sentence"]: s["meaning_ko"] for s in sentences if s.get("meaning_ko")}
    out.update(_MEANINGS_KO)
    return out


def example_set(name, sentences=None):
    """예시 묶음 이름 → 한 줄에 하나씩 이은 글. "영어"는 sentences.csv의 문장(example_lyrics)."""
    if name not in EXAMPLE_SETS:
        raise ValueError(f"알 수 없는 예시 묶음: {name!r}")
    return example_lyrics(sentences=sentences) if EXAMPLE_SETS[name] is None else "\n".join(EXAMPLE_SETS[name])        # "예시 문장 불러오기"에 쓰는 sentences.csv의 문장 번호(이미 TTS 캐시가 있음)


def split_lyrics(text):
    """가사 글을 줄 목록으로 나눈다(앞뒤 공백을 지우고 빈 줄은 뺀다)."""
    return [ln.strip() for ln in str(text).splitlines() if ln.strip()]


def line_keys(lines):
    """줄 목록 → 줄마다 화면 위젯의 열쇠(같은 길이의 문자열 목록). 줄 내용의 해시로 만들어 줄을 고치면 그 줄의 답이 사라지고,
    **같은 글이 여러 번 나오면(반복되는 후렴 등) 두 번째부터 `_1`, `_2`를 붙여** 위젯 열쇠가 겹치지 않게 한다
    (겹치면 Streamlit이 StreamlitDuplicateElementKey를 낸다, 11-08 서버에서 발견). 같은 입력이면 같은 열쇠다(같은 프로세스 안에서; 파이썬 해시는 실행마다 달라진다)."""
    seen, keys = {}, []
    for ln in lines:
        base = f"{abs(hash(ln)) % 10**8}"
        n = seen.get(base, 0)
        seen[base] = n + 1
        keys.append(base if n == 0 else f"{base}_{n}")
    return keys


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


def normalized_sounds(tts_path, recording, names=("표준 발음", "내 녹음"), sr=audio.TARGET_SR, peak=0.9):
    """소리 모양 비교용으로 표준 발음(경로)과 내 녹음(경로 또는 bytes)을 읽어 [(이름, 16 kHz 모노 파형)]으로 돌려준다.

    [수업과 같음] 읽기·모노 변환·16 kHz 리샘플링은 audio.load_audio가 한다(02: PCM16 읽기 ÷32768, 스테레오는 채널 평균, `resample_poly`).
    음성 인식과 그림에 16 kHz 모노를 쓰는 이유는 02 4교시 "왜 16,000Hz 모노로 준비하나요?"와 같다(말소리 정보는 8 kHz 아래에 대부분 있다: 나이퀴스트).
    [수업에 없음] 최대 진폭을 peak로 맞추는 정규화(수업 02의 최대 진폭·RMS 관찰을 두 소리의 비교에 응용).

    두 소리의 **모양**만 비교하려고 최대 진폭을 peak(0.9)로 맞춘다(마이크 음량 차이는 그림에서 지운다. 완전한 무음이면 그대로 둠).
    둘 중 하나라도 읽을 수 없으면 그 예외를 그대로 올린다(호출한 화면이 안내 문구로 바꾼다)."""
    out = []
    for name, src in zip(names, (tts_path, recording)):
        x, _sr, _ch = audio.load_audio(src, sr)
        out.append((name, (x / max(float(np.abs(x).max()), 1e-9) * peak).astype(np.float32)))
    return out


def error_spans(prep, res, locate=None):
    """따라읽기 결과에서 **틀린 단어가 소리의 어디인지**(TTS와 내 녹음의 시간 구간)를 구해 돌려준다. 그림은 그리지 않는다(화면이 plot_error_spans로 그림).

    돌려주는 dict: {"blocks": 틀린 덩어리 수, "text": 덩어리별 시간 구간 글(report.error_blocks), "sounds": plot_error_spans에 넘길 목록, "loc": align 결과}.
    틀린 덩어리가 없으면 blocks=0이고 text·sounds는 빈 값이다. 표준 발음(prep["tts_path"])이 없거나 채점 오류면 ValueError.
    내부에서 인식을 **두 번**(내 녹음, TTS; 단어별 시간 모드, tiny, VAD 켬) 더 돌려 몇 초 걸린다(practice.locate_errors, 노트북 '틀린 구간 표시'와 같은 경로).
    구간은 Whisper가 추정한 단어 시간이라 **대략의 위치**이고 평가가 아니다. locate: 테스트에서 가짜 함수를 넣는 자리."""
    if not prep.get("tts_path"):
        raise ValueError("표준 발음이 없어 틀린 구간을 표시할 수 없습니다.")
    if res.get("error") or not res.get("recording"):
        raise ValueError("채점 결과가 없어 틀린 구간을 표시할 수 없습니다.")
    out = (locate or practice.locate_errors)(prep, res)
    blocks = out["loc"]["blocks"]
    if not blocks:
        return {"blocks": 0, "text": "", "sounds": [], "loc": out["loc"]}
    return {"blocks": len(blocks), "text": report.error_blocks(prep, out["loc"]), "sounds": out["sounds"], "loc": out["loc"]}


def apply_japanese_reading(prep, res):
    """일본어(ja) 채점 결과를 **히라가나 읽기 기준**으로 다시 계산한다(이슈 #50): 기준 문장과 인식·입력 글을 둘 다 읽기로 바꿔 비교하므로
    한자·가타카나·히라가나 표기 차이가 오류로 세어지지 않는다. res를 제자리에서 고쳐 돌려준다.

    res["score_raw"]에 원문 기준 점수를 남기고 res["score"]를 읽기 기준 점수로 바꾸며, res["reading"]에 화면에 보여 줄 읽기·로마자를 넣는다:
    {"ref": 기준 읽기, "ref_romaji", "hyp": 인식·입력 읽기, "hyp_romaji"}. 일본어가 아니거나 오류 결과이거나 pykakasi가 없으면 아무것도 바꾸지 않는다.
    한계: 영어 단어는 읽기로 바뀌지 않아(Coffee ≠ こーひー) 섞인 줄은 영어 부분이 계속 다르게 셈된다."""
    if prep.get("lang") != "ja" or res.get("error") or not res.get("score") or not japanese.available():
        return res
    ref_r, ref_ro = japanese.readings(prep["text"])
    hyp_r, hyp_ro = japanese.readings(res.get("hyp") or "")
    res["score_raw"] = res["score"]
    res["score"] = scoring.evaluate(ref_r, hyp_r, "ja")
    res["reading"] = {"ref": ref_r, "ref_romaji": ref_ro, "hyp": hyp_r, "hyp_romaji": hyp_ro}
    return res


def reading_caption(text):
    """일본어 한 줄 밑에 보여 줄 '읽기 · 로마자' 글(pykakasi가 없거나 읽을 것이 없으면 빈 글)."""
    r, ro = japanese.readings(text)
    return f"읽기: {r} · 로마자: {ro}" if r and ro else ""


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
    '일치율'이 아니라 오류율과 바뀜·빠짐·더해짐 개수로 보여 준다(WER은 1을 넘을 수 있어서).
    일본어·중국어처럼 **공백 없이 쓰는 언어**는 글 전체가 단어 하나로 세어져 WER이 0% 또는 100%뿐이라, WER 칸은 "—"와 이유로 바꾸고 글자 오류율(CER)을 본다(이슈 #50)."""
    w, c = score["wer"], score["cer"]
    main = score["main"]
    if main is c:                                        # evaluate가 main으로 CER 결과를 그대로 돌려준 경우(공백 없는 언어)
        wer_box = ('<div><span>단어 오류율 · WER</span><b>—</b>'
                   '<small>공백 없이 쓰는 언어라 단어로 나눌 수 없어요. 글자 오류율을 봐요</small></div>')
    else:
        wer_box = f'<div><span>단어 오류율 · WER</span><b>{pct(w["rate"])}</b><small>{w["N"]}단어 중 {w["distance"]}개가 달라요</small></div>'
    return (
        '<div class="sl-result">'
        '<div class="sl-result-head">채점 결과 <small>발음 점수가 아니라 문장 인식 오류율이에요</small></div>'
        '<div class="sl-result-grid">'
        + wer_box +
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


# ---------- Azure 발음 평가 결과 → 화면용 조각 (이슈 #48) ----------
LOCALES = {code: v[1] for code, v in languages.LANGS.items()}   # prep["lang"] → Azure 로캘(표는 languages.py). 영어 외의 발음 평가 지원은 확인 전(미확인)
AZURE_LABELS = [("accuracy", "정확도", "음소가 원어민 발음과 얼마나 가까운가"), ("fluency", "유창성", "단어 사이 쉼이 자연스러운가"),
                ("completeness", "완성도", "기준 문장 중 발음된 단어의 비율"), ("prosody", "운율", "억양·강세·속도·리듬(영어만)"),
                ("pronunciation", "종합", "위 항목을 합친 참고 점수")]
ERROR_LABELS = {"Mispronunciation": "발음", "Omission": "빠짐", "Insertion": "더해짐", "UnexpectedBreak": "쉼 많음", "MissingBreak": "쉼 없음", "Monotone": "단조로움"}
BREAK_LABELS = {"UnexpectedBreak": "쉼 많음", "MissingBreak": "쉼 없음"}      # 운율 피드백의 단어 앞 쉼(영어만)


def azure_cards_html(result):
    """Azure 점수 카드(정확도·유창성·완성도·운율·종합). 점수가 없는 항목(영어가 아니면 운율)은 '해당 없음'으로 흐리게 표시한다.
    점수가 낮으면(poor) 글자색을 보라로 한다(빨강은 쓰지 않는 규칙)."""
    import azure_pronunciation as ap
    cards = []
    for key, name, desc in AZURE_LABELS:
        score = result["scores"].get(key)
        if score is None:
            cards.append(f'<div class="sl-az-card sl-az-na"><span>{name}</span><b>—</b><small>{html.escape(desc)} · 이 언어는 제공되지 않아요</small></div>')
        else:
            cards.append(f'<div class="sl-az-card lvl-{ap.level(score)}"><span>{name}</span><b>{score:.0f}</b><small>{html.escape(desc)}</small></div>')
    return f'<div class="sl-az-grid">{"".join(cards)}</div>'


def azure_words_html(result):
    """단어별 정확도. 점수가 낮거나(poor) 오류 종류가 있는 단어는 보라 + 물결 밑줄 + 이름표(색만으로 구분하지 않음), 보통(fair)은 점수만 흐리게."""
    cells = []
    for w in result["words"]:
        kind = ERROR_LABELS.get(w["error_type"], "" if w["error_type"] in (None, "None") else w["error_type"])
        score = "" if w["accuracy"] is None else f'{w["accuracy"]:.0f}'
        breaks = [BREAK_LABELS[b] for b in (w.get("prosody") or {}).get("break", []) if b in BREAK_LABELS]
        weak = w["level"] == "poor" or bool(kind)
        label = "".join(f"<small>{html.escape(x)}</small>" for x in ([kind] if kind else []) + breaks)
        cls = "sl-cell sl-wrong" if weak else ("sl-cell sl-fair" if w["level"] == "fair" else "sl-cell")
        word = html.escape(w["word"] or "")
        cells.append(f'<span class="{cls}"><span class="{"sl-und" if weak else ""}">{word}</span><span class="sl-az-score">{score}</span>{label}</span>')
    return f'<div class="sl-diff">{"".join(cells)}</div>'


def phoneme_lines(result, levels=("poor", "fair")):
    """점수가 낮은 단어(poor·fair)의 음소 점수를 글 한 줄씩으로: 'explore: ɛ 47 (ə로 들림) · k 90 …'. 음소 정보가 없는 단어는 건너뛴다."""
    lines = []
    for w in result["words"]:
        named = [ph for ph in w["phonemes"] if ph.get("phoneme")]      # 일본어·프랑스어는 음소 점수만 오고 음소 이름이 없을 수 있다(공식 문서)
        if w["level"] not in levels or not named:
            continue
        parts = []
        for ph in named:
            score = "?" if ph["accuracy"] is None else f'{ph["accuracy"]:.0f}'
            parts.append(f'{ph["phoneme"]} {score}' + (f' ({ph["heard"]}로 들림)' if ph["heard"] else ""))
        lines.append(f'{w["word"]}: ' + " · ".join(parts))
    return lines


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
.sl-az-grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin:8px 0; }}
.sl-az-card {{ border:1px solid #cfe0d3; border-radius:14px; padding:10px 12px; background:#fff; }}
.sl-az-card span {{ display:block; font-size:.8rem; opacity:.8; }}
.sl-az-card b {{ display:block; font-size:1.8rem; line-height:1.3; color:{theme.BUTTON_GREEN}; }}
.sl-az-card small {{ font-size:.68rem; opacity:.65; }}
.sl-az-card.lvl-fair b {{ color:{theme.FOREST}; }}
.sl-az-card.lvl-poor b {{ color:{theme.PURPLE}; }}
.sl-az-na {{ background:#f4f4f2; }} .sl-az-na b {{ color:#9a9a96; }}
.sl-fair {{ background:#f1fbc8; }}
.sl-az-score {{ font-size:.7rem; opacity:.7; }}
.sl-chip {{ display:inline-block; border-radius:999px; padding:2px 10px; margin:0 6px 4px 0; font-size:.8rem;
  background:rgba(255,255,255,.1); color:#fff; border:1px solid rgba(255,255,255,.25); }}
.sl-chip.warn {{ background:{theme.LIME}; color:{theme.FOREST}; border-color:{theme.LIME}; font-weight:700; }}
</style>"""


def azure_prosody_notes(result):
    """운율 피드백에서 학습자에게 알릴 문장들. 단조로움(Monotone)은 발화 전체를 한 번 판정해 모든 단어에 같은 태그가 붙으므로 **한 번만** 알린다."""
    notes = []
    if any("Monotone" in (w.get("prosody") or {}).get("intonation", []) for w in result["words"]):
        notes.append("억양이 단조롭게 들렸어요(발화 전체에 대한 판정이에요).")
    return notes
