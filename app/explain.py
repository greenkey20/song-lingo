"""화면 요소별 "어떻게 동작하나요?" 설명 상자(이슈 #56).

버튼·단계마다 **누르면 무엇이 불리고, 어떤 모듈·모델·라이브러리가 무슨 일을 하는지**를 3~5줄로 적는다.
글은 이 파일 한곳에 모으고 화면 코드는 `explain.show("키")` 한 줄만 부른다(글을 고칠 때 화면 코드를 건드리지 않으려는 구조).
내용은 해당 모듈의 코드·docstring으로 확인한 것이고, 모듈 이름은 저장소 루트의 `.py` 파일이다.

[수업에 없음] `st.expander`: 눌러서 펼치는 접는 상자(Streamlit). 평소에는 접혀 있어 화면을 어지럽히지 않는다.
"""
import streamlit as st

import theme

# 키 → 설명(마크다운). 형식: 누르면 → 호출되는 것 → 하는 일 → 수업 연결.
TEXTS = {
    "song_input": """
**누르면** 파일을 올리거나 마이크 녹음이 끝난 소리가 `bytes`로 모여 같은 흐름에 들어가요.
- 업로드는 `st.file_uploader`, 녹음은 `st.audio_input`(브라우저 마이크, 16 kHz)이 받아요. 둘 다 `web_song.save_upload`가 **세션 임시 폴더**에 저장하고, 곡 지우기·세션 정리 때 지워요.
- `audio.py`가 파일을 읽어 파형 윤곽을 그려요(수업 02·03의 샘플링·파형). 녹음은 `quality.py`가 음량·무음·클리핑을 점검해 안내만 해요(경고가 있어도 계속 진행).
""",
    "song_cut": """
**누르면** `web_song.cut` → `separate.cut_clip`이 고른 구간을 잘라 임시 폴더에 wav(44.1 kHz 스테레오)로 저장해요(몇 초).
- 보컬 분리(느림)나 인식(느림)을 하기 **전에** 귀로 구간을 확인하려는 단계예요.
- 미리 듣기는 자르지 않고 올린 원본에 재생 구간만 지정해요(`st.audio`의 `start_time`·`end_time`).
""",
    "song_lang": """
**누르면** `web_song.detect_clip_language` → `stt.detect_language`가 **faster-whisper `medium`** 모델로 구간 앞 30초를 한 번 훑어 언어별 확률을 계산해요(글을 받아 적지 않아 인식보다 빨라요).
- `languages.suggest_from_probs`가 이 앱이 지원하는 언어 안에서만 다시 순위를 매겨요(비슷한 다른 언어로 가는 오류를 줄이려고).
- **제안일 뿐**이라 네/아니오/모르겠어요로 확인하고, 그 답이 다음 단계의 인식 언어 옵션을 정해요(`languages.stt_options`).
""",
    "song_recog": """
**누르면** `song_practice.prepare_lines` → `stt.recognize_segments`가 **Whisper `medium`**(원곡, VAD 끔, 온도 폴백 켬)으로 구간별 글과 시각을 만들어요. 노래에서는 이 조합이 가장 나았어요(검토 문서 13.5).
- `song_lines.split_into_lines`가 구간을 **연습용 한 줄**로 다시 나눠요(길면 단어 사이 쉼에서 자르고, 짧으면 합침).
- 인식은 틀릴 수 있어서 가사를 고칠 수 있어요. 한 줄에는 글이 두 칸 있어요: **처음 인식한 글**(`stt_text`, 고쳐도 바뀌지 않음)과 **연습에 쓰는 글**(`text`, 고치면 이 칸만 바뀜). 고친 줄은 `edited`로 표시해요.
- 이 내용은 `lines.json`(임시 작업 폴더, 세션이 끝나면 삭제)에 있고, 로그인해서 저장을 켜 두면 **DB(`clips` 테이블)에도 두 칸 다 저장**돼요. 소리 파일은 저장하지 않아요.
- 전에 저장한 곡은 **같은 파일을 다시 올리면** "이 곡을 전에 저장했어요" 상자가 떠요(같은 곡의 구간을 여러 개 저장했다면 목록에서 고르세요). 불러오기를 누르면 인식을 다시 하지 않고 구간·고친 가사를 되살려요('기록' 메뉴는 연습 점수만 보여 줘요).
""",
    "song_listen": """
**원본 음악**은 올린 구간 그대로예요. **보컬만**은 `separate.py`의 **Demucs `htdemucs`** 모델이 반주를 빼고 목소리만 남긴 거예요(별도 프로세스, CPU로 1~3분이라 뒤에서 돌고 화면은 3초마다 상태만 확인해요).
**표준 발음**은 `tts.py`가 **OpenAI `gpt-4o-mini-tts`(voice alloy)** 로 만든 기준 소리예요(버튼을 누를 때만 호출·과금, 같은 문장은 `data/tts_cache/` 캐시).
""",
    "lyr_lang": """
**누르면** `languages.suggest_line_language`가 **줄마다** 글자 종류(가나·한글·한자·라틴)의 비중으로 언어를 제안해요. 라틴 문자 줄은 낱말·특징 글자로 영어·프랑스어 등을 구분해요(모델 호출 없음, 과금 없음).
- **제안일 뿐**이라 줄마다 네/아니오/모르겠어요로 확인해요. 그 언어가 TTS·채점 규칙(일본어·중국어는 글자 단위 CER 중심)·Azure 로캘을 정해요.
""",
    "lyr_tts": """
**누르면** `web_practice.make_prep` → `tts.py`가 **OpenAI `gpt-4o-mini-tts`** 로 그 줄의 기준 소리를 만들어요(버튼을 누를 때만 호출·과금, 같은 문장은 `data/tts_cache/` 캐시에서 바로 가져와요).
""",
    "read": """
**채점하기를 누르면** `practice.read`가 순서대로 불러요.
1. `quality.py`: 음량·무음·클리핑 점검(안내만)
2. `stt.py`: **faster-whisper**(기본 `tiny`, CPU int8, 7강 설정)가 녹음을 글로 바꿈
3. `scoring.py`: 정답과 인식 결과를 **편집 거리**로 비교해 오류율(WER, 일본어·중국어는 CER)과 틀린 부분을 구함
점수는 **발음 점수가 아니라 "문장 인식 일치도"** 예요(STT가 틀린 발음을 문맥으로 고쳐 적을 수 있음).
""",
    "dictation": """
**채점하기를 누르면** `practice.dictation`이 내가 적은 글을 정답과 `scoring.py`로 바로 비교해요. 소리 인식(STT)을 거치지 않아서 인식 오류가 섞이지 않고, **듣고 받아 적는 능력**만 봐요.
""",
    "error_spans": """
`practice.locate_errors` → `align.py`가 틀린 덩어리를 소리 위의 시간 구간으로 바꿔요. 내 녹음과 TTS를 각각 `stt.recognize_words`(Whisper 단어별 시간)로 다시 인식해서 얻은 시간이에요.
- 단어 시간은 Whisper의 **추정값**이라 정확한 강제 정렬이 아니에요. 그래서 몇 초 더 걸리고, 구간이 조금 어긋날 수 있어요.
""",
    "azure": """
**누르면** `azure_pronunciation.assess`가 **녹음과 기준 문장 글·로캘만** Microsoft Azure Speech로 보내요(TTS 소리는 안 보내고, 녹음은 서버에 저장하지 않아요).
- 평가 기준은 TTS가 아니라 **Azure의 원어민 발음 모델**이에요. 정확도·유창성·완성도·운율과 단어별 점수를 돌려줘요.
- 우리 채점(WER/CER)은 "글자가 같은가", Azure는 "발음이 자연스러운가"를 봐서 서로 보완해요.
""",
}


