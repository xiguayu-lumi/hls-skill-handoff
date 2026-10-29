# 上游 1.4.1 兼容说明

2026-10-26 更新。上游：https://github.com/threerocks/sweety-handdraw-video ，提交 `3ae9b78d22af907afe70c1af4b8dc677f883bae1`，包版本 1.4.1；此前为 1.2.3。

## 生效的集成顺序

1. 用户选定画风后，按完整稿件规划开场、presentation.mode、storyboard 和绘制计划。审核前预算标为估算；不虚构音频时间戳。
2. 生成并检查全部素材，展示编号总览及单图，结束当前轮等待用户确认。
3. 用户确认后，沿用固定声线通过适配的 voxcpm_voice.py 整篇生成，或读取已有完整录音。不得改用上游语义分段合成替换此默认。通过 align.py 按真实录音生成时间戳；运行声音门槛，不用估算冒充实测。
4. 按实际录音运行 storyboard_lint.py JOB --budget，补齐 composition、boards、visual_group 等新格式。若素材需调整，回到整套素材审核。
5. 新上游标准汉字笔顺、语义部位间抬笔、空间顺序上色、画面密度、线稿门槛、字幕同步与避让继续执行。板书累积显示不代表可重复登记素材事件。
6. 用适配副本 build/render/verify/finalize；reject 可记录用户拒绝。连续播放、试听分别如实记录，未执行填 not_done。

## 本地优先项

Router真实预览、明确画风选择、整套素材审核、素材仅用一次、整篇旁白、固定参考声线、微软雅黑Bold正文、64px思源宋体Medium加粗黑字字幕和默认无BGM继续生效。不能运行 production_options.py --apply 覆盖这些已确认的设置。自定义画风按当前 scripts/style_choice.py 的数据校验填写完整配方。

新配音后仍须执行声音门槛和全文对齐；整篇适配不代表声音已经通过。固定参考也接受新版 voice_reference 的哈希及声音检查，失败时报告原因，不放宽检查或悄悄换声。

## 版本与已有工程

patches/manifest.json 绑定1.4.1原文件及合并补丁。prepare_runtime.py继续拒绝依赖漂移和覆盖已有runtime。旧工程副本不随全局更新迁移；修订旧片须沿用其已验收视觉参数，并单独评估迁移。

Windows 使用已装齐 requirements.txt 的Python，并加 -X utf8；上游 setup.sh 只适用于macOS/Linux，不在Windows直接执行。


Windows补充适配：VoiceStudio和火山音频先写入并关闭临时文件再交给FFmpeg读取；两处上游测试改为及时关闭NPZ文件。原上游文件不直接修改，这些适配随项目runtime副本安装。
