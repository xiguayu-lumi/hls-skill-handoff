# 数据结构参考

本 Skill 在构建过程中使用以下 JSON 文件。AI 执行时按此结构产出数据，脚本按此结构读取。

## 1. source.json（extract_pdf.py 输出）

从 PDF 提取的原始结构化数据。

```json
{
  "title": "The Clown Vs. the Crown",
  "course": "English M02",
  "student": "Sample Student A",
  "professor": null,
  "date": "3 April 2013",
  "question": null,
  "paragraphs": [
    {
      "text": "When it comes to fast food, there are two names that come to mind...",
      "page": 1,
      "bbox": [85.2, 120.5, 310.8, 145.3]
    }
  ],
  "references": [
    { "text": "Smith, J. (2010). Fast Food Marketing. New York: Press.", "page": 5 }
  ],
  "original_annotations": [
    {
      "id": "o1",
      "source": "original",
      "source_page": 1,
      "anchor_text": "McDonald's might dominate with its cheap yet satisfying breakfast",
      "comment_en": "This is a good compare/contrast thesis statement.",
      "comment_zh": "",
      "anchor_confidence": 0.90,
      "annot_type": "Comment"
    }
  ],
  "annotation_mode": "A",
  "source_file": "input.pdf",
  "source_type": "pdf",
  "page_count": 5
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string\|null | Essay 标题（从首页推断） |
| `course` | string\|null | 课程代码 |
| `student` | string\|null | 学生姓名 |
| `professor` | string\|null | 教授姓名 |
| `date` | string\|null | 日期 |
| `question` | string\|null | Assignment question（如有） |
| `paragraphs` | array | 按阅读顺序的正文段落 |
| `paragraphs[].text` | string | 段落文本（已清理 PDF 提取错误） |
| `paragraphs[].page` | int | 源 PDF 页码 |
| `paragraphs[].bbox` | array\|null | 文本块坐标 [x0, y0, x1, y1] |
| `references` | array | 引用/参考文献条目 |
| `original_annotations` | array | 原教师批注 |
| `original_annotations[].id` | string | 唯一 ID（"o" + 数字） |
| `original_annotations[].source` | string | 固定为 "original" |
| `original_annotations[].source_page` | int | 批注所在源 PDF 页码 |
| `original_annotations[].anchor_text` | string | 批注对应的正文文本 |
| `original_annotations[].comment_en` | string | 原批注英文（已清理前缀） |
| `original_annotations[].comment_zh` | string | 中文翻译（初始为空，由翻译步骤填充） |
| `original_annotations[].anchor_confidence` | float | anchor 匹配置信度 0-1 |
| `annotation_mode` | string | "A"（批注充分）/ "B"（稀疏）/ "C"（无批注） |

## 2. bilingual.json（翻译步骤输出）

段级双语翻译数据。

```json
{
  "paragraphs": [
    {
      "id": "p1",
      "english": "When it comes to fast food...",
      "translation": "说到快餐......"
    }
  ],
  "references_translations": [
    { "text": "Smith, J. (2010). Fast Food Marketing. New York: Press.", "translation": "" }
  ]
}
```

翻译规则（SKILL.md §13）：
- 按自然段翻译，不漏句、不总结、不改写引用
- 人名/机构名/案例名保持准确
- 法律案例名保留英文
- 技术术语首次可"中文（English）"

## 3. annotations.json（批注分析步骤输出）

所有批注（原始 + 自动补充），按阅读顺序编号。

```json
[
  {
    "id": 1,
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
    "id": 2,
    "source": "generated",
    "anchor": "The specific example makes the claim more convincing.",
    "comment_en": "The specific example makes the claim more convincing.",
    "comment_zh": "这个具体例子使论点更有说服力。",
    "priority": 72,
    "category_internal": "evidence"
  }
]
```

内部字段（不在 PDF 中显示）：
- `source`: "original" | "generated"
- `priority`: 0-100，用于拥挤时删减低价值新增批注
- `category_internal`: 内部分类（thesis / evidence / structure / tone 等）

## 4. review_data.json（合并后输入 build_review_pdf.py / build_review_html.py）

AI 将 source.json + bilingual.json + annotations.json 合并为最终构建数据。

```json
{
  "title": "The Clown Vs. the Crown",
  "course": "English M02",
  "student": "Sample Student A",
  "professor": null,
  "date": "3 April 2013",
  "question": "Compare and contrast two fast-food restaurants...",
  "references": ["Smith, J. (2010). Fast Food Marketing. New York: Press."],
  "references_title": "Works Cited",
  "paragraphs": [
    {
      "id": "p1",
      "english": "When it comes to fast food, McDonald's and Burger King...",
      "translation": "说到快餐，麦当劳和汉堡王......",
      "annotations": [
        {
          "id": 1,
          "source": "original",
          "anchor_text": "McDonald's might dominate with its cheap yet satisfying breakfast, but Burger King rules over the lunch crowd.",
          "comment_en": "This is a good compare/contrast thesis statement.",
          "comment_zh": "这是一个很好的比较 / 对比型 thesis statement。"
        }
      ]
    }
  ]
}
```

关键规则：
- `paragraphs[].annotations[].anchor_text` 必须是 `english` 字段中实际出现的子串
- `id` 在全文范围内唯一，按阅读顺序从 1 开始
- `source` 和 `category_internal` 不出现在最终 PDF 中

## 5. 文件流关系

```text
input.pdf
    |
    v  extract_pdf.py
source.json
    |
    +---> AI 翻译 ---> bilingual.json
    |
    +---> AI 批注分析 ---> annotations.json
    |
    v  AI 合并
review_data.json
    |
    +---> build_review_html.py ---> review.html (浏览器预览)
    |
    +---> build_review_pdf.py  ---> Essay范例精读_xxx.pdf (最终交付)
         |
         v  render_pdf_verify.py
         renders/*.png + verification_report.json (验收)
```
