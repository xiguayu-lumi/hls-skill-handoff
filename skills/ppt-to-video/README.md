# PPT to Video — Codex 版

将 PPT/PPTX 与背景音乐转为 MP4，支持智能页时长、轻微推进、柔和淡入淡出、翻页动画与可选打字机效果。

## 在 Codex 中使用

新对话中直接说“把这个 PPT 转成视频”并提供 PPT 和音乐路径。Codex 会调用本目录的 `SKILL.md`，使用专用虚拟环境运行转换脚本。

## 能力边界

- 输出：1920×1080、25fps、H.264/AAC MP4；默认每页轻微推进并以交叉淡化衔接，避免生硬翻页。
- 渲染：优先 PowerPoint COM；不可用时尝试 LibreOffice。
- 依赖：`ffmpeg`、`ffprobe`，以及本目录 `.venv` 中的 Python 包。
- 不修改 PowerPoint 注册表、系统设置或源文件。
- 打字机效果是居中文字叠加，不能还原演示稿原有的逐字动画与排版。

## 原始来源

基于 [haoyiyong985/ppt-to-video](https://github.com/haoyiyong985/ppt-to-video)（MIT）适配。
