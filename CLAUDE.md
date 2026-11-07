# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**song-lingo** — 외국어 노래 문장 연습 도우미 (듣고 따라읽고 받아쓰고 확인하는 음성 학습 프로토타입). ICT 혁신 스퀘어 Voice-AI 부트캠프의 **개인 프로젝트**(2026-10-30 ~ 11-11 평일 9일 × 4h = 36h 개발, **11-12 발표**). 사용자가 TTS 기준 음성을 듣고 → 따라 읽은 녹음을 STT로 인식하거나 받아쓰기를 하고 → 정답과의 **오류율(WER/CER)** 과 틀린 부분을 피드백받는다. 점수는 **발음 점수가 아니라 "문장 인식 일치도"** 다(STT가 틀린 발음을 문맥으로 고쳐 적을 수 있음). 시연 화면은 **Jupyter 노트북(`experiments/practice.ipynb`)** 이다. 웹 UI는 **Streamlit**(`app/`, 가사 입력·내 노래·기록 3페이지, 11-05 구현; 검토 문서 16.4·16.10·16.11)이고 배포 호스트는 Oracle VM 쪽으로 기울었으나 **미확정**(검토 문서 16.13). `spike/`의 FastAPI 서버는 브라우저 녹음 점검용 임시 코드다.

**현황(진행 상황·남은 L1·이슈 번호)은 여기에 적지 않는다.** `docs/작업_일지.md`와 GitHub 이슈를 본다. README는 마일스톤(L1 완료·L2 완료·마지막 정리)마다 갱신한다.

