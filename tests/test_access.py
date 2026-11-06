"""access.py 단위 테스트(이슈 #52): 환경변수가 없으면 꺼짐, 있으면 맞고 틀림, 잠금 시간."""
import unittest

import access


class Enabled(unittest.TestCase):
    def test_off_when_unset_or_blank(self):
        self.assertFalse(access.enabled({}))
        self.assertFalse(access.enabled({access.ENV_NAME: ""}))
        self.assertFalse(access.enabled({access.ENV_NAME: "   "}))
        self.assertTrue(access.check("아무거나", {}))                 # 꺼져 있으면 항상 통과

    def test_on_when_set(self):
        self.assertTrue(access.enabled({access.ENV_NAME: "pw"}))


class Check(unittest.TestCase):
    env = {access.ENV_NAME: " s3cret-Pass "}                          # 앞뒤 공백은 설정값에서만 제거

    def test_right_and_wrong(self):
        self.assertTrue(access.check("s3cret-Pass", self.env))
        self.assertFalse(access.check("s3cret-pass", self.env))       # 대소문자 구분
        self.assertFalse(access.check("", self.env))
        self.assertFalse(access.check("s3cret-Pass ", self.env))      # 입력의 공백은 그대로 비교
        self.assertFalse(access.check("s3cret-Pas", self.env))

    def test_unicode_password(self):
        env = {access.ENV_NAME: "비밀번호!"}
        self.assertTrue(access.check("비밀번호!", env))
        self.assertFalse(access.check("비밀번호?", env))


class Lock(unittest.TestCase):
    def test_no_lock_below_limit(self):
        self.assertEqual(access.lock_remaining(access.MAX_FAILS - 1, 100.0, 100.0), 0)

    def test_lock_counts_down_and_expires(self):
        n = access.MAX_FAILS
        self.assertEqual(access.lock_remaining(n, 100.0, 100.0), access.LOCK_SECONDS)
        self.assertEqual(access.lock_remaining(n, 100.0, 130.0), access.LOCK_SECONDS - 30)
        self.assertEqual(access.lock_remaining(n, 100.0, 100.0 + access.LOCK_SECONDS), 0)
        self.assertEqual(access.lock_remaining(n, 100.0, 100.5), access.LOCK_SECONDS)   # 올림


if __name__ == "__main__":
    unittest.main()
