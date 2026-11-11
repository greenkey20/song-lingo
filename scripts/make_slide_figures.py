"""발표 장표용 그림 3장을 만든다: Whisper(8장), HTDemucs(9장), 두 모델 나란히(10장). 이슈 #21, `docs/발표_대본_20261112.md`.

왜 직접 그리나: ChatGPT가 보여 준 그림(`experiments/model anatomy/*chatgpt*`, 스크린샷)은 **다른 곳의 그림**이다. Demucs 그림은 MDX 대회 논문의 **Danna-Sep(U-Net·X-UMX·Demucs를 합친 앙상블)** 이라 HTDemucs의 구조가 아니고,
Whisper 그림은 입력 예시일 뿐 구조가 아니며 출처·사용 허락도 확인하지 못했다. 그래서 **이 저장소의 노트북에서 확인한 숫자(모양·층 수·토큰 수)** 로만 다시 그렸다.

흐름
    data/tts_cache/s03.wav(직접 쓴 문장의 OpenAI TTS 소리) ─▶ Whisper와 같은 방식의 Log-Mel (80 × 3000, 30초 창에 0으로 채움) ─▶ 그림 1의 실제 입력 예시
    숫자(층·모양)는 experiments/model anatomy/*.ipynb의 [확인] 값을 그대로 옮긴다 ─▶ docs/slides/*.png (1920×1080)

실행(프로젝트 루트에서): /opt/anaconda3/envs/voice-ai/bin/python scripts/make_slide_figures.py

수업과의 관계
- [수업과 같음] Log-Mel(03·lesson04): STFT → Mel 필터 → 로그. 여기서는 **Whisper의 설정**(창 400, 이동 160, Mel 80개, 로그10, 최대−8 아래 자르기, (x+4)/4)을 쓴다 — Whisper 노트북 5절에서 라이브러리와 같음을 확인한 값.
- [수업에 없음] matplotlib으로 상자·화살표를 그리는 방식(`FancyBboxPatch`, `annotate`).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import audio  # noqa: E402
import theme  # noqa: E402

OUT = ROOT / "docs" / "slides"
W, H = 160, 90                                  # 그림 좌표(16:9)


def canvas():
    """1920×1080 캔버스와 0~160 × 0~90 좌표의 전체 축을 만든다."""
    theme.apply_style()
    fig = plt.figure(figsize=(16, 9), dpi=120)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc=theme.MINT, ec=theme.BUTTON_GREEN, size=15, color=theme.FOREST, weight="bold", lw=2.0, ls="-"):
    """둥근 상자 + 가운데 글. (x, y)는 왼쪽 아래."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=lw, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=color, fontweight=weight, linespacing=1.35)


def arrow(ax, x1, y1, x2, y2, color=theme.INK_SECONDARY, lw=2.4, style="-|>", rad=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=0, shrinkB=0, connectionstyle=f"arc3,rad={rad}"))


def title(ax, main, sub):
    ax.text(5, 84, main, fontsize=30, fontweight="bold", color=theme.FOREST, va="center")
    ax.text(5, 78.5, sub, fontsize=15.5, color=theme.INK_SECONDARY, va="center")


def footer(ax, text):
    ax.text(5, 3.2, text, fontsize=12.5, color=theme.INK_SECONDARY, va="center")


def whisper_logmel(path, seconds=3.4):
    """Whisper와 같은 설정의 Log-Mel (80, 3000)과 앞 seconds초의 파형을 돌려준다. 모자란 부분은 0으로 채운다(Whisper 노트북 5절)."""
    import librosa
    x, _, _ = audio.load_audio(str(path), 16000)
    mel = librosa.feature.melspectrogram(y=x, sr=16000, n_fft=400, hop_length=160, n_mels=80, power=2.0, center=True)[:, :-1]
    log = np.log10(np.maximum(mel, 1e-10))
    log = np.maximum(log, log.max() - 8.0)
    log = (log + 4.0) / 4.0
    pad = np.zeros((80, 3000))
    n = min(log.shape[1], 3000)
    pad[:, :n] = log[:, :n]
    return x[: int(16000 * seconds)], pad, n


