# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**song-lingo** — 외국어 노래 문장 연습 도우미 (듣고 따라읽고 받아쓰고 확인하는 음성 학습 프로토타입). ICT 혁신 스퀘어 Voice-AI 부트캠프의 **개인 프로젝트**(2026-10-30 ~ 11-11 평일 9일 × 4h = 36h 개발, **11-12 발표**). 사용자가 TTS 기준 음성을 듣고 → 따라 읽은 녹음을 STT로 인식하거나 받아쓰기를 하고 → 정답과의 **오류율(WER/CER)** 과 틀린 부분을 피드백받는다. 점수는 **발음 점수가 아니라 "문장 인식 일치도"** 다(STT가 틀린 발음을 문맥으로 고쳐 적을 수 있음). **이 앱은 노래방이 아니다: 사용자가 부른 노래를 채점·평가하지 않는다.** 노래(원곡)는 가사를 얻고 듣기 위한 입력이고, 평가 대상은 사용자의 따라읽기·받아쓰기(와 STT의 가사 인식 품질)이다(11-08 사용자 정정, 이슈 #17). 시연 화면은 **Jupyter 노트북(`experiments/practice.ipynb`)** 이고, 웹 UI는 **Streamlit**(`app/`, 내 문장·내 노래·기록 3페이지)이다. 배포 호스트는 Oracle VM 쪽으로 기울었으나 **미확정**(검토 문서 16.13·16.15). `spike/`의 FastAPI 서버는 브라우저 녹음 점검용 임시 코드다.

**현황(진행 상황·남은 L1·이슈 번호)은 여기에 적지 않는다.** `docs/작업_일지.md`와 GitHub 이슈를 본다. README는 마일스톤(L1 완료·L2 완료·마지막 정리)마다 갱신한다.

## 먼저 지킬 것 (어기면 되돌릴 수 없는 것들)

- **git**: 사용자가 요청하기 전에는 commit·push·PR·브랜치 이동을 하지 않는다(문서만 바뀌어도 마찬가지, 11-07 지시). `git add -A`·`git add .` 금지: 파일을 하나씩 추가하고 `git status`로 확인한다. 커밋은 주제별로, 사용자가 확인한 뒤에만.
- **커밋·공개 금지**: `.env`, API key, 사용자 본인 목소리(녹음), 강사님 목소리, 강사 제공 WAV, 모델 파일, 화면 캡처, **상업 노래의 가사·음원**. 사용자 실명은 어떤 파일명·내용에도 쓰지 않는다(알려진 예외: Demucs 합본 노트북 `experiments/model anatomy/demucs/demucs_structure_analysis_*.ipynb`의 파일명에 실명이 들어 있다. 이름 변경은 미정이며, 바꾸면 노트북 안과 `docs/`·README의 참조도 함께 고친다. 문서에서 이 파일을 가리킬 때는 `*`로 줄여 쓴다). 가사는 로그·오류 메시지·이슈·PR·문서·채팅 답변에도 옮겨 적지 않는다(자세한 규칙은 아래 Privacy).
- **`.env`는 읽지 않는다**: `scripts/check_api_key.py`처럼 `.env`를 읽는 실행과 마이크가 필요한 실행은 사용자가 직접 한다(`! ...`).
- **환경 두 개를 섞지 않는다**: 노트북·스크립트·테스트는 conda `voice-ai`, Streamlit 앱은 별도 venv(`~/venvs/song-lingo-app`). `streamlit`을 `voice-ai`에 설치하지 않는다.
- **노트북 셀 실행은 실제 API 과금**이다. 커밋 전에는 노트북 출력을 지운 정리본만 올린다(Privacy 참고).

## 문서

