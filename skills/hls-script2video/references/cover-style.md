# 外刊风视频封面版式规范

供 scripts/render_cover.py 使用。视觉继承 Discussion 外刊风图文系列（cream paper + olive 报头细线 + 卡片骨架），报头统一为 HLS STUDY ABROAD。

## 画布与调色板

- 画布：1080×1440（3:4，小红书原生）。
- 色板：PAPER #F6F2E8（底）、INK #11110F（主文字）、GRAY #85827A（辅助）、OLIVE #7E8768（规则线与 kicker）、CREAM #FBF7EE（浅卡）、BLUE #8AAFC0、BRICK #B8654B、YELLOW #D6B25E。

## 字体

- CN_SERIF：C:/Windows/Fonts/NotoSerifSC-VF.ttf（中文标题，Black 字重）。
- CN_SANS：C:/Windows/Fonts/NotoSansSC-VF.ttf（中文正文）。
- EN_SERIF：C:/Windows/Fonts/times.ttf（英文与数字）。

## 版式坐标（自上而下）

1. masthead：HLS STUDY ABROAD（EN_SERIF 27pt，INK），左上 (72,46)。
2. 右上角：ACADEMIC WRITING（EN_SERIF 18pt，GRAY），右对齐 (1008,52)。
3. olive 细线：(72,96)→(1008,96)，宽 2。
4. kicker：纯英文标签（EN_SERIF 22pt，OLIVE），(72,140)；空则不画。
5. title：CN_SERIF Black 64pt，wrap_mixed 换行，可用宽 936，行距 gap 10，起点 (72,210)。
6. olive 短划线：(72, y+20)→(190, y+20)，宽 5，y 为标题末行底部。
7. subtitle：CN_SANS 30pt，INK，wrap_mixed 换行，可用宽 936，gap 10。
8. 底部 INK 圆角条：(104,1230,976,1330)，radius 24；account 白字（CN_SERIF Black 34pt）居中 (540,1280)。

## 封面三要素提炼规则

- kicker：纯英文、全大写、长度 ≤ 40 字符，如 DISSERTATION WRITING / INTRODUCTION。
- title：中文主标题，≤ 16 字，直给核心卖点，不以问号结尾。
- subtitle：一句中文卖点或行动指引，≤ 24 字。
- account：默认 Dissertation写作技巧 · 拆解实操。

## 混排换行规则（wrap_mixed）

- 拉丁 token（字母数字串）整体换行，不被按字符拆开。
- CJK 字符逐字换行。
- 标点依附前一 token 后换行。
- 渲染时每个 draw 调用只放单一语言段，避免 CJK 豆腐块。
