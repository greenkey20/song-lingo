나 자신은 이 프로젝트로부터 무엇을 얻게 되는 걸까? 개인적으로 어떤 목표를 가져야 할까?

1. 내가 실제로 사용 가능한 유용한 프로그램 작성(실제로 듣는 노래가 무슨 언어인지, 무슨 뜻인지, 어떻게 쓰는지, 어떻게 읽는지, 알고 싶음)
2. 부트캠프, 특히 마지막 017 sound 챕터에서 배운 내용 복습, 활/적용 = 음성 데이터 처리 내재화(또는 직접 체험)
3. 등등? (이 목록을 너가 보완/완성해줘)

그런데 지금은 소스코드는 Claude code가 거의 다 작성해주고 있고, 나는 어떤 모듈이 언제, 어떤 내용으로 생기는지, 못 따라가고 있는데, 어떡하지..? 소스코드 구조 및 내용을 모르니까, 내가 무언가를 얻는다, 배운다, 향상한다는 느낌이 없어.. 그냥 딸깍 해서 기능을 만들어내는 느낌이야.. => [현재 서울 날짜 및 시각 2026-11-05 15:06:00]

내 생각에는 지금 네가 느끼는 고민이 이 프로젝트에서 상당히 중요한 전환점이야.

지금까지는 SongLingo에 어떤 기능을 추가할지 고민했다면, 이제는 SongLingo를 만드는 과정에서 내가 무엇을 이해하고, 무엇을 직접 할 수 있게 될 것인가를 고민해야 하는 단계에 온 거야.

그리고 한 가지는 분명히 짚고 싶어.

작동하는 프로그램을 완성하는 것과, 그 프로그램을 만드는 능력을 내 것으로 만드는 것은 서로 다른 일이야.

현재는 전자는 상당히 진척되고 있지만, 후자는 충분히 따라오지 못하고 있는 것 같아. 이 문제를 의식하기 시작한 지금이 개발 방식을 바꿀 적기야.

# 1. 이 프로젝트에서 얻어야 할 개인적인 목표

내가 네 상황이라면 SongLingo의 목표를 다음 여섯 가지로 정의하겠어.

# SongLingo: My Personal Goals

하나의 프로젝트를 통해 얻고 싶은 여섯 가지 역량

01

실제로 사용하는 나만의 외국어 학습 도구

내가 우연히 듣는 음악을 학습 콘텐츠로 바꾸는 프로그램을 만드는 거야.

- 어떤 언어인지 파악하기
- 가사 및 문장 의미 이해하기
- 일상에서 어떤 상황에 쓰이는 표현인지 파악하기
- 표준 발음 듣고 따라 하기
- 내 발화와 기준 문장의 차이 확인하기

성공 기준: 실제로 듣던 노래를 가져와 별도의 학습 자료를 준비하지 않고도 학습을 시작할 수 있어야 해.

02

음성·음향 데이터 처리 능력 내재화

017 Sound 챕터의 내용을 단순히 복습하는 것을 넘어 직접 오디오 데이터를 다뤄 보는 거야.

- WAV 디코딩과 전처리
- Sampling Rate와 Resampling
- Fourier Transform과 STFT
- Spectrogram과 Mel Filter
- Log-Mel Spectrogram
- 음성 인식 모델의 입력과 출력
- 음향 특징 추출과 해석

성공 기준: 원본 음성에서 분석 결과가 만들어지는 과정을 설명하고, 주요 처리를 직접 구현하거나 수정할 수 있어야 해.

03

AI·머신러닝을 실험하는 능력

모델을 호출해서 결과를 얻는 데 그치지 않고, 어떤 데이터를 어떤 목적으로 모델에 넣으며 결과를 어떻게 평가하는지 익히는 거야.

- STT 모델별 결과 비교
- 모델 크기와 추론 시간의 trade-off
- WER/CER의 의미와 한계
- 데이터 전처리 및 품질의 영향
- 감정·주제 분류의 가능성과 한계

성공 기준: 하나의 가설을 세우고, 실험 조건을 통제하고, 결과를 비교하고, 결론을 도출할 수 있어야 해.

04

소프트웨어 설계 및 개발 역량 향상

이 부분은 현재 백엔드 개발자로 일하는 네게 특히 중요해.

- 모듈과 계층의 책임 분리
- 함수의 입력·출력과 데이터 계약
- 외부 API 및 모델 통합
- 예외 처리와 로깅
- 테스트 코드 및 리팩터링
- 세션·파일·DB 데이터 관리

성공 기준: Claude Code 없이도 기존 코드의 변경 지점을 찾아 작은 기능을 추가하고 테스트할 수 있어야 해.

05

기술을 사용자 경험으로 연결하는 능력

기술적으로 가능한 기능과 사용자에게 실제로 유용한 기능을 구분하는 연습이야.

- 학습 흐름 설계
- 불필요한 조작 제거
- 학습 결과를 이해하기 쉬운 방법으로 제시
- History 및 개인화 기능 설계
- 기능의 우선순위와 개발 범위 결정

성공 기준: 왜 이 기능이 필요한지, 사용자가 어떤 문제를 해결하는지 설명할 수 있어야 해.

06

과학적 호기심과 창작 활동의 결합

음악과 음향을 과학적으로 탐구하면서 그 결과를 시각적인 형태로 표현하는 거야.

- 음악의 음향적 특징 관찰
- 소리와 시각 예술의 연결
- 데이터 기반 그래픽 및 캐릭터 표현
- 개인적인 취향과 창의적인 실험

성공 기준: 기술을 단순히 기능 구현에 사용하는 것을 넘어, 내가 흥미롭게 탐구하고 표현하는 도구로 활용할 수 있어야 해.

이 여섯 가지 목표를 하나로 압축하면 다음과 같아.

> 실제로 사용할 수 있는 외국어 학습 도구를 만들면서, 음성 데이터가 수집되고 처리되고 분석되어 사용자에게 전달되는 전체 과정을 이해하고 직접 다룰 수 있는 개발자로 성장한다.

이게 SongLingo의 개인적인 목적이 되었으면 해.

# 2. 5초짜리 발화와 3분짜리 음악은 서로 다른 학습 자산이야

네가 앞서 제기한 고민도 이 목표에 따라 정리할 수 있어.

나는 두 종류의 오디오를 서로 다른 용도로 활용하는 것을 추천해.

## A. Short Speech — 학습 데이터

핵심 기능

