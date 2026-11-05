전에 프로젝트 주제 brainstorming 하다가 sound ➡️ visual art 같은 아이디어도 있었잖아. 현재 프로젝트에 적용해볼 수 있을까? 그냥 막연히 생각난 건, 소리 데이터에 대해 감정 분석이나 키워드 분석 등(수업 내용 중 딥러닝? 예측?) 적용해서 시각적으로 표현해보는 것..? 학습 시, 또는 history 메뉴에서, 내가 따라읽은 녹음 파일을 재생하면 내용이나 분위기에 맞게 캐릭터가 움직이는 것(표정이나 몸짓, 이동 등) 보여주기 = 작게나마 학습 동기나 즐거움 제공? => [현재 서울 날짜 및 시각 2026-11-05 13:54:00]

이 아이디어는 SongLingo에 적용할 가치가 충분해. 단순히 예쁜 캐릭터를 추가하는 것보다, 사용자의 목소리를 시각적 움직임으로 변환하고, 학습 과정을 작은 공연처럼 경험하게 만드는 기능으로 설계하면 좋겠어.

특히 현재 프로젝트에는 이 기능을 시작하기 위한 기반이 이미 있어. 새로운 딥러닝 모델부터 도입할 필요는 없어.

내가 제안하는 기능의 이름은 일단 Voice-to-Visual이야.

## 1. 우선, 세 가지 종류의 데이터를 구분하자

네가 생각한 감정 분석, 키워드 분석, 캐릭터 애니메이션은 사실 서로 다른 분석 작업이야.

A. Acoustic Analysis — 소리 자체 분석

실제로 사용자가 녹음한 목소리에서 추출하는 정보

- 음량과 에너지 변화
- 음높이(Pitch, F0)와 음높이 변화
- 발화 속도와 리듬
- 쉼(pause), 발화 구간

  캐릭터 움직임의 주요 입력

B. Semantic Analysis — 언어 내용 분석

ASR로 변환한 텍스트에서 추출하는 정보

- 핵심 키워드
- 문장 주제와 분위기
- 긍정·부정 감성
- 문장에 담긴 의미

  배경과 캐릭터의 표정·소품에 활용

C. Learning Analysis — 학습 결과 분석

기존 SongLingo의 학습 결과

- WER / CER
- 발화 완료 여부
- 반복 연습에 따른 오류율 변화
- 기준 발음과의 차이

  성취도 및 보상 애니메이션에 활용

이 세 가지를 구분하는 이유가 중요해.

예를 들어 사용자가 슬픈 내용의 가사를 읽었다고 해서 목소리도 반드시 슬프게 들리는 것은 아니야. 반대로 희망적인 가사를 무표정하고 낮은 목소리로 읽을 수도 있지.

따라서 다음처럼 접근하는 게 정확해.

- 텍스트 분석: 가사가 어떤 주제와 분위기를 담고 있는지 분석
- 소리 분석: 사용자가 실제로 어떤 음량·음높이·속도·리듬으로 읽었는지 분석
- 학습 분석: 문장을 얼마나 정확하게 읽었는지 분석

이 결과를 조합해서 캐릭터의 움직임과 주변 환경을 결정하는 거야.

## 2. 놀랍게도 현재 SongLingo에 이미 기반 기술이 있어

현재 GitHub 저장소의 코드를 확인해 봤어.

관련 모듈은 다음과 같아.

| 기존 모듈            | 이미 구현된 기능                    | 새로운 기능에 활용할 부분 |
| -------------------- | ----------------------------------- | ------------------------- |
| `visualisation.py`   | STFT, Mel Filter, Log-Mel           | 소리의 시간·주파수 분석   |
| `quality.py`         | RMS, Peak, Silence Ratio, 발화 시간 | 음량 및 발화 패턴         |
| `practice.py`        | 녹음 → STT → WER/CER                | 분석 파이프라인 연결      |
| `app/ui_practice.py` | 사용자 녹음 재생 및 TTS 재생        | 캐릭터 애니메이션 화면    |
| `practice_log.py`    | 연습 결과 기록                      | 시각화 결과와 기록 연결   |

특히 `visualisation.py`가 흥미로워.

현재 이 모듈은 이미 오디오 신호를 STFT 파워 스펙트로그램과 Log-Mel로 변환하고 있어.