# ───────────────────────── 그림 1: Whisper ─────────────────────────
def fig_whisper():
    fig, ax = canvas()
    title(ax, "Whisper: 소리 → 글", "합성곱 2개 + Transformer 인코더–디코더 · 입력은 항상 30초 창(80 × 3000) · LSTM 0개")
    wav, logmel, n = whisper_logmel(ROOT / "data/tts_cache/s03.wav")
    # ① 실제 입력 예시(직접 쓴 문장의 TTS 소리)
    # ①·② 는 같은 가로축(0~30초)을 쓴다: Whisper는 소리를 30초 창에 앞쪽부터 넣고 나머지를 0으로 채우므로, 파형도 같은 30초 축에 그려 두 그림이 맞게 한다
    sec = n / 100                                                                         # 소리가 차지한 길이(초). Log-Mel 한 칸 = 10 ms
    a1 = fig.add_axes([0.06, 0.60, 0.38, 0.12])
    t = np.arange(len(wav)) / 16000
    a1.plot(t, wav, color=theme.WAVEFORM, lw=0.6)
    a1.axvspan(sec, 30, color=theme.NO_DATA, alpha=0.9, lw=0)                             # 소리가 없는 구간(회색). 파형 자체를 채우는 것이 아니라 ②의 Log-Mel에서 0으로 채운다
    a1.text((sec + 30) / 2, 0, "소리 없음 → ②에서 0으로 채움", ha="center", va="center", fontsize=13, color=theme.INK_SECONDARY)
    a1.set_xlim(0, 30); a1.set_yticks([]); a1.set_xticks([])
    a1.set_title(f"① 입력 소리 (직접 쓴 문장의 TTS, {sec:.1f}초) — 30초 창의 앞쪽에 놓음", fontsize=13, color=theme.INK_SECONDARY, loc="left")
    a2 = fig.add_axes([0.06, 0.40, 0.38, 0.17])
    shown = np.ma.masked_where(np.tile(np.arange(3000) >= n, (80, 1)), logmel)          # 0으로 채운 부분은 회색(데이터 없음)으로 구분해서 보여 준다
    cm = theme.CMAP_SPEC.copy(); cm.set_bad(theme.NO_DATA)
    a2.imshow(shown, origin="lower", aspect="auto", cmap=cm, vmin=0, vmax=max(1.0, float(logmel.max())), extent=[0, 30, 0, 80])
    a2.text((sec + 30) / 2, 40, "0으로 채움", ha="center", va="center", fontsize=14, color=theme.INK_SECONDARY)
    a2.set_xlim(0, 30); a2.set_xticks([0, 15, 30]); a2.set_xticklabels(["0", "15초", "30초"], fontsize=11); a2.set_yticks([0, 80]); a2.set_yticklabels(["Mel 1", "Mel 80"], fontsize=10)
    a2.set_title("② Log-Mel (80 × 3000) — ①과 같은 가로축(시간)", fontsize=13, color=theme.INK_SECONDARY, loc="left")
    # 흐름
    y = 10
    ax.text(5, 28.5, "③ 계산 흐름", fontsize=16, fontweight="bold", color=theme.FOREST)
    box(ax, 4, y, 19, 14, "Log-Mel\n80 × 3000", fc="#ffffff", ec=theme.INK_SECONDARY, size=14)
    box(ax, 28, y, 21, 14, "합성곱 2개\n시간 3000 → 1500", fc="#ffffff", ec=theme.INK_SECONDARY, size=14)
    box(ax, 54, y, 30, 14, "Transformer 인코더\n(셀프 어텐션) 위치 1500개\ntiny 4층 … medium 24층", size=14)
    box(ax, 99, y, 31, 14, "Transformer 디코더\n이전 토큰 + 인코더 출력\n1500개를 보고 다음 토큰 선택", size=14, fc="#efe9ff", ec=theme.PURPLE, color=theme.PURPLE)
    box(ax, 140, y, 17, 14, "글\n(토큰)", fc="#ffffff", ec=theme.INK_SECONDARY, size=15)
    for x1, x2 in ((23, 28), (49, 54), (130, 140)):
        arrow(ax, x1 + 0.3, y + 7, x2 - 0.3, y + 7)
    arrow(ax, 84.3, y + 7, 99, y + 7, color=theme.BUTTON_GREEN)
    ax.text(91.5, y + 11.5, "교차\n어텐션", fontsize=12, ha="center", color=theme.BUTTON_GREEN, fontweight="bold")
    ax.annotate("", xy=(108, y + 14.5), xytext=(121, y + 14.5), arrowprops=dict(arrowstyle="-|>", color=theme.PURPLE, lw=2.2, connectionstyle="arc3,rad=0.9"))
    ax.text(114.5, y + 21.5, "한 토큰씩 붙여 다시 계산 (자기회귀)", fontsize=12.5, ha="center", color=theme.PURPLE, fontweight="bold")
    # 오른쪽 메모
    ax.add_patch(FancyBboxPatch((92, 40), 66, 36, boxstyle="round,pad=0.3,rounding_size=1.2", fc="#ffffff", ec=theme.GRID, lw=1.5))
    ax.text(95, 72.5, "확인한 것  [model.bin을 직접 읽음]", fontsize=14, fontweight="bold", color=theme.BUTTON_GREEN, va="center")
    ax.text(95, 57.5, "· 층 수 4 → 6 → 12 → 24, 차원 384 → 1024\n· LSTM·GRU 변수 0개 (Transformer만, 입력 앞 합성곱 2개)\n"
                    "· tiny는 파라미터의 절반 이상이 '단어 사전'\n· 입력은 항상 (80, 3000) — 짧아도 줄지 않음\n  (전체 시간은 생성 토큰 수에도 좌우됨)",
            fontsize=12.5, color=theme.INK, va="center", linespacing=1.5)
    ax.text(95, 43.5, "못 본 것: 가중치 값, 어텐션 패턴", fontsize=12.5, color=theme.PURPLE, va="center", fontweight="bold")
    footer(ax, "근거: experiments/model anatomy/whisper_anatomy_claude_code.ipynb (4·5·9절) · 소리 예시는 직접 쓴 문장의 OpenAI TTS · 개념도이며 실제 내부 층은 더 복잡")
    return fig


