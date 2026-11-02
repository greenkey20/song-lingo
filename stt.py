"""녹음 파일 찾기와 인식(faster-whisper).

practice.ipynb의 셀에서 옮겼습니다. 기본 설정은 7강과 같은 tiny + int8 + beam_size=1이며, 결과를 보고할 때 이 설정을 함께 적습니다(`settings()`).
모델은 크기별로 처음 부를 때 한 번 읽어 모듈에 보관합니다(tiny 로딩 약 2초). 크기를 바꿔 비교하려면
`recognize(path, model_size="small")`처럼 크기를 넘깁니다. 안 넘기면 기본 크기(`MODEL_SIZE`)라서 기존 호출은 그대로 동작합니다.
(크기 비교 판단과 근거는 docs/프로젝트_안내_및_주제_검토.md 15.2)

수업과의 관계 (017_sound/lesson07_whisper_minimal)
- [수업과 같음] `WhisperModel("tiny", device="cpu", compute_type="int8", download_root="models")`(셀 2)와
  `model.transcribe(path, language=..., beam_size=1)`(셀 4). 수업은 `language="ko"`였고 여기서는 `"en"`이다.
- [수업에 없음] 모델을 크기별로 한 번만 읽어 모듈에 보관하는 방식(`_models` dict), 모델 크기를 인자로 바꾸기,
  녹음 파일 찾기(`glob`), 단어별 시간(`word_timestamps`), 무음 구간 걸러내기(`vad_filter`).
- [수업에 없음] tiny보다 큰 모델(base, small, medium …). 모델 이름만 바꾸면 같은 코드로 읽히고, 처음 쓰는 크기는
  `download_root`(models/, git 제외)로 내려받는다. 큰 모델은 파일과 메모리가 커지고 CPU에서 느려진다.
"""
import time
from pathlib import Path

MODEL_SIZE = "tiny"                    # 기본 모델 크기: 가장 작은 다국어 모델(수업과 같음). 빠르지만 정확도는 낮을 수 있다
MODEL_SIZES = ("tiny", "base", "small")   # 크기 비교의 기본 후보(작은 것부터). medium 이상은 내려받는 파일이 훨씬 커서 필요할 때만 쓴다
MODEL_ORDER = ("tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en",
               "large-v1", "large-v2", "large-v3")   # 작은 모델부터 큰 모델 순서(비교 표의 열 순서). 여기 없는 이름은 맨 뒤에 가나다순
DEVICE = "cpu"                         # GPU 없이 실행
COMPUTE_TYPE = "int8"                  # 숫자를 8비트 정수로 줄여 CPU에서 빠르고 가볍게(수업과 같음)
BEAM_SIZE = 1                          # 후보를 하나만 탐색해 빠르게(수업과 같음)
REC_DIR = Path("data/recordings")      # 미리 녹음한 파일을 두는 곳(git에서 제외)

_models = {}       # 읽어 둔 모델: {"tiny": 모델, "small": 모델 …}. 없는 크기는 아직 안 읽은 것


def settings(model_size=None):
    """결과를 보고할 때 함께 적을 인식 설정을 dict로 돌려준다(모델 크기, 장치, 계산 방식, beam_size)."""
    return {"model": model_size or MODEL_SIZE, "device": DEVICE, "compute_type": COMPUTE_TYPE, "beam_size": BEAM_SIZE}


def load_model(model_size=None):
    """Whisper 모델을 (없으면) 읽어서 돌려준다. 학습 저장소의 models/를 복사해 둔 download_root를 쓴다.

    model_size: "tiny", "base", "small" … (안 주면 기본 MODEL_SIZE). 크기마다 한 번만 읽고 다음부터는 같은 객체를 돌려준다.
    처음 쓰는 크기는 download_root에 내려받으므로 시간이 걸리고 인터넷이 필요하다. 모델 읽기 시간을 따로 재려면
    recognize를 부르기 전에 이 함수를 먼저 불러 둔다(recognize의 시간에 로딩이 섞이지 않는다)."""
    size = model_size or MODEL_SIZE
    if size not in _models:
        from faster_whisper import WhisperModel
        _models[size] = WhisperModel(size, device=DEVICE, compute_type=COMPUTE_TYPE, download_root="models")
    return _models[size]


def loaded_models():
    """지금 메모리에 읽어 둔 모델 크기 목록을 돌려준다(예: ("tiny",))."""
    return tuple(_models)


def unload_models(model_size=None):
    """읽어 둔 모델을 버려 메모리를 돌려준다. 큰 모델을 여러 개 비교한 뒤에 쓴다(다음 호출 때 다시 읽는다).
    model_size를 주면 그 크기만, 안 주면 전부 버린다."""
    if model_size is None:
        _models.clear()
    else:
        _models.pop(model_size, None)


