---
name: cover-hero
description: 为多平台文章 / 内容生成 HyperFrames 视觉风格的封面 + 配图。支持公众号、小红书、抖音、知乎、B站、微博、OG Card、Twitter Card 8 个平台 + 任意自定义尺寸（--width/--height/--ratio）。v5 起小红书 / 抖音有专用竖版模板（不再套横版崩布局），每个平台自动适配尺寸 + 风格档位 + 渲染后自检（字数 / 文件大小 / 尺寸 / 安全区）。封装 HTML 手写 + Puppeteer 渲染 + 平台适配层（独立 CSS 文件）；8 套空白模板（v5 +2 套竖版）、严格的命名规范、不可改动的视觉 DNA。支持 `--article` 自动读 MD frontmatter、`-i` 交互模式、多平台一键（`--platform wechat,xhs,douyin`）；v5.3 起 `--all-platforms` 一键全 8 平台 + `--output <dir>/` 自动按平台分子目录。当用户提到"做封面"、"配图"、"做头图"、"做信息图"、"小红书封面"、"抖音封面"、"视频帧"且文章主题明确时立即触发。
---

# cover-hero · 封面侠（多平台封面 & 配图）

> **目录名**：`cover-hero/`
> **中文名**：封面侠
> **发布时间**：v3 — 多平台扩展版（2026-07-01）

> 统一路径：**手写 HTML + Puppeteer 渲染 + HyperFrames 视觉风格系统**。
> 多平台：**公众号 / 小红书 / 抖音 / 知乎 / B站 / 微博 / OG Card / Twitter Card**。
> 不调 AI 生图（名人/Logo 走嵌入路径）。

---

## 何时使用

✅ **使用本 skill 的场景**：

- 给一篇文章做**多平台分发**的封面（同一篇内容在公众号 / 小红书 / 抖音 / 知乎等同步发）
- 给公众号文章做封面 + 正文配图
- 给小红书笔记做封面（3:4 / 9:16）
- 给抖音视频做封面（9:16）或视频帧（16:9）
- 给 B站视频做封面
- 给知乎专栏做头图
- 给微博 / 头条号做封面
- 给博客 / 链接预览做 OG Card / Twitter Card

❌ **不要使用**：

- 用户没说要图，只是纯文字聊天
- 文章主题不明（让用户先说"这篇文章讲什么"）
- 用户明确要求 AI 生图风格（这与本 skill 的视觉风格不兼容）
- 用户要完全脱离 HyperFrames 风格的视觉（建议用 Figma / PS）

---

## 交互流程（5 步对话 · v4 简化）

> **核心原则**：用户先提供内容（**文案先行**），再选平台和风格。这样能让用户在最低门槛下开始，避免一开始就面对"哪个平台"的选择困难。

### Step 1 · 收集文章主题

**Agent 问**：

```
要配什么内容？请告诉我：
1. 文章主题（一句话）
2. 主要观点（2-3 句）
3. 提到了哪些名人 / 大公司 / 工具（如 Sam Altman / OpenAI / Cursor 等）
4. 文章类型：横评 / 教程 / 故事 / 决策 / 对比
```

**用户回答** 示例：

> 主题：5 个 Codex 视频插件横评
> 观点：Codex 的视频生成插件质量参差不齐，我测了 5 个，推荐其中 2 个
> 提到：OpenAI、Cursor、Codex
> 类型：横评

---

### Step 2 · 提炼视觉锤

Agent 内部完成（**无需让用户回答**）：

1. **扫名人/大公司**：OpenAI / Cursor / Codex → 封面必须出现
2. **回答"三个问题"**：
   - 类型：横评 → 大数字「5」+ 工具卡片
   - 视觉锤：「5」（横评用大数字）
   - 读者下一步动作：选合适的插件（脚注做"按需选"）
3. **技术词翻译**：「Codex 视频插件」→ 「AI 拍视频的工具」

这一步的结果会告诉用户在 Step 5 编辑 5 区内容时怎么填。

---

### Step 3 · 选平台（**多选**）

**Agent 问**：

```
要发到哪些平台？（可多选）
- [ ] 公众号（2.35:1 标准封面）
- [ ] 小红书（3:4 笔记封面 / 9:16 故事图，高反差风格）
- [ ] 抖音（9:16 视频封面 / 16:9 横屏视频帧，戏剧风格）
- [ ] 知乎（16:9 专栏头图 / 4:3 文章配图）
- [ ] B 站（16:10 视频封面）
- [ ] 微博（5:4 头条封面 / 16:9 长文配图）
- [ ] OG Card（1.91:1 链接预览）
- [ ] Twitter Card（2:1 链接预览）
```

**用户回答** 示例：

> 公众号 + 小红书 + 抖音

