"""화면 → 서버 DB 저장의 **얇은 연결**(이슈 #52). 로그인했고 저장을 켠 사용자만 저장하고, 저장이 실패해도 연습 기능은 멈추지 않는다.

계산은 `practice_log.py`(문장 열쇠·기록 한 줄), 저장은 `storage.py`, 누가 로그인했는지는 `app/auth_gate.py`(세션 상태)가 맡는다. 여기서는 그 셋을 이어 붙이기만 한다.
- 가사·인식문은 **로그·오류 메시지에 남기지 않는다**: 실패하면 오류 종류만 알리고 내용은 넘기지 않는다.
- 게스트나 저장을 끈 사용자는 아무것도 하지 않는다.
"""
import hashlib
import json

import streamlit as st

import auth_gate
import practice_log
import storage
import web_song


def _run(action):
    """DB 연결을 열어 action(conn)을 실행한다. 실패하면 짧은 안내(toast)만 띄우고 False. (예외 내용·가사는 노출하지 않음)"""
    try:
        with storage.connect() as conn:
            action(conn)
        return True
    except Exception as e:
        st.toast(f"서버에 저장하지 못했어요({type(e).__name__}). 연습은 계속 할 수 있어요.", icon="⚠️")
        return False


def _source(key, source):
    """sentences.csv의 예시 문장(key가 s03 꼴)이면 출처를 sample로 바꾼다(기록 CSV와 같은 규칙)."""
    return "sample" if key.startswith("s") and not key.startswith("h_") else source


def save_attempt(source, text, mode, res, lang=None):
    """따라읽기·받아쓰기 채점 결과 한 번을 저장한다. res는 practice.read·dictation의 결과. 점수가 없으면(오류) 저장하지 않는다."""
    if not auth_gate.save_enabled():
        return False
    rec = practice_log.make_record(source, text, mode, res)
    if rec is None:
        return False
    record = {"source": _source(rec["key"], rec["source"]), "key": rec["key"], "mode": mode, "lang": lang, "ref_text": text, "hyp_text": res.get("hyp"),
              "score": res["score"], "azure": None, "stt": practice_log.stt_label(rec["stt"])}
    uid = st.session_state["uid"]
    return _run(lambda conn: storage.append_attempt(conn, uid, record))


def save_azure(source, text, lang, azure_result):
    """Azure 발음 평가 결과 한 번을 저장한다(점수와 단어별 결과만, 녹음은 저장하지 않음)."""
    if not auth_gate.save_enabled() or not azure_result:
        return False
    key = practice_log.sentence_key(text)
    record = {"source": _source(key, source), "key": key, "mode": "azure", "lang": lang, "ref_text": text,
              "hyp_text": None, "score": None, "azure": azure_result, "stt": None}
    uid = st.session_state["uid"]
    return _run(lambda conn: storage.append_attempt(conn, uid, record))


def _call(action):
    """DB에서 값을 읽는다. 돌려주는 값: (성공했는가, 값). 실패하면 짧은 안내만 띄운다."""
    try:
        with storage.connect() as conn:
            return True, action(conn)
    except Exception as e:
        st.toast(f"서버에서 불러오지 못했어요({type(e).__name__}).", icon="⚠️")
        return False, None


def _digest_of(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


# ---------- 곡 기록 ----------
def saved_song(digest):
    """이 곡(음원 지문)으로 서버에 저장된 기록. 없거나 게스트면 None. 곡마다 한 번만 읽어 세션에 둔다."""
    if not auth_gate.is_user():
        return None
    ss = st.session_state
    key = f"saved_row_{digest}"
    if key not in ss:
        uid = ss["uid"]
        ok, row = _call(lambda conn: storage.load_song(conn, uid, digest))
        if not ok:
            return None                                   # 읽기 실패는 캐시하지 않는다(다음에 다시 시도)
        ss[key] = row
    return ss[key]


def song_list():
    """저장된 내 곡 목록(최근 수정 순, 가벼운 열 + 줄 수 n_lines). 게스트이거나 읽기에 실패하면 빈 목록."""
    if not auth_gate.is_user():
        return []
    uid = st.session_state["uid"]
    ok, rows = _call(lambda conn: storage.list_songs(conn, uid))
    return rows if ok and rows else []


def autosave_song(digest, ws, name, seconds, input_kind, cut=None):
    """지금 작업(구간·가사 줄·언어)이 바뀌었으면 서버에 저장한다(스크립트가 다시 실행될 때마다 부르고, 안 바뀌었으면 아무것도 안 함).
    **덮어쓰기 보호**: 같은 곡의 저장본에 가사가 있는데 이 세션에서는 아직 가사를 불러오지도 새로 인식하지도 않았다면 저장하지 않는다
    (같은 곡을 다시 올리고 구간만 고르다가 저장된 가사를 빈 기록으로 덮어쓰는 사고를 막는다).
    cut: (시작, 길이). 안 주면 세션의 지금 구간을 쓴다(소리 없이 저장본만 여는 '저장된 곡' 모드는 저장된 구간을 직접 넘긴다)."""
    if not auth_gate.save_enabled():
        return False
    ss = st.session_state
    snap = web_song.song_snapshot(ws, name, seconds, input_kind, cut or ss.get("cut"))
    row = saved_song(digest)
    if row and (row.get("doc") or {}).get("lines") and not snap["doc"].get("lines"):
        return False
    h = _digest_of(snap)
    if ss.get("saved_song_hash") == (digest, h):
        return True
    uid = ss["uid"]
    if _run(lambda conn: storage.save_song(conn, uid, digest, **snap)):
        ss["saved_song_hash"] = (digest, h)
        ss.pop(f"saved_row_{digest}", None)               # 다음에 읽을 때 방금 저장한 내용으로 새로 읽는다
        return True
    return False


# ---------- 내 문장 ----------
def saved_sentences():
    """서버에 저장된 내 문장 목록 dict({"lines": [{"text", "languages", "lang"}]}) 또는 None. 세션에 한 번만 읽어 둔다."""
    if not auth_gate.is_user():
        return None
    ss = st.session_state
    if "saved_sentences" not in ss:
        uid = ss["uid"]
        ok, doc = _call(lambda conn: storage.load_sentences(conn, uid))
        if not ok:
            return None
        ss["saved_sentences"] = doc
    return ss["saved_sentences"]


def autosave_sentences(entries):
    """내 문장 줄 목록(entries: [{"text", "languages", "lang"}])이 바뀌었으면 저장한다. 줄이 없으면 저장하지 않는다."""
    if not auth_gate.save_enabled() or not entries:
        return False
    doc = {"lines": entries}
    ss = st.session_state
    h = _digest_of(doc)
    if ss.get("saved_sentences_hash") == h:
        return True
    uid = ss["uid"]
    if _run(lambda conn: storage.save_sentences(conn, uid, doc)):
        ss["saved_sentences_hash"] = h
        ss["saved_sentences"] = doc
        return True
    return False
