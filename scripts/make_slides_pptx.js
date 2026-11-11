/*
 * 발표 장표(PPTX) 초안을 만든다: 장표 내용("화면")은 이 파일에 직접 적혀 있고, 발표자 노트는 docs/발표_대본_20261112.md의 "대본"에서 가져온다 + docs/slides/*.png. 이슈 #21.
 * 장 번호는 대본 문서의 `## N.`(1~13)과 같다. 대본의 장 번호나 장 안의 `> ` 문단 순서를 바꾸면 아래 noteOf("장", 시작, 끝) 호출도 함께 고친다(2026-11-12 개정).
 *
 * 실행 (프로젝트 루트에서):
 *   1) pptxgenjs를 어디든 설치한다:  mkdir -p /tmp/pptx && cd /tmp/pptx && npm init -y && npm install pptxgenjs
 *   2) NODE_PATH=/tmp/pptx/node_modules PPTX_SKILL_DIR=<pptx 스킬 폴더(선택, 테마 색 적용용)> node scripts/make_slides_pptx.js
 *      발표자 노트는 docs/발표_대본_20261112.md의 "대본"에서 자동으로 가져온다(대본을 고치면 다시 실행).
 *   → docs/slides/발표_20261112_초안.pptx
 *
 * 색은 웹 앱(theme.py)과 같다: 짙은 초록(FOREST 112D18)이 바탕·제목, 버튼 초록(08833C)이 주색, 민트(DFF3E4)가 카드, 라임(C6F24E)이 강조(설명 상자와 같은 용도),
 * 보라(6250D6)는 앱처럼 "틀린 것·해석(추정)·한계"에만 쓴다. 파형 파랑(1F77B4)은 파형 그림에만 쓴다.
 * 글꼴은 Arial(한글은 PowerPoint가 기본 한글 글꼴로 대체): 발표 PC에 없는 글꼴 때문에 깨지는 것을 피하려고 시스템 기본 글꼴만 쓴다.
 */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "docs", "slides", "발표_20261112_초안.pptx");
const LOGO = path.join(ROOT, "app", "assets", "logo.png");   // 2400×892, 투명 배경, 검은 글자라 어두운 바탕에는 흰 카드 위에 올린다
const ICON = path.join(ROOT, "app", "assets", "icon.png");   // 1024×1024 음표(초록·라임)
// 발표자 노트: 대본 문서에서 장(`## N.`)마다 "**대본**" 아래의 `> ` 문단을 뽑는다(문단 순서대로 슬라이드에 나눠 넣음). 빈 인용 줄(`>`)은 건너뛴다.
function parseNotes(mdPath) {
  const notes = {};
  let key = null, cap = false;
  for (const l of fs.readFileSync(mdPath, "utf-8").split("\n")) {
    const m = l.match(/^## (\d+)\./);
    if (m) { key = m[1]; cap = false; continue; }
    if (l.startsWith("## \u{1F4CE}")) { key = null; cap = false; continue; }
    if (l.trim() === "**대본**" && key) { cap = true; notes[key] = notes[key] || []; continue; }
    if (cap) {
      if (l.trim() === ">") continue;
      if (l.startsWith("> ")) notes[key].push(l.slice(2).trim());
      else if (l.trim() !== "") cap = false;
    }
  }
  return notes;
}
const NOTES = parseNotes(path.join(ROOT, "docs", "발표_대본_20261112.md"));
const SKILL = process.env.PPTX_SKILL_DIR;

const THEME = {
  name: "song-lingo",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "0B0B0B", lt1: "FCFCFB", dk2: "112D18", lt2: "DFF3E4",
    accent1: "08833C", accent2: "1A9F4C", accent3: "C6F24E", accent4: "6250D6", accent5: "8A8985", accent6: "1F77B4",
    hlink: "08833C", folHlink: "6250D6",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "song-lingo 최종 발표 (초안)";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.333, H = 7.5, MX = 0.6;

// ───────── 레이아웃(슬라이드 틀) ─────────
pres.defineSlideMaster({
  title: "DARK",
  background: { color: "112D18" },
  objects: [],
  slideNumber: { x: 12.3, y: 7.02, w: 0.5, h: 0.3, fontSize: 11, color: "8A8985", align: "right" },
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FCFCFB" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.88, w: W - 2 * MX, h: 0.9, fontSize: 34, bold: true, color: "112D18", align: "left", valign: "top", margin: 0 }, text: "" } },
    { image: { x: 12.2, y: 0.36, w: 0.55, h: 0.55, path: ICON, altText: "song-lingo 아이콘" } },
  ],
  slideNumber: { x: 12.3, y: 7.02, w: 0.5, h: 0.3, fontSize: 11, color: "8A8985", align: "right" },
});
pres.defineSlideMaster({
  title: "IMAGE",
  background: { color: "FCFCFB" },
  objects: [],
  slideNumber: { x: 12.3, y: 7.1, w: 0.5, h: 0.25, fontSize: 10, color: "8A8985", align: "right" },
});

// ───────── 도우미 ─────────
const T = { fontFace: "Arial", isTextBox: true, margin: 0 };

function pill(slide, text, opts = {}) {
  const w = opts.w || Math.max(1.4, text.length * 0.17 + 0.5);
  slide.addShape(pres.ShapeType.roundRect, { x: opts.x ?? MX, y: opts.y ?? 0.42, w, h: 0.36, rectRadius: 0.18, fill: { color: opts.fill || "C6F24E" }, line: { type: "none" }, objectName: "chapter-pill" });
  slide.addText(text, { ...T, x: opts.x ?? MX, y: opts.y ?? 0.42, w, h: 0.36, fontSize: 12, bold: true, color: opts.color || "112D18", align: "center", valign: "middle", objectName: "chapter-pill-text" });
}

function card(slide, x, y, w, h, o = {}) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.12, fill: { color: o.fill || "DFF3E4" }, line: o.line ? { color: o.line, width: 1.25 } : { type: "none" },
    shadow: o.shadow === false ? undefined : { type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 },
    objectName: o.name || "card",
  });
}

function badge(slide, x, y, n, o = {}) {
  const d = o.d || 0.52;
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: o.fill || "08833C" }, line: { type: "none" }, objectName: "badge" });
  slide.addText(String(n), { ...T, x, y, w: d, h: d, fontSize: o.size || 18, bold: true, color: o.color || "FFFFFF", align: "center", valign: "middle", objectName: "badge-text" });
}

function tag(slide, text, x, y, kind = "temp") {
  const fills = { temp: ["6250D6", "FFFFFF"], ok: ["C6F24E", "112D18"], gray: ["8A8985", "FFFFFF"] };
  const [f, c] = fills[kind];
  const w = Math.max(0.9, text.length * 0.15 + 0.4);
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h: 0.32, rectRadius: 0.16, fill: { color: f }, line: { type: "none" } });
  slide.addText(text, { ...T, x, y, w, h: 0.32, fontSize: 12, bold: true, color: c, align: "center", valign: "middle" });
}

function content(title, chapterLabel, notes, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (chapterLabel) pill(s, chapterLabel);
  if (notes) s.addNotes(notes);
  return s;
}

function noteOf(key, from, to) {
  const arr = NOTES[key] || [];
  return arr.slice(from, to).join("\n\n");
}

function bullets(slide, items, o) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { indent: 18 }, breakLine: i < items.length - 1, paraSpaceAfter: o.gap ?? 8 } }));
  slide.addText(runs, { ...T, x: o.x, y: o.y, w: o.w, h: o.h, fontSize: o.size || 16, color: o.color || "0B0B0B", valign: "top" });
}

let slideNo = 0;
const section = (t) => pres.addSection({ title: t });

// ═════════ 1장 ═════════
section("1 한 줄 소개");
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "1 한 줄 소개" });
  s.addNotes(noteOf("1"));
  // 파형 모티프: 막대 파형
  const bars = [0.4, 0.7, 1.1, 1.6, 2.0, 1.4, 0.9, 1.8, 2.3, 1.7, 0.9, 0.6, 1.3, 1.9, 1.2, 0.7, 0.4, 0.8];
  bars.forEach((h, i) => {
    s.addShape(pres.ShapeType.roundRect, { x: 8.6 + i * 0.245, y: 2.2 - h / 2, w: 0.15, h, rectRadius: 0.07, fill: { color: i % 5 === 3 ? "C6F24E" : "1A9F4C", transparency: i % 5 === 3 ? 0 : 35 }, line: { type: "none" } });
  });
  // 제목 자리: 흰 둥근 카드 위의 로고(로고의 글자가 검은색이라 짙은 초록 바탕에는 카드가 필요하다)
  s.addShape(pres.ShapeType.roundRect, { x: MX + 0.2, y: 0.9, w: 6.6, h: 2.55, rectRadius: 0.2, fill: { color: "FCFCFB" }, line: { type: "none" }, objectName: "logo-card" });
  s.addImage({ path: LOGO, x: MX + 0.5, y: 1.1, w: 6.0, h: 6.0 * 892 / 2400 + 0.0, altText: "song lingo 로고" });
  s.addText("듣고, 따라 읽고, 확인한다", { ...T, x: MX + 0.2, y: 3.7, w: 8, h: 0.7, fontSize: 32, bold: true, color: "C6F24E", valign: "middle" });
  s.addText("외국어 노래 속 문장을 듣고 → 따라 읽거나 받아 적고 → 어디가 다른지 확인하는 학습 도우미", { ...T, x: MX + 0.2, y: 4.45, w: 7.6, h: 0.9, fontSize: 18, color: "DFF3E4", valign: "top" });
  s.addShape(pres.ShapeType.roundRect, { x: MX + 0.2, y: 5.45, w: 8.6, h: 0.75, rectRadius: 0.15, fill: { color: "C6F24E" }, line: { type: "none" } });
  s.addText("소리가 데이터가 되고, 모델을 지나, 사용자에게 돌아오는 길을 직접 만들고 열어 본 프로젝트", { ...T, x: MX + 0.4, y: 5.45, w: 8.3, h: 0.75, fontSize: 16, bold: true, color: "112D18", valign: "middle" });
  s.addText("ICT 혁신 스퀘어 Voice-AI 부트캠프 개인 프로젝트  ·  2026-11-12", { ...T, x: MX + 0.2, y: 6.7, w: 9, h: 0.35, fontSize: 12, color: "8A8985" });
}

