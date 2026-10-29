# 资源与运行

核验与下载日期：2026-09-11。资源记录及SHA256见`assets/manifest.json`，font许可随文件保留。下列素材均按实际状态列出，不代表大学对海乐思的授权。

| 资源 | 状态与使用 |
| --- | --- |
| [Brand Book](https://www.monash.edu/brandbook) | 在线规范来源，细节在brand-rules.md所链页面 |
| [官方Explorer](https://explorer.monash.edu/campus)反白Logo | 已取得`assets/media/monash-reverse.svg`；直接来自官方站点，深蓝底使用，不重着色 |
| [Monash Lens](https://lens.monash.edu/)单色Logo | 已取得`assets/media/monash-mono.svg`；官方站点原文件，浅底需要单色版本时使用 |
| 蓝盾黑字首选Logo | 品牌站直链访问受限；未取得并未仿造。按需从Logo页面取得后更新manifest，不把已有单色版称作蓝盾版 |
| [M源文件](https://www.monash.edu/brandbook/brand-elements/the-m-device) | 规范可读，未取得可下载源文件。示例不使用仿造M |
| [模板入口](https://www.monash.edu/brandbook/templates)与Bynder | 模板下载当前未验证可用；Bynder为员工素材系统，未登录、未下载。无需因库不可用而阻塞其他制作 |
| [真实课堂活动](https://lens.monash.edu/fake-blood-escape-rooms-and-physiology-a-new-model-for-student-engagement/) | 已取得`assets/media/classroom-discussion.jpg`用于摄影演示，原文为生理学课堂活动。不是通用全部课程实景；以后按任务换图 |
| Noto Sans SC | 从已有伯明翰Skill中复制同一Google Fonts官方字库与OFL，中文适配 |
| Roboto | 从Google Fonts官方仓库取得可变字体与OFL，用于数字演示 |
| Helvetica Neue | 商业授权字体，未随包分发；本地有授权时使用，缺少时按官网用Arial替代并记录 |
| 海乐思Logo | 工作区`共享资源/品牌/海乐思/海乐思-logo-原图.png`；模板相对引用，原色完整保留 |

## 运行

使用本地Node及Playwright：`node scripts/render.mjs --html <绝对或相对HTML路径> --output <全新输出目录>`。默认从Codex bundled runtime定位Playwright，可通过`CODEX_NODE_MODULES`指定node_modules；默认浏览器为本机Edge。字体通过`@font-face`读取随包文件，不安装系统字体。

脚本验证页面尺寸、元素边界、字体加载和图片解码；失败时不产出半套图片。不能检测语义、人物裁切、Logo识别和所有文字遮挡，必须逐页目检。输出中的`render-report.json`是审核记录，正式图文交付可移入审核目录。

## 素材缺失与更新

主站直链403、浏览器工具连接失败以及员工库不可访问已在本次取材中遇到。可从其他可靠官方站点获取同一用途的原文件并记录实际来源；不绕过登录、不生成Logo、不把低清截图说成矢量源文件。无法取得的资源明确列出，继续制作不依赖它的部分。

在来源与用途吻合时使用已下载素材；新任务不需要每次重下同一字体或Logo。用户要求最新规范、来源冲突或链接失效时再核验并更新日期。图片的当前下载位置可能是官方CMS的CDN，manifest须同时保存官网内容页及图片直链。
