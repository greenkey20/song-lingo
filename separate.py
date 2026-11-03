"""노래 파일의 한 구간을 잘라 '보컬만' 분리한다(이슈 #18, 다음 단계는 #31·#32).

왜 필요한가
- Whisper는 음악이 섞인 소리에서 가사를 잘 못 받아 적을 수 있다. 보컬만 남기면 더 나아지는지 비교하고(#18),
  분리한 보컬 구간을 연습 문장의 '기준 음성'으로 쓰기 위한 첫 단계다(#31·#32).
- 곡은 내 컴퓨터 안에서만 처리한다(분리 모델도, 이후 STT도 로컬). 곡 파일과 결과는 git에서 제외된 `data/` 아래에만 둔다.

흐름
    곡 파일 ─ audio.load_raw(PyAV로 디코딩) ─ 구간 자르기 ─ 44.1 kHz 스테레오 ─ Demucs ─ 보컬(스테레오)
    ─ 구간 원본(mix)과 보컬을 `data/song_work/<clip_id>_mix.wav`, `<clip_id>_vocals.wav`로 저장
    자르기(`cut_clip`, 몇 초)와 분리(`separate_clip`, 구간당 1분 안팎)는 따로 부를 수 있다: 자른 구간을 먼저 듣고
    가사 부분이 맞을 때만 분리하려는 것이다(`process_clip`은 둘을 이어 부르는 편의 함수).
    (STT에 넣을 때의 16 kHz 모노 변환은 faster-whisper가 안에서 한다. 검토 문서 14.6)

수업과의 관계
- [수업과 같음] 파형 읽기·스테레오/모노 처리·`resample_poly` 리샘플링은 `audio.py`(017_sound lesson04 코드)를 그대로 쓴다.
- [수업에 없음] **Demucs**: 섞인 노래에서 보컬·드럼·베이스·기타(other)를 따로 떼어 내는 사전학습 분리 모델.
  `htdemucs`는 44.1 kHz 스테레오를 입력받아 네 가지 소리(drums, bass, other, vocals)를 돌려준다.
  CPU에서는 20초 구간에 약 65초가 걸렸다(곡 1개 1회, 스레드 2 — 검토 문서 13.5). 그래서 곡 전체가 아니라 구간 단위로 쓴다.
- [수업에 없음] `torch`: Demucs가 쓰는 딥러닝 라이브러리(환경에 이미 있음). 마이크·테스트 때처럼 분리를 안 쓰는 코드는
  torch를 불러오지 않도록 이 모듈은 필요한 순간에만 import한다.
"""
import csv
import time
from math import gcd
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

import audio
import recorder

SONG_DIR = "data/songs"          # 내 곡 폴더(git 제외): data/songs/<언어>/*.wma|mp3 …
WORK_DIR = "data/song_work"      # 구간·보컬·목록(clips.csv) 저장 위치(git 제외)
MODEL_NAME = "htdemucs"          # Demucs 모델 이름(4가지 소리를 분리하는 기본 모델)
MODEL_SR = 44100                 # htdemucs가 기대하는 표본화 주파수
SONG_EXTS = (".wma", ".mp3", ".wav", ".m4a", ".flac", ".ogg")

_models = {}                     # 모델 이름 → 불러 둔 모델(매번 읽으면 8초 안팎 걸려서 한 번만 읽는다)


def list_songs(lang="en", root=SONG_DIR):
    """`root/lang` 아래 곡 파일을 이름순으로 돌려준다(.DS_Store 같은 파일은 제외). 폴더가 없으면 FileNotFoundError."""
    folder = Path(root) / lang
    if not folder.is_dir():
        raise FileNotFoundError(f"곡 폴더가 없습니다: {folder}")
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SONG_EXTS)


