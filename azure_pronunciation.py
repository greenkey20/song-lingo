"""Azure Speech 발음 평가(Pronunciation Assessment) 결과를 우리 화면이 쓰는 dict로 바꾸는 모듈 (이슈 #48, 검토 문서 14.7의 7절).

이 모듈은 두 부분으로 나뉜다.
1부 `parse_assessment(result_json)`: Azure가 돌려주는 JSON(dict 또는 JSON 글)을 읽어 **점수 5개, 단어별·음소별 점수**로 정리한다. **네트워크·키가 필요 없어서**
   저장해 둔 JSON으로 단위 테스트를 할 수 있다(그래서 호출 코드와 분리했다).
2부 `assess(녹음, 기준 문장, locale)`: 녹음(경로·bytes) → 16 kHz 모노 PCM16 → Azure 푸시 스트림(파일로 저장하지 않음) → `recognize_once` → JSON → 1부.
   키·지역은 환경변수 `AZURE_SPEECH_KEY`·`AZURE_SPEECH_REGION`(`.env`)에서 읽고, 없으면 `NotConfigured`. **녹음이 Microsoft Azure로 전송되므로 화면에서 사용자가
   버튼을 누를 때만 부른다**(검토 문서 14.7의 7절). SDK(`azure-cognitiveservices-speech`)는 이 함수 안에서 처음 불러서 SDK가 없는 환경에서도 파서와 테스트는 돌아간다.

Azure 결과의 구조 (Microsoft 문서의 JSON 예시, 2026-11-05 확인)
    {"RecognitionStatus": ..., "DisplayText": "Hello.",
     "NBest": [{"PronunciationAssessment": {"AccuracyScore", "FluencyScore", "CompletenessScore", "ProsodyScore"(영어만), "PronScore"},
                "Words": [{"Word", "Offset", "Duration",                              # Offset·Duration은 100 나노초 단위
                           "PronunciationAssessment": {"AccuracyScore", "ErrorType"},  # ErrorType: None/Omission/Insertion/Mispronunciation …
                           "Syllables": [{"Syllable", "PronunciationAssessment": {"AccuracyScore"}, "Offset", "Duration"}],
                           "Phonemes": [{"Phoneme", "PronunciationAssessment": {"AccuracyScore", "NBestPhonemes": [{"Phoneme", "Score"}]}, ...}],
                           "Feedback": {"Prosody": {"Break": ..., "Intonation": ...}}}]}]}
    점수는 0~100(`HundredMark`로 요청한 경우). 음소 문자는 IPA. 운율(ProsodyScore·Feedback)은 en-US에서만 나온다.
    **[미확인]** `Feedback`의 안쪽 키 이름은 문서의 표로만 확인했고 실제 JSON 예시는 못 봤다. 그래서 파서는 `.get`으로 **없어도 깨지지 않게** 읽는다.

수업과의 관계
- [수업에 없음] 이 모듈 전체(Azure Speech 서비스). 외부 서비스를 감싸는 구조는 `tts.py`(013 OpenAI API 수업 코드)와 같고, **서비스 호출과 결과 해석을 나눈 것**이 다르다.
- [수업과 같음] 결과가 JSON이라 파이썬 `json`·dict·list를 읽는 방식은 수업 013(API 응답 읽기)과 같다.
"""
import json
import os

import numpy as np

import audio

TICKS_PER_SECOND = 1e7          # Azure의 Offset·Duration은 100 나노초(1e-7초) 단위

# 점수를 "좋음·보통·낮음"으로 나누는 기준.
# - FAIR_AT=60: Azure 공식 문서(ko-kr, 결과 매개 변수 표)에 "AccuracyScore가 60 미만이면 단어의 오류 유형이 Mispronunciation일 수 있다"고 적혀 있다 [확인].
# - GOOD_AT=80: 공식 기준이 **아니다**. Speech Studio 화면의 색 구분을 따른 값이다 [일반 지식, 미확인]. 학습자에게 보여 주는 라벨일 뿐이다.
GOOD_AT = 80
FAIR_AT = 60

# 쉼 오류 판정 기준. 공식 문서: 현재 버전은 쉼 오류 종류를 따로 주지 않고, UnexpectedBreak·MissingBreak의 신뢰도(Confidence)가 0.75보다 크면
# 각각 "예기치 않은 쉼"·"누락된 쉼"으로 보라고 권장한다(시나리오에 맞게 조정 가능) [확인: 문서].
BREAK_THRESHOLD = 0.75

OK_STATUS = (0, "0", "Success")  # RecognitionStatus: 예시 JSON은 숫자 0, SDK의 JSON은 "Success" 글자로 나올 수 있어 둘 다 받는다