# ───────────────────────── 그림 2: HTDemucs ─────────────────────────
def fig_demucs():
    fig, ax = canvas()
    title(ax, "HTDemucs: 섞인 소리 하나 → 소리 4개", "같은 소리를 파형·스펙트로그램 두 경로로 보고 → CNN 압축 → Transformer 결합 → 디코더 복원 (7.8초 조각)")
    # 입력
    box(ax, 3, 42, 17, 13, "섞인 소리\n(2, 343,980)\n스테레오 × 7.8초", fc="#ffffff", ec=theme.INK_SECONDARY, size=13)
    ytop, ybot = 58, 24
    ax.text(24, ytop + 13.5, "파형 경로   CNN 4층 (stride 4)", fontsize=13.5, fontweight="bold", color=theme.WAVEFORM)
    ax.text(24, ybot + 13.5, "스펙트로그램 경로   STFT → CNN 4층 (주파수만 1/4씩)", fontsize=13.5, fontweight="bold", color=theme.BUTTON_GREEN)
    wave = ["(48, 85,995)", "(96, 21,499)", "(192, 5,375)", "(384, 1,344)"]
    spec = ["(48, 512, 336)", "(96, 128, 336)", "(192, 32, 336)", "(384, 8, 336)"]
    xs = [24, 38, 52, 66]
    for xx, a_, b_ in zip(xs, wave, spec):
        box(ax, xx, ytop, 11.6, 11, a_.replace(", ", ",\n"), fc="#eaf2fa", ec=theme.WAVEFORM, color=theme.WAVEFORM, size=11.5)
        box(ax, xx, ybot, 11.6, 11, b_.replace(", ", ",\n", 1), size=11.5)
    ax.text(24, ytop - 2.2, "채널 2 → 48 → 96 → 192 → 384, 길이 343,980 → 1,344", fontsize=11, color=theme.INK_SECONDARY)
    ax.text(24, ybot - 2.2, "입력 (4, 2048, 336): 복소수를 실수 2채널로 풀어 4채널", fontsize=11, color=theme.INK_SECONDARY)
    arrow(ax, 20.3, 50, 24, ytop + 5); arrow(ax, 20.3, 47, 24, ybot + 5)
    for i in range(3):
        arrow(ax, xs[i] + 11.9, ytop + 5.5, xs[i + 1] - 0.3, ytop + 5.5, color=theme.WAVEFORM, lw=2.0)
        arrow(ax, xs[i] + 11.9, ybot + 5.5, xs[i + 1] - 0.3, ybot + 5.5, lw=2.0)
    # 가운데 Transformer
    box(ax, 84, 33, 24, 28, "Transformer 5층\n셀프 → 교차 → 셀프\n→ 교차 → 셀프\n\n토큰 1,344 ↔ 2,688\n(서로 다른 길이도 OK)", fc="#efe9ff", ec=theme.PURPLE, color=theme.PURPLE, size=13)
    arrow(ax, 78, ytop + 5.5, 84, 52, color=theme.WAVEFORM); arrow(ax, 78, ybot + 5.5, 84, 42)
    # 디코더
    box(ax, 114, 47, 26, 14, "디코더 4층 (파형)\n인코더 출력을 더하기(＋)로 합침", size=11.5)
    box(ax, 114, 33, 26, 12, "디코더 4층 (스펙트로그램)\n역 STFT로 파형 복원", size=11.5)
    arrow(ax, 108.3, 52, 114, 54); arrow(ax, 108.3, 42, 114, 39)
    box(ax, 144, 36, 14, 22, "소리 4개\n(4, 2, 343,980)\n\n드럼\n베이스\n그 밖의 반주\n보컬", fc="#ffffff", ec=theme.INK_SECONDARY, size=11.5)
    arrow(ax, 140.3, 54, 144, 50); arrow(ax, 140.3, 39, 144, 43)
    # 하단 메모
    ax.add_patch(FancyBboxPatch((3, 6), 154, 11.5, boxstyle="round,pad=0.3,rounding_size=1.2", fc="#ffffff", ec=theme.GRID, lw=1.5))
    ax.text(5, 14.3, "기억할 네 문장:  ① 두 표현(파형·스펙트로그램)  ② CNN이 경로마다 압축해 특징 벡터 생성  ③ Transformer가 경로 안과 경로 사이 정보 결합  ④ 디코더가 소리로 복원",
            fontsize=12.5, color=theme.FOREST, fontweight="bold", va="center")
    ax.text(5, 9.3, "파라미터 4,198만 개 중 75%가 Transformer — 학습되는 숫자의 '개수 비중'이며 연산량·성능 기여도가 아님  ·  nn.LSTM 0개  ·  못 본 것: 어텐션 가중치, 각 경로가 배운 것",
            fontsize=11.5, color=theme.PURPLE, va="center")
    footer(ax, "근거: experiments/model anatomy/demucs/demucs_structure_analysis_…ipynb (4·7·8절, 실행해 기록한 값) · 사전학습 모델의 추론과 구조 분석이며 직접 학습한 것이 아님 · 개념도")
    return fig


