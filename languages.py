"""언어에 대한 표와 규칙: 이름, Azure 로캘, 공백 여부, 글에서 언어 제안, 감지 확률에서 제안, 사용자의 답 → STT 옵션 (이슈 #50, 검토 문서 16.14).

모두 **순수 함수**라서 소리·모델·네트워크 없이 단위 테스트를 할 수 있다. 여러 모듈이 같은 표를 쓰려고 한곳에 모았다:
stt(언어 코드), scoring(공백 없는 언어), Azure 호출(로캘), 화면(언어 이름·선택 목록).
언어 코드는 Whisper와 같은 두 글자 코드(`en`, `ja`, `fr`, `ko` …)다.

수업과의 관계
- [수업에 없음] 이 모듈 전체. 수업 07은 한국어(`language="ko"`) 하나만 썼다. 문자 체계 판별은 유니코드 범위(히라가나 U+3040~309F, 가타카나 U+30A0~30FF,
  한글 U+AC00~D7A3, 키릴 U+0400~04FF, 한자 U+4E00~9FFF)를 비교하는 것으로, 자습 노트북 `normalize`의 유니코드·정규식 처리와 같은 계열이다.
- 한계: 라틴 문자는 영어·프랑스어·스페인어·스웨덴어를 구분하지 못하고, 한자만 있는 글은 일본어와 중국어를 구분하지 못한다. 그래서 결과를 **제안**으로만 쓰고
  확정은 사용자가 한다(`assumed`가 True면 "가정"이라는 뜻).
"""
# 코드 → (한국어 이름, Azure 로캘). 로캘은 음성 인식에서 쓰는 대표 값이고 **발음 평가의 지원 범위는 로캘마다 다르다**(영어 en-US는 운율·음소까지, 일본어·프랑스어는 기본 점수가 나오는 것을 사용자가 확인함(11-11), 나머지 로캘은 [미확인]).
LANGS = {
    "en": ("영어", "en-US"), "ja": ("일본어", "ja-JP"), "ko": ("한국어", "ko-KR"), "fr": ("프랑스어", "fr-FR"),
    "es": ("스페인어", "es-ES"), "de": ("독일어", "de-DE"), "zh": ("중국어", "zh-CN"), "it": ("이탈리아어", "it-IT"),
    "pt": ("포르투갈어", "pt-BR"), "ru": ("러시아어", "ru-RU"), "sv": ("스웨덴어", "sv-SE"),
}
COMMON = tuple(LANGS)                       # 화면의 기본 선택 목록(순서 고정)
NO_SPACE = ("ja", "zh")                     # 단어 사이에 공백이 없는 언어: 줄을 공백 없이 잇고 채점은 글자(CER) 중심
NO_LOWER = ("ja", "zh", "ko")               # 대소문자가 없는 문자 체계(소문자화를 하지 않음)


def name(code):
    """언어 코드 → 한국어 이름. 목록에 없는 코드는 코드 그대로."""
    return LANGS.get(code, (code, None))[0]


def azure_locale(code, default="en-US"):
    """언어 코드 → Azure 로캘. 목록에 없으면 default."""
    return LANGS.get(code, (None, default))[1] or default


def uses_spaces(code):
    """단어 사이에 공백이 있는 언어인가(일본어·중국어는 False)."""
    return code not in NO_SPACE


# ---------- 글에서 언어 제안 (문자 체계) ----------
def _scripts(text):
    """글에 들어 있는 문자 체계별 글자 수: {"kana", "hangul", "han", "cyrillic", "latin"}."""
    counts = {"kana": 0, "hangul": 0, "han": 0, "cyrillic": 0, "latin": 0}
    for ch in str(text):
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF:
            counts["kana"] += 1
        elif 0xAC00 <= o <= 0xD7A3 or 0x1100 <= o <= 0x11FF:
            counts["hangul"] += 1
        elif 0x4E00 <= o <= 0x9FFF:
            counts["han"] += 1
        elif 0x0400 <= o <= 0x04FF:
            counts["cyrillic"] += 1
        elif ch.isalpha() and o < 0x250:        # 기본 라틴 + 악센트 글자(é·ñ·ü 등)
            counts["latin"] += 1
    return counts


