-- 3단계: lines 정규화 (검토 문서 16.17, 이슈 #71). clips.doc·texts.doc 안의 JSON 줄 목록을 줄 단위 행으로 옮긴다.
-- 줄 하나 = 연습 한 줄(내 노래 구간의 인식 가사 한 줄, 또는 내 문장의 한 줄). original_source_type이 어느 쪽인지 알려 주고 clip_id/text_id 중 하나만 채운다.
-- 옛 doc 열은 이번 단계에서 지우지 않고(되돌리기 대비) NULL을 허용만 한다: 앱은 더 이상 쓰지 않고, 안정 확인 뒤 별도 마이그레이션에서 지운다.

CREATE TABLE lines (
    id                   BIGSERIAL PRIMARY KEY,
    user_id              BIGINT      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    original_source_type TEXT        NOT NULL CHECK (original_source_type IN ('clip', 'text')),
    clip_id              BIGINT      REFERENCES clips (id) ON DELETE CASCADE,
    text_id              BIGINT      REFERENCES texts (id) ON DELETE CASCADE,
    line_no              INT         NOT NULL,                      -- 구간(또는 문장 묶음) 안에서의 줄 번호(1부터)
    start_sec            NUMERIC(9,3),                              -- 구간 안에서의 시작·끝(내 노래만)
    end_sec              NUMERIC(9,3),
    stt_text             TEXT,                                      -- 처음 인식한 글(내 노래만, 고쳐도 바뀌지 않음)
    text                 TEXT        NOT NULL,                      -- 연습에 쓰는 글
    edited               BOOLEAN     NOT NULL DEFAULT false,
    status               TEXT        NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate', 'confirmed', 'dropped')),
    line_kind            TEXT,                                      -- segment | split | merged (줄이 만들어진 방식)
    low_confidence       BOOLEAN     NOT NULL DEFAULT false,
    too_long             BOOLEAN     NOT NULL DEFAULT false,
    n_words              INT,
    segment_ids          INT[],                                     -- 이 줄을 만든 Whisper 구간 번호들
    lang                 TEXT,
    languages            TEXT[],
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((original_source_type = 'clip' AND clip_id IS NOT NULL AND text_id IS NULL)
        OR (original_source_type = 'text' AND text_id IS NOT NULL AND clip_id IS NULL))
);
CREATE UNIQUE INDEX lines_clip_no ON lines (clip_id, line_no) WHERE clip_id IS NOT NULL;
CREATE UNIQUE INDEX lines_text_no ON lines (text_id, line_no) WHERE text_id IS NOT NULL;
CREATE INDEX lines_user ON lines (user_id);

-- ---------- clips: doc -> recognition(줄을 뺀 나머지: STT 설정·언어·원본 segments) + lines ----------
ALTER TABLE clips ADD COLUMN recognition JSONB;
UPDATE clips SET recognition = doc - 'lines';
INSERT INTO lines (user_id, original_source_type, clip_id, line_no, start_sec, end_sec, stt_text, text, edited, status, line_kind,
                   low_confidence, too_long, n_words, segment_ids, lang)
SELECT c.user_id, 'clip', c.id, (l.value->>'no')::int, (l.value->>'start')::numeric, (l.value->>'end')::numeric,
       l.value->>'stt_text', COALESCE(l.value->>'text', ''), COALESCE((l.value->>'edited')::boolean, false),
       COALESCE(l.value->>'status', 'candidate'), l.value->>'source',
       COALESCE((l.value->>'low_confidence')::boolean, false), COALESCE((l.value->>'too_long')::boolean, false),
       (l.value->>'n_words')::int,
       ARRAY(SELECT x::int FROM jsonb_array_elements_text(COALESCE(l.value->'segment_ids', '[]'::jsonb)) AS x),
       l.value->>'lang'
FROM clips c, jsonb_array_elements(c.doc->'lines') AS l
WHERE jsonb_typeof(c.doc->'lines') = 'array';
ALTER TABLE clips ALTER COLUMN doc DROP NOT NULL;

-- ---------- texts: doc -> lines (줄 번호는 목록 순서) ----------
INSERT INTO lines (user_id, original_source_type, text_id, line_no, text, lang, languages)
SELECT t.user_id, 'text', t.id, e.n::int, COALESCE(e.value->>'text', ''), e.value->>'lang',
       CASE WHEN jsonb_typeof(e.value->'languages') = 'array'
            THEN ARRAY(SELECT x FROM jsonb_array_elements_text(e.value->'languages') AS x) END
FROM texts t, jsonb_array_elements(t.doc->'lines') WITH ORDINALITY AS e(value, n)
WHERE jsonb_typeof(t.doc->'lines') = 'array';
ALTER TABLE texts ALTER COLUMN doc DROP NOT NULL;

-- ---------- practices: 연습한 줄 ----------
ALTER TABLE practices ADD COLUMN line_id BIGINT REFERENCES lines (id) ON DELETE SET NULL;
CREATE INDEX practices_line ON practices (line_id);
