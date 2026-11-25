# 数字人环境、费用与排障

## 后端选型
先定**生成方式**，画面和声音绑定走同一路线，不要先选语音再选画面。只在数字人分支检查这些依赖，真人剪辑不需要密钥、模型、requests 或 GPU。

| 路线 | 画面 | 声音 | 要求与成本 |
|---|---|---|---|
| **第三方平台** | compshare / 自托管 H3 / credits | 需要AI生成时由数字人模型自带声音，B段旁白从生成视频提取复用；若用户明确提供带声视频/音频，或选择本地生成声音（需用 --voice-backend local），直接复用对应媒体 | 实例小时费或软件积分；用户提供媒体无生成费；第三方生成时不调用大模型TTS API |
| **大模型 API** | MiniMax H3 | MiniMax TTS（可克隆音色） | 需要AI生成时由所选MiniMax TTS处理，首次克隆音色另计；用户提供媒体直接复用 |

> 选定第三方后，整条片子的画面+声音都走第三方，引擎不再出现「调 MiniMax / 选语音后端」的分叉；只有选大模型 API 路线时才配置 `MINIMAX_*` 与语音后端。

**引擎原生只支持 H3 一条视频生成路线**（Minimax 官方 API / 推荐平台 API / 自托管 ComfyUI H3 REF2VA）。Seedance（即梦）、Kling（可灵）、Wan、Vidu、PixVerse、BDMAX 等流行模型**没有内置原生 API 调用**：要用就在对应平台生成好带声音的片段，放进 `input/credits/`，按「第三方平台 / 软件积分」路线本地对齐。不要把这类模型当成 Skill 能直接调度的后端。

Python 3.10+，引擎依赖清单为 `requirements-digital.txt`（`requests>=2.28,<3`），ffmpeg/ffprobe 是系统依赖。模型、个人媒体和密钥均不随包。初始化不自动 pip install、不下载模型。

## 第三方 H3 平台（不想自己搭机器的选这个）

`compshare` 后端走的是标准 ComfyUI API，任何跑通 MiniMax H3 REF2VA 工作流的 ComfyUI 实例都能接。不想自己配 GPU 和工作流，就租一台第三方云实例，拿到地址填进 `COMPSHARE_BASE_URL` 即可，本 Skill 不自动开机、不替你付租金。

- **优云智算 Compshare**（实测可用）：注册后开一台带 ComfyUI 的 GPU 实例，在实例里打开 H3 REF2VA 工作流，复制实例地址（形如 `https://8188-xxxx.pod.compshare.cn`，带端口）填进 `.env`。
  - 推荐注册链接：<https://passport.compshare.cn/register?referral_code=GNzyXwuR5JuDQJFWsbpkQr>
  - 费用：实例按小时计费（RTX 4090 约 2.15 元/小时，含开机/空闲，以平台账单为准）；生成按模型实际耗时，不是「API 免费」就全免费。
  - 注意：实例重启后地址可能变，地址变了要更新 `.env` 并新建 job；关机状态下连不上，生成前先确认实例在运行。

接入命令（按所选路线二选一）：

**第三方路线**（需要AI生成的画面走第三方；若为图片并选本地声音需加 --voice-backend local）：

```bash
python3 scripts/init_digital_workspace.py \
  --target <选题>/mograph-task/digital-human \
  --video-backend compshare [--voice-backend local]
# 需要AI生成声音时由数字人模型自带；提供音频或本地声音直接复用
# 然后编辑工作区 .env，填 COMPSHARE_BASE_URL=<你的实例地址>
```

**大模型 API 路线**（画面+声音都走所选 API）：

```bash
python3 scripts/init_digital_workspace.py \
  --target <选题>/mograph-task/digital-human \
  --video-backend minimax --voice-backend minimax
# 填 MINIMAX_* 密钥与路由；画面+声音都走所选大模型 API
```

## 配置
从 `templates/digital.env.example` 初始化到工作区 `.env`，权限 600；已有文件原样保留。按实际选择填以下变量，切勿打印或上传 `.env`。