| 문서                                    | 무엇이 있나                                                                                                                                                                                               |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/프로젝트 개발 계획서_20261030.md` | **결정된 내용**(L1 필수 → L2 확장 → L3 선택, 일정·성공 기준·축소 규칙). 사용자가 직접 정리해 강사님께 공유하는 글이므로 **임의로 바꾸지 말고**, 고칠 때는 큰 흐름과 문체를 유지하며 필요한 부분만 고친다. |
| `docs/프로젝트_안내_및_주제_검토.md`    | 검토·근거·옵션 비교(주제별 9~16장, 변경 이력 9.1, 옛 8.x 번호는 17장 대응표). 이 저장소에서 이어 쓰는 원본. **새 판단은 8장에 잇지 말고 주제에 맞는 장(9~16)의 새 절로 넣는다.**                          |
| `docs/module_structures_and_data_flow.md` | 모듈별 구조·호출 관계·데이터 흐름(아래 Architecture의 자세한 버전).                                                                                                                                     |
| `docs/작업_일지.md`                     | 하루 작업 로그, 파일별 역할·읽는 순서, 이슈 정리, 용어 메모(사용자가 Notion으로 복사해 면담에 씀).                                                                                                        |
| `docs/프로젝트 개발 계획서_20261029.md` | 20261030으로 정리하며 빠진 내용의 보관본. A절 "1일차에 확인할 항목"을 점검해 결과는 검토 문서에 기록. L3 기호는 20261030과 다르다.                                                                        |
| `docs/개발환경_이슈노트.md`             | 환경·git 문제와 해결책. 새 문제가 생기면 번호를 이어 추가.                                                                                                                                                |

검토 문서의 절 안내: 코드 구조·검증·주석 9.4, README 갱신 시점 9.3, `quality.py` 기준값 14.3, 그래프 색 14.4, Azure 발음 평가 14.7, 일정 재조정·웹 UI 결정 시점 10.8, 외부 검토 반영 12.2, 면담 결과 12.3, 연습 문장 13.2, 표기 통일 13.4, 노래 비교 실험 13.5, TTS·WAV 헤더 15.1, 모델 크기 비교 15.2, API 키 확인 15.3, Demucs 15.4, 웹 UI 16.1·16.2·16.4·16.9~16.11, 다국어 16.14, 배포 시험 16.15, 사용자별 저장 16.16·16.17(스키마). 그 밖에 `experiments/WER, CER/연습_문장_데이터_설명.md`(연습 문장 10개), `experiments/skeleton/발표_대본_초안_스켈레톤.md`, `experiments/song vocals/노래_구간_비교_실험_절차.md`(곡 구간 분리·비교 실험 순서와 결과, 이슈 #18), `experiments/song practice/곡_구간_연습문장_만들기_작업기록.md`가 있다.

학습 배경(1~7강 노트북)은 형제 폴더 `../ict_innovation_sq_voice_ai/`(읽기 전용 참고): `017_sound/lesson07_whisper_minimal.ipynb`(faster-whisper), `013_openai_api/`(TTS/STT 호출), `017_sound/02·03·lesson04`(WAV 전처리, FFT/STFT/Mel). WER·CER은 수업이 아니라 자습 노트북(`experiments/WER, CER/WER_CER_이해하기.ipynb`) 기준이다.

## Environment

- **노트북·스크립트·테스트는 conda 환경 `voice-ai`**: `/opt/anaconda3/envs/voice-ai/bin/python` (Python 3.11). 노트북 커널도 `voice-ai`(`Python 3.11 (voice-ai)`). `base` 등 다른 conda 환경은 쓰지 않는다.
- **웹 앱은 별도 venv `~/venvs/song-lingo-app`**: `streamlit`이 protobuf를 끌어와 TensorFlow 2.16과 충돌하므로 `voice-ai`에는 설치하지 않는다. 프로젝트 폴더 **밖**에 둔다(`~/Documents`는 iCloud 동기화 대상). 패키지는 `app/requirements.txt`(`pyarrow==21.0.0` 고정: 26은 NumPy 2 요구). 새 환경의 첫 import는 macOS 검사로 몇 분 걸릴 수 있다(검토 문서 16.4, 이슈노트 #20·#21). 앱 환경에는 torch·demucs가 없다.
- `numpy`는 **1.26.4 고정**(TensorFlow 2.16). 새 패키지는 설치 전 **`pip install --dry-run`** 으로 numpy가 바뀌지 않는지 확인한다. 노트북에서는 `%pip` 또는 `!{sys.executable} -m pip`.
- `voice-ai`에 설치된 것: faster-whisper 1.2.1(디코더 `av` 포함), openai, python-dotenv, pandas, scipy, matplotlib, `sounddevice`(마이크 녹음), `demucs` 4.1.0(보컬 분리; torch 2.2.2 CPU; `sphn` 빌드 실패로 `pip install --no-deps`, 이슈노트 #14), `spike/`용 fastapi·uvicorn·python-multipart. **없는 것**: `pytest`, `streamlit`, `gradio`, `ipywidgets`, `soundfile`, `librosa`. 테스트는 표준 라이브러리 `unittest`. macOS에는 `timeout` 명령이 없으므로 시간 제한은 `faulthandler.dump_traceback_later(초, exit=True)`로 건다.
- 노트북 셀에서는 녹음하지 않고 **미리 녹음한 파일 경로를 지정**한다. 녹음은 터미널의 `scripts/record_takes.py`로, 마이크 권한이 필요해 Claude는 실행하지 않는다.
- 머신: macOS 13.7, Intel i7 4스레드, RAM 16GB, **GPU 없음**(CPU만). Whisper는 `tiny` + `int8`. (Oracle Cloud ARM 서버 4코어·RAM 23GB에서 배포 시험은 검토 문서 16.15.)
- **OpenAI API key**는 `.env`의 `OPENAI_API_KEY`(`.env.example`을 복사해 값을 채움). 호출 코드는 `load_dotenv()` 후 `OpenAI()`. TTS 결과는 캐시(`data/tts_cache/`)해서 재호출을 줄이고 호출 횟수(`tts.calls`)를 기록한다. 직접 입력한 문장은 TTS API로 나가 과금된다.
- **노트북 커널은 import한 모듈과 `.env`를 다시 읽지 않는다.** `.py`나 `.env`를 고친 뒤에는 커널을 재시작해야 반영된다.
- Read 도구로 `.ipynb`를 열면 출력까지 통째로 나와 매우 크다. 셀 구조는 `json`으로 읽고, 셀 수정은 NotebookEdit을 쓴다.

## Commands

```bash
PY=/opt/anaconda3/envs/voice-ai/bin/python    # 아래 명령은 모두 프로젝트 루트에서 실행(테스트가 루트의 모듈을 import함)
APP=~/venvs/song-lingo-app/bin/python         # 웹 앱 전용 환경
$PY -m unittest discover -s tests -v          # 전체 단위 테스트
$PY -m unittest tests.test_quality            # 파일 하나
$PY -m unittest tests.test_scoring.Boundaries.test_format_diff   # 테스트 하나
$PY scripts/check_notebook.py                 # experiments/practice.ipynb 코드 셀을 차례로 실행해 끝까지 되는지 점검(.env 안 읽음 → 과금 없음, 그림은 results/notebook_check/)
$PY scripts/scan_outputs.py [노트북 ...]      # 커밋 전: 노트북 출력의 오디오 플레이어·/Users 경로·key 검사
$PY scripts/check_api_key.py                  # 적용되는 OPENAI_API_KEY 확인(값은 가림). .env를 읽으므로 사용자가 직접
$PY scripts/record_takes.py [--status|--order sentence|--redo ID TAKE]   # 마이크 녹음 → data/recordings/sNN_takeK.wav. 사용자가 직접(검토 문서 13.3, 사용법은 experiments/WER, CER/연습_문장_데이터_설명.md 5.1)
$PY scripts/separate_clip.py [--list|--song N --start S --duration D --id cNN [--cut-only]|--id cNN --separate-only]   # 내 곡 한 구간 자르기(--cut-only)·Demucs 보컬 분리(--separate-only, 20초에 CPU 1~2분), data/song_work/에 저장
$PY scripts/compare_clips.py [--ids c01 …] [--sizes tiny base small] [--vad off|on|both] [--temperature 0.0|default …] [--repeats N]   # 구간별 정답(data/song_work/truth/<id>.txt)과 원곡/보컬 × 크기 × VAD 비교(#18). 노래는 같은 입력도 결과가 흔들려 주 결과는 --temperature 0.0, 확인용은 default --repeats 3. 인식 문장은 results/song_compare/texts.csv에만 저장
$PY scripts/make_slide_figures.py   # 발표 장표 그림 3장(docs/slides/*.png, 1920×1080): Whisper·HTDemucs·두 모델 비교. 숫자는 구조 탐구 노트북에서 확인한 값
NODE_PATH=<pptxgenjs가 있는 node_modules> [PPTX_SKILL_DIR=<pptx 스킬 폴더>] node scripts/make_slides_pptx.js   # docs/slides/발표_20261112_초안.pptx. 발표자 노트는 대본 문서에서 자동으로 가져옴(pptxgenjs는 저장소에 설치하지 않음, 방법은 스크립트 맨 위)
$PY -m uvicorn spike.server:app --host 127.0.0.1 --port 8000   # 브라우저 녹음 점검용 임시 서버(내 Mac 안에서만)