def load_clip(path, start=0.0, duration=20.0, sr=MODEL_SR):
    """곡 파일의 [start, start+duration)초를 (2, 샘플) float32 스테레오 파형(sr)으로 돌려준다.

    - 디코딩은 audio.load_raw(wav는 scipy, 그 밖에는 PyAV). 모노 곡은 같은 소리를 양쪽에 복사한다.
    - 곡이 구간보다 짧으면 있는 만큼만 돌려준다. 시작이 곡 길이를 넘으면 ValueError.
    - 리샘플링은 채널마다 resample_poly(원본 sr → sr)로 한다.
    """
    if start < 0 or duration <= 0:
        raise ValueError("start는 0 이상, duration은 0보다 커야 합니다.")
    x, orig_sr, _ = audio.load_raw(path)                   # (샘플, 채널)
    a, b = int(round(start * orig_sr)), int(round((start + duration) * orig_sr))
    x = x[a:b]
    if x.shape[0] == 0:
        raise ValueError(f"시작 위치({start}초)가 곡 길이를 넘었습니다: {Path(path).name}")
    x = x.T                                                # (채널, 샘플)
    if x.shape[0] == 1:
        x = np.repeat(x, 2, axis=0)                        # 모노 → 스테레오(모델이 2채널을 기대)
    elif x.shape[0] > 2:
        x = x[:2]                                          # 3채널 이상은 앞의 두 채널만(드문 경우)
    if orig_sr != sr:
        g = gcd(sr, orig_sr)
        x = resample_poly(x, sr // g, orig_sr // g, axis=1)
    return x.astype(np.float32)


def _load_model(name=MODEL_NAME):
    """Demucs 모델을 한 번만 읽어 캐시한다. 처음에는 인터넷에서 내려받는다(이후에는 캐시 사용)."""
    if name not in _models:
        from demucs.pretrained import get_model   # 지연 import: demucs·torch는 분리할 때만 필요
        model = get_model(name)
        model.eval()                               # 학습 모드가 아니라 추론 모드(드롭아웃 등 끔)
        _models[name] = model
    return _models[name]


def separate_vocals(clip, sr=MODEL_SR, model=None, apply_fn=None, device="cpu", overlap=0.25):
    """(2, 샘플) 스테레오 파형 → 보컬만 남긴 (2, 샘플) float32 파형.

    - 입력은 모델의 sr(44.1 kHz)이어야 한다(load_clip의 기본값). 다르면 ValueError.
    - 정규화: Demucs 명령줄 도구와 같이 '채널 평균'의 평균·표준편차로 입력을 정규화했다가 결과에 되돌린다.
    - split=True: 긴 소리를 조각으로 나눠 처리(메모리 절약), overlap=0.25: 조각이 25% 겹치게 해서 이음새를 부드럽게 한다.
    - 완전한 무음이면(표준편차 0) 모델을 돌리지 않고 무음을 돌려준다.
    - model, apply_fn은 테스트에서 가짜를 넣는 자리다. 평소에는 None.
    """
    if clip.ndim != 2 or clip.shape[0] != 2:
        raise ValueError("(2, 샘플) 모양의 스테레오 파형이 필요합니다.")
    if sr != MODEL_SR:
        raise ValueError(f"{MODEL_SR} Hz 파형이 필요합니다(받은 값 {sr}). load_clip(sr={MODEL_SR})로 만드세요.")
    import torch   # 지연 import

    model = model or _load_model()
    if apply_fn is None:
        from demucs.apply import apply_model
        apply_fn = apply_model
    wav = torch.from_numpy(np.ascontiguousarray(clip, dtype=np.float32))[None]    # (1, 2, 샘플) = 배치 1개
    ref = wav.mean(1)                                                              # 채널 평균 (1, 샘플)
    if float(ref.std()) == 0.0:
        return np.zeros_like(clip, dtype=np.float32)
    wav = (wav - ref.mean()) / ref.std()
    with torch.no_grad():                                                          # 기울기 계산을 끄면 메모리·시간이 줄어든다
        out = apply_fn(model, wav, device=device, split=True, overlap=overlap, progress=False)[0]   # (소리 수, 2, 샘플)
    out = out * ref.std() + ref.mean()
    return out[model.sources.index("vocals")].numpy().astype(np.float32)


def clip_paths(clip_id, work_dir=WORK_DIR):
    """구간 id의 (mix 경로, vocals 경로). 파일 이름 규칙을 한 곳에 둔다."""
    work = Path(work_dir)
    return work / f"{clip_id}_mix.wav", work / f"{clip_id}_vocals.wav"


def manifest_row(clip_id, work_dir=WORK_DIR):
    """clips.csv에서 구간 id의 줄(dict)을 찾아 돌려준다. 파일이 없거나 줄이 없으면 None."""
    path = Path(work_dir) / "clips.csv"
    if not path.exists():
        return None
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["clip_id"] == clip_id:
                return row
    return None


def is_cut_current(song_path, start, duration, clip_id, work_dir=WORK_DIR):
    """이미 잘라 둔 구간이 지금 요청(곡 파일, 시작, 길이)과 같은가. 같으면 다시 자를 필요가 없다.

    노트북에서 start를 고쳐 다시 실행하면 False가 되어, 그 구간만 자동으로 다시 자르게 한다(OVERWRITE 스위치를 따로 안 켜도 됨)."""
    mix_path, _ = clip_paths(clip_id, work_dir)
    row = manifest_row(clip_id, work_dir)
    return bool(mix_path.exists() and row
                and row["song_file"] == Path(song_path).name
                and float(row["start"]) == float(start) and float(row["duration"]) == float(duration))


def cut_clip(song_path, start, duration, clip_id, work_dir=WORK_DIR, overwrite=False):
    """곡의 한 구간을 잘라 `<work_dir>/<clip_id>_mix.wav`(44.1 kHz 스테레오 PCM16)로 저장한다. 몇 초면 끝난다.

    분리(느림)보다 먼저 해서, 구간이 가사 부분인지 귀로 확인한 뒤에 분리하려는 용도다.
    `clips.csv`에 (clip_id, song_file, start, duration)을 남긴다(나중에 어느 곡의 어느 구간인지 찾으려고).
    이미 있는 clip_id는 overwrite=True가 아니면 FileExistsError. 다시 자르면 **옛 구간의 보컬 파일은 지운다**
    (구간이 바뀌었는데 옛 보컬이 남아 있으면 엉뚱한 소리로 비교하게 되므로). 돌려주는 값: dict(mix, seconds)
    """
    mix_path, voc_path = clip_paths(clip_id, work_dir)
    if mix_path.exists() and not overwrite:
        raise FileExistsError(f"이미 있는 구간입니다: {clip_id} (다시 자르려면 overwrite=True)")
    clip = load_clip(song_path, start, duration)
    recorder.save_wav(mix_path, clip.T, MODEL_SR, overwrite=True)       # save_wav는 (샘플, 채널) 모양을 받는다
    if voc_path.exists():
        voc_path.unlink()                                               # 옛 구간의 보컬은 더 이상 맞지 않는다
    _append_manifest(Path(work_dir) / "clips.csv", clip_id, Path(song_path).name, start, duration)
    return {"mix": mix_path, "seconds": clip.shape[1] / MODEL_SR}


def separate_clip(clip_id, work_dir=WORK_DIR, separate=None, overwrite=False):
    """이미 잘라 둔 구간(`<clip_id>_mix.wav`)에서 보컬을 분리해 `<clip_id>_vocals.wav`로 저장한다(CPU에서 20초에 1분 안팎).

    mix가 없으면 FileNotFoundError(먼저 cut_clip). vocals가 이미 있으면 overwrite=True가 아닌 한 FileExistsError.
    돌려주는 값: dict(vocals, seconds, sr)
    """
    separate = separate or separate_vocals
    mix_path, voc_path = clip_paths(clip_id, work_dir)
    if not mix_path.exists():
        raise FileNotFoundError(f"자른 구간이 없습니다: {mix_path.name} (먼저 cut_clip으로 자르세요)")
    if voc_path.exists() and not overwrite:
        raise FileExistsError(f"이미 분리한 구간입니다: {clip_id} (다시 하려면 overwrite=True)")
    x, sr, _ = audio.load_raw(mix_path)                                  # (샘플, 채널) float32
    if sr != MODEL_SR or x.shape[1] != 2:
        raise ValueError(f"{mix_path.name}은 {MODEL_SR} Hz 스테레오여야 합니다(cut_clip이 만든 파일).")
    t0 = time.time()
    vocals = separate(np.ascontiguousarray(x.T, dtype=np.float32))
    seconds = time.time() - t0
    recorder.save_wav(voc_path, vocals.T, MODEL_SR, overwrite=True)
    return {"vocals": voc_path, "seconds": seconds, "sr": MODEL_SR}


def process_clip(song_path, start, duration, clip_id, work_dir=WORK_DIR, separate=None, overwrite=False):
    """자르기와 분리를 한 번에 한다(cut_clip + separate_clip). 돌려주는 값: dict(mix, vocals, seconds, sr).

    이미 있는 clip_id는 overwrite=True가 아니면 FileExistsError(실수로 지우지 않으려는 안전장치).
    구간을 먼저 듣고 확인하려면 cut_clip → (듣기) → separate_clip 순서로 따로 부르는 것이 낫다."""
    mix_path, voc_path = clip_paths(clip_id, work_dir)
    if (mix_path.exists() or voc_path.exists()) and not overwrite:
        raise FileExistsError(f"이미 있는 구간입니다: {clip_id} (덮어쓰려면 overwrite=True)")
    cut = cut_clip(song_path, start, duration, clip_id, work_dir, overwrite=True)
    sep = separate_clip(clip_id, work_dir, separate=separate, overwrite=True)
    return {"mix": cut["mix"], "vocals": sep["vocals"], "seconds": sep["seconds"], "sr": sep["sr"]}


def _append_manifest(path, clip_id, song_file, start, duration):
    """clips.csv에 한 줄 추가(없으면 머리글부터 만든다). 같은 clip_id 줄이 있으면 새 값으로 바꾼다."""
    rows = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["clip_id"] != clip_id]
    rows.append({"clip_id": clip_id, "song_file": song_file, "start": start, "duration": duration})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["clip_id", "song_file", "start", "duration"])
        w.writeheader()
        w.writerows(rows)
