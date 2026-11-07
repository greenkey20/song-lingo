"""아이디·비밀번호 로그인의 **판단 로직**(순수 함수): 해시, 검증, 아이디·비밀번호 규칙, 토큰, 잠금. 이슈 #52, 검토 문서 16.16 11절.

DB와 화면은 모른다. DB 읽기·쓰기는 `storage.py`, 화면은 `app/streamlit_app.py`가 맡고, 여기서는 "맞는가·잠가야 하는가·토큰은 어떻게 만드는가"만 정한다(단위 테스트가 쉽다).

- 비밀번호는 **`hashlib.scrypt`**(소금값 포함, 일부러 느린 해시)로 저장한다. 같은 비밀번호도 사용자마다 소금이 달라 해시가 다르다. 원문은 어디에도 남기지 않는다.
- 비교는 `hmac.compare_digest`(길이와 상관없이 같은 시간)를 쓴다.
- **로그인 유지 토큰**: 로그인 때 `secrets.token_urlsafe`로 만든 랜덤 값을 쿠키에 주고, DB에는 **sha256 해시만** 저장한다(DB가 새도 쿠키 값을 알 수 없게).
- 연속 실패 5번이면 5분 잠근다(계정마다 DB에 기록하므로 새 세션을 열어도 유지됨).

수업과의 관계: [수업에 없음] 이 파일 전체(웹 인증). 표준 라이브러리 `hashlib`, `hmac`, `secrets`, `re`만 쓴다.
"""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta

SCRYPT_N, SCRYPT_R, SCRYPT_P, DKLEN = 2 ** 14, 8, 1, 32    # scrypt 비용(메모리 약 16MB, 로그인 한 번에 0.05초 안팎)
USERNAME_RE = re.compile(r"^[A-Za-z0-9가-힣_.\-]{3,20}$")
PASSWORD_MIN, PASSWORD_MAX = 8, 128
MAX_FAILS = 5
LOCK = timedelta(minutes=5)
TOKEN_DAYS = 30
COOKIE_NAME = "sl_auth"


# ---------- 비밀번호 ----------
def hash_password(password, salt=None):
    """비밀번호 → (소금값 16바이트, 해시 32바이트). salt를 주면 그 소금으로(검증용), 안 주면 새로 만든다."""
    salt = salt if salt is not None else secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=DKLEN)
    return salt, digest


def verify_password(password, salt, expected_hash):
    """입력한 비밀번호가 저장된 (소금, 해시)와 맞는지."""
    _, digest = hash_password(password, bytes(salt))
    return hmac.compare_digest(digest, bytes(expected_hash))


def validate_username(name):
    """아이디 규칙 위반이면 안내 글, 맞으면 None. 3~20자, 영문·숫자·한글·`_ . -`."""
    if not isinstance(name, str) or not USERNAME_RE.match(name):
        return "아이디는 3~20자의 영문·숫자·한글과 _ . - 만 쓸 수 있어요."
    return None


def validate_password(password, username=""):
    """비밀번호 규칙 위반이면 안내 글, 맞으면 None. 8~128자이고 아이디와 같으면 안 된다."""
    if not isinstance(password, str) or not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return f"비밀번호는 {PASSWORD_MIN}~{PASSWORD_MAX}자로 정해 주세요."
    if username and password.lower() == username.lower():
        return "비밀번호는 아이디와 달라야 해요."
    return None


# ---------- 로그인 유지 토큰 ----------
def new_token():
    """쿠키에 줄 랜덤 토큰(원문). 43글자 안팎의 URL 안전 문자열."""
    return secrets.token_urlsafe(32)


def token_hash(raw):
    """토큰 원문 → DB에 저장할 sha256 해시(32바이트)."""
    return hashlib.sha256(raw.encode("utf-8")).digest()


def token_expiry(now):
    """토큰 만료 시각: now + 30일. 접속할 때마다 이 값으로 갱신한다(롤링)."""
    return now + timedelta(days=TOKEN_DAYS)


# ---------- 잠금 ----------
def is_locked(locked_until, now):
    """잠금 시각이 아직 안 지났으면 True."""
    return locked_until is not None and now < locked_until


def lock_remaining_seconds(locked_until, now):
    """남은 잠금 시간(올림한 초). 잠겨 있지 않으면 0."""
    if not is_locked(locked_until, now):
        return 0
    left = (locked_until - now).total_seconds()
    return int(left) + (1 if left > int(left) else 0)


def after_failure(failed_count, now):
    """로그인에 한 번 실패한 뒤의 (새 연속 실패 횟수, 잠금 해제 시각 또는 None). MAX_FAILS번째 실패에 잠그고 횟수는 0으로 되돌린다."""
    failed_count += 1
    if failed_count >= MAX_FAILS:
        return 0, now + LOCK
    return failed_count, None
