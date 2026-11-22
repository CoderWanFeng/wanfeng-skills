# 晚枫数字人-Pro

数字人**开工前的本地工作台**：把一份口播稿切成任何数字人平台都能直接开工的分段脚本——台词切段、参考素材体检、每段提示词排版。

**开源、不单独售卖。**「Pro」只表示长稿准备能力，不代表付费或自动出片。

**v3 主流程不调用任何数字人平台 API**，产出是文本与 JSON 的施工图。你在哪家平台做就用哪家：MiniMax / 可灵 / Vidu / HeyGen / D-ID / 万相 / 智影 / 火山 / 自托管 ComfyUI 都行。

只要一条 4–10 秒、零成本、不折腾外部接口的短片，用同目录的「晚枫数字人」（免费）。数字人画面已经在平台生成好、接下来加动效做成成片，接「晚枫自动剪视频 Pro」。

## 它交付什么

| 交付 | 说明 |
| --- | --- |
| `segments.json` | 分段脚本：段号 / 台词 / 预计秒数 / 情绪 / 场景 / 参考素材路径 |
| `prompts/seg_XXX.txt` | 每段独立提示词，按目标平台模板填 |
| `asset-checklist.md` | 素材体检清单：已到位 ✅ / 缺失 ⚠️ / 建议替换 🔄 |
| `README-for-platform.md` | 复制到平台后台即可开工的施工说明 |

**不交付**：mp4、mp3、srt、A-roll 拼接片。这些要么是数字人平台自己的产物，要么是后期（「晚枫自动剪视频 Pro」）的输入。

## 平台怎么选

本 skill 只列差异，不代你做决定：

| 平台 | 建议单段上限 | 需要的参考素材 | Prompt 风格 | 参考 |
| --- | --- | --- | --- | --- |
| MiniMax H3 | ≤ 10 秒 | 正脸参考 + 参考音频（可选，克隆音色） | 自然语言长句 | `platform-notes.md` |
| 可灵 Kling | ≤ 10 秒 | 正脸参考 | 自然语言 + 关键词 | 同上 |
| Vidu | ≤ 8 秒 | 正脸参考 | 自然语言 | 同上 |
| HeyGen | 无硬切段 | 正面照 + 半身照 + 音频 | 结构化字段 | 同上 |
| D-ID | ≤ 30 秒 | 正脸照 + 音频 | 结构化字段 | 同上 |
| 万相 / 智影 / 火山 | 各家产品不同 | 正脸 + 音频 | 后台向导 | 同上 |
| 自托管 ComfyUI | 由工作流决定 | 正脸 + 参考音频 | 工作流节点参数 | `legacy-integration.md` |
| 通用 | 6 秒 | 正脸 + 参考音频 | 六要素模板 | 拿不准就走这条 |

字段名、素材规格、单段上限都会随各家平台版本迭代变化。**上表是方向性参考**，最终一定以平台官方文档为准。

**通用视频大模型（Sora / Veo / Runway / PixVerse 通用档）不做数字人**：它们不接受参考音频，做不了口型。生成的素材只能当 B-roll 用。

## 目录结构

```
wanfeng-digital-human-pro/
├── SKILL.md                    主流程：S0 起手 → S4 交付 + 铁律
├── references/
│   ├── script-writing.md       文稿写法、双括号、9 种情绪、正反例
│   ├── platform-notes.md       各家平台差异对照（素材/长度/字段/风格）
│   ├── material-prep.md        素材准备与本地体检方法
│   ├── delivery-spec.md        施工图三件套的字段规范与验收清单
│   ├── troubleshooting.md      切段与素材相关踩坑
│   ├── visual-style.md         B-roll 素材与封面视觉约定
│   └── legacy-integration.md   v2.x 遗留：直连 MiniMax / 自托管 / 积分对齐
├── scripts/                    v2.x 遗留（init_workspace.py / preflight.py）
├── templates/
│   ├── script-template.txt     可直接改的示例稿
│   ├── env.example             v2.x 遗留（如需跑老路径）
│   ├── job-record.md           v2.x 遗留任务卡
│   └── market-frontmatter.yaml 上市场时用的完整 frontmatter
├── engine/                     生产引擎（含 MiniMax / 本地 Ming / ComfyUI H3 / 积分对齐）
└── requirements.txt            v2.x 遗留
```

`engine/`、`scripts/`、`templates/env.example`、`requirements.txt` 是 **v2.0.1 及之前**的完整调用流水线，**代码保留不删**但不再作为 v3 主流程。要跑老路径见 `references/legacy-integration.md`。

## 5 分钟上手

```bash
# 1. 建工作目录（不装依赖、不写 Key、不发网络请求）
mkdir -p digital-human-work/{input,prompts}
cp 你的稿子.txt digital-human-work/input/script.txt

# 2. 打开对话，把稿子与目标平台告诉技能
#    例："我要用 MiniMax 做数字人，帮我把这份稿子切段、素材列一下、每段写好提示词"

# 3. 技能按 S0–S4 出四份文件到工作目录，全程零 API 调用

# 4. 打开目标平台后台，按 README-for-platform.md 施工
```

## 典型用法

| 场景 | 怎么走 | 花费 |
| --- | --- | --- |
| 只想把长稿切成 8–10 段可用短稿 | S1 单跑 | 0 |
| 已知目标平台，要提示词 + 素材清单 | S0–S4 全跑 | 0 |
| 平台还没定，先看看素材齐不齐 | S0 选「通用」+ S2 | 0 |
| 换平台复用切段结果 | 只重跑 S3 | 0 |

## 与旧版 v2.0.1 的差别

- **v2.0.1**：把 MiniMax 云端、自托管 ComfyUI、软件积分三种后端串成一条 S0–S7 流水线，产出 mp4 + mp3 + `a_roll.srt` + `talking.mp4`。
- **v3.0.0**：不再做生成。engine/ 与旧脚本作为遗留代码保留在包内，但主流程不再经过它。要跑老路径见 `references/legacy-integration.md`。

因为交付契约变了（不再出 mp4），主版本号从 2 升到 3。**没有代码删除**，只有文档重定位。

## 安全边界

- **v3 主流程零 API 调用**：不发起任何网络请求，不装依赖，不写 Key；v2 遗留引擎只有用户明确选择旧路径时才使用。
- 用户素材留在本地。体检只读文件属性（`ffprobe` / `sips`），不上传。
- v2 遗留的 `.env`、`init_workspace.py`、`preflight.py` 已降级为可选，v3 主流程不使用它们。
- 包内不携带任何 API Key、音色 ID、本人视频、录音、历史产物、绝对路径。

## 已知限制

- **不生成数字人画面**。所有出镜段仍需在目标平台里点生成。
- **不生成配音**。参考音频只用于素材体检与克隆音色提示。
- **不做 A-roll 拼接、不加字幕、不做 B-roll**。后期请接「晚枫自动剪视频 Pro」。
- 各家平台的字段名与限制会随时变，`platform-notes.md` 是方向性参考，最终以平台文档为准。

## 版本

3.0.0 · 晚枫工作室
