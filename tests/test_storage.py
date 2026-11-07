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
        self.assertEqual(self.applied[:2], ["001_init.sql", "002_rename_ids_clips.sql"])
        with self.conn() as c:
            self.assertEqual(storage.migrate(c), [])                    # 두 번째는 할 일이 없다
            versions = [r["version"] for r in c.execute("SELECT version FROM schema_migrations").fetchall()]
            tables = {r["table_name"] for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                                                           (self.schema,)).fetchall()}
        self.assertEqual(versions.count("001_init.sql"), 1)
        self.assertTrue({"users", "login_tokens", "clips", "texts", "practices", "schema_migrations"} <= tables)
        self.assertFalse({"songs", "sentences", "attempts"} & tables)             # 옛 이름은 없어졌다

    def test_ping(self):
        self.assertTrue(storage.ping(INFO))


class MigrateFromV1(unittest.TestCase):
    """001(옛 이름·모양)에 데이터를 넣은 뒤 002를 적용해도 데이터가 그대로 읽히는지 시험한다(서버 DB에 이미 001이 적용돼 있는 상황)."""

    @unittest.skipUnless(INFO, "SONGLINGO_TEST_CONNINFO가 없어 DB 테스트를 건너뜁니다")
    def test_old_rows_survive_002(self):
        schema = "t_" + uuid.uuid4().hex[:10]
        with psycopg.connect(INFO, autocommit=True) as c:
            c.execute(f'CREATE SCHEMA "{schema}"')
        try:
            with storage.connect(INFO, schema) as conn:
                conn.execute((storage.MIGRATIONS_DIR / "001_init.sql").read_text(encoding="utf-8"))
                conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
                conn.execute("INSERT INTO schema_migrations (version) VALUES ('001_init.sql')")
                uid = conn.execute("INSERT INTO users (username, pw_salt, pw_hash) VALUES ('old', %s, %s) RETURNING id", (b"s", b"h")).fetchone()["id"]
                conn.execute("INSERT INTO songs (user_id, digest, name, seconds, input, clip_start, clip_duration, languages, doc) "
                             "VALUES (%s, 'dig1', '곡', 213.4, 'file', 65.1, 20, ARRAY['en'], %s::jsonb)", (uid, '{"lines": [{"no": 1}]}'))
                conn.execute("INSERT INTO songs (user_id, digest, doc) VALUES (%s, 'nocut', %s::jsonb)", (uid, '{"lines": []}'))       # 구간 없는 행
                conn.execute("INSERT INTO sentences (user_id, doc) VALUES (%s, %s::jsonb)", (uid, '{"lines": [{"text": "hi"}]}'))
                conn.execute("INSERT INTO attempts (user_id, source, key, mode, score, stt) VALUES (%s, 'lyrics', 'k1', 'read', '{\"wer\": {}}'::jsonb, 'tiny')", (uid,))
                conn.execute("INSERT INTO attempts (user_id, source, key, mode, stt) VALUES (%s, 'lyrics', 'k2', 'dictation', NULL)", (uid,))
                conn.execute("INSERT INTO attempts (user_id, source, key, mode, stt) VALUES (%s, 'lyrics', 'k3', 'read', %s)", (uid, '{"model": "tiny"}'))
            with storage.connect(INFO, schema) as conn:
                self.assertEqual(storage.migrate(conn), ["002_rename_ids_clips.sql"])
                clips = storage.list_clips(conn, uid)
                self.assertEqual(len(clips), 1)                                            # 구간 없는 옛 행은 지워진다
                c0 = storage.load_clip(conn, uid, "dig1", 65.1, 20)
                self.assertEqual((c0["song_title"], c0["song_duration_sec"], c0["input_type"], c0["languages"]), ("곡", 213.4, "file", ["en"]))
                self.assertEqual(c0["doc"], {"lines": [{"no": 1}]})
                self.assertEqual(storage.load_texts(conn, uid), {"lines": [{"text": "hi"}]})
                rows = {r["key"]: r for r in storage.list_practices(conn, uid)}
                self.assertEqual(rows["k1"]["scoring"], {"wer": {}})
                self.assertEqual(rows["k1"]["stt_settings"], "tiny")                       # 글이던 값은 JSON 글자로
                self.assertIsNone(rows["k2"]["stt_settings"])
                self.assertEqual(rows["k3"]["stt_settings"], {"model": "tiny"})            # JSON 글자는 객체로
                self.assertTrue(all(r["clip_id"] is None and r["created_at"] for r in rows.values()))
                self.assertIsNotNone(conn.execute("SELECT updated_at FROM users WHERE id = %s", (uid,)).fetchone()["updated_at"])
                new_id = storage.save_clip(conn, uid, "dig1", 90, 15, {"lines": []})      # 새 id가 이어서 발급된다
                self.assertNotEqual(new_id, c0["id"])
        finally:
            with psycopg.connect(INFO, autocommit=True) as c:
                c.execute(f'DROP SCHEMA "{schema}" CASCADE')


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