KEY_ENV, REGION_ENV = "AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"
MAX_SECONDS = 30                 # recognize_once는 30초까지(문서: 그 이상은 연속 모드). 우리 입력은 문장 하나라 넘으면 안내하고 보내지 않는다
SR = 16000                       # Azure 푸시 스트림에 넣는 형식: 16 kHz, 16비트, 모노(audio.TARGET_SR과 같다)
PROSODY_LOCALES = ("en-US",)     # 운율 평가는 en-US에서만 된다(Microsoft 문서)


class NotConfigured(RuntimeError):
    """Azure 키·지역이 설정되지 않았거나 SDK가 없을 때. 화면은 이 메시지를 안내 문구로 보여 준다."""


class AssessmentError(ValueError):
    """Azure가 평가를 돌려주지 못한 경우(소리 없음, 인식 실패, 결과 구조가 예상과 다름)."""


def level(score):
    """점수(0~100) → "good"(80 이상) / "fair"(60 이상) / "poor"(그 미만). 점수가 None이면 None."""
    if score is None:
        return None
    return "good" if score >= GOOD_AT else "fair" if score >= FAIR_AT else "poor"


def _score(block, key):
    """{"AccuracyScore": 95.0, ...}에서 key의 값을 float으로. 없으면 None(운율은 영어가 아니면 없다)."""
    value = (block or {}).get(key)
    return None if value is None else float(value)


def _seconds(ticks):
    return None if ticks is None else ticks / TICKS_PER_SECOND


def _parse_phonemes(raw_phonemes):
    """음소 목록을 [{"phoneme", "accuracy", "heard"}]로. heard는 NBestPhonemes에서 점수가 가장 높은 음소가 **기대한 음소와 다를 때만** 그 음소(들린 소리), 같거나 후보가 없으면 None."""
    out = []
    for ph in raw_phonemes or []:
        pa = ph.get("PronunciationAssessment") or {}
        expected = ph.get("Phoneme")
        heard = None
        nbest = pa.get("NBestPhonemes") or []
        if nbest:
            top = max(nbest, key=lambda c: c.get("Score", 0))
            if top.get("Phoneme") != expected:
                heard = top.get("Phoneme")
        out.append({"phoneme": expected, "accuracy": _score(pa, "AccuracyScore"), "heard": heard})
    return out


def _parse_prosody_feedback(word):
    """단어의 운율 피드백을 {"break": [...], "break_confidence": {...}, "intonation": [...]}로. 영어가 아니거나 요청하지 않았으면 빈 값.

    - break: JSON에 `Break.ErrorTypes`가 있으면 그대로 쓰고, 없으면 `UnexpectedBreak.Confidence`·`MissingBreak.Confidence`가 BREAK_THRESHOLD(0.75)보다 클 때 해당 이름을 넣는다.
    - intonation: `Intonation.ErrorTypes`(지금은 Monotone만; 발화 전체에서 한 번 판정해 모든 단어에 같은 태그가 붙는다).
    안쪽 키 이름은 공식 문서의 표를 따른 것이고 **실제 응답으로는 아직 확인하지 못했다 [미확인]** 그래서 `.get`으로 없어도 깨지지 않게 읽는다."""
    prosody = ((word.get("Feedback") or {}).get("Prosody")) or {}
    brk = prosody.get("Break") or {}
    conf = {"unexpected": (brk.get("UnexpectedBreak") or {}).get("Confidence"),
            "missing": (brk.get("MissingBreak") or {}).get("Confidence")}
    kinds = list(brk.get("ErrorTypes") or [])
    for name, key in (("UnexpectedBreak", "unexpected"), ("MissingBreak", "missing")):
        if name not in kinds and conf[key] is not None and conf[key] > BREAK_THRESHOLD:
            kinds.append(name)
    return {"break": kinds, "break_confidence": conf,
            "intonation": list((prosody.get("Intonation") or {}).get("ErrorTypes") or [])}


def expected_pron_score(accuracy, fluency, completeness, prosody=None):
    """Azure 공식 문서의 **읽기(스크립트) 시나리오 종합 점수 공식**으로 종합 점수를 직접 계산한다(검증·설명용).

    네 점수(운율이 없으면 셋)를 낮은 순서로 s0 ≤ s1 ≤ s2 ≤ s3라 할 때
      운율 있음: 0.4·s0 + 0.2·s1 + 0.2·s2 + 0.2·s3     운율 없음: 0.6·s0 + 0.2·s1 + 0.2·s2
    즉 **가장 낮은 점수에 가장 큰 가중치**를 준다. 그래서 한 항목(예: 완성도)이 낮으면 종합이 크게 내려간다.
    11-05 실제 결과 5건(첫 호출과 정상·생략·끊어 읽기·틀린 발음)에서 Azure가 돌려준 PronScore와 소수 첫째 자리까지 맞았다(단위 테스트)."""
    if prosody is None:
        s0, s1, s2 = sorted((accuracy, fluency, completeness))
        return 0.6 * s0 + 0.2 * s1 + 0.2 * s2
    s0, s1, s2, s3 = sorted((accuracy, fluency, completeness, prosody))
    return 0.4 * s0 + 0.2 * s1 + 0.2 * s2 + 0.2 * s3


