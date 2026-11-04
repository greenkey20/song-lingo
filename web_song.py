"""웹 앱 "내 노래" 페이지의 계산·파일 처리(화면 코드는 app/views/song.py). 이슈 #31·#37, 검토 문서 16.10.

흐름: 업로드한 곡(bytes) → 세션 작업 폴더에 저장 → 파형 윤곽(waveform_peaks)과 길이 → 구간(시작·길이)을 잘라 mix 저장(separate.cut_clip)
      → 줄 후보(song_practice.prepare_lines, medium) → 사람이 고침(song_practice.apply_edits) → 보컬 분리(separate.separate_clip, 선택).
이 모듈은 **기존 모듈을 순서대로 부르고 파일 위치만 정한다.** 새 계산은 파형 윤곽과 시각 표기뿐이다.

저장 규칙 (검토 문서 16.10, CLAUDE.md Privacy)
- 곡·구간·보컬·줄 목록은 모두 **세션 작업 폴더**(시스템 임시 폴더 아래 `songlingo_*`)에만 둔다. 저장소(git)와 `data/`에 곡을 두지 않는다.
- 작업 폴더는 앱이 새로 시작될 때 오래된 것(기본 1시간 초과)부터 지운다(cleanup_old_workspaces). 사용자가 "곡 지우기"를 누르면 바로 지운다.
- 예외: 표준 발음 음성(TTS)은 tts.py의 기존 캐시(`data/tts_cache/`, 문장 내용의 해시 이름)에 남는다. 배포 서버에서 이 캐시를 어떻게 할지는 **미결정**이다.

수업과의 관계
- [수업과 같음] 파형 읽기·스테레오/모노 처리는 audio.py(017_sound)를 그대로 쓴다. 파형 그림은 수업의 파형 그림과 같은 개념이다.
- [수업에 없음] 파형 **윤곽(peaks)**: 수만~수백만 개의 표본을 모두 그릴 수 없어서, 일정한 칸(bin)마다 최솟값·최댓값만 남겨 그린다.
  `tempfile.mkdtemp`: 파이썬 표준 라이브러리로 임시 폴더를 만든다(운영체제가 재부팅 때 정리하기도 하지만 우리가 직접도 지운다).
"""
import shutil
import tempfile
import time
from pathlib import Path

import numpy as np

import audio
import separate
import song_practice

WORKSPACE_PREFIX = "songlingo_"
CLIP_ID = "clip"                 # 웹 세션에서는 한 번에 구간 하나만 다룬다
DURATIONS = (10, 15, 20)         # 사용자가 고르는 구간 길이(초)


# ---------- 작업 폴더 ----------
def new_workspace(base=None):
    """이 세션의 작업 폴더를 만들어 Path로 돌려준다. base가 None이면 시스템 임시 폴더 아래."""
    return Path(tempfile.mkdtemp(prefix=WORKSPACE_PREFIX, dir=base))


def cleanup_old_workspaces(base=None, max_age_s=3600, now=None):
    """base 아래 `songlingo_*` 폴더 중 마지막 수정 후 max_age_s초가 지난 것을 지우고 지운 개수를 돌려준다."""
    base = Path(base or tempfile.gettempdir())
    now = time.time() if now is None else now
    n = 0
    for p in base.glob(WORKSPACE_PREFIX + "*"):
        if p.is_dir() and now - p.stat().st_mtime > max_age_s:
            shutil.rmtree(p, ignore_errors=True)
            n += 1
    return n


def delete_workspace(ws):
    """작업 폴더를 통째로 지운다(곡 지우기). 폴더 이름이 우리 접두어로 시작할 때만 지운다(엉뚱한 폴더를 지우지 않으려는 안전장치)."""
    ws = Path(ws)
    if not ws.name.startswith(WORKSPACE_PREFIX):
        raise ValueError(f"작업 폴더가 아닙니다: {ws.name}")
    shutil.rmtree(ws, ignore_errors=True)


def work_dir(ws):
    return Path(ws) / "work"


def practice_dir(ws):
    return Path(ws) / "practice"


def save_upload(ws, name, data):
    """업로드한 곡 bytes를 작업 폴더에 `song<확장자>`로 저장하고 경로를 돌려준다(원래 이름은 쓰지 않음: 이상한 문자·경로 조작 방지)."""
    suffix = Path(name).suffix.lower()
    path = Path(ws) / f"song{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


# ---------- 파형·시각 ----------
def format_hms(seconds):
    """초 → 'hh:mm:ss'(반올림한 정수 초)."""
    s = int(round(max(0.0, seconds)))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def clip_range_label(start, duration):
    """'00:01:05 ~ 00:01:20' 형식의 구간 표기."""
    return f"{format_hms(start)} ~ {format_hms(start + duration)}"


