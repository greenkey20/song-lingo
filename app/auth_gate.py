"""로그인·가입·게스트 화면과 사이드바 사용자 상자(이슈 #52, 검토 문서 16.16 11절).

`app/streamlit_app.py`가 페이지를 그리기 전에 `run()`을 부르면, 사용자가 확인되었을 때만 돌아오고 아니면 `st.stop()`으로 화면을 여기서 멈춘다.

신원(누구인가)은 세션 상태에 둔다: `uid`(계정 번호, 게스트는 없음), `uname`, `guest`(True면 저장 없이 사용), `save_on`, `remember_token`(로그인 유지 쿠키에 준 토큰 원문).
세 가지 경로로 들어온다
  1. **자동 로그인**: 새 세션이 시작될 때 브라우저가 보낸 쿠키(`sl_auth`)의 토큰이 DB에 있고 유효하면 로그인(만료는 30일 뒤로 연장).
  2. **로그인/가입**: 아이디·비밀번호. 가입에는 **초대 코드**(= `SONGLINGO_PASSWORD`)가 필요해서 공개 주소에서 아무나 가입해 외부 API를 쓰지 못한다.
  3. **게스트**: 초대 코드만 입력하고 **저장 없이** 쓴다(DB가 멈췄을 때의 비상구이기도 하다).
DB 접속 정보가 없으면(`storage.enabled()`가 False) 예전처럼 접근 제한 비밀번호만 묻고 게스트로 동작한다.

쿠키는 `st.html(..., unsafe_allow_javascript=True)`의 자바스크립트로 **쓰고**, 서버는 `st.context.cookies`로 **읽는다**(읽기 전용). 쿠키는 새 세션을 열 때 서버에 전달되므로 "다음에 접속할 때"의 자동 로그인에 쓰인다.
JS로 만든 쿠키는 `HttpOnly`를 걸 수 없고 아이폰 Safari는 기한을 7일로 제한한다(그래서 로그인 중에는 접속할 때마다 쿠키를 다시 써서 기한을 늘린다) [일반 지식].

수업과의 관계: [수업에 없음] 이 파일 전체. `st.form`·`st.tabs`·`st.session_state`는 Streamlit의 화면 기능이다.
"""
import time

import streamlit as st

import access
import account
import auth
import explain
import storage


_SCHEMA_READY = False        # 이 서버 프로세스에서 마이그레이션을 이미 적용했는지(프로세스당 한 번만 확인)


def _ensure_schema():
    """필요한 테이블이 없으면 만든다(`storage.migrate`: 아직 적용 안 된 migrations/*.sql만, 여러 프로세스가 동시에 해도 안전). 실패하면 False."""
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return True
    try:
        with storage.connect() as conn:
            storage.migrate(conn)
        _SCHEMA_READY = True
    except Exception:
        return False
    return True


# ---------- 쿠키 (JS로 쓰기) ----------
def _cookie_html(value, max_age):
    """쿠키 하나를 쓰는 <script>. https에서만 Secure를 건다(http://localhost 개발에서는 쿠키가 저장되도록)."""
    secure = "; Secure" if str(getattr(st.context, "url", "")).startswith("https") else ""
    return (f"<script>document.cookie = '{auth.COOKIE_NAME}={value}; max-age={max_age}; path=/; SameSite=Lax{secure}';</script>")


def _set_cookie(token):
    """로그인 유지 쿠키를 브라우저에 쓴다(자바스크립트로 `document.cookie`를 설정: Streamlit이 서버에서 쿠키를 쓰는 기능이 없어서)."""
    st.html(_cookie_html(token, auth.TOKEN_DAYS * 86400), unsafe_allow_javascript=True)


def _clear_cookie():
    """로그인 유지 쿠키를 지운다(만료 시간을 0으로 덮어씀)."""
    st.html(_cookie_html("", 0), unsafe_allow_javascript=True)


# ---------- 세션 상태 ----------
def _enter(user, token=None):
    """로그인된 사용자로 세션 상태를 채운다."""
    st.session_state.update(uid=user["id"], uname=user["username"], save_on=bool(user.get("save_on", True)), guest=False,
                            remember_token=token)


def _leave():
    """세션의 신원 정보를 지운다(로그아웃·계정 삭제 뒤)."""
    for k in ("uid", "uname", "guest", "save_on", "remember_token", "authed"):
        st.session_state.pop(k, None)
    st.session_state["clear_cookie"] = True


def is_user():
    """로그인한 사용자(게스트 아님)인가."""
    return st.session_state.get("uid") is not None


def save_enabled():
    """이 세션의 학습 기록을 서버에 저장해도 되는가(로그인했고 저장을 켰을 때만)."""
    return is_user() and bool(st.session_state.get("save_on", True))


