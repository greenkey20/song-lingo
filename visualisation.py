"""소리를 '시간-주파수 그림'용 숫자로 바꾸는 함수 모음: STFT 파워, Mel 필터, Log-Mel(이슈 #23).

원래 practice.ipynb 셀 안에 있던 수업 코드를 그대로 옮겼다(동작 변경 없음). 모듈로 빼 둔 이유는 두 가지다.
- quality.py(녹음 상태 점검)가 '프레임별 에너지'를 계산할 때 같은 STFT를 재사용한다.
- 노트북 밖에서 단위 테스트를 할 수 있다.

수업과의 관계
- [수업과 같음] STFT 설정(창 512, 이동 128, hann), 삼각형 Mel 필터 40개, 파워를 dB로 바꾸는 순서.
  출처: 017_sound/03_FFT_STFT_그림으로_소리읽기.ipynb(`compute_stft`), lesson04 실습 2-F(Mel 필터), 3-B(logmel).
- [수업에 없음] `stft_power` 함수로 한 번 감싼 것(logmel과 quality.py가 함께 쓰려는 용도)과 to_db 함수화.

이 모듈에는 '그릴 숫자'를 계산하는 함수(stft_power, logmel …)와 그림을 그리는 함수(plot_sound_pair,
plot_error_spans)가 함께 있다. 그림 함수는 파형과 단어별 시간을 인자로 받아 figure를 돌려줄 뿐,
녹음 찾기·인식·채점은 하지 않는다(그건 노트북의 practice/show_error_spans가 stt·align을 불러 준비한다).
[수업에 없음] 그림 함수의 구성(3x2 격자, 색 막대 칸, 틀린 구간 표시)은 직접 만든 것이고, 그리는 도구인
matplotlib 사용법(subplots, pcolormesh, axvspan)은 수업과 같다.
"""
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import stft

import theme

# 수업과 같은 설정. 16 kHz에서 창 512개 = 32 ms, 이동 128개 = 8 ms.
FRAME_LENGTH = 512
HOP_LENGTH = 128
N_MELS = 40


def stft_power(sound, sr, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH):
    """파형 → (주파수 축 hz, 시간 축 times, 파워 스펙트로그램). 파워의 모양은 (주파수 칸, 시간 프레임).

    scipy.signal.stft의 옵션 설명(수업의 compute_stft와 같은 값):
    - nperseg=frame_length: 한 번에 보는 창의 길이.
    - noverlap=frame_length - hop_length: 창끼리 겹치는 길이. 겹침이 클수록 창이 hop_length씩만 이동한다.
    - boundary=None, padded=False: 앞뒤를 0으로 채우지 않는다. 그래서 프레임 수는
      1 + (샘플 수 - frame_length) // hop_length 이다.
    - scaling="spectrum": 진폭 스케일. 절댓값을 제곱(|X|^2)한 값을 '파워'로 쓴다.
    """
    hz, times, spectrum = stft(sound, fs=sr, window="hann", nperseg=frame_length,
                               noverlap=frame_length - hop_length, nfft=frame_length,
                               boundary=None, padded=False, detrend=False, scaling="spectrum")
    return hz, times, np.abs(spectrum) ** 2


def to_db(power):
    """파워 → 데시벨: 10 * log10(파워). 파워 0에서 log가 -무한대가 되지 않게 1e-10(-100 dB)을 바닥으로 둔다."""
    return 10 * np.log10(np.maximum(power, 1e-10))


