"""storage.py 단위 테스트(이슈 #52).

- 접속 문자열 만들기 등 DB 없이 되는 테스트는 항상 돈다.
- **진짜 PostgreSQL이 필요한 테스트**는 환경변수 `SONGLINGO_TEST_CONNINFO`(libpq 접속 문자열, 예: "host=127.0.0.1 port=55432 dbname=songlingo_db user=… password=…")가
  있을 때만 돈다(없으면 건너뜀). 테스트마다 **임시 스키마**(`t_<랜덤>`)를 만들어 그 안에서만 실행하고 끝나면 지우므로 같은 DB의 다른 데이터를 건드리지 않는다.
  개발용 DB는 `docker run -d --name songlingo-local-db -e POSTGRES_USER=… -e POSTGRES_PASSWORD=… -e POSTGRES_DB=songlingo_db -p 127.0.0.1:55432:5432 postgres:16-alpine`.
"""
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

import psycopg

import auth
import storage

INFO = os.environ.get("SONGLINGO_TEST_CONNINFO", "")
NOW = datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc)


class NoDb(unittest.TestCase):
    def test_conninfo_needs_name_and_user(self):
        self.assertEqual(storage.conninfo({}), "")
        self.assertEqual(storage.conninfo({"DB_NAME": "x"}), "")
        self.assertFalse(storage.enabled({"DB_USER": "u"}))
        self.assertTrue(storage.enabled({"DB_NAME": "x", "DB_USER": "u"}))

    def test_conninfo_defaults_and_special_password(self):
        info = storage.conninfo({"DB_NAME": "songlingo_db", "DB_USER": "postgres", "DB_PASSWORD": "pa ss'wo\\rd"})
        d = psycopg.conninfo.conninfo_to_dict(info)
        self.assertEqual((d["host"], d["port"], d["dbname"], d["user"]), ("127.0.0.1", "5433", "songlingo_db", "postgres"))
        self.assertEqual(d["password"], "pa ss'wo\\rd")                 # 공백·따옴표·역슬래시가 있어도 그대로 전달된다
        self.assertEqual(d["connect_timeout"], "3")

    def test_connect_without_settings_raises(self):
        with self.assertRaises(storage.StorageError):
            with storage.connect(""):
                pass

    def test_invalid_schema_name_is_rejected_before_connecting(self):
        old = os.environ.get("DB_SCHEMA")
        os.environ["DB_SCHEMA"] = 'x"; DROP SCHEMA public; --'
        try:
            with self.assertRaises(storage.StorageError):
                with storage.connect("host=127.0.0.1 port=1 dbname=x user=x connect_timeout=1"):
                    pass
        finally:
            if old is None:
                os.environ.pop("DB_SCHEMA", None)
            else:
                os.environ["DB_SCHEMA"] = old

    def test_ping_false_when_unreachable(self):
        self.assertFalse(storage.ping("host=127.0.0.1 port=1 dbname=x user=x connect_timeout=1"))

    def test_jsonable_handles_numpy_and_tuples(self):
        import json
        import numpy as np
        out = json.dumps({"a": np.float64(1.5), "b": np.int64(2), "c": (1, 2), "d": np.array([1, 2])}, default=storage._default)
        self.assertEqual(json.loads(out), {"a": 1.5, "b": 2, "c": [1, 2], "d": [1, 2]})


@unittest.skipUnless(INFO, "SONGLINGO_TEST_CONNINFO가 없어 DB 테스트를 건너뜁니다")
class WithDb(unittest.TestCase):
    schema = None

    @classmethod
    def setUpClass(cls):
        cls.schema = "t_" + uuid.uuid4().hex[:10]
        with psycopg.connect(INFO, autocommit=True) as c:
            c.execute(f'CREATE SCHEMA "{cls.schema}"')
        with storage.connect(INFO, cls.schema) as conn:
            cls.applied = storage.migrate(conn)

    @classmethod
    def tearDownClass(cls):
        with psycopg.connect(INFO, autocommit=True) as c:
            c.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')

    def conn(self):
        return storage.connect(INFO, self.schema)

    def new_user(self, name=None):
        name = name or "u" + uuid.uuid4().hex[:8]
        salt, h = auth.hash_password("pw-" + name)
        with self.conn() as c:
            return storage.create_user(c, name, salt, h), name


