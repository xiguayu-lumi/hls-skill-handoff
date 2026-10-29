# 制作说明

## 运行环境

画面沿用本地 Remotion 4.0.506 / React 18.3.1，配音零点通过 FFmpeg 合成。Python 音频脚本依赖 numpy、scipy；ASR 另需 faster-whisper 和本地模型。后续用户只交输入，AI 执行下面命令。

先查本地已安装依赖。`REMOTION_DEPS` 指向带 `package.json` 和 `node_modules` 的目录；留空则使用当前新工程的 `node_modules`。`REMOTION_BROWSER` 可指向已安装的 Chrome headless shell；未设置时用 Remotion 支持的浏览器获取流程。缺少 JS 依赖才在新工程执行 `npm install`，版本已固定在 `template/package.json`。不要把 node_modules、模型或浏览器塞进素材包。

2026-09-29 本机验证的复用位置（仅环境参考，代码不绑定它们）：

- Node：`C:/Users/lgy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`。
- Remotion 依赖：工作区 `素材/视频工程/remotion_ch1/`。
- Browser：`C:/Users/lgy/.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7928.2/chrome-headless-shell-win64/chrome-headless-shell.exe`。
- 音频脚本用含 numpy/scipy 的 Python；ASR 用工作区 `.venv-video/Scripts/python.exe`。先检查可用性，不把路径当作跨电脑保证。

## 新建与渲染

以下 PowerShell 中 `$toastPack` 指本包绝对路径，`$toastProject` 指当期 `03_制作工程`；先按工作区规则建立当期根目录、CODEX 与项目索引。目标工程必须尚不存在，初始化不会覆盖旧工程。

```powershell
python "$toastPack/scripts/project.py" init "$toastProject" --voice "新配音绝对路径.mp3" --srt "新字幕绝对路径.srt"
# 没有 SRT 就省略 --srt，用转录脚本取得时间证据，然后由 AI 校正并写入 video.json。
# ASR Python：使用装有 faster-whisper 和缓存模型的环境。
& $toastAsrPython "$toastPack/scripts/transcribe.py" "新配音绝对路径.mp3" "$toastProject/asr-draft.json"
```

AI 读取新稿和时间证据，填写 `video.json` 的 scenes/subtitles/effects。空模板不会直接生成旧视频。保留语气和资料钩子，用户没要求改稿时不改写。

```powershell
python "$toastPack/scripts/project.py" prepare "$toastProject"
python "$toastPack/scripts/audio.py" "$toastProject"
& $toastNode "$toastProject/render.cjs" --stills "1,8,15"
# 看完效果帧再渲染；新版本文件名，避免覆盖已交付视频。
& $toastNode "$toastProject/render.cjs" "当期项目/05_最终交付/吐司视频_v1.mp4"
python "$toastPack/scripts/verify.py" "$toastProject" "当期项目/05_最终交付/吐司视频_v1.mp4"
```

`prepare` 重算配音长度并向上取整到 30fps，验证连续分镜、字幕重叠、缺素材和表情名称，预解码使用到的录屏片段。录屏原声不参与成片。录屏比镜头短时保持最后一帧；需要其他片段用 `recordStart`。再次 prepare 会替换本项目相应录屏帧缓存。

`audio.py` 根据新时长重新生成纯配乐，按新配音进行平滑避让与响度校准，输出 mix.wav / mix-report.json。不要复制旧片含口播混音。`render.cjs` 渲染后自动合成 mix.wav 并清理成功合成后的静音中间视频。

字幕导出：prepare 自动将配置中的 cues 写为工程内 `subtitles.srt`；交付时复制到本期最终交付目录。SRT 时间保留毫秒，不另做一套估时。

## video.json

所有媒体路径相对于新工程 `public/`，用 `/`。所有时间单位为秒。**场景 start/end 和字幕 start/end 是全片绝对时间；场景内 rows.at、poses.at、accentAt、footerAt 是相对该镜头开始的时间。** 音效 effects.at 是全片时间。

