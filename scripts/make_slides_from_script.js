/*
 * 발표 PPTX 생성(2026-11-12 최종 대본 14장 기준): docs/발표_대본_20261112.md의 장(`# N.`, 12장은 `# 12-A`~`12-D`)별로
 *  - 화면이 이미지인 장은 docs/slides의 PNG를 한 장에 꽉 차게 넣고,
 *  - 텍스트인 장(1·2·7·12)은 아래 코드에 적은 내용으로 슬라이드를 만들고,
 *  - **대본** 문단은 발표자 노트로 자동 삽입한다.
 * 실행: NODE_PATH=<pptxgenjs node_modules> node scripts/make_slides_from_script.js  → docs/slides/발표_20261112_최종.pptx
 */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const SL = path.join(ROOT, "docs", "slides");
const OUT = path.join(SL, "발표_20261112_최종.pptx");
const MD = path.join(ROOT, "docs", "발표_대본_20261112.md");

// 대본 파싱: `# 제목` 줄로 구간을 나누고 key = "1".."14", "12-A".. ; **대본** 이후 `---`/다음 `#`까지를 노트로.
function parseNotes() {
  const notes = {};
  let key = null, cap = false, buf = [];
  const flush = () => { if (key && buf.length) notes[key] = buf.join("\n").trim(); buf = []; };
  for (const l of fs.readFileSync(MD, "utf-8").split("\n")) {
    const m = l.match(/^#{1,2} (\d+(?:-[A-D])?)[.\s]/);
    if (m && !l.startsWith("###")) { flush(); key = m[1]; cap = false; continue; }
    if (l.trim() === "---") { flush(); cap = false; continue; }
    if (l.trim() === "**대본**") { cap = true; continue; }
    if (cap) buf.push(l);
  }
  flush();
  return notes;
}
const N = parseNotes();

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "song lingo 최종 발표";
const W = 13.333, H = 7.5, MX = 0.6;
const F = "Arial";
const GREEN = "08833C", FOREST = "112D18", MINT = "DFF3E4", LIME = "C6F24E", PURPLE = "6250D6";

pres.defineSlideMaster({ title: "CONTENT", background: { color: "FCFCFB" },
  slideNumber: { x: 12.3, y: 7.05, w: 0.5, h: 0.3, fontSize: 11, color: "8A8985", align: "right" } });
pres.defineSlideMaster({ title: "DARK", background: { color: FOREST } });
pres.defineSlideMaster({ title: "IMG", background: { color: "FCFCFB" } });

const T = { fontFace: F, margin: 0 };
const ICON = path.join(ROOT, "app", "assets", "icon.png");   // song lingo 아이콘(1024×1024)

function imageSlide(file, key) {
  const p = path.join(SL, file);
  if (!fs.existsSync(p)) throw new Error("이미지 없음: " + p);
  const dim = require("child_process").execSync(`sips -g pixelWidth -g pixelHeight "${p}"`).toString().match(/\d+/g).slice(-2).map(Number);
  const [iw, ih] = dim;
  const sc = Math.min((W - 0.4) / iw, (H - 0.3) / ih);
  const w = iw * sc, h = ih * sc;
  const s = pres.addSlide({ masterName: "IMG" });
  s.addImage({ path: p, x: (W - w) / 2, y: (H - h) / 2, w, h });
  s.addImage({ path: ICON, x: W - 0.62, y: H - 0.62, w: 0.45, h: 0.45, altText: "song lingo 아이콘" });
  if (N[key]) s.addNotes(N[key]);
  return s;
}

function textSlide(title, key, build) {
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText(title, { ...T, x: MX, y: 0.4, w: W - 2 * MX - 0.7, h: 0.8, fontSize: 28, bold: true, color: FOREST, valign: "top" });
  s.addImage({ path: ICON, x: 12.2, y: 0.36, w: 0.55, h: 0.55, altText: "song lingo 아이콘" });
  if (N[key]) s.addNotes(N[key]);
  build(s);
  return s;
}

function bullets(s, items, o) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { indent: 18 }, breakLine: i < items.length - 1, paraSpaceAfter: o.gap ?? 8 } }));
  s.addText(runs, { ...T, x: o.x, y: o.y, w: o.w, h: o.h, fontSize: o.size || 16, color: "0B0B0B", valign: "top" });
}

