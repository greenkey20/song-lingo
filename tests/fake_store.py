"""DB 없이 계정·저장 로직과 화면(AppTest)을 시험하려고 만든 **메모리 가짜 저장소**. storage.py와 같은 함수 이름을 갖는다.
진짜 SQL의 의미(사용자 격리, 대소문자 무시, 연쇄 삭제 등)는 tests/test_storage.py가 진짜 DB로 확인하고, 이 가짜는 호출 흐름만 시험한다."""
from contextlib import contextmanager
from datetime import datetime, timezone

import storage as real


class FakeStore:
    UsernameTaken = real.UsernameTaken

    def __init__(self):
        self.users, self.tokens, self.clips, self.texts, self.practices = {}, {}, {}, {}, []
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
        self.clips = {k: v for k, v in self.clips.items() if v["user_id"] != uid}
        self.texts.pop(uid, None)
        self.practices = [a for a in self.practices if a["user_id"] != uid]
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

    # 구간·문장·연습 기록 (storage.py와 같은 이름·열)
    def save_clip(self, conn, uid, audio_sha1, clip_start_sec, clip_duration_sec, doc, song_title=None, song_duration_sec=None,
                  input_type=None, languages=None):
        key = (uid, audio_sha1, round(float(clip_start_sec), 2), round(float(clip_duration_sec), 2))
        self.calls.append(("save_clip", uid, audio_sha1))
        old = self.clips.get(key)
        cid = old["id"] if old else self._new_id()
        self.clips[key] = {"id": cid, "user_id": uid, "audio_sha1": audio_sha1, "song_title": song_title, "song_duration_sec": song_duration_sec,
                           "input_type": input_type, "clip_start_sec": key[2], "clip_duration_sec": key[3], "languages": languages, "doc": doc,
                           "updated_at": datetime.now(timezone.utc)}
        return cid

    def load_clip(self, conn, uid, audio_sha1, clip_start_sec, clip_duration_sec):
        return self.clips.get((uid, audio_sha1, round(float(clip_start_sec), 2), round(float(clip_duration_sec), 2)))

    def load_clip_by_id(self, conn, uid, clip_id):
        return next((v for v in self.clips.values() if v["user_id"] == uid and v["id"] == clip_id), None)

    @staticmethod
    def _light(v):
        return {k: x for k, x in v.items() if k != "doc"} | {"n_lines": len(v["doc"].get("lines", []))}

    def list_clips(self, conn, uid):
        return [self._light(v) for v in sorted(self.clips.values(), key=lambda v: v["updated_at"], reverse=True) if v["user_id"] == uid]

    def list_clips_of(self, conn, uid, audio_sha1):
        return [self._light(v) for v in sorted(self.clips.values(), key=lambda v: (v["clip_start_sec"], v["clip_duration_sec"]))
                if v["user_id"] == uid and v["audio_sha1"] == audio_sha1]

    def save_texts(self, conn, uid, doc): self.texts[uid] = doc
    def load_texts(self, conn, uid): return self.texts.get(uid)

    def append_practice(self, conn, uid, record):
        self.calls.append(("append_practice", uid, record.get("mode")))
        self.practices.append(dict(record, user_id=uid, id=len(self.practices) + 1, created_at=datetime.now(timezone.utc)))
        return len(self.practices)

    def list_practices(self, conn, uid, limit=500, key=None):
        rows = [a for a in self.practices if a["user_id"] == uid and (key is None or a.get("key") == key)]
        return list(reversed(rows))[:limit]

    def count_practices(self, conn, uid): return sum(1 for a in self.practices if a["user_id"] == uid)

    def _new_id(self):
        self.next_clip_id = getattr(self, "next_clip_id", 0) + 1
        return self.next_clip_id


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
