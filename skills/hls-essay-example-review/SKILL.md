---
name: hls-essay-example-review
description: 将学生 Essay 样例（有批注、少批注或无批注）自动重排为 A4《Essay范例精读》双语批注 PDF。保留原文、忠实翻译、保留已有教师批注并按需补充高价值写作批注；正文连续流动，右栏批注与正文句子精确对应。
---

# HLS Essay范例精读 Skill

## 0. Skill 目标

输入一篇学生 Essay 文件，自动输出一份适合学生阅读和学习的 A4 PDF《Essay范例精读》。成品应像"精读型出版物 / 学术写作案例册"，不是海报、PPT、社交媒体卡片，也不是把 Essay 改写成更好的版本。

最终阅读体验：

- 左侧连续阅读英文原文；
- 每个英文自然段后紧跟忠实中文翻译；
- 中文翻译以浅色文字 + 左侧细竖线与英文区分；
- 右侧为简洁批注，英文批注在上、忠实中文翻译在下；
- 正文被批注的具体句子或短语使用统一细下划线，并以 `[n]` 与右侧批注对应；
- 已有教师批注必须保留；批注不足时自动补充类似教师评语风格的高价值批注；
- 无批注 Essay 也能由 Skill 自动完成批注；
- 不设置封面，不设置说明页，第一页直接进入 Essay 内容。

---

## 1. 核心设计原则

### 1.1 这是"范例精读"，不是"作文改写"

Skill 的工作是帮助读者判断：

- 这篇 Essay 哪里写得好；
- 为什么有效；
- 哪里有问题；
- 为什么是问题；
- 哪些结构、论证、证据与表达方法值得迁移到自己的写作中。

默认禁止直接改动学生正文。即使发现语法、拼写、重复、句子碎片、学术语气等问题，也必须保留原文，并通过右侧批注指出。

### 1.2 视觉优先于"强行一段一页"

正文必须像普通书页一样连续铺排。不要人为规定：

- 一页只能放一个自然段；
- 一页必须完整容纳一个知识点；
- 每页批注数量必须相同。

以 A4 页面空间和阅读节奏为准，放不下时自然换页。

### 1.3 原文与翻译必须忠实

英文原文只允许修复 PDF 提取造成的技术性错误，例如：

- 错误断行；
- 页眉页脚混入正文；
- 单词被硬拆行；
- OCR 明显误识别且能由原 PDF 页面直接确认。

不得：

- 润色；
- 改写；
- 修复作者原有语法错误；
- 删除重复；
- 替换不够 academic 的表达；
- 擅自补充引用。

中文翻译应忠实传达原文的：

- 信息；
- 语气；
- 强弱程度；
- 幽默或口语感；
- 原有逻辑关系。

不要把一个本来口语化、含混或不成熟的学生句子"翻译得比原文更高级"。

### 1.4 批注要短，不要写成小论文

右栏批注的价值来自"判断准确"，而不是解释长度。

推荐单条长度：

- 英文：15-55 words；
- 中文：20-90 个汉字；
- 通常 1-3 句；
- 极少数复杂结构问题允许稍长，但不得形成大段教学文章。

---

## 2. 输入与输出

### 2.1 支持输入

主要输入：

- `.pdf`

可兼容：

- `.docx`
- `.md`
- `.txt`

PDF 优先使用原始文本层。只有文件为扫描件、没有可靠文本层时，才使用 OCR；OCR 后必须回看页面图像校对关键段落、引用、批注编号和专有名词。

### 2.2 输入类型自动识别

Skill 自动判断三种模式：

#### Mode A - 已有较完整批注

特征：

- 文中已有 Comment / Commented / annotation；
- 每 150-250 英文词已有约 1 条以上有效批注；
- 已覆盖结构、论证或语言等多个维度。

处理：

- 全部保留原批注；
- 忠实翻译；
- 只补原批注明显遗漏的高价值点；
- 不为了"看起来更满"重复批注同一问题。

#### Mode B - 批注较少

特征：

- 有教师批注，但密度明显不足；
- 例如全文只有数条，无法覆盖主要结构和写作特点。

处理：

- 原批注全部保留；
- 忠实翻译；
- 依据本文结构自动补充批注；
- 最终视觉密度接近完整精读资料。

#### Mode C - 无批注

处理：

