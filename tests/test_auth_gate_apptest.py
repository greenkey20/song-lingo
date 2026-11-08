"""로그인·가입·게스트 화면(app/auth_gate.py)을 Streamlit AppTest로 시험한다(이슈 #52). DB 대신 메모리 가짜 저장소(tests/fake_store.py)를 쓴다.
streamlit이 있는 **앱 전용 환경**에서만 돈다: ~/venvs/song-lingo-app/bin/python -m unittest tests.test_auth_gate_apptest (voice-ai에서는 건너뜀)."""
import os
import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except Exception:                                    # voice-ai 환경에는 streamlit이 없다
    AppTest = None

import storage
from tests.fake_store import FakeStore, install

INVITE = "invite-code-123"
SCRIPT = str(Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")      # AppTest는 상대 경로를 이 파일 기준으로 해석한다


def find(elements, label, startswith=False):
    for e in elements:
        text = getattr(e, "label", "") or ""
        if text == label or (startswith and text.startswith(label)):
            return e
    raise AssertionError(f"'{label}' 요소를 찾지 못함: {[getattr(e, 'label', '') for e in elements]}")


@unittest.skipIf(AppTest is None, "streamlit이 없는 환경이라 건너뜁니다")
class Base(unittest.TestCase):
    """공통 준비: 가짜 저장소를 끼우고 초대 코드를 정하고, 앱 실행·가입 도우미를 제공한다."""

    def setUp(self):
        self.store = FakeStore()
        self.restore = install(self.store)
        self._old = os.environ.get("SONGLINGO_PASSWORD")
        os.environ["SONGLINGO_PASSWORD"] = INVITE

    def tearDown(self):
        self.restore()
        if self._old is None:
            os.environ.pop("SONGLINGO_PASSWORD", None)
        else:
            os.environ["SONGLINGO_PASSWORD"] = self._old

    def app(self):
        return AppTest.from_file(SCRIPT, default_timeout=90).run()

    def signup(self, at, code=INVITE, name="alice_1", pw="long-password-1", again=None):
        codes = [t for t in at.text_input if t.label == "초대 코드"]
        codes[0].set_value(code)                                         # 탭 순서: 가입 탭의 칸이 먼저, 게스트 탭의 칸이 나중
        find(at.text_input, "아이디 (3~20자", startswith=True).set_value(name)
        find(at.text_input, "비밀번호 (8자 이상)").set_value(pw)
        find(at.text_input, "비밀번호 한 번 더").set_value(again if again is not None else pw)
        return find(at.button, "가입하고 시작하기").click().run()


@unittest.skipIf(AppTest is None, "streamlit이 없는 환경이라 건너뜁니다")
class Gate(Base):
    def test_gate_shows_three_tabs_when_not_logged_in(self):
        at = self.app()
        self.assertEqual([t.label for t in at.tabs], ["로그인", "가입", "게스트"])
        self.assertFalse(at.exception)
        self.assertIsNone(at.session_state["uid"] if "uid" in at.session_state else None)

    def test_signup_logs_in_and_creates_remember_token(self):
        at = self.signup(self.app())
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(at.session_state["uname"], "alice_1")
        self.assertFalse(at.session_state["guest"])
        self.assertEqual(len(self.store.tokens), 1)                       # 로그인 유지 토큰이 만들어짐(해시만 저장)
        self.assertTrue(at.session_state["remember_token"])
        self.assertIn("alice_1", " ".join(m.value for m in at.sidebar.markdown))     # 사이드바에 사용자 이름

    def test_signup_wrong_invite_code(self):
        at = self.signup(self.app(), code="wrong")
        self.assertIn("초대 코드", " ".join(e.value for e in at.error))
        self.assertEqual(self.store.users, {})

    def test_signup_password_mismatch_and_weak(self):
        at = self.signup(self.app(), again="different-pass-2")
        self.assertIn("서로 달라요", " ".join(e.value for e in at.error))
        at = self.signup(self.app(), pw="short")
        self.assertIn("8~128", " ".join(e.value for e in at.error))
        self.assertEqual(self.store.users, {})

    def test_login_and_same_error_for_unknown_and_wrong(self):
        self.signup(self.app())
        at = self.app()
        find(at.text_input, "아이디").set_value("alice_1")
        find(at.text_input, "비밀번호").set_value("wrong-password-1")
        at = find(at.button, "로그인").click().run()
        wrong = " ".join(e.value for e in at.error)
        at = self.app()
        find(at.text_input, "아이디").set_value("nobody_9")
        find(at.text_input, "비밀번호").set_value("wrong-password-1")
        at = find(at.button, "로그인").click().run()
        unknown = " ".join(e.value for e in at.error)
        self.assertEqual(wrong, unknown)
        at = self.app()
        find(at.text_input, "아이디").set_value("alice_1")
        find(at.text_input, "비밀번호").set_value("long-password-1")
        at = find(at.button, "로그인").click().run()
        self.assertEqual(at.session_state["uname"], "alice_1")

    def test_logout_returns_to_gate_and_deletes_token(self):
        at = self.signup(self.app())
        at = find(at.sidebar.button, "로그아웃").click().run()
        self.assertEqual([t.label for t in at.tabs], ["로그인", "가입", "게스트"])
        self.assertEqual(len(self.store.tokens), 0)

    def test_guest_needs_invite_and_saves_nothing(self):
        at = self.app()
        codes = [t for t in at.text_input if t.label == "초대 코드"]
        codes[-1].set_value("wrong")
        at = find(at.button, "게스트로 들어가기").click().run()
        self.assertIn("초대 코드", " ".join(e.value for e in at.error))
        codes = [t for t in at.text_input if t.label == "초대 코드"]
        codes[-1].set_value(INVITE)
        at = find(at.button, "게스트로 들어가기").click().run()
        self.assertTrue(at.session_state["guest"])
        self.assertEqual(self.store.users, {})
        self.assertEqual(self.store.calls, [])

    def test_db_down_shows_guest_only(self):
        self.store.ping = lambda info=None: False
        storage.ping = self.store.ping
        at = self.app()
        self.assertTrue(at.warning)
        self.assertEqual(len(at.tabs), 0)
        self.assertIsNotNone(find(at.button, "게스트로 들어가기"))

    def test_delete_account_removes_everything(self):
        at = self.signup(self.app())
        uid = at.session_state["uid"]
        self.store.save_clip(None, uid, "d", 0, 10, {"lines": []})
        find(at.sidebar.text_input, "아이디 입력").set_value("alice_1").run()      # 입력 뒤 다시 그려야 삭제 버튼이 켜진다(브라우저에서는 Enter/포커스 이동)
        at = find(at.sidebar.button, "삭제하기").click().run()
        self.assertEqual(self.store.users, {})
        self.assertEqual(self.store.clips, {})
        self.assertEqual([t.label for t in at.tabs], ["로그인", "가입", "게스트"])


@unittest.skipIf(AppTest is None, "streamlit이 없는 환경이라 건너뜁니다")
class SavesAttempts(Base):
    """로그인한 사용자의 채점 결과가 서버(가짜 저장소)에 저장되고, 게스트는 저장되지 않으며, 기록 화면이 내 기록을 보여 주는지 시험한다."""

    def dictate(self, at, answer="Hello there."):
        find(at.button, "예시 문장 불러오기").click()
        at = at.run()
        at = find(at.button, "언어 알아보기").click().run()
        at = find(at.button, "제안이 있는 줄은 모두 맞아요").click().run()
        find(at.text_area, "들은 문장 적기").set_value(answer)
        go = [b for b in at.button if "dict_go" in (b.key or "")][0]
        return go.click().run()

    def test_user_attempt_is_saved_with_text_and_score(self):
        at = self.dictate(self.signup(self.app()))
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(self.store.practices), 1)
        a = self.store.practices[0]
        self.assertEqual((a["mode"], a["hyp_text"], a["user_id"]), ("dictation", "Hello there.", at.session_state["uid"]))
        self.assertTrue(a["ref_text"])                                              # 문장 글이 함께 저장된다
        self.assertEqual(a["source"], "sample")                                     # 예시 문장
        self.assertIsNotNone(a["line_id"])                                          # 내 문장의 어느 줄을 연습했는지 줄(lines)과 연결된다
        self.assertIn("wer", a["scoring"])

    def test_save_off_saves_nothing(self):
        at = self.signup(self.app())
        at.session_state["save_on"] = False
        at = self.dictate(at)
        self.assertEqual(self.store.practices, [])

    def test_guest_attempt_is_not_saved_but_kept_in_session(self):
        at = self.app()
        [t for t in at.text_input if t.label == "초대 코드"][-1].set_value(INVITE)
        at = find(at.button, "게스트로 들어가기").click().run()
        at = self.dictate(at)
        self.assertEqual(self.store.practices, [])
        self.assertEqual(len(at.session_state["session_rows"]), 1)

    def test_history_shows_my_saved_attempts(self):
        at = self.dictate(self.signup(self.app()))
        at = at.switch_page("views/history.py").run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertTrue(at.dataframe)                                                # 최근 시도 표
        self.assertIn("받아쓰기", str(at.dataframe[0].value.to_dict()))


