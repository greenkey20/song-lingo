"""채점 모듈: 정규화, 편집 거리, WER/CER, 틀린 부분 표시.

수업과의 관계
- [수업에 없음] WER·CER(8강)은 수업에서 다루지 않아 **자습**으로 정리한 노트북 `docs/WER_CER_이해하기.ipynb`의
  코드를 프로젝트용으로 옮겼다. 그 노트북의 순서(표 채우기 → 역추적 → 함수화)를 이 파일이 따른다.
- [수업에 없음] 동률 처리(`_similarity`, `_tie_scores`)는 자습 노트북에도 없는, 이 프로젝트에서 직접 추가한 규칙이다.

한눈에 보는 흐름: normalize → (토큰으로 나눔) → edit_matrix → backtrace → score → wer / cer → format_diff
- 오류율 = (치환 S + 삭제 D + 삽입 I) / 정답 토큰 수 N. 삽입이 많으면 1을 넘을 수 있다.
- 화면에는 "일치율(1 - WER)"이 아니라 오류율과 S·D·I 개수를 보여 줄 것(1을 넘을 수 있어서).
- 정규화 규칙은 tests/test_scoring.py의 예시가 함께 정의한다. 축약형·숫자 처리 방침(#3)은 검토 문서 13.4.
- 이 파일은 글자(문자열)만 다룬다. 소리·API는 없다. 소리와 이어 붙이는 일은 practice.py가 한다.
"""
import re
import unicodedata
from difflib import SequenceMatcher   # [수업에 없음] 표준 라이브러리: 두 문자열이 얼마나 비슷한지(0~1) 계산


# ---- 영어 표기 통일 규칙 (이슈 #3, 방침 C: 기본은 통일해서 채점하고, unify=False로 엄격 채점도 가능) ----
# 왜: Whisper는 "We're"를 "We are"로, "twenty"를 "20"으로 적기도 한다. 소리는 같고 표기만 다른 것을 오류로 세면
# 점수가 "문장 인식 일치도"를 덜 잘 나타낸다. 정답과 인식 결과 **양쪽에 같은 규칙**을 적용하므로 한쪽만 유리해지지 않는다.
# 바꾸지 않는 것: 's (is/has/소유격 구분 불가), 'd (would/had 구분 불가), 그 밖의 철자 차이.
_IRREGULAR = {"can't": "can not", "cannot": "can not", "won't": "will not", "shan't": "shall not",
              "gonna": "going to", "wanna": "want to", "gotta": "got to"}
_SUFFIX = (("n't", " not"), ("'re", " are"), ("'ll", " will"), ("'ve", " have"), ("'m", " am"))   # don't → do not, we're → we are …
_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
          "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_NUMBER_WORDS = {w: str(i) for i, w in enumerate(_UNITS)} | {w: str(n) for w, n in _TENS.items()}   # 0~19, 20·30·…·90
# "twenty-one" 처럼 하이픈으로 이어진 21~99는 구두점 제거(하이픈 삭제 → "twentyone") 전에 숫자로 바꿔야 한다.
_COMPOUND = re.compile(r"\b(" + "|".join(_TENS) + r")-(one|two|three|four|five|six|seven|eight|nine)\b")


def _unify_en(text):
    """소문자 영어 문장(구두점 제거 전)에서 하이픈 숫자(twenty-one → 21)를 바꾼다. 나머지는 _unify_tokens가 한다."""
    return _COMPOUND.sub(lambda m: str(_TENS[m.group(1)] + _UNITS.index(m.group(2))), text)


def _unify_tokens(tokens):
    """단어 목록에서 축약형을 펼치고(we're → we are) 0~99의 숫자 단어를 숫자로 바꾼다(twenty → 20). 숫자는 그대로 둔다.

    '단어마다' 바꾸므로 한 단어가 둘이 될 수는 있어도(we're → we, are) 단어 사이를 합치지는 않는다.
    그래서 "twenty one"(띄어쓰기)은 20·1이 된다. 정답과 인식 결과가 다르게 적으면 오류로 센다(알려진 한계)."""
    out = []
    for t in tokens:
        if t in _IRREGULAR:
            out += _IRREGULAR[t].split()
            continue
        for suffix, expansion in _SUFFIX:
            if t.endswith(suffix) and len(t) > len(suffix):
                out += (t[:-len(suffix)] + expansion).split()
                break
        else:
            out.append(_NUMBER_WORDS.get(t, t))
    return out


