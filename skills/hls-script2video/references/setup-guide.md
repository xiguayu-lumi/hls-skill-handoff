# 依赖配置指南

本 skill 编排 hls-dissertation-ppt（PPT 生成）与 hls-ppt2video（视频合成），两者分别管理自身环境；本指南只列编排器自身核验的依赖。全部依赖均为本机工具或项目环境，无需登录或凭据。

## node-runtime（生成 PPT）

- 用途：PptxGenJS 脚本运行环境，支撑阶段 1。
- 官方主页：https://nodejs.org/
- 官方文档：https://nodejs.org/docs/latest/
- 配置步骤：
  1. 从 https://nodejs.org/ 安装 Node.js 22 或更高版本（本机 managed 路径 ~/.workbuddy/binaries/node/versions/22.22.2/node.exe）。
  2. 在 managed node workspace（~/.workbuddy/binaries/node/workspace）执行 npm install pptxgenjs，确认 node_modules/pptxgenjs 存在。
  3. PPT 环节的实际生成由 hls-dissertation-ppt 完成，环境按其规范检查。
- 验证：node --version 输出 v22 及以上；pptxgenjs 目录存在。
- 安全：只装在 managed workspace，不安装全局包。

## ffmpeg-cli（合成视频）

- 用途：抽音频、合成 MP4，支撑阶段 3。
- 官方主页：https://ffmpeg.org/
- 官方文档：https://ffmpeg.org/documentation.html
- 配置步骤：
  1. 从 https://ffmpeg.org/download.html 下载构建版（如 Gyan 构建）并加入 PATH。
  2. 确认 ffmpeg 与 ffprobe 均可用。
- 验证：ffmpeg -version 与 ffprobe -version 均输出版本信息。
- 安全：只使用 PATH 内的系统 ffmpeg，不下载不明来源二进制。

## python-pillow（封面渲染与幻灯片直渲）

- 用途：render_cover.py 封面绘制，以及 hls-ppt2video 的 Pillow 直渲，支撑阶段 3、4。
- 官方主页：https://python-pillow.org/
- 官方文档：https://pillow.readthedocs.io/
- 配置步骤：
  1. 使用 managed Python（~/.workbuddy/binaries/python/versions/3.13.12/python.exe，自带 Pillow 12.3.0）。
  2. 确认字体存在：NotoSerifSC-VF.ttf、NotoSansSC-VF.ttf、times.ttf（C:/Windows/Fonts/）。
- 验证：python -c "import PIL; print(PIL.__version__)"；三个字体文件存在。
- 安全：不额外安装包；字体只用系统字体文件。

## faster-whisper-env（音频转录）

- 用途：口播音频转录时间戳，供 slide_timings.csv 对齐，支撑阶段 3。
- 官方主页：https://github.com/SYSTRAN/faster-whisper
- 官方文档：https://github.com/SYSTRAN/faster-whisper#installation
- 配置步骤：
  1. 使用项目转录环境 .venv-video（E:/留学辅导小红书运营/.venv-video/Scripts/python.exe，Python 3.12 + faster-whisper small 模型）。
  2. 英文源用 language=en，中文源用 language=zh；逐文件独立进程，不循环复用模型。
- 验证：python -c "import faster_whisper" 无报错；模型缓存存在。
- 安全：模型只从官方 Hugging Face 缓存下载。

核验日期：2026-08-26。适用版本：1.0.0。
