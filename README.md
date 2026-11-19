# 晚枫 Skills

> 一套**可复用的 AI Skill 集合**：让 AI Agent 通过对话完成自媒体内容生产、短视频剪辑、个人建站、开源协作等场景的完整工作流。

[![GitHub](https://img.shields.io/badge/GitHub-CoderWanFeng%2Fwanfeng--skills-blue?logo=github)](https://github.com/CoderWanFeng/wanfeng-skills)
[![AtomGit](https://img.shields.io/badge/AtomGit-CoderWanFeng1%2Fwanfeng--skills-orange?logo=git)](https://atomgit.com/CoderWanFeng1/wanfeng-skills)
[![skills.sh](https://img.shields.io/badge/skills.sh-Install%20Skills-black?logo=vercel)](https://www.skills.sh/coderwanfeng/wanfeng-skills)

---

## 🚀 快速开始

### 方式一：skills CLI 一键安装（推荐）

无需克隆仓库，一条命令把 Skill 装进你本地的 AI Agent（Claude Code / Cursor / Codex / Cline 等 20+ 客户端）：

```bash
# 安装单个 skill（以 mograph 为例）
npx skills add CoderWanFeng/wanfeng-skills --skill mograph

# 浏览仓库内全部 skill 后交互选择
npx skills add CoderWanFeng/wanfeng-skills
```

### 方式二：克隆仓库手动加载

```bash
# GitHub
git clone https://github.com/CoderWanFeng/wanfeng-skills.git

# 国内网络打不开 GitHub？用 AtomGit 镜像（内容与路径完全一致）
git clone https://atomgit.com/CoderWanFeng1/wanfeng-skills.git
```

然后在你的 AI Agent（Trae / Cursor / Claude Code 等）中加载对应目录的 `skills/<name>/SKILL.md` 即可触发。

### 装好之后，直接开口说：

| 你说 | 触发 |
|---|---|
| 「全网热搜今天值得跟什么」 | hot-topic-radar |
| 「我想搭一个个人博客」 | personal-website-builder |
| 「我想学 XX 这个开源项目怎么用」 | opensource-housekeeper |
| 「这条口播视频帮我自动剪辑，加点动效卡」 | mograph |
| 「这个选题做一条不出镜的 MG 短视频，横屏」 | ai-style-video |
| 「不登录把这篇公众号文章存下来」 | mp-saver |

---

## 📚 Skill 一览

17 个公开 Skill + 2 个付费 Skill，按场景分组（详细触发词与选用决策表见 [skills/README.md](skills/README.md)）：

### 🔍 选题与资讯

| Skill | 一句话用途 |
|---|---|
| [aihot-topic-selector](skills/aihot-topic-selector/) | 每天从 AIHOT 热点数据里自动选题，建 task 目录 [👉 介绍文章](https://www.python4office.cn/ads/ai/tools/AI热点选题/20261116-aihot选题skill-每天自动选一条/) |
| [hot-topic-radar](skills/hot-topic-radar/) | 7×24h 监控全网热搜，按关键词过滤 + 热度打分 [👉 介绍文章](https://www.python4office.cn/ads/ai/tools/选题雷达/20261116-选题雷达skill-全网热搜自动收集打分/) |
| [free-ai-models](skills/free-ai-models/) | 搜罗全网可白嫖的大模型（免费站点 / 软件内置 / API 额度）[👉 介绍文章](https://www.python4office.cn/ads/ai/tools/免费大模型查找器/20261116-免费大模型查找器skill-3轮对话问出能白嫖的大模型/) |

### ✍️ 图文创作

| Skill | 一句话用途 |
|---|---|
| [cover-hero](skills/cover-hero/) | 公众号 / 小红书 / 抖音等 8 平台的封面 + 配图（HTML 模板渲染）[👉 在线体验](https://qclaw.qq.com/as/BQ2Cw50sNfcy) |
| [wanfeng-writing-partner](skills/wanfeng-writing-partner/) | 晚枫写作搭子：AI 热点 / 产品体验 / 官方资料 → 可直接发布的中文长文，7 步全流程（选题→标题→结构→配图→图床→引用→检查） |
| [mp-saver](skills/mp-saver/) | 不登录保存公众号文章为单文件 MHTML，离线可看、可直接喂 LLM [👉 介绍文章](https://www.python4office.cn/ads/ai/tools/公众号保存侠/20261116-公众号保存侠skill-不登录存成单个文件/) |
| [doc-speedreader](skills/doc-speedreader/) | 晚枫速读侠：任意文档（PDF/Word/PPT 等 15+ 格式）一键转 Markdown + 摘要 [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-doc-speedreader) |

### 🎬 短视频

| Skill | 一句话用途 |
|---|---|
| [knowledge-short-video](skills/knowledge-short-video/) | 知识类短视频全流程：口播稿 → 视觉 → 动画 → TTS → 渲染 [👉 介绍文章](https://www.python4office.cn/ads/ai/tools/知识短视频/20261116-知识短视频skill-口播稿到成片一条命令/) |
| [ai-style-video](skills/ai-style-video/) | 晚枫AI动画：一句话生成 MG 短视频，8 风格 × 6 画幅 × 3 配音档，全程零付费 [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-ai-style-video) |
| [mograph](skills/mograph/) | 晚枫自动剪视频：给真人口播视频按讲话内容定时弹出字卡 / 数据 / 图表并渲染成片 [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-mograph) |
| [mograph-pro](skills/mograph-pro/) 💰 | 付费 Pro 版：晚枫自有风格 10 步一条龙（成片 + 封面换皮），自包含不装 Node |
| [wanfeng-digital-human](skills/wanfeng-digital-human/) | 一段视频 / 一张照片 → 4–10 秒会说话的数字人短片，零成本（只扣软件积分）[👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-digital-human) |
| [wanfeng-digital-human-pro](skills/wanfeng-digital-human-pro/) 💰 | 付费 Pro 版：30 秒以上长口播生产线，本人克隆音色、批量系列 |

### 🌐 建站与开源

| Skill | 一句话用途 |
|---|---|
| [personal-website-builder](skills/personal-website-builder/) | 对话式引导建个人网站（博客 / 知识库 / 作品集 / 简历）+ 多平台一键部署 [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-personal-website-builder) |
| [opensource-housekeeper](skills/opensource-housekeeper/) | 晚枫开源管家：零基础陪跑「找到 → 讲清 → 跑通 → 读懂 → 改一处用出效果」，也能反向发布 [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-opensource-housekeeper) |
| [repowiki-generator](skills/repowiki-generator/) | 晚枫知识库：为任意项目生成结构化 Wiki 文档，让 Agent 秒懂项目 [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-repowiki-generator) |
| [workbuddy-daily-credits](skills/workbuddy-daily-credits/) | WorkBuddy 成长中心每日积分自动领取（签到 / 猫猫旅行 / 开盲盒）[👉 介绍文章](https://www.python4office.cn/ads/ai/tools/WorkBuddy积分/20261116-workbuddy积分skill-签到猫猫盲盒自动领/) |

> 💰 两个付费 Skill（mograph-pro、wanfeng-digital-human-pro）不在公开仓库分发，购买与安装渠道见 SkillHub / WorkBuddy 开放平台。

---

## 🔗 推荐链路

Skill 之间相互独立，但串起来就是完整生产线：

```
图文线   [选题雷达/AIHOT] → [wanfeng-writing-partner] 写长文（含配图/图床）→ 发布
短视频线  [选题] → [knowledge-short-video] 出镜片 / [ai-style-video] 不出镜 MG 片 → 发布
口播包装  已拍口播视频 + 讲稿 → [mograph] 弹卡动效成片 → [cover-hero] 同视觉封面
存档线    [mp-saver] 公众号文章 → MHTML → [doc-speedreader] 转 Markdown → 喂 LLM
建站线    [personal-website-builder] 建站 → [opensource-housekeeper] 推 GitHub
```

---

## 🏗️ Skill 结构与设计原则

每个 Skill 都是一个自包含目录，`SKILL.md` 是对外契约（AI 读 frontmatter 决定何时触发，读正文决定怎么做）：

```
skills/<skill-name>/
├── SKILL.md      # ⭐ 核心：对话流程定义
├── references/   # 参考文档（命令速查、模板、配置说明）
├── scripts/      # 可执行脚本（以 Python 标准库为主）
├── templates/    # 模板文件
└── assets/       # 静态资源
```

所有 Skill 遵守同一套 UX 契约：**纯对话式 · 一问一答 · 默认推荐 · 人话解释 · 失败兜底（5 段式） · 零假设 · 不强推**。

---

## 📦 分发渠道

| 渠道 | 形态 |
|---|---|
| [GitHub](https://github.com/CoderWanFeng/wanfeng-skills) / [AtomGit 镜像](https://atomgit.com/CoderWanFeng1/wanfeng-skills) | 源码与内容源头 |
| [skills.sh](https://www.skills.sh/coderwanfeng/wanfeng-skills) | `npx skills add` 一键安装 |
| [SkillHub](https://skillhub.cn/skills/user_bf8c5b73) | 免费 + 付费 skill 发布页 |
| WorkBuddy 开放平台 | ZIP 包上架（含付费版） |

---

## 📝 添加新 Skill

在仓库根 `todo/` 目录建待办文件夹（设计笔记 + 需求起点），然后用 `skill-creator` 创建 Skill 到 `skills/` 下。
成熟范式参考 [personal-website-builder](skills/personal-website-builder/SKILL.md)。

---

## 📄 License

MIT

> 各 Skill 目录的授权以该目录自带的说明为准 —— `mograph-pro` 是**付费产品**，
> 适用其目录内 LICENSE.md 的商业授权条款，不适用仓库根的 MIT。
