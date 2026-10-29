# 交付物规范：封面多图排版 / PNG 输出 / 小红书文案

本文件沉淀三件“证据带读 deck 完成后还要交付什么”的规范，来自 PNAS 2023 睡眠-GPA 论文的实战：

1. 首页封面用**左右分栏多图排版**（`cover-evidence-grid`）。
2. 每条 slide 导出成 **1080×1440 PNG** 作为小红书九宫格/轮播图。
3. 同步产出一段**小红书发布文案**（带结构 + 因果纪律）。

---

## 一、首页封面规范（多图排版）

模板对 `page_type: "cover"` 有两种渲染模式：

- **单卡模式**：仅设 `data.source_image`（或都不设）→ 居中一张「今日文献」论文卡。
- **多图网格模式（推荐用于社媒）**：同时设 `data.source_image` **且** `data.feature_figures` 非空 → 渲染 `cover-evidence-grid`：**左侧整页论文截图 + 右侧上下两张特征图**。

### 多图网格的 deck.json 写法

```json
{
  "id": "S01",
  "page_type": "cover",
  "title": "熬夜赶Essay，可能比你想象中更亏",
  "lead": "一篇 PNAS 论文把「睡眠时长」和「大一 GPA」连了起来",
  "visual": {
    "component": "cover-hero",
    "data": {
      "top_label": "PNAS · 2023 · 睡眠与学业表现",
      "source_image": "assets/source/A001.png",
      "source_alt": "论文首页完整截图",
      "journal_left": "CRESWELL ET AL.",
      "journal_right": "PNAS · 2023",
      "feature_figures": [
        {
          "label": "图1 · 睡眠 vs GPA",
          "image": "assets/source/F001.png",
          "alt": "5个样本的睡眠时长与GPA回归线",
          "caption": "5个独立样本方向一致：睡越多，GPA越高"
        },
        {
          "label": "关键数据 · 分组对比",
          "image": "assets/source/A002.png",
          "alt": "睡眠阈值分组与GPA数据表",
          "caption": "<6h组GPA仅3.25，相对上学期下滑0.13分"
        }
      ]
    }
  },
  "evidence_ids": ["E001", "E005"],
  "source_label": "Creswell et al., 2023, PNAS"
}
```

### 三个素材怎么来

| 素材 | 类型 | 提取方式 |
|---|---|---|
| `A001`（左侧整页） | `text_crop` | 裁剪框取**整页** `clip: [0, 0, page_width, page_height]`（PNAS 约 `[0,0,584.8,783.0]`）。PyMuPDF `page.get_pixmap(clip=page.rect, matrix=3x)`。要含 PNAS 页眉、标题、作者、摘要、Significance 蓝框——不要只裁标题区。 |
| `F001`（右上特征图） | 图表 xref | 从 `work/figures.json` 取 Figure 1 的 `xref`，`extract_source_assets.py` 抽取。 |
| `A002`（右下特征图） | `text_crop` | 裁一张**关键数据区**（如阈值分组 GPA 表 / 描述性统计表），作为“数字证据”补充图。 |

写入 `work/source-assets.json` 后跑 `extract_source_assets.py`，输出落到 `work/assets/source/`。

### 必改字段（否则出 bug）

- **`journal_left` / `journal_right` 必须覆盖为本文作者与期刊**。模板默认占位符是 `GRAYSON, HARARI & MATZ` / `COMMUNICATIONS PSYCHOLOGY · 2026`（旧示例残留），不覆盖会显示成别人的论文。例如 `"CRESWELL ET AL."` + `"PNAS · 2023"`。
- 图卡 `paper-meta` 只显示 `journal_left`，所以**作者行要靠 `journal_left` 带出**。

### 封面避坑

- **标题过长会横向溢出**：`.cover-title-line` 只在 `，` 处换行。单段中文超过约 20 字、或字号 47px 时超出 1080 画布。处置：① 控制封面标题 ≤ 约 20 字；② 或在 `data` 加 `"title_size": 44`（必要时再降）。
- **右侧特征图 caption 要短**（≤ 18 字），否则压图。
- **整页截图文字密度高**：左侧 A001 是原文，不需要再叠中文；中文解读放在后面 `source-reading` / `figure-reading` 页。

---

## 二、输出 PNG 图片（社媒轮播图）

渲染 + DOM 检查 PASS 后才截图。

```powershell
node scripts/visual-dom-check.mjs output/deck.html        # 必须 0 issues
node scripts/screenshot.mjs output/deck.html output        # 产出 slides/*.png
python scripts/build_contact_sheets.py output/slides --output output
```

