---
name: hls-paper-to-academic-html
description: Use when a user wants to turn a Chinese or English academic PDF into an evidence-traceable Chinese knowledge deck, HLS-branded 1080x1440 offline HTML, slide PNGs, contact sheets, or academic social-media visuals.
---

# HLS Paper to Academic HTML

## Overview

把论文变成可逐段核对的中文带读，而不是把摘要拆成很多观点卡。核心顺序是：完整阅读 → 证据建模 → 原文素材提取 → 结构化规划 → 数据校验 → 品牌渲染 → 截图复核。任何后序阶段都不能替代前序证据。

默认提供 5 页核心证据速读结构：封面 → 研究问题与设计 → 研究 1 → 研究 2 → 结论与边界。事实页采用“PDF 原文截图 + 中文翻译/带读”，论文中的原始图表必须保留并配解释，不得擅自重绘为更好看的结论图。用户要求超过 5 页时，才增加目录以及背景、方法、结果和局限的逐段带读页。

默认画布为小红书 3:4 竖版 `1080×1440`。标准事实页依次使用品牌蓝章节横幅、标题与“这页读什么”、原文纸卡、带读笔记、无底框竖线批注、“一句话记住”和 Evidence 页脚。章节只换文字与 SECTION 序号，不更换主题色。

## Invocation

```text
$hls-paper-to-academic-html input/paper.pdf
```

用户可补充受众、页数、重点和禁区：

```text
$hls-paper-to-academic-html input/paper.pdf
受众是英国硕士留学生，重点解释方法和主要发现，控制在 5 页以内。
```

## Before Starting

1. 定位本 Skill 根目录。
2. 读取当前项目的 `CODEX.md`。
3. Windows 全局安装优先使用 Skill 根目录的 `.venv\Scripts\python.exe`；后文的 `python` 均指这个隔离解释器。依赖缺失时停止并报告，不得改用系统级安装。
4. 读取 `DESIGN.md`、`references/evidence-and-language-rules.md`、`references/narrative-templates.md` 和 `references/delivery-and-copy.md`（封面多图排版、PNG 输出、小红书文案规范）。
5. 只在需要选择论文类型时读取 `references/paper-analysis-framework.md`。
6. 只在规划或渲染页面时读取 `references/page-components.md` 和 `references/visual-system.md`。
7. 为运行实例建立 `input/`、`work/`、`output/`，不覆盖用户原文件。

## Hard Gates

- 必须完整阅读所有带 `<!-- page: N -->` 标记的论文页面；只读摘要时禁止写最终页面。
- 必须先生成并通过校验 `work/evidence-map.json`，再生成 `work/deck-plan.json`。
- 必须生成并校验 `work/source-assets.json`；每张 PDF 原文截图和原始图表都要记录页码、裁剪框或图像 xref 与证据 ID。
- `deck-plan.json` 通过后才能生成 `output/deck.json`。
- 未验证引用、措辞和页面数据时禁止渲染。
- 未实际生成并检查 PNG 时，不得宣布完成。

这些门槛是为了阻止基线评测中出现的三类失败：摘要直接成片、只有谨慎文案却没有机器可检验证据、计划 15 页但磁盘只存在 5 页。

## Workflow

### Phase 0: Preflight

Run:

```powershell
python scripts/preflight.py input/paper.pdf --work-dir work
python scripts/prepare_logo.py input/logo.png --output assets/brand/hls-logo-transparent.png
```

若用户没有提供 Logo，使用 Skill 内的 HLS Logo。PDF 缺失、损坏、加密或没有文本层时停止。扫描 PDF 只能在用户明确启用 OCR 后进入另一条流程。

### Phase 1: Extract the Full Paper

Run:

```powershell
python scripts/extract_pdf.py input/paper.pdf --work-dir work
```

逐页读取 `work/paper.md`，核对 `metadata.json`、图表候选和参考文献。不要把不同页文本合并后丢掉页码。

### Phase 2: Build Evidence

按 `schemas/evidence-map.schema.json` 创建 `work/evidence-map.json`。每条事实性结论包含：

- `E###` ID
- 研究编号与研究设计
- 中文结论和结论强度
- 原文页码、章节、图号或表号
- 原文摘录和数字
- 允许措辞、禁止措辞和 caveat

Run:

```powershell
python scripts/validate_evidence.py work/evidence-map.json --paper work/paper.md
```

错误未清零时禁止继续。必须保留不显著、方向相反和与主命题冲突的结果。

### Phase 3: Extract Source Assets

按 `schemas/source-assets.schema.json` 创建 `work/source-assets.json`。正文段落使用页码与裁剪框，图表使用所在页的图像 xref。然后运行：

```powershell
python scripts/extract_source_assets.py input/paper.pdf work/source-assets.json --output-dir output/assets/source
```

