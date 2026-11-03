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

입력은 파일 경로만이 아니다(이슈 #37, 웹 화면의 업로드·브라우저 녹음용)
- 웹 화면은 녹음을 파일이 아니라 **bytes**로 받는다(Streamlit의 업로드·녹음 위젯은 `.read()`/`.getvalue()`가 되는 객체를 준다).
  그래서 읽는 함수(`load_raw`·`load_audio`·`decode`)는 경로(str·Path), `bytes`·`bytearray`, `io.BytesIO` 같은 파일 객체를 모두 받는다.
- [수업에 없음] `io.BytesIO`: 메모리 안의 bytes를 파일처럼 읽게 해 주는 표준 라이브러리 클래스. scipy와 PyAV 모두 파일 객체를 받는다.
- wav인지는 bytes 맨 앞의 `RIFF`·`WAVE` 표지로 판별한다(경로는 확장자로 판별). 표지가 없으면 PyAV가 형식을 스스로 알아낸다.
- 한 번 디코딩한 결과를 여러 곳에서 같이 쓰려면 `decode`를 쓴다(원본 파형은 quality, 16 kHz 모노는 STT·그림).
"""
import io
import os
import warnings
from math import gcd

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

TARGET_SR = 16000   # Whisper와 수업(lesson04)이 쓰는 표본화 주파수


def as_source(source):
    """읽을 대상을 둘 중 하나로 통일한다: 경로 문자열(str) 또는 처음부터 읽을 수 있는 io.BytesIO.

    받는 것: 경로(str·os.PathLike), bytes·bytearray·memoryview, 그리고 .read()가 되는 파일 객체(BytesIO, 웹 업로드 객체 등).
    파일 객체는 이미 한 번 읽혀 읽는 위치가 끝에 가 있을 수 있어서(위젯이 먼저 읽는 경우), `.getvalue()`가 있으면 그것으로 전체를,
    없으면 처음(seek(0))으로 돌아가 전체를 다시 읽는다. 원본 객체의 읽는 위치는 바꾸지 않으려고 항상 **복사본 BytesIO**를 돌려준다.
    그 밖의 타입은 TypeError."""
    if isinstance(source, (str, os.PathLike)):
        return str(source)
    if isinstance(source, (bytes, bytearray, memoryview)):
        return io.BytesIO(bytes(source))
    if hasattr(source, "getvalue"):
        return io.BytesIO(bytes(source.getvalue()))
    if hasattr(source, "read"):
        if hasattr(source, "seek"):
            source.seek(0)
        return io.BytesIO(source.read())
    raise TypeError(f"경로, bytes, 파일 객체(BytesIO 등)만 읽을 수 있습니다(받은 형식: {type(source).__name__}).")


def _is_wav_bytes(buf):
    """BytesIO가 wav인가? 맨 앞 12바이트가 'RIFF' + (크기 4바이트) + 'WAVE'이면 wav다. 읽는 위치는 원래대로 되돌린다."""
    head = buf.getvalue()[:12]
    return len(head) == 12 and head[:4] == b"RIFF" and head[8:12] == b"WAVE"


def _read_wav(path):
    """PCM16 wav(경로 또는 BytesIO) → (float32 파형 [-1, 1], 원본 sr, 원본 채널 수). 채널이 둘 이상이면 (샘플, 채널) 배열 그대로."""
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
    """wav 이외의 파일(경로 또는 BytesIO)을 PyAV로 디코딩 → (float32 파형 (샘플, 채널), 원본 sr, 원본 채널 수)."""
    import av   # 지연 import: wav만 쓸 때는 PyAV가 없어도 되게 한다.

    chunks = []
    with av.open(path) as container:     # 경로 문자열이든 BytesIO든 av.open이 받는다(as_source가 둘 중 하나로 맞춰 줌)
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


def load_raw(source):
    """녹음 → (원본 그대로의 float32 파형 (샘플, 채널), 원본 sr, 원본 채널 수). 모노로 섞거나 sr을 바꾸지 않는다.

    source: 파일 경로(str·Path), bytes·bytearray, 또는 파일 객체(io.BytesIO, 웹 업로드 객체). 위 as_source 참고.
    quality.py의 클리핑 검사처럼 '원본 샘플'이 필요할 때 쓴다. 리샘플링을 거치면 가장자리에 울림이 생겨
    (예: 최대 0.95인 소리가 1.0을 넘음) 원본에는 없던 클리핑이 있는 것처럼 보일 수 있기 때문이다.
    PCM16 wav는 scipy로, 그 밖의 형식(webm, mp4, m4a, mp3 …)은 PyAV로 읽는다.
    """
    src = as_source(source)
    is_wav = src.lower().endswith(".wav") if isinstance(src, str) else _is_wav_bytes(src)
    if is_wav:
        try:
            x, orig_sr, channels = _read_wav(src)
        except ValueError:                  # 24비트·float wav 등 scipy 경로가 못 읽는 wav는 PyAV로 넘긴다.
            if not isinstance(src, str):
                src.seek(0)                 # scipy가 읽다 만 BytesIO를 처음으로 되돌려 PyAV가 다시 읽게 한다
            x, orig_sr, channels = _decode_with_av(src)
    else:
        x, orig_sr, channels = _decode_with_av(src)
    if x.size == 0:
        raise ValueError("샘플이 없는 파일입니다.")
    if x.ndim == 1:
        x = x[:, None]                      # 항상 (샘플, 채널) 모양으로 맞춘다
    return x, orig_sr, channels


def to_16k_mono(x, orig_sr, sr=TARGET_SR):
    """(샘플, 채널) 또는 (샘플,) 파형 → sr(기본 16 kHz) 모노 float32. 스테레오는 채널 평균, 리샘플링은 resample_poly."""
    if x.ndim > 1:
        x = x.mean(axis=1)                  # 스테레오 → 모노: 채널 평균(수업과 같은 방식)
    if orig_sr != sr:
        # resample_poly(x, up, down): 길이를 up/down 배로 바꾼다. 48000 → 16000이면 up=1, down=3.
        # gcd(최대공약수)로 약분해서 44100 → 16000도 (160, 441)처럼 정수 비율로 나타낸다.
        g = gcd(sr, orig_sr)
        x = resample_poly(x, sr // g, orig_sr // g)
    return x.astype(np.float32)


def load_audio(source, sr=TARGET_SR):
    """녹음(경로·bytes·파일 객체) → (16 kHz 모노 float32 파형, 원본 sr, 원본 채널 수).

    파형 값은 대략 -1~1이다. 길이는 원본 길이 × (16000 / 원본 sr)에 가깝다.
    load_raw(읽기) + to_16k_mono(모노·리샘플링)를 이어 붙인 것이다.
    """
    x, orig_sr, channels = load_raw(source)
    return to_16k_mono(x, orig_sr, sr), orig_sr, channels


def decode(source, sr=TARGET_SR):
    """한 번만 디코딩해서 여러 곳이 같이 쓸 결과를 만든다(이슈 #37). 돌려주는 dict:
      raw      : 원본 파형 (샘플, 채널) — quality.analyze(raw, orig_sr)에 넣는다(클리핑은 원본 샘플로 재야 한다)
      orig_sr  : 원본 표본화 주파수
      channels : 원본 채널 수
      mono16k  : 16 kHz 모노 float32 파형 — stt.recognize에 그대로 넣거나(ndarray 입력), 스펙트로그램 그림에 쓴다
    웹 화면에서 bytes를 상태 점검·그림에 각각 따로 디코딩하면 같은 일을 여러 번 하게 되므로 이 함수로 한 번만 한다.
    **주의**: mono16k를 STT에 넣으면 경로로 넣은 것과 파형이 조금 달라 노래에서 인식문이 달라질 수 있다(stt.transcribe_input 참고).
    STT에는 원본(경로·bytes)을 그대로 넣는 것이 안전하고, mono16k는 그림과 우리 쪽 계산에 쓴다."""
    raw, orig_sr, channels = load_raw(source)
    return {"raw": raw, "orig_sr": orig_sr, "channels": channels, "mono16k": to_16k_mono(raw, orig_sr, sr)}
