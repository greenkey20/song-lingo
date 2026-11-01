"""scripts/check_notebook.py 테스트. 실행: python -m unittest tests.test_check_notebook -v
작은 가짜 노트북을 임시 폴더에 만들어 스크립트를 실제로 실행(subprocess)하고, 종료 코드와 출력을 확인한다.
(OpenAI API·Whisper는 쓰지 않는다.)"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_notebook.py"


def make_notebook(path, cells):
    """(종류, 소스) 목록으로 최소한의 노트북 파일을 만든다."""
    nb = {"cells": [{"cell_type": kind, "source": src.splitlines(keepends=True), "metadata": {},
                     **({"outputs": [], "execution_count": None} if kind == "code" else {})}
                    for kind, src in cells],
          "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    Path(path).write_text(json.dumps(nb, ensure_ascii=False), encoding="utf-8")


class CheckNotebook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def run_script(self, cells, *extra):
        nb = self.dir / "nb.ipynb"
        make_notebook(nb, cells)
        return subprocess.run([sys.executable, str(SCRIPT), str(nb), "--out", str(self.dir / "figs"), *extra],
                              capture_output=True, text=True, cwd=ROOT, timeout=120)

    def test_all_cells_run_and_show_is_saved_as_png(self):
        r = self.run_script([
            ("markdown", "# 제목은 실행하지 않는다"),
            ("code", "x = 41"),
            ("code", "import matplotlib.pyplot as plt\nplt.plot([0, 1])\nplt.show()"),   # 변수 x를 다음 셀이 이어 쓴다
            ("code", "assert x == 41"),
        ])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("코드 셀 3개 모두 실행됨", r.stdout)
        self.assertTrue((self.dir / "figs" / "fig1.png").exists())

    def test_input_is_answered_without_waiting(self):
        r = self.run_script([("code", 'a = input("들은 대로 적어 보세요 > ")\nassert a == "정답", a')], "--answer", "정답")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_failure_reports_cell_number_and_stops(self):
        r = self.run_script([("code", "print('first')"), ("code", "raise ValueError('boom')"), ("code", "print('NEVER')")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("[셀 1] 실패", r.stdout)            # 노트북 전체 기준 셀 번호(0부터)
        self.assertIn("boom", r.stderr)
        self.assertNotIn("NEVER", r.stdout)               # 실패한 셀 뒤는 실행하지 않는다

    def test_notebook_magic_is_reported_as_failure(self):
        r = self.run_script([("code", "%pip install something")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("노트북 전용 명령", r.stderr)

    def test_load_dotenv_does_nothing_by_default(self):
        """기본은 .env를 읽지 않아 API key가 없다(과금 방지). load_dotenv()는 False를 돌려준다."""
        r = self.run_script([("code", "from dotenv import load_dotenv\nassert load_dotenv() is False")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_absolute_path_is_not_printed(self):
        r = self.run_script([("code", "pass")])
        self.assertNotIn("/Users/", r.stdout)


if __name__ == "__main__":
    unittest.main()