function table(s, rows, o) {
  const body = rows.map((r, i) => r.map((c) => ({ text: c, options: {
    fontFace: F, fontSize: o.size || 13, bold: i === 0, color: i === 0 ? "FFFFFF" : "0B0B0B",
    fill: { color: i === 0 ? GREEN : (i % 2 ? "FFFFFF" : MINT) }, valign: "middle", margin: 0.08 } })));
  s.addTable(body, { x: o.x ?? MX, y: o.y, w: o.w ?? W - 2 * MX, colW: o.colW, border: { type: "solid", color: "BBBBBB", pt: 0.5 } });
}

// ── 1. 표지 ──
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.addText("song lingo", { ...T, x: MX, y: 1.6, w: W - 2 * MX, h: 1.2, fontSize: 60, bold: true, color: "FFFFFF" });
  s.addText("외국어 노래 속 문장을 듣고 → 따라읽거나 받아적고 → 평가를 확인하는 학습 도우미", { ...T, x: MX, y: 3.0, w: W - 2 * MX, h: 0.9, fontSize: 24, color: LIME });
  s.addText("https://songlingo.kr/clip", { ...T, x: MX, y: 4.2, w: 8, h: 0.4, fontSize: 18, color: "FFFFFF" });
  s.addText("강은영 (https://github.com/greenkey20/song-lingo)", { ...T, x: MX, y: 6.3, w: 10, h: 0.4, fontSize: 16, color: "DFF3E4" });
  s.addShape(pres.ShapeType.roundRect, { x: MX, y: 0.5, w: 0.9, h: 0.9, rectRadius: 0.15, fill: { color: "FFFFFF" }, line: { type: "none" } });
  s.addImage({ path: ICON, x: MX + 0.1, y: 0.6, w: 0.7, h: 0.7, altText: "song lingo 아이콘" });
  s.addNotes(N["1"]);
}

// ── 2. 목적 및 목표 ──
textSlide("목적 및 목표", "2", (s) => {
  s.addText([
    { text: "문제: ", options: { bold: true } },
    { text: "외국어 노래를 듣다가 무슨 언어인지, 무슨 뜻인지, 어떻게 발음하고 표기하는지 궁금하다!" },
  ], { ...T, x: MX, y: 1.4, w: W - 2 * MX, h: 0.8, fontSize: 20 });
  s.addShape(pres.ShapeType.roundRect, { x: MX, y: 2.4, w: W - 2 * MX, h: 1.5, rectRadius: 0.12, fill: { color: MINT }, line: { type: "none" } });
  s.addText("내가 이 프로젝트로 얻고 싶은 것", { ...T, x: MX + 0.3, y: 2.5, w: 8, h: 0.4, fontSize: 14, bold: true, color: GREEN });
  s.addText("실제로 쓸 수 있는 외국어 학습 도구를 만들면서, 음성 데이터가 수집되고 처리되고 분석되어 사용자에게 전달되는 전체 과정을 이해하고 직접 다룰 수 있는 개발자로 성장한다",
    { ...T, x: MX + 0.3, y: 2.9, w: W - 2 * MX - 0.6, h: 0.9, fontSize: 18, bold: true, color: FOREST });
  s.addText("여섯 가지 목표 (14장에서 다시 점검)", { ...T, x: MX, y: 4.1, w: 8, h: 0.3, fontSize: 13, color: "8A8985" });
  const goals = ["01 쓰는 도구", "02 음성·음향 처리 내재화", "03 AI 실험 능력", "04 소프트웨어 설계", "05 기술 → 사용자 경험", "06 과학적 호기심"];
  const cw = (W - 2 * MX - 0.4) / 3;
  goals.forEach((g, i) => {
    const x = MX + (i % 3) * (cw + 0.2), y = 4.5 + Math.floor(i / 3) * 1.1;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: cw, h: 0.9, rectRadius: 0.1, fill: { color: GREEN }, line: { type: "none" } });
    s.addText(g, { ...T, x, y, w: cw, h: 0.9, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
  });
});

