// 竖屏 3:4 小红书教学PPT —— 瑞士极简风（Swiss / International Typographic Style）
// 白底 + 黑字 + 瑞士红(#E2231A)，网格化、左对齐、大字号序号、细规则线、大量留白
const PptxGenJS = require("pptxgenjs");

const pptx = new PptxGenJS();
pptx.defineLayout({ name: "V3x4", width: 7.5, height: 10 });
pptx.layout = "V3x4";
pptx.author = "Dissertation写作技巧";
pptx.title = "Chapter 1 被导师打回？先检查这 7 件事有没有对齐";

// 海乐思品牌配色（取自 brand-visual-identity）
const C = {
  white: "FFFFFF",
  ink: "1D3FA8",      // 深蓝：主文字 / 标题 / 规则线
  blue: "1F4CCB",     // 主蓝：大色块 / 条
  red: "E2673D",      // 暖橙：强调 / 关键句（品牌行动色）
  cyan: "55C0F4",     // 亮青：次级点缀
  grey: "6B7280",     // 辅助灰
  lightBlue: "EEF4FF",// 浅蓝底
  lightOrange: "FFF4EC",// 浅橙底
  light: "E3E8F0",    // 浅规则线
  line: "1D3FA8",     // 强规则线
};
const FH = "Microsoft YaHei";   // CJK 干净无衬线
const NUM = "Arial";            // 拉丁/数字，瑞士感
const W = 7.5, H = 10, MX = 0.55, CW = W - MX * 2;
const TOTAL = 10;

function bg(s, color) { s.background = { color }; }
function rule(s, x, y, w, color = C.line, width = 1.5) {
  s.addShape(pptx.ShapeType.line, { x, y, w, h: 0, line: { color, width } });
}
function kicker(s, text) {
  s.addText(text, { x: MX, y: 0.55, w: CW - 1.4, h: 0.35, fontFace: NUM, fontSize: 11, bold: true, color: C.grey, align: "left", valign: "middle", charSpacing: 2 });
}
function pageNo(s, n, onRed = false) {
  s.addText(`${String(n).padStart(2, "0")} / ${TOTAL}`, {
    x: W - MX - 1.3, y: 0.55, w: 1.3, h: 0.35, fontFace: NUM, fontSize: 11, bold: true,
    color: onRed ? C.white : C.red, align: "right", valign: "middle", charSpacing: 1,
  });
}
function title(s, zh, en) {
  s.addText(zh, { x: MX, y: 1.0, w: CW, h: 0.7, fontFace: FH, fontSize: 31, bold: true, color: C.ink, align: "left", valign: "middle" });
  if (en) s.addText(en, { x: MX, y: 1.72, w: CW, h: 0.22, fontFace: NUM, fontSize: 11, italic: true, color: C.grey, align: "left", valign: "middle", charSpacing: 1 });
  rule(s, MX, 1.95, CW, C.line, 1.5);
}
function footer(s, text) {
  rule(s, MX, 9.25, CW, C.light, 1);
  s.addText(text, { x: MX, y: 9.35, w: CW, h: 0.35, fontFace: FH, fontSize: 10, color: C.grey, align: "left", valign: "middle" });
}
function sqMark(s, x, y, color = C.red) {
  s.addShape(pptx.ShapeType.rect, { x, y: y + 0.04, w: 0.14, h: 0.14, fill: { color }, line: { type: "none" } });
}

