"""마이크 녹음 → 스테레오 PCM16 wav 저장 (윈도우 '녹음기'와 같은 형식). 이슈 #10의 30건 녹음과 이후 UI의 '따라 읽기'가 쓴다.

왜 필요한가
- 온라인 레코더는 파일 이름을 하나씩 바꿔야 했다. 이 모듈은 문장 번호와 회차로 `data/recordings/sNN_takeK.wav`를 직접 만든다.
- 형식은 수업 02 노트북의 `my_voice.wav`와 같다: 16비트 정수 PCM, 2채널(스테레오), 장치의 기본 표본화 주파수(44.1/48 kHz).
  뒤쪽 처리(`audio.load_audio`)가 스테레오 평균 → 16 kHz 모노로 바꾸므로 파이프라인은 그대로다.

구성 (UI가 바뀌어도 이 모듈은 그대로 쓰도록 '녹음'과 '화면'을 나눴다)
- 순수 함수: `recording_path`·`next_take`·`take_status`·`to_stereo_int16`·`save_wav` (마이크 없이 테스트 가능)
- `Recorder`: `start()` → (말하기) → `stop()`이 파형을 돌려주고, 파일 저장은 `save_wav`가 한다.
  Streamlit 버튼이든 터미널 Enter든 start/stop만 부르면 된다.
- 터미널 진행 도우미는 `scripts/record_takes.py`.

수업과의 관계
- [수업과 같음] 저장 형식(PCM16 wav, 스테레오), 읽을 때 ÷32768 정규화(02 노트북 `read_pcm16`), scipy.io.wavfile.
- [수업에 없음] `sounddevice`(마이크 입력 라이브러리; PortAudio를 감싼 것, pip 휠에 포함되어 macOS에서 따로 설치할 것이 없다).
  `InputStream`은 '마이크 소리가 들어올 때마다 callback을 불러 주는 통로'다. 녹음하는 동안 callback이 조각(block)을
  리스트에 쌓고, stop에서 이어 붙인다.
- macOS는 처음 녹음할 때 터미널(또는 VS Code)에 마이크 권한을 묻는다. 거부하면 무음이 녹음된다 → 권한 설정에서 허용.
"""
import re
import threading
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parent
RECORDINGS_DIR = ROOT / "data" / "recordings"
_TAKE_RE = re.compile(r"^s(\d+)_take(\d+)\.wav$")


# ---------- 파일 이름·상태 (마이크 없이 동작) ----------

def recording_path(sentence_id, take, root=RECORDINGS_DIR):
    """문장 번호·회차 → `<root>/sNN_takeK.wav` (번호는 두 자리, TTS 캐시 이름 s01.wav와 같은 규칙)."""
    return Path(root) / f"s{int(sentence_id):02d}_take{int(take)}.wav"


def existing_takes(sentence_id, root=RECORDINGS_DIR):
    """이미 있는 회차 번호 목록(오름차순). wav만 센다(`stt.find_recording`은 다른 확장자도 찾는다)."""
    takes = []
    for p in Path(root).glob(f"s{int(sentence_id):02d}_take*.wav"):
        m = _TAKE_RE.match(p.name)
        if m:
            takes.append(int(m.group(2)))
    return sorted(takes)


def next_take(sentence_id, root=RECORDINGS_DIR):
    """아직 없는 가장 작은 회차(1부터). take1·take3만 있으면 2를 돌려줘 빈칸을 먼저 채운다."""
    have = set(existing_takes(sentence_id, root))
    k = 1
    while k in have:
        k += 1
    return k


def take_status(sentence_ids, takes_per_sentence=3, root=RECORDINGS_DIR, order="round"):
    """진행 현황: {문장 번호: [있는 회차 …]}와 부족한 (문장, 회차) 목록을 돌려준다.

    order: 녹음 순서(검토 문서 13.3).
      "round"(기본)    — 1회전씩: 모든 문장의 1회차 → 2회차 → 3회차. 같은 문장을 연달아 읽어 직전 녹음을 흉내 내는 일을 줄인다.
      "sentence"       — 문장별: 한 문장을 3번 읽고 다음 문장.
    돌려주는 값: (have, missing). missing은 [(id, take), …] — 10문장×3회면 최대 30개."""
    if order not in ("round", "sentence"):
        raise ValueError(f"order는 'round' 또는 'sentence'입니다: {order!r}")
    have = {int(sid): existing_takes(sid, root) for sid in sentence_ids}
    takes = range(1, takes_per_sentence + 1)
    if order == "round":
        missing = [(sid, k) for k in takes for sid in have if k not in have[sid]]
    else:
        missing = [(sid, k) for sid in have for k in takes if k not in have[sid]]
    return have, missing


# ---------- 파형 → wav ----------

