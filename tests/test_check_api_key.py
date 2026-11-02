"""scripts/check_api_key.py의 마스킹과 우선순위 판정 테스트. 실행: python -m unittest tests.test_check_api_key -v
진짜 키는 쓰지 않고, 모양만 비슷한 가짜 문자열로 확인한다. 스크립트의 main()(.env를 읽는 부분)은 부르지 않는다."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import check_api_key as cak  # noqa: E402

FAKE_A = "sk-proj-" + "a" * 20 + "AAAA"
FAKE_B = "sk-proj-" + "b" * 20 + "BBBB"


class Mask(unittest.TestCase):
    def test_shows_only_prefix_suffix_and_length(self):
        m = cak.mask(FAKE_A)
        self.assertEqual(m, f"sk-proj…AAAA (길이 {len(FAKE_A)})")
        self.assertNotIn("a" * 8, m)                           # 가운데는 나오지 않는다

    def test_empty_and_short_values_are_not_revealed(self):
        self.assertEqual(cak.mask(None), "(없음)")
        self.assertEqual(cak.mask("short"), "(짧은 값, 길이 5)")


class Diagnose(unittest.TestCase):
    def test_environment_variable_wins_over_env_file(self):
        source, notes = cak.diagnose(FAKE_A, FAKE_B)
        self.assertEqual(source, "환경 변수(.env가 아님)")
        self.assertTrue(any("무시" in n for n in notes))       # load_dotenv(override=False)의 동작

    def test_same_key_in_both(self):
        source, notes = cak.diagnose(FAKE_A, FAKE_A)
        self.assertEqual(source, "환경 변수(.env가 아님)")
        self.assertTrue(any("같은 키" in n for n in notes))

    def test_env_file_used_when_no_environment_variable(self):
        self.assertEqual(cak.diagnose(None, FAKE_B)[0], ".env")

    def test_no_key_anywhere(self):
        source, notes = cak.diagnose(None, None)
        self.assertIsNone(source)
        self.assertTrue(notes)


if __name__ == "__main__":
    unittest.main()
