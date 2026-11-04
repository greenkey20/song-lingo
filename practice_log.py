"""연습 기록 CSV(이슈 #13): 채점할 때마다 한 줄씩 저장하고, 기록 페이지가 읽는다. 검토 문서 16.10·16.11.

저장 규칙 (공개 저장소·가사 저작물 전제)
- **문장 글은 저장하지 않는다.** 가사(특히 내 노래의 가사)가 기록 파일에 남지 않게, 문장은 `key`(sentences.csv의 문장이면 `s03`, 아니면 글을 정규화한 뒤의
  sha1 앞 10글자 `h_ab12cd34ef`)로만 적는다. 화면에 글을 보여 줄 때는 이번 세션의 메모리(session_state)나 sentences.csv에서 key로 찾는다.
- 인식한 문장·내 답도 저장하지 않는다. 숫자(WER·CER·S·D·I·N)와 설정만 남긴다.
- 파일은 `results/practice_log.csv`(git 제외). 한 사람이 쓰는 로컬 실행을 가정한다. **배포 서버에서 여러 사용자의 기록을 어떻게 나눌지는 미결정**이다.

열: ts(시각), source(sample 예시 문장 / lyrics 가사 입력 / song 내 노래), key, mode(read 따라읽기 / dictation 받아쓰기), wer, cer, S, D, I, n_words, n_chars,
    stt(따라읽기에서 쓴 인식 설정, 받아쓰기는 빈칸), unify(표기 통일 여부).

수업과의 관계: [수업에 없음] 이 모듈 전체. csv 모듈로 읽고 쓰며, 이 프로젝트의 계획서(#13: 시각·문장 id·모드·WER·CER·S/D/I·설정)를 따랐다.
"""
import csv
import hashlib
import time
from pathlib import Path

import scoring
import stt
import tts

LOG_PATH = Path("results/practice_log.csv")
FIELDS = ["ts", "source", "key", "mode", "wer", "cer", "S", "D", "I", "n_words", "n_chars", "stt", "unify"]
NUMERIC = ("wer", "cer", "S", "D", "I", "n_words", "n_chars")
MODES = {"read": "따라읽기", "dictation": "받아쓰기"}


def sentence_key(text, sentences=None):
    """문장 글 → 기록용 key. sentences.csv의 문장과 (정규화해서) 같으면 `s03`, 아니면 `h_<sha1 앞 10글자>`. 글은 key에서 복원할 수 없다."""
    sentences = tts.load_sentences() if sentences is None else sentences
    norm = scoring.normalize(text, unify=False)
    for s in sentences:
        if scoring.normalize(s["sentence"], unify=False) == norm:
            return f"s{int(s['id']):02d}"
    return "h_" + hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]


def make_record(source, text, mode, res, sentences=None, now=None):
    """채점 결과 res(practice.read·dictation의 dict)를 기록 한 줄(dict)로 바꾼다. 오류로 점수가 없으면 None."""
    if res.get("error") or not res.get("score"):
        return None
    sc = res["score"]
    w, c = sc["wer"], sc["cer"]
    return {"ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)), "source": source,
            "key": sentence_key(text, sentences), "mode": mode,
            "wer": round(w["rate"], 4), "cer": round(c["rate"], 4), "S": w["S"], "D": w["D"], "I": w["I"],
            "n_words": w["N"], "n_chars": c["N"],
            "stt": (stt.settings() if mode == "read" else ""), "unify": True}


def append(record, path=LOG_PATH):
    """기록 한 줄을 CSV 끝에 붙인다(파일·폴더·머리글이 없으면 만든다). record가 None이면 아무것도 안 한다."""
    if record is None:
        return None
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: record.get(k, "") for k in FIELDS})
    return record


def read_all(path=LOG_PATH):
    """기록을 시간순 dict 목록으로 읽는다(숫자 열은 숫자로). 파일이 없으면 빈 목록. 깨진 줄은 건너뛴다."""
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                for k in NUMERIC:
                    row[k] = float(row[k]) if k in ("wer", "cer") else int(float(row[k]))
            except (TypeError, ValueError):
                continue
            rows.append(row)
    return rows


def attempts(rows, key, mode):
    """같은 문장(key)·같은 방법(mode)의 시도들을 시간순으로 돌려준다(길이가 다른 문장의 오류율을 한 선에 섞지 않으려고 문장별로 나눈다)."""
    return [r for r in rows if r["key"] == key and r["mode"] == mode]


def practiced_keys(rows, source=None):
    """연습한 문장 key의 집합(source를 주면 그 출처만)."""
    return {r["key"] for r in rows if source is None or r["source"] == source}


def step_percent(n_words):
    """문장이 n_words단어일 때 단어 하나가 달라지면 WER이 몇 %p 움직이는지(그래프 아래 설명용). n_words가 0이면 None."""
    return None if not n_words else 100.0 / n_words