def to_stereo_int16(x):
    """float 파형(-1~1; 1차원 모노 또는 (샘플, 채널))을 (샘플, 2) int16으로 바꾼다.

    모노면 같은 값을 좌우에 복사한다(수업의 my_voice.wav도 좌우가 같았다). 채널이 둘 넘으면 앞의 둘만 쓴다.
    ×32767 후 반올림하고 범위를 잘라(clip) 정수 오버플로로 소리가 뒤집히는 일을 막는다."""
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return np.round(np.clip(x[:, :2], -1.0, 1.0) * 32767).astype(np.int16)


def save_wav(path, x, sr, overwrite=False):
    """파형을 스테레오 PCM16 wav로 저장하고 경로를 돌려준다. 폴더는 없으면 만든다.

    overwrite=False(기본)이면 이미 있는 파일을 덮어쓰지 않고 FileExistsError — 소중한 녹음을 실수로 지우지 않으려는 안전장치."""
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"이미 있는 파일입니다: {path.name} (다시 녹음하려면 overwrite=True)")
    path.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(path, int(sr), to_stereo_int16(x))
    return path


# ---------- 마이크 ----------

class Recorder:
    """마이크 녹음기. `start()` → `stop()` 한 쌍이 한 번의 녹음이다.

    sr: 표본화 주파수. None이면 입력 장치의 기본값(맥 내장 마이크는 보통 44100)을 쓴다 — 윈도우 녹음기처럼 장치 기본값 그대로.
    channels: 2(스테레오)가 기본. 장치가 1채널만 지원하면 1로 열고 저장할 때 좌우로 복사한다.
    device: 입력 장치 번호·이름. None이면 시스템 기본 입력.
    max_seconds: 깜빡하고 stop을 안 눌러도 이 시간이 지나면 더 쌓지 않는다(메모리 보호).
    sd: 테스트에서 가짜 sounddevice를 넣는 자리. 평소에는 None.
    """

    def __init__(self, sr=None, channels=2, device=None, max_seconds=60.0, sd=None):
        if sd is None:
            import sounddevice as sd      # 지연 import: 마이크를 안 쓰는 코드·테스트는 sounddevice 없이도 import 가능
        self._sd = sd
        info = sd.query_devices(device, "input")          # 장치 정보 dict (이름, 최대 입력 채널, 기본 sr …)
        self.device = device
        self.device_name = info["name"]
        self.sr = int(sr or info["default_samplerate"])
        self.channels = max(1, min(int(channels), int(info["max_input_channels"])))
        self.max_frames = int(max_seconds * self.sr)
        self._blocks, self._frames, self._stream = [], 0, None
        self._lock = threading.Lock()                     # callback은 다른 스레드에서 불리므로 리스트 접근을 잠근다

    @property
    def recording(self):
        return self._stream is not None

    @property
    def seconds(self):
        """지금까지 쌓인 길이(초). 화면에 '녹음 중 3.2초'를 보여 줄 때 쓴다."""
        return self._frames / self.sr

    def level(self, last_seconds=0.1):
        """최근 구간의 최대 진폭(0~1). 말하는 중 '소리가 들어오는지' 보여 주는 용도. 쌓인 게 없으면 0."""
        with self._lock:
            if not self._blocks:
                return 0.0
            tail = np.concatenate(self._blocks[-8:], axis=0)
        n = max(1, int(last_seconds * self.sr))
        return float(np.abs(tail[-n:]).max())

    def _callback(self, indata, frames, time_info, status):
        """마이크 조각이 도착할 때마다 호출된다. indata는 재사용되는 버퍼라서 반드시 복사해 둔다."""
        with self._lock:
            if self._frames < self.max_frames:
                self._blocks.append(indata.copy())
                self._frames += len(indata)

    def start(self):
        """녹음을 시작한다(이미 녹음 중이면 RuntimeError). 이전 녹음 내용은 버린다."""
        if self.recording:
            raise RuntimeError("이미 녹음 중입니다.")
        self._blocks, self._frames = [], 0
        # dtype="float32": 값이 -1~1 실수로 들어온다(저장할 때 int16으로 바꿈). 정수로 받아도 되지만 이후 계산이 같아진다.
        self._stream = self._sd.InputStream(samplerate=self.sr, channels=self.channels, dtype="float32",
                                            device=self.device, callback=self._callback)
        self._stream.start()

    def stop(self):
        """녹음을 멈추고 파형 (샘플, 채널) float32를 돌려준다. 녹음 중이 아니면 RuntimeError."""
        if not self.recording:
            raise RuntimeError("녹음 중이 아닙니다.")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        with self._lock:
            if not self._blocks:
                return np.zeros((0, self.channels), dtype=np.float32)
            return np.concatenate(self._blocks, axis=0)

    def play(self, x):
        """녹음한 파형을 스피커로 재생하고 끝날 때까지 기다린다(들어보고 다시 할지 정하는 용도)."""
        self._sd.play(np.asarray(x, dtype=np.float32), self.sr)
        self._sd.wait()
