"""분리 전/후 인식 비교 도구(이슈 #18): 같은 곡 구간을 원곡(mix)과 보컬(vocals)로, 모델 크기·VAD를 바꿔 인식하고 정답과 비교한다.

왜 필요한가
- "보컬만 남기면 STT가 얼마나 나아지는가"를 숫자로 답하려면 같은 구간을 조건만 바꿔 여러 번 인식해 정답과 비교해야 한다.
- 조건 = 소리(mix/vocals) × 모델 크기(tiny/base/small …) × VAD(끔/켬) × temperature(기본/0.0). 구간마다 정답 가사는 내가 직접 받아 적어 둔다.
- 노래에서는 같은 입력도 인식이 실행마다 달라질 수 있어서(온도 폴백, 검토 문서 13.5) temperature를 조건으로 넣고, 같은 조건을 되풀이(repeats)해 흔들림 범위를 낸다.

파일 규칙(모두 git 제외 폴더 `data/`)
- `data/song_work/<clip_id>_mix.wav`, `<clip_id>_vocals.wav`  ← separate.process_clip이 만든다
- `data/song_work/truth/<clip_id>.txt`  ← 내가 받아 적은 정답(한 구간의 가사, 줄바꿈은 공백처럼 취급)

설계
- 이 모듈은 계산만 하고 화면(print)을 모른다. 터미널 출력은 scripts/compare_clips.py가 한다.
- 인식 함수 `recognize`를 바꿔 끼울 수 있게 해서(기본 stt.recognize) 모델 없이 테스트할 수 있다.
- 점수는 scoring.wer / scoring.cer(영어 표기 통일 기본값). 노래는 합창·겹침·발음 변형이 많아 WER이 1을 넘을 수 있고,
  이 값은 **STT가 정답 가사를 얼마나 되살렸는지**이지 노래 실력이 아니다.
- 인식된 문장(hyp)은 곡의 가사라서 점수표(metrics)와 **따로** 저장한다. 점수표에는 가사가 들어 있지 않다.

수업과의 관계
- [수업과 같음] 인식은 stt.recognize(faster-whisper, 7강 설정), 채점은 scoring(자습 노트북 WER/CER).
- [수업에 없음] 조건 격자(소리 × 크기 × VAD)를 돌며 한 표로 모으는 구조.
"""
from pathlib import Path

import pandas as pd

import scoring
import stt

WORK_DIR = "data/song_work"
SOURCES = ("mix", "vocals")


def truth_path(clip_id, work_dir=WORK_DIR):
    return Path(work_dir) / "truth" / f"{clip_id}.txt"


def load_truth(clip_id, work_dir=WORK_DIR):
    """정답 파일을 읽어 한 줄 문자열로 돌려준다(줄바꿈·연속 공백은 한 칸으로). 없으면 FileNotFoundError."""
    text = truth_path(clip_id, work_dir).read_text(encoding="utf-8")
    return " ".join(text.split())


def available_clips(work_dir=WORK_DIR):
    """mix, vocals, 정답이 모두 있는 구간 id 목록(이름순)과, 하나라도 빠진 구간 id → 빠진 것 설명 dict를 돌려준다."""
    work = Path(work_dir)
    ids = sorted({p.name.rsplit("_", 1)[0] for p in work.glob("*_mix.wav")} |
                 {p.name.rsplit("_", 1)[0] for p in work.glob("*_vocals.wav")})
    ok, missing = [], {}
    for cid in ids:
        lack = [name for name, path in (("mix", work / f"{cid}_mix.wav"), ("vocals", work / f"{cid}_vocals.wav"),
                                        ("정답", truth_path(cid, work_dir))) if not path.exists()]
        if "정답" not in lack and not load_truth(cid, work_dir):
            lack.append("정답(비어 있음)")      # touch로 만들어 두기만 하고 아직 안 적은 파일은 준비된 것으로 치지 않는다
        if lack:
            missing[cid] = lack
        else:
            ok.append(cid)
    return ok, missing


def temp_label(t):
    """표에 쓰는 temperature 이름: None → '기본'(온도 폴백), 숫자 → 'T0.0'."""
    return "기본" if t is None else f"T{t}"


