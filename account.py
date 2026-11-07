"""계정 서비스(가입·로그인·로그인 유지·로그아웃): `auth.py`의 판단과 `storage.py`의 DB 읽기·쓰기를 이어 붙인다. 이슈 #52, 검토 문서 16.16 11절.

화면(`app/auth_gate.py`)은 이 함수들을 부르고 메시지만 보여 준다. 함수는 **(결과, 안내 글)** 을 돌려주고 안내 글에는 비밀번호·아이디의 존재 여부를 흘리지 않는다.
`store`로 저장소 모듈을 바꿀 수 있어서(기본은 `storage`) DB 없이 가짜 저장소로 테스트한다.

- 로그인 실패 안내는 **아이디가 없을 때와 비밀번호가 틀릴 때 똑같은 글**을 쓴다(어떤 아이디가 있는지 알아내지 못하게).
- 아이디가 없을 때도 해시를 한 번 계산해서 **응답 시간으로 아이디 존재를 알아채지 못하게** 한다.
- 잠금 중에는 비밀번호가 맞아도 거절한다.
수업과의 관계: [수업에 없음] 이 파일 전체(웹 인증).
"""
from datetime import datetime, timezone

import auth
import storage as _storage

FAIL_MESSAGE = "아이디나 비밀번호가 맞지 않아요."


def _now():
    return datetime.now(timezone.utc)


def signup(conn, username, password, store=_storage):
    """가입. 돌려주는 값: (사용자 id 또는 None, 안내 글). 규칙 위반·중복 아이디면 (None, 이유)."""
    message = auth.validate_username(username) or auth.validate_password(password, username)
    if message:
        return None, message
    salt, pw_hash = auth.hash_password(password)
    try:
        return store.create_user(conn, username, salt, pw_hash), ""
    except store.UsernameTaken:
        return None, "이미 쓰고 있는 아이디예요."


def login(conn, username, password, store=_storage, now=None):
    """로그인. 돌려주는 값: (사용자 행 또는 None, 안내 글). 실패 횟수와 잠금은 DB에 기록한다."""
    now = now or _now()
    user = store.get_user(conn, username) if isinstance(username, str) and username else None
    if user is None:
        auth.hash_password(password if isinstance(password, str) else "")      # 아이디가 있을 때와 비슷한 시간이 걸리게
        return None, FAIL_MESSAGE
    if auth.is_locked(user["locked_until"], now):
        return None, f"여러 번 틀려서 {auth.lock_remaining_seconds(user['locked_until'], now)}초 뒤에 다시 시도할 수 있어요."
    if isinstance(password, str) and auth.verify_password(password, user["pw_salt"], user["pw_hash"]):
        store.record_login_success(conn, user["id"], now)
        return user, ""
    count, until = auth.after_failure(user["failed_count"], now)
    store.record_login_failure(conn, user["id"], count, until)
    if until is not None:
        return None, f"여러 번 틀려서 {auth.lock_remaining_seconds(until, now)}초 뒤에 다시 시도할 수 있어요."
    return None, FAIL_MESSAGE


def start_remember(conn, user_id, store=_storage, now=None):
    """로그인 유지: 토큰을 만들어 해시를 DB에 저장하고 **원문**을 돌려준다(쿠키에 줄 값)."""
    now = now or _now()
    raw = auth.new_token()
    store.add_token(conn, user_id, auth.token_hash(raw), auth.token_expiry(now))
    return raw


def resume(conn, raw_token, store=_storage, now=None):
    """쿠키의 토큰으로 자동 로그인. 유효하면 사용자 행(만료는 30일 뒤로 연장), 아니면 None."""
    if not raw_token or not isinstance(raw_token, str) or len(raw_token) > 200:
        return None
    now = now or _now()
    return store.user_by_token(conn, auth.token_hash(raw_token), now, auth.token_expiry(now))


def end_session(conn, raw_token, store=_storage):
    """로그아웃: 이 토큰을 지운다(없어도 오류 없음)."""
    if raw_token and isinstance(raw_token, str):
        store.delete_token(conn, auth.token_hash(raw_token))
