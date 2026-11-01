"""연습 한 번의 순서를 이어 붙이는 얇은 연결 모듈(이슈 #9).

이 파일은 계산을 하지 않는다. 계산은 각 모듈이 한다. 여기서는 그 모듈들을 '어떤 순서로 부르는가'만 정하고,
결과를 dict로 돌려준다. 화면에 어떻게 보여 줄지는 report.py(글)와 visualisation.py(그림), 노트북(출력)이 맡는다.
그래서 같은 함수를 노트북에서도, 나중에 만들 웹 화면에서도 그대로 부를 수 있다.

| 일 | 어디서 하나 |
| 문장 찾기, TTS 음성(캐시) | tts.py |
| 녹음 상태 점검 | quality.py |
| 녹음 인식, 단어별 시간 | stt.py |
| 채점(WER/CER), 틀린 부분 | scoring.py |
| 틀린 부분을 시간 구간으로 | align.py |

흐름
    prep = prepare(문장)                    # 문장 확인 + 기준 음성 준비 (읽기·받아쓰기 공통)
    res  = read(prep, 녹음 경로)            # 따라 읽기: 점검 → 인식 → 채점
    res  = dictation(prep, 내가 적은 글)    # 받아쓰기: 채점
    loc  = locate_errors(prep, res)         # (선택) 틀린 부분의 시간 구간과 그림용 파형

[수업에 없음] 이 파일의 '순서를 이어 붙이고 결과를 dict로 돌려주는' 구성은 직접 설계했다. 수업의 코드는
각 모듈 안(tts: 013, stt: 7강, scoring: 보충 학습)에 들어 있다.
"""
from pathlib import Path

import numpy as np

import align
import audio
import quality
import scoring
import stt
import tts


def prepare(target, sentences=None):
    """문장을 찾고 기준 음성(TTS)을 준비한다. 돌려주는 dict:
    {"error", "row", "id", "text", "lang", "meaning_ko", "tts_path", "tts_new"}

    target: sentences.csv의 id(1, "2" …) 또는 직접 쓴 문장. 직접 쓴 문장은 TTS API로 나가고 과금된다.
    tts_new: 이번 호출에서 API로 새로 만들었으면 True, 캐시를 썼으면 False.
    """
    sentences = tts.load_sentences() if sentences is None else sentences
    row, wav_path = tts.lookup_sentence(target, sentences)
    prep = {"error": None, "row": row, "id": row["id"], "text": row["sentence"], "lang": row["lang"],
            "meaning_ko": row["meaning_ko"], "tts_path": None, "tts_new": False}
    if not prep["text"]:
        prep["error"] = "문장이 비어 있습니다."
        return prep
    calls_before = tts.calls
    prep["tts_path"] = tts.tts_wav(prep["text"], wav_path)
    prep["tts_new"] = tts.calls > calls_before          # tts.calls는 API를 부를 때마다 늘어나는 호출 횟수
    return prep


def read(prep, recording=None, take=1):
    """따라 읽기: 녹음 상태 점검 → 인식 → 채점. 돌려주는 dict:
    {"mode", "error", "recording", "quality", "hyp", "seconds", "score"}

    recording: 녹음 파일 경로. 안 주면 문장 번호로 data/recordings/sNN_take{take}.*를 찾는다(직접 쓴 문장은 번호가 없어 지정 필요).
    quality는 quality.analyze의 결과(경고는 안내일 뿐 인식은 그대로 진행한다), score는 scoring.evaluate의 결과.
    """
    res = {"mode": "read", "error": prep["error"], "recording": None, "quality": None,
           "hyp": None, "seconds": None, "score": None}
    if res["error"]:
        return res
    rec = recording if recording is not None else (stt.find_recording(prep["id"], take) if prep["id"].isdigit() else None)
    if rec is None or not Path(rec).exists():
        res["error"] = ('따라 읽은 녹음이 없습니다. recording="파일 경로"로 지정하거나 '
                        'data/recordings/sNN_take1.wav로 두세요.')
        return res
    res["recording"] = rec
    res["quality"] = quality.check_file(rec)
    res["hyp"], res["seconds"] = stt.recognize(rec, prep["lang"])
    res["score"] = scoring.evaluate(prep["text"], res["hyp"], prep["lang"])
    return res


def dictation(prep, answer):
    """받아쓰기: 내가 적은 글을 정답과 비교해 채점한다(STT를 거치지 않으므로 인식 오류가 섞이지 않는다).
    돌려주는 dict: {"mode", "error", "hyp", "score"}"""
    res = {"mode": "dictation", "error": prep["error"], "hyp": answer, "score": None}
    if res["error"]:
        return res
    if not answer.strip():
        res["error"] = "입력이 비어 있어 채점하지 않습니다."
        return res
    res["score"] = scoring.evaluate(prep["text"], answer, prep["lang"])
    return res


def locate_errors(prep, res, sr=audio.TARGET_SR):
    """따라 읽기 결과(res)의 틀린 덩어리를 TTS와 내 녹음의 시간 구간으로 바꾸고, 그림에 넣을 파형을 준비한다.

    인식을 단어별 시간(stt.recognize_words)으로 두 번(내 녹음, TTS) 다시 돌리므로 몇 초 걸린다.
    돌려주는 dict: {"loc"(align.locate_errors의 결과), "sounds"(visualisation.plot_error_spans에 넘길 목록)}
    """
    _, hyp_words, _ = stt.recognize_words(res["recording"], prep["lang"])
    _, tts_words, _ = stt.recognize_words(prep["tts_path"], prep["lang"])
    loc = align.locate_errors(prep["text"], hyp_words, tts_words, prep["lang"])
    sounds = []
    for name, path, tokens, key in [("TTS 기준 음성", prep["tts_path"], loc["tts_tokens"], "tts_span"),
                                    ("내 녹음", res["recording"], loc["hyp_tokens"], "hyp_span")]:
        x, _, _ = audio.load_audio(path, sr)
        # 두 소리의 모양만 비교하려고 최대 진폭을 0.9로 맞춘다(소리 크기 차이는 그림에서 지운다).
        sounds.append((name, x / max(np.abs(x).max(), 1e-9) * 0.9, tokens, key))
    return {"loc": loc, "sounds": sounds}