- `DH_VIDEO_BACKEND=minimax|credits|compshare`；`DH_VOICE_BACKEND=minimax|local` 仅在「大模型 API」路线配置——第三方路线不调 TTS，直接消费第三方/自备音频。
- `DH_MINIMAX_ROUTE=official`：`MINIMAX_API_KEY`；使用按量付费接口密钥，不是订阅通道。
- `DH_MINIMAX_ROUTE=recommended`：`MINIMAX_RECOMMENDED_BASE_URL`、`MINIMAX_RECOMMENDED_API_KEY`。必须先告诉用户具体供应方与素材将被上传的位置，不默认用不明中转。
- `MINIMAX_VOICE_ID`：本人/已授权音色。首次克隆要先说明上传录音与一次性费用，另获同意再执行克隆脚本；当前价格以供应方账单为准。
- `MING_TTS_PYTHON`、`MING_TTS_MODEL`、`MING_TTS_REF_AUDIO`、`MING_TTS_REF_TEXT`：全部必填，路径指向现有环境与素材。Ming 只有整段字幕时不能宣传逐字实测时间码。
- `COMPSHARE_BASE_URL`、`COMPSHARE_HOURLY_PRICE`、`COMPSHARE_TIMEOUT`：只声明已有实例，不自动开机。当前 H3 默认固定 832×480 / 16:9，竖屏需另做构图，不能声称原生任意画幅。

`.env` 优先于 shell 同名变量，显式 CLI 后端优先于 `.env`。MiniMax 原引擎鉴权会重读 `.env`，因此 CLI 路由与已配置的 `DH_MINIMAX_ROUTE` 不一致时禁止生成；先统一路由，再新建 job。同一 job 的配置指纹固定这些选择。模板与引擎历史单价仅为估算，不保证实时价格。

## 零调用与真实生成的界限
`preflight_digital.py` 只查本地条件，不校验远端账户余额或真实模型能力。`digital_human.py --dry-run` 只做切分和估价。两者都不能证明人脸/口型正确。

工作区原引擎含 `check_env.py`、`clone_voice.py`、`tts_demo.py`，这些会真实联网计费，不能拿来做默认体检。主流程只走安全包装器，不直接调用默认 `all` 的 `build.py`。

## 故障处理
| 现象 | 处理 |
|---|---|
| 单括号 / 缺少标记 / 空稿 | 另存明确的双括号标记稿，不自动把全文当 A |
| 提示换 job | 文稿/音色/形象/配置发生变化，保留旧 job，另起任务 |
| 完整配音已存在 | 校验分镜与完整时间轴一致后复用；确认后的音频与字幕有哈希保护，不能默认重跑 TTS |
| 分镜与时间轴不一致 | 恢复同一 job 的实测分镜；修改台词或 A/B 须修改标记稿并新建 job |
| MiniMax 缺少 raw 缓存 | 补齐前先恢复有效原始片；只有最终片时整批续跑可能重复计费，入口会阻断 |
| 已有片损坏或时长不足 | 保留文件供检查，不把存在 mp4 当成功，不自动重付费 |
| 中断配音被阻断 | 原引擎无配音 resume；保留有效音频，人工恢复完整时间码再继续，不能自动整批重付费 |
| 退出码 3 / waiting-media | 等积分/出镜素材；查看 credits-brief.md，补入后用同 job 重跑，不换云端 |
| .lock 已存在 | 检查该 job 是否仍在运行；只有确认无进程后人工移走遗留锁 |
| 缺 A 视频 / 音频 / SRT / 时间轴间隙 | 修复相应媒体或时间契约，不自动购买补生成 |
| B 仍 pending / 未实现 layers | 补真实截图或全屏自绘说明，注册实际绘图函数并通过静帧后才标 ready |
| 底片比文稿短 | 确认没用只拼 A 的 talking.mp4；重新按完整 a_roll.json 组装 |
| 人头裁到额头 | 新素材重新画网格实测，不套历史真人裁切坐标 |
| 归档损坏或含危险路径 | 停止初始化，重新获取完整包，不绕过哈希与路径校验 |

云端人脸、口型、自托管效果需用户真实运行验收；本地回归通过不等于真实生成已验收。