def normalize(text, lang="en", strip_accents=False, unify=True):
    """비교 전에 문장 형식을 같은 규칙으로 맞춘다. (자습 노트북 `normalize_en`을 일본어·프랑스어까지 넓힌 것)

    공통: 유니코드 NFC → (영어·프랑스어는 소문자화) → 구두점 제거(아포스트로피는 유지) → 공백 정리
    일본어(ja): 공백이 없는 언어라 구두점과 공백을 모두 제거
    strip_accents: 프랑스어 악센트를 지울지 (기본 False, 방침은 1일차에 결정)
    unify: 영어(en)만. True(기본)면 축약형을 펼치고(we're → we are, don't → do not, can't/cannot → can not, gonna → going to)
           0~99의 숫자 단어를 숫자로 바꾼다(twenty → 20, twenty-one → 21). False면 이 통일 없이 엄격하게 비교한다.
    """
    # NFC: 같은 글자를 만드는 여러 유니코드 표현(예: é 한 글자 vs e + 악센트 기호)을 한 가지로 맞춘다.
    # ’(둥근 아포스트로피)를 '(곧은 것)로 바꾸는 이유: 같은 문장인데 기호만 달라서 틀린 것으로 세지 않으려는 것.
    text = unicodedata.normalize("NFC", text).replace("’", "'")
    if lang in ("en", "fr"):
        text = text.lower()
    if lang == "en" and unify:
        text = _unify_en(text)
    if strip_accents:
        # NFD는 é를 e + 악센트 기호로 쪼갠다. 악센트 기호의 범주가 "Mn"(결합 기호)이라 그것만 빼면 악센트가 지워진다.
        text = "".join(c for c in unicodedata.normalize("NFD", text)
                       if unicodedata.category(c) != "Mn")
        text = unicodedata.normalize("NFC", text)
    # 정규식 [^\w\s']: 글자·숫자(\w, 한글·일본어 포함), 공백(\s), 아포스트로피(')가 "아닌" 것을 모두 지운다.
    text = re.sub(r"[^\w\s']", "", text)
    if lang == "ja":
        return re.sub(r"\s+", "", text)
    text = re.sub(r"\s+", " ", text).strip()   # 연속 공백을 하나로, 앞뒤 공백은 제거
    if lang == "en" and unify:
        text = " ".join(_unify_tokens(text.split()))
    return text


def edit_matrix(ref, hyp):
    """ref, hyp: 토큰 리스트. 편집 거리 표(2차원 리스트)를 돌려준다.

    d[i][j] = 정답의 앞 i개를 인식 결과의 앞 j개로 바꾸는 데 드는 최소 수정 횟수(치환·삭제·삽입 각 1번).
    (동적 계획법: 작은 문제의 답을 표에 채워 가며 큰 문제를 푼다. 자습 노트북 2절)
    """
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i          # 인식 결과가 비어 있으면 정답 i개를 모두 삭제해야 한다
    for j in range(m + 1):
        d[0][j] = j          # 정답이 비어 있으면 인식 결과 j개가 모두 삽입이다
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1       # 같은 토큰이면 비용 0(일치), 다르면 1(치환)
            d[i][j] = min(d[i - 1][j] + 1,                    # 삭제: 정답 토큰 하나를 지움
                          d[i][j - 1] + 1,                    # 삽입: 인식 결과에만 있는 토큰
                          d[i - 1][j - 1] + cost)             # 일치 또는 치환
    return d


def _similarity(a, b):
    """두 토큰이 얼마나 비슷한지 0~1. 같으면 1, 글자 하나짜리는 다르면 0, 그 밖에는 difflib 글자 비율(explore↔explor 0.92, the↔explor 0.2).
    [수업에 없음] 동률 처리에서 '비슷한 단어끼리 짝짓기' 위해 직접 추가한 점수다."""
    if a == b:
        return 1.0
    if len(a) == 1 and len(b) == 1:
        return 0.0    # 한 글자끼리는 우연히 비슷해 보이기 쉬워서 0점으로 둔다
    # SequenceMatcher(None, a, b).ratio(): 2 × (공통 글자 수) / (두 문자열 길이의 합). None은 "무시할 글자 없음".
    return SequenceMatcher(None, a, b).ratio()


def _tie_scores(ref, hyp, d):
    """최소 편집 거리를 만드는 경로들 중에서 '비슷한 토큰끼리 짝지은 정도'의 합이 가장 큰 값을 칸마다 계산한다.
    g[i][j]는 ref[:i], hyp[:j]를 최소 비용으로 맞추는 경로들의 최대 합이다(일치는 1점, 치환은 비슷한 만큼, 삭제·삽입은 0점).

    왜 필요한가: 최소 거리 경로가 여러 개일 때, 아무 경로나 고르면 "[+we+] [we'll→are]"처럼 어색한 짝이 나온다.
    같은 거리라도 "[we'll→we] [+are+]"처럼 비슷한 단어끼리 묶인 경로를 고르려는 것이다(오류율은 같다)."""
    n, m = len(ref), len(hyp)
    g = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            cands = []   # 이 칸에 도달할 수 있는, 거리가 최소인 경로들의 점수 후보
            if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
                cands.append(g[i - 1][j - 1] + _similarity(ref[i - 1], hyp[j - 1]))   # 일치/치환으로 온 경우
            if i > 0 and d[i][j] == d[i - 1][j] + 1:
                cands.append(g[i - 1][j])      # 삭제로 온 경우(점수는 더하지 않음)
            if j > 0 and d[i][j] == d[i][j - 1] + 1:
                cands.append(g[i][j - 1])      # 삽입으로 온 경우
            g[i][j] = max(cands)
    return g


