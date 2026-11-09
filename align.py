"""채점 결과(ops)의 틀린 부분을 소리 위의 시간 구간으로 바꾼다.

- 연속된 틀린 칸(치환·삭제·삽입)을 한 덩어리(블록)로 묶는다. 단어 수가 달라도(we'll ↔ we are) 한 덩어리로 비교할 수 있다.
- 블록의 정답 단어는 TTS 소리의 구간으로, 인식된 단어는 내 녹음의 구간으로 바꾼다. 한쪽에 단어가 없으면(삭제·삽입) 이웃 단어 사이의 한 점이다.
- 단어 시간은 Whisper가 추정한 값이라 정확한 강제 정렬이 아니다(stt.recognize_words 참고).

수업과의 관계
- [수업에 없음] 이 파일 전체가 이 프로젝트에서 직접 설계한 부분이다("틀린 단어가 소리의 어디인가"를 보여 주려는 것).
  재료는 수업에서 온 것이다: 채점 결과 ops(scoring, 자습 WER·CER), 단어별 시간(7강 Whisper의 옵션), 그림(03·lesson04).

데이터 흐름
    scoring.score(정답, 인식) → ops  ──error_blocks──▶ 틀린 덩어리의 토큰 번호 범위
    stt.recognize_words(…)  → 단어 목록 ──word_tokens──▶ 토큰별 (시작, 끝) 시간
    둘을 합쳐 locate_errors가 덩어리마다 TTS 구간과 내 녹음 구간을 돌려준다.
"""
import scoring


def word_tokens(words, lang="en"):
    """stt.recognize_words의 단어 목록을 scoring과 같은 규칙으로 정규화한 토큰 목록으로 바꾼다. 구두점뿐인 단어는 빠진다.

    왜 필요한가: Whisper의 단어는 "Hello," 같이 구두점이 붙어 있다. 채점은 정규화한 토큰("hello")으로 하므로
    같은 규칙으로 바꿔야 채점 결과의 번호와 시간을 맞출 수 있다. 정규화하면 한 단어가 둘이 될 수도 있어 split()으로 나눈다."""
    out = []
    for w in words:
        for t in scoring.normalize(w["word"], lang).split():
            out.append({"token": t, "start": w["start"], "end": w["end"], "prob": w["prob"]})
    return out


def error_blocks(ops):
    """ops에서 연속된 틀린 칸을 묶어 [{"ref": (시작, 끝), "hyp": (시작, 끝)}]로 돌려준다(토큰 번호, 끝은 포함 안 함).

    ri, hj는 지금까지 지나온 정답 토큰 수, 인식 토큰 수다(ops를 앞에서부터 읽으며 센다).
    일치가 아닌 칸이 이어지는 동안 cur(진행 중인 덩어리)의 범위를 늘리고, 일치를 만나면 덩어리를 닫는다."""
    blocks, ri, hj, cur = [], 0, 0, None
    for kind, a, b in ops:         # a: 정답 토큰(삽입이면 None), b: 인식 토큰(삭제면 None)
        if kind == "일치":
            if cur:
                blocks.append(cur); cur = None
            ri += 1; hj += 1
            continue
        if cur is None:
            cur = {"ref": [ri, ri], "hyp": [hj, hj]}     # 새 덩어리 시작: 아직 비어 있는 범위
        if a is not None:          # 정답 토큰이 있는 칸(치환·삭제)이면 정답 범위의 끝을 늘린다
            ri += 1; cur["ref"][1] = ri
        if b is not None:          # 인식 토큰이 있는 칸(치환·삽입)이면 인식 범위의 끝을 늘린다
            hj += 1; cur["hyp"][1] = hj
    if cur:                        # 문장이 틀린 칸으로 끝났으면 마지막 덩어리를 닫는다
        blocks.append(cur)
    return [{"ref": tuple(b["ref"]), "hyp": tuple(b["hyp"])} for b in blocks]


def _span(tokens, lo, hi):
    """tokens[lo:hi]의 (시작, 끝). 비어 있으면 lo 바로 앞 단어의 끝(없으면 첫 단어의 시작)인 한 점.

    범위가 비는 경우는 삭제·삽입이다(한쪽에만 단어가 있음). 그때는 "두 이웃 단어 사이"의 한 시점을 구간으로 쓴다."""
    if hi > lo:
        return tokens[lo]["start"], tokens[hi - 1]["end"]
    if not tokens:
        return 0.0, 0.0
    t = tokens[lo - 1]["end"] if lo > 0 else tokens[0]["start"]
    return t, t


def _ref_to_tts(ops):
    """정답 토큰 번호 → TTS 인식 토큰 번호(대응이 없으면 None). ops는 score(정답, TTS 인식)의 결과.

    TTS 소리도 Whisper로 인식하므로 그 결과가 정답과 완전히 같지 않을 수 있다. 그래서 정답 단어가 TTS 인식에서
    몇 번째 단어인지를 ops로 다시 맞춰 본다(일치·치환이면 짝이 있고, 삭제면 짝이 없다)."""
    mapping, j = [], 0
    for kind, _a, _b in ops:
        if kind in ("일치", "치환"):
            mapping.append(j); j += 1       # 정답 토큰 하나가 TTS 인식의 j번째 토큰과 짝
        elif kind == "삭제":
            mapping.append(None)            # 정답에는 있는데 TTS 인식에는 없다
        else:
            j += 1                          # 삽입: TTS 인식에만 있는 토큰이라 정답 번호는 늘지 않는다
    return mapping