// ═════════ 2장 ═════════
section("2 왜 만들었나 — 나의 목표");
{
  const s = content("노래로 외국어를 배울 때 알기 어려운 것", "② 왜 만들었나", noteOf("2", 0, 2), "2 왜 만들었나 — 나의 목표");
  const qs = [["1", "이 노래는 무슨 언어이고, 무슨 뜻일까?"], ["2", "어떻게 쓰고, 어떻게 읽는 문장일까?"], ["3", "내가 맞게 말하고 있는 걸까?"]];
  qs.forEach(([n, t], i) => {
    const y = 2.1 + i * 1.5;
    card(s, MX, y, 6.6, 1.25, { fill: "DFF3E4" });
    badge(s, MX + 0.3, y + 0.36, n);
    s.addText(t, { ...T, x: MX + 1.1, y, w: 5.3, h: 1.25, fontSize: 18, bold: true, color: "112D18", valign: "middle" });
  });
  card(s, 7.6, 2.1, 5.13, 4.25, { fill: "112D18" });
  s.addText("이 앱은 노래방이 아니다", { ...T, x: 7.95, y: 2.4, w: 4.5, h: 0.6, fontSize: 24, bold: true, color: "C6F24E", valign: "middle" });
  bullets(s, ["내가 부른 노래를 채점하지 않는다", "노래는 가사를 얻고 듣기 위한 입력", "평가 대상은 내 따라 읽기와 받아쓰기"], { x: 7.95, y: 3.3, w: 4.5, h: 2.8, size: 20, color: "FFFFFF", gap: 18 });
}
{
  const s = content("내가 이 프로젝트로 얻고 싶은 것", "② 나의 목표", noteOf("2", 2, 3), "2 왜 만들었나 — 나의 목표");
  card(s, MX, 2.0, W - 2 * MX, 3.6, { fill: "DFF3E4" });
  s.addText("“", { ...T, x: MX + 0.35, y: 2.05, w: 1, h: 1, fontSize: 80, bold: true, color: "08833C" });
  s.addText([
    { text: "실제로 쓸 수 있는 외국어 학습 도구", options: { bold: true, color: "08833C" } },
    { text: "를 만들면서, 음성 데이터가 수집되고 처리되고 분석되어 사용자에게 전달되는 ", options: {} },
    { text: "전체 과정을 이해하고 직접 다룰 수 있는 개발자", options: { bold: true, color: "08833C" } },
    { text: "로 성장한다", options: {} },
  ], { ...T, x: MX + 1.2, y: 2.35, w: W - 2 * MX - 1.8, h: 2.9, fontSize: 28, color: "112D18", valign: "middle" });
  s.addText("근거: docs/personal_goals.md  ·  마지막에 이 기준으로 점검합니다", { ...T, x: MX, y: 6.0, w: 9, h: 0.35, fontSize: 12, color: "52514E" });
}
{
  const s = content("여섯 가지 목표", "② 나의 목표", "여섯 가지 목표는 12장에서 다시 점검합니다.", "2 왜 만들었나 — 나의 목표");
  const g = [
    ["01", "쓰는 도구", "내가 듣는 노래를 학습 자료로"], ["02", "음성·음향 처리", "STFT·Log-Mel·FFT를 앱에 적용"], ["03", "AI 실험 능력", "가설 → 통제 → 비교 → 결론"],
    ["04", "소프트웨어 설계", "모듈 분리·테스트·배포"], ["05", "기술 → 사용자 경험", "점수와 관찰을 나눠 보여 주기"], ["06", "과학적 호기심·창작", "소리를 탐구하고 표현하기"],
  ];
  g.forEach(([n, t, d], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = MX + col * 4.1, y = 2.0 + row * 2.4;
    card(s, x, y, 3.93, 2.15, { fill: i === 5 ? "EFE9FF" : "DFF3E4" });
    badge(s, x + 0.3, y + 0.3, n, { fill: i === 5 ? "6250D6" : "08833C", size: 15 });
    s.addText(t, { ...T, x: x + 1.0, y: y + 0.28, w: 2.8, h: 0.6, fontSize: 18, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.3, y: y + 1.1, w: 3.4, h: 0.8, fontSize: 15, color: "0B0B0B", valign: "top" });
  });
  tag(s, "(임시) 6번은 '시작 전'으로 말할지 결정", 7.5, 0.45, "temp");
}

// ═════════ 3장 ═════════
section("3 전체 그림");
{
  // 사용자의 손그림을 옮긴 그림: docs/slides/slide_3_overview.png (scripts/make_slide_figures.py의 fig_overview)
  const s = pres.addSlide({ masterName: "IMAGE", sectionTitle: "3 전체 그림" });
  s.addImage({ path: path.join(ROOT, "docs/slides/slide_3_overview.png"), x: 0, y: 0, w: W, h: H, altText: "프로그램 전체 구조: 텍스트·원곡 소리 → 언어 확인 → TTS·설명·STT·Demucs → 사용자 청취·확인 → 따라읽기·받아쓰기 → 평가 → 학습 기록" });
  s.addNotes(noteOf("3", 0, 7));
}
{
  const s = content("무엇이 어디서 돌고 있나", "③ 전체 그림", "", "3 전체 그림");
  const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: "112D18" }, fontSize: 14, valign: "middle" } });
  const cell = (t, o = {}) => ({ text: t, options: { fontSize: 14, color: "0B0B0B", valign: "middle", ...o } });
  const rows = [
    [hdr("단계"), hdr("기술"), hdr("어디서")],
    ["기준 음성", "OpenAI TTS (gpt-4o-mini-tts)", "OpenAI"], ["인식", "faster-whisper (문장 tiny · 노래 medium)", "내 서버 CPU"],
    ["채점", "WER/CER · 편집 거리 (직접 구현)", "내 서버"], ["소리 그림·틀린 구간", "STFT · Log-Mel · FFT, 단어별 시간", "내 서버"],
    ["목소리 높낮이", "pYIN (F0)", "내 서버"], ["보컬 분리 (선택)", "Demucs htdemucs", "내 서버"],
    ["발음 평가 (선택)", "Azure Speech", "Azure"], ["저장·배포", "PostgreSQL · Oracle Cloud VM · HTTPS · 로그인", "내 서버"],
  ].map((r, i) => (i === 0 ? r : r.map((t, j) => cell(t, { bold: j === 0, fill: { color: i % 2 ? "DFF3E4" : "FFFFFF" }, color: t === "OpenAI" || t === "Azure" ? "6250D6" : "0B0B0B" }))));
  s.addTable(rows, { x: MX, y: 1.95, w: W - 2 * MX, colW: [3.2, 6.4, 2.53], rowH: 0.5, border: { type: "solid", pt: 0.5, color: "E4E3DF" }, margin: [0.04, 0.12, 0.04, 0.12] });
  s.addText("구조 4층:  화면(Streamlit) → 흐름 → 처리 → 저장    ·    보라색 = 밖으로 나가는 서비스", { ...T, x: MX, y: 6.65, w: 11, h: 0.35, fontSize: 13, color: "52514E" });
}
{
  const s = content("밖으로 나가는 것, 저장되는 것, 저장하지 않는 것", "③ 전체 그림", noteOf("3", 7, 8), "3 전체 그림");
  const cols = [
    ["밖으로 나가는 것", "EFE9FF", "6250D6", ["OpenAI TTS: 문장 글 (버튼을 누를 때, 캐시)", "OpenAI 뜻·설명: 문장 글과 언어 (버튼)", "Azure: 녹음 · 기준 문장 · 언어 (버튼을 누를 때만)", "분석 계산은 모두 내 서버 안에서"]],
    ["서버 DB에 저장 (로그인 · 저장 켬)", "DFF3E4", "08833C", ["연습 점수, 문장, 인식한 글", "내 노래의 가사 · 구간 정보", "한글 뜻 · 표현 설명", "스위치로 끄거나 계정과 함께 삭제"]],
    ["저장하지 않는 것", "112D18", "C6F24E", ["내 녹음", "올린 음원 · 잘라 낸 구간 소리", "보컬 분리 결과", "F0 · 소리 모양 그림"]],
  ];
  cols.forEach(([t, fill, head, items], i) => {
    const x = MX + i * 4.1;
    card(s, x, 2.0, 3.93, 4.4, { fill });
    s.addText(t, { ...T, x: x + 0.3, y: 2.2, w: 3.35, h: 0.8, fontSize: 18, bold: true, color: head, valign: "middle" });
    bullets(s, items, { x: x + 0.3, y: 3.15, w: 3.4, h: 3.1, size: 16, color: i === 2 ? "FFFFFF" : "0B0B0B", gap: 12 });
  });
}