[Introductory of Speech and Signal Processing | Lifelike Speech Synthesis | by Prim Wong | Super AI Engineer | Medium](https://images.openai.com/static-rsc-4/ObG2TeTeRj69RYhNHjxIFh8BWoWA3mZ6zbnsS0HCutJpB_gyTXPx0wzlvXgzGXEF3K8wuf-ecKfcSb7BJTsGBlZKGesCI8BLbptR9RByXAbhMzWSFzDdrVyNhHdQGqi8ZfJM104a_lC5wwLfh_GYq9kZn-5X9JD19ozCqUaB9S0?purpose=inline)

[Resonators: A Rust Port of the Resonate Algorithm | John Hartquist](https://images.openai.com/static-rsc-4/fbVVuuS1ojNzeybq53ervnyvp0XNecBIur-8G6mGaNYSf1V4mjCpYbTKWotXoJ881XI369u04I8nZQV5IbjDWK1v4-rElZgiRAIFKmBtCRnp_PVk2RE4S3I_NoqCVbixiQn_077cYzAZ1mv5Qe-MiwMmhmwjS_C3Cj7Sj4_DOUg?purpose=inline)

[Whisper Training: Weak Supervision & Multilingual ASR at Scale - Interactive | Michael Brenndoerfer | Michael Brenndoerfer](https://images.openai.com/static-rsc-4/xlrNbXqHLA8EskcZtDvO0HlPHiwNW8TYAfj1WlWMyD3fja4nGMQuXNmlfo47MUwssYR2iuOnlMDuNT5j_JefLk29dsbpBAUYkTkfyb4Xgls5cqDZZTQOOcqTJtTi5KgCBkGEeGtchSQSXlZYdQWBgBDYTaVfxn-CS6bCMOLdhHY?purpose=inline)

7

이것들은 단순한 그림이 아니야. 소리의 시간에 따른 변화를 수치로 표현한 데이터이기 때문에, 캐릭터의 움직임을 제어하는 데도 활용할 수 있어.

예를 들어 현재 `quality.py`에는 다음과 같은 정보가 있어.

- `rms_dbfs`: 평균적인 소리의 크기
- `peak`: 최대 진폭
- `silent_ratio`: 무음 프레임 비율
- `speech_seconds`: 소리가 있는 것으로 판단한 시간
- `low_freq_ratio`: 저주파 에너지 비율

다만 현재는 녹음 전체를 평가하는 요약값이 중심이야. 캐릭터를 실시간으로 움직이려면 시간에 따른 프레임별 값이 추가로 필요해.

참고 파일:

- [visualisation.py](https://github.com/greenkey20/song-lingo/blob/main/visualisation.py?utm_source=chatgpt.com)
- [quality.py](https://github.com/greenkey20/song-lingo/blob/main/quality.py?utm_source=chatgpt.com)
- [app/ui_practice.py](https://github.com/greenkey20/song-lingo/blob/main/app/ui_practice.py?utm_source=chatgpt.com)

즉, 지금까지 공부했던 STFT, Fourier Transform, Mel Spectrogram이 실제 사용자 인터페이스의 시각 효과로 연결되는 거야.

## 3. 캐릭터는 어떻게 움직일 수 있을까?

내가 가장 추천하는 방식은 Audio-reactive Character야.

오디오 데이터를 프레임 단위로 분석하고, 각 분석값을 캐릭터의 움직임에 연결하는 거지.

## Sound → Character Motion

[MascotCraft - AI-Powered Mascot Generation Platform](https://images.openai.com/static-rsc-4/vJzN_R2Jc0EO3hkW4J3xK-auFYRzYBq45M9KxwiQSnIoVOvXXx9HcLlPthBSebC5NiPIJF-0E5ampYFj-w8RKW02-S7rFDVbk4CWFrpViWI5cn-xxDW1u9wU3DoaN5XBQyvQWbKcQEPLtpdAowQoJL16CQ2C5yoCNfYxGI2FE8o?purpose=inline)

음량(RMS Energy)

소리가 커질수록 캐릭터의 점프 높이와 움직임 크기를 증가시켜.

Bounce

[Cartoon Illustration Of Cute Rabbit](https://images.openai.com/static-rsc-4/__nkBULe2_T7pVfV6Q-a34_wi3Q12rfYL2H6yerPCtvdjD6ReUNzAKqrbJof5yLB07M22ZpGhwkSz3DojOEI4nopCOD46zcXnwbYGaHkTftWqIXsrEpyO8L4i6wa8c-rQ_vZM5PHaevyPB34ucxZ1CzS0HPjvFLz7x_3PQh3LAjgiLl0Oi5Tx7b34rEdlaTB?purpose=inline)

음높이(Pitch / F0)

음높이가 높아지면 귀나 더듬이가 올라가고, 낮아지면 편안한 자세를 취해.

Ear movement

[Cute cartoon bunny rabbit sitting. Farm animals. Vector illustration of a smiling bunny](https://images.openai.com/static-rsc-4/9r_mVlh8urqyO8R6r1seRPikyvXoeWrHLdGA5zNqe8wnjuOwc9t5qSfOznBzBrE9MjuIddDUNBfLQUpLIIMtc_8unuLYagSE2tBXei3LpKb0gQUfQ6GdRNrePSmDqqR3h2h9b5SXRE4XVuPA066iaqsUgl1E1wWkQ2uej1qXgLHrmkzN0Mdag3T7YdnNFpkr?purpose=inline)

무음 및 쉼(Pause)

사용자가 말하지 않을 때는 귀를 기울이거나 눈을 깜박이는 동작을 보여줘.

Listening

[Green Bun Sticker pack - Stickers Cloud](https://images.openai.com/static-rsc-4/iI7EBLYLr9PoTYwhcZV7sDEtYMTPBcifFlvmNxNeaAWL3NGNDfQfvXkg98uzEBXdmZg-Is-i90xcovleuDtTFnbvHM5SA0is3Ieq07jfeiskhncxrfgajy3AbUH0WhogD11-mJLjR7yYhij7wWdVc8pJiFYhluIsOEaf_lCsPAI?purpose=inline)

문장 완료 및 학습 성취

문장을 끝까지 읽거나 이전보다 오류율이 개선되면 축하하는 동작을 보여줘.

Celebration

여기서 한 가지 구분해야 할 점이 있어.

캐릭터가 음량이 커졌다고 해서 사용자가 기뻐한다고 판정해서는 안 돼. 큰 소리는 단순히 마이크에 가까이 말했거나 강하게 발음한 결과일 수도 있어.

따라서 처음에는 감정 판정 대신 소리의 물리적 특징을 시각적으로 번역하는 것이 좋아.

### 실제 학습에서는 어떻게 보일까?

예를 들어 사용자가 다음 문장을 연습한다고 해보자.

`I will find my way home.`

1. 문장을 읽기 시작하면 캐릭터가 고개를 들고 귀를 세워.
2. 목소리가 입력되면 음량 변화에 맞춰 몸이 움직여.
3. 문장 중간에 쉼이 생기면 잠시 기다리는 자세를 취해.
4. 문장을 끝까지 읽으면 작은 점프를 해.
5. STT와 WER/CER 결과가 나오면 결과에 따라 작은 보상 효과가 나타나.

단순히 점수가 높을 때만 캐릭터가 기뻐하도록 만들지는 않았으면 해. 아직 발음이 정확하지 않더라도 연습을 완료했다는 사실 자체를 긍정적으로 표현하는 게 학습 동기 측면에서 더 나을 거야.

## 4. 그렇다면 감정 분석이나 키워드 분석에 딥러닝을 적용할 수 있을까?

가능해. 다만 분석하려는 데이터에 따라 접근법이 달라져.

| 분석             | 입력         | 기술                       | 딥러닝 필요성 |
| ---------------- | ------------ | -------------------------- | ------------- |
| 음량·음높이·리듬 | Audio        | DSP, STFT, F0 estimation   | 낮음          |
| 키워드 추출      | ASR Text     | NLP, KeyBERT 등            | 선택적        |
| 문장 감성 분석   | ASR Text     | 감성 분류 모델             | 중간          |
| 목소리 감정 분류 | Speech Audio | Speech Emotion Recognition | 높음          |
| 음악 분위기 분석 | Music Audio  | Music Emotion Recognition  | 높음          |

### ① 키워드 분석

이건 오디오 자체가 아니라 Whisper가 인식한 가사 텍스트를 분석하면 돼.

예를 들어:

| 가사에 등장하는 표현      | 분석 가능한 주제 |
| ------------------------- | ---------------- |
| stars, moon, sky          | 우주, 자연       |
| home, memories, yesterday | 추억, 일상       |
| dream, future, tomorrow   | 희망, 미래       |
| lonely, tears, goodbye    | 이별, 외로움     |

KeyBERT 같은 방법으로 핵심 단어를 추출하거나, 다국어 임베딩 모델을 활용해 문장 주제를 분류할 수 있어.

결과를 캐릭터의 배경이나 소품에 활용하면 재미있겠지.

[Sunny Bunnies Plush Toys Cute PNG Images | PSD Free Download - Pikbest](https://images.openai.com/static-rsc-4/2Emd0Y20IkXm0QG26qUS0sQrsPtl3tisoW23d-uJIvNl39DvvkZ8RQnXl7gGQ8vyELkNuCIXzt6Sls-xFZZ7MVr3uEiztr6N3vlHV5mFSL0PECerSKGq9b3ULdQZn6Vfkt8Q73TkUcx2SB41iWaZeTkYQ9U_KGMT_RUmumkQp0I?purpose=inline)

우주·꿈

별, 달, 미래

[Petit Lapin - Émission - Apple Podcasts](https://images.openai.com/static-rsc-4/AcARVEkEZ-tyPVqycVFu7hNCT9u1Dli7aMsKeC9rvBkYBSuCdaZJWuNKhmg6jGtY_drERhKfQp5NTwTQzsDgeB-TXgJAXw80JKVPEWcK9KqTJmqghi59UulAmx06u2b1AayU89IQ3GqphdrKc41o-nYkThX0ybkLwxQBim5PHWM?purpose=inline)

추억·그리움

기억, 이별, 과거

[Meet the Magical Forest Rabbit](https://images.openai.com/static-rsc-4/rTQ39KtZLXSEK5elCIFtfU55Pfy7lB33J-jxRGF0MTFh9hN7BCiuV0lvasyYKyKF9bPJ9bUiA4vPpKwPJdS6YZWry07RHidEjDyaKh3DyS6zS8PbnTk-NH3lyhR8s2SCeOqXX7Mv-ZlMXmy0LBpF-wmdnoD0L10f3Zj31zrgOMg?purpose=inline)

자연·여행

숲, 바다, 길

[AI Generated Rabbit Photos and Artwork | Deep Dream Generator](https://images.openai.com/static-rsc-4/xRwaJaOTAoyu7LUFhrUw6olL_Z5A3MqqCLFCkDpzw66Fd0qetyyU0NHqnf50XB_I2GlTwDoyxtHl6Nt3aZ6amWRDbweamhJIwqhd1g19dOq-Yi9523bv6T_j5a48nJ4LC8T6ejT8BflJOjrLuCsW7dVk7L56xEkLoOecucBei-I?purpose=inline)

희망·성장

꿈, 시작, 내일

이 기능은 가사의 내용을 분석해서 캐릭터 주변의 시각적 세계를 바꾸는 것이야.

### ② 목소리 감정 분석

이건 Speech Emotion Recognition(SER)이라는 분야야.

Wav2Vec2 같은 사전학습 모델을 기반으로 감정 분류 모델을 만들 수 있어. 예를 들어 `happy`, `sad`, `angry`, `neutral` 같은 분류 결과와 각 클래스의 확률을 얻는 방식이지.

다만 주의해야 할 부분이 있어.

음성 감정 분류 모델 중에는 일반적인 말하기 데이터를 대상으로 학습된 모델이 많아. 예를 들어 CREMA-D로 학습한 공개 Wav2Vec2 모델도 비음성 오디오나 음악은 적용 범위 밖이라고 명시하고 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://huggingface.co\&sz=32)

Hugging Face



그리고 음악 자체의 감정 분석인 Music Emotion Recognition(MER)은 별도의 연구 분야야. 2025년 발표된 관련 연구 리뷰에서도 데이터셋의 주관성, 평가 기준의 표준화, 감정 라벨의 일관성 등이 중요한 과제로 제시돼.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://repository.sutd.edu.sg\&sz=32)

Singapore University of Technology and Design+1



따라서 원곡의 분위기를 분석할 때와 사용자가 따라 읽는 목소리를 분석할 때는 서로 다른 모델과 평가 기준이 필요해.

내 생각에는 SER을 초기에 도입할 필요는 없어. 실제 목소리의 음량·음높이·속도만으로도 충분히 풍부한 애니메이션을 만들 수 있어.

### ③ 음향 특징 추출 라이브러리

현재 프로젝트에는 librosa가 requirements에 포함되어 있지 않지만, 향후 도입을 검토할 수 있어.

librosa는 음악과 음성 신호에서 다양한 특징을 계산해.

| 특징              | 의미                | 활용 아이디어      |
| ----------------- | ------------------- | ------------------ |
| RMS               | 프레임별 에너지     | 점프 크기          |
| Spectral Centroid | 스펙트럼의 무게중심 | 시각 효과의 밝기   |
| MFCC              | 음색 관련 특징      | 소리의 패턴 표현   |
| Tempo             | 박자 속도 추정      | 캐릭터 움직임 속도 |
| Chroma            | 음높이 계열 에너지  | 음악적 색상 변화   |

공식 문서: [librosa Feature Extraction](https://librosa.org/doc/latest/feature.html?utm_source=chatgpt.com)&#x20;

[image](https://www.google.com/s2/favicons?domain=https://librosa.org\&sz=32)

librosa 0.11.0 documentation



이 중에서도 현재 SongLingo에는 RMS와 F0, pause 정도부터 적용하는 게 적절해. Tempo나 Chroma는 반주가 섞인 원곡을 분석할 때 더 유용할 수 있어.

## 5. 가장 중요한 구현 문제: 오디오와 애니메이션을 어떻게 동기화할까?

여기서는 현재 Streamlit 구조를 고려해야 해.

현재 `app/ui_practice.py`는 `st.audio()`로 사용자 녹음과 TTS 파일을 재생하고 있어. 하지만 Python 쪽에서 브라우저의 오디오 재생 위치를 계속 추적하며 별도 캐릭터를 움직이는 건 기본 위젯만으로는 쉽지 않아.

따라서 두 단계로 나누자.

1단계: 재생 후 결과를 시각화

구현 난이도가 낮은 시작점

[Equalizer illustration.](https://images.openai.com/static-rsc-4/SlDreB7YyVaFAOpXuG-fJW-smSWHzx9QWrK8abrUuBb9igbjPrnKrV4Rcfw6myWt7LzL6DmGP4D9V8B3WwmaBUlam7eqqYBgyLs2XYR5qsy1ZZauruYSvA3caQ8Hm7FP0zm83YWNKNaqnrpFy9l8qa-YWMCLTku02bkQkVIiwZn3yrFtywOlevlY_PlfTi4y?purpose=inline)

사용자의 녹음이 끝나면 오디오 특징을 계산해서 음향 그래프와 캐릭터의 대표 동작을 보여줘. 실제 재생 위치와 완벽하게 동기화되지는 않지만 기능 검증이 가능해.

2단계: 재생과 동시에 캐릭터 애니메이션

완성된 경험을 위한 프런트엔드 확장

[Vídeo para GIF — MP4, MOV & WebM | PixMind](https://images.openai.com/static-rsc-4/KJtnYTaNhw-AU49ZBonZqceqfO4_4DgbfvvGPNvb5IGQiLpN_UXMKuguJWxPHLkObJeoB0NgJplKRNA1g9o2ThcrHw4LqJButZmjKuQ1GNl0RxMFnky86UVMjuZPwXo3PSKeKXNYn-1dEJBGjrFvkgwvYSl91-wVD4uzbhcz3HU?purpose=inline)

[pixmind.io](https://www.pixmind.io/pt/video-to-gif?utm_source=chatgpt.com)

하나의 커스텀 컴포넌트 안에 오디오 플레이어와 캐릭터 애니메이션을 함께 배치해. JavaScript의 `requestAnimationFrame()`으로 오디오 재생 위치를 읽고, 그 시점에 해당하는 특징값에 맞춰 캐릭터를 움직이는 구조야.

예를 들어 Python이 미리 분석한 값을 다음처럼 전달할 수 있어.

```
{
  "duration": 4.2,
  "frames": [
    {"time": 0.0, "energy": 0.12, "pitch": 180, "state": "listen"},
    {"time": 0.1, "energy": 0.24, "pitch": 185, "state": "speak"},
    {"time": 0.2, "energy": 0.38, "pitch": 205, "state": "speak"},
    {"time": 0.3, "energy": 0.08, "pitch": null, "state": "pause"}
  ]
}
```

이런 배열을 캐릭터 애니메이션 컴포넌트에 전달하는 거야.

실제 구현에서는 모든 프레임의 데이터를 다 전달하기보다는 10\~20Hz 정도로 특징값을 샘플링하고 보간하는 방법부터 시도해도 충분해.

캐릭터의 실제 움직임은 CSS animation, SVG, Lottie 또는 Rive 같은 도구로 구현할 수 있어. 초기에는 정적인 캐릭터 이미지를 여러 자세로 준비해 상태별로 전환하는 것만으로도 가능해.

## 6. History 메뉴에서는 한 단계 더 발전시킬 수 있어

여기서는 현재 구현 상태를 먼저 짚어야 해.

현재 `practice_log.py`는 연습 문장 원문과 인식 결과를 저장하지 않고, 해시 키와 WER/CER 등의 숫자 지표만 기록해.

또한 녹음 파일도 영구 저장하지 않아. `app/ui_practice.py`에서 `st.audio(rec)`로 보여주는 것은 현재 세션에 녹음 객체가 남아 있을 때뿐이야.

따라서 History에서 녹음 파일을 다시 재생하려면 별도의 저장 기능이 필요해.

내가 제안하는 기록 구조는 다음과 같아.

| 저장 데이터   | 저장 여부          | 이유                    |
| ------------- | ------------------ | ----------------------- |
| 녹음 파일     | 선택적 저장        | 나중에 재생하려면 필요  |
| 음향 특징값   | 저장 추천          | 캐릭터 움직임 재현      |
| WER/CER       | 기존 방식 유지     | 학습 기록               |
| 가사 원문     | 저장하지 않는 방향 | 저작권 및 개인정보 고려 |
| 인식된 텍스트 | 저장하지 않는 방향 | 기존 설계 원칙 유지     |
| 캐릭터 테마   | 저장 가능          | 당시 시각 효과 재현     |

그리고 History에 이런 내용을 보여주는 거야.

[Building a Tamagotchi-Style Language Learning iOS App - The Whole App is a Blob](https://images.openai.com/static-rsc-4/ekH0sbsRl-dzCszWj9gVM8iZppH1YksI5PKgTmgHrwcYTXWI2t-0cpHzposViZU7vTJCoIafzUm4GmtvITCJYD-0OSSe8TQCEwP-PRZRQlJ1aS6fns73AQMgxulIzoAOlm7Oh1O10PBWDDODX_V6fsTQ0rJ3__5QT9lqGYKYycU?purpose=inline)

[drobinin.com](https://drobinin.com/posts/the-whole-app-is-a-blob/?utm_source=chatgpt.com)

My Voice Journal

- 11월 5일 · 14:20
- 문장 연습 완료
- WER: 12%
- 이전 기록 대비 오류율 감소
- 녹음 재생
- 나의 목소리 움직임 다시 보기

이렇게 하면 History가 단순히 과거 점수를 보는 곳이 아니라, 나의 목소리와 학습 과정을 시각적으로 되돌아보는 공간이 될 수 있어.

단, 현재 개인 로컬 실행을 전제로 하는 CSV 기록과 달리 여러 사용자가 접속하는 배포 환경에서는 사용자별 저장소와 접근 제어가 필요해. 원본 음성을 보관할 때는 보관 기간과 삭제 기능도 설계해야 해.

## 7. 내가 추천하는 개발 로드맵

모든 기능을 한꺼번에 개발하지 말고 다음 순서로 확장하는 게 좋아.

Phase 1 · Sound Reactive Character

먼저 구현

[KBS RADIO KONG 캐릭터 리뉴얼 :: Behance](https://images.openai.com/static-rsc-4/YwyUPeR60M-DZvNQllnSaotmar9IEuHWiwGk1-c3xfMx2uNFmj6Dhrz9yJx8xQjNUs6ts1Z0WqG5c5IJfe7d42AQAFBn3eTe-3Rqu-oK2XLT_0svLQFJDXUQuHoCiICj9nsoPPB04rsqcncvGVd9Z_c-qBxeF5Kkz-LBNWJCycU?purpose=inline)

[behance.net](https://www.behance.net/gallery/226538181/KBS-RADIO-KONG-?utm_source=chatgpt.com)

기존 `quality.py`와 `visualisation.py`를 활용해서 RMS와 pause에 따른 캐릭터 동작을 구현해.

- 새 딥러닝 모델 불필요
- 프레임별 음향 특징 추출
- 캐릭터의 3\~4가지 기본 자세 전환

  Phase 2 · Voice Visualization

  [最佳音乐可视化工具 | 免费创建震撼的音乐视觉效果](https://images.openai.com/static-rsc-4/xa6GyGkOMPiRv_jzyeyGduuGtvCfQ4hoFqh1ES5P7Fz1mgR3PASTA9iTteDPjkQTyS2HUkJsv8NU-sOwXvr8FjqCokPQsYiXI7uV1mDphQiJBZZknGDlNhyKjfr-5weEDYH4LbZZWJTgUj9PN2tgMqJ3ZwWQeYs3vS77ZjQAbQY?purpose=inline)

  [musiccreator.ai](https://www.musiccreator.ai/zh/music-visualizer?utm_source=chatgpt.com)

  F0, 음높이 변화, 발화 속도를 분석해 파형이나 스펙트로그램을 시각화하고 캐릭터 움직임을 다양화해.
- F0 추정
- 시계열 특징 데이터
- 재생 위치와 애니메이션 동기화

  Phase 3 · Semantic Art

  [The Little Lost Star | Story.com](https://images.openai.com/static-rsc-4/lb6hvHKOWHr3kARIybqvX_FUvn5cIMOY-0614gTe90xqZg1Zjgv3CJwACgbeQVDvpNyJSUsMB50NAYdscTXCaQV8azHjIknJCVggvhbsHrIYHCAgk82ExRiM1n0e19n1HgdVDz-9-3OGR0RiZK1DuwBqIBKtKH56_ow6hl_EZOI?purpose=inline)

  [story.com](https://www.story.com/ai-stories/ai-childrens-stories/the-little-lost-star-17?utm_source=chatgpt.com)

  가사 텍스트에서 키워드와 주제를 추출해 주변 환경을 변경해.
- 다국어 키워드 분석
- 감성 및 주제 분류
- 배경·소품 자동 선택

  Phase 4 · Intelligent Feedback

  [The Importance of Making Math Joyful, Rigorous, and Personalized | by McGraw Hill | Inspired Ideas | Medium](https://images.openai.com/static-rsc-4/Pp_8TPlimkTgF0TA4FcbQPRdiqIIS4ystJs_-KyoF2JtVPkj9TH-3LBXNwuH6xuoRuezzF5-MkU-TuEIS8Bev6WiCknBL12zETgk3dqRbtxpZDsvDxB4tAik_2csQvZMfcjvHgR6z7RPGtcBGy8mD98oAC1Tx2kf9mP-LEjdBmA?purpose=inline)

  [medium.com](https://medium.com/inspired-ideas-prek-12/the-importance-of-making-math-joyful-rigorous-and-personalized-6f8359c91776?utm_source=chatgpt.com)

  학습 결과와 음향 분석을 결합해 더 개인화된 피드백을 제공해.
- 반복 학습에 따른 변화
- 발화 속도·리듬 피드백
- 발음 및 학습 성취 기반 보상

## 8. 이 프로젝트에서 특히 의미 있는 점

나는 이 아이디어가 단순히 캐릭터를 움직이는 데서 끝나지 않았으면 해.

현재 SongLingo에는 이미 다음과 같은 기술이 연결되어 있어.

- STT: 음성을 텍스트로 변환
- TTS: 표준 발음을 음성으로 생성
- WER/CER: 발화 결과와 기준 문장의 차이 계산
- STFT/Log-Mel: 음향 신호의 시간·주파수 특성 분석
- 품질 분석: 녹음 상태 및 발화 구간 분석

여기에 Voice-to-Visual을 더하면 하나의 학습 경험으로 연결할 수 있어.

사용자의 목소리 → 수치 데이터 → 시각적 표현 → 학습 피드백

이 과정 자체가 네가 공부하고 있는 음성 AI, 신호처리, 딥러닝, 프런트엔드 시각화가 만나는 지점이기도 해.

내가 가장 먼저 구현할 것은 딥러닝 감정 분석 모델이 아니라, 기존 STFT에서 프레임별 에너지 곡선을 추출하고 그 값에 맞춰 작은 초록색 캐릭터가 움직이는 기능이야. 이렇게 시작하면 모델 학습 없이도 아이디어를 실제 서비스에 적용할 수 있고, 이후 어떤 딥러닝 분석이 실제로 필요한지도 실험을 통해 판단할 수 있어.

---
그런데 사용자 따라읽기 문장 단위로 하면 5초 정도만 되는 것 같은데, 이럴 때도 캐릭터 시각화가 의미있을까..? 차라리 ‘소리 실험실, 부트캠프 내용 응용’(+개인 관심사)으로써, 어차피 프로그램에 내 음악 파일(보통 3분 이상) 업로드 하니까, 그걸 음성학적으로 분석해보는 다양한 실험(기본 파형 그래프 등 시각화 + 파형이나 음색 감정 분석 및 시각화(art, 캐릭터 등)을 한 번 해보는 게 나으려나..? 즉, 사용자가 따라읽기 녹음한 문장들은 무척 짧은데, 이걸 의미있게 시각화할 수 있는 건지 고민이 되는 거야.. 물론 현재 “학습이력(history)” 메뉴에 사용자 녹음 speech vs clip TTS 시각화 비교하도록 ui 구성되어있지..?

참고로, 이런 artistic visualisation은 맨 마지막에 할일이야. 진짜진짜 시간 남으면.. => [현재 서울 날짜 및 시각 2026-11-05 15:06:00]

내 생각에는 네가 방금 제시한 방향이 더 좋아. 특히 5초 정도의 짧은 발화에 억지로 예술적인 캐릭터 애니메이션을 붙이기보다는, 3분 이상의 음악 파일을 활용해 별도의 '소리 실험실(Sound Lab)'을 만들어 보는 것이 프로젝트의 학습적 가치와 개인적인 관심사를 모두 살릴 수 있어.

그리고 네가 말한 것처럼 artistic visualization은 정말 마지막에 시간이 남으면 할 일로 두자. 지금은 핵심 학습 기능에 집중하는 게 맞아.

## 1. 먼저, 현재 History 메뉴의 구현 상태를 정확히 확인하자

현재 GitHub 저장소의 코드를 다시 확인했어. 여기서는 한 가지 정정할 부분이 있어.

현재 구현 상태

따라읽기 결과 화면

일부 구현됨

`app/ui_practice.py`에서 다음 두 음성을 재생할 수 있어.

- 표준 발음: TTS 음성
- 내 녹음: 사용자가 실제로 녹음한 음성

즉, 두 음성을 청각적으로 비교할 수는 있어. 하지만 파형이나 스펙트로그램 비교는 아직 연결되지 않았어.

History 메뉴

시각 비교 미연결

`app/views/history.py`에는 다음 기능이 있어.

- 문장별 WER 변화 그래프
- 최근 연습 결과 표
- CSV 다운로드

사용자 녹음과 TTS 음성을 다시 재생하거나 음향 특성을 비교하는 UI는 현재 없어.

음향 시각화 모듈

비교 함수 존재

`visualisation.py`에 이미 `plot_sound_pair()`가 있어.

두 음성을 나란히 놓고 다음 세 가지를 비교할 수 있어.

- Waveform
- STFT Spectrogram
- Log-Mel Spectrogram

관련 코드:

- [History 화면](https://github.com/greenkey20/song-lingo/blob/main/app/views/history.py?utm_source=chatgpt.com)
- [따라읽기 UI](https://github.com/greenkey20/song-lingo/blob/main/app/ui_practice.py?utm_source=chatgpt.com)
- [음향 시각화](https://github.com/greenkey20/song-lingo/blob/main/visualisation.py?utm_source=chatgpt.com)

즉, 현재는 비교할 음성도 있고, 시각화 함수도 있지만, 둘을 연결한 UI는 아직 없는 상태야.

이 점을 구분하는 게 중요해.

## 2. 5초짜리 발화도 시각화할 가치가 있을까?

있어. 다만 시각화의 목적을 구분해야 해.

현재 `visualisation.py`의 STFT 설정을 보면 다음과 같아.

| 설정            | 현재 값     |
| --------------- | ----------- |
| Sample Rate     | 16,000 Hz   |
| Frame Length    | 512 samples |
| Frame Duration  | 32 ms       |
| Hop Length      | 128 samples |
| Frame 이동 간격 | 8 ms        |

5초 녹음이라면 대략 622개의 시간 프레임이 생성돼.

즉, 5초가 짧다고 해서 시간에 따른 음향적 변화를 관찰할 수 없는 건 아니야.

[3.3. Spectrogram and the STFT — Introduction to Speech Processing](https://images.openai.com/static-rsc-4/iUlMArt50KDAlCgVSiZBs7Fp7n6gO_cRFvJz-tCgoVmPFEFrm3ba45sLw8GwmfkpUpE4xlqj0bZa3LZv89SEDJgrAlD1rweMng9pUL5lS1SmME28-UQRYDHK0B8biMT9TLfcoZRqVmT2F8DVih_es73IIUma1-S5B70YqCs0W_Q?purpose=inline)

Waveform

발화 시작·종료, 진폭 변화, 쉼 구간

[lydspektrograf – Store norske leksikon](https://images.openai.com/static-rsc-4/VXilE3fe5sC1vs93EQ5F3OPBkcGYMFKFuGwLgec7_AYhplh7uybqt0_dwaFUExqymNbt1fl-AaIKtkJ6D5WnCMJZq2PF_mITHXiXWL7jb6MhMM18ydO9VTSZgnCYWlzZe_V2xAgGbxVRte3-OQ5zi6VYg6SutwZOTmcX15xhPYs?purpose=inline)

Spectrogram

시간에 따른 주파수 구성 변화

[Multi-Label Emotion Recognition of Korean Speech Data Using Deep Fusion Models](https://images.openai.com/static-rsc-4/K8e2AjvopGfEuNyoop0xQ1Vaf_4qzRPJZSsUZMKmOFaizQAXTW-d4-wr8djUM2xkCsFpVSecoL6BIwQm7dFwHqRFouuJtdUCmgBfS2Jfq_z0BiJxcnY33hqQEdNV6uSQEzo3xc5e5SfE0cvaPAHs4tyZ2OsFC7ypdtjkAfv7eoA?purpose=inline)

Log-Mel

음성의 주파수 특징을 Mel 눈금으로 표현

[K. J. Kohler - Timing and communicative functions of pitch contours](https://images.openai.com/static-rsc-4/hXgVLXidowx67whTDhFqJeA6DkoY8-bGWOuFcP0H5PqpCG7vRoHw64NGY-R0xXPGhovrnzNg0Ze34oaaFDER51TtaCXpxELzc9yvayRN2DPVCjKZ96-975Z3lRsmDNo7H5wJkbFiuMflMNXZF1D6fN75hDMzFf9iTiSEzxNCM2w?purpose=inline)

Pitch Contour

시간에 따른 기본 주파수 F0 변화

따라서 5초 발화에서도 다음 비교는 충분히 의미가 있어.

- 표준 TTS와 내 음성의 파형 비교
- 발화 속도 및 쉼 구간 비교
- 음높이 변화 비교
- 스펙트로그램과 Log-Mel 비교

다만 이 그림들이 곧바로 발음의 정확도를 증명하는 것은 아니야. 화자별 음색, 음높이, 발화 속도 등이 다르기 때문이야.

현재 SongLingo의 WER/CER도 엄밀하게는 발음 자체를 평가하는 값이 아니라, STT 결과와 기준 문장의 텍스트 일치도를 측정하는 값이라는 점을 유지해야 해.

내 판단: 5초 발화에 시각화를 적용한다면 학습 피드백용으로 충분히 의미가 있어. 다만 복잡한 캐릭터 움직임보다는 사용자의 음성과 기준 TTS의 음향적 차이를 이해하는 데 초점을 두는 편이 낫겠어.

## 3. 3분짜리 음악 파일은 오히려 Sound Lab에 더 적합해

여기서는 프로젝트의 성격을 조금 확장할 수 있어.

지금 My Song에 업로드하는 음원은 학습 문장을 추출하기 위한 데이터야. 하지만 같은 음원으로 별도의 음향 실험도 할 수 있지.

이때는 5초짜리 사용자 발화와 달리 3분 이상의 연속적인 신호가 있다는 점이 중요해.

예를 들어 노래 하나에서 다음과 같은 실험을 할 수 있어.

### 실험 A. 시간에 따른 음향 에너지 변화

[Decoding The Mix - Uptown Funk - Mark Ronson ft. Bruno Mars](https://images.openai.com/static-rsc-4/5jeyMtxidJLM3bmL-FT2uDT8sov5SYF_eDtFxQ-mhy0N8HDv9aOqGCGPXZmXft-VgbWDhhPbXU9KMZonDaSXezpAl-hlrtP4wc59p5au3zHQBXIqU78ae-OZHCSkuCJa9MybBbtc00jSIYxY4KBJm9gEy3EF1DdTItD8hz-fjM8?purpose=inline)

[masteringthemix.com](https://www.masteringthemix.com/blogs/learn/decoding-the-mix-uptown-funk-mark-ronson-ft-bruno-mars?utm_source=chatgpt.com)

음악 전체의 Waveform과 RMS Energy를 시각화하는 거야.

관찰할 수 있는 것:

- 음악의 시작과 종료
- 조용한 구간과 강한 구간
- Verse와 Chorus에서 나타나는 에너지 차이
- 음악의 전반적인 Dynamic Range

이미 `web_song.py`와 `visualisation.py`에 전체 곡의 파형 개요를 표시하는 기능이 있으므로 여기서 출발하면 돼.

### 실험 B. 주파수 구성과 음색 분석

[Untitled_02/데이먼스 이어(Damons year) - 벅스](https://images.openai.com/static-rsc-4/nCM2amqxt4hf2lCzBibnd3IHJsx_FsS5F_yZ7UP1qKb7Ab8I_st9F2dWtIvsqvKNGBeD9xQFI0z26UJM2Gar67JiniLvaRtuOd-8oOzC91itN9IKbLgfcWjTQ1H9497z37Fwz9XJeV1MfifcQabkUGmDMsVcmhlUkUzfG4PE8R0?purpose=inline)

[music.bugs.co.kr](https://music.bugs.co.kr/track/32677271?wl_ref=list_tr_08_tr\&utm_source=chatgpt.com)

STFT와 Log-Mel을 활용해서 전체 곡의 주파수 패턴을 보는 거야.

여기에 Spectral Centroid, Spectral Bandwidth, Spectral Rolloff 등을 추가하면 음색의 변화를 더 다양하게 관찰할 수 있어.

예를 들어:

- Centroid가 높아지는 구간: 스펙트럼 에너지 중심이 높은 주파수 쪽에 있음
- Bandwidth가 넓어지는 구간: 에너지가 더 넓은 주파수 범위에 분포
- Rolloff 변화: 특정 누적 에너지 비율에 해당하는 주파수 위치가 변함

이런 값을 음악 전체의 시간축에 배치하면 곡의 변화가 시각적으로 드러나.

### 실험 C. 음악의 음높이와 리듬

[(PDF) librosa: Audio and Music Signal Analysis in Python](https://images.openai.com/static-rsc-4/BTE4cb30_GHk525QTvOgkGfkLTPkvSCIQ8EJtgldn2KUDBtFFbtlI3W0SvLuz3TLEUsAwg5wqykql4VTx_n-5O7R2VKdqcBTBes5Qi-6l77XrThntvG5bW4jIe_JyXVP6BeapArtXne9uh6h9XBu2ptHykoc4olH1akmI-TB8BI?purpose=inline)

[academia.edu](https://www.academia.edu/18862537/librosa_Audio_and_Music_Signal_Analysis_in_Python?utm_source=chatgpt.com)

여기서는 다음 분석이 가능해.

| 분석          | 의미                           |
| ------------- | ------------------------------ |
| F0 / Pitch    | 음높이의 변화                  |
| Tempo         | 음악의 빠르기 추정             |
| Beat Tracking | 박자 위치 추정                 |
| Chroma        | 12개 음높이 계열의 에너지 분포 |
| MFCC          | 음색을 표현하는 계수           |

예를 들어 후렴구에서 음높이가 상승하는 패턴이나, 특정 구간에서 악기 구성이 변하는 모습을 시각적으로 확인할 수 있어.

단, 원곡 전체는 보컬과 반주가 혼합된 신호이므로 분석 결과도 두 요소가 합쳐진 특성이야. 가수의 발성이나 발음만을 분석하려면 보컬 분리본을 별도로 분석하는 실험이 필요해.

그리고 이 작업은 엄밀히 말하면 음성학적 분석보다는 음악 신호 및 음향 특성 분석에 더 가까워. 음성학을 깊게 다루려면 모음의 포먼트, 자음의 조음 특성, 음소별 지속 시간 같은 별도 분석이 필요해.

## 4. 그러면 감정 분석은 어디에 적용할까?

나는 이 부분을 세 가지로 나눠 보고 싶어.

| 분석 대상     | 분석 내용            | 표현 방법        |
| ------------- | -------------------- | ---------------- |
| 음악 자체     | 음악의 분위기·감성   | 배경과 색상 변화 |
| 가사 텍스트   | 키워드·주제·감성     | 상징적 오브젝트  |
| 사용자의 발화 | 음량·Pitch·속도·리듬 | 캐릭터의 움직임  |

예를 들어 동일한 곡에 대해 다음과 같은 시각화가 가능해.

## A Song, Three Interpretations

[Best Music Visualizer | Create Stunning Music Visuals Free](https://images.openai.com/static-rsc-4/Gwc0GeR1ri4POjrUTykjOvpU6ukyCA0onK2C3vX1FF17rmmOxNN_1i-wMax8OnbHaTLdtrzXj0Cp7TE-o_-9SCnKKjFk9RrY6tw2H6B0SJ9NIIOrQWDQIQjKR48Nx9kATWZYg3SvnB2KC5e6HGHeD62_jKjUzlbagCIfFYM7bf8?purpose=inline)

[musiccreator.ai](https://www.musiccreator.ai/music-visualizer?utm_source=chatgpt.com)

음악 신호

강약과 주파수 변화에 따라 배경의 빛과 파동이 움직여.

[PNG Vintage illustration open book | Free PNG  - rawpixel](https://images.openai.com/static-rsc-4/LRC7YojJzDQbLAehQiomyx-E4huFnjVLuj0nzxj88xgPyhjUXceuMB3veAOmnAjzLAIdOpVg5kIe1ZuMvXnh_y_jOJxRz-77t5Dlq4_OmVk9n5dSwtrB2c9puqHapOnf2Am8Xb3qe42RhrONrTofKUByo9WUOHGhxb_PBa6QSAc?purpose=inline)

[rawpixel.com](https://www.rawpixel.com/image/13883582/png-vintage-illustration-open-book-publication-sketch-star?utm_source=chatgpt.com)

가사 의미

가사에서 우주, 꿈, 자연 등의 키워드가 나오면 관련 오브젝트가 등장해.

[絵本に音楽をつけたら、主人公を動かしたくなった話（『空飛ぶウサギと不思議な雲』)｜白虎](https://images.openai.com/static-rsc-4/ott9rnposvvZslHPeMJGUrDmIkzw3Ma4JM-ZGQjpjzGiRUtAV7VYtZ2x32o-TIHM9S-N-u-uD092ye5jq846EnqOJqdwXItZupNcVGnSrCVthbiLLaqaS-gd4-cqCHOPKDQ4PD8_LAKm96eSXLoXhvRwrHCBWP4gUx5auAAYJFw?purpose=inline)

[note.com](https://note.com/whitetigerz/n/n334360490865?utm_source=chatgpt.com)

사용자 발화

사용자의 발화 에너지와 Pitch에 맞춰 캐릭터가 움직여.

다만 이건 최종적인 artistic visualization의 구상이지, 지금 당장 구현할 기능은 아니야.

감정 분류 모델을 도입한다면 모델이 실제로 무엇을 학습했는지, 노래와 일반 음성 중 어느 데이터를 대상으로 하는지 확인해야 해. 가사 내용이 슬프다고 음악 자체도 슬프다고 단정할 수는 없고, 목소리의 음높이가 높다고 행복하다고 판정해서도 안 돼.

## 5. 내가 추천하는 최종 구조: 학습과 소리 실험을 분리

현재 SongLingo의 핵심 목적을 유지하면서 실험적 기능을 추가하려면 다음과 같이 구성하는 게 좋겠어.

# SongLingo

Listen · Practice · Explore

1\. Lyrics

가사를 입력하고 문장 단위로 듣기·따라읽기·받아쓰기 연습

2\. My Song

음악 파일 업로드 또는 주변 음악 녹음 → 가사 추출 → 문장 연습

3\. History

WER/CER 변화, 녹음 재생, TTS와 사용자 음성의 음향적 비교

4\. Sound Lab

Future / Optional

전체 음악 파일에 대한 음향 실험, 주파수 분석, 음악적 특징 추출 및 artistic visualization

이렇게 분리하면 핵심 기능과 실험 기능의 목적도 명확해져.

Lyrics / My Song / History는 언어 학습을 위한 메뉴이고, Sound Lab은 프로젝트에 적용된 음성 AI와 수업에서 배운 신호처리·딥러닝 지식을 탐구하는 메뉴인 거야.

## 6. 지금부터 무엇을 먼저 할까?

네가 말한 우선순위를 반영해서 개발 순서를 다시 정리하면 다음과 같아.

| 우선순위 | 기능                                      | 판단          |
| -------- | ----------------------------------------- | ------------- |
| P0       | 가사 입력, ASR, TTS, STT, WER/CER 안정화  | 필수          |
| P0       | 일본어·영어 혼합 가사 처리                | 핵심 개선     |
| P1       | History에서 학습 결과 및 기록 관리        | 필수          |
| P2       | 기존 `plot_sound_pair()`를 History에 연결 | 여유가 있으면 |
| P3       | 3분 음악 파일의 음향 특성 분석            | 선택적 실험   |
| P4       | 가사 감정·키워드 분석                     | 선택적 실험   |
| P5       | Sound-to-Art, 캐릭터 애니메이션           | 최후의 확장   |

내가 생각하는 가장 좋은 전략은 이거야.

현재의 5초 발화는 학습 결과를 비교하는 데 활용하고, 3분짜리 음악은 Sound Lab에서 탐구하는 데 활용하자.

그러면 5초 발화의 짧은 길이를 억지로 예술적으로 해석할 필요가 없어. 동시에 네가 부트캠프에서 학습한 STFT, Spectrogram, Log-Mel, 딥러닝 및 음성 AI 지식을 실제 프로젝트에서 실험해 볼 수 있어.

그리고 artistic visualization은 Sound Lab의 분석 결과를 가져다가 마지막에 표현 계층으로 얹으면 돼. 분석 기능과 시각적 표현을 분리해 두면 나중에 캐릭터 디자인이나 인터랙션을 바꾸더라도 음향 분석 코드는 그대로 재사용할 수 있어.