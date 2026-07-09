# 产物命名 + 画布规格 + 模板选择

---

## 一、画布规格

> **唯一比例**：主封面 `2.35:1 900×383`，正文配图 `16:9 1200×675`。**其他比例不使用**。

| 用途 | 比例 | 画布 | HTML 类名 | data-* 属性 |
| --- | --- | --- | --- | --- |
| **主封面** | **2.35:1** | `900×383` | `.cover` | `data-width="900" data-height="383"` |
| 正文配图 / 信息图 | 16:9 | `1200×675` | `.canvas` | `data-width="1200" data-height="675"` |

- 输出 PNG 用 `deviceScaleFactor: 2`（封面 → 1800×766，配图 → 2400×1350，公众号上传清晰度足够）
- `render-cover.js` 已自动读 `.cover` / `.canvas` 上的 `data-width/height`，**不要手动改脚本里的尺寸**

---

## 二、产物文件命名（严格遵守）

### 封面（每篇文章 1 张，2.35:1）

- 唯一格式：`cover-vN.html` / `.png`
- **不要覆盖旧版本**，方便对比

### 正文配图（每篇按需 0–7 张，16:9）

```
fig-NN-sectionX-keyword.html
fig-NN-sectionX-keyword.png
```

- `NN`：阅读顺序，从 `01` 起，左 0 补齐
- `sectionX`：文章里的章节号，对应 `## X.`，例如第七节就是 `section7`
- `keyword`：英文小写连字符短语，3 词以内（如 `comparison-matrix` / `decision-tree`）

例：`fig-04-section9-combo-knowledge-blogger.png` 一眼就能定位到"文章第 9 节，第 4 张图"。

### 输出目录

```
公众号/task/<topic-slug>/imgs/
├── cover-v1.html / .png
├── fig-01-section3-keyword.html / .png
├── fig-02-section6-keyword.html / .png
└── ...
```

### 多平台文件命名（v2+ 新增）

当一篇文章同时发到多平台时，**每个平台单独命名**以避免混淆：

```
task/<topic-slug>/imgs/
├── wechat-cover-v1.html / .png       ← 公众号封面
├── xhs-cover-v1.html / .png          ← 小红书封面
├── douyin-frame-v1.html / .png       ← 抖音视频帧
├── og-cover-v1.html / .png           ← OG Card
├── fig-01-section3-keyword.html      ← 通用配图（不区分平台）
└── ...
```

**规则**：

- `wechat-` / `xhs-` / `douyin-` / `zhihu-` / `bilibili-` / `weibo-` / `og-` / `twitter-` 前缀标识平台
- `cover` / `figure` / `frame` 标识产物类型
- 通用配图（不是某个平台专属）不加平台前缀

- 子目录没有就**手动创建**（`mkdir -p`）
- 默认输出格式 `.png`（2× DPI）

---

## 三、按文章类型挑模板

> **首选**：直接跑 [`assets/code/src/pick-template.js`](../assets/code/src/pick-template.js)，自动输出完整清单（封面模板 + N 张 fig + 配图数量建议）。
>
> ```bash
> node assets/code/src/pick-template.js review          # 传 type
> node assets/code/src/pick-template.js --article <md> # 自动读 frontmatter
> ```

读完整篇文章后，先回答"三个问题"：

1. 这篇文章卖的是哪一类信息？（故事 / 教程 / 横评 / 工具清单 / 决策建议）
2. 全文最强的一个数字 / 关键词 / 名词是什么？（这就是视觉锤）
3. 读者看完会做的下一个动作是什么？（这是底部脚注 / 角标的语气）

然后按下面的表挑模板：

| 文章类型 | 视觉锤区放什么 | 信息区放什么 | 高亮卡片 | 配图模板 |
| --- | --- | --- | --- | --- |
| **横评 / 工具清单** | 大数字（"5"、"7"） | N 个工具卡片 | 推荐那一个 | `fig-template-1-card-row` |
| **教程 / 入门** | 单个英文动词或符号（`>_`、`▶`、`{}`） | 3 步流程卡片 | "Step 3 出片" | `fig-template-4-pipeline` |
| **故事 / 经验** | 一段短主标（≤12 字） | 1 个大图标场景 | 角标做态度词 | `fig-template-5-summary` |
| **决策 / 选型** | 大问号 `?` 或 决策树符号 | 2–4 个选项卡片 | 推荐答案 | `fig-template-3-decision-tree` |
| **对比表** | （配图用） | 矩阵网格，关键格子高亮 | 高亮对比项 | `fig-template-2-matrix` |

### 6 套模板清单

```
templates/
├── cover-template.html              ← 封面（2.35:1）— 视觉锤 + 3 卡片 + 角标
├── fig-template-1-card-row.html     ← N 卡片横排（横评清单用）
├── fig-template-2-matrix.html       ← 对比矩阵（对比表用）
├── fig-template-3-decision-tree.html    ← 决策树（怎么选用）
├── fig-template-4-pipeline.html     ← 流水线（教程/组合用法）
└── fig-template-5-summary.html      ← 总结大数字（结尾用）
```

---

## 四、图标选择规则（全部从原文里"挑"，不要凭空造）

- 文章里说 HTML → 用 `< >`
- 文章里说 React → 用 React 原子
- 文章里说数字人 → 用人头剪影
- 文章里说剪辑/口播 → 剪刀
- 文章里说混剪 → 4 块拼贴
- 文章里说聊天 → 聊天气泡 + 终端提示符
- 文章里说视频 → 胶卷条带 / 播放三角

**全部用纯 SVG 自绘**（不外链、不用图标字体），保证离线可渲染、可重排色。

---

## 五、文字长度上限

- 顶栏 1 行英文 kicker
- 视觉锤区 1 个字符 / 1 个超短词
- 主标 ≤ 14 个字，最多分两行
- 卡片每个 ≤ 8 字 + 一句话角色（≤ 14 字）
- 底部 1 行脚注

文字越少，封面越像封面、不像幻灯片。

---

## 六、产物清单检查

每次给配图，要顺手给一张表，让读者/编辑直接知道贴哪：

```
| 文件 | 插入位置 | 图意 |
|---|---|---|
| fig-01-…  | §1 标题之后、表格之前  | …… |
| fig-02-…  | §7 对比表之前         | …… |
```

不要让用户去翻文件看图意。