# ───────────────────────── 그림 3: 두 모델 나란히 ─────────────────────────
def fig_compare():
    fig, ax = canvas()
    title(ax, "두 모델, 다른 문제", "둘 다 CNN과 Transformer를 쓰지만, 출력이 다르면 놓는 자리가 달라진다")
    cols = [(6, "Whisper", "소리 → 글 (음성 인식)", theme.BUTTON_GREEN, "#e8f6ec"), (86, "HTDemucs", "섞인 소리 → 소리 4개 (음원 분리)", theme.PURPLE, "#efe9ff")]
    rows = {
        "Whisper": ["오디오 (30초 창)", "Log-Mel  80 × 3000", "입력 앞 합성곱 2개 → Transformer 인코더", "Transformer 디코더 (토큰 하나씩)", "텍스트 토큰 (글)"],
        "HTDemucs": ["섞인 오디오 (7.8초 조각)", "파형  +  STFT 스펙트로그램", "CNN 인코더 2경로 → 가운데 Transformer 5층", "CNN 디코더 2경로 (인코더 출력을 더함)", "오디오 소리 4개 (파형)"],
    }
    labels = ["입력", "표현", "인코딩", "복원·생성", "출력"]
    for x, name, sub, ec, fc in cols:
        ax.text(x + 34, 70, name, fontsize=26, fontweight="bold", color=ec, ha="center")
        ax.text(x + 34, 65, sub, fontsize=14, color=theme.INK_SECONDARY, ha="center")
        for k, text in enumerate(rows[name]):
            yy = 55 - k * 9.6
            box(ax, x, yy, 68, 6.8, text, fc=fc, ec=ec, color=theme.FOREST, size=14)
            if k < 4:
                arrow(ax, x + 34, yy - 0.2, x + 34, yy - 2.5, color=ec, lw=2.2)
    for k, lab in enumerate(labels):
        ax.text(80, 58.4 - k * 9.6, lab, fontsize=12, color=theme.INK_SECONDARY, ha="center", va="center", fontweight="bold")
    ax.add_patch(FancyBboxPatch((6, 3.5), 148, 8.5, boxstyle="round,pad=0.3,rounding_size=1.2", fc="#ffffff", ec=theme.GRID, lw=1.5))
    ax.text(80, 9.3, "공통점: 둘 다 CNN과 어텐션을 쓴다 — 다만 쓰는 자리가 다르다 (Whisper: Transformer 인코더·디코더, HTDemucs: CNN 인코더·디코더 + 가운데 Transformer)", fontsize=13, ha="center", color=theme.FOREST, fontweight="bold")
    ax.text(80, 5.6, "차이점: Transformer 디코더가 글을 한 토큰씩 생성 ↔ CNN 디코더가 소리를 복원 (HTDemucs에는 Transformer 디코더가 없음) · 개념 비교용 그림", fontsize=12, ha="center", color=theme.INK_SECONDARY)
    return fig