产物：

| 文件 | 说明 |
|---|---|
| `output/slides/01.png … 0N.png` | **每页一张 1080×1440 PNG**，即小红书轮播图，按顺序发布 |
| `output/01.png …`（contact） | 2-up 拼合预览，供内部 QA / 快速浏览 |
| `output/deck.html` | 交互式 HTML（键盘 ←→ 翻页），可作长图替代 |

QA 门槛：DOM 检查必须全过；**人工实际打开至少 4 张关键截图**（封面、核心结果、边界/局限、收尾页）确认无溢出、图不糊、Evidence 页脚在位，才宣布完成。

---

## 三、小红书发布文案

与 deck 同源、同证据、同纪律。结构对齐用户提供的范文（论文定位 → 方法样本 → 关键数字 → 机制解读 → 边界声明 → “值得读两点” → 标签）。

### 固定结构（7 段）

1. **论文定位**：年份 + 期刊（英文缩写即可）+ 英文标题 + 中文译名。
2. **样本 / 方法**：N、机构数、测量方式（如 Fitbit 客观记录）、追踪周期。
3. **关键发现 + 数字**：β、p、分组值，全部从 `evidence-map.json` 拷，不得改写。
4. **机制 / 解读**：为什么相关、边界在哪。
5. **边界声明（必写）**：非 RCT、关联≠因果、测量误差、不显著的反例（如验证样本控制后 p=.34）。
6. **“值得读的两个点”**：给读者的一条具体收获。
7. **标签**：`#话题` 6–8 个，含 `#论文带读 #科研干货` 与本研究领域词。

### 因果纪律（硬规则）

- **纵向 / 观察研究**一律用「关联 / 相关 / 独立相关」，**禁止**「导致 / 造成 / 使得 / 引发 / 驱动 / 改变」等因果动词（`language.py` 的 `CAUSAL_TERMS`）。
- **禁止绝对词**：「所有人 / 任何人 / 必然 / 永久 / 证明了 / 彻底」（`UNIVERSAL_TERMS`）。
- 边界段必须点明「箭头代表作者检验的关系方向，不等同已证因果」。

### 字数

- 默认 **≤ 800 字**（去空格计）。先按 ~1080 字写足证据，再压缩到 800 内；压缩只删过渡与铺陈，**保留全部关键数字与边界段**。
- 例：睡眠-GPA 论文 685 字版（见下）即为达标样例。

### 达标范例（685 字，睡眠-GPA 论文）

```text
分享一篇 2023 年发表于 PNAS 的研究：Nightly sleep duration predicts grade point average in the first year of college（睡眠时长预测大学一年级 GPA）。研究者用 Fitbit 客观记录三所美国大学、五个样本共 557 名大一学生学期初约一个月的睡眠，再追踪期末 GPA。

最值得注意的发现：开学初平均每晚多睡一小时，期末 GPA 平均高约 0.07 分（β=0.001/分钟，p<.01），且在控制上学期 GPA、种族、性别等变量后依然显著。

这些学生平均每晚只睡 6 小时 37 分钟。按睡眠分组后差异明显：每晚少于 6 小时者春季 GPA 仅 3.25，还比上学期下滑 0.13 分；6–7 小时者 3.48；7 小时以上者 3.51。不足 6 小时像是 GPA 下滑的分水岭。关键不是几点睡，而是总睡眠时长——只有它跨样本稳健复现，入睡时间等指标并不稳定。

样本里 21% 每晚睡不到 6 小时，仅 5% 达到 8 小时建议线。

边界必须说清：这不是随机对照试验，作者明确需要 RCT 才能确认“增加睡眠直接提高 GPA”的因果。关联代表检验方向，不等同已证因果；验证样本 Study 5 在控制上学期 GPA 后关联便不显著（p=.34）。手环还可能少算 7–67 分钟睡眠，真实睡眠或更充足。

值得读的两点：（1）用客观测睡眠 + 纵向追踪证明睡眠与学业表现是真实存在的关联，不是“感觉而已”；（2）把“睡多少够”具体化——6 小时是分水岭，而非模糊的“早点睡”。研究教育、健康心理或带学生的导师可作参考。

#睡眠与学习 #GPA #大学生健康 #睡眠研究 #PNAS #论文带读 #科研干货 #留学干货
```

> 文案另存为 `output/小红书文案.md`，与 deck、PNG 一起交付。
