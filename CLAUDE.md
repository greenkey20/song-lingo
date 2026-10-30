# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**song-lingo** — 외국어 노래 문장 연습 도우미 (듣고 따라읽고 받아쓰고 확인하는 음성 학습 프로토타입). ICT 혁신 스퀘어 Voice-AI 부트캠프의 **개인 프로젝트**(2026-10-30 ~ 11-11 평일 9일 × 4h = 36h 개발, **11-12 발표**). 사용자가 TTS 기준 음성을 듣고 → 따라 읽은 녹음을 STT로 인식하거나 받아쓰기를 하고 → 정답과의 **오류율(WER/CER)** 과 틀린 부분을 피드백받는다. 점수는 **발음 점수가 아니라 "문장 인식 일치도"** 다(STT가 틀린 발음을 문맥으로 고쳐 적을 수 있음). 시연 화면은 **Jupyter 노트북(`practice.ipynb`)** 이고, PWA/웹 앱은 범위 밖(후속 확장).

- **결정된 내용: `docs/프로젝트 개발 계획서_20261030.md`** (L1 필수 → L2 확장 → L3 심화 선택, 일정 · 성공 기준 · 축소 규칙 포함). 사용자가 직접 정리해 강사님께 공유하는 문서이므로 **사용자의 글을 임의로 바꾸지 말고**, 고칠 때는 큰 흐름과 문체를 유지하며 필요한 부분만 고친다.
- **`docs/프로젝트 개발 계획서_20261029.md`는 20261030으로 정리하면서 빠진 내용만 모은 보관본**이다. 특히 **A절의 "1일차에 확인할 항목"(확정되지 않은 항목 10개와 `[확인 필요]` 목록)** 을 1일차에 점검하고, 결과는 검토 문서에 기록한다. 이 파일의 L3 기호는 20261029 기준이라 20261030과 다르다(파일 머리의 주의 참고).
- **검토·근거·옵션 비교: `docs/프로젝트_안내_및_주제_검토.md`** (절 번호 8.x, 변경 이력은 8.19). 이 사본이 이 저장소에서 앞으로 이어 쓰는 원본이다(학습 저장소의 사본은 10-30 시점의 것).
- 학습 배경(1~7강 노트북)은 형제 폴더 `../ict_innovation_sq_voice_ai/`(읽기 전용 참고). 특히 `017_sound/lesson07_whisper_minimal.ipynb`(faster-whisper), `013_openai_api/`(TTS/STT 호출 코드), `017_sound/02·03·lesson04`(WAV 전처리, FFT/STFT/Mel).

## Environment

- **conda 환경 `voice-ai` 하나만 사용**: `/opt/anaconda3/envs/voice-ai/bin/python` (Python 3.11). 다른 환경(`base` 등)은 쓰지 않는다. 노트북 커널도 `voice-ai`(`Python 3.11 (voice-ai)`).
- `numpy`는 **1.26.4 고정**(TensorFlow 2.16). 새 패키지는 설치 전 **`pip install --dry-run`** 으로 numpy가 바뀌지 않는지 확인한다. 노트북에서는 `%pip` 또는 `!{sys.executable} -m pip`.
- 설치된 것: faster-whisper 1.2.1, openai, python-dotenv, pandas, scipy, matplotlib. **없는 것**: `pytest`, `streamlit`, `gradio`, `ipywidgets`, `sounddevice`, `soundfile`, `librosa` (노트북에서 직접 마이크 녹음 불가 → **미리 녹음한 파일 경로를 지정**). 테스트는 표준 라이브러리 `unittest`를 쓴다.
- 머신: macOS 13.7, Intel i7 4스레드, RAM 16GB, **GPU 없음**(CPU만). Whisper는 `tiny` + `int8`.
- **OpenAI API key**는 `.env`의 `OPENAI_API_KEY` (git에 올리지 않음; README가 `.env.example`을 언급하지만 **아직 파일이 없다** — 만들 때 key 값은 비운다). 학습 저장소의 `.env`를 쓰려면 사용자가 직접 `cp ../ict_innovation_sq_voice_ai/.env .env`. 호출 코드는 `load_dotenv()` 후 `OpenAI()`. 노트북 셀 실행은 **실제 과금**되므로 TTS 결과는 캐시(`data/tts_cache/`)해서 재호출을 줄이고 호출 횟수를 기록한다.

