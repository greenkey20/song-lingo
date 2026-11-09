"""발표 장표용 그림 3장을 만든다: Whisper(6장), HTDemucs(7장), 두 모델 나란히(7-2장). 이슈 #21, `docs/발표_대본_20261112.md`.

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
    a1 = fig.add_axes([0.06, 0.60, 0.38, 0.12])
    t = np.arange(len(wav)) / 16000
    a1.plot(t, wav, color=theme.WAVEFORM, lw=0.6); a1.set_xlim(0, t[-1]); a1.set_yticks([]); a1.set_xticks([])
    a1.set_title("① 입력 소리 (직접 쓴 문장의 TTS 예시)", fontsize=13, color=theme.INK_SECONDARY, loc="left")
    a2 = fig.add_axes([0.06, 0.40, 0.38, 0.17])
    shown = np.ma.masked_where(np.tile(np.arange(3000) >= n, (80, 1)), logmel)          # 0으로 채운 부분은 회색(데이터 없음)으로 구분해서 보여 준다
    cm = theme.CMAP_SPEC.copy(); cm.set_bad(theme.NO_DATA)
    a2.imshow(shown, origin="lower", aspect="auto", cmap=cm, vmin=0, vmax=max(1.0, float(logmel.max())))
    a2.text((n + 3000) / 2, 40, "0으로 채움", ha="center", va="center", fontsize=14, color=theme.INK_SECONDARY)
    a2.set_xticks([0, 1500, 3000]); a2.set_xticklabels(["0", "15초", "30초"], fontsize=11); a2.set_yticks([0, 79]); a2.set_yticklabels(["Mel 1", "Mel 80"], fontsize=10)
    a2.set_title("② Log-Mel (80 × 3000)  — 소리는 앞쪽, 나머지는 0으로 채움", fontsize=13, color=theme.INK_SECONDARY, loc="left")
    # 흐름
    y = 10
    ax.text(5, 28.5, "③ 계산 흐름", fontsize=16, fontweight="bold", color=theme.FOREST)
    box(ax, 4, y, 19, 14, "Log-Mel\n80 × 3000", fc="#ffffff", ec=theme.INK_SECONDARY, size=14)
    box(ax, 28, y, 21, 14, "합성곱 2개\n시간 3000 → 1500", fc="#ffffff", ec=theme.INK_SECONDARY, size=14)
    box(ax, 54, y, 30, 14, "Transformer 인코더\n(셀프 어텐션) 위치 1500개\ntiny 4층 … medium 24층", size=14)
    box(ax, 99, y, 31, 14, "Transformer 디코더\n이전 토큰 + 소리 요약을 보고\n다음 토큰을 하나 고름", size=14, fc="#efe9ff", ec=theme.PURPLE, color=theme.PURPLE)
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
    box(ax, 144, 36, 14, 22, "소리 4개\n(4, 2, 343,980)\n\n드럼\n베이스\n기타\n보컬", fc="#ffffff", ec=theme.INK_SECONDARY, size=11.5)
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
    title(ax, "두 모델, 다른 문제", "같은 Transformer 계열 부품이라도 입력 표현과 출력(학습 목표)이 다르면 전혀 다른 일을 한다")
    cols = [(6, "Whisper", "소리 → 글 (음성 인식)", theme.BUTTON_GREEN, "#e8f6ec"), (86, "HTDemucs", "섞인 소리 → 소리 4개 (음원 분리)", theme.PURPLE, "#efe9ff")]
    rows = {
        "Whisper": ["오디오 (30초 창)", "Log-Mel  80 × 3000", "합성곱 2개 + Transformer 인코더", "Transformer 디코더 (토큰 하나씩)", "텍스트 토큰 (글)"],
        "HTDemucs": ["섞인 오디오 (7.8초 조각)", "파형  +  STFT 스펙트로그램", "CNN 인코더 ×2경로 + Transformer 5층", "CNN 디코더 (인코더 출력 더하기)", "오디오 소리 4개 (파형)"],
    }
    labels = ["입력", "표현", "구조", "복원·생성", "출력"]
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
    ax.text(80, 9.3, "공통점: CNN과 Transformer를 쓴다 · 둘 다 nn.LSTM 0개 (LSTM·Attention은 '순서 있는 벡터의 열'을 다루는 범용 부품)", fontsize=13, ha="center", color=theme.FOREST, fontweight="bold")
    ax.text(80, 5.6, "차이점: 디코더가 글을 한 토큰씩 생성 ↔ 오디오를 복원 · 개념 비교용 그림, 실제 내부 층은 더 복잡", fontsize=12, ha="center", color=theme.INK_SECONDARY)
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("slide_6_whisper", fig_whisper), ("slide_7_demucs", fig_demucs), ("slide_7-2_compare", fig_compare)):
        fig = fn()
        path = OUT / f"{name}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        print("저장:", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
