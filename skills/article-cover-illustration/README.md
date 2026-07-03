# Article Cover & Illustration Skill

> 为公众号文章生成 HyperFrames 视觉风格的封面 + 正文配图。
> 封装：手写 HTML + Puppeteer 渲染 + 6 套空白模板。
> **唯一比例**：2.35:1 封面 + 16:9 配图。

## 一句话总结

读完一篇文章 → 提炼视觉锤 → 复制模板骨架 → 改 5 区内容 → 渲染 PNG → 贴入公众号编辑器。

## 快速开始

```bash
# 1. 安装依赖
npm install puppeteer-core

# 2. 复制封面骨架到目标文章
cp assets/code/templates/cover-template.html \
   task/<your-slug>/imgs/cover-v1.html

# 3. 改 5 区内容（顶栏 / 视觉锤 / 信息区 / 角标 / 脚注）
#    编辑器打开 cover-v1.html，按 SKILL.md 的"封面 5 区结构"填充

# 4. 渲染
node code/src/render-cover.js task/<your-slug>/imgs/cover-v1.html

# 产物：task/<your-slug>/imgs/cover-v1.png（1800×766，2× DPI）
```

## 目录结构

```
article-cover-illustration/
├── SKILL.md                            ← 入口 + 决策树（先看这个）
├── README.md                           ← 本文件（仓库说明）
├── reference/
│   ├── visual-system.md                ← HyperFrames 视觉 DNA
│   ├── hard-rules.md                   ← 封面三大硬性要求
│   ├── naming.md                       ← 命名 + 画布 + 模板选择
│   └── render.md                       ← 渲染 + 迭代流程
├── assets/
│   ├── code/
│   │   ├── src/render-cover.js         ← Puppeteer 渲染器
│   │   └── templates/                  ← 6 套空白 HTML 模板
│   └── examples/                       ← （预留）历史范例
└── progress.md                         ← 封装进度记录
```

## 核心约束（不可妥协）

1. **名人 / 大公司必须出现** —— 文章提到 Sam Altman / OpenAI → 封面必须有
2. **文字必须通俗易懂** —— 小学生能秒懂
3. **图标必须一眼可识别** —— 不用抽象几何、不用 AI 插画风
4. **元素 ≤ 5 个** —— 视觉锤 + 主标 + 卡片 + 角标 + 脚注
5. **唯一比例** —— 封面 2.35:1（900×383）、配图 16:9（1200×675）

## 视觉 DNA（不可改动）

- 米白底 `#f3efe6` + 圆点纹理
- 黑顶栏 `#0b0d12` 36px
- 橙 `#ff5b1f` / 绿 `#6cd76b` 强调色
- 卡片偏移黑阴影 `4px 4px 0 #0b0d12`（**HyperFrames 标志**）
- 字体 PingFang SC / Helvetica Bold

## 6 套模板

| 文件 | 用途 |
| --- | --- |
| `cover-template.html` | 主封面（2.35:1） |
| `fig-template-1-card-row.html` | N 卡片横排（横评清单） |
| `fig-template-2-matrix.html` | 对比矩阵 |
| `fig-template-3-decision-tree.html` | 决策树 |
| `fig-template-4-pipeline.html` | 流水线（教程） |
| `fig-template-5-summary.html` | 总结大数字 |

## 2 套历史范例

**`assets/examples/`** 下 2 套完整范例（HTML + 渲染产物 PNG + README）：

| 范例 | 类型 | 演示什么 |
|---|---|---|
| `ai-photo-father` | 教程 / 科普（3 步讲清）| 大汉字视觉锤 + 3 卡片流水线（Diffusion 高亮绿色）+ 5 卡片横排配图 |
| `netflix-headroom-save-token` | 硬核科普 / 对比 | 大数字视觉锤（÷ 20）+ 4 卡片纵列 + 5×5 对比矩阵 |

> ⚠️ **新用户强烈建议**：先看 `examples/<task>/README.md`，照着改比读文档快 3 倍。
> 所有范例的 footer 用了 `<账号名> · <slogan>` 占位符——用户使用时**替换成自己的账号信息**。

## 自动选模板 CLI

**`assets/code/src/pick-template.js`** · 按文章类型自动推荐产物清单：

```bash
# 方式 1：直接传 type（支持中文别名）
node assets/code/src/pick-template.js review
node assets/code/src/pick-template.js 教程

# 方式 2：自动读 frontmatter 的 type: 字段
node assets/code/src/pick-template.js --article task/<slug>/<slug>.md
```

**支持 type**（5 类）：

| type | 中文 | 推荐配图数 | 推荐 fig 模板 |
|---|---|---|---|
| `review` | 横评 | 4-6 | card-row + matrix + summary |
| `tutorial` | 教程 | 3-5 | pipeline + decision-tree + summary |
| `story` | 故事 | 2-3 | card-row + summary |
| `decision` | 决策 | 3-4 | decision-tree + matrix |
| `comparison` | 对比 | 1-2 | matrix |

## 文档导航

- **第一次用**：先看 [SKILL.md](SKILL.md) 走完整流程
- **不知道用哪个模板**：跑 `assets/code/src/pick-template.js`，或看 [reference/naming.md](reference/naming.md) 的"按文章类型挑模板"表
- **看真实范例**：`assets/examples/<task>/README.md`（强烈推荐新用户先看）
- **改配色 / 字体**：看 [reference/visual-system.md](reference/visual-system.md)
- **不确定是否合格**：看 [reference/hard-rules.md](reference/hard-rules.md) 自检清单
- **遇到渲染报错**：看 [reference/render.md](reference/render.md)

## 适用平台

**只用于公众号**（2.35:1 封面 + 16:9 配图）。

其他平台（博客 / 知乎 / Newsletter / OG Card 等）需要其他 skill，本 skill 不覆盖。

## 依赖

- Node.js（任意版本）
- `puppeteer-core`（`npm install puppeteer-core`）

## 封装进度

见 [progress.md](progress.md)。