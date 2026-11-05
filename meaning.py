"""문장의 **한글 뜻**: 예시 문장은 직접 쓴 뜻, 그 밖의 문장은 OpenAI 모델로 번역한다(이슈 #50, 검토 문서 16.14의 10절).

- 예시 문장(영어는 sentences.csv의 meaning_ko, 일본어·프랑스어·섞인 예는 web_practice.EXAMPLE_SETS)은 **직접 쓴 뜻**을 그대로 보여 준다(호출 없음).
- 사용자가 붙여 넣은 문장·내 노래 가사는 `translate_ko`가 OpenAI 채팅 모델로 번역한다. **외부 API 호출이라 과금**(문장 하나에 아주 작음)되고, 가사를 외부 API로
  보내는 것은 11-04에 허용했다. 결과는 `data/meaning_cache/`(git 제외)에 문장 내용의 해시로 캐시해 같은 문장은 다시 부르지 않는다.
- 화면에는 항상 "AI 번역 · 참고용"으로 표시한다(오역할 수 있다).
- **표현 설명(`explain_sentence`, 이슈 #58)**: 같은 방식(버튼 → OpenAI → 디스크 캐시)으로 문장의 단어·표현/숙어·문법 포인트·예문 2개를 JSON으로 받아 보여 준다.
  예문은 모델이 새로 지은 문장이다(원문 가사를 옮기지 않는다). 결과도 `data/meaning_cache/`(git 제외)에만 남고, 틀릴 수 있어 "AI 설명 · 참고용"으로 표시한다.

수업과의 관계
- [수업과 같음] OpenAI 클라이언트로 API를 부르는 방식은 013(OpenAI API)과 같다(키는 tts.py의 `_get_client`가 `.env`에서 읽음).
- [수업에 없음] 채팅 모델로 번역하기, 디스크 캐시. 모델 이름은 `MODEL`로 한곳에 두었고 **이 환경에서 호출해 확인하지 않았다 [미확인]**: 안 되면 오류 문구가 화면에 나온다.
"""
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("data/meaning_cache")
MODEL = "gpt-4o-mini"            # [미확인] 사용자의 키로 쓸 수 있는 모델 이름. 다르면 여기만 고친다
SYSTEM = ("You translate one sentence or one line of song lyrics into natural, plain Korean. "
          "Output only the Korean meaning on a single line, with no quotes, no romanization and no explanation.")


def _key(text, lang):
    return hashlib.sha1(f"{lang}\n{str(text).strip()}".encode("utf-8")).hexdigest()[:16]


def cached(text, lang="", cache_dir=None):
    """캐시에 있는 번역(없으면 None). 호출하지 않는다."""
    path = Path(cache_dir or CACHE_DIR) / f"{_key(text, lang)}.txt"
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def translate_ko(text, lang="", client=None, cache_dir=None):
    """문장 → 한글 뜻(한 줄). 캐시에 있으면 호출하지 않는다. 빈 글은 ValueError, API 오류는 그대로 올린다(화면이 안내 문구로 바꿈).

    client: 테스트용 가짜 클라이언트(`chat.completions.create(...)`를 가진 객체). 없으면 tts의 클라이언트(.env의 OPENAI_API_KEY)를 쓴다."""
    text = str(text).strip()
    if not text:
        raise ValueError("번역할 문장이 비어 있습니다.")
    hit = cached(text, lang, cache_dir)
    if hit:
        return hit
    if client is None:
        import tts
        client = tts._get_client()
    res = client.chat.completions.create(model=MODEL, temperature=0.2,
                                         messages=[{"role": "system", "content": SYSTEM},
                                                   {"role": "user", "content": f"[{lang or 'auto'}] {text}"}])
    raw = (res.choices[0].message.content or "").strip() if res.choices else ""
    out = raw.splitlines()[0].strip() if raw else ""                  # 첫 줄만(설명이 붙어 와도 뜻만)
    if not out:
        raise RuntimeError("번역 결과가 비어 있습니다.")
    folder = Path(cache_dir or CACHE_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_key(text, lang)}.txt").write_text(out, encoding="utf-8")
    return out


def lookup(text, lang="", examples=None, cache_dir=None):
    """화면용: 예시 문장의 직접 쓴 뜻 → 캐시된 번역 순서로 찾는다. 돌려주는 값: (뜻, 출처) 출처는 "직접 작성" / "AI 번역" / None."""
    t = str(text).strip()
    if examples and t in examples:
        return examples[t], "직접 작성"
    hit = cached(t, lang, cache_dir)
    return (hit, "AI 번역") if hit else (None, None)