// ═════════ 4장 ═════════
section("4 시연");
{
  const s = content("시연 순서", "④ 시연 (실제 서버 화면)", noteOf("4", 0, 1), "4 시연");
  const steps = [["1", "로그인", "내 문장"], ["2", "문장 입력", "언어 알아보기"], ["3", "표준 발음", "만들기 · 듣기"], ["4", "따라 읽기", "채점하기"], ["5", "결과 읽기", "위에서 아래로"]];
  steps.forEach(([n, t, d], i) => {
    const x = MX + i * 2.45;
    card(s, x, 2.15, 2.25, 2.5, { fill: i === 4 ? "08833C" : "DFF3E4" });
    badge(s, x + 0.85, 2.4, n, { fill: i === 4 ? "C6F24E" : "08833C", color: i === 4 ? "112D18" : "FFFFFF", d: 0.56 });
    s.addText(t, { ...T, x, y: 3.15, w: 2.25, h: 0.55, fontSize: 18, bold: true, color: i === 4 ? "FFFFFF" : "112D18", align: "center", valign: "middle" });
    s.addText(d, { ...T, x, y: 3.7, w: 2.25, h: 0.6, fontSize: 14, color: i === 4 ? "DFF3E4" : "0B0B0B", align: "center", valign: "top" });
  });
  card(s, MX, 5.0, W - 2 * MX, 1.35, { fill: "FFFFFF", line: "E4E3DF" });
  s.addText([{ text: "시연 문장: ", options: { bold: true, color: "08833C" } }, { text: "We'll sing together until the morning comes.  (직접 쓴 문장)", options: {} }],
    { ...T, x: MX + 0.35, y: 5.1, w: 9.2, h: 0.6, fontSize: 18, color: "112D18", valign: "middle" });
  s.addText("라이브 시연  ·  막히면 미리 찍은 캡처로 대체  ·  상업 노래 가사는 화면에 올리지 않음", { ...T, x: MX + 0.35, y: 5.7, w: 10.5, h: 0.5, fontSize: 14, color: "52514E", valign: "middle" });
  tag(s, "(임시) 시연 문장 확정 필요", 9.85, 5.32, "temp");
}
{
  const s = content("채점 버튼을 누르면 안에서 일어나는 일", "④ 시연 (실제 서버 화면)", noteOf("4", 1, 2), "4 시연");
  const st = [
    ["1", "녹음", "브라우저 마이크로 받은 소리가 bytes로 들어온다", "audio.load_raw"],
    ["2", "상태 점검", "음량 · 무음 · 클리핑. 안내만 하고 경고가 있어도 계속 진행", "quality.analyze"],
    ["3", "Whisper 인식", "소리를 글로 바꾼다 (문장 연습은 tiny)", "stt.recognize"],
    ["4", "채점", "정답과 편집 거리로 비교 → WER/CER, 바뀜·빠짐·더해짐", "scoring.evaluate"],
    ["5", "단어별 시간", "내 녹음과 표준 발음을 각각 다시 인식. 틀린 구간과 F0가 한 번만 구해 함께 씀", "practice.locate_errors"],
    ["6", "F0 + 그림", "pYIN → 상대 음높이 → 단어 칸에 겹침, 소리 모양 그림도 함께", "pitch · visualisation"],
  ];
  st.forEach(([n, t, d, m], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = MX + col * 4.1, y = 1.95 + row * 2.05;
    card(s, x, y, 3.93, 1.85, { fill: i === 4 ? "C6F24E" : "DFF3E4" });   // 5번(공유해서 한 번만 구하는 단계)만 라임으로 강조
    badge(s, x + 0.25, y + 0.2, n, { d: 0.5, size: 16, fill: i === 4 ? "112D18" : "08833C", color: i === 4 ? "C6F24E" : "FFFFFF" });
    s.addText(t, { ...T, x: x + 0.95, y: y + 0.2, w: 2.8, h: 0.5, fontSize: 18, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.3, y: y + 0.8, w: 3.4, h: 0.7, fontSize: 14, color: "0B0B0B", valign: "top" });
    s.addText(m, { ...T, x: x + 0.3, y: y + 1.5, w: 3.4, h: 0.28, fontSize: 12, color: "52514E", valign: "middle" });
  });
  card(s, MX, 6.15, W - 2 * MX, 0.7, { fill: "C6F24E", shadow: false });
  s.addText("인식을 세 번(채점용 1 + 단어 시간용 2) 돌리고 F0를 계산해서 몇 초 걸린다  ·  로컬 약 8~10초 (서버는 측정 중)", { ...T, x: MX + 0.3, y: 6.15, w: W - 2 * MX - 0.6, h: 0.7, fontSize: 15, bold: true, color: "112D18", valign: "middle" });
}
{
  const s = content("결과를 읽는 순서", "④ 시연 (실제 서버 화면)", noteOf("4", 2, 4), "4 시연");
  const items = [
    ["1", "문장 인식 일치도 · Whisper", "WER/CER, 바뀜·빠짐·더해짐"], ["2", "단어 대조", "보라 물결 밑줄 = 다른 단어"], ["3", "다시 듣기", "표준 발음과 내 녹음"], ["4", "틀린 구간 표시", "같은 번호 [k] = 대응 구간"],
    ["5", "목소리 높낮이 · F0", "참고 TTS와 겹친 상대 음높이"], ["6", "Azure 발음 평가", "선택 · 버튼을 누를 때만"], ["7", "소리 모양 자세히 보기", "파형·FFT·STFT·Log-Mel (접힘)"],
  ];
  items.forEach(([n, t, d], i) => {
    const col = i < 4 ? 0 : 1, row = i < 4 ? i : i - 4;
    const x = MX + col * 6.2, y = 1.95 + row * 1.12;
    card(s, x, y, 5.93, 0.98, { fill: "DFF3E4" });
    badge(s, x + 0.22, y + 0.23, n, { d: 0.52, fill: n === "4" ? "6250D6" : "08833C" });
    s.addText(t, { ...T, x: x + 0.95, y: y + 0.08, w: 4.85, h: 0.45, fontSize: 17, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.95, y: y + 0.5, w: 4.85, h: 0.4, fontSize: 14, color: "52514E", valign: "top" });
  });
  card(s, MX + 6.2, 5.55, 5.93, 1.05, { fill: "C6F24E", shadow: false });
  s.addText("점수가 아니라 관찰·참고\n오류율은 발음 점수가 아니다", { ...T, x: MX + 6.4, y: 5.55, w: 5.55, h: 1.05, fontSize: 17, bold: true, color: "112D18", valign: "middle" });
}

// ═════════ 5장 ═════════
section("5 따라읽기 음성 분석 방법");
{
  const s = content("따라읽기 음성 분석 네 가지와 각각의 한계", "⑤ 따라읽기 음성 분석", noteOf("5"), "5 따라읽기 음성 분석 방법");
  const cols = [
    ["오류율 WER / CER", "Whisper", "인식된 문장이 기준 문장과\n얼마나 다른가?", "오류율 (낮을수록 좋음)\n발음 점수가 아님", "문맥으로 틀린 발음도 맞게 적을 수 있고, 쉼·속도·억양은 못 잡는다", "DFF3E4", "08833C"],
    ["파형 분석", "틀린 구간 표시 · 스펙트로그램", "어느 단어 구간이 다르게 인식됐고\n소리 모양은 어떻게 다른가?", "점수 없음\n눈으로 보는 관찰", "단어 구간은 모델이 추정한 대략의 구간 · 그림만으로 발음을 판정하지 않음", "EFE9FF", "6250D6"],
    ["F0 목소리 높낮이", "pYIN", "음높이가 시간에 따라\n어떻게 변하나?", "점수 없음\n관찰용", "TTS 억양이 정답이 아님 · 무성음·쉼에는 값이 없고 상대 음높이만 비교", "EFE9FF", "6250D6"],
    ["Azure 발음 평가", "외부 서비스 · 선택", "기준 문장에 비추어\n발음·유창성·운율은?", "서비스가 주는 점수\n버튼을 눌렀을 때만", "한 사람·한 문장·1회 시험 · 운율·음소는 영어 중심 (7장)", "DFF3E4", "08833C"],
  ];
  cols.forEach(([t, sub, q, a, lim, fill, c], i) => {
    const x = MX + i * 3.08, w = 2.93;
    card(s, x, 2.0, w, 4.05, { fill });
    s.addText(t, { ...T, x: x + 0.2, y: 2.1, w: w - 0.4, h: 0.5, fontSize: 17, bold: true, color: c, valign: "middle" });
    s.addText(sub, { ...T, x: x + 0.2, y: 2.6, w: w - 0.4, h: 0.35, fontSize: 12, color: "52514E", valign: "middle" });
    s.addText(q, { ...T, x: x + 0.2, y: 3.05, w: w - 0.4, h: 0.85, fontSize: 14, bold: true, color: "112D18", valign: "top" });
    s.addText(a, { ...T, x: x + 0.2, y: 3.95, w: w - 0.4, h: 0.65, fontSize: 13, color: "0B0B0B", valign: "top" });
    s.addText([{ text: "한계  ", options: { bold: true, color: "6250D6" } }, { text: lim, options: { color: "0B0B0B" } }], { ...T, x: x + 0.2, y: 4.7, w: w - 0.4, h: 1.25, fontSize: 12, valign: "top" });
  });
  s.addShape(pres.ShapeType.roundRect, { x: MX, y: 6.2, w: W - 2 * MX, h: 0.65, rectRadius: 0.12, fill: { color: "112D18" }, line: { type: "none" } });
  s.addText("발음 점수를 하나 더 만든 것이 아니라, 하나의 소리를 서로 다른 층위로 분석하고 각각의 한계를 밝힌 것", { ...T, x: MX + 0.3, y: 6.2, w: W - 2 * MX - 0.6, h: 0.65, fontSize: 16, bold: true, color: "C6F24E", align: "center", valign: "middle" });
}