def fig_overview():
    """장표 3: 프로그램 전체 구조(사용자의 손그림 `drafts/slide_3_프로그램 전체 구조 도식화*.jpeg`을 옮긴 것).

    입력(텍스트 또는 원곡 소리) → **언어 확인(한 상자가 두 입력 앞에 걸침)** → OpenAI(TTS·한국어 뜻 설명)·STT·보컬 추출 → 사용자 청취·확인 → 따라읽기/받아쓰기 → 평가 → 학습 기록.
    상자 색: 진한 초록 = AI 모델·외부 서비스, 연한 초록 = 데이터·결과, 흰색 = 사용자가 하는 일. 점선 = 정답 문장이 오는 길.
    언어 확인: 텍스트는 문자 체계로, 소리는 Whisper 언어 감지(앞 30초)로 제안하고 사용자가 확인한다(app/views/lyrics.py·song.py).
    """
    fig, ax = canvas()
    ax.text(5, 84, "프로그램 전체 구조: 듣고, 따라읽거나 받아쓰고, 확인한다", fontsize=30, fontweight="bold", color=theme.FOREST, va="center")
    M = dict(fc=theme.BUTTON_GREEN, ec=theme.BUTTON_GREEN, color="white")          # AI 모델·외부 서비스
    U = dict(fc="white", ec=theme.BUTTON_GREEN, color=theme.FOREST)                # 사용자가 하는 일
    S = 13.5
    # ── 입력 ──
    ax.text(2, 67, "외국어\n노래 문장", fontsize=15, fontweight="bold", color=theme.FOREST, va="center", linespacing=1.4)
    ax.text(13.8, 66.5, "{", fontsize=84, color=theme.INK_SECONDARY, va="center", ha="center")
    box(ax, 18, 70.75, 16, 5, "텍스트", size=S)
    box(ax, 18, 58.5, 16, 5, "소리 (원곡)", size=S)
    # ── 언어 확인: 두 입력 앞에 걸친 상자 하나 ──
    box(ax, 41, 59, 17, 17.5, "언어 확인\n\nen · ja · fr\nes · zh 등\n총 11개", size=12.5, **U)
    arrow(ax, 34.6, 73.25, 40.6, 73.25)                                # 텍스트 → 언어 확인
    arrow(ax, 34.6, 61, 40.6, 61)                                      # 소리 → 언어 확인
    box(ax, 62, 58.5, 16, 5, "STT (Whisper)", size=S, **M)
    # ── OpenAI: 1열 2행 (위 TTS, 아래 한국어 뜻 설명) ──
    ax.add_patch(FancyBboxPatch((84, 60), 42, 17, boxstyle="round,pad=0.3,rounding_size=1.2", fc=theme.MINT, ec=theme.BUTTON_GREEN, lw=2.5))
    box(ax, 85.5, 70.5, 39, 5.5, "TTS (OpenAI)", size=S, **M)
    box(ax, 85.5, 61, 39, 7, "한국어 뜻, 관련 표현 등\n설명 (OpenAI)", size=12.5, **M)
    box(ax, 130, 70.75, 24, 5, "기준 음성 생성", size=S)
    arrow(ax, 58.6, 73.25, 83.6, 73.25)                                # 언어 확인 → OpenAI(텍스트)
    arrow(ax, 58.6, 61, 61.6, 61)                                      # 언어 확인 → STT(소리)
    arrow(ax, 78.6, 61.4, 83.6, 64.5, rad=-0.1)                        # STT → OpenAI(인식한 가사)
    arrow(ax, 126.6, 73.25, 129.6, 73.25)                              # TTS → 기준 음성
    # ── 보컬 추출 ──
    box(ax, 100, 45, 16, 5, "Demucs", size=S, **M)
    box(ax, 122, 45, 20, 5, "보컬 추출", size=S)
    arrow(ax, 26, 58.2, 99.6, 47.8, rad=0.1)                           # 소리 → Demucs
    arrow(ax, 116.6, 47.5, 121.6, 47.5)
    # ── 사용자 청취·확인 (들어오는 화살표 4개) ──
    box(ax, 70, 33, 34, 5, "사용자 청취·확인", size=S + 1, **U)
    arrow(ax, 22, 58.2, 69.6, 35.5, rad=0.3)                           # 원곡 → 청취
    arrow(ax, 92, 60.7, 92, 38.4)                                      # 설명 → 청취
    arrow(ax, 128, 44.6, 100, 38.6, rad=0.15)                          # 보컬 → 청취
    ax.plot([147, 147], [70.4, 35.5], color=theme.INK_SECONDARY, lw=2.4, solid_capstyle="butt")    # 기준 음성 → 청취(오른쪽 끝을 돌아 내려옴)
    arrow(ax, 147, 35.5, 104.6, 35.5)
    # ── 따라읽기 / 받아쓰기 ──
    box(ax, 14, 24, 22, 5, "따라읽기", size=S, **U)
    box(ax, 110, 24, 22, 5, "받아쓰기", size=S, **U)
    arrow(ax, 74, 32.6, 30, 29.6, rad=-0.15)
    arrow(ax, 100, 32.6, 118, 29.6, rad=0.15)
    box(ax, 6, 14, 12, 5, "녹음", size=S, **U)
    box(ax, 24, 13, 30, 7, "STT (Whisper)\n텍스트 생성", size=12.5, **M)
    box(ax, 112, 14, 22, 5, "텍스트 입력", size=S, **U)
    arrow(ax, 20, 23.8, 13, 19.4)
    arrow(ax, 18.6, 16.5, 23.6, 16.5)
    arrow(ax, 123, 23.8, 123, 19.4)
    # ── 평가와 기록 ──
    box(ax, 62, 14, 44, 5, "정답 문장 대비 오류율 평가", size=S)
    box(ax, 6, 2, 48, 7, "파형(틀린 구간 표시)·주파수(F0) 분석,\nAzure 발음 평가", size=12, **M)
    box(ax, 112, 2.5, 34, 6.5, "학습 기록\n(로그인 사용자)", size=12.5, fc=theme.LIME, ec=theme.BUTTON_GREEN, color=theme.FOREST)
    arrow(ax, 54.6, 16.5, 61.6, 16.5)                                  # STT 텍스트 → 오류율
    arrow(ax, 111.6, 16.5, 106.6, 16.5)                                # 텍스트 입력 → 오류율
    arrow(ax, 12, 13.6, 12, 9.4)                                       # 녹음 → 파형·Azure
    arrow(ax, 54.6, 5.5, 111.6, 5.7)                                   # 분석 → 기록
    arrow(ax, 96, 13.6, 122, 9.4, rad=-0.1)                            # 오류율 → 기록
    # ── 점선: 정답 문장이 오는 길(텍스트, 그리고 원곡을 인식한 STT) → 오류율 평가 ──
    dash = dict(color=theme.INK_SECONDARY, lw=2.0, ls=(0, (5, 4)))
    ax.plot([37.6, 37.6], [73.25, 22], **dash)                         # 텍스트에서 아래로
    ax.plot([64, 64], [58.4, 22], **dash)                              # STT에서 아래로
    ax.plot([37.6, 84], [22, 22], **dash)
    ax.plot([84, 84], [22, 19.8], **dash)
    arrow(ax, 84, 20.3, 84, 19.2)
    ax.text(44, 23.6, "정답 문장", fontsize=11, color=theme.INK_SECONDARY, va="center")
    return fig


def _card(ax, x, y, w, h, fc="white", ec=None, lw=2.0):
    """둥근 모서리 카드(글은 따로 얹는다). (x, y)는 왼쪽 아래."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec or theme.BUTTON_GREEN, lw=lw))


def _code_box(ax, x, y, w, h, lines, size=12.5):
    """회색 바탕의 코드 발췌 상자. lines는 (글, 굵게) 목록이 아니라 그냥 글 목록이다. 글꼴은 한글 주석이 깨지지 않게 그림 기본 글꼴을 쓴다."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=0.8", fc="#f0efeb", ec=theme.GRID, lw=1.5))
    n = len(lines)
    for i, s in enumerate(lines):
        ax.text(x + 1.2, y + h - (i + 0.65) * (h / max(n, 1)), s, fontsize=size, color=theme.FOREST, va="center", ha="left")


