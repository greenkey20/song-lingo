"""spike A: 브라우저 마이크 녹음 → 서버 → Whisper → 채점 (내 Mac 안에서만).

점검하려는 것: ① 브라우저가 만든 녹음 형식을 faster-whisper가 읽는가 ② 처리 시간이 쓸 만한가.
버려도 되는 시험 코드이며, TTS·LLM은 부르지 않고 .env도 읽지 않습니다(STT는 로컬 모델).
실행(프로젝트 루트에서): uvicorn spike.server:app --host 127.0.0.1 --port 8000
"""
import logging
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

import scoring
import stt
import tts   # load_sentences()만 씁니다(API 호출 없음)

HERE = Path(__file__).parent
UPLOAD_DIR = Path("data/uploads")          # data/는 git에서 제외됩니다
MAX_BYTES = 20 * 1024 * 1024
EXT_BY_TYPE = {                            # 업로드의 content-type으로 확장자를 정합니다
    "audio/webm": ".webm", "video/webm": ".webm", "audio/ogg": ".ogg", "audio/mp4": ".mp4",
    "video/mp4": ".mp4", "audio/aac": ".aac", "audio/mpeg": ".mp3", "audio/wav": ".wav",
    "audio/x-wav": ".wav", "audio/wave": ".wav", "audio/x-m4a": ".m4a",
}

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app):
    t0 = time.time()
    stt.load_model()
    log.info("Whisper 모델 로딩 %.1f초", time.time() - t0)
    yield


app = FastAPI(lifespan=lifespan)
sentences = tts.load_sentences()


@app.get("/")
def index():
    return FileResponse(HERE / "index.html")


@app.get("/api/sentences")
def list_sentences():
    return [{"id": s["id"], "sentence": s["sentence"]} for s in sentences]


@app.post("/api/transcribe")
def transcribe(sentence_id: str = Form(...), audio: UploadFile = File(...)):
    t_all = time.time()
    content_type = (audio.content_type or "").split(";")[0].strip().lower()   # audio/webm;codecs=opus → audio/webm
    data = audio.file.read()
    info = {"content_type": audio.content_type, "size": len(data), "ok": False}
    log.info("받음: content-type=%s, 크기=%d바이트, 파일이름=%s", audio.content_type, len(data), audio.filename)
    try:
        if not data:
            raise ValueError("빈 파일입니다.")
        if len(data) > MAX_BYTES:
            raise ValueError("파일이 너무 큽니다(20MB 초과).")
        row = next(s for s in sentences if s["id"] == sentence_id)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        path = UPLOAD_DIR / f"spike_{int(time.time())}{EXT_BY_TYPE.get(content_type, '.bin')}"
        path.write_bytes(data)
        text, seconds = stt.recognize(path)
        w = scoring.wer(row["sentence"], text)
        info.update(ok=True, saved_as=path.name, sentence=row["sentence"], text=text, seconds=round(seconds, 2),
                    wer=round(w["rate"], 3), S=w["S"], D=w["D"], I=w["I"], N=w["N"],
                    diff=scoring.format_diff(w["ops"]))
        log.info("성공: 인식 %.2f초, WER %.3f, 인식문장=%r", seconds, w["rate"], text)
    except Exception as e:   # 읽지 못하는 형식이면 이 메시지가 이 spike의 가장 중요한 발견입니다
        info.update(error=f"{type(e).__name__}: {e}")
        log.error("실패: content-type=%s, %s\n%s", audio.content_type, info["error"], traceback.format_exc())
    info["total_seconds"] = round(time.time() - t_all, 2)
    return info
