"""곡 구간 → 연습용 **줄 목록**을 만들고 사람이 고친 가사를 저장·불러오기 (이슈 #31).

흐름: 구간 파일(data/song_work/cNN_mix.wav) → STT 구간 시각(stt.recognize_segments, medium, 원곡 **경로**, VAD 끔)
      → 줄 나누기(song_lines.split_into_lines) → data/song_practice/<구간 id>/lines.json 저장
      → 사람이 줄별로 확인·수정(apply_edits) → 확정한 줄만 연습에 쓴다(confirmed_lines).
이 모듈은 **파일 읽기·쓰기와 순서 연결**만 한다. 인식은 stt, 줄 나누기 규칙은 song_lines, 표준 발음 음성(TTS)은 tts.py가 한다.

저장 규칙 (가사는 저작물이라 모두 data/ 아래 = git 제외, 문서·이슈·PR에는 옮기지 않는다)
- `stt_text`는 STT 원문 그대로 두고, 사용자가 고친 글은 `text`에 둔다(수정 전/후를 같이 남김). 고쳤으면 `edited`가 True.
- `status`: candidate(아직 확인 안 함) / confirmed(확인했거나 고침) / dropped(연습에서 뺌).
- **이미 저장된 파일은 덮어쓰지 않는다**(사용자가 고친 가사를 잃지 않게). 다시 만들려면 overwrite=True이고, 그때도 옛 파일을 lines.prev.json으로 남긴다.
- 곡 파일 이름은 저장하지 않고 구간 id·시작·길이만 남긴다(separate의 clips.csv와 같은 기준).

[수업에 없음] 이 모듈 전체. json 모듈로 읽고 쓰며, 쓸 때는 임시 파일에 쓴 뒤 이름을 바꿔(os.replace) 중간에 끊겨도 파일이 깨지지 않게 한다.
"""
import json
import os
import time
from pathlib import Path

import separate
import song_lines
import stt

SONG_DIR = "data/song_practice"      # 줄 목록 저장 위치(git 제외)
SONG_MODEL = "medium"                # 노래 STT 모델(검토 문서 13.5·15.2: medium + 원곡 + VAD 끔 + 기본 설정)
STATUSES = ("candidate", "confirmed", "dropped")


def lines_path(clip_id, out_dir=SONG_DIR):
    return Path(out_dir) / clip_id / "lines.json"