def available_models(include=None, download_root="models"):
    """이 PC의 download_root(기본 models/)에 **이미 내려받아 둔** 모델 크기 목록을 작은 모델부터 돌려준다.

    include: 아직 없어도 목록에 넣을 크기들(예: MODEL_SIZES). 그런 크기는 load_model이 처음 읽을 때 내려받는다.
    내려받은 모델은 download_root/models--Systran--faster-whisper-<크기>/snapshots/<해시>/model.bin 으로 저장된다
    (Hugging Face 캐시 구조). model.bin이 실제로 있는 것만 센다(받다가 만 폴더는 제외).

    [수업에 없음] Path.glob로 폴더를 훑어 모델 이름을 알아낸다. 7강은 크기를 직접 적었다."""
    prefix = "models--Systran--faster-whisper-"
    found = set(include or ())
    for d in Path(download_root).glob(prefix + "*"):
        if any(m.exists() for m in d.glob("snapshots/*/model.bin")):     # exists(): 심볼릭 링크가 가리키는 실제 파일까지 확인
            found.add(d.name[len(prefix):])
    rank = {name: i for i, name in enumerate(MODEL_ORDER)}
    return sorted(found, key=lambda n: (rank.get(n, len(rank)), n))


def find_recording(sid, take=1, rec_dir=REC_DIR):
    """sNN_takeK.* 파일을 확장자(wav·m4a·mp3 …)와 상관없이 찾는다. 없으면 None.

    [수업에 없음] Path.glob("패턴"): 패턴에 맞는 파일을 찾는다. `.*`는 "확장자가 무엇이든"이라는 뜻이다."""
    found = sorted(Path(rec_dir).glob(f"s{int(sid):02d}_take{take}.*"))
    return found[0] if found else None


def recognize(path, language="en", model_size=None, vad_filter=False):
    """녹음 파일 하나를 인식해 (문장, 걸린 시간)을 돌려준다. model_size를 안 주면 기본 크기(tiny).
    그 크기를 처음 쓰면 모델 읽기 시간이 걸린 시간에 섞인다(미리 load_model로 읽어 두면 섞이지 않음).

    vad_filter: [수업에 없음] True면 VAD(말소리 없는 구간을 걸러내는 처리)를 켠 채 인식한다. 기본 False는 7강과 같은 설정이다.
    같은 녹음도 큰 모델에서는 VAD 켬/끔에 따라 결과가 달라질 수 있다(검토 문서 15.2: small의 3번 문장 0.429 → 0.286).
    recognize_words는 기본이 True라서, 두 함수를 같은 설정으로 맞추려면 같은 값을 넘긴다."""
    t0 = time.time()
    segments, _info = load_model(model_size).transcribe(str(path), language=language, beam_size=BEAM_SIZE,
                                                        vad_filter=vad_filter)   # beam_size=1: 후보를 하나만 탐색해 빠르게(수업과 같음)
    # 수업은 list(segments)로 한 번에 모았다. 여기서는 구간 문장을 이어 붙여 하나의 문장으로 만든다.
    text = " ".join(seg.text.strip() for seg in segments)   # segments는 제너레이터라 여기서 실제로 인식이 돈다
    return text, time.time() - t0


def recognize_words(path, language="en", model_size=None, vad_filter=True):
    """recognize와 같은 설정에 단어별 시간을 더해 (문장, 단어 목록, 걸린 시간)을 돌려준다.
    단어 목록: [{"word", "start", "end", "prob"}]. 기본 vad_filter=True는 앞 무음이 첫 단어 시간에 섞이는 것을 줄이려는 것이며,
    단어 시간은 모델 내부 정보로 추정한 값이라 대략의 구간으로만 쓴다. recognize(기본 VAD 끔)와 설정을 맞추려면
    vad_filter=False를 넘긴다(그러면 앞 무음이 첫 단어 시간에 섞일 수 있다).

    [수업에 없음] word_timestamps=True: 단어마다 시작·끝 시간(초)과 확률을 함께 돌려준다.
    [수업에 없음] vad_filter=True: VAD(음성 구간 검출)로 말소리가 없는 구간을 걸러낸 뒤 인식한다.
    그렇게 하지 않으면 앞의 긴 무음이 첫 단어의 시간에 섞인다(실제로 첫 단어가 0.00초로 나오는 것을 확인했다)."""
    t0 = time.time()
    segments, _info = load_model(model_size).transcribe(str(path), language=language, beam_size=BEAM_SIZE,
                                                        word_timestamps=True, vad_filter=vad_filter)
    words = []
    for seg in segments:   # 제너레이터라 여기서 실제로 인식이 돈다
        words += [{"word": w.word.strip(), "start": w.start, "end": w.end, "prob": w.probability}
                  for w in seg.words]     # seg.words: 이 구간의 단어 목록. w.probability: 모델이 그 단어를 얼마나 확신하는지(0~1)
    return " ".join(w["word"] for w in words), words, time.time() - t0