// ═════════ 6장 ═════════
section("6 채점의 핵심 — 편집 거리");
{
  const s = content("채점의 핵심: 편집 거리를 표로 한 칸씩 채운다", "⑥ 채점의 핵심", noteOf("6"), "6 채점의 핵심 — 편집 거리");
  const hd = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: "112D18" }, fontSize: 14, align: "center", valign: "middle" } });
  // scoring.edit_matrix의 값 그대로: 정답 `we sing together until` × 인식 `we seeing together`
  const d = [[0, 1, 2, 3], [1, 0, 1, 2], [2, 1, 1, 2], [3, 2, 2, 1], [4, 3, 3, 2]];
  const ref = ["∅", "we", "sing", "together", "until"];
  const onPath = new Set(["0,0", "1,1", "2,2", "3,3", "4,3"]);   // 오른쪽 아래에서 거꾸로 되짚은 길
  const rows = [[hd("정답 \\ 인식"), hd("∅"), hd("we"), hd("seeing"), hd("together")]];
  d.forEach((r, i) => rows.push([hd(ref[i]), ...r.map((v, j) => {
    const on = onPath.has(`${i},${j}`);
    return { text: String(v), options: { fontSize: 16, align: "center", valign: "middle", bold: on, color: on ? "112D18" : "52514E", fill: { color: on ? "C6F24E" : "FFFFFF" } } };
  })]));
  s.addTable(rows, { x: MX, y: 1.95, w: 6.1, colW: [1.7, 1.0, 1.0, 1.2, 1.2], rowH: 0.55, border: { type: "solid", pt: 0.5, color: "E4E3DF" } });
  s.addText([
    { text: "되짚은 길 (연두 칸)", options: { bold: true, color: "112D18", breakLine: true } },
    { text: "we = we  일치  →  sing → seeing  바뀜(S)  →  together = together  일치  →  until → ∅  빠짐(D)", options: { color: "0B0B0B" } },
  ], { ...T, x: MX, y: 5.45, w: 6.1, h: 1.0, fontSize: 13, valign: "top" });
  card(s, 6.95, 1.95, 5.78, 1.85, { fill: "DFF3E4" });
  s.addText("한 칸을 채우는 규칙 (점화식)", { ...T, x: 7.2, y: 2.0, w: 5.3, h: 0.4, fontSize: 15, bold: true, color: "08833C", valign: "middle" });
  bullets(s, ["d[i][j] = 아래 세 값 중 가장 작은 것", "위 칸 + 1 : 삭제 (정답 단어를 지움)", "왼쪽 칸 + 1 : 삽입 (인식에만 있는 단어)", "대각선 칸 + (같으면 0, 다르면 1) : 일치·바뀜"], { x: 7.2, y: 2.45, w: 5.3, h: 1.3, size: 13, gap: 3 });
  card(s, 6.95, 3.95, 5.78, 0.95, { fill: "C6F24E", shadow: false });
  s.addText("오른쪽 아래 칸 = 최소 수정 횟수 = 2  →  WER = (S + D + I) ÷ N = (1 + 1 + 0) ÷ 4 = 0.50", { ...T, x: 7.15, y: 3.95, w: 5.4, h: 0.95, fontSize: 15, bold: true, color: "112D18", valign: "middle" });
  card(s, 6.95, 5.05, 5.78, 1.45, { fill: "112D18", shadow: false });
  s.addText("cost = 0 if ref[i-1] == hyp[j-1] else 1\nd[i][j] = min(d[i-1][j] + 1,       # 삭제\n              d[i][j-1] + 1,       # 삽입\n              d[i-1][j-1] + cost)  # 일치·바뀜", { ...T, x: 7.15, y: 5.1, w: 5.4, h: 1.35, fontSize: 12, fontFace: "Courier New", color: "DFF3E4", valign: "middle" });
  s.addText("scoring.edit_matrix (내 코드)  ·  이해한 방법: 점화식 → 표를 한 칸씩 넘기는 도구  ·  동률일 때 비슷한 단어끼리 짝짓는 규칙은 이 프로젝트에서 덧붙임", { ...T, x: MX, y: 6.65, w: 12.1, h: 0.3, fontSize: 11, color: "52514E" });
}

// ═════════ 7장 ═════════
section("7 Azure 발음 평가");
{
  const s = content("Azure API를 활용한 발음 평가 및 피드백 구현", "⑦ Azure 발음 평가", noteOf("7", 0, 2), "7 Azure 발음 평가");
  const cols = [
    ["① 도입 배경", ["처음 기획한 오류율(WER/CER)은 인식된 글의 일치도", "문맥으로 고쳐 적혀 오류율 0인데 Azure는 explore를 68점으로 봄 (내 녹음 1건)", "끊어 읽어도 오류율은 낮음 → 어디를 어떻게 고칠지 알려 주는 피드백이 필요 (동기, 추정)"]],
    ["② 서비스 개요", ["Azure AI Speech 발음 평가", "정확도 · 유창성 · 완성도 · 운율 · 종합", "단어별 점수와 오류 종류 (발음 · 빠짐 · 더해짐)", "기준은 TTS가 아니라 Azure의 원어민 발음 모델"]],
    ["③ 사용 방법", ["'Azure로 평가하기' 버튼을 누를 때만 전송", "녹음 · 기준 문장 글 · 언어만 보냄 (TTS 소리는 보내지 않음)", "녹음은 서버에 저장하지 않음", "로그인·저장 켬: 점수와 단어별 결과를 기록 (녹음 제외)"]],
  ];
  cols.forEach(([t, items], i) => {
    const x = MX + i * 4.1;
    card(s, x, 2.0, 3.93, 4.15, { fill: i === 1 ? "112D18" : "DFF3E4" });
    s.addText(t, { ...T, x: x + 0.3, y: 2.12, w: 3.35, h: 0.55, fontSize: 19, bold: true, color: i === 1 ? "C6F24E" : "08833C", valign: "middle" });
    bullets(s, items, { x: x + 0.3, y: 2.8, w: 3.4, h: 3.2, size: 14, color: i === 1 ? "FFFFFF" : "0B0B0B", gap: 10 });
  });
  s.addText("강사님 11-05 피드백: \"발음 자체를 평가하고 부족한 부분을 피드백하는 방향이 맞다\"  ·  발표 제목: Azure API를 활용한 발음 평가 및 피드백 구현", { ...T, x: MX, y: 6.4, w: 12.1, h: 0.4, fontSize: 12, color: "52514E" });
}
{
  const s = content("같은 문장을 네 가지로 읽어 보니", "⑦ Azure 발음 평가", noteOf("7", 2, 3), "7 Azure 발음 평가");
  const hd = (t, c = "112D18") => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: c }, fontSize: 13, align: "center", valign: "middle" } });
  const cl = (t, o = {}) => ({ text: t, options: { fontSize: 13, color: "0B0B0B", valign: "middle", align: "center", ...o } });
  const rows = [
    [hd("읽기 조건"), hd("정확도"), hd("유창성"), hd("완성도"), hd("운율"), hd("종합", "08833C"), hd("Azure가 표시한 단어"), hd("오류율 WER", "6250D6")],
    [cl("① 정상", { bold: true, align: "left" }), cl("81"), cl("90"), cl("71"), cl("81"), cl("79", { bold: true }), cl("we'll 51 · together 43 (발음)", { align: "left", fontSize: 12 }), cl("(캡처 없음)")],
    [cl("② 단어 생략", { bold: true, align: "left" }), cl("32"), cl("77"), cl("14", { bold: true }), cl("69"), cl("41", { bold: true }), cl("together · the · comes 빠짐", { align: "left", fontSize: 12 }), cl("0.750")],
    [cl("③ 끊어 읽기", { bold: true, align: "left" }), cl("45"), cl("49", { bold: true, fill: { color: "EFE9FF" } }), cl("14"), cl("66"), cl("38", { bold: true }), cl("We'll 빠짐 · the 더해짐", { align: "left", fontSize: 12 }), cl("0.250", { bold: true, fill: { color: "EFE9FF" } })],
    [cl("④ 틀린 발음", { bold: true, align: "left" }), cl("56"), cl("88"), cl("43"), cl("74"), cl("61", { bold: true }), cl("We'll 빠짐 · sing 47 · together 44 · the 55", { align: "left", fontSize: 12 }), cl("0.375")],
  ];
  s.addTable(rows, { x: MX, y: 1.95, w: W - 2 * MX, colW: [1.7, 0.95, 0.95, 0.95, 0.85, 0.95, 4.5, 1.28], rowH: [0.5, 0.52, 0.52, 0.52, 0.52], border: { type: "solid", pt: 0.5, color: "E4E3DF" }, margin: [0.03, 0.1, 0.03, 0.1] });
  card(s, MX, 4.75, 7.3, 1.95, { fill: "DFF3E4" });
  bullets(s, ["정상보다 세 경우 모두 종합이 내려감 (79 → 41 · 38 · 61): 차이가 평가에 반영된다", "끊어 읽기: 유창성 90 → 49로 가장 크게 하락, 그런데 오류율은 0.250으로 낮다 → 쉼·속도는 오류율이 못 잡고 Azure가 잡는다 (해석)", "단어 생략: 빠짐 표시와 완성도 71 → 14"], { x: MX + 0.25, y: 4.85, w: 6.8, h: 1.8, size: 13, gap: 4 });
  card(s, 8.1, 4.75, 4.63, 1.95, { fill: "EFE9FF", shadow: false });
  s.addText([{ text: "한계  ", options: { bold: true, color: "6250D6" } }, { text: "한 사람 · 한 문장 · 1회씩. 정상 읽기도 두 단어가 이미 낮아 완벽한 기준선이 아님. 운율·음소는 영어 중심, 일본어·프랑스어는 기본 점수까지만 확인. 완성도의 계산식은 미확인", options: { color: "0B0B0B" } }], { ...T, x: 8.3, y: 4.8, w: 4.25, h: 1.85, fontSize: 12.5, valign: "middle" });
  s.addText("문장: We'll sing together until the morning comes. (직접 쓴 문장, 사용자 화면 캡처 4장의 값)", { ...T, x: MX, y: 6.8, w: 12, h: 0.28, fontSize: 11, color: "52514E" });
}