// ── 3·4·5·6 이미지 ──
imageSlide("slide_3_overview.png", "3");
imageSlide("slide_4.png", "4");
imageSlide("slide_5_error rate.png", "5");

// ── 6. Azure (2장) ──
textSlide("Azure API를 활용한 발음 평가 및 피드백 구현", "6", (s) => {
  const items = [
    ["① 도입 배경", "처음 기획한 오류율(WER/CER)은 인식된 글의 일치도라서 한계가 있다. ⓐ 문맥으로 고쳐 적혀 오류율 0인데 Azure는 explore를 68점으로 봤다(내 녹음 1건) ⓑ 끊어 읽어도 오류율은 0.250으로 낮다 → 언어 학습에는 '어디를 어떻게 고칠지' 피드백이 필요"],
    ["② 서비스 개요", "Azure AI Speech 발음 평가. 정확도·유창성·완성도·운율·종합, 단어별 점수와 오류 종류(발음·빠짐·더해짐), 음소 펼침. 평가 기준은 TTS가 아니라 Azure의 원어민 발음 모델"],
    ["③ 사용 방법", "따라읽기 채점 후 'Azure로 평가하기' 버튼(누를 때만) → 녹음·기준 문장 글·언어만 전송(TTS 소리는 보내지 않음, 녹음은 서버에 저장 안 함) → 점수 카드 + 단어별 점수. 로그인·저장을 켜면 점수와 단어별 결과가 기록에 저장(녹음 제외)"],
    ["④ 결과 예시", "같은 문장을 네 가지로 읽은 비교표 (다음 장)"],
    ["⑤ 한계", "한 사람·한 문장·1회. 정상 읽기도 we'll 51·together 43으로 이미 낮아 완벽한 기준선이 아님. 운율·음절·음소는 영어 중심이고, 일본어·프랑스어는 기본 점수가 나오는 것까지만 확인"],
  ];
  let y = 1.3;
  const hs = [1.25, 1.0, 1.25, 0.55, 1.1];
  items.forEach(([h, t], i) => {
    s.addShape(pres.ShapeType.roundRect, { x: MX, y, w: W - 2 * MX, h: hs[i], rectRadius: 0.08, fill: { color: i === 4 ? "EEEAFB" : MINT }, line: { type: "none" } });
    s.addText(h, { ...T, x: MX + 0.2, y, w: 1.9, h: hs[i], fontSize: 15, bold: true, color: i === 4 ? PURPLE : GREEN, valign: "middle" });
    s.addText(t, { ...T, x: MX + 2.2, y, w: W - 2 * MX - 2.4, h: hs[i], fontSize: 13, color: "0B0B0B", valign: "middle" });
    y += hs[i] + 0.1;
  });
});
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("같은 문장을 네 가지로 읽어 보니 (Azure 발음 평가)", { ...T, x: MX, y: 0.4, w: W - 2 * MX - 0.7, h: 0.8, fontSize: 28, bold: true, color: FOREST, valign: "top" });
  s.addImage({ path: ICON, x: 12.2, y: 0.36, w: 0.55, h: 0.55, altText: "song lingo 아이콘" });
  if (N["6"]) s.addNotes(N["6"]);
  s.addText("문장: We'll sing together until the morning comes. (직접 쓴 문장, 11-05 화면 캡처 4장)", { ...T, x: MX, y: 1.2, w: W - 2 * MX, h: 0.35, fontSize: 13, color: "8A8985" });
  table(s, [
    ["읽기 조건", "정확도", "유창성", "완성도", "운율", "종합", "Azure가 표시한 단어", "오류율(WER)"],
    ["① 정상", "81", "90", "71", "81", "79", "we'll 51 · together 43(발음), 나머지 91~97", "(캡처 없음)"],
    ["② 단어 생략", "32", "77", "14", "69", "41", "together·the·comes 빠짐", "0.750"],
    ["③ 끊어 읽기", "45", "49", "14", "66", "38", "We'll 빠짐, the 더해짐", "0.250"],
    ["④ 틀린 발음", "56", "88", "43", "74", "61", "We'll 빠짐, sing 47 · together 44 · the 55(발음)", "0.375"],
  ], { y: 1.65, colW: [1.5, 0.9, 0.9, 0.9, 0.8, 0.8, 4.5, 1.83], size: 13 });
  bullets(s, [
    "정상(79)보다 세 경우 모두 종합이 내려갔다(41·38·61): 차이가 평가에 반영된다",
    "끊어 읽기는 유창성이 90 → 49로 가장 크게 내려갔는데 오류율은 0.250으로 낮다 → 쉼·속도는 오류율이 못 잡고 Azure(유창성)가 잡는다",
    "단어 생략은 '빠짐' 표시와 완성도 71 → 14로 반응했다",
  ], { x: MX, y: 4.7, w: W - 2 * MX, h: 1.6, size: 15, gap: 8 });
  s.addText("완성도·정확도 정의는 Microsoft 문서 기준[일반 지식]. 완성도 계산식은 문서에 없어 이 표본으로 확인하지 못했다 [미확인]", { ...T, x: MX, y: 6.5, w: W - 2 * MX, h: 0.4, fontSize: 12, color: PURPLE });
}

