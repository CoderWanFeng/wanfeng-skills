---
name: knowledge-short-video
description: 制作知识类短视频完整 skill（**主题通用** — 适用于任何 C 端知识科普：AI 工具 / 美食 / 职场 / 育儿 / 历史 / 健身 / 财经 ...）。Step 0 一次性确认 4 个开关（封面风格 4 选 1 / IP 信息默认不放 / 引导关注默认不引导 / 配音默认系统默认 TTS 或用户提供 4 参数+文档链接+代码路径）。覆盖：写口播稿（账号定位 + 三类栏目 + 钩子 + 小白细化 + **≥ 20 句硬下限 + segments.txt 拆段**）→ 选定视觉风格（swiss-grid/warm-grain/nyt-graph/embedded-captions）→ 3:4 封面 → GSAP 动画视频 composition（**不是图片拼接**）→ TTS 配音 → 渲染 → 3 文件精简发布包。每个任务 = 一个带 `YYYYMMDD_HHMMSS_` 时间戳的独立目录（避免连续任务冲突）。用户按自己的账号主题和定位替换示例占位符（`<主题>` / `<IP名>` / `<定位>` / `<slogan>`）。
version: 2.2.0
---

# 知识类短视频 · Skill 索引

> 把任何"知识科普"内容做成一条可在小红书 / 抖音 / 视频号发布的完整竖版短视频。
> 适用：**60-90s、9:16、单人口播讲解型、无人出镜、以排版为主的中文 TTS 视频**。
> 适用主题（不限于）：AI 工具 / 美食 / 职场 / 育儿 / 历史 / 健身 / 财经 / 心理 ...
> 不适用：长讲解视频、横版、纯图片拼接（**本 skill 强制输出动画视频**）。

---

## 〇、三句话看懂（必读 · 整个 skill 的工程框架）

