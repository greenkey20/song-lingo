"""auth.py 단위 테스트(이슈 #52): 해시·검증·규칙·토큰·잠금. DB 없이 돈다."""
import unittest
from datetime import datetime, timedelta, timezone

import auth

NOW = datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc)


class Password(unittest.TestCase):
    def test_hash_and_verify(self):
        salt, h = auth.hash_password("correct horse")
        self.assertEqual(len(salt), 16)
        self.assertEqual(len(h), auth.DKLEN)
        self.assertTrue(auth.verify_password("correct horse", salt, h))
        self.assertFalse(auth.verify_password("correct horsE", salt, h))
        self.assertFalse(auth.verify_password("", salt, h))

    def test_same_password_different_salt_different_hash(self):
        s1, h1 = auth.hash_password("same-password")
        s2, h2 = auth.hash_password("same-password")
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(h1, h2)

    def test_verify_accepts_memoryview(self):                      # psycopg는 BYTEA를 bytes나 memoryview로 돌려줄 수 있다
        salt, h = auth.hash_password("pw-12345678")
        self.assertTrue(auth.verify_password("pw-12345678", memoryview(salt), memoryview(h)))

    def test_unicode_password(self):
        salt, h = auth.hash_password("비밀번호-12345")
        self.assertTrue(auth.verify_password("비밀번호-12345", salt, h))


class Rules(unittest.TestCase):
    def test_username(self):
        for ok in ["abc", "Eun_young.1", "은영이", "a-b-c", "x" * 20]:
            self.assertIsNone(auth.validate_username(ok), ok)
        for bad in ["", "ab", "x" * 21, "has space", "a/b", "한글!", "a@b", None]:
            self.assertIsNotNone(auth.validate_username(bad), bad)

    def test_password(self):
        self.assertIsNone(auth.validate_password("12345678", "alice"))
        self.assertIsNotNone(auth.validate_password("1234567", "alice"))        # 너무 짧음
        self.assertIsNotNone(auth.validate_password("x" * 129, "alice"))        # 너무 김
        self.assertIsNotNone(auth.validate_password("Alice1234"[:8], "alice1234"[:8]))   # 아이디와 같음(대소문자 무시)
        self.assertIsNotNone(auth.validate_password(None))


class Token(unittest.TestCase):
    def test_token_is_random_and_hash_is_stable(self):
        a, b = auth.new_token(), auth.new_token()
        self.assertNotEqual(a, b)
        self.assertGreaterEqual(len(a), 40)
        self.assertEqual(auth.token_hash(a), auth.token_hash(a))
        self.assertNotEqual(auth.token_hash(a), auth.token_hash(b))
        self.assertEqual(len(auth.token_hash(a)), 32)

    def test_expiry_is_30_days(self):
        self.assertEqual(auth.token_expiry(NOW), NOW + timedelta(days=30))


class Lock(unittest.TestCase):
    def test_not_locked_when_none_or_past(self):
        self.assertFalse(auth.is_locked(None, NOW))
        self.assertFalse(auth.is_locked(NOW - timedelta(seconds=1), NOW))
        self.assertTrue(auth.is_locked(NOW + timedelta(seconds=1), NOW))

    def test_remaining_seconds_rounds_up(self):
        self.assertEqual(auth.lock_remaining_seconds(None, NOW), 0)
        self.assertEqual(auth.lock_remaining_seconds(NOW + timedelta(seconds=299.2), NOW), 300)
        self.assertEqual(auth.lock_remaining_seconds(NOW - timedelta(seconds=5), NOW), 0)

    def test_failures_lock_on_fifth(self):
        count, until = 0, None
        for i in range(1, auth.MAX_FAILS):
            count, until = auth.after_failure(count, NOW)
            self.assertEqual((count, until), (i, None))
        count, until = auth.after_failure(count, NOW)                    # 5번째 실패
        self.assertEqual(count, 0)
        self.assertEqual(until, NOW + auth.LOCK)


if __name__ == "__main__":
    unittest.main()