// ── 7. 편집 거리 ──
textSlide("채점의 핵심: 편집 거리를 표로 한 칸씩 채운다 (동적 계획법)", "7", (s) => {
  table(s, [
    ["정답 \\ 인식", "∅", "we", "seeing", "together"],
    ["∅", "0", "1", "2", "3"],
    ["we", "1", "0", "1", "2"],
    ["sing", "2", "1", "1", "2"],
    ["together", "3", "2", "2", "1"],
    ["until", "4", "3", "3", "2"],
  ], { x: MX, y: 1.5, w: 6.4, colW: [1.6, 1.2, 1.2, 1.2, 1.2], size: 15 });
  s.addText("정답 we sing together until × 인식 we seeing together", { ...T, x: MX, y: 4.9, w: 6.4, h: 0.3, fontSize: 12, color: "8A8985" });
  bullets(s, [
    "되짚은 길: we = we 일치 → sing → seeing 바뀜(S) → together 일치 → until 빠짐(D)",
    "점화식: d[i][j] = 위 칸+1(삭제) · 왼쪽 칸+1(삽입) · 대각선+(같으면 0, 다르면 1)(일치·바뀜) 중 최솟값",
    "오른쪽 아래 칸 = 최소 수정 횟수 = 2",
    "WER = (S + D + I) ÷ N = (1 + 1 + 0) ÷ 4 = 0.50",
  ], { x: 7.3, y: 1.5, w: 5.4, h: 3.2, size: 15, gap: 10 });
  s.addShape(pres.ShapeType.roundRect, { x: 7.3, y: 4.8, w: 5.4, h: 1.5, rectRadius: 0.1, fill: { color: "F1F1EF" }, line: { type: "none" } });
  s.addText("cost = 0 if ref[i-1] == hyp[j-1] else 1\nd[i][j] = min(d[i-1][j] + 1,   # 삭제\n             d[i][j-1] + 1,   # 삽입\n             d[i-1][j-1] + cost)",
    { ...T, x: 7.45, y: 4.9, w: 5.2, h: 1.3, fontSize: 12, fontFace: "Courier New", color: "0B0B0B", valign: "top" });
});

