프로젝트에 이제 db를 도입해야 할까? 11/12(목) 발표 때까지는 세션이나 메모리에 저장하는 걸로 구현 및 demonstration까지 할 수 있을까? => [현재 서울 날짜 및 시각 2026-11-05 13:54:00]

11월 12일 발표까지는 DB 없이 구현하고 데모까지 충분히 진행할 수 있어. 지금은 DB 설계보다 핵심 기능을 완성하고, 실제 사용자 흐름을 보여주는 데 시간을 쓰는 편이 낫겠어.

다만 단순히 모든 것을 메모리에 넣기보다는 데이터의 성격에 따라 저장 위치를 구분하자.

## 1. 현재 SongLingo에서 DB가 필요한가?

내 판단은 아직 필요하지 않아.

현재 프로젝트의 사용 흐름을 보면 다음과 같아.

1. 음악 파일 업로드 또는 마이크 녹음
2. 음원에서 가사 추출
3. 문장 단위 연습
4. 사용자 음성 녹음
5. STT 및 WER/CER 계산
6. 음향 특징 분석 및 캐릭터 시각화
7. History에서 이전 연습 결과 확인

이 중 1\~6번은 대부분 한 번의 사용자 세션 안에서 끝나는 작업이야.

예를 들어 사용자가 음악을 녹음하고, 가사를 추출하고, 문장 세 개를 연습한 다음, 캐릭터의 움직임을 재생해 보는 상황을 생각해 보자.

이 과정에서 데이터베이스가 제공하는 영속성이나 복잡한 검색 기능은 없어도 돼. 필요한 데이터만 세션 동안 유지하면 충분해.

## 2. 저장 위치는 데이터 성격에 따라 분리하자

내가 추천하는 구조는 다음과 같아.

| 데이터                   | 저장 위치                             | 유지 기간        |
| ------------------------ | ------------------------------------- | ---------------- |
| 현재 업로드한 음원       | 임시 파일 시스템                      | 세션 및 TTL      |
| 사용자가 녹음한 음성     | 임시 파일 시스템                      | 세션 및 TTL      |
| 인식된 가사              | `st.session_state`                    | 세션 종료까지    |
| 수정된 가사              | `st.session_state`                    | 세션 종료까지    |
| STT 결과                 | `st.session_state`                    | 세션 종료까지    |
| WER/CER 결과             | `st.session_state`                    | 세션 종료까지    |
| 음향 특징값(RMS, F0 등)  | `st.session_state`                    | 세션 종료까지    |
| 캐릭터 애니메이션 데이터 | `st.session_state`                    | 세션 종료까지    |
| 모델 및 연산 결과 캐시   | `st.cache_data` / `st.cache_resource` | 캐시 정책에 따름 |

특히 오디오 파일 자체와 분석 결과를 구분하는 것이 중요해.

예를 들어 5초짜리 녹음 파일이 있다면:

- 실제 녹음 WAV: 임시 파일로 관리
- 프레임별 음량 데이터: 세션 메모리에 저장
- 캐릭터 동작 시퀀스: 세션 메모리에 저장
- WER/CER 결과: 세션 메모리에 저장

이렇게 하면 History에서 녹음 파일을 다시 재생하고, 그때의 캐릭터 애니메이션도 재현할 수 있어.

권장 데이터 흐름

Audio Input

업로드 파일 또는 마이크 녹음

Temporary Files

오디오 원본

Processing

STT · Scoring · Audio Analysis

st.session_state

가사 · 점수 · 음향 특징 · 애니메이션 시퀀스

History

녹음 재생 · 캐릭터 움직임 재생 · 학습 이력

## 3. Streamlit의 session_state면 충분할까?

응. 현재 프로젝트 구조에서는 적절한 선택이야.

Streamlit의 `st.session_state`는 사용자 세션마다 독립적으로 유지되는 상태 저장소야.

공식 문서에서 설명하는 특징은 다음과 같아.