// 1. 封面
(function cover() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "Dissertation写作技巧  ·  ACADEMIC WRITING");
  pageNo(s, 1);
  rule(s, MX, 1.15, 1.3, C.red, 3);
  // 右侧大号浅灰「7」水印
  s.addText("7", { x: 3.9, y: 3.5, w: 3.4, h: 3.8, fontFace: NUM, fontSize: 230, bold: true, color: C.light, align: "center", valign: "middle" });
  s.addText("被导师打回？", { x: MX, y: 1.75, w: CW, h: 1.1, fontFace: FH, fontSize: 48, bold: true, color: C.ink, align: "left", valign: "middle" });
  s.addText([
    { text: "先检查这 ", options: { fontFace: FH, fontSize: 29, bold: true, color: C.ink } },
    { text: "7", options: { fontFace: NUM, fontSize: 36, bold: true, color: C.red } },
    { text: " 件事有没有对齐", options: { fontFace: FH, fontSize: 29, bold: true, color: C.ink } },
  ], { x: MX, y: 2.95, w: CW, h: 0.7, align: "left", valign: "middle" });
  s.addText("论文第一章不是「引言」，是地基。", { x: MX, y: 3.75, w: CW, h: 0.5, fontFace: FH, fontSize: 16, color: C.grey, align: "left", valign: "middle" });
  rule(s, MX, 8.7, CW, C.light, 1);
  s.addText("Dissertation写作技巧 · 拆解实操", { x: MX, y: 8.85, w: CW, h: 0.4, fontFace: FH, fontSize: 12, color: C.ink, align: "left", valign: "middle" });
})();

// 2. 常见误区
(function hook() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 常见误区");
  pageNo(s, 2);
  title(s, "学生把第一章，当成「引言」", "The #1 Misconception");
  s.addText("误读", { x: MX, y: 2.35, w: 2, h: 0.4, fontFace: FH, fontSize: 14, bold: true, color: C.red, align: "left", valign: "middle" });
  s.addText("以为是开场白、是铺垫，随便写写就过去了。", { x: MX, y: 2.78, w: CW, h: 0.45, fontFace: FH, fontSize: 15, color: C.ink, align: "left", valign: "middle" });
  rule(s, MX, 3.45, CW, C.light, 1);
  s.addText("真实定位", { x: MX, y: 3.65, w: 2.5, h: 0.4, fontFace: FH, fontSize: 14, bold: true, color: C.ink, align: "left", valign: "middle" });
  s.addText("它是整篇 Dissertation 的地基——后面每一章怎么写，这一章就定死了。", { x: MX, y: 4.08, w: CW, h: 0.7, fontFace: FH, fontSize: 15, color: C.ink, align: "left", valign: "top", lineSpacingMultiple: 1.15 });
  rule(s, MX, 5.0, CW, C.light, 1);
  // 收尾红色强调句
  s.addText([
    { text: "导师看第一章，看的不是文笔，", options: { fontFace: FH, fontSize: 18, bold: true, color: C.ink } },
    { text: "是你到底清不清楚自己在研究什么。", options: { fontFace: FH, fontSize: 18, bold: true, color: C.red } },
  ], { x: MX, y: 5.4, w: CW, h: 0.9, align: "left", valign: "middle", lineSpacingMultiple: 1.2 });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 3. 七件事总览（2 列网格）
(function overview() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 七件事总览");
  pageNo(s, 3);
  s.addText([
    { text: "第一章要写清 ", options: { fontFace: FH, fontSize: 31, bold: true, color: C.ink } },
    { text: "7", options: { fontFace: NUM, fontSize: 36, bold: true, color: C.red } },
    { text: " 件事", options: { fontFace: FH, fontSize: 31, bold: true, color: C.ink } },
  ], { x: MX, y: 1.0, w: CW, h: 0.85, align: "left", valign: "middle" });
  rule(s, MX, 1.95, CW, C.line, 1.5);
  const items = [
    ["01", "研究背景", "Research Background", "由宽到窄，收口到你的研究问题"],
    ["02", "问题陈述", "Problem Statement", "整章最重要：讲清「问题」本身"],
    ["03", "研究空白", "Research Gap", "前人没覆盖的，就是你存在的理由"],
    ["04", "研究目标", "Research Objectives", "三到四个，直接回应问题陈述"],
    ["05", "研究问题", "Research Questions", "把目标拆成可回答的问句"],
    ["06", "研究意义", "Research Significance", "对谁有用：研究者 / 行业 / 政策"],
    ["07", "研究范围", "Research Scope", "写死包含与不包含什么"],
  ];
  const colW = (CW - 0.5) / 2, rowH = 1.78, x0 = MX, y0 = 2.15;
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = x0 + col * (colW + 0.5), y = y0 + row * rowH;
    s.addText(it[0], { x, y: y - 0.05, w: 1.0, h: 0.7, fontFace: NUM, fontSize: 30, bold: true, color: C.red, align: "left", valign: "middle" });
    s.addText(it[1], { x: x + 1.0, y: y, w: colW - 1.0, h: 0.45, fontFace: FH, fontSize: 17, bold: true, color: C.ink, align: "left", valign: "middle" });
    s.addText(it[2], { x: x + 1.0, y: y + 0.45, w: colW - 1.0, h: 0.28, fontFace: NUM, fontSize: 9, italic: true, color: C.grey, align: "left", valign: "middle" });
    s.addText(it[3], { x: x + 1.0, y: y + 0.74, w: colW - 1.0, h: 0.4, fontFace: FH, fontSize: 10.5, color: C.grey, align: "left", valign: "top", lineSpacingMultiple: 1.05 });
    if (col === 0) rule(s, x + 1.0, y + 1.18, colW - 1.0, C.light, 1);
  });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 4. 研究背景（由宽到窄）
