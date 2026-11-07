-- 2단계: meanings (검토 문서 16.17, 이슈 #69). 한글 뜻·표현 설명을 **모든 사용자가 공유하는 캐시**로 저장한다(같은 문장은 한 번만 OpenAI를 부름).
-- 문장 글은 저장하지 않는다: cache_key = sha1(언어 + "\n" + 글.strip())의 앞 16자(meaning._key와 같음)와 모델이 만든 설명만 둔다.
-- lines에 외래키를 두지 않는다: 글을 고치면 해시가 바뀌어 옛 설명이 붙지 않는다(조회할 때마다 지금 글로 해시를 계산).
CREATE TABLE meanings (
    id             BIGSERIAL PRIMARY KEY,
    cache_key      TEXT        NOT NULL,
    kind           TEXT        NOT NULL CHECK (kind IN ('translation_ko', 'notes')),
    lang           TEXT,                                -- 파일 캐시에서 옮긴 행은 언어를 알 수 없어 NULL
    content        JSONB       NOT NULL,                -- translation_ko: 글 하나(JSON 문자열), notes: {"words","expressions","grammar","examples"}
    model          TEXT,
    prompt_version INT         NOT NULL DEFAULT 1,      -- 프롬프트·형식을 바꾸면 올린다(표현 설명의 옛 *.notes2.json이 2)
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (cache_key, kind, prompt_version)
);