- 自动分析全文；
- 生成教师评语式英文批注；
- 为新增英文批注生成忠实中文翻译；
- 批注呈现方式与 Mode A / B 完全一致。

### 2.3 输出

默认交付：

```text
output/
└── Essay范例精读_[essay-slug].pdf
```

构建过程中允许保留：

```text
build/
├── source.json
├── essay_analysis.json
├── bilingual.json
├── annotations.json
├── review.html
└── renders/
```

最终对用户交付时只保留成品 PDF，除非用户要求源文件。

---

## 3. 页面结构：无封面、无说明页

### 3.1 第一页直接开始正文

第一页顶部即为统一页头，下面直接进入 Essay 原始信息或题目。

如果源文件包含：

- Student name；
- Course；
- Professor；
- Date；
- Essay title；
- Assignment question；

则尽量保留，但重新整理为干净、克制的正文前置信息。

不要额外生成：

- Cover；
- Introduction page；
- 使用说明页；
- "本手册包含......"的大段说明；
- 宣传页。

### 3.2 默认不生成额外总结页

正文结束后：

- 保留原文自带的 Works Cited / Reference List / Footnotes；
- 不默认添加"Overall Review""值得学习的 5 点""Checklist"等附加页面。

如果未来用户单独要求，可作为可选功能开启，但本 Skill 默认关闭。

---

## 4. 页头与页面视觉

### 4.1 A4 规格

```text
Page: A4 portrait
Width: 210 mm
Height: 297 mm
```

建议基础边距：

```text
Top: 12-14 mm
Bottom: 12-14 mm
Left: 14-16 mm
Right: 12-14 mm
```

### 4.2 页头

固定格式：

```text
Essay范例精读 | [Essay Title]                                  03 / 08
──────────────────────────────────────────────────────────────
```

规则：

- 左侧固定出现"Essay范例精读"；
- 后接 Essay Title；
- 若标题过长，只保留标题，不再塞 Course 等信息；
- 右侧显示当前页 / 总页数；
- 下方一根极细横线；
- 页头高度要克制，不占正文空间。

建议：

```text
Header font: 9.5-10.5 pt
Rule: 0.4-0.6 pt
```

### 4.3 主版式比例

采用固定左右结构：

```text
左侧正文区：约 67-69%
中间留白：约 3-4%
右侧批注区：约 27-30%
```

建议 A4 内容宽度约 181 mm 时：

```text
Main column: 121-124 mm
Gap: 7-8 mm
Annotation column: 49-52 mm
```

禁止：

- 50/50 等宽双栏；
- 右栏过窄导致批注单词频繁断行；
- 右栏压缩正文到像报纸窄栏。

---

## 5. 左侧正文排版

### 5.1 英文原文

推荐：

```text
Font size: 10.2-10.8 pt
Line height: 1.45-1.58
Text color: #171717 / #202020
Paragraph space after: 2.5-3.5 mm
```

要求：

- 保持自然段；
- 不随意加小标题；
- 原文有 section heading 时保留；
- 原文有 block quote 时保留 block quote 层级；
- 原文有 footnote / citation 时保留。

### 5.2 中文翻译

每个英文自然段之后紧跟对应中文翻译。

视觉规范：

```text
Font size: 9.0-9.6 pt
Line height: 1.55-1.68
Text color: #666A70 左右
Left border: 0.7-1.0 pt
Border color: #BFC5CC / #C6CBD1
Padding-left: 3-4 mm
Margin-top: 1.5-2.5 mm
Margin-bottom: 4-5 mm
```

效果要类似：

```text
English paragraph...
English paragraph...

│ 中文忠实翻译......
│ 中文忠实翻译......
│ 中文忠实翻译......
```

注意：

- 中文翻译区不使用色块背景；
- 不用"翻译：""中文："等标签；
- 仅通过浅色竖线、较浅字体、略小字号建立层级。

### 5.3 Essay 题目

如果文件包含 assignment question，应在正文起始位置保留，使用轻度强调：

```text
Font size: 10-10.5 pt
Weight: 500-600
Spacing below: 5-7 mm
```

不要自行改写题目。

### 5.4 引用与参考文献

必须保留原引用体系：

- APA；
- Harvard；
- MLA；
- OSCOLA / footnote；
- Chicago；
- 其他原文格式。

不得为了"统一视觉"擅自转换引用格式。

法律 Essay 的脚注可使用较小字号：

