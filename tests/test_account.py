"""account.py 테스트(이슈 #52): 가짜 저장소로 가입·로그인·잠금·로그인 유지·로그아웃을 시험한다(DB 불필요)."""
import unittest
from datetime import datetime, timedelta, timezone

import account
import auth
from tests.fake_store import FakeStore

NOW = datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc)


class Signup(unittest.TestCase):
    def setUp(self):
        self.s = FakeStore()

    def test_ok_and_rules_and_duplicate(self):
        uid, msg = account.signup(None, "alice_1", "long-enough-pw", self.s)
        self.assertIsNotNone(uid)
        self.assertEqual(msg, "")
        self.assertIsNone(account.signup(None, "ab", "long-enough-pw", self.s)[0])            # 아이디 규칙
        self.assertIsNone(account.signup(None, "bob_22", "short", self.s)[0])                 # 비밀번호 규칙
        uid2, msg2 = account.signup(None, "ALICE_1", "another-long-pw", self.s)                # 대소문자 무시 중복
        self.assertIsNone(uid2)
        self.assertIn("이미", msg2)

    def test_password_is_hashed(self):
        account.signup(None, "carol_3", "my-secret-pw1", self.s)
        u = self.s.get_user(None, "carol_3")
        self.assertNotIn(b"my-secret-pw1", bytes(u["pw_hash"]) + bytes(u["pw_salt"]))


class Login(unittest.TestCase):
    def setUp(self):
        self.s = FakeStore()
        account.signup(None, "dave_4", "right-password1", self.s)

    def test_success(self):
        user, msg = account.login(None, "dave_4", "right-password1", self.s, NOW)
        self.assertEqual(user["username"], "dave_4")
        self.assertEqual(msg, "")
        self.assertEqual(self.s.users[user["id"]]["last_login"], NOW)

    def test_same_message_for_unknown_user_and_wrong_password(self):
        u1, m1 = account.login(None, "nobody_x", "whatever-pass", self.s, NOW)
        u2, m2 = account.login(None, "dave_4", "wrong-password1", self.s, NOW)
        self.assertIsNone(u1)
        self.assertIsNone(u2)
        self.assertEqual(m1, m2)                                                  # 아이디가 있는지 알려 주지 않는다
        self.assertEqual(m1, account.FAIL_MESSAGE)

    def test_lock_after_five_failures_and_blocks_correct_password(self):
        for _ in range(auth.MAX_FAILS):
            user, msg = account.login(None, "dave_4", "wrong-password1", self.s, NOW)
        self.assertIsNone(user)
        self.assertIn("초 뒤", msg)                                                # 5번째 실패 메시지가 잠금 안내
        user, msg = account.login(None, "dave_4", "right-password1", self.s, NOW + timedelta(seconds=10))
        self.assertIsNone(user)                                                    # 잠금 중에는 맞는 비밀번호도 거절
        user, msg = account.login(None, "dave_4", "right-password1", self.s, NOW + auth.LOCK + timedelta(seconds=1))
        self.assertIsNotNone(user)                                                 # 시간이 지나면 풀림

    def test_success_resets_failure_count(self):
        for _ in range(3):
            account.login(None, "dave_4", "wrong-password1", self.s, NOW)
        account.login(None, "dave_4", "right-password1", self.s, NOW)
        self.assertEqual(self.s.get_user(None, "dave_4")["failed_count"], 0)

    def test_non_string_inputs_do_not_crash(self):
        self.assertIsNone(account.login(None, None, None, self.s, NOW)[0])
        self.assertIsNone(account.login(None, "dave_4", None, self.s, NOW)[0])


class Remember(unittest.TestCase):
    def setUp(self):
        self.s = FakeStore()
        self.uid, _ = account.signup(None, "erin_5", "right-password1", self.s)

    def test_resume_logout(self):
        raw = account.start_remember(None, self.uid, self.s, NOW)
        self.assertNotIn(raw.encode(), b"".join(self.s.tokens.keys()))             # DB에는 원문이 없고 해시만
        user = account.resume(None, raw, self.s, NOW + timedelta(days=1))
        self.assertEqual(user["id"], self.uid)
        account.end_session(None, raw, self.s)
        self.assertIsNone(account.resume(None, raw, self.s, NOW + timedelta(days=1)))

    def test_bad_tokens(self):
        for bad in (None, "", "x" * 500, 123, "not-a-real-token"):
            self.assertIsNone(account.resume(None, bad, self.s, NOW))
        account.end_session(None, None, self.s)                                    # 없는 토큰 로그아웃도 오류 없음

    def test_expired(self):
        raw = account.start_remember(None, self.uid, self.s, NOW)
        self.assertIsNone(account.resume(None, raw, self.s, NOW + timedelta(days=31)))


if __name__ == "__main__":
    unittest.main()