def compare(clip_ids, sizes=("tiny", "base"), vads=(False,), work_dir=WORK_DIR, recognize=None, language="en",
            temperatures=(None,), repeats=1):
    """구간 × 소리(mix/vocals) × 모델 크기 × VAD × temperature 조건을 모두 인식·채점해 (metrics, texts) DataFrame 두 개를 돌려준다.

    metrics 열: clip, source, size, vad, temp, run, S, D, I, N, WER, CER, sec  (가사 없음)
    texts   열: clip, source, size, vad, temp, run, ref, hyp                    (가사 있음 — 화면·문서에 옮기지 않는다)
    S·D·I·N은 단어(WER) 기준. N은 정답의 정규화된 단어 수.

    temperatures: 조건마다 넘길 temperature 목록. None은 faster-whisper 기본(온도 폴백, 실행마다 달라질 수 있음),
      0.0은 폴백 없이 재현 가능(검토 문서 13.5). 예: (0.0,) 또는 (0.0, None).
    repeats: 같은 조건 전체를 몇 번 되풀이할지(열 run = 1, 2, …). 기본 설정(None)의 흔들림 범위를 보려면 3 이상으로 한다.
      0.0은 항상 같은 결과이므로 되풀이해도 값이 같다(확인용으로만 의미 있음).
    크기를 처음 쓰면 모델 읽기 시간이 sec에 섞이므로, 크기가 바깥 반복이 되게 했다(같은 모델을 이어서 쓴다).
    recognize에는 temperature가 None이 아닐 때만 인자로 넘겨서, 기존 인식 함수(예: 테스트의 가짜 함수)와도 호환된다.
    """
    recognize = recognize or stt.recognize
    refs = {cid: load_truth(cid, work_dir) for cid in clip_ids}
    mrows, trows = [], []
    for run in range(1, repeats + 1):
        for temp in temperatures:
            extra = {} if temp is None else {"temperature": temp}
            for size in sizes:
                for vad in vads:
                    for cid in clip_ids:
                        for src in SOURCES:
                            path = Path(work_dir) / f"{cid}_{src}.wav"
                            hyp, sec = recognize(path, language=language, model_size=size, vad_filter=vad, **extra)
                            w = scoring.wer(refs[cid], hyp, lang=language)
                            c = scoring.cer(refs[cid], hyp, lang=language)
                            key = {"clip": cid, "source": src, "size": size, "vad": bool(vad), "temp": temp_label(temp), "run": run}
                            mrows.append({**key, "S": w["S"], "D": w["D"], "I": w["I"], "N": w["N"],
                                          "WER": w["rate"], "CER": c["rate"], "sec": round(sec, 1)})
                            trows.append({**key, "ref": refs[cid], "hyp": hyp})
    return pd.DataFrame(mrows), pd.DataFrame(trows)


def summarize(metrics):
    """조건(크기, VAD, temperature, 소리)별 요약. 실행(run)이 여러 번이면 실행마다 계산한 뒤 평균과 범위를 낸다.

    열: clips(구간 수), runs(반복 수), errors(실행당 오류 합), N(실행당 정답 단어 합), micro_WER(실행들의 평균),
    micro_min·micro_max(실행 간 최솟값·최댓값 — 흔들림 크기), macro_WER·macro_CER(구간별 평균의 평균), sec(평균 인식 시간).
    Micro = 오류 합 ÷ 정답 단어 합(긴 구간이 더 크게 반영), 오류 합 = S+D+I.
    """
    keys = ["size", "vad", "temp", "source"]
    m = metrics.assign(err=metrics["S"] + metrics["D"] + metrics["I"])
    per_run = (m.groupby(keys + ["run"], sort=False)
                 .agg(clips=("clip", "nunique"), errors=("err", "sum"), N=("N", "sum"),
                      macro_WER=("WER", "mean"), macro_CER=("CER", "mean"), sec=("sec", "mean"))
                 .reset_index())
    per_run["micro"] = per_run["errors"] / per_run["N"]
    out = (per_run.groupby(keys, sort=False)
                  .agg(clips=("clips", "first"), runs=("run", "nunique"), errors=("errors", "mean"), N=("N", "first"),
                       micro_WER=("micro", "mean"), micro_min=("micro", "min"), micro_max=("micro", "max"),
                       macro_WER=("macro_WER", "mean"), macro_CER=("macro_CER", "mean"), sec=("sec", "mean"))
                  .reset_index())
    return out


def pivot_wer(metrics):
    """구간(행) × 조건(열: 크기/VAD/temperature/소리)의 WER 표. 실행이 여러 번이면 실행들의 평균. 어느 쪽이 나은지 한눈에 본다."""
    m = metrics.copy()
    m["cond"] = (m["size"] + "/" + m["vad"].map({True: "VAD켬", False: "VAD끔"}) + "/" + m["temp"] + "/" + m["source"])
    return m.pivot_table(index="clip", columns="cond", values="WER", aggfunc="mean")
