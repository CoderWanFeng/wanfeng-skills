---
name: wanfeng-digital-human-pro
description: AI 数字人**开工前的本地工作台**：把一份口播长稿切成任何数字人平台都能直接开工的分段脚本——台词切段、参考素材体检、每段提示词排版。平台无关，不代你调用 MiniMax / 可灵 / Vidu / HeyGen / D-ID / 万相 / 智影 / 火山 / 自托管 ComfyUI，产出是文本与 JSON 的施工图。当用户说「帮我把稿子切成 <平台> 能用的分段」「数字人开工前需要准备哪些素材」「按 MiniMax 规范给我 prompt」「批量给每段写好提示词」「我在做系列口播，先把素材和脚本对齐」时使用。适合自媒体做系列口播、批量产内容前的准备工作；不生成 mp4、不做 A-roll 拼接、不加字幕，出片交给平台，剪辑交给「晚枫自动剪视频 Pro」。只要一条 4–10 秒的零成本短片，用「晚枫数字人」。
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
---

用户输入：$ARGUMENTS

# 晚枫数字人-Pro

数字人开工前的**本地工作台**。做三件事：**切段、素材体检、提示词排版**。产物是任何数字人平台都能直接开工的施工图文本。**v3 主流程**不生成视频、不调任何 API；v2 遗留引擎只有用户明确选择旧路径时才使用。

**本 Skill 开源、不单独售卖。**「Pro」只表示长稿准备工作台，不代表付费或自动出片。只要一条 4–10 秒、零成本、不折腾外部接口的短片，用同目录的「晚枫数字人」；数字人画面已经生成好、接下来加动效卡做成片，交给「晚枫自动剪视频 Pro」。

## 与兄弟 skill 的分工

| Skill | 干什么 | 何时用 |
| --- | --- | --- |
| 晚枫数字人（免费） | 软件积分跑一条 4–10 秒会说话的短片，零成本 | 只想快速试效果，不要长稿 |
| **晚枫数字人-Pro（本 skill）** | 长稿切段 + 素材体检 + 每段提示词，产出施工图 | 30 秒以上长口播、跨平台批量做系列、开工前把准备工作做完 |
| 晚枫自动剪视频 Pro | 数字人 / 真人片段 + 口播稿 → 加动效卡的成片 + 封面 | 数字人画面已在平台生成好，接下来加动效与包装 |

## 三条职责

1. **合理安排数字人的提示词**：按目标平台的 prompt 规范给每段生成独立提示词（自然语言型 或 结构化字段型）。
2. **帮用户凑齐素材**：正脸参考、参考音频、风格锚点，逐项本地体检，缺什么直接告诉他去哪儿补。
3. **把长稿切得更合理**：按目标平台的单段上限、情绪切换、标点停顿切成独立可跑的段。

## 铁律（违反任何一条立刻停下并解释）

1. **不调用任何数字人平台 API**：不生成 mp4 / mp3 / srt，不做 A-roll 拼接，不上传任何素材。所有产出是文本与 JSON。
2. **平台由用户选**：skill 只告诉他"要跑通需要哪些字段、素材缺什么"，不代他做决定。用户没说清就用括号里的推荐值。
3. 文稿里出现单括号 `[A]` / `[B]` 一律先要求改成双括号 `[[A]]` / `[[B]]` 再切段。否则标签会被当正文。
4. 不打印 `.env` 内容；不把用户素材发给任务无关的第三方。
5. 交付的是**施工图**，不是成片。对外别说"一键出片"，否则交付时一定错位。
6. 每段 `duration_hint` ≤ 目标平台单段上限（见 `references/platform-notes.md` §5）。宁少勿长。

## S0 起手（每次必做，先于一切）

两轮问答，一轮一层，问完确认再问下一层。用户没说清就用括号里的推荐值。

1. **稿子**：口播稿全文（txt / md 均可）。没有稿 → 按 `references/script-writing.md` 帮用户写。
2. **目标平台**：MiniMax / 可灵 Kling / Vidu / HeyGen / D-ID / 万相 / 智影 / 火山 / 自托管 ComfyUI / 通用。不确定时选**通用**（切段 6 秒/段，prompt 走六要素模板）。

工作目录：默认 `./digital-human-work/`。只 `mkdir -p digital-human-work/{input,prompts}`，不写 `.env`、不装依赖、不发网络请求。

## S1 切段（本地，零成本）

产出 `digital-human-work/segments.json`。字段规范见 `references/delivery-spec.md` §2。