// ── 8~11 이미지 ──
imageSlide("slide_8.png", "8");
imageSlide("slide_9_whisper.png", "9");
imageSlide("slide_10_demucs.png", "10");
imageSlide("slide_11_compare.png", "11");

// ── 12-A ──
textSlide("시행착오·실험 1 — 노래와 가사를 어떻게 확보할까?", "12-A", (s) => {
  s.addText("초기 구상: 노래 검색 → 곡 정보 확인 → 가사 확보 → 학습 문장 선택", { ...T, x: MX, y: 1.3, w: W - 2 * MX, h: 0.4, fontSize: 16, color: "8A8985" });
  table(s, [
    ["접근 방식", "처리 흐름", "고려한 문제"],
    ["① 곡 식별 후 가사 검색", "주변 소리 → Shazam류 음원 식별 API → 곡 정보 → 가사 제공 API", "API 키·비용·이용 조건, 가사 제공 범위 및 저작권"],
    ["② 음원 직접 입력 후 STT", "파일 업로드 / 주변 음악 녹음 → Whisper STT → 인식 결과 수정", "반주·발성·음질에 따른 인식 정확도"],
    ["③ 가사 텍스트 직접 입력", "사용자가 문장·가사 입력 → 표준 발음·채점", "자동 곡 검색은 없지만 가장 단순한 대안"],
  ], { y: 1.85, colW: [3.0, 5.2, 3.93], size: 14 });
  bullets(s, [
    "가사 사이트 스크래핑은 이용약관·저작권·유지보수 위험으로 제외",
    "음원 식별 API·가사 제공 서비스는 키·약관·요금·언어 지원이 불확실해 보류",
    "파일 업로드와 마이크 녹음을 같은 STT 파이프라인으로 통합",
  ], { x: MX, y: 4.5, w: W - 2 * MX, h: 1.4, size: 15 });
  s.addShape(pres.ShapeType.roundRect, { x: MX, y: 6.0, w: W - 2 * MX, h: 0.7, rectRadius: 0.1, fill: { color: LIME }, line: { type: "none" } });
  s.addText("현재 흐름: 음원 업로드 / 주변 음악 녹음 → 로컬 Whisper STT → 사용자 수정 → 따라읽기·받아쓰기", { ...T, x: MX + 0.2, y: 6.0, w: W - 2 * MX - 0.4, h: 0.7, fontSize: 16, bold: true, color: FOREST, valign: "middle" });
});

// ── 12-B ──
textSlide("실험 | 노래 구간 STT — 분리한 보컬이 항상 더 잘 인식될까?", "12-B", (s) => {
  s.addText("실험 질문", { ...T, x: MX, y: 1.3, w: 5.8, h: 0.35, fontSize: 16, bold: true, color: GREEN });
  s.addText("원곡(mix)과 Demucs 분리 보컬(vocals) 중 Whisper 입력으로 어느 쪽이 적합한가? VAD·온도 폴백·모델 크기의 영향도 확인", { ...T, x: MX, y: 1.7, w: 5.8, h: 1.0, fontSize: 14, valign: "top" });
  s.addText("데이터와 비교 방법", { ...T, x: MX, y: 2.9, w: 5.8, h: 0.35, fontSize: 16, bold: true, color: GREEN });
  bullets(s, [
    "영어 노래 20초 구간: 8개(231단어) + 다른 곡 6개(165단어) = 14개, 396단어",
    "같은 구간의 원곡·분리 보컬을 각각 준비",
    "정답은 분리 보컬이 아닌 원곡을 들으며 직접 작성",
    "지표: micro-WER (낮을수록 좋음)",
  ], { x: MX, y: 3.3, w: 5.8, h: 2.6, size: 14 });
  table(s, [
    ["단계", "조건", "결과"],
    ["A 진단", "temperature=0.0 (폴백 끔)", "반복 루프 많음. base+보컬+VAD 켬 0.494가 최고로 보임"],
    ["B 기본 재검증", "폴백 켬, 3회 반복", "원곡+VAD 켬은 5/8 구간 빈 결과 → VAD 끄기. 최고 base+보컬+VAD 끔 0.382"],
    ["C 모델 크기", "VAD 끔", "보컬 base 0.382 → small 0.326 → medium 0.257. 처음 8개: medium 원곡 0.177 / 보컬 0.257"],
    ["D 새 곡 6개", "medium", "원곡 0.303 / 보컬 0.285. 14개 합산 원곡 0.230 / 보컬 0.269 → 우열 미확정"],
  ], { x: 6.7, y: 1.3, w: 6.0, colW: [1.3, 1.6, 3.1], size: 11 });
  s.addShape(pres.ShapeType.roundRect, { x: 6.7, y: 5.6, w: 6.0, h: 1.0, rectRadius: 0.1, fill: { color: LIME }, line: { type: "none" } });
  s.addText("결정: medium + 원곡 + VAD 끔 + 기본 폴백. Demucs 분리는 필수 전처리가 아니라 듣기 연습 선택 기능", { ...T, x: 6.85, y: 5.6, w: 5.7, h: 1.0, fontSize: 14, bold: true, color: FOREST, valign: "middle" });
  s.addText("한계: 영어 노래 14개 구간, 정답 작성자 1명. 3회 반복은 통계적 유의성 검정이 아님", { ...T, x: MX, y: 6.5, w: 5.8, h: 0.5, fontSize: 12, color: PURPLE });
});