```text
7.4-8.2 pt
line-height 1.3-1.4
```

但不得删除。

---

## 6. 正文与批注的对应方式

### 6.1 统一使用"细下划线 + 编号"

每条批注必须有具体 anchor。

正文中的被批注内容：

- 使用统一细下划线；
- 下划线颜色全书一致；
- 不使用多种 highlight 色区分不同批注来源；
- 在对应范围末尾放置小号 `[n]`。

示意：

```text
McDonald's might dominate with its cheap yet satisfying breakfast,
but Burger King rules over the lunch crowd.[3]
```

其中对应句子整体使用细下划线。

右栏：

```text
[3]
This is a good compare/contrast thesis statement.

这是一个很好的比较 / 对比型 thesis statement。
```

### 6.2 下划线样式

建议：

```text
Thickness: 0.6-0.9 pt
Offset: 1-1.8 px / 0.3-0.5 mm
Color: muted blue-gray, e.g. #4D6F9B / #526D8F
```

整本 PDF 只使用这一种 annotation underline。

不要：

- 荧光黄大片高亮；
- 红色改错线；
- 不同类别不同颜色；
- 手绘圈画；
- 箭头到处穿过正文。

### 6.3 anchor 范围

原则：**最小但语义完整**。

优先 anchor：

- 一整句；
- 一个完整 clause；
- 一个关键短语；
- 必要时连续 2 句。

不要为了批注 topic sentence 把整个自然段都下划线。

### 6.4 同一句多个批注

优先合并成一条更完整批注。

只有两个点评确实属于不同层级且均有高教学价值时，才允许：

```text
[4][5]
```

但应少用。

---

## 7. 右侧批注栏

### 7.1 右栏只放"批注 + 批注中文"

禁止出现：

- Original Comment
- Tutor Comment
- 教师原文
- 原老师批注
- 中文
- Translation
- Editor's Note
- HLS Note
- 编辑标注
- Strength
- Weakness
- Thesis
- Structure
- Academic Tone

等任何显式小标题。

呈现必须极简：

```text
[6]
Effective details about the subject. Nice bits of imagery to enhance the reading experience.

对主题的细节描写很有效，适当的意象也增强了阅读体验。
```

### 7.2 原批注和追加批注视觉完全一致

无论批注来自：

- 原 PDF 教师评语；
- Skill 后续补充；

都使用：

- 相同字体；
- 相同字号；
- 相同颜色；
- 相同行距；
- 相同编号格式；
- 相同间距。

内部数据必须保留 `source: original | generated`，但默认不在右栏视觉上区分。

为了避免把补充解析误读为全部出自原教师，默认允许在每页最底部用极浅、极小字号统一放置一行透明说明：

```text
右栏含原始评语与补充写作解析。
```

推荐字号 6.5-7 pt、浅灰；不得抢视觉。若用户明确要求完全不显示，可关闭。

### 7.3 右栏不要重型卡片

默认使用"无边框批注块"，靠留白形成分组。

推荐：

```text
Number: 8.2-8.8 pt, semibold
English: 8.2-8.8 pt
Chinese: 8.0-8.6 pt, slightly lighter
Line-height: 1.35-1.5
Gap between EN and CN: 1.2-2 mm
Gap between annotations: 4-6 mm
```

允许非常浅的右栏底色，例如 `#FAFAFB`，但不使用一个批注一个彩色框。

### 7.4 批注与正文纵向对齐

目标：批注块顶部尽量靠近对应 anchor 的纵向位置。

基础算法：

```text
desired_y = anchor_y
actual_y = max(desired_y, previous_annotation_bottom + gap)
```

若发生右栏拥挤：

优先处理顺序：

1. 压缩批注块间距，但不得低于 3 mm；
2. 微调正文段落分页，让对应 anchor 移到下一页；
3. 对"新增批注"删除低价值或重复条目；
4. 原始教师批注不得因版面拥挤被删除；
5. 最后才允许批注移至下一页。

禁止批注块互相重叠。

---

## 8. 原教师批注提取规则

### 8.1 必须提取的字段

对每条原教师批注生成：

```json
{
  "id": "w3",
  "source": "original",
  "source_page": 1,
  "anchor_text": "...",
  "comment_en": "...",
  "comment_zh": "...",
  "anchor_confidence": 0.96
}
```

### 8.2 原批注文本处理

允许：

