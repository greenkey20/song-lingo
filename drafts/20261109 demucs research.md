https://github.com/facebookresearch/demucs

https://kimjy99.github.io/%EB%85%BC%EB%AC%B8%EB%A6%AC%EB%B7%B0/ht-demucs/
https://velog.io/@jinthearchivist/Demucs%EC%9D%98-%EA%B3%84%EB%B3%B4

---
그런데 demucs, whisper 모두 ai 모델인 거 맞아? AI/딥러닝 기술이 발전하기 전에는, 그러면, 음악에서 보컬이나 특정 악기 소리 추출, stt, 어떻게 했어..? 과거에는 이런 작업 못했던 거야..? => [현재 서울 날짜 및 시각 2026-11-09 16:35:00]

맞아. Demucs와 Whisper는 모두 AI 모델이고, 구체적으로는 딥러닝 기반 모델이야. 그런데 흥미로운 점은 두 기술 모두 딥러닝이 등장하기 훨씬 전부터 연구되어 왔다는 거야.

음원 분리와 음성 인식은 컴퓨터공학과 신호처리 분야에서 수십 년간 연구한 주제야. 딥러닝은 이 문제들을 처음 해결한 것이 아니라, 기존에는 사람이 정한 규칙과 수학적 모델에 의존하던 작업을 데이터로부터 복잡한 패턴을 학습하는 방식으로 크게 발전시킨 것에 가까워.

먼저 두 모델을 구분하고, 딥러닝 이전에는 어떻게 구현했는지 살펴보자.

# 1. Demucs와 Whisper는 어떤 AI 모델인가?

