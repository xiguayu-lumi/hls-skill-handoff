---
name: hls-dissertation-ppt
description: 用 PptxGenJS 生成 3:4 竖版「海乐思」品牌 + Dissertation写作技巧 人设的留学生 Dissertation 学术写作教学 PPT。瑞士极简骨架（白底/网格/左对齐/大号序号/细规则线/留白）+ 海乐思品牌色。当用户给出口播稿/讲稿，要求做海乐思风格、Dissertation写作技巧 人设、3:4 竖版教学 PPT 时使用。已验证支持三种内容原型：独立技巧清单、流程步骤、概念辨析。
---

# 海乐思 3:4 竖版 Dissertation 教学 PPT 生成器

针对「海乐思留学」系列 Dissertation 学术写作教学 PPT 的可复用工作流。产出为**可编辑 .pptx**，竖屏 **3:4**（小红书/通用竖版比例），统一**海乐思品牌色** + **Dissertation写作技巧 人设**，瑞士极简排版骨架。

## 何时使用
- 用户给了一段口播稿/讲稿，要求「做 PPT」「海乐思风格」「同之前那版」。
- 目标比例是 **3:4 竖版**（画布 7.5"×10"）。如需 9:16 抖音竖版另算。
- 人设锁定为 **Dissertation写作技巧**（详见项目 `brand-visual-identity.md`）。**严禁使用「论文导师」「留学生学术写作辅导」「导师视角」等旧人设词**——这些词一律替换为 `Dissertation写作技巧`。

## 环境
- Node（managed）：`C:\Users\lgy\.workbuddy\binaries\node\versions\22.22.2-2\node.exe`
- 依赖 `pptxgenjs`：已装在 `C:\Users\lgy\.workbuddy\binaries\node\workspace\node_modules`。
- 运行方式（必须用 Windows 绝对路径作输出，node 会把 `/e/...` 当 C 盘相对路径）：
  ```
  NODE_PATH="C:/Users/lgy/.workbuddy/binaries/node/workspace/node_modules" \
  "C:/Users/lgy/.workbuddy/binaries/node/versions/22.22.2-2/node.exe" \
  <script>.js "E:/留学辅导小红书运营/素材/PPT/<文件名>.pptx"
  ```
- 未装 pptxgenjs 时：`cd` 到上述 workspace，`npm install pptxgenjs`。
- **本 skill 不生成 PDF**，只产出可编辑 `.pptx`（交付后用 PowerPoint/WPS 打开即可）。

## 设计系统（务必全程统一）
- **画布**：`defineLayout({ name: "V3x4", width: 7.5, height: 10 })`，比例 3:4（已校验 sldSz = 6858000×9144000 EMU）。
- **配色（海乐思品牌色，取自 `brand-visual-identity.md`）**：
  - `ink` `#1D3FA8`（深蓝：主文字 / 标题 / 规则线）— 注意**不等于**解码 Tutor 系统的 `#2C4A7C`，二者不可混用。
  - `blue` `#1F4CCB`（主蓝：大色块 / 强调条 / Logo HLS 主色）
  - `red` `#E2673D`（暖橙：关键句强调 / 行动色 / 中文「海乐思」）
  - `cyan` `#55C0F4`（亮青：次级点缀 / HIGH·EST）
  - `grey` `#6B7280`（辅助灰：kicker / footer / 英文小字）
  - `lightBlue` `#EEF4FF`（浅蓝底卡）、`lightOrange` `#FFF4EC`（浅橙底卡）
  - `light` `#E3E8F0`（浅规则线）、`line` `#1D3FA8`（强规则线）、`white` `#FFFFFF`
- **字体**：中文统一 `Microsoft YaHei`（微软雅黑）；大号数字 / 拉丁文用 `Arial`（瑞士感）。
- **瑞士极简骨架**：白底、严格网格、齐头左对齐、大号序号、细规则线、大量留白。封面/结尾可用 `red`(暖橙) 满底做对比海报。

## 统一版式零件（参考 `references/hls_ppt_template.js` 已封装为 helper）
- `bg(s, color)`：页面底色。
- `rule(s, x, y, w, color, width)`：细/粗规则线（横）。需要竖线时用 `s.addShape(pptx.ShapeType.line, {x, y, w:0, h, line:{color,width}})`。
- `kicker(s, text)`：页眉小字（灰色、字距 2、左上），放章节标签或品牌名。
- `pageNo(s, n, onRed)`：右上 `0N / TOTAL`，红色或白字。
- `title(s, zh, en)`：中文大标题（31pt 深蓝）+ 英文斜体小字（灰色）+ 下方 1.5pt 规则线。
- `footer(s, text)`：底部 `light` 细线 + 灰色小字（放 `Dissertation写作技巧 · 学术写作拆解` 之类）。
- `sqMark(s, x, y, color)`：小方块项目符号（暖橙/主蓝），用于清单。
- **封面**：白底 + kicker(`Dissertation写作技巧 · ACADEMIC WRITING`) + 大标题 + 副标题 + 可选大号水印数字。
- **结尾**：`red`(暖橙) 满底 + 白字大问句 + 账号行（`Dissertation写作技巧 · 关注我，把论文写明白`）+ 副行（`Dissertation写作技巧 · 拆解实操`）。

