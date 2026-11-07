-- song-lingo 사용자별 저장 스키마 (검토 문서 16.16 11절). 앱이 시작할 때 storage.migrate()가 아직 적용 안 된 파일만 순서대로 실행한다.
-- 규칙: 이미 적용된 파일은 고치지 않는다(바꿀 때는 002_*.sql처럼 새 파일을 추가). 비밀번호·토큰 원문은 저장하지 않는다(해시만).

CREATE TABLE users (
    id           BIGSERIAL PRIMARY KEY,
    username     TEXT        NOT NULL,
    pw_salt      BYTEA       NOT NULL,
    pw_hash      BYTEA       NOT NULL,
    failed_count INT         NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    save_on      BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login   TIMESTAMPTZ
);
-- 아이디는 대소문자를 구분하지 않고 유일하다(Alice와 alice는 같은 아이디)
CREATE UNIQUE INDEX users_username_lower ON users (lower(username));

CREATE TABLE login_tokens (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash BYTEA       NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_used  TIMESTAMPTZ
);
CREATE INDEX login_tokens_user ON login_tokens (user_id);

CREATE TABLE songs (
    user_id       BIGINT      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    digest        TEXT        NOT NULL,          -- 음원 bytes의 sha1(곡 지문). 음원 자체는 저장하지 않는다
    name          TEXT,
    seconds       REAL,
    input         TEXT,                          -- 'file' | 'record'
    clip_start    REAL,
    clip_duration REAL,
    languages     TEXT[],
    doc           JSONB       NOT NULL,          -- 가사 줄(lines.json과 같은 구조)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, digest)
);

CREATE TABLE sentences (
    user_id    BIGINT PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    doc        JSONB       NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE attempts (
    id       BIGSERIAL PRIMARY KEY,
    user_id  BIGINT      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    ts       TIMESTAMPTZ NOT NULL DEFAULT now(),
    source   TEXT,                               -- 'sample' | 'lyrics' | 'song'
    key      TEXT,                               -- practice_log.sentence_key와 같은 문장 열쇠
    mode     TEXT,                               -- 'read' | 'dictation' | 'azure'
    lang     TEXT,
    ref_text TEXT,
    hyp_text TEXT,
    score    JSONB,
    azure    JSONB,
    stt      TEXT
);
CREATE INDEX attempts_user_ts ON attempts (user_id, ts DESC);