// ═════════ 8장 ═════════
section("8 모델 속 1 — Whisper");
{
  const s = pres.addSlide({ masterName: "IMAGE", sectionTitle: "8 모델 속 1 — Whisper" });
  s.addImage({ path: path.join(ROOT, "docs/slides/slide_6_whisper.png"), x: 0, y: 0, w: W, h: H, altText: "Whisper 구조: Log-Mel(80×3000) → 합성곱 2개 → Transformer 인코더 → 디코더(토큰 하나씩) → 글" });
  s.addNotes(noteOf("8", 0, 3));
}
{
  const s = content("Whisper에서 확인한 숫자", "⑧ 모델 속 1 — Whisper", "모델 파일 model.bin을 직접 읽어 센 값입니다. 입력 크기는 짧아도 줄지 않지만, 전체 처리 시간은 디코더가 만드는 토큰 수에도 영향을 받습니다.", "8 모델 속 1 — Whisper");
  const st = [["4 → 24", "층 수 (tiny → medium)", "차원 384 → 1024", "DFF3E4", "08833C"], ["0", "LSTM · GRU 변수", "Transformer만 + 입력 앞 합성곱 2개", "DFF3E4", "08833C"], ["80 × 3000", "Log-Mel 입력, 항상", "30초 창 · 모자라면 0으로 채움", "DFF3E4", "08833C"], ["절반+", "tiny 파라미터 중 '단어 사전'", "토큰 51,865개 × 384", "DFF3E4", "08833C"]];
  st.forEach(([n, l, d, fill, c], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * 6.2, y = 2.0 + row * 2.2;
    card(s, x, y, 5.93, 1.95, { fill });
    s.addText(n, { ...T, x: x + 0.35, y: y + 0.15, w: 5.2, h: 0.95, fontSize: 46, bold: true, color: c, valign: "middle" });
    s.addText(l, { ...T, x: x + 0.35, y: y + 1.1, w: 5.2, h: 0.4, fontSize: 17, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.35, y: y + 1.5, w: 5.2, h: 0.35, fontSize: 14, color: "52514E", valign: "middle" });
  });
  s.addText("model.bin을 직접 읽어 센 값 [확인]   ·   못 본 것: 가중치 값, 어텐션 패턴", { ...T, x: MX, y: 6.5, w: 11, h: 0.35, fontSize: 14, color: "6250D6" });
}
{
  const s = content("내가 겪은 현상: 확인한 것과 해석", "⑧ 모델 속 1 — Whisper", noteOf("8", 3, 4), "8 모델 속 1 — Whisper");
  const h = (t, c) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: c }, fontSize: 15, valign: "middle" } });
  const c = (t, o = {}) => ({ text: t, options: { fontSize: 14, color: "0B0B0B", valign: "middle", ...o } });
  const rows = [
    [h("현상", "112D18"), h("확인한 것", "08833C"), h("해석 (추정)", "6250D6")],
    [c("무음에서 글이 생김", { bold: true }), c("무음 입력에서도 토큰이 생성됨. 규칙이 no_speech_prob · avg_logprob로 걸러 냄"), c("소리 정보가 부족하면 언어 패턴에 기대 그럴듯한 말을 쓸 수 있음. 원인을 증명한 것은 아님", { fill: { color: "EFE9FF" } })],
    [c("같은 말 반복", { bold: true }), c("temperature=0.0 (폴백 끔) 설정의 노래 구간에서 반복이 관찰됨"), c("폴백이 반복을 끊어 주는 장치와 맞지만 단일 원인으로 단정하지 않음", { fill: { color: "EFE9FF" } })],
    [c("노래에서 가사가 지워짐", { bold: true }), c("원곡에 VAD를 켜면 가사가 통째로 사라짐 (6곡)"), c("반주가 섞인 소리를 말소리로 잘 못 잡은 것으로 보임", { fill: { color: "EFE9FF" } })],
  ];
  s.addTable(rows, { x: MX, y: 2.0, w: W - 2 * MX, colW: [2.6, 4.9, 4.63], rowH: [0.55, 1.2, 1.1, 1.1], border: { type: "solid", pt: 0.5, color: "E4E3DF" }, margin: [0.06, 0.14, 0.06, 0.14] });
  card(s, MX, 6.15, W - 2 * MX, 0.7, { fill: "C6F24E", shadow: false });
  s.addText("그래서 노래에는 medium + 원곡 + VAD 끔 + 기본 설정으로 정리", { ...T, x: MX + 0.3, y: 6.15, w: W - 2 * MX - 0.6, h: 0.7, fontSize: 16, bold: true, color: "112D18", valign: "middle" });
}

// ═════════ 9장 ═════════
section("9 모델 속 2 — Demucs");

{
  const s = content("Demucs는 무엇인가", "⑨ 모델 속 2 — Demucs", noteOf("9", 0, 1), "9 모델 속 2 — Demucs");
  bullets(s, ["Meta AI가 공개한 오픈소스 음원 분리 모델", "곡 하나를 넣으면 소리 4개로 나눠 준다", "한 번에 7.8초 조각씩 처리한다", "우리 앱에서는 선택 기능: 보컬만 듣기 · 분리한 보컬이 가사 인식에 도움이 되는지 비교"], { x: MX, y: 1.95, w: 7.3, h: 2.6, size: 18, gap: 10 });
  [["drums", "드럼·타악기", "DFF3E4"], ["bass", "베이스", "DFF3E4"], ["other", "나머지 반주 전체 (기타가 아님)", "DFF3E4"], ["vocals", "목소리 — 우리 앱이 쓰는 것", "C6F24E"]].forEach(([n, d, f], i) => {
    const y = 1.95 + i * 0.68;
    card(s, MX + 7.9, y, 4.23, 0.56, { fill: f, shadow: false });
    s.addText([{ text: n + "  ", options: { bold: true, color: "112D18" } }, { text: d, options: { color: "0B0B0B" } }], { ...T, x: MX + 8.1, y, w: 3.9, h: 0.56, fontSize: 14, valign: "middle" });
  });
  const lin = [["v1 · v2", "파형을 직접 다루는 U-Net + BiLSTM", "DFF3E4", "112D18"], ["Hybrid", "파형 + 스펙트로그램 두 갈래", "DFF3E4", "112D18"], ["HT Demucs", "가운데에 Transformer — 우리 모델", "C6F24E", "112D18"]];
  lin.forEach(([t, d, f, c], i) => {
    const w = (W - 2 * MX - 0.6) / 3, x = MX + i * (w + 0.3);
    card(s, x, 4.85, w, 1.6, { fill: f, shadow: false });
    s.addText(t, { ...T, x: x + 0.25, y: 4.95, w: w - 0.5, h: 0.5, fontSize: 18, bold: true, color: c, valign: "middle" });
    s.addText(d, { ...T, x: x + 0.25, y: 5.5, w: w - 0.5, h: 0.85, fontSize: 15, color: "0B0B0B", valign: "top" });
  });
}

{
  const s = pres.addSlide({ masterName: "IMAGE", sectionTitle: "9 모델 속 2 — Demucs" });
  s.addImage({ path: path.join(ROOT, "docs/slides/slide_7_demucs.png"), x: 0, y: 0, w: W, h: H, altText: "HTDemucs 구조: 파형·스펙트로그램 두 경로의 CNN 4층 → Transformer 5층 → 디코더 4층 → 소리 4개" });
  s.addNotes(noteOf("9", 1, 3));
}