def locate_errors(ref, hyp_words, tts_words, lang="en"):
    """정답 문장, 내 녹음의 단어 목록, TTS의 단어 목록으로 틀린 블록마다 두 소리의 시간 구간을 구한다.
    돌려주는 값: {"result": score 결과, "hyp_tokens", "tts_tokens", "blocks": [{"ref_words", "hyp_words", "tts_span", "hyp_span"}]}

    순서: ① 정답·내 인식·TTS 인식을 모두 같은 규칙의 토큰으로 맞춘다 ② 정답 vs 내 인식을 채점해 틀린 덩어리를 찾는다
    ③ 덩어리의 정답 단어를 TTS 인식 단어로 옮겨 TTS 쪽 구간을, 인식 단어의 시간으로 내 녹음 쪽 구간을 얻는다."""
    ref_tokens = scoring.normalize(ref, lang).split()
    hyp_tok, tts_tok = word_tokens(hyp_words, lang), word_tokens(tts_words, lang)
    result = scoring.score(ref_tokens, [t["token"] for t in hyp_tok])
    mapping = _ref_to_tts(scoring.score(ref_tokens, [t["token"] for t in tts_tok])["ops"])
    blocks = []
    for b in error_blocks(result["ops"]):
        (r0, r1), (h0, h1) = b["ref"], b["hyp"]
        mapped = [m for m in mapping[r0:r1] if m is not None]     # 이 덩어리의 정답 단어들이 TTS 인식에서 몇 번째인지
        if mapped:
            tts_span = _span(tts_tok, min(mapped), max(mapped) + 1)
        else:   # TTS에서 대응하는 단어가 없으면 앞쪽 이웃 단어 뒤의 한 점
            prev = [m for m in mapping[:r0] if m is not None]
            tts_span = _span(tts_tok, prev[-1] + 1 if prev else 0, prev[-1] + 1 if prev else 0)
        blocks.append({"ref_words": ref_tokens[r0:r1], "hyp_words": [t["token"] for t in hyp_tok[h0:h1]],
                       "tts_span": tts_span, "hyp_span": _span(hyp_tok, h0, h1)})
    return {"result": result, "hyp_tokens": hyp_tok, "tts_tokens": tts_tok, "blocks": blocks}


def _split_shared_spans(tokens):
    """한 Whisper 단어가 두 토큰 이상이 된 경우(we'll → we·will) 그 토큰들이 같은 시간 구간을 나눠 쓰므로, 구간을 **토큰 수만큼 똑같이 나눠** 하나씩 준다.
    그렇지 않으면 억양 그래프에서 같은 곡선이 두 칸에 중복으로 그려진다. 글자 수나 실제 음소 길이를 보지 않는 단순한 가정이라 칸 경계는 대략이다.
    구간이 서로 같은 **연속된** 토큰만 한 단어로 본다. 원본을 고치지 않고 새 목록을 돌려준다."""
    out, i = [], 0
    while i < len(tokens):
        j = i
        while j + 1 < len(tokens) and (tokens[j + 1]["start"], tokens[j + 1]["end"]) == (tokens[i]["start"], tokens[i]["end"]):
            j += 1
        n = j - i + 1
        step = (tokens[i]["end"] - tokens[i]["start"]) / n
        for k in range(n):
            out.append({**tokens[i + k], "start": tokens[i]["start"] + step * k, "end": tokens[i]["start"] + step * (k + 1)})
        i = j + 1
    return out


def word_spans(ref, hyp_tokens, tts_tokens, lang="en"):
    """기준 문장의 단어(정규화한 토큰) **하나하나**에 대해 TTS와 내 녹음의 시간 구간을 돌려준다(F0 억양 비교의 단어축, 이슈 #82·검토 문서 16.18).

    ref: 기준 문장. hyp_tokens·tts_tokens: locate_errors 결과의 "hyp_tokens"·"tts_tokens"(word_tokens의 출력; 이미 인식을 한 번 돌렸으므로 다시 인식하지 않는다).
    돌려주는 값: 기준 토큰 순서대로 [{"token", "tts_span", "hyp_span", "tts_same", "hyp_same"}].
    - *_span: (시작, 끝) 초. 그 소리에서 대응하는 인식 단어가 없으면(삭제) None.
    - *_same: 대응한 인식 단어가 기준 단어와 **같은 글자**인가. False면 치환(다른 단어로 인식됨: 시간은 있지만 같은 단어라고 말할 수 없다), 대응이 없으면 None.
    대응은 locate_errors와 같은 방법(기준 vs 인식을 scoring.score로 맞추고 `_ref_to_tts`로 번호를 옮김)이라 새 정렬 알고리즘은 없다.
    한 Whisper 단어가 두 토큰이 되면(we'll → we will) 그 단어의 구간을 토큰 수로 **똑같이 나눠** 준다(_split_shared_spans; 같은 곡선이 두 칸에 중복으로 그려지지 않게).
    단어 시간은 Whisper의 추정이라 강제 정렬이 아니다."""
    ref_tokens = scoring.normalize(ref, lang).split()
    out = [{"token": t, "tts_span": None, "hyp_span": None, "tts_same": None, "hyp_same": None} for t in ref_tokens]
    if not ref_tokens:
        return out
    for tokens, span_key, same_key in ((tts_tokens, "tts_span", "tts_same"), (hyp_tokens, "hyp_span", "hyp_same")):
        tokens = _split_shared_spans(tokens)
        mapping = _ref_to_tts(scoring.score(ref_tokens, [t["token"] for t in tokens])["ops"])
        for item, j in zip(out, mapping):
            if j is not None:
                item[span_key] = (tokens[j]["start"], tokens[j]["end"])
                item[same_key] = tokens[j]["token"] == item["token"]
    return out
