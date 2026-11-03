"""STT 구간(segment) → 연습용 **줄(line)** 로 나누기 (이슈 #31, 연습 단위는 한 줄·문장).

왜 필요한가
- 노래 구간 하나(약 20초)를 통째로 따라 읽기는 어렵다. 한 줄(몇 초) 단위로 나눠야 줄마다 표준 발음 음성(TTS)과 보컬 조각을 만들 수 있다.
- faster-whisper의 구간(segment)은 대체로 구절 단위지만 항상 가사의 줄과 같지 않다(검토 문서 16.7의 7, [미확인]). 그래서
  **구간을 기본 줄로 삼고**, 너무 길면 단어 시간으로 쪼개고, 너무 짧으면 이웃과 합친다.

규칙 (모두 인자로 바꿀 수 있고, 기본값은 실제 구간 통계를 본 뒤 조정한다. 작업 기록 문서 C2)
1. 구간 하나 = 줄 하나로 시작한다.
2. **길면 쪼갠다**: 길이 > max_sec 이거나 단어 수 > max_words 인 줄은 단어 사이 **가장 큰 쉼**(앞 단어 끝 ~ 다음 단어 시작)에서 둘로 나눈다
   (가운데 쪽 후보에서 고름). 쪼갠 조각이 아직 길면 되풀이한다. 단어 시간이 없는 구간은 쪼갤 수 없어 "too_long" 표시만 한다.
3. **짧으면 합친다**: 길이 < min_sec 이거나 단어 수 < min_words 인 줄은 **쉼이 더 짧은 이웃**과 합친다(쉼이 max_merge_gap 이하이고
   합친 결과가 길이·단어 한도를 넘지 않을 때만). 이웃이 멀거나 합치면 너무 길어지면 그대로 둔다.
4. **의심 표시**: 부모 구간의 압축률이 높거나(같은 말 반복), 평균 로그확률이 낮거나, 말이 아닐 확률이 높으면 "suspect"로 표시한다
   (환각·반복 루프 의심, stt.recognize_segments 설명 참고). 줄을 버리지는 않고 사람이 확인하게 한다.

[수업에 없음] 이 모듈 전체. 입력은 stt.recognize_segments가 돌려주는 dict 목록이고, 계산만 하며 파일·모델은 건드리지 않는다.
"""

SUSPECT_COMPRESSION = 2.4     # faster-whisper의 기본 폴백 기준과 같은 값(같은 말을 되풀이하면 압축률이 커짐)
SUSPECT_LOGPROB = -1.0        # 평균 로그확률이 이보다 낮으면 인식에 자신이 없다는 뜻
SUSPECT_NO_SPEECH = 0.6       # 말이 아닐 확률이 이보다 높으면 반주만 있는 구간일 수 있다


def _n_words(line):
    return len(line["words"]) if line["words"] is not None else len(line["text"].split())


def _dur(line):
    return line["end"] - line["start"]


def _too_long(line, max_sec, max_words):
    return _dur(line) > max_sec or _n_words(line) > max_words


def _from_segment(i, seg):
    words = seg.get("words")
    return {"start": seg["start"], "end": seg["end"], "text": seg["text"].strip(), "words": words,
            "segment_ids": [i], "source": "segment", "parts": [seg]}


def _split_once(line):
    """단어 사이 가장 큰 쉼에서 줄을 둘로 나눈다. 단어가 2개 미만이거나 단어 시간이 없으면 None. 가운데 30~70% 위치의 쉼 중에서 고른다."""
    words = line["words"]
    if not words or len(words) < 2:
        return None
    n = len(words)
    lo, hi = max(1, int(n * 0.3)), min(n - 1, max(1, int(n * 0.7 + 0.999)))
    cands = range(lo, hi + 1) if lo <= hi else range(1, n)
    k = max(cands, key=lambda i: (words[i]["start"] - words[i - 1]["end"], -abs(i - n / 2)))   # 쉼이 같으면 가운데에 가까운 쪽
    out = []
    for part in (words[:k], words[k:]):
        out.append({"start": part[0]["start"], "end": part[-1]["end"], "text": " ".join(w["word"] for w in part), "words": part,
                    "segment_ids": list(line["segment_ids"]), "source": "split", "parts": line["parts"]})
    return out


