설명된 CNN과 Transformer 구조에 대한 구체적 수식 유도 요청 => [2026-11-10 19:52:00] 이번에는 CNN과 Transformer를 단순히 개념적으로 비교하는 수준에서 한 단계 더 들어가 보자.
목표는 각 연산이 어떤 수학적 원리로 동작하고, 입력 데이터가 어떤 계산을 거쳐 다음 Feature로 변환되는지 직접 유도하는 것이야.
특히 지금 공부하는 Song Lingo의 Whisper + HTDemucs 구조에 연결해서 설명할게.
전체 학습 순서는 다음과 같이 구성하겠어.

1. CNN의 Convolution 연산 유도
2. CNN Encoder의 Downsampling과 Feature Extraction
3. CNN Decoder와 Skip Connection의 수식
4. Transformer의 Self-Attention 유도
5. Transformer의 Multi-Head Attention과 Encoder-Decoder Attention
6. Whisper와 HTDemucs에 각각 적용

# 1. CNN: Convolution 연산의 수학적 원리

## 1-1. Convolution은 무엇을 계산하는가?

CNN의 핵심은 Kernel(또는 Filter)이라는 작은 가중치 행렬을 입력 데이터에 적용하는 거야.

먼저 1차원 데이터를 예로 들어보자.

입력 데이터가 다음과 같다고 가정할게.

\\[ X=[1,2,3,4,5] \\]

Kernel은 다음과 같아.

\\[ W=[1,0,-1] \\]

Bias는 0이라고 가정하자.

Kernel을 입력 데이터 위에서 한 칸씩 이동시키면서 각 위치의 값을 곱하고 더해.

첫 번째 위치:

\\[ y_1=1(1)+2(0)+3(-1) \\]

\\[ y_1=-2 \\]

두 번째 위치:

\\[ y_2=2(1)+3(0)+4(-1) \\]

\\[ y_2=-2 \\]

세 번째 위치:

\\[ y_3=3(1)+4(0)+5(-1) \\]

\\[ y_3=-2 \\]

결과는 다음과 같아.

\\[ Y=[-2,-2,-2] \\]

1D Convolution 연산 시각화

입력 X

# 1

# 2

# 3

# 4

# 5

Kernel W

# 1

# 0

# -1

첫 번째 계산

\\[ 1(1)+2(0)+3(-1)=-2 \\]

두 번째 계산

\\[ 2(1)+3(0)+4(-1)=-2 \\]

세 번째 계산

\\[ 3(1)+4(0)+5(-1)=-2 \\]

Output = [-2, -2, -2]

이것이 CNN의 기본적인 연산이야.

정확히 말하면 딥러닝 프레임워크의 `Conv1d`는 수학적인 의미의 Convolution에서 Kernel을 뒤집는 과정 없이 계산하는 Cross-Correlation을 사용해. 학습 과정에서 Kernel Weight가 최적화되므로 일반적으로 CNN의 Convolution이라고 부르는 거야.

## 1-2. 왜 이런 연산이 특징을 추출하는 것일까?

방금 사용한 Kernel을 다시 살펴보자.

\\[ W=[1,0,-1] \\]

이 Kernel은 앞쪽 값과 뒤쪽 값의 차이를 계산하는 형태야.

\\[ y_i=x_i-x\_{i+2} \\]

즉, 주변 값이 어떻게 변화하는지에 반응하는 필터라고 해석할 수 있어.

예를 들어 다음 입력을 생각해 보자.

\\[ X=[1,2,3,4,5] \\]

계속 증가하는 패턴이기 때문에 결과는 -2로 일정하지.

반대로 다음 입력은 어떨까?

\\[ X=[5,4,3,2,1] \\]

같은 Kernel을 적용하면:

\\[ y_1=5-3=2 \\]

\\[ y_2=4-2=2 \\]

\\[ y_3=3-1=2 \\]

결과는 다음과 같아.

\\[ Y=[2,2,2] \\]

즉, Kernel Weight에 따라 입력의 서로 다른 패턴에 반응하는 거야.

실제 CNN에서는 이런 Kernel Weight를 사람이 직접 지정하지 않아.

초기화된 Weight에서 시작해서 Backpropagation과 Optimizer를 통해 학습해.

따라서 어떤 Kernel은 진폭 변화에, 어떤 Kernel은 주기적인 패턴이나 다른 복합적인 특징에 반응하도록 최적화될 수 있어.

# 2. Conv1d와 Conv2d의 수식 유도

이제 앞에서 배운 내용을 일반화해 보자.

## 2-1. Conv1d

실제 오디오 데이터는 단순한 1차원 배열이 아니라 Channel을 가지고 있어.

예를 들어 Stereo 오디오는 다음과 같이 표현할 수 있지.

\\[ X\in\mathbb{R}^{B\times C\_{in}\times L} \\]

- \\(B\\): Batch Size
- \\(C\_{in}\\): 입력 Channel 수
- \\(L\\): 시간축 길이

Conv1d의 일반적인 연산은 다음과 같아.

\\[ Y[b,o,t] = \sum\_{c=0}^{C\_{in}-1} \sum\_{k=0}^{K-1} W[o,c,k]X[b,c,ts+k-p] +b[o] \\]

여기서:

| 기호       | 의미                      |
| ---------- | ------------------------- |
| \\(b\\)    | Batch Index               |
| \\(o\\)    | Output Channel            |
| \\(c\\)    | Input Channel             |
| \\(t\\)    | Output Time Position      |
| \\(k\\)    | Kernel 내부 위치          |
| \\(K\\)    | Kernel Size               |
| \\(s\\)    | Stride                    |
| \\(p\\)    | Padding                   |
| \\(W\\)    | 학습 가능한 Kernel Weight |
| \\(b[o]\\) | Bias                      |

중요한 것은 Output Channel마다 별도의 Kernel Weight가 존재한다는 거야.

예를 들어:

\\[ X\in\mathbb{R}^{1\times2\times8} \\]

입력 Channel이 2개이고 시간축 길이가 8이라고 하자.

여기에 다음 Conv1d를 적용해.

- Output Channel = 3
- Kernel Size = 3
- Stride = 1
- Padding = 0

출력 길이는:

\\[ L\_{out} = \left\lfloor \frac{L\_{in}+2p-d(K-1)-1}{s}+1 \right\rfloor \\]

Dilation \\(d=1\\)이므로:

\\[ L\_{out} = \frac{8-3}{1}+1=6 \\]

따라서 출력 형태는:

\\[ Y\in\mathbb{R}^{1\times3\times6} \\]

Conv1d 차원 변화

Input

\\[ (1,2,8) \\]

Batch 1 · Channel 2 · Length 8

Conv1d

\\[ K=3,\quad S=1,\quad P=0 \\]

Output Channel = 3

Output

\\[ (1,3,6) \\]

이것이 Demucs의 Waveform Encoder에서 활용하는 기본 연산이야.

## 2-2. Conv2d

이번에는 Spectrogram을 생각해 보자.

스펙트로그램은 시간과 주파수라는 두 축을 가지고 있어.

\\[ X\in\mathbb{R}^{B\times C\_{in}\times F\times T} \\]

Conv2d는 Kernel도 2차원이야.

\\[ W\in\mathbb{R}^{C\_{out}\times C\_{in}\times K_F\times K_T} \\]

연산은 다음과 같아.

\\[ \begin{aligned} Y[b,o,f,t] =&\sum_c\sum_i\sum_j W[o,c,i,j]\\\ &\cdot X[b,c,fs_F+i,ts_T+j] +b[o] \end{aligned} \\]

여기서 \\(s_F\\)와 \\(s_T\\)는 각각 주파수축과 시간축의 Stride야.

즉, Conv2d는 시간과 주파수 방향의 주변 영역을 동시에 살펴볼 수 있어.

예를 들어 Kernel이 다음과 같다고 하자.

\\[ K_F=3,\quad K_T=3 \\]

이것은 주파수 방향 3개, 시간 방향 3개 위치를 함께 처리한다는 뜻이야.

