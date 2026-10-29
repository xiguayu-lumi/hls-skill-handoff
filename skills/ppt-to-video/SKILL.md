---
name: ppt-to-video
description: 将 PPT/PPTX 与背景音乐转换为 1920×1080 MP4，带自然页面动效、柔和翻页动画和可选正文打字机效果。用于“PPT转视频”“PPT生成视频”“PPT加音乐”“将PPT做成视频”等请求。
---

# PPT 转视频

将演示文稿渲染为 25fps、H.264/AAC 的 MP4。默认使用按页面文字量计算的播放时长、轻微推进与交叉淡化，使页面切换更自然。

## 运行边界

- 仅处理用户明确指定或已放入当前工作目录的 `.ppt`、`.pptx` 和音频文件。
- 背景音乐为必需输入；没有音乐时，先向用户询问音乐文件或是否改用静音音轨。
- 输出默认与 PPT 同目录；若在内容项目内工作，优先输出到该项目的 `05_最终交付/`。
- 临时文件由脚本自动清理；除非用户明确要求，不使用 `--keep-temp`。
- 不修改 PowerPoint 注册表、系统设置或用户的源文件。

## 依赖与预检

本 Skill 的专用 Python 环境为 `<skill-root>/.venv`。始终用它运行脚本，不向系统 Python 安装包。

执行前检查：

```powershell
$skillRoot = 'C:\Users\lgy\.codex\skills\ppt-to-video'
& "$skillRoot\.venv\Scripts\python.exe" -c "import pptx, PIL, win32com.client; print('Python dependencies OK')"
ffmpeg -version
ffprobe -version
```

若 PowerPoint COM 不可用，脚本会尝试 LibreOffice；只有在两种渲染器都不可用时才报告缺失项，不应绕过错误或伪造视频。

## 执行

```powershell
$skillRoot = 'C:\Users\lgy\.codex\skills\ppt-to-video'
& "$skillRoot\.venv\Scripts\python.exe" "$skillRoot\scripts\ppt_to_video.py" `
  '<PPT路径>' '<音乐路径>' `
  --output '<输出MP4路径>' `
  --transition fade `
  --motion subtle `
  --fps 25
```

可选参数：

- `--transition slideup|diagtl|fade|none`：默认 `fade`，比推拉转场更柔和。
- `--transition-dur 0.5`：翻页动画时长。
- `--motion subtle|none`：默认 `subtle`，给每页添加轻微推进（最高 1.04 倍）和 0.35 秒淡入；信息密集或不想移动画面时用 `none`。
- `--typewriter`：只给正文页添加居中打字机文字层；它不能保留 PPT 原有文字排版，不要在排版敏感的演示稿上默认开启。
- `--cover-dur 1.5`、`--back-cover-dur 4`：封面和封底时长。
- `--content-cps 3`、`--content-min 6`、`--content-max 8`：正文页智能时长规则。

## 验收

转换成功后，验证输出文件存在并用 ffprobe 读取时长、分辨率和帧率：

```powershell
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate,duration -of default=noprint_wrappers=1 '<输出MP4路径>'
```

向用户报告输出绝对路径、页数、总时长、动画方式、是否启用打字机效果和实际渲染方案。若失败，报告 PowerPoint/LibreOffice/ffmpeg 中具体哪一项失败及原始错误摘要。