def _split_long(line, max_sec, max_words):
    if not _too_long(line, max_sec, max_words):
        return [line]
    halves = _split_once(line)
    if halves is None:
        return [dict(line, too_long=True)]       # 쪼갤 수 없음: 그대로 두고 표시
    return [p for h in halves for p in _split_long(h, max_sec, max_words)]


def _merge(a, b):
    words = (a["words"] or []) + (b["words"] or []) if a["words"] is not None and b["words"] is not None else None
    return {"start": a["start"], "end": b["end"], "text": (a["text"] + " " + b["text"]).strip(), "words": words,
            "segment_ids": a["segment_ids"] + [i for i in b["segment_ids"] if i not in a["segment_ids"]],
            "source": "merged", "parts": a["parts"] + [p for p in b["parts"] if p not in a["parts"]]}


def _merge_short(lines, min_sec, min_words, max_sec, max_words, max_merge_gap):
    lines = list(lines)
    i = 0
    while i < len(lines):
        ln = lines[i]
        if (_dur(ln) >= min_sec and _n_words(ln) >= min_words) or len(lines) == 1:
            i += 1
            continue
        options = []                                  # (쉼, 이웃 위치) 후보
        if i > 0:
            options.append((ln["start"] - lines[i - 1]["end"], i - 1))
        if i + 1 < len(lines):
            options.append((lines[i + 1]["start"] - ln["end"], i + 1))
        done = False
        for gap, j in sorted(options):                # 쉼이 짧은 이웃부터 시도
            a, b = (lines[j], ln) if j < i else (ln, lines[j])
            merged = _merge(a, b)
            if gap <= max_merge_gap and not _too_long(merged, max_sec, max_words):
                lines[min(i, j):max(i, j) + 1] = [merged]
                i = max(min(i, j) - 1, 0)             # 합쳐진 줄을 다시 검사(앞 줄과 또 합칠 수 있음)
                done = True
                break
        if not done:
            i += 1
    return lines


def _suspect(parts):
    return any((p.get("compression_ratio") or 0) > SUSPECT_COMPRESSION or (p.get("avg_logprob") if p.get("avg_logprob") is not None else 0) < SUSPECT_LOGPROB
               or (p.get("no_speech_prob") or 0) > SUSPECT_NO_SPEECH for p in parts)


def split_into_lines(segments, max_sec=7.0, max_words=16, min_sec=1.2, min_words=3, max_merge_gap=1.5):
    """구간 목록(stt.recognize_segments의 결과) → 줄 목록. 시간순이고 겹치지 않는다.

    돌려주는 줄: {"no"(1부터), "start", "end", "text", "n_words", "source"("segment"|"split"|"merged"), "segment_ids", "suspect", "too_long"}.
    인자의 뜻은 파일 맨 위 규칙 참고(길이·시간은 초). 빈 글의 구간은 버린다."""
    segs = [s for s in segments if s.get("text", "").strip()]
    lines = []
    for i, seg in enumerate(segs):
        lines += _split_long(_from_segment(i, seg), max_sec, max_words)
    lines = _merge_short(lines, min_sec, min_words, max_sec, max_words, max_merge_gap)
    out = []
    for no, ln in enumerate(lines, 1):
        out.append({"no": no, "start": round(ln["start"], 2), "end": round(ln["end"], 2), "text": ln["text"], "n_words": _n_words(ln),
                    "source": ln["source"], "segment_ids": ln["segment_ids"], "suspect": _suspect(ln["parts"]),
                    "too_long": bool(ln.get("too_long")) or _too_long(ln, max_sec, max_words)})
    return out
