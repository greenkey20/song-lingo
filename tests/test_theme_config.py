"""`.streamlit/config.toml`(앱 테마)의 색이 `theme.py`의 브랜드 색과 어긋나지 않는지 확인한다.
[수업에 없음] `tomllib`(파이썬 3.11 표준 라이브러리, toml 파일 읽기)을 쓴다."""
import tomllib
import unittest
from pathlib import Path

import theme

ROOT = Path(__file__).resolve().parent.parent


class ThemeConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / ".streamlit" / "config.toml", "rb") as f:
            cls.cfg = tomllib.load(f)["theme"]

    def test_brand_colors_match_theme_py(self):
        self.assertEqual(self.cfg["primaryColor"], theme.BUTTON_GREEN)
        self.assertEqual(self.cfg["textColor"], theme.FOREST)
        self.assertEqual(self.cfg["backgroundColor"], theme.SURFACE)
        self.assertEqual(self.cfg["redColor"], theme.PURPLE)
        self.assertEqual(self.cfg["yellowColor"], theme.LIME)
        self.assertEqual(self.cfg["greenColor"], theme.GREEN)

    def test_no_red_or_blue_family_left(self):
        # 화면에 빨강·파랑이 나오지 않게 한다는 결정: 두 계열의 색이 초록·보라로 바뀌어 있어야 한다.
        for key in ("redColor", "blueColor", "orangeColor"):
            self.assertNotIn(self.cfg[key].lower(), {"#ff4b4b", "#1c83e1", "#ffa421"}, key)

    def test_each_font_source_names_one_family(self):
        # Streamlit은 글꼴 설정 하나에 Google Fonts 주소를 하나만 받는다. 둘 이상이면 세션 생성이 실패해 앱이 "Connection lost"가 된다.
        for key in ("font", "headingFont", "codeFont"):
            if key in self.cfg:
                self.assertLessEqual(self.cfg[key].count("family="), 1, key)

    def test_chart_colors_have_expected_lengths(self):
        self.assertLessEqual(len(self.cfg["chartCategoricalColors"]), 4)   # 한 그림 최대 4개
        self.assertEqual(len(self.cfg["chartSequentialColors"]), 10)       # Streamlit이 요구하는 개수


if __name__ == "__main__":
    unittest.main()
