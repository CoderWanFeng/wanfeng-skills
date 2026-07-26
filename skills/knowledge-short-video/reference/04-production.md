# 四、8 步制作流程（"怎么做"）

> 拿到口播稿后，按本章 **Step 0 → Step 1-7** 走完 → 出 1 份 3 文件发布包 → 直接发小红书 / 抖音 / 视频号。
>
> ⚠️ **Step 0 是 4 个开关**（**必须在 Step 1 之前一次性问完用户**）→ 这是整个流程里**唯一不可跳过的步骤**。

## 0.0 任务目录结构（标准约定 · 必读）

> ⚠️ **每个任务 = 一个独立目录**。因为可能连续做多个任务，目录名带**时间戳**避免重名。

```
<workspace>/<YYYYMMDD_HHMMSS>_<任务名>/     ← 任务根目录
├── task-config.json                        ← Step 0 4 开关
├── 01-Script/                              ← Step 1 口播稿 + 拆段
│   ├── script.md
│   ├── segments.txt                        ← ≥ 20 段（硬下限）
│   └── reverse-check.md                    ← 段↔句 映射表
├── 02-VisualSpec/                          ← Step 2 视觉规范
│   └── visual-spec.md
├── 03-Cover/                               ← Step 3 封面（多版本时建 v2/ v3/ 子目录）
│   ├── cover-v1.html
│   ├── cover-v1.png          ← 验证用
│   └── cover.png             ← 选定版（v1/v2/v3 之一）
├── 04-Composition/                         ← Step 4 GSAP 动画视频模板
│   └── composition.html
├── 05-Audio/                               ← Step 5 TTS 配音
│   ├── tts-config.json       ← 用户自定义 TTS 时填
│   ├── segments/             ← 每段独立 wav（中间产物）
│   ├── narration.wav         ← 拼接后的完整配音
│   └── timeline.json         ← 实测时长 + 段↔句 映射
├── 06-Render/                              ← Step 6 渲染
│   ├── render.py
│   └── video_full.mp4        ← 最终 mp4（封面用的源）
└── 07-Publish/                             ← Step 7 发布包（3 文件精简版）
    ├── cover.png             ← 从 03-Cover/ 复制
    ├── video_full.mp4        ← 从 06-Render/ 复制
    └── publish.md            ← 标题 + 简介 + hashtag
```

**目录命名规则**：

| 阶段 | 旧名 | 新名 |
|---|---|---|
| Step 1 | 准备口播稿 | `01-Script/` |
| Step 2 | 选模板定视觉规范 | `02-VisualSpec/` |
| Step 3 | 生成封面 | `03-Cover/` |
| Step 4 | 写composition | `04-Composition/` |
| Step 5 | 合成配音 | `05-Audio/` |
| Step 6 | 注入渲染 | `06-Render/` |
| Step 7 | 发布包 | `07-Publish/` |

**任务根目录命名规则**：

```
格式：YYYYMMDD_HHMMSS_<任务名>
示例：20260629_203000_什么是Token
```

> ⚠️ **禁止**用 `Process/` 这种语义空泛的目录名。任务目录必须带**任务名 + 时间戳**。

### 0.0.1 中间产物清理（必读）

> ⚠️ **每个 Step 完成后立刻清理中间产物**。最终交付只保留必要的成品。