- 合并由于 PDF 断行造成的换行；
- 修复明显由字符编码造成的破碎；
- 去掉 `Comment [w3]:`、`Commented [A3]:` 这类软件界面前缀；

不允许：

- 改写教师评语；
- 把委婉批评改得更严重；
- 把短评扩写成教学文章；
- 替老师补充未说过的判断。

`comment_en` 必须尽可能接近原教师原文。

### 8.3 原批注中文

中文只做忠实翻译，不做二次解释。

例如：

```text
Original:
Avoid repetition when possible.

Correct translation:
尽量避免重复表达。
```

不要扩写为：

```text
这里 Burger King 出现了三次，所以建议改用代词或同义表达，这样会更有学术感。
```

后者属于新增解析，不能混入原批注翻译。

---

## 9. 自动补充批注框架

> 以下分类只用于 Skill 内部判断。最终 PDF 右栏禁止显示分类标题。

新增批注从这些维度中选择高价值点：

### 9.1 Task Response

检查：

- 是否真正回应题目；
- 是否漏答多部分题目；
- 是否持续围绕 directive；
- 是否讨论了 alternative position。

适合批注：

```text
The paragraph stays focused on the second part of the question and makes the writer's position explicit.

这一段始终围绕题目的第二部分展开，并明确表达了作者立场。
```

### 9.2 Introduction / Context

检查：

- 背景是否相关；
- 是否过于宽泛；
- 是否 cliché；
- 是否定义关键概念；
- 是否有效从 broad context 收窄到 essay focus。

### 9.3 Thesis / Position

检查：

- 是否有明确立场；
- 是否只是"本文将讨论......"；
- 是否回应题目措辞；
- 是否给出 essay map；
- 是否过宽、含糊、不可论证。

### 9.4 Paragraph Control / Topic Sentence

检查：

- topic sentence 是否提出 claim；
- 是否控制段落内容；
- 段落后文是否偏离；
- 结尾是否回扣中心论点。

### 9.5 Evidence / Sources

检查：

- 有没有具体例子；
- evidence 是否真的支持 claim；
- quotation 是否被整合；
- paraphrase 是否有效；
- 引用细节是否完整；
- 是否只是堆文献。

### 9.6 Analysis / Writer's Voice

检查：

- evidence 后有没有解释；
- 有没有从材料中得出自己的判断；
- 是否明确说明 evidence 为什么重要；
- 是否有"so what"层面的推进。

### 9.7 Criticality / Counterargument

检查：

- 是否承认 alternative view；
- 是否只是描述反方；
- rebuttal 是否足够；
- 是否有 qualification / nuance；
- 是否体现 balanced judgement。

### 9.8 Structure / Signposting

检查：

- 各段顺序是否合理；
- 段与段之间是否推进；
- introduction 中的 roadmap 与 body 是否对应；
- 是否需要 section headings；
- conclusion 是否回到 thesis。

### 9.9 Academic Style / Tone

检查：

- 过度使用 `you / I`；
- conversational tone；
- 夸张、俚语；
- cliché；
- vague wording；
- sentence fragment；
- awkward expression；
- 不必要的 repetition；
- concision。

只批对学术写作有明显影响的问题，不做逐句语法批改。

### 9.10 Conclusion

检查：

- 是否总结主论点；
- 是否重新表达立场而不是机械重复；
- 是否引入新证据；
- 最后一句是否有力度；
- 是否有合理 implication。

### 9.11 Referencing

只在确有教学价值时批：

- citation integration；
- page number；
- footnote use；
- Ibid；
- Reference List 格式；
- source authority。

不要每一个 reference 都批一遍。

---

## 10. 自动批注的语言风格

新增英文批注必须模仿真实大学写作中心 / 教师批注的风格：

- direct；
- concise；
- specific；
- educational；
- restrained；
- 不营销；
- 不夸张。

推荐句型：

```text
This is a clear thesis statement and gives the reader a useful map of the essay.

The specific example makes the claim more convincing.

This sentence links the paragraph back to the writer's position.

The point is relevant, but it needs more analysis to show why the evidence supports the claim.

The tone is engaging, but the direct use of "you" is more conversational than most academic essays require.

This repeats the previous idea without adding much. A more concise sentence would strengthen the paragraph.
```

禁止风格：