{
  const s = content("이 모델에서 말할 네 가지", "⑨ 모델 속 2 — Demucs", noteOf("9", 3, 4), "9 모델 속 2 — Demucs");
  const st = [["1", "두 표현", "같은 소리를 파형과 스펙트로그램, 두 가지 모양으로 본다"], ["2", "CNN 압축", "각 경로의 CNN이 시간·주파수를 줄이고 채널을 늘려 특징 벡터를 만든다"], ["3", "Transformer 결합", "경로 안(self)과 경로 사이(cross)의 정보를 결합한다"], ["4", "디코더 복원", "인코더 출력을 더해 가며 원래 크기의 소리 4개로 복원한다"]];
  st.forEach(([n, t, d], i) => {
    const x = MX + i * 3.05;
    card(s, x, 2.0, 2.88, 3.0, { fill: i === 2 ? "EFE9FF" : "DFF3E4" });
    badge(s, x + 0.25, 2.25, n, { fill: i === 2 ? "6250D6" : "08833C" });
    s.addText(t, { ...T, x: x + 0.25, y: 2.95, w: 2.4, h: 0.5, fontSize: 18, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.25, y: 3.5, w: 2.4, h: 1.4, fontSize: 15, color: "0B0B0B", valign: "top" });
  });
  card(s, MX, 5.4, W - 2 * MX, 1.0, { fill: "112D18", shadow: false });
  s.addText([{ text: "(2, 343,980)", options: { color: "C6F24E", bold: true } }, { text: "  섞인 소리 →  두 경로 → CNN → Transformer → 디코더  → ", options: { color: "FFFFFF" } }, { text: "(4, 2, 343,980)", options: { color: "C6F24E", bold: true } }, { text: "  소리 4개", options: { color: "FFFFFF" } }],
    { ...T, x: MX + 0.3, y: 5.4, w: W - 2 * MX - 0.6, h: 1.0, fontSize: 19, align: "center", valign: "middle" });
}

{
  const s = content("LSTM·Attention은 자연어 전용이 아니다", "⑨ 모델 속 2 — Demucs", noteOf("9", 4, 5), "9 모델 속 2 — Demucs");
  const bx = (x, y, w, h, t, o = {}) => {
    s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.12, fill: { color: o.fill || "DFF3E4" }, line: o.line ? { color: o.line, width: 1.5 } : { type: "none" } });
    s.addText(t, { ...T, x, y, w, h, fontSize: o.size || 15, bold: true, color: o.color || "112D18", align: "center", valign: "middle" });
  };
  const ar = (x1, y1, x2, y2) => s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipV: y2 < y1, line: { color: "52514E", width: 2, endArrowType: "triangle" } });
  s.addText("같은 nn.LSTM 층에 두 가지를 넣어 봄  [확인: 노트북 2-2절]", { ...T, x: MX, y: 1.95, w: 9, h: 0.4, fontSize: 16, bold: true, color: "08833C" });
  bx(MX, 2.6, 3.6, 0.95, "단어 임베딩 5개\n(1, 5, 16)", { fill: "FFFFFF", line: "8A8985" });
  bx(MX, 3.85, 3.6, 0.95, "음향 특징 5프레임\n(1, 5, 16)", { fill: "FFFFFF", line: "8A8985" });
  ar(MX + 3.6, 3.07, MX + 4.4, 3.5); ar(MX + 3.6, 4.32, MX + 4.4, 3.9);
  bx(MX + 4.4, 3.1, 3.2, 1.2, "같은 LSTM 층", { fill: "08833C", color: "FFFFFF", size: 18 });
  ar(MX + 7.6, 3.7, MX + 8.4, 3.7);
  bx(MX + 8.4, 3.2, 3.73, 1.0, "(1, 5, 8)\n똑같이 계산됨", { fill: "C6F24E", size: 16 });
  card(s, MX, 5.15, 6.0, 1.7, { fill: "DFF3E4", shadow: false });
  s.addText("소리에서는 CNN이 '벡터의 열'을 만든다", { ...T, x: MX + 0.3, y: 5.2, w: 5.5, h: 0.5, fontSize: 16, bold: true, color: "112D18", valign: "middle" });
  s.addText("(1, 384, 1344) → 토큰 1,344개 × 384차원", { ...T, x: MX + 0.3, y: 5.75, w: 5.5, h: 0.45, fontSize: 15, color: "0B0B0B", valign: "middle" });
  s.addText("층은 입력이 단어인지 소리인지 모른다", { ...T, x: MX + 0.3, y: 6.25, w: 5.5, h: 0.45, fontSize: 14, color: "52514E", valign: "middle" });
  card(s, MX + 6.2, 5.15, 5.93, 1.7, { fill: "112D18", shadow: false });
  s.addText("수업 6강의 음성 모델도 소리 프레임(Log-Mel 40개)을 LSTM이 읽었다", { ...T, x: MX + 6.5, y: 5.15, w: 5.35, h: 1.7, fontSize: 17, bold: true, color: "C6F24E", valign: "middle" });
}

{
  const s = content("숫자와 한계", "⑨ 모델 속 2 — Demucs", noteOf("9", 5, 6), "9 모델 속 2 — Demucs");
  const st = [
    ["4,198만 개", "파라미터 중 75%가 Transformer", "학습되는 숫자의 '개수 비중'이며 연산량·성능 기여도가 아님", "DFF3E4", "08833C"],
    ["21.6 dB", "Demucs SDR  (고정 필터는 3~4 dB)", "정답을 아는 쉬운 합성 입력 한정, 실제 노래 성능이 아님", "EFE9FF", "6250D6"],
    ["7.8초 조각", "한 번에 보는 길이", "어텐션 점수 표가 토큰 수의 제곱(약 720만 칸)이라 긴 소리는 나눠 넣음", "DFF3E4", "08833C"],
    ["직접 학습 아님", "추론 + 학습 코드 읽기 + 장난감 학습", "사전학습 HTDemucs의 추론과 구조 분석, 장난감 모델은 Demucs가 아님", "EFE9FF", "6250D6"],
  ];
  st.forEach(([n, l, d, fill, c], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * 6.2, y = 1.95 + row * 2.1;
    card(s, x, y, 5.93, 1.9, { fill });
    s.addText(n, { ...T, x: x + 0.35, y: y + 0.12, w: 5.2, h: 0.75, fontSize: 36, bold: true, color: c, valign: "middle" });
    s.addText(l, { ...T, x: x + 0.35, y: y + 0.88, w: 5.2, h: 0.4, fontSize: 16, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.35, y: y + 1.25, w: 5.2, h: 0.62, fontSize: 14, color: "0B0B0B", valign: "top" });
  });
  card(s, MX, 6.25, W - 2 * MX, 0.62, { fill: "C6F24E", shadow: false });
  s.addText("우리 앱에서는 분리가 항상 STT를 좋게 하지 않았다 (8구간 tiny: 보컬 0.606 대 원곡 0.506)  →  선택 기능", { ...T, x: MX + 0.3, y: 6.25, w: W - 2 * MX - 0.6, h: 0.62, fontSize: 15, bold: true, color: "112D18", valign: "middle" });
}

// ═════════ 10장 ═════════
section("10 두 모델을 나란히");
{
  const s = pres.addSlide({ masterName: "IMAGE", sectionTitle: "10 두 모델을 나란히" });
  s.addImage({ path: path.join(ROOT, "docs/slides/slide_7-2_compare.png"), x: 0, y: 0, w: W, h: H, altText: "두 모델 나란히: Whisper는 소리→글, HTDemucs는 섞인 소리→소리 4개. 공통점은 CNN과 Transformer" });
  s.addNotes(noteOf("10"));
}

