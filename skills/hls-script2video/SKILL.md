---
name: hls-script2video
description: "把口播稿做成海乐思完整交付的编排器：生成 3:4 Dissertation 教学 PPT（委托 hls-dissertation-ppt）、在豆包音频上传点暂停等待配音、合成 3:4 竖屏口播视频（委托 hls-ppt2video 管线）、渲染外刊风封面。用户说「把这份口播稿做成完整视频」「口播稿配豆包音合成视频一条龙」「从口播稿做全套含封面」「走一遍 PPT 音频视频封面全流程」时使用。"
version: 1.0.0
agent_created: true
---

# 海乐思口播稿 → PPT + 视频 + 封面 全流程编排器

把一份口播稿做成完整交付的编排器：依次产出 3:4 海乐思教学 PPT、豆包配音后的 3:4 竖屏口播视频、外刊风封面图。本 skill 不重写 PPT 生成与视频合成，而是编排两个项目级 skill（hls-dissertation-ppt、hls-ppt2video），在中间插入豆包音频上传暂停点，并内置外刊风封面渲染器。

## 何时使用

- 用户给出口播稿/讲稿，说「做成完整视频」「一条龙：PPT、音频、视频、封面」。
- 用户已有口播稿，需要按海乐思规范成套出片（PPT + 视频 + 封面）。
- 需要外刊风封面作为视频封面。

不适用：只做 PPT（走 hls-dissertation-ppt）；已有 PPT 和音频只合成视频（走 hls-ppt2video）；只做图文不拍视频。

## 流程总览

0. 环境检查：运行 scripts/check_environment.py
1. 生成 PPT：委托 hls-dissertation-ppt，产出 3:4 可编辑 .pptx
2. 暂停点：提醒用户上传豆包音频，等音频到位才继续
3. 合成视频：委托 hls-ppt2video 管线，产出 1080×1440 3:4 竖屏 MP4
4. 生成封面：提炼封面三要素 → scripts/render_cover.py → 1080×1440 PNG
5. 归档与校验：按目录规范落位，跑最终校验清单

## 阶段 0：环境检查（必做）

用 managed Python 运行：

```
python scripts/check_environment.py --capability generate_ppt --capability synthesize_video --capability render_cover
```

读输出中的 status 字段路由：

- ready：直接进入阶段 1。
- partial：进入流程，向用户说明受影响功能与降级方式。
- needs_setup：只展示缺失必需项的配置步骤（见 @references/setup-guide.md），等用户完成后重检。
- unavailable：区分故障原因，按降级矩阵处理。若唯一失败原因是 cli_probe/auth_probe 的 `probe_required`（存在性检查已通过、仅缺可信宿主版本探测），按 partial 继续，并在阶段内标注「版本/状态探测未验证」。其余情况按核心依赖不可用处理，无安全降级时停止。

> **`probe_required` 的实测处理方式（2026-08-28）**：本沙箱的 `check_environment.py` 对 ffmpeg-cli 固定报 `probe_required` + `unavailable`，但 ffmpeg/ffprobe 实际可用。Agent 应自己用 Bash 直接探测补齐证据，确认后按 partial 继续，不要据此判定环境不可用：
>
> ```
> where ffmpeg; where ffprobe; ffmpeg -version 2>&1 | head -2; ffprobe -version 2>&1 | head -2
> ```
>
> 实测返回 ffmpeg / ffprobe 8.1.2（WinGet Gyan 包路径），视频合成能力不受影响。

## 阶段 1：生成 PPT（委托 hls-dissertation-ppt）

1. 加载项目级 skill hls-dissertation-ppt，按其「环境 / 设计系统 / 三种内容原型 / 人设红线」执行。
2. 读口播稿，确定内容原型（独立技巧清单 / 流程步骤 / 概念辨析），复制对应模板脚本到本次工程。
3. 用 PptxGenJS 生成 3:4 竖版 .pptx（画布 7.5×10 英寸），输出到 素材/PPT/，文件名用中文主题。
4. 跑 PPT 校验：页数符合原型预期、sldSz 为 6858000×9144000（3:4）、人设残留（论文导师/留学生学术写作辅导）为 0。
5. 模型无法直接看渲染图，版式按坐标精算；交付前请用户在 PowerPoint/WPS 打开复核。