[Artificial Neural Networks (ANN): Understanding the Complete Architecture | by Learner | May, 2026 | Medium](https://images.openai.com/static-rsc-4/NMR6r39S9UKQnr1Bpfh1KsBorkOQ8Qs_Hq5TCKQ6VV2oCtHIInr-FqpdLY7IuWwGCiosy3dFdvf1MBazkMEhNQy8yb3u0w2W1ECTALOLJUh-PA3eeG9TbOsVLL22Md3SvLuQ9GmJo3TbLt4trjCOkMQQxCBo9ta5ox_wMUUo3Nk?purpose=inline)

[medium.com](https://medium.com/%40parulsingh1074/artificial-neural-networks-ann-understanding-the-complete-architecture-a9f9fda18c84?utm_source=chatgpt.com)

### CNN에서 중요한 수학적 특징

Conv1d와 Conv2d의 차이를 다시 정리하면:

- Conv1d: 시간 방향으로 Kernel을 이동시키며 연산
- Conv2d: 시간과 주파수 방향으로 Kernel을 이동시키며 연산

그리고 두 연산 모두 \*\*학습 가능한 가중치의 공유(Weight Sharing)\*\*라는 특성이 있어.

동일한 Kernel을 여러 위치에 적용하기 때문에 파라미터 수를 줄일 수 있고, 위치가 달라져도 유사한 패턴을 인식할 수 있어.

# 3. CNN Encoder: Downsampling과 Feature Extraction

이제 CNN이 여러 Layer를 거치면서 어떻게 압축되는지 보자.

앞에서 이야기했던 Demucs의 Waveform Branch를 예로 들게.

첫 번째 Layer의 입력이 다음과 같다고 하자.

\\[ X_0\in\mathbb{R}^{B\times2\times343,980} \\]

두 번째 Channel은 Stereo의 Left와 Right를 의미해.

네가 첨부한 HTDemucs 장표에서는 다음과 같이 표현했지.

| Layer    | Channel | Length  |
| -------- | ------- | ------- |
| Input    | 2       | 343,980 |
| Conv1d 1 | 48      | 85,995  |
| Conv1d 2 | 96      | 21,499  |
| Conv1d 3 | 192     | 5,375   |
| Conv1d 4 | 384     | 1,344   |

여기서는 각 Layer의 Stride가 4인 구조를 개념적으로 가정하고 있어.

예를 들어 첫 번째 Layer의 출력 길이를 계산해 보자.

\\[ L\_{out} = \left\lfloor \frac{343980+2p-d(K-1)-1}{4}+1 \right\rfloor \\]

실제 출력 길이는 Kernel Size와 Padding 설정에 따라 결정돼.

따라서 Stride가 4라는 정보만으로 정확한 출력 길이를 확정할 수는 없어.

이것은 실제 코드의 `kernel_size`, `padding`, `dilation`까지 확인해야 해.

## 3-1. Channel이 증가하는 이유는?

여기서 흥미로운 점이 있어.

Feature Map의 시간축 길이는 줄어들지만 Channel은 증가하지?

\\[ 2\rightarrow48\rightarrow96\rightarrow192\rightarrow384 \\]

이것은 모델이 서로 다른 종류의 특징을 표현할 수 있도록 Feature Dimension을 확장하는 설계야.

가령 첫 번째 Layer에서 48개의 Output Channel을 만들었다고 하자.

각 Channel은 서로 다른 학습 가능한 Kernel을 가지고 있어.

\\[ Y_1= \begin{bmatrix} Feature_1\\\ Feature_2\\\ \vdots\\\ Feature\_{48} \end{bmatrix} \\]

이 48개 Feature가 각각 보컬, 드럼 등 특정 악기를 전담한다는 의미는 아니야.

서로 다른 음향적 패턴을 표현하는 여러 Feature가 함께 사용되는 거지.

# 4. CNN Decoder와 Skip Connection의 수식

Encoder에서 데이터가 압축됐다면 이제 다시 복원해야 해.

이것이 Decoder의 역할이야.

## 4-1. Transposed Convolution

일반적인 Convolution이 Feature Map을 줄이는 데 사용될 수 있다면, Transposed Convolution은 반대로 출력의 공간적 크기를 확대하는 데 사용할 수 있어.

출력 크기는 다음과 같아.

\\[ L\_{out} = (L\_{in}-1)s -2p+d(K-1)+output\\\_padding+1 \\]

예를 들어:

- Input Length = 4
- Kernel Size = 4
- Stride = 2
- Padding = 1
- Dilation = 1
- Output Padding = 0

이라면:

\\[ L\_{out}=(4-1)\times2-2+3+1 \\]

\\[ L\_{out}=8 \\]

즉:

\\[ 4\rightarrow8 \\]

로 확대되는 거야.

다만 Transposed Convolution은 원본 Convolution의 정확한 역연산은 아니야. 출력 크기를 확대하는 학습 가능한 연산이지.

## 4-2. Skip Connection

이제 Skip Connection의 수식을 다시 보자.

Encoder의 중간 결과를 \\(E\\), Decoder의 결과를 \\(D\\)라고 하자.

HTDemucs에서는 다음과 같은 덧셈 방식으로 결합해.

\\[ Y=D+E \\]

단, 두 Tensor의 Shape가 호환되어야 해.

예를 들어:

\\[ E= \begin{bmatrix} 1&2&3&4\\\ 5&6&7&8 \end{bmatrix} \\]

\\[ D= \begin{bmatrix} 0.1&0.2&0.3&0.4\\\ 0.5&0.6&0.7&0.8 \end{bmatrix} \\]

그렇다면:

\\[ Y= \begin{bmatrix} 1.1&2.2&3.3&4.4\\\ 5.5&6.6&7.7&8.8 \end{bmatrix} \\]

이렇게 Encoder의 Feature와 Decoder의 Feature가 결합돼.

여기서 핵심은 Decoder가 압축된 표현만으로 복원하지 않고, Encoder가 이전에 추출했던 세부 특징도 활용한다는 점이야.

# 5. Transformer: Self-Attention의 수식 유도

이제 Transformer로 넘어가자.

CNN과 Transformer의 가장 중요한 수학적 차이를 이해할 수 있는 부분이야.

CNN은 Kernel을 이용해 주변 데이터를 계산했지.

Transformer는 Query, Key, Value라는 세 가지 벡터를 사용해 데이터 위치 간의 관계를 계산해.

## 5-1. 입력 데이터 X

먼저 3개의 Token이 있다고 가정하자.

\\[ X= \begin{bmatrix} 1&0\\\ 0&1\\\ 1&1 \end{bmatrix} \\]

Shape는:

\\[ X\in\mathbb{R}^{3\times2} \\]

각 행이 하나의 Token이고, 각 Token은 2차원 벡터야.

실제 Transformer에서는 오디오나 텍스트의 특징 벡터가 이 Token 역할을 해.

## 5-2. Query, Key, Value 계산

Transformer는 입력 X를 각각 세 개의 학습 가능한 Weight Matrix와 곱해.

\\[ Q=XW_Q \\]

\\[ K=XW_K \\]

\\[ V=XW_V \\]

여기서:

- Query: 현재 위치가 어떤 정보를 찾는가?
- Key: 각 위치가 어떤 정보를 가지고 있는가?
- Value: 실제로 전달할 정보는 무엇인가?

이것은 직관적인 비유이고, 수학적으로는 학습 가능한 선형 변환이야.

계산을 단순하게 하기 위해 다음과 같이 가정하자.

\\[ W_Q=W_K=W_V=I \\]

여기서 \\(I\\)는 단위행렬이야.

그러면:

\\[ Q=K=V=X \\]

즉:

\\[ Q=K=V= \begin{bmatrix} 1&0\\\ 0&1\\\ 1&1 \end{bmatrix} \\]

실제 모델에서는 이 세 Weight Matrix가 독립적으로 학습돼.

## 5-3. Attention Score 계산

Query와 Key의 내적을 계산해.

\\[ S=QK^T \\]

먼저:

\\[ K^T= \begin{bmatrix} 1&0&1\\\ 0&1&1 \end{bmatrix} \\]

따라서:

\\[ S= \begin{bmatrix} 1&0\\\ 0&1\\\ 1&1 \end{bmatrix} \begin{bmatrix} 1&0&1\\\ 0&1&1 \end{bmatrix} \\]

결과는:

\\[ S= \begin{bmatrix} 1&0&1\\\ 0&1&1\\\ 1&1&2 \end{bmatrix} \\]

이 행렬은 각 Query가 각각의 Key와 얼마나 높은 유사도를 갖는지 나타내는 점수야.

## 5-4. Scaling

그런데 여기서 한 가지 문제가 있어.

벡터의 차원이 커지면 Dot Product의 크기도 커지는 경향이 있어.

이로 인해 Softmax 결과가 지나치게 한쪽으로 치우칠 수 있지.

그래서 다음과 같이 나눠 줘.

\\[ S'=\frac{QK^T}{\sqrt{d_k}} \\]

여기서 \\(d_k\\)는 Key 벡터의 차원이야.

지금은:

\\[ d_k=2 \\]

이므로:

\\[ S'= \frac{1}{\sqrt{2}} \begin{bmatrix} 1&0&1\\\ 0&1&1\\\ 1&1&2 \end{bmatrix} \\]

이것이 Scaled Dot-Product Attention의 Scaling 부분이야.

## 5-5. Softmax

이제 각 행에 Softmax를 적용해.

\\[ Softmax(x_i)= \frac{e^{x_i}}{\sum_j e^{x_j}} \\]

Softmax를 사용하는 이유는 각 Query가 여러 Key를 참고하는 정도를 확률적인 가중치 형태로 변환하기 위해서야.

예를 들어 첫 번째 Query의 Score는:

\\[ [0.707,\ 0,\ 0.707] \\]

이야.

Softmax를 적용하면 대략:

\\[ [0.401,\ 0.198,\ 0.401] \\]

이 돼.

즉, 첫 번째 Query는 첫 번째와 세 번째 Token의 정보를 상대적으로 더 많이 참고하는 거야.

전체 Attention Weight Matrix는 다음과 같이 계산돼.

\\[ A=Softmax\left( \frac{QK^T}{\sqrt{d_k}} \right) \\]

Attention Weight의 의미

아래는 위의 수치 예제에서 계산한 근사값이야.

| Query ↓ / Key → | Token 1 | Token 2 | Token 3 |
| --------------- | ------- | ------- | ------- |
| Token 1         | 0.401   | 0.198   | 0.401   |
| Token 2         | 0.198   | 0.401   | 0.401   |
| Token 3         | 0.248   | 0.248   | 0.504   |

각 행의 합은 약 1이야.

## 5-6. Value와 곱하기

이제 실제 정보를 가져와야 해.

Attention Weight와 Value를 곱해.

\\[ Attention(Q,K,V)=AV \\]

첫 번째 Token의 결과를 계산해 보자.

\\[ Output_1= 0.401V_1+0.198V_2+0.401V_3 \\]

우리가 가정했던 Value를 대입하면:

\\[ =0.401 \begin{bmatrix}1\\\0\end{bmatrix} +0.198 \begin{bmatrix}0\\\1\end{bmatrix} +0.401 \begin{bmatrix}1\\\1\end{bmatrix} \\]

따라서:

\\[ Output_1= \begin{bmatrix} 0.802\\\ 0.599 \end{bmatrix} \\]

첫 번째 Token의 원래 벡터는:

\\[ [1,0] \\]

이었지만, Attention을 거친 후에는:

\\[ [0.802,0.599] \\]

로 바뀌었어.

왜 그럴까?

첫 번째 Token이 두 번째와 세 번째 Token의 정보를 참고해서 새로운 문맥적 표현을 만들었기 때문이야.

이것이 Self-Attention의 핵심이야.

Self-Attention 전체 계산 흐름

Input X

\\[ (3,2) \\]

Q = XWQ

K = XWK

V = XWV

Attention Score

\\[ \frac{QK^T}{\sqrt{d_k}} \\]

Softmax

\\[ A=Softmax(Score) \\]

Weighted Sum

\\[ Output=AV \\]

여기까지가 Transformer에서 가장 중요한 수학적 연산이야.

# 6. Multi-Head Attention은 왜 필요한가?

지금까지는 Query, Key, Value를 한 세트만 사용했어.

이것을 Single-Head Attention이라고 생각하면 돼.

그런데 음악에서는 한 가지 관계만 학습하는 것으로 충분할까?

예를 들어 다음과 같은 관계가 있을 수 있어.

- 서로 가까운 시간에 나타나는 특징
- 멀리 떨어진 시간에 반복되는 패턴
- 보컬과 반주 사이의 관계
- 특정 주파수 대역과 다른 주파수 대역 사이의 관계

하나의 Attention Head만으로 모든 관계를 효과적으로 표현하기 어려울 수 있어.

그래서 여러 개의 Head를 사용하는 거야.

## 6-1. 수식

Head 하나의 계산은 다음과 같아.

\\[ Head_i=Attention(Q_i,K_i,V_i) \\]

여러 Head를 계산한 다음 결과를 연결해.

\\[ MultiHead(Q,K,V) = Concat(Head_1,\ldots,Head_h)W_O \\]

여기서:

- \\(h\\): Head 개수
- \\(W_O\\): 최종 출력 차원을 조정하는 학습 가능한 행렬

[Transformers & Attention Mechanism - Complete NLP Series Part 8 - Wasil Zafar](https://images.openai.com/static-rsc-4/sXKWwFTfbfiwH3JSdQgKx_I3rFkDfSHlOKC2gMCxPQvvBrhWjlDVQrVgY05bjPEXB24oKKf2TAi5klgRS1XLQtF32OPrVCAYgfevW_63npiEzHLdwSyr8aEeqYVlFHmZlANKpMkK56gs_RV27Mm4TImTaR40cSFTs_RjxHiUTxY?purpose=inline)

[wasilzafar.com](https://www.wasilzafar.com/pages/series/nlp/nlp-transformers-attention.html?utm_source=chatgpt.com)

중요한 점은 Head마다 서로 다른 Weight Matrix를 갖는다는 거야.

따라서 각각의 Head가 서로 다른 관계를 학습할 수 있어.

다만 특정 Head가 반드시 보컬만 학습한다거나 드럼만 학습한다고 사전에 정해지는 것은 아니야.

## 6-2. 실제 차원 예시

Whisper의 Medium 모델에서 다음과 같이 가정해 보자.

- Model Dimension: 1024
- Attention Head: 16

그러면 Head 하나의 차원은:

\\[ d_k=\frac{1024}{16}=64 \\]

각 Head는 64차원의 Query, Key, Value를 사용해.

\\[ 1024 \rightarrow 16\times64 \\]

16개의 Head 결과를 Concatenation하면 다시 1024차원이 돼.

이것이 Multi-Head Attention의 기본 구조야.

# 7. Transformer Encoder와 Decoder의 수식 차이

이제 Whisper와 연결해 보자.

## 7-1. Transformer Encoder

Transformer Encoder는 Self-Attention을 수행한 뒤 Feed Forward Network(FFN)를 거쳐.

대표적인 구조를 수식으로 나타내면 다음과 같아.

먼저 Attention:

\\[ Z=MultiHead(X,X,X) \\]

Residual Connection과 Layer Normalization:

\\[ H=LayerNorm(X+Z) \\]

그다음 Feed Forward Network:

\\[ FFN(H)=W_2\sigma(W_1H+b_1)+b_2 \\]

최종 출력:

\\[ Y=LayerNorm(H+FFN(H)) \\]

여기서 \\(\sigma\\)는 활성화 함수야. 현대 Transformer에서는 GELU나 ReLU 등이 사용돼.

왜 FFN이 필요할까?

Attention이 여러 Token의 정보를 서로 결합한다면, FFN은 각 Token의 특징 벡터를 비선형적으로 변환하는 역할을 해.

즉:

- Attention: Token 사이의 정보 결합
- FFN: 결합된 각 Token의 특징 변환

이 두 작업이 반복되면서 문맥적인 표현이 만들어져.

## 7-2. Transformer Decoder

Decoder에는 추가적인 구조가 들어가.

Whisper의 Decoder는 다음 두 가지 Attention을 사용해.

1. Masked Self-Attention
2. Cross-Attention

먼저 Masked Self-Attention을 살펴보자.

일반적인 Self-Attention에서는 모든 Token을 참고할 수 있지만, 텍스트를 생성하는 Decoder에서는 미래 Token을 참고하면 안 돼.

따라서 Attention Score에 Mask를 적용해.

\\[ Attention= Softmax\left( \frac{QK^T}{\sqrt{d_k}}+M \right)V \\]

여기서 \\(M\\)은 미래 Token에 해당하는 위치에 \\(-\infty\\)를 부여하는 Causal Mask야.

예를 들어 세 개의 Token을 생성하는 상황이라면:

\\[ M= \begin{bmatrix} 0&-\infty&-\infty\\\ 0&0&-\infty\\\ 0&0&0 \end{bmatrix} \\]

이렇게 하면 첫 번째 Token은 자기 자신만, 두 번째 Token은 첫 번째와 두 번째 Token만 참고할 수 있어.

Softmax에 \\(-\infty\\)가 들어가면 해당 위치의 가중치는 0이 돼.

## 7-3. Cross-Attention

이제 Whisper에서 가장 중요한 부분이야.

Decoder가 이전에 생성한 텍스트 Token만 참고하는 것이 아니라, Encoder가 생성한 오디오 특징도 참고해야 하잖아?

이때 사용하는 것이 Cross-Attention이야.

수식은 다음과 같아.

\\[ Q=X\_{decoder}W_Q \\]

\\[ K=X\_{encoder}W_K \\]

\\[ V=X\_{encoder}W_V \\]

즉:

- Query는 Decoder에서 가져오고
- Key와 Value는 Encoder에서 가져와.

그다음:

\\[ CrossAttention= Softmax\left( \frac{QK^T}{\sqrt{d_k}} \right)V \\]

이것이 Whisper가 오디오 특징을 참고하면서 텍스트를 생성할 수 있는 핵심 원리야.

Whisper Cross-Attention

Audio Encoder

오디오 문맥

# K, V

Text Decoder

이전까지 생성된 토큰

# Q

Cross-Attention

\\[ Softmax(QK^T/\sqrt{d_k})V \\]

다음 텍스트 Token 예측

이것이 Whisper의 Transformer Decoder가 CNN Decoder와 다른 중요한 이유야.

Whisper의 Decoder는 오디오 파형을 복원하는 것이 아니라, 오디오 Encoder의 특징을 참고해서 다음 텍스트 Token을 생성하는 거야.

# 8. HTDemucs의 Transformer는 무엇이 다른가?

여기서 네 발표 자료의 두 번째 장표로 돌아가 보자.

HTDemucs에서는 Waveform과 Spectrogram을 별도로 처리해.

각각의 CNN Encoder를 통과한 결과가 있다고 하자.

\\[ X_t\in\mathbb{R}^{B\times C_t\times T} \\]

\\[ X_f\in\mathbb{R}^{B\times C_f\times F\times T} \\]

- \\(X_t\\): 시간 영역 Feature
- \\(X_f\\): 주파수·시간 영역 Feature

각 경로의 특징을 Transformer가 처리할 수 있는 Token 형태로 변환해.

예를 들어 시간축을 따라 Feature를 나열하면:

\\[ Z_t\in\mathbb{R}^{B\times T\times D} \\]

스펙트럼 경로는 주파수와 시간 위치를 펼쳐서 Token Sequence로 만들 수 있어.

\\[ Z_f\in\mathbb{R}^{B\times(FT)\times D} \\]

실제 구현에서는 차원 축소 및 Embedding 과정을 거치고, 모든 차원과 Token 구성은 모델 설정에 따라 달라져.

## 8-1. Cross-Domain Attention

HTDemucs의 핵심은 두 표현 사이의 정보를 교환하는 것이야.

시간 영역의 Query가 스펙트럼 영역의 Key와 Value를 참고한다고 가정해 보자.

\\[ Q_t=Z_tW_Q \\]

\\[ K_f=Z_fW_K \\]

\\[ V_f=Z_fW_V \\]

그러면:

\\[ A\_{t\leftarrow f} = Softmax\left( \frac{Q_tK_f^T}{\sqrt{d_k}} \right) \\]

\\[ O_t=A\_{t\leftarrow f}V_f \\]

이것은 시간 영역 Feature가 스펙트럼 영역의 정보를 참고해 새로운 표현을 만드는 계산이야.

반대로 스펙트럼 영역에서 시간 영역의 정보를 참고하는 계산도 가능해.

\\[ A\_{f\leftarrow t} = Softmax\left( \frac{Q_fK_t^T}{\sqrt{d_k}} \right) \\]

\\[ O_f=A\_{f\leftarrow t}V_t \\]

이렇게 서로 다른 표현의 정보를 교환하는 것이 Cross-Domain Transformer의 핵심 아이디어야.

실제 HTDemucs 구현에서는 Self-Attention과 Cross-Attention 블록을 교대로 사용하는 구조를 볼 수 있어.

즉, Whisper의 Cross-Attention은 오디오 Encoder와 텍스트 Decoder 사이의 정보 전달이고, HTDemucs의 Cross-Attention은 Waveform과 Spectrogram 표현 사이의 정보 교환이라는 차이가 있어.

# 9. 두 모델의 수식 구조를 한 번에 비교하기

지금까지의 내용을 Song Lingo 발표에 적용할 수 있도록 정리해 보자.

| 처리 단계 | Whisper                            | HTDemucs                    |
| --------- | ---------------------------------- | --------------------------- |
| 입력 특징 | Log-Mel                            | Waveform + Spectrogram      |
| 초기 연산 | CNN Front-end                      | CNN Encoder 2개             |
| 특징 추출 | Conv + Transformer                 | Conv1d + Conv2d             |
| Attention | Self-Attention                     | Self + Cross-Attention      |
| 중간 표현 | Audio Context                      | Audio Domain Features       |
| Decoder   | Transformer Decoder                | CNN Decoder                 |
| 핵심 연산 | Masked Attention + Cross-Attention | Transposed Conv 계열 + Skip |
| 최종 출력 | Text Token                         | Audio Waveform              |

## 발표에서 설명할 수 있는 핵심 수식

Whisper

CNN Front-end:

\\[ X\_{audio}\xrightarrow{Conv1d}Z \\]

Transformer Encoder:

\\[ H=Encoder(Z) \\]

Transformer Decoder:

\\[ P(y_t|y\_{\<t},H) \\]

이전 텍스트 토큰과 오디오 문맥을 조건으로 다음 토큰을 예측.

HTDemucs

Dual CNN Encoder:

\\[ Z_t=Enc_t(X_t) \\]

\\[ Z_f=Enc_f(X_f) \\]

Cross-Domain Transformer:

\\[ (H_t,H_f)=Transformer(Z_t,Z_f) \\]

Dual CNN Decoder:

\\[ \hat X_t=Dec_t(H_t,Skip_t) \\]

\\[ \hat X_f=Dec_f(H_f,Skip_f) \\]

두 표현을 결합하고 각각의 경로에서 오디오를 복원.

# 10. 다음 단계: 직접 계산해 보는 것이 가장 효과적이야

지금까지 설명한 수식 중에서 특히 중요한 것은 세 가지야.

1. Convolution: 주변 입력값과 Kernel Weight의 곱셈·합산
2. Self-Attention: Query와 Key의 유사도 계산 및 Value의 가중합
3. Cross-Attention: 서로 다른 입력 표현 사이의 정보 교환

이 세 가지를 이해하면 Whisper와 HTDemucs의 주요 연산을 수학적으로 설명할 수 있어.

다만 여기서 한 단계 더 들어가면 중요한 질문이 남아.

왜 CNN과 Transformer의 Weight가 학습 가능한 것인지, 그리고 이 Weight들이 Loss와 Backpropagation을 통해 어떻게 최적화되는지야.

이것까지 연결하면 단순히 모델의 Forward 연산을 이해하는 것을 넘어 실제 학습 원리까지 이해하게 돼.

### 이어서 공부할 세 가지 질문

1. Conv1d의 Kernel Weight와 Transformer의 Query·Key·Value Weight가 역전파를 통해 업데이트되는 과정을 실제 숫자로 유도해 줄 수 있어?
2. Whisper의 Cross-Attention에서 특정 오디오 구간이 특정 텍스트 토큰에 높은 Attention Weight를 갖는 과정을 시각적으로 보여줄 수 있어?
3. HTDemucs의 Waveform과 Spectrogram Branch가 서로 다른 정보를 학습한다는 것을 실제 오디오 파형과 스펙트로그램 예제로 분석해 줄 수 있어?

---
Self-Attention과 Cross-Attention의 차이 예제 생성 => [2026-11-10 19:52:00]

이번에는 Self-Attention과 Cross-Attention을 동일한 숫자 데이터를 사용해서 직접 계산하고, 두 연산이 어떤 차이를 만드는지 비교해 보자.

특히 Whisper와 HTDemucs에서 각각 어떤 역할을 하는지도 연결할게.

핵심 차이는 다음과 같아.

Self-Attention

같은 데이터 내부에서 관계 학습

Input X

Q, K, V 모두 X에서 생성

Attention

Cross-Attention

서로 다른 데이터 사이에서 관계 학습

Input A

Q 생성

Input B

K, V 생성

Attention

# 1. Self-Attention: 같은 데이터 안에서 관계를 학습한다

## 예제: 세 개의 오디오 구간

3개의 오디오 구간이 있다고 가정하자.

| Token | 오디오 구간 | 특징 벡터 |
| ----- | ----------- | --------- |
| A1    | 0\~1초      | [1, 0]    |
| A2    | 1\~2초      | [0, 1]    |
| A3    | 2\~3초      | [1, 1]    |

각 벡터는 실제 오디오 데이터가 아니라 이해를 위해 단순화한 2차원 Feature야.

우리가 알고 싶은 것은 다음과 같아.

- A1은 A2의 정보를 얼마나 참고할까?
- A1은 A3의 정보를 얼마나 참고할까?
- A2와 A3는 서로 어떤 관계가 있을까?

이것을 계산하는 것이 Self-Attention이야.

## Step 1. Q, K, V 생성

입력 행렬을 다음과 같이 정의하자.

\\[ X= \begin{bmatrix} 1&0\\\ 0&1\\\ 1&1 \end{bmatrix} \\]

Transformer는 입력 X에 각각의 Weight Matrix를 곱해.

\\[ Q=XW_Q \\]

\\[ K=XW_K \\]

\\[ V=XW_V \\]

계산을 단순화하기 위해 세 Weight Matrix를 단위행렬로 가정할게.

\\[ W_Q=W_K=W_V=I \\]

그러면:

\\[ Q=K=V=X \\]

즉, 동일한 입력에서 Q, K, V가 만들어지는 거야.

실제 모델에서는 세 Weight Matrix가 서로 다르고 학습을 통해 최적화돼.

## Step 2. Q와 K의 유사도 계산

Attention Score를 계산해 보자.

\\[ S=QK^T \\]

\\[ = \begin{bmatrix} 1&0\\\ 0&1\\\ 1&1 \end{bmatrix} \begin{bmatrix} 1&0&1\\\ 0&1&1 \end{bmatrix} \\]

결과는:

\\[ S= \begin{bmatrix} 1&0&1\\\ 0&1&1\\\ 1&1&2 \end{bmatrix} \\]

이 행렬의 의미는 다음과 같아.

| Query ↓ / Key → | A1  | A2  | A3  |
| --------------- | --- | --- | --- |
| A1              | 1   | 0   | 1   |
| A2              | 0   | 1   | 1   |
| A3              | 1   | 1   | 2   |

예를 들어 첫 번째 행을 보면 A1이 A1, A2, A3 각각과 얼마나 유사한지를 나타내.

## Step 3. Scaling 및 Softmax

Attention Score를 다음과 같이 Scaling해.

\\[ S'=\frac{QK^T}{\sqrt{d_k}} \\]

여기서 \\(d_k=2\\)야.

첫 번째 행은:

\\[ [1,0,1]/\sqrt{2} \\]

\\[ =[0.707,0,0.707] \\]

여기에 Softmax를 적용하면:

\\[ Softmax([0.707,0,0.707]) \\]

\\[ \approx[0.401,0.198,0.401] \\]

전체 Attention Weight Matrix는 다음과 같아.

\\[ A\approx \begin{bmatrix} 0.401&0.198&0.401\\\ 0.198&0.401&0.401\\\ 0.248&0.248&0.504 \end{bmatrix} \\]

Self-Attention Weight 시각화

행은 Query, 열은 Key야. 숫자가 클수록 해당 위치를 더 많이 참고한다는 의미야.

A1

A2

A3

A1

0.401

0.198

0.401

A2

0.198

0.401

0.401

A3

0.248

0.248

0.504

첫 번째 행을 해석해 보자.

A1은 다음과 같이 정보를 참고해.

- 자기 자신 A1: 40.1%
- A2: 19.8%
- A3: 40.1%

즉, A1의 새로운 표현을 만들 때 세 구간의 정보를 모두 활용하는 거야.

## Step 4. Value의 가중합

이제 실제 정보를 결합해.

\\[ Output=AV \\]

첫 번째 Token의 결과는:

\\[ Output_1 = 0.401V_1+0.198V_2+0.401V_3 \\]

각 Value를 대입하면:

\\[ =0.401 \begin{bmatrix}1\\\0\end{bmatrix} +0.198 \begin{bmatrix}0\\\1\end{bmatrix} +0.401 \begin{bmatrix}1\\\1\end{bmatrix} \\]

따라서:

\\[ Output_1= \begin{bmatrix} 0.802\\\ 0.599 \end{bmatrix} \\]

원래 A1은 [1, 0]이었는데 Attention을 통과한 후 [0.802, 0.599]가 됐어.

A2와 A3의 정보가 반영된 거야.

Self-Attention 전후 비교

| 구분    | 첫 번째 특징 | 두 번째 특징 |
| ------- | ------------ | ------------ |
| 입력 A1 | 1.000        | 0.000        |
| 출력 A1 | 0.802        | 0.599        |

주변 Token의 문맥 정보 반영

이것이 Self-Attention이야.

동일한 입력 시퀀스 안에서 각 Token이 다른 Token의 정보를 참고해 새로운 문맥적 표현을 만드는 것이지.

# 2. Cross-Attention: 서로 다른 데이터 사이에서 관계를 학습한다

이번에는 Whisper의 음성 인식 상황을 생각해 보자.

Whisper에는 두 종류의 데이터가 있어.

1. Encoder가 처리한 오디오 특징
2. Decoder가 처리 중인 텍스트 토큰

Decoder가 다음 텍스트를 생성하려면 오디오의 어느 부분을 참고해야 할지 판단해야 해.

예를 들어 오디오에 다음과 같은 발화가 있다고 하자.

> "오늘은 음악을 듣는다."

오디오를 세 구간으로 나누었다고 가정하자.

| 오디오 Token | 내용   | Key / Value |
| ------------ | ------ | ----------- |
| A1           | 오늘은 | [1, 0]      |
| A2           | 음악을 | [0, 1]      |
| A3           | 듣는다 | [1, 1]      |

한편 Decoder에서는 다음 텍스트를 생성하려고 해.

> "오늘은 \_\_\_"

이때 Decoder의 현재 상태에서 Query가 생성된다고 가정하자.

\\[ Q=[0,1] \\]

이것은 단순한 예제 벡터이며, 실제 Transformer에서는 Decoder의 Hidden State에 학습된 Projection을 적용해서 Query를 생성해.

## Step 1. Q, K, V의 출처가 다르다

Cross-Attention에서는 다음과 같아.

\\[ Q=X\_{decoder}W_Q \\]

\\[ K=X\_{encoder}W_K \\]

\\[ V=X\_{encoder}W_V \\]

즉,

Whisper Cross-Attention의 데이터 출처

Text Decoder

# Q

이전 텍스트의 문맥

Audio Encoder

# K, V

오디오의 문맥적 특징

Cross-Attention

텍스트 Query가 오디오 Key와 Value를 참고

Self-Attention에서는 Q, K, V가 동일한 시퀀스에서 생성됐지만, Cross-Attention에서는 Q와 K·V가 서로 다른 시퀀스에서 생성됐다는 점이 핵심이야.

## Step 2. Query와 Key의 유사도 계산

이번에는 Query가 다음과 같아.

\\[ Q=[0,1] \\]

Audio Key는 다음과 같아.

\\[ K= \begin{bmatrix} 1&0\\\ 0&1\\\ 1&1 \end{bmatrix} \\]

계산하면:

\\[ QK^T= \begin{bmatrix} 0&1&1 \end{bmatrix} \\]

Scaling을 적용해.

\\[ S'= \frac{[0,1,1]}{\sqrt{2}} \\]

\\[ =[0,0.707,0.707] \\]

Softmax를 적용하면:

\\[ A\approx[0.198,0.401,0.401] \\]

즉, 현재 Decoder의 Query는 다음과 같이 오디오를 참고해.

| 오디오 구간 | Attention Weight |
| ----------- | ---------------- |
| A1: 오늘은  | 19.8%            |
| A2: 음악을  | 40.1%            |
| A3: 듣는다  | 40.1%            |

여기서 A2와 A3에 상대적으로 높은 가중치가 부여됐어.

## Step 3. Value의 가중합

Value는 Encoder에서 가져온 오디오 특징이야.

\\[ V= \begin{bmatrix} 1&0\\\ 0&1\\\ 1&1 \end{bmatrix} \\]

따라서:

\\[ Output=AV \\]

\\[ =0.198 \begin{bmatrix}1\\\0\end{bmatrix} +0.401 \begin{bmatrix}0\\\1\end{bmatrix} +0.401 \begin{bmatrix}1\\\1\end{bmatrix} \\]

결과는:

\\[ Output= \begin{bmatrix} 0.599\\\ 0.802 \end{bmatrix} \\]

이 결과를 Decoder의 다음 계산에 활용해 다음 텍스트 Token을 예측하는 거야.

여기서 주의할 점은 Attention Output 자체가 곧 '음악을'이라는 텍스트가 되는 것은 아니라는 거야. 이후 Decoder의 나머지 Layer와 Vocabulary Projection을 거쳐 Token 확률을 계산해.

# 3. 두 연산을 직접 비교해 보자

지금까지의 계산을 하나로 합쳐 보자.

## Self-Attention vs Cross-Attention

Self-Attention

같은 시퀀스 내부에서 정보 교환

Cross-Attention

서로 다른 시퀀스 사이에서 정보 교환

| 구분   | Self-Attention   | Cross-Attention       |
| ------ | ---------------- | --------------------- |
| Q 출처 | 입력 X           | 입력 A                |
| K 출처 | 입력 X           | 입력 B                |
| V 출처 | 입력 X           | 입력 B                |
| 관계   | 동일 시퀀스 내부 | 서로 다른 시퀀스 사이 |
| 목적   | 내부 문맥 학습   | 외부 정보 참조        |

수식으로 비교하면 더욱 명확해.

Self-Attention

\\[ \boxed{ Softmax\left( \frac{XW_Q(XW_K)^T}{\sqrt{d_k}} \right)XW_V } \\]

Cross-Attention

\\[ \boxed{ Softmax\left( \frac{X_AW_Q(X_BW_K)^T}{\sqrt{d_k}} \right)X_BW_V } \\]

두 수식의 핵심 차이는 Q와 K·V의 입력 출처야.

# 4. Whisper와 HTDemucs에서는 어떻게 적용될까?

여기가 Song Lingo 발표와 직접 연결되는 부분이야.

## 4-1. Whisper

Whisper에는 두 가지 Attention이 모두 사용돼.

Whisper의 Attention 흐름

Audio Encoder

오디오 Feature Sequence

Encoder Self-Attention

오디오 구간들 사이의 문맥 학습

Decoder Masked Self-Attention

이전까지 생성된 텍스트 Token 사이의 관계 학습

Decoder Cross-Attention

텍스트 Query가 오디오 Encoder의 K, V를 참고

다음 텍스트 Token 생성

여기서 Encoder의 Self-Attention과 Decoder의 Self-Attention은 서로 다른 시퀀스를 처리해.

- Encoder Self-Attention: 오디오 내부 관계
- Decoder Self-Attention: 생성 중인 텍스트 내부 관계
- Decoder Cross-Attention: 텍스트와 오디오 사이 관계

## 4-2. HTDemucs

HTDemucs에서도 Self-Attention과 Cross-Attention을 활용해.

하지만 데이터의 출처가 달라.

| Attention                  | Query       | Key / Value | 목적                       |
| -------------------------- | ----------- | ----------- | -------------------------- |
| Waveform Self-Attention    | Waveform    | Waveform    | 시간 영역 내부 문맥        |
| Spectrogram Self-Attention | Spectrogram | Spectrogram | 주파수·시간 영역 내부 문맥 |
| Cross-Attention            | Waveform    | Spectrogram | 스펙트럼 정보 참고         |
| Cross-Attention            | Spectrogram | Waveform    | 파형 정보 참고             |

여기서 두 Cross-Attention은 서로 다른 표현의 정보를 교환한다는 점이 중요해.

HTDemucs의 Cross-Domain Attention

Waveform

시간 영역

Qₜ

Spectrogram

주파수·시간 영역

Kᶠ, Vᶠ

Cross-Attention

Waveform이 Spectrogram 정보를 참고

Spectrogram

Qᶠ

Waveform

Kₜ, Vₜ

Cross-Attention

Spectrogram이 Waveform 정보를 참고

실제 HTDemucs에서는 Transformer Block의 Self-Attention과 Cross-Attention을 교대로 사용해. 모든 Layer가 항상 동일한 방식으로 양방향 정보를 교환하는 것은 아니므로, 발표에서는 '두 표현 사이의 정보를 교환한다'고 설명하는 것이 정확해.

# 5. 이해도 확인: 직접 선택해 보기

지금까지의 내용을 확인할 수 있도록 간단한 문제를 만들었어.

Attention 개념 테스트

0/4 응답

Q1. Whisper Decoder에서 이전에 생성한 텍스트 Token들이 서로의 정보를 참고한다. 어떤 Attention인가?

Self-Attention

Cross-Attention

Q2. Whisper Decoder가 오디오 Encoder의 특징을 참고해 다음 단어를 생성한다. 어떤 Attention인가?

Self-Attention

Cross-Attention

Q3. HTDemucs에서 Waveform Feature가 Spectrogram Feature를 참고한다. 어떤 Attention인가?

Self-Attention

Cross-Attention

Q4. Attention에서 Q, K, V가 모두 같은 입력 시퀀스에서 생성됐다. 어떤 Attention인가?

Self-Attention

Cross-Attention

정답 확인

마지막으로 꼭 기억할 한 문장:

Self-Attention은 '내부의 다른 위치를 참고하는 것'이고, Cross-Attention은 '다른 입력에서 정보를 가져오는 것'이야.

이 차이를 이해하면 Whisper의 텍스트 생성 구조와 HTDemucs의 Waveform-Spectrogram 정보 교환 구조를 모두 수식으로 설명할 수 있어.

다음으로는 Attention Weight가 학습 과정에서 어떻게 최적화되는지, 즉 Q·K·V의 Weight Matrix에 역전파가 어떻게 적용되는지 살펴보면 좋아.

---
https://github.com/greenkey20/song-lingo/blob/main/experiments/model%20anatomy/whisper_anatomy_claude_code.ipynb  파일 전체 흐름, 즉 whisper 모델의 전체 구조를 더 구체적으로 이해할 수 있도록 도와줘. 전체 및 층별 입/출력 크기? 파라미터 수, 각 층에서 일어나는 데이터 변화?나 계산 내용의 구체적인 예시(실제 수치) 등을 스토리텔링으로 설명해줘.

참고로 아래 demucs 스토리로 공부 시작했는데, 도움이 많이 되었었어.
—-

══════════════════════════════════════════════════════════════════════════════
장면 1. 도착   섞인 소리 (2, 343980) = 2채널 × 343,980표본 (7.8초). 모델이 받는 것은 이 하나뿐이다.
                x(t) = vocals + drums + bass + other.  어떤 소리가 어떤 모양인지는 알려 주지 않는다.
──────────────────────────────────────────────────────────────────────────────
장면 2. 두 가지 표현   같은 소리를 ① 파형 그대로 (1, 2, 343980)  ② STFT 스펙트로그램 (1, 4, 2048, 336) 로 나란히 본다.
                ②의 4채널 = 스테레오 2 × (실수, 허수), 2048칸 × 10.77 Hz, 336칸 × 23.2 ms
──────────────────────────────────────────────────────────────────────────────
장면 3. CNN 인코더  (4층, 한 층마다 시간 또는 주파수를 1/4로, 채널은 2배로)
                층 0:  파형 (2, 343980) → (48, 85995)   |   스펙트로그램 (4, 2048, 336) → (48, 512, 336)
                층 1:  파형 (48, 85995) → (96, 21499)   |   스펙트로그램 (48, 512, 336) → (96, 128, 336)
                층 2:  파형 (96, 21499) → (192, 5375)   |   스펙트로그램 (96, 128, 336) → (192, 32, 336)
                층 3:  파형 (192, 5375) → (384, 1344)   |   스펙트로그램 (192, 32, 336) → (384, 8, 336)
──────────────────────────────────────────────────────────────────────────────
장면 4. 만남   채널을 512로 맞추고 한 줄로 펼쳐 토큰으로 만든다: 스펙트로그램 8×336 = 2,688개, 파형 1,344개 (차원 512)
                Transformer 5층, 순서 = 셀프 → 교차 → 셀프 → 교차 → 셀프  (셀프 6개 · 교차 4개)
                교차 어텐션 예) layers.1: 질의 2,688개(한 가지) ↔ 키 1,344개(다른 가지) = 서로 다른 표현을 섞는다
──────────────────────────────────────────────────────────────────────────────
장면 5. 복원   디코더 4층이 인코더의 같은 단계 출력을 **더하며**(건너뛰기 연결) 크기를 4배씩 되돌린다.
                마지막 tdecoder.3 출력 (8, 343980) → 8채널 = 소리 4개 × 스테레오 2, 길이 343,980로 복원
                최종 출력 (1, 4, 2, 343980) = (배치, 소리, 채널, 표본),  소리 순서 = ['drums', 'bass', 'other', 'vocals']
══════════════════════════════════════════════════════════════════════════════
학습된 숫자(가중치) 42.0M개 중 crosstransformer가 75%  ← 압축된 표현 위에서 일하는 부분이 가장 무겁다 => [2026-11-11 09:57:21]

이번에는 네 Demucs 스토리와 같은 방식으로 Whisper를 분석해 보자. 단순히 Transformer가 4층이라는 사실을 외우는 것이 아니라, 실제 오디오 데이터 하나가 모델에 들어와서 어떤 계산을 거치고, 어떻게 텍스트로 변환되는지를 처음부터 끝까지 따라가 볼게.

네가 만든 노트북을 실제로 읽고 분석했어.

[song-lingo — whisper_anatomy_claude_code.ipynb](https://github.com/greenkey20/song-lingo/blob/main/experiments/model%20anatomy/whisper_anatomy_claude_code.ipynb?utm_source=chatgpt.com)

먼저 분석 대상과 주의할 점을 명확하게 하자.

## 0. 이번에 분석할 Whisper는 어떤 모델인가?

이 노트북은 OpenAI의 원본 PyTorch Whisper를 직접 실행한 것이 아니라, CTranslate2로 변환된 `faster-whisper`를 사용하고 있어.

노트북에서 확인한 환경은 다음과 같아.

| 항목             | 실제 설정                   |
| ---------------- | --------------------------- |
| faster-whisper   | 1.2.1                       |
| CTranslate2      | 4.8.4                       |
| 분석 모델        | tiny                        |
| 실행 장치        | CPU                         |
| 실행 정밀도 설정 | int8                        |
| LSTM / GRU       | 0개                         |
| 모델 구조        | Transformer Encoder-Decoder |
| 예시 오디오      | 직접 작성한 영어 문장의 TTS |
| 예시 음성의 길이 | 2.65초                      |

여기서 중요한 구분이 있어.

노트북에서는 세 가지 작업을 했어.

1. `model.bin`을 직접 파싱해서 모델의 변수 이름, 텐서 Shape, 저장된 파라미터 수를 확인했어.
2. 모델을 실제로 실행해서 Log-Mel, Encoder 출력, 생성 토큰과 확률을 관찰했어.
3. 무음·잡음·반복 문장 등을 입력해 Whisper의 실제 동작을 실험했어.

반면, 각 Transformer Layer 내부의 실제 Attention Weight나 모든 중간 Feature Map을 직접 추출한 것은 아니야. CTranslate2로 변환된 모델을 사용했기 때문이야.

따라서 아래에서는 다음과 같이 구분할게.

-

  직접 확인

  &#x20;노트북에서 실행하거나 모델 파일을 읽어서 확인한 결과


-

  구조로부터 계산

  &#x20;확인한 Weight Shape와 아키텍처를 바탕으로 유도한 값


-

  해석·추정

  &#x20;데이터 변화를 이해하기 위한 해석으로, 실제 내부 활성값을 직접 확인한 것은 아닌 내용



# 전체 스토리: 소리가 글이 되기까지

## Whisper 전체 데이터 흐름

1. 소리의 도착

   16kHz 오디오 → 30초 길이로 맞춤
2. 소리의 변환

   STFT → Power Spectrum → Mel Filter → Log-Mel
3. CNN Front-end

   Conv1d 두 개 → 시간축 3000에서 1500으로 압축
4. Transformer Encoder

   1500개 오디오 위치의 Self-Attention과 FFN
5. Transformer Decoder

   텍스트 Token Embedding → Masked Self-Attention → Cross-Attention
6. 텍스트 생성

   Vocabulary 51,865개에 대한 확률 계산 → 다음 Token 선택
7. 종료 및 후처리

   End-of-Text, Timestamp, 신뢰도 지표

이제 실제 숫자를 가지고 장면별로 들어가 보자.

# 장면 1. 도착 — 모델이 받는 것은 소리 하나뿐이다

노트북에서 사용한 예시 문장은 다음과 같아.

실제 노트북 예시

"I want to explore the universe."

직접 작성한 문장을 TTS로 생성한 오디오

# 2.65초

오디오 길이

# 42,400

16kHz 기준 샘플 수

Waveform의 데이터 구조

\\[ x\in\mathbb{R}^{42400} \\]

단일 음성 채널, 1초당 16,000개 샘플

Whisper가 받는 것은 위 문장이 아니라 오디오 파형이야.

사람이 작성한 원본 문장과 TTS 오디오는 실험 데이터 준비 과정에 존재하지만, Whisper의 입력은 파형뿐이야.

여기서 중요한 것은 Whisper의 목적이 Demucs와 전혀 다르다는 점이야.

- Demucs: 혼합된 소리에서 각각의 소리를 분리
- Whisper: 입력된 소리가 무엇을 말하는지 텍스트로 변환

Whisper는 입력된 소리의 정답 문장을 직접 전달받지 않아. 이미 학습된 모델의 가중치를 가지고 입력을 해석하는 거야.

## 1-1. 왜 16kHz로 바꿀까?

노트북에서 `decode_audio()`를 호출할 때 Sampling Rate를 16,000Hz로 지정했어.

\\[ f_s=16,000Hz \\]

2.65초의 오디오라면:

\\[ 2.65\times16,000=42,400 \\]

총 42,400개의 샘플이 만들어지는 거야.

실제 오디오가 Stereo라면 채널별 파형이 존재하지만, 이번 Whisper 입력은 Mono로 디코딩되기 때문에 1차원 배열이 돼.

# 장면 2. 소리의 다른 표현 — Log-Mel Spectrogram

이제 중요한 변환이 시작돼.

사람에게는 음악이나 음성이 파형으로 보이지만, 신경망이 음성의 음향적 특성을 학습하기 위해서는 파형을 다른 형태로 변환하는 것이 유용해.

Whisper는 Log-Mel Spectrogram을 입력으로 사용해.

## 2-1. STFT

먼저 오디오를 짧은 시간 구간으로 나누고 각 구간에 Fourier Transform을 적용해.

노트북의 설정은 다음과 같아.

| 파라미터      | 값       | 의미                     |
| ------------- | -------- | ------------------------ |
| Sampling Rate | 16,000Hz | 초당 16,000 샘플         |
| FFT Size      | 400      | 400 샘플을 이용          |
| Window Length | 25ms     | 400 / 16,000             |
| Hop Length    | 160      | 다음 프레임까지 160 샘플 |
| Hop Interval  | 10ms     | 160 / 16,000             |
| Mel Channels  | 80       | Mel 필터 80개            |

따라서 1초 동안 약 100개의 시간 프레임이 만들어져.

\\[ \frac{16,000}{160}=100 \\]

2.65초짜리 음성은 노트북에서 다음과 같이 나왔어.

실제 실행 결과

STFT 및 Mel 변환 결과

| 항목           | 결과      |
| -------------- | --------- |
| 파형 샘플      | 42,400    |
| Log-Mel 프레임 | 266       |
| FFT 주파수 Bin | 201       |
| Mel 필터 수    | 80        |
| Log-Mel Shape  | (80, 266) |

FFT의 주파수 Bin은 실수 입력에 대한 RFFT 결과이므로 400 / 2 + 1 = 201개야.

## 2-2. 실제 숫자로 Mel 변환 이해하기

한 프레임에 대해 FFT를 실행하면 201개의 주파수 성분이 만들어져.

\\[ X\_{FFT}\in\mathbb{C}^{201} \\]

여기서 각 주파수 성분의 Power를 계산해.

\\[ P_k=|X_k|^2 \\]

그러면 201개의 Power 값이 만들어지지.

이제 Mel Filter Bank를 적용해.

노트북에서 실제로 확인한 Mel Filter 행렬의 Shape는 다음과 같아.

\\[ M\in\mathbb{R}^{80\times201} \\]

이를 Power Spectrum에 곱해.

\\[ Mel=MP \\]

차원을 확인하면:

\\[ (80,201)\times(201,1) =(80,1) \\]

즉, FFT의 201개 주파수 Bin을 Mel Scale의 80개 주파수 대역으로 변환하는 거야.

이 연산을 시간 프레임 266개에 각각 적용하면:

\\[ (80,201)\times(201,266) =(80,266) \\]

이렇게 Log-Mel의 크기가 결정돼.

## 2-3. Log 변환과 정규화

여기서 아직 끝이 아니야.

Whisper는 Mel 에너지에 로그를 적용하고 정규화해.

노트북에서 직접 구현해 라이브러리의 결과와 비교한 계산 흐름은 다음과 같아.

\\[ P=|STFT(x)|^2 \\]

\\[ M=MelFilterBank(P) \\]

\\[ L=\log\_{10}(\max(M,10^{-10})) \\]

그다음:

\\[ L'=\max(L,\max(L)-8) \\]

마지막으로:

\\[ LogMel=\frac{L'+4}{4} \\]

왜 로그를 사용하는 걸까?

소리의 에너지 크기는 큰 범위에 걸쳐 변화하기 때문에 로그를 취하면 작은 에너지 차이와 큰 에너지 차이를 좀 더 다루기 쉬운 범위로 변환할 수 있어.

노트북에서는 직접 작성한 Log-Mel 구현과 `faster-whisper`의 결과가 거의 완전히 일치했어.

직접 검증

최대 절대 오차:

\\[ 8.293\times10^{-8} \\]

즉, 네가 직접 구현한 계산과 라이브러리의 계산이 사실상 동일하다는 것을 확인한 거야.

## 2-4. 그런데 왜 2.65초짜리 소리가 30초로 바뀔까?

이것이 Whisper의 중요한 설계 특징이야.

모델은 항상 30초 길이의 입력을 받도록 설계되어 있어.

\\[ 30\times100=3000 \\]

따라서:

\\[ (80,266)\rightarrow(80,3000) \\]

나머지 2,734개 프레임에 해당하는 영역은 0으로 채워.

실제 30초 입력의 구성

시간축 방향으로 표현한 개념도

2.66초 · 음성 특징

27.34초 · 0 Padding

# 80 × 3000

Mel Channel 80개 × Time Frame 3000개Batch Dimension을 추가하면 (1, 80, 3000)이야.

여기서 주의할 점이 있어.

Padding으로 채운 0은 실제 무음 구간의 Log-Mel 값과 반드시 같지는 않아. 이 노트북에서도 실제 음성의 Log-Mel 값 범위는 -0.8\~1.2였고, Padding 영역은 정확히 0이었어.

따라서 모델은 학습 과정에서 이런 고정 길이 입력과 Padding 패턴을 함께 학습하게 돼.

이제 본격적으로 CNN이 등장해.

# 장면 3. CNN Front-end — 80개의 주파수 특성을 384차원으로 변환

Whisper에는 CNN이 존재해.

하지만 Demucs처럼 여러 층을 쌓아서 Encoder-Decoder를 구성하는 것은 아니야.

Whisper에서는 Transformer Encoder 앞에 두 개의 Conv1d가 배치되어 있어.

이 두 개의 Layer가 Log-Mel을 Transformer가 처리하기 좋은 형태로 변환해.

## 3-1. Conv1d Layer 1

입력:

\\[ X_0\in\mathbb{R}^{1\times80\times3000} \\]

첫 번째 Conv1d의 실제 Weight Shape:

\\[ W_1\in\mathbb{R}^{384\times80\times3} \\]

의미는 다음과 같아.

- Input Channel: 80
- Output Channel: 384
- Kernel Size: 3

즉, Mel Channel 80개를 384개의 Feature Channel로 변환하는 거야.

여기서 각 Output Channel은 별도의 학습 가능한 Kernel Weight를 가지고 있어.

출력:

\\[ (1,80,3000) \rightarrow (1,384,3000) \\]

이 단계에서는 시간축 크기가 유지돼.

Convolution 이후 GELU 활성화 함수가 적용돼.

### 파라미터 수

Weight:

\\[ 384\times80\times3=92,160 \\]

Bias:

\\[ 384 \\]

합계:

\\[ \boxed{92,544} \\]

## 3-2. Conv1d Layer 2

두 번째 Convolution의 Weight Shape:

\\[ W_2\in\mathbb{R}^{384\times384\times3} \\]

이번에는 Input Channel과 Output Channel이 모두 384야.

하지만 중요한 차이가 있어.

Stride가 2라는 점이야.

첫 번째 Conv1d는 시간축을 유지했지만 두 번째 Conv1d는 시간축을 절반으로 줄여.

\\[ (1,384,3000) \rightarrow (1,384,1500) \\]

왜 줄일까?

Transformer가 처리해야 하는 Token 수를 줄이기 위해서야.

3000개의 위치를 그대로 Attention에 넣는 것보다 1500개로 줄이면 Self-Attention의 계산량을 크게 줄일 수 있어.

### 파라미터 수

Weight:

\\[ 384\times384\times3=442,368 \\]

Bias:

\\[ 384 \\]

합계:

\\[ \boxed{442,752} \\]

## 3-3. CNN을 거친 전체 변화

Whisper CNN Front-end

Log-Mel

\\[ (1,80,3000) \\]

Conv1d #1

80 → 384 Channel · Kernel 3 · Stride 1

\\[ (1,384,3000) \\]

파라미터 92,544개

Conv1d #2

384 → 384 Channel · Kernel 3 · Stride 2

\\[ (1,384,1500) \\]

파라미터 442,752개

Transformer Input

\\[ (1,1500,384) \\]

시간축 1500개 위치 × 각 위치의 384차원 Feature

여기서 `(1,384,1500)`을 `(1,1500,384)`로 바꾸는 것은 Transpose 또는 차원 재배열이야.

새로운 특징을 학습하는 연산은 아니고, 시간 위치를 Token 축으로 사용하기 위한 데이터 배치 변경이지.

## 3-4. 이때 각 위치가 의미하는 것은?

입력 Log-Mel은 10ms마다 한 프레임이었어.

그런데 두 번째 Conv1d에서 Stride가 2이므로 출력 위치는 20ms 단위가 돼.

\\[ 10ms\times2=20ms \\]

결과적으로 30초를 다음과 같이 표현해.

\\[ \frac{30}{0.02}=1500 \\]

따라서 Transformer는 30초 오디오를 1500개의 위치로 바라보는 거야.

중요한 것은 1500개의 위치가 1500개의 단어라는 뜻은 아니라는 점이야.

각 위치는 20ms 간격으로 배치된 음향 특징 벡터야. 실제 각 벡터는 주변 시간 영역도 함께 반영할 수 있어.

# 장면 4. Transformer Encoder — 1500개의 오디오 위치가 서로를 참고한다

이제 Whisper의 첫 번째 거대한 Transformer 영역으로 들어가자.

네 노트북에서 `tiny` 모델의 Encoder 구조를 실제로 확인했어.

| 항목                      | 값   |
| ------------------------- | ---- |
| Transformer Encoder Layer | 4개  |
| Model Dimension           | 384  |
| Attention Head            | 6개  |
| Head Dimension            | 64   |
| Input Sequence Length     | 1500 |
| 출력 Dimension            | 384  |

Head 개수 6개는 Whisper tiny의 아키텍처 설정에 해당하며, 노트북이 직접 덤프한 Weight Shape 자체에는 Head 개수가 별도 변수로 저장되어 있지는 않아.

## 4-1. Positional Encoding

그런데 문제가 하나 있어.

Transformer는 Convolution이나 RNN과 다르게 입력의 순서를 자체적으로 보장하지 않아.

따라서 각 위치에 위치 정보를 제공해야 해.

Whisper Encoder에는 다음과 같은 위치 정보가 존재해.

\\[ P\in\mathbb{R}^{1500\times384} \\]

이를 CNN 출력에 더해.

\\[ X\_{position}=X\_{CNN}+P \\]

입력과 위치 정보의 Shape가 동일하기 때문에 Element-wise Addition을 할 수 있어.

여기서 한 가지 세부사항이 있어. OpenAI Whisper의 위치 정보는 고정된 Sinusoidal Positional Encoding이야. 노트북에서 저장된 Tensor 크기를 셌다고 해서 모든 위치값이 학습 가능한 파라미터라는 뜻은 아니야.

## 4-2. Transformer Encoder Layer 하나의 내부 구조

Encoder Layer 하나에는 크게 두 가지 연산이 있어.

1. Self-Attention
2. Feed Forward Network(FFN)

그리고 각각 Residual Connection과 Layer Normalization이 결합돼.

Encoder Layer 1개

Input

\\[ (1,1500,384) \\]

LayerNorm

Multi-Head Self-Attention

Q, K, V 생성 및 Attention

Residual Addition

LayerNorm

Feed Forward Network

384 → 1536 → 384

Residual Addition

Output

\\[ (1,1500,384) \\]

출력 Shape가 입력과 같다는 사실이 중요해.

Transformer Layer를 통과한다고 시간 위치가 계속 줄어들거나 차원이 계속 늘어나는 것은 아니야.

같은 Shape 안에서 각 위치의 특징 벡터가 다른 위치의 정보를 반영하도록 갱신되는 거야.

## 4-3. Self-Attention의 실제 계산 크기

입력은:

\\[ X\in\mathbb{R}^{1\times1500\times384} \\]

먼저 Query, Key, Value를 계산해.

\\[ Q=XW_Q,\quad K=XW_K,\quad V=XW_V \\]

노트북에서 확인한 QKV 통합 Weight의 Shape는:

\\[ W\_{QKV}\in\mathbb{R}^{1152\times384} \\]

왜 1152일까?

\\[ 384\times3=1152 \\]

Q, K, V를 하나의 Projection에서 동시에 계산하기 때문이야.

계산 결과를 분리하고 6개의 Head로 나누면 각 Head의 차원은 64가 돼.

\\[ 384=6\times64 \\]

따라서:

\\[ Q,K,V\in\mathbb{R}^{1\times6\times1500\times64} \\]

이제 Attention Score를 계산해.

\\[ S=\frac{QK^T}{\sqrt{64}} \\]

각 Head의 Attention Matrix는:

\\[ A\in\mathbb{R}^{1500\times1500} \\]

이야.

즉, 하나의 위치가 나머지 1500개 위치를 참고할 수 있도록 1500×1500의 관계 행렬을 계산하는 거지.

Encoder Self-Attention Matrix

[What is the Self-Attention Mechanism in Transformers? | by Param.dev | Medium](https://images.openai.com/static-rsc-4/fZ18Se3GzFFODt4_LUzh3h2A7ktbpXSrBf3A5YGnKitzhteIXo4jIKnvtVVmJPVjIeDKn9QfvV3hSdh_035dPJmVLFA-sss1zWQMjMNGHTf0AmJ5_eUYDG7ByTw3KlNsq0LavOw7YfppepQBkMW9j9koeqQrttl-sVZzthXMHt4?purpose=inline)

[medium.com](https://medium.com/%40paramahuja04/what-is-the-self-attention-mechanism-in-transformers-4205070d719d?utm_source=chatgpt.com)

# 1500 × 1500

Head 하나의 Attention Score 행렬 크기. Tiny 모델은 Head가 6개이므로 Layer 하나에서 6개의 관계 행렬을 계산해.

실제 Attention 행렬의 값은 이 노트북에서 추출하지 않았어. 위 그림은 구조 이해를 위한 개념도야.

여기서 중요한 점은 Encoder의 Self-Attention에는 Decoder와 같은 미래 차단 Mask가 기본적으로 적용되지 않는다는 거야.

오디오 입력 전체를 한 번에 살펴보는 Bidirectional Context를 학습하는 거지.

## 4-4. Feed Forward Network

Attention을 통과한 다음에는 FFN이 실행돼.

노트북의 Weight Shape는 다음과 같아.

| Weight   | Shape       | 연산       |
| -------- | ----------- | ---------- |
| Linear 0 | (1536, 384) | 384 → 1536 |
| Linear 1 | (384, 1536) | 1536 → 384 |

따라서:

\\[ FFN(x)=W_2\cdot GELU(W_1x+b_1)+b_2 \\]

왜 1536으로 늘렸다가 다시 384로 줄일까?

384차원의 특징을 더 넓은 중간 공간에서 비선형적으로 변환하기 위해서야.

이 과정이 각 위치의 특징 표현을 더 복잡하게 만드는 역할을 해.

## 4-5. Encoder Layer를 4번 통과하면?

Tiny 모델은 이 Layer를 4번 통과해.

| 단계            | 입력 Shape     | 출력 Shape     |
| --------------- | -------------- | -------------- |
| CNN 출력        | (1, 1500, 384) | (1, 1500, 384) |
| Encoder Layer 0 | (1, 1500, 384) | (1, 1500, 384) |
| Encoder Layer 1 | (1, 1500, 384) | (1, 1500, 384) |
| Encoder Layer 2 | (1, 1500, 384) | (1, 1500, 384) |
| Encoder Layer 3 | (1, 1500, 384) | (1, 1500, 384) |

실제 실행으로 확인

노트북에서 `model.encode()`를 실행한 결과는:

\\[ E\in\mathbb{R}^{1500\times384} \\]

였어. Batch 차원을 제외하고 출력한 결과야.

즉, Whisper가 입력한 30초짜리 오디오를 최종적으로 1500개의 384차원 벡터로 표현한 거야.

이제 이 결과가 Decoder에 전달돼.

# 장면 5. Decoder의 준비 — 글을 쓸 준비를 한다

이제부터는 조금 다른 세계가 시작돼.

Encoder는 소리를 이해하기 위한 특징을 만들었어.

Decoder는 그 특징을 보면서 텍스트를 생성해야 해.

그런데 Decoder는 무엇을 입력받아야 할까?

정답은 현재까지 생성한 텍스트 Token이야.

## 5-1. Vocabulary와 Token Embedding

Whisper Tiny의 Vocabulary 크기는 51,865개야.

노트북에서 확인한 구성은 다음과 같아.

| 구성                      | 개수   |
| ------------------------- | ------ |
| 일반 텍스트 및 특수 Token | 50,364 |
| Timestamp Token           | 1,501  |
| 합계                      | 51,865 |

모든 Token에는 ID가 부여되어 있어.

예를 들어:

| Token                       | ID    |
| --------------------------- | ----- |
| `<\\|startoftranscript\\|>` | 50258 |
| `<\\|en\\|>`                | 50259 |
| `<\\|transcribe\\|>`        | 50359 |
| `<\\|notimestamps\\|>`      | 50363 |
| `<\\|endoftext\\|>`         | 50257 |

그런데 숫자 ID만으로 Transformer가 문맥을 이해할 수는 없어.

그래서 Token Embedding을 사용해.

노트북에서 실제로 확인한 Embedding Weight의 Shape는 다음과 같아.

\\[ W\_{emb}\in\mathbb{R}^{51865\times384} \\]

이것은 51,865개의 Token 각각이 384차원 벡터를 가진다는 의미야.

예를 들어 Token ID 50258을 입력받으면 Embedding Matrix의 50258번째 행을 가져오는 거야.

\\[ Embedding(50258)=W\_{emb}[50258] \\]

결과는:

\\[ \mathbb{R}^{384} \\]

즉, Token ID 하나가 384차원의 벡터로 변환돼.

## 5-2. 위치 정보 추가

Decoder에도 위치 정보가 필요해.

노트북에서 확인한 Shape는:

\\[ P\_{decoder}\in\mathbb{R}^{448\times384} \\]

즉, Decoder가 최대 448개 위치의 Token을 처리하도록 설계돼 있어.

Token Embedding에 위치 정보를 더해.

\\[ X\_{decoder}=Embedding(Token)+P\_{decoder} \\]

이제 Transformer Decoder에 넣을 수 있는 형태가 된 거야.

# 장면 6. Transformer Decoder — 소리를 참고하며 글을 한 토큰씩 쓴다

이제 Whisper의 핵심인 Decoder야.

Decoder에서는 세 가지 중요한 계산이 발생해.

1. Masked Self-Attention
2. Cross-Attention
3. Feed Forward Network

Encoder와 달리 Decoder에서는 두 가지 Attention이 있다는 점이 중요해.

## 6-1. 처음 Decoder에 전달되는 것은 무엇인가?

노트북에서 사용한 실제 Prompt는 다음과 같아.

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
```

각각의 의미는 다음과 같아.

| Token             | 역할                           |
| ----------------- | ------------------------------ |
| startoftranscript | 텍스트 생성 시작               |
| en                | 영어 인식                      |
| transcribe        | 음성 인식 작업                 |
| notimestamps      | Timestamp를 출력하지 않는 모드 |

따라서 초기 입력 Token 수는 4개야.

각 Token을 Embedding으로 변환하면:

\\[ X_d\in\mathbb{R}^{1\times4\times384} \\]

이렇게 돼.

이것이 Decoder의 첫 번째 입력이야.

## 6-2. 첫 번째 계산: Masked Self-Attention

Decoder도 입력 Token들 사이의 관계를 계산해.

다만 미래 Token을 참조하면 안 돼.

예를 들어 모델이 다음과 같이 문장을 작성하고 있다고 생각해 보자.

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
I
```

현재까지 작성한 Token은 참고할 수 있지만, 아직 생성하지 않은 미래의 Token은 알 수 없어야 해.

그래서 Causal Mask를 적용해.

\\[ Attention= Softmax\left( \frac{QK^T}{\sqrt{d_k}}+M \right)V \\]

여기서 \\(M\\)은 미래 위치에 \\(-\infty\\)를 부여하는 Mask야.

예를 들어 길이 4인 시퀀스를 기준으로 하면:

\\[ M= \begin{bmatrix} 0&-\infty&-\infty&-\infty\\\ 0&0&-\infty&-\infty\\\ 0&0&0&-\infty\\\ 0&0&0&0 \end{bmatrix} \\]

이렇게 미래의 정보를 차단하는 거야.

## 6-3. 두 번째 계산: Cross-Attention

여기가 Whisper Decoder에서 가장 중요한 부분이야.

Decoder는 자기 자신이 생성한 텍스트 Token뿐 아니라 Encoder가 만든 오디오 특징도 참고해야 해.

따라서 Cross-Attention을 사용해.

\\[ Q=X\_{decoder}W_Q \\]

\\[ K=E W_K \\]

\\[ V=E W_V \\]

여기서 \\(E\\)는 앞에서 계산했던 Encoder의 출력이야.

\\[ E\in\mathbb{R}^{1\times1500\times384} \\]

즉:

- Query: 현재 Decoder의 텍스트 표현
- Key: Encoder의 오디오 표현
- Value: Encoder의 오디오 표현

이렇게 구성돼.

### 실제 Weight Shape를 살펴보자.

네 노트북에서 tiny 모델의 Decoder Layer 0을 열었을 때 다음과 같은 변수를 확인했어.

| 변수               | Weight Shape | 역할                |
| ------------------ | ------------ | ------------------- |
| attention/linear_0 | (384, 384)   | Query 생성          |
| attention/linear_1 | (768, 384)   | Key와 Value 생성    |
| attention/linear_2 | (384, 384)   | Attention 결과 투영 |

왜 `linear_1`의 Output Dimension이 768일까?

\\[ 384\times2=768 \\]

Key와 Value를 하나의 연산으로 동시에 계산하기 때문이야.

따라서:

\\[ K,V\in\mathbb{R}^{1\times6\times1500\times64} \\]

이고 Query는:

\\[ Q\in\mathbb{R}^{1\times6\times L\times64} \\]

이야. 여기서 \\(L\\)은 현재까지 Decoder가 처리하는 Token 길이야.

Cross-Attention의 Score 행렬은 다음과 같아.

\\[ QK^T \\]

결과적으로 각 Head에서:

\\[ A\_{cross}\in\mathbb{R}^{L\times1500} \\]

이라는 Attention Matrix가 만들어져.

이것이 의미하는 바가 중요해.

Decoder의 텍스트 Token 하나가 Encoder가 만든 1500개 오디오 위치 전체를 참고할 수 있다는 뜻이야.

Whisper Cross-Attention의 데이터 흐름

Audio Encoder Output

\\[ (1,1500,384) \\]

30초 오디오를 표현하는 1500개 위치

Key / Value

각각 1500개 오디오 위치의 특징

Decoder Query

\\[ (1,6,L,64) \\]

현재 텍스트 Token들의 Query

Cross-Attention

\\[ (L,1500) \\]

텍스트의 각 위치가 오디오의 어느 부분을 참고할지 계산

직관적으로 생각해 보자.

모델이 다음 단어로 'universe'를 생성하려고 한다면, Encoder가 만든 오디오 특징 중 어떤 위치들이 지금까지의 텍스트와 관련이 있는지 Attention을 통해 계산할 수 있어.

물론 실제로 Attention Weight만 보고 '여기가 universe라는 발음이다'라고 단정할 수는 없어. 각 위치의 음향 정보와 여러 Layer에서 처리된 문맥이 종합적으로 작용하기 때문이야.

## 6-4. 세 번째 계산: FFN

Self-Attention과 Cross-Attention을 통해 정보를 결합한 후에는 FFN이 실행돼.

앞에서 봤던 Encoder와 마찬가지로:

\\[ 384\rightarrow1536\rightarrow384 \\]

의 구조야.

\\[ FFN(x)=W_2GELU(W_1x+b_1)+b_2 \\]

그리고 Residual Connection과 Layer Normalization이 사용돼.

## 6-5. Decoder Layer도 4개다

Tiny 모델의 Decoder Layer 수는 4개야.

| Layer     | 입력        | 출력        |
| --------- | ----------- | ----------- |
| Decoder 0 | (1, L, 384) | (1, L, 384) |
| Decoder 1 | (1, L, 384) | (1, L, 384) |
| Decoder 2 | (1, L, 384) | (1, L, 384) |
| Decoder 3 | (1, L, 384) | (1, L, 384) |

각 Layer는 앞에서 생성한 텍스트 표현을 더 풍부하게 만드는 역할을 해.

그리고 마지막 Layer를 통과한 결과가 최종 Token 예측 단계로 전달돼.

# 장면 7. 생성 — 이제 실제로 글을 써 보자

이제부터는 노트북에서 실제로 실행한 결과를 따라가 볼게.

Encoder가 한 번 실행되어 출력 \\(E\\)를 만들었어.

이제 Decoder가 다음 Token을 하나씩 생성하기 시작해.

## 7-1. Token을 하나씩 생성한다

초기 Prompt는 다음과 같아.

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
```

Decoder는 이 입력과 Encoder 출력을 이용해서 다음 Token의 확률을 계산해.

모든 Token 후보는 51,865개야.

즉, 한 단계에서 다음과 같은 확률분포가 만들어져.

\\[ P(y_t|y\_{\<t},E) \\]

여기서:

- \\(y_t\\): 현재 예측할 Token
- \\(y\_{\<t}\\): 이전에 생성한 Token
- \\(E\\): Encoder 출력

### 실제 노트북에서 생성한 결과

실제 실행 결과

생성된 문장

# I want to explore the universe.

| 단계 | Decoder가 선택한 결과 |
| ---- | --------------------- |
| 1    | ` I`                  |
| 2    | ` want`               |
| 3    | ` to`                 |
| 4    | ` explore`            |
| 5    | ` the`                |
| 6    | ` universe`           |
| 7    | `.`                   |
| 8    | `<\\|endoftext\\|>`   |

7개의 텍스트 Token을 생성하고 8번째 단계에서 종료 Token을 선택했어.

여기서 반드시 이해해야 하는 것이 있어.

매 단계마다 Encoder가 다시 실행되는 것은 아니야.

전체 흐름은 다음과 같아.

```
                     Audio
                       │
                       ▼
                Transformer Encoder
                       │
                       ▼
                Encoder Output
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
        Decoder 1   Decoder 2   Decoder 3 ...
           │           │           │
          "I"        "want"        "to"
           │           │           │
           └───────────┴───────────┘
                       ...
```

Encoder는 한 번 실행되고, Decoder가 이전 Token을 추가하면서 반복적으로 실행되는 구조야.

실제 CTranslate2는 KV Cache를 활용해서 이전 단계에서 계산한 Key와 Value를 재사용하므로, 매번 기존 Token 전체의 Attention을 처음부터 다시 계산하지 않아.

노트북에서 사용한 `beam_size=1`은 Greedy Decoding이야. 각 단계에서 가장 높은 확률을 가진 후보 하나를 선택해.

## 7-2. 실제 확률과 신뢰도

노트북에서는 단순히 결과 문장만 출력한 것이 아니라, 각 단계의 Logits도 가져왔어.

코드에서는:

```
logits = np.array(res.logits[0])
```

이렇게 했지.

Logits는 Softmax를 적용하기 전의 점수야.

\\[ P_i= \frac{e^{z_i}}{\sum_j e^{z_j}} \\]

여기서 \\(z_i\\)가 각 Vocabulary Token의 Logit이야.

각 생성 단계에서 51,865개 후보의 점수를 계산하고 확률로 변환해.

따라서 생성된 문장뿐 아니라 각 시점에서 어떤 후보가 얼마나 유력했는지도 확인할 수 있었던 거야.

참고로 노트북의 토큰화 비교 표에서는 영어 문장을 9 Token으로 계산했지만, 실제 CTranslate2 생성 결과는 텍스트 Token 7개로 나와 있어. 두 경로의 Token 분할 결과를 동일한 것으로 취급해서는 안 되고, 발표에서 정확한 토큰 수를 제시하려면 이 부분은 동일한 Tokenizer 인터페이스로 다시 대조하는 게 좋아.

## 7-3. 언어도 알아낸다

노트북에는 언어 감지 실험도 있어.

Encoder의 출력을 이용해 언어 Token을 예측하는 방식이야.

실제 실행 결과는 다음과 같아.

| 언어       | 확률   |
| ---------- | ------ |
| 영어       | 0.9670 |
| 웨일스어   | 0.0080 |
| 라틴어     | 0.0077 |
| 노르웨이어 | 0.0024 |
| 말레이어   | 0.0023 |

모델은 입력 오디오를 영어일 가능성이 가장 높다고 판단했어.

즉, 언어 감지도 완전히 별도의 RNN 모델을 실행하는 것이 아니라 Whisper의 Encoder 출력에 기반해 처리하는 거야.

## 7-4. Timestamp도 Token이다

여기서 흥미로운 사실이 하나 더 있어.

Whisper는 텍스트만 생성하는 것이 아니라 Timestamp Token도 생성할 수 있어.

예를 들어 노트북에서 Timestamp 출력 기능을 켜고 실행한 결과는 다음과 같았어.

```
<|0.00|>
I want to explore the universe.
<|2.00|>
```

Whisper의 Timestamp Token은 0.02초 단위로 표현돼.

\\[ Time=(TokenID-TimestampBegin)\times0.02 \\]

따라서 Token ID가 1 증가하면 시간이 20ms 증가해.

노트북에서 확인한 값은:

- 시작: 0.00초
- 종료: 2.00초

였어.

즉, Whisper가 시간을 별도의 숫자 필드로만 다루는 것이 아니라 특수 Token을 이용해 텍스트 시퀀스에 포함할 수 있다는 점이 특징이야.

# 장면 8. 모델 내부에는 몇 개의 학습 가능한 숫자가 있을까?

지금까지는 데이터가 어떻게 처리되는지 살펴봤어.

이번에는 모델이 그 계산을 수행하기 위해 얼마나 많은 Weight를 가지고 있는지 보자.

## 8-1. 모델 크기별 파라미터 수

네 노트북에서는 `model.bin`을 직접 파싱해서 각 Tensor의 Shape를 읽었어.

이때 Tensor의 차원 크기를 모두 곱하면 저장된 숫자의 개수를 계산할 수 있어.

예를 들어:

\\[ W\in\mathbb{R}^{384\times80\times3} \\]

이라면:

\\[ 384\times80\times3=92,160 \\]

개의 Weight가 존재하지.

전체 모델도 이런 식으로 집계했어.

Whisper 모델 크기 비교

| 모델   | Encoder | Decoder | Dimension | 전체 수치 수 |
| ------ | ------- | ------- | --------- | ------------ |
| tiny   | 4층     | 4층     | 384       | 37.8M        |
| base   | 6층     | 6층     | 512       | 72.6M        |
| small  | 12층    | 12층    | 768       | 241.8M       |
| medium | 24층    | 24층    | 1024      | 763.9M       |

노트북의 model.bin 텐서 Shape를 곱해 집계한 값. 논문에 표시된 약 39M, 74M, 244M, 769M과 약간 차이가 있어.

여기서 주의할 점은 이 수치가 엄밀한 의미의 학습 가능한 파라미터만을 뜻하지는 않는다는 거야.

노트북의 집계 방식은 모델 파일에 저장된 Tensor의 원소 수를 세는 방식이고, Whisper의 고정 위치 인코딩처럼 학습되지 않는 값도 포함할 수 있어.

따라서 발표에서는 'model.bin에서 확인한 텐서 원소 수' 또는 '파라미터 규모의 근사치'라고 설명하는 것이 정확해.

## 8-2. Tiny 모델의 파라미터를 구성 요소별로 살펴보자

여기서는 네가 실제로 공부한 `tiny` 모델을 기준으로 좀 더 구체적인 수치를 계산해 볼게.

Whisper Tiny의 구성

Encoder

## 8.21M

Decoder

## 29.56M

# 37.77M

두 부분의 텐서 원소 수를 합산한 근사값

### Encoder의 파라미터 구성

| 구성              | 계산                        | 원소 수   |
| ----------------- | --------------------------- | --------- |
| Conv1             | 384×80×3 + 384              | 92,544    |
| Conv2             | 384×384×3 + 384             | 442,752   |
| Position Encoding | 1500×384                    | 576,000   |
| Encoder Layer 1개 | 내부 Attention + FFN + Norm | 1,774,464 |
| Encoder Layer 4개 | 1,774,464×4                 | 7,097,856 |
| 최종 LayerNorm    | 384×2                       | 768       |
| 합계              |                             | 8,209,920 |

여기서 Encoder Layer 1개가 약 177만 개의 숫자를 사용하는 거야.

### Decoder의 파라미터 구성

| 구성              | 계산                                          | 원소 수    |
| ----------------- | --------------------------------------------- | ---------- |
| Token Embedding   | 51,865×384                                    | 19,916,160 |
| Position Encoding | 448×384                                       | 172,032    |
| Decoder Layer 1개 | Self-Attention + Cross-Attention + FFN + Norm | 2,366,592  |
| Decoder Layer 4개 | 2,366,592×4                                   | 9,466,368  |
| 최종 LayerNorm    | 384×2                                         | 768        |
| 합계              |                                               | 29,555,328 |

이 계산은 노트북에서 직접 확인한 Layer의 Weight Shape를 이용해 유도한 값이야.

여기서 가장 흥미로운 사실은 Decoder의 Token Embedding이 약 1,992만 개라는 점이야.

Tiny 모델 전체의 절반 이상을 Token Embedding이 차지하는 셈이지.

\\[ \frac{19,916,160}{37,765,248} \times100 \approx52.7\\% \\]

이것이 네 노트북의 파라미터 구성 그래프에서 확인한 결과와 일치해.

핵심 발견

Whisper Tiny에서는 Attention이나 CNN보다 Token Embedding이 더 많은 수치 공간을 차지해.

단, 파라미터가 많다는 것이 반드시 해당 부분의 계산량도 가장 많다는 뜻은 아니야.

특히 Encoder는 1500개 오디오 위치에 대해 Attention을 수행하기 때문에 연산량이 상당히 커.

# 장면 9. 실제로 모델이 잘못 동작하는 순간 — 환각과 반복

네 노트북에서 특히 흥미로운 부분이 바로 여기야.

Whisper의 구조를 이해한 뒤 실제로 어떤 문제가 발생하는지 실험했어.

## 9-1. 무음인데도 글을 생성한다

노트북에서 5초짜리 무음 오디오를 입력했어.

그런데 모델이 다음과 같이 출력했지.

```
you
```

| 측정값         | 결과  |
| -------------- | ----- |
| 생성된 문장    | you   |
| avg_logprob    | -2.81 |
| no_speech_prob | 0.76  |

왜 이런 일이 발생할까?

Decoder에는 언어 모델의 역할도 있어.

소리의 증거가 부족해도 그럴듯한 Token을 선택할 가능성이 있는 거야.

그래서 faster-whisper는 두 가지 지표를 확인해.

- `no_speech_prob`: 소리가 없는 구간일 확률
- `avg_logprob`: 생성한 Token의 평균 로그확률

두 조건이 동시에 충족되면 해당 구간을 건너뛰도록 처리해.

```
no_speech_prob > 0.6
         AND
avg_logprob < -1.0
         │
         ▼
   음성 없는 구간으로 판단
         │
         ▼
       Skip
```

즉, 모델 자체가 아무것도 생성하지 않는 것이 아니라, 생성 후 결과를 평가해 무의미한 구간을 제거하는 절차가 별도로 존재하는 거야.

## 9-2. 잡음이 강해지면?

노트북에서는 SNR을 변경하면서 실험했어.

| SNR    | 모델 출력     |
| ------ | ------------- |
| 깨끗함 | 정상 문장     |
| 20dB   | 정상 문장     |
| 10dB   | 정상 문장     |
| 0dB    | 정상 문장     |
| -5dB   | 문장이 달라짐 |

-5dB에서는 다음과 같이 다른 문장을 생성한 사례도 있었어.

```
I want the fluid in there.
```

이 실험은 단순히 잡음이 있다고 해서 즉시 인식 결과가 무너지는 것은 아니지만, 음향적 증거가 약해질수록 잘못된 문장을 생성할 수 있음을 보여줘.

다만 이 결과는 특정 TTS 예문에 합성 흰 잡음을 추가한 실험이기 때문에 실제 노래나 모든 잡음 환경에 일반화해서는 안 돼.

## 9-3. 반복 문장 문제

노트북에서는 반복 문장에 대한 압축률도 측정했어.

- 정상 문장: 1.09
- 같은 단어 반복 문장: 3.51

반복이 심해지면 텍스트를 압축했을 때 비정상적으로 높은 압축률이 나타날 수 있어.

faster-whisper는 압축률 임계값 2.4를 초과하는 경우 Temperature를 높여 다시 디코딩하는 Fallback을 수행할 수 있어.

이것도 모델의 기본적인 자기회귀 생성 특성에서 발생할 수 있는 문제를 보완하기 위한 장치야.

# 장면 10. Song Lingo에서 Whisper는 어디에 위치하는가?

이제 전체 구조를 우리 프로젝트와 연결해 보자.

노트북에서 확인한 Song Lingo의 STT 실행 과정에는 세 가지 주요 부품이 있어.

| 구성 요소           | 역할                                   |
| ------------------- | -------------------------------------- |
| `feature_extractor` | 오디오를 Log-Mel로 변환                |
| `model`             | CTranslate2로 실행되는 Encoder-Decoder |
| `hf_tokenizer`      | Token ID와 실제 문자열 사이 변환       |

애플리케이션의 `stt.py`에서는 대략 다음 흐름으로 모델을 호출해.

```
사용자 오디오
      │
      ▼
stt.py
      │
      ▼
faster-whisper
      │
      ├─ Feature Extractor
      │       │
      │       ▼
      │    Log-Mel
      │
      ├─ CTranslate2 Model
      │       │
      │       ▼
      │    Encoder-Decoder
      │       │
      │       ▼
      │    Token IDs
      │
      └─ HuggingFace Tokenizer
              │
              ▼
          인식 문장
              │
              ▼
       scoring.py
              │
              ▼
       정답 문장과 비교
```

여기서 굉장히 중요한 서비스 설계상의 구분이 있어.

Whisper가 발음 점수를 계산하는 것은 아니야.

Whisper는 무엇을 말했는지 텍스트로 변환하는 모델이고, Song Lingo의 `scoring.py`가 인식 문장과 정답 문장을 비교해서 일치도를 계산하는 거야.

따라서 Whisper의 인식 정확도와 실제 발음의 정확도는 서로 다른 개념이야.

또한 노트북에서 확인한 `tiny`는 CPU 환경에서 구조와 동작을 분석하기 위한 모델이야. 앱에서는 일반적인 문장 연습에 tiny를 사용하고, 노래 가사 인식에는 medium을 사용하는 설정도 구분하고 있어.

# 장면 11. 전체를 하나의 데이터 흐름으로 정리

Demucs 스토리와 같은 형식으로 Whisper를 압축해 볼게.

## WHISPER — 소리 → 글

① 도착

2.65초 TTS 오디오 = 42,400 샘플 (16kHz, Mono)

② 표현 변환

STFT 400 / Hop 160 → 201개 FFT Bin → 80 Mel Channel

\\[ (80,266)\rightarrow(80,3000) \\]

짧은 소리는 0으로 Padding, 입력은 항상 30초

③ CNN Front-end

Conv1: (1,80,3000) → (1,384,3000)

Conv2: (1,384,3000) → (1,384,1500)

시간 해상도 10ms → 20ms

④ Transformer Encoder

Position Encoding 추가

4층, Dimension 384, 6 Heads

Self-Attention + FFN

\\[ (1,1500,384)\rightarrow(1,1500,384) \\]

⑤ Transformer Decoder

Prompt: SOT + en + transcribe + notimestamps

Token Embedding: 51,865 × 384

4층, Dimension 384

Masked Self-Attention + Cross-Attention + FFN

Encoder의 1500개 오디오 위치를 참고

⑥ 텍스트 생성

매 단계 Vocabulary 51,865개에 대한 Logits 계산

하나의 Token 선택 → 다음 단계 입력에 추가

⑦ 최종 결과

`I want to explore the universe.`

`<|endoftext|>`에서 생성 종료

## 마지막으로, 이 노트북에서 특히 주목할 만한 발견 5가지

| 발견                              | 기술적 의미                                    |
| --------------------------------- | ---------------------------------------------- |
| 짧은 오디오도 30초로 Padding      | Encoder의 입력 크기와 위치 수가 고정됨         |
| CNN이 시간축을 절반으로 압축      | Transformer가 처리할 Token 수를 감소           |
| Encoder 출력 1500×384             | 오디오를 1500개의 문맥적 Feature Vector로 표현 |
| Decoder가 51,865개 후보 중 선택   | 텍스트 생성은 Vocabulary 확률분포 예측 문제    |
| Decoder 파라미터가 Encoder보다 큼 | 큰 Token Embedding과 Cross-Attention이 존재    |

그리고 앞에서 공부했던 Demucs와 비교하면 더욱 명확해져.

| 구분        | HTDemucs Tiny 계열 분석   | Whisper Tiny         |
| ----------- | ------------------------- | -------------------- |
| 입력        | Waveform + Spectrogram    | Log-Mel              |
| CNN         | Encoder 2개 + Decoder 2개 | 입력 앞단 Conv1d 2개 |
| Transformer | 중간 Cross-Domain Encoder | Encoder + Decoder    |
| 출력        | 오디오 4개                | 텍스트 Token         |
| 최종 목적   | 소리 분리                 | 음성 인식            |

## 학습 노트북에 대한 기술적 보완 사항

네 노트북은 상당히 좋은 분석 과정을 담고 있어. 다만 발표나 후속 연구에서 정확성을 높이려면 다음 네 가지를 구분해 두는 게 좋아.

1\. 파라미터 수와 저장된 Tensor 원소 수

앞에서 계산한 37.8M은 `model.bin`에 저장된 Tensor의 원소를 Shape로 집계한 값이야. 고정 위치 인코딩 등의 비학습 Tensor도 포함될 수 있으므로 엄밀한 trainable parameter 수와 동일하다고 단정하면 안 돼.

2\. 저장 정밀도와 실행 정밀도

노트북의 모델 파일 파서가 출력한 Tensor 자료형은 float16이지만, 모델을 로드할 때는 `compute_type="int8"`을 지정했어.

저장된 파일의 자료형과 실제 런타임에서 사용하는 계산 정밀도는 구분해야 해.

3\. Attention Weight는 아직 직접 관찰하지 않았어.

현재 노트북은 Attention Layer의 Weight Shape와 전체 Encoder 출력 크기를 확인했어. 하지만 실제로 어느 오디오 위치에 Attention이 집중되는지는 확인하지 않았어.

그 부분은 별도로 PyTorch 기반 Whisper를 실행하거나 Attention 추출이 가능한 구현을 사용해야 해.

4\. 실험 데이터의 범위

이번 실험은 영어 TTS 예문과 합성 흰 잡음으로 진행됐어. 실제 노래, 한국어 노래, 다른 가수의 발성에 대한 일반화 성능을 검증한 것은 아니야.

내가 특히 권장하는 다음 학습 목표는 Encoder의 1500개 위치와 Decoder의 텍스트 Token 사이의 Cross-Attention을 실제 Heatmap으로 시각화하는 것이야.

그것까지 확인하면 지금까지 숫자로만 이해했던 Whisper의 구조가 실제 오디오의 시간축과 텍스트의 순서가 연결되는 과정으로 보이기 시작할 거야.

---
- CTranslate2 무엇인가?

- FFN 무엇인가? FFN linear 0의 모양? (1536,384)에서 1536은 어떻게 나온 숫자야?

- power spectrum, bin이 뭐야?

- log-Mel의 시간 프레임 266개는 어떻게 나온 숫자야?

- 첫번째 CNN에서 bias 384개는 어디서 나온 거야? Weights 384랑 연관이 있는 거야? 그리고 transformer encoder model 차원 수 384와도 관련이 있는 거야?
- Mel Channel 80개를 384개의 Feature Channel로 변환 ➡️ 왜 384개? Feature channel 내용의 예시? (구체적으로 feature가 무엇을 의미하는지 모르겠어) 한편, 이 행위가 각 시각마다 Mel로 표시/입력된 소리의 성질을 다른 feature로 바꾼다는 이해가 맞아?

- 각 Output Channel은 별도의 학습 가능한 Kernel Weight ➡️ 여기서 별도의 ‘학습‘은 누가, 언제, 무엇을, 왜, ‘학습’하는 걸 말하는 거야? 이 output을 입력으로 받는 decoder에서?

- 시간 위치를 Token 축으로 사용하기 위한 데이터 배치 변경 ➡️ token 축이 뭐야? 그리고 decoder의 입력 모양이 정확히/구체적으로 뭐길래? 구체적인 데이터나 그림으로 보여줘

- [두 번째 Conv1d에서 Stride가 2이므로 출력 위치는 20ms 단위가 돼 ➡️ 결과적으로 30초를 다음과 같이 표현해.. 각 위치는 20ms 간격으로 배치된 음향 특징 벡터] 이 설명을 조금 더 구체적으로, 실제 데이터나 그림으로, 설명해줘. Stride가 뭐길래 출력 위치가 이렇게 되는 건지, 그리고 ‘음향 특징 벡터‘가 구체적으로 무엇이고 어떻게 생긴 건지..

- [Encoder는 소리를 이해하기 위한 특징을 만들었어. Decoder는 그 특징을 보면서(= Encoder가 만든 오디오 특징도 참고, 이 말과 같은 뜻인 거 맞아?) 텍스트를 생성..] [Decoder의 텍스트 Token = Decoder가 입력받는 것] ➡️ 이 말은 Whisper의 Encoder 출력이 텍스트 토큰이라는 거야..? 출력 채널 384 * 384 이런 게 텍스트 토큰이라구? Encoder에서는 언제 텍스트 토큰을 만든 거야? 그런데 위 인용문에 따르면 encoder는 오디오 특징을 만들었다며? 오디오 특징 = 텍스트 토큰? Decoder 입력 설명에 갑자기 텍스트 토큰이 튀어나오는 게 이해가 안 돼..

- [정답은 현재까지 생성한 텍스트 Token] [Decoder가 최대 448개 위치의 Token을 처리] ➡️ 448 위치는 뭐야? 이 숫자는 어디서 나온 거지? 그리고 decoder에서 448 위치의 token_id 하나가 384차원 벡터로 변환된다고 했는데 , 이게 무슨 뜻이야? Decoder가 입력으로 384 어쩌구저쩌구 받은 거 아니었어..?

- Residual Connection과 Layer Normalization 각각 무엇인지?

- Transformer Layer를 통과한다고 시간 위치가 계속 줄어들거나 차원이 계속 늘어나는 것은 아니야. 같은 Shape 안에서 각 위치의 특징 벡터가 다른 위치의 정보를 반영하도록 갱신 ➡️ 특징 벡터라는 게 구체적으로, 정확히 무엇인지 여전히 모르겠어. 그리고 이게 self-attention인 거야?

- Q, K, V를 하나의 Projection에서 동시에 계산 ➡️ projection이 뭐야? 한 번의 epoch? Batch?

- 하나의 위치가 나머지 1500개 위치를 참고할 수 있도록 1500×1500의 관계 행렬을 계산 ➡️ 왜 관계 행렬을 만드는 거야..? 서로의 위치를 참고하는 계산 구현을 위한 방법이 행렬인 거야..? 이 행렬의 값들은 어떤 의미를 가져?

- [Head 하나의 Attention Score 행렬 크기. Tiny 모델은 Head가 6개이므로 Layer 하나에서 6개의 관계 행렬을 계산해] ➡️ 왜 head별로 관계 행렬을 계산해..?

- 큰 그림을 내가 이해한 건, whisper 입력(소리, 음성)에 대해 encoder에서 음성 특징을 뽑아냄 ➡️ decoder에서 특정 음성 특징을 특정 언어, 단어와 매칭시키는 확률을 약 51,000개 임베딩 단어 사전 항목별로 계산한다? 이 때 encoder 출력인 1500개 위치에 대해서도 참조해서 추측한다? 이게 맞아..? => [2026-11-11 11:33:00]

이번 질문은 사실 지금까지의 Whisper 학습에서 가장 중요한 전환점이야. 개별 용어를 이해하는 것도 중요하지만, 이제는 오디오 데이터, 신경망 내부의 숫자, 학습 가능한 Weight, Attention 계산, 텍스트 생성이 어떻게 하나의 계산 과정으로 연결되는지 이해해야 하거든.

네 질문을 살펴보니 특히 세 가지가 아직 명확하게 연결되지 않은 것 같아.

1. `384차원 Feature Vector`가 정확히 무엇인지.
2. Encoder가 만든 오디오 특징과 Decoder가 입력받는 텍스트 Token이 어떻게 다른지.
3. Attention의 1500×1500 행렬이 왜 필요하고, 그 숫자들이 무엇을 의미하는지.

먼저 가장 중요한 오해부터 바로잡을게.

가장 중요한 개념 구분

Whisper의 Encoder는 텍스트 Token을 만들지 않아.

Audio Encoder

혼합된 음성 특징을 1500개의 384차원 벡터로 표현

\\[ (1,1500,384) \\]

Audio Feature

Encoder의 출력은 Decoder에 별도로 전달돼.

Text Decoder의 입력

현재까지 생성한 텍스트 Token ID를 Embedding으로 변환

\\[ (1,L)\rightarrow(1,L,384) \\]

Text Feature

Cross-Attention

텍스트 특징이 오디오 Encoder 출력을 참고

Vocabulary Projection

다음 Text Token의 확률 계산

\\[ (1,L,384)\rightarrow(1,L,51865) \\]

즉, Whisper에는 서로 다른 두 종류의 표현이 존재해.

- Audio Feature Vector: 소리의 특징을 나타내는 숫자 벡터
- Text Token Embedding: 텍스트 Token ID에 대응하는 숫자 벡터

두 표현은 모두 384차원일 수 있지만, 담고 있는 정보와 생성 경로가 달라.

이제 이 차이를 중심으로 하나씩 풀어볼게.

# 1. CTranslate2는 무엇인가?

먼저 모델의 구조와 모델을 실행하는 소프트웨어를 구분하자.

CTranslate2는 Transformer 계열 모델을 효율적으로 실행하기 위한 C++ 기반 추론(Inference) 엔진이야.

여기서 중요한 용어는 추론이야.

- Training: 데이터를 이용해 Weight를 학습하고 업데이트하는 과정
- Inference: 이미 학습된 Weight를 사용해 새로운 입력에 대한 결과를 계산하는 과정

네 프로젝트에서는 다음과 같은 구조로 사용하고 있어.

Song Lingo의 Whisper 실행 구조

Whisper Pretrained Model

이미 학습된 Encoder / Decoder Weight

CTranslate2 변환 형식

`model.bin`

모델 변수와 Weight를 CTranslate2 형식으로 저장

CTranslate2 Runtime

CPU / GPU에서 최적화된 연산 수행

음성 인식 결과

여기서 `faster-whisper`는 Python에서 Whisper를 편리하게 사용할 수 있도록 CTranslate2를 연결해 주는 구현체야.

각 요소를 비교하면 다음과 같아.

| 구성 요소              | 역할                                         |
| ---------------------- | -------------------------------------------- |
| Whisper                | 음성 인식 모델 및 아키텍처                   |
| CTranslate2            | 모델 추론을 최적화하는 실행 엔진             |
| faster-whisper         | Whisper를 CTranslate2로 실행하는 Python 구현 |
| Hugging Face Tokenizer | Token ID와 텍스트 변환                       |

CTranslate2는 Whisper라는 새로운 모델을 만드는 것이 아니야. 동일한 모델의 학습된 Weight를 변환하고, 이를 효율적으로 계산하는 실행 환경을 제공하는 거야.

참고: [CTranslate2 공식 GitHub](https://github.com/OpenNMT/CTranslate2?utm_source=chatgpt.com) · [faster-whisper 공식 GitHub](https://github.com/SYSTRAN/faster-whisper?utm_source=chatgpt.com)

네 노트북에서는 `model.bin`의 Weight 자료형을 float16으로 확인했지만, 모델을 실행할 때는 `compute_type="int8"`을 지정했지.

이것도 서로 모순되는 게 아니야.

- 저장 파일의 자료형: Weight가 파일에 기록된 방식
- 실행 계산 자료형: CTranslate2가 연산할 때 사용하는 정밀도

모델 파일과 실행 엔진을 분리해서 이해하면 돼.

# 2. Power Spectrum과 Bin은 무엇인가?

이제 오디오 전처리로 돌아가자.

Whisper는 파형을 Log-Mel로 변환한다고 했지? 그 안에 들어가는 두 개념이 Power Spectrum과 Frequency Bin이야.

## 2-1. 먼저 FFT를 수행하면 무엇이 나오는가?

1초 동안 녹음한 소리가 있다고 하자.

Sampling Rate가 16kHz라면 샘플은 16,000개야.

그중 400개를 하나의 프레임으로 잘라 FFT를 수행한다고 생각해 보자.

\\[ 400\text{ samples}\div16000 =0.025\text{ sec} \\]

즉, 25ms짜리 소리 구간을 주파수 성분으로 변환하는 거야.

FFT를 수행하면 복소수 결과가 나와.

\\[ X[k]=a_k+jb_k \\]

여기서 \\(k\\)는 Frequency Bin의 인덱스야.

Bin은 특정 주파수에 대응하는 하나의 주파수 슬롯 또는 칸이라고 생각하면 돼.

Whisper의 FFT 설정은 다음과 같아.

\\[ N=400,\quad f_s=16000 \\]

따라서 인접한 FFT Bin의 주파수 간격은:

\\[ \Delta f=\frac{f_s}{N} =\frac{16000}{400}=40Hz \\]

실수 오디오 신호에 RFFT를 적용하면 양의 주파수 방향으로 다음과 같이 201개의 Bin이 생겨.

| Bin Index | 대응 주파수 |
| --------- | ----------- |
| 0         | 0Hz         |
| 1         | 40Hz        |
| 2         | 80Hz        |
| 3         | 120Hz       |
| 4         | 160Hz       |
| 5         | 200Hz       |
| ...       | ...         |
| 200       | 8,000Hz     |

Frequency Bin 개념도

실제 오디오의 FFT 그래프가 아니라 Bin이 주파수축에 배치되는 방식을 나타낸 개념도야.

## 2-2. Power Spectrum

FFT 결과에는 실수부와 허수부가 있어.

\\[ X[k]=a_k+jb_k \\]

각 주파수 성분의 크기(Magnitude)는 다음과 같아.

\\[ |X[k]|=\sqrt{a_k^2+b_k^2} \\]

그런데 Power Spectrum은 이 크기를 제곱해.

\\[ P[k]=|X[k]|^2 \\]

따라서:

\\[ P[k]=a_k^2+b_k^2 \\]

예를 들어 어떤 주파수 Bin의 FFT 결과가:

\\[ X[5]=3+4j \\]

라면:

\\[ |X[5]|=\sqrt{3^2+4^2}=5 \\]

Power는:

\\[ P[5]=3^2+4^2=25 \\]

이야.

| 항목      | 값  |
| --------- | --- |
| Real      | 3   |
| Imaginary | 4   |
| Magnitude | 5   |
| Power     | 25  |

즉, Power Spectrum은 각 주파수 성분의 에너지 크기를 표현하기 위한 값이야. 정확한 물리적 전력이나 에너지로 해석하려면 FFT 정규화와 Window 보정도 고려해야 해.

여기서 한 가지 중요한 차이가 있어.

- Magnitude Spectrum: 주파수 성분의 크기
- Power Spectrum: 주파수 성분 크기의 제곱
- Complex Spectrum: 크기와 위상 정보를 모두 포함

Whisper는 이 Power Spectrum을 Mel Filter Bank에 입력해.

반면 HTDemucs의 복소 스펙트럼 경로에서는 실수부와 허수부를 보존하는 방식도 사용했었지.

# 3. Log-Mel의 시간 프레임 266개는 어떻게 나오는가?

이제 정확한 숫자를 계산해 보자.

네 노트북의 입력은:

- 오디오 길이: 2.65초
- Sampling Rate: 16,000Hz
- FFT Size: 400
- Hop Length: 160

먼저 샘플 개수는:

\\[ N=2.65\times16000=42400 \\]

Hop Length는 160이므로:

\\[ \frac{16000}{160}=100 \\]

즉, 이론적으로 1초당 100개의 시간 프레임을 만들 수 있어.

따라서 2.65초라면 단순 계산으로:

\\[ 2.65\times100=265 \\]

프레임이 예상돼.

그런데 실제 노트북은 266개를 출력했어.

왜 1개 차이가 날까?

이것은 STFT의 경계 처리 방식 때문이야.

노트북에서 직접 구현한 `my_logmel()`을 살펴보면 다음과 같은 처리를 해.

1. 오디오 뒤에 160개의 0 샘플 추가
2. FFT 창의 절반인 200개 샘플을 앞뒤로 Reflect Padding
3. 400개 샘플짜리 Window를 160개 샘플씩 이동
4. 마지막 프레임 하나 제거

실제 숫자로 계산해 보자.

① 입력과 추가 Padding

\\[ 42400+160=42560 \\]

② 양쪽 Reflect Padding

\\[ 42560+200+200=42960 \\]

③ STFT 프레임 수

일반적인 프레임 개수 계산식은:

\\[ N\_{frames} = 1+\left\lfloor\frac{N\_{input}-N\_{FFT}}{Hop}\right\rfloor \\]

따라서:

\\[ =1+\left\lfloor \frac{42960-400}{160} \right\rfloor \\]

\\[ =1+266=267 \\]

④ 마지막 프레임 제거

노트북은 마지막 프레임을 제거했어.

\\[ 267-1=\boxed{266} \\]

2.65초 오디오의 실제 프레임 계산

42,400 samples

\+ 160 samples at the end

\+ 200 samples on each side

267 STFT frames

Remove last frame

# 266 frames

따라서 266이라는 숫자는 단순히 2.65초에 100을 곱한 결과가 아니라, `faster-whisper`의 STFT 경계 처리 및 마지막 프레임 제거 방식까지 반영된 결과야.

이런 세부 사항은 실제 코드로 확인해야 하는 부분이지.

# 4. CNN의 Weight 384개와 Bias 384개는 어떤 관계인가?

이제 질문한 CNN의 첫 번째 Layer로 돌아가자.

노트북에서 확인한 값은 다음과 같아.

```
encoder/conv1/weight : [384, 80, 3]
encoder/conv1/bias   : [384]
```

여기서 384가 세 번 등장하는 이유를 이해해 보자.

## 4-1. Output Channel이 384개라는 뜻

Conv1d의 Weight Shape는 다음 순서야.

\\[ (C\_{out},C\_{in},K) \\]

따라서:

\\[ (384,80,3) \\]

은 다음과 같은 의미야.

- Output Channel: 384개
- Input Channel: 80개
- Kernel Size: 3

즉, 출력 Feature Map을 384개 만들겠다는 뜻이야.

그렇다면 각 Output Channel에 필요한 Bias도 1개씩 존재해.

\\[ b\in\mathbb{R}^{384} \\]

왜 그럴까?

Convolution 계산 결과에 Bias를 더하기 때문이야.

일반적인 Conv1d 계산식은 다음과 같아.

\\[ Y[o,t]= \sum_c\sum_k W[o,c,k]X[c,ts+k-p]+b[o] \\]

여기서 \\(o\\)가 Output Channel이야.

각 Output Channel의 모든 시간 위치에 동일한 Bias \\(b[o]\\)가 적용돼.

따라서:

- Output Channel 0 → Bias 0
- Output Channel 1 → Bias 1
- ...
- Output Channel 383 → Bias 383

이렇게 384개의 Bias가 필요한 거야.

Bias가 각 시간 위치마다 하나씩 있는 것은 아니야. Channel마다 하나씩 존재해.

## 4-2. 실제 숫자로 계산해 보자.

아주 단순한 CNN을 가정해 보자.

Input Channel이 2개이고 Kernel Size가 2, Output Channel이 2개라고 하자.

\\[ W\in\mathbb{R}^{2\times2\times2} \\]

그리고 Bias는:

\\[ b=[0.5,-1.0] \\]

이야.

첫 번째 Output Channel의 Kernel은 다음과 같다고 가정할게.

\\[ W_0= \begin{bmatrix} 1&2\\\ 0&1 \end{bmatrix} \\]

두 번째 Output Channel은:

\\[ W_1= \begin{bmatrix} -1&0\\\ 2&1 \end{bmatrix} \\]

첫 번째 시간 위치에서 입력값이:

\\[ X= \begin{bmatrix} 3&4\\\ 5&6 \end{bmatrix} \\]

이라면 첫 번째 Output Channel의 계산 결과는:

\\[ Y[0,0] =3(1)+4(2)+5(0)+6(1)+0.5 \\]

\\[ =17.5 \\]

두 번째 Output Channel은:

\\[ Y[1,0] =3(-1)+4(0)+5(2)+6(1)-1 \\]

\\[ =12 \\]

결과적으로 출력은:

\\[ Y[:,0]=[17.5,12] \\]

가 돼.

Channel별 Weight와 Bias

Output Channel 0

\\(W_0\cdot X+0.5\\)

# 17.5

Bias = 0.5

Output Channel 1

\\(W_1\cdot X-1.0\\)

# 12

Bias = -1.0

이런 연산을 384개의 Output Channel에 대해 수행하는 거야.

## 4-3. 그렇다면 이 384가 Transformer의 Model Dimension 384와 같은 이유는?

이것은 우연이 아니야.

Whisper Tiny는 모델의 기본 표현 차원인 `n_state`를 384로 설정했어.

따라서 CNN의 출력 Channel을 384개로 설계한 거야.

\\[ C\_{out}=d\_{model}=384 \\]

이렇게 맞춰 놓으면 CNN의 출력을 별도의 차원 변환 없이 Transformer Encoder에 전달할 수 있어.

즉, 다음 두 가지는 서로 연결돼 있어.

- CNN의 Output Channel 384개
- Transformer의 Model Dimension 384

다만 CNN의 Bias 384개가 Transformer Dimension 384를 만들어 내는 것은 아니야.

384는 모델 설계자가 선택한 공통 Dimension이고, CNN Weight·Bias의 첫 번째 축은 그 Dimension에 맞춰 설계된 결과야.

# 5. Mel Channel 80개를 Feature Channel 384개로 변환한다는 것은?

이제 가장 중요한 질문 중 하나야.

> Feature Channel의 내용이 구체적으로 무엇이고, 소리의 성질을 다른 Feature로 바꾼다는 게 무슨 뜻인가?

여기서부터는 실제 숫자로 생각하는 게 가장 좋아.

## 5-1. CNN 입력 데이터는 어떤 모습일까?

Log-Mel의 Shape가 다음과 같았지.

\\[ X\in\mathbb{R}^{1\times80\times3000} \\]

이것을 그림으로 나타내면 다음과 같아.

Log-Mel 입력 데이터

[Whisper Architecture: Encoder-Decoder Speech Recognition - Interactive | Michael Brenndoerfer | Michael Brenndoerfer](https://images.openai.com/static-rsc-4/hkyUSTCcC4ampdecjGodfoKvtbv0TF83dAuODt9iavF_YRquYVKSE_Rz8_90ZHaFrWM-psHkLADu4sYyrJtUkOTjpeMzS7RH0Fx8gcZYMerWYGoJ3RNs-GcMOsuFFUkGHa0t5shIp5mvO_pRxARSyO_S53mKzsbevkD52BGcRR4?purpose=inline)

[mbrenndoerfer.com](https://mbrenndoerfer.com/writing/whisper-architecture-encoder-decoder-multilingual-asr?utm_source=chatgpt.com)

실제 노트북의 이미지가 아니라 음성 Log-Mel의 일반적인 시각적 예시야.

- 세로축: Mel Channel 80개
- 가로축: 시간 Frame 3000개
- 각 칸의 숫자: 해당 시각·Mel 대역의 Log Energy

예를 들어 시간 위치 100번에서 Log-Mel 값은 다음과 같은 벡터야.

\\[ x\_{100}= \begin{bmatrix} -0.1\\\ 0.2\\\ 0.5\\\ \vdots\\\ -0.3 \end{bmatrix} \in\mathbb{R}^{80} \\]

이것은 특정 시간 구간의 소리를 주파수 대역 80개로 표현한 숫자 묶음이야.

## 5-2. 첫 번째 CNN은 이 80개 값을 384개 값으로 바꿔.

이때 각 Output Channel이 서로 다른 Kernel Weight를 사용해.

수식으로 단순화하면:

\\[ y_j(t)= \sum\_{c=1}^{80}\sum\_{k=1}^{3} W\_{j,c,k}x_c(t+k-1)+b_j \\]

여기서:

- \\(c\\): 80개의 입력 Mel Channel 중 하나
- \\(k\\): 시간 방향 Kernel 위치
- \\(j\\): 384개의 Output Channel 중 하나

즉, Output Channel 하나를 만들 때 입력의 80개 Mel Channel과 인접한 시간 구간의 값을 모두 조합하는 거야.

그 결과:

\\[ 80\text{ Mel Channels} \rightarrow 384\text{ Feature Channels} \\]

가 되는 거지.

## 5-3. Feature란 구체적으로 무엇일까?

이 부분이 핵심이야.

우리가 앞에서 공부했던 소리의 특징을 떠올려 보자.

- 주파수 에너지 분포
- Harmonics
- Formants
- 진폭의 급격한 변화
- 시간적 반복 패턴
- 특정 주파수 대역의 변화

이런 정보는 음성의 발음이나 음향적 특성을 구분하는 데 도움이 될 수 있어.

CNN의 384개 Output Channel은 이런 정보들을 표현하는 데 사용할 수 있는 384개의 학습된 Feature 표현 공간을 구성해.

예를 들어 이해를 위한 가상의 Channel을 만들어 보자.

| 가상 Channel | 높은 활성값을 보이는 입력 패턴의 예       |
| ------------ | ----------------------------------------- |
| Channel 1    | 낮은 주파수 대역의 에너지가 증가하는 패턴 |
| Channel 2    | 높은 주파수 대역의 에너지 변화            |
| Channel 3    | 짧은 시간에 발생한 급격한 에너지 변화     |
| Channel 4    | 특정 주파수 영역의 지속적인 에너지        |
| Channel 5    | 여러 대역에 걸친 복합적인 변화            |
| ...          | ...                                       |
| Channel 384  | 또 다른 학습된 조합                       |

이 표는 개념을 설명하기 위해 만든 가상의 예시야. 실제 Whisper Tiny의 Channel 1이 반드시 저주파 에너지를 담당한다는 사실을 확인한 것은 아니야.

실제 Channel들이 어떤 음향 특징에 반응하는지는 각 Channel의 Weight와 Activation을 분석해야 알 수 있어.

### 중요한 질문: 매 시간 위치마다 384개의 Feature가 생성되는가?

맞아.

첫 번째 CNN은 시간 위치 3000개 각각에 대해 384개 Feature 값을 생성해.

예를 들어 특정 시간 위치 t에서:

\\[ Y_t= \begin{bmatrix} 0.15\\\ -0.32\\\ 1.07\\\ 0.45\\\ \vdots\\\ -0.12 \end{bmatrix} \in\mathbb{R}^{384} \\]

이런 벡터가 생성되는 거야.

따라서:

\\[ Y\in\mathbb{R}^{1\times384\times3000} \\]

이 돼.

이것은 네가 말한 이해와 대체로 일치해.

각 시간 위치에서 관찰된 Mel 주파수 정보가 CNN의 학습된 Kernel을 거쳐 다른 384개 Feature 값으로 변환되는 것이야.

다만 첫 번째 CNN의 Kernel Size가 3이므로, 정확히는 해당 시각 하나만 보는 게 아니라 인접한 세 시간 프레임의 정보를 함께 사용해.

## 5-4. 그런데 이 Feature Channel은 누가 학습하는가?

여기가 매우 중요해.

앞에서 이야기했던 역전파와 연결하자.

Whisper가 학습될 때, 모델은 대량의 오디오와 그에 대응하는 텍스트를 사용해 학습돼.

```
학습 데이터

Audio
  │
  ▼
CNN Encoder
  │
  ▼
Transformer Encoder
  │
  ▼
Transformer Decoder
  │
  ▼
예측 Token
  │
  ▼
정답 Token과 비교
  │
  ▼
Loss 계산
  │
  ▼
Backpropagation
  │
  ▼
CNN + Transformer + Embedding Weight 업데이트
```

CNN의 Weight만 별도로 학습하는 게 아니야.

모델 전체가 하나의 학습 과정에 참여해.

예를 들어 Decoder의 예측이 틀리면 Loss가 커져.

역전파는 이 Loss가 CNN의 각 Weight에 얼마나 영향을 받는지 계산하고, Optimizer는 Weight를 업데이트해.

따라서:

- CNN Kernel Weight도 학습되고
- CNN Bias도 학습되고
- Attention의 Projection Weight도 학습되고
- FFN Weight도 학습되고
- Token Embedding Weight도 학습돼.

Decoder가 CNN Output Channel을 학습하는 것이 아니라, 모델 전체의 학습 과정에서 CNN Weight도 함께 최적화되는 것이야.

그리고 네 노트북은 이 학습을 수행한 것이 아니라, 이미 학습이 끝난 Tiny 모델을 불러와 구조와 결과를 분석한 거야.

# 6. Token 축은 무엇인가? Encoder 출력과 Decoder 입력의 모양

이제 앞에서 생긴 가장 큰 혼란을 해결해 보자.

먼저 Token이라는 단어에는 두 가지 의미가 존재할 수 있어.

1. Transformer에 넣는 Sequence의 한 위치를 의미하는 넓은 표현
2. 자연어 Tokenizer가 만든 텍스트 Token ID

이 둘을 구분해야 해.

## 6-1. Encoder의 1500개 위치도 Token이라고 부를 수 있을까?

Transformer 관점에서는 각각의 위치를 하나의 입력 요소로 볼 수 있어.

따라서 오디오 Encoder의 1500개 위치를 편의상 Audio Token 또는 Audio Position이라고 부르기도 해.

하지만 이것은 자연어의 단어 Token과 달라.

예를 들어:

```
Audio Position 0  → 384차원 음향 특징
Audio Position 1  → 384차원 음향 특징
Audio Position 2  → 384차원 음향 특징
...
Audio Position 1499 → 384차원 음향 특징
```

어떤 위치가 `hello`라는 단어를 나타내는 것은 아니야.

그냥 특정 시간 위치에서의 오디오 Feature Vector야.

## 6-2. CNN 출력의 차원 변경

CNN의 출력은 다음과 같았어.

\\[ X\_{CNN}\in\mathbb{R}^{1\times384\times1500} \\]

여기서 Channel과 Time 축을 바꿔.

\\[ X\_{EncoderInput} = Transpose(X\_{CNN}) \\]

\\[ \in\mathbb{R}^{1\times1500\times384} \\]

왜 바꾸는 걸까?

Transformer는 일반적으로 다음과 같은 형태의 입력을 처리하기 때문이야.

\\[ (Batch,Sequence,EmbeddingDimension) \\]

그러면:

| 차원 | 의미                            |
| ---- | ------------------------------- |
| 1    | Batch                           |
| 1500 | Sequence Length                 |
| 384  | 각 Position의 Feature Dimension |

이렇게 되는 거야.

CNN 출력과 Transformer Encoder 입력의 관계

CNN 출력 (B, C, T)

# (1, 384, 1500)

384개 Feature Channel × 1500개 시간 위치

Transpose (B, T, C)

# (1, 1500, 384)

1500개 시간 위치 × 각 위치의 384차원 Feature

이 Transpose는 데이터를 다시 학습하거나 새로운 정보를 생성하는 연산이 아니야. Tensor의 축 순서를 바꾸는 작업이지.

# 7. Stride 2는 왜 20ms 간격을 만드는가?

이번에는 실제 시간 데이터를 만들어 보자.

Whisper의 Log-Mel은 10ms마다 하나의 프레임이 만들어져.

가상의 작은 구간을 다음과 같이 표현하자.

| Frame Index | 시간 | 각 프레임의 Feature |
| ----------- | ---- | ------------------- |
| 0           | 0ms  | \\(x_0\\)           |
| 1           | 10ms | \\(x_1\\)           |
| 2           | 20ms | \\(x_2\\)           |
| 3           | 30ms | \\(x_3\\)           |
| 4           | 40ms | \\(x_4\\)           |
| 5           | 50ms | \\(x_5\\)           |
| 6           | 60ms | \\(x_6\\)           |
| 7           | 70ms | \\(x_7\\)           |

여기서 두 번째 Conv1d가 다음과 같이 설정되어 있어.

- Kernel Size = 3
- Stride = 2
- Padding = 1

## 7-1. Stride는 무엇인가?

Stride는 Kernel이 다음 위치로 이동하는 간격이야.

Kernel Size가 3이므로 한 번 연산할 때 세 프레임을 함께 살펴봐.

Stride가 1이라면:

```
첫 번째 연산
[x0][x1][x2]
       ↓ 10ms 이동

두 번째 연산
    [x1][x2][x3]
          ↓ 10ms 이동

세 번째 연산
        [x2][x3][x4]
```

Stride가 2라면:

```
첫 번째 연산
[x0][x1][x2]
          ↓ 20ms 이동

두 번째 연산
        [x2][x3][x4]
                  ↓ 20ms 이동

세 번째 연산
              [x4][x5][x6]
```

즉, Kernel이 10ms씩 움직이는 대신 20ms씩 움직이는 거야.

그래서 출력 위치가 10ms 간격에서 20ms 간격으로 바뀌는 거지.

## 7-2. 실제 계산 결과의 시간 위치

Padding 1을 적용하므로 첫 번째와 마지막 Kernel이 입력의 경계도 처리할 수 있어.

이를 시간축 기준으로 단순화하면 다음과 같아.

Stride 2의 위치 변화

3개 프레임을 한 번에 보고, 다음 계산은 2프레임 뒤에서 시작해.

입력: 10ms 간격

0

10

20

30

40

50

60

70

출력 중심 위치: 20ms 간격

## 0

ms

## 20

ms

## 40

ms

## 60

ms

여기서 아주 중요한 오해를 하나 방지할게.

출력 위치 사이의 간격이 20ms라는 것이지, 각 출력 벡터가 정확히 20ms 분량의 소리만 담는다는 의미는 아니야.

실제로 Kernel Size가 3이고, 그 앞의 Conv1에서도 Kernel Size가 3이므로 두 Convolution을 합친 시간 방향 Receptive Field는 5개의 Log-Mel 프레임이야.

계산해 보면:

\\[ RF=3+(3-1)\times1=5 \\]

즉, 하나의 출력 벡터는 개념적으로 주변 약 5개 Log-Mel 프레임의 정보를 반영할 수 있어.

각 프레임의 간격이 10ms니까 대략 50ms에 해당하는 범위야.

그러면서 출력 벡터의 위치 중심은 20ms 간격으로 배치되는 거지.

이 둘은 다른 개념이야.

- Receptive Field: 한 출력값이 참고하는 입력의 범위
- Output Stride: 출력 위치 사이의 간격

## 7-3. 그러면 음향 특징 벡터는 실제로 어떻게 생겼을까?

이제 20ms 위치마다 384개의 숫자가 만들어지는 과정을 보자.

예를 들어 CNN의 두 번째 Layer를 통과한 첫 번째 출력 위치가 다음과 같다고 해보자.

\\[ h_0= [0.12,-0.31,0.85,0.22,\ldots,0.41] \\]

두 번째 출력 위치는:

\\[ h_1= [0.18,-0.25,0.74,0.39,\ldots,0.12] \\]

세 번째 출력 위치는:

\\[ h_2= [-0.07,0.52,0.31,0.11,\ldots,-0.28] \\]

각 벡터에는 384개의 숫자가 있어.

실제 Weight와 Activation을 이 노트북에서 추출하지는 않았으므로 위 숫자는 이해를 위한 가상의 예시야.

실제 구조는 다음과 같아.

Whisper Audio Feature Matrix

384차원 벡터를 시간 순서로 배열한 모습. 아래 값은 가상 데이터야.

| 시간 위치 | Feature 1 | Feature 2 | Feature 3 | ... | Feature 384 |
| --------- | --------- | --------- | --------- | --- | ----------- |
| 0ms       | 0.12      | -0.31     | 0.85      | ... | 0.41        |
| 20ms      | 0.18      | -0.25     | 0.74      | ... | 0.12        |
| 40ms      | -0.07     | 0.52      | 0.31      | ... | -0.28       |
| 60ms      | 0.30      | 0.11      | -0.16     | ... | 0.57        |
| ...       | ...       | ...       | ...       | ... | ...         |
| 29.98s    | 0.02      | -0.13     | 0.44      | ... | 0.07        |

이 행렬을 다음과 같이 생각하면 돼.

- 가로 방향: 하나의 시점에서 추출한 384개 Feature
- 세로 방향: 20ms 간격으로 배열된 1500개 시점

이것이 Transformer Encoder의 입력이야.

여기서 Feature Vector의 384개 원소가 각각 무엇을 의미하는지는 사람이 미리 정해 놓은 게 아니야.

학습 과정에서 모델이 음성 인식에 유용한 표현을 만들어 낸 결과야.

# 8. 그렇다면 Decoder는 무엇을 입력받는가?

이제 네가 가장 혼란스러워했던 부분을 정확히 해결하자.

Whisper의 Decoder는 두 가지 입력 경로를 가지고 있어.

첫 번째 입력: 지금까지 생성한 텍스트 Token

두 번째 입력: Encoder가 만들어 놓은 오디오 Feature

이 둘을 절대로 같은 것으로 이해하면 안 돼.

## 8-1. 텍스트 Token ID가 먼저 존재한다

노트북에서 Decoder에 입력한 Prompt는 다음과 같아.

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
```

이것을 Token ID로 바꾸면:

```
[50258, 50259, 50359, 50363]
```

Shape는 다음과 같아.

\\[ TokenIDs\in\mathbb{N}^{1\times4} \\]

여기서 4는 Token의 개수야.

즉, Decoder에 처음 입력되는 데이터는 384차원 벡터가 아니라 4개의 정수 ID야.

## 8-2. Embedding Lookup

그런데 Transformer는 이런 정수 ID만으로 계산하지 않아.

각 Token ID에 대응하는 384차원 벡터를 가져와야 해.

이를 Embedding Lookup이라고 불러.

노트북에서 확인한 Embedding Weight는:

\\[ W\_{emb}\in\mathbb{R}^{51865\times384} \\]

이야.

행렬을 상상해 보자.

Token Embedding Matrix

51,865행 × 384열

실제 Weight 값이 아니라 Matrix의 행과 열을 설명하는 그림이야.

예를 들어 첫 번째 Token ID 50258을 입력하면:

\\[ e_1=W\_{emb}[50258] \\]

결과는 384개의 숫자로 구성된 벡터야.

\\[ e_1\in\mathbb{R}^{384} \\]

두 번째 Token도 동일하게:

\\[ e_2=W\_{emb}[50259] \\]

이렇게 변환해.

네 개의 Token ID를 모두 변환하면:

\\[ (1,4)\rightarrow(1,4,384) \\]

가 되는 거야.

즉, Token ID 하나가 384차원 벡터 하나로 변환되고, Token ID 네 개가 네 개의 384차원 벡터가 되는 것이지.

이것이 Decoder의 초기 입력 형태야.

## 8-3. 실제 Decoder에 들어가는 두 가지 데이터

이제 다시 비교해 보자.

## Decoder의 두 가지 입력

입력 A · Text Tokens

Prompt Token IDs

\\[ (1,4) \\]

Token Embedding

\\[ (1,4,384) \\]

지금까지 작성한 텍스트 정보

입력 B · Audio Features

Encoder Output

\\[ (1,1500,384) \\]

음성에서 추출된 시간적·음향적 정보

Decoder

Masked Self-Attention은 입력 A를 처리하고, Cross-Attention은 입력 A의 Query로 입력 B의 Key와 Value를 참고해.

이것이 바로 네가 인용했던 두 문장이 어떻게 연결되는지에 대한 답이야.

- Encoder는 소리를 의미 있는 Audio Feature로 변환해.
- Decoder는 이전 텍스트 Token을 입력받아, Encoder의 Audio Feature도 참고하면서 다음 텍스트 Token을 생성해.

Encoder 출력이 Text Token이 되는 순간은 없어.

텍스트 Token은 처음에는 Prompt로 제공되고, 그다음에는 Decoder가 하나씩 생성하는 거야.

# 9. Decoder의 448 위치는 정확히 무엇인가?

노트북에서 다음 변수를 확인했지.

```
decoder/position_encodings
[448, 384]
```

이것은 Decoder가 사용할 수 있도록 준비된 위치 정보의 최대 길이를 의미해.

448은 실제 입력 Token 개수가 아니고, 모델이 처리할 수 있는 Token Sequence의 최대 위치 수야.

Whisper Tiny의 `n_text_ctx` 설정이 448인 것이지.

앞에서 본 Encoder의 위치 정보는:

\\[ [1500,384] \\]

였어.

두 개를 비교해 보자.

| 구분                   | Encoder               | Decoder           |
| ---------------------- | --------------------- | ----------------- |
| Position Encoding 길이 | 1500                  | 448               |
| Dimension              | 384                   | 384               |
| 대상                   | 오디오 위치           | 텍스트 위치       |
| 1개 위치의 의미        | 20ms 간격의 음향 특징 | 텍스트 Token 하나 |

## 9-1. 실제로는 네 개부터 시작한다

이번 예시의 최초 Prompt는 Token 4개야.

따라서:

\\[ Input=(1,4,384) \\]

이 상태에서 Decoder가 한 번 계산하면 다음 Token을 예측해.

모델이 ` I`를 선택했다면 다음 입력은:

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
ĠI
```

총 5개 Token이 되지.

Embedding을 적용하면:

\\[ (1,5,384) \\]

이제 다시 Decoder에 입력해 다음 Token을 예측하는 거야.

이렇게 반복되는 거지.

| 생성 단계 | Decoder 입력 Token 수 | 입력 Tensor Shape |
| --------- | --------------------- | ----------------- |
| 1         | 4                     | (1,4,384)         |
| 2         | 5                     | (1,5,384)         |
| 3         | 6                     | (1,6,384)         |
| 4         | 7                     | (1,7,384)         |
| ...       | ...                   | ...               |
| 최대 문맥 | 최대 448              | (1,448,384)       |

이것이 448이라는 숫자의 의미야.

실제 추론에서는 KV Cache를 사용하므로 이미 처리한 위치 전체의 연산을 반복하지 않고 새 Token에 필요한 부분을 주로 계산해.

그리고 이 448은 Tiny 모델이 가진 Decoder의 최대 Text Context 설정이지, 모든 문장 길이가 448개이거나 448개를 항상 입력받는다는 뜻은 아니야.

# 10. Residual Connection과 Layer Normalization

이제 Transformer Layer 내부에서 빠뜨리기 쉬운 두 가지 개념을 살펴보자.

## 10-1. Residual Connection: 입력을 출력에 더한다

예를 들어 어떤 Transformer Sub-layer에 다음 입력이 들어갔다고 하자.

\\[ x=[1,2,3] \\]

Sub-layer가 계산한 결과가:

\\[ F(x)=[0.1,-0.2,0.5] \\]

라면 Residual Connection은 다음과 같아.

\\[ y=x+F(x) \\]

따라서:

\\[ y=[1.1,1.8,3.5] \\]

이렇게 입력 정보가 출력에도 직접 반영되는 거야.

Residual Connection

Input \\(x\\)

\\[ [1,2,3] \\]

Sub-layer \\(F(x)\\)

\\[ [0.1,-0.2,0.5] \\]

원래 Input

\\[ x \\]

Sub-layer Output

\\[ F(x) \\]

Residual Output

\\[ x+F(x)=[1.1,1.8,3.5] \\]

왜 이런 구조를 사용할까?

깊은 신경망에서는 Layer가 많아질수록 Gradient가 전달되기 어려워지는 문제가 발생할 수 있어.

Residual Connection은 입력이 출력으로 직접 전달되는 경로를 만들어 학습과 정보 전달을 돕는 역할을 해.

Whisper의 Transformer Layer에서도 Attention 및 FFN의 출력과 기존 입력을 더하는 Residual 구조를 사용해.

## 10-2. Layer Normalization: 특징 벡터의 값 분포를 정규화한다

이번에는 Layer Normalization이야.

384차원 Feature Vector의 각 값이 서로 다른 크기를 가질 수 있잖아?

예를 들어:

\\[ x=[1,2,3,4] \\]

라고 해보자.

먼저 평균을 계산해.

\\[ \mu=\frac{1+2+3+4}{4}=2.5 \\]

분산은:

\\[ \sigma^2=1.25 \\]

표준편차는:

\\[ \sigma=\sqrt{1.25} \approx1.118 \\]

각 원소에서 평균을 빼고 표준편차로 나눠.

\\[ \hat x_i= \frac{x_i-\mu}{\sqrt{\sigma^2+\epsilon}} \\]

여기서는 계산 편의상 \\(\epsilon\\)을 무시하면:

\\[ \hat{x}\approx[-1.342,-0.447,0.447,1.342] \\]

이것이 정규화된 값이야.

그런데 실제 Layer Normalization은 여기서 끝나지 않아.

학습 가능한 두 가지 파라미터를 추가해.

- Gamma: 값의 Scale 조정
- Beta: 값의 Shift 조정

\\[ y_i=\gamma_i\hat x_i+\beta_i \\]

이렇게 하면 모델이 필요한 값의 범위를 다시 학습할 수 있어.

Whisper의 LayerNorm은 각 Token 위치마다 384개의 Feature Dimension을 기준으로 평균과 분산을 계산해.

즉, Batch 전체에 대해 정규화하는 Batch Normalization과는 달라.

| 개념                | 역할                                |
| ------------------- | ----------------------------------- |
| Residual Connection | 기존 입력을 Sub-layer 출력에 더함   |
| Layer Normalization | 각 Token의 Feature 값 분포를 정규화 |

Whisper의 CTranslate2 변수에서도 `gamma`, `beta`가 각각 384개씩 저장된 것을 확인할 수 있었지.

# 11. FFN은 무엇이고, 왜 384에서 1536으로 늘어날까?

이제 Transformer의 내부에서 Attention과 함께 사용되는 FFN을 자세히 살펴보자.

FFN은 Feed-Forward Network의 약자야.

Whisper의 Transformer Layer에서는 Attention을 수행한 후 FFN을 통과해.

## 11-1. FFN의 기본 구조

Whisper Tiny에서 확인한 Weight Shape는 다음과 같아.

```
ffn/linear_0/weight : (1536, 384)
ffn/linear_0/bias   : (1536)

ffn/linear_1/weight : (384, 1536)
ffn/linear_1/bias   : (384)
```

두 개의 Linear Layer를 사용하는 구조야.

\\[ 384\rightarrow1536\rightarrow384 \\]

첫 번째 Linear 연산은 다음과 같아.

\\[ h=W_1x+b_1 \\]

여기서:

\\[ W_1\in\mathbb{R}^{1536\times384} \\]

\\[ x\in\mathbb{R}^{384} \\]

따라서:

\\[ h\in\mathbb{R}^{1536} \\]

이제 GELU 활성화 함수를 적용해.

\\[ h'=GELU(h) \\]

그리고 두 번째 Linear Layer를 통과해.

\\[ y=W_2h'+b_2 \\]

\\[ W_2\in\mathbb{R}^{384\times1536} \\]

따라서 최종적으로:

\\[ y\in\mathbb{R}^{384} \\]

다시 원래 차원으로 돌아오는 거야.

FFN 내부 차원 변화

입력 Feature

# 384

Linear 0

\\[ W_1:(1536,384) \\]

# 1536

GELU

비선형 변환

Linear 1

\\[ W_2:(384,1536) \\]

# 384

출력 Feature

# 384

## 11-2. 1536은 어떻게 결정된 숫자일까?

이 숫자는 데이터에서 자동으로 발견된 결과가 아니야.

Whisper의 아키텍처 설계자가 Model Dimension의 4배를 FFN의 중간 차원으로 설정했기 때문이야.

\\[ d\_{FFN}=4d\_{model} \\]

Whisper Tiny에서는:

\\[ 4\times384=1536 \\]

Base에서는:

\\[ 4\times512=2048 \\]

Medium에서는:

\\[ 4\times1024=4096 \\]

이 되는 거야.

이 4배 설정은 Transformer 계열에서 널리 사용되는 설계 선택이야. 모든 Transformer가 반드시 4배를 사용하는 것은 아니고, 아키텍처에 따라 달라질 수 있어.

## 11-3. 왜 차원을 늘렸다가 다시 줄일까?

Attention이 수행하는 일과 FFN이 수행하는 일이 다르기 때문이야.

- Attention: 여러 Token 위치 사이에서 정보를 결합
- FFN: 각 위치의 Feature Vector 자체를 비선형적으로 변환

예를 들어 Attention을 통해 다른 시간 위치의 정보가 반영된 384차원 벡터가 만들어졌다고 하자.

FFN은 이 벡터를 1536차원의 중간 표현으로 확장해 더 다양한 선형 조합을 만들 수 있게 하고, GELU를 통해 비선형성을 부여한 뒤 다시 384차원으로 투영해.

384개의 입력 특징을 그대로 유지하면서도 더 복잡한 특징 조합을 학습하도록 하는 거야.

### FFN의 파라미터 수

이 부분도 실제 숫자로 계산해 보자.

첫 번째 Linear:

\\[ 1536\times384+1536 =591,360 \\]

두 번째 Linear:

\\[ 384\times1536+384 =590,208 \\]

두 개를 더하면:

\\[ \boxed{1,181,568} \\]

개의 Weight와 Bias가 있어.

LayerNorm의 Gamma와 Beta까지 포함하면:

\\[ 1,181,568+768 =\boxed{1,182,336} \\]

이야.

Whisper Tiny의 Encoder Layer 하나에서 FFN 부분이 약 118만 개의 수치를 차지하는 거지.

# 12. Projection은 무엇인가? Batch나 Epoch와 같은 개념인가?

아니야. Projection은 선형 변환을 의미해.

앞에서 FFN을 설명할 때 사용했던 Linear Layer와 동일한 기본 연산이야.

\\[ Y=XW+b \\]

입력 벡터에 Weight Matrix를 곱해 다른 차원 또는 다른 표현 공간으로 옮기는 것이지.

## 실제 숫자로 계산하기

입력이 다음과 같다고 하자.

\\[ X=[1,2] \\]

Weight Matrix가:

\\[ W= \begin{bmatrix} 1&2\\\ 3&4\\\ 5&6 \end{bmatrix} \\]

라면:

\\[ XW^T = [1,2] \begin{bmatrix} 1&3&5\\\ 2&4&6 \end{bmatrix} \\]

\\[ =[5,11,17] \\]

입력은 2차원 벡터였지만 결과는 3차원 벡터가 됐어.

이런 선형 변환을 Projection이라고 부르는 거야.

| 용어       | 의미                                       |
| ---------- | ------------------------------------------ |
| Projection | Vector를 Weight Matrix로 선형 변환         |
| Batch      | 한 번의 연산에서 함께 처리하는 데이터 묶음 |
| Epoch      | 전체 학습 데이터를 한 번 순회하는 단위     |
| Stride     | Convolution Kernel의 이동 간격             |

서로 다른 개념이지.

## 12-1. Whisper의 QKV Projection

Encoder의 Self-Attention에서는 다음과 같은 Weight가 있어.

\\[ W\_{QKV}\in\mathbb{R}^{1152\times384} \\]

입력의 각 위치는 384차원 벡터야.

\\[ x\in\mathbb{R}^{384} \\]

Projection을 적용하면:

\\[ xW\_{QKV}^T\in\mathbb{R}^{1152} \\]

이 결과를 세 부분으로 나눠.

\\[ 1152=384+384+384 \\]

따라서:

```
Projection 결과: 1152차원
       │
       ├── 앞의 384개 → Query
       ├── 다음 384개 → Key
       └── 마지막 384개 → Value
```

이렇게 한 번의 큰 Matrix Multiplication으로 Q, K, V를 함께 계산할 수 있어.

따라서 'Q, K, V를 하나의 Projection에서 계산한다'는 의미는 하나의 학습 가능한 선형 변환 행렬을 사용해 3개의 벡터를 동시에 계산한다는 뜻이야.

Batch나 Epoch와는 관련이 없어.

# 13. Attention은 왜 1500 × 1500 행렬을 만드는가?

이제 Transformer의 가장 중요한 수학적 개념을 다시 연결해 보자.

Encoder에는 1500개의 Audio Position이 있어.

각 Position은 384차원 벡터를 가지고 있지.

\\[ X\in\mathbb{R}^{1500\times384} \\]

우리가 알고 싶은 것은 각 위치가 다른 위치의 정보를 얼마나 참고해야 하는지야.

예를 들어:

- 0번 위치는 100번 위치를 얼마나 참고할까?
- 100번 위치는 900번 위치를 얼마나 참고할까?
- 900번 위치는 1200번 위치를 얼마나 참고할까?

이런 관계를 계산해야 해.

## 13-1. Query와 Key의 Dot Product

각 위치에서 Query와 Key를 만들었다고 하자.

\\[ Q\in\mathbb{R}^{1500\times64} \\]

\\[ K\in\mathbb{R}^{1500\times64} \\]

여기서는 Head 하나의 차원을 사용한 거야.

이제 다음 연산을 수행해.

\\[ S=QK^T \\]

행렬 크기를 확인해 보자.

\\[ (1500\times64)\times(64\times1500) \\]

따라서 결과는:

\\[ \boxed{1500\times1500} \\]

이 되는 거야.

이것이 Attention Score Matrix야.

행과 열에 각각 1500개의 위치가 들어가기 때문에 1500×1500이 되는 것이지.

## 13-2. 이 행렬을 왜 만드는가?

행렬의 각 원소가 두 위치 사이의 유사도를 나타내기 때문이야.

\\[ S\_{i,j}=Q_i\cdot K_j \\]

예를 들어:

\\[ S\_{100,900} \\]

은 100번 위치의 Query와 900번 위치의 Key 사이의 Dot Product야.

이 값을 통해 100번 위치가 900번 위치의 정보를 얼마나 참고할지 계산할 수 있는 거지.

그다음 Scaling과 Softmax를 적용해.

\\[ A=Softmax \left( \frac{QK^T}{\sqrt{d_k}} \right) \\]

이렇게 하면 각 행의 값이 0\~1 사이의 가중치로 변환되고, 각 행의 합은 1이 돼.

## 13-3. 실제 숫자로 의미 해석하기

설명을 위해 Attention Matrix가 4×4라고 가정해 보자.

\\[ A= \begin{bmatrix} 0.7&0.1&0.1&0.1\\\ 0.2&0.5&0.2&0.1\\\ 0.1&0.2&0.6&0.1\\\ 0.1&0.1&0.2&0.6 \end{bmatrix} \\]

| Query 위치 ↓ / Key 위치 → | 0   | 1   | 2   | 3   |
| ------------------------- | --- | --- | --- | --- |
| 0                         | 0.7 | 0.1 | 0.1 | 0.1 |
| 1                         | 0.2 | 0.5 | 0.2 | 0.1 |
| 2                         | 0.1 | 0.2 | 0.6 | 0.1 |
| 3                         | 0.1 | 0.1 | 0.2 | 0.6 |

예를 들어 첫 번째 행을 보자.

\\[ [0.7,0.1,0.1,0.1] \\]

이것은 Query 0번 위치가 새로운 Feature를 만들 때:

- Key 0번의 Value를 70%
- Key 1번의 Value를 10%
- Key 2번의 Value를 10%
- Key 3번의 Value를 10%

정도로 반영한다는 의미야.

실제 Output은 다음과 같이 계산돼.

\\[ O_0= 0.7V_0+0.1V_1+0.1V_2+0.1V_3 \\]

즉, Attention 행렬은 단순한 유사도 표가 아니라 어떤 위치의 Value 정보를 얼마나 결합할지 결정하는 가중치 행렬이야.

Attention 행렬의 실제 의미

가상의 4×4 데이터

K0

K1

K2

K3

Q0

0.7

0.1

0.1

0.1

Q1

0.2

0.5

0.2

0.1

Q2

0.1

0.2

0.6

0.1

Q3

0.1

0.1

0.2

0.6

밝고 진한 칸일수록 해당 Key 위치의 Value 정보를 더 많이 반영하는 예시야.

이렇게 각 위치는 서로 다른 위치의 정보를 결합해서 새로운 Feature Vector를 만들어.

그 계산 결과가:

\\[ O=AV \\]

야.

## 13-4. 이 행렬은 학습 가능한 파라미터인가?

아니야. 이 부분도 매우 중요해.

다음 두 가지를 구분하자.

| 대상                             | 성격                                  |
| -------------------------------- | ------------------------------------- |
| \\(W_Q,W_K,W_V\\)                | 학습 가능한 Weight Parameter          |
| \\(A=Softmax(QK^T/\sqrt{d_k})\\) | 입력에 따라 계산되는 Attention Weight |

Attention Matrix는 입력 오디오가 바뀌면 값도 달라져.

반면 Q, K, V를 만드는 Projection Weight는 모델을 학습하는 동안 최적화되어 저장되는 파라미터야.

즉, Attention Matrix 자체는 모델 파일에 고정된 학습 파라미터가 아니라, 입력마다 동적으로 계산되는 결과야.

# 14. 왜 Head별로 Attention Matrix를 따로 계산할까?

Whisper Tiny는 Attention Head가 6개야.

384차원을 6개로 나누면:

\\[ d\_{head}=\frac{384}{6}=64 \\]

각 Head는 별도의 Query·Key·Value Projection Weight를 가지고 있어.

따라서 동일한 1500개 위치를 사용하더라도 각 Head가 서로 다른 표현 공간에서 관계를 계산하는 거야.

예를 들어 개념적으로 생각해 보자.

| Head   | 학습할 수 있는 관계의 예          |
| ------ | --------------------------------- |
| Head 1 | 가까운 시간 위치의 관계           |
| Head 2 | 멀리 떨어진 시간 위치의 관계      |
| Head 3 | 반복되는 음향 패턴                |
| Head 4 | 특정 음향 특징과 다른 시점의 관계 |
| Head 5 | 음성의 시간적 문맥                |
| Head 6 | 또 다른 복합적 관계               |

주의할 점은 이것이 설명을 위한 가상의 역할이라는 거야. 실제 Whisper Tiny의 각 Head가 정확히 저 역할을 맡는다는 증거는 없어.

각 Head의 Projection Weight가 서로 다르기 때문에 학습 과정에서 서로 다른 표현을 학습할 수 있다는 것이 핵심이야.

따라서 Encoder Layer 하나에서는:

\\[ 6\times(1500\times1500) \\]

개의 Attention Weight가 계산되는 셈이야.

Multi-Head Attention의 구조

Input Sequence

\\[ (1500,384) \\]

Head 1

## 64

차원

1500×1500

Attention

Head 2

## 64

차원

1500×1500

Attention

Head 3

## 64

차원

1500×1500

Attention

Head 4

## 64

차원

1500×1500

Attention

Head 5

## 64

차원

1500×1500

Attention

Head 6

## 64

차원

1500×1500

Attention

Concat + Output Projection

\\[ 6\times64=384 \\]

6개의 Head가 각각 계산한 결과를 결합하면 다시 384차원이 돼.

이런 구조를 Multi-Head Attention이라고 해.

참고로 이 6개의 Head는 Encoder Self-Attention에서만 사용되는 것이 아니야. Whisper의 Decoder Self-Attention과 Cross-Attention에도 각각 동일한 Head 수가 적용돼.

# 15. 이제 가장 중요한 질문: 네가 정리한 Whisper의 전체 그림은 맞는가?

네가 마지막에 정리한 내용은 다음과 같았지.

> Whisper 입력 소리에 대해 Encoder에서 음성 특징을 뽑아냄 → Decoder에서 특정 음성 특징을 특정 언어, 단어와 매칭시키는 확률을 약 51,000개 임베딩 단어 사전 항목별로 계산한다? 이때 Encoder 출력인 1500개 위치에 대해서도 참조해서 추측한다?

전체적인 방향은 맞아. 다만 실제 계산은 두 단계로 나눠 이해해야 해.

첫 번째는 오디오 특징을 참고하는 단계이고, 두 번째는 다음 Token 후보를 평가하는 단계야.

## 15-1. Decoder는 먼저 두 종류의 문맥을 결합해

현재까지 입력한 텍스트가 다음과 같다고 가정하자.

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
I want to
```

Decoder는 이 텍스트 문맥을 Self-Attention으로 처리해.

동시에 Cross-Attention으로 Encoder의 1500개 오디오 위치를 참고해.

\\[ Q=TextFeature\times W_Q \\]

\\[ K,V=AudioFeature\times W\_{K,V} \\]

그리고:

\\[ Context= Softmax\left( \frac{QK^T}{\sqrt{d_k}} \right)V \\]

이렇게 현재 텍스트 문맥과 관련된 오디오 정보를 결합하는 거야.

여기서 '음성 특징과 단어를 1:1로 매칭한다'고 이해하면 안 돼.

특정 단어 하나가 특정 오디오 위치 하나와 대응되는 단순한 검색 구조는 아니야.

현재까지의 텍스트 문맥이 Query를 만들고, 1500개 오디오 위치의 Key와 Value가 참조 대상이 되는 거야.

## 15-2. 그다음 모든 Vocabulary 후보를 평가해

Cross-Attention과 FFN을 거친 Decoder의 마지막 Feature Vector는 384차원이야.

\\[ h_t\in\mathbb{R}^{384} \\]

이제 이 벡터를 Vocabulary의 모든 후보 Token에 대해 점수화해.

Whisper에서는 Token Embedding Matrix를 출력 Projection에도 공유해서 사용할 수 있어.

\\[ W\_{emb}\in\mathbb{R}^{51865\times384} \\]

따라서:

\\[ Logits=h_tW\_{emb}^T \\]

결과는:

\\[ Logits\in\mathbb{R}^{51865} \\]

가 돼.

즉, 다음 Token 후보 51,865개에 대해 각각 하나의 점수가 만들어지는 거야.

이 점수에 Softmax를 적용하면:

\\[ P(y_t=i)= \frac{e^{Logit_i}} {\sum\_{j=1}^{51865}e^{Logit_j}} \\]

가 되는 거지.

여기서 높은 확률을 가진 Token이 다음 Token 후보가 되는 거야.

참고로 51,865개는 51,865개의 일반 단어를 의미하지 않아.

- 단어의 일부를 구성하는 BPE Token
- 공백 및 문자 조각
- 언어 Token
- 작업 지시 Token
- Timestamp Token
- 종료 Token

등이 모두 포함돼 있어.

## 15-3. 실제 계산 흐름을 하나로 연결하자

## Whisper의 다음 Token 예측

현재 텍스트

`I want to`

이전 Token의 Embedding

Masked Self-Attention

이전까지의 텍스트 관계 학습

Cross-Attention

Audio Encoder Output

1500개 위치 × 384개 특징

현재 텍스트의 Query로 오디오 특징을 참고

Decoder Hidden State

384차원

Vocabulary Projection

384 → 51,865

다음 Token 후보 점수

| 후보      | 확률 예시 |
| --------- | --------- |
| `explore` | 0.72      |
| `listen`  | 0.12      |
| `see`     | 0.08      |
| 기타 후보 | 0.08      |

이 표는 계산 흐름을 설명하기 위한 가상의 확률이야.

선택된 Token: `explore`

이 예시의 확률은 설명을 위해 만든 것이고, 실제 노트북의 Token별 확률값은 앞서 설명한 `return_logits_vocab=True` 결과에서 확인할 수 있어.

이제 `explore`를 기존 텍스트 뒤에 붙여서 다시 Decoder를 실행해.

```
I want to
     │
     ▼
explore 선택
     │
     ▼
I want to explore
     │
     ▼
다음 Token 확률 계산
     │
     ▼
the 선택
     │
     ▼
I want to explore the
     │
     ▼
다음 Token 확률 계산
```

이 과정을 `<|endoftext|>`가 나올 때까지 반복하는 거야.

# 16. 마지막으로, 학습할 때와 실제 사용할 때의 Decoder 입력은 다르다

여기까지 이해했다면 한 가지 더 알아두면 좋아.

Whisper가 처음 학습되는 과정과 이미 학습된 Whisper를 사용하는 과정은 Decoder 입력을 구성하는 방식이 달라.

## 16-1. Training: 정답 Token을 제공한다

예를 들어 원본 음성이 다음 문장이라고 하자.

> I want to explore the universe.

학습할 때는 정답 문장을 Token ID로 변환하고, Decoder에 정답 Token을 한 칸 밀어서 입력하는 Teacher Forcing 방식을 사용해.

개념적으로는 다음과 같아.

| Decoder 입력     | 예측 목표 |
| ---------------- | --------- |
| SOT              | I         |
| SOT, I           | want      |
| SOT, I, want     | to        |
| SOT, I, want, to | explore   |
| ...              | ...       |

모델은 다음 Token을 예측하고 실제 정답 Token과 비교해.

\\[ Loss=-\sum_t\log P(y_t\mid y\_{\<t},Audio) \\]

Loss가 작아지는 방향으로 Encoder와 Decoder 전체의 Weight를 업데이트해.

이 과정에서 CNN의 Kernel Weight도 학습되는 거야.

## 16-2. Inference: 자신이 생성한 Token을 다시 입력한다

반면 실제 Song Lingo에서 Whisper를 사용할 때는 정답 문장을 모르잖아.

따라서 최초 Prompt만 제공해.

그 후에는 모델이 직접 생성한 Token을 다음 입력에 붙여.

```
초기 Prompt
    │
    ▼
다음 Token 예측
    │
    ▼
선택한 Token 추가
    │
    ▼
다음 Token 예측
    │
    ▼
반복
```

이때는 학습된 Weight를 업데이트하지 않아.

Training에서는 정답을 기준으로 Weight를 학습하고, Inference에서는 이미 학습된 Weight로 정답을 추론하는 것이야.

# 17. 지금까지의 질문을 하나의 개념 지도에 정리

네가 질문한 개념들을 다시 연결하면 다음과 같아.

| 개념             | 정확한 의미                              | Whisper에서의 위치    |
| ---------------- | ---------------------------------------- | --------------------- |
| Power Spectrum   | FFT 주파수 성분의 크기 제곱              | STFT 이후             |
| Frequency Bin    | FFT의 개별 주파수 위치                   | STFT                  |
| Log-Mel Frame    | 특정 시간 구간의 Mel 에너지 벡터         | CNN 이전              |
| Feature Channel  | 학습된 필터가 추출한 특징의 한 축        | CNN                   |
| Weight           | 학습되는 가중치                          | CNN, Transformer 전체 |
| Bias             | 각 출력 Channel에 더하는 학습 파라미터   | CNN, Linear           |
| Stride           | Kernel의 이동 간격                       | CNN                   |
| Projection       | Weight Matrix를 이용한 선형 변환         | Attention, FFN        |
| Feature Vector   | 특정 위치의 여러 특징값을 모은 벡터      | CNN, Transformer      |
| Token Axis       | Sequence에서 각 요소가 놓인 위치 축      | Transformer           |
| Embedding        | Token ID를 벡터로 변환                   | Decoder               |
| FFN              | 각 위치의 Feature를 비선형 변환          | Transformer           |
| Residual         | 기존 입력과 연산 결과를 더하는 연결      | Transformer           |
| LayerNorm        | Feature 값의 분포를 정규화               | Transformer           |
| Attention Matrix | Query와 Key 사이의 가중치 행렬           | Transformer           |
| Head             | 독립적인 Attention 연산 경로             | Multi-Head Attention  |
| CTranslate2      | 학습된 Transformer 모델의 추론 실행 엔진 | Runtime               |

## 내가 권장하는 이해도 점검

다음 5개 질문에 답할 수 있다면 Whisper의 전체 구조를 상당히 정확하게 이해한 거야.

1. CNN이 80개의 Mel Channel을 384개의 Feature Channel로 변환할 때, 384개의 값은 누가 어떤 목적으로 학습하는가?
2. Encoder의 (1, 1500, 384)와 Decoder의 (1, 4, 384)는 각각 어떤 데이터를 표현하는가?
3. Self-Attention의 1500×1500 행렬과 Cross-Attention의 L×1500 행렬은 무엇이 다른가?
4. FFN의 384 → 1536 → 384는 왜 필요한가?
5. Decoder의 384차원 Hidden State가 어떻게 51,865개 Token 후보의 점수로 변환되는가?

내가 특히 강조하고 싶은 것은 2번이야.

Encoder와 Decoder는 모두 384차원을 사용하지만, 그 안에 담긴 의미는 다르다는 사실을 이해하는 것이 Whisper를 이해하는 핵심이야.

그리고 네가 Demucs를 공부하면서 이해했던 Feature Extraction, Downsampling, Attention, Decoder Restoration의 원리가 Whisper에서도 이어지고 있다는 점도 발견했을 거야.

다만 두 모델이 Feature를 사용하는 최종 목적은 달라.

- Demucs: 오디오의 특징을 이용해 개별 소리를 복원
- Whisper: 오디오의 특징을 이용해 언어 Token을 예측

이 차이를 중심에 놓으면 앞으로 다른 음성·오디오 딥러닝 모델을 공부할 때도 구조를 훨씬 쉽게 비교할 수 있을 거야.

참고할 자료: [OpenAI Whisper 원본 모델 구현](https://github.com/openai/whisper/blob/main/whisper/model.py?utm_source=chatgpt.com) · [네 Whisper 구조 분석 노트북](https://github.com/greenkey20/song-lingo/blob/main/experiments/model%20anatomy/whisper_anatomy_claude_code.ipynb?utm_source=chatgpt.com).

---
그런데 근본적으로 384 숫자가 어디서 나온 건지 여전히 불분명해. 이거 모델러가 정한 하이퍼파라미터야?

그리고 I want to explore the universe 문장의 녹음 데이터가 whisper에 입력되었을 때, 가장 처음 I라는 단어를 생성?해내는 게 정확히 어떻게 되는 건지 여전히 이해가 안 돼.. 근본적으로 이게 소리 ➡️ 텍스트로 변환하는 건데.. => [2026-11-11 18:31:00]

이번 질문은 두 가지 모두 Whisper를 이해하는 데 결정적인 질문이야.

특히 두 번째 질문은 단순히 Transformer 구조를 이해하는 것을 넘어, \*\*컴퓨터가 연속적인 음향 신호를 어떻게 이산적인 언어 기호(Token)로 변환하는가?\*\*라는 음성 인식(Automatic Speech Recognition, ASR)의 본질에 관한 질문이야.

이번에는 추상적인 설명을 최소화하고, 실제 `I want to explore the universe.`라는 문장을 처음 인식하는 순간을 계산 과정으로 재구성해 볼게.

# 1. 384는 누가, 왜 정한 숫자인가?

네, 모델 설계자가 정한 하이퍼파라미터야.

정확히는 Whisper Tiny 아키텍처의 `n_audio_state`와 `n_text_state`라는 설정값이 384야.

이 값은 음성을 입력했더니 계산 결과로 384가 나온 것이 아니야.

모델을 설계할 때 내부의 특징 표현 차원을 384로 사용하기로 결정한 거야.

## 1-1. Whisper 모델별 설정을 비교해 보자

OpenAI의 Whisper 논문에 모델별 아키텍처 설정이 나와 있어.

| 모델   | Encoder 층 | Decoder 층 | Model Dimension | Attention Head | 파라미터 |
| ------ | ---------- | ---------- | --------------- | -------------- | -------- |
| Tiny   | 4          | 4          | 384             | 6              | 39M      |
| Base   | 6          | 6          | 512             | 8              | 74M      |
| Small  | 12         | 12         | 768             | 12             | 244M     |
| Medium | 24         | 24         | 1024            | 16             | 769M     |
| Large  | 32         | 32         | 1280            | 20             | 1,550M   |

[image](https://www.google.com/s2/favicons?domain=https://cdn.openai.com\&sz=32)

cdn.openai.com+1

이 표에서 발견할 수 있는 게 있어.

모델이 커질수록 내부 표현의 차원이 커지고, Layer 수도 증가해.

이것은 모델의 표현 능력과 계산 비용 사이의 균형을 고려한 설계 선택이야.

## 1-2. 384가 Whisper의 여러 부분에서 반복되는 이유

Whisper Tiny의 기본 설정을 다음과 같이 정의해 보자.

\\[ d\_{model}=384 \\]

그러면 이 값을 기반으로 다른 구성 요소들의 차원이 결정돼.

## Whisper Tiny의 Dimension 설계

Model Dimension

# 384

아키텍처 설계 시 정한 기본 내부 표현 차원

CNN Output Channel

# 384

Mel 80 → Feature 384

Transformer Hidden

# 384

각 위치의 벡터 차원

Token Embedding

# 384

Token 하나의 벡터 차원

FFN Hidden

# 1536

384 × 4

Attention Head Dimension

\\[ 384\div6=64 \\]

# 64

Head 하나가 담당하는 차원

여기서 384가 등장하는 이유는 모두 같은 기본 Dimension을 공유하도록 설계했기 때문이야.

### Attention Head와의 관계

Whisper Tiny는 Head가 6개야.

\\[ d\_{head}=\frac{d\_{model}}{n\_{head}} \\]

\\[ =\frac{384}{6}=64 \\]

따라서 전체 384차원 표현을 6개의 Head가 각각 64차원으로 나눠 처리해.

### FFN과의 관계

FFN의 중간 차원은 다음과 같이 결정돼.

\\[ d\_{FFN}=4d\_{model} \\]

\\[ =4\times384=1536 \\]

따라서 1536도 384를 기준으로 정해지는 거야.

다만 4배라는 비율 역시 보편적인 필수 규칙이 아니라 Whisper가 채택한 설계 선택이야.

## 1-3. 그렇다면 모델러는 왜 하필 384를 선택했을까?

여기서는 조금 구분해야 해.

- 384라는 값은 명시적인 아키텍처 하이퍼파라미터야.
- 그 값을 선택한 구체적인 실험·탐색 과정은 논문의 모델 구성표만으로는 알 수 없어.

일반적으로 이런 Dimension을 정할 때는 다음 요소를 고려해.

① 표현 능력

384차원보다 1024차원에서 더 많은 정보를 표현할 수 있는 여유가 있어.

그렇다고 무조건 차원이 클수록 좋은 것은 아니야.

② 계산 비용

Attention의 계산량은 Sequence Length에도 영향을 받지만, Dimension과 Head 수가 커지면 연산 및 메모리 비용도 증가해.

③ 모델 크기와 학습 자원

Layer 수와 Dimension을 동시에 늘리면 파라미터 수와 학습 비용이 커져.

결국 모델 설계자는 성능과 계산 비용을 고려해서 아키텍처를 선택하는 거야.

여기서 기억할 개념이 있어.

Hyperparameter는 모델의 뼈대를 정하고, Parameter는 그 뼈대 안에서 실제 학습되는 숫자야.

| 구분           | 예시                                 | 누가 결정하는가?       |
| -------------- | ------------------------------------ | ---------------------- |
| Hyperparameter | 384, Layer 4개, Head 6개             | 모델 설계자            |
| Parameter      | Conv Kernel Weight, Attention Weight | 학습 알고리즘이 최적화 |

즉, 384라는 구조는 사람이 설계하지만, 그 안에 들어가는 384개의 Feature 값이나 Weight 값은 학습을 통해 결정되는 거야.

# 2. 그런데 도대체 어떻게 소리가 'I'라는 글자가 되는가?

이제 진짜 핵심으로 들어가자.

나는 이 문제를 이해하려면 먼저 한 가지 사고방식의 전환이 필요하다고 생각해.

Whisper는 소리를 글자로 직접 치환하는 사전(Dictionary)이 아니야.

예를 들어 이런 규칙을 가지고 있는 것이 아니야.

```
어떤 소리 모양 → I
어떤 소리 모양 → want
어떤 소리 모양 → explore
```

대신 다음과 같은 방식이야.

> 오디오의 음향적 증거와 지금까지 생성된 텍스트 문맥을 종합해서, 다음에 나올 가능성이 가장 높은 Token을 계산한다.

이 능력은 대량의 음성·텍스트 학습 데이터를 통해 모델 전체에 학습돼 있어.

조금 더 구체적으로 들어가 보자.

## 장면 A. 학습할 때 Whisper는 무엇을 배웠을까?

먼저 네가 지금 사용하는 Tiny 모델은 이미 학습이 완료된 모델이야.

우리는 그 학습된 Weight를 가지고 새로운 음성을 인식하는 거지.

그렇다면 최초의 학습 과정에서는 어떤 일이 벌어졌을까?

예를 들어 학습 데이터에 다음과 같은 쌍이 있다고 하자.

학습 데이터 한 쌍

Audio

"I want to explore the universe."라는 발화가 녹음된 음성

Transcript

`I want to explore the universe.`

학습 과정에서 Whisper는 Audio를 입력받아 Text를 예측하고, 정답 Transcript와 비교해.

예를 들어 모델이 첫 번째 Token으로 `You`를 예측했다고 하자.

실제 정답은 `I`니까 잘못 예측한 거야.

이 차이를 Loss로 계산하고 Backpropagation을 통해 CNN과 Transformer의 Weight를 모두 업데이트해.

이러한 학습을 대량의 음성·텍스트 쌍에 대해 반복하는 거야.

Whisper 원 논문은 대규모 Weakly Supervised 음성 인식 학습을 설명하고 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://cdn.openai.com\&sz=32)

cdn.openai.com



### 학습의 핵심 수식

Whisper가 최적화하는 목적을 단순화하면 다음과 같아.

\\[ \mathcal{L} = -\sum\_{t=1}^{T} \log P(y_t\mid y\_{\<t},x) \\]

여기서:

- \\(x\\): 입력 오디오
- \\(y_t\\): 정답 Token
- \\(y\_{\<t}\\): 이전 정답 Token들
- \\(P\\): 모델이 계산한 Token 확률

모델은 정답 Token에 높은 확률을 부여하도록 학습돼.

중요한 점은 이 과정에서 CNN이 특정 발음만 외우거나 Transformer가 특정 단어만 외우는 게 아니라는 거야.

전체 신경망의 Weight가 함께 조정되면서 음향 정보와 언어 문맥 사이의 관계를 학습하는 거지.

## 장면 B. 실제 추론 시작 — 'I want to explore...'라는 소리가 들어왔다

이제 학습이 끝난 모델에 새로운 오디오를 넣는 상황으로 돌아오자.

입력은 네 노트북에서 사용한 실제 TTS 예시야.

실제 노트북 데이터

입력 문장 (사람이 알고 있는 정답)

"I want to explore the universe."

| 항목        | 값        |
| ----------- | --------- |
| 오디오 길이 | 2.65초    |
| 샘플레이트  | 16kHz     |
| 샘플 수     | 42,400    |
| Log-Mel     | 80 × 3000 |

모델은 정답 문장을 모르는 상태로 입력받아.

### Step 1. CNN과 Encoder가 소리의 표현을 만든다

앞에서 공부한 과정을 거쳐:

\\[ Audio\rightarrow LogMel \\]

\\[ (1,80,3000) \\]

그다음:

\\[ CNN\rightarrow(1,384,1500) \\]

Transpose 및 Position Encoding을 추가한 후 Transformer Encoder를 통과해.

\\[ E\in\mathbb{R}^{1\times1500\times384} \\]

이것이 Encoder의 최종 출력이야.

그런데 이 1500×384의 숫자가 무엇을 의미할까?

각 위치는 약 20ms 간격으로 배치된 오디오의 문맥적 Feature를 담고 있어.

예를 들어 설명을 위해 다음과 같은 벡터들이 만들어졌다고 가정해 보자.

| Audio Position | 대응 시간 중심(개념적) | Feature Vector           |
| -------------- | ---------------------- | ------------------------ |
| 0              | 0ms                    | [0.12, -0.31, 0.85, ...] |
| 1              | 20ms                   | [0.18, -0.25, 0.74, ...] |
| 2              | 40ms                   | [-0.07, 0.52, 0.31, ...] |
| 3              | 60ms                   | [0.30, 0.11, -0.16, ...] |
| ...            | ...                    | ...                      |
| 1499           | 약 29.98초             | [0.02, -0.13, 0.44, ...] |

실제 Feature 값은 공개된 노트북에서 추출하지 않았으므로 위 숫자는 가상의 예시야.

여기서 중요한 것은 Encoder가 다음을 출력했다는 사실이야.

Encoder의 최종 결과

\\[ 1500\text{ positions}\times384\text{ features} \\]

즉, 소리를 1500개의 숫자 벡터로 표현하는 데 성공한 거야.

하지만 아직 `I`라는 단어는 나오지 않았어.

Encoder의 임무는 소리에서 문맥적인 음향 표현을 만드는 것이지, 최종 텍스트를 생성하는 것이 아니기 때문이야.

## 장면 C. Decoder에게 첫 번째 작성 지시를 내린다

이제 Decoder가 등장해.

Whisper는 Decoder에 다음과 같은 특수 Token을 먼저 입력해.

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
```

이것은 모델에게 다음과 같은 작업을 지시하는 거야.

- 새로운 Transcript를 시작해.
- 영어를 사용해.
- 음성 인식을 수행해.
- Timestamp는 출력하지 마.

노트북에서 이 Prompt는 다음 ID로 구성돼.

```
[50258, 50259, 50359, 50363]
```

총 4개의 Token이야.

따라서 Decoder의 최초 텍스트 입력은:

\\[ (1,4) \\]

이야.

이 ID들을 Embedding Matrix에서 조회하면:

\\[ (1,4)\rightarrow(1,4,384) \\]

가 돼.

즉, Decoder는 이제 네 개의 384차원 텍스트 벡터를 입력받았어.

동시에 Decoder에는 앞에서 만든 오디오 Encoder의 출력도 전달돼.

\\[ E=(1,1500,384) \\]

이것이 앞에서 설명했던 두 가지 입력이야.

- 텍스트 문맥: (1, 4, 384)
- 오디오 문맥: (1, 1500, 384)

이 두 가지가 Decoder 안에서 결합돼.

## 장면 D. Cross-Attention — Decoder가 소리를 참고한다

이제 첫 번째 텍스트 Token을 생성하기 위한 계산이 이루어져.

현재 Decoder는 네 개의 특수 Token을 알고 있어.

그리고 오디오 Encoder의 1500개 위치도 참고할 수 있어.

Decoder는 현재 텍스트 표현을 이용해서 Query를 만들고, Encoder의 오디오 표현을 이용해서 Key와 Value를 만들어.

\\[ Q=X\_{text}W_Q \\]

\\[ K=EW_K \\]

\\[ V=EW_V \\]

이제 Cross-Attention을 계산하지.

\\[ A=Softmax\left( \frac{QK^T}{\sqrt{64}} \right) \\]

최초 Prompt의 길이가 4이므로, Head 하나에서 계산하는 Attention Score의 크기는:

\\[ (4,64)\times(64,1500) \\]

\\[ =\boxed{(4,1500)} \\]

이야.

이 말은 네 개의 텍스트 Prompt 위치 각각이 1500개의 오디오 위치를 참고할 수 있다는 의미야.

그 결과 오디오 정보를 반영한 새로운 텍스트 표현이 만들어져.

중요한 건 Decoder가 단순히 오디오의 첫 번째 위치만 보고 `I`를 선택하는 게 아니라는 점이야.

오디오 전체를 표현하는 1500개 위치의 정보와 현재 텍스트 문맥을 함께 활용해서 다음 Token을 예측하는 거야.

참고로 현재는 첫 번째 생성 Token을 구하는 단계이므로, 아직 출력된 일반 텍스트는 하나도 없어.

# 3. 드디어 첫 번째 'I'는 어떻게 만들어지는가?

이제 마지막 계산이야.

Cross-Attention과 FFN 등 Decoder의 계산을 거치면 다음 Token을 예측할 수 있는 Hidden State가 만들어져.

현재 마지막 위치의 Hidden State를 \\(h\\)라고 하자.

\\[ h\in\mathbb{R}^{384} \\]

이 벡터가 현재 입력된 오디오와 텍스트 Prompt를 반영한 표현이야.

그런데 이것은 아직 글자가 아니야.

384개의 숫자로 이루어진 내부 표현일 뿐이야.

## 3-1. Vocabulary의 모든 Token과 점수를 비교한다

Whisper Tiny의 Token Vocabulary는 51,865개야.

각 Token에는 384차원 Embedding Vector가 있어.

다음과 같이 생각해 보자.

Vocabulary Embedding Matrix

\\[ W\_{emb}\in\mathbb{R}^{51865\times384} \\]

| Token   | Embedding의 개념적 표현  |
| ------- | ------------------------ |
| `ĠI`    | [0.12, 0.84, -0.31, ...] |
| `ĠYou`  | [-0.22, 0.35, 0.62, ...] |
| `ĠWe`   | [0.56, 0.21, -0.18, ...] |
| `ĠThe`  | [-0.12, 0.45, 0.73, ...] |
| `ĠWant` | [0.18, -0.37, 0.51, ...] |
| ...     | ...                      |

실제 Embedding 값이 아니라 원리를 설명하기 위해 만든 예시야.

여기서 중요한 사실이 있어.

OpenAI Whisper 구현에서는 Token Embedding Weight를 최종 출력 Projection에도 공유해.

실제 코드의 핵심 계산은 다음과 같아.

```
logits = x @ self.token_embedding.weight.T
```

따라서:

\\[ (1,1,384)\times(384,51865) \\]

\\[ =\boxed{(1,1,51865)} \\]

이 계산으로 51,865개의 Token 후보에 대한 점수가 생성돼.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



이것이 Logits야.

## 3-2. 점수는 어떻게 결정될까?

Token별 Logit은 다음과 같이 표현할 수 있어.

\\[ logit_i=h\cdot e_i \\]

여기서:

- \\(h\\): Decoder의 최종 Hidden State
- \\(e_i\\): i번째 Token의 Embedding Vector

즉, 384차원 Hidden State와 각 Token의 384차원 Embedding 사이의 내적을 계산하는 거야.

이 계산을 Vocabulary 전체에 수행하는 거지.

예를 들어 다음과 같은 가상의 결과가 나왔다고 해보자.

| 후보 Token | Logit | Softmax 확률 |
| ---------- | ----- | ------------ |
| `ĠI`       | 5.0   | 72%          |
| `ĠYou`     | 3.0   | 10%          |
| `ĠWe`      | 2.5   | 6%           |
| `ĠThe`     | 1.5   | 2%           |
| 기타       | ...   | 10%          |

이것은 원리를 설명하기 위한 가상의 숫자야. 실제 노트북에서 이 확률들이 나왔다는 뜻은 아니야.

Softmax를 적용한 다음 가장 높은 확률을 가진 Token을 선택해.

\\[ y_1=\arg\max_i P(Token_i\mid Audio,Prompt) \\]

이 예시에서는:

\\[ \boxed{y_1=\texttt{ĠI}} \\]

가 되는 거야.

## 첫 번째 Token 생성의 순간

Audio Encoder Output

1500 × 384

Text Prompt Embedding

4 × 384

Transformer Decoder

Self-Attention + Cross-Attention + FFN

Hidden State

384개 숫자

Vocabulary Projection

384 → 51,865

51,865개 후보 중 선택

`ĠI`

가장 높은 점수

# I

첫 번째 텍스트 Token 생성 완료

여기서 한 가지 더 중요해.

`ĠI`는 단어의 시작 부분에 공백이 붙는다는 것을 나타내는 Token 표기야. Whisper의 Tokenizer가 사용하는 byte-level BPE의 표현 방식이지.

즉, 실제 모델이 첫 번째로 선택하는 것은 사람이 생각하는 추상적인 '영어 단어 I'라기보다 해당 문자열을 나타내는 Token ID야.

# 4. 그런데 왜 하필 'I'인가? 소리와 의미를 어떻게 연결한 걸까?

여기서 네가 가장 근본적으로 궁금했던 부분에 도달했어.

Whisper가 51,865개 Token 중에서 `I`를 선택한 이유는 무엇일까?

이 질문에 답하려면 두 가지 정보가 함께 작용한다는 것을 이해해야 해.

## 4-1. 음향적 증거(Acoustic Evidence)

입력된 소리에는 실제로 발화된 음성의 특징이 존재해.

예를 들어 문장이:

> I want to explore the universe.

로 시작한다면 첫 부분에는 영어의 1인칭 대명사 `I`에 해당하는 발음이 존재하겠지.

Encoder는 이 소리를 여러 단계의 Convolution과 Self-Attention으로 처리해서 문맥적 오디오 특징으로 만들어.

학습을 통해 만들어진 Weight에는 다양한 음성 패턴과 텍스트 사이의 관계가 반영되어 있어.

따라서 Decoder는 오디오 Encoder의 표현에서 현재 발화에 관련된 정보를 얻을 수 있어.

## 4-2. 언어적 문맥(Language Context)

그런데 음성만으로 모든 것을 결정할 수 있는 것은 아니야.

같은 소리라도 발음이 불분명하거나 잡음이 섞이면 여러 단어로 해석될 수 있어.

이때 Decoder의 Self-Attention과 학습된 언어적 패턴이 함께 작용해.

예를 들어:

```
이전까지 생성한 Token:
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
```

이 상황에서 모델은 영어 음성 인식 작업을 수행하도록 설정돼 있어.

이제 오디오에서 얻은 특징과 언어적으로 학습된 확률을 함께 활용해서 다음 Token의 확률을 계산하는 거야.

수식으로 표현하면:

\\[ P(y_t\mid y\_{\<t},x) \\]

여기서:

- \\(x\\): 입력 오디오
- \\(y\_{\<t}\\): 이전까지 생성한 텍스트
- \\(y_t\\): 다음에 생성할 Token

이것이 음성 인식 모델의 핵심적인 조건부 확률이야.

단순히 소리와 단어를 1:1로 매칭하는 것이 아니라, 음향 정보와 언어적 문맥을 종합해 가장 적절한 다음 Token을 예측하는 거지.

따라서 발음이 정확하지 않아도 문맥을 이용해 그럴듯한 문장을 만들어 낼 수 있어.

이것이 네 노트북에서 실험했던 무음 환각이나 잡음에 따른 잘못된 문장 생성과도 연결되는 이유야.

# 5. 첫 번째 I가 생성된 다음에는 어떻게 될까?

이제 첫 번째 Token이 생성됐어.

처음에는:

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
```

였지.

첫 번째 Token을 추가하면:

```
<|startoftranscript|>
<|en|>
<|transcribe|>
<|notimestamps|>
ĠI
```

이제 Token은 5개가 됐어.

새로운 입력은:

\\[ (1,5) \\]

Embedding을 거치면:

\\[ (1,5,384) \\]

가 되지.

이제 다음 Token을 예측해야 해.

이번에는 Decoder의 Self-Attention이 현재까지 생성한 Prompt와 `I` 사이의 관계를 학습하고, Cross-Attention은 다시 Encoder의 오디오 특징을 참조해.

그 결과 다음 Token의 확률을 계산해.

이번에는 `Ġwant`가 가장 높은 점수를 얻었다고 하자.

그러면:

```
I want
```

가 만들어지는 거야.

이 과정을 반복하면:

## 실제 노트북의 Token 생성 결과

1. 초기 Prompt

   `<|startoftranscript|><|en|><|transcribe|><|notimestamps|>`
2. Token 1

   `ĠI`
3. Token 2

   `Ġwant`
4. Token 3

   `Ġto`
5. Token 4

   `Ġexplore`
6. Token 5

   `Ġthe`
7. Token 6

   `Ġuniverse`
8. Token 7

   `.`
9. Token 8

   `<|endoftext|>` — 생성 종료

최종 Transcript

# I want to explore the universe.

네 노트북에서 실제 실행된 결과

여기서 다시 강조하고 싶은 점이 있어.

Encoder는 한 번만 실행돼.

반복되는 것은 Decoder의 Token 생성 과정이야.

앞에서 생성한 Token들이 다음 단계의 입력에 추가되고, 매번 동일한 Encoder Output을 참고하는 거지.

# 6. 그러면 Whisper는 소리와 글자의 관계를 어떻게 학습했을까?

이제 전체 구조를 이해하기 위해 학습과 추론을 비교해 보자.

| 구분            | Training               | Inference             |
| --------------- | ---------------------- | --------------------- |
| 오디오          | 입력                   | 입력                  |
| 정답 Transcript | 제공됨                 | 제공되지 않음         |
| Encoder         | 실행                   | 실행                  |
| Decoder 입력    | 정답 Token의 이전 위치 | 현재까지 생성한 Token |
| Decoder 출력    | 다음 Token 예측        | 다음 Token 예측       |
| Loss 계산       | 정답과 비교            | 일반적으로 없음       |
| Weight 업데이트 | 수행                   | 수행하지 않음         |

Training에서는 다음과 같은 데이터를 반복적으로 제공해.

\\[ (Audio,Transcript) \\]

모델은 정답 Transcript를 예측하도록 학습돼.

그 결과 CNN과 Transformer 안에 수많은 Weight가 최적화되는 거야.

Inference에서는 정답을 모르니까, 입력 오디오만 가지고 학습된 Weight를 이용해 확률이 높은 Token을 순서대로 만들어 내는 거지.

이것이 Sequence-to-Sequence 기반 음성 인식의 원리야.

# 7. 마지막으로 네 질문을 정확한 답으로 정리할게

Q1. 384는 어디서 나온 것인가?

Whisper Tiny를 설계한 사람들이 선택한 Model Dimension이야. 입력 Mel Channel이 80개라고 해서 384가 수학적으로 유도되는 것은 아니야. 다른 모델 크기에서는 512, 768, 1024 등이 사용돼.

Q2. Encoder가 I라는 단어를 생성하는가?

아니야. Encoder는 오디오를 1500개의 384차원 Audio Feature Vector로 변환해. 텍스트 Token 생성은 Decoder가 담당해.

Q3. Decoder는 무엇을 참고해서 I를 생성하는가?

현재까지의 텍스트 Prompt와 Encoder의 Audio Feature를 함께 활용해. 특히 Cross-Attention으로 1500개 오디오 위치의 정보를 참고해.

Q4. 어떻게 I라는 단어를 선택하는가?

Decoder의 마지막 Hidden State 384차원 벡터를 Vocabulary의 51,865개 Token Embedding과 비교하는 출력 Projection을 수행해. 그 결과 51,865개 Logit이 생성되고 Softmax로 확률을 계산해. 그중 가장 높은 후보가 `ĠI`였던 거야.

Q5. 그럼 모델이 음소(Phoneme)를 하나씩 읽어서 단어로 조합하는 것인가?

Whisper의 기본 추론 구조는 명시적인 음소 인식 단계를 거쳐 단어를 조립하는 방식이 아니야. 오디오 특징에서 텍스트 Token 확률을 직접 예측하는 End-to-End 방식이야. 물론 내부 Feature에는 음소적·음향적 단서가 반영될 수 있지만, 각 Layer의 Feature를 명시적으로 음소라고 부르면 안 돼.

## 내가 권장하는 다음 실험

이제는 이론을 더 읽는 것보다 네 노트북에서 첫 번째 Token이 선택되는 순간의 실제 확률을 직접 출력해 보는 것이 가장 효과적일 것 같아.

이미 네 노트북의 7절-3에는 다음 코드가 있어.

```
logits = np.array(res.logits[0])# 첫 번째 생성 단계first_logits = logits[0]# Softmaxfirst_probs = softmax(first_logits)# 상위 10개 후보top = np.argsort(first_probs)[::-1][:10]for idx in top:    print(        hf.id_to_token(int(idx)),        first_probs[idx]    )
```

이 코드를 실행하면 내가 앞에서 가상의 숫자로 설명했던 부분을 실제 모델의 결과로 확인할 수 있어.

`ĠI`가 몇 퍼센트였는지, `ĠYou`나 다른 Token은 몇 퍼센트였는지 직접 볼 수 있는 거지.

내가 생각하는 이번 학습의 가장 중요한 결론은 이것이야.

Whisper는 소리를 입력받아 글자를 찾아내는 검색 엔진이 아니야.

소리를 384차원 공간의 수많은 특징 벡터로 표현하고, 그 특징을 학습된 언어적 표현과 결합한 다음, 다음에 올 Token의 확률분포를 계산하는 신경망이야.

결국 우리가 듣는 문장 하나는 음향적 증거를 수많은 수학적 변환으로 처리한 결과, 가장 가능성이 높다고 선택된 Token들의 순차적인 조합인 거야.

---
\\[\
P(y_t\mid y\_{\<t},x)\
\\] 이 수식 어떻게 읽는 것인지, 해석해줘..

한편 내 노트북 7절-3에 있다는 코드, 어떤 노트북을 말하는 거야? song-lingo/experiments/model anatomy/whisper_anatomy_claude_code.ipynb 파일의 아래 코드 말한 거야? => [현재 서울 날짜 및 시각 2026-11-11 20:19:00]

두 가지를 구분해서 설명할게.

1. 수식 \\(P(y_t \mid y\_{\<t}, x)\\)는 Whisper가 현재 시점의 토큰을 어떤 확률로 예측하는지 표현하는 수식이야.
2. 네가 붙여준 코드는 내가 말한 노트북의 7절-3 코드가 맞아. 정확히 `song-lingo/experiments/model anatomy/whisper_anatomy_claude_code.ipynb` 파일의 코드야.

## 1. 수식 \\(P(y_t \mid y\_{\<t}, x)\\) 읽는 법과 의미

먼저 수식을 기호별로 나눠보자.

\\[ P(y_t \mid y\_{\<t}, x) \\]

| 기호           | 읽는 법                 | 의미                                |
| -------------- | ----------------------- | ----------------------------------- |
| \\(P\\)        | Probability             | 확률                                |
| \\(y_t\\)      | 와이 티                 | 현재 시점 \\(t\\)의 토큰            |
| \\(\mid\\)     | Given, 조건으로 했을 때 | 주어진 조건하에서                   |
| \\(y\_{\<t}\\) | 와이 티 미만            | 현재 시점보다 앞서 생성된 모든 토큰 |
| \\(x\\)        | 엑스                    | 입력 오디오                         |

자연어로 읽으면 다음과 같아.

> 입력 오디오 \\(x\\)와 이전까지 생성된 토큰 \\(y\_{\<t}\\)가 주어졌을 때, 현재 토큰 \\(y_t\\)가 나올 확률.

조금 더 자연스럽게 표현하면,

"지금까지 들은 오디오와 지금까지 작성한 문장을 바탕으로, 다음 토큰이 무엇일 가능성이 얼마나 높은가?"

라는 의미야.

### 1-1. 실제 문장으로 생각해 보자

Whisper에 다음 오디오가 입력되었다고 가정하자.

입력 오디오 \\(x\\)

"I want to explore the universe."

현재까지 생성된 토큰

<|startoftranscript|>

<|en|>

<|transcribe|>

<|notimestamps|>

ĠI

Ġwant

Ġto

여기서는 다음 토큰을 예측하는 시점이라고 가정할게.

이때 모델이 예측해야 하는 \\(y_t\\)는 다음 토큰이야.

모델은 현재까지의 조건을 바탕으로 어휘 사전 51,865개에 대해 각각 점수를 계산하고, 이를 확률로 변환해.

예를 들어 설명을 위한 가상의 확률 분포가 다음과 같다고 해보자.

| 후보 토큰    | 예측 확률 |
| ------------ | --------- |
| `Ġexplore`   | 75%       |
| `Ġexploring` | 12%       |
| `Ġsee`       | 5%        |
| `Ġdiscover`  | 3%        |
| 기타 토큰    | 5%        |

이때,

\\[ P(y_t=\text{Ġexplore}\mid y\_{\<t},x)=0.75 \\]

라고 표현할 수 있어.

즉, 이전 토큰들과 오디오를 조건으로 했을 때 `Ġexplore`가 다음 토큰일 확률이 75%라는 뜻이지.

참고로 위 확률은 원리 설명을 위한 가상 수치야. 네 노트북에서 실제로 계산된 확률은 아니야.

### 1-2. 왜 \\(y\_{\<t}\\)와 \\(x\\)가 모두 필요한가?

여기가 중요한 부분이야.

Whisper는 다음 토큰을 예측할 때 두 종류의 정보를 활용해.

- \\(x\\): 오디오에서 추출한 정보. 실제로 어떤 소리가 입력되었는가?
- \\(y\_{\<t}\\): 이전에 생성한 텍스트 정보. 지금까지 어떤 문맥의 문장을 만들어 왔는가?

예를 들어 오디오가 비슷하게 들리더라도 이전 문맥에 따라 다음 토큰의 확률은 달라질 수 있어.

이것이 Transformer Decoder의 Cross-Attention과 Masked Self-Attention이 각각 필요한 이유 중 하나야.

- Masked Self-Attention: 이전 텍스트 토큰들을 참고해 문맥을 파악해.
- Cross-Attention: Encoder가 만든 오디오 표현을 참고해.

결국 다음 토큰은 오디오 정보와 언어 문맥을 함께 고려해서 결정돼.

## 2. 네가 붙여준 7절-3 코드가 맞아

맞아. 네가 붙여준 코드가 내가 언급했던 바로 그 코드야.

파일 경로는 다음과 같아.

`experiments/model anatomy/whisper_anatomy_claude_code.ipynb`

GitHub에서 확인할 수 있는 파일이야.

[whisper_anatomy_claude_code.ipynb 열기](https://github.com/greenkey20/song-lingo/blob/main/experiments/model%20anatomy/whisper_anatomy_claude_code.ipynb?utm_source=chatgpt.com)

그리고 이 코드에서 내가 앞서 언급한 다음 부분이 실제로 존재해.

```
logits = np.array(res.logits[0])
```

이 부분이 중요한 이유는 Whisper가 각 생성 단계에서 계산한 logits를 직접 가져오기 때문이야.

### 2-1. 코드 실행 흐름

코드를 실행하면 다음 순서로 동작해.

① Encoder 출력 enc

\\((1500,384)\\)

오디오의 잠재 표현

② Decoder 입력 prompt

`<|startoftranscript|> <|en|> ...`

텍스트 생성을 위한 시작 조건

③ generate() 실행

`return_logits_vocab=True`

각 단계의 어휘별 logits 반환

④ logits → softmax

\\(P(y_t\mid y\_{\<t},x)\\)

어휘별 점수를 확률로 변환

⑤ 상위 5개 후보 추출

`np.argsort(p)[::-1][:5]`

확률이 높은 토큰 5개 시각화

### 2-2. 네 코드에서 특히 중요한 세 부분

첫 번째: 모델의 토큰 생성

```
res = model.model.generate(    enc,    [prompt],    beam_size=1,    max_length=60,    return_scores=True,    return_logits_vocab=True,    return_no_speech_prob=True)[0]
```

여기서 `return_logits_vocab=True`가 핵심이야.

모델이 단순히 최종 생성 토큰만 반환하는 게 아니라, 각 생성 단계에서 어휘 사전 전체에 대해 계산한 logits도 반환하도록 요청하는 거야.

두 번째: logits를 확률로 변환

```
p = softmax(logits[t])
```

Softmax는 logits라는 점수들을 확률 분포로 변환해.

수식으로는 다음과 같아.

\\[ P_i=\frac{e^{z_i}}{\sum\_{j=1}^{V}e^{z_j}} \\]

- \\(z_i\\): i번째 토큰의 logit
- \\(V\\): 전체 어휘 개수, 여기서는 51,865
- \\(P_i\\): i번째 토큰의 예측 확률

세 번째: 상위 5개 후보 추출

```
top = np.argsort(p)[::-1][:5]
```

확률이 높은 순서대로 토큰 5개를 뽑는 코드야.

따라서 이 코드는 매 단계에서 모델이 어떤 토큰을 얼마나 유력하게 고려했는지를 보여주는 거지.

## 3. 한 가지 중요한 구분

여기서 혼동하지 않았으면 하는 개념이 있어.

| 개념            | 의미                                   |
| --------------- | -------------------------------------- |
| Logits          | 각 토큰에 대한 모델의 원시 점수        |
| Softmax         | Logits를 확률 분포로 변환하는 함수     |
| Probability     | 각 토큰이 다음 토큰일 모델의 예측 확률 |
| Generated token | 모델이 실제로 선택한 토큰              |

그리고 네 코드의 `beam_size=1`은 Greedy Decoding에 해당해. 매 단계에서 가장 높은 점수를 받은 토큰을 선택하는 방식이야.

단, `res.logits`는 각 생성 단계의 후보 분포를 보여주는 것이고, 모델이 실제로 어떤 후보를 선택했는지는 `ids`를 통해 확인할 수 있어.

이 둘을 비교해서 보여주는 것이 바로 네 코드의 초록색 막대야.

즉, 7절-3은 Whisper의 텍스트 생성 과정을 내부적으로 관찰할 수 있게 해주는 상당히 유용한 실험 코드야.

다음 단계로는 이 코드의 `logits.shape`를 출력하고, 실제로 첫 번째 생성 단계에서 51,865개 후보 중 어떤 토큰들이 가장 높은 확률을 얻었는지 확인하면 수식과 구현이 연결될 거야.

---
Encoder의 1500개 위치와 Decoder의 텍스트 Token 사이의 Cross-Attention을 실제 Heatmap으로 시각화해줘 => [현재 서울 날짜 및 시각 2026-11-11 20:19:00]

가능해. 다만 실제 Cross-Attention Heatmap을 만들려면 먼저 모델 내부의 Attention Weight를 추출해야 해. 현재 7절-3 코드만으로는 아직 그 값을 얻을 수 없어.

여기서 중요한 차이가 있어.

## 1. 지금 코드가 반환하는 값과 필요한 값

네 노트북의 다음 코드:

```
res = model.model.generate(    enc, [prompt],    beam_size=1,    max_length=60,    return_scores=True,    return_logits_vocab=True,    return_no_speech_prob=True)[0]
```

에서 `res.logits`는 어휘 사전 51,865개에 대한 예측 점수야.

우리가 Heatmap에 사용해야 하는 것은 이와 다른 데이터야.

Cross-Attention Weight

Decoder의 각 텍스트 위치가 Encoder의 1,500개 오디오 위치 중 어디에 얼마나 주의를 기울였는지를 나타내는 값이야.

Whisper Tiny의 한 Decoder Cross-Attention Layer를 예로 들면 다음과 같은 형태야.

\\[ A \in \mathbb{R}^{6 \times T \times 1500} \\]

- 6: Attention Heads
- \\(T\\): Decoder 텍스트 토큰 위치 수
- 1500: Encoder 오디오 위치 수

각 Head의 Attention Weight를 시각화하면 다음과 같은 Heatmap을 만들 수 있어.

## 2. 만들고자 하는 Heatmap의 형태

Cross-Attention Heatmap — 목표 형태

아래는 구조를 설명하기 위한 예시이며 실제 모델에서 추출한 값은 아니야.

[Whisper Architecture: Encoder-Decoder Speech Recognition - Interactive | Michael Brenndoerfer | Michael Brenndoerfer](https://images.openai.com/static-rsc-4/kRQOeiHlScpzCdltUI3SgsNkBEmc7rTbgSD03_u-hJGYtilaL2MP82PuzPOA4FDOe2uTQarM5nWGg_n1D0fC8MlZtB9SqXSTBInYma5GEn7ilOiH7fCXQzv2fWxmi7ToaG9T0GwY5S60GRRf4J6LoYR6g-2ub6P8OlVlDAlAzx0?purpose=inline)

[mbrenndoerfer.com](https://mbrenndoerfer.com/writing/whisper-architecture-encoder-decoder-multilingual-asr?utm_source=chatgpt.com)

가로축: Encoder 오디오 위치 0–1499

세로축: Decoder 텍스트 토큰

밝은 영역일수록 해당 텍스트 토큰이 해당 오디오 위치에 더 높은 Attention Weight를 부여했다는 뜻이야.

실제 데이터를 추출하면 다음과 같은 분석이 가능해져.

- `ĠI` 토큰은 오디오의 어느 구간에 주의를 기울였는가?
- `Ġwant`와 `Ġto`는 서로 다른 오디오 구간을 참고하는가?
- 각 Attention Head는 서로 다른 정렬 패턴을 학습했는가?
- 여러 Decoder Layer에서 오디오와 텍스트의 관계가 어떻게 달라지는가?

## 3. 실제 값을 얻으려면 무엇을 바꿔야 할까?

현재 노트북은 `faster-whisper`와 `CTranslate2`를 사용하고 있어. 이 경로의 `generate()` 반환값에는 일반적인 Cross-Attention Weight가 포함되어 있지 않아.

따라서 실제 Attention Weight를 얻으려면 OpenAI Whisper의 PyTorch 구현을 사용하거나, CTranslate2 내부 연산을 별도로 계측해야 해.

내가 권장하는 방법은 동일한 Whisper Tiny 모델의 PyTorch 구현에서 Decoder Cross-Attention의 Softmax 결과를 Hook으로 수집하는 것이야.

이렇게 하면 기존 노트북의 오디오와 전처리 결과를 활용하면서 실제 Attention Weight를 추출할 수 있어.

한 가지 확인할게.

현재 노트북에 PyTorch 기반 Attention 추출 코드를 추가해서, 실제 Whisper Tiny의 Cross-Attention Weight를 수집하고 Heatmap으로 그리는 방향으로 진행할까?

이 방식으로 진행하면 단순한 예시 그림이 아니라, 네 오디오 `I want to explore the universe`를 입력했을 때 모델이 실제로 계산한 Attention을 시각화할 수 있어.

---
응 => [현재 서울 날짜 및 시각 2026-11-11 20:19:00]

좋아. 기존 노트북의 7절-3 실험을 유지하면서, 실제 Whisper Tiny의 Cross-Attention Weight를 추출하고 시각화하는 코드를 추가하는 방향으로 진행할게.

구현은 다음 원칙으로 할 거야.

1. 기존 `s01.wav`와 동일한 오디오를 사용해.
2. OpenAI Whisper PyTorch 모델의 Encoder와 Decoder를 실행해.
3. Decoder의 각 Layer에서 Cross-Attention Weight를 수집해.
4. 텍스트 토큰과 Encoder의 1,500개 오디오 위치를 연결한 Heatmap을 그려.
5. 전체 Layer와 Head를 구분해서 볼 수 있도록 구성해.

중요한 점은 기존 `faster-whisper`의 `res.logits`를 Attention Weight로 오해하지 않는 거야. 두 값은 서로 다른 모델 내부 데이터야.

## 4. 노트북에 추가할 코드

현재 노트북은 PyTorch를 의도적으로 import하지 않고 있어. 과거에 Whisper와 Demucs를 같은 커널에서 불러왔을 때 OpenMP 충돌이 발생했기 때문이야.

따라서 이번 실험은 기존 노트북을 보존하고, 별도의 Jupyter 커널에서 실행하는 것을 권장해. 아래 코드는 기존 노트북의 `SAMPLE`, `ids`, `prompt`를 사용할 수 있도록 구성했어. 다만 별도 커널에서는 해당 변수들을 다시 준비해야 해.

### 4-1. 환경 준비

별도 가상환경에 다음 패키지를 설치해.

```
pip install openai-whisper torch matplotlib numpy
```

기존 프로젝트의 `data/tts_cache/s01.wav` 파일에 접근할 수 있는 환경이어야 해.

### 4-2. Attention Weight 추출

아래 코드를 새로운 노트북에 하나의 셀로 추가해.

```
import torchimport whisperimport whisper.modelimport numpy as npimport matplotlib.pyplot as pltfrom pathlib import Path# --------------------------------------------------# 1. 모델과 오디오 준비# --------------------------------------------------DEVICE = "cpu"# 기존 faster-whisper와 동일한 모델 크기whisper_model = whisper.load_model("tiny", device=DEVICE)tokenizer = whisper.tokenizer.get_tokenizer(    whisper_model.is_multilingual,    language="en",    task="transcribe")# 기존 노트북의 예시 오디오SAMPLE = Path("data/tts_cache/s01.wav")audio = whisper.load_audio(str(SAMPLE))audio = whisper.pad_or_trim(audio)mel = whisper.log_mel_spectrogram(audio).to(DEVICE)with torch.inference_mode():    audio_features = whisper_model.encoder(mel.unsqueeze(0))print("Encoder output:", audio_features.shape)# 예상: [1, 1500, 384]
```

## 5. 실행 후 반드시 확인할 것

예상 구조

Whisper Tiny라면 다음 형태가 나와야 해.

| 데이터               | 예상 형태                 |
| ----------------- | --------------------- |
| Encoder 출력        | `(1, 1500, 384)`      |
| Decoder Layer 수   | 4                     |
| Attention Head 수  | 6                     |
| 각 Layer Attention | `(6, 텍스트 위치 수, 1500)` |
| Layer 평균 Heatmap  | `(생성 토큰 수, 1500)`     |

여기서 한 가지 중요한 개념을 짚을게.

### Teacher Forcing 방식으로 Attention을 추출한다는 것

위 코드는 실제 생성 과정을 다시 한 토큰씩 실행하는 대신, 이미 생성된 토큰 시퀀스를 Decoder에 한꺼번에 넣어.

이것은 Teacher Forcing 방식의 재평가에 가까워.

예를 들어 생성 결과가 다음과 같다면,

`ĠI → Ġwant → Ġto → Ġexplore`

Decoder에는 다음 입력이 들어가.

`<|notimestamps|> → ĠI → Ġwant → Ġto`

각 위치의 출력이 다음 토큰을 예측하도록 대응시켜 Attention을 추출하는 거야.

따라서 이 Heatmap은 실제 생성 결과를 조건으로 계산한 Attention이지, 생성 과정에서 각 시점에 저장했던 Attention을 그대로 복원한 것은 아니야. Greedy 생성 결과와 동일한 토큰 시퀀스를 사용하므로, 정상적인 결정론적 추론에서는 각 위치의 계산을 비교할 수 있어.

또한 Attention Weight가 높다고 해서 그 오디오 구간이 해당 토큰의 음향적 원인이라고 단정할 수는 없어. Attention은 정보 참조 패턴이지, 인과관계를 직접 증명하는 지표는 아니야.

## 6. 내가 특히 보고 싶은 분석

Heatmap을 얻으면 단순히 색깔이 진한 곳을 보는 데서 끝내지 말고 다음 세 가지를 비교해 보자.

1. Layer별 차이: 초기 Layer와 마지막 Layer가 오디오 위치를 참조하는 방식은 같은가?
2. Head별 차이: 6개 Head가 모두 같은 위치를 보는가, 아니면 서로 다른 패턴을 보이는가?
3. 토큰별 차이: `I`, `want`, `explore`, `universe`가 각각 어떤 오디오 위치에 높은 Attention을 보이는가?

특히 마지막 질문이 네가 처음부터 궁금해했던 핵심과 연결돼.

"소리에서 어떻게 첫 번째 `I`라는 토큰을 생성하는가?"

이제 Encoder의 1,500개 위치와 Decoder의 `I` 토큰 사이에 실제로 어떤 참조 패턴이 나타나는지 관찰할 수 있게 되는 거야.

다음으로는 위 코드를 실행한 Heatmap 이미지를 이 대화에 첨부해 줘. 실제 결과를 기준으로 Layer와 Head별 패턴을 함께 해석하자.