def backtrace(ref, hyp, d):
    """편집 거리 표를 거꾸로 따라가 (종류, 정답 토큰, 인식 토큰) 목록을 만든다.
    종류: 일치 / 치환 / 삭제 / 삽입. 최소 거리를 만드는 경로가 여러 개면 비슷한 토큰끼리 짝지은 경로(_tie_scores)를 고르고,
    그것도 같으면 일치·치환 → 삭제 → 삽입 순으로 고른다. 경로가 달라져도 오류율(거리)은 같다.

    표의 오른쪽 아래 끝(i, j)에서 시작해 왼쪽 위(0, 0)로 되짚어 가며 "어느 칸에서 왔는가"를 기록한다.
    (자습 노트북 3절의 역추적에 동률 처리를 더한 것)"""
    g = _tie_scores(ref, hyp, d)
    i, j = len(ref), len(hyp)
    ops = []
    while i > 0 or j > 0:
        options = []   # (총점, 우선순위, 다음 칸, 기록할 ops) 중 거리가 맞는 것만
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            kind = "일치" if ref[i - 1] == hyp[j - 1] else "치환"
            options.append((g[i - 1][j - 1] + _similarity(ref[i - 1], hyp[j - 1]), 0, (i - 1, j - 1), (kind, ref[i - 1], hyp[j - 1])))
        if i > 0 and d[i][j] == d[i - 1][j] + 1:
            options.append((g[i - 1][j], 1, (i - 1, j), ("삭제", ref[i - 1], None)))
        if j > 0 and d[i][j] == d[i][j - 1] + 1:
            options.append((g[i][j - 1], 2, (i, j - 1), ("삽입", None, hyp[j - 1])))
        # 점수가 큰 것을 고르고, 점수가 같으면 우선순위 숫자가 작은 것(-우선순위가 큰 것)을 고른다.
        # round(..., 9): 소수 계산의 아주 작은 오차 때문에 같은 점수가 다르게 보이는 일을 막는다.
        _, _, (i, j), op = max(options, key=lambda o: (round(o[0], 9), -o[1]))
        ops.append(op)
    return ops[::-1]    # 끝에서 시작 쪽으로 거슬러 모았으므로 뒤집어서 문장 순서로 돌려준다


def score(ref_tokens, hyp_tokens):
    """S·D·I·N, 편집 거리, 오류율, 역추적 목록(ops)을 돌려준다. 정답이 비면 ValueError."""
    if len(ref_tokens) == 0:
        raise ValueError("정답이 비어 있어 오류율을 계산할 수 없습니다 (분모 N = 0)")
    d = edit_matrix(ref_tokens, hyp_tokens)
    ops = backtrace(ref_tokens, hyp_tokens, d)
    S = sum(o[0] == "치환" for o in ops)
    D = sum(o[0] == "삭제" for o in ops)
    I = sum(o[0] == "삽입" for o in ops)
    distance = d[-1][-1]
    assert S + D + I == distance    # 역추적으로 센 개수의 합이 표의 편집 거리와 같아야 한다(검산)
    return {"S": S, "D": D, "I": I, "N": len(ref_tokens), "distance": distance,
            "rate": distance / len(ref_tokens), "ops": ops}


def wer(ref, hyp, lang="en", **kw):
    """단어 단위 오류율. 일본어처럼 공백이 없는 언어는 cer를 쓴다."""
    return score(normalize(ref, lang, **kw).split(), normalize(hyp, lang, **kw).split())   # 공백으로 나눈 단어 목록으로 비교


def cer(ref, hyp, lang="en", **kw):
    """글자 단위 오류율 (공백은 글자로 세지 않음)."""
    r = list(normalize(ref, lang, **kw).replace(" ", ""))   # list("abc") → ["a", "b", "c"]: 글자 하나가 토큰 하나
    h = list(normalize(hyp, lang, **kw).replace(" ", ""))
    return score(r, h)


def evaluate(ref, hyp, lang="en", **kw):
    """한 문장의 채점 결과를 한 번에 돌려준다: {"wer": wer 결과, "cer": cer 결과, "main": 틀린 부분 표시에 쓸 쪽}.

    main은 일본어처럼 공백으로 단어를 나눌 수 없는 언어면 cer, 그 밖에는 wer이다.
    (practice.ipynb의 show_result에 있던 판단을 채점 모듈로 옮긴 것.)"""
    w, c = wer(ref, hyp, lang, **kw), cer(ref, hyp, lang, **kw)
    return {"wer": w, "cer": c, "main": c if lang == "ja" else w}


def format_diff(ops):
    """틀린 부분을 한 줄로 표시: 일치는 그대로, 치환은 [정답→인식], 삭제는 [-정답-], 삽입은 [+인식+]."""
    parts = []
    for kind, a, b in ops:
        if kind == "일치":
            parts.append(a)
        elif kind == "치환":
            parts.append(f"[{a}→{b}]")
        elif kind == "삭제":
            parts.append(f"[-{a}-]")
        else:
            parts.append(f"[+{b}+]")
    return " ".join(parts)
