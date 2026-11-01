"""채점 모듈: 정규화, 편집 거리, WER/CER, 틀린 부분 표시.

학습 노트북 `docs/WER_CER_이해하기.ipynb`의 코드를 프로젝트용으로 옮긴 것입니다.
- 오류율 = (치환 S + 삭제 D + 삽입 I) / 정답 토큰 수 N  (삽입이 많으면 1을 넘을 수 있음)
- 화면에는 "일치율(1 - WER)"이 아니라 오류율과 S·D·I 개수를 보여 줄 것
- 정규화 규칙은 docs/ 의 정규화 규칙 문서와 tests/test_scoring.py 의 예시가 함께 정의함
"""
import re
import unicodedata
from difflib import SequenceMatcher


def normalize(text, lang="en", strip_accents=False):
    """비교 전에 문장 형식을 같은 규칙으로 맞춘다.

    공통: 유니코드 NFC → (영어·프랑스어는 소문자화) → 구두점 제거(아포스트로피는 유지) → 공백 정리
    일본어(ja): 공백이 없는 언어라 구두점과 공백을 모두 제거
    strip_accents: 프랑스어 악센트를 지울지 (기본 False, 방침은 1일차에 결정)
    """
    text = unicodedata.normalize("NFC", text).replace("’", "'")
    if lang in ("en", "fr"):
        text = text.lower()
    if strip_accents:
        text = "".join(c for c in unicodedata.normalize("NFD", text)
                       if unicodedata.category(c) != "Mn")
        text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[^\w\s']", "", text)
    if lang == "ja":
        return re.sub(r"\s+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def edit_matrix(ref, hyp):
    """ref, hyp: 토큰 리스트. 편집 거리 표(2차원 리스트)를 돌려준다."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d


def _similarity(a, b):
    """두 토큰이 얼마나 비슷한지 0~1. 같으면 1, 글자 하나짜리는 다르면 0, 그 밖에는 difflib 글자 비율(explore↔explor 0.92, the↔explor 0.2)."""
    if a == b:
        return 1.0
    if len(a) == 1 and len(b) == 1:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _tie_scores(ref, hyp, d):
    """최소 편집 거리를 만드는 경로들 중에서 '비슷한 토큰끼리 짝지은 정도'의 합이 가장 큰 값을 칸마다 계산한다.
    g[i][j]는 ref[:i], hyp[:j]를 최소 비용으로 맞추는 경로들의 최대 합이다(일치는 1점, 치환은 비슷한 만큼, 삭제·삽입은 0점)."""
    n, m = len(ref), len(hyp)
    g = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            cands = []
            if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
                cands.append(g[i - 1][j - 1] + _similarity(ref[i - 1], hyp[j - 1]))
            if i > 0 and d[i][j] == d[i - 1][j] + 1:
                cands.append(g[i - 1][j])
            if j > 0 and d[i][j] == d[i][j - 1] + 1:
                cands.append(g[i][j - 1])
            g[i][j] = max(cands)
    return g


def backtrace(ref, hyp, d):
    """편집 거리 표를 거꾸로 따라가 (종류, 정답 토큰, 인식 토큰) 목록을 만든다.
    종류: 일치 / 치환 / 삭제 / 삽입. 최소 거리를 만드는 경로가 여러 개면 비슷한 토큰끼리 짝지은 경로(_tie_scores)를 고르고,
    그것도 같으면 일치·치환 → 삭제 → 삽입 순으로 고른다. 경로가 달라져도 오류율(거리)은 같다."""
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
        _, _, (i, j), op = max(options, key=lambda o: (round(o[0], 9), -o[1]))
        ops.append(op)
    return ops[::-1]


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
    assert S + D + I == distance
    return {"S": S, "D": D, "I": I, "N": len(ref_tokens), "distance": distance,
            "rate": distance / len(ref_tokens), "ops": ops}


def wer(ref, hyp, lang="en", **kw):
    """단어 단위 오류율. 일본어처럼 공백이 없는 언어는 cer를 쓴다."""
    return score(normalize(ref, lang, **kw).split(), normalize(hyp, lang, **kw).split())


def cer(ref, hyp, lang="en", **kw):
    """글자 단위 오류율 (공백은 글자로 세지 않음)."""
    r = list(normalize(ref, lang, **kw).replace(" ", ""))
    h = list(normalize(hyp, lang, **kw).replace(" ", ""))
    return score(r, h)


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