# 웹 앱(앱 전용 환경). 서버는 끝나지 않으므로 Claude는 백그라운드로 띄우고 http://localhost:8501을 연다(`!`로는 출력이 안 보임, 이슈노트 #23).
# `.streamlit/config.toml`을 고치면 서버를 다시 띄운다. 보컬 분리는 SONGLINGO_SEPARATE_PYTHON의 파이썬이 별도 프로세스(scripts/separate_worker.py)로 돌린다(이슈노트 #24).
SONGLINGO_SEPARATE_PYTHON=$PY $APP -m streamlit run app/streamlit_app.py

# 사용자별 저장(PostgreSQL). 접속 정보는 .env의 DB_HOST·DB_PORT(기본 5433)·DB_NAME·DB_USER·DB_PASSWORD — 값을 출력하지 않는 명령이지만 .env를 읽으므로 사용자가 직접
sudo docker compose -f docker-compose.db.yml up -d   # 서버의 전용 DB 컨테이너(127.0.0.1에서만 접속). POSTGRES_PASSWORD는 빈 데이터 폴더를 처음 만들 때만 적용됨
$APP storage.py ping | migrate | import-meanings | reset-password <아이디>   # 연결 확인 / migrations/*.sql 적용(앱도 시작 때 한 번 함) / data/meaning_cache 파일을 DB로 / 잊은 비밀번호 초기화(관리자)
```

- DB 시험은 환경변수 `SONGLINGO_TEST_CONNINFO`(libpq 접속 문자열)가 있을 때만 돌고(테스트마다 임시 스키마 `t_<랜덤>`을 만들어 지움) 없으면 건너뛴다. 로그인·저장 화면 시험(`tests/test_auth_gate_apptest.py`, Streamlit AppTest)은 앱 환경에서 따로 실행한다. DB 없는 가짜 저장소는 `tests/fake_store.py`.
- `tests/test_check_notebook.py`는 스크립트를 실제로 실행해 전체 테스트가 10초 안팎 걸린다. 노트북은 VS Code 또는 `jupyter notebook`에서 연다. 빌드/린트 도구는 없다.

## Architecture

모듈은 프로젝트 루트에 나란히 있는 flat 구조다(`songlingo/` 패키지로의 정리는 이슈 #24, 판단은 9.4). 모듈별 자세한 호출 관계는 `docs/module_structures_and_data_flow.md`.

한 문장 연습의 데이터 흐름:

```
sentences.csv ─ tts.py ─(캐시 data/tts_cache)─▶ 기준 음성(TTS)
내 녹음 ─ audio.py(16 kHz 모노) ─ quality.py(상태 점검, 경고는 안내일 뿐)
        └ stt.py(faster-whisper) ─▶ 인식 문장 ─ scoring.py(WER/CER, 틀린 부분)