顶层：

| 字段 | 意义 |
|---|---|
| label | 左上角账号/栏目名；避免残留旧期栏目 |
| voice | 新口播音频路径，init 自动设置 |
| music | `generated` 为本地原创 108 BPM，`null` 关闭，或自选音乐路径 |
| musicBelowVoiceDb | 默认 20；实际测量结果见混音记录 |
| scenes | 按开始时间排序、覆盖整段语音的场景 |
| subtitles | `{start,end,text}`；按自然语义断句，不切碎英文单词 |
| effects | `{at,file,gain}`；如 `assets/audio/paper.wav` 或 `tick.wav`，默认 gain .2 |
| durationInFrames / fps / width / height | prepare 写入；模板固定 1080p/30fps，时长来自新音频 |

场景公共字段：`start/end/bg/title` 必需，`bg` 例如 `assets/scenes/library.jpg`；`eyebrow` 为上方小标题，`toast` 为初始表情，`side` 可为 left/right，`poses` 为 `[{at,pose}]`。`size` 可调场景主标题字号；标题换行用 `\n`。

| mode | 使用方式 |
|---|---|
| scene（默认） | 实景 + 大字；可选 accent / accentAt |
| versus | 实景大字区分两个概念：title 为第一项，rows 一行 main 为第二项 |
| topics | 实景 + 2×2 重点列表，最多四行 rows |
| paper | 完整便签本 + 同源模糊背景；最多三行 rows，每行 main / sub / at |
| classification | 同便签本，两张并排卡；rows 恰好两项，可用 label / main / sub / at |
| record | 真实资料录屏；record 为视频路径，recordStart 默认为 0；title 置左，录屏置右；可用 footer / footerAt |

paper / classification 也可放 footer / footerAt，但避免三行都带副标题时再堆尾注。`recordDir/recordFrames` 由 prepare 写入，不手改。表情可选 toast、deadpan、question、panic、idea、proud、pointer、startled、thinking、wink。

新配置只含当期内容，Skill 的空 video.json 不含上一期口播和时间线。完整分镜表可放本期 Markdown，真正渲染的数据以 video.json 为准。

## 风格与人工检查

- 米白纸 `#f5e9c9`、深墨 `#303141`、锈红 `#a84b35`、橄榄 `#667047`；有包边、线圈与纸纹，四边可见。
- 真实场景轻推近、暖暗；方法背景模糊 15px。大标题通常 100–135px，纸页标题 57px、重点 43px、补充 30px；根据真实长度主动分镜，不能为了塞字改掉句意。
- 常规字幕 51px、距底 115px；进度线距底 18px、mini 吐司 68px。录屏已预留字幕空间。角色在方法画面缩小，放置于纸页两侧。
- 抽看开头、中段、结尾，所有模式各一张，最长字幕、角色换位和重点显字的前后帧；核对身体、纸页轮廓及完整本子没有意外裁切。
- ASR 曾漏掉片头一段。默认关闭 VAD 与上一段条件提示，仍要看首尾时间并听音；缺段只重转对应片段并校正偏移。不要对 ASR 拼接点机械加标点。
- 录屏随机寻帧曾失败，因此只预解码需要的片段到当前工程帧缓存。换稿重建；缓存不进入共享包。
- 输出音轨要对原配音测量偏移；不要把旧工具的 2048 采样补偿沿用到新工程。当前流程以静音画面+FFmpeg 零点混音避免该偏移。

## 复用范围

每期通常只需要更换稿件、配音、video.json 及资料录屏；角色、背景、纸本、文字动画、进度条、音乐生成算法均复用。风格模板目前以静态真实场景为主；素材包附源 B-roll，可用它们重新选帧。要让实景连续运动时，再按具体片段扩展背景层并验证，不应为了这次封装重做完整剪辑系统。
