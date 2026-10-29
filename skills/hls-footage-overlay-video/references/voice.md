# VoxCPM2 自动配音

用户只需给讲稿和素材；Agent负责匹配声线。先把标题、舞台提示与正文分开，纯口播正文存UTF-8文本。根据受众、内容和情绪选择：学术方法用academic，学长建议用friendly，减压安抚用reassuring，经历叙述用story；可用`--voice-description`写更贴合本篇的自然语言声音描述。保持清晰自然，避免夸张播音腔。无需参考音频。

脚本的auto只是关键词兜底；正式任务优先由Agent理解全文后指定style或description。声线设计是生成提示，不保证每次音色完全一致。需要系列音色连续性时保留已接受音频和参数，再按用户需求另做参考声线。

## 本地运行环境

个人配置默认`~/.local/share/hls-footage-overlay-video/runtime.json`，也可用`--runtime`指定。配置不打入Skill包；指向已安装的Python环境和完整本地模型：

```json
{
  "python": "/path/to/voxcpm-env/python",
  "model_path": "/path/to/VoxCPM2",
  "device": "cuda",
  "asr_python": "/path/to/whisper-env/python",
  "asr_model_path": "/path/to/faster-whisper-medium"
}
```

实测VoxCPM 2.0.3、CUDA PyTorch、soundfile及numpy；ASR为faster-whisper 1.2.1，CPU int8。模型与环境是外部依赖，不含在下载包内。新机器先检查环境、已有模型和磁盘，按实际平台配置官方依赖；缺失时报告具体依赖，不把“请提供配音”作为默认替代流程。本脚本离线加载，不隐式下载模型。

## 调用与接入成片

```powershell
python "$SKILL/scripts/generate_voice.py" --text-file "讲稿.txt" --output "配音_v1.wav" --style academic --check
python "$SKILL/scripts/generate_voice.py" --text-file "讲稿.txt" --output "配音_v1.wav" --style academic
python "$SKILL/scripts/transcribe_voice.py" --audio "配音_v1.wav" --text-file "讲稿.txt" --output "配音_v1_asr.json"
```

生成器整篇一次合成，输出48kHz WAV及`.voice.json`（实际采样率以元数据为准）。相同输入和音频哈希可以复用；不同参数不能覆盖旧文件。种子默认2026，可通过新版本和新种子重试。GPU不可用时明确改`--device cpu`或修复环境。TTS进程退出后才启动ASR，释放显存。

ASR输出词级时间戳、18字左右的字幕JSON/SRT及稿件比较结果。它是识别时间戳，不是强制对齐。退出0表示忽略标点大小写后逐字一致，退出2表示需要复核：中文同音错字、繁简差异、数字和英文缩写可能只是识别差异；不能直接宣布配音读错，也不能把原稿强塞到不匹配时间轴。核对头尾和专有词；确有漏读、重复或截断则修改提示或种子生成v2，再识别。自动重试最多两次，仍失败则记录具体位置。

从ASR JSON读取`captions`写入视频config；`audio`写相对于config的WAV路径；`duration`按`ceil(audio_duration*fps)/fps`取整。逐条高亮依据`segments[].words`的实际边界填写。先确定实际发声，再规划场景，不用字数比例估算同步。完整配音过长或模型截断时按自然段分段并保持同一描述，拼接后对最终WAV重新识别，记录分段方式与衔接复核结果。

台词匹配与主观听感分开记录。无法听辨时保持`listening_status: not_reviewed`并提供试听；不要把ASR通过写成听感验收。

实现依据：[OpenBMB/VoxCPM官方说明](https://github.com/OpenBMB/VoxCPM)。Voice Design使用括号内声音描述加正文；本地2.0.3通过`torch.manual_seed`设种子，`max_len`控制生成上限。版本升级按已安装API核验。