틀린 부분 + 단어별 시간(stt.recognize_words) ─ align.py ─▶ TTS·내 녹음의 시간 구간
practice.py(위 순서를 이어 부르고 dict 반환) ─▶ report.py(글) / visualisation.py(그림) ─▶ practice.ipynb(출력만)
```

- **`practice.py`는 계산을 하지 않는 얇은 연결 모듈**이다(`prepare`·`read`·`dictation`·`locate_errors`가 dict를 돌려줌). 기능이 자라면(기록 CSV, 그래프 …) 여기에 넣지 말고 별도 모듈로 만든다. 채점 계산은 `scoring.py`(`evaluate`가 WER·CER과 표시용 쪽을 한 번에), 글은 `report.py`(문자열을 돌려줄 뿐 print하지 않음), 그림은 `visualisation.py`(Figure를 돌려줌). 새 채점 로직은 `scoring.score()`의 결과 dict를 재사용한다.
- **노트북은 얇게 둔다**: `run_practice(문장, "read"|"dictation")`와 `show_error_spans`는 `display`·`input`·`plt.show` 같은 Jupyter 전용 처리만 한다. 노트북에서는 `import practice as flow`. 재사용·테스트할 함수는 `.py`로 분리한다.
- `scoring.py`의 흐름: `normalize` → 토큰화(`wer`는 공백 단위, `cer`는 글자 단위) → `edit_matrix` → `backtrace`(ops: 일치/치환/삭제/삽입; 최소 거리 경로가 여러 개면 비슷한 토큰끼리 짝짓는 `_tie_scores`) → `score`가 S·D·I·N·rate·ops를 dict로 반환 → `format_diff(ops)`로 표시.
- **입력은 경로뿐 아니라 bytes·`BytesIO`도 받는다**(웹 업로드·브라우저 녹음용, 이슈 #37): `audio.load_raw`·`load_audio`·`decode`, `stt.recognize`·`recognize_words`, `quality.check_file`, `practice.read`. **STT에는 경로나 bytes를 그대로** 넣는다. 우리 `audio.py`가 16 kHz로 바꾼 배열을 넣으면 파형이 조금 달라져, 말소리 30건은 같았지만 노래 구간(원곡, tiny, `temperature=0.0`)은 14개 중 10개의 인식문이 달라졌다(검토 문서 16.4). 결과를 경로와 맞춰야 할 때 배열 입력은 쓰지 않는다.
- `recorder.py`는 마이크 녹음과 `sNN_takeK.wav` 저장만 하고 화면을 모른다(터미널은 `scripts/record_takes.py`, 웹은 `st.audio_input`). 녹음 파일의 STT 입력용 리샘플링은 faster-whisper가 안에서 한다(`audio.py`는 상태 점검·그림용, 검토 문서 14.6).
- `separate.py`: 내 곡의 구간 디코딩(`audio.load_raw` 재사용), 자르기(`cut_clip`)와 Demucs 보컬 분리(`separate_clip`)를 따로 부를 수 있고(`process_clip`은 둘을 잇는 편의 함수), 저장만 한다(이슈 #18). 곡·결과는 `data/songs`, `data/song_work`(git 제외)에만 둔다.
- **노래 구간 → 연습 줄 흐름(이슈 #31)**: `stt.recognize_segments`(구간 시각·신뢰 지표, 노래용 기본은 VAD 끔·경로 그대로) → `song_lines.split_into_lines`(구간을 한 줄로, 길면 단어 사이 쉼에서 분할·짧으면 병합, 기본 6초·14단어) → `song_practice`(`prepare_lines`가 `data/song_practice/<id>/lines.json` 저장, `apply_edits`로 사람이 고친 가사 반영(`stt_text`는 원문 보존, **이미 있으면 덮어쓰지 않음**), `make_tts`는 기본이 호출 없는 계획 모드이고 `generate=True`일 때만 OpenAI TTS 호출·과금). faster-whisper의 `avg_logprob` 등 신뢰 지표는 30초 창 하나의 값이라 한 클립의 모든 구간이 같으므로 줄별이 아닌 **클립 단위 힌트**(`low_confidence`)로만 쓴다. 줄 단위 보컬 조각(#32)은 아직 없다. 확인·수정 노트북은 `experiments/song practice/song_practice.ipynb`(출력에 곡 소리·가사가 들어가므로 정리본만 커밋).
- **F0 분석(이슈 #82, 검토 문서 16.18)**: `pitch.py`(`audio.load_audio` 16 kHz 모노 → `librosa.pyin`, 20 ms 간격)가 `analyze_f0`·`analyze_waveform`·`relative_semitones`(중앙값 기준 semitone)·`to_word_axis`(`x = i + (t−s)/(e−s)`)·`warm_up`을 둔다. **무성음은 NaN(0 Hz 아님)**, 실패는 예외가 아니라 `status`. 그림은 `visualisation.plot_f0_contour`·`plot_f0_compare`(참고 TTS와 내 녹음을 **단어축**에 겹침), 화면은 `app/ui_practice._show_f0`.
  단어축은 `align.word_spans`가 기준 단어마다 TTS·내 구간을 구해 만든다. **`practice.locate_errors` 결과를 재사용**하고(`ui_practice._locate_words`가 채점 직후 한 번만 구해 틀린 구간 그림과 공유), 한 Whisper 단어가 두 토큰이 되는 `we'll → we·will`은 **구간을 토큰 수로 균등 분할**한다(같은 곡선이 두 칸에 중복되지 않게). 공백 없는 언어·TTS 없음·단어 시간 실패는 내 윤곽만 보여 준다.
  **점수·등급 없는 참고용 관찰**이며 DB에 저장하지 않는다. 의존성 `librosa==0.11.0`(1.0.0은 Python 3.12+)·`numba==0.62.1`·`llvmlite==0.45.1`(Intel Mac 휠 때문에 고정, `--only-binary`), 새 프로세스의 첫 호출은 numba 컴파일로 12~20초라 앱이 시작 때 `warm_up`을 백그라운드로 돌린다.
- `clip_compare.py`·`model_compare.py`는 실험 도구(구간별 정답 비교, 모델 크기 비교)로 `practice.py`와 분리돼 있다.

### 웹 앱 (Streamlit; 검토 문서 16.10·16.11, 이후 변경은 16.14~16.17)