# ---------- 초대 코드 확인 (세션별 5회 잠금) ----------
def _invite_ok(code):
    """초대 코드가 맞는지. 틀리면 세션 실패 횟수를 늘린다. 돌려주는 값: (맞는가, 안내 글)."""
    if not access.enabled():
        return True, ""
    ss = st.session_state
    left = access.lock_remaining(ss.get("fails", 0), ss.get("last_fail", 0.0), time.time())
    if left > 0:
        return False, f"여러 번 틀려서 {left}초 뒤에 다시 시도할 수 있어요."
    if access.check(code):
        ss["fails"] = 0
        return True, ""
    ss.update(fails=ss.get("fails", 0) + 1, last_fail=time.time())
    return False, "초대 코드가 맞지 않아요."


def _invite_screen():
    """DB가 없을 때의 예전 화면: 비밀번호(접근 제한) 한 칸."""
    st.title("song lingo")
    st.caption("접근 제한이 걸려 있어요. 비밀번호를 입력하세요.")
    with st.form("form_gate"):
        typed = st.text_input("비밀번호", type="password")
        go = st.form_submit_button("들어가기", type="primary")
    if go:
        ok, msg = _invite_ok(typed)
        if ok:
            st.session_state.update(authed=True, guest=True)
            st.rerun()
        st.error(msg)


# ---------- 로그인·가입·게스트 화면 ----------
def _guest_form(db_alive):
    """게스트 입장 양식. 양식의 key는 세션 상태 key(guest)와 겹치면 오류가 나서 form_ 접두어를 붙인다."""
    note = "저장 없이 써 볼 수 있어요. 기록과 가사는 이 브라우저 탭을 닫으면 사라져요."
    if not db_alive:
        note = "지금은 저장 기능을 쓸 수 없어요(저장소에 연결하지 못함). " + note
    st.caption(note)
    with st.form("form_guest"):
        code = st.text_input("초대 코드", type="password") if access.enabled() else ""
        go = st.form_submit_button("게스트로 들어가기", type="primary")
    if go:
        ok, msg = _invite_ok(code)
        if ok:
            st.session_state.update(guest=True, authed=True)
            st.rerun()
        st.error(msg)


