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


def _clip_id_for(source):
    """내 노래에서 연습한 것이면 지금 구간의 clip id(autosave_clip이 세션에 보관), 아니면 None. 내 문장·예시 문장은 구간과 무관하다."""
    return st.session_state.get("clip_id") if source == "song" else None


def _line_id_for(source, line_no):
    """연습한 줄의 lines.id: 내 노래(source="song")는 지금 구간의 줄 번호로, 내 문장(source="lyrics")은 문장 묶음의 줄 번호로 찾는다
    (autosave가 저장하면서 세션에 보관한 {줄 번호: id}). 모르면 None."""
    if line_no is None:
        return None
    ss = st.session_state
    if source == "song":
        return (ss.get("clip_line_ids") or {}).get(line_no)
    if source == "lyrics":
        return (ss.get("text_line_ids") or {}).get(line_no)
    return None


def save_practice(source, text, mode, res, lang=None, line_no=None):
    """따라읽기·받아쓰기 채점 결과 한 번을 저장한다. res는 practice.read·dictation의 결과. 점수가 없으면(오류) 저장하지 않는다.
    line_no: 화면에서 연습 중인 줄 번호(있으면 practices.line_id로 연결)."""
    if not auth_gate.save_enabled():
        return False
    rec = practice_log.make_record(source, text, mode, res)
    if rec is None:
        return False
    record = {"source": _source(rec["key"], rec["source"]), "key": rec["key"], "mode": mode, "lang": lang, "ref_text": text, "hyp_text": res.get("hyp"),
              "scoring": res["score"], "azure": None, "stt_settings": rec["stt"] or None, "clip_id": _clip_id_for(source),
              "line_id": _line_id_for(source, line_no)}
    uid = st.session_state["uid"]
    return _run(lambda conn: storage.append_practice(conn, uid, record))


def save_azure(source, text, lang, azure_result, line_no=None):
    """Azure 발음 평가 결과 한 번을 저장한다(점수와 단어별 결과만, 녹음은 저장하지 않음). 인식된 글은 hyp_text에 둔다."""
    if not auth_gate.save_enabled() or not azure_result:
        return False
    key = practice_log.sentence_key(text)
    record = {"source": _source(key, source), "key": key, "mode": "azure", "lang": lang, "ref_text": text,
              "hyp_text": azure_result.get("text") or None, "scoring": None, "azure": azure_result, "stt_settings": None,
              "clip_id": _clip_id_for(source), "line_id": _line_id_for(source, line_no)}
    uid = st.session_state["uid"]
    return _run(lambda conn: storage.append_practice(conn, uid, record))


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


# ---------- 구간(clips) ----------
def clip_list():
    """저장된 내 구간 목록(최근 수정 순, 가벼운 열 + 줄 수 n_lines). 게스트이거나 읽기에 실패하면 빈 목록."""
    if not auth_gate.is_user():
        return []
    uid = st.session_state["uid"]
    ok, rows = _call(lambda conn: storage.list_clips(conn, uid))
    return rows if ok and rows else []


def saved_clips_of(audio_sha1):
    """같은 음원(곡)에서 저장해 둔 구간들(시작 시각 순, 가벼운 열). 없거나 게스트면 빈 목록. 곡마다 한 번만 읽어 세션에 둔다."""
    if not auth_gate.is_user():
        return []
    ss = st.session_state
    key = f"saved_clips_{audio_sha1}"
    if key not in ss:
        uid = ss["uid"]
        ok, rows = _call(lambda conn: storage.list_clips_of(conn, uid, audio_sha1))
        if not ok:
            return []                                      # 읽기 실패는 캐시하지 않는다(다음에 다시 시도)
        ss[key] = rows or []
    return ss[key]


def saved_clip(clip_id):
    """clip id로 저장된 구간 기록 전체(가사 doc 포함). 없거나 게스트면 None."""
    if not auth_gate.is_user():
        return None
    uid = st.session_state["uid"]
    ok, row = _call(lambda conn: storage.load_clip_by_id(conn, uid, clip_id))
    return row if ok else None


def _saved_same_clip(audio_sha1, start, duration):
    """(음원, 시작, 길이)가 같은 저장본 전체 기록. 없으면 None."""
    uid = st.session_state["uid"]
    ok, row = _call(lambda conn: storage.load_clip(conn, uid, audio_sha1, start, duration))
    return row if ok else None