> ⚠️ **平台越多，工作量越大**。建议一次选 ≤ 3 个平台，避免一次性出 10+ 张图导致迭代混乱。

详细规格见 [reference/platforms.md](reference/platforms.md)。

---

### Step 4 · 选风格档位（**单选**）

**Agent 问**：

```
默认是「标准 HyperFrames」风格。要调整吗？
- default（推荐）：完整 HyperFrames 视觉（米白底 + 黑顶栏 + 橙绿强调）
- compact：信息密度更高（教程 / 大量卡片场景）
- bold：吸睛更强（封面 / 故事场景）
```

> 所有档位**都基于 HyperFrames**，不引入新风格。可调维度只有：字号 / 间距 / 元素个数 / 装饰强度。

---

### Step 5 · 选产物类型（**自动推荐 + 用户确认**）

**Agent 问**：

```
每个平台默认产物清单：
- 公众号：1 张封面 + 0~7 张配图（按文章长度）
- 小红书：1 张笔记封面 + 0~5 张内页图
- 抖音：1 张视频封面（9:16）
- 知乎：1 张专栏头图 + 0~5 张文章配图
- B 站：1 张视频封面（16:10）
- 微博：1 张头条封面 + 0~3 张长文配图
- OG Card / Twitter Card：1 张链接预览

调整吗？或者直接「按默认走」？
```

---

### Step 5 · 渲染 + 迭代（v4 增强）

```bash
# === 方式 1：传统（多平台逐次跑）===
node assets/code/src/pick-template.js --platform wechat --type cover --output task/foo/imgs/wechat-cover-v1.html
node assets/code/src/pick-template.js --platform xhs --type cover --output task/foo/imgs/xhs-cover-v1.html
node assets/code/src/pick-template.js --platform douyin --type frame --output task/foo/imgs/douyin-frame-v1.html

# === 方式 2：v4 新增 · 一键多平台 ===
node assets/code/src/pick-template.js --platform wechat,xhs,douyin --type cover --output task/foo/imgs/

# === 方式 2.5：v5.3 新增 · 一键全 8 平台 ===
#  跑 wechat/xhs/douyin/zhihu/bilibili/weibo/og/twitter，无需列平台名
#  产物自动按平台分子目录：task/foo/imgs/<platform>/cover-v1.html
node assets/code/src/pick-template.js --all-platforms --output task/foo/imgs/

# === 方式 3：v4 新增 · 自动读 MD frontmatter（推荐）===
#  MD 头部加：
#    ---
#    type: tutorial
#    platform: wechat xhs douyin
#    ---
node assets/code/src/pick-template.js --article task/foo/foo.md

# === 方式 4：v4 新增 · 交互问答（适合新手）===
node assets/code/src/pick-template.js -i
# 逐步问：平台 → 类型 → 风格 → 输出路径 → 是否自定义尺寸

# === 方式 5：v4 新增 · 自定义尺寸（任意平台外的 ratio）===
node assets/code/src/pick-template.js --width 1440 --height 600 --label landing-hero --type cover --output task/foo/imgs/
node assets/code/src/pick-template.js --ratio "21:9" --base-width 1920 --label wide-hero --type cover --output task/foo/imgs/

# === 渲染所有 HTML（v4 自动跑自检）===
cd task/foo/imgs/
for f in *.html; do
  node ../../../assets/code/src/render-cover.js "$f"
done
# 渲染后自动打印 4 项自检报告：尺寸 / 主标字数 / 文件大小 / 安全区
```

**迭代节奏**：每轮只改一处（字号 / 间距 / 配色 / 文案 / 图标），开下一版 vN+1。

详细命令 + 禁止动作见 [reference/render.md](reference/render.md)。

---

## 平台规格速查（详细见 platforms.md）

| 平台 | 比例 | 渲染尺寸 | 输出尺寸（2×） | 适配模式 |
| --- | --- | --- | --- | --- |
| 公众号 | 2.35:1 | 900 × 383 | 1800 × 766 | 标准 |
| 小红书 | 3:4 / 9:16 | 1080 × 1440 / 1920 | 2160 × 2880 / 3840 | 高反差 |
| 抖音 | 9:16 / 16:9 | 1080 × 1920 / 720 | 2160 × 3840 / 1440 | 戏剧 |
| 知乎 | 16:9 / 4:3 | 1200 × 675 / 900 | 2400 × 1350 / 1800 | 标准 |
| B 站 | 16:10 | 1146 × 717 | 2292 × 1434 | 标准 |
| 微博 | 5:4 / 16:9 | 1280 × 1024 / 675 | 2560 × 2048 / 1350 | 标准 |
| OG Card | 1.91:1 | 1200 × 630 | 2400 × 1260 | 标准 |
| Twitter Card | 2:1 | 1200 × 600 | 2400 × 1200 | 标准 |

---

## 硬性约束（不可妥协）

