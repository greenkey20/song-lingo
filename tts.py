"""기준 음성(TTS)과 연습 문장 조회.

노트북과 이후 화면(UI)이 같은 코드를 쓰도록 practice.ipynb의 셀에서 옮겼습니다.
- 모델과 voice는 013 노트북 설정(gpt-4o-mini-tts, alloy)입니다. 호출은 실제로 과금됩니다.
- 같은 문장은 data/tts_cache/에 저장해 두고 다시 호출하지 않습니다. 호출 횟수는 `calls`에 셉니다.
- 경로는 프로젝트 루트에서 실행한다고 보고 상대 경로로 둡니다(노트북 출력에 /Users 경로가 남지 않게 하려는 것).

수업과의 관계
- [수업과 같음] `tts_wav`의 API 호출 부분(`client.audio.speech.with_streaming_response.create(...)` →
  `stream_to_file`)은 013 `OpenAI_API_Whisper_입문과 한국어 음성 AI 실습`의 `text_to_wav`(셀 20)와 같은 방식이다.
- [수업에 없음] 캐시(이미 있으면 호출하지 않음), 호출 횟수 `calls`, 클라이언트를 처음 필요할 때 만드는 지연 생성,
  문장 조회와 직접 입력 문장 처리(`lookup_sentence`), 문장 파일 `sentences.csv` 읽기(`csv`).
"""
import csv                      # [수업에 없음] 표준 라이브러리: CSV 파일을 읽어 줄마다 dict로 만들어 준다
import hashlib                  # 해시(내용을 짧은 고정 길이 값으로 바꾸는 함수). 수업 05에서는 파일 무결성 확인(SHA-256)에 썼고, 여기서는 파일 이름을 만드는 데 쓴다
from pathlib import Path

TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "alloy"
CACHE_DIR = Path("data/tts_cache")      # git에서 제외되는 폴더
SENTENCES_CSV = Path("sentences.csv")

calls = 0          # 이 프로세스(커널)에서 실제로 API를 부른 횟수. 캐시를 썼으면 늘지 않는다
_client = None     # OpenAI 클라이언트. 처음 필요할 때 만든다(앞의 밑줄은 "이 파일 안에서만 쓰는 값"이라는 관례)


def _get_client():
    """OpenAI 클라이언트는 처음 필요할 때 만든다. 키는 그 시점의 환경 변수(load_dotenv 이후)를 읽는다.

    왜 import할 때 만들지 않는가: 키가 없는 환경(테스트, 캐시만 쓰는 시연)에서도 이 모듈을 불러올 수 있게 하려는 것이다."""
    global _client      # 함수 안에서 모듈 변수 _client의 값을 바꾸겠다는 선언
    if _client is None:
        from openai import OpenAI    # 필요할 때만 불러온다
        _client = OpenAI()           # 키는 환경 변수 OPENAI_API_KEY에서 읽는다(수업 013과 같음)
    return _client


def reset_client():
    """.env의 key를 바꾼 뒤 커널 재시작 없이 다시 읽게 한다(load_dotenv(override=True) 후 호출)."""
    global _client
    _client = None


def load_sentences(path=SENTENCES_CSV):
    """sentences.csv를 dict 목록으로 읽는다(id는 문자열)."""
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))     # 첫 줄(id,lang,sentence,…)을 열 이름으로 써서 줄마다 {열 이름: 값} dict가 된다


def lookup_sentence(target, sentences):
    """sentences의 id면 그 행과 TTS 캐시 경로를, 아니면 직접 입력한 문장으로 만든 행과 경로를 돌려준다.

    직접 쓴 문장은 id를 "직접 입력"으로 둔다. 캐시 파일 이름은 문장 내용의 해시로 정해서, 같은 문장이면 같은 파일을 다시 쓴다."""
    for s in sentences:
        if s["id"] == str(target):
            return s, CACHE_DIR / f"s{int(s['id']):02d}.wav"     # 1 → s01.wav (두 자리, 앞에 0)
    text = str(target).strip()
    # sha1(문장 바이트).hexdigest()는 40글자의 16진수 문자열. 앞 10글자만 파일 이름에 쓴다(충돌 가능성은 이 규모에서 무시).
    key = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return {"id": "직접 입력", "lang": "en", "sentence": text, "meaning_ko": ""}, CACHE_DIR / f"custom_{key}.wav"


def tts_wav(text, path):
    """문장을 WAV로 만든다. 이미 있으면 API를 부르지 않는다."""
    global calls
    path = Path(path)
    if path.exists():
        return path                # 캐시 적중: API를 부르지 않으니 과금도 없다
    path.parent.mkdir(parents=True, exist_ok=True)     # 폴더가 없으면 만든다(수업 013과 같음)
    # [수업과 같음] 음성 데이터가 도착하는 대로 파일에 기록한다. response_format="wav"로 받아 수업의 WAV 처리와 맞춘다.
    with _get_client().audio.speech.with_streaming_response.create(
        model=TTS_MODEL, voice=TTS_VOICE, input=text, response_format="wav",
    ) as response:
        response.stream_to_file(path)
    calls += 1
    return path