def detect_text_language(text):
    """글(한 줄 또는 여러 줄)의 문자 체계로 언어를 **제안**한다: {"languages": [코드…], "primary": 코드 또는 None, "assumed": bool, "scripts": {...}}.

    - 가나(히라가나·가타카나)가 있으면 일본어(같은 글의 한자도 일본어 글자로 셈), 한글은 한국어, 키릴 문자는 러시아어, 라틴 문자는 영어.
    - **primary(주 언어)는 "대략 음절 수"가 가장 많은 언어**다(이슈 #50: 영어가 대부분인 줄이 가나 몇 글자 때문에 일본어가 되지 않게, 반대로 일본어 줄에 영어 단어가 두어 개 섞였다고 영어가 되지도 않게). 같으면 라틴이 아닌 쪽이 우선.
      languages는 글에 나타난 언어들을 글자 수가 많은 순서로 적은 목록이다(일본어 글에 영어 단어가 섞이면 ["ja","en"]).
    - 한자만 있으면 일본어인지 중국어인지 구분할 수 없어 languages=[], primary=None.
    - 라틴 문자만 있으면 영어로 **가정**한다(assumed=True): 프랑스어·스페인어·스웨덴어 등과 문자로는 구분할 수 없다.
    - 글자가 하나도 없으면 languages=[], primary=None."""
    c = _scripts(text)
    # 글자 수를 그대로 비교하면 한자·가나 한 글자(대개 1~2 음절)가 라틴 문자 한 글자(약 0.4 음절)와 같은 무게가 되어, 영어 단어가 두어 개만 있어도 영어가 된다.
    # 그래서 "대략 음절 수"로 센다(가나·한글 1, 한자 2, 라틴·키릴 0.4). 표본 없이 정한 **잠정 가중치**다 [추정].
    weight = {}
    if c["kana"]:
        weight["ja"] = c["kana"] + 2 * c["han"]             # 가나가 있으면 한자도 일본어 글자로 센다
    if c["hangul"]:
        weight["ko"] = c["hangul"]
    if c["cyrillic"]:
        weight["ru"] = 0.4 * c["cyrillic"]
    if c["latin"]:
        weight["en"] = 0.4 * c["latin"]
    if not weight:
        return {"languages": [], "primary": None, "assumed": False, "scripts": c}
    # 무게가 큰 순서, 같으면 라틴(en)이 뒤로
    langs = sorted(weight, key=lambda k: (-weight[k], k == "en"))
    return {"languages": langs, "primary": langs[0], "assumed": langs == ["en"], "scripts": c}


def detect_lines_language(lines):
    """줄 목록 → 줄마다 detect_text_language 결과 목록. 줄마다 언어가 다를 수 있다(일본어 줄, 영어 줄, 섞인 줄)."""
    return [detect_text_language(ln) for ln in lines]


# ---------- 라틴 문자 글의 언어 제안 (자주 쓰는 낱말 + 악센트 글자) ----------
# 문자 체계만으로는 영어·프랑스어·스페인어 …를 구분할 수 없어서(위 detect_text_language는 영어로 "가정"만 한다), 라틴 문자 글은 언어마다 **자주 나오는 낱말**
# (관사·대명사·접속사·be 동사 같은 기능어)이 몇 개 들어 있는지와 **그 언어에 특징적인 글자**(é·ñ·ß·å 등)로 점수를 매겨 제안한다.
# 직접 만든 가벼운 규칙이라(새 의존성 없음) 짧은 글에서는 틀릴 수 있다. 그래서 결과는 "제안"이고 화면에서 사용자가 확인한다(이슈 #50, 검토 문서 16.14).
_STOPWORDS = {
    "en": "the and is are you to of a in that it for with my we i this be on at have can will do not your me what so but".split(),
    "fr": "le la les un une des et est je tu il elle nous vous ils de du en que qui pas pour dans ce cette avec sur au aux où plaît suis très mais ou ça".split(),
    "es": "el la los las un una y es que de en por para con no se mi tu su yo qué dónde está muy pero como".split(),
    "de": "der die das und ist ich du er sie wir ihr nicht ein eine mit zu auf für den dem was wo aber auch habe".split(),
    "it": "il lo gli le un una e è che di per con non mi ti io noi voi sono molto dove ma".split(),
    "pt": "o os as um uma e é que de em por para com não eu você nós está muito onde mas".split(),
    "sv": "och är jag du han hon vi ni det en ett att som på med inte för har var vad men".split(),
}
# 그 언어에 특징적인 글자(점수에 더함). 여러 언어가 공유하는 글자(ä: 독일어·스웨덴어)는 둘에 모두 더한다.
_CHAR_HINTS = {"fr": "éèêëàâçîïôùûœ", "es": "ñ¿¡áíóú", "de": "ßäöü", "sv": "åäö", "pt": "ãõçáâêô", "it": "ìòùè"}


def detect_latin_language(text):
    """라틴 문자 글의 언어를 낱말·글자 점수로 **제안**한다: {"top": 코드, "ranked": [(코드, 비율)], "confidence": "high"|"low"}.

    점수 = 그 언어의 자주 쓰는 낱말이 글에 나온 횟수 + 특징적인 글자 수(×0.5). 점수가 모두 0이면(짧거나 낱말이 겹치지 않는 글) 영어로 가정하고
    confidence="low"다. confidence="high"는 1등의 비율이 0.6 이상이고 점수가 2 이상일 때다. 표본 없이 정한 **잠정 기준**이다 [추정]."""
    import re
    t = str(text).lower()
    words = re.findall(r"[^\W\d_]+", t)
    scores = {}
    for code, stops in _STOPWORDS.items():
        sc = sum(1 for w in words if w in stops)
        sc += 0.5 * sum(1 for ch in t if ch in _CHAR_HINTS.get(code, ""))
        scores[code] = sc
    total = sum(scores.values())
    if total <= 0:
        return {"top": "en", "ranked": [("en", 1.0)], "confidence": "low"}
    ranked = sorted(((c, v / total) for c, v in scores.items() if v > 0), key=lambda x: -x[1])
    top, share = ranked[0]
    return {"top": top, "ranked": ranked, "confidence": "high" if share >= 0.6 and scores[top] >= 2 else "low"}


