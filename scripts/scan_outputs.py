"""커밋 전 점검: 노트북(.ipynb)에 오디오 플레이어, 개인 경로, key 패턴이 남아 있는지 검사한다.
사용: python scripts/scan_outputs.py [파일 ...]   (인자가 없으면 저장소의 모든 .ipynb)
문제가 있으면 종료 코드 1.

왜 필요한가: 노트북(.ipynb)은 코드와 함께 **실행 결과(출력)** 도 파일에 저장된다. 출력에는 내 목소리(오디오 플레이어의
base64 데이터), 내 컴퓨터 경로(/Users/…), API key가 들어갈 수 있어서, 공개 저장소에 올리기 전에 이를 검사한다.
[수업에 없음] 정규식(`re`)으로 글에서 패턴을 찾는 방식과 종료 코드 사용. 정규식 자체는 scoring.py의 정규화에서도 쓴다.
"""
import pathlib
import re
import sys

# 찾을 패턴 이름 → 정규식. re.I는 대소문자를 구분하지 않는다는 뜻이다.
PATTERNS = {
    "오디오 플레이어(<audio)": re.compile(r"<audio", re.I),
    "base64 오디오(data:audio)": re.compile(r"data:audio"),
    "개인 경로(/Users/)": re.compile(r"/Users/"),
    "OpenAI key 형태(sk-)": re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    "OPENAI_API_KEY 값": re.compile(r"OPENAI_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_-]{8,}"),
}


def main(argv):
    root = pathlib.Path(__file__).resolve().parent.parent       # 이 파일의 위치(scripts/)에서 두 단계 위 = 프로젝트 루트
    # 인자로 파일을 주면 그 파일만, 안 주면 저장소의 모든 노트북(rglob = 하위 폴더까지 재귀 검색)을 검사한다.
    files = [pathlib.Path(a) for a in argv] or [p for p in root.rglob("*.ipynb")
                                                 if ".ipynb_checkpoints" not in p.parts]
    bad = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for name, pat in PATTERNS.items():
            n = len(pat.findall(text))         # findall: 패턴에 맞는 모든 곳의 목록 → 개수
            if n:
                bad += 1
                print(f"[문제] {f.relative_to(root) if f.is_absolute() else f}: {name} {n}건")
    print("깨끗합니다." if not bad else f"총 {bad}개 항목에서 문제가 발견되었습니다. 출력을 지우거나 정리본을 만드세요.")
    return 1 if bad else 0          # 0이면 성공, 1이면 문제 있음(셸에서 이 값으로 성공 여부를 알 수 있다)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