| 문서                                    | 무엇이 있나                                                                                                                                                                                               |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/프로젝트 개발 계획서_20261030.md` | **결정된 내용**(L1 필수 → L2 확장 → L3 선택, 일정·성공 기준·축소 규칙). 사용자가 직접 정리해 강사님께 공유하는 글이므로 **임의로 바꾸지 말고**, 고칠 때는 큰 흐름과 문체를 유지하며 필요한 부분만 고친다. |
| `docs/프로젝트_안내_및_주제_검토.md`    | 검토·근거·옵션 비교(주제별 9~16장, 변경 이력 9.1, 옛 8.x 번호는 17장 대응표). 이 저장소에서 이어 쓰는 원본. **새 판단은 8장에 잇지 말고 주제에 맞는 장(9~16)의 새 절로 넣는다.**                          |
| `docs/작업_일지.md`                     | 하루 작업 로그, 파일별 역할·읽는 순서, 이슈 정리, 용어 메모(사용자가 Notion으로 복사해 면담에 씀).                                                                                                        |
| `docs/프로젝트 개발 계획서_20261029.md` | 20261030으로 정리하며 빠진 내용의 보관본. A절 "1일차에 확인할 항목"을 점검해 결과는 검토 문서에 기록. L3 기호는 20261030과 다르다.                                                                        |

검토 문서의 절 안내: 코드 구조·검증·주석 9.4, README 갱신 시점 9.3, `quality.py` 기준값 14.3, 일정 재조정·웹 UI 결정 시점 10.8, 외부 검토 반영 12.2, 면담 결과 12.3, 연습 문장 13.2, TTS·WAV 헤더 15.1, 모델 크기 비교 15.2, API 키 확인 15.3, 웹 UI 결정·`audio.py` 활용 16.4, Demucs(음원 분리) 기술 검토 15.4, 노래 비교 실험 13.5, 웹 UI 16.1·16.2. 그 밖에 `experiments/WER, CER/연습_문장_데이터_설명.md`(연습 문장 10개), `experiments/skeleton/발표_대본_초안_스켈레톤.md`(3분 발표 초안), `experiments/skeleton/주말_스켈레톤_시연_계획.md`(끝난 스켈레톤 계획), `docs/개발환경_이슈노트.md`(환경·git 문제와 해결책 — 새 문제가 생기면 번호를 이어 추가), `experiments/song vocals/노래_구간_비교_실험_절차.md`(곡 구간 분리·정답·비교 실험을 따라 하는 순서와 결과 기록, 이슈 #18)가 있다.

- 학습 배경(1~7강 노트북)은 형제 폴더 `../ict_innovation_sq_voice_ai/`(읽기 전용 참고). 특히 `017_sound/lesson07_whisper_minimal.ipynb`(faster-whisper), `013_openai_api/`(TTS/STT 호출 코드), `017_sound/02·03·lesson04`(WAV 전처리, FFT/STFT/Mel). WER·CER은 수업이 아니라 자습 노트북(`experiments/WER, CER/WER_CER_이해하기.ipynb`) 기준이다.

## Environment

- **conda 환경 `voice-ai` 하나만 사용**: `/opt/anaconda3/envs/voice-ai/bin/python` (Python 3.11). 다른 환경(`base` 등)은 쓰지 않는다. 노트북 커널도 `voice-ai`(`Python 3.11 (voice-ai)`).
- `numpy`는 **1.26.4 고정**(TensorFlow 2.16). 새 패키지는 설치 전 **`pip install --dry-run`** 으로 numpy가 바뀌지 않는지 확인한다. 노트북에서는 `%pip` 또는 `!{sys.executable} -m pip`.
- 설치된 것: faster-whisper 1.2.1(디코더 PyAV `av`를 함께 설치함), openai, python-dotenv, pandas, scipy, matplotlib, `sounddevice` 0.5.6(마이크 녹음, `recorder.py`·`scripts/record_takes.py`), `demucs` 4.1.0(보컬 분리, `separate.py`; torch 2.2.2 CPU), 그리고 `spike/`용 fastapi·uvicorn·python-multipart. **없는 것**: `pytest`, `streamlit`(**`voice-ai`에 설치 금지**: protobuf가 TensorFlow 2.16과 충돌. 앱은 **별도 환경 `~/venvs/song-lingo-app`**(프로젝트 폴더 **밖**: `~/Documents`는 iCloud 동기화 대상)에서, 패키지는 `app/requirements.txt`(`pyarrow==21.0.0` 고정: 26은 NumPy 2 요구). 새 환경의 첫 import는 macOS 검사로 몇 분 걸릴 수 있음; 검토 문서 16.4, 이슈노트 #20·#21), `gradio`, `ipywidgets`, `soundfile`, `librosa` (노트북 셀에서는 녹음하지 않고 **미리 녹음한 파일 경로를 지정**; 녹음은 터미널의 `scripts/record_takes.py`로 한다. 마이크 권한이 필요해 Claude는 실행하지 않고 사용자가 직접 실행). 테스트는 표준 라이브러리 `unittest`를 쓴다. macOS에는 `timeout` 명령이 없으므로 시간 제한은 파이썬 `faulthandler.dump_traceback_later(초, exit=True)`로 건다.
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
$PY scripts/check_notebook.py                 # experiments/practice.ipynb 코드 셀을 차례로 실행해 끝까지 되는지 점검(.env 안 읽음 → API 과금 없음, 그림은 results/notebook_check/)
$PY scripts/scan_outputs.py [노트북 ...]      # 커밋 전: 노트북 출력의 오디오 플레이어·/Users 경로·key 검사
$PY scripts/check_api_key.py                  # 어떤 OPENAI_API_KEY가 적용되는지(값은 가림). .env를 읽으므로 Claude는 실행하지 않고 사용자가 직접(`! ...`)
$PY scripts/record_takes.py [--status|--order sentence|--redo ID TAKE]   # 터미널에서 문장을 보며 data/recordings/sNN_takeK.wav로 녹음(스테레오 PCM16). 기본은 없는 건만 1회전씩. 마이크가 필요하므로 사용자가 직접(검토 문서 13.3, 사용법은 experiments/WER, CER/연습_문장_데이터_설명.md 5.1)
$PY scripts/separate_clip.py [--list|--song N --start S --duration D --id cNN [--cut-only]|--id cNN --separate-only]   # 내 곡(data/songs/en)의 한 구간을 자르고(--cut-only, 몇 초) 들어 확인한 뒤(--separate-only) Demucs로 보컬 분리, data/song_work/에 저장(처리 시간·RMS만 출력, 가사는 출력 안 함). 분리는 20초에 CPU 1~2분(검토 문서 13.5)
$PY scripts/compare_clips.py [--ids c01 …] [--sizes tiny base small] [--vad off|on|both] [--temperature 0.0|default …] [--repeats N]   # 노래는 같은 입력도 결과가 흔들려(온도 폴백) 주 결과는 --temperature 0.0, 확인용은 default를 --repeats 3으로. 구간별 정답(data/song_work/truth/<id>.txt)이 있을 때 원곡/보컬 × 크기 × VAD 인식·WER/CER 비교(#18). 인식 문장(가사)은 results/song_compare/texts.csv에만 저장
SONGLINGO_SEPARATE_PYTHON=/opt/anaconda3/envs/voice-ai/bin/python ~/venvs/song-lingo-app/bin/python -m streamlit run app/streamlit_app.py   # 웹 앱(앱 전용 환경, 메뉴 3개: 내 문장·내 노래·기록). 서버는 끝나지 않으므로 Claude는 백그라운드로 띄우고 http://localhost:8501에서 연다(`!`로는 출력이 안 보임, 이슈노트 #23). `.streamlit/config.toml`을 고치면 서버를 다시 띄운다. 보컬 분리는 `SONGLINGO_SEPARATE_PYTHON`의 파이썬이 별도 프로세스로 돌린다(앱 환경에 torch·demucs가 없음, 이슈노트 #24)
$PY -m uvicorn spike.server:app --host 127.0.0.1 --port 8000   # 브라우저 녹음 점검용 임시 서버(내 Mac 안에서만)
```
`tests/test_check_notebook.py`는 스크립트를 실제로 실행해 전체 테스트가 10초 안팎 걸린다. 노트북은 VS Code 또는 `jupyter notebook`에서 연다(커널 `voice-ai`). 빌드/린트 도구는 없다.

## Architecture

