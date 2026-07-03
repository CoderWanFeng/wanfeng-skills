---
name: article-cover-illustration
description: 为公众号文章生成 HyperFrames 视觉风格的封面 + 正文配图。封装 HTML 手写 + Puppeteer 渲染流水线；6 套空白模板、严格的命名规范、不可改动的视觉 DNA、唯一比例（2.35:1 封面 + 16:9 配图）。当用户提到"公众号封面"、"公众号配图"、"做头图"、"做信息图"、"配张图"且文章主题明确时立即触发。
---

# Article Cover & Illustration（公众号封面 & 配图）

> 统一路径：**手写 HTML + Puppeteer 渲染 + HyperFrames 视觉风格系统**。
> 不调 AI 生图（名人/Logo 走嵌入路径）。

---

## 何时使用

✅ **使用本 skill 的场景**：

- 给一篇公众号新文章做封面（2.35:1 900×383）
- 给公众号文章正文做信息图（16:9 1200×675）
- 已有封面想按本风格迭代（v2 / v3）
- 用户说"做封面但不知道用哪个配图模板" → 直接跑 `assets/code/src/pick-template.js`，按文章类型自动推荐清单

❌ **不要使用**：

- 用户没说要图，只是纯文字聊天
- 文章主题不明（让用户先说"这篇文章讲什么"）
- 用户明确要求 AI 生图风格（这与本 skill 的视觉风格不兼容）
- 非公众号场景（博客 / 知乎 / Newsletter 等，需要其他 skill）

---

## 决策树（第一步）

用户说"做封面 / 配图"后，先问 3 个问题：

```
1. 这篇文章讲什么？→ 一句话主题
2. 提到了哪些名人 / 大公司？→ 必查（影响封面是否有视觉锤）
3. 文章里有几个"信息密度高"的小节值得配图？→ 决定 N 张图
```

> ⚠️ **不要跳过这步**。封面是给特定文章特定的，不是模板填空。

详细问法 + 自检清单见 [reference/hard-rules.md](reference/hard-rules.md)。

---

## 执行流程（5 步走）

### Step 1 · 读文章 → 提炼视觉锤

按 [reference/hard-rules.md §"封面三大硬性要求"](reference/hard-rules.md)：

1. 扫一遍正文，标出所有名人 / 大公司 → 封面必须出现
2. 回答"三个问题"：类型 / 视觉锤 / 读者下一步动作
3. 把"技术词"翻译成"生活化比喻 + 数字 + 动作"

### Step 2 · 按文章类型挑模板

> **首选**：直接跑 `assets/code/src/pick-template.js`，自动读 type + 打印完整清单。
>
> ```bash
> # 方式 1：直接传 type
> node assets/code/src/pick-template.js review
>
> # 方式 2：自动读 frontmatter
> node assets/code/src/pick-template.js --article task/<slug>/<slug>.md
> ```
>
> 输出示例：
> ```
> ✓ 检测到 type: review (横评)
>
> 推荐产物清单：
>   封面   cover-v1.html            ← 复用 cover-template.html（大数字视觉锤）
>   配图1  fig-01-section?-横评.html  ← fig-template-1-card-row.html（N 卡片横排）
>   配图2  fig-02-section?-横评.html  ← fig-template-2-matrix.html（对比矩阵）
>   配图3  fig-03-section?-横评.html  ← fig-template-5-summary.html（总结大数字）
>
> 配图数量建议：4-6 张
> ```

参考 [reference/naming.md §"按文章类型挑模板"](reference/naming.md)：

| 文章类型 | 模板 |
| --- | --- |
| 横评 / 工具清单 | `cover-template` + `fig-template-1-card-row` |
| 教程 / 入门 | `cover-template` + `fig-template-4-pipeline` |
| 故事 / 经验 | `cover-template` + `fig-template-5-summary` |
| 决策 / 选型 | `cover-template` + `fig-template-3-decision-tree` |
| 对比表 | `fig-template-2-matrix` |

> 💡 **新用户**：直接看 `assets/examples/` 下 2 个历史范例（`ai-photo-father` 教程型 + `netflix-headroom-save-token` 对比型），照着改比看文档更快。

### Step 3 · 复制骨架 + 改 5 区内容

```bash
# 1. 复制封面骨架
cp assets/code/templates/cover-template.html \
   task/<slug>/imgs/cover-v1.html

# 2. 复制配图骨架（按需）
cp assets/code/templates/fig-template-N.html \
   task/<slug>/imgs/fig-01-sectionX-keyword.html
```

按 [reference/visual-system.md §"封面 5 区结构"](reference/visual-system.md) 改：