class Migrations(WithDb):
    def test_applied_and_idempotent(self):
        self.assertIn("001_init.sql", self.applied)
        with self.conn() as c:
            self.assertEqual(storage.migrate(c), [])                    # 두 번째는 할 일이 없다
            versions = [r["version"] for r in c.execute("SELECT version FROM schema_migrations").fetchall()]
            tables = {r["table_name"] for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                                                           (self.schema,)).fetchall()}
        self.assertEqual(versions.count("001_init.sql"), 1)
        self.assertTrue({"users", "login_tokens", "songs", "sentences", "attempts", "schema_migrations"} <= tables)

    def test_ping(self):
        self.assertTrue(storage.ping(INFO))


class Users(WithDb):
    def test_create_and_get_case_insensitive(self):
        uid, name = self.new_user("Alice" + uuid.uuid4().hex[:4])
        with self.conn() as c:
            self.assertEqual(storage.get_user(c, name.lower())["id"], uid)
            self.assertEqual(storage.get_user(c, name.upper())["id"], uid)
            self.assertIsNone(storage.get_user(c, "nobody-" + uuid.uuid4().hex))
            self.assertTrue(storage.get_user_by_id(c, uid)["save_on"])

    def test_username_unique_ignoring_case(self):
        _, name = self.new_user("Bob" + uuid.uuid4().hex[:4])
        with self.assertRaises(storage.UsernameTaken):
            self.new_user(name.lower())
        with self.conn() as c:                                          # 실패한 뒤에도 같은 연결/트랜잭션 흐름이 살아 있어야 한다
            self.assertIsNotNone(storage.get_user(c, name))

    def test_password_roundtrip(self):
        uid, name = self.new_user()
        with self.conn() as c:
            u = storage.get_user(c, name)
        self.assertTrue(auth.verify_password("pw-" + name, u["pw_salt"], u["pw_hash"]))     # BYTEA를 되읽어도 검증된다(memoryview 포함)
        self.assertFalse(auth.verify_password("wrong-password", u["pw_salt"], u["pw_hash"]))

    def test_failure_lock_and_success_reset(self):
        uid, name = self.new_user()
        count, until = 0, None
        for _ in range(auth.MAX_FAILS):
            count, until = auth.after_failure(count, NOW)
        with self.conn() as c:
            storage.record_login_failure(c, uid, count, until)
            u = storage.get_user(c, name)
            self.assertTrue(auth.is_locked(u["locked_until"], NOW))
            storage.record_login_success(c, uid, NOW + timedelta(minutes=10))
            u = storage.get_user(c, name)
        self.assertEqual(u["failed_count"], 0)
        self.assertIsNone(u["locked_until"])
        self.assertIsNotNone(u["last_login"])

    def test_set_password_resets_lock_and_tokens(self):
        uid, name = self.new_user()
        count, until = 0, None
        for _ in range(auth.MAX_FAILS):
            count, until = auth.after_failure(count, NOW)
        salt, h = auth.hash_password("brand-new-password")
        with self.conn() as c:
            storage.record_login_failure(c, uid, count, until)
            storage.add_token(c, uid, auth.token_hash("tok"), auth.token_expiry(NOW))
            storage.set_password(c, uid, salt, h)
            u = storage.get_user(c, name)
            self.assertTrue(auth.verify_password("brand-new-password", u["pw_salt"], u["pw_hash"]))
            self.assertFalse(auth.verify_password("pw-" + name, u["pw_salt"], u["pw_hash"]))
            self.assertIsNone(u["locked_until"])
            self.assertEqual(u["failed_count"], 0)
            self.assertIsNone(storage.user_by_token(c, auth.token_hash("tok"), NOW, auth.token_expiry(NOW)))       # 토큰도 지워짐

    def test_set_save_on(self):
        uid, name = self.new_user()
        with self.conn() as c:
            storage.set_save_on(c, uid, False)
            self.assertFalse(storage.get_user(c, name)["save_on"])

    def test_sql_injection_like_username_is_just_data(self):
        evil = "x'; DROP TABLE users;--"
        uid, _ = self.new_user(evil)
        with self.conn() as c:
            self.assertEqual(storage.get_user(c, evil)["id"], uid)
            self.assertEqual(c.execute("SELECT count(*) AS n FROM users").fetchone()["n"] >= 1, True)    # users 표가 살아 있다