```text
Amazing sentence!
This is a perfect high-scoring technique!
Students must copy this structure!
这里写得太牛了！
这一句就是70+密码！
```

---

## 11. 批注密度控制

### 11.1 目标密度

不要固定"每段 N 条"，改为动态密度。

一般 1000-2000 英文词 Essay：

```text
建议总批注：18-30 条
建议每 A4 正文页：4-7 条
```

较短的 500-900 词 Essay：

```text
建议总批注：10-18 条
```

较长的 2500+ 词 Essay：

```text
每页保持 3-6 条即可，不必线性增加到 50+ 条。
```

### 11.2 高价值优先级

当候选批注过多时，按以下优先级保留：

1. 回应题目 / thesis；
2. argument / critical analysis；
3. paragraph control；
4. evidence 与 source integration；
5. conclusion / linking；
6. academic tone；
7. repetition / clarity；
8. 小型 grammar 问题。

### 11.3 正负面平衡

批注不应只"挑错"。

整篇至少应覆盖：

- 有效做法；
- 可改进问题；
- 结构与论证判断；
- 语言风格判断。

如果文章质量较高，可以更多解释"为什么这段有效"；如果文章质量一般，可以更多指出可改进点。

---

## 12. 避免重复批注

新增批注前先建立 `issue_registry`。

例如已经批过：

```text
Repeated use of "you" makes the tone conversational.
```

后面再次出现 `you` 时，默认不再重复同样评语，除非：

- 使用程度明显升级；
- 在重要位置如 conclusion 产生新问题；
- 原教师本身有对应批注，必须保留。

同样适用于：

- cliché；
- repetition；
- weak topic sentence；
- missing citation；
- vague wording。

---

## 13. 翻译流程

### 13.1 正文翻译

按"自然段"作为主单元翻译。

要求：

- 不漏句；
- 不自行总结；
- 不把引用改写为概述；
- 人名、机构名、案例名、论文名保持准确；
- 法律案例名一般保留英文；
- 技术术语首次出现可采用"中文（English）"，后续自然翻译。

### 13.2 批注翻译

批注必须逐条对应，不额外解释。

### 13.3 引文翻译

Essay 正文中的 direct quote：

- 英文原文保持原样；
- 中文段落中忠实翻译；
- 原引用标记 / citation 保留在译文适当位置；
- 不伪造译者来源。

---

## 14. 自动分页逻辑

### 14.1 内容单位

排版时，每个自然段建立一个 `content_unit`：

```json
{
  "paragraph_id": "p04",
  "english": "...",
  "translation": "...",
  "anchors": ["a12", "a13"]
}
```

### 14.2 英文 + 中文的分页策略

优先把一个英文自然段与对应中文译文作为一个阅读单元。

规则：

- 若完整单元较短且当前页能放下，则完整放在当前页；
- 若完整单元较短但当前页只剩少量空间，则整个单元移到下一页；
- 若单元本身很长，占超过约 45-50% 页面高度，则允许自然跨页；
- 尽量避免页面底部只出现 1 行英文或 1 行中文；
- widow/orphan 最少保留 2-3 行。

### 14.3 批注优先同页

对应 anchor 与批注应尽量在同页。

若自动生成的新增批注导致右栏溢出，应优先删掉该页最低价值的"新增批注"，而不是把大量批注推到下一页。

原教师批注优先保留同页。

### 14.4 不允许的版面问题

- 注释盖住正文；
- 注释互相重叠；
- 中文竖线跨过页眉；
- 页面底部出现半截批注；
- 参考文献被右栏覆盖；
- 下划线延伸到不相关句子；
- 编号重复或跳号无原因。

---

## 15. 推荐的数据结构

### 15.1 `source.json`

```json
{
  "title": "The Clown Vs. the Crown",
  "course": "English M02",
  "student": "Sample Student A",
  "date": "3 April 2013",
  "question": null,
  "paragraphs": [],
  "references": [],
  "original_annotations": []
}
```

### 15.2 `annotations.json`

```json
[
  {
    "id": 3,
    "source": "original",
    "anchor": "McDonald's might dominate ... lunch crowd.",
    "anchor_start": 812,
    "anchor_end": 934,
    "comment_en": "This is a good compare/contrast thesis statement.",
    "comment_zh": "这是一个很好的比较 / 对比型 thesis statement。",
    "priority": 100,
    "category_internal": "thesis"
  },
  {
    "id": 4,
    "source": "generated",
    "anchor": "...",
    "comment_en": "The example is vivid, but the paragraph relies mainly on personal preference rather than evidence.",
    "comment_zh": "这个例子很具体，但本段主要依赖个人偏好，而不是可验证的证据。",
    "priority": 72,
    "category_internal": "evidence"
  }
]
```

