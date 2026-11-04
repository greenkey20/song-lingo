"""이미 잘라 둔 구간의 보컬을 분리하는 **별도 프로세스용** 작은 실행 파일(검토 문서 16.10).

웹 앱은 Streamlit 전용 환경에서 돌고 거기에는 torch·demucs가 없다. 앱이 `SONGLINGO_SEPARATE_PYTHON`으로 지정한 파이썬(예: voice-ai)으로
이 파일을 실행시키고, 끝난 vocals wav 파일만 받는다. faster-whisper와 torch를 한 프로세스에서 불러 죽는 문제(이슈노트 #15)도 피한다.

사용(프로젝트 루트에서): python scripts/separate_worker.py <구간 id> <작업 폴더>
출력: 마지막 줄에 JSON 한 줄({"seconds": …}). 가사는 출력하지 않는다. 실패하면 종료 코드 1과 오류 이름만 stderr에 쓴다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import separate  # noqa: E402


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("사용: separate_worker.py <구간 id> <작업 폴더>", file=sys.stderr)
        return 2
    clip_id, work_dir = argv
    try:
        out = separate.separate_clip(clip_id, work_dir=work_dir, overwrite=True)
    except Exception as e:                                     # 원인 종류와 짧은 메시지만(곡 내용은 메시지에 없음)
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"seconds": round(out["seconds"], 1)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
