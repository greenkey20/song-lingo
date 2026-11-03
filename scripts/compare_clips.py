"""분리 전/후 인식 비교(이슈 #18). 정답이 있는 구간들을 원곡/보컬 × 모델 크기 × VAD로 인식해 WER·CER 표를 보여 준다.

사전 준비(내 컴퓨터, git 제외 폴더):
    python scripts/separate_clip.py --song N --start S --duration D --id c01      # 구간마다
    data/song_work/truth/c01.txt 에 그 구간의 정답 가사를 받아 적기                 # 구간마다

실행(프로젝트 루트에서):
    python scripts/compare_clips.py                         # 준비된 모든 구간, 크기 tiny·base, VAD 끔
    python scripts/compare_clips.py --sizes tiny base small --vad both
    python scripts/compare_clips.py --ids c01 c02

저장(results/song_compare/, git 제외): metrics.csv(점수표, 가사 없음), texts.csv(인식된 문장 — 가사이므로 화면에 안 찍고
문서·이슈에 옮기지 않는다). 화면에는 점수 숫자만 나온다.
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import clip_compare  # noqa: E402

OUT_DIR = Path("results/song_compare")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", nargs="+", help="비교할 구간 id(기본: mix·vocals·정답이 모두 있는 구간 전부)")
    ap.add_argument("--sizes", nargs="+", default=["tiny", "base"], help="Whisper 모델 크기들(기본 tiny base)")
    ap.add_argument("--vad", choices=["off", "on", "both"], default="off", help="VAD 끔/켬/둘 다(기본 끔)")
    ap.add_argument("--work-dir", default=clip_compare.WORK_DIR)
    a = ap.parse_args(argv)

    ok, missing = clip_compare.available_clips(a.work_dir)
    ids = a.ids or ok
    bad = [i for i in ids if i not in ok]
    if bad:
        ap.error("준비가 덜 된 구간: " + ", ".join(f"{i}(빠진 것: {'/'.join(missing.get(i, ['없는 id']))})" for i in bad))
    if not ids:
        ap.error("비교할 구간이 없습니다. 분리(separate_clip.py)와 정답(truth/<id>.txt)을 먼저 준비하세요.")
    if missing and not a.ids:
        print("건너뜀(빠진 것):", {k: "/".join(v) for k, v in missing.items()})
    vads = {"off": (False,), "on": (True,), "both": (False, True)}[a.vad]
    print(f"구간 {len(ids)}개 × 소리 2 × 크기 {len(a.sizes)} × VAD {len(vads)} = {len(ids) * 2 * len(a.sizes) * len(vads)}번 인식 (로컬, 과금 없음)")

    metrics, texts = clip_compare.compare(ids, a.sizes, vads, a.work_dir)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(OUT_DIR / "metrics.csv", index=False)
    texts.to_csv(OUT_DIR / "texts.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print("\n[1] 조건별 요약 (micro = 오류 합 ÷ 정답 단어 합, macro = 구간별 평균)")
        print(clip_compare.summarize(metrics).round(3).to_string(index=False))
        print("\n[2] 구간 × 조건 WER")
        print(clip_compare.pivot_wer(metrics).round(3).to_string())
    print(f"\n저장: {OUT_DIR / 'metrics.csv'} (점수), {OUT_DIR / 'texts.csv'} (인식 문장 — 가사)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
