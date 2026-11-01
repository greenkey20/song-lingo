# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**song-lingo** — 외국어 노래 문장 연습 도우미 (듣고 따라읽고 받아쓰고 확인하는 음성 학습 프로토타입). ICT 혁신 스퀘어 Voice-AI 부트캠프의 **개인 프로젝트**(2026-10-30 ~ 11-11 평일 9일 × 4h = 36h 개발, **11-12 발표**). 사용자가 TTS 기준 음성을 듣고 → 따라 읽은 녹음을 STT로 인식하거나 받아쓰기를 하고 → 정답과의 **오류율(WER/CER)** 과 틀린 부분을 피드백받는다. 점수는 **발음 점수가 아니라 "문장 인식 일치도"** 다(STT가 틀린 발음을 문맥으로 고쳐 적을 수 있음). 시연 화면은 **Jupyter 노트북(`practice.ipynb`)** 이다. 웹 UI(PWA/Streamlit/Gradio) 도입 여부는 **결정 전**이며(검토 문서 8.27·8.29), 지금 `spike/`의 FastAPI 서버는 브라우저 녹음을 점검하려고 만든 임시 코드다.

- **진행 상황(2026-11-01 밤 기준)**: 주말 스켈레톤(S0~S6, 소리 그림 S4.5, 틀린 구간 표시 S4.6)은 끝났고 종강식 설문(오프라인 참석·발표)을 제출했다. 이제 계획서 일정(2일차~)으로 복귀한다(웹 UI 도입 여부는 4일차 결정). README는 매일 쓰지 않고 마일스톤(L1 완료·L2 완료·마지막 정리)마다 갱신한다. 이슈 #1~21은 계획서 항목, #22 이후는 작업 중 추가한 것이다. 남은 L1의 큰 것: 연습 문장 10개(#2), 정규화 방침 확정(#3), 10문장×3회 검증(#10). 현황은 `docs/작업_일지.md`와 GitHub 이슈를 본다.
- **결정된 내용: `docs/프로젝트 개발 계획서_20261030.md`** (L1 필수 → L2 확장 → L3 심화 선택, 일정 · 성공 기준 · 축소 규칙 포함). 사용자가 직접 정리해 강사님께 공유하는 문서이므로 **사용자의 글을 임의로 바꾸지 말고**, 고칠 때는 큰 흐름과 문체를 유지하며 필요한 부분만 고친다.
- **검토·근거·옵션 비교: `docs/프로젝트_안내_및_주제_검토.md`** (절 번호 8.x, 변경 이력은 8.19). 이 사본이 이 저장소에서 앞으로 이어 쓰는 원본이다(학습 저장소의 사본은 10-30 시점의 것). 코드 구조·검증·주석에 관한 판단은 8.32, `quality.py` 기준값 근거는 8.25, 보관본 A절 확인 항목 현황·일정 재조정·웹 UI 결정 시점은 8.33, README 갱신 시점은 8.34.
- **`docs/작업_일지.md`**: 하루 작업 로그, 파일별 역할과 읽는 순서, 이슈 정리, 용어 메모. 사용자가 Notion으로 복사해 면담에 쓴다. `docs/발표_대본_초안_스켈레톤.md`는 3분 발표 대본 초안, `docs/주말_스켈레톤_시연_계획.md`는 끝난 스켈레톤 계획이다.
- **`docs/프로젝트 개발 계획서_20261029.md`는 20261030으로 정리하면서 빠진 내용만 모은 보관본**이다. 특히 **A절의 "1일차에 확인할 항목"(확정되지 않은 항목 10개와 `[확인 필요]` 목록)** 을 점검하고 결과는 검토 문서에 기록한다. 이 파일의 L3 기호는 20261029 기준이라 20261030과 다르다(파일 머리의 주의 참고).
- 학습 배경(1~7강 노트북)은 형제 폴더 `../ict_innovation_sq_voice_ai/`(읽기 전용 참고). 특히 `017_sound/lesson07_whisper_minimal.ipynb`(faster-whisper), `013_openai_api/`(TTS/STT 호출 코드), `017_sound/02·03·lesson04`(WAV 전처리, FFT/STFT/Mel). WER·CER은 수업이 아니라 자습 노트북(`docs/WER_CER_이해하기.ipynb`) 기준이다.

## Environment