class Clips(WithDb):
    DOC = {"lines": [{"no": 1, "text": "hello there", "status": "candidate"}, {"no": 2, "text": "again", "status": "confirmed"}]}

    def test_save_load_upsert_list(self):
        uid, _ = self.new_user()
        with self.conn() as c:
            self.assertIsNone(storage.load_clip(c, uid, "d1", 65, 20))
            cid = storage.save_clip(c, uid, "d1", 65, 20, self.DOC, song_title="내 곡.mp3", song_duration_sec=213.4, input_type="file", languages=["en", "ja"])
            s = storage.load_clip(c, uid, "d1", 65, 20)
            self.assertEqual(s["id"], cid)
            self.assertEqual(s["doc"], self.DOC)                              # JSONB가 파이썬 dict로 돌아온다
            self.assertEqual((s["song_title"], s["clip_start_sec"], s["clip_duration_sec"], s["languages"]), ("내 곡.mp3", 65.0, 20.0, ["en", "ja"]))
            self.assertIsInstance(s["clip_start_sec"], float)                 # NUMERIC(Decimal)을 float로 바꿔 돌려준다
            again = storage.save_clip(c, uid, "d1", 65, 20, {"lines": []}, song_title="이름 바꿈")      # 같은 곡·같은 구간이면 덮어씀(같은 id)
            self.assertEqual(again, cid)
            self.assertEqual(storage.load_clip(c, uid, "d1", 65, 20)["song_title"], "이름 바꿈")
            self.assertEqual(storage.load_clip_by_id(c, uid, cid)["audio_sha1"], "d1")

    def test_same_song_different_ranges_are_separate_rows(self):
        uid, _ = self.new_user()
        with self.conn() as c:
            a = storage.save_clip(c, uid, "song1", 10, 15, self.DOC, song_title="곡")
            b = storage.save_clip(c, uid, "song1", 40, 15, {"lines": []}, song_title="곡")
            d = storage.save_clip(c, uid, "song1", 10, 20, self.DOC, song_title="곡")      # 시작이 같아도 길이가 다르면 다른 구간
            self.assertEqual(len({a, b, d}), 3)
            of = storage.list_clips_of(c, uid, "song1")
            self.assertEqual([(x["clip_start_sec"], x["clip_duration_sec"]) for x in of], [(10.0, 15.0), (10.0, 20.0), (40.0, 15.0)])
            self.assertEqual({x["id"]: x["n_lines"] for x in storage.list_clips(c, uid)}, {a: 2, b: 0, d: 2})
            self.assertNotIn("doc", of[0])                                    # 목록에는 가사 전체를 싣지 않는다

    def test_float_noise_does_not_create_a_second_row(self):
        uid, _ = self.new_user()
        with self.conn() as c:
            a = storage.save_clip(c, uid, "s", 0.1 + 0.2, 15, {"lines": []})            # 0.30000000000000004
            b = storage.save_clip(c, uid, "s", 0.3, 15, {"lines": []})
            self.assertEqual(a, b)

    def test_users_are_isolated(self):
        a, _ = self.new_user()
        b, _ = self.new_user()
        with self.conn() as c:
            cid = storage.save_clip(c, a, "same-sha", 0, 10, self.DOC, song_title="A의 곡")
            self.assertIsNone(storage.load_clip(c, b, "same-sha", 0, 10))
            self.assertIsNone(storage.load_clip_by_id(c, b, cid))               # 남의 clip id로도 못 읽는다
            self.assertEqual(storage.list_clips(c, b), [])
            self.assertEqual(storage.list_clips_of(c, b, "same-sha"), [])
            storage.save_clip(c, b, "same-sha", 0, 10, {"lines": []}, song_title="B의 곡")   # 같은 지문·구간이어도 사용자별로 따로
            self.assertEqual(storage.load_clip(c, a, "same-sha", 0, 10)["song_title"], "A의 곡")

    def test_texts(self):
        uid, _ = self.new_user()
        with self.conn() as c:
            self.assertIsNone(storage.load_texts(c, uid))
            storage.save_texts(c, uid, {"lines": [{"text": "朝の光", "lang": "ja"}]})
            storage.save_texts(c, uid, {"lines": [{"text": "Bonjour", "lang": "fr"}]})
            self.assertEqual(storage.load_texts(c, uid)["lines"][0]["lang"], "fr")