@unittest.skipIf(AppTest is None, "streamlit이 없는 환경이라 건너뜁니다")
class SavesSentences(Base):
    """내 문장 묶음(여러 개)과 줄마다 확인한 언어가 서버에 저장되고, 다음 세션에서 골라 불러와지는지, 제목·새 묶음·삭제·상한을 시험한다."""

    def type_and_check(self, at, text):
        """입력 → 언어 알아보기 → 모두 맞아요(자동 저장까지)."""
        find(at.text_area, "문장").set_value(text)
        at = at.run()
        at = find(at.button, "언어 알아보기").click().run()
        return find(at.button, "제안이 있는 줄은 모두 맞아요").click().run()

    def sets(self, uid):
        return sorted((t for t in self.store.texts.values() if t["user_id"] == uid), key=lambda t: t["id"])

    def test_sentences_saved_then_restored_in_a_new_session(self):
        at = self.signup(self.app())
        find(at.button, "예시 문장 불러오기").click()
        at = at.run()
        text_before = at.session_state["lyrics"]
        at = find(at.button, "언어 알아보기").click().run()
        at = find(at.button, "제안이 있는 줄은 모두 맞아요").click().run()
        uid = at.session_state["uid"]
        saved = self.sets(uid)[0]["doc"]["lines"]
        self.assertEqual("\n".join(e["text"] for e in saved), text_before)
        self.assertTrue(all(e["lang"] for e in saved))                                  # 줄마다 확인한 언어가 함께 저장됨
        set_id = self.sets(uid)[0]["id"]

        # 브라우저를 닫았다 연 것처럼 새 세션에서 로그인
        at2 = self.app()
        find(at2.text_input, "아이디").set_value("alice_1")
        find(at2.text_input, "비밀번호").set_value("long-password-1")
        at2 = find(at2.button, "로그인").click().run()
        self.assertEqual(at2.session_state["lyrics"], "")
        find(at2.selectbox, "저장된 묶음").select(set_id).run()
        at2 = find(at2.selectbox, "저장된 묶음").select(set_id).run()
        at2 = find(at2.button, "불러오기").click().run()
        self.assertFalse(at2.exception, [e.value for e in at2.exception])
        self.assertEqual(at2.session_state["lyrics"], text_before)
        self.assertEqual(at2.session_state["text_id"], set_id)                             # 불러온 묶음이 지금 묶음
        self.assertTrue(at2.session_state["lyr_det"])                                    # 언어 확인 단계가 이미 끝난 상태로 복원

    def test_new_set_keeps_the_old_one_and_editing_updates_the_same_set(self):
        at = self.signup(self.app())
        uid = at.session_state["uid"]
        at = self.type_and_check(at, "Hello there.\nWe sing together.")
        self.assertEqual(len(self.sets(uid)), 1)                                          # 입력창 하나 = 묶음 하나(줄이 2개여도)
        at = self.type_and_check(at, "Hello there.\nWe sing together.\nOne more line.")  # 같은 입력창을 고침 → 같은 묶음 갱신
        self.assertEqual(len(self.sets(uid)), 1)
        self.assertEqual(len(self.sets(uid)[0]["doc"]["lines"]), 3)
        at = find(at.button, "새 묶음으로 시작").click().run()
        self.assertEqual((at.session_state["lyrics"], at.session_state["lyr_title"]), ("", ""))
        at = self.type_and_check(at, "A brand new set.")
        sets = self.sets(uid)
        self.assertEqual(len(sets), 2)                                                    # 새 묶음이 만들어지고
        self.assertEqual(len(sets[0]["doc"]["lines"]), 3)                                 # 이전 묶음은 그대로
        self.assertEqual([e["text"] for e in sets[1]["doc"]["lines"]], ["A brand new set."])

    def test_title_is_saved_and_auto_title_is_shown_when_empty(self):
        at = self.signup(self.app())
        uid = at.session_state["uid"]
        at = self.type_and_check(at, "Hello there, how are you today?")
        self.assertIsNone(self.sets(uid)[0]["title"])                                     # 제목을 안 쓰면 저장하지 않는다
        self.assertIn("“Hello there, h…”", find(at.selectbox, "저장된 묶음").options[0])   # 자동 제목: 첫 줄 앞 14자
        find(at.text_input, "제목 (선택)").set_value("  아침 연습  ")
        at = at.run()
        self.assertEqual(self.sets(uid)[0]["title"], "아침 연습")                          # 같은 칸에서 이름 바꾸기, 앞뒤 공백 제거
        self.assertEqual(len(self.sets(uid)), 1)
        self.assertTrue(find(at.selectbox, "저장된 묶음").options[0].startswith("아침 연습 · "))

    def test_delete_needs_confirmation_and_clears_the_input(self):
        at = self.signup(self.app())
        uid = at.session_state["uid"]
        at = self.type_and_check(at, "Hello there.")
        at = find(at.button, "이 묶음 삭제").click().run()
        self.assertEqual(len(self.sets(uid)), 1)                                          # 첫 클릭은 확인만
        at = find(at.button, "취소").click().run()
        self.assertEqual(len(self.sets(uid)), 1)
        at = find(at.button, "이 묶음 삭제").click().run()
        at = find(at.button, "삭제하기").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(self.sets(uid), [])
        self.assertEqual(at.session_state["lyrics"], "")                                  # 입력칸도 비워진다

    def test_limit_of_50_sets_blocks_new_ones_until_a_delete(self):
        at = self.signup(self.app())
        uid = at.session_state["uid"]
        first = None
        for i in range(50):
            sid = self.store.save_texts(None, uid, {"lines": [{"text": f"seed line {i}", "languages": ["en"], "lang": "en"}]})
            first = first or sid
        at = at.run()
        at = self.type_and_check(at, "A line that does not fit.")
        self.assertEqual(len(self.sets(uid)), 50)                                         # 51번째는 저장되지 않는다
        self.assertTrue(any("50개" in w.value for w in at.warning))
        find(at.selectbox, "저장된 묶음").select(first).run()
        at = find(at.selectbox, "저장된 묶음").select(first).run()
        at = find(at.button, "불러오기").click().run()
        at = find(at.button, "이 묶음 삭제").click().run()
        at = find(at.button, "삭제하기").click().run()
        self.assertEqual(len(self.sets(uid)), 49)
        at = self.type_and_check(at, "A line that fits now.")
        self.assertEqual(len(self.sets(uid)), 50)                                         # 하나 지우니 다시 저장된다

    def test_repeated_lines_do_not_crash_language_check(self):
        """같은 줄이 여러 번 나와도(후렴) '언어 알아보기'가 위젯 열쇠 중복으로 죽지 않는다(11-08 서버에서 발견한 오류)."""
        at = self.signup(self.app())
        find(at.text_area, "문장").set_value("Hello there.\nWe sing together.\nHello there.\nHello there.")
        at = at.run()
        at = find(at.button, "언어 알아보기").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.radio), 4)                                              # 줄마다 따로 확인할 수 있다

    def test_guest_cannot_save_and_sees_no_set_controls(self):
        at = self.app()
        [t for t in at.text_input if t.label == "초대 코드"][-1].set_value(INVITE)
        at = find(at.button, "게스트로 들어가기").click().run()
        find(at.button, "예시 문장 불러오기").click()
        at = at.run()
        at = find(at.button, "언어 알아보기").click().run()
        self.assertEqual(self.store.texts, {})
        self.assertFalse([b for b in at.button if (b.label or "") in ("불러오기", "새 묶음으로 시작", "이 묶음 삭제")])
        self.assertFalse([x for x in at.text_input if x.label == "제목 (선택)"])