def waveform_peaks(x, n_bins=600):
    """파형 x((샘플,) 또는 (샘플, 채널))를 n_bins칸으로 나눠 칸마다 (최솟값, 최댓값)을 돌려준다: (mins, maxs) 두 배열(길이 n_bins).

    채널은 평균으로 모노로 만든다. 샘플이 n_bins보다 적으면 있는 만큼만 돌려준다. 비어 있으면 ValueError."""
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 2:
        x = x.mean(axis=1)
    if x.size == 0:
        raise ValueError("샘플이 없습니다.")
    n_bins = max(1, min(int(n_bins), x.size))
    edges = np.linspace(0, x.size, n_bins + 1).astype(int)
    mins = np.array([x[a:b].min() for a, b in zip(edges[:-1], edges[1:])])
    maxs = np.array([x[a:b].max() for a, b in zip(edges[:-1], edges[1:])])
    return mins, maxs


def song_overview(source, n_bins=600):
    """곡(경로 또는 bytes)을 한 번 디코딩해 {"mins", "maxs", "seconds", "sr"}를 돌려준다(그림·구간 슬라이더용)."""
    x, sr, _ = audio.load_raw(source)
    mins, maxs = waveform_peaks(x, n_bins)
    return {"mins": mins, "maxs": maxs, "seconds": x.shape[0] / sr, "sr": sr}


# ---------- 구간 → 줄 ----------
def cut(ws, song_path, start, duration):
    """곡의 구간을 잘라 작업 폴더에 저장한다(예전 구간·보컬·줄 목록은 지움). separate.cut_clip의 결과 dict를 돌려준다."""
    out = separate.cut_clip(song_path, start, duration, CLIP_ID, work_dir=work_dir(ws), overwrite=True)
    lines = song_practice.lines_path(CLIP_ID, practice_dir(ws))
    if lines.exists():
        lines.unlink()                 # 구간이 바뀌었으니 옛 줄 목록은 맞지 않는다
    return out


def recognize_lines(ws, model_size=song_practice.SONG_MODEL, recognize=None):
    """잘라 둔 구간을 인식해 줄 후보를 만들어 저장하고 doc(dict)을 돌려준다. recognize: 테스트용 가짜 인식 함수."""
    kw = {} if recognize is None else {"recognize": recognize}
    return song_practice.prepare_lines(CLIP_ID, work_dir=work_dir(ws), out_dir=practice_dir(ws), model_size=model_size,
                                       overwrite=True, **kw)


def load_doc(ws):
    """저장된 줄 목록 doc. 없으면 None."""
    try:
        return song_practice.load_lines(CLIP_ID, practice_dir(ws))
    except FileNotFoundError:
        return None


def confirm_line(ws, no, text):
    """줄 no의 가사를 text로 확정한다(고쳤으면 edited)."""
    return song_practice.apply_edits(CLIP_ID, edits={no: text}, out_dir=practice_dir(ws))


def drop_line(ws, no):
    """줄 no를 연습에서 뺀다."""
    return song_practice.apply_edits(CLIP_ID, drop=[no], out_dir=practice_dir(ws))


def make_vocals(ws, separate_fn=None, python=None):
    """잘라 둔 구간의 보컬을 분리한다(CPU에서 20초에 1~2분). 이미 있으면 다시 하지 않는다. 결과 경로를 돌려준다.

    기본은 **별도 프로세스**(separate.separate_clip_subprocess)다: 쓸 파이썬은 python 인자 > 환경변수 SONGLINGO_SEPARATE_PYTHON > 지금 파이썬.
    separate_fn은 테스트용으로, 주면 같은 프로세스 안에서 그 함수로 분리한다."""
    _mix, voc = separate.clip_paths(CLIP_ID, work_dir(ws))
    if voc.exists():
        return voc
    if separate_fn is not None:
        separate.separate_clip(CLIP_ID, work_dir=work_dir(ws), separate=separate_fn)
    else:
        separate.separate_clip_subprocess(CLIP_ID, work_dir=work_dir(ws), python=python)
    return voc


def tts_summary(ws):
    """확정한 줄의 표준 발음 음성을 만들 때의 계획(새로 부를 호출 수·글자 수)을 파일·API 없이 돌려준다."""
    return song_practice.make_tts(CLIP_ID, out_dir=practice_dir(ws), generate=False)


def make_tts(ws, synth=None):
    """확정한 줄의 표준 발음 음성을 만든다(**OpenAI TTS 과금**, 캐시에 있는 문장은 부르지 않음)."""
    return song_practice.make_tts(CLIP_ID, out_dir=practice_dir(ws), generate=True, synth=synth)


def line_range(line, clip_seconds, pad=0.1):
    """줄 하나의 재생 구간 (시작, 끝)을 앞뒤로 pad초 넓혀 [0, clip_seconds] 안에 맞춘다."""
    return max(0.0, line["start"] - pad), min(float(clip_seconds), line["end"] + pad)