// ── 12-C ──
textSlide("음악적 유형별 관찰 — 보컬 분리 효과는 입력 특성에 따라 달라졌을까?", "12-C", (s) => {
  s.addText("서로 다른 음악적 특성의 구간에서 원곡(mix)과 분리 보컬(vocals) 비교 (WER 낮을수록 좋음, 원곡 → 보컬)", { ...T, x: MX, y: 1.2, w: W - 2 * MX, h: 0.5, fontSize: 14, color: "8A8985" });
  table(s, [
    ["유형 (표본 수)", "관찰 결과", "해석"],
    ["또렷한 솔로 보컬 (5)", "c03·c09·c10은 분리 보컬 WER이 낮음, c01·c02는 차이 거의 없음", "분리가 항상 필요한 것은 아니며 구간별 차이가 있음"],
    ["두꺼운 반주 (4)", "c04 0.41→0.59, c05 0.34→0.79로 원곡 우세. c11 동일(0.09)", "반주가 두꺼워도 분리가 항상 개선하지는 않음"],
    ["합창·아카펠라 (4)", "c07 차이 거의 없음, c13 동일(0.06), c14 보컬 우세(0.29→0.19)", "보컬 편성만으로 우열을 설명하기 어려움"],
    ["힙합·랩 (1)", "c12는 원곡·보컬 모두 0.6 이상. 이 구간을 빼면 검증 결과의 우열이 바뀜", "어려운 단일 구간이 전체 결과에 미치는 영향 확인"],
  ], { y: 1.8, colW: [2.6, 5.2, 4.33], size: 14 });
  bullets(s, [
    "한쪽이 모든 유형에서 일관되게 우세하지는 않았다",
    "음악적 특성에 따라 분리 효과가 달라질 가능성을 관찰했다",
  ], { x: MX, y: 5.3, w: W - 2 * MX, h: 1.0, size: 16 });
  s.addText("탐색적 분석이며 유형별 성능 순위나 일반화된 결론이 아니다. 유형별 표본 수가 제한적이다.", { ...T, x: MX, y: 6.5, w: W - 2 * MX, h: 0.4, fontSize: 13, color: PURPLE });
});