[Frontiers | Music Demixing Challenge 2021](https://images.openai.com/static-rsc-4/MCF52JxduNlvJDk6jh0qq-g6WgPlqDQC_iHwEQCa__J5jtN2ho2uw0dnSTcpXiod68vFMV4KclRfD0CHGanW9HqgoTsgicVkJ6956EO2M2kEYz9YxfldQMeooGmGwr57OUUzaqUCUKvHCHPiBo31riwVD1HC48FfyB44DGEZv1A?purpose=inline)

Demucs — 음악 소스 분리(Source Separation)

음악 파일 하나에 섞여 있는 보컬, 드럼, 베이스, 기타 반주 등의 구성 요소를 분리하는 딥러닝 모델이야.

입력: 여러 소리가 섞인 음악

출력: 보컬·드럼·베이스·기타 반주 등의 개별 오디오

[How Whisper Works: OpenAI’s Speech-to-Text Model Explained | by Helen K Joy | Medium](https://images.openai.com/static-rsc-4/2jQN0R2yZgx1hAZJuwyawjOFU0j64EiOCvwyL9skCEoacFfsDraC5N5V5iGZjcM-fZiYCwuQZ47Q_LfO6cK8V6u40c-nervSbc0xMeINKRQ_qszXSnw-cdRBz6PWrME2qTl0q210BkbivwEJpmx6Z-KsTzXHkYu9iH3AWDMCuH4?purpose=inline)

Whisper — 음성 인식(ASR, Automatic Speech Recognition)

음성 파형에서 발화 내용을 파악해 텍스트로 변환하는 딥러닝 모델이야.

입력: 사람의 음성

출력: 인식된 문장과 관련 부가 정보

두 모델은 해결하려는 문제가 달라.

- Demucs: 여러 음원이 섞인 신호에서 특정 소리를 분리한다.
- Whisper: 음성 신호에 담긴 언어 정보를 텍스트로 변환한다.

Demucs의 2019년 연구에서는 합성곱 신경망(Convolutional Network)과 순환 신경망 계열 구조를 활용한 음악 분리 모델을 제안했어. 이후 버전에는 Transformer 구조도 도입됐지.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://arxiv.org\&sz=32)

arxiv.org+2



Whisper는 2022년에 공개됐고, Encoder-Decoder Transformer 구조를 사용해. OpenAI가 발표한 자료에 따르면 약 68만 시간의 다국어·다중 작업 음성 데이터를 학습했어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://openai.com\&sz=32)

OpenAI+1



# 2. 딥러닝 이전에는 음악에서 보컬이나 악기를 어떻게 분리했을까?

여기서는 먼저 한 가지 중요한 사실을 이해해야 해.

음악 파일은 여러 소리가 합쳐진 결과물이지, 각 악기의 소리가 독립된 채널로 저장된 파일이 아니야.

예를 들어 다음과 같은 음악이 있다고 해보자.

원본 음악 파일

보컬 + 드럼 + 베이스 + 피아노

하나의 혼합된 오디오 신호

보컬

드럼

베이스

피아노

목표: 혼합된 신호에서 각 구성 요소를 추정해 복원하는 것

수학적으로 단순화하면 다음과 같이 표현할 수 있어.

\\[ x(t)=v(t)+d(t)+b(t)+p(t) \\]

- \\(x(t)\\): 원본 음악 신호
- \\(v(t)\\): 보컬 신호
- \\(d(t)\\): 드럼 신호
- \\(b(t)\\): 베이스 신호
- \\(p(t)\\): 피아노 신호

우리가 원하는 것은 \\(x(t)\\)만 가지고 각각의 원래 신호를 추정하는 일이야.

그런데 이 작업은 생각보다 어려워. 보컬과 피아노가 같은 시간에 울리고, 비슷한 주파수 영역을 차지할 수 있기 때문이야.

딥러닝 이전에는 주로 다음과 같은 방법을 사용했어.

## 방법 A. 주파수 필터링과 EQ

[Understanding the fundamentals of EQ | MusicRadar](https://images.openai.com/static-rsc-4/Jcvw382_YcgP7hgXKQixWhuns_7IDc5KUx3Ffkzqq7aZsz9PiQAYpRr4buqgSnxuib6DVCW8VeoXWZlSLNeUnhaICDLjpQxWE1ueYpZz4V5uj31RfKWA-EmmgQAcYf2P3dtoQYICUFdzt88o_OSdYR2XcR6djYqyBCz3pl__CSQ?purpose=inline)

[musicradar.com](https://www.musicradar.com/how-to/understanding-the-fundamentals-of-eq?utm_source=chatgpt.com)

가장 직관적인 방법이야.

소리에는 주파수라는 물리적 특성이 있어. 예를 들어 저음역대에는 베이스와 킥 드럼이 많이 분포하고, 고음역대에는 심벌즈나 고음 보컬의 성분이 분포할 수 있지.

그러면 특정 주파수만 통과시키거나 제거하는 필터를 적용하는 거야.

- Low-pass filter: 낮은 주파수만 통과
- High-pass filter: 높은 주파수만 통과
- Band-pass filter: 특정 주파수 범위만 통과
- Band-stop filter: 특정 주파수 범위를 제거

그런데 여기에는 근본적인 한계가 있어.

보컬만의 고유한 주파수 영역이 존재하는 것은 아니야.

보컬의 배음과 기타·피아노의 배음은 서로 겹칠 수 있어. 따라서 보컬이 포함된 주파수만 남기려고 하면 다른 악기 소리도 함께 남고, 보컬의 일부도 제거될 수 있어.

즉, 주파수 필터링은 특정 주파수 성분을 제거하는 것이지, 보컬이라는 음원의 정체성을 구분하는 기술은 아니야.

## 방법 B. 스테레오 위상 상쇄(Center Cancellation)

[How to Remove Vocals from a Song: 5 Methods That Actually Work (2026) — Undetectr](https://images.openai.com/static-rsc-4/DFNSuIPMEGYKc5gqLK8HHWF6YZYzwXKAFzhaShDR7lIJ9bqGQsheLIYrRw3jtj6gCEsaWh9yoLSn3jUUVGw7hUUq-pogBXydXTQT8CLhvxpn_nRm3CoVebhcwSZhLKGEITIcyaDeXW4KM2A8lVJdfswI6rHe3K7n1MYS5B-rv78?purpose=inline)

[undetectr.com](https://undetectr.com/blog/remove-vocals-from-song?utm_source=chatgpt.com)

과거 노래방 기기나 보컬 제거 소프트웨어에서 사용된 대표적인 방법이야.

스테레오 음악은 왼쪽(L)과 오른쪽(R) 두 채널로 구성되어 있지.

음악을 믹싱할 때 보컬을 정중앙에 배치하는 경우가 많다는 특성을 이용하는 거야.

왼쪽과 오른쪽 채널에서 동일하게 들어 있는 신호를 서로 상쇄하면 중앙에 위치한 성분을 제거할 수 있어.

수식으로 표현하면 다음과 같아.

\\[ y(t)=L(t)-R(t) \\]

예를 들어 다음과 같은 신호가 있다고 가정해 보자.

\\[ L(t)=V(t)+M_L(t) \\]

\\[ R(t)=V(t)+M_R(t) \\]

여기서 \\(V(t)\\)는 좌우 채널에 동일하게 들어 있는 보컬이야.

\\[ L(t)-R(t)=M_L(t)-M_R(t) \\]

보컬이 제거되는 원리지.

다만 실제 음악에서는 보컬 외에도 베이스, 킥 드럼 등 중앙에 배치된 소리가 함께 제거될 수 있어. 좌우 채널의 차이가 있는 보컬은 완전히 제거되지 않고 남을 수도 있고.

따라서 이것도 진정한 의미의 보컬 추출이라기보다는 스테레오 믹싱 특성을 이용한 보컬 억제에 가까워.

## 방법 C. ICA와 NMF — 통계적·수학적 분리

여기부터는 조금 더 컴퓨터공학적인 이야기야.

대표적인 방법이 ICA(Independent Component Analysis)와 NMF(Non-negative Matrix Factorization)야.

ICA — 독립 성분 분석

[PPT - Introduction to Independent Component Analysis and its generalizations PowerPoint Presentation - ID:6013542](https://images.openai.com/static-rsc-4/3n7uwUfcWUPspG-KOCP2L1UBonTRFuZRokvveQ21isaT8BVU5OVj9EvVsNqcXi1CowPP_7MV560NrMj4YQ7TvJX4Xz5AbduE9Ul1By8WFu2lVd4yVAvWbLpytLCUfaEV4IJf2EmsJcg8yB5Lq8n9lYMj-kp9pgy5e3a80P4N8M4?purpose=inline)

[slideserve.com](https://www.slideserve.com/alea-hall/introduction-to-independent-component-analysis-and-its-generalizations?utm_source=chatgpt.com)

여러 마이크에서 녹음된 혼합 신호가 있다고 가정해 보자.

사람 A와 사람 B가 서로 다른 위치에서 말하고, 마이크 여러 개가 그 소리를 각각 다르게 수신하는 상황이야.

ICA는 관측된 신호들 사이의 통계적 독립성을 활용해 원래의 독립적인 신호들을 추정해.

다만 여러 소스가 섞인 신호를 분리하려면 일반적으로 관측 채널이 충분해야 하고, 소스 간 독립성 등 가정도 필요해.

NMF — 비음수 행렬 분해

[librosa.decompose.decompose — librosa 0.11.0 documentation](https://images.openai.com/static-rsc-4/tpRsdp_HYUxrEpcsGc0rZqPDReQxnAE_j_xwgV0iCA74wbHkGp04ytYfEHTEuff7LRCrQ6QUl6TZeYlgH0H6U-AxhJfokIe43LIT_RIcwqvDZF0s5Z2Y1Z3qwNmdBKwi1DgzPX_nQhRFZjhIbcqHVVB_QZECV-qGyK6ok1LByBg?purpose=inline)

[librosa.org](https://librosa.org/doc/latest/generated/librosa.decompose.decompose.html?utm_source=chatgpt.com)

이 방법은 SongLingo의 음향 시각화에서 다루는 STFT 스펙트로그램과 연결돼.

먼저 오디오를 시간-주파수 행렬로 표현해. 그다음 행렬을 두 개의 작은 행렬로 분해하는 거야.

\\[ X \approx WH \\]

- \\(X\\): 원본 음악의 스펙트로그램
- \\(W\\): 각 소리의 주파수 패턴을 표현하는 기저 행렬
- \\(H\\): 시간에 따라 각 패턴이 얼마나 활성화됐는지 표현하는 행렬

예를 들어 피아노의 특정 음은 고유한 주파수 패턴을 가지겠지. 이 패턴을 \\(W\\)에 표현하고, 실제 음악에서 해당 패턴이 나타나는 시간과 강도를 \\(H\\)로 추정하는 거야.

이렇게 분해한 뒤 특정 성분에 해당하는 부분만 남겨서 오디오를 복원할 수 있어.

특히 NMF는 딥러닝 이전부터 음악 소스 분리 연구에 활용됐어. 2008년 발표된 연구에서도 음악 신호를 행렬로 분해해 악기 성분을 구분하는 접근을 다루고 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://pmc.ncbi.nlm.nih.gov\&sz=32)

pmc.ncbi.nlm.nih.gov+2



여기서 중요한 구분이 있어.

ICA와 NMF는 딥러닝 모델이 아니야. 수학적 최적화와 통계적 가정을 사용해 문제를 해결하는 알고리즘이야. 다만 NMF는 머신러닝의 비지도 학습과 밀접한 관계가 있어. 그러므로 'AI가 아니었다'라고 단정하면 부정확해.

# 3. 딥러닝 이전의 STT는 어떻게 작동했을까?

이쪽은 역사가 더 길어.

1952년 Bell Labs에서 개발한 Audrey라는 음성 인식 시스템이 대표적인 초기 사례야.

[Reconocimiento de voz: definición, origen y aplicaciones tecnológicas](https://images.openai.com/static-rsc-4/qBGk2BxCjx-mS6iNf3s_HflzAHfrltufNxY0yayMmEpYPnEcrNPGpKczHV3fOXyerRPaUfy6O6GOKOupkL4RJYBYPPyH0ltQ7icdBPGLkkKM9TYLk_720IB5K-EqWVQs03nIQ5UPAfnU1aHvI7aBCA_6Ew5CXxFFD0_qnLOZ7jE?purpose=inline)

[liora.io](https://liora.io/es/reconocimiento-de-voz?utm_source=chatgpt.com)

Audrey는 사람이 말한 숫자 0\~9를 인식할 수 있었어. 다만 아무 목소리나 인식하는 것은 아니었어. 미리 등록한 화자의 목소리에 의존했고, 숫자 사이에 충분한 간격을 두고 발음해야 하는 등 제약이 있었지.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://nyuscholars.nyu.edu\&sz=32)

nyuscholars.nyu.edu+2



1961년에는 IBM이 Shoebox라는 음성 인식 시스템을 공개했어. 숫자와 `plus`, `minus`, `total` 같은 제한된 명령어를 인식해서 계산할 수 있었지.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.ibm.com\&sz=32)

ibm.com



그렇다면 당시에는 어떤 원리로 작동했을까?

## ① 초창기: 미리 저장한 음성 패턴과 비교

예를 들어 컴퓨터에 다음과 같은 음성 패턴을 미리 저장한다고 생각해 보자.

| 단어  | 저장된 음성 특징 |
| ----- | ---------------- |
| ONE   | 패턴 A           |
| TWO   | 패턴 B           |
| THREE | 패턴 C           |

새로운 음성이 들어오면 저장된 패턴과 비교해 가장 유사한 것을 선택하는 거야.

그런데 사람마다 발음 속도가 다르잖아?

같은 'hello'라도 어떤 사람은 짧게 말하고, 어떤 사람은 길게 말할 수 있어.

그래서 DTW(Dynamic Time Warping)라는 알고리즘이 등장해.

DTW는 시간축이 서로 다르게 늘어나거나 줄어든 두 신호를 비선형적으로 정렬해 유사도를 계산하는 기법이야.

예를 들어 다음 두 음성을 비교한다고 해보자.

- A: `hello`를 0.5초에 발음
- B: `hello`를 0.9초에 발음

단순히 같은 시간 위치끼리 비교하면 일치하지 않겠지만, DTW는 시간축을 유연하게 정렬해서 비교할 수 있어.

## ② 1980\~1990년대: HMM-GMM 기반 음성 인식

[Introduction to Automatic Speech Recognition (ASR) -](https://images.openai.com/static-rsc-4/hzcOuXPx5xgf4lY8l-B87nvJJM-9ZqrQv4fbGoRdW_Apx2wjM8eg_AGITRmlt3Ff_enm1RUIkhkEAKDevFZjnoQhdwcQk1XWEoawkiOiQlawo9k9i307G0z99WX8YXf9Q68Doyn9xVOgmMFIiTB1AnEoZpbTvGSJwoKLDam0bTk?purpose=inline)

[maelfabien.github.io](https://maelfabien.github.io/machinelearning/speech_reco/?utm_source=chatgpt.com)

이 시대가 상당히 중요해.

HMM(Hidden Markov Model)은 관측할 수 없는 상태가 시간에 따라 변화하고, 그 상태에 따라 관측값이 생성된다고 가정하는 확률 모델이야.

음성 인식에서는 음성 신호 뒤에 숨어 있는 음소의 상태를 추정하는 데 사용했어.

예를 들어 `CAT`이라는 단어를 생각해 보자.

\\[ CAT \rightarrow /k/ \rightarrow /æ/ \rightarrow /t/ \\]

컴퓨터는 음성 파형을 일정한 짧은 프레임으로 나누고, 각 프레임의 음향적 특성을 추출해.

대표적으로 사용한 것이 다음과 같아.

- LPC(Linear Predictive Coding)
- MFCC(Mel-Frequency Cepstral Coefficients)

이 특징들을 바탕으로 어떤 음소 상태에서 음성이 발생했을 가능성이 높은지를 GMM(Gaussian Mixture Model) 등으로 추정했어.

그리고 HMM과 Viterbi 알고리즘 등을 이용해 가장 가능성이 높은 음소와 단어의 경로를 찾아냈지.

여기서 실제 문장 인식은 음향 모델만으로 끝나지 않아.

\*\*언어 모델(Language Model)\*\*도 함께 사용했어.

예를 들어 다음 두 문장을 비교해 보자.

- `I scream`
- `ice cream`

소리만 들으면 구분하기 어려울 수 있어. 이때 언어 모델은 단어의 출현 확률과 문맥을 이용해 더 자연스러운 문장을 선택하는 역할을 해.

정리하면 전통적인 STT는 다음과 같은 파이프라인이었어.

1

음성 입력

마이크로 수집한 음성 파형

2

특징 추출

LPC, MFCC 등으로 음향 특징 계산

3

음향 모델

HMM-GMM으로 음소 상태의 확률 추정

4

발음 사전

음소와 단어 사이의 관계 확인

5

언어 모델 + 디코딩

문맥과 단어 확률을 고려해 최적의 문장 선택

이 방식은 1990년대부터 2000년대까지 상용 음성 인식 시스템의 핵심 기반이었어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://web.stanford.edu\&sz=32)

AUTOMATIC SPEECH RECOGNITION AND TEXT-TO-SPEECH+2



# 4. 그러면 딥러닝은 무엇을 바꾼 걸까?

핵심은 특징을 설계하는 방식과 소리의 패턴을 학습하는 방식이 바뀌었다는 점이야.

전통적인 방식에서는 개발자가 음성을 분석하는 특징을 직접 설계하고, 여러 단계의 통계 모델과 규칙을 조합해야 했어.

딥러닝에서는 대규모 데이터를 이용해 신경망이 음성과 텍스트 사이의 복잡한 관계를 학습하게 할 수 있어.

| 구분      | 전통적 방식                       | 딥러닝 방식                                       |
| --------- | --------------------------------- | ------------------------------------------------- |
| 음악 분리 | 주파수 필터, ICA, NMF 등          | Demucs 등 신경망                                  |
| 음성 인식 | DTW, HMM-GMM, 언어 모델           | Whisper 등 Transformer                            |
| 특징 활용 | 사람이 특징을 설계하는 비중이 큼  | 신경망이 표현을 학습                              |
| 데이터    | 패턴 사전, 통계 모델, 학습 데이터 | 대규모 학습 데이터                                |
| 한계      | 사전에 둔 가정과 규칙에 민감      | 학습 데이터와 모델의 한계, 환각·오류 및 계산 비용 |

그렇다고 딥러닝이 모든 면에서 완벽한 것은 아니야. 음악 소스 분리에서도 보컬과 반주가 완전히 분리되지 않거나 원본에 없던 음향적 왜곡이 생길 수 있어. Whisper도 발음을 잘못 인식할 수 있지.

# 5. SongLingo에 대입하면 더 잘 이해할 수 있어

지금 만들고 있는 SongLingo의 처리 과정을 생각해 보자.

① 음악에서 보컬 추출

딥러닝

Demucs

음악 파일 → 보컬 트랙 + 반주 트랙

② 사용자의 발음 녹음

딥러닝

Whisper

사용자 음성 → 인식된 문장

③ 기준 문장과 인식 문장 비교

전통 알고리즘

Edit Distance

기준 문장과 인식 문장의 삽입·삭제·대체 횟수 계산 → WER/CER

④ 음향 특징 분석

신호처리

STFT / FFT / Log-Mel / pYIN

주파수, 시간에 따른 에너지 분포, 기본 주파수(F0) 추정

⑤ 선택적 외부 발음 평가

AI 기반 서비스

Azure Pronunciation Assessment

발음 정확도, 유창성 등 별도의 평가 결과 제공

이 구조에서 중요한 점은 SongLingo가 AI 모델만으로 작동하는 애플리케이션은 아니라는 거야.

- Demucs와 Whisper는 딥러닝 모델이야.
- WER/CER 계산은 편집 거리 기반의 알고리즘이야.
- STFT와 FFT는 디지털 신호처리 알고리즘이야.
- pYIN은 기본 주파수를 추정하는 알고리즘이야.
- Azure는 외부의 AI 기반 발음 평가 서비스를 활용하는 부분이야.

즉, 현대적인 AI 애플리케이션은 딥러닝 모델, 수학적 알고리즘, 전통적인 신호처리, 데이터베이스와 소프트웨어 엔지니어링이 결합된 시스템이라고 이해하면 정확해.

# 6. 이 주제에서 꼭 기억할 세 가지

1\. 딥러닝 이전에도 음성 인식과 음원 분리는 가능했어. 다만 제한된 어휘, 특정 화자, 특정 녹음 환경 또는 강한 수학적 가정에 의존하는 경우가 많았어.

2\. AI와 딥러닝은 동의어가 아니야. HMM 같은 통계적 학습 방식도 넓은 의미에서 AI의 역사에 포함돼. 신경망을 사용하지 않는다고 해서 반드시 AI가 아닌 것은 아니야.

3\. 딥러닝은 기존 신호처리와 알고리즘을 대체하기만 한 것이 아니야. 오히려 FFT, STFT, MFCC 같은 전통적인 신호처리 기법은 딥러닝 모델에서도 여전히 중요하게 사용돼. Whisper가 Log-Mel 스펙트로그램을 입력 표현으로 사용하는 것이 대표적인 예야.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://openai.com\&sz=32)

OpenAI+1



특히 네가 지금 SongLingo에서 Demucs, Whisper, STFT, FFT, Log-Mel, pYIN을 함께 다루는 것은 꽤 좋은 학습 사례야. 하나의 애플리케이션을 만들면서 디지털 신호처리(DSP) → 통계적 패턴 인식 → 머신러닝 → 딥러닝 → 응용 소프트웨어 아키텍처라는 기술의 발전 흐름을 실제 코드로 경험하고 있기 때문이야.

다음 단계로는 STFT 스펙트로그램을 NMF로 분해하면 어떻게 악기별 소리를 추정할 수 있는지를 수식과 Python 예제로 연결해 보면 좋아.

---
그런데 demucs에서 사용한 신경망? 중 lstm, attention, transformer 다 딥러닝을 이용한 자연어 처리 모델들 아니야..? 부트캠프 수업에서도 , 책 “모두의 딥러닝(개정 4판)”에도 그렇게 분류되고 다뤄지는 것 같은데.. 그런데 어떻게 demucs에서 소리 데이터 처리에 이 모델들의 층?이 사용되는 거야..? => [현재 서울 날짜 및 시각 2026-11-09 22:14:00]

이 질문은 딥러닝 아키텍처를 이해하는 데 상당히 중요한 지점이야. 지금 혼동하는 이유는 자연스러워. 부트캠프나 딥러닝 교재에서는 LSTM, Attention, Transformer를 주로 자연어 처리(NLP) 문제와 연결해 설명하기 때문이야.

그런데 여기서 핵심적인 개념을 하나 구분해야 해.

LSTM, Attention, Transformer는 자연어를 처리하기 위해서만 만들어진 기술이 아니야. 순서가 있는 데이터(sequence data)의 관계와 패턴을 학습하기 위한 범용적인 신경망 구조 또는 메커니즘이야.

자연어도 순서가 있는 데이터이고, 음악도 순서가 있는 데이터야. 따라서 같은 아키텍처를 사용할 수 있어.

# 1. NLP와 오디오 처리에서 입력 데이터가 어떻게 다를까?

우선 컴퓨터가 실제로 처리하는 데이터를 비교해 보자.

## ① 자연어 처리에서의 입력

예를 들어 다음 문장이 있다고 해보자.

> I love music.

컴퓨터는 이 문장을 그대로 이해하지 못해. 먼저 토큰화하고, 각 토큰을 임베딩 벡터로 변환하지.

Text input

I

love

music

Token Embedding

각 단어를 수치 벡터로 변환

Sequence of vectors

v₁ → v₂ → v₃

결국 신경망이 입력으로 받는 것은 단어 그 자체가 아니라, 시간적·순차적 순서가 있는 벡터들의 집합이야.

## ② 오디오 처리에서의 입력

이번에는 음악 파일을 생각해 보자.

디지털 오디오는 일정한 시간 간격으로 측정한 진폭(amplitude) 값들의 연속이야.

예를 들어 44.1kHz 오디오라면 1초에 44,100개의 샘플이 존재하지.

Audio input

시간에 따른 오디오 진폭 변화

Audio Encoder

Convolution으로 음향 특징 추출

Sequence of feature vectors

h₁ → h₂ → h₃ → h₄ → ...

여기서 중요한 부분은 Audio Encoder야.

음성이나 음악 신호를 그대로 LSTM에 전달하는 것만이 아니라, 앞쪽의 Convolutional Layer 등이 오디오 신호에서 특징을 추출하고, 그 특징들을 시간 순서대로 배열해 LSTM이나 Attention에 전달할 수 있어.

예를 들어 다음과 같이 표현할 수 있지.

\\[ H = [h_1,h_2,h_3,\ldots,h_T] \\]

- \\(T\\): 시간 순서에 따른 특징 벡터의 개수
- \\(h_i\\): 해당 시간 구간에서 추출한 특징 벡터

이때 \\(h_i\\)는 단어의 임베딩이 아니라 오디오에서 추출한 음향 특징의 임베딩이야.

즉, 두 분야가 사용하는 데이터의 의미는 다르지만 신경망에 입력되는 구조는 비슷하게 만들 수 있어.

# 2. 그렇다면 LSTM은 오디오에서 무엇을 학습할까?

먼저 LSTM을 다시 생각해 보자.

LSTM(Long Short-Term Memory)은 RNN(Recurrent Neural Network)의 한 종류야.

자연어 처리에서 LSTM을 사용하는 이유는 문장 안에서 앞서 등장한 단어의 정보를 뒤에 등장하는 단어를 처리할 때 활용할 수 있기 때문이지.

그런데 이 특성은 음악에서도 유용해.

예를 들어 기타의 음이 일정 시간 지속되다가 다른 음으로 바뀌는 상황을 생각해 보자.

현재 시점의 소리만 살펴보면 그 소리가 기타인지, 보컬인지, 피아노인지 판단하기 어려울 수 있어.

하지만 이전 시점과 이후 시점의 소리 변화까지 고려하면 판단에 도움이 되는 정보가 늘어나.

LSTM은 바로 이런 시간적 관계를 학습할 수 있어.

음악에서 LSTM이 처리하는 시간 순서

t₁

기타 시작

t₂

음 지속

t₃

보컬 시작

t₄

드럼 추가

LSTM

이전 시간 구간의 정보와 현재 입력을 결합해 새로운 상태를 계산

음향 특징의 시간적 변화와 장기적인 의존 관계를 학습

LSTM의 핵심 수식은 다음과 같아.

\\[ h_t,c_t = \operatorname{LSTM}(x_t,h\_{t-1},c\_{t-1}) \\]

여기서:

- \\(x_t\\): 현재 시간의 입력 특징
- \\(h\_{t-1}\\): 이전 시점의 은닉 상태
- \\(c\_{t-1}\\): 이전 시점의 셀 상태
- \\(h_t,c_t\\): 현재 계산된 상태

자연어 처리에서는 이전 단어의 정보가 다음 단어 처리에 영향을 주고, 음악 처리에서는 이전 구간의 음향 정보가 다음 구간을 분석하는 데 영향을 주는 거야.

LSTM이라는 구조는 동일하고, 학습 데이터와 입력 특징이 달라지는 거지.

실제로 최초 Demucs 논문에서 사용한 모델은 U-Net 형태의 Convolutional Encoder-Decoder 구조에 양방향 LSTM(Bidirectional LSTM)을 중간에 배치했어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://openreview.net\&sz=32)

openreview\.net+1



# 3. Attention은 음악에서 어떻게 작동할까?

Attention도 마찬가지야.

자연어 처리에서 Attention을 배울 때 흔히 이런 예시를 사용하지.

> The animal didn't cross the street because it was too tired.

여기서 `it`이 무엇을 가리키는지 판단할 때, 문장 안의 다른 단어들에 주의를 기울이는 방식이야.

하지만 Attention의 본질은 언어적 의미를 이해하는 것이 아니야.

하나의 위치에서 다른 위치들의 정보를 얼마나 참고할 것인지 계산하는 메커니즘이야.

음악에서도 똑같이 활용할 수 있어.

예를 들어 현재 구간의 소리를 분석하면서 이전에 등장했던 비슷한 리듬이나 음색의 패턴을 참고할 수 있겠지.

Attention은 일반적으로 다음과 같이 설명할 수 있어.

\\[ Attention(Q,K,V) = softmax\left( \frac{QK^T}{\sqrt{d_k}} \right)V \\]

각 요소를 음악에 대입해 보자.

| 요소             | 자연어 처리        | 음악 처리                 |
| ---------------- | ------------------ | ------------------------- |
| Query(Q)         | 현재 단어의 표현   | 현재 오디오 구간의 특징   |
| Key(K)           | 다른 단어들의 표현 | 다른 오디오 구간들의 특징 |
| Value(V)         | 참고할 단어 정보   | 실제로 가져올 음향 정보   |
| Attention Weight | 단어 간 관련성     | 시간 구간 간 관련성       |

예를 들어 특정 구간의 보컬을 분리할 때, 다른 시간 구간에서 나타난 보컬의 특징을 참고하도록 학습할 수 있어.

다만 여기서 주의할 점이 있어.

모델이 Attention을 사용한다고 해서 특정 시점의 소리가 무조건 보컬이라고 판별하는 것은 아니야. Attention은 학습된 표현 사이의 정보 관계를 계산하는 메커니즘이고, 실제 보컬·악기 분리 능력은 전체 네트워크와 학습 데이터, 손실 함수 등이 함께 만들어 내는 결과야.

# 4. Transformer도 결국 같은 원리야

이제 Transformer를 보자.

Transformer는 Attention을 핵심 구성 요소로 사용하는 신경망 아키텍처야.

2017년에 발표된 논문 Attention Is All You Need에서 자연어 번역 문제를 대상으로 제안됐지.

[The Illustrated Transformer – Jay Alammar – Visualizing machine learning one concept at a time.](https://images.openai.com/static-rsc-4/UMi_8NQxfMLEaLGaH1iWeDjSMxVSh7EZzXi4DJpHoH4k5HFNiegBSBQkcimaolkncuIy2XpYkgee44hcvC1r2q7htaDcWUT7--yy69lLHKQJunWRr3E6bQb2_umUPh4n2PypcGaJ-PYw88qlqFfooT3HKRAved1-RReDMeXzQy8?purpose=inline)

[jalammar.github.io](https://jalammar.github.io/illustrated-transformer/?utm_source=chatgpt.com)

그런데 Transformer의 내부 계산은 특정 언어에 종속되어 있지 않아.

입력 데이터가 텍스트 토큰 임베딩이든, 이미지 패치 임베딩이든, 오디오 특징 벡터든, 일정한 벡터 표현으로 만들어지면 Attention을 적용할 수 있어.

실제로 Transformer는 자연어 처리뿐 아니라 컴퓨터 비전, 음성 인식, 시계열 분석 등 다양한 분야에서 사용돼.

여기서 핵심은 다음과 같아.

- NLP의 Transformer: 단어 또는 토큰 사이의 관계를 학습
- 오디오의 Transformer: 시간 구간 또는 음향 특징 사이의 관계를 학습
- 이미지의 Transformer: 이미지 패치 사이의 관계를 학습

같은 Transformer라는 구조라도 무엇을 입력받고 무엇을 예측하도록 학습하는지에 따라 역할이 달라져.

# 5. 실제 Demucs는 어떻게 이 구조들을 조합했을까?

여기서 네 질문에 대한 가장 직접적인 답이 나와.

Demucs는 하나의 고정된 모델이 아니고, 버전이 발전하면서 아키텍처도 달라졌어.

이 차이를 구분해야 해.

## ① Original Demucs

최초 구조

[image](https://www.google.com/s2/favicons?domain=https://openreview.net\&sz=32)

openreview\.net

[Music Source Separation in the waveform domain - jaechang’s blog](https://images.openai.com/static-rsc-4/Lh2jzxOm_d6wqqNAp_AjB-nOhHj2Q28saynUFY1lNc6XT7BmWsFZOvwQ2TIL2CDLgrrfyvlDOdvLnO-6Xrb43_kG9F3sBKotFiT1vFvV1Updxp9RvwXvlTOaamQPN9dcgxniEc5HszXiK9o9XpViVS24WKNRkRxPqsHwEmJii_w?purpose=inline)

[jaechang.dev](https://jaechang.dev/paper%20-%20audio/paper-demucs/?utm_source=chatgpt.com)

최초 Demucs의 구조를 간단하게 표현하면 다음과 같아.

입력: 원본 Waveform

Convolutional Encoder

시간축을 압축하며 음향 특징 추출

Bidirectional LSTM

시간 순서의 앞·뒤 방향 정보를 함께 처리

Convolutional Decoder

특징을 다시 오디오 파형으로 복원

분리된 음원

여기서 BiLSTM은 원본 음악 파형 전체를 직접 받아 처리하는 것이 아니라, Encoder가 압축한 음향 특징을 처리해.

즉, LSTM이 문장을 처리하는 것과 원리는 비슷하지만, 그 입력이 단어 임베딩이 아니라 오디오의 잠재 특징(latent features)인 거야.

## ② Hybrid Demucs — v3

Waveform + Spectrogram

2021년 발표된 Hybrid Demucs에서는 중요한 변화가 생겨.

기존에는 시간 영역의 Waveform을 중심으로 처리했지만, 이번에는 두 가지 입력 표현을 함께 활용하는 구조를 도입했어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://mdx-workshop.github.io\&sz=32)

mdx-workshop.github.io+1



[Architectures — Open-Source Tools & Data for Music Source Separation](https://images.openai.com/static-rsc-4/w47gwPvPGqw17rd9CXTeDfYkd-d6fT6hImfA6HwsVd8fJUpn_7XBps4BY2m6HtkpwL4PuRNomq-WilCrXMmJwfdTHhOpvZxHvc1enPoTksOY_EXyFPmUn4ZdQwVJ9PdVOQOaIj1Oc-d2D0gB990gtVtafYryaQdJ4gCFZj07Lfo?purpose=inline)

[source-separation.github.io](https://source-separation.github.io/tutorial/approaches/deep/architectures.html?utm_source=chatgpt.com)

두 개의 처리 경로가 존재해.

| 경로            | 입력             | 주요 처리               |
| --------------- | ---------------- | ----------------------- |
| Temporal branch | 원본 Waveform    | 시간 영역 Convolution   |
| Spectral branch | STFT Spectrogram | 주파수 영역 Convolution |

그리고 두 경로의 특징을 결합하는 구조를 사용하지.

여기서 LSTM과 Attention도 사용돼.

논문은 압축된 Residual Branch에 dilated convolution, LSTM, Attention을 도입했다고 명시하고 있어. 특히 Attention은 local content를 중심으로 활용했어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://mdx-workshop.github.io\&sz=32)

mdx-workshop.github.io+1



## ③ Hybrid Transformer Demucs — v4

Transformer 기반 최신 주요 구조

네가 SongLingo에서 사용하고 있는 Demucs가 `htdemucs`라면 바로 이 계열이야.

v4에서는 Hybrid Demucs의 중간에 있는 계층 일부를 Cross-domain Transformer Encoder로 교체했어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



[\[Paper 리뷰\] Hybrid Transformers for Music Source Separation](https://images.openai.com/static-rsc-4/dFWyBw5EIirvhSbpJGLcCcFfNzkaTBVw6gQGAwQ4jD2Ysld4F3ccnZnNPtpoHXU-pAPbmXYJ457JXxNSTO0R24Fnya2n3aODZgTLWqaSGIlzwd4TbEkpkHYhRoJyR_0cnKAZ2tnq7jdJcn8VMdc7YXYjON0QYFxJ3VuCNir7k5A?purpose=inline)

[randomsampling.tistory.com](https://randomsampling.tistory.com/62?utm_source=chatgpt.com)

핵심은 두 가지 정보를 함께 활용한다는 점이야.

- Temporal domain: 원본 오디오의 시간적 특징
- Spectral domain: STFT로 변환한 주파수별 특징

Transformer는 각 영역 내부에서 Self-Attention을 수행하고, 두 영역 사이에서는 Cross-Attention을 수행해.

| Attention 종류  | Demucs에서 하는 일                                |
| --------------- | ------------------------------------------------- |
| Self-Attention  | 같은 영역 안의 특징들이 서로 정보를 참고          |
| Cross-Attention | 시간 영역과 주파수 영역의 특징이 서로 정보를 교환 |

예를 들어 시간 영역에서는 소리가 언제 시작하고 얼마나 지속되는지를 학습하는 데 유용한 단서가 있고, 주파수 영역에서는 특정 시간 구간에 어떤 주파수 성분이 분포하는지를 살펴볼 수 있어.

두 영역의 정보를 함께 활용하면 분리 모델이 더 풍부한 음향 정보를 활용할 수 있는 거야.

공식 저장소 README도 v4를 Hybrid Spectrogram/Waveform 모델이라고 설명하며, 내부의 Transformer가 Self-Attention과 Cross-Attention을 사용한다고 명시하고 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



# 6. 지금까지 배운 딥러닝 지식을 어떻게 확장하면 될까?

이 내용을 표로 다시 정리하면 다음과 같아.

| 기술        | 교재에서 주로 접하는 분야 | Demucs에서 활용되는 분야       |
| ----------- | ------------------------- | ------------------------------ |
| CNN         | 이미지 분류               | Waveform·Spectrogram 특징 추출 |
| RNN         | 문장 순서 학습            | 시간에 따른 음향 패턴 학습     |
| LSTM        | 문맥과 장기 의존성        | 음악의 시간적 의존성           |
| Attention   | 단어 간 관계 파악         | 오디오 구간 간 정보 관계       |
| Transformer | 기계 번역·언어 모델       | 시간·주파수 영역의 특징 통합   |

여기서 정말 중요한 관점이 하나 있어.

신경망 아키텍처와 데이터 도메인은 별개의 개념이야.

예를 들어 LSTM이라는 엔진을 만들었다고 생각해 보자. 그 엔진은 입력으로 순서가 있는 벡터를 받아들이고, 이전 정보와 현재 정보를 결합하는 기능을 수행해.

그 벡터가 다음 중 무엇인지는 별개의 문제야.

- 문장 속 단어의 임베딩
- 음악의 음향 특징
- 주식 가격의 시간별 변화
- 센서에서 측정한 온도와 진동
- 영상에서 추출한 프레임별 특징

따라서 동일한 LSTM을 금융 데이터의 시계열 분석에 사용할 수도 있어. 네가 업무에서 다루는 시장 데이터나 거래량, 가격, 변동성 지표도 시간 순서가 있는 데이터라는 점에서는 음악과 공통점이 있지.

다만 각 도메인의 데이터 특성과 예측 목표가 다르므로 전처리, 입력 표현, 모델 구조, 학습 목적은 각각 설계해야 해.

## 내가 권하는 다음 학습 순서

지금 단계에서는 자연어 처리 모델을 다시 공부하기보다, 이미 배운 신경망 구조를 오디오 데이터에 적용하면 입력과 출력이 어떻게 바뀌는지를 살펴보는 게 좋아.

1. `CNN → LSTM → Decoder` 구조로 최초 Demucs의 작동 원리 이해하기
2. Waveform과 STFT Spectrogram을 각각 CNN에 입력했을 때 텐서의 차원 변화 이해하기
3. Transformer의 Self-Attention과 Cross-Attention이 두 가지 오디오 표현을 어떻게 결합하는지 이해하기

특히 다음 세 가지 질문을 이어서 탐구하면 Demucs의 내부 구조를 훨씬 깊이 이해할 수 있어.

- 텐서 관점: Demucs의 Convolutional Encoder를 거친 오디오 데이터는 정확히 어떤 shape의 텐서가 되고, LSTM에는 어떤 형태로 입력될까?
- Attention 관점: Query, Key, Value는 실제 오디오의 어떤 특징을 나타내며, Self-Attention과 Cross-Attention은 계산상 어떻게 다를까?
- 학습 관점: Demucs는 정답 보컬 파일과 원본 음악 파일을 어떻게 비교하면서 보컬을 분리하는 방법을 학습할까?

이 중 첫 번째인 텐서의 차원 변화부터 이해하면, NLP 교재에서 배운 이론과 실제 오디오 모델 사이의 연결이 가장 명확해질 거야.