// ═════════ 11장 ═════════
section("11 시행착오와 한계");
{
  const s = content("시행착오", "⑪ 시행착오와 한계", noteOf("11", 0, 1), "11 시행착오와 한계");
  const it = [
    ["VAD를 켜자 원곡 가사가 통째로 사라짐", "8구간 중 5구간이 비었음 (설정 B)"], ["폴백을 끄고(temperature=0.0) 돌리자 반복 루프", "폴백 켬(기본 설정)에서는 거의 사라짐"], ["분리하면 좋아질 거라는 가설", "구간마다 갈림 → 선택 기능"],
    ["av 최신판이 faster-whisper와 호환되지 않음", "버전 고정 · 앱 전용 환경 분리"], ["새 numba 휠이 이 Mac(Intel)에 없음", "휠이 있는 버전으로 고정"], ["시간 측정을 한 번만 보고 오해할 뻔함", "번갈아 8번 재서 '흔들림' 확인"],
  ];
  it.forEach(([t, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * 6.2, y = 2.0 + row * 1.6;
    card(s, x, y, 5.93, 1.4, { fill: "DFF3E4" });
    badge(s, x + 0.25, y + 0.44, i + 1, { d: 0.5, size: 16 });
    s.addText(t, { ...T, x: x + 0.95, y: y + 0.15, w: 4.85, h: 0.65, fontSize: 16, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.95, y: y + 0.82, w: 4.85, h: 0.4, fontSize: 14, color: "52514E", valign: "middle" });
  });
}
{
  const s = content("한계", "⑪ 시행착오와 한계", noteOf("11", 1, 2), "11 시행착오와 한계");
  const it = [
    ["내 목소리 한 명, 조용한 방", "다른 화자·잡음은 확인하지 못함"], ["모델 탐구는 모양·설정까지", "가중치 값과 어텐션 패턴은 못 봄 · Demucs는 추론·코드 읽기·장난감 학습"],
    ["오류율 ≠ 발음 점수", "F0는 관찰용이고 TTS의 억양이 정답이 아님"], ["서버 채점 시간은 측정 중", "로컬은 한 번에 약 8~10초"], ["언어별 억양 평가는 하지 않음", "중국어 성조 · 일본어 악센트"],
    ["언어별 지원 수준은 다름", "선택 11개(en 영어 · ja 일본어 · fr 프랑스어 · es 스페인어 · zh 중국어 …) · Azure 운율·음소는 영어 중심 · 영어 외 end-to-end 시험은 일부 [미확인]"],
  ];
  it.forEach(([t, d], i) => {
    const y = 1.95 + i * 0.8;
    card(s, MX, y, W - 2 * MX, 0.7, { fill: "EFE9FF", shadow: false });
    s.addShape(pres.ShapeType.ellipse, { x: MX + 0.25, y: y + 0.14, w: 0.42, h: 0.42, fill: { color: "6250D6" }, line: { type: "none" } });
    s.addText("!", { ...T, x: MX + 0.25, y: y + 0.14, w: 0.42, h: 0.42, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    s.addText(t, { ...T, x: MX + 0.95, y, w: 4.6, h: 0.7, fontSize: 16, bold: true, color: "112D18", valign: "middle" });
    s.addText(d, { ...T, x: MX + 5.6, y, w: 6.4, h: 0.7, fontSize: 14, color: "0B0B0B", valign: "middle" });
  });
}

{
  const s = content("노래 구간 인식 실험: 가설이 두 번 바뀌었다", "⑪ 시행착오와 한계", noteOf("11", 2, 3), "11 시행착오와 한계");
  s.addText("VAD = 말소리 없는 구간을 지우는 전처리  ·  폴백 = 인식이 나쁘면 온도를 올려 다시 인식하는 기본 동작  ·  값은 정답 대비 단어 오류율(낮을수록 좋음)", { ...T, x: MX, y: 1.62, w: 12.1, h: 0.3, fontSize: 11.5, color: "52514E" });
  const cards = [
    ["① 설정 A — 폴백 끔", "tiny·base·small × VAD 끔/켬 × 원곡/보컬, 1회", ["반복 루프가 많아 WER이 1을 넘는 조건 다수", "예) c05 base 보컬: 정답 32단어에 인식 222단어"], "당시 해석: \"분리가 VAD를 쓸 수 있게 한다\"", "DFF3E4"],
    ["② 설정 B — 기본 설정(폴백 켬)", "tiny·base × VAD × 소리, 3회 반복", ["루프가 거의 사라짐 (삽입 40개 이상 3/64 → 1/96)", "VAD 켬 + 원곡: 8구간 중 5구간이 통째로 비었음"], "→ A의 해석 철회, 최고는 base + VAD 끔 + 보컬", "DFF3E4"],
    ["③ 설정 C — 모델 크기 확대", "small·medium 추가, 기본 설정, VAD 끔", ["medium은 원곡이 보컬보다 낫고, base는 반대"], "→ medium + 원곡 + VAD 끔 + 기본 설정", "C6F24E"],
  ];
  cards.forEach(([h, cond, lines, dec, fill], i) => {
    const x = MX + i * 4.1;
    card(s, x, 1.98, 3.93, 2.3, { fill });
    s.addText(h, { ...T, x: x + 0.2, y: 2.03, w: 3.55, h: 0.4, fontSize: 15, bold: true, color: "112D18", valign: "middle" });
    s.addText(cond, { ...T, x: x + 0.2, y: 2.43, w: 3.55, h: 0.3, fontSize: 10.5, color: "52514E", valign: "middle" });
    bullets(s, lines, { x: x + 0.2, y: 2.78, w: 3.55, h: 0.95, size: 12, gap: 3 });
    s.addText(dec, { ...T, x: x + 0.2, y: 3.78, w: 3.55, h: 0.45, fontSize: 12, bold: true, color: "6250D6", valign: "middle" });
  });
  const ch = (x, title, labels, series, colors, maxV) => s.addChart(pres.charts.BAR, series.map(([name, values]) => ({ name, labels, values })), {
    x, y: 4.4, w: 3.93, h: 2.45, barDir: "col", barGrouping: "clustered", chartColors: colors, showLegend: true, legendPos: "b", legendFontSize: 10,
    showValue: true, dataLabelFontSize: 9, dataLabelFormatCode: "0.00", catAxisLabelFontSize: 10, valAxisLabelFontSize: 9, valAxisMinVal: 0, valAxisMaxVal: maxV,
    valGridLine: { style: "none" }, showTitle: true, title, titleFontSize: 11, titleColor: "52514E",
  });
  ch(MX, "VAD 끔, 소리·크기별 WER (A → B)", ["tiny 원곡", "tiny 보컬", "base 원곡", "base 보컬"], [["폴백 끔 (A)", [1.026, 0.983, 0.584, 1.221]], ["폴백 켬 (B)", [0.556, 0.586, 0.509, 0.382]]], ["8A8985", "1A9F4C"], 1.5);
  ch(MX + 4.1, "base, 기본 설정 3회 평균 (VAD 켬 원곡은 5/8구간이 빔)", ["VAD 끔", "VAD 켬"], [["원곡", [0.509, 0.740]], ["보컬", [0.382, 0.499]]], ["1A9F4C", "2A78D6"], 1.0);
  ch(MX + 8.2, "VAD 끔, 기본 설정 WER", ["base", "medium"], [["원곡", [0.509, 0.177]], ["보컬", [0.382, 0.257]]], ["1A9F4C", "2A78D6"], 0.75);
  s.addText("구간 c01~c08(10~20초), 정답 231단어, 영어, CPU·int8. 곡 번호와 숫자만 기록(가사 없음). 이 조건에서의 결과이고 일반화하지 않는다.", { ...T, x: MX, y: 6.88, w: 11.4, h: 0.25, fontSize: 10, color: "52514E" });
}

// ═════════ 12장 ═════════
section("12 목표에 비춰 본 나의 성장");
{
  const s = content("여섯 가지 목표에 비춰 보면", "⑫ 목표에 비춰 본 나의 성장", noteOf("12", 0, 1), "12 목표에 비춰 본 나의 성장");
  const h = (t, c = "112D18") => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: c }, fontSize: 14, valign: "middle" } });
  const c = (t, o = {}) => ({ text: t, options: { fontSize: 14, color: "0B0B0B", valign: "middle", ...o } });
  const rows = [
    [h("목표"), h("이 프로젝트에서의 증거", "08833C"), h("아직 부족한 것", "6250D6")],
    ["01 쓰는 도구", "서버 배포 · 로그인 · 내 문장/내 노래 · 기록, 11개 언어", "실제 사용 후기 · 검수"],
    ["02 음성·음향 처리", "16 kHz 변환, STFT·Log-Mel·FFT, pYIN F0, 단어 시간 정렬", "직접 구현한 부분의 폭"],
    ["03 AI 실험", "모델 크기·VAD·온도 비교, 원곡 대 보컬, WER/CER의 한계", "실제 환경·다른 화자"],
    ["04 소프트웨어 설계", "모듈 분리, 단위 테스트 524개(65개 건너뜀), 호출 관계 문서, DB·배포", "패키지 정리 (발표 뒤)"],
    ["05 기술 → UX", "점수와 관찰 분리, 결과 화면 순서, '어떻게 동작하나요?'", "사용자 테스트"],
    ["06 호기심·창작", "Whisper·Demucs·F0를 열어 보는 탐구 노트북", "창작(시각 표현)은 시작 전 (임시)"],
  ].map((r, i) => (i === 0 ? r : r.map((t, j) => c(t, { bold: j === 0, fill: { color: i % 2 ? "DFF3E4" : "FFFFFF" }, color: j === 2 ? "6250D6" : "0B0B0B" }))));
  s.addTable(rows, { x: MX, y: 1.95, w: W - 2 * MX, colW: [2.4, 6.3, 3.43], rowH: 0.62, border: { type: "solid", pt: 0.5, color: "E4E3DF" }, margin: [0.04, 0.12, 0.04, 0.12] });
  s.addText("단위 테스트: voice-ai 환경 unittest discover 11-10 실행 524개 통과 · 앱 화면 시험(AppTest) 27개는 따로 통과", { ...T, x: MX, y: 6.5, w: 11.5, h: 0.35, fontSize: 12, color: "52514E" });
}
{
  const s = content("AI와 함께 만든 방식", "⑫ 목표에 비춰 본 나의 성장", noteOf("12", 1, 2), "12 목표에 비춰 본 나의 성장");
  tag(s, "(임시) 표현 확정 필요", 9.2, 0.45, "temp");
  const st = [["Claude Code와 함께", "코드의 상당 부분은 Claude Code와 함께 작성했다", "DFF3E4", "112D18"], ["내가 한 것", "설계 결정 · 실험 설계 · 검증", "08833C", "FFFFFF"], ["이해하려고 만든 것", "호출 관계 문서 · 구조 탐구 노트북 · '수업과의 관계' 주석 기준", "DFF3E4", "112D18"]];
  st.forEach(([t, d, fill, c], i) => {
    const x = MX + i * 4.1;
    card(s, x, 2.0, 3.93, 3.0, { fill });
    s.addText(t, { ...T, x: x + 0.3, y: 2.25, w: 3.35, h: 0.7, fontSize: 20, bold: true, color: i === 1 ? "C6F24E" : "08833C", valign: "middle" });
    s.addText(d, { ...T, x: x + 0.3, y: 3.1, w: 3.35, h: 1.7, fontSize: 18, color: c, valign: "top" });
  });
  card(s, MX, 5.4, W - 2 * MX, 1.15, { fill: "EFE9FF", shadow: false });
  s.addText("이해하지 못한 부분은 따로 표시했다 — 확인한 것 / 추정 / 미확인을 구분해서 말한다", { ...T, x: MX + 0.3, y: 5.4, w: W - 2 * MX - 0.6, h: 1.15, fontSize: 18, bold: true, color: "6250D6", valign: "middle" });
}

