---
name: hls-ppt2video
description: 把海乐思 3:4 / 9:16 竖版 PPT 与口播音频合成为「幻灯片跟着音频走」的视频（MP4）。当项目已有 Dissertation 教学 PPT（PptxGenJS 或任何 PPTX）和一段口播 mp3/wav 时使用。已验证两条路线：① PPTX→PDF→PNG（soffice + PyMuPDF，优先）；② Pillow 直渲（soffice 失败时的 fallback）。
---

# 海乐思 PPT → 口播视频 生成器

把「PPT 幻灯片 + 口播音频」合成为竖屏讲解视频（MP4）。适用于海乐思 Dissertation 教学系列：已有 `素材/PPT/*.pptx`（3:4 或 9:16）和一段口播音频（mp3/wav），要产出幻灯片随音频切换的成片。

## 何时使用
- 用户给一个音频文件 + 一个 PPT（或之前用 `hls-dissertation-ppt` skill 生成的 .pptx），说「合成」「做成视频」「音频配 PPT」。
- 不要求逐字对齐字幕，只要求**幻灯片切换点贴合音频的话题边界**。

## 环境（已验证，本沙箱）
- ffmpeg / ffprobe：系统 PATH 可用（Gyan 构建 8.x）。✅
- soffice / LibreOffice：`C:/Program Files/LibreOffice/program/soffice.exe` 可用，必须带 `-env:UserInstallation=file:///.../lo_profile`，否则 headless 转换会失败。✅
- pdftoppm：❌ 未安装。因此 **PDF→PNG 走 PyMuPDF**，不走 pdftoppm。
- 转录：faster-whisper 装于 `E:/留学辅导小红书运营/.venv-video/Scripts/python.exe`（small / int8 / cpu，zh 用 `language="zh"`、en 用 `"en"`）。
- PyMuPDF 1.28.0 在 `.venv-video` 里，用于 PDF 切片。✅
- 渲染 fallback：managed Python 3.13.12 自带 Pillow 12.3.0；字体 `C:/Windows/Fonts/msyh.ttc` + `msyhbd.ttc`（微软雅黑，含 Latin 字形）。仅当没有 PPTX 或 soffice 失败时使用。

## 可靠管线

### 路线 A：已有 PPTX（优先，保留原稿视觉）
1. **PPTX → PDF**：
   ```
   "C:/Program Files/LibreOffice/program/soffice.exe" --headless --norestore \
     --convert-to pdf:impress_pdf_Export --outdir OUTDIR \
     -env:UserInstallation=file:///E:/.../lo_profile \
     input.pptx
   ```
2. **PDF → PNG（PyMuPDF）**：
   ```python
   import fitz
   doc = fitz.open("input.pdf")
   for i, page in enumerate(doc, 1):
       pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # 1620×2160 for 3:4 PPT
       pix.save(f"slides/slide-{i:02d}.png")
   doc.close()
   ```
   - 若目标是 1080×1440，zoom=3 已足够清晰；如需 2160×2880 则用 zoom=4。
3. **转录**（已有 SRT 可直接复用；否则独立进程转录）：
   ```python
   from faster_whisper import WhisperModel
   m = WhisperModel("small", device="cpu", compute_type="int8")
   segs, info = m.transcribe("audio.wav", language="zh", beam_size=5, vad_filter=True)
   ```
   - 每文件独立进程，勿在一个 Python 进程里循环转多个文件。
4. **规划 slide_timings.csv**（不要均分，除非用户要求）：
   ```csv
   slide,start_sec,end_sec,duration_sec,reason
   1,0.000,8.160,8.160,cover hook
   2,8.160,10.160,2.000,misconception
   ...
   ```
   - 读 SRT 逐段 `[start,end,text]`，按话题边界把 9 张幻灯片切到对应时段。
   - 如需让结尾 CTA 卡片多停留几秒，可让最后一行 end_sec > 音频时长，并在 ffmpeg 里用 `-t total_duration` 而不是 `-shortest`。
5. **生成标准 ffconcat 列表**（最后一张图不加 duration）：
   ```
   ffconcat version 1.0
   file 'E:/.../slides/slide-01.png'
   duration 8.160
   file 'E:/.../slides/slide-02.png'
   duration 2.000
   ...
   file 'E:/.../slides/slide-09.png'
   ```
   - 路径用**正斜杠**；ffconcat 中单引号内反斜杠会被当转义字符。
6. **合成 MP4**：
   ```
   ffmpeg -y -f concat -safe 0 -i slides.ffconcat -i audio.wav \
     -vf "scale=1080:1440:flags=lanczos,setsar=1,fps=30,format=yuv420p" \
     -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k \
     -t 50.600 -movflags +faststart OUT.mp4
   ```
   - 3:4 输出用 `scale=1080:1440`；9:16 用 `scale=1080:1920`。
   - 想保留结尾 CTA 静默尾：去掉 `-shortest`，改用 `-t <图片流总时长>`。
   - 若不需要尾帧，直接用 `-shortest`，此时视频时长 ≈ 音频时长。

### 路线 B：无 PPTX 或 soffice 失败（Pillow 直渲）
每个 PPT 需写一段 `render_xxx.py` 复刻其版面（品牌色 + 微软雅黑 + 瑞士极简）。参考 `hls-dissertation-ppt` skill 的版式零件。
- ⚠️ **中文字体两条铁律**：
  a. **绝不把「Latin + 中文」混在同一个 `draw.text` 调用里**——msyh 在混排时会把中文渲染成豆腐块（.notdef）。必须逐字符/逐段拆分，使每次 draw 调用只含单一语言。
  b. **本沙箱加载 `arialbd.ttf` 会 OSError**。因此**全程只用 `msyh.ttc` / `msyhbd.ttc`**。`ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", sz)` 取 index 0。
- 坐标换算：PPTX 7.5×10in(3:4) → PNG：1in=144px，MX≈79，CW≈922，字号 pt×2=px。9:16(7.5×13.33in) 见 `素材/视频工程/ch1_ppt2video/render_slides.py`（teal 旧风，仅参考 helper，勿直接用于海乐思品牌）。

## 校验清单（每次必做）
- 视频分辨率：3:4→1080×1440；9:16→1080×1920；H.264 + yuv420p。
- 视频时长 ≈ 音频时长（或 audio + CTA 尾时长）。
- 抽查 2–3 张最复杂幻灯片 PNG（封面、对比/双栏页、结尾）：用 Read 工具看图确认无文字溢出、无豆腐块。
- 人设残留：若源 PPT 用 `hls-dissertation-ppt` 生成，确认无 `论文导师 / 留学生学术写作辅导` 等旧词。

## 输出位置
- 成片放 `E:\留学辅导小红书运营\素材\PPT\`（同名 + `_口播视频.mp4`）。
- 工程文件（slides/、transcript、slide_timings.csv、render_*.py）可放 ASCII 工作目录 `E:/hls_video_work/`，再拷成片进项目目录。

## 已知不可行 / 避坑
- pdftoppm（未安装）
- 给 ffmpeg concat input 加 `-r`（duration 失效，视频塌成 ~1s）
- Pillow 内加载 arialbd.ttf（OSError）
- 同一 draw 调用混排 Latin+CJK（豆腐块）
- soffice 不带 `-env:UserInstallation` 时沙箱内会失败