class Tokens(WithDb):
    def test_token_lookup_renews_and_expires(self):
        uid, _ = self.new_user()
        raw = auth.new_token()
        th = auth.token_hash(raw)
        with self.conn() as c:
            storage.add_token(c, uid, th, auth.token_expiry(NOW))
            u = storage.user_by_token(c, th, NOW + timedelta(days=1), auth.token_expiry(NOW + timedelta(days=1)))
            self.assertEqual(u["id"], uid)
            # 롤링: 1일째 접속으로 만료가 31일째로 늦춰졌고(원래는 30일째), 30일째에 접속하면 다시 60일째로, 59일째에도 살아 있다
            # (경계값인 만료 시각 그 순간은 "이미 만료"로 본다: expires_at > now 이므로 일부러 경계를 피해서 시험)
            self.assertIsNotNone(storage.user_by_token(c, th, NOW + timedelta(days=30), auth.token_expiry(NOW + timedelta(days=30))))
            self.assertIsNotNone(storage.user_by_token(c, th, NOW + timedelta(days=59), auth.token_expiry(NOW + timedelta(days=59))))
            # 접속 없이 만료 시각이 지나면 거절
            self.assertIsNone(storage.user_by_token(c, th, NOW + timedelta(days=200), auth.token_expiry(NOW + timedelta(days=200))))
            # 만료 시각 정확히 그 순간은 거절(경계값)
            storage.add_token(c, storage.get_user_by_id(c, uid)["id"], auth.token_hash("edge"), NOW + timedelta(days=5))
            self.assertIsNone(storage.user_by_token(c, auth.token_hash("edge"), NOW + timedelta(days=5), auth.token_expiry(NOW)))

    def test_unknown_token_and_delete(self):
        uid, _ = self.new_user()
        th = auth.token_hash(auth.new_token())
        with self.conn() as c:
            self.assertIsNone(storage.user_by_token(c, auth.token_hash("nope"), NOW, auth.token_expiry(NOW)))
            storage.add_token(c, uid, th, auth.token_expiry(NOW))
            storage.delete_token(c, th)
            self.assertIsNone(storage.user_by_token(c, th, NOW, auth.token_expiry(NOW)))

    def test_delete_all_tokens_and_purge(self):
        uid, _ = self.new_user()
        with self.conn() as c:
            storage.add_token(c, uid, auth.token_hash("a1"), NOW - timedelta(days=1))      # 이미 만료
            storage.add_token(c, uid, auth.token_hash("a2"), NOW + timedelta(days=1))
            self.assertEqual(storage.purge_expired_tokens(c, NOW), 1)
            self.assertEqual(storage.delete_user_tokens(c, uid), 1)


class Songs(WithDb):
    DOC = {"lines": [{"no": 1, "text": "hello there", "status": "candidate"}, {"no": 2, "text": "again", "status": "confirmed"}]}

    def test_save_load_upsert_list_delete(self):
        uid, _ = self.new_user()
        with self.conn() as c:
            self.assertIsNone(storage.load_song(c, uid, "d1"))
            storage.save_song(c, uid, "d1", self.DOC, name="내 곡.mp3", seconds=213.4, input="file", clip_start=65, clip_duration=20, languages=["en", "ja"])
            s = storage.load_song(c, uid, "d1")
            self.assertEqual(s["doc"], self.DOC)                              # JSONB가 파이썬 dict로 돌아온다
            self.assertEqual((s["name"], s["clip_start"], s["clip_duration"], s["languages"]), ("내 곡.mp3", 65, 20, ["en", "ja"]))
            storage.save_song(c, uid, "d1", {"lines": []}, name="이름 바꿈", clip_start=70)      # 같은 곡 지문이면 덮어씀
            self.assertEqual(storage.load_song(c, uid, "d1")["name"], "이름 바꿈")
            storage.save_song(c, uid, "d2", self.DOC)
            songs = storage.list_songs(c, uid)
            self.assertEqual({x["digest"] for x in songs}, {"d1", "d2"})
            self.assertEqual({x["digest"]: x["n_lines"] for x in songs}, {"d1": 0, "d2": 2})
            self.assertNotIn("doc", songs[0])                                 # 목록에는 가사 전체를 싣지 않는다
            self.assertEqual(storage.delete_song(c, uid, "d1"), 1)
            self.assertEqual(storage.delete_song(c, uid, "d1"), 0)

    def test_users_are_isolated(self):
        a, _ = self.new_user()
        b, _ = self.new_user()
        with self.conn() as c:
            storage.save_song(c, a, "same-digest", self.DOC, name="A의 곡")
            self.assertIsNone(storage.load_song(c, b, "same-digest"))
            self.assertEqual(storage.list_songs(c, b), [])
            self.assertEqual(storage.delete_song(c, b, "same-digest"), 0)       # 남의 곡은 지울 수 없다
            self.assertIsNotNone(storage.load_song(c, a, "same-digest"))
            storage.save_song(c, b, "same-digest", {"lines": []}, name="B의 곡")  # 같은 지문이어도 사용자별로 따로
            self.assertEqual(storage.load_song(c, a, "same-digest")["name"], "A의 곡")

    def test_sentences(self):
        uid, _ = self.new_user()
        with self.conn() as c:
            self.assertIsNone(storage.load_sentences(c, uid))
            storage.save_sentences(c, uid, {"lines": [{"text": "朝の光", "lang": "ja"}]})
            storage.save_sentences(c, uid, {"lines": [{"text": "Bonjour", "lang": "fr"}]})
            self.assertEqual(storage.load_sentences(c, uid)["lines"][0]["lang"], "fr")


