# 制作与配置

## 素材与配音

素材按台词语义找，不按文件夹随意轮换。记录源路径、入点、出点、焦点和用途；先看实际片段，确认人物动作、横竖裁切和时长。优先短的本地MP4派生片段，避免把数小时视频整段装入浏览器内存。共享素材只读引用；派生片段写入本期制作目录。

```powershell
ffmpeg -i "source.mp4" -ss 12 -t 8 -an -c:v libx264 -pix_fmt yuv420p "clip.mp4"
```

ASR生成草稿后核对专有词及边界；字幕只覆盖实际发声内容。画面重点可以简写，但不能偷换意思。句式、CTA和资料名称来自本期输入，不默认继承“评论区拿一份”。素材自带声音默认不混入；配音从0秒入轨。需要配乐时先生成独立mix.wav再配置为audio，并另测人声同步。

## 参数协议

`config.json`中的所有文件路径相对于该JSON目录。渲染脚本把指定文件映射到本机HTTP白名单，不要求文件必须位于模板目录，也不扫描整个工作区。

| 字段 | 含义 |
|---|---|
| width / height / fps / duration | 输出宽高、帧率、总时长；偶数宽高，整帧时长；starter仅9:16 |
| audio | 配音或预混音路径；时长不得超过画面，短于画面时尾部静音补齐 |
| font_family | Windows默认Microsoft YaHei；其他系统应指定可用中文字体 |
| font_file | 可选本地字体路径，加载后使用OverlayFont；字体授权由素材来源记录 |
| media[key].file | 本地视频路径；不是图片占位符 |
| media[key].focus_x / focus_y | 0至1的裁切焦点，0为左/上，1为右/下 |
| scenes | 连续覆盖0至duration，start/end是全片绝对秒；id唯一 |
| scene.asset / offset / loop | 素材key、源片入点、是否明确允许循环；默认不循环，片段不足会报错 |
| scene.chapter | 可选顶部章节小标签 |
| panel.x/y/w/h | 面板坐标，按1080×1920设计坐标；输出缩放时自动等比缩放 |
| panel.opacity | 面板不透明度，默认0.62 |
| panel.active_only | true时只高亮当前已出现行，先前行降亮度 |
| panel.rows | text、at（场景内秒）、size（默认76）、color、line_height，以及可选mark=underline或strike |
| motion_roi | 实际输出像素的[x,y,w,h]，不使用设计坐标；不能覆盖文字/字幕/动态批注 |
| captions | [全片起点,全片终点,文字]数组；不重叠，允许留白；支持换行，最多两行 |

面板不自动无限缩小字体或挤压长句；文字越宽、面板越界、超过两行字幕会报错。优先缩短画面重点或拆分场景，读字幕不依赖缩成小字。字体和自定义布局由当前工程的engine.js控制。

本机已安装Edge或Chrome时，渲染参数可加`--channel msedge`或`--channel chrome`，使用独立无头浏览器进程。也可安装Playwright自带Chromium（首次缺失时）：

```powershell
uv run --with playwright python -m playwright install chromium
```

`--check`仅检查输入与配置，不证明版式正确。`--stills`会采每段早期、末期及行出现后状态，实际运行Canvas才发现文字溢出。`--full`输出`_captioned.mp4`、`_clean.mp4`和`.srt`；`--output`是带版本的文件名前缀，已存在时拒绝覆盖。若只输出stills后再出full，使用新前缀。

## 确定性视频取帧

模板先fetch短片为Blob URL，再加载video。每帧先await prepare(t)，完成seek后核对actual currentTime与目标误差<=0.04秒，再绘制Canvas。不要删掉这段断言；原工程曾发生seeked成功但currentTime仍为0，整片背景冻结。

动画全部来自绝对时间，不依赖requestAnimationFrame累计状态。start/end和行级at应依据新配音重排。0.22秒入场和0.62不透明度是已用默认值，可调整；23镜头、四问数量和76.2秒均不是模板限制。