注意：

- `source` 和 `category_internal` 只用于内部；
- 最终 PDF 不展示这些字段。

---

## 16. 实现技术路线

### 16.1 本沙箱推荐架构

```text
PDF/DOCX
  |
  v
scripts/extract_pdf.py (PyMuPDF)
  |
  v
Structured JSON (source.json)
  |
  v
Translation (AI 逐段翻译)
  |
  v
Annotation analysis (AI 分析 + 原批注提取)
  |
  v
scripts/build_review_html.py (HTML + CSS)
  |
  v
WeasyPrint HTML -> PDF
  |
  v
scripts/render_pdf_verify.py (PDF -> PNG 验证)
```

### 16.2 为什么推荐 HTML/CSS

本产品是：

- 文本密集；
- 连续流动；
- A4 固定页面；
- 左正文 + 右侧注释；
- 需要自动分页；
- 需要 underlined anchors；
- 需要快速视觉调试。

HTML/CSS 比直接在 PDF 坐标中逐字绘制更适合。

建议：

- 使用 semantic HTML；
- CSS 定义统一出版样式；
- JS 处理分页、anchor 位置和注释碰撞；
- 浏览器预览确认后导出 PDF。

### 16.3 环境

```text
Python venv:  C:\Users\lgy\.workbuddy\binaries\python\envs\essay-review
Python exe:   C:\Users\lgy\.workbuddy\binaries\python\envs\essay-review\Scripts\python.exe
依赖:         PyMuPDF (fitz), WeasyPrint, Pillow
```

首次使用前安装依赖：

```bash
"C:\Users\lgy\.workbuddy\binaries\python\versions\3.13.12\python.exe" -m venv "C:\Users\lgy\.workbuddy\binaries\python\envs\essay-review"
"C:\Users\lgy\.workbuddy\binaries\python\envs\essay-review\Scripts\pip.exe" install PyMuPDF weasyprint Pillow
```

若 WeasyPrint 因 GTK 依赖在 Windows 上不可用，备用方案：
- 用 ReportLab 直接生成 PDF（纯 Python，无系统依赖）；
- 或用 Pillow 逐页渲染 PNG 后合并为 PDF。

### 16.4 PDF 输入解析

优先：

```text
PyMuPDF (fitz)
```

需要同时读取：

- 页面文字；
- 文字坐标；
- PDF annotations（如存在）；
- 原页码；
- footnote 与正文位置。

不要只依赖 `page.get_text()` 后直接拼接，因为这容易把右栏 Comment 混进正文顺序。

先按坐标识别：

```text
main_text_region
annotation_region
header_footer_region
```

再重建逻辑文本。

### 16.5 批注 anchor 匹配

优先级：

1. PDF annotation 本身带 anchor / rect；
2. Word-style comment range 可恢复；
3. 根据批注语义与相邻正文自动匹配；
4. 人工无法确定时，匹配置信度标记为低，自动选择最近的语义完整句。

`anchor_confidence < 0.65` 时，在 build log 中输出 warning，要求在导出前人工查看页面图像确认。

---

## 17. 页面布局实现建议

### 17.1 HTML 结构示例

```html
<section class="page">
  <header class="page-header">...</header>

  <div class="page-grid">
    <main class="essay-column">
      <div class="paragraph-unit" data-id="p1">
        <p class="essay-en">...</p>
        <div class="translation-zh">...</div>
      </div>
    </main>

    <aside class="annotation-column">
      <div class="annotation" data-anchor="a3">
        <div class="annotation-number">[3]</div>
        <div class="annotation-en">...</div>
        <div class="annotation-zh">...</div>
      </div>
    </aside>
  </div>
</section>
```

### 17.2 anchor 示例

```html
<span class="annotated-text" data-annotation="3">
  McDonald's might dominate with its cheap yet satisfying breakfast, but Burger King rules over the lunch crowd.
</span><sup class="annotation-ref">[3]</sup>
```

### 17.3 注释定位

浏览器完成正文布局后：