def suggest_line_language(text):
    """한 줄의 언어 제안(화면용). 문자 체계(detect_text_language)에 라틴 문자 줄의 낱말 점수(detect_latin_language)를 더한다.

    돌려주는 dict: {"primary": 코드 또는 None, "languages": [코드…], "confidence": "high"|"medium"|"low"|"none", "source": "script"|"words"|"none"}.
    - 가나·한글·키릴이 있으면 문자 체계로 정한다(confidence high, 섞이면 medium).
    - 라틴 문자만 있으면 낱말 점수로 정한다(source="words", confidence는 detect_latin_language의 것).
    - 한자만 있거나 글자가 없으면 primary=None(confidence none)."""
    d = detect_text_language(text)
    if d["primary"] is None:
        return {"primary": None, "languages": [], "confidence": "none", "source": "none"}
    if d["languages"] == ["en"]:                       # 라틴 문자뿐: 낱말 점수로 언어를 추정
        lat = detect_latin_language(text)
        return {"primary": lat["top"], "languages": [lat["top"]], "confidence": lat["confidence"], "source": "words"}
    return {"primary": d["primary"], "languages": d["languages"], "confidence": "high" if len(d["languages"]) == 1 else "medium",
            "source": "script"}


# ---------- 소리에서 언어 제안 (Whisper 감지 확률) ----------
def suggest_from_probs(all_probs, candidates=COMMON):
    """Whisper의 언어별 확률 [(코드, 확률), …]에서 **후보 언어 안에서만** 순위를 매긴다: [(코드, 후보 안의 비율)] 큰 순서.

    100개 언어 중에서 고르면 비슷한 다른 언어(프랑스어 → 브르타뉴어, 일본어 → 자바어)로 가는 일이 있어서(검토 문서 16.12: 14곡 시험에서 후보를 좁히면
    base·medium이 11 → 13곡) 앱이 지원하는 언어로 좁혀서 제안한다. 후보의 확률 합이 0이면 빈 목록."""
    probs = dict(all_probs)
    total = sum(probs.get(c, 0.0) for c in candidates)
    if total <= 0:
        return []
    ranked = sorted(((c, probs.get(c, 0.0) / total) for c in candidates), key=lambda x: -x[1])
    return [(c, p) for c, p in ranked if p > 0]


def mixed_hint(ranked, threshold=0.25):
    """제안 순위에서 1등과 함께 **섞여 있을 수 있는 언어**(2등의 비율이 threshold 이상)를 돌려준다. 없으면 None.
    threshold 0.25는 표본 없이 정한 **잠정값**이다 [추정]."""
    if len(ranked) >= 2 and ranked[1][1] >= threshold:
        return ranked[1][0]
    return None


# ---------- 사용자의 답 → STT 옵션 ----------
def stt_options(answer, languages, mixed="primary"):
    """내 노래의 "언어가 맞나요?"에 대한 사용자의 답을 `stt.recognize_segments`의 인자로 바꾼다.

    answer: "yes"(제안이 맞음, languages=[제안 언어]) / "no"(아니오, languages=사용자가 고른 언어들) / "unknown"(모르겠어요).
    돌려주는 값: {"language": 코드 또는 None, "multilingual": bool, "languages": 줄 데이터에 남길 목록, "primary": 주 언어 또는 None}
    - 언어 1개 → 그 코드로 고정(가장 정확).  - "unknown" 또는 선택이 비어 있으면 자동(language=None).
    - 언어 2개 이상 → mixed="primary"이면 첫 번째를 주 언어로 고정, mixed="auto"이면 language=None + multilingual=True.
      **주의(소스 확인)**: multilingual=True는 **30초 창마다** 100개 언어 중에서 다시 감지해 language를 덮어쓰고, 30초 이하의 소리는 창이 하나라 그냥 자동과 같다.
      우리 구간(파일은 10·15·20·30초 중 선택, 최대 30초 = 창 하나)에서는 효과가 없어서 화면에서는 mixed="auto"를 쓰지 않는다(30초를 넘는 소리를 다룰 때를 위해 남겨 둠).
      faster-whisper에는 "허용 언어 목록" 옵션이 없어서 혼합 가사는 주 언어 고정이 기본이다 [검토 문서 16.14의 2절]."""
    if answer not in ("yes", "no", "unknown"):
        raise ValueError(f"알 수 없는 답: {answer!r}")
    langs = [c for c in dict.fromkeys(languages or []) if c]
    if answer == "unknown" or not langs:
        return {"language": None, "multilingual": False, "languages": [], "primary": None}
    if len(langs) == 1:
        return {"language": langs[0], "multilingual": False, "languages": langs, "primary": langs[0]}
    if mixed == "auto":
        return {"language": None, "multilingual": True, "languages": langs, "primary": langs[0]}
    return {"language": langs[0], "multilingual": False, "languages": langs, "primary": langs[0]}