切段规则：

- **硬约束**：目标平台单段上限（`platform-notes.md` §5）。中文口播按 **4 字/秒**折算，超过上限就在标点处再拆。
- **软约束**：优先在句号、问号、感叹号处断；其次在逗号、破折号处断；情绪切换处必断；`[[A:happy|scene=...]]` 里的 `emotion` 与 `scene` 解析进字段，**不再出现在 `text`**。
- **场景 / 服装 / 背景变化**必须断段。跨段保持视觉一致会明显穿帮。
- **B-roll 段**（`[[BROLL]]` 之后）不进 `refs.persona`，`kind` 设成 `"b"`，只保留 `text` 与 `broll_hint`。

产出后向用户念一遍：**一共几段，最长段几秒，哪几段有情绪切换**。用户可以手工改 `segments.json` 里任意字段，重跑只走 S3 即可。

## S2 素材体检（本地，零成本）

产出 `digital-human-work/asset-checklist.md`。规范见 `references/material-prep.md`。

必查项：

| 素材 | 通用底线 | 加严项 |
| --- | --- | --- |
| 正脸参考（照片或视频） | 单人、正脸、≥ 512×512、光照均匀 | 见 `platform-notes.md` §1 |
| 参考音频（仅在需要克隆音色时） | 10 秒 – 5 分钟、单人、无 BGM | MiniMax ≤ 20MB |
| 风格锚点（可选） | 一张氛围参考 | 视平台 |

体检方法：本地 `sips` / `ffprobe` 只读文件属性，**不上传、不做人脸检测、不做 ASR**。用户素材留在本机。

每项标 ✅ 已到位 / ⚠️ 缺失 / 🔄 建议替换。**至少一项 persona 是 ✅**，才能进 S3；带 ⚠️ 缺项硬上，产物就是"看起来对但一开工就报错"的施工图。

## S3 提示词排版（本地，零成本）

对每一段生成 `digital-human-work/prompts/seg_XXX.txt`。排版规范见 `references/delivery-spec.md` §3。

两种风格：

- **A. 自然语言长句型**（MiniMax / 可灵 / Vidu / 通用）：六要素（主体 / 景别 / 光线 / 情绪 / 动作 / 背景）拼成一段连贯描述，末尾附台词。
- **B. 结构化字段型**（HeyGen / D-ID / 云厂商控制台）：每行一个 `key: value`，用户直接复制贴到对应输入框。

同时产出 `digital-human-work/README-for-platform.md` —— 复制到平台后台即可开工的施工说明，结构见 `delivery-spec.md` §5。

## S4 交付确认

把四份文件的位置念给用户，然后过一遍 `references/delivery-spec.md` §6 的验收清单。全部通过才算完。

用户如果提"我想让 skill 直接调 API 生成"——不改主流程，把 `references/legacy-integration.md` 指给他。

## 常见分支

| 用户说 | 怎么做 |
| --- | --- |
| 稿子还没写 | 走 `references/script-writing.md`，先出稿再切段 |
| 不知道选哪家平台 | 选「通用」，同时列 3 家常用平台的差异（`platform-notes.md` §1） |
| 素材不齐 | 在 `asset-checklist.md` 明确列出缺什么、去哪儿补；**不要凑合出提示词** |
| 某段超过平台上限 | 拆到符合上限，改 `segments.json` 后只重跑 S3 |
| 换了目标平台 | 保留切段结果，只重跑 S3；`target_platform` 与 `max_seconds_per_segment` 跟着改 |
| 想直接调 API 生成 | 本 skill 不做；见 `references/legacy-integration.md`（v2 遗留路径） |

## 参考文档（按需读）

- `references/script-writing.md` — 文稿写法、双括号标记、9 种情绪、正反例
- `references/platform-notes.md` — 各家平台对参考素材 / prompt / 切段长度 / 字段名的差异
- `references/material-prep.md` — 素材准备与本地体检方法
- `references/delivery-spec.md` — 施工图三件套的字段规范与验收清单
- `references/troubleshooting.md` — 切段与素材相关踩坑
- `references/visual-style.md` — B-roll 素材与封面视觉约定
- `references/legacy-integration.md` — v2.x 遗留：直连 MiniMax / 自托管 ComfyUI / 积分对齐

---

上一版的执行引擎在 `engine/`，v3.0 起主流程不再经过它；如需真调用云端，按 `references/legacy-integration.md` 走。