```javascript
const anchorRect = anchor.getBoundingClientRect();
const pageRect = page.getBoundingClientRect();
const desiredY = anchorRect.top - pageRect.top;
```

再执行 collision avoidance。

不要使用 SVG 连接线作为默认视觉元素。

### 17.4 参考模板

完整 HTML/CSS 模板见 `references/layout_template.html`，包含：
- 全部设计 token（CSS 变量）
- A4 页面尺寸与边距
- 双栏比例与间距
- 英文正文 + 中文翻译竖线样式
- 右栏批注块样式
- 下划线 anchor 样式
- 页头页脚

---

## 18. 参考样例中应模仿的"批注逻辑"

本 Skill 的新增批注应吸收以下类型的教师判断：

- 判断开头是否 cliché；
- 肯定 specific examples 是否有效；
- 判断 wording 是否 awkward；
- 评价 thesis 是否 clear、insightful、是否有 essay map；
- 评价 opposing viewpoint 的处理是否削弱作者立场；
- 评价 paraphrased research 和 quotation 的使用；
- 指出 repetition、vagueness、fragment；
- 判断 academic tone；
- 判断 introduction 是否交代 broader topic、definition、thesis 和 outline；
- 判断 topic sentence 是否是一个 claim，并控制 paragraph development；
- 判断 supporting sentences 是否解释并用 sources 支撑 claim；
- 判断 writer 是否从 evidence 中形成自己的 conclusion；
- 判断 paragraph ending 是否 link back to question；
- 判断 conclusion 是否 restate position、summarise main arguments、提出 implication；
- 法律类 Essay 中进一步检查是否识别 alternative positions、是否持续回应 directive、是否使用 section heading、是否正确处理 footnotes / Ibid。

重要：这些只是生成逻辑，不要把它们做成右栏可见的小标题。

---

## 19. 质量控制与 PDF 验证

### 19.1 必须执行 render -> verify

生成 PDF 后必须渲染为 PNG 检查。

```bash
"C:\Users\lgy\.workbuddy\binaries\python\envs\essay-review\Scripts\python.exe" \
  "<skill_dir>/scripts/render_pdf_verify.py" \
  output/Essay范例精读_xxx.pdf \
  --out_dir build/renders \
  --dpi 180
```

检查：

- 字体是否缺字；
- 中文是否出现方框；
- 英文 quotation marks 是否正常；
- underlines 是否与目标文本匹配；
- annotation number 是否对应；
- 右栏是否溢出；
- 页头是否统一；
- 翻译竖线是否断裂异常；
- footnotes / references 是否完整；
- 是否有巨大空白；
- 是否有过密页面。

### 19.2 必须进行内容校验

自动输出检查表：

```text
[ ] 原文段落数量与源文件一致
[ ] 原引用/脚注未丢失
[ ] 原教师批注全部保留
[ ] 每条原批注已有中文翻译
[ ] 每条批注有唯一编号
[ ] 每条批注有 anchor
[ ] 新增批注无明显重复
[ ] 中文正文无漏译自然段
[ ] 不存在封面页
[ ] 不存在说明页
[ ] 页头统一为 Essay范例精读
```

### 19.3 视觉验收门槛

以下任一出现则不得交付：

- clipped text；
- overlapping annotation；
- black squares / missing glyph；
- 页码错位；
- 下划线批错句子；
- 批注编号与正文编号不一致；
- 右栏文本被截断；
- 中文翻译和英文原文顺序错位；
- 单页出现超过 35% 无意义空白且可通过重排解决。

---

## 20. 默认视觉参数

可先采用以下 token，之后根据实际样稿微调：

```css
:root {
  --page-bg: #ffffff;
  --text-main: #1d1f22;
  --text-translation: #666b72;
  --annotation-text: #25282d;
  --annotation-cn: #555b63;
  --rule: #25282d;
  --translation-rule: #c5cad0;
  --annotation-underline: #55C0F4;
  --annotation-column-bg: #EEF4FF;

  --font-en: "Arial", "Helvetica", sans-serif;
  --font-zh: "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei", sans-serif;
}
```

注意：

- 不打包或分发字体文件；
- 使用运行环境已安装字体；
- 若指定字体不存在，必须安全 fallback；
- 最终 PDF 嵌入字体或保证渲染稳定。

---

## 21. 禁止事项

Skill 绝对禁止：