## 三种内容原型（选最接近的参考改）
`references/` 下提供：
- `hls_ppt_template.js`：**通用骨架模板**——品牌色 + 全部 helper + 封面/内容页/结尾示例占位，复制后填内容即可。
- `example_ch1_7things.js`：**已跑通的完整范例**——Chapter 1「被导师打回？先检查这 7 件事」10 页实战，可直接仿写或改文案复用。

| 原型 | 典型结构 | 页面数 |
|------|---------|-------|
| **独立技巧清单**（如 5 个减压技巧） | 封面→误区→总览→每技巧页(要点卡)+结尾 | 9–10 |
| **流程步骤**（如 6 步工作流） | 封面→痛点→带连接线的步骤页(做什么+操作)+结尾 | 10 |
| **概念辨析**（如 Critical≠Negative） | 封面→总览→编号内容页(定义/对比/清单)+结尾 | 9 |

改写方法：
1. 复制 `hls_ppt_template.js` 或 `example_ch1_7things.js` 为本次脚本。
2. 改 `pptx.title`、封面 kicker/标题/副标题、结尾账号行。
3. 改各页 `kicker` 章节标签、`title` 中文/英文、正文文案。
4. 概念辨析型可用「误读✕(red 暖橙) vs 正确理解✓(blue 主蓝)」对比块，或红色焦点块突出重点句。
5. 保持 `TOTAL` 与 `pageNo` 一致；纵向排布：kicker 0.55 → title 1.0~1.95 → 内容区 ~2.2 起 → footer 9.25。

## 人设红线（重要）
- 全篇人设统一写 **`Dissertation写作技巧`**。
- 任何位置出现 `论文导师` / `留学生学术写作辅导` / `留学生写作辅导` / `导师视角` → **一律替换为 `Dissertation写作技巧`**（或去掉该旧 tagline，改写价值描述如「Dissertation写作技巧 · 拆解实操」）。
- **例外**：正文中指代「学术导师 / 你的 supervisor」的「导师」是内容用词（如「被导师打回」「导师看第一章」），**保留不动**。
- 封面/结尾旧 tagline「导师视角 · 拆解实操技巧」已废止，改用「Dissertation写作技巧 · 拆解实操」。

## 校验（每次必做）
生成后确认：
- 页数：`python -c "import zipfile; print(sum(1 for n in zipfile.ZipFile(f).namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')))"` = 预期页数。（本机 `unzip` 不可用，用 python `zipfile` 替代。）
- 比例：`python -c "import zipfile,re; print(re.search(r'sldSz[^/]*cx=\"(\d+)\" cy=\"(\d+)\"', zipfile.ZipFile(f).read('ppt/presentation.xml').decode()).groups())"` 应得 `('6858000', '9144000')`（3:4）。
- 人设残留：`python -c "import zipfile; t=''.join(zipfile.ZipFile(f).read(n).decode('utf-8','ignore') for n in zipfile.ZipFile(f).namelist() if 'slides/slide' in n); print('论文导师',t.count('论文导师'),'留学生学术写作辅导',t.count('留学生学术写作辅导'))"` 应均为 0。

## 视觉复核（2026-08-28 验证可用，建议每次都做）

早期版本写「模型无法直接看 PNG」，该限制已不存在。坐标精算只是必要条件，必须再跑一遍目视复核：

```
# 1) pptx → PDF（soffice 不在 PATH，用全路径 + 独立 UserInstallation）
"/c/Program Files/LibreOffice/program/soffice.exe" --headless --norestore \
  "-env:UserInstallation=file:///C:/Users/lgy/AppData/Roaming/LibreOffice_preview" \
  --convert-to pdf --outdir <预览目录> <文件.pptx>

# 2) PDF → 逐页 PNG（PyMuPDF 装在 essay-review venv，managed 3.13 未装）
"C:/Users/lgy/.workbuddy/binaries/python/envs/essay-review/Scripts/python.exe" -c \
  "import pymupdf;d=pymupdf.open('<文件.pdf>');[d[i].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(f'<前缀>_p{i+1:02d}.png') for i in range(len(d))]"

# 3) 用 Read 工具逐页看图，重点查：文字溢出卡片、标题压副标题、底部元素顶到 footer
```

重点看三类问题：
- 大号装饰文字（≥ 48pt）溢出文本框压住下一行——给足框高，副标题与规则线留 ≥ 0.2" 缓冲。
- 列表/卡片最后一项顶到 `footer` 的细线（y=9.25）——内容区底部控制在 y ≤ 9.0。
- 中英混排出现豆腐块（本 skill 全部用 `Microsoft YaHei` + `Arial`，正常不会触发，看到即为字体串错）。

目视通过后仍请用户在 PowerPoint/WPS 打开做最终确认（渲染器与 Office 存在细微字距差异）。

## 输出位置
统一放 `E:\留学辅导小红书运营\素材\PPT\`，文件名用主题命名（中文），如 `Chapter1_七件事对齐_海乐思.pptx`。
