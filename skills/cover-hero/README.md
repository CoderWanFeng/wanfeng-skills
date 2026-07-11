# cover-hero · 封面侠

> **目录名**：`cover-hero/`
> **中文名**：封面侠
> **版本**：v5.3 · CLI 自动分目录 + 一键全平台（2026-07）

> 为**多平台**文章 / 内容生成 HyperFrames 视觉风格的封面 + 配图。
> 封装：手写 HTML + Puppeteer 渲染 + **多平台模板选择器**（8 个平台 + 任意自定义尺寸）。
> v5 起小红书 / 抖音有**专用竖版模板**（不再套横版崩布局）。
> 不调 AI 生图，零 token 消耗。

## 一句话总结

用户提供内容 → 选平台（可多选 + 可自定义尺寸）→ 选风格档位 → 自动生成多平台适配的封面 + 配图 → **自动自检**（4 项：尺寸 / 字数 / 文件大小 / 安全区）。

## v4 新增能力（相比 v3）

| 能力 | 命令 | 价值 |
|---|---|---|
| 自动读 MD frontmatter | `pick-template.js --article <md>` | 新用户首选路径，少打 N 个参数 |
| 交互问答模式 | `pick-template.js -i` | 命令行不熟用户逐步选 |
| 多平台一键 | `--platform wechat,xhs,douyin` | 一次跑 3 个平台 |
| **一键全 8 平台**（v5.3） | `--all-platforms --output imgs/` | 无需列平台名，自动跑 8 平台 |
| **`--output` 目录自动分子目录**（v5.3） | `--output imgs/` → `imgs/<platform>/cover-v1.html` | 目录路径自动按平台分目录（带 `.html` 后缀则原样输出）|
| **任意自定义尺寸** | `--width 1440 --height 600` / `--ratio "21:9"` | landing page / App Store 截图 / 飞书头图等非 12 平台尺寸 |
| 渲染后自动自检 | `render-cover.js` 跑完自动打印 4 项检查 | 不用人工对照 platforms.md |
| 平台适配层拆 CSS | `assets/code/adaptations/*.css` | 用户改 CSS 永久生效，不被覆盖 |

## 5 步交互流程（v4 简化）

| Step | 谁完成 | 内容 |
| --- | --- | --- |
| 1 · 收集主题 | Agent 问 / 用户答 | 文章主题 + 观点 + 名人/公司 + 类型 |
| 2 · 提炼视觉锤 | Agent 自动 | 扫名人/公司 + 答"三个问题" + 技术词翻译 |
| 3 · 选平台 + 风格 | Agent 问 / 用户答 | 8 选 N（可加 `--ratio` 自定义尺寸）+ 3 档位 |
| 4 · 选产物类型 | Agent 推荐 / 用户确认 | 每个平台默认产物清单 |
| 5 · 渲染 + 迭代 | Agent 执行 / 用户反馈 | pick-template.js + render-cover.js（**自动自检**）|

## 快速开始

### 方式 1：v4 新用户首选（`--article` 自动读 frontmatter）

```bash
# 1. 在 MD 头部加 frontmatter
cat > my-article.md << 'EOF'
---
title: 5 个 Codex 视频插件横评
type: review
platform: wechat xhs douyin
---
# 正文...
EOF

# 2. 一键生成 3 平台封面
node assets/code/src/pick-template.js --article my-article.md
# 产物：my-article/imgs/{wechat,xhs,douyin}-cover-v1.html

# 3. 编辑 5 区内容（每个 HTML 各改 5 处）

# 4. 渲染 + 自动自检
cd my-article/imgs
for f in *.html; do node ../../assets/code/src/render-cover.js "$f"; done
# 渲染完自动打印 4 项自检报告
```

### 方式 2：手动指定（v3 兼容）

