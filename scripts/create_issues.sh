#!/usr/bin/env bash
# 저장소를 GitHub에 만들고 `gh` 로그인이 되어 있을 때, 저장소 폴더에서 실행합니다.
#   bash scripts/create_issues.sh
# 라벨을 만든 뒤 docs/issues_초안.md 의 이슈를 생성합니다. 실행 전에 내용을 확인하세요.
set -euo pipefail

for l in "L1:0e8a16" "L2:1d76db" "L3:5319e7" "docs:cfd3d7"; do
  gh label create "${l%%:*}" --color "${l##*:}" --force >/dev/null
done

mk() { gh issue create --label "$1" --title "$2" --body "$3" ; }

mk L1 "환경 점검: OpenAI TTS/STT 호출·키 한도, Whisper 로컬 로드, 녹음 방법" "[1일차] 영어 TTS 1건 생성, 로컬 STT 1건 인식, 사용할 녹음 방법 결정, 계획서 20261029 A절의 1일차 확인 항목 점검"
mk L1 "연습 문장 10개 작성·확정 (sentences.csv)" "[1일차] 5~12단어, 축약형 2~3개, 비슷한 소리 단어 쌍 1~2개, 출처·라이선스 기록"
mk L1 "scoring.py 이식·손계산 5건 대조·정규화 규칙 확정" "[1일차] unittest 통과, 정규화 규칙 문서 초안, 초기 CER 기준 측정"
mk docs "Notion 개설과 일일 기록 틀" "[1일차] 일일 기록·질문·실험·결정 기록"
mk L1 "tts.py: 문장 → 기준 음성 생성·캐시" "[2일차] 재호출 방지 캐시, 호출 횟수 기록"
mk L1 "녹음 입력 → 16kHz 모노 변환" "[2일차] wav/m4a 입력"
mk L1 "quality.py: 녹음 입력 상태 점검" "[2일차] 빈 파일·작은 소리·무음·클리핑 경고, 기준값은 본인 녹음으로 확정"
mk L1 "stt.py: faster-whisper 인식(언어 지정)" "[3일차] 모델·compute_type·beam_size 기록"
mk L1 "읽기 연습 흐름 연결 (practice.ipynb)" "[3일차] 듣기 → 녹음 → 점검 → STT → 채점 → 틀린 부분 표시"
mk L1 "L1 통합·검증: 10문장 x 3회 = 30건" "[4일차] 실패 0건, 손계산 5건 일치, 입력 상태 경고 동작"
mk L2 "받아쓰기 모드" "[5일차] TTS 듣기 → 입력 → 같은 채점 → 틀린 부분 표시"
mk L2 "재생 제어 플레이어 (player.py)" "[5일차] 체크리스트 5항목 통과 또는 기본 플레이어 대체 기록"
mk L2 "연습 기록 CSV 저장" "[5일차] 시각·문장 id·모드·WER·CER·S/D/I·설정"
mk L2 "오류율 그래프" "[6일차] 기록 30건 이상으로 그래프 1개"
mk L2 "LLM 뜻·연관 표현 (explain.py) + 직접 검수" "[6일차] 문장 10개 검수표, AI 생성(참고용) 표시"
mk L2 "L2 통합 점검" "[6일차] 읽기·받아쓰기·기록을 한 흐름으로 시연"
mk L3 "(a) 노래 구간 인식: 낭독 vs 노래 CER 비교" "[7일차] 문장 5~10개 x (낭독, 노래), 표·해석, 시드 3회 이상"
mk L3 "(a) 음악·음성 분리 전/후 비교 (시간이 되면)" "[7일차] 분리 모델 설치·속도 확인 후 분리 전/후 CER·스펙트로그램"
mk L3 "실험 결과 정리·해석" "[8일차] 표 + 해석 3줄 이상, 한계 명시"
mk docs "테스트·오류 처리·README, 예비 시간" "[8일차] 수업 출처 표, 한계"
mk docs "최종 점검 체크리스트와 발표 자료" "[9일차] 개인 음성·key·상업 가사 미포함, git status 확인, 보고 자료"
