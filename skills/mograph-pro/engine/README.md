# 引擎副本

这里是生产引擎的完整拷贝，**结构与原项目保持一致**，所以 `build.py` 里基于 `__file__` 算出来的项目根依然正确，不需要改代码。

## 为什么复制一份

Skill 包应当保持只读：代码在这里，用户的文稿、形象素材、录音、`.env` 和全部产物都放在工作目录。`scripts/init_workspace.py` 负责把这个目录复制到工作目录并建好运行时结构。

## 各模块职责

| 文件 | 作用 | 是否联网 |
| --- | --- | --- |
| `scripts/build.py` | 主流程：plan / broll / digital / merge / persona | 部分阶段联网计费 |
| `scripts/check_env.py` | 鉴权自检，发一次 2 字符合成（约 0.0004 元） | 联网，极少量 |
| `scripts/clone_voice.py` | 克隆音色，写 `config/voices.json` | 联网，一次性 9.90 元 |
| `scripts/tts_demo.py` | 用指定音色合成一句试听（也用于激活音色） | 联网，几分钱 |
| `src/ai_digital_human/client/base.py` | 双路由：`official` 官方 / `recommended` 推荐平台 | 被下面调用 |
| `src/ai_digital_human/client/` | MiniMax 接口封装：语音、图像、视频、文件 | 被上面调用 |
| `src/ai_digital_human/client/compshare.py` | 自托管 ComfyUI 实例（上传、提交、轮询、下载） | 实例 |
| `src/ai_digital_human/client/local_speech.py` | 本地 Ming 语音，起子进程调 mlx_audio | 不联网 |
| `src/ai_digital_human/pipeline/talking_line.py` | 云端 H3 逐段生成 | 联网计费 |
| `src/ai_digital_human/pipeline/h3_line.py` | 自托管 H3 串行生成 | 实例 |
| `src/ai_digital_human/pipeline/credits_line.py` | 积分片段对齐与拼接（**零调用**） | 本地 |
| `src/ai_digital_human/pipeline/voice_line.py` | 配音：MiniMax / 本地 Ming 两分支 | 视后端 |
| `src/ai_digital_human/media/` | ffmpeg 封装：探测、归一化、拼接、替换音轨 | 本地 |
| `src/ai_digital_human/plan.py` | 文稿 → 分镜表 / 时间契约 | 本地 |
| `src/ai_digital_human/pricing.py` | 计价与预估（积分/自托管记 0） | 本地 |
| `src/ai_digital_human/delivery.py` | 时间码表、字幕、视频路径回填 | 本地 |
| `prompts/` | 视频与形象图提示词模板 | 本地 |

## 后端怎么选

见 `references/engines.md`。一句话：`--video-backend minimax|credits|compshare` × `--voice-backend minimax|local` ×（仅 MiniMax）`--minimax-route official|recommended`。

## 改过的地方

1. `client/base.py` 的 `.env` 定位：原来写死 `parents[3]`，现在用 `find_work_root()`，依次尝试 `DH_WORK_ROOT`、向上查找含 `.env` 或 `scripts/build.py` 的目录。
2. `client/base.py` 增加双路由：`api_base()` / `api_key()` 按 `DH_MINIMAX_ROUTE` 取地址与密钥，其余客户端统一走 `api_base()`。
3. 新增 `pipeline/credits_line.py` 与 `build.py` 的 credits 分支。

## 改代码的正确姿势

不要在技能包里直接改。改原项目的 `src/` 与 `scripts/`，跑通测试后再同步过来，否则两边会分叉。
