"""녹음 입력 상태 점검: 음량 · 무음 · 클리핑만 본다(이슈 #7). 잡음이 있는지는 판정하지 않는다.

점검 항목과 경고 기준은 계획서(20261030) 3장 "녹음 입력 상태 점검 방법" 표를 따른다. **기준값은 초안**이라
본인 녹음으로 확정한다(아래 상수를 바꾸면 된다). 경고는 '이 녹음은 인식이 잘 안 될 수 있다'는 안내이고
녹음을 거부하는 것이 아니다. 발음이 좋은지 나쁜지와는 상관이 없다.

| 점검 | 계산 | 경고 기준(초안) |
| 빈 파일·길이 | 샘플 수 ÷ sr | 길이가 MIN_SECONDS보다 짧음 |
| 너무 작음 | 전체 RMS(dBFS), 최대 진폭 | RMS < -40 dBFS 또는 최대 진폭 < 0.05 |
| 클리핑 | 원본 샘플 중 절댓값 ≥ 0.999 인 비율 | 0.1% 이상 |
| 대부분 무음 | STFT 프레임 에너지가 가장 큰 프레임보다 35 dB 이상 낮은 프레임의 비율 | 80% 이상 |
| (참고) 저주파 웅웅거림 | 80 Hz 이하 에너지 비율 | 경고 없이 값만 보여 줌 |
| (참고) 앞 무음 | 처음으로 소리가 나는 프레임까지의 시간 | 경고 없이 값만 보여 줌 |

수업과의 관계
- [수업과 같음] RMS, 최대 진폭, STFT 프레임 에너지, dB 변환은 수업(02 WAV 전처리, 03 STFT)의 개념과 같다.
  STFT 계산은 visualisation.stft_power를 그대로 쓴다.
- [수업에 없음] 클리핑 비율, '가장 큰 프레임 대비 상대 기준' 무음 판정, 점검 결과를 경고 목록으로 돌려주는 구성.
"""
import numpy as np

import audio
import visualisation

# ---- 경고 기준 (초안: 본인 녹음으로 확정) --------------------------------------------------------------
MIN_SECONDS = 0.5            # 이보다 짧으면 경고. [제안값: 계획서에는 '너무 짧음'만 있고 숫자가 없다]
MIN_RMS_DBFS = -40.0         # 전체 RMS가 이보다 작으면 '너무 작음'
MIN_PEAK = 0.05              # 최대 진폭이 이보다 작으면 '너무 작음'
CLIP_LEVEL = 0.999           # 절댓값이 이 이상이면 한계에 닿은(잘린) 샘플로 센다
MAX_CLIP_RATIO = 0.001       # 잘린 샘플이 0.1% 이상이면 경고
SILENCE_BELOW_DB = 35.0      # 가장 큰 프레임보다 이만큼(dB) 이상 낮으면 무음 프레임
MAX_SILENT_RATIO = 0.80      # 무음 프레임이 80% 이상이면 경고
LOW_HZ = 80.0                # 이 주파수 이하를 '저주파'로 본다(참고 정보)

_EPS = 1e-10                 # log10(0)을 피하기 위한 아주 작은 값


def _dbfs(amplitude):
    """진폭(최대 1.0) → dBFS. 1.0이 0 dBFS, 0.1이 -20 dBFS. 0이면 -200 dBFS로 바닥을 둔다."""
    return 20 * np.log10(max(float(amplitude), _EPS))