来自 [reference/hard-rules.md](reference/hard-rules.md)：

1. **名人 / 大公司必须出现**（如文章提到了 Sam Altman → 封面必须有他的头像）
2. **文字必须通俗易懂**（小学生能秒懂）
3. **图标必须一眼可识别**（不用抽象几何、不用 AI 插画风）
4. **元素 ≤ 5 个**（视觉锤 + 主标 + 卡片 + 角标 + 脚注）

**额外约束**：
- 小红书主标 ≤ 20 字（信息流缩略图小）
- 抖音主标 ≤ 8 字（3 秒法则）
- OG/Twitter 文字必须中央安全区（1200×600 内）
- ❌ 不要换字体 / 不要改圆点纹理 / 不要去偏移黑阴影
- ❌ 不要引入非 HyperFrames 风格

---

## 不可改动的视觉 DNA

来自 [reference/visual-system.md](reference/visual-system.md)：

- 米白底 `#f3efe6` + 圆点纹理
- 黑顶栏 `#0b0d12` 36px（标准）/ 44px（小红书）/ 56px（抖音）
- 橙 `#ff5b1f` / 绿 `#6cd76b` 强调色（小红书改 `#ff2d55`）
- 卡片偏移黑阴影 `4px 4px 0 #0b0d12`（**标志**，不要模糊）
- 字体 PingFang SC / Helvetica Bold
- ❌ 不要渐变、阴影模糊、玻璃拟态
- ❌ 不要 emoji 当主视觉锤

---

## 自检清单（交付前必过）

```
□ 文章里的名人/大公司都出现在封面上了吗？
□ 所有文字小学生能看懂吗？
□ 每个图标 3 秒内能识别吗？
□ 整体元素 ≤ 5 个？
□ 主标字数符合平台限制？（抖音 ≤ 8 / 小红书 ≤ 20）
□ 文字在安全区内？（OG/Twitter 1200×600 中央）
□ 文件尺寸 ≤ 平台限制？（公众号/抖音 ≤ 2MB）
□ 渲染输出分辨率 = 2× DPI？
```

---

## 目录结构

```
cover-hero/
├── SKILL.md                            ← 本文件（入口 + 交互流）
├── README.md                           ← 仓库级说明
├── reference/
│   ├── visual-system.md                ← HyperFrames 视觉 DNA（不要换）
│   ├── hard-rules.md                   ← 封面三大硬性要求
│   ├── platforms.md                    ← 8 个平台规格 + 适配层
│   ├── naming.md                       ← 命名 + 模板选择
│   └── render.md                       ← 渲染 + 迭代流程
├── assets/
│   ├── code/
│   │   ├── src/
│   │   │   ├── render-cover.js         ← Puppeteer 渲染器（v4 渲染后调 quality-check）
│   │   │   ├── quality-check.js        ← v4 渲染后自检（4 项）
│   │   │   └── pick-template.js        ← 多平台模板选择器（v4 + --article / -i；v5 平台专用模板）
│   │   ├── adaptations/                ← v4 平台适配层（独立 CSS 文件）
│   │   │   ├── standard.css            公众号 / 知乎 / B站 / 微博 / OG / Twitter
│   │   │   ├── high-contrast.css       小红书
│   │   │   └── theatrical.css          抖音
│   │   └── templates/                  ← 8 套空白 HTML 模板（v5 +2 套竖版专用）
│   │       ├── cover-template.html        横版通用（公众号 / 知乎 / B站 / 微博 / OG / Twitter）
│   │       ├── xhs-cover.html            ⭐ v5 小红书 3:4 专用
│   │       ├── douyin-cover.html         ⭐ v5 抖音 9:16 专用
│   │       ├── fig-template-1-card-row.html
│   │       ├── fig-template-2-matrix.html
│   │       ├── fig-template-3-decision-tree.html
│   │       ├── fig-template-4-pipeline.html
│   │       └── fig-template-5-summary.html
│   └── examples/                       ← 历史范例（v4 README 加多平台建议）
└── progress.md                         ← 封装进度记录（v1→v2→v3→v4→v5）
```

## v5.1 · 任务目录约定（v5 推荐）

