<p align="center">
  <img src="app/assets/logo.svg" alt="song lingo" width="360">
</p>

# song-lingo

외국어 노래에서 떠올린 문장을 **듣고 → 따라 읽거나 받아쓰고 → 오류율(WER/CER)과 틀린 부분을 확인**하는 음성 학습 프로토타입입니다. ICT 혁신 스퀘어 Voice-AI 부트캠프 개인 프로젝트(2026-10-30 ~ 11-12, 발표 11-12)입니다.

> 점수는 발음 점수가 아니라 **문장 인식 일치도(WER/CER 기반 오류율)** 입니다. STT가 틀린 발음을 문맥으로 고쳐 적을 수 있기 때문입니다. 발음 자체는 별도로 Azure 발음 평가(참고용)를 보여 줍니다.
>
> **이 앱은 노래방이 아닙니다.** 사용자가 부른 노래를 채점하지 않습니다. 노래(원곡)는 가사를 얻고 듣기 위한 입력이고, 평가 대상은 따라 읽기·받아쓰기입니다.

*최종 갱신: 2026-11-09 (L1·L2 주요 기능 구현, **Oracle 서버 배포 완료**(#52), **사용자별 서버 저장**(로그인·로그인 유지, #63)과 저장 스키마 정리(#67~#75)까지). 진행 상황의 자세한 기록은 [`docs/작업_일지.md`](docs/작업_일지.md)와 GitHub 이슈를 봅니다.*

## 바로 써 보기

<table>
<tr>
<td><img src="app/assets/qr_songlingo.svg" alt="songlingo.kr QR 코드" width="150"></td>
<td>

**https://songlingo.kr**

휴대폰 카메라로 왼쪽 QR을 스캔하세요. 처음 들어가면 **로그인·가입·게스트** 탭이 보입니다. 가입과 게스트 입장에는 **초대 코드**가 필요합니다(발표 때 안내). 가입하면 연습 기록과 작업이 서버에 저장되어 브라우저를 닫아도 이어서 쓸 수 있고(**로그인 유지** 30일), 게스트는 아무것도 저장되지 않습니다. 아이폰은 Safari, 안드로이드는 Chrome을 권합니다. 마이크 허용 창이 뜨면 **허용**을 눌러 주세요(HTTPS 주소라서 녹음이 됩니다).

</td>
</tr>
</table>

서버는 Oracle Cloud VM이고 Cloudflare 터널로 연결합니다. 서버 구성과 운영 절차는 [`docs/프로젝트_안내_및_주제_검토.md`](docs/프로젝트_안내_및_주제_검토.md) 16.15·16.15.1, 도메인·터널 개념과 겪은 문제는 [`docs/개발환경_이슈노트.md`](docs/개발환경_이슈노트.md) #25~#31에 있습니다.

## 무엇을 할 수 있나

웹 앱(Streamlit) 메뉴 3개로 구성됩니다.

| 메뉴 | 하는 일 |
|---|---|
| **내 문장** (`/text`) | 문장을 붙여 넣고(또는 예시 불러오기) **줄마다 언어를 확인**한 뒤, 표준 발음(TTS)을 듣고 **따라 읽기 / 받아쓰기**로 연습합니다. 일본어는 히라가나 읽기·로마자를, 모든 줄은 한글 뜻과 "표현 설명"(단어·IPA 발음 기호·표현·문법·예문)을 볼 수 있습니다. 로그인하면 입력한 내용이 **묶음**(입력창 하나 = 묶음 하나, 최대 50개, 선택 제목)으로 저장되어 골라서 불러오고 삭제할 수 있습니다 |
| **내 노래** (`/clip`) | 내 곡 파일을 올리거나 **스피커로 튼 노래를 마이크로 녹음**해, 구간을 정하고 → 언어를 확인한 뒤 → 가사를 인식해 **연습할 줄**로 나눕니다. 줄을 고치고, 빼고, **다음 줄과 합칠** 수 있고, 줄마다 원본 음악 / 보컬만(Demucs) / 표준 발음을 들을 수 있습니다(원본·보컬은 **앞뒤 5초도 함께** 들을 수 있음). 로그인하면 구간·가사가 저장되어 같은 곡의 **여러 구간**을 따로 이어 쓸 수 있고, **저장된 곡** 방식으로는 곡 파일 없이도 가사·표준 발음으로 연습합니다 |
| **기록** (`/history`) | 채점 결과(점수, 로그인 사용자는 문장·인식문까지 서버에 저장)를 모아 문장별 오류율 변화를 봅니다 |

연습 결과에는 다음이 나옵니다.

- **오류율**: 영어·프랑스어는 WER(단어), 일본어·중국어는 CER(글자) 중심. S(치환)·D(삭제)·I(삽입) 개수와 틀린 단어 대조
- **틀린 구간 표시**와 **소리 모양 비교**(파형·FFT·STFT·Log-Mel, 수업 방식)
- **Azure 발음 평가(선택, 버튼을 눌렀을 때만)**: 정확도·유창성·완성도·운율, 단어·음소별 점수
- 화면 곳곳의 **"어떻게 동작하나요?"**(라임색 접는 상자)에 어떤 모듈·모델이 무슨 일을 하는지 적혀 있습니다

## 동작 흐름

```
문장/가사 ─ tts.py(OpenAI TTS, 캐시) ─▶ 표준 발음
내 녹음 ─ quality.py(상태 점검) ─ stt.py(faster-whisper) ─▶ 인식 문장 ─ scoring.py(WER/CER) ─▶ 결과
                                     └ align.py(틀린 구간의 시간)   └ azure_pronunciation.py(선택)
내 곡/주변 음악 녹음 ─ web_song.py ─ separate.py(Demucs, 선택) ─ stt.py(medium) ─ song_lines.py(줄 나누기) ─▶ 연습할 줄
언어 제안 ─ languages.py(글자·낱말 규칙, Whisper 언어 확률) / 일본어 읽기 ─ japanese.py(pykakasi) / 뜻·표현 ─ meaning.py(OpenAI, 버튼, DB·파일 캐시)
로그인 ─ app/auth_gate.py ─ account.py(auth.py 규칙) ─ storage.py ─ PostgreSQL ◀─ app/persist.py(자동 저장: 연습 기록·구간·줄·문장 묶음)
```

화면 코드(`app/`)는 위젯 배치만 하고 계산은 루트의 모듈이, 저장은 `app/persist.py` → `storage.py`가 합니다. 모듈별 호출 관계와 다이어그램은 [`docs/module_structures_and_data_flow.md`](docs/module_structures_and_data_flow.md), 읽는 순서는 [`docs/작업_일지.md`](docs/작업_일지.md) 2-3절에 있습니다.

## 사용한 것

| 역할 | 기술 |
|---|---|
| 음성 인식(STT) | **faster-whisper**: 말소리 연습은 `tiny`(CPU, int8, 수업 7강 설정), 노래 구간은 `medium`(원곡, VAD 끔) |
| 표준 발음(TTS) | OpenAI `gpt-4o-mini-tts`(voice `alloy`), 버튼을 누를 때만 호출·과금, 결과는 캐시 |
| 보컬 분리 | **Demucs** `htdemucs`(별도 프로세스, CPU로 1~3분, 선택 기능) |
| 발음 평가 | Microsoft Azure Speech 발음 평가(녹음·기준 문장 글·로캘만 전송, 사용자가 버튼을 누를 때만) |
| 뜻·표현 설명 | OpenAI 채팅 모델(`gpt-4o-mini` 설정, **호출 확인 전 [미확인]**), 버튼을 누를 때만 |
| 일본어 읽기 | `pykakasi` |
| 화면 | Streamlit |
| 서버 저장 | **PostgreSQL**(전용 컨테이너) + `psycopg` 3, 스키마 변경은 `migrations/*.sql`을 앱이 시작할 때 순서대로 적용 |
| 계정 | 아이디·비밀번호 로그인(표준 라이브러리 `hashlib.scrypt`로 해시, 5회 실패 5분 잠금), 로그인 유지 토큰(DB에는 해시만), 초대 코드 가입 |
| 배포 | Oracle Cloud VM + `systemd` + Cloudflare 터널(HTTPS) |

수업(음성 1~7강, 013)과의 관계는 각 모듈 맨 위 docstring에 `[수업과 같음]` / `[수업에 없음]`으로 적혀 있습니다. WER·CER은 수업이 아니라 자습 노트북 기준입니다.

## 실행

환경은 두 가지입니다.

- **`voice-ai`**(conda, Python 3.11): 개발·테스트·노트북·보컬 분리. `numpy 1.26.4`(TensorFlow 2.16) 고정
- **앱 전용 환경**(`~/venvs/song-lingo-app`, 프로젝트 폴더 밖): Streamlit 앱. `streamlit`을 `voice-ai`에 설치하면 protobuf가 충돌하므로 분리했습니다

API key와 설정은 `.env.example`을 복사해 `.env`에 채웁니다(`OPENAI_API_KEY`, 선택으로 `AZURE_SPEECH_KEY`·`AZURE_SPEECH_REGION`, `SONGLINGO_SEPARATE_PYTHON`). **저장 기능**은 `DB_HOST`·`DB_PORT`·`DB_NAME`·`DB_USER`·`DB_PASSWORD`가 있을 때만 켜지고(없으면 로그인 없이 저장하지 않는 개발용 동작), `SONGLINGO_PASSWORD`가 가입·게스트 입장에 필요한 초대 코드입니다. `.env`는 git에 올리지 않습니다.

```bash
# 테스트 (프로젝트 루트에서)
PY=/opt/anaconda3/envs/voice-ai/bin/python
$PY -m unittest discover -s tests -v   # DB 시험은 환경변수 SONGLINGO_TEST_CONNINFO가 있을 때만 돌고, 로그인·저장 화면 시험(AppTest)은 앱 환경에서 따로 실행

# 앱 환경 만들기 (처음 한 번)
python -m venv ~/venvs/song-lingo-app
~/venvs/song-lingo-app/bin/python -m pip install -r app/requirements.txt

# (선택) 저장 기능용 DB: docker-compose.db.yml로 PostgreSQL 컨테이너를 만들고 .env에 DB_*를 채운 뒤
#   python storage.py ping       # 접속 확인
#   python storage.py migrate    # 스키마 적용(앱도 시작할 때 자동 적용)

# 웹 앱 실행 → http://localhost:8501
SONGLINGO_SEPARATE_PYTHON=$PY ~/venvs/song-lingo-app/bin/python -m streamlit run app/streamlit_app.py
```

시연용 Jupyter 노트북은 `experiments/practice.ipynb`입니다(커널 `voice-ai`). 마이크 녹음을 노트북·스크립트로 하려면 터미널에서 `scripts/record_takes.py`를 씁니다. 그 밖의 스크립트와 명령은 [`CLAUDE.md`](CLAUDE.md)의 Commands를 봅니다.

## 폴더

| 위치 | 내용 |
|---|---|
| 루트 `*.py` | 처리 모듈(`stt`·`tts`·`scoring`·`quality`·`align`·`languages`·`japanese`·`meaning`·`web_song`·`web_practice` …)과 저장 모듈(`storage`·`auth`·`account`·`access`) |
| `app/` | Streamlit 화면(`streamlit_app.py`, `views/`, `ui_practice.py`, `auth_gate.py`, `persist.py`, `explain.py`, `assets/`, `static/`) |
| `migrations/` | 저장 스키마 변경 이력(`001`~`005`, 이미 적용된 파일은 고치지 않고 새 번호를 추가) |
| `tests/` | 모듈마다 `test_*.py`(표준 `unittest`, 합성 신호만 사용) |
| `experiments/` | 작업 과정·실험(노트북, WER/CER, 노래 구간 비교, 스켈레톤) |
| `docs/` | 계획서, 검토 문서, 작업 일지, 개발환경 이슈노트 |
| `data/`, `results/` | 녹음·캐시·업로드·기록(**git 제외**) |

## 개인정보와 한계

- **목소리 녹음, 곡·가사, API key는 저장소에 올리지 않습니다.** 상업 가사는 예시·문서에 넣지 않고 직접 쓴 문장만 씁니다.
- **서버에 저장되는 것**(로그인하고 저장을 켠 경우만, 사이드바에서 끌 수 있음): 연습 기록(점수·문장·인식문), 내 문장 묶음, 내 노래의 구간·인식된 가사·고친 가사, 비밀번호 해시. **업로드한 음원, 잘라 낸 구간, 보컬 분리 결과, 내 녹음은 서버에 저장하지 않습니다**(업로드한 곡은 세션 임시 폴더에만 두고 세션이 끝나면 지움). 계정을 삭제하면 저장된 것이 함께 지워지고, 게스트는 아무것도 저장되지 않습니다. 사용자끼리는 분리됩니다.
- 외부 서비스로 나가는 것: 표준 발음 문장 → OpenAI, 뜻·표현 설명 문장 → OpenAI(버튼), 녹음 → Azure(버튼, 자동 전송 없음). 모두 사용자가 누를 때만 호출되며 과금될 수 있습니다.
- 배포는 접근 제한(초대 코드, `access.py`)·로그인과 HTTPS(마이크)를 갖춰 **완료**했습니다(Oracle VM + Cloudflare 터널, 이슈 #52·#63). 공개 주소에서는 누구나 외부 API(TTS·STT·Azure)를 부를 수 있으므로 초대 코드는 발표 때만 알려 주고 이후 바꿉니다. 안 되면 SSH 터널이나 로컬 시연으로 합니다.
- 점수는 **문장 인식 일치도**입니다(발음 점수 아님). 노래는 같은 입력도 인식 결과가 실행마다 달라질 수 있고(온도 폴백), 일본어+영어가 섞인 줄은 영어가 읽기로 바뀌지 않아 글자 비교가 어긋납니다. 녹음 실험은 대부분 본인 한 명의 목소리라 일반화할 수 없습니다.
- 뜻·표현·IPA 발음 기호는 AI가 만든 **참고용**이며 틀릴 수 있습니다.

## 문서

- 계획(결정된 내용): [`docs/프로젝트 개발 계획서_20261030.md`](docs/프로젝트%20개발%20계획서_20261030.md)
- 검토와 근거: [`docs/프로젝트_안내_및_주제_검토.md`](docs/프로젝트_안내_및_주제_검토.md)
- 모듈 호출 관계·데이터 흐름(다이어그램): [`docs/module_structures_and_data_flow.md`](docs/module_structures_and_data_flow.md)
- 하루 작업 기록, 파일별 역할, 소스 읽는 순서, 남은 일정: [`docs/작업_일지.md`](docs/작업_일지.md)
- 환경·git 문제 해결: [`docs/개발환경_이슈노트.md`](docs/개발환경_이슈노트.md)
- WER/CER 학습 노트: [`experiments/WER, CER/WER_CER_이해하기.ipynb`](experiments/WER,%20CER/WER_CER_이해하기.ipynb)
- 저장소 작업 규칙: [`CLAUDE.md`](CLAUDE.md)