def analyze(raw, orig_sr, sr=audio.TARGET_SR):
    """원본 샘플(audio.load_raw의 결과)로 상태를 점검한다. 돌려주는 값: {"ok", "metrics", "warnings", "info"}.

    raw: (샘플, 채널) float 배열. 클리핑은 원본 샘플로, 나머지는 16 kHz 모노로 바꾼 파형으로 계산한다
    (리샘플링 울림이 없던 클리핑을 만들어 내지 않게 하려는 것이다).
    """
    raw = np.asarray(raw, dtype=np.float32)
    if raw.ndim == 1:
        raw = raw[:, None]
    warnings, metrics = [], {}

    seconds = raw.shape[0] / orig_sr if raw.size else 0.0
    metrics["seconds"] = seconds
    if seconds < MIN_SECONDS:
        warnings.append(f"녹음이 너무 짧습니다({seconds:.2f}초). {MIN_SECONDS:g}초 이상 녹음하세요.")
    if raw.size == 0:
        return {"ok": False, "metrics": metrics, "warnings": warnings, "info": {}}

    # 클리핑과 최대 진폭은 원본 샘플로 잰다. 16 kHz로 바꾼 파형은 가장자리 울림 때문에 최대값이 1을 살짝 넘을 수 있다.
    metrics["clip_ratio"] = float(np.mean(np.abs(raw) >= CLIP_LEVEL))   # 모든 채널의 샘플 중 한계에 닿은 비율
    metrics["peak"] = float(np.abs(raw).max())

    x = audio.to_16k_mono(raw, orig_sr, sr)          # 이후 점검은 16 kHz 모노 파형으로
    metrics["rms_dbfs"] = _dbfs(np.sqrt(np.mean(x.astype(np.float64) ** 2)))

    # 프레임별 에너지(dB). visualisation.stft_power의 (주파수, 시간) 파워를 주파수 방향으로 더한다.
    hz, times, power = visualisation.stft_power(x, sr)
    info = {}
    if power.shape[1] > 0:
        frame_db = visualisation.to_db(power.sum(axis=0))
        # 상대 기준: '가장 큰 프레임보다 35 dB 이상 낮은' 프레임을 무음으로 본다.
        # 작게 녹음된 파일도 말하는 부분은 그 파일 안에서 가장 크기 때문에, 절대 기준(예: -60 dB)보다 공정하다.
        silent = frame_db < frame_db.max() - SILENCE_BELOW_DB
        metrics["silent_ratio"] = float(silent.mean())
        voiced = np.flatnonzero(~silent)
        info["leading_silence_sec"] = float(times[voiced[0]]) if voiced.size else float(times[-1])
        total = float(power.sum())
        info["low_freq_ratio"] = float(power[hz <= LOW_HZ].sum() / total) if total > 0 else 0.0
    else:
        metrics["silent_ratio"] = 0.0     # 프레임을 만들기엔 너무 짧은 파형(이미 '너무 짧음' 경고가 붙는다)

    if metrics["rms_dbfs"] < MIN_RMS_DBFS or metrics["peak"] < MIN_PEAK:
        warnings.append(f"소리가 너무 작습니다(RMS {metrics['rms_dbfs']:.1f} dBFS, 최대 진폭 {metrics['peak']:.3f}). "
                        "마이크에 더 가까이 하거나 입력 음량을 높여 보세요.")
    if metrics["clip_ratio"] >= MAX_CLIP_RATIO:
        warnings.append(f"소리가 잘렸을 수 있습니다(한계에 닿은 샘플 {metrics['clip_ratio'] * 100:.2f}%). "
                        "입력 음량을 낮추거나 마이크에서 조금 떨어져 보세요.")
    if metrics["silent_ratio"] >= MAX_SILENT_RATIO:
        warnings.append(f"대부분이 무음입니다(무음 구간 {metrics['silent_ratio'] * 100:.0f}%). "
                        "말하는 부분이 짧거나 소리가 잘 들어가지 않았을 수 있습니다.")
    return {"ok": not warnings, "metrics": metrics, "warnings": warnings, "info": info}


def check_file(path, sr=audio.TARGET_SR):
    """녹음 파일 경로 → analyze 결과. wav·webm·m4a 등 audio.load_raw가 읽는 형식이면 된다."""
    raw, orig_sr, _channels = audio.load_raw(path)
    return analyze(raw, orig_sr, sr)


def format_report(result):
    """analyze 결과를 사람이 읽는 몇 줄의 글로 만든다. 경고가 없으면 '이상 없음'."""
    m, info = result["metrics"], result["info"]
    head = "녹음 상태: 이상 없음" if result["ok"] else "녹음 상태: 확인이 필요합니다"
    lines = [head]
    lines += [f"  ⚠ {w}" for w in result["warnings"]]
    if "rms_dbfs" in m:
        lines.append(f"  (참고) 길이 {m['seconds']:.1f}초, RMS {m['rms_dbfs']:.1f} dBFS, 최대 진폭 {m['peak']:.2f}, "
                     f"클리핑 {m['clip_ratio'] * 100:.2f}%, 무음 프레임 {m['silent_ratio'] * 100:.0f}%")
        if info:
            lines.append(f"  (참고) 앞 무음 {info['leading_silence_sec']:.1f}초, "
                         f"{LOW_HZ:g} Hz 이하 에너지 {info['low_freq_ratio'] * 100:.1f}%")
    return "\n".join(lines)
