"""채점 결과(ops)의 틀린 부분을 소리 위의 시간 구간으로 바꾼다.

- 연속된 틀린 칸(치환·삭제·삽입)을 한 덩어리(블록)로 묶는다. 단어 수가 달라도(we'll ↔ we are) 한 덩어리로 비교할 수 있다.
- 블록의 정답 단어는 TTS 소리의 구간으로, 인식된 단어는 내 녹음의 구간으로 바꾼다. 한쪽에 단어가 없으면(삭제·삽입) 이웃 단어 사이의 한 점이다.
- 단어 시간은 Whisper가 추정한 값이라 정확한 강제 정렬이 아니다(stt.recognize_words 참고).
"""
import scoring


def word_tokens(words, lang="en"):
    """stt.recognize_words의 단어 목록을 scoring과 같은 규칙으로 정규화한 토큰 목록으로 바꾼다. 구두점뿐인 단어는 빠진다."""
    out = []
    for w in words:
        for t in scoring.normalize(w["word"], lang).split():
            out.append({"token": t, "start": w["start"], "end": w["end"], "prob": w["prob"]})
    return out


def error_blocks(ops):
    """ops에서 연속된 틀린 칸을 묶어 [{"ref": (시작, 끝), "hyp": (시작, 끝)}]로 돌려준다(토큰 번호, 끝은 포함 안 함)."""
    blocks, ri, hj, cur = [], 0, 0, None
    for kind, a, b in ops:
        if kind == "일치":
            if cur:
                blocks.append(cur); cur = None
            ri += 1; hj += 1
            continue
        if cur is None:
            cur = {"ref": [ri, ri], "hyp": [hj, hj]}
        if a is not None:
            ri += 1; cur["ref"][1] = ri
        if b is not None:
            hj += 1; cur["hyp"][1] = hj
    if cur:
        blocks.append(cur)
    return [{"ref": tuple(b["ref"]), "hyp": tuple(b["hyp"])} for b in blocks]


def _span(tokens, lo, hi):
    """tokens[lo:hi]의 (시작, 끝). 비어 있으면 lo 바로 앞 단어의 끝(없으면 첫 단어의 시작)인 한 점."""
    if hi > lo:
        return tokens[lo]["start"], tokens[hi - 1]["end"]
    if not tokens:
        return 0.0, 0.0
    t = tokens[lo - 1]["end"] if lo > 0 else tokens[0]["start"]
    return t, t


def _ref_to_tts(ops):
    """정답 토큰 번호 → TTS 인식 토큰 번호(대응이 없으면 None). ops는 score(정답, TTS 인식)의 결과."""
    mapping, j = [], 0
    for kind, _a, _b in ops:
        if kind in ("일치", "치환"):
            mapping.append(j); j += 1
        elif kind == "삭제":
            mapping.append(None)
        else:
            j += 1
    return mapping


def locate_errors(ref, hyp_words, tts_words, lang="en"):
    """정답 문장, 내 녹음의 단어 목록, TTS의 단어 목록으로 틀린 블록마다 두 소리의 시간 구간을 구한다.
    돌려주는 값: {"result": score 결과, "hyp_tokens", "tts_tokens", "blocks": [{"ref_words", "hyp_words", "tts_span", "hyp_span"}]}"""
    ref_tokens = scoring.normalize(ref, lang).split()
    hyp_tok, tts_tok = word_tokens(hyp_words, lang), word_tokens(tts_words, lang)
    result = scoring.score(ref_tokens, [t["token"] for t in hyp_tok])
    mapping = _ref_to_tts(scoring.score(ref_tokens, [t["token"] for t in tts_tok])["ops"])
    blocks = []
    for b in error_blocks(result["ops"]):
        (r0, r1), (h0, h1) = b["ref"], b["hyp"]
        mapped = [m for m in mapping[r0:r1] if m is not None]
        if mapped:
            tts_span = _span(tts_tok, min(mapped), max(mapped) + 1)
        else:   # TTS에서 대응하는 단어가 없으면 앞쪽 이웃 단어 뒤의 한 점
            prev = [m for m in mapping[:r0] if m is not None]
            tts_span = _span(tts_tok, prev[-1] + 1 if prev else 0, prev[-1] + 1 if prev else 0)
        blocks.append({"ref_words": ref_tokens[r0:r1], "hyp_words": [t["token"] for t in hyp_tok[h0:h1]],
                       "tts_span": tts_span, "hyp_span": _span(hyp_tok, h0, h1)})
    return {"result": result, "hyp_tokens": hyp_tok, "tts_tokens": tts_tok, "blocks": blocks}