def _write_json(path, doc):
    """임시 파일에 쓴 뒤 이름을 바꿔 저장한다(쓰다 끊겨도 기존 파일이 깨지지 않음)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def prepare_lines(clip_id, work_dir=separate.WORK_DIR, out_dir=SONG_DIR, model_size=SONG_MODEL, recognize=stt.recognize_segments,
                  overwrite=False, language="en", **split_kwargs):
    """구간 하나를 인식해 줄 후보를 만들고 lines.json으로 저장한 뒤 그 내용(dict)을 돌려준다.

    clip_id: 구간 id(예: "c05"). work_dir의 `<id>_mix.wav`(원곡 구간)를 쓴다. 없으면 FileNotFoundError.
    recognize: 인식 함수(테스트에서 가짜로 바꿈). 기본은 stt.recognize_segments이고 **경로를 그대로**, vad_filter=False, 단어 시간 포함으로 부른다.
    overwrite: False면 이미 lines.json이 있을 때 FileExistsError(고친 가사를 지키려고). True면 옛 파일을 lines.prev.json으로 남기고 새로 만든다.
    split_kwargs: song_lines.split_into_lines의 인자(max_sec 등)."""
    mix_path, _ = separate.clip_paths(clip_id, work_dir)
    if not Path(mix_path).exists():
        raise FileNotFoundError(f"{clip_id}의 원곡 구간 파일이 없습니다: {mix_path} (먼저 separate_clip.py --cut-only로 자르세요)")
    target = lines_path(clip_id, out_dir)
    if target.exists() and not overwrite:
        raise FileExistsError(f"이미 있습니다: {target} (고친 가사를 지키려고 덮어쓰지 않습니다. 다시 만들려면 overwrite=True)")
    segs, seconds = recognize(str(mix_path), language, model_size=model_size, vad_filter=False, word_timestamps=True)
    lines = song_lines.split_into_lines(segs, **split_kwargs)
    meta = separate.manifest_row(clip_id, work_dir) or {}
    doc = {
        "clip_id": clip_id, "start": _num(meta.get("start")), "duration": _num(meta.get("duration")),
        "stt": {"model": model_size, "vad_filter": False, "temperature": "default", "seconds": round(seconds, 1), "n_segments": len(segs)},
        "lines": [{"no": l["no"], "start": l["start"], "end": l["end"], "stt_text": l["text"], "text": l["text"], "edited": False,
                   "status": "candidate", "source": l["source"], "low_confidence": l["low_confidence"], "too_long": l["too_long"],
                   "n_words": l["n_words"], "segment_ids": l["segment_ids"], "tts_path": None} for l in lines],
        "segments": segs,      # 줄을 다시 나누거나 보컬 조각을 자를 때 쓰려고 원본 구간(단어 시간 포함)도 남긴다
    }
    if target.exists():
        os.replace(target, target.with_name("lines.prev.json"))
    _write_json(target, doc)
    return doc


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_lines(clip_id, out_dir=SONG_DIR):
    """저장된 lines.json을 읽어 dict로 돌려준다. 없으면 FileNotFoundError."""
    path = lines_path(clip_id, out_dir)
    if not path.exists():
        raise FileNotFoundError(f"저장된 줄 목록이 없습니다: {path} (prepare_lines로 먼저 만드세요)")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def apply_edits(clip_id, edits=None, confirm=(), drop=(), out_dir=SONG_DIR):
    """사람이 고친 내용을 저장한다. 고친 뒤의 문서(dict)를 돌려준다.

    edits: {줄 번호: 새 가사}. 새 가사가 STT 원문과 다르면 edited=True, 같으면 edited=False. 고친 줄은 자동으로 confirmed가 된다.
    confirm: 고치지 않고 **맞다고 확인만** 한 줄 번호들(status=confirmed).
    drop: 연습에서 뺄 줄 번호들(status=dropped, 반주만 있는 구간 등).
    없는 줄 번호나 빈 가사는 ValueError(빈 줄은 drop으로 뺀다). 저장은 모든 검사가 끝난 뒤에 한꺼번에 해서 일부만 반영되지 않는다."""
    doc = load_lines(clip_id, out_dir)
    by_no = {l["no"]: l for l in doc["lines"]}
    edits = dict(edits or {})
    for no in list(edits) + list(confirm) + list(drop):
        if no not in by_no:
            raise ValueError(f"줄 {no}번이 없습니다(있는 줄: {sorted(by_no)}).")
    for no, text in edits.items():
        if not str(text).strip():
            raise ValueError(f"줄 {no}번의 가사가 비어 있습니다. 빼려면 drop을 쓰세요.")
    for no, text in edits.items():
        ln = by_no[no]
        ln["text"] = str(text).strip()
        ln["edited"] = ln["text"] != ln["stt_text"]
        ln["status"] = "confirmed"
    for no in confirm:
        if by_no[no]["status"] != "dropped":
            by_no[no]["status"] = "confirmed"
    for no in drop:
        by_no[no]["status"] = "dropped"
    doc["edited_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _write_json(lines_path(clip_id, out_dir), doc)
    return doc


def confirmed_lines(clip_id, out_dir=SONG_DIR):
    """연습에 쓸 줄(status=confirmed)만 [{"no","start","end","text"}]로 돌려준다."""
    return [{k: l[k] for k in ("no", "start", "end", "text")} for l in load_lines(clip_id, out_dir)["lines"] if l["status"] == "confirmed"]


def status_summary(clip_id, out_dir=SONG_DIR):
    """상태별 줄 수와 고친 줄 수를 {"candidate", "confirmed", "dropped", "edited", "low_confidence"}로 돌려준다(가사는 포함하지 않음)."""
    lines = load_lines(clip_id, out_dir)["lines"]
    out = {s: sum(l["status"] == s for l in lines) for s in STATUSES}
    out["edited"] = sum(l["edited"] for l in lines)
    out["low_confidence"] = sum(l["low_confidence"] for l in lines)
    return out


def tts_plan(clip_id, out_dir=SONG_DIR, lookup=None):
    """확정된 줄(confirmed) 중 **표준 발음 음성이 아직 없거나 가사가 바뀐** 줄을 찾아 [{"no", "text", "path", "cached"}]로 돌려준다.
    cached=True면 같은 문장의 음성 파일이 이미 있어 API를 부르지 않는다(tts.py는 문장 내용의 해시로 캐시 파일 이름을 정함). 파일은 만들지 않는다.
    lookup: tts.lookup_sentence처럼 (문장, []) → (행, 경로)를 돌려주는 함수(테스트에서 가짜로 바꿈)."""
    import tts
    lookup = lookup or tts.lookup_sentence
    plan = []
    for ln in load_lines(clip_id, out_dir)["lines"]:
        if ln["status"] != "confirmed":
            continue
        _row, path = lookup(ln["text"], [])
        if ln.get("tts_text") == ln["text"] and ln.get("tts_path") and Path(ln["tts_path"]).exists():
            continue                                     # 이미 만들어 둔 줄
        plan.append({"no": ln["no"], "text": ln["text"], "path": Path(path), "cached": Path(path).exists()})
    return plan


def make_tts(clip_id, out_dir=SONG_DIR, generate=False, lookup=None, synth=None):
    """확정된 줄마다 **표준 발음 기준 음성**(OpenAI TTS, 기존 tts.py)을 만든다. 기본은 **계획만 보여 주는 안전 모드**다.

    generate=False(기본): 파일도 API 호출도 없이 {"n_lines", "n_api_calls"(캐시에 없어 새로 부를 줄 수), "n_cached", "chars"(새로 보낼 글자 수), "done": False}만 돌려준다.
    generate=True: 줄마다 음성을 만들고(캐시에 있으면 API를 부르지 않음) lines.json에 tts_path·tts_text를 저장한다. 호출은 **과금**된다.
    가사가 외부 API로 나가는 것은 11-04 사용자 결정으로 허용했다(검토 문서 13.5). 만든 음성은 data/ 아래(git 제외)에만 있다.
    synth: tts.tts_wav처럼 (문장, 경로)로 음성 파일을 만드는 함수(테스트에서 가짜로 바꿈)."""
    import tts
    synth = synth or tts.tts_wav
    plan = tts_plan(clip_id, out_dir, lookup)
    new = [p for p in plan if not p["cached"]]
    summary = {"n_lines": len(plan), "n_api_calls": len(new), "n_cached": len(plan) - len(new),
               "chars": sum(len(p["text"]) for p in new), "done": False}
    if not generate or not plan:
        return summary
    doc = load_lines(clip_id, out_dir)
    by_no = {l["no"]: l for l in doc["lines"]}
    for p in plan:
        wav = synth(p["text"], p["path"])
        by_no[p["no"]]["tts_path"] = str(wav)
        by_no[p["no"]]["tts_text"] = p["text"]
    _write_json(lines_path(clip_id, out_dir), doc)
    summary["done"] = True
    return summary


def save_review(clip_id, boundary_notes, out_dir=SONG_DIR):
    """귀로 확인한 **줄 경계 메모**를 lines.json의 "review"에 저장한다(줄 번호 → 짧은 메모, 예: "너무 짧음", "앞 줄과 합쳐야 함").
    가사는 바꾸지 않는다. 규칙(song_lines)을 고칠 때 근거로 쓴다. 없는 줄 번호는 ValueError. 빈 dict를 주면 메모를 지운다."""
    doc = load_lines(clip_id, out_dir)
    nos = {l["no"] for l in doc["lines"]}
    bad = [n for n in boundary_notes if n not in nos]
    if bad:
        raise ValueError(f"줄 {bad}번이 없습니다(있는 줄: {sorted(nos)}).")
    doc["review"] = {"boundary_notes": {str(k): str(v) for k, v in boundary_notes.items()}, "reviewed_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    _write_json(lines_path(clip_id, out_dir), doc)
    return doc["review"]
