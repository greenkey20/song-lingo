"""spike A: 브라우저 마이크 녹음 → 서버 → Whisper → 채점 (내 Mac 안에서만).

점검하려는 것: ① 브라우저가 만든 녹음 형식을 faster-whisper가 읽는가 ② 처리 시간이 쓸 만한가.
버려도 되는 시험 코드이며, TTS·LLM은 부르지 않고 .env도 읽지 않습니다(STT는 로컬 모델).
실행(프로젝트 루트에서): uvicorn spike.server:app --host 127.0.0.1 --port 8000

수업과의 관계
- [수업에 없음] 이 파일 전체. 웹 서버를 만드는 **FastAPI**(파이썬 웹 프레임워크)와 이를 실제로 실행하는 **uvicorn**을 쓴다.
  재료인 stt(7강 Whisper)와 scoring(자습 WER·CER)은 수업/자습 코드를 부르기만 한다.
- 웹 서버의 기본 모양: 브라우저가 주소(URL)로 요청을 보내면, 그 주소에 연결된 함수가 실행되어 결과를 돌려준다.
    GET  /                → 화면(index.html)을 돌려준다
    GET  /api/sentences   → 연습 문장 목록(JSON)을 돌려준다
    POST /api/transcribe  → 녹음 파일을 받아 인식·채점한 결과(JSON)를 돌려준다
  (JSON은 파이썬의 dict/list와 거의 같은 모양의 글자 형식이라 브라우저와 서버가 주고받기 좋다.)
- 최종 화면(UI)이 아니라 점검용이다. 이슈 #9의 남은 항목에서 practice.py와 중복을 정리할지 검토한다.
"""
import logging
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile    # FastAPI: 서버 본체. Form·File·UploadFile: 업로드된 데이터를 받는 도구
from fastapi.responses import FileResponse             # 파일(HTML)을 그대로 돌려주는 응답

import scoring
import stt
import tts   # load_sentences()만 씁니다(API 호출 없음)

HERE = Path(__file__).parent                 # 이 파일이 있는 폴더(spike/). index.html을 찾는 데 쓴다
UPLOAD_DIR = Path("data/uploads")          # data/는 git에서 제외됩니다
MAX_BYTES = 20 * 1024 * 1024               # 업로드 크기 제한 20MB (잘못된 큰 파일을 막으려는 것)
EXT_BY_TYPE = {                            # 업로드의 content-type으로 확장자를 정합니다
    "audio/webm": ".webm", "video/webm": ".webm", "audio/ogg": ".ogg", "audio/mp4": ".mp4",
    "video/mp4": ".mp4", "audio/aac": ".aac", "audio/mpeg": ".mp3", "audio/wav": ".wav",
    "audio/x-wav": ".wav", "audio/wave": ".wav", "audio/x-m4a": ".m4a",
}

log = logging.getLogger("uvicorn.error")      # uvicorn이 터미널에 찍는 로그와 같은 곳에 기록한다


@asynccontextmanager
async def lifespan(app):
    """서버가 켜질 때(yield 앞)와 꺼질 때(yield 뒤) 실행되는 부분. [수업에 없음]
    여기서는 켜질 때 Whisper 모델을 미리 읽어, 첫 요청이 모델 로딩 때문에 몇 초 느려지는 것을 막는다."""
    t0 = time.time()
    stt.load_model()
    log.info("Whisper 모델 로딩 %.1f초", time.time() - t0)
    yield


app = FastAPI(lifespan=lifespan)       # uvicorn이 이 `app`을 찾아 실행한다(실행 명령의 spike.server:app)
sentences = tts.load_sentences()


@app.get("/")                          # [수업에 없음] 데코레이터: 아래 함수를 "GET /" 요청에 연결한다
def index():
    return FileResponse(HERE / "index.html")


@app.get("/api/sentences")
def list_sentences():
    return [{"id": s["id"], "sentence": s["sentence"]} for s in sentences]     # 화면의 문장 선택 목록용


@app.post("/api/transcribe")
def transcribe(sentence_id: str = Form(...), audio: UploadFile = File(...)):
    """sentence_id(어떤 문장인지)와 audio(녹음 파일)를 받아 인식·채점 결과를 돌려준다.
    Form(...)/File(...)의 "..."는 "꼭 있어야 하는 값"이라는 뜻이다."""
    t_all = time.time()
    # 브라우저가 알려 주는 형식(content-type)은 "audio/webm;codecs=opus"처럼 부가 설명이 붙으므로 ';' 앞만 쓴다.
    content_type = (audio.content_type or "").split(";")[0].strip().lower()   # audio/webm;codecs=opus → audio/webm
    data = audio.file.read()       # 업로드된 파일의 바이트를 모두 읽는다
    info = {"content_type": audio.content_type, "size": len(data), "ok": False}
    log.info("받음: content-type=%s, 크기=%d바이트, 파일이름=%s", audio.content_type, len(data), audio.filename)
    try:
        if not data:
            raise ValueError("빈 파일입니다.")
        if len(data) > MAX_BYTES:
            raise ValueError("파일이 너무 큽니다(20MB 초과).")
        row = next(s for s in sentences if s["id"] == sentence_id)     # 조건에 맞는 첫 문장(없으면 오류)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        # 파일 이름: spike_현재시각.확장자. 확장자는 content-type에서 정하고, 모르는 형식이면 .bin
        path = UPLOAD_DIR / f"spike_{int(time.time())}{EXT_BY_TYPE.get(content_type, '.bin')}"
        path.write_bytes(data)
        text, seconds = stt.recognize(path)         # 확장자와 상관없이 faster-whisper가 내부 디코더(PyAV)로 읽는다
        w = scoring.wer(row["sentence"], text)
        info.update(ok=True, saved_as=path.name, sentence=row["sentence"], text=text, seconds=round(seconds, 2),
                    wer=round(w["rate"], 3), S=w["S"], D=w["D"], I=w["I"], N=w["N"],
                    diff=scoring.format_diff(w["ops"]))
        log.info("성공: 인식 %.2f초, WER %.3f, 인식문장=%r", seconds, w["rate"], text)
    except Exception as e:   # 읽지 못하는 형식이면 이 메시지가 이 spike의 가장 중요한 발견입니다
        info.update(error=f"{type(e).__name__}: {e}")
        log.error("실패: content-type=%s, %s\n%s", audio.content_type, info["error"], traceback.format_exc())
    info["total_seconds"] = round(time.time() - t_all, 2)
    return info      # FastAPI가 dict를 자동으로 JSON으로 바꿔 브라우저에 보낸다
