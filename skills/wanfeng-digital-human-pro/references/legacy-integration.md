# v2.x 遗留：直连 MiniMax / 自托管 ComfyUI / 软件积分

**这份文档不属于 v3 主流程。** 只在用户明确说"我要让 skill 直接调 API 把片子生成出来"或"我要跑离线流水线"时才读。

v3 起本 skill 的主契约是「施工图三件套」（见 `delivery-spec.md`），不发起任何 API 调用。v2.0.1 及之前实现的完整流水线（引擎矩阵、Key 配置、克隆音色、本地 Ming、自托管 ComfyUI、`build.py` 八阶段、`a_roll.json` 时间码表与 `talking.mp4` 拼接片）**代码原样保留在 `engine/`、`scripts/`、`templates/env.example`、`templates/job-record.md` 中**，但不作为默认路径。

## 1. 什么时候还要用 v2 路径

- 用户已经配好 MiniMax 官方 Key 或推荐平台 Key，明确要"一键跑完不要我复制粘贴"；
- 用户有自托管 ComfyUI 实例与 GPU 额度，要在离线环境批量出片；
- 用户只想让 skill 做本地对齐与拼接，画面用软件积分手动生成后放进 `input/credits/`；
- 历史 job 需要复现。

不满足以上任一条件，一律走 v3 主流程。

## 2. 三后端配置

| 后端 | 参数 | 凭据 | 状态 |
| --- | --- | --- | --- |
| MiniMax H3（官方） | `--video-backend minimax --minimax-route official` | `MINIMAX_API_KEY` | 已验证 |
| MiniMax H3（推荐平台） | `--video-backend minimax --minimax-route recommended` | `MINIMAX_RECOMMENDED_BASE_URL` + `MINIMAX_RECOMMENDED_API_KEY` | 接口同构，只换地址与 Key |
| 自托管 ComfyUI H3 | `--video-backend compshare` | `COMPSHARE_BASE_URL` + `COMPSHARE_HOURLY_PRICE` | 本地 mock 通过，云端未端到端验收 |
| 软件积分 | `--video-backend credits` | 无 | 本地对齐与拼接已验证 |
| MiniMax 克隆音色 | `--voice-backend minimax` | 同 MiniMax H3 | 已验证 |
| 本地 Ming | `--voice-backend local` | `MING_TTS_PYTHON` + `MING_TTS_MODEL` + `MING_TTS_REF_AUDIO` + `MING_TTS_REF_TEXT` | 本机已验证 |

`templates/env.example` 是完整模板，`scripts/init_workspace.py` 会按参数写工作区 `.env`（权限 600）。

## 3. MiniMax Key 与账号

- 打开 `platform.minimax.cn` 注册；
- **完成个人或企业实名认证**（未认证时音色复刻返回 `2038`）；
- 创建按量付费 Key（`sk-api-` 开头），**不要**用 `sk-cp-` 开头的订阅通道 Key；
- 有些账号里还躺着 `sk-cp-` 中转 Key。用它调按量接口会返回 `2049 invalid api key`。

`.env` 优先于 shell 环境变量（有意设计：多数机器的 shell 里残留着旧 Key）。命令行 `--minimax-route` 优先于 `.env` 里的 `DH_MINIMAX_ROUTE`，适合临时切换。

## 4. 克隆音色（一次性）

素材要求见 `material-prep.md`；执行入口：

```bash
python3 scripts/clone_voice.py input/voice/source.mp3 \
  --voice-id my-clone-voice \
  --text "这是我的声音克隆试听，听起来像不像我？"
```

**三条硬约束**：

1. **7 天内必须正式调用一次**。复刻出的音色若 7 天内没被真正用于合成，会被系统删除。克隆完立刻合成一次激活。
2. **账号需实名认证**，否则 `2038`。
3. **`file_id` 必须是整数**。上传接口返回的 ID 若被当字符串传回，服务端判 `2013 invalid params`。

## 5. 本地 Ming 语音（`--voice-backend local`）