(function p1() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 研究背景");
  pageNo(s, 4);
  title(s, "研究背景", "Research Background");
  const bars = [
    [5.6, C.ink, "行业 & 社会 · 大环境", C.white],
    [4.2, C.ink, "你的研究领域 / 语境", C.white],
    [2.6, C.red, "你的研究问题", C.white],
  ];
  let y = 2.55;
  bars.forEach(([w, f, t, tc], i) => {
    s.addShape(pptx.ShapeType.rect, { x: MX, y, w, h: 0.95, fill: { color: f }, line: { type: "none" } });
    s.addText(t, { x: MX + 0.25, y, w: w - 0.4, h: 0.95, fontFace: FH, fontSize: 14, bold: true, color: tc, align: "left", valign: "middle" });
    if (i < bars.length - 1) s.addShape(pptx.ShapeType.downArrow, { x: MX + 0.18, y: y + 1.0, w: 0.3, h: 0.28, fill: { color: C.ink }, line: { type: "none" } });
    y += 1.28;
  });
  s.addText([
    { text: "由宽到窄", options: { fontFace: FH, fontSize: 15, bold: true, color: C.red } },
    { text: "：背景不是凑字数，是为你的问题铺路。", options: { fontFace: FH, fontSize: 15, color: C.ink } },
  ], { x: MX, y: 6.7, w: CW, h: 0.6, align: "left", valign: "middle" });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 5. 问题陈述（最重要 · 红色焦点块）
(function p2() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 问题陈述");
  pageNo(s, 5);
  title(s, "问题陈述", "Problem Statement");
  s.addShape(pptx.ShapeType.rect, { x: MX, y: 2.25, w: CW, h: 1.45, fill: { color: C.red }, line: { type: "none" } });
  s.addText("PROBLEM STATEMENT", { x: MX + 0.3, y: 2.4, w: CW - 0.6, h: 0.35, fontFace: NUM, fontSize: 12, bold: true, color: "FFFFFF", align: "left", valign: "middle", charSpacing: 1 });
  s.addText("整章最重要的一段，没有之一", { x: MX + 0.3, y: 2.78, w: CW - 0.6, h: 0.75, fontFace: FH, fontSize: 20, bold: true, color: "FFFFFF", align: "left", valign: "middle" });
  s.addText([
    { text: "✕  ", options: { fontFace: FH, fontSize: 15, bold: true, color: C.red } },
    { text: "别只描述话题——把 topic 复述一遍，没讲清「问题」到底是什么。", options: { fontFace: FH, fontSize: 14.5, color: C.ink } },
  ], { x: MX, y: 4.0, w: CW, h: 0.6, align: "left", valign: "middle", lineSpacingMultiple: 1.1 });
  rule(s, MX, 4.7, CW, C.light, 1);
  const pts = ["到底哪里出了问题？", "文献里缺了什么？", "为什么这件事值得研究？"];
  let y = 4.95;
  pts.forEach((t) => {
    sqMark(s, MX, y);
    s.addText(t, { x: MX + 0.32, y, w: CW - 0.4, h: 0.45, fontFace: FH, fontSize: 15, bold: true, color: C.ink, align: "left", valign: "middle" });
    y += 0.62;
  });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 6. 研究空白（四宫格维度）
(function p3() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 研究空白");
  pageNo(s, 6);
  title(s, "研究空白", "Research Gap");
  s.addText("前人的研究还没覆盖什么？你整个研究存在的理由，就写在这里。", { x: MX, y: 2.2, w: CW, h: 0.6, fontFace: FH, fontSize: 14.5, color: C.ink, align: "left", valign: "middle", lineSpacingMultiple: 1.15 });
  s.addText("空白，可能是不同的——", { x: MX, y: 3.0, w: CW, h: 0.4, fontFace: FH, fontSize: 14, bold: true, color: C.red, align: "left", valign: "middle" });
  const chips = [["国家", "Context"], ["语境", "Setting"], ["人群", "Sample"], ["方法", "Method"]];
  const topColors = [C.blue, C.red, C.cyan, C.blue];
  const cw = (CW - 3 * 0.3) / 4, ch = 2.0;
  chips.forEach((c, i) => {
    const x = MX + i * (cw + 0.3);
    s.addShape(pptx.ShapeType.rect, { x, y: 3.6, w: cw, h: ch, fill: { color: C.white }, line: { color: C.ink, width: 1.25 } });
    s.addShape(pptx.ShapeType.rect, { x, y: 3.6, w: cw, h: 0.12, fill: { color: topColors[i] }, line: { type: "none" } });
    s.addText(c[0], { x, y: 4.0, w: cw, h: 0.9, fontFace: FH, fontSize: 19, bold: true, color: C.ink, align: "center", valign: "middle" });
    s.addText(c[1], { x, y: 4.9, w: cw, h: 0.4, fontFace: NUM, fontSize: 10, italic: true, color: C.grey, align: "center", valign: "middle" });
  });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 7. 研究目标 & 研究问题（逻辑链）
(function p4() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 研究目标 & 研究问题");
  pageNo(s, 7);
  title(s, "研究目标 & 研究问题", "Objectives & Questions");
  s.addText("目标不用多，三个就够；这些目标要直接回应问题陈述。", { x: MX, y: 2.2, w: CW, h: 0.5, fontFace: FH, fontSize: 14.5, color: C.ink, align: "left", valign: "middle" });
  const boxes = [["01", "问题陈述", "Statement"], ["02", "研究目标", "Objectives"], ["03", "研究问题", "Questions"]];
  const bw = 1.9, bh = 1.75, by = 3.0, gap = (CW - 3 * bw) / 2;
  boxes.forEach(([n, t, en], i) => {
    const x = MX + i * (bw + gap);
    s.addShape(pptx.ShapeType.rect, { x, y: by, w: bw, h: bh, fill: { color: C.white }, line: { color: C.ink, width: 1.25 } });
    s.addText(n, { x: x + 0.2, y: by + 0.15, w: bw - 0.4, h: 0.5, fontFace: NUM, fontSize: 22, bold: true, color: C.red, align: "left", valign: "middle" });
    s.addText(t, { x: x + 0.2, y: by + 0.7, w: bw - 0.4, h: 0.5, fontFace: FH, fontSize: 16, bold: true, color: C.ink, align: "left", valign: "middle" });
    s.addText(en, { x: x + 0.2, y: by + 1.18, w: bw - 0.4, h: 0.35, fontFace: NUM, fontSize: 9.5, italic: true, color: C.grey, align: "left", valign: "middle" });
    if (i < boxes.length - 1) s.addShape(pptx.ShapeType.rightArrow, { x: x + bw + 0.02, y: by + bh / 2 - 0.16, w: gap - 0.04, h: 0.32, fill: { color: C.red }, line: { type: "none" } });
  });
  rule(s, MX, 5.25, CW, C.light, 1);
  s.addText([
    { text: "硬逻辑：", options: { fontFace: FH, fontSize: 15, bold: true, color: C.ink } },
    { text: "问题连着目标，目标连着问句，三者必须", options: { fontFace: FH, fontSize: 15, color: C.ink } },
    { text: "环环相扣", options: { fontFace: FH, fontSize: 15, bold: true, color: C.red } },
    { text: "。这条线一断，导师一眼就能看出来。", options: { fontFace: FH, fontSize: 15, color: C.ink } },
  ], { x: MX, y: 5.5, w: CW, h: 1.4, align: "left", valign: "middle", lineSpacingMultiple: 1.25 });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 8. 研究意义 & 研究范围（双栏 + 中缝规则）
(function p5() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 研究意义 & 研究范围");
  pageNo(s, 8);
  title(s, "研究意义 & 研究范围", "Significance & Scope");
  // 中缝竖线
  s.addShape(pptx.ShapeType.line, { x: MX + CW / 2, y: 2.2, w: 0, h: 4.0, line: { color: C.light, width: 1 } });
  // 左：意义
  s.addText("研究意义", { x: MX, y: 2.35, w: CW / 2 - 0.4, h: 0.4, fontFace: FH, fontSize: 17, bold: true, color: C.red, align: "left", valign: "middle" });
  s.addText("回答「对谁有用」", { x: MX, y: 2.8, w: CW / 2 - 0.4, h: 0.4, fontFace: FH, fontSize: 13, color: C.ink, align: "left", valign: "middle" });
  ["研究者", "行业", "政策制定者"].forEach((t, i) => {
    const y = 3.45 + i * 0.72;
    sqMark(s, MX, y);
    s.addText(t, { x: MX + 0.32, y, w: CW / 2 - 0.8, h: 0.5, fontFace: FH, fontSize: 15, bold: true, color: C.ink, align: "left", valign: "middle" });
  });
  // 右：范围
  const rx = MX + CW / 2 + 0.4;
  s.addText("研究范围", { x: rx, y: 2.35, w: CW / 2 - 0.4, h: 0.4, fontFace: FH, fontSize: 17, bold: true, color: C.red, align: "left", valign: "middle" });
  s.addText("回答包含什么、不包含什么", { x: rx, y: 2.8, w: CW / 2 - 0.4, h: 0.4, fontFace: FH, fontSize: 13, color: C.ink, align: "left", valign: "middle" });
  ["对象", "地点", "语境"].forEach((t, i) => {
    const y = 3.45 + i * 0.72;
    sqMark(s, rx, y);
    s.addText(t, { x: rx + 0.32, y, w: CW / 2 - 0.8, h: 0.5, fontFace: FH, fontSize: 15, bold: true, color: C.ink, align: "left", valign: "middle" });
  });
  rule(s, MX, 6.4, CW, C.light, 1);
  s.addText("意义讲价值，范围划边界。", { x: MX, y: 6.6, w: CW, h: 0.5, fontFace: FH, fontSize: 15, bold: true, color: C.ink, align: "left", valign: "middle" });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 9. 自检页
(function selftest() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 01 — 自检");
  pageNo(s, 9);
  title(s, "七件事写完，别急着交", "Self-Check");
  s.addText("做一个连线测试", { x: MX, y: 2.25, w: CW, h: 0.5, fontFace: FH, fontSize: 18, bold: true, color: C.red, align: "left", valign: "middle" });
  s.addText("把这三样单独抄出来，放在一起：", { x: MX, y: 2.9, w: CW, h: 0.45, fontFace: FH, fontSize: 14.5, color: C.ink, align: "left", valign: "middle" });
  s.addText([
    { text: "Problem Statement", options: { fontFace: NUM, fontSize: 20, bold: true, color: C.ink } },
    { text: "   ·   ", options: { fontFace: NUM, fontSize: 18, color: C.grey } },
    { text: "研究目标", options: { fontFace: FH, fontSize: 20, bold: true, color: C.ink } },
    { text: "   ·   ", options: { fontFace: NUM, fontSize: 18, color: C.grey } },
    { text: "研究问题", options: { fontFace: FH, fontSize: 20, bold: true, color: C.ink } },
  ], { x: MX, y: 3.5, w: CW, h: 0.6, align: "left", valign: "middle" });
  s.addText("看它们能不能连成一条线。", { x: MX, y: 4.25, w: CW, h: 0.45, fontFace: FH, fontSize: 14.5, color: C.ink, align: "left", valign: "middle" });
  s.addShape(pptx.ShapeType.rect, { x: MX, y: 5.2, w: CW, h: 1.6, fill: { color: C.red }, line: { type: "none" } });
  s.addText("连不上 —— 导师一定看得出来。", { x: MX + 0.3, y: 5.2, w: CW - 0.6, h: 1.6, fontFace: FH, fontSize: 22, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// 10. 结尾（瑞士红海报）
(function closing() {
  const s = pptx.addSlide();
  bg(s, C.red);
  s.addText("Dissertation写作技巧  ·  ACADEMIC WRITING", { x: MX, y: 0.55, w: CW - 1.4, h: 0.35, fontFace: NUM, fontSize: 11, bold: true, color: "FFFFFF", align: "left", valign: "middle", charSpacing: 2 });
  s.addText("10 / 10", { x: W - MX - 1.3, y: 0.55, w: 1.3, h: 0.35, fontFace: NUM, fontSize: 11, bold: true, color: "FFFFFF", align: "right", valign: "middle", charSpacing: 1 });
  s.addText("你现在卡在第一章的哪一块？", { x: MX, y: 1.9, w: CW, h: 1.0, fontFace: FH, fontSize: 33, bold: true, color: "FFFFFF", align: "left", valign: "middle", lineSpacingMultiple: 1.05 });
  s.addText("评论区告诉我", { x: MX, y: 3.1, w: CW, h: 0.5, fontFace: FH, fontSize: 18, color: "FFFFFF", align: "left", valign: "middle" });
  rule(s, MX, 3.85, CW, "FFFFFF", 1.5);
  const nums = ["01", "02", "03", "04", "05", "06", "07"];
  const nw = CW / 7;
  nums.forEach((n, i) => {
    s.addText(n, { x: MX + i * nw, y: 4.3, w: nw, h: 0.5, fontFace: NUM, fontSize: 16, bold: true, color: "FFFFFF", align: "left", valign: "middle" });
  });
  s.addText([
    { text: "Dissertation写作技巧 · 关注我，把论文写明白", options: { breakLine: true, fontFace: FH, fontSize: 13, bold: true, color: "FFFFFF" } },
    { text: "Dissertation写作技巧 · 拆解实操", options: { fontFace: NUM, fontSize: 10.5, color: "FFFFFF" } },
  ], { x: MX, y: 8.6, w: CW, h: 0.8, fontFace: FH, align: "left", valign: "middle", lineSpacingMultiple: 1.2 });
})();

const OUT = process.argv[2] || "Chapter1_七件事对齐_瑞士极简.pptx";
pptx.writeFile({ fileName: OUT }).then((fn) => console.log("生成成功:", fn)).catch((e) => { console.error("生成失败:", e); process.exit(1); });