def fig_dp():
    """장표 5의 보조: 편집 거리(동적 계획법)로 WER을 구하는 과정. 표는 `scoring.edit_matrix`가 만든 값 그대로이고, 되짚은 길을 색으로 표시한다.

    예시 문장은 직접 쓴 `we sing together until`(정답)과 인식 결과 `we seeing together`(바뀜 1 + 빠짐 1 → 편집 거리 2, WER 0.50).
    """
    import scoring
    ref, hyp = ["we", "sing", "together", "until"], ["we", "seeing", "together"]
    d = scoring.edit_matrix(ref, hyp)
    fig, ax = canvas()
    ax.text(5, 84, "채점의 핵심: 편집 거리를 표로 한 칸씩 채운다 (동적 계획법)", fontsize=30, fontweight="bold", color=theme.FOREST, va="center")
    ax.text(5, 78.5, "정답과 인식 결과가 얼마나 다른지를, 작은 문제의 답을 표에 적어 가며 큰 문제의 답을 구한다", fontsize=15.5, color=theme.INK_SECONDARY, va="center")
    # ── 표 (왼쪽) ──
    x0, y0, cw, ch = 17, 66, 10.5, 6.6
    ax.text(8.5, y0 + ch / 2 + 0.2, "인식 결과\n(hyp) →", fontsize=13.5, color=theme.INK_SECONDARY, ha="center", va="center")
    for j, w in enumerate([""] + hyp):
        ax.text(x0 + (j + 0.5) * cw, y0 + ch / 2 + 0.2, w if w else "∅", fontsize=14, fontweight="bold", color=theme.FOREST, ha="center", va="center")
    ax.text(4, y0 - 2 * ch + 0.5, "정답\n(ref)", fontsize=13.5, color=theme.INK_SECONDARY, ha="center", va="center")
    # 되짚기: 오른쪽 아래 → 왼쪽 위(같은 값이면 대각선을 먼저)
    i, j, path = len(ref), len(hyp), []
    while i > 0 or j > 0:
        path.append((i, j))
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1):
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            i -= 1
        else:
            j -= 1
    path.append((0, 0))
    on = set(path)
    for r in range(len(ref) + 1):
        ax.text(x0 - 1.2, y0 - (r + 0.5) * ch + 0.2, ref[r - 1] if r else "∅", fontsize=14, fontweight="bold", color=theme.FOREST, ha="right", va="center")
        for c in range(len(hyp) + 1):
            hit = (r, c) in on
            ax.add_patch(FancyBboxPatch((x0 + c * cw + 0.4, y0 - (r + 1) * ch + 0.4), cw - 0.8, ch - 0.8, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        fc=theme.MINT if hit else "white", ec=theme.BUTTON_GREEN if hit else theme.GRID, lw=2.4 if hit else 1.4))
            ax.text(x0 + (c + 0.5) * cw, y0 - (r + 0.5) * ch + 0.2, str(d[r][c]), fontsize=16, fontweight="bold" if hit else "normal",
                    color=theme.FOREST if hit else theme.INK_SECONDARY, ha="center", va="center")
    # 되짚은 길의 뜻(위에서 아래로 읽는 순서)
    ops = [("we = we", "일치", theme.BUTTON_GREEN), ("sing → seeing", "바뀜(S)", theme.PURPLE), ("together = together", "일치", theme.BUTTON_GREEN), ("until → (없음)", "빠짐(D)", theme.PURPLE)]
    ax.text(x0, y0 - 5 * ch - 3.2, "되짚은 길 (초록 칸):", fontsize=13.5, fontweight="bold", color=theme.FOREST, va="center")
    for k, (a, b, col) in enumerate(ops):
        ax.text(x0, y0 - 5 * ch - 7.2 - k * 3.6, f"{a}", fontsize=13, color=theme.INK, va="center")
        ax.text(x0 + 30, y0 - 5 * ch - 7.2 - k * 3.6, b, fontsize=13, fontweight="bold", color=col, va="center")
    # ── 오른쪽 설명 ──
    _card(ax, 74, 52, 80, 22, fc="white")
    ax.text(77, 71, "한 칸을 채우는 규칙 (점화식)", fontsize=15, fontweight="bold", color=theme.FOREST, va="center")
    for k, s in enumerate(["d[i][j] = 세 값 중 가장 작은 것", "· 위 칸 + 1   : 삭제 (정답 단어를 지움)", "· 왼쪽 칸 + 1 : 삽입 (인식에만 있는 단어)", "· 대각선 칸 + (같으면 0, 다르면 1) : 일치 · 바뀜"]):
        ax.text(77, 66.6 - k * 3.6, s, fontsize=13.5, color=theme.INK, va="center")
    _card(ax, 74, 36, 80, 13, fc=theme.MINT)
    ax.text(77, 45.6, "표의 오른쪽 아래 칸 = 최소 수정 횟수 = 2", fontsize=14.5, fontweight="bold", color=theme.FOREST, va="center")
    ax.text(77, 41.2, "WER = (바뀜 S + 빠짐 D + 더해짐 I) ÷ 정답 단어 수 N = (1 + 1 + 0) ÷ 4 = 0.50", fontsize=14, color=theme.FOREST, va="center")
    _code_box(ax, 74, 14, 80, 18.5, ["# scoring.edit_matrix 의 핵심 (내 코드)", "cost = 0 if ref[i-1] == hyp[j-1] else 1     # 같으면 0, 다르면 1",
                                      "d[i][j] = min(d[i-1][j] + 1,                  # 삭제", "              d[i][j-1] + 1,                  # 삽입",
                                      "              d[i-1][j-1] + cost)             # 일치 또는 바뀜"], size=12.3)
    ax.text(74, 9.2, "이해한 방법: 점화식 → 표를 한 칸씩 넘기는 도구(DP_편집거리_이해하기.html)", fontsize=12.5, color=theme.INK_SECONDARY, va="center")
    ax.text(74, 5.6, "동률일 때 비슷한 단어끼리 짝짓는 규칙은 이 프로젝트에서 덧붙인 부분(수업에 없음)", fontsize=12.5, color=theme.INK_SECONDARY, va="center")
    return fig