**只用本机现有的 Python 3.11，不要为它另装版本。** mlx_audio 不进主项目依赖，引擎只在选了 local 时才起子进程。

四项都要配齐：

| 变量 | 说明 |
| --- | --- |
| `MING_TTS_PYTHON` | 已装 mlx_audio 的 Python 3.11 解释器绝对路径 |
| `MING_TTS_MODEL` | Ming-3.0-tts 模型目录 |
| `MING_TTS_REF_AUDIO` | 10 秒以上单人清晰说话音频 |
| `MING_TTS_REF_TEXT` | 上面那段音频的**准确逐字文本**，错一个字音色就飘 |

本地合成没有逐句时间码，字幕会退化成「每个合成段一条」。想更细的字幕时间码，把 `--segment-seconds` 调小。

## 6. 自托管 ComfyUI H3（`--video-backend compshare`）

1. 把 GPU 实例开机；
2. 装好 ComfyUI 与 REF2VA 工作流，确认模型能加载；
3. 填 `COMPSHARE_BASE_URL=http://实例地址:8188`；
4. 先跑 `--stage digital --limit-segments 1` 试一段。

**能力边界**：当前模板固定 `832x480` + `16:9`，竖屏形象会被裁；H3 严格串行，不能像云端那样开 4 个并发。**云端链路尚未端到端验收**，首次成功前不要向用户说"H3 已经跑通"。

实例费按开机时长算，引擎报的是"本次新生成耗时 × 配置单价"，不含开机、空闲、关机时间，以平台账单为准。不用时提醒用户关机。

## 7. 单价参考（MiniMax 官方）

| 项 | 单价 |
| --- | --- |
| 音色复刻 | 9.90 元 / 音色（首次正式合成时才扣） |
| `speech-2.8-hd` | 3.50 元 / 万字符（1 个汉字计 2 字符） |
| `image-01` 形象图 | 0.025 元 / 张 |
| `MiniMax-H3-Lite` 768P | 0.26 元 / 秒 |
| `MiniMax-H3-Lite` 480P | 0.16 元 / 秒 |
| `MiniMax-H3` 768P / 2K | 0.50 / 0.80 元 / 秒 |
| 自托管 `ComfyUI-H3-REF2VA` | API 费 0；实例按平台账单，默认单价 2.15 元/小时 |
| 本地 `Ming-3.0-tts` | API 字符费 0 |
| 软件积分画面 | 0 元（扣积分） |

**费用按每次生成请求的秒数算，不按最终剪进成片的秒数算。** 请求 7 秒、实际只用 1.5 秒，也是按 7 秒付费。每段有 4 秒最低请求时长，所以碎片化分段反而更贵。

## 8. 完整流水线：S0-S7

```bash
# S0 起手：选引擎（v2 是三维度：语音 / 画面 / 接入方式）
# S1 初始化工作区
python3 scripts/init_workspace.py --target ./digital-human-work \
  --script 稿子.txt --persona 自拍.mov --voice 录音.mp3 \
  --video-backend minimax --voice-backend minimax --minimax-route official

# S2 体检
cd digital-human-work && python3 <skill>/scripts/preflight.py --root . --stage broll

# S3 拆解
python3 scripts/build.py --script input/script/<稿子>.txt --stage plan --job <job名>

# S4 配音 + 占位预览
python3 scripts/build.py --script input/script/<稿子>.txt --stage broll --job <job名>

# S5 出镜画面（三选一）
python3 scripts/build.py --stage digital --job <job名> --limit-segments 1              # MiniMax 先试一段
python3 scripts/build.py --stage digital --job <job名>                                  # MiniMax 补齐
python3 scripts/build.py --stage digital --job <job名> --video-backend compshare        # 自托管
python3 scripts/build.py --stage digital --job <job名> --video-backend credits          # 积分（分两次跑）

# S6 合成
python3 scripts/build.py --stage merge --job <job名>

# S7 收尾：写 templates/job-record.md 任务卡
```

**铁律（v2）**：