```bash
# 单平台
node assets/code/src/pick-template.js --platform wechat --type cover --output imgs/

# 多平台一键
node assets/code/src/pick-template.js --platform wechat,xhs,douyin --type cover --output imgs/

# 一键全 8 平台（v5.3）— 自动按平台分子目录 imgs/<platform>/cover-v1.html
node assets/code/src/pick-template.js --all-platforms --output imgs/

# --output 是目录（无 .html 后缀）→ 自动进 <platform>/ 子目录；带 .html → 原样输出
node assets/code/src/pick-template.js --platform wechat --output imgs/          # → imgs/wechat/cover-v1.html
node assets/code/src/pick-template.js --platform wechat --output imgs/foo.html  # → imgs/foo.html

# 自定义尺寸（任意 ratio）
node assets/code/src/pick-template.js --width 1440 --height 600 --label app-banner --type cover --output imgs/
node assets/code/src/pick-template.js --ratio "21:9" --base-width 1920 --label wide-hero --type cover --output imgs/
```

### 方式 3：交互模式（适合新手）

```bash
node assets/code/src/pick-template.js -i
# 逐步问：平台 → 类型 → 风格 → 输出路径 → 是否自定义尺寸
```

## 平台支持（8 个 + 任意自定义）

| 平台 | 比例 | 适配模式 | 主标字数限制 |
| --- | --- | --- | --- |
| 公众号 | 2.35:1 | 标准 | ≤ 14 |
| 小红书 | 3:4 / 9:16 | 高反差（顶栏 44px / 强调色改 `#ff2d55`）| ≤ 20 |
| 抖音 | 9:16 / 16:9 | 戏剧（视觉锤 240px / 顶栏 56px）| ≤ 8 |
| 知乎 | 16:9 / 4:3 | 标准 | ≤ 14 |
| B 站 | 16:10 | 标准 | ≤ 14 |
| 微博 | 5:4 / 16:9 | 标准 | ≤ 14 |
| OG Card | 1.91:1 | 标准 | ≤ 30 |
| Twitter Card | 2:1 | 标准 | ≤ 30 |
| **自定义** | 任意 | 标准（不应用小红书/抖音的强装饰）| 无限制 |

详细规格见 [reference/platforms.md](reference/platforms.md)。

## 渲染后自动自检（v4 新增）

每次 `node render-cover.js <html>` 跑完自动打印 4 项检查：

```
--- 渲染后自检 ---
✓ 尺寸 2160×3840 = 1080×1920 × 2× DPI
✓ "5"（1 字 ≤ 8 限制）
✓ 0.15MB ≤ 2MB
ℹ douyin 平台无安全区限制

✓ 所有自检通过
```

| 检查项 | 规则 | 失败示例 |
|---|---|---|
| 尺寸 | PNG 实际尺寸 = data-width × 2 × data-height × 2 | "PNG=2000×800，预期=1800×766" |
| 主标字数 | 平台限制（抖音 ≤ 8 / 小红书 ≤ 20 / 其他 ≤ 14）| "19 字 > 14 限制" |
| 文件大小 | ≤ 2MB（公众号/抖音）/ ≤ 5MB（其他）| "3.5MB > 2MB" |
| 安全区 | OG / Twitter 必须标 safe-area 类 | "应在中央 1200×600 加 safe-area" |

⚠ 自检**不阻塞渲染**——4 项未通过仍生成 PNG（用户可继续发布），但提供修正建议。

## 目录结构