// ── 12-D ──
textSlide("실험의 한계와 다음 검증 — 말할 수 있는 것, 더 확인할 것", "12-D", (s) => {
  table(s, [
    ["현재 실험의 한계", "다음에 시도할 것"],
    ["표본 수와 유형 불균형: 20초 구간 14개, 힙합은 1개뿐", "유형별로 서로 다른 곡 10~15개씩 추가 확보"],
    ["유형 분류 기준의 혼재: 장르·반주 밀도·보컬 편성·발성 방식이 섞임", "반주 밀도 / 보컬 구성 / 발성 스타일을 독립 속성으로 기록"],
    ["정답 데이터의 불확실성: 한 사람이 원곡을 듣고 작성", "2인 이상 독립 전사·교차 검수, 채점 규칙 사전 정의"],
    ["평가와 반복의 한계: 3회 반복은 유의성 검정이 아니며 WER은 발음 평가가 아님", "곡별·유형별 WER, 오류 유형(S/D/I), 빈 인식, 반복 현상 평가"],
    ["분리 품질의 별도 측정 부족", "청취 평가, 정답 stem이 있는 데이터에서 SDR 등 확인"],
  ], { y: 1.3, colW: [6.4, 5.73], size: 13 });
  s.addText("이번 실험으로 확인한 것", { ...T, x: MX, y: 4.8, w: 6, h: 0.35, fontSize: 16, bold: true, color: GREEN });
  bullets(s, [
    "이번 표본에서 medium은 base보다 나은 인식 결과",
    "원곡에 VAD를 적용하면 특정 구간 가사가 통째로 사라지는 문제 재현",
    "원곡과 분리 보컬의 우열은 구간에 따라 달라짐",
  ], { x: MX, y: 5.2, w: W - 2 * MX, h: 1.2, size: 15 });
  s.addText("의미: 입력이 항상 정답이라고 증명한 것이 아니라, 가설을 실험 결과에 맞춰 수정하고 후속 검증 질문을 구체화한 것", { ...T, x: MX, y: 6.6, w: W - 2 * MX, h: 0.5, fontSize: 13, color: PURPLE });
});

// ── 13. AI 코드 다루기 ──
textSlide("시행착오 사례 2 — AI가 쓴 코드를 어떻게 내 것으로 만들었나?", "13", (s) => {
  s.addText("코드 생성보다 어려웠던 것은 이해와 검증이었다", { ...T, x: MX, y: 1.15, w: 10, h: 0.35, fontSize: 15, color: "8A8985" });
  const arrow = (y) => s.addText("↓", { ...T, x: 0, y, w: W, h: 0.25, fontSize: 16, color: "8A8985", align: "center", valign: "middle" });
  const head = (t, y, c) => s.addText(t, { ...T, x: MX, y, w: 6, h: 0.35, fontSize: 17, bold: true, color: c || FOREST });
  // ① 문제 발견
  head("① 문제 발견", 1.65);
  s.addText("19~34%", { ...T, x: MX, y: 2.0, w: 3.2, h: 0.55, fontSize: 32, bold: true, color: FOREST });
  s.addText("기존 주요 모듈의 주석·docstring 비율", { ...T, x: 4.0, y: 2.1, w: 6, h: 0.4, fontSize: 13, color: "8A8985", valign: "middle" });
  s.addText("수업에서 배운 코드와 AI가 추가한 코드의 경계가 불분명했다.", { ...T, x: MX, y: 2.6, w: 11, h: 0.35, fontSize: 15 });
  arrow(3.0);
  // ② 개선 시도
  head("② 개선 시도", 3.3);
  bullets(s, ["파일·함수의 역할과 입출력 명시", "수업과 같은 부분 / 수업에서 다루지 않은 부분 구분", "인라인 주석은 코드의 '왜'를 설명", "주석 수정 시 기존 동작 유지"], { x: MX, y: 3.65, w: 11, h: 1.35, size: 14, gap: 3 });
  arrow(5.0);
  // ③ 검증
  head("③ 검증", 5.3);
  s.addText("동일", { ...T, x: MX, y: 5.65, w: 3, h: 0.45, fontSize: 26, bold: true, color: GREEN });
  s.addText("65개", { ...T, x: 5.2, y: 5.65, w: 3, h: 0.45, fontSize: 26, bold: true, color: GREEN });
  s.addText("주석 제외 AST 비교", { ...T, x: MX, y: 6.1, w: 4, h: 0.3, fontSize: 12, color: "8A8985" });
  s.addText("당시 단위 테스트 통과", { ...T, x: 5.2, y: 6.1, w: 4, h: 0.3, fontSize: 12, color: "8A8985" });
  s.addText("주석만 바뀌었고 실행 코드는 바뀌지 않았는지 확인했다.", { ...T, x: 8.6, y: 5.65, w: 4.2, h: 0.75, fontSize: 13, valign: "middle" });
  // ④ 한계와 배운 점
  s.addShape(pres.ShapeType.roundRect, { x: MX, y: 6.5, w: W - 2 * MX, h: 0.6, rectRadius: 0.08, fill: { color: LIME }, line: { type: "none" } });
  s.addText("④ 주석을 읽을 수 있는 것과 코드를 이해하는 것은 다르다. 아직 내 말로 설명 못 하는 부분은 핵심 함수부터 직접 설명하며 공부할 계획", { ...T, x: MX + 0.2, y: 6.5, w: W - 2 * MX - 0.4, h: 0.6, fontSize: 13, bold: true, color: FOREST, valign: "middle" });
});