## 阶段 2：豆包音频暂停点（硬暂停，不得跳过）

1. 停止流水线，向用户说明：PPT 已就绪，请在豆包语音生成口播音频并上传到工作目录。
2. 给出音频命名规范：与 PPT 同名、扩展名 .mp3 或 .wav（如 Chapter1_七件事对齐_海乐思.mp3）。
3. 等用户确认音频已上传、文件存在且可读后，才进入阶段 3。
4. 音频缺失或用户暂不提供时：不合成视频，停留在阶段 2，交付 PPT 与暂停说明。

## 阶段 3：合成视频（委托 hls-ppt2video 管线）

1. 加载项目级 skill hls-ppt2video，按其「可靠管线 6 步」执行，目标比例 3:4（1080×1440）。
2. 工程目录用 ASCII 路径（如 E:/hls_video_work/），避免中文目录导致 ffmpeg 读写错位。
3. 步骤：ffmpeg 抽 16k 单声道 wav → faster-whisper 转录（.venv-video 环境，逐文件独立进程）→ Pillow 直渲 1080×1440 幻灯片 PNG → 按话题边界写 slide_timings.csv → ffmpeg concat 合成。
4. 编码参数：libx264、crf 18、yuv420p、输出侧 fps=30、setsar=1、aac 192k、-shortest。
5. 校验：ffprobe 时长 ≈ 音频时长；抽查 2–3 张复杂幻灯片 PNG，确认无文字溢出、无豆腐块。

## 阶段 4：生成外刊风封面

1. 加载 @references/cover-style.md 获取版式、调色板、字体与混排换行规范。
2. 从口播稿提炼封面三要素：kicker（纯英文标签）、title（中文主标题，≤ 16 字）、subtitle（一句卖点，≤ 24 字）。
3. 写 cover_content.json（kicker / title / subtitle / account 字段）。
4. 运行 scripts/render_cover.py --input cover_content.json --output <封面.png>。
5. 校验：1080×1440、无文字溢出、无豆腐块；模型可用 Read 工具看图确认。

## 阶段 5：归档与校验

- PPT：素材/PPT/<主题>.pptx
- 成片：课程视频/<主题>/<主题>_口播视频.mp4
- 封面：课程视频/<主题>/<主题>_封面.png

跑最终校验清单（见下），全部通过后向用户交付三件产物与使用说明。

## 校验清单（每次必做）

- [ ] PPT：3:4、页数符合原型、人设残留 0
- [ ] 视频：1080×1440、时长 ≈ 音频时长、无豆腐块
- [ ] 封面：1080×1440、三要素齐全、无溢出
- [ ] 三个产物同主题归档，路径可追溯

## 边界与停止条件

- 不在用户确认音频前合成视频。
- 不修改 hls-dissertation-ppt / hls-ppt2video 源 skill。
- 不发布内容、不虚构发布数据。
- 任一环节校验失败：停止该环节，向用户报告具体失败项，修复后重跑该环节。
- 核心依赖缺失且无降级：停止并说明需要补齐的条件。

## 已踩坑（继承自两个源 skill，勿重试）

- soffice 转 PDF / pdftoppm 在本沙箱不可用，幻灯片渲染走 Pillow 直渲。
- 中英混排必须拆分语言段渲染，同一 draw 调用混排会出豆腐块；封面标题用 wrap_mixed 逐 token 换行。
- ffmpeg concat 输入加 -r 会导致 duration 失效，只在输出 -vf 里用 fps=30。
- 转录不要在同一 Python 进程循环复用模型，逐文件独立进程。
- ffprobe 路径用独立常量，不用字符串替换 ffmpeg 路径推导。
- slide_timings.csv 若带 UTF-8 BOM，csv.DictReader 会 KeyError，先剥 BOM。
