"""녹음 파일 찾기와 인식(faster-whisper).

practice.ipynb의 셀에서 옮겼습니다. 설정은 7강과 같은 tiny + int8 + beam_size=1이며, 결과를 보고할 때 이 설정을 함께 적습니다.
모델은 처음 부를 때 한 번 읽어 모듈에 보관합니다(로딩 약 2초).
"""
import time
from pathlib import Path

MODEL_SIZE = "tiny"
REC_DIR = Path("data/recordings")

_model = None


def load_model():
    """Whisper 모델을 (없으면) 읽어서 돌려준다. 학습 저장소의 models/를 복사해 둔 download_root를 쓴다."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8", download_root="models")
    return _model


def find_recording(sid, take=1, rec_dir=REC_DIR):
    """sNN_takeK.* 파일을 확장자(wav·m4a·mp3 …)와 상관없이 찾는다. 없으면 None."""
    found = sorted(Path(rec_dir).glob(f"s{int(sid):02d}_take{take}.*"))
    return found[0] if found else None


def recognize(path, language="en"):
    """녹음 파일 하나를 인식해 (문장, 걸린 시간)을 돌려준다."""
    t0 = time.time()
    segments, _info = load_model().transcribe(str(path), language=language, beam_size=1)
    text = " ".join(seg.text.strip() for seg in segments)   # segments는 제너레이터라 여기서 실제로 인식이 돈다
    return text, time.time() - t0


def recognize_words(path, language="en"):
    """recognize와 같은 설정에 단어별 시간을 더해 (문장, 단어 목록, 걸린 시간)을 돌려준다.
    단어 목록: [{"word", "start", "end", "prob"}]. vad_filter=True는 앞 무음이 첫 단어 시간에 섞이는 것을 줄이려는 것이며,
    단어 시간은 모델 내부 정보로 추정한 값이라 대략의 구간으로만 쓴다."""
    t0 = time.time()
    segments, _info = load_model().transcribe(str(path), language=language, beam_size=1,
                                              word_timestamps=True, vad_filter=True)
    words = []
    for seg in segments:   # 제너레이터라 여기서 실제로 인식이 돈다
        words += [{"word": w.word.strip(), "start": w.start, "end": w.end, "prob": w.probability}
                  for w in seg.words]
    return " ".join(w["word"] for w in words), words, time.time() - t0
