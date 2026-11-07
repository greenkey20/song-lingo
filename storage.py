"""사용자별 저장(PostgreSQL): 계정·로그인 토큰·곡 기록·내 문장·채점 시도를 읽고 쓴다. 이슈 #52, 검토 문서 16.16 11절.

이 모듈은 **SQL을 실행하는 일만** 한다. 해시·토큰 만들기·잠금 판단은 `auth.py`(순수 함수), 화면은 `app/`이 맡는다. Streamlit을 부르지 않아 단위 테스트가 쉽다.

사용 흐름
    with storage.connect() as conn:          # 열기 → 성공하면 commit, 예외가 나면 rollback → 닫기
        storage.migrate(conn)                # 아직 적용 안 된 migrations/*.sql만 순서대로 실행(앱 시작 때 한 번)
        uid = storage.create_user(conn, "alice", salt, pw_hash)
        storage.append_attempt(conn, uid, {...})

- **접속 정보는 환경변수**(`.env`): `DB_HOST`(기본 127.0.0.1), `DB_PORT`(기본 5433), `DB_NAME`, `DB_USER`, `DB_PASSWORD`(inner-orbit과 같은 이름).
  `DB_NAME`·`DB_USER`가 없으면 `enabled()`가 False이고 앱은 저장 없이(게스트 모드로) 동작한다.
- **호출마다 연결을 열고 닫는다**(Streamlit은 세션마다 스레드가 달라 연결을 공유하기 어렵고, 이 규모에서는 비용이 작다). 연결 제한시간은 3초라서 DB가 멈춰도 화면이 오래 멈추지 않는다.
- **모든 SQL은 값을 따로 넘기는 방식(`%s`)** 이라 문자열을 이어 붙이지 않는다(SQL 주입을 막는다). 사용자별 데이터는 항상 `user_id` 조건으로 걸러서 다른 사용자의 것이 섞이지 않게 한다.
- 가사·비밀번호는 **로그·오류 메시지에 남기지 않는다**(예외 메시지에 값을 넣지 않음).

수업과의 관계: [수업에 없음] 이 파일 전체(데이터베이스). 드라이버는 `psycopg`(v3), JSON 열은 `JSONB`.
"""
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
ADVISORY_LOCK_KEY = 5207001          # 마이그레이션을 한 번에 한 프로세스만 하게 하는 잠금 번호(임의의 고정 숫자)
CONNECT_TIMEOUT = 3


class StorageError(Exception):
    """저장소 관련 오류의 부모. 메시지에 가사·비밀번호를 넣지 않는다."""


class UsernameTaken(StorageError):
    """이미 있는 아이디(대소문자 무시)로 가입하려 할 때."""


# ---------- 접속 ----------
def conninfo(env=None):
    """환경변수 → libpq 접속 문자열. DB_NAME·DB_USER가 없으면 빈 글. (비밀번호의 특수문자는 make_conninfo가 알아서 이스케이프한다.)"""
    e = env if env is not None else os.environ
    name, user = e.get("DB_NAME", "").strip(), e.get("DB_USER", "").strip()
    if not (name and user):
        return ""
    return make_conninfo(host=(e.get("DB_HOST", "").strip() or "127.0.0.1"), port=(e.get("DB_PORT", "").strip() or "5433"),
                         dbname=name, user=user, password=e.get("DB_PASSWORD", ""), connect_timeout=CONNECT_TIMEOUT)


def enabled(env=None):
    """저장 기능을 쓸 수 있는지(접속 정보가 설정돼 있는지). DB가 실제로 살아 있는지는 따로 본다."""
    return bool(conninfo(env))