# ---------- 표현 설명 (이슈 #58) ----------
NOTES_SYSTEM = (
    "You help a Korean speaker study one foreign-language sentence or one line of song lyrics. "
    "Reply with JSON only, with exactly these keys: "
    '"words": up to 6 important words, each {"word": the word as written, "meaning": Korean meaning in this sentence}; '
    '"expressions": idioms, phrasal verbs or set phrases found in the sentence, each {"expression": ..., "meaning": Korean}; use [] if none; '
    '"grammar": one short Korean note about the most useful grammar point, or "" if none; '
    '"examples": exactly 2 NEW simple sentences in the same language that reuse the key words or expressions, each {"sentence": ..., "meaning": Korean translation}. '
    "Do not quote the original sentence in the examples. Keep every Korean explanation short."
)


def _clean_notes(data):
    """모델이 준 dict를 화면에 필요한 모양으로 정리한다(없는 칸은 빈 목록·빈 글, 글자가 아닌 값은 버림). 모양이 아예 틀리면 ValueError."""
    if not isinstance(data, dict):
        raise ValueError("설명 형식이 올바르지 않습니다.")

    def pairs(key, a, b):
        out = []
        for it in data.get(key) or []:
            if isinstance(it, dict) and str(it.get(a, "")).strip():
                out.append({a: str(it[a]).strip(), b: str(it.get(b, "")).strip()})
        return out

    notes = {"words": pairs("words", "word", "meaning"), "expressions": pairs("expressions", "expression", "meaning"),
             "grammar": str(data.get("grammar") or "").strip(), "examples": pairs("examples", "sentence", "meaning")[:2]}
    if not (notes["words"] or notes["expressions"] or notes["grammar"] or notes["examples"]):
        raise ValueError("설명 결과가 비어 있습니다.")
    return notes


def cached_notes(text, lang="", cache_dir=None):
    """캐시에 있는 표현 설명(없거나 깨졌으면 None). 호출하지 않는다."""
    path = Path(cache_dir or CACHE_DIR) / f"{_key(text, lang)}.notes.json"
    if not path.exists():
        return None
    try:
        return _clean_notes(json.loads(path.read_text(encoding="utf-8")))
    except ValueError:                  # json.JSONDecodeError도 ValueError의 하위 클래스: 깨진 캐시는 없는 것으로 보고 다시 받는다
        return None


def explain_sentence(text, lang="", client=None, cache_dir=None):
    """문장 → 표현 설명 dict {"words","expressions","grammar","examples"}. 캐시에 있으면 호출하지 않는다.

    [수업에 없음] `response_format={"type": "json_object"}`: 채팅 모델이 반드시 JSON 객체로만 답하게 하는 옵션(프롬프트에도 JSON이라고 적어야 한다).
    빈 글은 ValueError, 응답이 JSON이 아니거나 비어 있으면 ValueError, API 오류는 그대로 올린다(화면이 안내 문구로 바꿈).
    client: 테스트용 가짜 클라이언트(translate_ko와 같다)."""
    text = str(text).strip()
    if not text:
        raise ValueError("설명할 문장이 비어 있습니다.")
    hit = cached_notes(text, lang, cache_dir)
    if hit:
        return hit
    if client is None:
        import tts
        client = tts._get_client()
    res = client.chat.completions.create(model=MODEL, temperature=0.3, response_format={"type": "json_object"},
                                         messages=[{"role": "system", "content": NOTES_SYSTEM},
                                                   {"role": "user", "content": f"[{lang or 'auto'}] {text}"}])
    raw = (res.choices[0].message.content or "").strip() if res.choices else ""
    notes = _clean_notes(json.loads(raw))        # 깨진 JSON이면 JSONDecodeError(ValueError)
    folder = Path(cache_dir or CACHE_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_key(text, lang)}.notes.json").write_text(json.dumps(notes, ensure_ascii=False), encoding="utf-8")
    return notes


def notes_markdown(notes):
    """표현 설명 dict → 화면용 마크다운(HTML 태그는 만들지 않는다: 모델이 준 글을 `unsafe_allow_html` 없이 st.markdown으로만 그리려는 것)."""
    lines = []
    if notes["words"]:
        lines.append("**단어**")
        lines += [f"- **{w['word']}** — {w['meaning']}" for w in notes["words"]]
    if notes["expressions"]:
        lines.append("\n**표현·숙어**")
        lines += [f"- **{e['expression']}** — {e['meaning']}" for e in notes["expressions"]]
    if notes["grammar"]:
        lines.append(f"\n**문법 포인트** · {notes['grammar']}")
    if notes["examples"]:
        lines.append("\n**예문**")
        lines += [f"- {x['sentence']}  \n  {x['meaning']}" for x in notes["examples"]]
    return "\n".join(lines)
