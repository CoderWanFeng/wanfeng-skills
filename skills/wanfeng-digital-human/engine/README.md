# 引擎副本

这里是生产引擎的完整拷贝，**结构与原项目保持一致**，所以 `build.py` 里基于 `__file__` 算出来的项目根依然正确，不需要改代码。

## 为什么复制一份

Skill 包保持只读：代码在这里，用户的素材、`.env` 和全部产物都放在工作目录。

**本版不需要把引擎复制到工作目录。** `scripts/clip.py` 直接从这里 import，并通过 `DH_WORK_ROOT` 环境变量告诉引擎去哪个目录读 `.env`——否则 `find_work_root()` 会顺着本目录的 `scripts/build.py` 命中 `engine/`，读错配置。

`engine/` 里的 `build.py` 等脚本是多段长视频流水线用的，本 Skill 的主入口只有 `scripts/clip.py`；保留它们是为了后续要接长视频时不用重新找代码。

## 各脚本职责

| 文件 | 作用 | 是否联网 |
| --- | --- | --- |
| `scripts/build.py` | 主流程：plan / broll / digital / merge / persona | 部分阶段联网计费 |
| `scripts/check_env.py` | 鉴权自检，发一次 2 字符合成（约 0.0004 元） | 联网，极少量 |
| `scripts/clone_voice.py` | 克隆音色，写 `config/voices.json` | 联网，一次性 9.90 元 |
| `scripts/tts_demo.py` | 用指定音色合成一句试听（也用于激活音色） | 联网，几分钱 |
| `src/ai_digital_human/client/` | MiniMax 接口封装：语音、图像、视频、文件 | 被上面调用 |
| `src/ai_digital_human/pipeline/` | 三条产线的业务编排 | 被 build.py 调用 |
| `src/ai_digital_human/media/` | ffmpeg 封装：探测、归一化、拼接、替换音轨 | 本地 |
| `src/ai_digital_human/plan.py` | 文稿 → 分镜表 / 时间契约 | 本地 |
| `src/ai_digital_human/pricing.py` | 计价与预估 | 本地 |
| `src/ai_digital_human/delivery.py` | 时间码表、字幕、视频路径回填 | 本地 |
| `prompts/` | 视频与形象图提示词模板 | 本地 |

## 唯一改过的地方

`src/ai_digital_human/client/base.py` 的 `.env` 定位：原来写死 `parents[3]`，现在改成 `find_work_root()`，依次尝试 `DH_WORK_ROOT` 环境变量、向上查找含 `.env` 或 `scripts/build.py` 的目录。搬到哪里都能找到配置。

## 改代码的正确姿势

不要在技能包里直接改。改原项目，跑通测试后再同步过来，否则两边会分叉。
