# 数字人混剪分支

## 边界与预分镜
仅用户选择文稿生成数字人时读取本页。包内引擎自包含，不运行兄弟 Skill。最终剪辑仍用任务级 Pillow 渲染器，设计令牌、字幕风格、响度和封面不变。数字人参考素材不能替换固定封面人像。

1. 确认可用稿件与素材；已提供带声数字人视频时无需生成画面/声音，直接复用并校验；只有图片或缺声音时才执行对应生成。原稿只读，标记稿另存。
2. Agent 根据语义列出「镜头内容 / A 或 B / 原文 / 素材需求 / 估时 / 判断理由」。开场、个人观点、关键结论、收尾优先 A；操作、数据、案例证据优先 B，不硬定比例、不靠关键词决策。
3. 先确认预分镜，再配音实测、生成必要的出镜片段。预估时间不能冒充最终时间。素材就绪后 Step B 才完成正式 layers 与场景表。

标记稿每个段落必须明确类型，标记在行首；同一镜头可连续多行，空行后的新段落重新标记。只写需要念出的台词，不含 Markdown 标题、备注或费用表。

```text
[[A]]
今天介绍怎么把文稿变成一条有设计感的视频。

[[BROLL:自绘三步流程，说明分镜、配音、合成的顺序]]
先拆镜头，再确定声音的时长，最后把画面对齐。

[[A:happy|scene=明亮的书房]]
关键是只在需要表达观点的时候出镜。
```

`[[B]]` 与 `[[BROLL]]` 都有效；单括号 `[A]` / `[B]`、未知标记、未标记全文、空稿、只有标记没有台词一律阻断。标记不会被念出；不要在句子中间内嵌标记。

## 工作区与执行入口
`<选题>/mograph-task/digital-human/` 存代码运行副本、配置、输入和所有生成结果。Skill 安装目录只读。

```bash
# 以下命令只初始化和做零调用预览；原稿另存标记稿后再传入
python3 <skill>/scripts/init_digital_workspace.py \
  --target <选题>/mograph-task/digital-human --video-backend credits \
  --script <选题>/标记稿.txt
python3 <skill>/scripts/preflight_digital.py \
  --root <工作区> --script <工作区>/input/script/标记稿.txt --stage plan
python3 <skill>/scripts/digital_human.py \
  --root <工作区> --script <工作区>/input/script/标记稿.txt --job demo-v1 --stage plan
python3 <skill>/scripts/digital_human.py \
  --root <工作区> --script <工作区>/input/script/标记稿.txt --job demo-v1 --stage digital --dry-run
```

初始化验证来源哈希，分发包的 `engine.tar.gz` 还校验归档哈希与路径安全；仅补缺失文件，重复运行不覆盖 `.env`、稿件、代码或结果。完整引擎快照的出处和文件哈希见 `engine-source.json`，只显式同步，不在运行时找其他包。

`digital_human.py` 要求显式 `--stage` 和 `--job`，不接受 `all`、`--yes`、`--no-resume`，未知参数不透传。`--dry-run` 不写任务状态、不触发生成；计划报价是估算，不是账单。

## 四阶段与授权闸
| 阶段 | 动作 | 进入条件 |
|---|---|---|
| `plan` | 输出带 A/B 的语义标记分镜，时长仍是估算 | 明确标记稿；零费用 |
| `broll` | A/B 全部台词配音，写完整 `a_roll.json` 与 SRT，生成占位预览 | 用户确认稿件、预分镜和本阶段成本；`--approve-plan --approve-stage broll` |
| `digital` | 仅 A 段生成画面；首次默认实际第一段样段 | 已完成配音并试听；`--approve-audio --approve-stage digital` |
| `merge` | 将已存在的 A 段视频路径回填完整时间轴 | 全部 A 段素材可探测；不补发生成 |

`broll` 是引擎历史阶段名，**不是最终 B-roll 画面制作**。最终 B 画面仍由 Step A2/B 的真实素材或自绘 layers 实现。