| 阶段 | 必须删掉的中间产物 |
|---|---|
| Step 1 | `script.md` 的早期 v0/v1 草稿（保留最终 v2） |
| Step 3 | 验证用的 `cover-v1.png`/`v2.png`/`v3.png`（保留选定的 `cover.png`）|
| Step 3 | 用过的临时 HTML 草稿 `cover-test*.html` |
| Step 4 | composition 验证截图 `composition_preview_t*.png` |
| Step 5 | `segments/` 子目录里的每段独立 wav（保留拼接后的 `narration.wav`）|
| Step 6 | 渲染中间产物 `frames/frame_*.png` 几千张图（保留 `video_full.mp4`）|
| Step 7 | 中间产物**绝不进发布包**（详见 [§7.4 不放进发布包的文件](#74-不放进发布包的文件)）|

**经验法则**：

- ✅ 保留：成品（cover.png / video_full.mp4 / narration.wav）+ 配置（task-config.json / tts-config.json / timeline.json）
- ❌ 删除：截图、预览图、测试 HTML、中间 wav、原始帧

### 0.0.2 一键脚手架（Step 0 进入时跑 · 借鉴自 ai-cut pipeline §7）

```bash
task=<带任务名的字符串，不要带空格>
TS=$(date +%Y%m%d_%H%M%S)
ROOT="${TS}_${task}"

# 1. 一次性建好 7 个子目录（含 segments/、samples/ 兜底）
mkdir -p "$ROOT"/{01-Script,02-VisualSpec,03-Cover,04-Composition,05-Audio/segments,06-Render/snapshots,07-Publish}

# 2. 把 Step 0 的任务配置骨架拷过去（用户后续编辑填写 4 开关）
cp "$(dirname "$0")/../assets/task-config.sample.json" "$ROOT/task-config.json"

# 3. 打印完成提示
echo "✅ 任务目录已创建：$ROOT"
echo "   下一步：在 $ROOT/task-config.json 里确认 4 个开关。"
```

> 借鉴自 `ai-cut/pipeline` 的 §7 一键脚手架：连续做 5 期以上视频 = 必须脚手架，否则第一步就栽在目录命名上。

## 总览流水线

```
                           ┌─────────────────────────┐
                           │ [Step 0] 4 个开关一次性问完 │
                           │ ① 封面风格 4 选 1       │
                           │ ② IP 信息（默认 false）   │
                           │ ③ 引导关注（默认 false）   │
                           │ ④ 配音大模型（默认 / 自定义）│
                           └─────────────────────────┘
                                       ↓
口播稿
  ↓ [Step 1] 文本确认 + 拆段（≥ 20 段）
01-Script/{script.md, segments.txt, reverse-check.md}
  ↓ [Step 2] 按 Step 0 选定的风格，落地视觉规范
02-VisualSpec/visual-spec.md
  ↓ [Step 3] 生成 3:4 封面（多版本建 v2/ v3/ 子目录）
03-Cover/cover.png
  ↓ [Step 4] 写 composition.html（GSAP fromTo · **动画视频**不是图片拼接）
04-Composition/composition.html
  ↓ [Step 5] TTS 合成（默认 / 自定义按 Step 0）
05-Audio/{tts-config.json, narration.wav, timeline.json}
  ↓ [Step 6] 注入时间 + render
06-Render/video_full.mp4  ← 这是动画视频（GSAP timeline 驱动）
  ↓ [Step 7] 拼发布包（按 Step 0 决定是否放 IP / 是否加 CTA）
07-Publish/{cover.png, video_full.mp4, publish.md}
```

---

## Step 0 · 开始前 4 个开关（必走 · 不可跳过）

> ⭐ **本步是流程里唯一不可跳过的步骤**。
> **不写稿、不拆段、不选风格、不调 TTS**——先把 4 个开关答案定下来。

### 0.1 第一句话（必须一次问完，不要拆开问）

> "在开始做视频之前，我先确认 4 个开关：
>
> **1. 封面风格**用哪种？（swiss-grid · 默认 / warm-grain / nyt-graph / embedded-captions）
> **2. 是否放 IP 信息**？（你的 IP 名 + slogan · 默认 **不放**。如果要放，你提供自己的 IP 名称和 slogan。）
> **3. 结尾是否引导关注**？（关注 CTA · 默认 **不放**。如果放，你提供自己的引导话术。）
> **4. 配音用哪个大模型**？（默认 = 系统默认 TTS / 自定义 = 你提供 [文档链接 / 代码路径 / 4 个参数]）
>
> 都不指定就走默认（A swiss-grid / 不放 / 不放 / 默认 TTS）。"

### 0.2 4 个开关的默认值与判定规则

| 开关 | 默认值 | 用户确认 / 沉默 → 默认 | 见 |
|---|---|---|---|
| ① 封面风格 | A · swiss-grid | → A | [`03-visual-spec.md` §3.1](../reference/03-visual-spec.md) |
| ② IP 信息 | **false** | → false（不放） | [`03-visual-spec.md` §3.6](../reference/03-visual-spec.md) |
| ③ 引导关注 | **false** | → false（不放） | [`02-script.md` §2.7](../reference/02-script.md) |
| ④ 配音大模型 | 系统默认 TTS | → 默认 | [§5.1 配音大模型选择](#51-配音大模型选择sop--开始前必走)（本章）|

### 0.3 任务配置保存

把 4 个开关答案写到任务根目录的 `task-config.json`：

```bash
cp assets/task-config.sample.json \
   <task>/task-config.json
# 编辑填写 4 个开关
```

完整 JSON schema + 填写示例见 [`assets/task-config.sample.json`](../assets/task-config.sample.json)。

### 0.4 同任务变体一致性（硬约束）

> ⚠️ **同任务的所有变体（v1/v2/v3）必须保持 4 个开关一致**。
> - v1 默认、v2 自定义 TTS = 不可（**会出现两个完全不同的视频**）
> - 一旦选定，整个任务生命周期内不变；要换开关 = 开新任务

### 0.5 Step 0 自检清单（写完后过一遍）

- [ ] 4 个开关**全部**问完用户？
- [ ] 用户沉默 → 全部走默认（A swiss-grid / 不放 / 不放 / 默认 TTS）？
- [ ] 用户回的部分开关 → 其他沉默按默认处理？
- [ ] `task-config.json` 已保存到任务根目录？
- [ ] 没有替用户做决定？
- [ ] 任务根目录名带时间戳 `YYYYMMDD_HHMMSS_`？

---

## Step 1 · 准备口播稿 + 拆段（segments.txt）

> 见 [`reference/02-script.md` §2.X 分段规范](../reference/02-script.md)。

写完脚本后**立刻分段**（≥ 20 段），分段文件 = TTS 配音 + composition 视觉 + 反向同步的唯一数据源。

**交付**：`01-Script/segments.txt`（用户确认版本）+ `01-Script/script.md` + `01-Script/reverse-check.md`。

### 输入分流

- **A 路 · 知识点形式**：用户提供零散知识点 / 概念 / 要点 → 先**聚合为口播稿**（Hook + 正文 + 结尾三段式），再进入下方"复核 + 拆段"
- **B 路 · 已成稿文档**：用户提供现成的口播稿 / 文章 / 博客 / 教程 → 直接进入下方"复核 + 拆段"
- 无论 A/B，最终都要落到 `segments.txt`，交付形态一致

### 复核口播稿

- 时长 **60-90s**，字数 **250-380 字**
- 包含 Hook（3s）+ 正文（是什么/为什么/怎么用）+ 结尾（5-10s）
- 结尾元素（关注引导 + slogan）**可选**，由创作者根据发布场景决定
- 必须满足 [`reference/02-script.md`](../reference/02-script.md) 的全部硬规则

### 拆 segments.txt

- **格式**：每行 `段号 | 段类型 | 文本`，纯文本
- **段类型**：hook / persona / main / recap / transition / cta
- **总段数 ≥ 20**（硬下限，不含标题）
- 一段 ≤ 30 字 / ≤ 8 秒；超过就拆
- 标点要全（、`。！？），半角 `,;.` TTS 读不顺
- **emotion 标签可选**：见 Step 5
- 段间留 0.15s 静音间隔（拼接 narration.wav 时插入）

### reverse-check.md（反向同步用）

> 把段号映射回口播稿的句号，方便 Step 6 反向同步时定位问题段。

```markdown
# Reverse Check · <任务名>

| 段号 | 段类型 | 对应口播稿句号 | 文本 | 实测时长 |
|---|---|---|---|---|
| 01 | hook | 句 1 | AI 按字收费... | 3.76s |
| 02 | persona | 句 2 | 我是<IP名>... | 4.74s |
| ... |
```

### 已知坑

- ❌ 不要在这一步就调 TTS。两件事分开做。
- ❌ 不要在 segments.txt 里用半角标点。
- ❌ A 路（知识点形式）不要跳过"聚合为口播稿"环节直接拆段——**结构化先于分镜**。
- ❌ 总段数 < 20 = 内容没展开，禁止交付。
- ❌ 验证用的预览截图/中间 HTML/早期 wav 必须删（见 [§0.0.1](#001-中间产物清理必读)）。

> ⚠️ **用户确认文本后再进 Step 2**。文本没确认就调 TTS = 浪费调用 + 重对音画（V7 教训）。

**交付**：`01-Script/{script.md, segments.txt, reverse-check.md}`。

---

## Step 2 · 锁定 swiss-grid 视觉规范

> 见 [`reference/03-visual-spec.md`](../reference/03-visual-spec.md)。

直接复用第 3 章 3.1-3.2 的规范，写入 `02-VisualSpec/visual-spec.md`。

**交付**：`02-VisualSpec/visual-spec.md`（本期确认 + swiss-grid DNA）。

---

## Step 3 · 生成封面（swiss-grid 体系）

> 基于 [3.3 封面设计规范](../reference/03-visual-spec.md)，用 HTML 渲染生成 **1 张主封面**（3:4 1080×1440，swiss-grid 风格），用于发布包。

### 3.1 复制 swiss-grid 封面骨架

```bash
# 1. 复制上一期的 03-Cover/cover.html 骨架
cp <上一期>/03-Cover/cover.html \
   <本期>/03-Cover/cover-v1.html

# 2. 改主标 / 副标 / 视觉锤（保持 swiss-grid DNA 不变）
# 3. Chrome headless 渲染
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --no-sandbox --window-size=1080,1440 \
  --screenshot=cover-v1.png cover-v1.html
```

### 核心结构（与视频本体完全一致）

- 顶部红色横条：`<主题> · KICKER`（**默认不放期号**，仅系列视频才加）
- 主视觉区：巨型数字 / 核心问句 / 视觉锤
- 底部黑条：工具条 + 脚注
- 配色：白 `#fff` + 黑 `#0a0a0a` + 红 `#E30613`（3 色限定）

### 比例

- **唯一 3:4 1080×1440**（各平台通用，不会被裁切）
- 禁止 9:16、16:9、1:1 多尺寸
- 禁止裁切

### 已知坑

- ❌ 用暗底 + 金字 + 人物出镜（已废弃）
- ❌ 用 9:16 比例（9:16 上传平台会被裁切，必须用 3:4）
- ❌ 用其他配色（蓝/绿/紫/橙）
- ❌ 覆盖 v1 封面（建 v2 子目录，**绝不覆盖**）
- ❌ 字太多，重点不突出
- ✅ 严格遵循 swiss-grid DNA（白底 + Helvetica + 红黑）
- ✅ 浮动徽章 ≥40px 缓冲带

**交付**：`03-Cover/cover.png`（最终选定的版本，可多个变体）。

> ASCII 布局草图见 [`assets/cover-layouts.md`](../assets/cover-layouts.md)。

---

## Step 4 · 写 composition.html（GSAP fromTo）

> ⚠️ **这一步产出的是动画视频，不是图片拼接**。详见下方"动画视频 vs 图片拼接"对比。

### ⚠️ 动画视频 vs 图片拼接（必看）

> **本 skill 的最终交付一定是动画视频**——由 GSAP timeline 驱动的连续动效。
> **不允许**：把所有场景渲染成图片 → ffmpeg concat → 冒充视频。

| 维度 | ❌ 图片拼接（禁止） | ✅ 动画视频（本 skill）|
|---|---|---|
| **生产方式** | 每帧渲染为静态图 → ffmpeg concat | GSAP timeline 驱动元素动效 |
| **动效** | 无（全静态）| 进场淡入 / 退场淡出 / stagger / 缓动 / SVG 绘制 |
| **音频** | wav | wav + GSAP timeline 同步 |
| **代码量** | 一堆 PNG + concat 脚本 | 1 个 HTML + GSAP timeline |
| **复用性** | 改一字 = 重渲所有图 | 改文案 = 改 data dict 即可 |
| **观众感知** | 像 PPT 翻页 | 像短视频 |

**GSAP 必备元素**：

- `gsap.fromTo()` 起始/结束态双定义（V9 教训，`from()` 会跳变）
- timeline 必须 `paused` 且注册到 `window.__timelines[composition-id]`
- 视觉段和音频段**同一份时间精度**（3 位小数 + 0.01s gap）
- 每个 timed 元素必须有 `data-start` + `data-duration` + `data-track-index` + `class="clip"`
- **第 0 帧必须可见**（见下方铁律 #0）

### 模板架构

```
src/<template>/composition.template.html    ← 唯一视觉源（含 __VAR_XXX__ 占位符）
tasks/<task>/work/composition.html          ← resync.py 注入实际时间后产物
```

### 核心模式（V9 教训 · 已锁定）

| ❌ 错误写法 | ✅ 正确写法 | 原因 |
|---|---|---|
| `tl.from("#s1 .big", {opacity: 0, y: 40})` | `tl.fromTo("#s1 .big", {opacity: 0, y: 40}, {opacity: 1, y: 0, duration: 0.5, ease: "power2.out"})` | inline 初始属性导致视觉跳变 |

### 4+1 条硬约束（不遵守会 lint 报错）

1. 每个 timed 元素必须有 `data-start` + `data-duration` + `data-track-index` + `class="clip"`
2. timeline 必须 paused 且注册到 `window.__timelines[composition-id]`
3. 视频 `muted` + 单独 `<audio>` 元素
4. 只用确定性逻辑（**禁** `Date.now()` / `Math.random()` / 网络 fetch）
5. **第 0 帧必须有可见内容**（绝不能是空白）

### 铁律 #0 · 第 0 帧必须可见（必读 · 实战踩坑）

> ⭐ **最常被忽略的一条**。用户打开视频的第一眼 = 第 0 帧。如果第 0 帧是空白 = 用户立刻划走 = 完蛋。

**问题表现**：

```javascript
// ❌ 错误：第一个 clip 用 fromTo 从 opacity:0 开始
tl.fromTo("#s1-hook", { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.5 }, 0.0);
// ↓
// 第 0 帧：opacity=0（空白）
// 第 0.25 帧：opacity=0.5（半透明）
// 第 0.5 帧：opacity=1（才完全可见）
// 用户在前 0.5 秒看到的是空白 + 渐入动画
```

**正确写法 · 3 种方案**（选 1）：

**方案 A · 第一个 clip 只动位置，不动透明度**：

```javascript
// ✅ 第一个 clip：CSS 默认 opacity:1，fromTo 只动 y
tl.fromTo("#s1-hook", { y: 60 }, { y: 0, duration: 0.5, ease: "power2.out" }, 0.0);
// 第 0 帧：opacity=1（立刻可见）+ y=60（下方）
// 第 0.5 帧：opacity=1（一直可见）+ y=0（到位）
```

**方案 B · 第一个 clip 的动画在 t=0 之前完成**：

```javascript
// ✅ 第一个 clip 起点用负时间，到 t=0 时已结束
tl.fromTo("#s1-hook", { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.5 }, -0.5);
// 第 0 帧：动画已结束，opacity=1（直接显示）
```

**方案 C · 第一个 clip 强制 inline opacity:1，跳过进场动画**：

```html
<!-- ✅ 第一个 clip 不写 fromTo，CSS 直接 opacity:1 -->
<div class="clip first" data-track-index="0" data-start="0.000" data-duration="3.760" id="s1-hook">
  <div class="hero-text">...</div>
</div>
```

```css
.clip.first { opacity: 1 !important; }
```

**经验法则**：

- ✅ **方案 A 首选**（最简洁，进场动画保持完整）
- ✅ 后续 clip（s2 / s3 / ...）正常用 `fromTo(..., {opacity: 0, y: 60}, {opacity: 1, y: 0})`
- ❌ 禁止：所有 clip 全部从 opacity:0 进入（包括第一个）
- ❌ 禁止：第 0 帧依赖 GSAP 渲染（GSAP 渲染前 = 空白）

### 已知坑

- 所有 `data-start` / `data-end` 用 Python 计算到 **3 位小数 + 0.01s gap**
- 视觉段和音频段必须用**同一份**时间精度（不能 visual 2 位 + audio 3 位）
- `bg` 黑色露出边缘 → 显式 `html,body{background:#fff}` + 每个 section 单独 bg
- 大脚本 `write` 工具 JSON parse 失败 → 改用极简生成器（57 行模板 + 数据 dict）
- **第 0 帧空白** → 第一个 clip 不能从 opacity:0 进入（见铁律 #0 + 3 种方案）

**交付**：`src/<task>/composition.template.html`（含完整 section + GSAP 时间线）。

---

## Step 5 · 合成 TTS 配音

把 `segments.txt` 合成 N 段独立 wav + `timeline.json`。**每段必须带情绪**（不许纯 neutral 一路念到底）。

### 5.1 配音大模型选择（SOP · 开始前必走）

> 🆕 **第一步不是调 TTS，是问用户用哪个配音。**

**第一句话**问用户：

> "配音用 **系统默认** 还是 **自定义配音大模型**？
>
> - **默认** = 系统默认 TTS（开箱即用，零返工）
> - **自定义** = 你提供 [API 端点 / API Key 环境变量名 / Voice ID / 速度] 4 个参数（任意支持 SSML 或情感标签的 TTS：Azure / 阿里云 / 火山引擎 / 自建 / 一口价克隆音 等都支持），或提供 API 文档链接，或提供本地客户端代码路径"

**判定规则**：

- 用户**没指定**或回"用默认" → 走 [§5.2 系统默认配置](#52-系统默认配置)
- 用户**提供自定义素材** → 写入 `05-Audio/tts-config.json`，走 [§5.3 自定义配置](#53-用户自定义-tts-配置)

> ⚠️ **不要替用户做选择**。哪怕你"觉得"用默认更省事，也要先问 → 用户沉默或确认后才动。
> ⚠️ **同一个任务的变体之间要保持一致**（同一期视频不能 v1 用默认、v2 换自定义）—— 选择一次，整个 task 复用。

### 5.1.1 自定义 TTS 的 3 种接入方式（用户任选）

> 用户提供自定义配音大模型时，**3 种接入方式选 1 个就行**，不要求全填。

**方式 A · 直接 4 个参数**（最轻量）

用户口头回复：

> "用我的火山引擎 TTS，API 端点是 `https://openspeech.bytedance.com/api/v1/tts`，API Key 在环境变量 `VOLC_TTS_KEY` 里，Voice ID 用 `BV001_streaming`，速度 1.0x。"

→ 直接写到 `tts-config.json` 的 `config_json_inline` 字段。

**方式 B · API 文档**（用户懒得写参数时）

用户提供一个文档（如 `tts-docs/my-tts.md`），说明：

- API 端点 + 请求方法
- 鉴权方式（环境变量名 / Header / Query）
- Voice ID 列表
- 速度参数范围
- 情感支持（是/否/格式）
- 返回格式（wav/mp3/opus）
- 一个 curl / Python 调用示例

→ 把文档路径写到 `config_doc_path` 字段，从文档提取 4 个必填参数。

**方式 C · 客户端代码**（用户有现成 SDK 时）

用户提供一段 Python / JS 代码（如 `tts-clients/my_client.py`），调用函数是 `synthesize(text, voice, speed) → wav_bytes`。

→ 把代码路径写到 `config_client_code_path` 字段，agent 读取源码后：

- 识别函数签名
- 提取鉴权环境变量名
- 把 `tools/tts/custom-tts.py` 的逻辑替换成调用这个 SDK

→ 样例见 [`assets/tts-config.sample.json`](../assets/tts-config.sample.json)。

**判定**：3 种方式选 1 → 不可同时多个（防歧义）。如果用户给了多个，选最先说的那种。

### 5.2 系统默认配置

| 项 | 值 |
|---|---|
| **引擎** | 系统默认 TTS（开箱即用，无需用户配置）|
| **声音 ID** | 系统默认音色 |
| **速度** | **1.0x**（1.3x 仅 dev 预览，不用于发布）|
| **API 端点** | 系统默认（无需用户配置）|
| **API Key** | 系统默认（无需用户配置）|
| **情绪** | 支持 5 种：`neutral` / `happy` / `surprised` / `sad` / `angry` |

### 5.3 用户自定义 TTS 配置

#### 5.3.1 必填 4 个参数（用户必须提供）

| 参数 | 含义 | 示例 |
|---|---|---|
| `tts_endpoint` | API 端点 URL | `https://your-tts.example.com/v1/synthesize` |
| `tts_api_key_env` | API Key 在**环境变量里**的字段名（不要直接给 key）| `MY_TTS_API_KEY` |
| `tts_voice` | Voice ID / 声音标识 | `<your-voice-id>` / `aliyun-zhixiaobai` |
| `tts_speed` | 速度倍数（建议 1.0x）| `1.0` |

#### 5.3.2 可选 3 个参数（不提供就用默认）

| 参数 | 默认 | 含义 |
|---|---|---|
| `tts_model` | 引擎默认模型名 | 引擎有多个 TTS 模型时指定（如 `tts-1` / `tts-1-hd`）|
| `emotion_support` | `true` | 引擎是否支持情绪标签 |
| `emotion_format` | `[emotion]` | 情绪标签格式（`[emotion]` / `<emotion>` / `(emotion)` 三选一）|

#### 5.3.3 配置文件位置

写到任务目录的 `05-Audio/tts-config.json`：

```bash
cp assets/tts-config.sample.json \
   <task>/05-Audio/tts-config.json
```

样例见 [`assets/tts-config.sample.json`](../assets/tts-config.sample.json)。

#### 5.3.4 情绪兼容性处理

如果用户的引擎 **不支持情绪标签**（`emotion_support=false`）：

1. 合成前自动剥掉所有 `[emotion]` 标签
2. 改用语气词（！/？/……）和标点变体表达情绪
3. 后续配 `narration.wav` 时 emotion 信息会丢失——靠"反转用 ↑升调、警告用 ↓降调"的 SSML 提示或重录兜底

#### 5.3.5 已知坑（自定义引擎）

- ❌ **不要直接拿 API Key 写入配置文件** → 必须用环境变量名（防止泄露到 git）
- ❌ **不要假定所有引擎都支持 emotion 标签** → 先用 1 段测试 wav 验证
- ❌ **不要假定所有引擎都返回 wav/mp3** → Azure 返回 mp3、自建可能返回 opus，确认后选正确的拼接脚本
- ❌ **不要跳过 1 段测试就批量合成** → 1 段测音质 + 时长 → 通过后再批量
- ⚠️ **速度档位可能不同**（Azure 默认 1.0 但支持 0.5-2.0；阿里云 -500 到 +500 整数；其他引擎各异）→ 按用户引擎映射

---

### 5.4 命令

```bash
# 1. 单段 wav（独立，支持单段重试）
# 系统默认：
OUT_DIR=tasks/<task>/work/audio/variants/<v>/segments \
  python3 tools/tts/minimax-tts.py

# 用户自定义：先读 05-Audio/tts-config.json 自动适配
OUT_DIR=<task>/05-Audio/segments \
  CONFIG=<task>/05-Audio/tts-config.json \
  python3 tools/tts/custom-tts.py

# 2. 拼接 + timeline.json
SEGMENTS_DIR=tasks/<task>/work/audio/variants/<v> \
  VARIANT_NAME=<v> TTS_MODEL=<engine-model> TTS_VOICE=<voice-id> \
  ./tools/audio/concat-wav.sh
```

### segments.txt 情绪格式（**必带**）

```
N	[emotion]	text
```

- **N**：段号（1, 2, 3...）
- **[emotion]**：情绪标签，必须是以下 5 个之一：
  - `neutral` — 陈述、定义、说明（**全篇最多 40%**）
  - `happy` — 反常识揭示、行动号召、好消息、结尾引导关注（可选）
  - `surprised` — 反转、惊讶、揭示（如"答案很反常识——"）
  - `sad` — 警告、避坑（如"不写这句，AI 把你爸画成别人"）
  - `angry` — 强烈批判（极少用）
- **text**：口播文本

### 情绪分配原则

| 段类型 | 默认情绪 |
|---|---|
| Hook（前 3 秒）| `happy` / `surprised` |
| 反转 / 揭示 | `surprised` |
| 行动号召 | `happy` |
| 好结果 / 数字冲击 | `happy` |
| 警告 / 避坑 | `sad` |
| 术语解释 / 陈述 | `neutral` |
| 结尾 CTA（可选）| `happy` |

### 禁止

- ❌ 全篇 neutral 一路念到底（生成的配音太平，没情绪）
- ❌ 每段都加情绪标签但没认真选（乱标 happy/sad）
- ❌ emotion 标签位置错（必须 `[emotion]` 在 text 前面，不是后面）

### 已知坑

- **emotion 参数必须在 `voice_setting` 内嵌套**，不能放 payload 顶层（V9 调试记录）
- 同一段不要重复 emotion 标签（否则 API 报错）
- 不要换 TTS 引擎对比效果，浪费时间
- **实测时长常超过预估**（V11 数据：预估 127.8s，实测 136.7s，+7%），靠 Step 6 的 sync-to-composition.py 反向同步修正

**交付**：`scene_NN.wav` × N + `narration.wav` + `timeline.json`。

---

## Step 5.5 · 一键变体脚本（借鉴自 ai-cut pipeline）

> 重复 TTS → 拼接 → 注入 → 渲染 4 步 = 浪费生命。本节沉淀"一条命令产出变体"，让 v1 默认 TTS / v2 自定义 TTS 能复用同一份 composition。

### 核心思想

```
变体 = 同一份 segments.txt + 同一份 composition 模板
     + 不同的 TTS 配置（引擎 / 声音 / 速度）
```

> ⚠️ **前提**：Step 0 选了 ④ = 默认 TTS 时，所有变体用同一引擎；如果用户在「v1 后改主意想换自定义 TTS」= **开新任务**（[§0.4 同任务变体一致性](#04-同任务变体一致性硬约束)）。

### 单变体命令（最少操作版）

```bash
# 标准流程：TTS → 拼接 → 注入 → QA → render → 抽帧
./tools/run-variant.sh <任务名> <变体名> [--engine default|custom] [--no-extract]

# 示例：
./tools/run-variant.sh 20260720_什么是Token v1 --engine default
./tools/run-variant.sh 20260720_什么是Token v2 --engine custom  # 用户后面想换声音？
```

> **注意**：本 skill 默认**不允许同一任务变体之间换引擎**（见 §0.4）。上例 `v2 --engine custom` 仅作为「V1 跑完、TTS 配置后来又改了」的兜底场景，**用前先确认是不是要新开任务**。

### 串行步骤与失败行为

脚本内部依次执行（**任一步失败即停、保留中间物**）：

```
[1/5] TTS        → 05-Audio/segments/scene_NN.wav
[2/5] concat     → 05-Audio/narration.wav + timeline.json（ffprobe 实测时长）
[3/5] resync     → 04-Composition/composition.html（同时拦截 §6.0 五条硬错误）
[3b/5] QA        → 自动跑 §6.0 H1-H5 + composition 4 条硬约束
[4/5] render     → 06-Render/video_full.mp4（npx hyperframes render）
[5/5] extract    → 06-Render/snapshots/v1/frame_*.png（12 帧 QA）
```

### 命令速查

| 目的 | 命令 |
|---|---|
| 一键产出变体 | `./tools/run-variant.sh <task> <v> [--engine default\|custom] [--no-extract]` |
| 跳过抽帧 | 同上加 `--no-extract` |
| 换口播稿 | `SEGMENTS_FILE=/path/to.txt ./tools/run-variant.sh ...` |
| 仅本地预览 | 加 `--engine default`，与正式发布共用模板 |

### 环境依赖

- `ffmpeg` / `ffprobe`（拼接 + 抽帧）
- `npx hyperframes` 或已安装的 `hyperframes` 二进制（**别用 npx 第一次**，会被交互确认卡住）
- 自定义 TTS 需对应 4 参数 + 客户端代码（[§5.1.1](#511-自定义-tts-的-3-种接入方式用户任选)）

> 借鉴自 `ai-cut/pipeline` 的 V9 教训（路径：`/Users/wanfeng/code/aiwf365/free-ai/ai-cut/pipeline/README.md`）：**一段命令、任一步失败即停**比手动四步效率高 5×、返工率降一半。
> 如果用户的工程里已有 `tools/run-variant.sh`，直接复用；没有的话，按本节各步骤（[§5.1](#51-配音大模型选择sop--开始前必走) / [§5.4](#54-命令) / [§6 4 步最小循环](#4-步最小循环)）拼一个 `run-variant.sh` 出来。

---

## Step 6 · 注入时间 + render

把 `timeline.json` 里的实测时间注入模板，渲染出无音/占位音的 mp4。

### 4 步最小循环

```bash
# 1. TTS（Step 5 已完成）
# 2. concat + timeline.json（Step 5 已完成）

# 3. 注入时间戳
python3 tools/video/resync.py \
  --template src/<task>/composition.template.html \
  --variant  tasks/<task>/work/audio/variants/<v> \
  --out      tasks/<task>/work/composition.html

# 4. 渲染
cd tasks/<task> && npx hyperframes render . --output output/video_<v>.mp4
```

### 已知坑

- ⚠️ `npm run dev` 是**长驻服务**（不是一次性命令），必须 `run_in_background: true` 后台跑
- F5+ 渲染全黑 / 截断 → 检查相邻 clip 是否真的 0.01s 分离
- **实测时长超过预估**：靠 `sync-to-composition.py` **反向同步**（用实测 audio 时长重算 visual 的 `data-start`），不要回头改 segments.txt

### ⚠️ `data-duration` 必须精确匹配 narration.wav 总时长

```bash
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 narration.wav
# → 115.21s
```

- **场景时长分配**：把总时长按 segments.txt 的累计时长分配到各 scene 的 `data-duration` 上
- **症状 A**：`data-duration` 设大（> 实际场景总时长）→ 67s-115s 之间视频全空白
- **症状 B**：`data-duration` 设小（< 配音时长）→ 配音被 `-shortest` 截断
- **执行顺序（硬性）**：
  1. 先完成 Step 5 TTS + concat narration.wav
  2. **测 narration.wav 实际时长**（ffprobe）
  3. 再分配各场景的 data-start / data-duration
  4. 最后再 render

**交付**：`composition.html`（已注入时间）+ `video_anim.mp4`（占位音）。

---

## Step 7 · 拼发布包（3 文件精简版 · 竖版短视频唯一模式）

> ⚠️ **做发布包前第一句话问用户**：发布包要几个文件？竖版短视频固定 **3 个**（视频 + 1 封面 + 1 文案）。

### 目录结构

```
07-Publish/
├── cover.png          (~50 KB, 1080×1440, 3:4 swiss-grid 选定版)
├── video_full.mp4     (~1-10 MB, 1080×1920, 5-30fps, 含配音)
└── publish.md         (标题3选1 + 简介 + hashtag + 引导关注可选)
```

### 封面

- **唯一比例 3:4 1080×1440**：从 `03-Cover/cover.png`（或 v2/v3 选定版）复制 → 改名为 `cover.png`
- **不要裁切**：平台自动适配比例，裁切会损失构图
- **不要出 1:1 / 4:3 / 9:16 / 16:9 / 640 多尺寸**

### 视频

- **直接复制** `06-Render/video_full.mp4`
- 视频本体保持 9:16 1080×1920（视频比例 ≠ 封面比例）
- 不需要 `video_silent.mp4`（那是渲染中间产物）

### 文案 publish.md（从口播稿快速提炼 · 5 分钟）

> ⚠️ **标题必须用 viral-title skill 生成**（见 [`reference/02-script.md` §2.8](../reference/02-script.md)）。

```bash
# 复制发布包 3 文件
PUB=<task>/07-Publish
mkdir -p "$PUB"
cp 03-Cover/cover.png          "$PUB/cover.png"
cp 06-Render/video_full.mp4    "$PUB/video_full.mp4"
# publish.md 手工写（5 分钟）
```

### publish.md 模板

```markdown
# 发布文案 · <主题>

> 视频时长：~137s ｜ 平台：小红书 / 抖音 / 视频号
> 封面：cover.png ｜ 视频：video_final.mp4

---

## 标题（3 选 1 · viral-title skill 生成）
1. <反常识钩子>  ← 推荐
2. <数字冲击>
3. <行动钩子>

---

## 简介（正文）
<保留口播稿的 1-2 个核心类比 + 三件事行动清单>

---

## Hashtag
#<主题> #<主题>工具 #<主题>科普 #<主题>避坑 ...（8-10 个）

---

## [可选] 引导关注
> <用户提供的引导关注话术>
> *创作者可根据发布场景决定是否添加；若不添加，直接删除本节即可。*

---

## 评论区置顶话术
> <工具地址预告 + 下期预告>
```

### ⚠️ 简介去格式（发布平台不识别 Markdown）

- ❌ 简介里禁止出现 `**加粗**` `*斜体*` `- 列表项` `# 标题`
- ❌ Hashtag 里的 `` ` `` 反引号要去掉（平台识别为代码块）
- ❌ 行内的 `>` 引用标记要去掉
- ✅ 简介用纯文本 + 中文标点（，。：；！？）就行
- ✅ 列表用「第一/第二/第三」或「①/②/③」编号
- ✅ Hashtag 用空格分隔，不用 `` ` ``

### 已知坑

- ❌ 不要把渲染中间产物（silent.mp4 / segments / 测试 cover）放进发布包
- ❌ 不要给 1 张封面出 4 个尺寸再裁切 → 直接用原图
- ✅ 文案从口播稿摘录，**不要重新写**（保持口播稿的类比一致性）

---

## Step 8 · 发布到小红书

### 操作

1. 打开小红书创作者中心
2. 上传 `video_full.mp4`（9:16 1080×1920）
3. 选择 `cover.png` 作为封面（视频号会自动适配比例）
4. 粘贴 `publish.md` 里的标题 + 简介 + hashtag
5. 发布

### 发布后

- 评论区置顶（用 publish.md 的"评论区置顶话术"）
- 24 小时内回复前 20 条评论（提升算法推荐）

### 已知坑

- ⚠️ 小红书对视频长度敏感，**60-90s 最稳**（< 60s 太短，> 90s 完播率下降）。抖音 / 视频号同理。
