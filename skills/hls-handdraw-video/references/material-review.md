# 素材审核与去重

出齐素材 → Agent目检和去重 → 展示编号总览、单图与台词对应 → **结束当前轮等用户审核** → 全部当前素材获明确认可 → 配音、动画与成片。新素材或裁切变化返回审核；无超时、无默认批准。

## 清单与确认

工程中保存 `design/materials.json`，每张有稳定的 `asset_id`、项目相对 `source`、图集区域 `crop`（独立图片为null）。同一素材的路径别名、同图不同蒙版不能另起ID。不同图集单元分别登记，不能把整张图集当一份素材反复使用。

```json
{"assets":[{"asset_id":"background-maze","source":"inputs/atlas.png","crop":[0,0,444,444]}]}
```

清理元数据、检查实际图片后运行副本：

```powershell
python -X utf8 <runtime>/scripts/material_gate.py snapshot <JOB>
```

snapshot绑定当前源文件SHA-256及裁切后的RGBA像素SHA-256，生成 `design/materials-approval.json` 的pending记录，不批准、不开始制作。展示这版完整清单后结束当前轮；确认前不能生成新增旁白。用户确认后由Agent依据真实消息填写：

```json
{"status":"approved","materials_sha256":"当前清单哈希","user_quote":"用户实际确认全部素材可用的原话","evidence":"这次用户消息的定位依据","paused":false}
```

schema示例不是用户授权；不得把本轮制定规则的消息、此前画风确认或Agent的PASS写成素材认可。部分认可、沉默或暂停都不能填写approved。更改素材后再次snapshot，它会清除旧确认并回到pending。

## 视频使用登记

每个illustration action显式写 `asset_id`，指向审核清单中的图片/图集单元；保留原来的drawing_plan_id，两者职责不同。一个素材只安排一个illustration事件，按部位描线与填色在该事件内完成，不为长口播重复插画。长段落可在同一连续场景累积新文字或使用已审核的其他新图。

`job.json` 的 `cover.material_asset_ids` 必须列出视频内片头封面合成用了哪些清单素材；纯文字封面用空数组。独立的平台封面不在视频时间轴里，不计次数。不得漏报封面所用图以绕过去重。

```json
{"cover":{"source":"inputs/cover.png","seconds":1,"material_asset_ids":[]}}
```

新增配音、构建、渲染与交付前运行：

```powershell
python -X utf8 <runtime>/scripts/material_gate.py check <JOB>
```

适配的handdraw_video入口对build/render/verify/finalize自动执行同样检查；已有旧副本没有此门槛，未来继续制作须更新副本，不能视为豁免。旧完成视频不因升级自动改动。

## 检查范围

脚本检查：确认与当前整套清单绑定、文件/区域未变、每个事件对应批准素材、素材ID不重复、相同解码像素不重复（包括改名或重新编码的副本）、同源的大幅重叠裁切不重复，以及片头封面与正文的重复。图集不同单元可分别使用。

Agent还须实际看图，检查缩放、旋转、轻微重绘或局部改字等实质相同的图，不能把像素不同误当成内容不同。脚本不能识别用户意图或证明确认原话真实；它只拦截缺记录、失配与可确定的重复。