## Commands

```bash
PY=/opt/anaconda3/envs/voice-ai/bin/python
$PY -m unittest discover -s tests -v          # scoring.py 단위 테스트
$PY -m unittest tests.test_scoring.Boundaries.test_format_diff   # 테스트 1개 (프로젝트 루트에서)
$PY scripts/scan_outputs.py                   # 커밋 전: 노트북 출력의 오디오 플레이어·/Users 경로·key 검사
```
노트북은 VS Code 또는 `jupyter notebook`에서 연다(커널 `voice-ai`). 빌드/린트 도구는 없다.

## Layout (계획서 3장)

`scoring.py`(정규화·WER/CER·역추적·틀린 부분 표시, **구현·테스트 있음**), 이후 만들 모듈: `tts.py`, `stt.py`, `quality.py`(녹음 입력 상태 점검), `player.py`(L2 HTML 플레이어), `explain.py`(L2 LLM 뜻·표현), `visualisation.py`(L3), 시연 노트북 `practice.ipynb`, `experiments/`(L3 실험), `sentences.csv`(id, lang, sentence, meaning_ko, source, license). `scoring.py`의 흐름: `normalize` → 토큰화(`wer`는 공백 단위, `cer`는 글자 단위) → `edit_matrix` → `backtrace`(ops: 일치/치환/삭제/삽입) → `score`가 S·D·I·N·rate·ops를 dict로 반환 → `format_diff(ops)`로 표시. 새 채점 로직은 이 `score()` 결과 dict를 재사용한다. `sentences.csv`와 `.ipynb`는 아직 헤더/뼈대뿐이다. 먼저 `practice.ipynb`에서 흐름을 연결하고 재사용·테스트할 함수부터 `.py`로 분리한다. `data/`(녹음·TTS 캐시)와 `results/`(기록 CSV·그래프)는 **git에서 제외**된다.

## Key decisions (자세한 근거는 docs 두 파일)

- **STT**: 기본 로컬 `faster-whisper tiny` (`device="cpu"`, `compute_type="int8"`, `beam_size=1` — 7강 설정, 결과 보고 때 설정을 함께 기록). OpenAI STT는 대체·비교용. **TTS는 OpenAI로 고정.** 6강에서 만든 Keras 모델은 제품 STT로 쓰지 않는다.
- **채점**: `(S+D+I)/N`. 영어 정규화 = NFC → 소문자 → 구두점 제거(아포스트로피 유지) → 공백 정리. 정답이 비면 오류. **WER은 1을 넘을 수 있으므로 "일치율(1−WER)"로 표시하지 말고** 오류율과 S·D·I 개수로 표시. 틀린 부분 표시는 `difflib`이 아니라 **편집 거리 역추적**(`difflib`은 최소 경로를 보장하지 않음). 일본어는 CER 중심. 축약형·숫자·프랑스어 악센트 방침은 1일차에 확정(`normalize()`의 인자로 열어 둠).
- **녹음 입력 상태 점검(`quality.py`)** 은 음량·무음·클리핑만 본다(잡음 판정이 아님): 너무 작음(RMS < −40 dBFS 또는 최대 진폭 < 0.05), 클리핑(0.999 이상 샘플 ≥ 0.1%), 대부분 무음(STFT 프레임 에너지가 최대 프레임보다 35 dB 이상 낮은 프레임 ≥ 80% — **절대 기준이 아니라 상대 기준**), 참고로 80 Hz 이하 에너지 비율. 기준값은 초안이며 1일차에 본인 녹음으로 확정.
- **L3 기본안은 (a) 노래 구간 인식 + 음악·음성 분리**(강사님 권유; 분리 없는 낭독 vs 노래 CER 비교가 최소 구성). 막히면 (e) 잡음 견고성. 분리 모델(Demucs)은 `--dry-run` 확인만 했고 CPU 속도는 **미확인**. 실험은 시드를 바꿔 **3회 이상** 반복해 평균·범위를 보고하고, 합성 흰 잡음 결과를 실제 환경으로 일반화하지 않으며, 모든 녹음이 본인 한 명이라는 한계를 명시한다.
- **지연 시 축소 순서(L2)**: ① LLM 뜻·표현 → ② 재생 속도·±5초(기본 `Audio` 플레이어로 대체) → ③ 오류율 그래프 → ④ 기록 CSV, **받아쓰기는 마지막까지 유지**. L3는 항상 선택.
- 방향: 이 프로젝트는 **수업(음성 1~7강 + 013) 복습·활용 수단**이다. **새 기능·새 기술 시도는 최소화**(계획서 공유본에는 빠졌지만 사용자의 방향이다).

