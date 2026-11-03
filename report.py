"""연습 결과(practice.py가 돌려준 dict)를 사람이 읽는 글로 바꾼다(이슈 #9).

모든 함수는 print하지 않고 글(문자열)을 돌려준다. 노트북은 그 글을 print하고, 나중에 만들 웹 화면은 같은 글을
화면에 넣거나 자기 방식으로 다시 꾸밀 수 있다. 계산은 하지 않는다(점수는 scoring, 점검은 quality가 이미 계산함).

[수업에 없음] 결과를 dict로 받아 글만 만드는 구성은 직접 설계했다. 문자열 만들기(f-string, join)와 `:.3f` 같은 숫자 서식은
수업에서 쓴 것과 같은 기본 파이썬 문법이다.

입력으로 받는 두 dict (모양은 practice.py 맨 위 설명 참고)
- prep: practice.prepare의 결과. 키: id, text(정답 문장), meaning_ko(뜻), tts_new(이번에 API를 불렀는가) …
- res : practice.read / practice.dictation의 결과. 키: mode, error, hyp(인식 또는 내가 적은 글), score, quality, recording …
"""
import os
from pathlib import Path

import quality
import scoring

MODE_NAME = {"read": "따라 읽기", "dictation": "받아쓰기"}    # 화면에 보일 모드 이름


def header(prep, mode):
    """연습을 시작할 때 보여 줄 안내. 따라 읽기는 문장과 뜻을 먼저, 받아쓰기는 문장을 숨긴다(들은 뒤에 공개)."""
    lines = [f"=== 문장 {prep['id']} · {MODE_NAME[mode]} ==="]
    if prep["id"] == "직접 입력":
        lines.append("※ 입력한 문장은 TTS API로 전송되고 과금됩니다(만든 음성은 data/tts_cache/에 저장해 다시 씁니다).")
    if mode == "read":
        lines.append(f"문장: {prep['text']}")
        if prep["meaning_ko"]:
            lines.append(f"뜻  : {prep['meaning_ko']}")
    else:
        lines.append("문장은 들은 뒤에 보여 줍니다. 아래 플레이어로 듣고 적어 보세요.")
    return "\n".join(lines)


def tts_status(prep):
    """기준 음성을 새로 만들었는지(API 호출·과금) 캐시를 썼는지."""
    return "기준 음성: " + ("새로 만듦(API 1회)" if prep["tts_new"] else "캐시 사용(API 0회)")


def result(prep, res):
    """채점 결과 글. 따라 읽기는 녹음 점검 → 정답·인식·오류율·틀린 부분, 받아쓰기는 정답·내 글·오류율·틀린 부분·뜻."""
    if res["error"]:
        return res["error"]      # 오류(녹음 없음, 빈 입력 등)면 그 안내 문구만 보여 준다
    lines = []
    if res["mode"] == "read":
        rec = res["recording"]
        name = Path(rec).name if isinstance(rec, (str, os.PathLike)) else "업로드·브라우저 녹음"   # bytes·파일 객체에는 파일 이름이 없다
        lines.append(f"내 녹음: {name} ({res['seconds']:.1f}초)")
        lines.append(quality.format_report(res["quality"]))
        label = "인식(Whisper tiny)"
    else:
        label = "내가 적은 글"
    sc = res["score"]            # scoring.evaluate의 결과: {"wer", "cer", "main"}
    w, c = sc["wer"], sc["cer"]
    lines += [f"정답 : {prep['text']}",
              f"{label}: {res['hyp']}",
              f"WER {w['rate']:.3f}  (치환 {w['S']}, 삭제 {w['D']}, 삽입 {w['I']} / 정답 {w['N']}단어)",
              f"CER {c['rate']:.3f}  (치환 {c['S']}, 삭제 {c['D']}, 삽입 {c['I']} / 정답 {c['N']}글자)",
              "틀린 부분: " + scoring.format_diff(sc["main"]["ops"])]   # main: 일본어면 CER, 그 밖에는 WER의 ops
    if res["mode"] == "read":
        lines.append("※ 이 점수는 발음 점수가 아니라 문장 인식 일치도입니다.")
    elif prep["meaning_ko"]:
        lines.append(f"뜻  : {prep['meaning_ko']}")
    return "\n".join(lines)


def error_blocks(prep, loc):
    """틀린 덩어리마다 TTS와 내 녹음의 시간 구간을 한 줄씩. loc는 practice.locate_errors()["loc"]."""
    blocks = loc["blocks"]
    lines = [f'정답: {prep["text"]}   WER {loc["result"]["rate"]:.3f}   틀린 덩어리 {len(blocks)}개']
    for k, b in enumerate(blocks, 1):
        (a0, a1), (b0, b1) = b["tts_span"], b["hyp_span"]
        # 정답 단어가 TTS 소리의 몇 초 구간인지, 인식된 단어가 내 녹음의 몇 초 구간인지(단어가 없으면 "(없음)")
        lines.append(f'  [{k}] 정답 {b["ref_words"] or "(없음)"} → TTS {a0:.2f}~{a1:.2f}초 / '
                     f'인식 {b["hyp_words"] or "(없음)"} → 내 녹음 {b0:.2f}~{b1:.2f}초')
    return "\n".join(lines)