def apply_mel_filters(hz, power, sr, n_mels=N_MELS):
    """STFT 파워 → 삼각형 Mel 필터 가중합. 돌려주는 값: (Mel 파워 (n_mels, 시간), 필터 (n_mels, 주파수 칸)).

    Mel 눈금은 사람 귀가 낮은 소리 차이에 더 민감한 점을 반영해 주파수를 비선형으로 나눈 것이다.
    0 Hz ~ sr/2 구간을 Mel 눈금에서 같은 간격으로 n_mels + 2개 점으로 나누고,
    이웃한 세 점(왼쪽·가운데·오른쪽)이 삼각형 하나(필터 하나)가 된다.
    """
    hz_to_mel = lambda f: 2595.0 * np.log10(1.0 + f / 700.0)
    mel_to_hz = lambda m: 700.0 * (10.0 ** (m / 2595.0) - 1.0)
    edges = mel_to_hz(np.linspace(hz_to_mel(0), hz_to_mel(sr / 2), n_mels + 2))
    filters = np.zeros((n_mels, len(hz)))
    for k in range(n_mels):
        left, center, right = edges[k:k + 3]
        # 삼각형: 왼쪽 경사 (hz-left)/(center-left)와 오른쪽 경사 (right-hz)/(right-center) 중 작은 값, 음수는 0.
        filters[k] = np.maximum(0, np.minimum((hz - left) / (center - left), (right - hz) / (right - center)))
    return filters @ power, filters


def logmel(sound, sr, n_mels=N_MELS, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH):
    """파형 → STFT 파워 → Mel 파워 → Log-Mel(dB). 그림에 쓸 값을 딕셔너리로 돌려준다.

    돌려주는 값: {"hz", "times", "power"(STFT 파워), "log_mel"(Mel 칸, 시간)}
    """
    hz, times, power = stft_power(sound, sr, frame_length, hop_length)
    mel_power, _ = apply_mel_filters(hz, power, sr, n_mels)
    return {"hz": hz, "times": times, "power": power, "log_mel": to_db(mel_power)}


def plot_sound_pair(sounds, title, sr=16000):
    """소리 여러 개(보통 2개: TTS와 내 녹음)를 같은 설정·같은 색 범위로 나란히 그린다. 위부터 파형, 스펙트로그램, Log-Mel.

    sounds: [(이름, 16 kHz 모노 파형)]. 비교를 위해 최대 진폭을 0.9로 맞춘 파형을 넣는다.
    돌려주는 값: matplotlib Figure (화면에 보이려면 호출한 쪽에서 plt.show()).
    """
    theme.apply_style()
    feats = [(name, x, logmel(x, sr)) for name, x in sounds]
    # 두 소리를 같은 색 범위(가장 센 값 기준 80 dB 아래까지)로 그려야 밝기를 비교할 수 있다.
    spec_max = max(to_db(f["power"]).max() for _, _, f in feats)
    mel_max = max(f["log_mel"].max() for _, _, f in feats)
    t_max = max(len(x) for _, x, _ in feats) / sr          # 두 그림의 시간축을 같게

    fig, axes = plt.subplots(3, len(feats), figsize=(13, 9), sharex=True, squeeze=False)
    for col, (name, x, f) in enumerate(feats):
        axes[0, col].plot(np.arange(len(x)) / sr, x, lw=0.6, color=theme.WAVEFORM)   # 파형은 수업과 같은 기본 파랑
        axes[0, col].set(title=name, ylabel="진폭", ylim=(-1, 1))
        im1 = axes[1, col].pcolormesh(f["times"], f["hz"] / 1000, to_db(f["power"]),
                                      shading="auto", cmap=theme.CMAP_SPEC, vmin=spec_max - 80, vmax=spec_max)
        axes[1, col].set(ylabel="주파수 (kHz)")
        im2 = axes[2, col].pcolormesh(f["times"], np.arange(N_MELS), f["log_mel"],
                                      shading="auto", cmap=theme.CMAP_SPEC, vmin=mel_max - 80, vmax=mel_max)
        axes[2, col].set(ylabel="Mel 칸 번호", xlabel="시간 (초)", xlim=(0, t_max))
        for r in (1, 2):
            axes[r, col].set_facecolor(theme.NO_DATA)     # 더 짧은 녹음의 뒤쪽(데이터 없음)을 소리 없음과 구분
    fig.colorbar(im1, ax=axes[1, :], label="STFT 파워 (dB)")
    fig.colorbar(im2, ax=axes[2, :], label="Log-Mel (dB)")
    fig.suptitle(title)
    return fig