- **conda 환경 `voice-ai` 하나만 사용**: `/opt/anaconda3/envs/voice-ai/bin/python` (Python 3.11). 다른 환경(`base` 등)은 쓰지 않는다. 노트북 커널도 `voice-ai`(`Python 3.11 (voice-ai)`).
- `numpy`는 **1.26.4 고정**(TensorFlow 2.16). 새 패키지는 설치 전 **`pip install --dry-run`** 으로 numpy가 바뀌지 않는지 확인한다. 노트북에서는 `%pip` 또는 `!{sys.executable} -m pip`.
- 설치된 것: faster-whisper 1.2.1(디코더 PyAV `av`를 함께 설치함), openai, python-dotenv, pandas, scipy, matplotlib, 그리고 `spike/`용 fastapi·uvicorn·python-multipart. **없는 것**: `pytest`, `streamlit`, `gradio`, `ipywidgets`, `sounddevice`, `soundfile`, `librosa` (노트북에서 직접 마이크 녹음 불가 → **미리 녹음한 파일 경로를 지정**). 테스트는 표준 라이브러리 `unittest`를 쓴다.
- 머신: macOS 13.7, Intel i7 4스레드, RAM 16GB, **GPU 없음**(CPU만). Whisper는 `tiny` + `int8`. (별도로 Oracle Cloud ARM 서버 4코어·RAM 23GB에서 `faster-whisper` import까지만 확인했고 배포는 하지 않았다.)
- **OpenAI API key**는 `.env`의 `OPENAI_API_KEY` (git에 올리지 않음; `.env.example`을 복사해 값을 채운다). 호출 코드는 `load_dotenv()` 후 `OpenAI()`. 노트북 셀 실행은 **실제 과금**되므로 TTS 결과는 캐시(`data/tts_cache/`)해서 재호출을 줄이고 호출 횟수(`tts.calls`)를 기록한다. 직접 입력한 문장은 TTS API로 나가 과금된다.
- **노트북 커널은 import한 모듈과 `.env`를 다시 읽지 않는다.** `.py`나 `.env`를 고친 뒤에는 커널을 재시작해야 반영된다(키를 바꿨는데 같은 401이 나던 원인이었음).
- Read 도구로 `.ipynb`를 열면 출력까지 통째로 나와 매우 크다. 셀 구조는 `json`으로 읽고, 셀 수정은 NotebookEdit을 쓴다.

## Commands

```bash
PY=/opt/anaconda3/envs/voice-ai/bin/python    # 아래 명령은 모두 프로젝트 루트에서 실행(테스트가 루트의 모듈을 import함)
$PY -m unittest discover -s tests -v          # 전체 단위 테스트
$PY -m unittest tests.test_quality            # 파일 하나
$PY -m unittest tests.test_scoring.Boundaries.test_format_diff   # 테스트 하나
$PY scripts/check_notebook.py                 # practice.ipynb 코드 셀을 차례로 실행해 끝까지 되는지 점검(.env 안 읽음 → API 과금 없음, 그림은 results/notebook_check/)
$PY scripts/scan_outputs.py [노트북 ...]      # 커밋 전: 노트북 출력의 오디오 플레이어·/Users 경로·key 검사
$PY -m uvicorn spike.server:app --host 127.0.0.1 --port 8000   # 브라우저 녹음 점검용 임시 서버(내 Mac 안에서만)
```
`tests/test_check_notebook.py`는 스크립트를 실제로 실행해 전체 테스트가 10초 안팎 걸린다. 노트북은 VS Code 또는 `jupyter notebook`에서 연다(커널 `voice-ai`). 빌드/린트 도구는 없다.

## Architecture

