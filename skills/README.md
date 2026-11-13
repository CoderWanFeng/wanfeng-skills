# wanfeng-skills / skills 目录

> 这是一个**可复用的 AI Skill 集合**。每个子目录都是一个独立的 skill，对应一个具体的工作流。
> Skill 之间**正交**：可单独使用，也可按场景串起来。

---

## 📚 Skill 一览（11 个）

| Skill | 用途 | 适用场景 | 触发词举例 | 在线体验 |
|---|---|---|---|---|
| [**aihot-topic-selector**](aihot-topic-selector/) | 从 AIHOT 热点数据里每天自动选题 | 自媒体日常选题、内容运营 | 「今天 AI 有什么热点」「按热点选个题」 | — |
| [**hot-topic-radar**](hot-topic-radar/) | 7×24h 监控全网热搜，按关键词过滤 + 热度打分 | 自媒体选题雷达、跨平台聚合 | 「监控 XX 话题」「全网热搜」「今天值得跟什么」 | — |
| [**cover-hero**](cover-hero/) | 给公众号文章做封面 + 正文配图（HyperFrames 风格） | 公众号配图、长文视觉 | 「做公众号封面」「配张图」「头图」 | [👉 封面侠](https://qclaw.qq.com/as/BQ2Cw50sNfcy) |
| [**mp-saver**](mp-saver/) | 不登录保存公众号文章为单文件 MHTML（HTML + base64 内嵌图片，离线可看）。v2.0 起零依赖（只用 Python 标准库 urllib） | 公众号文章收藏、批量存档、喂 LLM | 「保存公众号文章」「下载公众号文章」「不登录存公众号」 | — |
| [**knowledge-short-video**](knowledge-short-video/) | 知识类短视频全流程（口播稿 → 视觉 → 动画 → TTS → 渲染） | 短视频制作、知识科普 | 「做条知识视频」「短视频口播稿」 | — |
| [**personal-website-builder**](personal-website-builder/) | 对话式引导创建个人网站（博客/知识库/作品集/简历） | 个人建站、博客搭建 | 「我想做个博客」「搭个个人网站」「建个简历站」 | [👉 建站搭子](https://qclaw.qq.com/as/5oDmikXxsQEo) |
| [**opensource-housekeeper**](opensource-housekeeper/) | 晚枫开源管家：给零基础小白做开源项目陪跑——找到项目 → 讲清它是干嘛的 → 拉下来跑起来 → 读懂它 → 改一处、用出效果；也能反向发布项目、生成项目文档 | 开源小白、学用开源项目、跨平台发布 | 「我想学 XX 怎么用」「这项目干嘛」「帮我推到 GitHub」「拉一下 llama.cpp 跑起来」 | [👉 晚枫开源管家](https://qclaw.qq.com/as/4VlrmxmvAnlV) |
| [**free-ai-models**](free-ai-models/) | 搜罗全网可以免费使用的大模型（直接用 / 软件内置 / 平台免费额度） | 找免费 GPT/Claude/Gemini、找软件里能白嫖的模型、找永久免费 API | 「免费大模型」「GPT 免费吗」「Cursor 里哪个免费」「API 免费额度」 | — |
| [**wanfeng-digital-human**](wanfeng-digital-human/) | 把一段视频或一张照片变成 4–10 秒会说话的数字人短片（MiniMax 克隆音色 + 自动字幕） | 数字人口播、不露脸出镜、照片说话 | 「做个数字人视频」「让我的照片说话」「用我的声音念这段话」「做一条十秒口播」 | — |
| [**mograph**](mograph/) | 晚枫自动剪辑：给真人口播视频按讲话内容自动加动效卡（数字滚动 / 图表 / 分屏对比 / 清单 / 引用卡），在人的上下左右定时弹出并渲染成片。v1「检索驱动」：运行时由本地 AI 联网拉社区最新的 Remotion / HyperFrames 实现 | 口播视频包装、出镜科普、lower-third 数据卡 | 「自动剪辑」「口播加动画」「给视频贴片」「上下左右弹卡」「加数据卡」「用 Remotion 给口播做叠加」 | — |
| [**ai-style-video**](ai-style-video/) | 晚枫AI动画：把任意选题做成 8 种风格的竖屏 MG 静音样片（1080×1920 / 24–25s / 9 场景）。**先选风格 → 再按清单交素材** → 渲染样片，自带文字重叠检测、缺素材占位卡、跨平台字体解析 | 不出镜的 MG 短视频、产品/功能/事件/教程解读 | 「做条不出镜的 MG 视频」「选个风格重做这条」「素材要哪些」「证据图发虚」 | — |

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
- **[wanfeng-digital-human](wanfeng-digital-human/)** — 数字人：一段素材 + 一句话，出 4–10 秒会说话的短片（克隆音色 + 自动字幕）
- **[mograph](mograph/)** — 晚枫自动剪辑：真人已出镜的视频 + 口播稿 → 按讲话内容在四周弹卡（不重拍、不剪镜头）
- **[ai-style-video](ai-style-video/)** — 晚枫AI动画，不出镜的风格 MG 片：任何选题 → 先选 8 种风格之一 → 按清单交素材 → 竖屏静音样片

### 🌐 个人项目 / 建站

- **[personal-website-builder](personal-website-builder/)** — 对话式建站：5 种类型（博客/知识库/AI 导航/作品集/简历）

### 🚀 开源协作

- **[opensource-housekeeper](opensource-housekeeper/)** — 晚枫开源管家：主打「学用开源项目」（找到 → 讲清 → 跑通 → 读懂 → 改一处用出效果），也能反向发布项目、生成项目文档

---

## 🎯 如何选用 skill？

| 你想做的事 | 用这个 skill |
|---|---|
| 我要做自媒体，从哪开始找选题？ | [hot-topic-radar](hot-topic-radar/) |
| AI 领域怎么选今天的话题？ | [aihot-topic-selector](aihot-topic-selector/) |
| 文章写完了，给它配个封面 | [cover-hero](cover-hero/) |
| 我想做短视频，怎么起步？ | [knowledge-short-video](knowledge-short-video/) |
| 我想用我的脸和声音做口播短片 | [wanfeng-digital-human](wanfeng-digital-human/) |
| 我想搭个博客 / 个人站 | [personal-website-builder](personal-website-builder/) |
| 我想把代码推到 GitHub | [opensource-housekeeper](opensource-housekeeper/) |
| 我想学一个开源项目、把它真正用起来 | [opensource-housekeeper](opensource-housekeeper/) |
| 我想把公众号文章存本地（不登录） | [mp-saver](mp-saver/) |
| 哪个大模型能白嫖？Cursor 里哪个能白嫖？哪个 API 有免费额度？ | [free-ai-models](free-ai-models/) |
| 视频已经拍好了，只想在讲话时旁边弹出数据卡 / 图表 | [mograph](mograph/) |
| 手上有一推资料（官网/公告/数据），想快速出条竖屏短视频，人不出镜 | [ai-style-video](ai-style-video/) |

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

不出镜的版本（只要静音 MG 样片）：

```
[aihot-topic-selector 或 hot-topic-radar] 选题
    ↓
[ai-style-video] 选风格 → 按清单交素材 → 渲染竖屏静音 MG
    ↓
[wanfeng-digital-human] 需要口播时再叠数字人
```

### 链路 3 · 个人项目上 GitHub

```
[personal-website-builder] 建站
    ↓
[opensource-housekeeper] 推到 GitHub/AtomGit/Gitee
```

### 链路 4 · 学用开源项目（主打）

```
[opensource-housekeeper] 找到项目 → 用人话讲清它是干嘛的
    ↓
拉取 + 装依赖 + 跑起来
    ↓
读懂结构 → 改一处 → 用自己的东西跑出效果
```

### 链路 5 · 公众号文章存档 + 转 Markdown

```
[mp-saver] 把 mp.weixin.qq.com/s/... 保存为 MHTML 单文件
    ↓
[doc-speedreader] 把 .mhtml 转成 .md
    ↓
[喂给 LLM / 笔记软件 / RAG]
```

### 链路 6 · 真人口播视频的动效包装

```
[knowledge-short-video] 出口播稿（或自己写的稿）
    ↓  稿子 + 已拍好的出镜视频（可选 .srt / 词级时间戳）
[mograph] 出 overlay-spec.json → 联网检索动效实现 → 渲染弹卡成片
    ↓
[cover-hero] 同账号视觉令牌出封面
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
| wanfeng-digital-human | ✅ v1 可用（待配 MiniMax Key） | 2026-11 |
| mograph（晚枫自动剪辑） | 🚧 v1 首发（骨架脚本本地跑通；渲染链路待 v1.1 实测） | 2026-11 |
| ai-style-video（晚枫AI动画） | ✅ v2.0 稳定（8 种风格均已验证；字体跨平台；不限题材；配音 / 字幕不在范围内） | 2026-11-13 |

---

## 📝 添加新 skill

在 `/Users/wanfeng/code/wanfeng-skills/todo/` 目录建一个待办文件夹，放设计笔记 + 需求起点。
然后用 `skill-creator` 创建 skill 目录到 `skills/` 下。

详见：[/Users/wanfeng/code/wanfeng-skills/skills/personal-website-builder/SKILL.md](personal-website-builder/SKILL.md) 内的成熟范式。