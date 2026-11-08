"""DB 없이 계정·저장 로직과 화면(AppTest)을 시험하려고 만든 **메모리 가짜 저장소**. storage.py와 같은 함수 이름을 갖는다.
진짜 SQL의 의미(사용자 격리, 대소문자 무시, 연쇄 삭제 등)는 tests/test_storage.py가 진짜 DB로 확인하고, 이 가짜는 호출 흐름만 시험한다."""
from contextlib import contextmanager
from datetime import datetime, timezone

import storage as real


class FakeStore:
    UsernameTaken = real.UsernameTaken

    def __init__(self):
        self.users, self.tokens, self.clips, self.texts, self.practices = {}, {}, {}, {}, []
        self.meanings = {}
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
        self.texts = {k: v for k, v in self.texts.items() if v["user_id"] != uid}
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
        lines = v["doc"].get("lines", [])
        first = next((l["text"] for l in lines if l.get("status") != "dropped"), None)
        return {k: x for k, x in v.items() if k != "doc"} | {"n_lines": len(lines), "first_text": first, "created_at": v.get("created_at") or v["updated_at"]}

    def list_clips(self, conn, uid):
        return [self._light(v) for v in sorted(self.clips.values(), key=lambda v: v["updated_at"], reverse=True) if v["user_id"] == uid]

    def list_clips_of(self, conn, uid, audio_sha1):
        return [self._light(v) for v in sorted(self.clips.values(), key=lambda v: (v["clip_start_sec"], v["clip_duration_sec"]))
                if v["user_id"] == uid and v["audio_sha1"] == audio_sha1]

    def _line_id(self, kind, owner, no):
        ids = self.__dict__.setdefault("line_ids", {})
        return ids.setdefault((kind, owner, no), len(ids) + 1)

    def clip_line_ids(self, conn, uid, clip_id):
        clip = self.load_clip_by_id(conn, uid, clip_id)
        return {l["no"]: self._line_id("clip", clip_id, l["no"]) for l in (clip["doc"].get("lines", []) if clip else [])}

    def text_line_ids(self, conn, uid, text_id):
        t = self.texts.get(text_id)
        return {i: self._line_id("text", text_id, i) for i, _ in enumerate((t["doc"].get("lines", []) if t and t["user_id"] == uid else []), 1)}

    def count_texts(self, conn, uid): return sum(1 for t in self.texts.values() if t["user_id"] == uid)

    def save_texts(self, conn, uid, doc, text_id=None, title=None):
        title = (title or "").strip() or None
        now = datetime.now(timezone.utc)
        if text_id is None:
            if self.count_texts(conn, uid) >= real.MAX_TEXT_SETS:
                raise real.TextSetLimit("limit")
            text_id = self._new_id()
            self.texts[text_id] = {"id": text_id, "user_id": uid, "created_at": now}
        elif text_id not in self.texts or self.texts[text_id]["user_id"] != uid:
            raise real.TextSetMissing("missing")
        self.texts[text_id].update(title=title, doc=doc, updated_at=now)
        self.calls.append(("save_texts", uid, text_id))
        return text_id

    def list_texts(self, conn, uid):
        rows = sorted((t for t in self.texts.values() if t["user_id"] == uid), key=lambda t: (t["updated_at"], t["id"]), reverse=True)
        return [{"id": t["id"], "title": t["title"], "created_at": t["created_at"], "updated_at": t["updated_at"],
                 "n_lines": len(t["doc"].get("lines", [])), "first_text": next((l["text"] for l in t["doc"].get("lines", [])), None)} for t in rows]

    def load_text_by_id(self, conn, uid, text_id):
        t = self.texts.get(text_id)
        if not t or t["user_id"] != uid:
            return None
        return {"id": text_id, "title": t["title"], "lines": [dict(l) for l in t["doc"].get("lines", [])]}

    def delete_text(self, conn, uid, text_id):
        t = self.texts.get(text_id)
        if not t or t["user_id"] != uid:
            return 0
        del self.texts[text_id]
        return 1

    def append_practice(self, conn, uid, record):
        self.calls.append(("append_practice", uid, record.get("mode")))
        self.practices.append(dict(record, user_id=uid, id=len(self.practices) + 1, created_at=datetime.now(timezone.utc)))
        return len(self.practices)

    def list_practices(self, conn, uid, limit=500, key=None):
        rows = [a for a in self.practices if a["user_id"] == uid and (key is None or a.get("key") == key)]
        return list(reversed(rows))[:limit]

    def count_practices(self, conn, uid): return sum(1 for a in self.practices if a["user_id"] == uid)

    def get_meaning(self, conn, cache_key, kind, prompt_version): return self.meanings.get((cache_key, kind, prompt_version))

    def put_meaning(self, conn, cache_key, kind, lang, content, model, prompt_version):
        k = (cache_key, kind, prompt_version)
        if k in self.meanings:
            return 0
        self.meanings[k] = content
        return 1

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
