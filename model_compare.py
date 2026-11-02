"""같은 녹음을 여러 Whisper 모델 크기로 인식·채점해 표로 비교한다(11-02 면담 조언: 모델을 올려 보기, 검토 문서 15.2).

이 모듈은 '연습 한 번'(practice.py)이 아니라 **모델 크기를 바꿔 가며 같은 녹음을 여러 번 재 보는 실험 도구**다.
그래서 practice.py(계산 없는 얇은 연결 모듈)에서 분리했다. 계산은 각 모듈이 한다: 크기별 인식은 stt.py,
채점은 scoring.py, 문장 읽기는 tts.py이고 이 파일은 그것들을 모델 × 녹음 순서로 이어 붙여 결과를 모은다.

흐름
    out = compare_models([1, 2, 3], ["tiny", "base", "small"], takes=[1], release=True)
    out["rows"]       # 모델 × 녹음마다 한 줄(WER, CER, 틀린 부분, 인식 시간 …) → pandas DataFrame으로 표를 만든다

수업과의 관계
- [수업에 없음] 이 파일 전체. 모델 크기를 바꿔 비교하는 것은 수업 7강(tiny만 사용)에 없는 확장이고, 크기별 모델을 읽는
  방식은 stt.py의 load_model(model_size)에 있다. WER·CER 채점은 자습 노트북(scoring.py) 기준이다.
"""
import time
from pathlib import Path

import scoring
import stt
import tts


def compare_models(ids, sizes=None, takes=(1,), sentences=None, rec_dir=None, release=False, vad_filters=(False,)):
    """같은 녹음을 여러 Whisper 모델 크기로 인식·채점해 비교한다(면담 조언: 모델을 올려 보기, 검토 문서 15.2).

    ids: 문장 id 목록(예: [1, 2, 3]). sizes: 모델 크기 목록(안 주면 기본 크기 하나). takes: 회차 목록(예: [1, 2, 3]).
    녹음은 stt.find_recording이 data/recordings/sNN_takeK.*에서 찾는다(rec_dir로 폴더를 바꿀 수 있다).
    모델은 크기마다 한 번만 읽고(처음 쓰는 크기는 내려받음), 그 읽는 시간은 인식 시간과 따로 잰다.
    release=True면 한 크기의 비교가 끝날 때마다 그 모델을 메모리에서 내린다(이미 읽혀 있던 모델은 남김). 큰 모델을 여러 개
    돌릴 때 메모리가 쌓이지 않게 하려는 것이다. 어떤 크기의 모델을 읽지 못해도(내려받기 실패, 이름 오류 등) 그 크기만
    건너뛰고 errors에 적은 뒤 나머지를 계속한다. 이 PC에 있는 모델 전부를 쓰려면 sizes=stt.available_models().

    vad_filters: 인식할 때 VAD(말소리 없는 구간 걸러내기)를 켤지 끌지. (False,)가 기본이고 7강과 같은 설정이다. (False, True)를 주면
    모델마다 끔/켬 두 번씩 인식해 rows의 "vad" 열로 구분한다(True나 False 하나만 줘도 된다).

    돌려주는 dict
      rows: 모델 × VAD × 녹음마다 한 줄 {"model", "vad", "id", "take", "file"(이름만), "ref", "hyp", "wer", "cer", "S", "D", "I", "N",
            "diff"(틀린 부분 표시), "sec"(인식 시간)}. S·D·I·N은 scoring.evaluate의 main 쪽(일본어는 CER, 그 밖은 WER)
      missing: 문장이나 녹음을 찾지 못한 항목 설명(건너뛰고 계속한다)
      load_sec: 크기별 모델 읽는 시간(이미 읽어 둔 모델은 0에 가깝다). 읽지 못한 크기는 없음
      errors: 모델을 읽지 못한 크기 → 오류 설명
      settings: 인식 설정(장치, 계산 방식, beam_size). 결과를 보고할 때 함께 적는다
    """
    sizes = list(sizes) if sizes else [stt.MODEL_SIZE]
    vad_filters = (bool(vad_filters),) if isinstance(vad_filters, bool) else tuple(vad_filters)
    sentences = sentences if sentences is not None else tts.load_sentences()
    by_id = {s["id"]: s for s in sentences}
    jobs, missing = [], []
    for sid in ids:
        row = by_id.get(str(sid))
        if row is None:
            missing.append(f"문장 {sid}: sentences.csv에 없음")
            continue
        for take in takes:
            rec = stt.find_recording(sid, take, rec_dir) if rec_dir is not None else stt.find_recording(sid, take)
            if rec is None:
                missing.append(f"문장 {sid} take{take}: 녹음 없음 (sNN_takeK 파일)")
            else:
                jobs.append((row, take, rec))
    rows, load_sec, errors = [], {}, {}
    preloaded = set(stt.loaded_models())        # release=True여도 비교 전에 이미 읽혀 있던 모델은 내리지 않는다
    for size in sizes:
        t0 = time.time()
        try:
            stt.load_model(size)                # 읽는 시간을 인식 시간과 따로 재려고 먼저 읽는다
        except Exception as e:                  # 내려받기 실패·잘못된 이름 등: 이 크기만 건너뛰고 계속한다
            errors[size] = f"{type(e).__name__}: {e}"
            continue
        load_sec[size] = time.time() - t0
        for vad in vad_filters:
            for row, take, rec in jobs:
                hyp, sec = stt.recognize(rec, row["lang"], model_size=size, vad_filter=vad)
                ev = scoring.evaluate(row["sentence"], hyp, row["lang"])
                main = ev["main"]
                rows.append({"model": size, "vad": vad, "id": row["id"], "take": take, "file": Path(rec).name,
                             "ref": row["sentence"], "hyp": hyp, "wer": ev["wer"]["rate"], "cer": ev["cer"]["rate"],
                             "S": main["S"], "D": main["D"], "I": main["I"], "N": main["N"],
                             "diff": scoring.format_diff(main["ops"]), "sec": sec})
        if release and size not in preloaded:
            stt.unload_models(size)
    return {"rows": rows, "missing": missing, "load_sec": load_sec, "errors": errors, "settings": stt.settings()}
