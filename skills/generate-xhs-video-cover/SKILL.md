---
name: generate-xhs-video-cover
description: 从真人口播视频、成片或静态人物图中选取封面主体，结合口播稿、字幕或主题文档提炼标题与 4–5 个内容关键词，参考已确认的暖米白撕纸拼贴系列，生成并验证 1080×1440 的小红书 3:4 封面。用户要求“基于这个视频做封面”“再做一张同系列封面”“从成片生成小红书封面”或“制作真人口播 3:4 封面”时使用。
---

# 生成小红书真人口播封面

把项目内的口播视频和文稿转为可追溯、可复用、未发布的 3:4 小红书封面。最终文件必须进入对应内容项目，不覆盖旧版本。

## 输入与边界

至少取得：

- 一个内容项目目录，且已有 `CODEX.md` 和 `项目索引.md`。
- 一个真人口播视频、成片或静态人物图。
- 一份口播稿、字幕或主题文档，用于确定封面文字。

优先使用该项目已验证的权威成片；若没有成片，再使用基础素材包或原始视频。不要从文件名猜内容。不要删除、覆盖或发布文件。

开始业务处理前：

1. 读取根目录 `CODEX.md`、Vault 启动记忆、项目 `CODEX.md` 和 `项目索引.md`。
2. 在 `项目索引.md` 中登记当前负责人、本轮封面目标和未发布边界。
3. 检查目标封面文件是否已存在；已存在时递增 `v2`、`v3`，不得覆盖。

## 工作流

### 1. 提炼封面信息

从文稿中提取：

- 一个明确任务场景或痛点。
- 一个两行主标题。
- 一个受众或场景小标签。
- 一个橙色行动/判断标签。
- 4–5 个能代表正文结构的关键词。

遵守以下文字合同：

- 主标题最多两行；中文每行优先 4–8 字，英文术语可单独占一行。
- 小标签和橙色标签各一个。
- 关键词胶囊最多 5 个，每个优先 2–6 个汉字；英文术语保持标准大小写。
- 所有可见文字都必须来自内容事实，不添加无法验证的承诺，不使用代写暗示。
- `Dissertation`、`Research Gap`、`Literature Review` 等术语逐字母核对。

### 2. 选取人物帧

视频输入先生成六宫格。脚本产物文件名使用 ASCII，避免 Windows PowerShell 与 ffmpeg 之间传递中文文件名时发生编码错误：

```powershell
powershell -ExecutionPolicy Bypass -File ".codex/skills/generate-xhs-video-cover/scripts/extract-cover-frame.ps1" `
  -VideoPath "<video>" `
  -ReviewDir "<project>/04_审核记录" `
  -Prefix "<topic>" `
  -Mode ContactSheet
```

视觉检查六帧后，选择：

- 眼睛自然睁开、直视或接近直视镜头。
- 嘴型自然，不处于夸张闭眼或大幅运动模糊状态。
- 手势有讲解感，但不遮住眼睛、鼻子或整张脸。
- 上半身和项目中有识别度的真实物件尽量完整。
- 右侧排人物时，脸和手仍能避开左侧标题区。

再抽取指定时刻：

```powershell
powershell -ExecutionPolicy Bypass -File ".codex/skills/generate-xhs-video-cover/scripts/extract-cover-frame.ps1" `
  -VideoPath "<video>" `
  -ReviewDir "<project>/04_审核记录" `
  -Prefix "<topic>" `
  -Mode Still `
  -ChosenTimeSeconds <seconds>
```

静态人物图可跳过抽帧，但必须先视觉检查。

### 3. 选择版式参考

从用户明确指定的参考图或已验证同系列封面中选一张。输入角色必须写清：

- 图 1：人物与真实场景主体。
- 图 2：仅作为排版、层级、质感和配色参考。

不得把参考图人物混入新封面，也不得复制参考图文案。详细视觉系统和提示词骨架见 [references/visual-system.md](references/visual-system.md)。

### 4. 生成封面

使用内置图像生成工具；若当前环境提供 `imagegen` Skill，先按其要求加载和执行。

提示词必须包含：

- `Use case: ads-marketing`
- 画布为小红书竖版 3:4。
- 人物身份、服装、眼镜、手势和真实物件的不变量。
- 左上大标题、左下关键词胶囊、人物右侧约 50%–55%。
- 所有可见文字的逐字文本。
- 不增加人物、不改脸、不加 Logo、水印或代写暗示。

生成后逐字检查标题、英文术语和关键词。若只有一个局部错误，进行单点迭代并重复所有人物不变量；不要无目标地重写整份提示词。

### 5. 标准化输出

生成图必须先接近 3:4；比例偏差超过 0.01 时返回生成步骤，禁止强行拉伸。

```powershell
powershell -ExecutionPolicy Bypass -File ".codex/skills/generate-xhs-video-cover/scripts/normalize-cover.ps1" `
  -InputPath "<generated-image>" `
  -OutputPath "<project>/05_最终交付/小红书/<topic>-小红书封面-v1.png"
```

脚本输出最终尺寸、字节数和 SHA-256。最终权威文件只放在 `05_最终交付/小红书/`。

### 6. 归档与收尾

在 `03_制作工程/` 保存 `<topic>-小红书封面-vN-生成说明.md`，至少记录：

- 内容依据、人物来源、选帧记录、人物帧和风格参考。
- 最终完整提示词。
- 最终路径、尺寸、SHA-256 和视觉检查结论。

更新 `项目索引.md` 的状态、最终交付、验证证据、下一步和未发布状态。任务产生可继承结果时，按根目录 `CODEX.md` 写回 Vault。

## 验收

完成前必须同时满足：

- PNG 为 1080×1440，比例为 3:4。
- 主标题在手机缩略图下仍可辨认。
- 所有中文、数字和英文逐字正确。
- 人物身份、眼镜、服装、手势和关键真实物件没有异常漂移。
- 标题、关键词、箭头不遮挡人物眼睛和核心手势。
- 画面没有额外人物、Logo、水印、多余小字或代写暗示。
- 最终文件、生成说明和 `项目索引.md` 互相引用一致。
- 未执行公开发布。

## 资源

- `scripts/extract-cover-frame.ps1`：生成六宫格或抽取指定时刻人物帧。
- `scripts/normalize-cover.ps1`：验证比例，标准化为 1080×1440 PNG，并输出哈希。
- `references/visual-system.md`：同系列视觉规范、文案规则、参考路径和提示词骨架。
