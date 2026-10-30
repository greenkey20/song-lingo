# song-lingo

외국어 노래에서 떠올린 문장을 **듣고 → 따라 읽거나 받아쓰고 → 오류율(WER/CER)과 틀린 부분을 확인**하는 음성 학습 프로토타입입니다. ICT 혁신 스퀘어 Voice-AI 부트캠프 개인 프로젝트(2026-10-30 ~ 11-12).

> 점수는 발음 점수가 아니라 **문장 인식 일치도(WER/CER 기반 오류율)** 입니다. 노래 가사·음원은 사용하지 않고, 직접 작성한 예문만 씁니다.

- 계획: [`docs/프로젝트 개발 계획서_20261030.md`](docs/프로젝트%20개발%20계획서_20261030.md)
- 검토와 근거: [`docs/프로젝트_안내_및_주제_검토.md`](docs/프로젝트_안내_및_주제_검토.md)
- WER/CER 학습 노트: [`docs/WER_CER_이해하기.ipynb`](docs/WER_CER_이해하기.ipynb)

## 실행

환경은 conda `voice-ai`(Python 3.11)를 씁니다. API key는 `.env.example`을 복사해 `.env`에 채웁니다.

```bash
/opt/anaconda3/envs/voice-ai/bin/python -m unittest discover -s tests -v
```

(구현이 진행되면서 이 문서를 갱신합니다. 각 기능의 수업 출처 표와 한계는 최종 README에 정리합니다.)