def fig_class_code():
    """장표 9의 보조: 수업(017_sound)에서 배운 것이 내 코드의 어디에 들어갔는지 — 수업 주제, 코드 발췌(한 줄 주석), 같음/응용.

    발췌는 `audio.py`·`visualisation.py`·`stt.py`에서 줄여 옮겼고 근거는 검토 문서 16.12의 대응표다.
    """
    fig, ax = canvas()
    ax.text(5, 84, "수업에서 배운 것 → 내 코드에 들어간 자리", fontsize=30, fontweight="bold", color=theme.FOREST, va="center")
    ax.text(5, 78.5, "017_sound 수업의 코드 흐름을 그대로 따르고, 실제 소리·노래에 맞게 응용한 곳만 덧붙였다", fontsize=15.5, color=theme.INK_SECONDARY, va="center")
    rows = [
        ("02 리샘플링", "audio.to_16k_mono", ["g = gcd(sr, orig_sr)                            # 44100→16000이면 (160, 441)",
                                              "x = resample_poly(x, sr // g, orig_sr // g)     # 16 kHz 모노로 맞춤"], "수업과 같음"),
        ("03·lesson04 STFT", "visualisation.stft_power", ["hz, t, spec = stft(sound, fs=sr, window=\"hann\", nperseg=512, noverlap=512-128)",
                                                          "power = abs(spec) ** 2                  # 창 512, 이동 128, 파워 = |X|²"], "수업과 같음 (인자를 한 줄씩 대조)"),
        ("lesson04 Log-Mel", "visualisation.logmel", ["mel_power, _ = apply_mel_filters(hz, power, sr, 40)   # Mel 필터 40개로 묶기",
                                                      "log_mel = to_db(mel_power)                       # 로그(dB)로 바꿈"], "수업과 같음 + 두 소리를 같은 색 범위로 비교"),
        ("07 Whisper 최소 예제", "stt.load_model", ["WhisperModel(size, device=\"cpu\", compute_type=\"int8\")   # 7강과 같은 설정",
                                                    "segments, _ = model.transcribe(audio, beam_size=1)      # 후보 하나만 탐색"], "수업과 같음 + 모델 크기·VAD·온도 옵션"),
        ("05 WAV와 정답 연결", "sentences.csv ↔ 녹음", ["sentences.csv 의 id=1  ↔  data/recordings/s01_take1.wav",
                                                       "녹음 파일 번호로 정답 문장을 찾아 인식 결과와 비교"], "같은 발상 [추정]\n(5강 manifest의 id·file·reference)"),
    ]
    y = 71
    rh = 11.6
    for k, (topic, where, code, note) in enumerate(rows):
        yy = y - k * (rh + 0.9)
        box(ax, 5, yy - rh + 1.5, 28, rh - 1.5, f"{topic}\n→ {where}", size=13, fc=theme.MINT)
        _code_box(ax, 36, yy - rh + 1.5, 83, rh - 1.5, code, size=12)
        ax.text(122, yy - rh / 2 + 0.7, note, linespacing=1.4, fontsize=12.5, color=theme.INK_SECONDARY, va="center")
    ax.text(5, 4.5, "STFT 창 512·이동 128은 수업 설정을 그대로 썼다. 앱에 덜 응용된 것: 창 길이·Mel 개수를 바꿔 보는 실험(노트북·이슈 #35에서만).", fontsize=12.5, color=theme.INK_SECONDARY, va="center")
    return fig