[3.3. Spectrogram and the STFT — Introduction to Speech Processing](https://images.openai.com/static-rsc-4/iUlMArt50KDAlCgVSiZBs7Fp7n6gO_cRFvJz-tCgoVmPFEFrm3ba45sLw8GwmfkpUpE4xlqj0bZa3LZv89SEDJgrAlD1rweMng9pUL5lS1SmME28-UQRYDHK0B8biMT9TLfcoZRqVmT2F8DVih_es73IIUma1-S5B70YqCs0W_Q?purpose=inline)

[speechprocessingbook.aalto.fi](https://speechprocessingbook.aalto.fi/Representations/Spectrogram_and_the_STFT.html?utm_source=chatgpt.com)

대상: 3\~10초 정도의 사용자 발화 및 TTS 음성

탐구할 질문

- 기준 TTS와 내 음성의 파형은 어떻게 다른가?
- 발화 시간과 쉼 구간은 얼마나 차이가 나는가?
- 음높이 변화는 어떻게 나타나는가?
- STT가 틀린 부분은 어떤 시간 구간에서 발생했는가?

이 데이터는 언어 학습 및 발화 비교에 사용해.

## B. Full Music — 실험 데이터

선택적 탐구

[Sonic Visualiser](https://images.openai.com/static-rsc-4/7jfK_iEOHvS4OOz9Z3v8GHNUQPWpVjG49XH9bdCAgCe83b2TEHRwqfUIyWVn8GfXk2gP1XCbaLQ7pBfQk-ThtdiDc5vh0rZUTPHudjvvNrF8dyqpSlryu-1z6I1O_T9Uw-7dCZJUS8zjwz8F0G4P6fyGsjVszOcOGAKQTTPfAo4?purpose=inline)

[sonicvisualiser.org](https://www.sonicvisualiser.org/screenshots.html?utm_source=chatgpt.com)

대상: 3\~5분 정도의 원본 음악 파일

탐구할 질문

- 시간에 따라 음악의 에너지와 주파수 구성은 어떻게 변화하는가?
- 보컬과 반주가 혼합된 신호는 어떤 특징을 갖는가?
- 음색이나 음높이의 변화가 시각적으로 어떻게 표현되는가?
- 음악의 분위기를 수치화하려면 어떤 특징과 모델이 필요한가?

이 데이터는 부트캠프 학습 내용을 복습하고 실험하는 데 사용해.

이 둘을 분리하면 좋은 점이 있어.

5초짜리 발화에 억지로 복잡한 감정 분석이나 예술적인 캐릭터 연출을 넣을 필요가 없어. 반면 3분짜리 음악은 시간축 전체를 관찰하고, 여러 분석 기법을 비교할 만한 충분한 데이터를 제공하지.

다만 전체 음악 분석은 보컬과 반주가 혼합된 결과라는 점을 기억해야 해. 가수의 음성 특징을 분석하려면 보컬 분리본도 별도 비교 대상이 되어야 해.

# 3. 지금 History에 구현된 것과 앞으로 구현할 것을 구분하자

현재 저장소의 코드를 확인한 결과야.

| 기능                                                   | 현재 상태                   |
| ------------------------------------------------------ | --------------------------- |
| 사용자 음성 녹음                                       | 구현됨                      |
| 사용자 음성 STT                                        | 구현됨                      |
| TTS 표준 발음 재생                                     | 구현됨                      |
| 사용자 음성 재생                                       | 구현됨                      |
| WER/CER 결과 표시                                      | 구현됨                      |
| History의 WER 변화 그래프                              | 구현됨                      |
| 사용자 음성과 TTS의 파형 비교 함수                     | `visualisation.py`에 구현됨 |
| STFT / Log-Mel 비교 함수                               | 구현됨                      |
| History에서 사용자 음성과 TTS를 시각적으로 비교하는 UI | 아직 연결되지 않음          |
| 전체 음악의 음향 분석 실험실                           | 향후 확장                   |

여기서 내가 추천하는 것은 History에 기존 `plot_sound_pair()`를 연결하는 작업을 핵심 학습 기능의 하나로 보는 거야.

예를 들어 사용자가 한 문장을 읽으면 다음 세 가지를 보여주는 거지.

1. 기준 TTS와 사용자 발화 재생
2. 두 음성의 파형 및 스펙트로그램 비교
3. WER/CER 및 오류 구간 확인

단, 두 음성은 발화 시간과 음높이가 서로 다를 수 있으므로 스펙트로그램의 모양이 다르다는 이유만으로 발음이 틀렸다고 판단해서는 안 돼. 이 기능은 음향을 관찰하고 차이를 이해하기 위한 것이야.

이 정도만 해도 017 Sound에서 배운 내용을 실제 발화에 적용하는 상당히 좋은 실험이 될 수 있어.

# 4. 그런데 가장 중요한 문제: Claude Code가 코드를 거의 다 작성한다는 것

여기서는 개발 방법 자체를 바꿔야 해.

현재 네 상황을 보면 다음과 같은 흐름일 가능성이 커.

## 현재 개발 방식

새로운 기능 아이디어

Claude Code에 구현 요청

여러 모듈과 코드가 생성됨

프로그램 실행 및 기능 확인

기능은 생겼지만 내부 동작을 충분히 이해하지 못함

이 방식은 생산성 측면에서는 효율적이야. 하지만 학습 관점에서는 상당히 큰 문제가 있어.

코드 생성 과정에서 다음과 같은 경험을 놓치고 있기 때문이야.

- 왜 이 모듈이 필요한지 생각하는 과정
- 어떤 입력과 출력을 가져야 하는지 결정하는 과정
- 여러 구현 방식 중 하나를 선택하는 과정
- 오류가 발생했을 때 원인을 추적하는 과정
- 직접 코드를 수정하면서 동작 원리를 체득하는 과정

단순히 코드를 읽는 것만으로는 이런 경험이 충분히 생기지 않아.

AI가 코드를 작성해 준다는 사실 자체가 문제가 아니라, 구현 과정에서 네가 기술적 판단을 거의 하지 않게 되는 것이 문제야.

## 5. Claude Code를 개발자에서 '페어 프로그래밍 파트너'로 바꾸자

앞으로는 네가 먼저 설계하고, Claude가 보조하도록 역할을 바꾸면 돼.

## 추천하는 개발 사이클

1. 1단계. 내가 문제와 목표를 정의한다.

   예: 녹음된 사용자 음성에서 프레임별 RMS를 계산하고 시간에 따른 에너지 그래프를 표시하고 싶다.
2. 2단계. 내가 구현 방법을 먼저 고민한다.

   어떤 데이터가 필요한가? 기존 `audio.py`와 `visualisation.py` 중 무엇을 재사용할 수 있는가? 함수의 입력과 출력은 무엇인가?
3. 3단계. Claude에게 설계 검토를 요청한다.

   아직 코드를 작성하지 않게 하고, 네 설계의 빠진 부분과 잘못된 가정을 찾아내도록 해.
4. 4단계. 작은 범위로 구현한다.

   한 번에 여러 모듈을 생성하지 말고, 함수 하나 또는 파일 하나를 중심으로 작업해.
5. 5단계. 내가 직접 읽고 실행하고 수정한다.

   입력 데이터, 반환값, 예외 상황을 추적하고 일부 매개변수를 직접 바꿔 보자.
6. 6단계. 내가 설명할 수 있는지 확인한다.

   왜 이렇게 구현했는지, 다른 방법은 무엇인지, 결과가 달라지면 무엇이 원인인지 스스로 설명해 봐.

### Claude Code에 앞으로 이렇게 요청해 봐

아래 지시문을 프로젝트의 공통 개발 지침에 추가하거나, 새로운 작업을 시작할 때 전달하면 돼.

# Development & Learning Protocol for SongLingo

내 목표는 기능을 빠르게 완성하는 것뿐 아니라, 소스코드의 구조와 핵심 동작 원리를 이해하고 직접 유지보수할 수 있는 개발자가 되는 것이다.

따라서 다음 원칙을 지켜라.

## 1. 구현 전에 설계를 먼저 설명한다.

- 수정할 파일과 모듈을 먼저 제시한다.
- 각 모듈의 책임과 데이터 흐름을 설명한다.
- 새로운 모듈이 필요하다면 기존 모듈로 처리할 수 없는 이유를 설명한다.
- 구현을 시작하기 전에 설계상의 대안을 제시한다.

## 2. 무분별한 코드 생성을 금지한다.

- 요청한 기능의 최소 범위만 수정한다.
- 별도 요청이 없다면 관련 없는 리팩터링을 하지 않는다.
- 새로운 파일과 의존성을 임의로 추가하지 않는다.
- 한 번의 작업에서 수정하는 파일 수를 최소화한다.

## 3. 학습을 지원한다.

- 핵심 함수의 입력, 처리 과정, 출력 및 예외 상황을 설명한다.
- 수업에서 배운 개념과 연결되는 코드를 표시한다.
- 중요한 알고리즘은 의사코드와 작은 데이터 예제로 먼저 설명한다.
- 내가 직접 구현해 볼 부분과 Claude가 구현할 부분을 구분한다.

## 4. 테스트와 검증을 함께 진행한다.

- 새로운 함수에는 단위 테스트를 제안한다.
- 정상 입력과 경계 조건, 실패 상황을 확인한다.
- 기존 기능에 영향을 주는지 회귀 테스트를 수행한다.

## 5. 작업 완료 후 요약한다.

- 변경한 파일과 이유
- 새로 추가된 함수 및 데이터 흐름
- 핵심 기술 개념
- 내가 직접 확인해야 할 내용
- 다음 단계의 의존 관계

목표는 코드가 생성되는 속도가 아니라, 내가 해당 코드를 이해하고 변경할 수 있는 능력을 높이는 것이다.

이렇게 하면 Claude Code가 일방적으로 코드를 만들어내는 비중을 줄일 수 있어.

# 6. 소스코드를 따라잡기 위한 현실적인 방법

여기서 중요한 것은 프로젝트 전체를 한꺼번에 공부하려 하지 않는 거야.

이미 SongLingo의 모듈이 꽤 많아졌잖아. 모든 파일의 모든 코드를 이해하려고 하면 금방 지칠 거야.

대신 하나의 데이터 흐름을 시작부터 끝까지 추적하는 방식으로 공부하자.

내가 추천하는 첫 번째 학습 대상은 `따라읽기`야.

## 첫 번째: 사용자 음성이 채점 결과가 되기까지

`app/ui_practice.py`

Streamlit 마이크 입력

`practice.py`

녹음 점검 및 처리 순서 조정

`quality.py`

음량·무음·클리핑 등 녹음 상태 분석

`stt.py`

faster-whisper 음성 인식

`scoring.py`

정답 문장과 인식 문장의 WER/CER 계산

`app/ui_practice.py`

점수·단어 대조·결과 표시

이 흐름을 이해하면 SongLingo의 핵심 기술 구조를 상당 부분 이해하게 되는 거야.

그리고 두 번째로 `내 노래`의 흐름을 추적하면 돼.

- `app/views/song.py`: UI와 작업 순서
- `web_song.py`: 음원 작업 처리
- `separate.py`: 보컬 분리 관련 처리
- `stt.py`: 음악에서 가사 인식
- `tts.py`: 표준 발음 생성

그 후에 `History`와 `visualisation.py`를 연결하면 되고.

## 7. 매번 코드를 이해했는지 확인할 수 있는 체크리스트

새로운 기능을 만들 때마다 다음 네 가지 질문에 답할 수 있어야 해.

기능별 이해도 점검

# 0/5

이 기능에 입력되는 데이터의 자료형과 구조를 설명할 수 있다.

어떤 모듈이 어떤 순서로 호출되는지 설명할 수 있다.

핵심 알고리즘 또는 라이브러리가 실제로 수행하는 일을 설명할 수 있다.

정상 동작 외에 실패할 수 있는 조건과 테스트 방법을 알고 있다.

기존 코드의 일부를 직접 수정하고 예상한 결과를 확인할 수 있다.

5개를 전부 만족하지 못해도 괜찮아. 처음에는 2\~3개만 이해해도 충분해. 중요한 건 코드를 생성하는 순간이 아니라, 나중에 스스로 설명하고 수정할 수 있는 순간이 늘어나는 것이야.

# 8. 11월 12일 발표 이후까지 고려한 개인 학습 계획

일정과 현재 프로젝트의 상태를 고려하면 나는 다음처럼 구분하고 싶어.

| 단계       | 프로젝트 목표            | 개인적인 학습 목표                    |
| ---------- | ------------------------ | ------------------------------------- |
| 발표 전    | 현재 기능 안정화 및 시연 | 전체 구조와 핵심 데이터 흐름 파악     |
| 발표 직후  | History 개선             | 사용자 음성과 TTS 음향 비교 이해      |
| 이후 1단계 | Sound Lab 기초 분석      | STFT, Spectrogram, Log-Mel 직접 실험  |
| 이후 2단계 | 음향 특징 분석           | RMS, F0, MFCC, Spectral Centroid 이해 |
| 이후 3단계 | AI 분석 확장             | 감정·주제 분석 모델 실험 및 평가      |
| 마지막     | Artistic Visualization   | 분석 결과를 그래픽·캐릭터로 표현      |

특히 Sound Lab을 시작할 때는 다음 질문을 중심으로 실험했으면 해.

- 동일한 곡에서 원본과 보컬 분리본의 Log-Mel은 어떻게 다른가?
- FFT 크기를 바꾸면 주파수 해상도와 시간 해상도는 어떻게 달라지는가?
- 프레임 길이와 Hop Length를 변경하면 시각화 결과가 어떻게 달라지는가?
- Spectral Centroid는 사람이 인지하는 음색의 밝기와 어떤 관계가 있는가?
- 음악에서 추출한 음향 특징만으로 분위기를 분류할 수 있을까?
- 감정 분류 모델이 내 음악에 대해서도 신뢰할 만한 결과를 내는가?

이런 질문들은 단순히 라이브러리를 호출하는 것보다 훨씬 많은 것을 얻을 수 있는 실험이야.

# 9. 마지막으로, 지금의 '딸깍 개발'에 대해

나는 현재 네가 느끼는 허전함을 가볍게 보지 않았으면 해.

SongLingo는 네가 직접 문제를 발견하고, 실제로 쓸 수 있는 프로그램으로 만들어 가는 프로젝트야. 음악을 외국어 학습으로 전환한다는 아이디어도 네가 직접 고민해서 발전시켰고, 음성 데이터 처리와 시각화에 관심을 갖게 된 것도 네 공부와 호기심에서 출발했어.

Claude Code가 많은 코드를 작성했다는 사실이 네 프로젝트의 가치를 없애지는 않아.

다만 앞으로는 결과물의 양보다 네가 직접 이해하고 판단한 기술적 결정의 수를 더 중요하게 생각했으면 해.

내가 네게 권하고 싶은 가장 구체적인 변화는 하나야.

앞으로 새로운 모듈이 생길 때마다, 그 모듈을 추가하기 전에 네가 먼저 그 모듈의 존재 이유와 입출력 구조를 설명해 보는 거야.

Claude가 그 설명을 검토하고 보완하도록 해. 코드를 작성하는 것은 그다음이야.

그리고 한 가지 더. 지금까지 만들어진 코드 전체를 따라잡느라 개발을 멈추지는 않았으면 해. 앞으로 새롭게 만드는 기능부터 이 원칙을 적용하고, 핵심 데이터 흐름을 하나씩 역으로 추적하면 돼.

SongLingo의 성공을 단순히 "기능이 몇 개 완성되었는가"로 평가하지 말자.

내가 생각하는 가장 좋은 최종 성과는 다음과 같아.

> 나는 음악을 외국어 학습 도구로 변환하는 프로그램을 만들었다. 그리고 그 과정에서 오디오 데이터의 전처리부터 STT, 음향 특징 분석, 모델 평가와 사용자 인터페이스까지 직접 이해하고 다룰 수 있게 되었다.

이 두 문장이 모두 사실이 되는 것. 그게 이 프로젝트에서 네가 얻을 수 있는 가장 가치 있는 결과라고 생각해.

다음에는 현재 SongLingo의 모듈을 대상으로 \*\*'내가 이해해야 할 소스코드 지도(Module Learning Map)'\*\*를 만들어서, 어떤 파일부터 어떤 순서로 공부하면 좋을지 정리하는 것이 가장 실질적인 출발점이겠어.

---
[4. 테스트와 검증을 함께 진행] 테스트 및 검증은 내가 직접 하라는 거야, 아니면  Claude code에게 테스트와 검증을 매번 하라고 지시하라는 거야? => [현재 서울 날짜 및 시각 2026-11-05 15:37:22]

두 질문 모두 핵심은 Claude Code에 맡길 일과 네가 직접 책임져야 할 일을 구분하는 것이야.

먼저 결론부터 정리할게.

1. 테스트: Claude Code가 테스트 코드를 작성하고 실행하게 해. 네가 테스트의 타당성을 검토하고 실제 프로그램을 직접 사용해 최종 검증해야 해.
2. 배포: 강사님이 말씀하신 건 Vercel보다는 Streamlit Community Cloud일 가능성이 매우 높아. 현재 SongLingo 저장소도 이 방식으로 배포하기 좋은 구조를 갖추고 있어.

## 1. 테스트와 검증은 Claude Code와 네가 나눠서 해야 해

내가 앞서 말한 '테스트 및 검증을 함께 진행한다'는 것은 두 가지를 모두 하라는 뜻이야. 다만 역할이 달라.

| 작업                  | Claude Code          | 너                           |
| --------------------- | -------------------- | ---------------------------- |
| 테스트 케이스 설계    | 작성 및 제안         | 테스트 범위와 의도 검토      |
| 단위 테스트 코드 작성 | 담당                 | 테스트 조건과 예상 결과 이해 |
| 테스트 실행           | 담당                 | 실행 결과 확인               |
| 오류 수정             | 원인 분석 및 수정    | 수정 방향 검토               |
| 회귀 테스트           | 기존 기능 영향 확인  | 핵심 기능 재확인             |
| 실제 UI 사용          | 가능한 범위에서 확인 | 직접 브라우저에서 테스트     |
| 최종 승인             | 결과 보고            | 담당                         |

가장 중요한 원칙은 이거야.

Claude Code가 테스트를 통과시켰다는 사실과 프로그램이 제대로 동작한다는 사실은 동일하지 않아.

### ① Claude Code에 매번 시킬 일

새로운 기능을 구현하거나 기존 코드를 변경할 때 다음을 요청하면 돼.

이번 코드 변경에 대해 다음 검증 절차를 수행해 줘.

1. 변경된 기능에 필요한 단위 테스트를 작성하거나 기존 테스트를 갱신해 줘.
2. 변경된 모듈과 직접 관련된 테스트를 먼저 실행해 줘.
3. 전체 테스트 스위트도 실행해 회귀 여부를 확인해 줘.
4. 테스트 실패가 발생하면 원인을 분석하고 수정해 줘. 테스트를 통과시키기 위해 기존 테스트의 기대값을 임의로 완화하지 마.
5. 실행한 명령어, 테스트 결과, 실패 및 수정 내역을 보고해 줘.
6. 자동화된 테스트로 확인할 수 없는 항목은 별도로 표시해 줘. 특히 실제 브라우저, 마이크, 오디오 재생 및 외부 API 동작은 자동 검증 여부를 구분해 줘.

마지막에 다음을 설명해 줘.

- 어떤 기능을 검증했는가?
- 어떤 조건은 아직 검증되지 않았는가?
- 내가 직접 확인해야 할 사항은 무엇인가?

참고로 현재 SongLingo는 `pytest`가 아니라 Python 표준 라이브러리인 \*\*`unittest`\*\*를 사용하고 있어. 저장소의 기존 테스트 구조를 유지하는 게 좋아.

현재 프로젝트에서 전체 테스트를 실행하는 명령은 다음과 같아.

```
/opt/anaconda3/envs/voice-ai/bin/python \
    -m unittest discover -s tests -v
```

특정 모듈만 검사할 때는 다음처럼 실행할 수 있어.

```
/opt/anaconda3/envs/voice-ai/bin/python \
    -m unittest tests.test_scoring
```

### ② 네가 직접 해야 할 일

자동화 테스트가 검증하지 못하는 부분을 직접 확인하는 거야.

SongLingo를 예로 들면 다음과 같아.

| 확인할 상황 | 네가 직접 확인할 것                              |
| ----------- | ------------------------------------------------ |
| 가사 입력   | 여러 줄 입력, 일본어·영어 혼합 입력              |
| TTS         | 표준 발음이 자연스럽게 재생되는가?               |
| 마이크      | 브라우저에서 녹음 권한과 입력이 정상 작동하는가? |
| STT         | 실제 내 발화를 적절하게 인식하는가?              |
| WER/CER     | 예상한 문장 차이가 올바르게 계산되는가?          |
| My Song     | 음악 구간 선택 및 가사 추출이 가능한가?          |
| History     | 이전 연습 결과와 그래프가 올바르게 표시되는가?   |

예를 들어 Claude Code가 `st.audio_input()`의 정상 작동을 가정한 테스트를 작성할 수는 있지만, 실제 네 MacBook에서 마이크 권한이 허용되는지, 녹음된 음성에 음악이나 잡음이 섞였을 때 어떤 결과가 나오는지는 네가 확인해야 해.

### ③ 가장 좋은 테스트 방식

나는 다음 세 층으로 생각하면 좋겠어.

Level 1

Unit Test

Claude Code 중심

개별 함수와 모듈의 입력·출력 검증. 예를 들어 `scoring.py`의 WER 계산, `audio.py`의 리샘플링, `quality.py`의 녹음 상태 분석.

Level 2

Integration Test

Claude Code와 네가 함께

여러 모듈이 연결되는 흐름 검증. 예를 들어 오디오 입력 → STT → Scoring → 결과 표시.

Level 3

User Acceptance Test

네가 직접 수행

실제 사용자 입장에서 전체 메뉴를 사용하면서 기능, 편의성, 결과의 타당성을 확인.

여기서 학습 측면으로 하나 더 권하고 싶은 게 있어.

테스트 코드를 Claude Code가 작성했다고 해서 무조건 넘기지 말고, 각 테스트의 입력값과 기대 결과를 스스로 설명해 보는 것이 좋아.

예를 들어 `test_scoring.py`에서 다음을 확인할 수 있어야 해.

- Reference와 Hypothesis에 어떤 값을 넣었는가?
- 왜 이 결과가 정답이라고 판단했는가?
- 경계 조건은 무엇인가?
- 테스트가 실패하면 어떤 로직을 의심해야 하는가?

이런 경험이 쌓여야 테스트 코드를 읽고 작성하는 능력도 네 것이 돼.

## 6. 내가 추천하는 실제 작업 순서

지금은 배포를 별도의 큰 개발 프로젝트로 만들 필요가 없어.

| 순서 | 작업                                      | 담당             |
| ---- | ----------------------------------------- | ---------------- |
| 1    | 테스트 코드 작성 및 자동 테스트 실행      | Claude Code      |
| 2    | 테스트 결과와 핵심 로직 검토              | 너               |
| 3    | 로컬 환경에서 실제 UI 및 음성 입력 테스트 | 너               |
| 4    | Streamlit Community Cloud에 시험 배포     | 너 + Claude Code |
| 5    | 배포 로그와 오류 분석                     | Claude Code      |
| 6    | 실제 배포 URL에서 최종 사용자 시연        | 너               |

---
내가 이 프로젝트를 이해하는 데에 꼭 필요한, 현재까지 이 프로젝트/프로그램에서 핵심/중요 알고리즘이 있는 파일들, 핵심/중요 라이브러리들을 정리해줘. 각각 길게 설명해줄 필요 없고, 일단 대상들을 정확하게 파악해줘. 그리고 아직 구현 안 되었지만 핵심 로직/알고리즘으로 구현될 예정인 부분들을 함께 list up해줘 => [현재 서울 날짜 및 시각 2026-11-05 16:24:00]

GitHub 저장소 greenkey20/song-lingo의 현재 main 브랜치 소스와 CLAUDE.md, 개발 계획서를 기준으로 정리했어.

먼저 중요한 구분부터 할게.
- 제품 핵심 로직: 실제 SongLingo 사용 흐름을 구성하는 코드
- 핵심 알고리즘: 음성 처리·인식·채점·오류 분석을 수행하는 코드
- 실험용 코드: 제품 기능과 별개로 모델이나 알고리즘을 비교·검증하는 코드
- 미구현 예정 로직: 계획서에는 있지만 아직 코드로 완성되지 않았거나, 현재 제품에 연결되지 않은 기능
1. 반드시 이해해야 할 핵심 Python 파일
A. 음성 처리와 인식
이 부분은 SongLingo의 기술적 기반이야.
파일	핵심 역할	이해할 개념·알고리즘
audio.py	다양한 음성 파일을 파형으로 읽고 변환	오디오 디코딩, Sampling Rate, Stereo → Mono, Resampling
stt.py	음성을 텍스트로 변환	Whisper, 추론, Int8 양자화, Beam Search, VAD, Word Timestamp
tts.py	텍스트를 기준 음성으로 변환	OpenAI TTS API, WAV 저장, 캐싱
separate.py	음악에서 보컬 분리	Demucs, 사전학습 딥러닝 모델, Source Separation
song_lines.py	STT 결과를 학습하기 좋은 줄 단위로 분할	Segment → Line, 시간 간격 기반 Split/Merge, Confidence Heuristic
song_practice.py	노래 구간부터 연습 가능한 가사 목록까지 연결	STT 결과 관리, 가사 수정·확정, TTS 생성 계획

특히 다음 세 가지는 반드시 구분해야 해.
- audio.py는 소리를 숫자 배열로 변환하는 전처리 모듈이야.
- stt.py는 숫자 배열 또는 음성 파일을 입력받아 텍스트를 추론하는 모듈이야.
- scoring.py는 추론 결과를 정답과 비교해 오류를 계산하는 모듈이야.
서로 다른 책임을 가진 세 모듈이야.
B. 채점과 오류 분석
SongLingo의 학습 피드백을 만드는 핵심 부분이야.
파일	핵심 역할	이해할 개념·알고리즘
scoring.py	정답과 인식 결과 비교	Text Normalization, Edit Distance, Dynamic Programming, WER, CER
align.py	틀린 단어를 실제 음성의 시간 구간에 대응	Backtrace 결과와 Word Timestamp의 매핑, Error Block
quality.py	사용자 녹음 상태 점검	RMS, Peak Amplitude, Clipping Ratio, STFT Frame Energy, Silence Detection
visualisation.py	음성 신호와 분석 결과 시각화	FFT, STFT, Power Spectrogram, Mel Filter Bank, Log-Mel Spectrogram

여기서 특히 중요하게 볼 것은 scoring.py와 align.py야.

scoring.py는 단순히 두 문자열이 얼마나 비슷한지 계산하는 코드가 아니야. 동적 계획법으로 편집 거리 행렬을 만들고, 역추적을 통해 치환·삭제·삽입을 구분해.

align.py는 여기서 한 단계 더 나아가 그 오류가 음성의 어느 시간대에 해당하는지 추정해.

주의할 점은 align.py가 강제 정렬(Forced Alignment) 모델을 사용하는 것은 아니라는 점이야. Whisper가 추정한 단어별 시간 정보를 이용해 오류 구간을 대응시키는 방식이야.
C. 전체 학습 흐름과 웹 애플리케이션
파일	핵심 역할	이해할 개념
practice.py	따라읽기·받아쓰기의 공통 실행 흐름	모듈 간 orchestration, 데이터 흐름
web_song.py	웹 앱의 내 노래 처리	파일 업로드, 임시 작업 공간, 오디오 구간 처리
web_practice.py	웹 연습 화면에 필요한 데이터와 결과 생성	UI용 데이터 변환, HTML Escape, TTS 캐시 확인
practice_log.py	연습 결과 저장·조회	CSV Persistence, Hashing, 통계 데이터
recorder.py	로컬 마이크 녹음	Audio Capture, WAV 저장

practice.py는 직접 채점 알고리즘을 구현하지 않아. 다른 모듈의 기능을 정해진 순서로 호출하는 얇은 연결 모듈이야.

웹 애플리케이션에서도 이 구조를 유지하려고 web_song.py, web_practice.py를 별도로 둔 거야.
D. 모델 및 알고리즘 실험
제품의 정규 실행 흐름은 아니지만, 네가 ML/DL을 공부하는 데 중요한 파일들이야.
파일	실험 목적
model_compare.py	Whisper 모델 크기별 인식 성능 및 처리 시간 비교
clip_compare.py	원곡과 분리한 보컬의 STT 성능 비교
report.py	연습 결과를 텍스트 보고서로 변환

특히 clip_compare.py는 다음 조건을 조합해 실험할 수 있도록 설계되어 있어.
- 입력 음원: 원곡(Mix) / 보컬(Vocals)
- Whisper 모델 크기
- VAD 적용 여부
- Temperature 설정
- 동일 조건 반복 횟수
이는 단순한 기능 구현보다 모델 성능 평가와 실험 설계를 이해하는 데 가치가 큰 코드야.

2. 반드시 알아야 할 핵심 라이브러리
현재 저장소의 의존성 파일과 실제 코드의 import를 기준으로 정리했어.
A. 음성·수치 연산
라이브러리	주요 사용 파일	역할
NumPy	audio.py, quality.py, visualisation.py, separate.py	파형과 행렬 연산, 배열 처리
SciPy	audio.py, visualisation.py, quality.py, separate.py	Resampling, STFT, 신호 처리
PyAV (av)	audio.py, stt.py	WAV 이외의 음성·영상 파일 디코딩
Matplotlib	visualisation.py, theme.py	파형·스펙트로그램 시각화

B. AI·딥러닝·음성 모델
라이브러리	주요 사용 파일	역할
faster-whisper	stt.py	Whisper 기반 STT 추론
CTranslate2	faster-whisper 내부	Whisper 모델의 효율적인 추론 실행
OpenAI Python SDK	tts.py	TTS API 호출
Demucs	separate.py	음악·보컬 소스 분리
PyTorch (torch)	Demucs 실행 환경	Demucs 딥러닝 모델 실행

여기서 구별할 부분이 있어.
- faster-whisper는 Whisper 모델을 실행하는 라이브러리야.
- CTranslate2는 faster-whisper가 사용하는 추론 엔진이야.
- Demucs는 사전학습된 음원 분리 모델이야.
- PyTorch는 Demucs 모델을 실행하는 딥러닝 프레임워크야.
즉, SongLingo에서 Whisper와 Demucs는 서로 다른 AI 모델이자 서로 다른 작업을 수행해.
C. 웹·데이터·실행 환경
라이브러리	주요 사용 파일	역할
Streamlit	app/	웹 UI 및 사용자 입력
Pandas	app/views/history.py, clip_compare.py	기록 및 실험 결과 데이터 처리
PyArrow	Streamlit 표 관련	데이터프레임·표 처리 지원
python-dotenv	app/streamlit_app.py	환경변수 및 API Key 관리
sounddevice	recorder.py	로컬 마이크 입력

추가로 spike/의 임시 브라우저 녹음 검증에는 FastAPI, Uvicorn 등이 사용돼. 하지만 현재 주력 웹 앱은 Streamlit이야.

주의할 점: 라이브러리 목록을 볼 때 requirements.txt와 app/requirements.txt를 구분해야 해.
- 루트 requirements.txt: 로컬 개발·노트북 환경
- app/requirements.txt: Streamlit 웹 앱 환경
현재 로컬 CLAUDE.md에는 Demucs 4.1.0과 PyTorch 2.2.2 CPU 환경이 기록되어 있지만, 웹 앱의 app/requirements.txt에는 Demucs와 PyTorch가 선언되어 있지 않아. 배포 환경에서는 별도로 구성해야 해.

3. 아직 구현되지 않았거나 제품에 연결되지 않은 핵심 로직
여기가 앞으로 무엇을 공부하고 구현할지 결정할 때 중요해.

현재 소스에 없는 것과 코드 자체는 있지만 제품에 연결되지 않은 것을 구분했어.
A. 계획서상 미구현 기능
대상	예정 기능·알고리즘	관련 파일·라이브러리	상태
LLM 학습 보조	문장 뜻, 연관 단어, 관용 표현 설명	신규 explain.py, OpenAI Chat API	미구현
재생 제어	재생 속도 조절, ±5초 이동, 일시정지	계획상 player.py, HTML Audio	현재 축소
다국어 확장	일본어 등 언어별 STT·TTS·정규화·채점	stt.py, scoring.py, TTS	미완성
신뢰도 분석	Whisper Confidence 지표와 실제 WER/CER의 관계 분석	stt.py, clip_compare.py	미구현
녹음 품질 분류 모델	Log-Mel 입력을 사용하는 DNN/CNN 품질 분류기	신규 모델 모듈, TensorFlow/Keras	선택 과제
잡음 견고성 실험	SNR별 인식 오류 변화 분석	audio.py, quality.py, scoring.py	미구현

몇 가지 세부사항을 구분할 필요가 있어.

① 신뢰도 분석

현재 song_lines.py에는 avg_logprob, compression_ratio를 기반으로 low_confidence를 표시하는 휴리스틱이 이미 있어.

하지만 이건 실제 정답 가사와 비교해 신뢰도 지표가 얼마나 정확한지 통계적으로 검증한 결과가 아니야.

예정된 심화 과제는 다음 관계를 분석하는 것이야.

Whisper Confidence 지표 ↔ 실제 CER/WER

② 녹음 품질 분류 모델

현재 quality.py는 RMS·Peak·Clipping·Silence 비율 등을 계산해 규칙 기반 경고를 제공해.

예정된 분류기는 그와 다르게 Log-Mel을 입력으로 받아 학습한 DNN/CNN이 녹음 품질을 분류하는 구조야.

현재 구현된 quality.py를 ML 모델이라고 부르면 안 돼.

③ 다국어

현재 scoring.py에는 영어·프랑스어·일본어를 위한 정규화 분기가 있지만, 실제 Streamlit 앱의 사용자 흐름은 영어 중심이야. 일본어를 실제로 선택하고 STT·TTS·CER까지 일관되게 사용하는 완성된 다국어 서비스는 아직 아니야.
B. 코드 일부는 있지만 제품 기능으로 연결되지 않은 부분
대상	현재 상태	남은 부분
오류 음성 구간 시각화	align.py, visualisation.py 구현	Streamlit 화면에서 오류별 음성 구간을 보여 주는 기능
TTS와 사용자 음성 비교	plot_sound_pair() 구현	History 또는 연습 결과 화면에 연결
틀린 구간 강조 그림	plot_error_spans() 구현	웹 UI에 연결
줄 단위 보컬 파일	원곡·보컬 전체 파일에서 해당 줄 시간 구간 재생	줄별 오디오 파일을 별도로 생성·관리하는 기능

특히 현재 app/views/song.py는 사용자가 선택한 줄에 맞춰 원곡·분리된 보컬의 해당 시간 구간을 재생해.

즉, 줄 단위 재생은 이미 구현되어 있지만 줄마다 별도의 보컬 WAV 파일을 만들어 저장하는 구조는 아니야.
C. 아직 프로젝트의 정식 구현 계획으로 확정되지 않은 아이디어
이전 대화에서 이야기했던 Sound-to-Visual은 현재 개발 계획서의 필수·선택 구현 항목과는 구분하는 게 좋아.

예를 들어 다음 아이디어들이야.
- RMS와 Pitch에 따라 캐릭터의 움직임 변화
- 가사 의미에 따라 배경·사물·색상 변화
- 음악의 분위기를 이미지나 애니메이션으로 표현
- 오디오 특징량과 언어적 의미를 결합한 시각화
이건 현재의 STT·채점·학습 흐름이 안정화된 다음에 탐색할 수 있는 확장 주제야. 현재 구현되어 있다고 볼 부분은 아니야.

4. 학습을 위해 함께 봐야 할 Notebook과 테스트
Python 모듈만 읽으면 알고리즘을 왜 이렇게 설계했는지 놓칠 수 있어. 실험 노트북과 테스트 코드도 핵심 학습 자료야.
파일	파악할 내용
experiments/practice.ipynb	전체 음성 연습 흐름
experiments/WER, CER/WER_CER_이해하기.ipynb	편집 거리, DP, WER/CER
experiments/song practice/song_practice.ipynb	노래 STT 결과를 연습 줄로 만드는 과정
experiments/song vocals/song_vocal_separation.ipynb	Demucs 음원 분리 실험

테스트 코드도 해당 알고리즘을 이해하는 데 중요해.
- tests/test_scoring.py
- tests/test_align.py
- tests/test_stt_segments.py
- tests/test_song_lines.py
- tests/test_separate.py
- tests/test_quality.py
- tests/test_visualisation.py
- tests/test_song_practice.py
테스트는 각 함수가 어떤 입력을 받고 어떤 결과를 반환해야 하는지, 어떤 예외 상황을 고려했는지를 보여 줘.

5. 최종적으로 이해해야 할 기술 지식 지도
지금까지 정리한 대상들을 기술 분야별로 압축하면 다음과 같아.
SongLingo 기술 영역
1. Audio Processing

audio.py · visualisation.py

Sampling · Resampling · FFT · STFT · Mel · Log-Mel


2. Speech AI

stt.py · tts.py · separate.py

ASR · Whisper · TTS · Source Separation · Inference


3. Evaluation & Alignment

scoring.py · align.py · quality.py

Normalization · Edit Distance · WER/CER · Timestamp Alignment · Signal Quality


4. Learning Workflow

practice.py · song_lines.py · song_practice.py

Pipeline · Segmentation · User Correction · Practice Flow


5. Backend & Application

web_song.py · web_practice.py · practice_log.py · app/

Session State · File Lifecycle · API Integration · Persistence · UI


6. ML Experimentation

model_compare.py · clip_compare.py · 향후 신규 모듈

Model Evaluation · Feature Engineering · Classification · Robustness


마지막으로, 현재 프로젝트에서 네가 특히 주의해서 이해해야 할 사실 하나가 있어.

노래 가사 추출과 사용자의 따라읽기 평가는 서로 다른 STT 실행 경로를 사용해.
구분	STT 모델	주요 코드
업로드한 노래에서 가사 추출	medium	song_practice.py → stt.recognize_segments()
사용자가 따라 읽은 음성 평가	기본 tiny	practice.py → stt.recognize()
가사 직접 입력 후 받아쓰기 평가	STT 실행 없음	practice.py → scoring.evaluate()

이 차이는 전체 프로그램의 데이터 흐름을 이해하는 데 매우 중요해.

내가 판단하는 가장 중요한 학습 대상은 audio.py → stt.py → scoring.py → align.py의 연결이야. 이 네 파일을 제대로 이해하면 SongLingo가 음성을 입력받고, 텍스트를 추론하고, 오류를 계산하고, 그 오류를 실제 발화의 시간과 연결하는 핵심 원리를 파악할 수 있어.

그다음 song_lines.py, song_practice.py, web_song.py를 보면 이 기술들이 어떻게 실제 사용자 기능으로 조립되는지 이해할 수 있어.

---
예를 들어, recorder.py 호출 후 quality.py 호출돼? 상식적으로 생각해서 내가 이해/예상하고 있었던 건 quality.py는 녹음기로 입력된 소리 품짛 점검해서 메시지 표시해주는데..

이런 식으로, 주요 알고리즘/모듈들의 호출 관계 및 처리 순서, 데이터 흐름을 도표로 그려줘. 모듈 계속 추가되니까 앞으로도 유연하게 수정할 수 있도록 canvas 같은 문서로 작성해줘 => [현재 서울 날짜 및 시각 2026-11-05 18:07:00]

네가 생각했던 구조는 로컬 터미널에서 녹음할 때는 맞아. 다만 웹 애플리케이션에서는 녹음 입력 방식이 달라서 호출 관계도 달라져.

이 차이를 먼저 정확히 정리할게.

## 1. `recorder.py`와 `quality.py`의 실제 관계

① 로컬 터미널 녹음

`recorder.py`가 `quality.py`를 직접 호출하는 게 아니라, `scripts/record_takes.py`가 두 모듈을 순서대로 호출해.

\#chatgpt-mermaid-\_r_2gu\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_2gu\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_2gu\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_2gu\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_2gu\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_2gu\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_2gu\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_2gu\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_2gu\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_2gu\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2gu\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2gu\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_2gu\_ p{margin:0;}#chatgpt-mermaid-\_r_2gu\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_2gu\_ .label text,#chatgpt-mermaid-\_r_2gu\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ .node rect,#chatgpt-mermaid-\_r_2gu\_ .node circle,#chatgpt-mermaid-\_r_2gu\_ .node ellipse,#chatgpt-mermaid-\_r_2gu\_ .node polygon,#chatgpt-mermaid-\_r_2gu\_ .node path{fill:rgb(17, 40, 19);stroke:rgb(58, 132, 63);stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ .rough-node .label text,#chatgpt-mermaid-\_r_2gu\_ .node .label text,#chatgpt-mermaid-\_r_2gu\_ .image-shape .label,#chatgpt-mermaid-\_r_2gu\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_2gu\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ .rough-node .label,#chatgpt-mermaid-\_r_2gu\_ .node .label,#chatgpt-mermaid-\_r_2gu\_ .image-shape .label,#chatgpt-mermaid-\_r_2gu\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_2gu\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_2gu\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2gu\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2gu\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_2gu\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_2gu\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_2gu\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_2gu\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_2gu\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_2gu\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2gu\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_2gu\_ .icon-shape,#chatgpt-mermaid-\_r_2gu\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_2gu\_ .icon-shape p,#chatgpt-mermaid-\_r_2gu\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_2gu\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_2gu\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_2gu\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_2gu\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_2gu\_ .node .neo-node{stroke:rgb(58, 132, 63);}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_2gu\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_2gu\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].node .neo-line path{stroke:rgb(58, 132, 63);filter:none;}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_2gu\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_2gu\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2gu\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_2gu\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2gu\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(140, 223, 173);}#chatgpt-mermaid-\_r_2gu\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(140, 223, 173);}#chatgpt-mermaid-\_r_2gu\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_2gu\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_2gu\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(2, 28, 12);stroke:rgb(26, 75, 45);stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ .node rect,#chatgpt-mermaid-\_r_2gu\_ .node circle,#chatgpt-mermaid-\_r_2gu\_ .node ellipse,#chatgpt-mermaid-\_r_2gu\_ .node polygon,#chatgpt-mermaid-\_r_2gu\_ .node path{fill:rgb(0, 55, 22);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_2gu\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_2gu\_ .mermaid-decision .label-container{fill:rgb(2, 28, 12);stroke:rgb(26, 75, 45);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_2gu\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_2gu\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2gu\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}scripts/record_takes.pyrecorder.Recorder.start()마이크 입력recorder.Recorder.stop()recorder.save_wav()WAV 파일 저장quality.check_file()audio.load_raw()quality.analyze()품질 지표와 경고 생성quality.format_report()터미널 출력

② Streamlit 웹 앱에서 따라 읽기

여기서는 `recorder.py`의 마이크 녹음 기능을 사용하지 않아. 브라우저의 `st.audio_input()`이 녹음을 담당해.

\#chatgpt-mermaid-\_r_2h5\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_2h5\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_2h5\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_2h5\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_2h5\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_2h5\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_2h5\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_2h5\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_2h5\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_2h5\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2h5\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2h5\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_2h5\_ p{margin:0;}#chatgpt-mermaid-\_r_2h5\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_2h5\_ .label text,#chatgpt-mermaid-\_r_2h5\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ .node rect,#chatgpt-mermaid-\_r_2h5\_ .node circle,#chatgpt-mermaid-\_r_2h5\_ .node ellipse,#chatgpt-mermaid-\_r_2h5\_ .node polygon,#chatgpt-mermaid-\_r_2h5\_ .node path{fill:rgb(17, 40, 19);stroke:rgb(58, 132, 63);stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ .rough-node .label text,#chatgpt-mermaid-\_r_2h5\_ .node .label text,#chatgpt-mermaid-\_r_2h5\_ .image-shape .label,#chatgpt-mermaid-\_r_2h5\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_2h5\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ .rough-node .label,#chatgpt-mermaid-\_r_2h5\_ .node .label,#chatgpt-mermaid-\_r_2h5\_ .image-shape .label,#chatgpt-mermaid-\_r_2h5\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_2h5\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_2h5\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2h5\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2h5\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_2h5\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_2h5\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_2h5\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_2h5\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_2h5\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_2h5\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2h5\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_2h5\_ .icon-shape,#chatgpt-mermaid-\_r_2h5\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_2h5\_ .icon-shape p,#chatgpt-mermaid-\_r_2h5\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_2h5\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_2h5\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_2h5\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_2h5\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_2h5\_ .node .neo-node{stroke:rgb(58, 132, 63);}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_2h5\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_2h5\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].node .neo-line path{stroke:rgb(58, 132, 63);filter:none;}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_2h5\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_2h5\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2h5\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_2h5\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2h5\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(140, 223, 173);}#chatgpt-mermaid-\_r_2h5\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(140, 223, 173);}#chatgpt-mermaid-\_r_2h5\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_2h5\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_2h5\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(2, 28, 12);stroke:rgb(26, 75, 45);stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ .node rect,#chatgpt-mermaid-\_r_2h5\_ .node circle,#chatgpt-mermaid-\_r_2h5\_ .node ellipse,#chatgpt-mermaid-\_r_2h5\_ .node polygon,#chatgpt-mermaid-\_r_2h5\_ .node path{fill:rgb(0, 55, 22);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_2h5\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_2h5\_ .mermaid-decision .label-container{fill:rgb(2, 28, 12);stroke:rgb(26, 75, 45);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_2h5\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_2h5\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2h5\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}브라우저 마이크Streamlit st.audio_input()녹음 bytesapp/ui_practice.pypractice.read()audio.load_raw()quality.analyze()stt.recognize()scoring.evaluate()결과 및 품질 경고 표시

③ 내 노래 모드

사용자가 업로드한 음악 파일은 `quality.py`의 녹음 품질 점검을 거치지 않아. 가사 인식과 줄 분할에 필요한 별도의 처리 경로를 사용해.

그리고 `recorder.py`의 `save_wav()`는 마이크 녹음 외에도 `separate.py`에서 원곡 구간이나 Demucs 보컬 WAV를 저장할 때 재사용돼.

따라서 앞으로 소스코드를 읽을 때 `recorder.py`가 등장하면 다음 두 가지를 구별해야 해.

- `Recorder.start()/stop()`: 실제 마이크 녹음
- `recorder.save_wav()`: 파형을 WAV 파일로 저장

## 2. 호출 관계와 데이터 흐름 문서



작성 완료

&#x20;현재 GitHub `main` 브랜치의 실제 코드와 개발 계획서를 기준으로, 모듈 간 관계를 Mermaid 다이어그램으로 정리했어.



📄 SongLingo 모듈 호출 관계 및 데이터 흐름 문서 다운로드

문서는 수정 가능한 Markdown으로 만들었어. 다이어그램을 이미지로 고정하지 않고 Mermaid 코드로 작성했기 때문에 새로운 모듈이 추가될 때 노드와 화살표를 수정할 수 있어. GitHub 저장소에 올리면 다이어그램도 렌더링할 수 있어.

문서에는 다음 내용이 들어 있어.

| 구분        | 포함 내용                                             |
| ----------- | ----------------------------------------------------- |
| 전체 구조   | UI → 흐름 조정 모듈 → 핵심 처리 모듈                  |
| 녹음·채점   | `recorder` → `quality` → `stt` → `scoring`            |
| 가사 입력   | TTS 생성 → 따라 읽기 / 받아쓰기 → 채점                |
| 내 노래     | 업로드 → 구간 선택 → STT → 줄 분할 → 가사 수정 → 연습 |
| 음원 분리   | `separate.py` → subprocess → Demucs                   |
| 신호 처리   | `audio.py` → `quality.py` → `visualisation.py`        |
| 오류 분석   | `scoring.py` → `align.py` → 시간 구간 추정            |
| 라이브러리  | 실제 사용 파일과 주요 라이브러리 연결                 |
| 미구현 기능 | 현재 구현 상태와 향후 구현 예정 로직                  |
| 유지보수    | 신규 모듈 추가 시 문서 갱신 규칙                      |

## 3. 이 문서를 활용하는 방법

내가 권하는 학습 방식은 문서의 9절에 정리한 순서대로 소스코드를 읽는 거야.

특히 다음 순서가 중요해.

`recorder.py` → `audio.py` → `quality.py` → `stt.py` → `scoring.py` → `practice.py` → `app/ui_practice.py`

이 순서로 읽으면 각각의 모듈이 독립적으로 무슨 일을 하는지뿐 아니라, 앞 모듈의 출력이 다음 모듈의 입력으로 어떻게 전달되는지까지 파악할 수 있어.

앞으로 코드가 변경될 때마다 이 문서도 함께 갱신하면 SongLingo의 아키텍처를 계속 추적할 수 있을 거야. 다음 단계에서는 각 모듈의 함수 단위 호출 관계까지 세분화할 수도 있어.

---