只允许从原 PDF 确定性提取。不要用截图软件手工修图，不要把论文图表重绘成自制图；若图表无法直接提取，使用 PDF 页面裁剪并保留图号。

### Phase 4: Analyze and Choose an Angle

生成：

```text
work/paper-analysis.md
work/angle-options.json
work/selected-angle.json
```

角度排序固定为：

```text
证据强度 > 读者价值 > 清晰度 > 新颖度 > 视觉潜力
```

若 `pause_before_render=true`，展示论文类型、研究问题、3–5 个角度、推荐主命题、目录和三项过度解读风险，等待内容审核。

### Phase 5: Plan Before Writing Pages

按 Schema 生成 `work/deck-plan.json`。默认严格跟随论文结构顺序，不以“观点是否吸睛”重排证据。每页只承担一个认知任务，必须写明 `communication_goal`、`page_type`、`visual_plan`、`evidence_ids` 和 `risk_note`。

组件使用规则：

- `agenda-reading`：超过 5 页时使用的目录页，条目必须包含目标页 ID 与真实页码；5 页以内默认省略。
- `source-reading`：事实页，左侧为 PDF 原文截图，右侧为忠实中文翻译与重点标记。
- `figure-reading`：结果图表页，保留原始图表，旁边解释读图顺序、方向、数值和边界。

语言规则：

- **术语不能代替解释。** 不得把“人内共变”“因果边界”“即时情绪解释”等词单独当成结论；必须用完整句子说明谁发生了什么、依据是什么、不能推出什么。
- 第一次出现统计或心理学专有名词时，先写白话解释。中文翻译会损失含义时，保留英文原词并在括号内解释，例如 `momentary affect（参与者当时的心情）`。
- 篇幅不足时，删除优先级较低的内容，不得删掉主语、条件或结论来制造短句。每条带读标注都必须能够脱离标签独立读懂。

然后生成 `output/deck.json` 并运行：

```powershell
python scripts/validate_deck.py output/deck.json --evidence work/evidence-map.json --output-root output
```

### Phase 6: Render HLS HTML

Run:

```powershell
python scripts/render_html.py output/deck.json --output output/deck.html
```

同一 `deck.json` 必须确定性生成相同 HTML。不得添加 CDN、在线字体、远程图片或论文中没有的数据。

若启用视觉审核点，先渲染封面、研究背景、核心结果和局限四页。视觉确认后再渲染全部页面。

### Phase 7: Browser QA and Screenshots

Run:

```powershell
node scripts/visual-dom-check.mjs output/deck.html
node scripts/screenshot.mjs output/deck.html output
python scripts/build_contact_sheets.py output/slides --output output/contact-sheets
```

检查字体、图片、溢出、Logo 比例、证据 footer 和 PNG 尺寸。实际打开至少四张关键截图。

截图产物即交付物：`output/slides/01.png … 0N.png` 是每页 1080×1440 PNG（小红书轮播图）；`output/01.png …` 是 2-up 拼合预览（内部 QA / 快速浏览）。DOM 检查未全过不得截图。

### Phase 7.5: 小红书发布文案

随 deck 同步产出 `output/小红书文案.md`。结构、因果纪律与字数见 `references/delivery-and-copy.md`：论文定位 → 样本方法 → 关键数字（β/p/分组值，从 evidence-map 照搬）→ 机制解读 → 边界声明（非 RCT、关联≠因果、测量误差、不显著反例）→ “值得读两点” → 标签；纵向/观察研究全程用「关联」，默认 ≤ 800 字，压缩时不删关键数字与边界段。

### Phase 8: Final QA

输出：

```text
output/qa-evidence-report.md
output/qa-language-report.md
output/qa-visual-report.md
output/references.md
output/小红书文案.md
```

证据、语言、DOM、截图或人工视觉复核任一必需项失败，就报告未完成。不得通过删除页面、注释测试、降低字号或隐藏警告制造通过。

## Stop vs Degrade

必须停止：

- PDF 不可读、加密、损坏或无文本层。
- 关键结论缺证据 ID、页码或原文摘录。
- 观察性结果被写成确定因果。
- deck/manifest 引用不存在的文件。
- HTML 溢出、图片缺失或截图失败。

允许明确降级：

- 复杂表格 → 原表截图 + 中文解释。
- 复杂公式 → 原图 + 页码说明。
- 元数据缺失 → `null`。

降级必须写入 QA 报告，不能静默发生。

## Completion Report

最终汇报：

- 提取页数、图表候选数和文本层状态
- 论文类型、主命题和最终页数
- 证据校验通过率
- 生成的 HTML、PNG 轮播图（`output/slides/`）、接触表和 QA 路径
- 小红书文案路径与字数
- 视觉检查中发现并修复的问题
- 未解决问题和明确降级

只有所有必需检查通过后才使用“完成”。