> 本节吸收自 [ai-cut pipeline](#八-与其他-skill--文档的关系) 的工程实践。**先理解这 3 句话，再走下面 7 步流程**。

1. **一个任务 = 一份视觉模板 + 一份口播稿 → 多个配音变体（MP4）**。模板与口播稿解耦，换 TTS 引擎 / 换声音 = 走"变体"流程，不重写模板。
2. **时间由实测配音时长驱动**，不是拍脑袋估算。`resync.py` 把 TTS 实测时间反向注入模板，画面与声音严格同步。
3. **一条命令产出变体**：`./tools/run-variant.sh <任务> <变体>` 串起 **TTS → 拼接 → 注入 → QA → 渲染 → 抽帧**，任一步失败即停、保留中间物。

> ⚠️ **唯一音频约定**（借鉴自 ai-cut pipeline，最容易踩坑的点）：
> `scene_NN.wav` / `narration.wav` / `timeline.json` **全在同一个目录**（`tasks/<task>/05-Audio/segments/` 或 `05-Audio/` 内）。
> TTS **写**进去，拼接**读**同一个目录，resync 也**读**它。把它们拆到不同目录是历史返工的根因。

---

## 一、一句话用法

> 拿到选题 → 建带时间戳的任务目录 → **Step 0 一次性问用户 4 个开关** → 走 7 步流程 → 出 1 份 3 文件发布包（视频 + 1 封面 + 1 文案）→ 一键发小红书 / 抖音 / 视频号。
> **每个 Step 完成后立即清理中间产物**（截图、预览图、测试 HTML、中间 wav、原始帧）。

```
TS=$(date +%Y%m%d_%H%M%S)_<任务名>/
  ↓ [Step 0] 4 开关一次性确认（默认：A swiss-grid / 不放 IP / 不引导关注 / 默认 TTS）
  ↓ [Step 1] 写口播稿（≥ 20 句）+ 拆 segments.txt + 用户确认
  ↓ [Step 2] 按选定风格，落地视觉规范（02-VisualSpec/visual-spec.md）
  ↓ [Step 3] 生成 3:4 封面（03-Cover/cover.png）
  ↓ [Step 4] 写 composition（GSAP fromTo · 动画视频）
  ↓ [Step 5] TTS 合成（05-Audio/narration.wav + timeline.json）
  ↓ [Step 6] 注入时间 + render（实测时长反向同步）
  ↓ [Step 7] 拼 3 文件发布包（07-Publish/）
video_full.mp4 + cover.png + publish.md
```

---

## 二、目录结构约定（必读）

### 任务根目录命名

```
格式：YYYYMMDD_HHMMSS_<任务名>
示例：20260629_203000_什么是Token
```

> ⚠️ **禁止**用 `Process/` 这种语义空泛的目录名。每个任务必须带**任务名 + 时间戳**，避免连续做多个任务时重名冲突。

### 任务根目录下的 7 个子目录

```
<task>/
├── task-config.json                ← Step 0 4 开关
├── 01-Script/                      ← Step 1 口播稿 + 拆段
│   ├── script.md                   ← 完整口播稿（≥ 20 句）
│   ├── segments.txt                ← 段号|类型|文本（≥ 20 段，硬下限）
│   └── reverse-check.md            ← 段↔句 映射（反向同步用）
├── 02-VisualSpec/                  ← Step 2 视觉规范
│   └── visual-spec.md
├── 03-Cover/                       ← Step 3 封面（多版本建 v2/ v3/ 子目录）
│   ├── cover-v1.html
│   ├── cover-v1.png                ← 验证用
│   └── cover.png                   ← 选定版
├── 04-Composition/                 ← Step 4 GSAP 动画视频模板
│   └── composition.html
├── 05-Audio/                       ← Step 5 TTS 配音
│   ├── tts-config.json             ← 用户自定义 TTS 时填
│   ├── segments/                   ← 每段独立 wav（中间产物，验证后删）
│   ├── narration.wav               ← 拼接后的完整配音
│   └── timeline.json               ← 实测时长 + 段↔句 映射
├── 06-Render/                      ← Step 6 渲染
│   ├── render.py
│   └── video_full.mp4              ← 最终 mp4
└── 07-Publish/                     ← Step 7 发布包（3 文件精简版）
    ├── cover.png                   ← 从 03-Cover/ 复制
    ├── video_full.mp4              ← 从 06-Render/ 复制
    └── publish.md                  ← 标题 + 简介 + hashtag
```

### 中间产物清理（每个 Step 完成后立即做）

| 阶段 | 必须删掉的中间产物 |
|---|---|
| Step 1 | `script-v0.md` / `script-v1.md` 早期草稿（保留最终 v2）|
| Step 3 | 验证用的 `cover-v1.png` / `cover-v2.png`（保留选定的 `cover.png`）|
| Step 4 | 验证截图 `composition_preview_t*.png` |
| Step 5 | `segments/` 子目录里的每段独立 wav（保留 `narration.wav`）|
| Step 6 | 渲染中间产物 `frames/frame_*.png` 几千张图（保留 `video_full.mp4`）|
| Step 7 | **绝不进发布包**（详见 [reference/04-production.md §7.5](reference/04-production.md)）|

**经验法则**：

- ✅ 保留：成品（cover.png / video_full.mp4 / narration.wav）+ 配置（task-config.json / tts-config.json / timeline.json）
- ❌ 删除：截图、预览图、测试 HTML、中间 wav、原始帧

---

## 三、文件结构

| 文件 | 用途 |
|---|---|
| `SKILL.md`（本文）| 主入口：导航 + 触发词 + 核心铁律 + 7 步索引 |
| `reference/01-account.md` | 账号定位 + 内容比例硬约束 |
| `reference/02-script.md` | 口播稿创作（含引导关注开关 + **分段规范**）|
| `reference/03-visual-spec.md` | 4 种视觉风格 + IP 信息开关 + 封面设计 |
| `reference/04-production.md` | Step 0 4 开关 + 7 步制作流程 + 目录约定 + 清理规则 |
| `reference/05-commands.md` | 关键命令速查（含清理命令）|
| `reference/06-pitfalls.md` | 踩坑清单 + 铁律 |
| `assets/cover-layouts.md` | ASCII 草图（视频本体/封面/黑条/徽章） |
| `assets/style-options.md` | 4 种风格的对比 + 适用场景 + ASCII 草图 |
| `assets/task-config.sample.json` | **Step 0 任务配置模板**（4 开关 + TTS 4 接入方式）|
| `assets/tts-config.sample.json` | 用户自定义 TTS 配置样例（4 必填 + 3 可选）|

---

## 四、触发本 skill 的场景

**用户提到下列任意一项时使用本 skill**：

- 短视频 / 知识视频 / 知识科普视频 / 知识类短视频
- 口播稿 / 单人口播 / 60-90s / 9:16 / 竖版
- 封面风格 / swiss-grid / warm-grain / nyt-graph / embedded-captions
- 3:4 封面 / 公众号头图封面 / 封面设计
- TTS 配音 / 系统默认 TTS / 自定义配音大模型（4 参数 / 文档链接 / 代码路径）
- GSAP 动画视频 / 短视频动画 / 不是图片拼接
- 短视频发布包 / 小红书发布 / 抖音发布 / 视频号发布
- 是否放 IP 信息 / 是否引导关注 / 4 个开关
- "做一条 AI 工具实操视频" / "做一条美食教程" / "做一条职场技能分享" / "把 XX 知识点做成视频" / "用我的声音做配音"

---

## 五、核心铁律（必看 · 违反任何一条必返工）

### H 系列（阻断性硬错误 · 借鉴自 ai-cut pipeline）

> **这些不是警告，是 lint / resync / render 工具会自动拦截并中止的硬错误**。任何一条为真 → 修完再继续，**不会**产出一个残缺视频。详情 + 触发场景：[`reference/06-pitfalls.md` §6.0](reference/06-pitfalls.md)。

| # | 硬错误 | 一句话说明 |
|---|---|---|
| **H1** | **段数与模板占位符对不上** | 模板里 N 个 `__S*__`，segments.txt 必须正好 N 段。对不上 = lint 拒绝 |
| **H2** | **残留 `__XXX__` 占位符** | resync 后还有未替换占位符 = 直接报错 |
| **H3** | **配音片段时间重叠** | timeline 相邻段 start/end 重叠 = 全黑视频根因（V9 教训）|
| **H4** | **timed 元素缺 `data-track-index`** | 每个真 clip 必须有（根时间线豁免）|
| **H5** | **BGM 音量 > 0.25** | 旁白满音量正常，**只有 BGM**会被查 |

### 12 条常规铁律

1. **Step 0 必走**：开始前**一次性**问用户 4 个开关（封面风格 / IP 信息 / 引导关注 / 配音大模型），用户沉默走默认。用户没指定就当默认处理，但**必须问过**。
2. **第一句话必须把人留住**。前 3 秒留不住人，后面写得再好也没用——用户已经划走了。
3. **绑定具体工具 / 食材 / 案例 + 真实场景**。"AI 工具很好用" ❌ → "Cursor 进了我日常写作流，每周省 10 小时" ✅。[美食] "做了 20 次才稳定" ✅。[职场] "5 年 HR 看过的 1000 份简历" ✅。
4. **小白能看懂是硬要求**。术语翻译 + 类比 + 数字 + 原始数据 + 行动项拆分，每条稿子过 7 项自检表。
5. **总段数 ≥ 20 句**（硬下限，不含标题）。少于 20 句 = 内容没展开。
6. **封面风格默认 swiss-grid**。其他 3 种（warm-grain / nyt-graph / embedded-captions）由用户在 Step 0 明确指定才用。
7. **IP 信息默认不放 / 引导关注默认不放**。商业感越弱，平台越推荐。
8. **最终一定是动画视频，不是图片拼接**。GSAP `fromTo` 驱动元素动效，不允许 ffmpeg concat 静态图。
9. **发布包固定 3 文件**。竖版短视频最小发布包 = 视频 + 1 张封面 + 1 份文案，不要默认全套。
10. **任务目录带时间戳**。`YYYYMMDD_HHMMSS_<任务名>`，连续任务不冲突。
11. **每个 Step 完成后立刻清理中间产物**。验证截图、预览图、测试 HTML、中间 wav、原始帧 = 脏数据。
12. **第 0 帧必须有可见内容**（铁律 #0）— 第一个 clip 不能从 `opacity: 0` 进入，否则用户打开看到的就是空白 + 渐入动画。3 种方案见 [Step 4 铁律 #0](reference/04-production.md#铁律-0--第-0-帧必须可见必读--实战踩坑)，方案 A 首选。

> 完整铁律 + 踩坑清单见 [`reference/06-pitfalls.md`](reference/06-pitfalls.md)。

---

## 六、7 步流程（每期必走）

| Step | 做什么 | 详见 |
|---|---|---|
| **Step 0** | **4 开关一次性问完**（封面风格 / IP 信息 / 引导关注 / 配音）| [`reference/04-production.md#step-0`](reference/04-production.md) |
| **Step 1** | 写口播稿（Hook + 正文 + 结尾，**≥ 20 句**）+ 拆 segments.txt + **用户确认** | [`reference/02-script.md`](reference/02-script.md) + [`reference/04-production.md#step-1`](reference/04-production.md) |
| **Step 2** | 按 Step 0 选定风格，落地视觉规范（写 `02-VisualSpec/visual-spec.md`）| [`reference/03-visual-spec.md`](reference/03-visual-spec.md) |
| **Step 3** | 生成 3:4 封面（v1/v2/v3 变体管理）| [`reference/03-visual-spec.md`](reference/03-visual-spec.md) |
| **Step 4** | 写 composition（**GSAP fromTo · 动画视频**）+ 4 条硬约束 | [`reference/04-production.md#step-4`](reference/04-production.md) |
| **Step 5** | TTS 配音（默认 / 自定义 3 接入方式）→ `05-Audio/narration.wav` + `timeline.json` | [`reference/04-production.md#step-5`](reference/04-production.md) |
| **Step 5.5** | **一键变体脚本**（借鉴自 ai-cut pipeline）：v1/v2/v3 用同一模板换配音不返工 | [`reference/04-production.md#step-55--一键变体脚本借鉴自-ai-cut-pipeline`](reference/04-production.md) |
| **Step 6** | 注入时间 + render（CDP 单 Chrome 长连接 + 实测时长反向同步 + 自动拦截 H1-H5 硬错误）| [`reference/04-production.md#step-6`](reference/04-production.md) |
| **Step 7** | 拼 3 文件发布包到 `07-Publish/`（按 Step 0 决定 IP / CTA）| [`reference/04-production.md#step-7`](reference/04-production.md) |

> ⚠️ **顺序不可乱**：先 Step 0 → Step 1 文本确认 → Step 5 TTS（文本没确认就合成 = 100% 返工）。
> ⚠️ **同任务变体一致性**：v1/v2/v3 必须保持 4 开关一致（开关变了 = 开新任务）。

---

## 七、Step 0 的 4 个开关速查

> **用户沉默 → 全部走默认**：A swiss-grid / 不放 IP / 不引导关注 / 默认 TTS。
> 完整 SOP 见 [`reference/04-production.md` §0.1](reference/04-production.md)。

| # | 开关 | 默认值 | 用户明确时的行为 |
|---|---|---|---|
| ① | 封面风格 | **A · swiss-grid** | 4 选 1：A swiss-grid / B warm-grain / C nyt-graph / D embedded-captions |
| ② | IP 信息 | **false** | true = 封面/视频脚注放 `@<用户IP名>` + `<slogan>`（由用户提供）|
| ③ | 引导关注 | **false** | true = 结尾加关注 CTA（用户提供话术，可选预设："关注我，下期接着聊"）|
| ④ | 配音大模型 | **系统默认 TTS** | 用户提供 4 参数 / API 文档链接 / 客户端代码路径 任选 1 |

---

## 八、与其他 skill / 文档的关系

| Skill / 文档 | 何时用 |
|---|---|
| **`knowledge-short-video`（本 skill）** | 做 9:16 60-90s 知识类短视频全流程 |
| `viral-title` skill（外部）| 生成 publish.md 的标题（3 选 1）|
| `公众号文章创作指南.md` | 把口播稿扩写成深度公众号文章 |
| `AI 博主创作更新建议.md` | AI 主题账号的定位与栏目策略母版（其他主题可忽略）|
| 官方 HyperFrames 模板 | [hyperframes.mintlify.app/showcase](https://hyperframes.mintlify.app/showcase) |

本 skill **不写**横版 / 长视频 / 公众号配图（那些不在本 skill 范围内）。
本 skill **不写**具体任务的实战细节（直接按 7 步在任务目录里走，不写额外的 PLAN 文件）。
本 skill **强制输出动画视频**——纯图片拼接不在本 skill 范围内。

---

## 九、更新规则

出现以下情况之一，本 skill 需要更新：

1. 新的工程决策（如换 TTS 引擎、换渲染管线）
2. 新的踩坑清单（如新的视觉错误、新的发布平台规范）
3. 新的 SOP（如新的封面迭代流程、新的发布包模式）
4. 实战案例的更新（如 netflix 之外的新任务沉淀）

**更新原则**：

- 不做版本号：连续维护的单一文档，所有任务共享一份
- 不做版本日志：有新规则直接改正文，历史从 git 查
- 跨任务的全局改动 → 直接修改正文
- 单任务的特殊经验 → 写到该任务的 `经验总结.md`，不污染本 skill