@unittest.skipIf(AppTest is None, "streamlit이 없는 환경이라 건너뜁니다")
class SavedSongs(Base):
    """'내 노래' > '저장된 곡': 서버에 저장된 곡을 소리 없이 골라 가사를 되살리고, 고친 가사가 다시 저장되는지 시험한다."""

    LINE = {"no": 1, "start": 0.0, "end": 3.0, "stt_text": "hello wrld", "text": "hello wrld", "edited": False, "status": "candidate",
            "low_confidence": False, "too_long": False, "tts_path": None, "tts_text": None, "lang": "en"}

    def seed(self, at):
        uid = at.session_state["uid"]
        self.cid = self.store.save_clip(None, uid, "d1" * 20, 10.0, 15.0, {"lines": [dict(self.LINE)], "languages": ["en"], "stt": {}},
                                        song_title="my.mp3", song_duration_sec=100.0, input_type="file", languages=["en"])
        return uid

    @staticmethod
    def signup_uid(at):
        return at.session_state["uid"]

    def open_saved(self, at):
        at = at.switch_page("views/song.py").run()
        at.session_state["song_mode"] = "저장된 곡"
        return at.run()

    def test_pick_saved_song_restores_lines_and_saves_edit(self):
        at = self.signup(self.app())
        uid = self.seed(at)
        at = self.open_saved(at)
        self.assertFalse(at.exception, [e.value for e in at.exception])
        at.selectbox[0].select(self.cid).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual([t.value for t in at.text_input if t.label.startswith("가사")], ["hello wrld"])
        find(at.text_input, "가사 (고치면 아래에 저장 버튼이 나와요)").set_value("hello world")
        at = at.run()
        at = find(at.button, "고친 가사 저장").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        saved = self.store.clips[(uid, "d1" * 20, 10.0, 15.0)]
        doc = saved["doc"]
        self.assertEqual(doc["lines"][0]["text"], "hello world")
        self.assertEqual(doc["lines"][0]["stt_text"], "hello wrld")                    # 처음 인식한 글은 그대로
        self.assertEqual((saved["clip_start_sec"], saved["id"]), (10.0, self.cid))       # 구간 정보와 id도 유지(같은 행을 갱신)

    def test_saved_list_label_has_preview_and_detail_caption(self):
        at = self.signup(self.app())
        uid = self.seed(at)
        at = self.open_saved(at)
        label = at.selectbox[0].options[0]
        self.assertIn("“hello wrld”", label)                                          # 첫 줄 미리보기가 목록에 보인다
        at.selectbox[0].select(self.cid).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertTrue(any("my.mp3" in c.value and "(15초)" in c.value for c in at.caption))   # 선택하면 자세한 정보 한 줄

    def test_merge_with_next_line_saves_one_merged_line(self):
        at = self.signup(self.app())
        uid = self.signup_uid(at)
        second = dict(self.LINE, no=2, start=3.0, end=6.0, stt_text="second line", text="second line")
        cid = self.store.save_clip(None, uid, "m" * 40, 10.0, 15.0, {"lines": [dict(self.LINE), second], "languages": ["en"], "stt": {}},
                                   song_title="my.mp3", song_duration_sec=100.0, input_type="file", languages=["en"])
        at = self.open_saved(at)
        at.selectbox[0].select(cid).run()
        at = find(at.button, "다음 줄과 합치기").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        lines = self.store.clips[(uid, "m" * 40, 10.0, 15.0)]["doc"]["lines"]
        self.assertEqual([(l["no"], l["text"], l["start"], l["end"], l["source"]) for l in lines], [(1, "hello wrld second line", 0.0, 6.0, "merged")])
        self.assertEqual(lines[0]["stt_text"], "hello wrld second line")                # 합친 처음 인식 글도 보존
        self.assertEqual([t.value for t in at.text_input if t.label.startswith("가사")], ["hello wrld second line"])   # 화면의 입력칸도 합친 글로
        self.assertTrue(find(at.button, "다음 줄과 합치기").disabled)                        # 이제 다음 줄이 없다

    def test_same_song_two_clips_are_listed_separately(self):
        at = self.signup(self.app())
        uid = self.seed(at)
        other = self.store.save_clip(None, uid, "d1" * 20, 40.0, 15.0, {"lines": [dict(self.LINE)]}, song_title="my.mp3", song_duration_sec=100.0, input_type="file")
        self.assertNotEqual(other, self.cid)                                          # 같은 곡의 다른 구간은 다른 행
        at = self.open_saved(at)
        self.assertEqual(len(at.selectbox[0].options), 2)

    def test_practice_on_saved_clip_records_clip_id(self):
        at = self.signup(self.app())
        self.seed(at)
        at = self.open_saved(at)
        at.selectbox[0].select(self.cid).run()
        find(at.text_area, "들은 문장 적기").set_value("hello wrld")
        at = [b for b in at.button if "dict_go" in (b.key or "")][0].click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        song_rows = [p for p in self.store.practices if p["source"] == "song"]
        self.assertEqual([p["clip_id"] for p in song_rows], [self.cid])               # 내 노래의 연습 기록은 구간과 연결된다
        self.assertEqual([p["line_id"] for p in song_rows], [self.store.clip_line_ids(None, self.store.users and at.session_state["uid"], self.cid)[1]])   # 연습한 줄(1번)과도

    def test_empty_list_message_and_guest_has_no_saved_mode(self):
        at = self.signup(self.app())
        at = self.open_saved(at)
        self.assertTrue(any("저장된 곡이 아직 없어요" in i.value for i in at.info))
        g = self.app()
        [t for t in g.text_input if t.label == "초대 코드"][-1].set_value(INVITE)
        g = find(g.button, "게스트로 들어가기").click().run()
        g = g.switch_page("views/song.py").run()
        self.assertNotIn("저장된 곡", g.segmented_control[0].options)


@unittest.skipIf(AppTest is None, "streamlit이 없는 환경이라 건너뜁니다")
class NoDatabase(unittest.TestCase):
    """저장소 설정이 없으면 예전처럼 접근 제한 비밀번호만 묻고 게스트로 동작한다."""

    def test_old_gate_when_storage_disabled(self):
        env = {k: os.environ.pop(k, None) for k in ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT")}
        old = os.environ.get("SONGLINGO_PASSWORD")
        os.environ["SONGLINGO_PASSWORD"] = INVITE
        os.environ["DB_NAME"] = ""
        try:
            self.assertFalse(storage.enabled())
            at = AppTest.from_file(SCRIPT, default_timeout=90).run()
            self.assertEqual([t.label for t in at.text_input], ["비밀번호"])
            at.text_input[0].set_value(INVITE)
            at = at.button[0].click().run()
            self.assertTrue(at.session_state["guest"])
            self.assertFalse(at.exception)
        finally:
            for k, v in env.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
            if old is None:
                os.environ.pop("SONGLINGO_PASSWORD", None)
            else:
                os.environ["SONGLINGO_PASSWORD"] = old


if __name__ == "__main__":
    unittest.main()
