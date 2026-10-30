"""커밋 전 점검: 노트북(.ipynb)에 오디오 플레이어, 개인 경로, key 패턴이 남아 있는지 검사한다.
사용: python scripts/scan_outputs.py [파일 ...]   (인자가 없으면 저장소의 모든 .ipynb)
문제가 있으면 종료 코드 1."""
import pathlib
import re
import sys

PATTERNS = {
    "오디오 플레이어(<audio)": re.compile(r"<audio", re.I),
    "base64 오디오(data:audio)": re.compile(r"data:audio"),
    "개인 경로(/Users/)": re.compile(r"/Users/"),
    "OpenAI key 형태(sk-)": re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    "OPENAI_API_KEY 값": re.compile(r"OPENAI_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_-]{8,}"),
}


def main(argv):
    root = pathlib.Path(__file__).resolve().parent.parent
    files = [pathlib.Path(a) for a in argv] or [p for p in root.rglob("*.ipynb")
                                                 if ".ipynb_checkpoints" not in p.parts]
    bad = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for name, pat in PATTERNS.items():
            n = len(pat.findall(text))
            if n:
                bad += 1
                print(f"[문제] {f.relative_to(root) if f.is_absolute() else f}: {name} {n}건")
    print("깨끗합니다." if not bad else f"총 {bad}개 항목에서 문제가 발견되었습니다. 출력을 지우거나 정리본을 만드세요.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