1. 顶栏：kicker + 期号
2. 视觉锤区：大字 + 副标
3. 信息区：主标 + 卡片
4. 角标：旋转 5deg
5. 脚注：账号名 + 期号

### Step 4 · 渲染 + 迭代

```bash
# 单张
node code/src/render-cover.js task/<slug>/imgs/cover-v1.html

# 批量
cd task/<slug>/imgs/
for f in cover-*.html fig-*.html; do
  node ../../../code/src/render-cover.js "$f"
done
```

**迭代节奏**（每轮只改一处）：
1. 写 `cover-vN.html`
2. 渲染 → 用户看 PNG
3. 只调一处（字号 / 间距 / 配色 / 文案 / 图标）
4. 开下一轮 vN+1

详细命令 + 禁止动作见 [reference/render.md](reference/render.md)。

### Step 5 · 交付

产物 PNG 在 `task/<slug>/imgs/`，按位置对照表贴入公众号编辑器即可。

---

## 硬性约束（不可妥协）

来自 [reference/hard-rules.md](reference/hard-rules.md)：

1. **名人 / 大公司必须出现**（如文章提到了 Sam Altman → 封面必须有他的头像）
2. **文字必须通俗易懂**（小学生能秒懂）
3. **图标必须一眼可识别**（不用抽象几何、不用 AI 插画风）
4. **元素 ≤ 5 个**（视觉锤 + 主标 + 卡片 + 角标 + 脚注）

违反任一条 = 封面不合格，必须返工。

---

## 不可改动的视觉 DNA

来自 [reference/visual-system.md](reference/visual-system.md)：

- 米白底 `#f3efe6` + 圆点纹理
- 黑顶栏 `#0b0d12` 36px
- 橙 `#ff5b1f` / 绿 `#6cd76b` 强调色
- 卡片偏移黑阴影 `4px 4px 0 #0b0d12`（**标志**，不要模糊）
- 字体 PingFang SC / Helvetica Bold
- ❌ 不要渐变、阴影模糊、玻璃拟态
- ❌ 不要 emoji 当主视觉锤
- ❌ 不要超过 5 个主要元素
- ❌ **不要换比例**（封面必须 2.35:1 900×383，配图必须 16:9 1200×675）

---

## 自检清单（交付前必过）

```
□ 文章里的名人/大公司都出现在封面上了吗？
□ 所有文字小学生能看懂吗？
□ 每个图标 3 秒内能识别吗？
□ 整体元素 ≤ 5 个？
□ 5 秒测试：朋友刷到，5 秒内能不能说出"哦这是讲 XX 的"？
□ 配图位置对照表写了吗？
```

---

## 目录结构

```
article-cover-illustration/
├── SKILL.md                            ← 本文件（入口 + 决策树）
├── README.md                           ← 仓库级说明
├── reference/
│   ├── visual-system.md                ← HyperFrames 视觉 DNA（不要换）
│   ├── hard-rules.md                   ← 封面三大硬性要求
│   ├── naming.md                       ← 命名 + 画布 + 模板选择
│   └── render.md                       ← 渲染 + 迭代流程
├── assets/
│   ├── code/
│   │   ├── src/
│   │   │   ├── render-cover.js         ← Puppeteer 渲染器
│   │   │   └── pick-template.js        ← 自动选模板 CLI（按 type 推荐）
│   │   └── templates/                  ← 6 套空白 HTML 模板
│   │       ├── cover-template.html
│   │       ├── fig-template-1-card-row.html
│   │       ├── fig-template-2-matrix.html
│   │       ├── fig-template-3-decision-tree.html
│   │       ├── fig-template-4-pipeline.html
│   │       └── fig-template-5-summary.html
│   └── examples/                       ← 历史范例（2 套完整可改）
│       ├── ai-photo-father/           ← 教程型：3 卡片流水线 + 5 卡片横排
│       │   ├── README.md
│       │   ├── cover-v1.html + .png
│       │   └── fig-01-section1-5-tips.html + .png
│       └── netflix-headroom-save-token/ ← 对比型：4 卡片纵列 + 对比矩阵
│           ├── README.md
│           ├── cover-v1.html + .png
│           └── fig-01-section3-comparison.html + .png
└── progress.md                         ← 封装进度记录
```

---

## 相关参考

- 视觉 DNA 速查：[reference/visual-system.md](reference/visual-system.md)
- 硬性要求 + 自检：[reference/hard-rules.md](reference/hard-rules.md)
- 命名 + 模板选择：[reference/naming.md](reference/naming.md)
- 渲染 + 迭代命令：[reference/render.md](reference/render.md)