{
  const s = content("수업에서 배운 것 → 내 코드에 들어간 자리", "⑫ 목표에 비춰 본 나의 성장", noteOf("12", 2, 3), "12 목표에 비춰 본 나의 성장");
  const hd = (t, c = "112D18") => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: c }, fontSize: 13, valign: "middle" } });
  const topic = (t, fill) => ({ text: t, options: { fontSize: 12, bold: true, color: "112D18", valign: "middle", fill: { color: fill } } });
  const code = (t, fill) => ({ text: t, options: { fontSize: 10.5, fontFace: "Courier New", color: "0B0B0B", valign: "middle", fill: { color: fill } } });
  const note = (t, fill) => ({ text: t, options: { fontSize: 12, color: "52514E", valign: "middle", fill: { color: fill } } });
  const R = [
    ["02 리샘플링\n→ audio.to_16k_mono", "g = gcd(sr, orig_sr)  # 44100→16000이면 (160, 441)\nx = resample_poly(x, sr // g, orig_sr // g)  # 16 kHz 모노로", "수업과 같음"],
    ["03·lesson04 STFT\n→ visualisation.stft_power", "hz, t, spec = stft(sound, fs=sr, window=\"hann\",\n    nperseg=512, noverlap=512-128)\npower = abs(spec) ** 2  # 창 512, 이동 128, 파워 = |X|²", "수업과 같음\n(인자를 한 줄씩 대조)"],
    ["lesson04 Log-Mel\n→ visualisation.logmel", "mel_power, _ = apply_mel_filters(hz, power, sr, 40)  # Mel 40개\nlog_mel = to_db(mel_power)  # 로그(dB)", "수업과 같음 + 두 소리를\n같은 색 범위로 비교"],
    ["07 Whisper 최소 예제\n→ stt.load_model", "WhisperModel(size, device=\"cpu\", compute_type=\"int8\")  # 7강과 같은 설정\nmodel.transcribe(audio, beam_size=1)  # 후보 하나만 탐색", "수업과 같음 + 모델 크기·\nVAD·온도 옵션"],
    ["05 WAV와 정답 연결\n→ sentences.csv ↔ 녹음", "sentences.csv id=1  ↔  data/recordings/s01_take1.wav\n녹음 파일 번호로 정답 문장을 찾아 비교", "같은 발상 (추정)\n5강 manifest의 id·file·reference"],
  ];
  const rows = [[hd("수업 주제 → 내 코드"), hd("코드 발췌 (한 줄 주석)", "08833C"), hd("같음 / 응용", "6250D6")]];
  R.forEach(([a, c, n], i) => { const f = i % 2 ? "FFFFFF" : "DFF3E4"; rows.push([topic(a, f), code(c, f), note(n, f)]); });
  s.addTable(rows, { x: MX, y: 1.9, w: W - 2 * MX, colW: [3.0, 6.3, 2.83], rowH: [0.42, 0.78, 0.9, 0.78, 0.78, 0.78], border: { type: "solid", pt: 0.5, color: "E4E3DF" }, margin: [0.04, 0.1, 0.04, 0.1] });
  s.addText("STFT 창 512·이동 128은 수업 설정을 그대로 썼다. 앱에 덜 응용된 것: 창 길이·Mel 개수를 바꿔 보는 실험(노트북·이슈 #35에서만). 근거: 검토 문서 16.12의 대응표", { ...T, x: MX, y: 6.6, w: 12.1, h: 0.4, fontSize: 11, color: "52514E" });
}
{
  const s = content("AI가 쓴 코드를 이해하려는 노력: 시도 → 한계 → 앞으로", "⑫ 목표에 비춰 본 나의 성장", "", "12 목표에 비춰 본 나의 성장");
  const st = [
    ["시도", "08833C", "DFF3E4", ["주석 기준을 정해 달라고 함 (이슈 #25): 파일 맨 위에 역할·흐름·수업과의 관계, 함수마다 입력·출력, 인라인은 '왜'", "수업 코드와 대응표로 대조", "호출 관계 문서·구조 탐구 노트북을 만들어 따라가기", "모르는 알고리즘은 따로 공부 (편집 거리 표 도구)"]],
    ["한계", "6250D6", "EFE9FF", ["주석을 많이 달았지만 끝까지 읽어 내지 못한 곳이 많다 (사용자 설명)", "코드를 닫고 내 말로 설명할 수 있는 곳과 아닌 곳이 섞여 있다", "직접 구현해 본 알고리즘은 일부 (F0 단어축 변환은 연습으로 남김)", "모델의 가중치·어텐션은 열어 보지 못함"]],
    ["앞으로", "112D18", "C6F24E", ["채점(scoring)·줄 나누기(song_lines)·언어 제안(languages)부터 코드를 닫고 설명해 보기", "직접 구현해 볼 부분을 정해 연습", "패키지 구조 정리 (이슈 #24)"]],
  ];
  st.forEach(([t, c, fill, items], i) => {
    const x = MX + i * 4.1;
    card(s, x, 2.0, 3.93, 4.5, { fill });
    s.addText(t, { ...T, x: x + 0.3, y: 2.12, w: 3.35, h: 0.6, fontSize: 22, bold: true, color: c, valign: "middle" });
    bullets(s, items, { x: x + 0.3, y: 2.85, w: 3.4, h: 3.55, size: 14, gap: 10 });
  });
}

// ═════════ 13장 ═════════
section("13 다음 단계와 마무리");
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "13 다음 단계와 마무리" });
  s.addNotes(noteOf("13"));
  s.addText("다음 단계", { ...T, x: MX + 0.2, y: 0.8, w: 6, h: 0.6, fontSize: 24, bold: true, color: "C6F24E" });
  bullets(s, ["서버에서 채점 속도 측정, 실제 사용자 테스트", "코드를 패키지 구조로 정리", "언어별 억양을 단어·음절 단위로 비교"], { x: MX + 0.2, y: 1.55, w: 6.2, h: 2.6, size: 18, color: "FFFFFF", gap: 12 });
  s.addText("더 알고 싶은 것", { ...T, x: 7.2, y: 0.8, w: 5.5, h: 0.6, fontSize: 24, bold: true, color: "C6F24E" });
  s.addShape(pres.ShapeType.roundRect, { x: 7.2, y: 1.55, w: 5.53, h: 1.6, rectRadius: 0.15, fill: { color: "1A9F4C", transparency: 30 }, line: { type: "none" } });
  s.addText("어텐션은 실제로 무엇을 보는가?\n두 경로는 각각 무엇을 배웠는가?", { ...T, x: 7.45, y: 1.55, w: 5.1, h: 1.6, fontSize: 18, color: "FFFFFF", valign: "middle" });
  s.addShape(pres.ShapeType.roundRect, { x: MX + 0.2, y: 4.3, w: W - 2 * MX - 0.4, h: 1.55, rectRadius: 0.15, fill: { color: "C6F24E" }, line: { type: "none" } });
  s.addText("듣고, 따라 읽고, 확인한다 —\n그리고 소리가 데이터가 되어 모델을 지나 돌아오는 길을 직접 열어 본 프로젝트", { ...T, x: MX + 0.5, y: 4.3, w: W - 2 * MX - 1.0, h: 1.55, fontSize: 24, bold: true, color: "112D18", valign: "middle", align: "center" });
  s.addText("감사합니다", { ...T, x: MX + 0.2, y: 6.2, w: 6, h: 0.7, fontSize: 32, bold: true, color: "FFFFFF" });
  s.addImage({ path: ICON, x: 11.4, y: 5.95, w: 1.0, h: 1.0, altText: "song-lingo 아이콘" });
}

(async () => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  if (SKILL) {
    const { applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"));
    await applyTheme(OUT, THEME);
  } else {
    console.log("PPTX_SKILL_DIR가 없어 테마 색 적용(applyTheme)은 건너뜀: 장표 색은 직접 지정한 값이라 모양은 같지만 PowerPoint의 테마 색 목록은 Office 기본값으로 남는다");
  }
  console.log("저장:", path.relative(ROOT, OUT));
})();
