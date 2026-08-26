# wanfeng-skills / skills 目录

> 这是一个**可复用的 AI Skill 集合**。每个子目录都是一个独立的 skill，对应一个具体的工作流。
> Skill 之间**正交**：可单独使用，也可按场景串起来。

---

## 📚 Skill 一览（8 个）

| Skill | 用途 | 适用场景 | 触发词举例 | 在线体验 |
|---|---|---|---|---|
| [**aihot-topic-selector**](aihot-topic-selector/) | 从 AIHOT 热点数据里每天自动选题 | 自媒体日常选题、内容运营 | 「今天 AI 有什么热点」「按热点选个题」 | — |
| [**hot-topic-radar**](hot-topic-radar/) | 7×24h 监控全网热搜，按关键词过滤 + 热度打分 | 自媒体选题雷达、跨平台聚合 | 「监控 XX 话题」「全网热搜」「今天值得跟什么」 | — |
| [**cover-hero**](cover-hero/) | 给公众号文章做封面 + 正文配图（HyperFrames 风格） | 公众号配图、长文视觉 | 「做公众号封面」「配张图」「头图」 | [👉 封面侠](https://qclaw.qq.com/as/BQ2Cw50sNfcy) |
| [**mp-saver**](mp-saver/) | 不登录保存公众号文章为单文件 MHTML（HTML + base64 内嵌图片，离线可看）。v2.0 起零依赖（只用 Python 标准库 urllib） | 公众号文章收藏、批量存档、喂 LLM | 「保存公众号文章」「下载公众号文章」「不登录存公众号」 | — |
| [**knowledge-short-video**](knowledge-short-video/) | 知识类短视频全流程（口播稿 → 视觉 → 动画 → TTS → 渲染） | 短视频制作、知识科普 | 「做条知识视频」「短视频口播稿」 | — |
| [**personal-website-builder**](personal-website-builder/) | 对话式引导创建个人网站（博客/知识库/作品集/简历） | 个人建站、博客搭建 | 「我想做个博客」「搭个个人网站」「建个简历站」 | [👉 建站搭子](https://qclaw.qq.com/as/5oDmikXxsQEo) |
| [**opensource-housekeeper**](opensource-housekeeper/) | 一站式开源管家：发布本地项目到 GitHub/AtomGit/Gitee + 拉取网上的项目本地运行 | 开源小白、跨平台发布、跑开源项目 | 「帮我推到 GitHub」「开源搭子」「拉一下 llama.cpp 跑起来」 | [👉 开源管家](https://qclaw.qq.com/as/4VlrmxmvAnlV) |
| [**free-ai-models**](free-ai-models/) | 搜罗全网可以免费使用的大模型（直接用 / 软件内置 / 平台免费额度） | 找免费 GPT/Claude/Gemini、找软件里能白嫖的模型、找永久免费 API | 「免费大模型」「GPT 免费吗」「Cursor 里哪个免费」「API 免费额度」 | — |

---

## 🗂️ 按场景分类

### 🔍 内容创作 / 自媒体

```
每日选题 → 写文章 → 配图 → 发布
  ↓         ↓        ↓      ↓
hot-topic-radar / 人工  cover-hero  公众号
aihot-topic-selector
```

```
要保存别人写的公众号文章（不登录）？
  ↓
mp-saver
```

- **[aihot-topic-selector](aihot-topic-selector/)** — AI 领域专属：每天从 AIHOT 拉热点，按 2 问选 1 条，建 task 目录
- **[hot-topic-radar](hot-topic-radar/)** — 全网通用：自定义关键词 + 多平台 + 记忆去重，适合任何垂直领域
- **[cover-hero](cover-hero/)** — 配图：6 套模板 + 严格视觉 DNA + Puppeteer 渲染
- **[mp-saver](mp-saver/)** — 公众号文章保存器：v2.0 纯 HTTP 版 → MHTML 单文件，不登录、双击可看；v2.0 起只需 Python 标准库
- **[knowledge-short-video](knowledge-short-video/)** — 短视频：覆盖 20+ 步骤，从口播稿到渲染产物

### 🌐 个人项目 / 建站

- **[personal-website-builder](personal-website-builder/)** — 对话式建站：5 种类型（博客/知识库/AI 导航/作品集/简历）

### 🚀 开源协作

- **[opensource-housekeeper](opensource-housekeeper/)** — 一站式开源管家：发布 + 拉取双向，支持非代码项目（文档/图片/dotfiles）

---

## 🎯 如何选用 skill？

| 你想做的事 | 用这个 skill |
|---|---|
| 我要做自媒体，从哪开始找选题？ | [hot-topic-radar](hot-topic-radar/) |
| AI 领域怎么选今天的话题？ | [aihot-topic-selector](aihot-topic-selector/) |
| 文章写完了，给它配个封面 | [cover-hero](cover-hero/) |
| 我想做短视频，怎么起步？ | [knowledge-short-video](knowledge-short-video/) |
| 我想搭个博客 / 个人站 | [personal-website-builder](personal-website-builder/) |
| 我想把代码推到 GitHub | [opensource-housekeeper](opensource-housekeeper/) |
| 我想跑一下网上的开源项目 | [opensource-housekeeper](opensource-housekeeper/) |
| 我想把公众号文章存本地（不登录） | [mp-saver](mp-saver/) |
| 哪个大模型能白嫖？Cursor 里哪个能白嫖？哪个 API 有免费额度？ | [free-ai-models](free-ai-models/) |

---

## 🏗️ 通用 skill 结构

每个 skill 目录都遵循相同结构：

```
skills/<skill-name>/
├── SKILL.md              # ⭐ 必读：skill 主定义（对话流程）
├── reference/            # 详细文档（命令速查、模板、配置说明）
├── scripts/              # 可执行脚本（Python/Shell）
├── templates/            # 模板文件（HTML/Markdown 等）
├── assets/               # 静态资源（图片、配置示例）
├── README.md             # 部分 skill 附带需求/设计笔记
└── progress.md / config  # 部分 skill 附带的进度/配置
```

**SKILL.md 是核心**——AI 通过读它的 frontmatter 决定何时触发，读正文决定怎么做。其他目录是参考资料和工具。

---

## 🔗 Skill 之间的衔接（推荐链路）

### 链路 1 · 自媒体内容生产全流程

```
[hot-topic-radar] 选题
    ↓
[人工写作]
    ↓
[cover-hero] 配图
    ↓
[发布]
```

### 链路 2 · 短视频生产全流程

```
[aihot-topic-selector 或 hot-topic-radar] 选题
    ↓
[knowledge-short-video] 写口播稿 + 渲染
    ↓
[发布]
```

### 链路 3 · 个人项目上 GitHub

```
[personal-website-builder] 建站
    ↓
[opensource-housekeeper] 推到 GitHub/AtomGit/Gitee
```

### 链路 4 · 跑开源项目

```
[opensource-housekeeper] 拉取 + 装依赖 + 跑起来
    ↓
[改代码 / 学习 / 部署]
```

### 链路 5 · 公众号文章存档 + 转 Markdown

```
[mp-saver] 把 mp.weixin.qq.com/s/... 保存为 MHTML 单文件
    ↓
[doc-speedreader] 把 .mhtml 转成 .md
    ↓
[喂给 LLM / 笔记软件 / RAG]
```

---

## ⚙️ 共同设计原则

所有 skill 都遵守以下原则（如果用户友好度比「正确」更重要）：

1. **纯对话式**：不弹窗、不做表单，所有选项通过对话询问
2. **一问一答**：每轮只问 1 个关键问题
3. **默认推荐**：对每个问题给出 ⭐ 推荐选项
4. **人话解释**：技术命令先用人话讲一遍再执行
5. **失败兜底**：每个失败处理都按「原文 + 人话 + 根因 + 3 步 + 兜底」5 段式
6. **零假设**：不假设用户已有任何前置条件（账号/凭证/技能）
7. **不强推**：用户放弃就放弃，不逼

---

## 📦 版本与状态

| Skill | 状态 | 最近更新 |
|---|---|---|
| aihot-topic-selector | ✅ 稳定 | 2026-07 |
| hot-topic-radar | ✅ 稳定 | 2026-07 |
| cover-hero | ✅ 稳定 | 2026-07 |
| mp-saver | ✅ v2.0 稳定（纯 HTTP 零依赖） | 2026-08-13 |
| knowledge-short-video | ✅ v2.2 稳定 | 2026-07 |
| personal-website-builder | ✅ 稳定 | 2026-06 |
| opensource-housekeeper | ✅ v2 稳定（已优化可用性） | 2026-07-03 |
| free-ai-models | ✅ v1 稳定 | 2026-07-12 |

---

## 📝 添加新 skill

在 `/Users/wanfeng/code/wanfeng-skills/todo/` 目录建一个待办文件夹，放设计笔记 + 需求起点。
然后用 `skill-creator` 创建 skill 目录到 `skills/` 下。

详见：[/Users/wanfeng/code/wanfeng-skills/skills/personal-website-builder/SKILL.md](personal-website-builder/SKILL.md) 内的成熟范式。