def autosave_clip(audio_sha1, ws, name, seconds, input_kind, cut=None):
    """지금 작업(구간·가사 줄·언어)이 바뀌었으면 서버에 저장하고, 이 구간의 clip id를 세션(`clip_id`)에 보관한다(연습 기록이 어느 구간인지 잇는 데 쓴다).
    스크립트가 다시 실행될 때마다 부르고, 안 바뀌었으면 아무것도 안 한다. **구간(시작·길이)을 정한 뒤에만** 행을 만든다(구간이 없으면 저장하지 않음).
    **덮어쓰기 보호**: 같은 구간의 저장본에 가사가 있는데 이 세션에서는 아직 가사를 불러오지도 새로 인식하지도 않았다면 저장하지 않는다
    (같은 곡을 다시 올리고 구간만 고르다가 저장된 가사를 빈 기록으로 덮어쓰는 사고를 막는다).
    cut: (시작, 길이). 안 주면 세션의 지금 구간을 쓴다(소리 없이 저장본만 여는 '저장된 곡' 모드는 저장된 구간을 직접 넘긴다)."""
    ss = st.session_state
    ss["clip_id"], ss["clip_line_ids"] = None, {}           # 저장되지 않는 경우(게스트·저장 끔·구간 없음)에는 연습 기록에 clip_id·line_id를 달지 않는다
    if not auth_gate.save_enabled():
        return False
    cut = cut or ss.get("cut")
    if not cut:
        return False
    start, duration = float(cut[0]), float(cut[1])
    snap = web_song.song_snapshot(ws, name, seconds, input_kind, (start, duration))
    uid = ss["uid"]
    key = (audio_sha1, round(start, 2), round(duration, 2))
    row = _saved_same_clip(audio_sha1, start, duration)
    if row and (row.get("doc") or {}).get("lines") and not snap["doc"].get("lines"):
        ss["clip_id"] = row["id"]
        ok, ids = _call(lambda conn: storage.clip_line_ids(conn, uid, row["id"]))
        ss["clip_line_ids"] = ids if ok else {}
        return False
    h = _digest_of(snap)
    state = ss.get("saved_clip_state")                      # (구간 열쇠, 내용 해시, clip id): 마지막으로 저장한 것
    if state and state[0] == key and state[1] == h:
        ss["clip_id"], ss["clip_line_ids"] = state[2], state[3]
        return True
    holder = {}

    def act(conn):
        holder["id"] = storage.save_clip(conn, uid, audio_sha1, start, duration, snap["doc"], song_title=snap["song_title"],
                                         song_duration_sec=snap["song_duration_sec"], input_type=snap["input_type"], languages=snap["languages"])
        holder["lines"] = storage.clip_line_ids(conn, uid, holder["id"])
    if _run(act):
        ss["saved_clip_state"] = (key, h, holder["id"], holder["lines"])
        ss["clip_id"], ss["clip_line_ids"] = holder["id"], holder["lines"]
        ss.pop(f"saved_clips_{audio_sha1}", None)           # 다음에 읽을 때 방금 저장한 내용으로 새로 읽는다
        return True
    return False


# ---------- 내 문장(texts) ----------
def saved_texts():
    """서버에 저장된 내 문장 목록 dict({"lines": [{"text", "languages", "lang"}]}) 또는 None. 세션에 한 번만 읽어 둔다."""
    if not auth_gate.is_user():
        return None
    ss = st.session_state
    if "saved_texts" not in ss:
        uid = ss["uid"]
        ok, doc = _call(lambda conn: storage.load_texts(conn, uid))
        if not ok:
            return None
        ss["saved_texts"] = doc
    return ss["saved_texts"]


def autosave_texts(entries):
    """내 문장 줄 목록(entries: [{"text", "languages", "lang"}])이 바뀌었으면 저장한다. 줄이 없으면 저장하지 않는다."""
    if not auth_gate.save_enabled() or not entries:
        return False
    doc = {"lines": entries}
    ss = st.session_state
    h = _digest_of(doc)
    if ss.get("saved_texts_hash") == h and "text_line_ids" in ss:
        return True
    uid = ss["uid"]
    holder = {}

    def act(conn):
        storage.save_texts(conn, uid, doc)
        holder["ids"] = storage.text_line_ids(conn, uid)
    if _run(act):
        ss["saved_texts_hash"] = h
        ss["saved_texts"] = doc
        ss["text_line_ids"] = holder["ids"]                 # 연습 기록이 줄(lines.id)과 이어지도록 {줄 번호: id}를 보관
        return True
    return False