@contextmanager
def connect(info=None, schema=None):
    """연결을 열어 주고, with 블록이 끝나면 commit(예외가 나면 rollback) 후 닫는다. info를 안 주면 환경변수로 만든다.
    schema: 격리된 스키마를 쓰려고 search_path를 바꾼다(테스트가 직접 지정). 안 주면 환경변수 `DB_SCHEMA`(개발용: 서버 DB를 내 컴퓨터에서 시험할 때
    진짜 데이터가 있는 public 스키마를 건드리지 않으려고 `dev_test` 같은 별도 스키마를 쓴다)를 보고, 둘 다 없으면 기본(public)이다.
    환경변수로 정한 스키마는 없으면 만들어 준다(`CREATE SCHEMA IF NOT EXISTS`)."""
    info = info or conninfo()
    if not info:
        raise StorageError("DB 접속 정보가 설정되어 있지 않습니다.")
    explicit = schema
    schema = schema or os.environ.get("DB_SCHEMA", "").strip() or None
    if schema and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,40}", schema):
        raise StorageError("스키마 이름이 올바르지 않습니다.")
    conn = psycopg.connect(info, row_factory=dict_row)
    try:
        if schema:
            ident = psycopg.sql.Identifier(schema)
            if explicit is None:
                conn.execute(psycopg.sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(ident))
            conn.execute(psycopg.sql.SQL("SET search_path TO {}").format(ident))
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def ping(info=None):
    """DB에 접속해서 `select 1`이 되는지. 안 되면 False(예외를 삼킨다: 화면이 게스트 모드로 넘어가는 판단용)."""
    try:
        with connect(info) as conn:
            return conn.execute("SELECT 1 AS ok").fetchone()["ok"] == 1
    except Exception:
        return False