> 跑 `pick-template.js` 后，产物放在**任务子目录的 `imgs/`** 下。
>
> **全 8 平台子目录**（按需选跑，不一定要全跑）：
>
> ```
> <task>/imgs/
> ├── wechat/                      公众号 2.35:1   (横版)
> │   ├── cover-v1.html
> │   ├── cover-v1.png
> │   ├── fig-01/                   公众号配图 16:9
> │   │   ├── cover-v1.html
> │   │   └── cover-v1.png
> │   └── fig-02/
> │       ├── cover-v1.html
> │       └── cover-v1.png
> ├── xhs/                         小红书 3:4     (竖版)
> │   └── cover-v1.html + .png
> ├── xhs-story/                   小红书 9:16   (故事图)
> │   └── cover-v1.html + .png
> ├── douyin/                      抖音 9:16      (竖版)
> │   └── cover-v1.html + .png
> ├── douyin-wide/                 抖音横屏 16:9
> │   └── cover-v1.html + .png
> ├── zhihu/                       知乎 16:9
> │   └── cover-v1.html + .png
> ├── bilibili/                    B 站 16:10
> │   └── cover-v1.html + .png
> ├── weibo/                       微博 5:4
> │   └── cover-v1.html + .png
> ├── weibo-fig/                   微博配图 16:9
> │   └── cover-v1.html + .png
> ├── og/                          OG Card 1.91:1 (链接预览)
> │   └── cover-v1.html + .png
> └── twitter/                     Twitter Card 2:1
>     └── cover-v1.html + .png
> ```
>
> **fig 命名 = `cover-v1`**：fig 也是"为该平台做的图"，统一叫 `cover-v1.html/.png`（不叫 `fig-01-v1`，避免命名混乱）。每个 fig 配图在 `wechat/fig-01/`、`xhs/fig-01/` 等子目录里。
>
> **约定**：
> - **平台子目录**（`wechat/`, `xhs/`, `douyin/` 等）：每个平台一个子目录
> - **fig 放平台子目录里**（`wechat/fig-01/`、`xhs/fig-01/` 等），因为 fig 通常是为**某个平台**做的
> - **HTML 源 + PNG 产物配对**在每个子目录里
> - **vN 迭代**：每个文件带 `v1` / `v2` 版本号（旧版本不删，方便回滚）
> - **实战示例**：`todo/wanfeng-skills-readme-cover/imgs/` 目录里就有 wechat / xhs / douyin / xhs-story / douyin-wide / zhihu / bilibili / weibo / weibo-fig / og / twitter（v5.2 起全跑）
```

---

## v5.3 · CLI 自动分目录 + 一键全平台

> v5.1/v5.2 只是**文档化约定**（要手动组织目录）；v5.3 起 `pick-template.js` **自动实现**这套约定。

**改动 A · `--output` 是目录时自动按平台分子目录**

```bash
# --output 以 / 结尾或无 .html 后缀 → 目录，自动分子目录
node pick-template.js --platform wechat --output imgs/
#   → imgs/wechat/cover-v1.html   ⭐ 自动进 <platform>/ 子目录

# --output 带 .html 后缀 → 文件路径，原样输出（不分目录，供显式覆盖）
node pick-template.js --platform wechat --output imgs/my-name.html
#   → imgs/my-name.html
```

**改动 B · `--all-platforms` 一键全 8 平台**

```bash
node pick-template.js --all-platforms --output imgs/
#   → imgs/wechat/cover-v1.html
#   → imgs/xhs/cover-v1.html
#   → imgs/douyin/cover-v1.html
#   → imgs/zhihu/cover-v1.html
#   → imgs/bilibili/cover-v1.html
#   → imgs/weibo/cover-v1.html
#   → imgs/og/cover-v1.html
#   → imgs/twitter/cover-v1.html
```

- `--all-platforms` 必须配 `--output <dir>`（否则报错）
- 会覆盖 `--platform`（同时传会警告并跳过自定义值）
- 只跑 8 个核心平台（不含 custom / xhs-story / douyin-wide / weibo-fig 尺寸变体）
- 可与 `--article` 组合：`--article foo.md --all-platforms --output imgs/`

---

## 相关参考

- 视觉 DNA 速查：[reference/visual-system.md](reference/visual-system.md)
- 硬性要求 + 自检：[reference/hard-rules.md](reference/hard-rules.md)
- 8 个平台规格：[reference/platforms.md](reference/platforms.md)
- 命名 + 模板选择：[reference/naming.md](reference/naming.md)
- 渲染 + 迭代命令：[reference/render.md](reference/render.md)

## v4 快速参考卡

```
┌────────────────────────────────────────────────────────────┐
│ 新用户首选路径（v4）                                        │
│                                                            │
│   1. 在 MD 头部加 frontmatter:                              │
│      ---                                                   │
│      type: tutorial                                        │
│      platform: wechat xhs                                  │
│      ---                                                   │
│                                                            │
│   2. 一键生成：                                              │
│      node assets/code/src/pick-template.js \               │
│        --article task/<slug>/<slug>.md                    │
│                                                            │
│   3. 渲染（自动自检）：                                      │
│      node assets/code/src/render-cover.js \                │
│        task/<slug>/imgs/wechat-cover-v1.html               │
│                                                            │
│   4. 看到 4 项 ✓ = 发布。                                  │
│      看到 ❌ = 改 HTML 重新跑。                            │
└────────────────────────────────────────────────────────────┘
```