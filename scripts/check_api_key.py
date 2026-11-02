"""어떤 OPENAI_API_KEY가 적용되는지 확인한다. 키 값은 출력하지 않고 앞 7자·끝 4자·길이만 보여 준다.

사용 (프로젝트 루트에서):
    python scripts/check_api_key.py          # 터미널에서
    ! python scripts/check_api_key.py        # Claude Code 세션에서 (사용자가 직접 실행)

왜 필요한가
- 키를 바꿨는데 같은 401이 나거나(작업 일지 11-01), 수업 제공 키와 개인 키 중 어느 것이 쓰이는지 모를 때 확인한다.
- `load_dotenv()`는 기본값이 `override=False`라서, 터미널·VS Code에 `OPENAI_API_KEY`가 이미 있으면 `.env`를 덮어쓰지 않는다
  [일반 지식]. 그래서 ".env를 고쳤는데 반영이 안 된다"가 생긴다. 이 스크립트는 그 우선순위를 그대로 따라 보여 준다.
- 노트북 커널은 이미 읽은 환경 변수를 다시 읽지 않으므로(CLAUDE.md), .env를 고친 뒤에는 커널을 재시작해야 한다.

수업과의 관계
- [수업에 없음] 이 파일 전체. `python-dotenv`의 `dotenv_values`(파일 내용을 읽기만 함)와 `load_dotenv`(환경 변수에 넣음)의 차이를 쓴다.

보안: 끝 4자는 대시보드의 키 목록(끝 4자 표시)과 맞춰 보려는 용도다. 이 출력을 노트북 출력으로 저장하지 않는다.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "OPENAI_API_KEY"


def mask(value):
    """키를 앞 7자…끝 4자(길이)로 가린다. 12자 미만이면 앞뒤도 보여 주지 않는다."""
    if not value:
        return "(없음)"
    if len(value) < 12:
        return f"(짧은 값, 길이 {len(value)})"
    return f"{value[:7]}…{value[-4:]} (길이 {len(value)})"


def diagnose(process_value, file_value):
    """(적용되는 곳, 설명 목록)을 돌려준다.

    process_value: load_dotenv 전에 이미 환경 변수에 있던 값(터미널·VS Code·셸 프로필에서 온 것).
    file_value: .env 파일에 적힌 값.
    load_dotenv(override=False) 규칙: 환경 변수에 이미 있으면 그것이 이기고 .env는 무시된다."""
    notes = []
    if process_value:
        source = "환경 변수(.env가 아님)"
        if file_value and file_value != process_value:
            notes.append(".env의 키와 다릅니다. .env는 무시되고 있습니다. 환경 변수를 지우거나 "
                         "load_dotenv(override=True) 후 tts.reset_client()를 부르세요.")
        elif file_value:
            notes.append(".env와 같은 키입니다.")
    elif file_value:
        source = ".env"
    else:
        source = None
        notes.append("키가 없습니다. .env.example을 .env로 복사해 OPENAI_API_KEY를 채우세요.")
    return source, notes


def main():
    from dotenv import dotenv_values       # 파일 내용만 읽는다(환경 변수에 넣지 않음)
    process_value = os.environ.get(NAME)
    file_value = dotenv_values(ROOT / ".env").get(NAME)
    source, notes = diagnose(process_value, file_value)
    print(f"환경 변수 {NAME}: {mask(process_value)}")
    print(f".env 파일 {NAME}: {mask(file_value)}")
    print(f"적용되는 곳: {source or '없음'}")
    for n in notes:
        print("-", n)
    return 0 if source else 1


if __name__ == "__main__":
    sys.exit(main())