def parse_assessment(result):
    """Azure 발음 평가 결과(JSON 글 또는 이미 읽은 dict) → 화면용 dict.

    돌려주는 값:
      {"text": 인식된 글, "locale_has_prosody": 운율 점수가 있는가,
       "scores": {"accuracy", "fluency", "completeness", "prosody", "pronunciation"}   # 0~100, 없으면 None
       "words": [{"word", "accuracy", "level", "error_type", "start", "duration",       # 초
                  "syllables": [{"syllable", "accuracy"}], "phonemes": [{"phoneme", "accuracy", "heard"}],
                  "prosody": {"break": [...], "intonation": [...]}}],
       "weak_words": 점수가 낮거나(poor) 오류 종류가 None이 아닌 단어의 목록}
    예외: AssessmentError — 결과가 비었거나 인식 실패(RecognitionStatus가 성공이 아님)이거나 NBest·PronunciationAssessment가 없을 때."""
    data = json.loads(result) if isinstance(result, (str, bytes)) else result
    if not isinstance(data, dict):
        raise AssessmentError("평가 결과가 JSON 객체가 아닙니다.")
    status = data.get("RecognitionStatus", 0)
    if status not in OK_STATUS:
        raise AssessmentError(f"인식하지 못했어요(RecognitionStatus={status}). 소리가 너무 작거나 말이 없는지 확인하세요.")
    nbest = data.get("NBest") or []
    if not nbest:
        raise AssessmentError("평가 결과에 NBest가 없습니다.")
    best = nbest[0]                                           # 첫 번째가 가장 가능성이 높은 인식 결과
    pa = best.get("PronunciationAssessment")
    if not pa:
        raise AssessmentError("발음 평가 점수가 없습니다(평가를 켜지 않고 요청했는지 확인하세요).")

    words = []
    for w in best.get("Words") or []:
        wpa = w.get("PronunciationAssessment") or {}
        accuracy = _score(wpa, "AccuracyScore")
        words.append({
            "word": w.get("Word"), "accuracy": accuracy, "level": level(accuracy),
            "error_type": wpa.get("ErrorType", "None"),
            "start": _seconds(w.get("Offset")), "duration": _seconds(w.get("Duration")),
            "syllables": [{"syllable": s.get("Syllable"), "accuracy": _score(s.get("PronunciationAssessment"), "AccuracyScore")}
                          for s in w.get("Syllables") or []],
            "phonemes": _parse_phonemes(w.get("Phonemes")),
            "prosody": _parse_prosody_feedback(w),
        })
    scores = {"accuracy": _score(pa, "AccuracyScore"), "fluency": _score(pa, "FluencyScore"),
              "completeness": _score(pa, "CompletenessScore"), "prosody": _score(pa, "ProsodyScore"),
              "pronunciation": _score(pa, "PronScore")}
    return {"text": data.get("DisplayText") or best.get("Display") or "",
            "locale_has_prosody": scores["prosody"] is not None,
            "scores": scores, "words": words,
            "weak_words": [w for w in words if w["level"] == "poor" or w["error_type"] not in (None, "None")]}


# ---------- 2부: Azure 호출 ----------
def pcm16_bytes(source, sr=SR):
    """녹음(경로·bytes·파일 객체) → 16 kHz 모노 **PCM16 원시 바이트**와 길이(초): (bytes, seconds).

    [수업과 같음] audio.load_audio가 wav 읽기·모노·16 kHz 리샘플링을 한다(02). 정수로 되돌리는 것은 02의 PCM16 저장과 반대 방향(실수 -1~1 × 32767)이다.
    [수업에 없음] Azure SDK의 푸시 스트림은 WAV 머리글이 없는 **원시 PCM**을 받는다."""
    x, _orig_sr, _ch = audio.load_audio(source, sr)
    pcm = (np.clip(x, -1.0, 1.0) * 32767).astype("<i2")      # little-endian 16비트 정수
    return pcm.tobytes(), len(x) / sr


def _credentials(key=None, region=None):
    key = key or os.environ.get(KEY_ENV)
    region = region or os.environ.get(REGION_ENV)
    if not key or not region:
        raise NotConfigured(f".env에 {KEY_ENV}와 {REGION_ENV}를 적어 주세요(Azure 포털의 Speech 리소스 > 키 및 엔드포인트). 서버를 다시 띄워야 반영돼요.")
    return key, region