def plot_error_spans(sounds, blocks, title, sr=16000):
    """틀린 덩어리의 시간 구간을 두 소리의 파형·스펙트로그램·Log-Mel 위에 같은 번호 [k]로 표시한다.

    sounds: [(이름, 파형, 단어 목록, 구간 키)] 두 개. 단어 목록은 align이 돌려준 tts_tokens/hyp_tokens,
            구간 키는 blocks의 어느 항목을 쓸지("tts_span" 또는 "hyp_span").
    blocks: align.locate_errors가 돌려준 blocks. 구간은 Whisper가 추정한 단어 시간이라 대략의 위치다.
    """
    theme.apply_style()
    feats = [(name, x, logmel(x, sr), toks, key) for name, x, toks, key in sounds]
    spec_max = max(to_db(f["power"]).max() for _, _, f, _, _ in feats)
    mel_max = max(f["log_mel"].max() for _, _, f, _, _ in feats)
    t_max = max(len(x) for _, x, _, _, _ in feats) / sr

    # 오른쪽의 좁은 칸은 색 막대용이다. 이렇게 하면 파형 행과 그림 행의 가로 폭이 같아져 같은 시간이 같은 세로선에 놓인다.
    # [수업에 없음] gridspec_kw로 열 너비 비율을 정하는 방식.
    fig, axes = plt.subplots(3, 3, figsize=(14, 9), gridspec_kw={"width_ratios": [1, 1, 0.04]})
    axes[0, 2].axis("off")
    plots = [axes[r, c] for r in range(3) for c in range(2)]
    for ax in plots[1:]:
        ax.sharex(plots[0])
        ax.label_outer()
    plots[0].label_outer()
    for col, (name, x, f, toks, key) in enumerate(feats):
        axes[0, col].plot(np.arange(len(x)) / sr, x, lw=0.6, color=theme.WAVEFORM)
        axes[0, col].set(title=name, ylabel="진폭", ylim=(-1, 1))
        im1 = axes[1, col].pcolormesh(f["times"], f["hz"] / 1000, to_db(f["power"]),
                                      shading="auto", cmap=theme.CMAP_SPEC, vmin=spec_max - 80, vmax=spec_max)
        axes[1, col].set(ylabel="주파수 (kHz)")
        im2 = axes[2, col].pcolormesh(f["times"], np.arange(N_MELS), f["log_mel"],
                                      shading="auto", cmap=theme.CMAP_SPEC, vmin=mel_max - 80, vmax=mel_max)
        axes[2, col].set(ylabel="Mel 칸 번호", xlabel="시간 (초)", xlim=(0, t_max))
        for r in (1, 2):
            axes[r, col].set_facecolor(theme.NO_DATA)
        for n, t in enumerate(toks):   # 단어 이름표: 파형 위쪽에 단어와 시작 위치(겹치지 않게 번갈아 높이를 바꿈)
            axes[0, col].axvline(t["start"], color=theme.GRID, lw=0.8)
            axes[0, col].text((t["start"] + t["end"]) / 2, 0.97 - 0.14 * (n % 2), t["token"], ha="center", va="top",
                              fontsize=8, color=theme.INK_SECONDARY)
        for k, b in enumerate(blocks, 1):   # 틀린 덩어리: 같은 번호를 두 그림에 표시
            s, e = b[key]
            for r in range(3):
                shade = theme.INK_SECONDARY if r == 0 else "white"
                if e - s > 0.02:
                    axes[r, col].axvspan(s, e, color=shade, alpha=0.2 if r else 0.15, lw=0)
                    axes[r, col].axvline(s, color=shade, lw=1, ls="--"); axes[r, col].axvline(e, color=shade, lw=1, ls="--")
                else:   # 단어가 없는 쪽(삭제·삽입)은 한 점
                    axes[r, col].axvline(s, color=shade, lw=1.5, ls=":")
            axes[1, col].text((s + e) / 2, 7.6, f"[{k}]", ha="center", va="top", color="white", fontsize=11)
    fig.colorbar(im1, cax=axes[1, 2], label="STFT 파워 (dB)")
    fig.colorbar(im2, cax=axes[2, 2], label="Log-Mel (dB)")
    fig.suptitle(title)
    return fig
