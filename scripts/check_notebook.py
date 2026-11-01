"""노트북의 코드 셀을 위에서부터 차례로 실행해 끝까지 되는지 점검한다(이슈 #26).

사용 (프로젝트 루트에서):
    python scripts/check_notebook.py [노트북 경로] [--answer "받아쓰기 입력"] [--out 그림 저장 폴더]
                                     [--with-env] [--verbose]
기본값: 노트북은 practice.ipynb, 그림은 results/notebook_check/ (git에서 제외되는 폴더)에 PNG로 저장.
끝까지 되면 종료 코드 0, 어느 셀에서 실패하면 그 셀 번호와 오류를 보여 주고 1.

왜 필요한가
- 노트북을 고친 뒤 "처음부터 끝까지 한 번에 실행(Run All)"이 되는지 사람이 직접 확인하던 일을 한 줄 명령으로 한다.
- 발표 전 점검 체크리스트(이슈 #21)의 "커널 재시작 후 Run All"에도 쓴다.
- 화면(창)이 없어도 돌아가므로(헤드리스) 터미널이나 자동화에서 쓸 수 있다.

수업과의 관계
- [수업에 없음] 이 파일 전체. 노트북(.ipynb)은 JSON 파일이라 `json`으로 읽어 코드 셀의 글만 꺼내 `exec`로 실행한다.
  통상은 nbmake·papermill 같은 도구를 쓰지만, 새 패키지를 늘리지 않으려고 표준 라이브러리만으로 최소 구현했다.

노트북 화면에서 실행하는 것과 다른 점 (이 때문에 "대체"이지 같은 실행이 아니다)
- `input()`은 --answer로 준 글을 대신 돌려준다(받아쓰기 셀이 입력창에서 멈추지 않게).
- `plt.show()`는 창을 띄우는 대신 그림을 PNG로 저장한다(matplotlib의 Agg: 화면 없이 이미지 파일만 만드는 방식).
- `load_dotenv()`는 기본으로 아무것도 하지 않는다. .env를 읽지 않으니 API key가 없어서, 캐시에 없는 문장을 TTS로
  만들어야 하는 셀은 **과금되지 않고 실패**한다. 실제 호출까지 해 보려면 --with-env를 준다.
- `%`·`!`로 시작하는 노트북 전용 명령(매직)은 실행하지 않고 실패로 알린다(지금 노트북에는 없음).
- 셀의 출력(인식 문장, 파일 이름 등)은 화면에 보이지 않는다. 내용을 보려면 --verbose.
"""
import argparse
import builtins
import contextlib
import io
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # 이 파일(scripts/)에서 두 단계 위 = 프로젝트 루트
MAGIC = re.compile(r"^\s*[%!]", re.M)                  # 줄 맨 앞(공백 제외)이 % 또는 ! 인 줄 = 노트북 전용 명령


def code_cells(nb_path):
    """노트북에서 내용이 있는 코드 셀만 (셀 번호, 소스 글) 목록으로 돌려준다. 번호는 노트북 전체 기준(0부터)."""
    nb = json.loads(Path(nb_path).read_text(encoding="utf-8"))
    cells = []
    for i, c in enumerate(nb["cells"]):
        src = c["source"] if isinstance(c["source"], str) else "".join(c["source"])   # 소스는 글 하나이거나 줄 목록이다
        if c["cell_type"] == "code" and src.strip():
            cells.append((i, src))
    return cells