class Attempts(WithDb):
    def test_append_list_order_filter_and_json(self):
        import numpy as np
        uid, _ = self.new_user()
        with self.conn() as c:
            first = storage.append_attempt(c, uid, {"source": "song", "key": "h_1", "mode": "read", "lang": "en", "ref_text": "hello there",
                                                    "hyp_text": "hello their", "score": {"wer": np.float64(0.5), "ops": [("equal", "hello", "hello")]},
                                                    "stt": "tiny/cpu/int8"})
            second = storage.append_attempt(c, uid, {"source": "lyrics", "key": "h_2", "mode": "azure", "azure": {"pron": 79.0}})
            rows = storage.list_attempts(c, uid)
            self.assertEqual([r["id"] for r in rows], [second, first])           # 최신 순
            self.assertEqual(rows[1]["score"]["wer"], 0.5)                        # numpy 값도 저장·복원된다
            self.assertEqual(rows[1]["score"]["ops"], [["equal", "hello", "hello"]])
            self.assertEqual(rows[0]["azure"], {"pron": 79.0})
            self.assertIsNone(rows[0]["score"])
            self.assertEqual([r["id"] for r in storage.list_attempts(c, uid, key="h_1")], [first])
            self.assertEqual(len(storage.list_attempts(c, uid, limit=1)), 1)
            self.assertEqual(storage.count_attempts(c, uid), 2)

    def test_attempts_are_per_user(self):
        a, _ = self.new_user()
        b, _ = self.new_user()
        with self.conn() as c:
            storage.append_attempt(c, a, {"source": "song", "key": "k", "mode": "read"})
            self.assertEqual(storage.list_attempts(c, b), [])
            self.assertEqual(storage.count_attempts(c, b), 0)


class Cascade(WithDb):
    def test_delete_user_removes_everything(self):
        uid, name = self.new_user()
        other, _ = self.new_user()
        with self.conn() as c:
            storage.add_token(c, uid, auth.token_hash("t"), auth.token_expiry(NOW))
            storage.save_song(c, uid, "d", {"lines": []})
            storage.save_sentences(c, uid, {"lines": []})
            storage.append_attempt(c, uid, {"source": "song", "key": "k", "mode": "read"})
            storage.save_song(c, other, "d", {"lines": []})
            self.assertEqual(storage.delete_user(c, uid), 1)
            self.assertIsNone(storage.get_user(c, name))
            for table in ("login_tokens", "songs", "sentences", "attempts"):
                self.assertEqual(c.execute(f"SELECT count(*) AS n FROM {table} WHERE user_id = %s", (uid,)).fetchone()["n"], 0, table)
            self.assertIsNotNone(storage.load_song(c, other, "d"))             # 다른 사용자의 데이터는 그대로
            self.assertEqual(storage.delete_user(c, uid), 0)


if __name__ == "__main__":
    unittest.main()
