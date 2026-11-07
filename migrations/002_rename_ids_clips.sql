-- 1단계: 이름·id·clips (검토 문서 16.17, 이슈 #67). 001에서 만든 테이블의 이름과 열을 정리한다. 이미 쌓인 데이터는 그대로 옮긴다.
-- 규칙: 테이블은 복수형, 기본키는 id BIGSERIAL, 시각은 created_at/updated_at, 단위는 열 이름에 넣는다(_sec).

-- ---------- users ----------
ALTER TABLE users ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- ---------- songs -> clips: 곡(파일) 하나에서 구간을 여러 개 저장 ----------
-- 구간 정보가 없는 옛 행은 가사도 없으므로(구간을 자른 뒤에야 가사를 인식함) 지운다.
DELETE FROM songs WHERE clip_start IS NULL OR clip_duration IS NULL;
ALTER TABLE songs RENAME TO clips;
ALTER TABLE clips DROP CONSTRAINT songs_pkey;                              -- 옛 기본키 (user_id, digest)
ALTER TABLE clips ADD COLUMN id BIGSERIAL PRIMARY KEY;
ALTER TABLE clips RENAME COLUMN digest TO audio_sha1;                      -- 음원 bytes의 sha1(음원 자체는 저장하지 않음)
ALTER TABLE clips RENAME COLUMN name TO song_title;
ALTER TABLE clips RENAME COLUMN input TO input_type;
ALTER TABLE clips RENAME COLUMN seconds TO song_duration_sec;
ALTER TABLE clips RENAME COLUMN clip_start TO clip_start_sec;
ALTER TABLE clips RENAME COLUMN clip_duration TO clip_duration_sec;
-- 소수(REAL)는 같은 값이 미세하게 달라 비교가 어긋날 수 있어 소수 2자리 NUMERIC으로 바꾼다.
ALTER TABLE clips ALTER COLUMN song_duration_sec TYPE NUMERIC(9,2) USING song_duration_sec::numeric(9,2);
ALTER TABLE clips ALTER COLUMN clip_start_sec TYPE NUMERIC(9,2) USING clip_start_sec::numeric(9,2);
ALTER TABLE clips ALTER COLUMN clip_duration_sec TYPE NUMERIC(9,2) USING clip_duration_sec::numeric(9,2);
ALTER TABLE clips ALTER COLUMN clip_start_sec SET NOT NULL;
ALTER TABLE clips ALTER COLUMN clip_duration_sec SET NOT NULL;
-- 같은 곡의 같은 구간은 한 행(다른 구간은 다른 행)
ALTER TABLE clips ADD CONSTRAINT clips_user_audio_range_key UNIQUE (user_id, audio_sha1, clip_start_sec, clip_duration_sec);

-- ---------- sentences -> texts ----------
ALTER TABLE sentences RENAME TO texts;
ALTER TABLE texts DROP CONSTRAINT sentences_pkey;                          -- 옛 기본키 (user_id)
ALTER TABLE texts ADD COLUMN id BIGSERIAL PRIMARY KEY;
ALTER TABLE texts ADD COLUMN title TEXT;                                   -- 문장 묶음 이름(지금 화면은 묶음 하나만 다룸)
ALTER TABLE texts ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE texts ADD CONSTRAINT texts_user_id_key UNIQUE (user_id);       -- 지금은 사용자당 한 묶음(여러 개로 늘릴 때 이 제약만 없앤다)

-- ---------- attempts -> practices ----------
ALTER TABLE attempts RENAME TO practices;
ALTER INDEX attempts_pkey RENAME TO practices_pkey;
ALTER SEQUENCE attempts_id_seq RENAME TO practices_id_seq;
ALTER TABLE practices RENAME COLUMN ts TO created_at;                      -- 채점 결과를 저장한 시각
ALTER TABLE practices RENAME COLUMN score TO scoring;                      -- 따라읽기·받아쓰기의 WER/CER 결과
ALTER TABLE practices ALTER COLUMN stt TYPE JSONB USING
    CASE WHEN stt IS NULL OR stt = '' THEN NULL
         WHEN left(ltrim(stt), 1) = '{' THEN stt::jsonb
         ELSE to_jsonb(stt) END;
ALTER TABLE practices RENAME COLUMN stt TO stt_settings;                   -- 따라읽기에서 쓴 STT 설정
ALTER TABLE practices ADD COLUMN clip_id BIGINT REFERENCES clips (id) ON DELETE SET NULL;   -- 연습한 구간(내 노래일 때만)
ALTER INDEX attempts_user_ts RENAME TO practices_user_created_at;
CREATE INDEX practices_clip ON practices (clip_id);
