"""웹 앱의 접근 제한(비밀번호). 이슈 #52, CLAUDE.md Privacy ②("배포 앱은 접근 제한을 건다").

공개 주소에서는 누구나 TTS·STT·Azure·곡 업로드를 불러 내 키로 과금될 수 있어서, 환경변수 `SONGLINGO_PASSWORD`가 **설정돼 있을 때만** 비밀번호 확인을 켠다.
설정이 없으면(내 컴퓨터에서 개발할 때) 꺼져서 지금처럼 바로 열린다. 화면은 `app/streamlit_app.py`가 맡고, 이 모듈은 **판단만** 한다(Streamlit을 부르지 않아 단위 테스트가 쉽다).

- 비교는 `hmac.compare_digest`로 한다: 글자가 처음 다른 곳에서 멈추는 일반 비교는 "몇 글자까지 맞았나"가 응답 시간에 드러날 수 있어서(시간차 공격), 길이와 상관없이 같은 시간에 비교하는 함수를 쓴다 [일반 지식].
- 틀리면 **세션별로** 일정 횟수 뒤에 잠시 잠근다. 새 세션을 열면 초기화되므로 이것만으로는 무차별 대입을 막지 못한다 → 서버 앞단(Cloudflare)의 속도 제한과 **긴 비밀번호**가 함께 필요하다.
- 비밀번호는 로그·화면·오류 메시지 어디에도 남기지 않는다.

수업과의 관계: [수업에 없음] 이 파일 전체(웹 보안). 표준 라이브러리 `hmac`, `os`만 쓴다.
"""
import hmac
import os

ENV_NAME = "SONGLINGO_PASSWORD"
MAX_FAILS = 5          # 한 세션에서 이만큼 틀리면 잠근다
LOCK_SECONDS = 60      # 잠그는 시간(초)


def expected(env=None):
    """설정된 비밀번호(앞뒤 공백 제거). 없으면 빈 글. env는 테스트용 dict(기본은 os.environ)."""
    return (env if env is not None else os.environ).get(ENV_NAME, "").strip()


def enabled(env=None):
    """비밀번호 확인을 켤지: 환경변수가 비어 있지 않을 때만 True."""
    return bool(expected(env))


def check(given, env=None):
    """입력한 비밀번호가 맞는지. 확인이 꺼져 있으면 항상 True. 입력은 앞뒤 공백을 제거하지 않는다(그대로 비교)."""
    want = expected(env)
    if not want:
        return True
    return hmac.compare_digest(str(given).encode("utf-8"), want.encode("utf-8"))


def lock_remaining(fails, last_fail, now):
    """틀린 횟수(fails)가 MAX_FAILS 이상이면 마지막 실패(last_fail, 초) 뒤 남은 잠금 시간(올림한 초), 아니면 0. now는 현재 시각(초)."""
    if fails < MAX_FAILS:
        return 0
    left = LOCK_SECONDS - (now - last_fail)
    return int(left) + (1 if left > int(left) else 0) if left > 0 else 0
