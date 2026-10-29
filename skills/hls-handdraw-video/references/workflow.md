# 项目记录与运行

工程资料保存在项目 03_制作工程；审核证据在04_审核记录；最终文件在05_最终交付。完整稿件、单片工程和成品留在项目。用户明确要求固定的可复用字体与声线参考可作为Skill的assets，记录真实来源与哈希。

`style/confirmation.json` 示例（值由本次真实对话填写，不照抄示例充当确认）：
```json
{"topic":"本条主题","style_id":"FA-035","status":"confirmed","user_quote":"第二个，先出三张样张","evidence":"当前用户消息的可定位标识或记录路径","scope":"samples","paused":false}
```
`scope` 为 samples 或 production。只有本次确实授权整片制作时才使用 production。样张通过但用户要求暂停，设 paused=true，保留原话。新主题新建记录；改画风重新确认。生产副本准备脚本要求 confirmed、production、paused=false，并把确认哈希写入 runtime-receipt.json。若后续暂停，不因已有副本继续运行。

任务级画风资料包含 selection、resolved、完整配方、参考图和版本；使用 sweety `references/production-options.md` 的数据结构与脚本校验，但不启动其自动倒计时选择器。Router deliver 的配方是来源，不能将推荐理由当成配方；每次更换资料重新绑定哈希。

准备运行副本后，读取 sweety `references/runtime-contract.md`、`continuous-narration.md`、`quality-gates.md`，使用副本的 scripts/handdraw_video.py doctor / build / render / verify / finalize（参数先查看 --help）。不要误调用原安装目录渲染混音。资产、字体及托管依赖按 sweety 的解析器获取并校验。

所有新视频必须使用本包副本并执行[素材审核与去重](material-review.md)。画风确认后先生成全部图片、展示并结束当前轮；全部当前素材由用户确认后才进入新增配音和动画制作。每个illustration使用一次asset_id；视频片头封面也登记素材ID。material_gate的snapshot只生成pending，不代替确认；check核对清单、文件、裁切与使用次数。修改素材后确认失效，须再次展示并等用户审查。旧运行副本不能绕过新要求，升级不自动改旧视频。

适配文件与原文件SHA记录在 patches/manifest.json；依赖漂移时脚本停止，须对比新版本并重新验证，禁止强行覆盖。《Essay评分逻辑》v4提供三项适配：art_direction.py支持真实旧图导入，drawing_contract.py支持 ready_for_animation，video_renderer.py修复配乐混音声道。2026-10-14《Essay第一段》增加caption_assets.py的加粗/换行/时间戳适配和voxcpm_voice.py的素材门槛、模型配置校验与max_len传递，默认准备及声线资源见[production-baseline](production-baseline.md)。白底阈值不照搬为全局默认。

旧图记录读取适配 art_direction.py 的字段约束：method=user_selected_existing_asset；在记录顶层写 existing_asset_authorization={"mode":"explicit_user_request","instruction":"用户实际指令"}、真实 original_source、原生成记录 original_generation_record、当前视觉 evidence、源图和当前文件哈希。裁切需列 approved_crops。没有旧生成记录就如实说明并检查可行的导入方式，不伪造文件通过门槛。

Windows运行Python统一加 `-X utf8`，避免依赖脚本默认GBK读取中文JSON或Markdown失败。

旧图 images 条目必须有 status=pass、非空 evidence 和当前 sha256；只有实际看图并通过才填写 pass。original_generation_record 的脚本检查只证明文件存在，不证明来源内容真实，执行者须读记录核对。旧图分支不调用 bind-evidence：该命令要求新生成图的 brief_file/prompt_file。新生图按生成前绑定执行；混合新旧图时先分别准备新图证据，再合并已绑定的新图条目与真实旧图条目，使用 check_record/build 校验，禁止伪造旧图简报。

本条用户明确指定或沿用既有风格时，集成流程允许不跑Router新候选 start，直接建立本主题确认记录并绑定真实配方；这个例外优先于Router的新任务重新推荐默认行为。


2026-10-26：已迁移到sweety 1.4.1。参见[上游兼容说明](upstream-compatibility.md)，新工程增加分镜密度、绘制预算与声音检查；HLS画风、素材审批和整篇固定声线流程仍优先。