// ── 14. 결과·한계·다음 단계 ──
textSlide("프로젝트 결과 · 한계 · 다음 단계", "14", (s) => {
  s.addText("실사용 가능한 학습 도구에서 시작해, 음성 데이터의 이해와 활용으로", { ...T, x: MX, y: 1.15, w: 11, h: 0.35, fontSize: 15, color: "8A8985" });
  const cols = [
    ["RESULT · 구현 결과", GREEN, MINT, ["Oracle Cloud 배포·HTTPS", "아이폰 홈 화면 바로가기", "로그인·PostgreSQL 사용자별 저장", "STT·TTS·채점·음향 분석 통합", "비밀번호는 scrypt 해시, 음성 파일은 DB 미저장"]],
    ["LIMIT · 검증 한계", PURPLE, "EEEAFB", ["다국어별 품질 검증 부족", "성조·악센트·억양 평가 미지원", "1인·조용한 환경 중심 테스트", "학습 기록·복습 기능의 확장 필요"]],
    ["NEXT · 다음 단계", FOREST, "F1F1EF", ["다양한 화자·언어 테스트", "학습 이력·복습 기능 고도화", "음향 기반 시각화·창작", "GPU 기반 Demucs 학습 탐구"]],
  ];
  const cw = (W - 2 * MX - 0.4) / 3;
  cols.forEach(([h, c, bg, items], i) => {
    const x = MX + i * (cw + 0.2);
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.75, w: cw, h: 3.9, rectRadius: 0.1, fill: { color: bg }, line: { type: "none" } });
    s.addText(h, { ...T, x: x + 0.25, y: 1.95, w: cw - 0.5, h: 0.4, fontSize: 17, bold: true, color: c });
    bullets(s, items, { x: x + 0.25, y: 2.5, w: cw - 0.5, h: 3.0, size: 14, gap: 8 });
  });
  s.addShape(pres.ShapeType.roundRect, { x: MX, y: 5.95, w: W - 2 * MX, h: 1.1, rectRadius: 0.1, fill: { color: FOREST }, line: { type: "none" } });
  s.addText("듣고, 따라읽고, 확인한다.", { ...T, x: MX, y: 6.0, w: W - 2 * MX, h: 0.5, fontSize: 22, bold: true, color: LIME, align: "center", valign: "middle" });
  s.addText("소리가 데이터가 되고, 모델을 지나, 학습 경험으로 돌아오는 과정을 구현하고 탐구했다.", { ...T, x: MX, y: 6.5, w: W - 2 * MX, h: 0.4, fontSize: 14, color: "FFFFFF", align: "center", valign: "middle" });
});


pres.writeFile({ fileName: OUT }).then((f) => console.log("saved", f));
