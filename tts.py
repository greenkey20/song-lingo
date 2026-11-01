"""기준 음성(TTS)과 연습 문장 조회.

노트북과 이후 화면(UI)이 같은 코드를 쓰도록 practice.ipynb의 셀에서 옮겼습니다.
- 모델과 voice는 013 노트북 설정(gpt-4o-mini-tts, alloy)입니다. 호출은 실제로 과금됩니다.
- 같은 문장은 data/tts_cache/에 저장해 두고 다시 호출하지 않습니다. 호출 횟수는 `calls`에 셉니다.
- 경로는 프로젝트 루트에서 실행한다고 보고 상대 경로로 둡니다(노트북 출력에 /Users 경로가 남지 않게 하려는 것).
"""
import csv
import hashlib
from pathlib import Path

TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "alloy"
CACHE_DIR = Path("data/tts_cache")
SENTENCES_CSV = Path("sentences.csv")

calls = 0          # 이 프로세스(커널)에서 실제로 API를 부른 횟수
_client = None


def _get_client():
    """OpenAI 클라이언트는 처음 필요할 때 만든다. 키는 그 시점의 환경 변수(load_dotenv 이후)를 읽는다."""
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI()
    return _client


def reset_client():
    """.env의 key를 바꾼 뒤 커널 재시작 없이 다시 읽게 한다(load_dotenv(override=True) 후 호출)."""
    global _client
    _client = None


def load_sentences(path=SENTENCES_CSV):
    """sentences.csv를 dict 목록으로 읽는다(id는 문자열)."""
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lookup_sentence(target, sentences):
    """sentences의 id면 그 행과 TTS 캐시 경로를, 아니면 직접 입력한 문장으로 만든 행과 경로를 돌려준다."""
    for s in sentences:
        if s["id"] == str(target):
            return s, CACHE_DIR / f"s{int(s['id']):02d}.wav"
    text = str(target).strip()
    key = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return {"id": "직접 입력", "lang": "en", "sentence": text, "meaning_ko": ""}, CACHE_DIR / f"custom_{key}.wav"


def tts_wav(text, path):
    """문장을 WAV로 만든다. 이미 있으면 API를 부르지 않는다."""
    global calls
    path = Path(path)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with _get_client().audio.speech.with_streaming_response.create(
        model=TTS_MODEL, voice=TTS_VOICE, input=text, response_format="wav",
    ) as response:
        response.stream_to_file(path)
    calls += 1
    return path
