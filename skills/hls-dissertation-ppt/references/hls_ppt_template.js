// 海乐思 3:4 竖版 Dissertation 教学 PPT —— 通用骨架模板（Swiss / International Typographic Style）
// 白底 + 海乐思品牌色 + 网格化、左对齐、大字号序号、细规则线、大量留白
// 人设：Dissertation写作技巧（不要用 论文导师 / 留学生学术写作辅导 / 导师视角）
//
// 用法：复制本文件，按 TODO 填内容，然后：
//   NODE_PATH="C:/Users/lgy/.workbuddy/binaries/node/workspace/node_modules" \
//   "C:/Users/lgy/.workbuddy/binaries/node/versions/22.22.2/node.exe" \
//   this_template.js "E:/留学辅导小红书运营/素材/PPT/<主题>.pptx"

const PptxGenJS = require("pptxgenjs");

const pptx = new PptxGenJS();
pptx.defineLayout({ name: "V3x4", width: 7.5, height: 10 });
pptx.layout = "V3x4";
pptx.author = "Dissertation写作技巧";
// TODO: 改标题
pptx.title = "主题 · 副标题占位";

// ===== 海乐思品牌配色（取自 brand-visual-identity.md）=====
// 注意：ink #1D3FA8 ≠ 解码 Tutor 的 #2C4A7C，二者不可混用
const C = {
  white: "FFFFFF",
  ink: "1D3FA8",      // 深蓝：主文字 / 标题 / 规则线
  blue: "1F4CCB",     // 主蓝：大色块 / 条（Logo HLS 主色）
  red: "E2673D",      // 暖橙：强调 / 关键句 / 行动色
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
const TOTAL = 10;               // TODO: 改成实际页数

// ===== 统一版式零件（Swiss 骨架）=====
function bg(s, color) { s.background = { color }; }
function rule(s, x, y, w, color = C.line, width = 1.5) {
  s.addShape(pptx.ShapeType.line, { x, y, w, h: 0, line: { color, width } });
}
function vRule(s, x, y, h, color = C.light, width = 1) {
  s.addShape(pptx.ShapeType.line, { x, y, w: 0, h, line: { color, width } });
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

// ===== 1. 封面（白底）=====
(function cover() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "Dissertation写作技巧  ·  ACADEMIC WRITING");
  pageNo(s, 1);
  rule(s, MX, 1.15, 1.3, C.red, 3);
  // TODO: 封面主标题 / 副标题
  s.addText("主标题占位", { x: MX, y: 1.9, w: CW, h: 1.1, fontFace: FH, fontSize: 44, bold: true, color: C.ink, align: "left", valign: "middle" });
  s.addText("副标题占位", { x: MX, y: 3.2, w: CW, h: 0.5, fontFace: FH, fontSize: 16, color: C.grey, align: "left", valign: "middle" });
  rule(s, MX, 8.7, CW, C.light, 1);
  s.addText("Dissertation写作技巧 · 拆解实操", { x: MX, y: 8.85, w: CW, h: 0.4, fontFace: FH, fontSize: 12, color: C.ink, align: "left", valign: "middle" });
})();

// ===== 2. 内容页示例（白底 + title + 规则线 + 正文）=====
(function contentExample() {
  const s = pptx.addSlide();
  bg(s, C.white);
  kicker(s, "CHAPTER 0X — 章节标签");
  pageNo(s, 2);
  title(s, "中文标题", "English Subtitle");
  // TODO: 正文区（y 从 ~2.2 起，footer 在 9.25）
  s.addText("要点一", { x: MX, y: 2.4, w: CW, h: 0.45, fontFace: FH, fontSize: 16, bold: true, color: C.ink, align: "left", valign: "middle" });
  sqMark(s, MX, 3.1);
  s.addText("清单条目示例（用 sqMark 做项目符号）", { x: MX + 0.32, y: 3.05, w: CW - 0.4, h: 0.45, fontFace: FH, fontSize: 15, bold: true, color: C.ink, align: "left", valign: "middle" });
  // 红色焦点块示例（重点句）
  s.addShape(pptx.ShapeType.rect, { x: MX, y: 4.2, w: CW, h: 1.2, fill: { color: C.red }, line: { type: "none" } });
  s.addText("关键句 / 警示放进红色焦点块", { x: MX + 0.3, y: 4.2, w: CW - 0.6, h: 1.2, fontFace: FH, fontSize: 18, bold: true, color: "FFFFFF", align: "left", valign: "middle" });
  footer(s, "Dissertation写作技巧 · 学术写作拆解");
})();

// ===== 3. 结尾（暖橙满底海报）=====
(function closing() {
  const s = pptx.addSlide();
  bg(s, C.red);
  s.addText("Dissertation写作技巧  ·  ACADEMIC WRITING", { x: MX, y: 0.55, w: CW - 1.4, h: 0.35, fontFace: NUM, fontSize: 11, bold: true, color: "FFFFFF", align: "left", valign: "middle", charSpacing: 2 });
  s.addText("10 / 10", { x: W - MX - 1.3, y: 0.55, w: 1.3, h: 0.35, fontFace: NUM, fontSize: 11, bold: true, color: "FFFFFF", align: "right", valign: "middle", charSpacing: 1 });
  // TODO: 结尾大问句
  s.addText("你现在卡在哪一块？", { x: MX, y: 1.9, w: CW, h: 1.0, fontFace: FH, fontSize: 33, bold: true, color: "FFFFFF", align: "left", valign: "middle", lineSpacingMultiple: 1.05 });
  s.addText("评论区告诉我", { x: MX, y: 3.1, w: CW, h: 0.5, fontFace: FH, fontSize: 18, color: "FFFFFF", align: "left", valign: "middle" });
  rule(s, MX, 3.85, CW, "FFFFFF", 1.5);
  s.addText([
    { text: "Dissertation写作技巧 · 关注我，把论文写明白", options: { breakLine: true, fontFace: FH, fontSize: 13, bold: true, color: "FFFFFF" } },
    { text: "Dissertation写作技巧 · 拆解实操", options: { fontFace: NUM, fontSize: 10.5, color: "FFFFFF" } },
  ], { x: MX, y: 8.6, w: CW, h: 0.8, fontFace: FH, align: "left", valign: "middle", lineSpacingMultiple: 1.2 });
})();

const OUT = process.argv[2] || "output_3x4.pptx";
pptx.writeFile({ fileName: OUT }).then((fn) => console.log("生成成功:", fn)).catch((e) => { console.error("生成失败:", e); process.exit(1); });