## Privacy / security (공개 저장소 전제)

- `.env`, API key, **사용자 본인 목소리(녹음)**, 강사님 목소리, 강사 제공 WAV, 모델 파일, 화면 캡처(다른 수강생 이름·얼굴)는 **절대 커밋하지 않는다**. **사용자 실명은 어떤 파일명·내용에도 쓰지 않는다.**
- **상업 노래의 가사·음원**은 저장소에 두지 않고, 시연에 쓰지 않고, LLM API에 입력하지 않는다. 연습 문장은 직접 쓴 예문 또는 이용이 확인된 공개 문장이다. 음악·음성 분리 실험의 반주도 직접 만든 것 또는 이용이 허용된 음원만 쓰고 이용 조건을 기록한다.
- **노트북 출력**에는 `<audio>` 플레이어(base64 음원), `/Users/…` 경로, key가 박힐 수 있다. 커밋 전에 출력을 지우고 `scripts/scan_outputs.py`로 확인한다(깨끗한 복사본을 커밋하고 로컬 원본은 그대로 둬도 된다).
- `git add -A`, `git add .` 금지 — 파일을 하나씩 추가하고 `git status`로 확인한다. 최종 점검 체크리스트는 계획서 6장 9일차 항목.

## Working agreements (사용자와의 합의)

- 채팅은 **친근한 반말**. 문서(md, 노트북 설명 셀)는 "~입니다" 문체를 유지한다.
- **프로젝트 판단·옵션 비교·질문 답변은 채팅에만 남기지 말고 `docs/프로젝트_안내_및_주제_검토.md`에 먼저 기록**하고, 계획서에는 **결정된 내용만** 적는다. 계획서를 고치면 검토 문서 8.19 변경 이력에 한 줄 추가한다.
- **실험·확인은 방법과 코드를 알려 주고 사용자가 직접 실행**하게 한다. 내가 돌린 값은 "참고 baseline"으로 표시하고 해석을 돕는다.
- 코드·문서의 숫자와 동작 주장은 **실행해서 확인**하고, 추정은 **[추정]**, 일반 지식은 **[일반 지식]**, 못 한 확인은 **[미확인]** 으로 표시한다(사용자가 이 문서들로 공부한다).
- **커밋은 주제별로, 사용자가 확인한 뒤에만**. 가능하면 적은 수의 큰 커밋. push는 사용자가 요청할 때만. 직접 커밋에는 세션의 `Co-Authored-By` 트레일러를 넣는다. 한국어 `feat:`/`docs:`/`chore:` 메시지 관례(학습 저장소와 동일).
- 칸반은 GitHub Projects, 작업은 **이슈 1개 = 카드 1개(L1/L2/L3 라벨)**. 브랜치 → PR → 셀프 머지는 **기능 단위**(scoring, tts, stt, player …)로만 하고, 문서·잡무는 `main` 직접 커밋도 허용한다. 일정이 밀리면 절차를 줄인다. 이슈 초안은 `docs/issues_초안.md`.
- 사용자가 열어 둔 노트북을 고칠 때는 파일을 다시 읽고, 사용자의 셀은 건드리지 않고 새 셀만 삽입하며, 사용자에게 *File → Reload Notebook from Disk* 를 안내한다.
