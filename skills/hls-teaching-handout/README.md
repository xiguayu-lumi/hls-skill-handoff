# HLS Teaching Handout Skill v1.5.2

将 Markdown、DOCX、TXT、HTML 或可提取文字的 PDF，整理为海乐思品牌化的 A4 教材式教学讲义。

## 已定稿的默认效果

- 固定蓝橙品牌封面，只根据当前资料替换标题。
- 详细多级目录，HTML/PDF 可点击跳转。
- 目录默认单栏；只有单栏实测溢出 A4 目录页时才显式启用双栏，避免双栏造成大面积空白。
- 正文连续阅读优先，不做成 PPT 或知识卡片合集。
- 中文正文采用教材式衬线字体。
- 表格使用无竖线的 LaTeX 双线表。
- 章标题、本章导读、首个二级标题与首段正文保持连续，不让章标题孤立在页尾。
- PDF 批注后的修订版使用新的版本化文件名，避免附件预览继续显示旧缓存。
- 正式 PDF 生成前在本地浏览器中预览，可修改文字、表头、表题/图题、来源说明、受控字号、行距、加粗、对齐和分页符。
- 撤销与重做同时覆盖文字编辑和字号、行距、加粗、对齐、段落类型、分页符等格式变化。
- 目录、锚点、书签、固定封面背景、页眉页脚与表格结构受到锁定保护。
- 没有有效 `EDITOR_APPROVED` 时拒绝生成正式 PDF。
- 输出 HTML、PDF、结构化 JSON、Contact Sheet 与 QA 报告。
- PDF 渲染和 QA 成功后，自动归档到标准内容项目的 `05_最终交付/教学讲义/`。
- 成品禁用“原资料”，按语境使用“来源文档”“源文档”“原文”或具体文献名。

## 使用方式

保留整个文件夹结构，将该文件夹作为一个 Skill 导入或放入 Skill 目录。入口文件为：

```text
SKILL.md
```

不要只复制 `SKILL.md`，否则固定封面模板和 CSS 会丢失。

## 预览编辑流程

先生成讲义 HTML，然后执行：

```powershell
python scripts/prepare_preview.py --project "D:\path\handout-project" --html "D:\path\draft.html"
python scripts/preview_server.py --project "D:\path\handout-project"
```

打开 `http://127.0.0.1:8765`，完成修改后点击“确认并生成 PDF”。服务器会保存批准 HTML、创建带哈希的批准标记、两阶段回填目录页码、生成 PDF、执行 QA，并在全部通过后自动归档到标准内容项目的 `05_最终交付/教学讲义/`。

如果只想检查编辑与批准，不运行渲染，可加 `--approval-only`。测试环境才允许在独立渲染命令中使用 `--auto-approve-for-test`。

## 包内关键文件

- `assets/hls-cover-template-clean.jpg`：固定封面底图。
- `templates/hls-handout.css`：已通过示例验证的蓝橙教材样式。
- `templates/preview-*`：预览编辑器外壳、样式和原生 JavaScript。
- `scripts/preview_core.py`：结构保护、清洗与批准标记。
- `scripts/preview_server.py`：仅绑定本机的预览服务器。
- `scripts/render_pdf.py`、`scripts/qa_handout.py`：审批门禁后的 PDF 与 QA。
- `scripts/render_contact_sheet.js`：从最终 PDF 逐页渲染 PNG 并生成总览图。
- `templates/cover-fragment.html`：封面文字层模板。
- `references/cover-template-spec.md`：封面标题与坐标规范。
- `references/content-model.example.json`：内容模型示例。
- `references/qa-checklist.md`：最终验收清单。
- `examples/`：一组可用于回归测试的真实示例输入。

## 推荐回归测试 Prompt

见 `examples/example-user-prompt.txt`。运行后重点检查：封面标题、三级目录、正文密度、双线表和内部跳转。

## 自动测试

```powershell
python -m unittest discover -s tests -v
```
