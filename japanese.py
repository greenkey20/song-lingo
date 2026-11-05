"""일본어 글을 **히라가나 읽기**와 **로마자(헤본식)** 로 바꾸는 도구 (이슈 #50, 검토 문서 16.14의 9절).

왜 필요한가: 일본어는 같은 말을 한자·히라가나·가타카나로 다르게 적을 수 있다. 음성 인식(Whisper)은 영어 단어를 가타카나로, 한자 문장을 가나로 적기도 해서
기준 문장과 글자를 그대로 대조하면 의미가 없다. 그래서 **둘 다 히라가나 읽기로 바꿔 비교**하고, 학습자가 한자·가타카나를 읽지 못해도 보도록 **히라가나 읽기와 로마자**를 함께 보여 준다.
(예: 朝の光 → あさのひかり → asa no hikari)

수업과의 관계
- [수업에 없음] 이 모듈 전체. `pykakasi`(순수 파이썬 일본어 읽기 변환 라이브러리, 사전을 내장)를 11-06 사용자 승인으로 추가했다(앱 환경과 voice-ai 모두, numpy 불변).
- 한계: ① 한자의 읽기는 사전과 문맥 규칙으로 정한 **추정**이라 틀릴 수 있다(동형이음 한자, 고유명사) ② **영어 단어는 그대로 둔다**(Coffee는 coffee로 남고 가타카나 コーヒー와 같은 소리로 맞춰 주지 못한다)
  ③ 조사 は·を·へ의 읽기는 로마자에서 문법 표기 그대로(ha·wo·he)로 나온다.
"""
_kks = None            # pykakasi 변환기(처음 쓸 때 한 번 만든다)


def available():
    """pykakasi를 불러올 수 있는가(설치되지 않은 환경에서는 False, 그때는 변환 없이 원문을 쓴다)."""
    try:
        import pykakasi  # noqa: F401
        return True
    except ImportError:
        return False


def _convert(text):
    """pykakasi의 결과 목록 [{"orig","hira","kana","hepburn",…}]. 없으면 ImportError."""
    global _kks
    if _kks is None:
        import pykakasi
        _kks = pykakasi.kakasi()
    return _kks.convert(str(text))


def reading(text):
    """글 → **히라가나 읽기**(한자·가타카나가 히라가나가 됨, 영어·숫자·기호는 그대로). pykakasi가 없으면 원문 그대로."""
    if not available():
        return str(text)
    return "".join(p["hira"] for p in _convert(text))


def romaji(text):
    """글 → **로마자(헤본식)**, 낱말 사이는 공백 한 칸. 히라가나·가타카나·한자의 읽기 모두 로마자가 된다. pykakasi가 없으면 빈 글."""
    if not available():
        return ""
    return " ".join(p["hepburn"].strip() for p in _convert(text) if p["hepburn"].strip())


def readings(text):
    """(히라가나 읽기, 로마자) 한 쌍. 화면에서 기준 문장과 인식 결과 밑에 함께 보여 줄 때 쓴다."""
    return reading(text), romaji(text)
