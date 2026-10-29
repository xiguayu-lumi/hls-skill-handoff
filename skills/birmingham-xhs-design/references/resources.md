# 资源索引

页面与入口核验日期：2026-09-10。除随包字体外，仅核对官网列出的入口，未逐一下载模板。字体文件的实际来源、字节数及 SHA256 见 `assets/fonts/manifest.json`；未收录的资源不代表已下载或已获使用权。

| 资源 | 入口与使用方式 |
| --- | --- |
| 品牌总览 | https://brand.birmingham.ac.uk/essentials/ |
| 配色 | https://brand.birmingham.ac.uk/guidelines/colour/ |
| 线条与构图 | https://brand.birmingham.ac.uk/guidelines/brand-system/ |
| 模板库 | https://brand.birmingham.ac.uk/downloads/ ，有 Social Media Templates 分类；按实际访问情况使用，未将整库打包 |
| Manrope 官方下载 | https://brand.birmingham.ac.uk/wp-content/uploads/2023/07/Manrope.zip |
| Noto Sans SC | https://fonts.google.com/noto/specimen/Noto+Sans+SC |
| 字体可分发源 | Google Fonts 官方仓库 https://github.com/google/fonts/tree/main/ofl/manrope 与 https://github.com/google/fonts/tree/main/ofl/notosanssc ；随包保留各自 OFL.txt |
| Larken | 官网说明通过 Adobe Fonts 或 Ellen Luff 获取。未购买、未收录；用户本地已有授权时可使用 |
| 大学主 Logo | https://brand.birmingham.ac.uk/wp-content/uploads/2024/01/Primary_Logo.zip ，按需下载原文件；本 Skill 不自制校徽 |
| 主色文档 | https://brand.birmingham.ac.uk/wp-content/uploads/2023/07/UoB_Primary_Colour_Pallete.docx |
| 辅助色文档 | https://brand.birmingham.ac.uk/wp-content/uploads/2023/10/UoB_Secondary_Colour_Palette.docx |
| 海乐思署名 | 工作区根目录 `共享资源/品牌/海乐思/海乐思-logo-原图.png`，唯一权威资产，模板通过相对路径引用 |

字体仅供排版加载，不执行系统级安装。先核对实际字体 family 名称及字重；Noto Sans SC 随包使用可变字体，Manrope 也使用 Google Fonts 可变字体。正常生产不必每次联网；用户要求最新规则、发现冲突或入口失效时重新查阅官方页面并更新核验日期。

Larken 替代记录示例：`英文展示标题使用 Times New Roman；未使用 Larken，属于项目适配。中文 Noto Sans SC / 英文正文 Manrope 已加载。`
