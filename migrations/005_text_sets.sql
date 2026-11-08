-- 내 문장 여러 묶음 저장 (검토 문서 16.17 13절, 이슈 #75). 지금까지는 사용자당 문장 묶음이 하나뿐(UNIQUE (user_id))이라 새로 입력하면 이전 묶음이 덮어써졌다.
-- 이 제약을 없애고 사용자당 여러 묶음을 둔다. 묶음 하나 = 내 문장 입력창 하나의 내용 전체(여러 줄은 lines 테이블). 서버에 이미 있는 한 묶음은 그대로 한 묶음이 된다.
-- 사용자당 상한(50개)은 앱(storage.MAX_TEXT_SETS)이 검사한다. title은 사용자가 입력했을 때만 값이 있고, 비어 있으면 화면이 첫 줄과 시각으로 자동 제목을 보여 준다.
ALTER TABLE texts DROP CONSTRAINT texts_user_id_key;
CREATE INDEX texts_user_updated ON texts (user_id, updated_at DESC);