class Practices(WithDb):
    def test_append_list_order_filter_and_json(self):
        import numpy as np
        uid, _ = self.new_user()
        with self.conn() as c:
            cid = storage.save_clip(c, uid, "s", 0, 10, {"lines": []})
            first = storage.append_practice(c, uid, {"source": "song", "key": "h_1", "mode": "read", "lang": "en", "ref_text": "hello there",
                                                     "hyp_text": "hello their", "clip_id": cid,
                                                     "scoring": {"wer": np.float64(0.5), "ops": [("equal", "hello", "hello")]},
                                                     "stt_settings": {"model": "tiny", "device": "cpu"}})
            second = storage.append_practice(c, uid, {"source": "lyrics", "key": "h_2", "mode": "azure", "hyp_text": "hello", "azure": {"pron": 79.0}})
            rows = storage.list_practices(c, uid)
            self.assertEqual([r["id"] for r in rows], [second, first])           # 최신 순
            self.assertEqual(rows[1]["scoring"]["wer"], 0.5)                      # numpy 값도 저장·복원된다
            self.assertEqual(rows[1]["scoring"]["ops"], [["equal", "hello", "hello"]])
            self.assertEqual(rows[1]["stt_settings"], {"model": "tiny", "device": "cpu"})   # dict가 JSONB로 그대로 저장된다(따라읽기 기록이 안 남던 버그의 회귀 방지)
            self.assertEqual((rows[1]["clip_id"], rows[0]["clip_id"]), (cid, None))
            self.assertEqual((rows[0]["azure"], rows[0]["hyp_text"]), ({"pron": 79.0}, "hello"))
            self.assertIsNone(rows[0]["scoring"])
            self.assertIsNotNone(rows[0]["created_at"])
            self.assertEqual([r["id"] for r in storage.list_practices(c, uid, key="h_1")], [first])
            self.assertEqual(len(storage.list_practices(c, uid, limit=1)), 1)
            self.assertEqual(storage.count_practices(c, uid), 2)

    def test_practices_are_per_user(self):
        a, _ = self.new_user()
        b, _ = self.new_user()
        with self.conn() as c:
            storage.append_practice(c, a, {"source": "song", "key": "k", "mode": "read"})
            self.assertEqual(storage.list_practices(c, b), [])
            self.assertEqual(storage.count_practices(c, b), 0)


class Cascade(WithDb):
    def test_delete_user_removes_everything(self):
        uid, name = self.new_user()
        other, _ = self.new_user()
        with self.conn() as c:
            storage.add_token(c, uid, auth.token_hash("t"), auth.token_expiry(NOW))
            cid = storage.save_clip(c, uid, "d", 0, 10, {"lines": []})
            storage.save_texts(c, uid, {"lines": []})
            storage.append_practice(c, uid, {"source": "song", "key": "k", "mode": "read", "clip_id": cid})
            other_cid = storage.save_clip(c, other, "d", 0, 10, {"lines": []})
            self.assertEqual(storage.delete_user(c, uid), 1)
            self.assertIsNone(storage.get_user(c, name))
            for table in ("login_tokens", "clips", "texts", "practices"):
                self.assertEqual(c.execute(f"SELECT count(*) AS n FROM {table} WHERE user_id = %s", (uid,)).fetchone()["n"], 0, table)
            self.assertIsNotNone(storage.load_clip_by_id(c, other, other_cid))             # 다른 사용자의 데이터는 그대로
            self.assertEqual(storage.delete_user(c, uid), 0)


if __name__ == "__main__":
    unittest.main()