# 설명 상자는 연습 흐름(주 기능)이 아닌 **부가 요소**라서 보조색 라임으로 구분한다(11-06 사용자 요청). 라임은 바탕·테두리로만 쓰고 글자는 짙은 색이다(theme.LIME 설명).
# 상자를 `st.container(key="explain-…")`로 감싸면 Streamlit이 그 컨테이너에 `st-key-explain-…` 클래스를 붙여서, 이 클래스 안의 expander만 골라 칠할 수 있다(다른 expander는 그대로).
# **Streamlit 내부 요소 이름(`stExpander`)에 기대므로 Streamlit을 올리면 깨질 수 있다.** 그때는 이 CSS만 지우면 기본 모양으로 돌아간다.
CSS = f"""<style>
[class*="st-key-explain-"] [data-testid="stExpander"] {{ border: 1px solid {theme.LIME}; border-radius: 0.5rem; background: {theme.LIME}1f; }}
[class*="st-key-explain-"] [data-testid="stExpander"] summary {{ background: {theme.LIME}; color: {theme.FOREST}; font-weight: 600; border-radius: 0.5rem; }}
[class*="st-key-explain-"] [data-testid="stExpander"] summary:hover {{ background: {theme.LIME}cc; }}
[class*="st-key-explain-"] [data-testid="stExpander"] summary * {{ color: {theme.FOREST}; }}
</style>"""


def show(key, title="어떻게 동작하나요?"):
    """키에 해당하는 설명을 라임색 접는 상자로 그린다. 키가 없으면 KeyError(오타를 빨리 알아채려고 조용히 넘기지 않는다)."""
    with st.container(key=f"explain-{key}"):
        with st.expander(title):
            st.markdown(TEXTS[key].strip())