한 문장 연습의 데이터 흐름(모듈은 프로젝트 루트에 나란히 있는 flat 구조; `songlingo/` 패키지로의 정리는 이슈 #24, 판단은 9.4):

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
- **입력은 경로뿐 아니라 bytes·`BytesIO`도 받는다**(웹 업로드·브라우저 녹음용, 이슈 #37): `audio.load_raw`·`load_audio`·`decode`, `stt.recognize`·`recognize_words`, `quality.check_file`, `practice.read`. STT에는 **경로나 bytes를 그대로** 넣는다. 우리 `audio.py`가 16 kHz로 바꾼 배열을 넣으면 faster-whisper가 직접 바꾼 것과 파형이 조금 달라, 말소리 30건은 같았지만 노래 구간(원곡, tiny, `temperature=0.0`)은 14개 중 10개의 인식문이 달라졌다(검토 문서 16.4). 배열 입력은 지원하지만 결과를 경로와 맞춰야 할 때는 쓰지 않는다.
- `recorder.py`는 마이크 녹음과 `sNN_takeK.wav` 저장(`Recorder.start()/stop()`, `save_wav`, `take_status`)만 하고 화면을 모른다. 터미널 진행은 `scripts/record_takes.py`, 나중의 웹 화면도 같은 `Recorder`를 부른다. 녹음 파일의 STT 입력용 리샘플링은 faster-whisper가 안에서 하고(`audio.py`는 상태 점검·그림용, 검토 문서 14.6), 영어 채점은 `scoring.normalize(unify=True)` 기본 + `unify=False` 엄격 모드(검토 문서 13.4).
- `separate.py`는 내 곡의 구간 디코딩(`audio.load_raw` 재사용), 자르기(`cut_clip`)와 Demucs 보컬 분리(`separate_clip`)를 따로 부를 수 있게 하고(`process_clip`은 둘을 잇는 편의 함수), 저장만 한다(이슈 #18; `demucs`는 `sphn` 빌드 실패로 `pip install --no-deps`로 설치, 개발환경 이슈노트 #14). 곡·결과는 `data/songs`, `data/song_work`(git 제외)에만 둔다.
- **노래 구간 → 연습 줄 흐름(이슈 #31)**: `stt.recognize_segments`(구간 시각·신뢰 지표, 노래용 기본은 VAD 끔·경로 그대로) → `song_lines.split_into_lines`(구간을 한 줄로, 길면 단어 사이 쉼에서 분할·짧으면 병합, 기본 6초·14단어) → `song_practice`(`prepare_lines`가 `data/song_practice/<id>/lines.json` 저장, `apply_edits`로 사람이 고친 가사 반영(`stt_text`는 원문 보존, **이미 있으면 덮어쓰지 않음**), `make_tts`는 기본이 호출 없는 계획 모드이고 `generate=True`일 때만 OpenAI TTS 호출·과금). **주의**: faster-whisper의 `avg_logprob` 등 신뢰 지표는 30초 창 하나의 값이라 한 클립의 모든 구간이 같은 값이므로 줄별이 아닌 **클립 단위 힌트**(`low_confidence`)로만 쓴다. 확인·수정은 노트북 `experiments/song practice/song_practice.ipynb`(출력에 곡 소리·가사가 들어가므로 정리본만 커밋), 작업 기록은 `experiments/song practice/곡_구간_연습문장_만들기_작업기록.md`. 줄 단위 보컬 조각(#32)은 아직 없다.
- **웹 앱(Streamlit, 검토 문서 16.10·16.11)**: `app/streamlit_app.py`가 `st.navigation`으로 페이지 3개(메뉴 이름 **내 문장**(11-05에 "가사 입력"에서 변경, 파일은 `app/views/lyrics.py`)·**내 노래**(`song.py`)·**기록**(`history.py`))를 연결하고, 화면 코드는 위젯 배치만 한다. 계산은 루트 모듈: `web_song.py`(업로드·파형 윤곽·구간 자르기·줄 인식·확정·보컬 분리, 세션 임시 작업 폴더 `songlingo_*`에만 저장), `web_practice.py`(prep 만들기·TTS 캐시 확인·결과 카드/단어 대조 HTML, 사용자 글은 `html.escape`), 따라읽기·받아쓰기 화면 부품은 `app/ui_practice.py`(두 페이지가 공유; 채점 때마다 `practice_log.py`가 `results/practice_log.csv`에 **문장 글 없이** key·점수만 기록(11-07 결정으로 사용자별 저장이 구현되면 바뀐다, 검토 문서 16.16), 따라읽기 결과 아래에 `web_practice.error_spans`(틀린 구간 표시, `practice.locate_errors` 재사용)와 `visualisation.plot_sound_panels`(파형·FFT·STFT·Log-Mel 2×2; FFT는 수업 방식의 `fft_spectrum`) 표시). `azure_pronunciation.py`는 Azure 발음 평가 래퍼(`parse_assessment`는 키 없이 테스트하는 순수 함수, `assess`는 녹음 → 16 kHz PCM16 푸시 스트림 → `recognize_once`; SDK는 앱 환경에만 있고 함수 안에서 처음 불러온다; 운율·음절·들린 음소·음소 이름은 en-US 중심, 음소 기호는 지정하지 않으면 SAPI라 `phoneme_alphabet="IPA"`로 요청; 종합 점수는 낮은 점수에 큰 가중치(0.4·s0+0.2·s1+0.2·s2+0.2·s3, `expected_pron_score`로 검증); 일본어·프랑스어 지원은 미확인; 공식 문서 대조는 검토 문서 14.7의 10절; **Azure에는 녹음·기준 문장 글·로캘만 보내고 TTS 소리는 보내지 않으며, 평가 기준은 TTS가 아니라 Azure의 원어민 발음 모델이다**, 11절), 화면은 `app/ui_practice._show_azure`(결과 카드·단어별 점수는 `web_practice.azure_*_html`). 테마는 `.streamlit/config.toml`(색은 `theme.py`의 `BUTTON_GREEN`·`PURPLE`·`LIME` 등과 `tests/test_theme_config.py`로 일치 확인; **글꼴 설정에는 Google Fonts 주소를 하나만**, 둘 이상이면 세션이 안 만들어져 Connection lost, 이슈노트 #22). **접근 제한(이슈 #52)은 `access.py`(판단)와 `app/streamlit_app.py` 맨 위의 비밀번호 화면: 환경변수 `SONGLINGO_PASSWORD`가 있을 때만 켜지고(없으면 개발용으로 바로 열림), 모든 페이지 앞에서 `st.stop()`으로 막는다. 세션별 잠금뿐이라 서버 앞단의 속도 제한과 긴 비밀번호가 함께 필요하다.** **주소는 내 문장 `/text`, 내 노래 `/clip`(11-08에 `/song`에서 변경), 기록 `/history`(Streamlit은 기본 페이지 주소를 `/`로 고정하므로 보이지 않는 기본 페이지가 내 문장으로 보냄), 로고는 `app/assets/logo.png`(시안 A를 잘라 배경을 투명하게 한 PNG, `st.logo`). 내 문장은 입력 → 언어 알아보기 → 줄마다 네/아니오/모르겠어요 → 연습 순서이고, 일본어·중국어는 WER 대신 CER을 보며(WER은 문장 전체가 1단어가 됨) 일본어는 Azure 평가를 주로 본다. 라틴 문자 줄의 언어는 낱말·특징 글자 점수로 제안한다(`languages.detect_latin_language`).** **일본어는 `japanese.py`(`pykakasi`)로 한자·가타카나를 히라가나 읽기와 로마자로 바꿔 보여 주고 기준·인식을 읽기로 바꿔 채점한다(`web_practice.apply_japanese_reading`, 영어 단어는 안 바뀜). 한글 뜻·**표현 설명**(단어·IPA·표현·문법·예문 2개, JSON, 이슈 #58)은 `meaning.py`(예시는 직접 쓴 뜻, 그 밖은 버튼으로 OpenAI·캐시 `data/meaning_cache/`; 모델 `gpt-4o-mini` 호출은 **확인 전 [미확인]**; 화면은 `ui_practice.meaning_group`·`notes_box`). 화면 요소별 "어떻게 동작하나요?" 라임색 설명 상자는 `app/explain.py`(`TEXTS` 키와 화면 호출은 `tests/test_explain_keys.py`로 맞춤, 이슈 #56). 보컬 분리는 화면을 막지 않는 백그라운드(`web_song.start_vocals`·`vocals_status`, 화면은 `st.fragment(run_every)`로 확인). 구간 슬라이더는 곡 전체 범위(파형 가로축과 같음), 미리 듣기는 원본을 `st.audio(start_time, end_time)`로.** **내 노래의 입력은 파일 업로드와 마이크 녹음(`st.audio_input`, 주변 음악 녹음, 이슈 #51) 두 가지이며 `(이름, bytes)`로 합쳐 같은 흐름을 탄다(녹음은 전체가 구간, 길이 제한 없음, `web_song.recording_info`는 `quality.check_file` 재사용).** **내 노래는 인식된 가사를 확정 없이 바로 연습할 수 있다(방식 C, 고치면 저장, 연습에서 뺄 줄만 뺌; 표준 발음은 지금 보는 한 줄만 만든다). 사용자가 붙여넣은 상업 가사는 예시 문장·코드·문서에 넣지 않는다(직접 쓴 문장만).** **언어(이슈 #50, 검토 문서 16.14)**: `languages.py`가 언어 표(이름·Azure 로캘·공백 여부)와 규칙을 한곳에 둔다. 내 문장은 **줄마다** 글자 수가 가장 많은 문자 체계로 언어를 **제안**(가나 → 일본어, 한글 → 한국어, 라틴 문자 → 영어로 가정)하고 그 줄만 바꾸는 선택 칸을 둔다. `multilingual=True`는 30초 창마다 재감지하고 `language`를 덮어써 10~20초 구간에서는 효과가 없다(소스 확인). 내 노래는 구간을 정한 뒤 `stt.detect_language`로 **제안 → 사용자 확인(네/아니오+선택/모르겠어요)** 을 거쳐 `languages.stt_options`가 `recognize_segments`의 `language`·`multilingual`을 정한다(감지는 앱이 지원하는 언어 안에서만 순위를 매김). 일본어·중국어는 공백 없이 이어 줄을 만들고 채점은 CER 중심이며, 줄 데이터(`lines.json`)에 `languages`·`lang`이 기록된다. 앱은 TTS를 자동으로 부르지 않고 버튼으로만 부른다(`practice.prepare` 대신 `web_practice.make_prep`).
- 다른 파일: `theme.py`(그래프 공통 색·스타일), `sentences.csv`(id, lang, sentence, meaning_ko, source, license, probe; 10문장, 문장별 의도는 `probe` 열과 `experiments/WER, CER/연습_문장_데이터_설명.md`), `spike/`(임시 웹 점검), `scripts/`, `tests/`(모듈마다 `test_*.py`, 합성 신호만 사용). `clip_compare.py`(구간별 정답과 비교하는 노래 인식 실험 도구: 원곡/보컬 × 모델 크기 × VAD × temperature × 반복, `scripts/compare_clips.py`가 부름, `practice.py`와 분리), `experiments/`(**작업 과정·실험은 모두 여기**, 주제별 하위 폴더: `practice.ipynb`(시연 화면)·`song vocals/`·`WER, CER/`·`skeleton/`; `docs/`에는 프로젝트 전체 문서만 둔다. 노트북은 위로 올라가며 루트(`practice.py` 등)를 찾아 `chdir`·`sys.path`를 맞추는 셀로 시작한다. 실험 노트북: 지금은 `song vocals/song_vocal_separation.ipynb`, 실험 절차·기록은 `experiments/song vocals/노래_구간_비교_실험_절차.md` — 실험 상세는 검토 문서가 아니라 여기 12절). 아직 없는 계획 모듈: `player.py`(L2; 재생 속도). **이름 주의**: 루트 `explain.py`는 만들지 않았다 — LLM 뜻·표현 설명은 `meaning.py`에, 화면 설명 상자 글은 `app/explain.py`에 있다, 소리 대 소리 발음 평가 `pronunciation.py`(설계만 있음, 검토 문서 14.7; **구현 전에 설계 승인 필요**).
- `data/`(녹음·TTS 캐시·업로드)와 `results/`(기록 CSV·그래프·노트북 점검 그림)는 **git에서 제외**된다.

## Key decisions (자세한 근거는 docs 두 파일)

- **STT**: 기본 로컬 `faster-whisper tiny` (`device="cpu"`, `compute_type="int8"`, `beam_size=1` — 7강 설정, 결과 보고 때 `stt.settings()`로 설정을 함께 기록), 인식 언어는 `en`으로 고정(시연은 영어 문장만). **모델 크기는 `stt.recognize(model_size=)`로, VAD(말소리 없는 구간 걸러내기)는 `vad_filter=`로 바꿔 비교한다**(기본은 `recognize` 끔·`recognize_words` 켬이라 두 경로 설정이 다르다. `tiny`에서는 결과가 같지만 `small`에서는 달라진 사례가 있어, 기본 모델을 바꿀 때 통일한다)(11-02 면담: 모델을 올려 보기). 기본은 `tiny`(기준선)를 유지하고, `model_compare.compare_models`(모델 크기 비교 실험 도구, `practice.py`와 분리)로 같은 녹음을 여러 크기에 돌려 본 뒤 기본 모델을 정한다(`stt.available_models()`가 `models/`에 내려받아 둔 모델을 자동으로 찾고, 노트북의 `DOWNLOAD_MORE`로 더 내려받음; 검토 문서 15.2; 노트북 S8). 큰 모델은 틀린 발음을 문맥으로 더 고쳐 적을 수 있어 "발음 점수가 아님"에 유의. **노래 구간(내 곡 로컬 처리)의 STT는 `medium` + 원곡 + VAD 끔 + 기본 설정(폴백 켬)으로 한다**(11-03 비교: `medium`은 원곡이 보컬보다 낫고 빠름 micro WER 0.177 대 0.257; `base`는 분리한 보컬이 나음; 원곡에 VAD를 켜면 가사가 통째로 지워지고 `temperature=0.0`은 반복 루프를 낳음; 노래에서는 `recognize_words(vad_filter=False)`를 명시; 분리는 선택 기능이고 용도는 두 가지: 학습자용 기준 음성(#32)과, 11-05에 정한 UI의 **"보컬만 듣기"**(반주를 뺀 원어민 발음을 들어 보는 듣기 보조, 따라 부르기가 아님; 검토 문서 16.10); 검토 문서 13.5·15.2). OpenAI STT는 대체·비교용. **TTS는 OpenAI(`gpt-4o-mini-tts`, voice `alloy`)로 고정.** 6강에서 만든 Keras 모델은 제품 STT로 쓰지 않는다.
- **채점**: `(S+D+I)/N`. 영어 정규화 = NFC → 소문자 → 구두점 제거(아포스트로피 유지) → 공백 정리 → **표기 통일**(축약형 펼치기 `we're→we are`, 0~99 숫자 단어→숫자 `twenty→20`; `'s`·`'d` 제외; 양쪽에 같은 규칙; 기본 켬, `normalize(unify=False)`로 엄격 채점; 이슈 #3 확정, 검토 문서 13.4; **점수를 보고할 때는 어느 쪽인지 적는다**). 정답이 비면 오류. **WER은 1을 넘을 수 있으므로 "일치율(1−WER)"로 표시하지 말고** 오류율과 S·D·I 개수로 표시. 틀린 부분은 `difflib` 비교가 아니라 **편집 거리 역추적**으로 구한다(`difflib`은 최소 경로를 보장하지 않음; `difflib`은 동률일 때 단어 유사도 점수에만 쓴다). 일본어는 CER 중심. 프랑스어 악센트 방침은 **아직 미확정**(`normalize(strip_accents=)`로 열어 둠).
- **녹음 입력 상태 점검(`quality.py`)** 은 음량·무음·클리핑·말한 시간만 본다(잡음 판정이 아님). 기준값은 2026-11-01에 본인 녹음으로 **확정**했다(근거 표는 `quality.py` 맨 위와 검토 문서 14.3): 너무 작음(RMS < −55 dBFS 또는 최대 진폭 < 0.02), 클리핑(**원본** 샘플 0.999 이상 ≥ 1%; 리샘플링 뒤 값으로 재면 울림 때문에 오판), 대부분 무음(STFT 프레임 에너지가 최대 프레임보다 35 dB 이상 낮은 프레임 ≥ 80% — **절대 기준이 아니라 상대 기준**), 말한 시간 < 1.0초, 길이 < 0.5초. 경고가 있어도 인식·채점은 계속한다. Whisper tiny는 소리 크기에 매우 강했다(표본 1명). 잡음 환경은 미시험.
- **L3 기본안은 (a) 노래 구간 인식 + 음악·음성 분리**(강사님 권유; 분리 없는 낭독 vs 노래 CER 비교가 최소 구성). 막히면 (e) 잡음 견고성. 분리 모델(Demucs)은 `--dry-run` 확인만 했고 CPU 속도는 **미확인**. 실험은 시드를 바꿔 **3회 이상** 반복해 평균·범위를 보고하고, 합성 흰 잡음 결과를 실제 환경으로 일반화하지 않으며, 모든 녹음이 본인 한 명이라는 한계를 명시한다.
- **웹 UI 방향(11-04 면담·결정, 검토 문서 16.9)**: **UI를 먼저** 만든다(Streamlit, MVP 메뉴는 Practice와 History). 시안 팔레트는 `theme.py`와 같고(`#1a9f4c`·`#fcfcfb`·`#0b0b0b`), **틀린 단어는 보라 `#6250d6` + 밑줄, 빨강은 쓰지 않는다**(Streamlit `redColor` 계열 테마도 보라로 바꿈). 로고는 사용자가 외부에서 만들어 옴(그때까지 없음). `app/references/`(시안·손그림)는 커밋하지 않는다(`.git/info/exclude`). TTS wav는 스트리밍 저장이라 헤더 길이가 `0xFFFFFFFF`(wave 모듈이 2.75초를 89478초로 읽음)인데, `tts.tts_wav`가 저장 직후와 캐시 적중 때 `fix_wav_header`로 고쳐 두므로 `st.audio`에 그대로 넘겨도 된다(폴더 전체는 `tts.fix_wav_headers()`). 추가 STT 실험은 하지 않기로 했고(원곡 대 보컬은 확정 못 함) 발표는 시행착오를 있는 그대로 공유한다.
- **지연 시 축소 순서(L2)**: ① LLM 뜻·표현 → ② 재생 속도·±5초(기본 `Audio` 플레이어로 대체) → ③ 오류율 그래프 → ④ 기록 CSV, **받아쓰기는 마지막까지 유지**(받아쓰기는 스켈레톤에서 이미 앞당겨 구현됨). L3는 항상 선택.
- **그래프 색은 초록 계열로 통일**하고 공통 설정은 `theme.py`에 둔다(근거·검증은 검토 문서 14.4): 그림 전에 `theme.apply_style()`, 스펙트로그램·Log-Mel은 `CMAP_SPEC`, 흰 바탕 히트맵은 `CMAP_HEAT`, 시리즈는 `SERIES` 순서대로 **한 그림 최대 4개**(초록 옆에 주황 금지), 모든 쌍이 이웃하는 그림(산점도 등)은 초록+파랑 2개까지. 파형 그래프만 수업과 같은 기본 파랑(`theme.WAVEFORM`)을 직접 지정한다(`apply_style()`가 색 순환을 초록으로 바꾸기 때문). 색을 새로 정하면 `validate_palette.js`(dataviz 스킬)로 검증하고, `magma`·`Greens_r` 같은 라이브러리 기본 cmap을 그림마다 직접 쓰지 않는다.
- 방향: 이 프로젝트는 **수업(음성 1~7강 + 013) 복습·활용 수단**이기도 하다.

## Privacy / security (공개 저장소 전제)

- `.env`, API key, **사용자 본인 목소리(녹음)**, 강사님 목소리, 강사 제공 WAV, 모델 파일, 화면 캡처(다른 수강생 이름·얼굴)는 **절대 커밋하지 않는다**. **사용자 실명은 어떤 파일명·내용에도 쓰지 않는다.**
- **상업 노래의 가사·음원**(내 보유곡, `data/songs`)은 **저장소·이슈·PR·문서에 올리지 않는다**(결과는 곡 번호와 숫자로만 적고 가사를 옮겨 적지 않는다). **11-04 변경(사용자 결정, 검토 문서 13.5): 가사를 외부 API(OpenAI TTS·LLM)로 보내는 것은 허용한다.** 이전의 "보내지 않는다" 규칙은 오해에서 나온 것이었고 #18을 프로젝트 핵심으로 올리면서 폐지했다. 그 결과물(가사로 만든 TTS 음성, LLM 설명, 인식된 가사)도 `data/`(git 제외)에만 두고 저장소·이슈·PR·문서에 올리지 않는다. **11-05 변경(사용자 결정, 검토 문서 16.10): "내 노래" 모드도 배포 버전에 만든다.** 사용자가 **실행 중에 자기 곡을 업로드**해 처리하는 것은 허용하되, ① 곡 파일·가사·가사로 만든 결과물은 **저장소에 두지 않고**(코드·문서·이슈·PR·커밋 어디에도) 서버에서도 **세션이 끝나면 지우는 임시 저장**을 기본으로 한다(영구 저장은 사용자가 정하기 전까지 하지 않음 → **11-07에 사용자가 정함, 아래 "11-07 변경"**) ② 배포 앱은 **접근 제한(비밀번호)** 을 건다(공개 주소에서 누구나 TTS·LLM·STT를 불러 과금·곡 업로드를 하지 못하게) ③ 로그·`print`·오류 메시지에 가사를 남기지 않는다 ④ 배포 서버에서 `medium` STT와 Demucs가 돌 수 있는지는 **미확인**이라 호스트를 정하기 전에 측정한다. **11-07 변경(사용자 결정, 검토 문서 16.16 — 설계 단계, 구현 전): 사용자별 서버 저장을 허용한다.** 아이폰에서 브라우저를 닫아도 이어서 쓰도록, **내 곡에서 뽑은 가사(STT)·고친 가사·구간 정보(시작·길이)·한글 뜻·표현 설명·내 문장·채점 결과(WER/CER, Azure 평가, 인식문·내 답 포함)** 를 **보관 코드(사용자별 열쇠)** 로 나눠 서버의 `data/`(git 제외, DB를 쓰면 그 파일)에 **계속 보관**하고 **사용자가 원하면 직접 삭제**한다(저장 기본값은 켜짐, 끌 수 있고 화면에 "서버에 저장된다"고 알린다). **그대로 지키는 것**: ① 가사·곡 이름·결과를 저장소·문서·이슈·PR·커밋·**로그·오류 메시지**에 올리거나 남기지 않는다(상업 가사 규칙 그대로) ② **업로드한 음원, 잘라 낸 구간 wav, 보컬 분리 결과, 내 녹음은 저장하지 않는다**(후속으로 사용자가 직접 켜는 선택 저장을 검토할 수 있으나 기본은 저장 안 함) ③ 접근은 비밀번호 뒤에서만, 사용자끼리 분리 ④ 경로 조작·사용자 간 누출이 없게 단위 테스트로 확인. 이 결정이 구현되기 전까지 현재 동작(임시 폴더 + `practice_log.csv`에 문장 글 없이 key·점수만)은 그대로다. **11-08 변경(사용자 결정, 검토 문서 16.17): 가사에서 만든 한글 뜻·표현 설명을 서버 DB의 공유 테이블 `meanings`에 저장해도 된다**(문장 글은 저장하지 않고 글+언어의 해시 키와 설명만, 내부 로직에서만 사용하고 저장소·문서·로그에는 올리지 않는다). 11-03 조정(검토 문서 13.5): ① 내 컴퓨터에서 로컬로 처리하는 **개인 학습 도구**(Demucs 분리 + 로컬 Whisper)는 허용 ② **발표 시연에서 곡 1개를 로컬 재생**하는 것은 허용(저장소·슬라이드에는 음원 없음) ③ **Claude가 사용자의 허락 아래 인식된 가사 텍스트를 읽고 분석**(오류 분류·CER 계산·코드 확인)하는 것은 허용하되, 문서·이슈·PR·채팅 답변에 가사를 옮겨 적지 않는다. 연습 문장 기본은 여전히 직접 쓴 예문 또는 이용이 확인된 공개 문장이다. 계획서의 합성 반주 실험(L3-(a)의 직접 부른 노래+허용 반주)을 할 때는 이용 조건을 기록한다.
- **사용자 녹음의 외부 전송(11-05 사용자 결정, 검토 문서 14.7의 7절)**: 따라읽기 녹음을 **Microsoft Azure Speech(발음 평가)로 보내는 것은 시연·발표용 옵션으로 허용**한다. 단 ① **사용자가 "Azure로 평가하기" 버튼을 누를 때만** 전송(자동 전송 금지) ② 화면에 전송 안내를 적는다 ③ 녹음을 서버 디스크에 저장하지 않는다(푸시 스트림) ④ 키·지역(`AZURE_SPEECH_KEY`·`AZURE_SPEECH_REGION`)은 `.env`에만 두고 Claude는 `.env`를 읽지 않는다(실제 호출은 사용자가 실행). 다른 외부 서비스로 녹음을 보내려면 사용자 승인을 따로 받는다.
- **노트북 출력**에는 `<audio>` 플레이어(base64 음원), `/Users/…` 경로, key가 박힐 수 있다. 커밋 전에 출력을 지우고 `scripts/scan_outputs.py`로 확인한다. 로컬 원본(출력 있음)은 그대로 두고 **출력을 지운 정리본을 커밋**한다: 정리본을 임시 파일에 만들어 스캔한 뒤 `git hash-object -w` → `git update-index --cacheinfo 100644,<hash>,experiments/practice.ipynb`로 인덱스에 넣는다(그래서 `git status`에 `M practice.ipynb`가 계속 남는 것은 정상).
- `git add -A`, `git add .` 금지 — 파일을 하나씩 추가하고 `git status`로 확인한다. 최종 점검 체크리스트는 계획서 6장 9일차 항목.
- `spike/` 서버는 `127.0.0.1`에서만 열고, 업로드 녹음은 git 제외 폴더 `data/uploads/`에 두며, `.env`·TTS·LLM을 쓰지 않는다. 인터넷에 배포하면 공개 주소에서 누구나 TTS를 불러 과금되므로 접근 제한(비밀번호)이 필요하다(Streamlit 앱도 같다, 내 노래 모드 포함).

## Working agreements (사용자와의 합의)

- 채팅은 **친근한 반말**. 문서(md, 노트북 설명 셀)는 "~입니다" 문체를 유지한다.
- **프로젝트 판단·옵션 비교·질문 답변은 채팅에만 남기지 말고 `docs/프로젝트_안내_및_주제_검토.md`에 먼저 기록**하고, 계획서에는 **결정된 내용만** 적는다. 계획서를 고치면 검토 문서 9.1 변경 이력에 한 줄 추가한다.
- **실험·확인은 방법과 코드를 알려 주고 사용자가 직접 실행**하게 한다. 내가 돌린 값은 "참고 baseline"으로 표시하고 해석을 돕는다. 헤드리스로 돌린 노트북 확인은 참고일 뿐 최종 확인은 사용자가 VS Code에서 직접 실행하는 것이다.
- 코드·문서의 숫자와 동작 주장은 **실행해서 확인**하고, 추정은 **[추정]**, 일반 지식은 **[일반 지식]**, 못 한 확인은 **[미확인]** 으로 표시한다(사용자가 이 문서들로 공부한다).
- **커밋은 주제별로, 사용자가 확인한 뒤에만**. 가능하면 적은 수의 큰 커밋. push는 사용자가 요청할 때만(**예외: 문서(md)만 바뀐 커밋은 `main`에서 바로 commit하고 push한다**, 11-04 사용자 허락. 코드·노트북이 섞이면 브랜치 → PR). 직접 커밋에는 세션의 `Co-Authored-By` 트레일러를 넣고, 관련 이슈는 메시지에 `Refs #N`으로 적는다. 한국어 `feat:`/`docs:`/`chore:` 메시지 관례(학습 저장소와 동일).
- 칸반은 GitHub Projects(`song-lingo` 보드), 작업은 **이슈 1개 = 카드 1개(L1/L2/L3 라벨; 문서는 `docs`, 기타는 `enhancement`)**. 새 작업이 생기면 이슈를 등록하고 보드에 올린 뒤 그에 맞춰 작업한다. 이슈는 완료 기준 대비 상태를 댓글로 남기되 **닫는 것은 사용자가 판단**한다. `gh`에 `gh project`가 없어 보드는 `gh api graphql`로 조작한다(project id `PVT_kwHOBTa5js4BpeHY`, Status 필드 `PVTSSF_lAHOBTa5js4BpeHYzhn5n0w`, 옵션 Todo `f75ad846` / In Progress `47fc9ee4` / Done `98236657`). 브랜치 → PR → 셀프 머지는 **기능 단위**로만 하고, 문서·잡무는 `main` 직접 커밋도 허용한다. 일정이 밀리면 절차를 줄인다. 이슈 초안은 `docs/issues_초안.md`.
- **사용자가 AI가 쓴 코드를 이해해야 한다**(강사님 요구). **주석 기준**(이슈 #25): ① 파일 맨 위 docstring에 역할·흐름과 **수업과의 관계**(`[수업과 같음]` + 출처 노트북/강, `[수업에 없음]` + 한 줄 설명; 수업은 `../ict_innovation_sq_voice_ai`, 단 WER·CER은 수업이 아니라 자습 노트북) ② 함수 docstring에 하는 일·인자·돌려주는 값 ③ 인라인 주석은 "왜"(읽기만으로 모르는 줄, 라이브러리 옵션의 뜻, 숫자 상수의 의미) ④ 수업에 없는 라이브러리·옵션·개념은 반드시 `[수업에 없음]`과 설명 ⑤ 주석만 고칠 때는 동작을 바꾸지 않고, 단위 테스트가 그대로 통과해야 한다(주석·docstring을 뺀 코드를 AST로 비교해 확인했다). 하루 작업은 `docs/작업_일지.md`에 계획서 9장 양식(한 일·막힌 점·내일 할 일·질문)으로 남기고(강사님 면담이 있는 날의 엔트리에는 **전날 밤에 '강사님께 말씀드릴 것'** 을 "진행 상태 → 막힌 점 → 시도한 것 → 질문" 순서로 미리 적어 두고, 면담 뒤 결정 사항 3줄을 채운다), 새 파일을 만들면 그 문서의 파일 표와 읽는 순서 표에도 한 줄 추가한다(사용자가 Notion으로 복사). 낯선 용어는 같은 문서의 용어 표에 추가한다.
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