def fig_vad():
    """장표 8의 보조: 노래 구간 인식 실험(설정 A → B → C)에서 가설이 어떻게 바뀌었나.

    숫자는 `experiments/song vocals/노래_구간_비교_실험_절차.md`의 표(구간 c01~c08, 정답 231단어, micro WER)를 그대로 옮겼다. 가사는 없고 곡 번호와 숫자만 쓴다.
    """
    fig, ax = canvas()
    ax.text(5, 84, "노래 구간 인식 실험: 가설이 두 번 바뀌었다", fontsize=30, fontweight="bold", color=theme.FOREST, va="center")
    ax.text(5, 78.5, "VAD = 말소리 없는 구간을 지우는 전처리 · 폴백 = 인식이 나쁘면 온도를 올려 다시 인식(기본 동작) · 값은 정답 대비 단어 오류율(낮을수록 좋음)", fontsize=14, color=theme.INK_SECONDARY, va="center")
    cols = [
        (4, "① 설정 A — 폴백 끔", "tiny·base·small × VAD 끔/켬 × 원곡/보컬, 1회",
         ["반복 루프가 많아 WER이 1을 넘는 조건이 다수", "예) c05 base 보컬: 정답 32단어에 인식 222단어", "→ 당시 해석: \"분리가 VAD를 쓸 수 있게 한다\""]),
        (56, "② 설정 B — 기본 설정(폴백 켬)", "tiny·base × VAD × 소리, 3회 반복",
         ["루프가 거의 사라짐 (삽입 40개 이상 3/64 → 1/96)", "VAD 켬 + 원곡: 8구간 중 5구간이 통째로 비었음", "→ A의 해석 철회, 최고는 base + VAD 끔 + 보컬"]),
        (108, "③ 설정 C — 모델 크기 확대", "small·medium 추가, 기본 설정, VAD 끔",
         ["medium은 원곡이 보컬보다 낫고 base는 반대", "→ 결정: medium + 원곡 + VAD 끔 + 기본 설정", "분리는 학습용 기준 음성·보컬만 듣기용 선택 기능"]),
    ]
    for x, head, cond, notes in cols:
        _card(ax, x, 46, 48, 28, fc="white")
        ax.text(x + 1.8, 71, head, fontsize=15, fontweight="bold", color=theme.FOREST, va="center")
        ax.text(x + 1.8, 67.2, cond, fontsize=11.5, color=theme.INK_SECONDARY, va="center")
        for k, s in enumerate(notes):
            ax.text(x + 1.8, 62.2 - k * 4.8, s, fontsize=12.3, color=theme.INK if k < 2 else theme.PURPLE, va="center", fontweight="normal" if k < 2 else "bold")
    GREEN, BLUE, GRAY = theme.GREEN, theme.SERIES[1], theme.MUTED

    def chart(x, y, w, h, groups, series, ylim, title, annot=None, legend="upper right"):
        a = fig.add_axes([x / W, y / H, w / W, h / H])
        a.set_title(title, fontsize=12.5, color=theme.INK_SECONDARY, loc="left", pad=8)
        n = len(series)
        bw = 0.8 / n
        for s, (name, vals, col) in enumerate(series):
            xs = np.arange(len(groups)) + (s - (n - 1) / 2) * bw
            bars = a.bar(xs, vals, bw * 0.92, color=col, label=name)
            for b_, v in zip(bars, vals):
                a.text(b_.get_x() + b_.get_width() / 2, v + ylim * 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=10.5, color=theme.FOREST)
        a.set_xticks(np.arange(len(groups))); a.set_xticklabels(groups, fontsize=10.5, color=theme.FOREST)
        a.set_ylim(0, ylim); a.tick_params(axis="y", labelsize=10, colors=theme.INK_SECONDARY)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
        a.legend(fontsize=10, frameon=False, loc=legend)
        if annot:
            a.text(annot[1], annot[2], annot[0], fontsize=10.5, color=theme.PURPLE, ha="center", va="bottom", fontweight="bold")
        return a
    # ① 폴백 끔 → 켬 (VAD 끔)
    chart(6, 14, 44, 28, ["tiny\n원곡", "tiny\n보컬", "base\n원곡", "base\n보컬"],
          [("폴백 끔 (A)", [1.026, 0.983, 0.584, 1.221], GRAY), ("폴백 켬 (B)", [0.556, 0.586, 0.509, 0.382], GREEN)], 1.7, "VAD 끔, 소리·크기별 WER", legend="upper left")
    # ② VAD 끔/켬 (base, 설정 B)
    chart(58, 14, 44, 28, ["VAD 끔", "VAD 켬"], [("원곡", [0.509, 0.740], GREEN), ("보컬", [0.382, 0.499], BLUE)], 1.0, "base, 기본 설정 3회 평균 WER",
          annot=("원곡은 8구간 중\n5구간이 비어 있음", 0.8, 0.84))
    # ③ 모델 크기 (VAD 끔, 기본 설정)
    chart(110, 14, 44, 28, ["base", "medium"], [("원곡", [0.509, 0.177], GREEN), ("보컬", [0.382, 0.257], BLUE)], 0.75, "VAD 끔, 기본 설정 WER")
    ax.text(5, 4.0, "구간 c01~c08(10~20초), 정답 231단어, 영어, CPU·int8. 곡 번호와 숫자만 기록(가사 없음). 이 조건에서의 결과이고 일반화하지 않는다.", fontsize=12, color=theme.INK_SECONDARY, va="center")
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("slide_6_whisper", fig_whisper), ("slide_7_demucs", fig_demucs), ("slide_7-2_compare", fig_compare), ("slide_3_overview", fig_overview), ("slide_dp", fig_dp), ("slide_class_code", fig_class_code), ("slide_vad_experiment", fig_vad)):
        fig = fn()
        path = OUT / f"{name}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        print("저장:", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