1. 禁止 `--stage all`（确认关卡在非交互环境会自动放行）。
2. 禁止 `--yes`、`--no-resume`，除非用户明确知道代价后仍要求。
3. 进入 `digital` 前必须报预估费用并拿到明确同意。
4. 全程同一个 `--job`。改稿、换音色、换素材、换后端就换新 job。
5. 不打印 `.env` 内容；不把用户素材发给任务无关第三方。
6. 文稿里出现单括号 `[A]` / `[B]` 时，先要求改成双括号再合成。
7. 成片不出现段号、`B-roll` 字样、版式示意、制作进度。
8. 积分后端不许偷偷调云端接口。

## 9. v2 交付包字段（`a_roll.json`）

```json
{
  "total_duration": 24.156,
  "a_roll_duration": 11.556,
  "b_roll_duration": 12.6,
  "segments": [
    {
      "index": 1, "kind": "a", "shot": 0,
      "emotion": "happy", "scene": "明亮的书房", "note": "",
      "text": "大家好，我是这个账号的作者……",
      "audio": "seg_001.mp3", "video": "seg_001.mp4",
      "start": 0.0, "end": 5.29, "duration": 5.29
    }
  ]
}
```

| 字段 | 含义 |
| --- | --- |
| `kind` | `a` 出镜口播 / `b` 只出声音 |
| `shot` | 镜头序号，同号即同一镜头 |
| `video` | A-roll 是成片文件名；B-roll 为 `null` |
| `start` / `end` | 全片时间轴入出点 |
| `note` | B-roll 段的画面提示 |

**关键**：B-roll 段同样占时间轴位置，它的旁白在片子里，不能跳过。

## 10. 剪辑四步（v2 交付给后期）

1. 导入 `a_roll.srt` 作为字幕底稿
2. 按 `a_roll.json` 的 `start` / `end`，把各 `seg_XXX.mp4` 放到对应位置
3. B-roll 段（`video: null`）放 MG 动画或人工素材，`note` 是画面提示
4. 检查相邻 A-roll 的接缝，必要时用 `--transition` 淡化

`talking.mp4` 只把 A-roll 顺序拼起来，中间跳过了 B-roll 时长，**不是成片**。拿它的时长对位一定错。

## 11. v2 专属错误码

| 返回码 | 含义 | 怎么办 |
| --- | --- | --- |
| `2049 invalid api key` | Key 无效，或被 `sk-cp-` 订阅 Key 污染 | 换 `sk-api-` 开放平台 Key，确认 `.env` 生效 |
| `1004 login fail` | Key 不属于开放平台 | 同上 |
| `1008` | 余额不足 | 充值 |
| `2013 invalid params`（复刻） | `file_id` 传成了字符串 | 提交前 `int(file_id)` |
| `2038` | 账号未实名 | 完成认证 |
| 音色用不了 | 7 天内没正式调用 | 重新克隆并立刻合成一次 |
| ComfyUI 连接失败 | 实例未开机 / 地址端口不对 / 模型未加载 | 先浏览器打开地址确认；不要盲目重试扣时长 |
| 积分路线提示"缺少 N 个片段" | `input/credits/` 未放齐 | 看 `plan/<job>/credits-brief.md`，严格按 `seg_001.mp4` 命名 |
| 本地 Ming 报"参考文本不得为空" | `MING_TTS_REF_TEXT` 未配 | 填与参考音频逐字一致的文本 |

## 12. 迁移到 v3 主流程

从 v2 迁到 v3 只需要三件事：

1. **不再要求用户配 `.env`**（除非他明确要跑 v2 路径）；
2. SKILL.md 主流程改为 S0-S3 三步（切段 / 素材 / 提示词 / 交付），不再出现 `python3 scripts/build.py`；
3. `engine/` 与 `scripts/init_workspace.py`、`scripts/preflight.py`、`templates/env.example`、`templates/job-record.md` **保留不删**，只是从"入口"降级为"参考实现"。

用户如果提"我还是想让 skill 直接调 MiniMax"，把这一份文档发给他，让他自己按 §3–§8 走完；不要在本 skill 的 v3 主流程里回头补调用逻辑。
