"""녹음의 기본주파수(F0, 목소리의 음높이) 윤곽을 구한다. 이슈 #82, 검토 문서 16.18.

F0는 성대가 1초에 몇 번 진동하는가(Hz)이고, 유성음(모음 등)에서만 값이 있다. 이 모듈은 **발음 점수를 만들지 않는다**:
시간에 따른 음높이 변화를 관찰할 수 있게 숫자를 구해 줄 뿐이다(WER/CER은 인식 일치도, Azure는 외부 발음 평가, F0는 음향 관찰).

흐름
    audio.load_audio(source, 16 kHz)  →  librosa.pyin  →  f0·voiced_flag·voiced_probs(프레임마다)
    →  valid(유성이고 값이 있는 프레임)  →  중앙값·P10·P90·폭(semitone)  /  relative_semitones(중앙값 기준 상대 음높이)

- **무성음·무음 프레임의 f0는 NaN**이다. 0 Hz로 바꾸지 않는다(0은 "측정된 음높이"가 아니다). 그래프는 NaN에서 선이 끊긴다.
- 기대할 수 있는 실패(너무 짧음, 유성음 부족, librosa 없음)는 예외가 아니라 `status`로 돌려준다. 화면은 status를 보고 안내만 한다.
  소리를 읽을 수 없는 등 예상 못 한 예외는 그대로 올라가며, 부르는 화면이 F0 칸에만 안내하도록 잡는다(채점 결과에는 영향을 주지 않는다).
- 음악·반주가 섞인 소리에는 쓰지 않는다(pYIN은 주된 음높이가 하나인 단일 화자 소리용).

수업과의 관계
- [수업과 같음] 16 kHz 모노 변환(audio.load_audio, 02), 주기 신호와 주파수(01·03: 200 Hz면 한 주기가 5 ms = 16 kHz에서 80샘플).
  FFT·STFT는 "어떤 주파수 성분이 얼마나 센가"이고, F0는 "소리가 얼마 주기로 반복되는가"라서 같은 값이 아니다(배음이 더 클 수 있다).
- [수업에 없음] pYIN(librosa.pyin): YIN(파형을 조금씩 밀어 자기 자신과 얼마나 비슷한지 보고 주기를 찾는 방법)에 확률적 후보 평가와
  시간 연속성(HMM·Viterbi), 유성/무성 판정을 더한 알고리즘. [수업에 없음] semitone(반음): 음높이 차이의 단위, 12 semitone = 2배(한 옥타브).
- [수업에 없음] librosa는 numba를 쓴다. 첫 호출에서 컴파일 때문에 몇 초 걸릴 수 있다.
"""
import time

import numpy as np

import audio

SR = audio.TARGET_SR              # 16000. 목소리의 F0(대개 80~400 Hz)와 말소리 정보를 다루기에 충분한 표본화 주파수
FMIN, FMAX = 65.0, 500.0          # 찾을 F0의 범위(Hz). 시작값일 뿐 모든 화자에게 맞는 절대 범위가 아니다(실제 녹음에서 한쪽에 몰리는지 확인)
FRAME_LENGTH = 2048               # 한 번의 추정에 쓰는 샘플 수(128 ms). 가장 낮은 F0(65 Hz)의 주기(약 15 ms)가 여러 번 들어가야 한다
HOP_LENGTH = 320                  # 프레임 사이 간격(샘플): 20 ms마다 F0를 하나 구한다(단어 하나가 보통 0.2초 이상이라 윤곽을 보기에 충분)
RESOLUTION = 0.25                 # pYIN이 F0 후보를 나누는 간격(semitone). 기본 0.1이면 후보 칸이 2.5배라 5초 녹음에 8.6초 걸렸고 0.25로 키우면
                                  # 같은 중앙값에 4배 빨랐다(Intel i7 CPU 측정, 검토 문서 16.18). 반음의 1/4 단위면 억양 관찰에는 충분하다
MIN_VOICED_FRAMES = 10            # 요약(중앙값 등)을 보여 줄 최소 유성음 프레임 수. 제품 기준이며 pYIN의 요구사항이 아니다
JUMP_SEMITONES = 6.0              # 이웃한 유성음 프레임 사이에 이만큼 튀면 "추정이 흔들림" 후보(옥타브 오류를 의심)


def _result(status, **extra):
    """analyze_f0가 돌려주는 dict의 틀. 값이 없는 칸은 None."""
    out = {"status": status, "times": None, "f0": None, "voiced_flag": None, "voiced_probs": None, "valid": None,
           "median_hz": None, "p10_hz": None, "p90_hz": None, "range_semitones": None,
           "n_voiced": 0, "jump_ratio": None, "duration": None, "seconds": None}
    out.update(extra)
    return out


def valid_mask(f0, voiced_flag=None):
    """요약·정규화에 쓸 프레임: 유성음으로 판정됐고(voiced_flag가 있으면), 값이 유한하며 0보다 큰 프레임만 True.
    NaN(무성음·무음), inf, 0 이하는 모두 제외한다."""
    f0 = np.asarray(f0, dtype=float)
    ok = np.isfinite(f0) & (f0 > 0)
    if voiced_flag is not None:
        ok &= np.asarray(voiced_flag, dtype=bool)
    return ok


