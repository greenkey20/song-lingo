"""어떤 녹음 파일이든 '16 kHz 모노 float32 파형'으로 바꾼다(이슈 #6).

왜 필요한가
- Whisper와 스펙트로그램·녹음 상태 점검(quality.py)은 모두 같은 규격의 파형을 기대한다.
- 파일은 형식이 제각각이다: 온라인 레코더 wav(48 kHz), 브라우저 녹음 webm/opus(48 kHz)·mp4/aac(44.1 kHz), 스테레오 등.

수업과 같은 부분 / 다른 부분
- [수업과 같음] wav 읽기(scipy.io.wavfile) → 스테레오는 채널 평균으로 모노 → scipy.signal.resample_poly로 16 kHz
  (017_sound/lesson04 실습 4-D의 변환 순서). 그래서 wav는 practice.ipynb의 load_16k_mono와 같은 값이 나온다.
- [수업에 없음] wav가 아닌 형식(webm, mp4, m4a, mp3 …)은 PyAV(`av`)로 읽는다. PyAV는 faster-whisper가
  이미 설치해 둔 패키지라 새로 설치할 것이 없고, 내부적으로 ffmpeg 라이브러리를 품고 있다.
  (faster-whisper도 같은 방식으로 파일을 읽기 때문에 Whisper에는 변환 없이 파일을 줘도 된다. 이 모듈은
  Whisper가 아니라 '우리 코드가 직접 파형이 필요할 때'(그림, 상태 점검)를 위한 것이다.)
"""
import warnings
from math import gcd

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

TARGET_SR = 16000   # Whisper와 수업(lesson04)이 쓰는 표본화 주파수


def _read_wav(path):
    """PCM16 wav → (float32 파형 [-1, 1], 원본 sr, 원본 채널 수). 채널이 둘 이상이면 (샘플, 채널) 배열 그대로."""
    with warnings.catch_warnings():
        # 스트리밍으로 저장한 TTS wav는 헤더의 길이 값이 부정확해서 scipy가 경고를 낸다(내용은 정상).
        warnings.simplefilter("ignore", wavfile.WavFileWarning)
        sr, x = wavfile.read(path)
    if x.dtype != np.int16:
        raise ValueError(f"PCM16 wav만 직접 읽습니다(읽은 형식: {x.dtype}). 다른 형식이면 PyAV로 읽으세요.")
    channels = 1 if x.ndim == 1 else x.shape[1]
    # int16은 -32768~32767이므로 32768로 나누면 -1~1 범위가 된다(수업과 같은 정규화).
    return x.astype(np.float32) / 32768.0, int(sr), channels


def _decode_with_av(path):
    """wav 이외의 파일을 PyAV로 디코딩 → (float32 파형 (샘플, 채널), 원본 sr, 원본 채널 수)."""
    import av   # 지연 import: wav만 쓸 때는 PyAV가 없어도 되게 한다.

    chunks = []
    with av.open(str(path)) as container:
        if not container.streams.audio:
            raise ValueError("오디오 트랙이 없는 파일입니다.")
        stream = container.streams.audio[0]
        sr, channels = stream.rate, stream.channels
        # 디코더가 내놓는 샘플 형식은 코덱마다 다르다(opus는 float 평면형, aac는 float 평면형, mp3는 s16p 등).
        # 한 가지 형식('fltp' = float32, 채널별로 따로 저장)으로 통일하면 이후 처리가 같아진다.
        # 표본화 주파수와 채널 배치는 그대로 두고(layout=stream.layout, rate=sr) 숫자 형식만 바꾸는 설정이다.
        resampler = av.AudioResampler(format="fltp", layout=stream.layout, rate=sr)
        for frame in container.decode(stream):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray())   # 모양: (채널 수, 샘플 수)
        for out in resampler.resample(None):      # None을 주면 내부에 남은 샘플을 마저 내보낸다(flush)
            chunks.append(out.to_ndarray())
    if not chunks:
        raise ValueError("디코딩된 샘플이 없습니다(빈 파일이거나 손상된 파일).")
    x = np.concatenate(chunks, axis=1).T.astype(np.float32)   # (채널, 샘플) → (샘플, 채널)
    return x, int(sr), int(channels)


def load_audio(path, sr=TARGET_SR):
    """녹음 파일 → (16 kHz 모노 float32 파형, 원본 sr, 원본 채널 수).

    파형 값은 대략 -1~1이다. 길이는 원본 길이 × (16000 / 원본 sr)에 가깝다.
    PCM16 wav는 scipy로, 그 밖의 형식(webm, mp4, m4a, mp3 …)은 PyAV로 읽는다.
    """
    path = str(path)
    if path.lower().endswith(".wav"):
        try:
            x, orig_sr, channels = _read_wav(path)
        except ValueError:                  # 24비트·float wav 등 scipy 경로가 못 읽는 wav는 PyAV로 넘긴다.
            x, orig_sr, channels = _decode_with_av(path)
    else:
        x, orig_sr, channels = _decode_with_av(path)

    if x.size == 0:
        raise ValueError("샘플이 없는 파일입니다.")
    if x.ndim > 1:
        x = x.mean(axis=1)                  # 스테레오 → 모노: 채널 평균(수업과 같은 방식)
    if orig_sr != sr:
        # resample_poly(x, up, down): 길이를 up/down 배로 바꾼다. 48000 → 16000이면 up=1, down=3.
        # gcd(최대공약수)로 약분해서 44100 → 16000도 (160, 441)처럼 정수 비율로 나타낸다.
        g = gcd(sr, orig_sr)
        x = resample_poly(x, sr // g, orig_sr // g)
    return x.astype(np.float32), orig_sr, channels