def _login_form():
    """'로그인' 탭의 폼: 아이디·비밀번호·로그인 유지 체크. 성공하면 세션을 채우고 화면을 다시 그린다(`account.login`이 판단, 실패 문구는 아이디 존재 여부를 알려 주지 않는 같은 문구)."""
    with st.form("form_login"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        keep = st.checkbox("로그인 유지(30일)", value=True)
        go = st.form_submit_button("로그인", type="primary")
    if not go:
        return
    try:
        with storage.connect() as conn:
            user, msg = account.login(conn, username, password)
            token = account.start_remember(conn, user["id"]) if (user and keep) else None
    except Exception:
        st.error("저장소에 연결하지 못했어요. 잠시 뒤에 다시 하거나 게스트로 들어가세요.")
        return
    if user:
        _enter(user, token)
        st.rerun()
    st.error(msg)


def _signup_form():
    """'가입' 탭의 폼: 초대 코드(접근 제한이 켜져 있을 때)·아이디·비밀번호·확인. 규칙 검사와 저장은 `account.signup`이 한다."""
    with st.form("form_signup"):
        code = st.text_input("초대 코드", type="password") if access.enabled() else ""
        username = st.text_input("아이디 (3~20자, 영문·숫자·한글·_ . -)")
        password = st.text_input("비밀번호 (8자 이상)", type="password")
        again = st.text_input("비밀번호 한 번 더", type="password")
        go = st.form_submit_button("가입하고 시작하기", type="primary")
    st.caption("이메일은 받지 않아요. **비밀번호를 잊으면 찾을 방법이 없어요**(관리자가 초기화해야 해요). 가입하면 가사·구간·채점 결과가 서버에 저장돼요(끌 수 있어요).")
    if not go:
        return
    ok, msg = _invite_ok(code)
    if not ok:
        st.error(msg)
        return
    if password != again:
        st.error("비밀번호가 서로 달라요.")
        return
    try:
        with storage.connect() as conn:
            uid, msg = account.signup(conn, username, password)
            user = token = None
            if uid:
                user, _ = account.login(conn, username, password)
                token = account.start_remember(conn, uid)
    except Exception:
        st.error("저장소에 연결하지 못했어요. 잠시 뒤에 다시 하거나 게스트로 들어가세요.")
        return
    if user:
        _enter(user, token)
        st.rerun()
    st.error(msg)


def run():
    """사용자가 확인될 때까지 화면을 그리고(필요하면 st.stop()), 확인되면 돌아온다."""
    ss = st.session_state
    if ss.pop("clear_cookie", False):
        _clear_cookie()                                  # 로그아웃 뒤 쿠키를 지운다
    if is_user() or ss.get("guest"):
        if ss.get("remember_token"):
            _set_cookie(ss["remember_token"])            # 접속할 때마다 쿠키를 다시 써서 기한을 늘린다(아이폰 7일 제한 보완)
        return
    if not storage.enabled():                            # 저장소 설정이 없으면 예전처럼 접근 제한만(게스트)
        if access.enabled() and not ss.get("authed"):
            _invite_screen()
            st.stop()
        ss["guest"] = True
        return

    alive = storage.ping() and _ensure_schema()          # DB가 살아 있고 테이블이 준비됐을 때만 로그인·가입을 연다
    if alive and not ss.get("cookie_tried"):             # 새 세션의 첫 실행에서 한 번만 쿠키로 자동 로그인을 시도
        ss["cookie_tried"] = True
        raw = st.context.cookies.get(auth.COOKIE_NAME)
        if raw:
            try:
                with storage.connect() as conn:
                    user = account.resume(conn, raw)
            except Exception:
                user = None
            if user:
                _enter(user, raw)
                _set_cookie(raw)
                return
            _clear_cookie()                              # 만료·잘못된 쿠키는 지운다

    st.title("song lingo")
    if alive:
        tab_in, tab_up, tab_guest = st.tabs(["로그인", "가입", "게스트"])
        with tab_in:
            _login_form()
        with tab_up:
            _signup_form()
        with tab_guest:
            _guest_form(True)
    else:
        st.warning("저장소에 연결하지 못했어요. 로그인·가입은 잠시 쓸 수 없어요.")
        _guest_form(False)
    st.stop()


# ---------- 사이드바 사용자 상자 ----------
def _on_toggle():
    """사이드바 '저장' 스위치의 on_change: 세션과 DB(`users.save_on`)에 저장 켜기/끄기를 반영한다. DB가 안 되면 세션 값만 바꾸고 `save_error`를 켜서 사이드바에 안내한다."""
    on = st.session_state.get("save_toggle", True)
    st.session_state["save_on"] = on
    try:
        with storage.connect() as conn:
            storage.set_save_on(conn, st.session_state["uid"], on)
    except Exception:
        st.session_state["save_error"] = True


def _logout():
    """로그아웃: 서버의 로그인 유지 토큰을 지우고(`account.end_session`) 브라우저 쿠키도 지우도록 표시한 뒤 세션을 비운다."""
    try:
        with storage.connect() as conn:
            account.end_session(conn, st.session_state.get("remember_token"))
    except Exception:
        pass
    _leave()


def sidebar():
    """사이드바에 지금 누구로 쓰는지, 저장 켜기/끄기, 로그아웃, 계정 삭제를 그린다."""
    ss = st.session_state
    with st.sidebar:
        st.divider()
        if is_user():
            st.markdown(f"**{ss.get('uname', '')}** 님")
            st.toggle("학습 기록을 서버에 저장", value=bool(ss.get("save_on", True)), key="save_toggle", on_change=_on_toggle,
                      help="끄면 새로 하는 연습은 저장되지 않아요. 이미 저장된 것은 그대로예요.")
            if ss.pop("save_error", False):
                st.caption("설정을 저장하지 못했어요. 잠시 뒤에 다시 해 보세요.")
            explain.show("save")                                              # 무엇이 저장되고 무엇이 저장되지 않는지
            if st.button("로그아웃", key="logout_btn"):
                _logout()
                st.rerun()
            with st.expander("내 계정과 데이터 모두 삭제"):
                st.caption("저장된 곡·문장·채점 결과와 계정이 모두 지워지고 **되돌릴 수 없어요.** 확인하려면 아이디를 그대로 입력하세요.")
                typed = st.text_input("아이디 입력", key="delete_confirm", label_visibility="collapsed")
                if st.button("삭제하기", key="delete_btn", disabled=typed != ss.get("uname")):
                    try:
                        with storage.connect() as conn:
                            storage.delete_user(conn, ss["uid"])
                        _leave()
                        st.rerun()
                    except Exception:
                        st.error("삭제하지 못했어요. 잠시 뒤에 다시 해 보세요.")
        elif storage.enabled():
            st.caption("게스트로 이용 중이에요. 기록이 저장되지 않아요.")
            if st.button("로그인·가입하기", key="to_login_btn"):
                ss["guest"] = False
                ss.pop("authed", None)
                st.rerun()
