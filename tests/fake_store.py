"""DB 없이 계정·저장 로직과 화면(AppTest)을 시험하려고 만든 **메모리 가짜 저장소**. storage.py와 같은 함수 이름을 갖는다.
진짜 SQL의 의미(사용자 격리, 대소문자 무시, 연쇄 삭제 등)는 tests/test_storage.py가 진짜 DB로 확인하고, 이 가짜는 호출 흐름만 시험한다."""
from contextlib import contextmanager
from datetime import datetime, timezone

import storage as real


class FakeStore:
    UsernameTaken = real.UsernameTaken

    def __init__(self):
        self.users, self.tokens, self.songs, self.sentences, self.attempts = {}, {}, {}, {}, []
        self.next_id, self.calls = 1, []

    # 접속
    def enabled(self, env=None): return True
    def ping(self, info=None): return True

    @contextmanager
    def connect(self, info=None, schema=None):
        yield self

    def migrate(self, conn): return []

    # 사용자
    def create_user(self, conn, username, salt, pw_hash):
        if any(u["username"].lower() == username.lower() for u in self.users.values()):
            raise real.UsernameTaken("이미 있는 아이디입니다.")
        uid, self.next_id = self.next_id, self.next_id + 1
        self.users[uid] = {"id": uid, "username": username, "pw_salt": salt, "pw_hash": pw_hash, "failed_count": 0,
                           "locked_until": None, "save_on": True, "last_login": None}
        return uid

    def get_user(self, conn, username):
        return next((u for u in self.users.values() if u["username"].lower() == username.lower()), None)

    def get_user_by_id(self, conn, uid): return self.users.get(uid)

    def record_login_failure(self, conn, uid, count, until):
        self.users[uid].update(failed_count=count, locked_until=until)

    def record_login_success(self, conn, uid, now):
        self.users[uid].update(failed_count=0, locked_until=None, last_login=now)

    def set_password(self, conn, uid, salt, pw_hash):
        self.users[uid].update(pw_salt=salt, pw_hash=pw_hash, failed_count=0, locked_until=None)

    def set_save_on(self, conn, uid, on): self.users[uid]["save_on"] = bool(on)

    def delete_user(self, conn, uid):
        if uid not in self.users:
            return 0
        del self.users[uid]
        self.tokens = {h: t for h, t in self.tokens.items() if t["user_id"] != uid}
        self.songs = {k: v for k, v in self.songs.items() if k[0] != uid}
        self.sentences.pop(uid, None)
        self.attempts = [a for a in self.attempts if a["user_id"] != uid]
        return 1

    # 토큰
    def add_token(self, conn, uid, th, expires): self.tokens[bytes(th)] = {"user_id": uid, "expires_at": expires}

    def user_by_token(self, conn, th, now, new_expiry):
        t = self.tokens.get(bytes(th))
        if not t or t["expires_at"] <= now:
            return None
        t["expires_at"] = new_expiry
        return self.users.get(t["user_id"])

    def delete_token(self, conn, th): self.tokens.pop(bytes(th), None)
    def delete_user_tokens(self, conn, uid): return 0
    def purge_expired_tokens(self, conn, now): return 0

    # 곡·문장·시도
    def save_song(self, conn, uid, digest, doc, name=None, seconds=None, input=None, clip_start=None, clip_duration=None, languages=None):
        self.calls.append(("save_song", uid, digest))
        self.songs[(uid, digest)] = {"user_id": uid, "digest": digest, "doc": doc, "name": name, "seconds": seconds, "input": input,
                                     "clip_start": clip_start, "clip_duration": clip_duration, "languages": languages}

    def load_song(self, conn, uid, digest): return self.songs.get((uid, digest))

    def list_songs(self, conn, uid):
        return [dict(v, n_lines=len(v["doc"].get("lines", []))) for k, v in self.songs.items() if k[0] == uid]

    def delete_song(self, conn, uid, digest): return 1 if self.songs.pop((uid, digest), None) else 0

    def save_sentences(self, conn, uid, doc): self.sentences[uid] = doc
    def load_sentences(self, conn, uid): return self.sentences.get(uid)

    def append_attempt(self, conn, uid, record):
        self.calls.append(("append_attempt", uid, record.get("mode")))
        self.attempts.append(dict(record, user_id=uid, id=len(self.attempts) + 1, ts=datetime.now(timezone.utc)))
        return len(self.attempts)

    def list_attempts(self, conn, uid, limit=500, key=None):
        rows = [a for a in self.attempts if a["user_id"] == uid and (key is None or a.get("key") == key)]
        return list(reversed(rows))[:limit]

    def count_attempts(self, conn, uid): return sum(1 for a in self.attempts if a["user_id"] == uid)


def install(store):
    """진짜 storage 모듈의 함수들을 가짜로 바꾸고, 되돌리는 함수를 돌려준다."""
    names = [n for n in dir(store) if not n.startswith("_") and callable(getattr(store, n)) and n != "UsernameTaken"]
    saved = {n: getattr(real, n) for n in names if hasattr(real, n)}
    for n in names:
        setattr(real, n, getattr(store, n))

    def restore():
        for n, f in saved.items():
            setattr(real, n, f)
    return restore
