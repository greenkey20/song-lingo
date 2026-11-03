"""곡 한 구간을 잘라 보컬을 분리하고 처리 시간·소리 크기를 보여 준다(이슈 #18 스파이크 재현용).

사용(프로젝트 루트에서, 내 컴퓨터 안에서만 처리하며 가사는 출력하지 않는다):
    python scripts/separate_clip.py --list                          # 영어 곡 번호와 파일 이름
    python scripts/separate_clip.py --song 12 --start 60 --duration 20 --id c01          # 자르기 + 분리
    python scripts/separate_clip.py --song 12 --start 60 --duration 20 --id c01 --cut-only   # 자르기만(몇 초) → 들어 보고
    python scripts/separate_clip.py --id c01 --separate-only                                # 맞으면 분리만(1분 안팎)
결과: data/song_work/c01_mix.wav, c01_vocals.wav, clips.csv (모두 git 제외 폴더).
처음 한 번은 Demucs 모델을 인터넷에서 내려받는다. 20초 구간에 CPU로 1분 안팎 걸린다(검토 문서 13.5).
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import separate  # noqa: E402


def rms_db(x):
    return 20 * np.log10(float(np.sqrt((x.astype(np.float64) ** 2).mean())) + 1e-12)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--list", action="store_true", help="곡 번호와 파일 이름 보기")
    ap.add_argument("--song", type=int, help="--list에 나온 번호(1부터)")
    ap.add_argument("--start", type=float, default=0.0, help="구간 시작(초)")
    ap.add_argument("--duration", type=float, default=20.0, help="구간 길이(초)")
    ap.add_argument("--id", dest="clip_id", help="저장 이름(예: c01)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--cut-only", action="store_true", help="자르기만(분리 안 함). 구간을 듣고 확인한 뒤 --separate-only")
    ap.add_argument("--separate-only", action="store_true", help="이미 자른 구간(--id)만 분리(곡 번호·시작·길이 불필요)")
    a = ap.parse_args(argv)

    if a.separate_only:
        if not a.clip_id:
            ap.error("--separate-only에는 --id가 필요합니다.")
        print(f"{a.clip_id} 분리 중(CPU, 1분 안팎)…")
        r = separate.separate_clip(a.clip_id, overwrite=a.overwrite)
        print(f"분리 {r['seconds']:.1f}초 | 저장: {r['vocals']}")
        return 0

    songs = separate.list_songs(a.lang)
    if a.list or a.song is None:
        for i, p in enumerate(songs, 1):
            print(f"{i:3d}  {p.name}")
        return 0
    if not 1 <= a.song <= len(songs):
        ap.error(f"--song은 1~{len(songs)} 사이여야 합니다.")
    if not a.clip_id:
        ap.error("--id가 필요합니다(예: --id c01).")
    song = songs[a.song - 1]
    if a.cut_only:
        r = separate.cut_clip(song, a.start, a.duration, a.clip_id, overwrite=a.overwrite)
        print(f"자름: {r['mix']} ({r['seconds']:.1f}초). 들어 보고 맞으면 --separate-only")
        return 0
    print(f"곡 {a.song}번, 구간 {a.start:.1f}초부터 {a.duration:.1f}초 → 분리 중(CPU, 1분 안팎)…")
    r = separate.process_clip(song, a.start, a.duration, a.clip_id, overwrite=a.overwrite)
    from scipy.io import wavfile
    mix = wavfile.read(r["mix"])[1] / 32768.0
    voc = wavfile.read(r["vocals"])[1] / 32768.0
    print(f"분리 {r['seconds']:.1f}초 ({r['seconds'] / a.duration:.2f}배) | RMS dBFS 원곡 {rms_db(mix):.1f}, 보컬 {rms_db(voc):.1f}")
    print("저장:", r["mix"], r["vocals"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
