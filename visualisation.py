"""소리를 '시간-주파수 그림'용 숫자로 바꾸는 함수 모음: STFT 파워, Mel 필터, Log-Mel(이슈 #23).

원래 practice.ipynb 셀 안에 있던 수업 코드를 그대로 옮겼다(동작 변경 없음). 모듈로 빼 둔 이유는 두 가지다.
- quality.py(녹음 상태 점검)가 '프레임별 에너지'를 계산할 때 같은 STFT를 재사용한다.
- 노트북 밖에서 단위 테스트를 할 수 있다.

수업과의 관계
- [수업과 같음] STFT 설정(창 512, 이동 128, hann), 삼각형 Mel 필터 40개, 파워를 dB로 바꾸는 순서.
  출처: 017_sound/03_FFT_STFT_그림으로_소리읽기.ipynb(`compute_stft`), lesson04 실습 2-F(Mel 필터), 3-B(logmel).
- [수업과 같음] **전체 FFT**: `np.fft.rfft`(실수 신호의 FFT) → `np.abs(...)`(복소수의 크기) → `np.fft.rfftfreq(길이, d=1/sr)`(칸마다 Hz)로 주파수별 크기를 구한다.
  출처: 03 실습1~3, lesson04 실습 1-B(한 구간에 `np.hanning` 창을 곱한 뒤 rfft). `fft_spectrum`이 이 순서를 그대로 따른다.
- [수업과 같음] 그림 그리기: `plt.subplots`, `pcolormesh(shading="auto")`로 시간×주파수(또는 Mel 칸)를 색으로, `colorbar`로 색의 뜻을 표시, `axvspan`으로 구간 표시(02 실습7).
- [수업에 없음] `stft_power` 함수로 한 번 감싼 것(logmel과 quality.py가 함께 쓰려는 용도)과 to_db 함수화.
- [수업에 없음] 두 소리를 **같은 색 범위(가장 센 값 기준 80 dB 아래까지)** 로 맞춰 밝기를 비교하는 것. 수업은 그림마다 자동 범위나 `Greens`를 썼다.
  색 지도는 수업의 `Greens`·`magma` 대신 프로젝트 팔레트(theme.CMAP_SPEC, 검토 문서 14.4)를 쓴다.

이 모듈에는 '그릴 숫자'를 계산하는 함수(stft_power, logmel …)와 그림을 그리는 함수(plot_sound_pair,
plot_error_spans, plot_sound_panels)가 함께 있다. 그림 함수는 파형과 단어별 시간을 인자로 받아 figure를 돌려줄 뿐,
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


def fft_spectrum(sound, sr, use_window=True):
    """소리 전체의 **FFT 크기 스펙트럼**을 돌려준다: (주파수 hz 배열, 크기 배열). 시간 정보는 없고 "어떤 주파수가 얼마나 들어 있나"만 보여 준다.

    수업과 같은 순서(03 실습1~3, lesson04 실습 1-B):
      1. `np.hanning(길이)`를 곱한다(use_window=True, lesson04). 창 함수는 소리의 양 끝을 0으로 부드럽게 줄여, 끝이 갑자기 잘린 것처럼 보여서 생기는
         가짜 주파수 성분(누설)을 줄인다. 03은 창을 곱하지 않았다(use_window=False로 같은 결과).
      2. `np.fft.rfft(x)`: 실수 소리를 주파수 성분의 **복소수** 배열로 바꾼다. 실수 신호는 음의 주파수가 중복이라 절반(길이//2+1칸)만 돌려준다.
      3. `np.abs(...) / 길이`: 복소수의 **크기**(위상은 버림)를 샘플 수로 나눠, 길이가 다른 소리끼리도 크기를 비교할 수 있게 보정한다(03 셀 9).
      4. `np.fft.rfftfreq(길이, d=1/sr)`: 각 칸이 몇 Hz인지. 간격은 sr/길이 Hz이고 마지막 칸은 sr/2(나이퀴스트 주파수)다.
    [수업에 없음] 말소리 전체를 한 번에 FFT하는 것은 시간에 따른 변화를 모두 평균내므로, "어느 순간에 어떤 소리가 났나"는 STFT가 보여 준다."""
    x = np.asarray(sound, dtype=np.float64)
    if x.ndim != 1 or x.size < 2:
        raise ValueError("모노 파형(샘플 2개 이상)이 필요합니다.")
    if use_window:
        x = x * np.hanning(len(x))                          # lesson04 실습 1-B
    hz = np.fft.rfftfreq(len(x), d=1 / sr)                  # 칸마다 주파수(Hz)
    amplitude = np.abs(np.fft.rfft(x)) / len(x)             # 칸마다 크기(복소수의 절댓값 ÷ 샘플 수)
    return hz, amplitude


def plot_sound_panels(sounds, sr=16000):
    """소리 두 개(표준 발음과 내 녹음)를 **칸마다 따로** 그려 {"wave", "fft", "stft", "logmel"} Figure 4개를 돌려준다(웹 화면의 2×2 칸용).

    sounds: [(이름, 16 kHz 모노 파형)] 2개. 비교를 위해 최대 진폭을 맞춘 파형을 넣는다(web_practice.normalized_sounds).
    칸마다 수업의 어느 부분과 이어지는지 (출처는 017_sound):
    - wave  [수업과 같음, 01·02]: 시간(초)에 따른 진폭. 두 소리의 시간축(긴 쪽 기준)과 세로 범위(-1~1)를 같게 해 소리 크기와 타이밍을 비교한다.
    - fft   [수업과 같음, 03 실습1~3·lesson04 1-B]: **소리 전체**의 주파수별 크기(`fft_spectrum`). 두 소리를 한 그림에 겹쳐(초록·보라, theme.SERIES 규칙) 낮은 주파수
            (목소리 높이와 배음)가 어디에 몰려 있는지 본다. 시간 정보는 없다. 가장 큰 봉우리(50 Hz 이상, 03 실습3의 argmax)를 이름 옆에 적는다.
    - stft  [수업과 같음, 03·lesson04 1교시]: 창 512·이동 128·hann으로 한 프레임씩 FFT한 파워(dB). "어떤 주파수가 **언제** 나타났나". 밝을수록 센 소리.
    - logmel [수업과 같음, lesson04 2·3교시]: STFT 파워를 삼각형 Mel 필터 40개로 묶고 로그(dB). 사람 귀가 낮은 소리 차이에 더 민감한 점을 반영한 눈금이라 음성 인식 모델 입력으로 쓴다.
    [수업에 없음] stft·logmel은 두 소리를 **같은 색 범위**(가장 센 값 기준 80 dB 아래까지)로 그려 밝기를 비교할 수 있게 한다. 짧은 쪽의 뒤는 '데이터 없음' 색.
    그림은 소리의 모양을 보는 **참고용**이고 점수가 아니다(목소리·마이크·방이 달라도 모양이 달라진다)."""
    for name, x in sounds:
        if len(x) < FRAME_LENGTH:      # 수업 compute_stft와 같은 검사(1 ≤ 이동 ≤ 창 ≤ 샘플 수): 창 하나(32 ms)를 못 채우면 STFT를 만들 수 없다
            raise ValueError(f"'{name}'이 너무 짧아요({len(x) / sr * 1000:.0f} ms). 32 ms 이상이어야 그릴 수 있어요.")
    theme.apply_style()
    feats = [(name, x, logmel(x, sr)) for name, x in sounds]
    t_max = max(len(x) for _, x, _ in feats) / sr
    n = len(feats)
    figs = {}

    fig, axes = plt.subplots(1, n, figsize=(6.5, 2.4), sharey=True, squeeze=False)
    for ax, (name, x, _) in zip(axes[0], feats):
        ax.plot(np.arange(len(x)) / sr, x, lw=0.6, color=theme.WAVEFORM)
        ax.set(title=name, xlabel="시간 (초)", xlim=(0, t_max), ylim=(-1, 1))
    axes[0, 0].set_ylabel("진폭")
    fig.tight_layout()
    figs["wave"] = fig

    fig, ax = plt.subplots(figsize=(6.5, 2.4))
    for (name, x, _), color in zip(feats, (theme.SERIES[0], theme.PURPLE)):
        hz, amp = fft_spectrum(x, sr)
        keep = hz >= 50                                          # 50 Hz 미만(직류·진동 잡음)은 봉우리 후보에서 뺀다
        peak = hz[keep][int(np.argmax(amp[keep]))]               # 03 실습3: argmax로 가장 큰 칸 → 그 칸의 Hz
        ax.plot(hz / 1000, amp, lw=1.0, color=color, label=f"{name} (가장 큰 봉우리 {peak:.0f} Hz)")
    ax.set(xlabel="주파수 (kHz)", ylabel="FFT 크기 / 샘플 수", xlim=(0, 4))     # 말소리의 대부분은 4 kHz 아래
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    figs["fft"] = fig

    for key, label, value in (("stft", "STFT 파워 (dB)", lambda f: to_db(f["power"])), ("logmel", "Log-Mel (dB)", lambda f: f["log_mel"])):
        vmax = max(value(f).max() for _, _, f in feats)
        fig, axes = plt.subplots(1, n, figsize=(6.5, 2.6), sharey=True, squeeze=False)
        for ax, (name, x, f) in zip(axes[0], feats):
            y = f["hz"] / 1000 if key == "stft" else np.arange(N_MELS)
            im = ax.pcolormesh(f["times"], y, value(f), shading="auto", cmap=theme.CMAP_SPEC, vmin=vmax - 80, vmax=vmax)
            ax.set(title=name, xlabel="시간 (초)", xlim=(0, t_max))
            ax.set_facecolor(theme.NO_DATA)
        axes[0, 0].set_ylabel("주파수 (kHz)" if key == "stft" else "Mel 칸 번호")
        fig.colorbar(im, ax=axes[0, :], label=label)
        figs[key] = fig
    return figs


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


def plot_f0_contour(analysis, title="목소리 높낮이 변화 (F0)"):
    """pitch.analyze_f0의 결과(status "ok")로 **시간에 따른 F0 윤곽** Figure를 만든다(실제 시간축, 단위 Hz).

    무성음·무음 프레임은 NaN이라 선이 끊긴다(0 Hz로 이어 그리지 않는다). 유성음 프레임이 하나만 홀로 있으면 선이 안 보이므로 작은 점도 찍는다.
    가운데 점선은 중앙 F0, 연한 띠는 P10~P90(주로 나타난 범위). 이 그림은 음높이 변화를 **관찰**하는 참고용이고 점수가 아니다.
    [수업과 같음] 시간에 따른 값을 선으로 그리는 matplotlib 사용(02 파형). [수업에 없음] NaN에서 선이 끊기는 성질을 이용한 표시, axhspan으로 범위 띠."""
    if analysis.get("status") != "ok":
        raise ValueError("F0 분석 결과가 없어 그림을 그릴 수 없습니다.")
    theme.apply_style()
    t, f0 = np.asarray(analysis["times"]), np.asarray(analysis["f0"], dtype=float)
    y = np.where(np.asarray(analysis["valid"], dtype=bool), f0, np.nan)
    fig, ax = plt.subplots(figsize=(9, 3.4), layout="constrained")     # constrained: 가로축 이름이 잘리지 않게 여백을 자동으로 잡는다
    ax.axhspan(analysis["p10_hz"], analysis["p90_hz"], color=theme.GREEN, alpha=0.12, lw=0,
               label=f"주로 나타난 범위 {analysis['p10_hz']:.0f}–{analysis['p90_hz']:.0f} Hz")
    ax.axhline(analysis["median_hz"], color=theme.INK_SECONDARY, lw=1, ls="--", label=f"중앙 {analysis['median_hz']:.0f} Hz")
    ax.plot(t, y, color=theme.GREEN, lw=1.8, marker="o", ms=2.5)
    lo, hi = np.nanmin(y), np.nanmax(y)
    pad = max((hi - lo) * 0.15, 10.0)
    ax.set(title=title, xlabel="시간 (초)", ylabel="F0 (Hz)", xlim=(0, max(float(t[-1]), analysis.get("duration") or 0)),
           ylim=(max(lo - pad, 0), hi + pad))
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    return fig


def plot_f0_compare(curves, words, title="억양 흐름 비교 (상대 음높이)"):
    """참고 TTS와 내 녹음의 **상대 음높이**(각자의 중앙 F0를 0으로 한 semitone)를 **단어축** 위에 한 그래프로 겹쳐 그린다(검토 문서 16.18).

    curves: [{"name", "x", "y", "color"}] (보통 [참고 TTS, 내 녹음]). x·y는 pitch.to_word_axis의 결과(NaN에서 선이 끊김).
    words: 기준 문장의 단어 칸 목록 [{"token", "mismatch"}]. 칸 i는 x축의 i~i+1이고, mismatch가 참이면(내 녹음에서 다르게 인식되거나 빠진 단어) 연한 보라 띠로 칠한다
    (보라는 이 앱에서 '틀린 단어' 표시색이다, theme.PURPLE). 단어 이름표는 정규화한 토큰(we're → we are, twenty → 20)이다.
    y축은 Hz가 아니라 semitone이라 목소리 높이가 달라도 **올라가고 내려가는 모양**만 비교한다. TTS의 억양은 비교 기준이지 정답이 아니다.
    [수업에 없음] axvspan으로 단어 칸 띠, set_xticks로 단어 이름표(수업 02 실습7의 axvspan을 구간 표시에 응용)."""
    if not words:
        raise ValueError("비교할 단어가 없습니다.")
    theme.apply_style()
    fig, ax = plt.subplots(figsize=(9, 3.8), layout="constrained")
    for i, w in enumerate(words):
        if w.get("mismatch"):
            ax.axvspan(i, i + 1, color=theme.PURPLE, alpha=0.13, lw=0)
        elif i % 2 == 0:
            ax.axvspan(i, i + 1, color=theme.NO_DATA, alpha=0.5, lw=0)
        if i:
            ax.axvline(i, color=theme.GRID, lw=0.8)
    ax.axhline(0, color=theme.INK_SECONDARY, lw=1, ls="--", label="각자의 중앙 음높이 (0)")
    ys = []
    for c in curves:
        if len(c["x"]):
            ax.plot(c["x"], c["y"], color=c["color"], lw=2.2, marker="o", ms=2.5, label=c["name"])
            ys.append(np.asarray(c["y"], dtype=float))
    finite = np.concatenate(ys) if ys else np.array([])
    finite = finite[np.isfinite(finite)]
    span = max(float(np.abs(finite).max()) if len(finite) else 0.0, 3.0) * 1.15
    ax.set(title=title, ylabel="상대 음높이 (semitone)", xlim=(0, len(words)), ylim=(-span, span),
           xlabel="기준 문장의 단어 (단어마다 같은 폭으로 맞춤)")
    ax.set_xticks([i + 0.5 for i in range(len(words))], [w["token"] for w in words])
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="upper right", fontsize=8, frameon=False, ncols=3)
    return fig


def plot_song_selection(mins, maxs, seconds, start, duration):
    """곡 전체 파형 윤곽(web_song.waveform_peaks의 mins·maxs) 위에 고른 구간 [start, start+duration]을 띠로 표시한 Figure를 돌려준다.

    가로축은 초. 선택 구간은 라임색 띠(theme.LIME)와 양 끝 선으로 나타낸다(앱의 "내 노래" 화면, 검토 문서 16.10)."""
    theme.apply_style()
    n = len(mins)
    t = np.linspace(0, seconds, n)
    fig, ax = plt.subplots(figsize=(9, 2.2))
    ax.fill_between(t, mins, maxs, color=theme.GREEN, alpha=0.45, linewidth=0)
    end = min(seconds, start + duration)
    ax.axvspan(start, end, color=theme.LIME, alpha=0.55, zorder=0)
    ax.axvline(start, color=theme.BUTTON_GREEN, linewidth=1.5)
    ax.axvline(end, color=theme.BUTTON_GREEN, linewidth=1.5)
    ax.set_xlim(0, seconds)
    # 세로축은 소리의 세기(진폭)다: 두 채널을 평균한 모노 파형의 칸별 최솟값~최댓값(수업 01·02의 파형과 같은 축). 눈금과 이름표는 그리지 않는다:
    # 왼쪽 눈금이 그림을 오른쪽으로 밀어 아래의 시작 위치 슬라이더와 시간축이 어긋나기 때문이다(사용자 피드백, 11-06). 위치는 가로축(초)만 읽으면 된다.
    ax.set_yticks([])
    ax.set_xlabel("시간 (초)")
    for side in ("left", "top", "right"):
        ax.spines[side].set_visible(False)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.28, top=0.97)
    return fig
