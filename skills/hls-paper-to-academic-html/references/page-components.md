# Page Components

## Core Components

| Component | Use |
|-----------|-----|
| `cover-hero` | Paper identity and one restrained thesis |
| `paper-identity` | Authors, year, journal, DOI, design |

## Cover（`cover-hero`）两种渲染模式

`page_type: "cover"` 的 `visual.data` 决定排版：

- **多图网格（社媒推荐）**：同时有 `source_image` 与 `feature_figures` 列表 → `cover-evidence-grid`：**左整页论文截图 + 右上下两张特征图**。
- **单卡**：仅 `source_image` 或都没有 → 居中一张「今日文献」论文卡。

字段：

| 字段 | 作用 | 必填 |
|---|---|---|
| `source_image` | 左侧论文图，应为**整页截图**（含页眉/标题/作者/摘要），不是标题裁切 | 多图模式必填 |
| `feature_figures` | `[{label, image, alt, caption}]`，通常 2 张（原始图 + 关键数据区） | 多图模式必填 |
| `journal_left` | 作者行（如 `CRESWELL ET AL.`），覆盖模板默认占位 | **必须覆盖** |
| `journal_right` | 期刊·年份（如 `PNAS · 2023`） | 建议 |
| `top_label` | 封面顶部小标签 | 可选 |
| `title_size` | 封面标题字号，标题过长时降到 44 防溢出 | 可选 |

详见 `references/delivery-and-copy.md`。
| `problem-gap` | Existing belief versus research gap |
| `method-three-arm` | Two/three group experimental design |
| `sample-profile` | Sample and observation structure |
| `process-timeline` | Procedure or longitudinal sequence |
| `finding-hero` | One central result |
| `metric-cards` | Two to four comparable values |
| `outcome-matrix` | Mixed significant/null directions |
| `chart-line` | Time or ordered trend |
| `chart-bar` | Comparable magnitudes with zero baseline |
| `moderation-panel` | Conditional relationship |
| `mediation-path` | Statistical indirect path |
| `risk-balance` | Value versus risk |
| `limitations-list` | Boundaries grouped by type |
| `references-clean` | Human-readable sources |

## HLS Components

- `Signal Rail`: small cobalt cut rail for section identity.
- `Evidence Tag`: `E014 · p.11 · Table 2`.
- `Takeaway Slash`: cobalt cut edge with a short orange action line.
- `Data Peak`: angular key-number treatment.
- `Compare Split`: slanted comparison for study/control or value/risk.
- `Research Route`: numbered route rather than a generic centered agenda.

## Selection Rule

Choose a component because it explains the evidence. Do not choose a chart merely to fill space. Unknown component names must fail rendering instead of silently falling back.

Chapter labels and paper-card metadata are content, not decoration. Derive chapter labels from the current page task and populate author, journal, and year from the current paper; never inherit those values from a previous example.

## source-reading 排版硬约束

- `.reading-highlight` 在 `templates/deck.html.j2` 里设了 `white-space: nowrap`：emphasis 段的文本**不会自动换行**，超出列宽会横向溢出画布右边缘、被截断。带读笔记里被高亮的中文段必须 ≤ 约 20 字（中文 + 引号 + 标点），超出就拆：把长上下文放进非 emphasis 段、只把 12–16 字的核心 punchline 设为 emphasis，让非高亮段自由 wrap。
- 高亮段必须跟**裁剪里真实可见**的原文对齐，否则图文不一致。每次渲染后用 image 阅读人眼对一遍「高亮 ↔ 可见原文」，不一致就以图片为准重写 translation。

## source-assets clip 精度

- `source-assets.json` 整页裁剪 `clip: [0, 0, page_w, page_h]` 不能用 PDF 工具报告的「名义」页尺寸（如 439.4×666.1），要用 PyMuPDF `page.rect` 实测值（如 439.3699951171875×666.1420288085938）。`extract_source_assets.py` 的 `source_assets.py` 用 `page.rect.contains(clip)` 校验，向外溢出 0.01pt 都会被拒。保险做法：所有整页裁剪向内缩 0.01pt（例如 `[0, 0, 439.36, 666.13]`）。