한 문장 연습의 데이터 흐름(모듈은 프로젝트 루트에 나란히 있는 flat 구조; `songlingo/` 패키지로의 정리는 이슈 #24, 판단은 8.32):

```
sentences.csv ─ tts.py ─(캐시 data/tts_cache)─▶ 기준 음성(TTS)
내 녹음 ─ audio.py(16 kHz 모노) ─ quality.py(상태 점검, 경고는 안내일 뿐)
        └ stt.py(faster-whisper) ─▶ 인식 문장 ─ scoring.py(WER/CER, 틀린 부분)
틀린 부분 + 단어별 시간(stt.recognize_words) ─ align.py ─▶ TTS·내 녹음의 시간 구간
practice.py(위 순서를 이어 부르고 dict 반환) ─▶ report.py(글) / visualisation.py(그림) ─▶ practice.ipynb(출력만)
```

- **`practice.py`는 계산을 하지 않는 얇은 연결 모듈**이다(`prepare`·`read`·`dictation`·`locate_errors`가 dict를 돌려줌). 기능이 자라면(기록 CSV, 그래프 …) 여기에 넣지 말고 별도 모듈로 만든다. 채점 계산은 `scoring.py`(`evaluate`가 WER·CER과 표시용 쪽을 한 번에), 글은 `report.py`(문자열을 돌려줄 뿐 print하지 않음), 그림은 `visualisation.py`(Figure를 돌려줌; `stft_power`·`logmel`·`to_db` 계산도 여기). 새 채점 로직은 `scoring.score()`의 결과 dict를 재사용한다.
- **노트북은 얇게 둔다**: `run_practice(문장, "read"|"dictation")`와 `show_error_spans`는 `display`·`input`·`plt.show` 같은 Jupyter 전용 처리만 한다. 모듈 `practice`는 노트북에서 `import practice as flow`로 부른다. 재사용·테스트할 함수는 `.py`로 분리한다.
- `scoring.py`의 흐름: `normalize` → 토큰화(`wer`는 공백 단위, `cer`는 글자 단위) → `edit_matrix` → `backtrace`(ops: 일치/치환/삭제/삽입; 최소 거리 경로가 여러 개면 비슷한 토큰끼리 짝짓는 `_tie_scores`) → `score`가 S·D·I·N·rate·ops를 dict로 반환 → `format_diff(ops)`로 표시.
- 다른 파일: `theme.py`(그래프 공통 색·스타일), `sentences.csv`(id, lang, sentence, meaning_ko, source, license; 지금 3문장), `spike/`(임시 웹 점검), `scripts/`, `tests/`(모듈마다 `test_*.py`, 합성 신호만 사용). 아직 없는 계획 모듈: `player.py`·`explain.py`(L2), `experiments/`(L3 실험).
- `data/`(녹음·TTS 캐시·업로드)와 `results/`(기록 CSV·그래프·노트북 점검 그림)는 **git에서 제외**된다.

## Key decisions (자세한 근거는 docs 두 파일)

- **STT**: 기본 로컬 `faster-whisper tiny` (`device="cpu"`, `compute_type="int8"`, `beam_size=1` — 7강 설정, 결과 보고 때 설정을 함께 기록), 인식 언어는 `en`으로 고정(시연은 영어 문장만). OpenAI STT는 대체·비교용. **TTS는 OpenAI(`gpt-4o-mini-tts`, voice `alloy`)로 고정.** 6강에서 만든 Keras 모델은 제품 STT로 쓰지 않는다.
- **채점**: `(S+D+I)/N`. 영어 정규화 = NFC → 소문자 → 구두점 제거(아포스트로피 유지) → 공백 정리. 정답이 비면 오류. **WER은 1을 넘을 수 있으므로 "일치율(1−WER)"로 표시하지 말고** 오류율과 S·D·I 개수로 표시. 틀린 부분은 `difflib` 비교가 아니라 **편집 거리 역추적**으로 구한다(`difflib`은 최소 경로를 보장하지 않음; `difflib`은 동률일 때 단어 유사도 점수에만 쓴다). 일본어는 CER 중심. 축약형·숫자·프랑스어 악센트 방침은 **아직 미확정**(`normalize()`의 인자로 열어 둠, 이슈 #3).
- **녹음 입력 상태 점검(`quality.py`)** 은 음량·무음·클리핑·말한 시간만 본다(잡음 판정이 아님). 기준값은 2026-11-01에 본인 녹음으로 **확정**했다(근거 표는 `quality.py` 맨 위와 검토 문서 8.25): 너무 작음(RMS < −55 dBFS 또는 최대 진폭 < 0.02), 클리핑(**원본** 샘플 0.999 이상 ≥ 1%; 리샘플링 뒤 값으로 재면 울림 때문에 오판), 대부분 무음(STFT 프레임 에너지가 최대 프레임보다 35 dB 이상 낮은 프레임 ≥ 80% — **절대 기준이 아니라 상대 기준**), 말한 시간 < 1.0초, 길이 < 0.5초. 경고가 있어도 인식·채점은 계속한다. Whisper tiny는 소리 크기에 매우 강했다(표본 1명). 잡음 환경은 미시험.
- **L3 기본안은 (a) 노래 구간 인식 + 음악·음성 분리**(강사님 권유; 분리 없는 낭독 vs 노래 CER 비교가 최소 구성). 막히면 (e) 잡음 견고성. 분리 모델(Demucs)은 `--dry-run` 확인만 했고 CPU 속도는 **미확인**. 실험은 시드를 바꿔 **3회 이상** 반복해 평균·범위를 보고하고, 합성 흰 잡음 결과를 실제 환경으로 일반화하지 않으며, 모든 녹음이 본인 한 명이라는 한계를 명시한다.
- **지연 시 축소 순서(L2)**: ① LLM 뜻·표현 → ② 재생 속도·±5초(기본 `Audio` 플레이어로 대체) → ③ 오류율 그래프 → ④ 기록 CSV, **받아쓰기는 마지막까지 유지**(받아쓰기는 스켈레톤에서 이미 앞당겨 구현됨). L3는 항상 선택.
- **그래프 색은 초록 계열로 통일**하고 공통 설정은 `theme.py`에 둔다(근거·검증은 검토 문서 8.26): 그림 전에 `theme.apply_style()`, 스펙트로그램·Log-Mel은 `CMAP_SPEC`, 흰 바탕 히트맵은 `CMAP_HEAT`, 시리즈는 `SERIES` 순서대로 **한 그림 최대 4개**(초록 옆에 주황 금지), 모든 쌍이 이웃하는 그림(산점도 등)은 초록+파랑 2개까지. 파형 그래프만 수업과 같은 기본 파랑(`theme.WAVEFORM`)을 직접 지정한다(`apply_style()`가 색 순환을 초록으로 바꾸기 때문). 색을 새로 정하면 `validate_palette.js`(dataviz 스킬)로 검증하고, `magma`·`Greens_r` 같은 라이브러리 기본 cmap을 그림마다 직접 쓰지 않는다.
- 방향: 이 프로젝트는 **수업(음성 1~7강 + 013) 복습·활용 수단**이기도 하다.

## Privacy / security (공개 저장소 전제)

- `.env`, API key, **사용자 본인 목소리(녹음)**, 강사님 목소리, 강사 제공 WAV, 모델 파일, 화면 캡처(다른 수강생 이름·얼굴)는 **절대 커밋하지 않는다**. **사용자 실명은 어떤 파일명·내용에도 쓰지 않는다.**
- **상업 노래의 가사·음원**은 저장소에 두지 않고, 시연에 쓰지 않고, LLM API에 입력하지 않는다. 연습 문장은 직접 쓴 예문 또는 이용이 확인된 공개 문장이다. 음악·음성 분리 실험의 반주도 직접 만든 것 또는 이용이 허용된 음원만 쓰고 이용 조건을 기록한다.
- **노트북 출력**에는 `<audio>` 플레이어(base64 음원), `/Users/…` 경로, key가 박힐 수 있다. 커밋 전에 출력을 지우고 `scripts/scan_outputs.py`로 확인한다. 로컬 원본(출력 있음)은 그대로 두고 **출력을 지운 정리본을 커밋**한다: 정리본을 임시 파일에 만들어 스캔한 뒤 `git hash-object -w` → `git update-index --cacheinfo 100644,<hash>,practice.ipynb`로 인덱스에 넣는다(그래서 `git status`에 `M practice.ipynb`가 계속 남는 것은 정상).
- `git add -A`, `git add .` 금지 — 파일을 하나씩 추가하고 `git status`로 확인한다. 최종 점검 체크리스트는 계획서 6장 9일차 항목.
- `spike/` 서버는 `127.0.0.1`에서만 열고, 업로드 녹음은 git 제외 폴더 `data/uploads/`에 두며, `.env`·TTS·LLM을 쓰지 않는다. 인터넷에 배포하면 공개 주소에서 누구나 TTS를 불러 과금되므로 접근 제한(비밀번호)이 필요하다.

## Working agreements (사용자와의 합의)

- 채팅은 **친근한 반말**. 문서(md, 노트북 설명 셀)는 "~입니다" 문체를 유지한다.
- **프로젝트 판단·옵션 비교·질문 답변은 채팅에만 남기지 말고 `docs/프로젝트_안내_및_주제_검토.md`에 먼저 기록**하고, 계획서에는 **결정된 내용만** 적는다. 계획서를 고치면 검토 문서 8.19 변경 이력에 한 줄 추가한다.
- **실험·확인은 방법과 코드를 알려 주고 사용자가 직접 실행**하게 한다. 내가 돌린 값은 "참고 baseline"으로 표시하고 해석을 돕는다. 헤드리스로 돌린 노트북 확인은 참고일 뿐 최종 확인은 사용자가 VS Code에서 직접 실행하는 것이다.
- 코드·문서의 숫자와 동작 주장은 **실행해서 확인**하고, 추정은 **[추정]**, 일반 지식은 **[일반 지식]**, 못 한 확인은 **[미확인]** 으로 표시한다(사용자가 이 문서들로 공부한다).
- **커밋은 주제별로, 사용자가 확인한 뒤에만**. 가능하면 적은 수의 큰 커밋. push는 사용자가 요청할 때만. 직접 커밋에는 세션의 `Co-Authored-By` 트레일러를 넣고, 관련 이슈는 메시지에 `Refs #N`으로 적는다. 한국어 `feat:`/`docs:`/`chore:` 메시지 관례(학습 저장소와 동일).
- 칸반은 GitHub Projects(`song-lingo` 보드), 작업은 **이슈 1개 = 카드 1개(L1/L2/L3 라벨; 문서는 `docs`, 기타는 `enhancement`)**. 새 작업이 생기면 이슈를 등록하고 보드에 올린 뒤 그에 맞춰 작업한다. 이슈는 완료 기준 대비 상태를 댓글로 남기되 **닫는 것은 사용자가 판단**한다. `gh`에 `gh project`가 없어 보드는 `gh api graphql`로 조작한다(project id `PVT_kwHOBTa5js4BpeHY`, Status 필드 `PVTSSF_lAHOBTa5js4BpeHYzhn5n0w`, 옵션 Todo `f75ad846` / In Progress `47fc9ee4` / Done `98236657`). 브랜치 → PR → 셀프 머지는 **기능 단위**로만 하고, 문서·잡무는 `main` 직접 커밋도 허용한다. 일정이 밀리면 절차를 줄인다. 이슈 초안은 `docs/issues_초안.md`.
- **사용자가 AI가 쓴 코드를 이해해야 한다**(강사님 요구). **주석 기준**(이슈 #25): ① 파일 맨 위 docstring에 역할·흐름과 **수업과의 관계**(`[수업과 같음]` + 출처 노트북/강, `[수업에 없음]` + 한 줄 설명; 수업은 `../ict_innovation_sq_voice_ai`, 단 WER·CER은 수업이 아니라 자습 노트북) ② 함수 docstring에 하는 일·인자·돌려주는 값 ③ 인라인 주석은 "왜"(읽기만으로 모르는 줄, 라이브러리 옵션의 뜻, 숫자 상수의 의미) ④ 수업에 없는 라이브러리·옵션·개념은 반드시 `[수업에 없음]`과 설명 ⑤ 주석만 고칠 때는 동작을 바꾸지 않고, 단위 테스트가 그대로 통과해야 한다(주석·docstring을 뺀 코드를 AST로 비교해 확인했다). 하루 작업은 `docs/작업_일지.md`에 계획서 9장 양식(한 일·막힌 점·내일 할 일·질문)으로 남기고(강사님 면담이 있는 날의 엔트리에는 **전날 밤에 '강사님께 말씀드릴 것'** 을 "진행 상태 → 막힌 점 → 시도한 것 → 질문" 순서로 미리 적어 두고, 면담 뒤 결정 사항 3줄을 채운다), 새 파일을 만들면 그 문서의 파일 표와 읽는 순서 표에도 한 줄 추가한다(사용자가 Notion으로 복사). 낯선 용어는 같은 문서의 용어 표에 추가한다.
- 사용자가 열어 둔 노트북을 고칠 때는 파일을 다시 읽고(NotebookEdit이 "수정됨" 오류를 내면 다시 읽는다), 사용자의 셀은 건드리지 않고 새 셀만 삽입하며, 사용자에게 *File → Reload Notebook from Disk* 를 안내한다.