1. 创建封面；
2. 创建说明页；
3. 把每个自然段强行拆成一页；
4. 把右栏做成知识卡片合集；
5. 显示"原老师批注 / 编辑批注 / 中文 / 英文"等标签；
6. 用不同颜色区分原批注和新增批注；
7. 对正文直接进行润色改写；
8. 未经依据给学生 Essay 打出具体分数；
9. 把所有语言问题都批一遍；
10. 生成大段 AI 教程式解释；
11. 将引用格式统一成 Skill 自己偏好的格式；
12. 删除 Works Cited / Reference List；
13. 使用夸张营销语；
14. 让 HLS 品牌元素压过 Essay 内容；
15. 默认加 Logo、水印、价格、联系方式。

---

## 22. 默认行为配置

```yaml
page:
  size: A4
  orientation: portrait
  cover: false
  intro_page: false
  summary_page: false

header:
  label: "Essay范例精读"
  show_essay_title: true
  show_page_count: true

content:
  preserve_original: true
  translate_to_zh: true
  translation_style: faithful
  preserve_references: true

annotations:
  preserve_original: true
  generate_when_sparse: true
  generate_when_missing: true
  visual_source_distinction: false
  internal_source_tracking: true
  target_per_page_min: 4
  target_per_page_max: 7
  show_category_labels: false
  show_translation_labels: false
  anchor_style: thin_underline
  connector_lines: false
  disclosure_footer: true

layout:
  main_column_ratio: 0.68
  annotation_column_ratio: 0.28
  continuous_flow: true
  keep_short_bilingual_unit_together: true
```

---

## 23. 执行指令

当用户提供 Essay 文件并要求使用本 Skill 时，按以下顺序执行，不要跳步：

```text
1. Inspect input file.
2. Determine whether it is annotated, sparsely annotated, or unannotated.
3. Extract the essay body, metadata, assignment question, citations, footnotes and existing comments.
4. Reconstruct clean original text without rewriting the student's wording.
5. Build paragraph-level bilingual translation.
6. Recover each original comment and its anchor.
7. Analyse the essay globally before generating any new comment.
8. Create only high-value supplementary comments where coverage is weak.
9. Remove redundant generated comments.
10. Number all comments in final reading order.
11. Build A4 HTML using the fixed two-column layout.
12. Apply thin underlines to exact anchor text.
13. Place each English comment and Chinese translation in the right column without labels.
14. Paginate continuously; do not force one paragraph per page.
15. Export PDF.
16. Render all pages to images and visually inspect.
17. Fix clipping, annotation collisions, large blank areas, bad anchors and typography problems.
18. Re-export and verify before delivery.
```

---

## 24. 成品判断标准

一份合格的《Essay范例精读》应该让学生打开任意一页后，几秒内理解三个层级：

1. **黑色英文**：学生原文；
2. **浅灰中文 + 左竖线**：忠实翻译；
3. **右侧 `[n]` 英文批注 + 中文批注**：对应某一处正文的写作评价。

视觉上应：

- 信息密度高但不拥挤；
- 像认真整理的阅读材料；
- 不像 AI 生成的信息图；
- 不像 Word 修订模式截图；
- 不像营销海报；
- 不需要说明也能理解版式关系。

内容上应：

- 保留真实学生写作的优点和问题；
- 教师已有批注一个不丢；
- 新增批注克制、准确、可迁移；
- 读者能够通过一篇完整 Essay 学到结构、论证、证据和学术表达。

---

## 25. MVP 验收任务

首次开发完成后，用至少三种样例测试：

### Test 1 - 少批注 Essay

目标：验证原批注提取 + 自动补批注。

检查：

- 原批注全部保留；
- 增补后密度自然；
- 不重复老师已有判断。

### Test 2 - 高密度 UTS 类批注 Essay

目标：验证"已有批注足够时不过度追加"。

检查：

- thesis / topic sentence / evidence / linking 等原批注能准确匹配正文；
- 右栏不会因批注多而溢出；
- 生成批注数量明显减少。

### Test 3 - 无批注高分 Essay

目标：验证全自动 annotation mode。

检查：

- 批注既能指出 exemplary features，也能指出有限的改进空间；
- 不因文章质量高而机械"找茬"；
- 批注覆盖 thesis、paragraph development、source use、analysis、linking、conclusion 等核心层级。

三类均通过后，才将 Skill 视为稳定版本。