def _pronunciation_config(speechsdk, reference_text, prosody):
    """발음 평가 요청 설정을 만든다(네트워크 없음, SDK만 필요). 기준 문장, 0~100점, 음소 단위까지, 빠짐·끼어듦 계산, 음소 후보 5개, **IPA 기호**.

    음소 기호를 지정하지 않으면 영어(en-US)는 SAPI 기호(iy·ax·eh 같은 영문자)로 나온다. 화면은 IPA(ɛ·ə)라고 안내하므로 IPA로 요청한다
    (11-05 첫 화면에서 SAPI 기호가 나와 안내와 달랐던 것을 고침). 설정이 JSON에 실제로 들어갔는지는 config.to_json()으로 확인한다."""
    config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True)                                  # True면 빠진 단어(Omission)·끼어든 단어(Insertion)를 오류 종류로 표시
    config.phoneme_alphabet = "IPA"
    config.nbest_phoneme_count = 5                           # 음소마다 "가장 가깝게 들린 음소 후보" 5개(파서의 heard)
    if prosody:
        config.enable_prosody_assessment()                   # 운율(억양·강세·속도·리듬), en-US만
    return config


def _azure_recognize(pcm, reference_text, locale, key, region, prosody):
    """Azure Speech SDK로 발음 평가를 한 번 요청해 **결과 JSON 글**을 돌려준다(네트워크 호출, 키·SDK 필요). 테스트에서는 이 함수를 가짜로 바꾼다.

    [수업에 없음] Azure Speech SDK. 순서: SpeechConfig(키·지역) → 푸시 스트림에 PCM을 넣고 닫기 → SpeechRecognizer(언어) → PronunciationAssessmentConfig
    (기준 문장, 0~100점, 음소 단위까지, 빠짐·끼어듦 계산) → apply_to(recognizer) → recognize_once() → 결과 속성의 JSON."""
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        raise NotConfigured("azure-cognitiveservices-speech가 설치돼 있지 않아요(앱 환경: pip install -r app/requirements.txt).") from None
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    stream = speechsdk.audio.PushAudioInputStream(speechsdk.audio.AudioStreamFormat(samples_per_second=SR, bits_per_sample=16, channels=1))
    stream.write(pcm)
    stream.close()                                           # 닫아야 인식기가 "소리가 끝났다"고 안다
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language=locale,
                                            audio_config=speechsdk.audio.AudioConfig(stream=stream))
    config = _pronunciation_config(speechsdk, reference_text, prosody)
    config.apply_to(recognizer)
    result = recognizer.recognize_once()
    reason = speechsdk.ResultReason
    if result.reason == reason.RecognizedSpeech:
        return result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
    if result.reason == reason.NoMatch:
        raise AssessmentError("말소리를 알아듣지 못했어요. 소리가 너무 작거나 말이 없는지 확인하세요.")
    details = speechsdk.CancellationDetails(result)          # 키·지역이 틀리거나 한도 초과일 때 여기로 온다(키 값은 메시지에 없다)
    raise AssessmentError(f"Azure 요청이 취소됐어요({details.reason.name}): {details.error_details}")


def assess(recording, reference_text, locale="en-US", key=None, region=None, prosody=None, recognize=None):
    """녹음 하나를 기준 문장과 비교해 Azure에 발음 평가를 요청하고 parse_assessment의 dict에 {"locale", "seconds"}를 더해 돌려준다.

    recording: 경로·bytes·파일 객체(웹 녹음). reference_text: 읽어야 할 문장(빈 글이면 ValueError). locale: "en-US" 등.
    prosody: 운율 평가를 켤지. None이면 en-US일 때만 켠다. recognize: 테스트용 가짜 호출 함수(pcm, ref, locale, key, region, prosody) → JSON.
    예외: NotConfigured(키·지역·SDK 없음, **네트워크 호출 전에 확인**), ValueError(빈 문장), AssessmentError(30초 초과·인식 실패·취소)."""
    if not str(reference_text).strip():
        raise ValueError("기준 문장이 비어 있습니다.")
    key, region = _credentials(key, region)
    pcm, seconds = pcm16_bytes(recording)
    if seconds > MAX_SECONDS:
        raise AssessmentError(f"녹음이 {seconds:.0f}초예요. {MAX_SECONDS}초 이하의 한 문장만 평가할 수 있어요.")
    if prosody is None:
        prosody = locale in PROSODY_LOCALES
    raw = (recognize or _azure_recognize)(pcm, str(reference_text).strip(), locale, key, region, prosody)
    out = parse_assessment(raw)
    out.update({"locale": locale, "seconds": round(seconds, 2)})
    return out