def relative_semitones(f0, valid, median_hz=None):
    """각 프레임의 음높이를 **그 화자의 중앙 F0 기준 상대 semitone**으로 바꾼다: 12 · log2(F0 / 중앙값).

    왜: 목소리의 기본 높이(남녀·합성 목소리)는 사람마다 달라서 절대 Hz를 비교하면 안 된다. 중앙값을 0으로 맞추면
    "자기 기본 높이에서 얼마나 올라가고 내려갔는가"만 남는다(+12는 중앙값의 2배, -12는 절반).
    f0·valid: 같은 길이의 배열. median_hz: 안 주면 valid인 프레임의 중앙값. 돌려주는 값: 같은 길이의 배열이며 valid가 아닌 프레임과
    유성 프레임이 없을 때는 모두 NaN(0으로 채우지 않음)."""
    f0 = np.asarray(f0, dtype=float)
    valid = np.asarray(valid, dtype=bool) & valid_mask(f0)
    out = np.full(f0.shape, np.nan)
    if not valid.any():
        return out
    ref = float(np.median(f0[valid])) if median_hz is None else float(median_hz)
    if not (np.isfinite(ref) and ref > 0):
        return out
    out[valid] = 12.0 * np.log2(f0[valid] / ref)
    return out


def jump_ratio(rel, valid):
    """바로 이웃한 두 유성음 프레임 사이에서 JUMP_SEMITONES 넘게 튄 비율(0~1). 옥타브 오류(F0가 두 배·절반으로 잡힘)를 의심할 때 쓰는 참고값.
    유성음 구간이 끊긴 곳(사이에 무성음)은 이웃으로 세지 않는다. 비교할 쌍이 없으면 None."""
    rel = np.asarray(rel, dtype=float)
    both = np.asarray(valid, dtype=bool)
    both = both[1:] & both[:-1]
    if not both.any():
        return None
    diff = np.abs(np.diff(rel))[both]
    return float((diff > JUMP_SEMITONES).mean())


def analyze_f0(source, fmin=FMIN, fmax=FMAX, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH):
    """녹음 하나(경로·bytes·파일 객체)의 F0 윤곽과 요약을 구한다. 돌려주는 dict:

    status: "ok" / "too_short"(분석 창보다 짧음) / "insufficient_voicing"(유성음 프레임이 MIN_VOICED_FRAMES 미만) / "unavailable"(librosa 없음)
    times(초)·f0(Hz, 무성음은 NaN)·voiced_flag·voiced_probs·valid: 프레임마다 하나(길이가 같다). 시간은 원본 녹음의 시간축과 같다(Whisper 단어 시간과 겹칠 수 있다).
    median_hz·p10_hz·p90_hz·range_semitones: valid 프레임의 중앙값·10%·90% 지점·P10~P90의 폭(semitone). 최소·최대 대신 백분위를 쓰는 이유는
    옥타브 오류 같은 이상치에 덜 흔들리기 때문이다. status가 "ok"가 아니면 None.
    n_voiced: valid 프레임 수. jump_ratio: jump_ratio() 참고. duration: 소리 길이(초). seconds: 분석에 걸린 시간.
    audio.load_audio가 읽지 못하는 입력이면 그 예외를 그대로 올린다."""
    t0 = time.time()
    try:
        import librosa           # 지연 import: 앱 시작과 F0를 안 쓰는 화면에는 비용을 안 준다(numba 불러오기가 느리다)
    except ImportError:
        return _result("unavailable")
    y, _sr, _ch = audio.load_audio(source, SR)
    duration = len(y) / SR
    if len(y) < frame_length:
        return _result("too_short", duration=duration, seconds=time.time() - t0)
    f0, voiced_flag, voiced_probs = librosa.pyin(y, sr=SR, fmin=fmin, fmax=fmax, frame_length=frame_length, hop_length=hop_length,
                                         resolution=RESOLUTION)
    times = librosa.times_like(f0, sr=SR, hop_length=hop_length)
    valid = valid_mask(f0, voiced_flag)
    n_voiced = int(valid.sum())
    out = _result("ok" if n_voiced >= MIN_VOICED_FRAMES else "insufficient_voicing", times=times, f0=f0, voiced_flag=voiced_flag,
                  voiced_probs=voiced_probs, valid=valid, n_voiced=n_voiced, duration=duration)
    if out["status"] == "ok":
        p10, median, p90 = np.percentile(f0[valid], [10, 50, 90])
        out.update(median_hz=float(median), p10_hz=float(p10), p90_hz=float(p90),
                   range_semitones=float(12.0 * np.log2(p90 / p10)),
                   jump_ratio=jump_ratio(relative_semitones(f0, valid, median), valid))
    out["seconds"] = time.time() - t0
    return out