- Agent 必须先解释供应方、路由、上传内容与本阶段预计成本，得到明确同意后才能加授权参数。参数记录同意，不能代替对话中的同意。
- 文稿/形象/语音上传外部服务需额外 `--approve-upload`；本地 Ming 和积分片段对齐不需要上传。
- 首次克隆音色是独立的上传及付费步骤；说明成本并获授权后才使用工作区 `scripts/clone_voice.py`。不要默认执行，也不要用 `check_env.py` 做零调用体检（它真实合成语音）。
- `digital --limit-segments 1` 是**第一段 A-roll**，不是自动找最短段。先看这段的人脸、口型、声音后确认，补齐时再加 `--approve-sample` 并去掉限制；禁止跳过样段。
- 同任务保持同一 job；修改稿件、音色、形象或后端配置时新建 job，不能挪旧状态冒充新任务。工作区锁阻止同 job 并发。
- 完整配音复用，不默认重跑 TTS；中断配音因原引擎不支持逐段恢复而阻断整批重跑，保留已有音频，人工恢复实测分镜、完整时间码与字幕后再继续。生成前校验 `storyboard.json` 与 `a_roll.json` 的 A/B、台词、时间和音频路径一致，并以 ffprobe 检查音频实际时长；发现估时或明显偏差时先修正，禁止先生成画面。已确认音频/字幕改动会被阻断。
- 视频中断复用已有有效片段；所选片段齐全且解码、时长通过时，入口直接复用，不上传、不调用后端。MiniMax 补齐时已有段还须保留 `raw/seg_*.mp4`，缺 raw 则阻断，避免原引擎重复生成；损坏片段先人工检查，不自动覆盖。
- 积分缺片返回状态 `waiting-media` / 退出码 3，照 `output/final/plan/<job>/credits-brief.md` 补素材，仍用原 job；不自动切换云端。退出 0 不是完工证据。

## 完整时间轴与底片
权威数据为 `output/final/talking/<job>/a_roll.json`，配套 `a_roll.srt`。它包含 A 与 B 的 `index/kind/start/end/duration`，不能只读取 A 段。音频裸文件名相对 `output/final/voice/<job>/`；视频裸文件名相对时间轴目录，非裸相对路径相对 JSON 目录解析。

导入时按数据 kind 判断出镜，不按文件名猜；阻断未知 kind、重复编号、缺音频、缺 A 视频、非法时长、间隙、重叠、字幕和总长不匹配。B 段不绑定数字人视频。不跨 A/B 重新按 5–12 秒分组。

```bash
python3 <skill>/scripts/assemble_digital_base.py \
  --digital-timeline <工作区>/output/final/talking/demo-v1/a_roll.json \
  --out <选题>/mograph-task/digital-base.mp4 \
  --plan-out <选题>/mograph-task/wanfeng-scene-plan.json
```

组装工具只做本地合成：A 视频按全局时间摆放，B 用品牌深色背景占位；所有段音频顺序拼接，屏蔽视频自带声音。保持宽高比补边，不自动裁脸；如需满屏构图，先实测人脸安全区再配置任务渲染器。毫秒时间码到帧的量化采用累计边界，误差不累加。

**禁止拿 `talking.mp4` 作完整底片**：它只拼 A，跳过 B 的时长。底片与占位预览都不是交付成片。

## 正式渲染衔接
扩展契约 `wanfeng-scene-plan@2`：
- `roll=a|b`、`presenter=full|circle|none`，同时保留 `mode/head/layers`。
- A 可 `overlay/full` 或 `fs/circle`；B 固定 `fs/none/head=false`，完整覆盖该段时间。
- 用 `templates/digital_render.example.py` 的分支接进本条任务 `render_full.py`，不是另起通用渲染引擎。
- 每个 B 段需要可执行 layers，标记 `visual_status=ready` 和 `full_frame=true`；启动全片前以真实注册表调用 `validate_render_plan(plan, implemented_layers=registry, final=True)`。素材文件必须存在，找不到外部素材可以真实自绘说明，不能只把状态改成 ready。
- B 的画面背景立即铺满，卡片仍可按原缓动入场；全段不绘人头。A 圆形人头坐标重新实测，不能抄旧真人 `(505,655)`。
- 数字人默认 1.0×、不套真人 `map_t()` 提速，不留卡片 0.1–0.2 秒空洞。后续任何提速须同时改音视频、字幕、场景，并重新验口型。
- 配色、字体、字幕、步骤条与封面沿用主规范；封面人像不随数字人素材更换。

## 验收与交付
全片前先静帧/短样片；最终逐场读图并看 A/B 边界前后帧，B 不闪人脸、不错位、无占位黑场，旁白完整连续且无双声。完整解码、时长与字幕检验后再按原流程响度归一（发布版 -14.4 LUFS / TP -1.0），交付母版、发布版、封面与八节交接文档。

交接写清 source_mode、job、A/B 表、素材来源、时间权威、后端与授权、估算/实际成本及待验项。本轮开发仅本地与 mock 验证，不调用付费接口、不扣积分、不启动云实例；真实人脸、口型与云端效果必须留给用户实跑验收。