- 페이지가 다시 실행되어도 상태가 유지돼.
- 멀티페이지 앱에서도 페이지 간 상태를 공유할 수 있어.
- 브라우저 탭을 새로고침하거나 WebSocket 연결이 끊어지면 상태가 초기화돼.&#x20;

  [image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

  Streamlit Docs+1



이 말은 현재 SongLingo의 구조에 잘 맞는다는 뜻이야.

예를 들어 사용자가 My Song에서 연습을 마친 후 History 메뉴로 이동하면, 같은 세션의 데이터를 그대로 조회할 수 있어.

단, 발표 시에는 브라우저 새로고침을 하지 않는 것이 좋아. 세션 메모리만으로 구성했다면 새로고침 후 기존 이력이 사라질 수 있기 때문이야.

### 추천하는 session_state 구조

현재의 `practice_log.py`가 만드는 기록 구조를 참고해서, 새로운 연습 기록을 다음처럼 관리할 수 있어.

```
import streamlit as stfrom datetime import datetimefrom uuid import uuid4def save_practice_result(    source: str,    score: dict,    audio_path: str | None,    audio_features: dict | None,    animation: list | None,):    record = {        "id": str(uuid4()),        "created_at": datetime.now().isoformat(),        "source": source,        "score": score,        "audio_path": audio_path,        "audio_features": audio_features,        "animation": animation,    }    st.session_state.setdefault(        "practice_history", []    ).append(record)
```

여기서 핵심은 `practice_history`라는 하나의 목록에 연습 기록을 쌓는 거야.

History 페이지에서는 다음처럼 읽으면 돼.

```
records = st.session_state.get(    "practice_history", [])for record in records:    st.write(record["created_at"])    st.write(record["score"])
```

이것은 구조를 설명하기 위한 간단한 예시야. 실제 적용에서는 현재 `practice_log.py`의 `make_record()`를 재사용하고, 오디오 파일의 수명 관리와 오류 처리도 추가하면 돼.

## 4. 현재 구현과 어떻게 연결할까?

현재 GitHub 코드를 기준으로 보면, 이미 활용할 만한 부분이 있어.

| 파일                   | 현재 역할                        | 이번 변경 방향                                     |
| ---------------------- | -------------------------------- | -------------------------------------------------- |
| `practice_log.py`      | CSV에 연습 결과 저장             | 기록 생성 로직 재사용, 저장소만 세션으로 전환 가능 |
| `app/ui_practice.py`   | 따라읽기·받아쓰기 및 채점        | 결과와 음향 분석 데이터를 세션에 추가              |
| `app/views/history.py` | CSV에서 기록 읽기                | 세션의 `practice_history` 조회                     |
| `visualisation.py`     | STFT, Log-Mel 계산 및 그림       | 프레임별 음향 특징 추출 확장                       |
| `web_song.py`          | 음원 작업 파일 및 세션 폴더 관리 | 기존 임시 파일 정책 유지                           |

특히 현재 `practice_log.py`에는 좋은 설계 원칙이 있어.

가사 원문과 인식 텍스트를 기록 파일에 저장하지 않고, 점수와 식별 키만 기록하는 것이야.

이번에 캐릭터 시각화 데이터를 추가하더라도 이 원칙을 유지하는 걸 추천해. 음향 특징값과 애니메이션 데이터만으로도 시각적 기록을 충분히 재현할 수 있어.

그리고 현재 `app/views/song.py`에서 음원을 임시 작업 공간에 저장하고 1시간 경과 후 정리하는 방식도 당장 바꿀 필요가 없어.

## 5. 주의할 점: Session State와 Cache는 다르다

둘을 혼동하지 않았으면 해.

| 구분      | `st.session_state`              | `st.cache_data`         |
| --------- | ------------------------------- | ----------------------- |
| 주목적    | 사용자별 상태 관리              | 계산 결과 재사용        |
| 데이터    | 사용자별 작업 상태              | 함수의 반환 결과        |
| 기본 범위 | 세션별                          | 전역                    |
| 주요 용도 | 연습 이력, 현재 가사, 선택 상태 | 파형 분석, 변환 결과 등 |

특히 `st.cache_data`는 기본적으로 여러 사용자가 공유할 수 있어. 세션별로만 사용하려면 별도의 session scope를 지정해야 해. 따라서 개인의 녹음 및 학습 이력을 저장하는 용도로 무심코 사용하면 안 돼.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs+1



현재 `app/views/song.py`의 `overview()`에 `@st.cache_data`가 붙어 있는데, 이것은 계산 비용이 큰 음원 개요 분석을 재사용하기 위한 것이지, 사용자의 작업 이력을 보관하기 위한 것은 아니야.

## 6. 11월 12일 발표까지의 개발 우선순위

추천 전략: DB 도입 보류

발표까지는 다음 범위로 제한하는 게 좋겠어.

| 일정        | 개발 목표                    | 완료 기준                                    |
| ----------- | ---------------------------- | -------------------------------------------- |
| 11/5\~11/6  | Session State 기반 기록 구조 | 채점 결과를 세션에 저장하고 History에서 조회 |
| 11/7\~11/8  | 음향 특징 추출               | 녹음 구간별 RMS 및 음향 데이터 생성          |
| 11/9\~11/10 | 캐릭터 시각화                | 음량과 무음에 따라 캐릭터 자세 변경          |
| 11/11       | 통합 테스트 및 발표 시나리오 | My Song → 연습 → 캐릭터 재생 → History 시연  |
| 11/12       | 발표                         | 실제 사용 흐름 Demonstration                 |

특히 발표에서는 실시간 애니메이션까지 무리하게 구현하지 않아도 돼.

사용자가 녹음한 뒤, 녹음 파일을 재생하면 미리 계산한 음향 특징값에 맞춰 캐릭터가 움직이는 재생 동기화 방식만으로도 충분히 기능을 보여줄 수 있어.

이 방식이 실험 결과를 재현하기에도 유리해.

## 7. DB는 언제 도입할까?

발표 이후 다음 요구사항이 실제로 생기면 도입하자.

| 요구사항                                   | DB 도입 필요성 |
| ------------------------------------------ | -------------- |
| 브라우저를 닫아도 학습 이력을 유지         | 높음           |
| 다른 기기에서 로그인해 기존 학습 기록 확인 | 높음           |
| 사용자별 데이터 분리 및 계정 관리          | 높음           |
| 사용자 간 학습 통계 및 랭킹                | 높음           |
| 동일 세션에서 연습하고 History 확인        | 낮음           |
| 캐릭터 애니메이션 재생                     | 낮음           |
| 기존 CSV 학습 결과 확인                    | 낮음           |

향후 DB를 도입한다면 SQLite로 단일 사용자 로컬 프로토타입을 먼저 만들거나, 여러 사용자를 지원하는 서비스로 확장할 때 PostgreSQL을 사용하는 방향을 검토하면 돼.

내가 추천하는 최종 방향은 다음과 같아.

11월 12일 발표 버전

- DB 도입하지 않음
- `st.session_state`로 사용자별 학습 상태와 History 관리
- 음원 및 사용자 녹음은 임시 파일로 관리
- 음향 특징과 캐릭터 애니메이션 데이터는 세션 메모리에 보관
- 기존 `practice_log.py`의 기록 생성 및 정규화 로직은 재사용

발표 이후

- 사용자 인증 및 장기 기록 보존 요구사항을 확정
- 기록 데이터 모델 설계
- PostgreSQL 등 영속 저장소 도입

이렇게 하면 지금까지 만든 모듈을 대부분 그대로 활용하면서 발표에 필요한 기능을 구현할 수 있어. DB를 도입하는 것 자체가 프로젝트의 완성도를 높이는 것은 아니야. 지금 시점에서는 오히려 구현 범위를 통제하는 게 더 중요해.

다음으로는 현재 CSV 기반 `practice_log.py`를 세션 저장 방식으로 전환하면서 기존 History 화면을 최대한 유지하는 설계를 구체화하는 게 가장 효과적이겠어.

---
한편, 이번주 초 강사님과 면담 시 streamlit으로 쉽게 ui 구현하고, GitHub에 올리면 배포 및 url 획득도 가능하다고 하셨는데, 이 배포 방법이 뭘까? Vercel 말씀하신 거였을까..? 아니면, 뭐지..? => [현재 서울 날짜 및 시각 2026-11-05 15:37:22]

두 질문 모두 핵심은 Claude Code에 맡길 일과 네가 직접 책임져야 할 일을 구분하는 것이야.

먼저 결론부터 정리할게.

1. 테스트: Claude Code가 테스트 코드를 작성하고 실행하게 해. 네가 테스트의 타당성을 검토하고 실제 프로그램을 직접 사용해 최종 검증해야 해.
2. 배포: 강사님이 말씀하신 건 Vercel보다는 Streamlit Community Cloud일 가능성이 매우 높아. 현재 SongLingo 저장소도 이 방식으로 배포하기 좋은 구조를 갖추고 있어.

## 2. 강사님이 말씀하신 배포는 Streamlit Community Cloud일 가능성이 높아

가장 유력한 후보

Streamlit Community Cloud는 GitHub 저장소를 연결해서 Streamlit 앱을 배포하고, 별도의 서버 설정 없이 URL을 받을 수 있는 서비스야.

공식 사이트: [Streamlit Community Cloud](https://share.streamlit.io/?utm_source=chatgpt.com)

[43  Deploying to Streamlit Community Cloud – HSMA - Web Apps with Streamlit](https://images.openai.com/static-rsc-4/Ic8LOiB-U59q1XcMPaFCJ1-PEF6u-LpvXJiG9Gs67hRSh-dOesH7mDmJ4Q7CVD5pZqj3r3cEh-RRmd4bhc3khVzWcP_-Hz5GRTaGdfn9ItpZgscJg0XbeGIynVHv5nK2j3Mb14In3YAbbgJo5DxfTlwmTL8AwEuYU0bj3bKJdZ4?purpose=inline)

[webapps.hsma.co.uk](https://webapps.hsma.co.uk/streamlit_community_cloud.html?utm_source=chatgpt.com)

이 방식이 강사님 말씀과 일치하는 이유가 있어.

- GitHub에 소스코드를 올려 둔다.
- Streamlit Cloud에서 GitHub 계정을 연결한다.
- 저장소와 실행할 Python 파일을 지정한다.
- Deploy를 누른다.
- `https://...streamlit.app` 형태의 URL을 받는다.

이후 GitHub에 코드를 push하면 배포된 앱도 자동으로 업데이트돼.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs+2



### Vercel과는 무엇이 다를까?

Vercel도 GitHub 저장소를 연결해 웹사이트를 배포하고 URL을 얻는 서비스야.

다만 두 서비스의 주된 배포 대상이 달라.

| 구분                       | Streamlit Community Cloud | Vercel                         |
| -------------------------- | ------------------------- | ------------------------------ |
| 주요 목적                  | Streamlit 앱 배포         | 웹 프런트엔드와 서버 기능 배포 |
| 대표 대상                  | Python + Streamlit        | Next.js, React 등              |
| GitHub 연동                | 지원                      | 지원                           |
| 배포 URL                   | `streamlit.app`           | `vercel.app`                   |
| 현재 SongLingo에 적합한가? | 매우 적합                 | 별도 구조 변경이 필요          |

참고로 2026년 10월 15일 Vercel은 Python을 정식 지원하는 런타임을 발표했어. 하지만 공식적으로 안내하는 자동 프레임워크 지원은 FastAPI, Flask, Django 등이야. Python을 지원한다는 것과 현재 Streamlit 앱을 그대로 가져와 클릭 한 번으로 배포할 수 있다는 것은 다른 문제야.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://vercel.com\&sz=32)

Vercel+1



따라서 지금 SongLingo를 배포한다면 Vercel보다는 Streamlit Community Cloud를 먼저 선택하는 게 합리적이야.

## 3. 실제 SongLingo 저장소를 살펴보니 배포 준비가 상당히 되어 있어

현재 GitHub 저장소의 관련 파일을 확인했어.

현재 배포에 필요한 파일

`app/streamlit_app.py`

존재

Streamlit 앱의 진입점(entrypoint)

[소스코드 확인](https://github.com/greenkey20/song-lingo/blob/main/app/streamlit_app.py?utm_source=chatgpt.com)

`app/requirements.txt`

존재

웹 앱 실행에 필요한 Python 패키지와 버전

[소스코드 확인](https://github.com/greenkey20/song-lingo/blob/main/app/requirements.txt?utm_source=chatgpt.com)

`.streamlit/config.toml`

존재

초록색 테마와 UI 설정

[소스코드 확인](https://github.com/greenkey20/song-lingo/blob/main/.streamlit/config.toml?utm_source=chatgpt.com)

`.env.example`

존재

OpenAI API 키 환경변수 예시

[소스코드 확인](https://github.com/greenkey20/song-lingo/blob/main/.env.example?utm_source=chatgpt.com)

특히 눈여겨볼 점은 `app/requirements.txt`야.

Streamlit Community Cloud는 Python 의존성 파일을 저장소 루트 또는 앱 진입 파일이 있는 디렉터리에서 찾을 수 있어. 따라서 현재처럼 `app/streamlit_app.py`와 `app/requirements.txt`를 같은 디렉터리에 둔 구조도 유효해.

또한 설정 파일 `.streamlit/config.toml`은 저장소 루트에 있어야 하는데, 현재 그렇게 구성되어 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs+2



즉, 현재 프로젝트의 기본적인 배포 파일 구조는 이미 준비되어 있어.

## 4. 실제 배포 과정

내가 추천하는 실행 순서는 다음과 같아.

1. Streamlit Community Cloud 접속

   [share.streamlit.io](https://share.streamlit.io/?utm_source=chatgpt.com)에서 GitHub 계정으로 로그인해.

2. GitHub 저장소 연결

   `greenkey20/song-lingo` 저장소에 접근할 수 있도록 권한을 연결해.

3. Create app

   다음 정보를 입력해.

   | 항목           | 값                      |
   | -------------- | ----------------------- |
   | Repository     | `greenkey20/song-lingo` |
   | Branch         | `main`                  |
   | Main file path | `app/streamlit_app.py`  |

4. Advanced settings

   Python 버전과 API 키를 설정해.

   현재 프로젝트의 앱 전용 환경은 Python 3.11을 사용하므로 배포 환경도 3.11로 맞추는 것을 추천해. Community Cloud 기본값은 현재 Python 3.12이므로 직접 선택해야 해.&#x20;

   [image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

   Streamlit Docs

5. Deploy

   배포를 실행하면 빌드 로그가 표시되고, 완료되면 공유 가능한 URL이 생성돼.

### OpenAI API 키는 어떻게 설정할까?

이 부분은 반드시 주의해야 해.

현재 `app/streamlit_app.py`는 `.env` 파일을 읽고 있고, `tts.py`는 OpenAI 클라이언트를 생성할 때 `OPENAI_API_KEY` 환경변수를 읽어.

배포 서버에는 네 Mac의 `.env` 파일이 없으므로 Streamlit의 Secrets 기능에 키를 설정하면 돼.

Advanced settings의 Secrets 항목에 다음 TOML을 입력하면 돼.

```
OPENAI_API_KEY = "실제_OpenAI_API_키"
```

Streamlit은 최상위 수준의 secrets 항목을 환경변수로도 제공하므로 현재 `OpenAI()`를 생성하는 방식과 호환돼. `.env`나 실제 API 키를 GitHub에 올릴 필요는 없어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs+2



## 5. 다만 SongLingo는 배포 전에 확인할 기술적 위험이 있어

여기부터는 현재 저장소의 코드를 바탕으로 한 구체적인 점검 사항이야.

① Medium 모델의 메모리와 실행 시간

현재 노래 가사 인식에는 `song_practice.py`의 `SONG_MODEL = "medium"`이 사용되고 있어.

로컬에서는 네 컴퓨터의 CPU와 메모리 환경에서 동작하지만, Community Cloud는 앱별 자원 제한이 있어. 자원 제한을 초과하면 처리 속도가 느려지거나 앱이 동작하지 않을 수 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs+1



따라서 다음 순서로 검증하는 걸 추천해.

- 처음에는 10초 구간 하나만 처리하기
- 최초 medium 모델 다운로드와 로딩 시간 측정하기
- 실제 STT가 완료되는지 확인하기
- 메모리 부족이나 앱 재시작 발생 여부 확인하기

문제가 생기면 발표용 배포 환경에서 `small` 모델을 쓰는 방법도 검토할 수 있지만, 기존 실험의 medium 모델과 결과가 달라질 수 있으니 설정과 성능 차이를 명시해야 해.

② 보컬 분리 기능

현재 `separate.py`는 Demucs와 PyTorch를 사용하고, 앱 전용 패키지인 `app/requirements.txt`에는 이들이 포함되어 있지 않아.

로컬에서는 `SONGLINGO_SEPARATE_PYTHON` 환경변수로 별도의 개발 환경을 사용하도록 설계되어 있지.

하지만 배포 서버에서는 네 Mac의 Python 환경을 사용할 수 없어.

따라서 지금 구성 그대로라면 클라우드에서 '보컬만 만들기' 기능은 실패할 가능성이 높아. 발표용 배포 버전에서는 이 선택 기능을 비활성화하거나, 별도의 실행 환경을 마련해야 해.

③ 공개 URL과 API 비용

GitHub 공개 저장소에서 배포하면 앱도 기본적으로 공개 상태로 만들어져. 앱의 공개·비공개 설정은 조정할 수 있고, 비공개 앱에는 지정된 사용자를 초대할 수 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs+1



현재 SongLingo의 TTS는 OpenAI API를 호출하므로 공개 앱이라면 다른 사용자도 API 호출을 발생시킬 수 있어.

발표용으로는 다음 중 하나를 추천해.

- 비공개 앱으로 배포하고 강사님을 초대
- 공개 앱으로 배포하되 TTS 호출 등 과금 기능에 사용 제한 추가

④ 음원 파일의 서버 전송

로컬 실행과 달리 클라우드 배포에서는 사용자가 업로드한 음악과 녹음이 서버로 전송돼. Streamlit Community Cloud는 현재 미국의 인프라에서 앱을 호스팅한다고 안내하고 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs



따라서 실제 시연에 사용하는 음원은 서버 업로드가 허용되는 파일을 선택하고, 사용자 녹음과 임시 파일의 보관·삭제 동작도 확인해야 해.

마지막으로 Community Cloud 앱은 12시간 동안 접속이 없으면 잠들 수 있어. 발표 직전에 URL을 열어 깨워 두고 실제로 작동하는지 확인하는 것이 좋아.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs

그리고 현재 저장소의 `CLAUDE.md`를 다시 확인해 보니, 강사님 면담 이후 Streamlit + GitHub 배포 방식이 이미 결정된 것으로 기록되어 있어. 따라서 지금 이야기하는 Community Cloud가 당시 강사님이 권하신 방식일 가능성이 높아.

내 최종 제안은 이번 발표 전까지 Streamlit Community Cloud에 실제 배포하는 것을 목표로 삼는 것이야. 로컬에서 실행되는 프로그램을 보여주는 것과 다른 사람이 URL을 통해 접속할 수 있는 프로그램을 보여주는 것은 프로젝트의 완성도 측면에서 차이가 있어.

다만 medium 모델과 Demucs는 배포 환경에서 별도로 확인해야 해. 이 두 가지를 먼저 시험하면 불필요한 구조 변경 없이 배포 가능성을 판단할 수 있어.

---
[medium 모델과 Demucs는 배포 환경에서 별도로 확인] 이거 오늘(11/5 목) 퇴근하고 19시~22시50분 부트캠프 작업 시간에 먼저 해도 괜찮을까, 지금 GitHub 소스코드 상태로? => [현재 서울 날짜 및 시각 2026-11-05 15:37:22]

응. 오늘 19:00~22:50에 배포 환경 테스트를 시작하는 건 좋은 선택이야. 현재 GitHub의 main 브랜치 소스코드로도 충분히 시작할 수 있어.

다만 현재 코드 그대로 가능한 테스트와, 코드 변경이 필요한 테스트를 구분해야 해.
1. 현재 코드로 어디까지 테스트할 수 있을까?
방금 확인한 GitHub 소스코드 기준이야.
테스트 대상	현재 코드로 가능?	판단
Streamlit 앱 배포 및 실행	가능	배포 파일 구조 준비됨
faster-whisper medium 모델 로딩	가능	현재 코드에서 이미 medium 지정
음악 구간 가사 인식	가능	실제 클라우드 자원에 따라 성공 여부 달라짐
Demucs 보컬 분리	불가능	배포용 의존성 누락
medium과 Demucs 연속 실행	추가 검증 필요	메모리 부족 위험

① Medium 모델: 지금 바로 시험 가능
현재 코드는 다음과 같이 연결되어 있어.
- song_practice.py: SONG_MODEL = "medium"
- stt.py: WhisperModel()에 device="cpu", compute_type="int8" 설정
- web_song.py: 업로드된 음원의 선택 구간을 song_practice.prepare_lines()에 전달
- app/views/song.py: 사용자가 선택한 구간에 대해 가사 인식 실행
즉, 로컬에서 사용하던 노래 인식 설정을 바꾸지 않고 배포 환경에서 실행해 볼 수 있어.

다만 중요한 위험이 있어.

Streamlit Community Cloud가 공개한 자원 한도 안내에는 앱별 메모리가 약 690MB~2.7GB, CPU가 최대 2코어로 기재되어 있어. 이 수치는 2024년 2월 기준의 근사치이며 변경될 수 있다고 명시되어 있어. 

Streamlit Docs+1

Medium 모델은 상대적으로 무거워. 따라서 클라우드에서 반드시 실행된다고 장담할 수는 없어.

오늘은 10초짜리 음악 구간 하나로 먼저 검증하자. 첫 모델 다운로드 및 로딩 시간과 실제 인식 시간을 따로 기록해 두면 좋아.
② Demucs: 현재 코드를 그대로 사용하면 실행되지 않아
여기는 소스코드를 확인해 보니 문제가 명확해.

현재 app/requirements.txt에는 다음 패키지가 있어.
- streamlit
- numpy
- scipy
- matplotlib
- faster-whisper
- av
- openai
- python-dotenv 등
그런데 다음 패키지는 없어.
- torch
- torchaudio
- demucs
현재 separate.py는 Demucs와 PyTorch를 필요한 순간에만 불러오도록 되어 있어서 앱 자체는 실행될 수 있어. 하지만 실제로 '보컬만 만들기'를 누르면 의존성 오류가 발생할 가능성이 높아.

또한 SONGLINGO_SEPARATE_PYTHON이 설정되지 않으면 현재 실행 중인 Python을 사용하도록 되어 있어. 클라우드에서는 네 Mac의 별도 Python 환경을 사용할 수 없으므로, Demucs를 실행하려면 클라우드 환경 자체에 관련 패키지를 설치해야 해.

공식 Demucs 저장소도 PyTorch와 torchaudio 등의 의존성을 명시하고 있어. 

GitHub+1

공식 자료: Demucs GitHub

따라서 오늘 현재 코드로 Demucs를 실제 실행하는 것은 불가능하고, 실행 환경을 별도로 구성해야 해.
2. 내가 더 우려하는 부분: Medium과 Demucs의 메모리 중첩
사실 이 부분이 중요해.

현재 stt.py에는 모델을 메모리에 보관하는 _models 딕셔너리가 있어.

한 번 medium 모델을 로딩하면 프로세스가 살아 있는 동안 모델이 메모리에 남아 있어.

그리고 separate.py는 Demucs를 별도 프로세스(subprocess)로 실행해.

이 구조는 PyTorch와 faster-whisper의 프로세스 내 충돌을 피하기 위한 설계지만, 별도 프로세스라고 해서 서버의 메모리를 별도로 배정받는 것은 아니야.
현재 클라우드에서 예상되는 프로세스 구조
Streamlit 메인 프로세스
Medium 모델 상주 가능
faster-whisper · CTranslate2 · 앱 상태


Demucs subprocess
별도 메모리 사용
PyTorch · Demucs 모델 · 분리 연산


클라우드 인스턴스의 메모리 자원 공유


그러므로 medium을 로딩한 뒤 Demucs를 실행하면 두 프로세스의 메모리 사용량이 합산되어 자원 한도를 넘을 가능성이 있어.

이건 실제 실행 전에는 알 수 없는 부분이야. 클라우드 환경에서 순차 실행을 시험해야 해.

3. 오늘 저녁 작업 계획
3시간 50분을 전부 배포 오류와 의존성 설치에 소비하지 않도록 순서를 정하자.
11월 5일 부트캠프 작업
19:00–22:50 · 총 3시간 50분
1. 19:00–19:25 | 배포 준비
   - GitHub에 실험용 브랜치 cloud-deployment-test 생성
   - 현재 main의 코드와 설정 확인
   - Streamlit Community Cloud 연결
   - Python 3.11 선택
   - 진입 파일 app/streamlit_app.py 지정
   기존 app/requirements.txt는 진입 파일과 같은 디렉터리에 있으므로 Community Cloud가 의존성 파일로 인식할 수 있어. .streamlit/config.toml도 현재처럼 저장소 루트에 두면 돼. 
   
   Streamlit Docs+1
2. 19:25–20:00 | 최초 배포 및 기본 동작 확인
   - 패키지 설치 및 빌드 로그 확인
   - 앱 화면이 정상적으로 표시되는지 확인
   - 가사 입력과 History 메뉴 확인
   - API 키가 필요한 기능은 Secrets 설정 확인
   TTS까지 테스트하려면 Community Cloud Secrets에 OPENAI_API_KEY를 설정해야 해.
3. 20:00–21:15 | Medium 모델 테스트
   오늘의 핵심 목표
   - 음악 파일 업로드
   - 10초 구간 선택
   - 가사 인식 실행
   - 모델 최초 로딩 및 다운로드 시간 확인
   - STT 완료 여부와 추론 시간 기록
   - 동일 구간을 다시 인식해 모델 캐시 효과 확인
   이 과정에서 자원 부족이나 앱 재시작이 발생하는지도 확인하자.
4. 21:15–21:40 | Demucs 배포 의존성 분석
   - 현재 app/requirements.txt에 누락된 패키지 확인
   - 로컬 개발 환경의 Demucs 및 PyTorch 버전 확인
   - CPU 전용 패키지 설치 가능성 확인
   - 별도 실험 브랜치에서만 수정할 범위 결정
   아직 설치하지 않아도 돼. 먼저 의존성 충돌과 크기를 확인하자.
5. 21:40–22:25 | Demucs 테스트 가능 여부 판단
   
   의존성 설치가 순조롭게 진행되고 자원 여유가 있으면 별도 브랜치에서 실제 실행을 시도해.
   
   그렇지 않으면 오늘은 실행 환경 구성까지 확인하고 마무리하는 것이 낫겠어. Medium과 Demucs를 동시에 검증하려고 무리하지 말자.
6. 22:25–22:50 | 결과 정리
   - 성공·실패한 기능
   - 클라우드 로그 및 오류 메시지
   - 모델 로딩·추론 시간
   - 메모리 관련 증상
   - 다음 실험에 필요한 변경 사항
   다음 작업일에 이어갈 수 있도록 기록하자.

4. Claude Code에는 시작 전에 이렇게 요청하자
오늘은 Claude Code가 소스코드를 임의로 변경해서 배포를 시도하지 않도록 하는 게 중요해.
오늘 Streamlit Community Cloud 배포 환경에서 faster-whisper medium 모델과 Demucs의 실행 가능성을 검증하려고 해.

현재 GitHub main 브랜치의 소스코드를 기준으로 사전 점검해 줘.

주의: 우선 소스코드를 수정하지 마.

다음 항목을 조사해 줘.
1. app/streamlit_app.py, app/requirements.txt, .streamlit/config.toml을 기준으로 Community Cloud 배포가 가능한 구조인지 확인해 줘.
2. song_practice.py → web_song.py → stt.py의 호출 경로에서 medium 모델이 실제로 사용되는지 확인해 줘.
3. medium 모델의 다운로드 위치, CPU/int8 설정, 모델 캐시 방식과 클라우드에서 발생 가능한 자원 문제를 정리해 줘.
4. separate.py와 web_song.py에서 Demucs 실행에 필요한 의존성과 subprocess 동작을 분석해 줘.
5. 현재 app/requirements.txt로 Demucs가 실행 가능한지 판단해 줘.
6. 로컬 개발 환경의 torch, torchaudio, demucs 버전을 확인하고, 배포 환경에 반영할 때 발생할 수 있는 의존성 충돌을 분석해 줘.
7. medium 모델과 Demucs를 순차 실행할 때 두 프로세스가 메모리를 함께 사용하는 구조인지 확인해 줘.
결과는 다음 순서로 보고해 줘.
- 현재 상태에서 바로 테스트할 수 있는 기능
- 현재 상태에서 실행할 수 없는 기능과 이유
- 클라우드 배포 시 가장 위험한 부분
- 별도 실험 브랜치에서 수정할 파일과 필요한 변경 사항
- 오늘 테스트할 추천 순서
추가 패키지 설치, requirements 수정, 모델 변경, 리팩터링 및 GitHub 커밋은 내 승인 없이 진행하지 마.




5. 오늘 테스트에서 남겨야 할 결과
단순히 "배포 성공"이라고 기록하는 것보다 이런 표를 채우는 게 좋아.
검증 항목	결과
Streamlit 앱 부팅	성공 / 실패
Python 버전	3.11 확인
faster-whisper 설치	성공 / 실패
Medium 모델 다운로드	성공 / 실패
Medium 모델 로딩	성공 / 실패
10초 음악 구간 STT	성공 / 실패
첫 실행 소요 시간	측정값
두 번째 실행 소요 시간	측정값
Demucs 의존성 설치	성공 / 실패 / 미시도
Demucs 실행	성공 / 실패 / 미시도
Medium + Demucs 순차 실행	확인 / 미확인


내 최종 판단
오늘 진행 추천
오늘은 현재 GitHub 코드로 실제 배포하고 medium 모델을 검증하는 데 가장 큰 비중을 두자. Demucs는 현재 의존성 설정으로는 실행할 수 없으므로, 별도 브랜치에서 설치 가능성을 시험하는 작업으로 분리하는 게 좋아.

그리고 이번 실험은 단순히 발표용 URL을 만드는 것 이상의 가치가 있어.

로컬에서 정상 작동하는 AI 모델이 클라우드 환경에서도 똑같이 작동하는지 확인하는 과정이니까. 모델의 크기, CPU 추론, 메모리 사용량, 외부 패키지 의존성, 프로세스 격리 같은 실제 배포 엔지니어링 문제를 경험하게 되는 거야.

오늘 밤의 가장 좋은 성과는 medium이 클라우드에서 실제로 동작하는지 확인하고, Demucs를 실행하려면 무엇을 바꿔야 하는지 근거를 확보하는 것이야.

---
그런데 4시간 작업했는데, 결국 streamlit cloud 배포 불가능하면 어떻게 해? 그럴 거면 그냥 바로 내 oracle cloud 서버에 배포하는 게 낫지 않나..? => [현재 서울 날짜 및 시각 2026-11-05 16:24:00]

내 판단은 이번에는 Oracle Cloud를 주 배포 환경으로 삼는 게 더 합리적이야. Streamlit Community Cloud를 먼저 시도하느라 4시간을 모두 쓰는 전략은 추천하지 않아.

다만 Oracle Cloud로 옮긴다고 배포가 자동으로 쉬워지는 건 아니야. 핵심은 현재 Oracle VM의 사양이 SongLingo의 추론 작업을 감당할 수 있는지야.

## 1. Streamlit Community Cloud를 고집할 이유가 크지 않은 이유

현재 SongLingo의 구성을 기준으로 보면 다음과 같아.

| 구성 요소        | 현재 구현               | 배포 시 고려 사항                             |
| ---------------- | ----------------------- | --------------------------------------------- |
| STT              | faster-whisper `medium` | 모델 다운로드, 메모리, CPU 추론 시간          |
| Vocal Separation | Demucs                  | PyTorch·torchaudio·Demucs 설치 및 실행 메모리 |
| 앱 서버          | Streamlit               | 세션과 업로드 파일 관리                       |
| 외부 API         | OpenAI API              | API Key 및 사용량 관리                        |

Streamlit Community Cloud는 리소스 제한이 있어. 공식 문서에 공개된 근사치로는 앱별 메모리가 약 690MB\~2.7GB, CPU가 0.078\~2코어야. 이 한도는 변경될 수 있다고 문서에서도 명시하고 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.streamlit.io\&sz=32)

Streamlit Docs+1



여기서 특히 신경 써야 할 부분은 medium Whisper와 Demucs를 함께 사용하는 경우야.

현재 소스코드 구조에서는 다음과 같은 상황이 발생할 수 있어.

1. Streamlit 프로세스가 medium Whisper 모델을 메모리에 올려.
2. 사용자가 보컬 분리를 요청해.
3. Demucs가 별도 Python subprocess로 실행돼.
4. 부모 프로세스의 Whisper 모델과 자식 프로세스의 Demucs 모델이 동시에 메모리를 사용해.

즉, subprocess를 사용한다고 메모리 사용량이 격리되는 것은 아니야. 같은 컨테이너의 리소스 한도를 공유하거든.

게다가 현재 [app/requirements.txt](https://github.com/greenkey20/song-lingo/blob/main/app/requirements.txt?utm_source=chatgpt.com)에는 `torch`, `torchaudio`, `demucs`가 들어 있지 않아. 따라서 현재 의존성 그대로는 Community Cloud에서 Demucs 기능까지 실행할 수 없어.

이건 단순히 설정을 잘못해서 생기는 문제가 아니라, 배포 환경의 리소스와 의존성 구조가 현재 애플리케이션의 기능 요구사항에 적합한가라는 문제야.

## 2. Oracle Cloud가 더 적합할 수 있는 이유

Oracle Cloud VM을 사용하면 서버의 리소스와 실행 환경을 직접 관리할 수 있어.

| 비교 항목      | Streamlit Community Cloud  | Oracle Cloud VM                             |
| -------------- | -------------------------- | ------------------------------------------- |
| 메모리·CPU     | 플랫폼의 리소스 한도 적용  | VM 사양에 따라 직접 관리                    |
| PyTorch·Demucs | 의존성 설치 및 리소스 제약 | 필요한 패키지와 시스템 라이브러리 설치 가능 |
| Python 환경    | 배포 환경 중심             | 가상환경을 직접 분리 가능                   |
| 실행 프로세스  | 플랫폼이 관리              | systemd 등으로 관리 가능                    |
| 로그·서버 설정 | 제한된 관리 기능           | 직접 관리 가능                              |
| 발표용 URL     | `streamlit.app`            | IP 또는 도메인 연결 가능                    |

Oracle Cloud의 Always Free A1 Flex 리소스는 월간 무료 할당량 기준 2 OCPU와 메모리 12GB에 해당해. 단, 실제로는 사용 중인 VM의 Shape와 설정을 확인해야 해.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.oracle.com\&sz=32)

docs.oracle.com+1



이 정도 메모리라면 Streamlit Community Cloud의 공개된 한도보다 여유가 있지만, CPU 추론 속도와 Demucs 실행 시간은 별도로 측정해야 해.

한 가지 주의할 점도 있어. Oracle VM이 Ampere A1이라면 ARM 기반이야. 현재 사용 중인 로컬 환경과 CPU 아키텍처가 다르므로 PyTorch와 CTranslate2의 설치 및 실행 가능 여부를 실제 VM에서 확인해야 해.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://pytorch.org\&sz=32)

PyTorch+1



## 3. 내가 권하는 배포 구조

현재 SongLingo의 코드 구조를 최대한 유지하면서 Oracle Cloud에 배포하는 방향이 좋아.

사용자 브라우저

Lyrics · My Song · History

Nginx

HTTPS · Reverse Proxy

Streamlit Application

app/streamlit_app.py

App Python venv

Streamlit · faster-whisper · OpenAI SDK

Demucs Python venv

PyTorch · torchaudio · Demucs

Oracle Cloud VM

CPU · RAM · Storage · Temporary Workspace · Model Files

이 구조를 제안하는 이유는 현재 코드가 이미 두 Python 환경을 분리하도록 설계되어 있기 때문이야.

`separate.py`의 `SONGLINGO_SEPARATE_PYTHON` 설정을 그대로 활용하면 돼.

- App venv: 기존 `app/requirements.txt` 설치
- Demucs venv: torch, torchaudio, demucs 설치
- Streamlit 프로세스: `SONGLINGO_SEPARATE_PYTHON`으로 Demucs 환경의 Python 경로 전달

즉, 로컬 환경에서 사용하던 설계 의도를 Oracle Cloud에서도 재현하는 거야. 애플리케이션 구조를 크게 변경할 필요가 없어.

단, Nginx와 HTTPS는 외부 발표자가 접속할 수 있게 공개할 때 필요한 설정이야. 일단은 VM 내부에서 Streamlit이 정상 실행되는 것부터 확인하면 돼.

## 4. 그렇다면 오늘 19:00\~22:50 작업 계획을 바꾸자

나는 오늘 작업의 우선순위를 바꾸는 것을 권해.

2026-11-05 · 3시간 50분

1. 19:00–19:20 | Oracle VM 사양 확인

   VM Shape, CPU 아키텍처, 메모리, 디스크, Python 버전을 확인해.
   ```
   uname -m
   nproc
   free -h
   df -h /
   python3 --version
   ```
   여기서 VM의 자원이 부족하다면 모델 크기나 기능 범위를 조정해야 해.
2. 19:20–20:10 | 앱 실행 환경 구성

   Python 3.11, App venv, 기존 `app/requirements.txt`, 환경변수를 준비해. OpenAI API Key는 GitHub에 올리지 말고 VM 내부 환경변수나 접근 권한을 제한한 환경 파일로 관리해.
3. 20:10–21:00 | Streamlit + medium Whisper 검증

   우선 앱을 띄우고 Lyrics, My Song, History 페이지를 확인해. 그다음 10초 내외 파일로 medium 모델 다운로드, 로딩, 추론을 각각 측정해.
4. 21:00–22:00 | Demucs 검증

   별도 가상환경에 필요한 패키지를 설치하고 짧은 오디오로 보컬 분리 기능을 테스트해. 모델 실행 시간과 최대 메모리 사용량도 기록해.
5. 22:00–22:50 | 통합 테스트와 배포 마무리

   medium 추론 후 Demucs를 실행하는 상황까지 확인해. 정상 동작하면 systemd 등록 등 서버 재시작 후에도 앱이 유지되는 설정을 진행해.

여기서 중요한 원칙이 있어. 19:20에 환경 구성이 시작되면 Streamlit Community Cloud 배포 시도는 오늘 작업에서 제외하자. 배포 대상이 두 개가 되면 검증해야 할 환경도 두 배가 돼.

## 5. 단, Oracle Cloud에서도 반드시 검증할 세 가지

단순히 앱이 실행되는 것만으로 성공이라고 판단하면 안 돼.

| 검증 항목      | 성공 조건                                                             |
| -------------- | --------------------------------------------------------------------- |
| Medium Whisper | 모델 로딩과 짧은 오디오 추론이 정상 완료                              |
| Demucs         | 별도 프로세스 실행과 보컬 분리 파일 생성 성공                         |
| 동시 리소스    | Whisper 사용 후 Demucs 실행 시 OOM 또는 프로세스 종료가 발생하지 않음 |

그리고 발표용으로는 다음도 확인해야 해.

- VM 재부팅 후에도 앱이 자동 실행되는가?
- 업로드한 음악 파일과 결과 파일은 어디에 저장되는가?
- 사용자 세션이 서로의 업로드 파일이나 결과에 접근하지 않는가?
- 공개 URL에 접근할 때 인증과 HTTPS가 적절하게 적용되는가?

특히 현재 `practice_log.csv`는 서버 파일로 저장되기 때문에, 여러 사용자가 동시에 이용한다면 기록이 공유될 수 있다는 점도 고려해야 해.

## 결론

내가 권하는 방향은 명확해.

Oracle Cloud를 SongLingo의 주 배포 환경으로 정하고, Streamlit Community Cloud는 필요할 때 별도로 검증하는 선택지로 남겨두자.

이번 프로젝트에서 중요한 건 Streamlit Cloud에 배포했다는 사실이 아니야. 실제로 사용자가 음악을 업로드하고, medium Whisper로 가사를 추출하고, Demucs로 보컬을 분리하고, 자신의 발화를 분석할 수 있는 서비스를 발표 시점에 안정적으로 제공하는 것이야.

마지막으로 한 가지 정보가 필요해. 현재 Oracle Cloud VM의 Shape과 메모리 용량이 어떻게 돼? OCI 콘솔의 Compute Instance 상세 정보나 위 명령어 결과를 보여주면, medium Whisper와 Demucs를 함께 실행할 수 있을지 더 구체적으로 판단할 수 있어.

---
도메인 미리 준비해둘까..? => [현재 서울 날짜 및 시각 2026-11-05 16:24:00]

응. 도메인은 지금 미리 확보해두는 게 좋아. 단, 도메인 구매와 서버 연결은 별개의 작업이야. 도메인만 먼저 등록하고, Oracle Cloud 배포가 정상적으로 확인된 다음 DNS를 연결하는 순서를 추천해.
1. SongLingo 도메인 후보
프로젝트 이름이 SongLingo이고, 음악을 활용한 외국어 학습 서비스라는 점을 고려하면 다음 세 가지가 적합해.
후보	인상	내 의견
songlingo.com	일반적인 서비스·제품 도메인	1순위  가장 범용적
songlingo.app	앱·소프트웨어 서비스	서비스 성격을 잘 드러냄
song-lingo.com	GitHub 저장소 이름과 일치	하이픈 때문에 조금 길어짐

실제 등록 가능 여부는 아직 확인하지 않았어. 이미 다른 사람이 등록한 도메인일 수도 있으니 구매 전 확인해야 해.

내 선택은 songlingo.com이야. 나중에 Streamlit이 아닌 다른 프레임워크로 전환하거나 별도 API 서버를 만들어도 도메인을 계속 사용할 수 있기 때문이야.

참고로 .app은 HTTPS가 필수인 도메인이야. Oracle Cloud에서 Nginx와 SSL 인증서를 구성할 계획이라면 문제가 되지는 않지만, 이 조건을 알고 선택하는 게 좋아. 

Google Registry+1

2. 구매 후에는 이렇게 연결하면 돼
songlingo.com
사용자가 접속할 주소

DNS A 레코드

Oracle Cloud Reserved Public IP

변경되지 않도록 예약한 공인 IP


Nginx Reverse Proxy

HTTPS · SSL 인증서 · 요청 전달

Streamlit

localhost:8501


실제 설정은 다음 순서야.
1. 도메인 구매
2. Oracle VM에 Reserved Public IP 할당
3. DNS에서 A 레코드 설정
   - 호스트 @ → Oracle VM 공인 IP
   - 호스트 www → 루트 도메인
4. Oracle VM에 Nginx 설치 및 Reverse Proxy 설정
5. Let's Encrypt로 HTTPS 인증서 발급
6. 브라우저에서 https://songlingo.com 접속 확인
여기서 Reserved Public IP를 권장하는 이유가 있어. Oracle Cloud의 임시 공인 IP는 리소스 변경이나 삭제 등에 따라 달라질 수 있지만, 예약된 공인 IP는 VM과 분리해 보존하고 다른 인스턴스에 재할당할 수 있어. 

docs.oracle.com+1

그리고 외부에는 80·443 포트만 열고 Streamlit의 8501 포트는 외부에 직접 노출하지 않는 구조를 권장해.
3. 오늘은 어디까지 할까?
작업	오늘 진행 여부
도메인 후보 결정	진행
도메인 등록	이름이 확정되면 진행
Oracle Reserved IP 확인	진행
DNS A 레코드 연결	서버 실행 확인 후
Nginx 및 HTTPS 설정	앱 배포 성공 후

한 가지 더. 도메인을 구매할 때는 첫해 할인 가격보다는 갱신 가격, 자동 갱신 설정, WHOIS 개인정보 보호, 이전 가능 여부를 확인해. 특히 1년 뒤 갱신 비용이 예상보다 높아지는 상품은 피하는 게 좋아.

내 제안은 songlingo.com을 우선 확인하고, 가능하면 그 도메인 하나만 등록하는 거야. 지금은 여러 도메인을 구매하거나 DNS를 미리 복잡하게 구성할 필요는 없어.

이제 SongLingo가 단순한 GitHub 프로젝트를 넘어 실제 접속 가능한 개인 서비스로 발전하는 단계라고 생각하면 돼. 🟢

---
내 프로그램을 pwa로 배포 시, 아이폰 youtube music app으로 음악 재생하면서 내 웹앱 녹음기 켜서 듣고 있는 노래를 녹음할 수 있어? => [현재 서울 날짜 및 시각 2026-11-06 10:32:00]

조건부로 가능해. 다만 iPhone의 YouTube Music 앱에서 재생되는 디지털 오디오를 PWA가 직접 가져오는 것은 불가능하고, iPhone 스피커로 출력되는 소리를 PWA의 마이크가 다시 수음하는 방식으로는 가능해.

이 두 가지는 기술적으로 완전히 다른 방식이야.

## 1. 가능한 방식과 불가능한 방식

[OPPO A77s | OPPO Nigeria](https://images.openai.com/static-rsc-4/6LeZ3tlefYiGt28OYOxVvkw81TByxs8CDC7oFzkysg_ze6qqPfZZ9l5dkX47Xsd1ASbDxjKyPDTb5QmOOXMWuZYqZZpYBzboQfWW1y4D1XpfZ8a0MLF41f5Ws9-vKRuvqo2sEPoxPE2v3U-Wd8kEs6Myl7_3ONsmM8OkaqGwWbA?purpose=inline)

조건부 가능

YouTube Music → iPhone 스피커 → 마이크 → SongLingo

스피커에서 나온 음악을 iPhone 마이크가 공기 중의 소리로 수음하는 방식이야. 현재 SongLingo의 주변 음악 녹음 기능과 같은 원리야.

직접 녹음 불가능

YouTube Music → Bluetooth 이어폰 → SongLingo 마이크

음악이 이어폰으로 직접 전달되기 때문에 휴대폰 마이크가 음악을 수음하지 못해. 이어폰에서 새어 나오는 소리가 있다면 일부 잡힐 수 있지만 정상적인 녹음 방식은 아니야.

[如何解决移动直播下的耳返延迟问题_电子设备](https://images.openai.com/static-rsc-4/HVuPA8tEqu69KtjJr04_Xphv5Ogh5yv9z9I1MfcuA34IINn_lE5pca-lXrT9tTgQIEeKqpNBdG89q5nJGlRzHgaisuQWWLnYDjM2Ll4ELUarmuZOwkQgcbQ3y0swNCEi9P-xtqkEiXsvrOFFn4sHaM4kmz5lLha8jk5Nq9xmEyA?purpose=inline)

PWA에서는 불가능

YouTube Music 앱의 디지털 오디오 스트림 → SongLingo

웹의 `getUserMedia()`는 마이크 같은 미디어 입력 장치에서 스트림을 얻는 API야. 다른 앱의 내부 오디오 출력 스트림을 직접 가져오는 API가 아니야.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



## 2. iPhone에서 실제로 작동할 수 있는 조건

여기서 한 가지 추가적인 제약이 있어.

iOS Safari와 PWA에서 마이크를 활성화하면 오디오 세션과 출력 경로가 변경될 수 있어. WebKit에서도 마이크를 활성화한 뒤 출력 음량이나 스피커·수신기 경로가 달라지는 사례가 보고돼 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://bugs.webkit.org\&sz=32)

bugs.webkit.org+1



따라서 다음 조건을 권장해.

| 조건          | 권장 설정                       |
| ------------- | ------------------------------- |
| 음악 출력     | iPhone 내장 스피커              |
| 이어폰        | 연결하지 않음                   |
| SongLingo     | 녹음하는 동안 화면 전면에 유지  |
| YouTube Music | 백그라운드 재생이 유지되는 상태 |
| 녹음          | PWA에서 마이크 권한 허용        |
| 서버          | HTTPS 적용                      |

특히 PWA를 백그라운드로 보내고 YouTube Music을 전면에 띄운 상태에서 계속 녹음하는 방식은 기대하지 않는 게 좋아. iOS에서는 웹앱이 백그라운드로 전환되거나 화면이 잠기면 마이크 캡처가 중단·음소거될 수 있어.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



## 3. 실제 iPhone에서 테스트하는 방법

현재 SongLingo의 주변 음악 녹음 기능으로 다음 순서대로 테스트하면 돼.

## iPhone PWA 실험 절차

1. YouTube Music 실행

   iPhone 스피커로 노래를 재생해.
2. SongLingo PWA로 돌아오기

   홈 화면에 설치한 SongLingo를 열어. YouTube Music이 백그라운드에서 계속 재생되는지 확인해.
3. 주변 음악 녹음 선택

   SongLingo의 `내 노래` 메뉴에서 주변 음악 녹음을 선택해.
4. 녹음 시작 및 음악 재생

   10\~15초 정도 녹음해. 녹음 중에도 SongLingo 화면이 전면에 있어야 해.
5. 녹음 결과 확인

   저장된 음성을 직접 재생해 보고, 음악이 얼마나 선명하게 들어갔는지 확인해.

테스트 시나리오

YouTube Music 백그라운드 재생 유지

PWA 마이크 권한 정상 획득

녹음 중 음악 재생 유지

녹음 결과에 음악이 실제로 포함됨

녹음된 음성을 Whisper가 인식할 수 있음

0/5개 확인

여기서 주의할 기술적 문제가 하나 더 있어.

브라우저 마이크 녹음에는 에코 제거(Echo Cancellation), 잡음 억제(Noise Suppression), 자동 게인 조절(Auto Gain Control) 같은 처리가 적용될 수 있어. 이 기능들이 스피커에서 재생되는 음악을 약화시키거나 변형시킬 가능성이 있어.

현재 SongLingo의 `st.audio_input()`은 브라우저가 제공하는 마이크 녹음 기능을 사용하므로, 이 입력 처리 설정을 세밀하게 제어하기 어려울 수 있어. 나중에 직접 JavaScript `getUserMedia()`와 `MediaRecorder`를 구현한다면 관련 설정을 실험해 볼 수 있지.

## 4. SongLingo 관점에서의 판단

사실 이 부분은 현재 프로젝트의 중요한 사용 시나리오야.

사용자가 YouTube Music에서 노래를 듣다가 마음에 드는 구간을 발견했을 때, 그 노래를 SongLingo에 가져와서 바로 학습하는 흐름이니까.

다만 iPhone에서는 스피커 출력 기반 수음이라는 한계가 있어.

내가 권하는 제품 설계는 다음과 같아.

- 파일 업로드: 음원 파일이 있는 경우
- 주변 음악 녹음: 다른 기기 또는 휴대폰 스피커로 재생하는 경우
- 직접 마이크 녹음: 사용자가 노래를 직접 따라 부르거나 문장을 읽는 경우

그리고 iPhone PWA에서는 주변 음악 녹음 화면에 다음과 같은 안내를 제공하는 게 좋아.

> 다른 앱에서 노래를 재생한 뒤, 이 앱으로 돌아와 녹음해 주세요. 음악이 iPhone 스피커에서 출력되어야 녹음할 수 있습니다. 이어폰 사용 시 음악은 녹음되지 않을 수 있습니다.

결론적으로 iPhone PWA에서도 YouTube Music을 재생하면서 SongLingo로 주변 음악을 녹음하는 사용 경험을 구현할 수는 있어. 다만 디지털 오디오를 직접 캡처하는 방식이 아니라 스피커를 통한 음향적 수음이며, iOS의 오디오 세션과 백그라운드 동작에 영향을 받으므로 실제 iPhone에서 검증해야 해.