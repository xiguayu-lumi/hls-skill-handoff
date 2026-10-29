# HLS 论文拆解 HTML Skill

把一篇有文本层的学术 PDF 转成三类可核查成果：

- 证据地图：每条中文结论都能追到原文页码、摘录和数字。
- HLS 品牌论文带读：固定 1080×1440、离线可打开、键盘翻页，事实页同时呈现 PDF 原文截图与中文解释。
- 原始图表带读：保留论文图表，不重绘，并在旁边解释方向、数值与证据边界。
- 发布与质检文件：逐页 PNG、2160×1440 双页接触表，以及证据、语言、视觉 QA 报告。

它的原理很直接：Codex 负责理解论文和组织叙事，脚本负责 PDF 提取、Schema 校验、HTML 渲染、浏览器截图与尺寸检查。这样既保留语义判断，也避免“计划写了 15 页，实际只生成 5 页”这类不可见失败。

## 本地安装

本项目当前是独立候选包，没有写入个人 Codex Skill 目录，也没有安装任何全局依赖。

在 PowerShell 中进入项目目录：

```powershell
cd E:\论文拆解\hls-paper-to-academic-html
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
npm install
```

Python 包和 Node 包都只安装在当前目录的 `.venv` 与 `node_modules` 中。浏览器截图优先调用电脑已有的 Edge 或 Chrome，不需要另装全局浏览器。

## 全局 Skill 安装

从源码项目执行：

```powershell
.\.venv\Scripts\python.exe scripts\package_skill.py C:\Users\lgy\.codex\skills\hls-paper-to-academic-html
cd C:\Users\lgy\.codex\skills\hls-paper-to-academic-html
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
npm ci
```

打包脚本采用运行文件允许清单，只复制 `SKILL.md`、规则、品牌资产、Python 实现、脚本、模板、Schema 和参考资料；不会复制 `.git`、源码项目的 `.venv`、`node_modules`、测试、评测记录、真实论文案例或缓存。运行依赖安装在 Skill 自己的 `.venv` 与 `node_modules` 中，不写入系统 Python 或全局 npm。

如果目标目录已经存在，脚本会停止并保留原目录，不会静默覆盖。全局包中的 `release-manifest.json` 记录全部发布文件、大小与 SHA-256，可用于核对安装完整性。

## 调用方式

作为 Codex Skill 使用时：

```text
$hls-paper-to-academic-html D:\资料\paper.pdf
受众是中文普通读者，重点讲研究方法、主要发现与局限，控制在 15 页。
```

如果尚未复制到个人 Skill 目录，也可以让 Codex读取本项目的 `SKILL.md`，再按其中流程执行。

底层命令的最短路径：

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py input\paper.pdf --work-dir work
.\.venv\Scripts\python.exe scripts\extract_pdf.py input\paper.pdf --work-dir work
.\.venv\Scripts\python.exe scripts\validate_evidence.py work\evidence-map.json --paper work\paper.md
.\.venv\Scripts\python.exe scripts\extract_source_assets.py input\paper.pdf work\source-assets.json --output-dir output\assets\source
.\.venv\Scripts\python.exe scripts\validate_deck.py output\deck.json --evidence work\evidence-map.json --output-root output
.\.venv\Scripts\python.exe scripts\render_html.py output\deck.json --output output\index.html
node scripts\visual-dom-check.mjs output\index.html --report output\qa-dom-report.json
node scripts\screenshot.mjs output\index.html output
```

## 默认内容结构

默认输出 5 页核心证据速读版：封面、研究问题与设计、研究 1、研究 2、结论与边界。5 页以内不设置目录；超过 5 页时才使用 `agenda-reading`。普通事实页使用 `source-reading`，图表页使用 `figure-reading`。

原理很简单：左侧图片让读者能核对论文原话，右侧中文翻译降低阅读门槛；遇到图表时保留作者原图，避免重绘时改变坐标、误差线或统计含义。

竖版页面采用固定品牌蓝章节横幅和暖纸白底色。原文截图放入纸感白卡，中文解释使用荧光笔重点、无底框竖线批注和“一句话记住”收束，适配手机端连续阅读。

## 两个审阅点

### 内容审阅点

在 `work/evidence-map.json` 与 `work/deck-plan.json` 完成后、正式渲染前进行。检查：

- 研究问题和论文类型是否识别正确。
- 实验因果与观察相关是否分开措辞。
- 非显著、方向相反和不支持主命题的结果是否保留。
- 每页的 `E###` 证据 ID、页码和原文摘录是否齐全。

配置 `pause_before_render=false` 时允许自动通过这一节点，但验证器仍必须通过。

### 视觉审阅点

先查看封面、研究设计、核心结果和限制四类关键页；确认后再渲染全套。至少检查：

- Logo 比例与透明背景。
- 中文是否清楚、标题是否断得自然。
- 证据脚注是否可见。
- 是否有溢出、截断、资源缺失或空白页。

## 目录结构

```text
hls-paper-to-academic-html/
├─ SKILL.md                    # Codex 执行规则
├─ DESIGN.md                   # HLS 视觉规范
├─ schemas/                    # 证据、页面、原文素材等 JSON 数据契约
├─ references/                 # 论文分析、证据、叙事与页面规则
├─ scripts/                    # 可重复运行的命令
├─ templates/                  # 离线 HTML 模板
├─ hls_academic/               # Python 实现
├─ tests/                      # 单元、契约与真实论文烟雾测试
└─ examples/smoke-test/
   ├─ input/                   # 受众与配置
   ├─ work/                    # 全文、证据地图、角度、页面计划
   └─ output/                  # HTML、PNG、接触表、manifest、QA
```

每次真实运行也使用 `input/`、`work/`、`output/` 三层；原 PDF 不被覆盖。

## 失败条件

以下情况必须停止，不允许“先生成再说”：

- PDF 缺失、损坏、加密或没有可用文本层。
- 关键结论没有证据 ID、页码或原文摘录。
- 观察性研究被写成确定因果。
- 页面引用不存在的文件或证据。
- HTML 有溢出、图片缺失，或截图数量与页面数不一致。

复杂公式或表格可以明确降级为原图加中文解释，但必须写入 QA 报告。

## 烟雾测试

项目附带一篇 7 页真实论文：

```powershell
npm run smoke
```

命令会依次验证 23 条证据、5 页 deck、浏览器 DOM、5 张 1080×1440 PNG、3 张接触表和三类 QA 报告。示例成品入口：

```text
examples/smoke-test/output/index.html
```

完整验证：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\validate_skill.py .
npm test
npm run smoke
```

## 已知限制

- 目前只接受有文本层的 PDF；扫描件 OCR 没有自动开启。
- 元数据依赖 PDF 内嵌信息，作者列表不完整时需要人工核对。
- 图表候选能定位；默认采用原始图表或 PDF 裁剪，不擅自重绘。
- 自动语言检查能抓因果越界和禁止措辞，但不能替代学术判断。
- 全局发布包不包含源码仓库的测试和真实论文烟雾案例；完整回归测试仍从源码项目执行。