```
cover-hero/
├── SKILL.md                            ← 入口 + 5 步交互流（v4）
├── README.md                           ← 本文件（仓库说明 v4）
├── reference/ (5 文件)
│   ├── visual-system.md                ← HyperFrames 视觉 DNA
│   ├── hard-rules.md                   ← 封面三大硬性 + 平台字数限制
│   ├── platforms.md                    ← 8 平台规格 + 适配层 CSS
│   ├── naming.md                       ← 命名 + 模板选择
│   └── render.md                       ← 渲染 + 迭代流程
├── assets/
│   ├── code/
│   │   ├── src/
│   │   │   ├── render-cover.js         ← Puppeteer 渲染器（v4 渲染后调 quality-check）
│   │   │   ├── quality-check.js        ← NEW · v4 渲染后自检（4 项）
│   │   │   └── pick-template.js        ← v4 多平台模板选择器
│   │   ├── adaptations/                ← NEW · v4 平台适配层（独立 CSS 文件）
│   │   │   ├── standard.css            公众号 / 知乎 / B站 / 微博 / OG / Twitter
│   │   │   ├── high-contrast.css       小红书
│   │   │   └── theatrical.css          抖音
│   │   └── templates/                  ← 6 套空白 HTML 模板
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

## 任务目录约定（v5.1 推荐）

跑 `pick-template.js` 后，产物按以下结构组织：

```
<task>/imgs/                       ← 任务名/imgs/ 是默认输出目录
├── wechat/                        ← 公众号 2.35:1（横版）
│   ├── cover-v1.html + .png
│   ├── fig-01/                    ← 公众号配图（16:9 横版）
│   │   └── cover-v1.html + .png
│   └── fig-02/
│       └── cover-v1.html + .png
├── xhs/                           ← 小红书 3:4（竖版）
├── xhs-story/                     ← 小红书 9:16（故事图）
├── douyin/                        ← 抖音 9:16（竖版）
├── douyin-wide/                   ← 抖音横屏 16:9
├── zhihu/                         ← 知乎 16:9
├── bilibili/                      ← B 站 16:10
├── weibo/                         ← 微博 5:4
├── weibo-fig/                     ← 微博配图 16:9
├── og/                            ← OG Card 1.91:1（链接预览）
└── twitter/                       ← Twitter Card 2:1
```

**规则**：
- **每个平台一个子目录**（`wechat/`, `xhs/`, `douyin/` 等共 8+ 个）
- **fig 放平台子目录里**（`wechat/fig-01/`、`xhs/fig-01/` 等）：fig 通常是为某个平台做的
- **HTML 源 + PNG 产物配对**在每个子目录里
- **fig 命名 = `cover-v1`**（不是 `fig-01-v1`）：fig 也是为该平台做的图，统一叫 `cover-v1`
- **vN 迭代**：版本号清晰，回滚方便
- **实战示例**：`todo/wanfeng-skills-readme-cover/imgs/` 就是这个结构（v5.2 起全 8 平台）

## 核心约束（不可妥协）

1. **名人 / 大公司必须出现** —— 文章提到 Sam Altman / OpenAI → 封面必须有
2. **文字必须通俗易懂** —— 小学生能秒懂
3. **图标必须一眼可识别** —— 不用抽象几何、不用 AI 插画风
4. **元素 ≤ 5 个** —— 视觉锤 + 主标 + 卡片 + 角标 + 脚注
5. **主标字数按平台限制** —— 抖音 ≤ 8 / 小红书 ≤ 20 / 其他 ≤ 14
6. **风格只允许在 HyperFrames 内部调整** —— 不引入非 HyperFrames 风格

## 视觉 DNA（不可改动）

- 米白底 `#f3efe6` + 圆点纹理
- 黑顶栏 `#0b0d12` 36px（标准）/ 44px（小红书）/ 56px（抖音）
- 橙 `#ff5b1f` / 绿 `#6cd76b` 强调色（小红书改 `#ff2d55`）
- 卡片偏移黑阴影 `4px 4px 0 #0b0d12`（**HyperFrames 标志**）
- 字体 PingFang SC / Helvetica Bold

## 6 套模板

| 文件 | 用途 |
| --- | --- |
| `cover-template.html` | 主封面（默认 2.35:1，可被 pick-template.js 覆盖尺寸） |
| `fig-template-1-card-row.html` | N 卡片横排（横评清单） |
| `fig-template-2-matrix.html` | 对比矩阵 |
| `fig-template-3-decision-tree.html` | 决策树 |
| `fig-template-4-pipeline.html` | 流水线（教程） |
| `fig-template-5-summary.html` | 总结大数字 |

## 文档导航

- **第一次用**：跑 `pick-template.js -i`（交互模式）或 `pick-template.js --article <md>`（自动读 frontmatter）
- **不知道平台/比例**：跑 `pick-template.js --help` 看 12+ 预设
- **改配色 / 字体**：看 [reference/visual-system.md](reference/visual-system.md)
- **不确定是否合格**：跑 `render-cover.js` 后看自动自检报告
- **平台规格 / 适配层**：看 [reference/platforms.md](reference/platforms.md)
- **改平台适配层 CSS**：直接改 `assets/code/adaptations/*.css`（永久生效）
- **遇到渲染报错**：看 [reference/render.md](reference/render.md)

## 依赖

- Node.js（任意版本）
- `puppeteer-core`（`npm install puppeteer-core`）
- Google Chrome（`/Applications/Google Chrome.app`，macOS 默认）

## 封装进度

见 [progress.md](progress.md)（v1→v2→v3→v4）。