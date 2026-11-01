"""녹음 파일 찾기와 인식(faster-whisper).

practice.ipynb의 셀에서 옮겼습니다. 설정은 7강과 같은 tiny + int8 + beam_size=1이며, 결과를 보고할 때 이 설정을 함께 적습니다.
모델은 처음 부를 때 한 번 읽어 모듈에 보관합니다(로딩 약 2초).

수업과의 관계 (017_sound/lesson07_whisper_minimal)
- [수업과 같음] `WhisperModel("tiny", device="cpu", compute_type="int8", download_root="models")`(셀 2)와
  `model.transcribe(path, language=..., beam_size=1)`(셀 4). 수업은 `language="ko"`였고 여기서는 `"en"`이다.
- [수업에 없음] 모델을 한 번만 읽어 모듈에 보관하는 방식, 녹음 파일 찾기(`glob`), 단어별 시간(`word_timestamps`),
  무음 구간 걸러내기(`vad_filter`).
"""
import time
from pathlib import Path

MODEL_SIZE = "tiny"                    # 가장 작은 다국어 모델(수업과 같음). 빠르지만 정확도는 낮을 수 있다
REC_DIR = Path("data/recordings")      # 미리 녹음한 파일을 두는 곳(git에서 제외)

_model = None      # 읽어 둔 모델. None이면 아직 안 읽음


def load_model():
    """Whisper 모델을 (없으면) 읽어서 돌려준다. 학습 저장소의 models/를 복사해 둔 download_root를 쓴다.

    모델 읽기는 몇 초 걸리므로 한 번만 하고 다음부터는 같은 객체를 돌려준다."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        # device="cpu": GPU 없이 실행, compute_type="int8": 숫자를 8비트 정수로 줄여 CPU에서 빠르고 가볍게(수업과 같음)
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8", download_root="models")
    return _model


def find_recording(sid, take=1, rec_dir=REC_DIR):
    """sNN_takeK.* 파일을 확장자(wav·m4a·mp3 …)와 상관없이 찾는다. 없으면 None.

    [수업에 없음] Path.glob("패턴"): 패턴에 맞는 파일을 찾는다. `.*`는 "확장자가 무엇이든"이라는 뜻이다."""
    found = sorted(Path(rec_dir).glob(f"s{int(sid):02d}_take{take}.*"))
    return found[0] if found else None


def recognize(path, language="en"):
    """녹음 파일 하나를 인식해 (문장, 걸린 시간)을 돌려준다."""
    t0 = time.time()
    segments, _info = load_model().transcribe(str(path), language=language, beam_size=1)   # beam_size=1: 후보를 하나만 탐색해 빠르게(수업과 같음)
    # 수업은 list(segments)로 한 번에 모았다. 여기서는 구간 문장을 이어 붙여 하나의 문장으로 만든다.
    text = " ".join(seg.text.strip() for seg in segments)   # segments는 제너레이터라 여기서 실제로 인식이 돈다
    return text, time.time() - t0


def recognize_words(path, language="en"):
    """recognize와 같은 설정에 단어별 시간을 더해 (문장, 단어 목록, 걸린 시간)을 돌려준다.
    단어 목록: [{"word", "start", "end", "prob"}]. vad_filter=True는 앞 무음이 첫 단어 시간에 섞이는 것을 줄이려는 것이며,
    단어 시간은 모델 내부 정보로 추정한 값이라 대략의 구간으로만 쓴다.

    [수업에 없음] word_timestamps=True: 단어마다 시작·끝 시간(초)과 확률을 함께 돌려준다.
    [수업에 없음] vad_filter=True: VAD(음성 구간 검출)로 말소리가 없는 구간을 걸러낸 뒤 인식한다.
    그렇게 하지 않으면 앞의 긴 무음이 첫 단어의 시간에 섞인다(실제로 첫 단어가 0.00초로 나오는 것을 확인했다)."""
    t0 = time.time()
    segments, _info = load_model().transcribe(str(path), language=language, beam_size=1,
                                              word_timestamps=True, vad_filter=True)
    words = []
    for seg in segments:   # 제너레이터라 여기서 실제로 인식이 돈다
        words += [{"word": w.word.strip(), "start": w.start, "end": w.end, "prob": w.probability}
                  for w in seg.words]     # seg.words: 이 구간의 단어 목록. w.probability: 모델이 그 단어를 얼마나 확신하는지(0~1)
    return " ".join(w["word"] for w in words), words, time.time() - t0