- `app/streamlit_app.py`가 `st.navigation`으로 페이지 3개를 연결한다: **내 문장**(`/text`, `app/views/lyrics.py`)·**내 노래**(`/clip`, `song.py`)·**기록**(`/history`, `history.py`). Streamlit은 기본 페이지 주소를 `/`로 고정하므로 보이지 않는 기본 페이지가 내 문장으로 보낸다. 화면 코드는 위젯 배치만 하고 계산은 루트 모듈이 한다.
  - `web_song.py`: 업로드·파형 윤곽·구간 자르기·줄 인식·확정·보컬 분리(세션 임시 작업 폴더 `songlingo_*`에만 저장). 보컬 분리는 화면을 막지 않는 백그라운드(`start_vocals`·`vocals_status`, 화면은 `st.fragment(run_every)`).
  - `web_practice.py`: prep 만들기·TTS 캐시 확인·결과 카드/단어 대조 HTML(사용자 글은 `html.escape`), `error_spans`(틀린 구간, `practice.locate_errors` 재사용). 앱은 TTS를 자동으로 부르지 않고 버튼으로만 부른다(`practice.prepare` 대신 `web_practice.make_prep`).
  - `app/ui_practice.py`: 따라읽기·받아쓰기 화면 부품(두 페이지 공유). `visualisation.plot_sound_panels`(파형·FFT·STFT·Log-Mel 2×2)를 결과 아래에 표시.
  - `app/explain.py`: 화면 요소별 "어떻게 동작하나요?" 설명 상자 글(`TEXTS` 키와 화면 호출은 `tests/test_explain_keys.py`로 맞춤, 이슈 #56). 루트 `explain.py`는 없다 — LLM 뜻·표현 설명은 `meaning.py`.
- **내 노래**: 입력은 파일 업로드와 마이크 녹음(`st.audio_input`, 이슈 #51) 두 가지이며 `(이름, bytes)`로 합쳐 같은 흐름을 탄다. 구간 슬라이더는 곡 전체 범위(파형 가로축과 같음), 미리 듣기는 `st.audio(start_time, end_time)`. 인식된 가사는 확정 없이 바로 연습할 수 있다(고치면 저장, 표준 발음은 지금 보는 한 줄만 만든다). 노래의 STT는 구간을 정한 뒤 `stt.detect_language`로 **제안 → 사용자 확인**을 거쳐 `languages.stt_options`가 `language`·`multilingual`을 정한다(`multilingual=True`는 30초 창마다 재감지하고 `language`를 덮어써 10~20초 구간에서는 효과가 없다).
- **언어(이슈 #50, 16.14)**: `languages.py`가 언어 표(이름·Azure 로캘·공백 여부)와 규칙을 한곳에 둔다. 내 문장은 줄마다 글자 수가 가장 많은 문자 체계로 언어를 **제안**하고(라틴 문자는 `languages.detect_latin_language`의 낱말·특징 글자 점수) 그 줄만 바꾸는 선택 칸이 있다. 일본어·중국어는 공백 없이 이어 줄을 만들고 WER 대신 CER을 본다(WER은 문장 전체가 1단어가 됨). 일본어는 `japanese.py`(`pykakasi`)로 한자·가타카나를 히라가나 읽기·로마자로 바꿔 보여 주고 기준·인식을 읽기로 바꿔 채점하며(`web_practice.apply_japanese_reading`), Azure 평가를 주로 본다.
- **한글 뜻·표현 설명**(이슈 #58): `meaning.py`(예시는 직접 쓴 뜻, 그 밖은 버튼으로 OpenAI `gpt-4o-mini`, 호출은 **확인 전 [미확인]**). 캐시는 서버 DB의 공유 테이블 `meanings`(이슈 #69) + 파일 `data/meaning_cache/`. 화면은 `ui_practice.meaning_group`·`notes_box`.
- **Azure 발음 평가**(`azure_pronunciation.py`, 검토 문서 14.7): `parse_assessment`는 키 없이 테스트하는 순수 함수, `assess`는 녹음 → 16 kHz PCM16 푸시 스트림 → `recognize_once`(SDK는 앱 환경에만 있고 함수 안에서 처음 불러옴). **Azure에는 녹음·기준 문장 글·로캘만 보내고 TTS 소리는 보내지 않으며, 평가 기준은 TTS가 아니라 Azure의 원어민 발음 모델이다.** 음소 기호는 지정하지 않으면 SAPI라 `phoneme_alphabet="IPA"`로 요청한다. 일본어·프랑스어 지원은 미확인. 화면은 `ui_practice._show_azure`, 카드·단어별 점수는 `web_practice.azure_*_html`.
- **계정·저장(이슈 #52·#63·#65·#67, 16.16·16.17)** — 세 층으로 나뉜다:
  - `auth.py`: 순수 판단 로직(scrypt 해시, 아이디·비밀번호 규칙, 로그인 유지 토큰, 5회 실패 시 5분 잠금). DB·화면을 모른다.
  - `storage.py`: **SQL만 실행**(PostgreSQL, `psycopg` v3, 호출마다 연결을 열고 닫음, 모든 SQL은 `%s` 파라미터 + `user_id` 조건). 테이블: 계정·토큰·구간(`clips`)·내 문장 묶음(`texts`, 사용자당 최대 50)·줄(`lines`)·연습 기록(`practices`)·공유 `meanings`. 스키마는 `migrations/NNN_*.sql`(번호 순서, `storage.migrate`). `DB_NAME`·`DB_USER`가 없으면 `enabled()`가 False라 저장 없이 개발용 게스트 모드로 동작한다.
  - `account.py`: `auth`와 `storage`를 이어 붙인 가입·로그인·로그인 유지 서비스(`store=`로 가짜 저장소를 넣어 DB 없이 시험; 로그인 실패 글은 아이디 없음·비밀번호 틀림이 같고 응답 시간도 비슷하게).
  - 화면: `app/auth_gate.py`(로그인·가입·게스트 화면, 자동 로그인 쿠키 `sl_auth`는 JS로 쓰고 `st.context.cookies`로 읽음; 가입은 **초대 코드 = `SONGLINGO_PASSWORD`** 필요; DB 접속 정보가 없으면 예전처럼 비밀번호만 묻고 게스트로 동작) + `app/persist.py`(화면 → DB 저장의 얇은 연결: 로그인했고 저장을 켠 사용자만 저장, 내용 지문이 같으면 건너뜀, 실패해도 연습은 계속, 오류 종류만 알림).
  - 접근 제한은 `access.py`(판단)와 `app/streamlit_app.py` 맨 위의 인증 게이트이며 모든 페이지 앞에서 `st.stop()`으로 막는다. 세션별 잠금뿐이라 서버 앞단의 속도 제한과 긴 비밀번호가 함께 필요하다.
  - `practice_log.py`는 채점 때마다 `results/practice_log.csv`에 **문장 글 없이** key·점수만 기록하고, 로그인한 사용자의 DB 기록(`practices`)에는 인식문·내 답이 포함된다(Privacy 참고).
- 테마는 `.streamlit/config.toml`(색은 `theme.py`의 `BUTTON_GREEN`·`PURPLE`·`LIME` 등과 `tests/test_theme_config.py`로 일치 확인; **글꼴 설정에는 Google Fonts 주소를 하나만**, 둘 이상이면 세션이 안 만들어져 Connection lost, 이슈노트 #22). 로고는 `app/assets/logo.png`(`st.logo`).
- 다른 파일: `theme.py`(그래프 공통 색·스타일), `sentences.csv`(id, lang, sentence, meaning_ko, source, license, probe; 10문장), `spike/`(임시 웹 점검), `scripts/`, `tests/`(모듈마다 `test_*.py`, 합성 신호만 사용), `experiments/`(**작업 과정·실험은 모두 여기**, 주제별 하위 폴더; `docs/`에는 프로젝트 전체 문서만. 노트북은 위로 올라가며 루트를 찾아 `chdir`·`sys.path`를 맞추는 셀로 시작한다). 계획만 있고 **파일이 없는** 모듈: `player.py`(L2; 재생 속도), `pronunciation.py`(소리 대 소리 평가, 설계만 14.7; **구현 전에 설계 승인 필요**).
- `data/`(녹음·TTS 캐시·업로드·내 곡)와 `results/`(기록 CSV·그래프·노트북 점검 그림)는 **git에서 제외**된다.

## 발표 자료 (11-12 발표, 온라인이 될 가능성이 큼)

- **대본의 원본은 `docs/발표_대본_20261112.md`**: 장마다 **화면**(슬라이드 내용)과 **대본**(발표자 노트가 됨), 부록에 시연 체크리스트·백업 계획·**온라인 발표 점검표**·예상 질문·숫자 근거표·장표 그림 검토·**[결정 필요] 목록**. 말하는 모든 숫자·주장은 **[확인]/[추정]/[미확인]** 중 하나로 표시하고, 확인한 것과 해석을 구분해서 쓴다(발표 원칙: 시행착오를 있는 그대로, 이해한 것과 못 한 것을 나눔). 슬라이드나 숫자를 고칠 때는 **대본 문서를 먼저** 고친다.
- `docs/slides/`: 직접 그린 구조 그림 PNG 3장과 PPTX 초안(25장, 웹 앱 팔레트: 짙은 초록·버튼 초록·민트·**라임 강조**, 보라는 틀린 것·해석·한계에만; 로고·아이콘은 `app/assets/`). 외부(ChatGPT가 보여 준) 그림은 출처·정확성 문제로 쓰지 않았다(대본 부록의 검토 표). 생성은 위 Commands의 두 스크립트이고, PPTX 렌더 확인에는 LibreOffice가 필요하다. 시연 문장·6번 목표 표현·AI 협업 문구는 **(임시)** 표시가 붙은 미확정 항목이다.
- **용어 사전의 원본은 `docs/작업_일지.md` 5장**이다(한글은 가나다순, 영문은 알파벳순). 대본의 "용어 정리" 같은 다른 문서의 용어표는 **요약**이므로 새 용어는 일지 5장에 먼저 추가한다.

## Key decisions (자세한 근거는 docs 두 파일)

- **STT**: 기본 로컬 `faster-whisper tiny`(`device="cpu"`, `compute_type="int8"`, `beam_size=1` — 7강 설정, 결과 보고 때 `stt.settings()`로 설정을 함께 기록), 연습 문장의 인식 언어는 `en` 고정. **모델 크기는 `stt.recognize(model_size=)`, VAD는 `vad_filter=`로 바꿔 비교한다**(기본은 `recognize` 끔·`recognize_words` 켬이라 두 경로 설정이 다르다. `tiny`에서는 결과가 같지만 `small`에서는 달라진 사례가 있어 기본 모델을 바꿀 때 통일한다). 기본 `tiny`(기준선)를 유지하고 `model_compare.compare_models`로 같은 녹음을 여러 크기에 돌려 본 뒤 정한다(`stt.available_models()`가 `models/`의 모델을 찾음; 15.2). 큰 모델은 틀린 발음을 문맥으로 더 고쳐 적을 수 있어 "발음 점수가 아님"에 유의. **노래 구간(내 곡 로컬 처리)의 STT는 `medium` + 원곡 + VAD 끔 + 기본 설정(폴백 켬)** (11-03 비교: `medium`은 원곡이 보컬보다 낫고 빠름, micro WER 0.177 대 0.257; `base`는 분리한 보컬이 나음; 원곡에 VAD를 켜면 가사가 통째로 지워지고 `temperature=0.0`은 반복 루프를 낳음; 노래에서는 `recognize_words(vad_filter=False)`를 명시; 13.5·15.2). 보컬 분리는 선택 기능이고 용도는 학습자용 기준 음성(#32)과 UI의 **"보컬만 듣기"**(반주를 뺀 원어민 발음을 듣는 보조, 따라 부르기가 아님; 16.10). OpenAI STT는 대체·비교용. **TTS는 OpenAI(`gpt-4o-mini-tts`, voice `alloy`)로 고정.** 6강의 Keras 모델은 제품 STT로 쓰지 않는다. 추가 STT 실험은 하지 않기로 했고(원곡 대 보컬은 확정 못 함) 발표는 시행착오를 있는 그대로 공유한다.
- **채점**: `(S+D+I)/N`. 영어 정규화 = NFC → 소문자 → 구두점 제거(아포스트로피 유지) → 공백 정리 → **표기 통일**(축약형 펼치기 `we're→we are`, 0~99 숫자 단어→숫자 `twenty→20`; `'s`·`'d` 제외; 양쪽에 같은 규칙; 기본 켬, `normalize(unify=False)`로 엄격 채점; 이슈 #3, 13.4; **점수를 보고할 때는 어느 쪽인지 적는다**). 정답이 비면 오류. **WER은 1을 넘을 수 있으므로 "일치율(1−WER)"로 표시하지 말고** 오류율과 S·D·I 개수로 표시. 틀린 부분은 `difflib`이 아니라 **편집 거리 역추적**으로 구한다(`difflib`은 동률일 때 단어 유사도 점수에만). 일본어는 CER 중심. 프랑스어 악센트 방침은 **미확정**(`normalize(strip_accents=)`로 열어 둠).
- **녹음 입력 상태 점검(`quality.py`)** 은 음량·무음·클리핑·말한 시간만 본다(잡음 판정이 아님). 기준값은 11-01 본인 녹음으로 확정(근거 표는 `quality.py` 맨 위와 14.3): 너무 작음(RMS < −55 dBFS 또는 최대 진폭 < 0.02), 클리핑(**원본** 샘플 0.999 이상 ≥ 1%; 리샘플링 뒤 값은 울림 때문에 오판), 대부분 무음(STFT 프레임 에너지가 최대 프레임보다 35 dB 이상 낮은 프레임 ≥ 80% — 상대 기준), 말한 시간 < 1.0초, 길이 < 0.5초. 경고가 있어도 인식·채점은 계속한다. Whisper tiny는 소리 크기에 매우 강했다(표본 1명). 잡음 환경은 미시험.
- **L3 기본안은 (a) 노래 구간 인식 + 음악·음성 분리**(강사님 권유). 막히면 (e) 잡음 견고성. 실험은 시드를 바꿔 **3회 이상** 반복해 평균·범위를 보고하고, 합성 흰 잡음 결과를 실제 환경으로 일반화하지 않으며, 모든 녹음이 본인 한 명이라는 한계를 명시한다.
- **웹 UI(11-04 면담·결정, 16.9)**: UI를 먼저 만든다. 시안 팔레트는 `theme.py`와 같고(`#1a9f4c`·`#fcfcfb`·`#0b0b0b`), **틀린 단어는 보라 `#6250d6` + 밑줄, 빨강은 쓰지 않는다**(Streamlit `redColor` 계열 테마도 보라). `app/references/`(시안·손그림)는 커밋하지 않는다(`.git/info/exclude`). TTS wav는 스트리밍 저장이라 헤더 길이가 `0xFFFFFFFF`인데 `tts.tts_wav`가 저장 직후와 캐시 적중 때 `fix_wav_header`로 고치므로 `st.audio`에 그대로 넘겨도 된다(폴더 전체는 `tts.fix_wav_headers()`).
- **지연 시 축소 순서(L2)**: ① LLM 뜻·표현 → ② 재생 속도·±5초(기본 `Audio` 플레이어로 대체) → ③ 오류율 그래프 → ④ 기록 CSV, **받아쓰기는 마지막까지 유지**. L3는 항상 선택.
- **그래프 색은 초록 계열로 통일**하고 공통 설정은 `theme.py`(근거·검증 14.4): 그림 전에 `theme.apply_style()`, 스펙트로그램·Log-Mel은 `CMAP_SPEC`, 흰 바탕 히트맵은 `CMAP_HEAT`, 시리즈는 `SERIES` 순서대로 **한 그림 최대 4개**(초록 옆에 주황 금지), 모든 쌍이 이웃하는 그림(산점도 등)은 초록+파랑 2개까지. 파형 그래프만 수업과 같은 기본 파랑(`theme.WAVEFORM`)을 직접 지정한다. 색을 새로 정하면 `validate_palette.js`(dataviz 스킬)로 검증하고, `magma`·`Greens_r` 같은 라이브러리 기본 cmap을 직접 쓰지 않는다.
- 이 프로젝트는 **수업(음성 1~7강 + 013) 복습·활용 수단**이기도 하다.

## Privacy / security (공개 저장소 전제)

현재 유효한 규칙만 적는다. 변경 경위(11-03·11-04·11-05·11-07·11-08 결정)는 검토 문서 13.5·16.10·16.16·16.17.

- **상업 노래의 가사·음원**(`data/songs`)은 저장소·이슈·PR·문서에 올리지 않는다(결과는 곡 번호와 숫자로만). 가사를 **외부 API(OpenAI TTS·LLM)로 보내는 것은 허용**하나, 그 결과물(가사로 만든 TTS, LLM 설명, 인식된 가사)도 `data/`(git 제외)나 서버 DB에만 둔다. 연습 문장 기본은 직접 쓴 예문 또는 이용이 확인된 공개 문장이며, 사용자가 붙여넣은 상업 가사는 예시 문장·코드·문서에 넣지 않는다.
- **허용되는 처리**: 내 컴퓨터에서의 로컬 개인 학습 도구(Demucs + 로컬 Whisper), 발표 시연에서 곡 1개 로컬 재생(저장소·슬라이드에는 음원 없음), **사용자 허락 아래 Claude가 인식된 가사를 읽고 분석**(오류 분류·CER 계산·코드 확인; 문서·이슈·PR·채팅에 가사를 옮기지 않음), 합성 반주 실험은 이용 조건을 기록.
- **내 노래 모드는 배포 버전에도 있다**: 사용자가 실행 중 업로드한 곡은 ① 저장소 어디에도 두지 않고 ② 배포 앱은 접근 제한(초대 코드·로그인)을 걸며 ③ 로그·`print`·오류 메시지에 가사를 남기지 않는다. 서버에서 `medium` STT와 Demucs가 돌 수 있는지는 호스트를 정하기 전에 측정한다(16.15).
- **사용자별 서버 저장(구현됨, 서버 적용 전)**: 로그인하고 저장을 켠 사용자(기본 켬, 끌 수 있고 화면에 "서버에 저장된다"고 알림)의 **가사(STT)·고친 가사·구간 정보(시작·길이)·한글 뜻·표현 설명·내 문장·채점 결과(인식문·내 답 포함)** 를 서버 DB에 계속 보관하고 사용자가 원하면 직접 삭제한다. 그대로 지키는 것: ① 가사·곡 이름·결과를 저장소·문서·이슈·PR·커밋·**로그·오류 메시지**에 올리거나 남기지 않는다 ② **업로드한 음원, 잘라 낸 구간 wav, 보컬 분리 결과, 내 녹음은 저장하지 않는다**(세션 임시 폴더뿐, 세션이 끝나면 지움) ③ 접근은 로그인 뒤에서만, 사용자끼리 분리(모든 쿼리에 `user_id` 조건) ④ 경로 조작·사용자 간 누출은 단위 테스트로 확인. 공유 테이블 `meanings`는 문장 글 없이 글+언어의 해시 키와 설명만 저장하고 내부 로직에서만 쓴다.
- **사용자 녹음의 외부 전송**: 따라읽기 녹음을 **Azure Speech(발음 평가)로 보내는 것은 시연·발표용 옵션으로 허용**한다. ① **사용자가 "Azure로 평가하기" 버튼을 누를 때만** 전송(자동 전송 금지) ② 화면에 전송 안내 ③ 녹음을 서버 디스크에 저장하지 않음(푸시 스트림) ④ 키·지역(`AZURE_SPEECH_KEY`·`AZURE_SPEECH_REGION`)은 `.env`에만. 다른 외부 서비스로 녹음을 보내려면 사용자 승인을 따로 받는다.
- **노트북 출력**에는 `<audio>` 플레이어(base64 음원), `/Users/…` 경로, key가 박힐 수 있다. 로컬 원본(출력 있음)은 그대로 두고 **출력을 지운 정리본을 커밋**한다: 정리본을 임시 파일에 만들어 `scripts/scan_outputs.py`로 스캔한 뒤 `git hash-object -w` → `git update-index --cacheinfo 100644,<hash>,<노트북 경로>`로 인덱스에 넣는다(그래서 `git status`에 `M …ipynb`가 계속 남는 것은 정상). **커밋 전에 소스 diff를 확인한다**: 출력을 지운 정리본이 HEAD와 셀 소스가 같으면 올릴 것이 없고, 소스가 다르면 그 차이가 **의도한 변경인지** 본다(로컬 실행 설정 `GENERATE=True`·`APPLY=True`·`CLIP_ID`, 엉뚱한 자리에 붙은 셀은 올리지 않는다).
- `spike/` 서버는 `127.0.0.1`에서만 열고, 업로드 녹음은 git 제외 폴더 `data/uploads/`에 두며, `.env`·TTS·LLM을 쓰지 않는다. 인터넷에 배포하면 공개 주소에서 누구나 TTS를 불러 과금되므로 접근 제한이 필요하다(Streamlit 앱도 같다).

## Working agreements (사용자와의 합의)

- 채팅은 **친근한 반말**. 문서(md, 노트북 설명 셀)는 "~입니다" 문체를 유지한다.
- **프로젝트 판단·옵션 비교·질문 답변은 채팅에만 남기지 말고 `docs/프로젝트_안내_및_주제_검토.md`에 먼저 기록**하고, 계획서에는 **결정된 내용만** 적는다. 계획서를 고치면 검토 문서 9.1 변경 이력에 한 줄 추가한다.
- **실험·확인은 방법과 코드를 알려 주고 사용자가 직접 실행**하게 한다. 내가 돌린 값은 "참고 baseline"으로 표시한다. 헤드리스로 돌린 노트북 확인은 참고일 뿐 최종 확인은 사용자가 VS Code에서 직접 실행하는 것이다.
- 코드·문서의 숫자와 동작 주장은 **실행해서 확인**하고, 추정은 **[추정]**, 일반 지식은 **[일반 지식]**, 못 한 확인은 **[미확인]** 으로 표시한다(사용자가 이 문서들로 공부한다).
- **커밋·push·PR은 사용자가 요청할 때만**(위 "먼저 지킬 것"). 커밋하게 되면 한국어 `feat:`/`docs:`/`chore:` 메시지 관례, 관련 이슈는 `Refs #N`, 세션의 `Co-Authored-By` 트레일러를 넣는다. 브랜치 → PR → 셀프 머지는 기능 단위로만 하고, 일정이 밀리면 절차를 줄인다.
- 칸반은 GitHub Projects(`song-lingo` 보드), 작업은 **이슈 1개 = 카드 1개(L1/L2/L3 라벨; 문서는 `docs`, 기타는 `enhancement`)**. 새 작업이 생기면 이슈를 등록하고 보드에 올린 뒤 그에 맞춰 작업한다. 이슈는 완료 기준 대비 상태를 댓글로 남기되 **닫는 것은 사용자가 판단**한다. `gh`에 `gh project`가 없어 보드는 `gh api graphql`로 조작한다(project id `PVT_kwHOBTa5js4BpeHY`, Status 필드 `PVTSSF_lAHOBTa5js4BpeHYzhn5n0w`, 옵션 Todo `f75ad846` / In Progress `47fc9ee4` / Done `98236657`). 이슈 초안은 `docs/issues_초안.md`.
- **사용자가 AI가 쓴 코드를 이해해야 한다**(강사님 요구). **주석 기준**(이슈 #25): ① 파일 맨 위 docstring에 역할·흐름과 **수업과의 관계**(`[수업과 같음]` + 출처 노트북/강, `[수업에 없음]` + 한 줄 설명; 수업은 `../ict_innovation_sq_voice_ai`, 단 WER·CER은 자습 노트북) ② 함수 docstring에 하는 일·인자·돌려주는 값 ③ 인라인 주석은 "왜"(읽기만으로 모르는 줄, 라이브러리 옵션의 뜻, 숫자 상수의 의미) ④ 수업에 없는 라이브러리·옵션·개념은 반드시 `[수업에 없음]`과 설명 ⑤ 주석만 고칠 때는 동작을 바꾸지 않고 단위 테스트가 그대로 통과해야 한다. 하루 작업은 `docs/작업_일지.md`에 계획서 9장 양식(한 일·막힌 점·내일 할 일·질문)으로 남기고(면담이 있는 날의 엔트리에는 **전날 밤에 '강사님께 말씀드릴 것'** 을 "진행 상태 → 막힌 점 → 시도한 것 → 질문" 순서로 미리 적고, 면담 뒤 결정 사항 3줄을 채운다), 새 파일을 만들면 그 문서의 파일 표와 읽는 순서 표에도 한 줄 추가한다(사용자가 Notion으로 복사). 낯선 용어는 같은 문서의 용어 표에 추가한다.
- 사용자가 열어 둔 노트북을 고칠 때는 파일을 다시 읽고(NotebookEdit이 "수정됨" 오류를 내면 다시 읽는다), 사용자의 셀은 건드리지 않고 새 셀만 삽입하며, 사용자에게 *File → Reload Notebook from Disk* 를 안내한다.

## Development & Learning Protocol for SongLingo

내 목표는 기능을 빠르게 완성하는 것뿐 아니라, 소스코드의 구조와 핵심 동작 원리를 이해하고 직접 유지보수할 수 있는 개발자가 되는 것이다.
따라서 다음 원칙을 지켜라.

### 1. 구현 전에 설계를 먼저 설명한다.
- 수정할 파일과 모듈을 먼저 제시한다.
- 각 모듈의 책임과 데이터 흐름을 설명한다.
- 새로운 모듈이 필요하다면 기존 모듈로 처리할 수 없는 이유를 설명한다.
- 구현을 시작하기 전에 설계상의 대안을 제시한다.

### 2. 무분별한 코드 생성을 금지한다.
- 요청한 기능의 최소 범위만 수정한다.
- 별도 요청이 없다면 관련 없는 리팩터링을 하지 않는다.
- 새로운 파일과 의존성을 임의로 추가하지 않는다.
- 한 번의 작업에서 수정하는 파일 수를 최소화한다.

### 3. 학습을 지원한다.
- 핵심 함수의 입력, 처리 과정, 출력 및 예외 상황을 설명한다.
- 수업에서 배운 개념과 연결되는 코드를 표시한다.
- 중요한 알고리즘은 의사코드와 작은 데이터 예제로 먼저 설명한다.
- 내가 직접 구현해 볼 부분과 Claude가 구현할 부분을 구분한다.

### 4. 테스트와 검증을 함께 진행한다.
- 새로운 함수에는 단위 테스트를 제안한다.
- 정상 입력과 경계 조건, 실패 상황을 확인한다.
- 기존 기능에 영향을 주는지 회귀 테스트를 수행한다.

### 5. 작업 완료 후 요약한다.
- 변경한 파일과 이유
- 새로 추가된 함수 및 데이터 흐름
- 핵심 기술 개념
- 내가 직접 확인해야 할 내용
- 다음 단계의 의존 관계

목표는 코드가 생성되는 속도가 아니라, 내가 해당 코드를 이해하고 변경할 수 있는 능력을 높이는 것이다.