def run(nb_path, answer, out_dir, with_env, verbose):
    """코드 셀을 차례로 실행한다. 모두 되면 0, 실패하면 1."""
    os.chdir(ROOT)                          # 노트북은 프로젝트 루트 기준 상대 경로(data/…)를 쓴다
    sys.path.insert(0, str(ROOT))           # `import scoring` 같은 프로젝트 모듈을 찾게 한다
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    import matplotlib
    matplotlib.use("Agg")                   # 화면 없이 이미지 파일만 만드는 방식. pyplot을 불러오기 전에 정해야 한다
    import matplotlib.pyplot as plt
    figures = []

    def save_instead_of_show(*args, **kwargs):
        """plt.show() 대신 지금 그린 그림을 PNG로 저장하고 닫는다."""
        path = out_dir / f"fig{len(figures) + 1}.png"
        plt.gcf().savefig(path, dpi=100)
        figures.append(path)
        plt.close("all")

    plt.show = save_instead_of_show
    builtins.input = lambda prompt="": answer        # input()이 사람을 기다리지 않고 준비한 글을 돌려준다

    import dotenv
    real_load_dotenv = dotenv.load_dotenv
    # 노트북의 load_dotenv()는 exec로 실행하면 호출한 파일 위치를 못 찾아 AssertionError가 난다.
    # --with-env일 때는 .env 경로를 직접 알려 주고, 아니면 아무것도 읽지 않는다(키가 없으니 API 과금이 없다).
    dotenv.load_dotenv = ((lambda *a, **k: real_load_dotenv(dotenv_path=ROOT / ".env", **k)) if with_env
                          else (lambda *a, **k: False))

    cells = code_cells(nb_path)
    shown = nb_path.relative_to(ROOT) if nb_path.is_relative_to(ROOT) else nb_path.name    # 내 컴퓨터의 절대 경로(/Users/…)를 화면에 남기지 않으려는 것
    print(f"노트북: {shown} (코드 셀 {len(cells)}개), .env 읽기: {'예' if with_env else '아니오(API 과금 없음)'}")
    ns = {"__name__": "__main__"}            # 모든 셀이 같은 변수 공간을 공유한다(노트북 커널과 같다)
    for i, src in cells:
        first = src.strip().splitlines()[0][:50]
        buf = io.StringIO()
        t0 = time.time()
        try:
            if MAGIC.search(src):
                raise RuntimeError("노트북 전용 명령(% 또는 !)은 실행할 수 없습니다.")
            with contextlib.redirect_stdout(buf):                  # 셀이 print한 글을 화면 대신 buf에 모은다
                exec(compile(src, f"<셀 {i}>", "exec"), ns)       # 셀의 글을 파이썬 코드로 실행한다
        except Exception as e:
            print(f"[셀 {i}] 실패 ← {first}")
            if buf.getvalue():
                print("  (실패 전까지의 출력)\n" + "\n".join("  " + l for l in buf.getvalue().splitlines()))
            traceback.print_exc()
            if "api_key" in str(e).lower():
                print("힌트: API key가 필요한 셀입니다(캐시에 없는 문장). 과금을 감수하고 실행하려면 --with-env를 주세요.")
            return 1
        print(f"[셀 {i}] 완료 ({time.time() - t0:.1f}초) ← {first}")
        if verbose and buf.getvalue():
            print("\n".join("    | " + l for l in buf.getvalue().splitlines()))

    api_calls = getattr(sys.modules.get("tts"), "calls", 0)         # tts.py가 불러와졌다면 이번 실행의 API 호출 횟수
    print(f"결과: 코드 셀 {len(cells)}개 모두 실행됨 · 그림 {len(figures)}개 저장({out_dir}) · TTS API 호출 {api_calls}회")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description="노트북의 코드 셀을 차례로 실행해 점검합니다.")
    ap.add_argument("notebook", nargs="?", default="practice.ipynb", help="점검할 노트북 (기본 practice.ipynb)")
    ap.add_argument("--answer", default="I want to explor univers", help="input()에 대신 줄 글(받아쓰기 셀용)")
    ap.add_argument("--out", default="results/notebook_check", help="그림을 저장할 폴더 (git 제외 폴더)")
    ap.add_argument("--with-env", action="store_true", help=".env를 읽는다(캐시에 없으면 TTS API 호출·과금)")
    ap.add_argument("--verbose", action="store_true", help="각 셀의 출력도 보여 준다")
    a = ap.parse_args(argv)
    nb = Path(a.notebook)
    nb = nb if nb.is_absolute() else (ROOT / nb)         # 상대 경로는 프로젝트 루트 기준
    return run(nb, a.answer, a.out, a.with_env, a.verbose)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
