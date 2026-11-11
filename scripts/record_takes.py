"""터미널에서 문장을 하나씩 보여 주며 따라읽기 녹음을 `data/recordings/sNN_takeK.wav`로 저장한다 (이슈 #10: 10문장 × 3회).

사용 (프로젝트 루트에서; 마이크가 필요하므로 사용자가 직접 실행):
    python scripts/record_takes.py                 # 아직 없는 (문장, 회차)만 1회전씩(전 문장 1회차 → 2회차 → 3회차) 녹음
    python scripts/record_takes.py --order sentence  # 문장별로(한 문장 3번 → 다음 문장)
    python scripts/record_takes.py --status        # 진행 현황만 보기
    python scripts/record_takes.py --ids 3,7       # 문장 3·7만
    python scripts/record_takes.py --redo 3 2      # 문장 3의 2회차를 다시 녹음(덮어쓰기)
    python scripts/record_takes.py --devices       # 마이크 목록 보기 → --device 번호로 선택

진행 방식: Enter로 시작 → 말하기(앞뒤 1초쯤 조용히) → Enter로 끝 → 저장과 동시에 녹음 상태 점검(quality.py) →
  Enter 다음 / r 다시 / p 들어보기 / s 건너뛰기 / q 종료. 이미 있는 파일은 건드리지 않는다(--redo만 덮어씀).

수업과의 관계: [수업에 없음] 이 스크립트(`input()` 반복문). 녹음·저장은 `recorder.py`, 상태 점검은 `quality.py`.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import quality  # noqa: E402
import recorder  # noqa: E402
import tts  # noqa: E402

TAKES = 3


def show_sentence(row, sid, take, takes=TAKES):
    print(f"\n──── 문장 {sid} · {take}/{takes}회차 ────")
    print(row["sentence"])
    if row.get("meaning_ko"):
        print(f"({row['meaning_ko']})")


def record_one(rec, row, sid, take, root, ask=input, overwrite=False):
    """한 건을 녹음·저장한다. 돌려주는 값: 'saved' | 'skip' | 'quit'. 저장 뒤 '다시(r)'를 고르면 같은 건을 한 번 더 한다."""
    path = recorder.recording_path(sid, take, root)
    while True:
        show_sentence(row, sid, take)
        cmd = ask("  Enter = 녹음 시작 (s = 건너뛰기, q = 종료) > ").strip().lower()
        if cmd == "q":
            return "quit"
        if cmd == "s":
            return "skip"
        rec.start()
        ask("  ● 녹음 중... 다 읽었으면 Enter (뒤로 1초쯤 조용히) > ")
        x = rec.stop()
        if len(x) == 0:
            print("  소리가 하나도 들어오지 않았습니다. 마이크 권한·장치를 확인하세요.")
            continue
        recorder.save_wav(path, x, rec.sr, overwrite=overwrite)   # 기존 파일은 --redo일 때만 덮어씀
        overwrite = True                                          # 방금 이 자리에서 만든 파일의 재녹음(r)은 덮어써도 된다
        print(f"  저장: {path.name} ({len(x) / rec.sr:.1f}초, {rec.sr} Hz, 스테레오)")
        print(quality.format_report(quality.check_file(path)))
        while True:
            cmd = ask("  Enter = 다음 / r = 다시 / p = 들어보기 / q = 종료 > ").strip().lower()
            if cmd == "p":
                rec.play(x)
            elif cmd == "r":
                break
            elif cmd == "q":
                return "quit"
            else:
                return "saved"


def session(sentences, todo, rec, root, ask=input, redo=False):
    """todo [(id, take), …]를 차례로 녹음한다. 끝난 건수를 돌려준다."""
    by_id = {int(s["id"]): s for s in sentences}
    done = 0
    for sid, take in todo:
        result = record_one(rec, by_id[sid], sid, take, root, ask, overwrite=redo)
        if result == "quit":
            break
        done += result == "saved"
    return done


def print_status(have, takes=TAKES):
    for sid, got in have.items():
        marks = " ".join(("●" if k in got else "○") + f"{k}" for k in range(1, takes + 1))
        print(f"  문장 {sid:>2}: {marks}")
    print(f"  (● 있음 ○ 없음 · 합계 {sum(len(v) for v in have.values())}/{len(have) * takes})")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true", help="진행 현황만 보기")
    ap.add_argument("--devices", action="store_true", help="입력 장치 목록 보기")
    ap.add_argument("--device", type=int, default=None, help="입력 장치 번호(기본: 시스템 기본 마이크)")
    ap.add_argument("--ids", default=None, help="녹음할 문장 번호(쉼표로 구분, 기본: 전체)")
    ap.add_argument("--takes", type=int, default=TAKES, help="문장당 회차 수(기본 3)")
    ap.add_argument("--order", choices=("round", "sentence"), default="round",
                    help="round=1회전씩(기본), sentence=문장별로 3번씩")
    ap.add_argument("--redo", nargs=2, type=int, metavar=("ID", "TAKE"), help="이미 있는 한 건을 다시 녹음(덮어쓰기)")
    args = ap.parse_args(argv)

    sentences = tts.load_sentences()
    ids = [int(s["id"]) for s in sentences]
    if args.ids:
        ids = [i for i in map(int, args.ids.split(",")) if i in ids]

    if args.devices:
        import sounddevice as sd
        print(sd.query_devices())
        return 0

    have, missing = recorder.take_status(ids, args.takes, order=args.order)
    print_status(have, args.takes)
    if args.status:
        return 0

    todo = [tuple(args.redo)] if args.redo else missing
    if not todo:
        print("모두 녹음되어 있습니다.")
        return 0
    rec = recorder.Recorder(device=args.device)
    print(f"\n마이크: {rec.device_name} ({rec.sr} Hz, {rec.channels}채널) · 조용한 곳에서 읽고, 문장 앞뒤로 1초쯤 쉬세요.")
    n = session(sentences, todo, rec, recorder.RECORDINGS_DIR, redo=bool(args.redo))
    print(f"\n이번에 저장한 녹음: {n}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