# ---------- 마이그레이션 ----------
def migrate(conn):
    """`migrations/*.sql`을 이름순으로 보면서 **아직 적용 안 된 것만** 실행하고 `schema_migrations`에 기록한다. 적용한 파일 이름 목록을 돌려준다.
    여러 프로세스가 동시에 시작해도 어드바이저리 잠금(트랜잭션이 끝날 때까지 유지)으로 한 번에 하나만 실행된다.
    규칙: 적용된 파일은 고치지 않고, 바꿀 때는 새 번호의 파일을 추가한다."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (ADVISORY_LOCK_KEY,))
    applied = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    done = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        conn.execute(path.read_text(encoding="utf-8"))            # 매개변수가 없으므로 여러 문장을 한 번에 실행할 수 있다
        conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
        done.append(path.name)
    return done


# ---------- JSON 변환 ----------
def _default(o):
    """json.dumps가 모르는 타입(numpy 숫자·배열, 집합 등)을 파이썬 기본 타입으로 바꾼다. 채점 결과 dict에 numpy 값이 섞여 있을 수 있다."""
    if hasattr(o, "item") and callable(o.item):
        try:
            return o.item()
        except Exception:
            pass
    if hasattr(o, "tolist"):
        return o.tolist()
    if isinstance(o, (set, frozenset, tuple)):
        return list(o)
    raise TypeError(f"JSON으로 바꿀 수 없는 타입: {type(o).__name__}")


def _jsonb(obj):
    return None if obj is None else Jsonb(obj, dumps=lambda o: json.dumps(o, default=_default, ensure_ascii=False))


# ---------- 사용자 ----------
def create_user(conn, username, salt, pw_hash):
    """새 사용자를 만들고 id를 돌려준다. 아이디는 대소문자를 구분하지 않고 유일해야 한다(이미 있으면 UsernameTaken)."""
    try:
        with conn.transaction():                                  # 실패해도 바깥 트랜잭션이 깨지지 않게 부분 롤백(세이브포인트)
            row = conn.execute("INSERT INTO users (username, pw_salt, pw_hash) VALUES (%s, %s, %s) RETURNING id",
                               (username, salt, pw_hash)).fetchone()
    except psycopg.errors.UniqueViolation:
        raise UsernameTaken("이미 있는 아이디입니다.") from None
    return row["id"]


def get_user(conn, username):
    """아이디(대소문자 무시)로 사용자 한 명. 없으면 None."""
    return conn.execute("SELECT * FROM users WHERE lower(username) = lower(%s)", (username,)).fetchone()


def get_user_by_id(conn, user_id):
    return conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()


def record_login_failure(conn, user_id, failed_count, locked_until):
    """로그인 실패를 기록한다. 새 횟수와 잠금 시각은 `auth.after_failure`로 계산해서 넘긴다."""
    conn.execute("UPDATE users SET failed_count = %s, locked_until = %s WHERE id = %s", (failed_count, locked_until, user_id))


def record_login_success(conn, user_id, now):
    """로그인 성공: 연속 실패와 잠금을 지우고 마지막 로그인 시각을 갱신한다."""
    conn.execute("UPDATE users SET failed_count = 0, locked_until = NULL, last_login = %s WHERE id = %s", (now, user_id))


def set_password(conn, user_id, salt, pw_hash):
    """비밀번호를 새 (소금, 해시)로 바꾸고 잠금·실패 횟수를 지우고 로그인 유지 토큰을 모두 지운다(모든 기기에서 로그아웃). 관리자 초기화용."""
    conn.execute("UPDATE users SET pw_salt = %s, pw_hash = %s, failed_count = 0, locked_until = NULL WHERE id = %s", (salt, pw_hash, user_id))
    conn.execute("DELETE FROM login_tokens WHERE user_id = %s", (user_id,))


def set_save_on(conn, user_id, on):
    """이 사용자의 '기록 저장' 켜기/끄기."""
    conn.execute("UPDATE users SET save_on = %s WHERE id = %s", (bool(on), user_id))


def delete_user(conn, user_id):
    """계정과 그에 딸린 모든 데이터(토큰·곡·문장·시도)를 지운다(ON DELETE CASCADE). 지운 사용자 수(0 또는 1)를 돌려준다."""
    return conn.execute("DELETE FROM users WHERE id = %s", (user_id,)).rowcount


# ---------- 로그인 유지 토큰 ----------
def add_token(conn, user_id, token_hash, expires_at):
    """로그인 유지 토큰(해시)을 저장한다."""
    conn.execute("INSERT INTO login_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)", (user_id, token_hash, expires_at))


def user_by_token(conn, token_hash, now, new_expiry):
    """토큰(해시)이 유효하면 그 사용자를 돌려주고 만료를 새로 늦춘다(롤링). 없거나 만료됐으면 None."""
    row = conn.execute("SELECT u.* FROM login_tokens t JOIN users u ON u.id = t.user_id WHERE t.token_hash = %s AND t.expires_at > %s",
                       (token_hash, now)).fetchone()
    if row:
        conn.execute("UPDATE login_tokens SET last_used = %s, expires_at = %s WHERE token_hash = %s", (now, new_expiry, token_hash))
    return row


def delete_token(conn, token_hash):
    """로그아웃: 이 토큰 하나를 지운다."""
    conn.execute("DELETE FROM login_tokens WHERE token_hash = %s", (token_hash,))


def delete_user_tokens(conn, user_id):
    """이 사용자의 모든 로그인 유지 토큰을 지운다(모든 기기에서 로그아웃)."""
    return conn.execute("DELETE FROM login_tokens WHERE user_id = %s", (user_id,)).rowcount


def purge_expired_tokens(conn, now):
    """만료된 토큰을 지우고 지운 개수를 돌려준다(가끔 정리용)."""
    return conn.execute("DELETE FROM login_tokens WHERE expires_at <= %s", (now,)).rowcount


# ---------- 곡 기록 ----------
def save_song(conn, user_id, digest, doc, name=None, seconds=None, input=None, clip_start=None, clip_duration=None, languages=None):
    """곡 기록을 저장한다(같은 곡 지문이면 덮어쓰고 수정 시각을 갱신). doc은 가사 줄 등을 담은 dict. 음원 자체는 저장하지 않는다."""
    conn.execute(
        "INSERT INTO songs (user_id, digest, name, seconds, input, clip_start, clip_duration, languages, doc) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (user_id, digest) DO UPDATE SET name = EXCLUDED.name, seconds = EXCLUDED.seconds, input = EXCLUDED.input, "
        "clip_start = EXCLUDED.clip_start, clip_duration = EXCLUDED.clip_duration, languages = EXCLUDED.languages, "
        "doc = EXCLUDED.doc, updated_at = now()",
        (user_id, digest, name, seconds, input, clip_start, clip_duration, list(languages) if languages is not None else None, _jsonb(doc)))


def load_song(conn, user_id, digest):
    """곡 기록 한 개(없으면 None). 다른 사용자의 곡은 user_id 조건 때문에 절대 나오지 않는다."""
    return conn.execute("SELECT * FROM songs WHERE user_id = %s AND digest = %s", (user_id, digest)).fetchone()


def list_songs(conn, user_id):
    """내 곡 목록(최근 수정 순). 가사 전체(doc) 대신 가벼운 열과 줄 수(n_lines)만 돌려준다."""
    return conn.execute(
        "SELECT digest, name, seconds, input, clip_start, clip_duration, languages, created_at, updated_at, "
        "COALESCE(jsonb_array_length(doc->'lines'), 0) AS n_lines FROM songs WHERE user_id = %s ORDER BY updated_at DESC", (user_id,)).fetchall()


def delete_song(conn, user_id, digest):
    """곡 기록 하나를 지운다. 지운 개수를 돌려준다."""
    return conn.execute("DELETE FROM songs WHERE user_id = %s AND digest = %s", (user_id, digest)).rowcount


# ---------- 내 문장 ----------
def save_sentences(conn, user_id, doc):
    """내 문장 목록(줄 글과 줄마다 확인한 언어)을 통째로 저장한다."""
    conn.execute("INSERT INTO sentences (user_id, doc) VALUES (%s, %s) "
                 "ON CONFLICT (user_id) DO UPDATE SET doc = EXCLUDED.doc, updated_at = now()", (user_id, _jsonb(doc)))


def load_sentences(conn, user_id):
    """내 문장 목록 dict(없으면 None)."""
    row = conn.execute("SELECT doc FROM sentences WHERE user_id = %s", (user_id,)).fetchone()
    return row["doc"] if row else None


# ---------- 채점 시도 ----------
def append_attempt(conn, user_id, record):
    """채점 시도 한 번을 저장하고 id를 돌려준다. record 열쇠: source, key, mode, lang, ref_text, hyp_text, score(dict), azure(dict 또는 None), stt."""
    row = conn.execute(
        "INSERT INTO attempts (user_id, source, key, mode, lang, ref_text, hyp_text, score, azure, stt) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (user_id, record.get("source"), record.get("key"), record.get("mode"), record.get("lang"), record.get("ref_text"),
         record.get("hyp_text"), _jsonb(record.get("score")), _jsonb(record.get("azure")), record.get("stt"))).fetchone()
    return row["id"]


def list_attempts(conn, user_id, limit=500, key=None):
    """내 시도 목록(최신 순, 최대 limit개). key를 주면 그 문장의 시도만."""
    if key is None:
        return conn.execute("SELECT * FROM attempts WHERE user_id = %s ORDER BY ts DESC, id DESC LIMIT %s", (user_id, limit)).fetchall()
    return conn.execute("SELECT * FROM attempts WHERE user_id = %s AND key = %s ORDER BY ts DESC, id DESC LIMIT %s",
                        (user_id, key, limit)).fetchall()


def count_attempts(conn, user_id):
    return conn.execute("SELECT count(*) AS n FROM attempts WHERE user_id = %s", (user_id,)).fetchone()["n"]


# ---------- 명령줄: python storage.py migrate | ping | reset-password <아이디> ----------
def _main(argv):
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")           # 값은 출력하지 않는다
    if not enabled():
        print("DB 접속 정보(DB_NAME·DB_USER 등)가 설정되어 있지 않습니다.")
        return 1
    cmd = argv[0] if argv else "ping"
    if cmd == "ping":
        ok = ping()
        print("DB 접속:", "OK" if ok else "실패")
        return 0 if ok else 1
    if cmd == "migrate":
        with connect() as conn:
            done = migrate(conn)
        print("적용한 마이그레이션:", done or "없음(이미 최신)")
        return 0
    if cmd == "reset-password" and len(argv) == 2:                  # 비밀번호를 잊은 사용자를 관리자가 초기화
        import getpass
        import auth
        pw = getpass.getpass(f"'{argv[1]}'의 새 비밀번호(영문·숫자 등 8자 이상): ")
        if pw != getpass.getpass("한 번 더: ") or auth.validate_password(pw, argv[1]):
            print("입력이 다르거나 비밀번호 규칙(8~128자)에 맞지 않아요. 아무것도 바뀌지 않았어요.")
            return 1
        salt, h = auth.hash_password(pw)
        with connect() as conn:
            user = get_user(conn, argv[1])
            if user is None:
                print("그 아이디가 없어요.")
                return 1
            set_password(conn, user["id"], salt, h)
        print("비밀번호를 바꿨어요(모든 기기에서 로그아웃됨).")
        return 0
    print("사용: python storage.py [ping|migrate|reset-password <아이디>]")
    return 2


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
