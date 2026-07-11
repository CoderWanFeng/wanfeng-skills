# wanfeng-skills

> 一个**可复用的 AI Skill 集合** —— 让 AI Agent 通过对话完成自媒体内容生产、个人建站、开源协作等场景的完整工作流。

[![GitHub](https://img.shields.io/badge/GitHub-CoderWanFeng%2Fwanfeng--skills-blue?logo=github)](https://github.com/CoderWanFeng/wanfeng-skills)

---

## ✨ 这是什么？

本仓库沉淀了 **6 个相互独立、可自由组合**的 AI Skill。每个 Skill 都是一个针对真实场景的「对话式工作流」，AI 通过读取 Skill 定义，自动完成从「用户开口」到「产物交付」的完整链路。

设计原则：**纯对话、一问一答、人话解释、零假设、不强推**。

---

## 📚 Skill 一览

| Skill | 用途 | 适用场景 | 在线体验 |
|---|---|---|---|
| [**aihot-topic-selector**](skills/aihot-topic-selector/) | 从 AIHOT 热点数据里每天自动选题 | 自媒体日常选题、内容运营 | — |
| [**hot-topic-radar**](skills/hot-topic-radar/) | 7×24h 监控全网热搜，按关键词过滤 + 热度打分 | 自媒体选题雷达、跨平台聚合 | — |
| [**cover-hero**](skills/cover-hero/) | 给公众号文章做封面 + 正文配图（HyperFrames 风格） | 公众号配图、长文视觉 | [👉 封面侠](https://qclaw.qq.com/as/BQ2Cw50sNfcy) |
| [**knowledge-short-video**](skills/knowledge-short-video/) | 知识类短视频全流程（口播稿 → 视觉 → 动画 → TTS → 渲染） | 短视频制作、知识科普 | — |
| [**personal-website-builder**](skills/personal-website-builder/) | 对话式引导创建个人网站（博客/知识库/作品集/简历） | 个人建站、博客搭建 | [👉 建站搭子](https://qclaw.qq.com/as/5oDmikXxsQEo) |
| [**opensource-housekeeper**](skills/opensource-housekeeper/) | 一站式开源管家：发布本地项目到 GitHub/AtomGit/Gitee + 拉取网上的项目本地运行 | 开源小白、跨平台发布、跑开源项目 | [👉 开源管家](https://qclaw.qq.com/as/4VlrmxmvAnlV) |

📖 详细说明见 [skills/README.md](skills/README.md)

---

## 🚀 快速开始

每个 Skill 都是**独立的**，可以单独使用：

```bash
# 1. 克隆仓库
git clone https://github.com/CoderWanFeng/wanfeng-skills.git

# 2. 在你的 AI Agent（Trae / Cursor / Claude Code 等）中加载对应 Skill 目录
#    例如加载 cover-hero：
#      /skills/cover-hero/SKILL.md
```

然后在对话里说出你的需求，比如：
- 「帮我监控一下 AI 圈今天的热点」 → 触发 `hot-topic-radar`
- 「我想搭一个个人博客」 → 触发 `personal-website-builder`
- 「帮我把这个项目推到 GitHub」 → 触发 `opensource-housekeeper`

---

## 🔗 推荐链路

### 链路 1 · 自媒体内容生产全流程

```
[hot-topic-radar / aihot-topic-selector]  选题
                ↓
            [人工写作]
                ↓
          [cover-hero]                     配图
                ↓
              [发布]
```

### 链路 2 · 短视频生产全流程

```
[aihot-topic-selector / hot-topic-radar]   选题
                ↓
   [knowledge-short-video]            写口播稿 + 渲染
                ↓
              [发布]
```

### 链路 3 · 个人项目上 GitHub

```
[personal-website-builder]   建站
                ↓
[opensource-housekeeper]    推到 GitHub / AtomGit / Gitee
```

### 链路 4 · 跑开源项目

```
[opensource-housekeeper]   拉取 + 装依赖 + 跑起来
                ↓
       [改代码 / 学习 / 部署]
```

---

## 🏗️ 通用 Skill 结构

```
skills/<skill-name>/
├── SKILL.md              # ⭐ 必读：Skill 主定义（对话流程）
├── reference/            # 详细文档（命令速查、模板、配置说明）
├── scripts/              # 可执行脚本（Python / Shell）
├── templates/            # 模板文件（HTML / Markdown 等）
├── assets/               # 静态资源（图片、配置示例）
├── README.md             # 部分 Skill 附带需求/设计笔记
└── progress.md / config  # 部分 Skill 附带的进度/配置
```

**SKILL.md 是核心**——AI 通过读它的 frontmatter 决定何时触发，读正文决定怎么做。

---

## ⚙️ 设计原则

所有 Skill 都遵守以下原则：

1. **纯对话式** —— 不弹窗、不做表单，所有选项通过对话询问
2. **一问一答** —— 每轮只问 1 个关键问题
3. **默认推荐** —— 对每个问题给出 ⭐ 推荐选项
4. **人话解释** —— 技术命令先用人话讲一遍再执行
5. **失败兜底** —— 每个失败处理都按「原文 + 人话 + 根因 + 3 步 + 兜底」5 段式
6. **零假设** —— 不假设用户已有任何前置条件（账号/凭证/技能）
7. **不强推** —— 用户放弃就放弃，不逼

---

## 📦 版本与状态

| Skill | 状态 | 最近更新 |
|---|---|---|
| aihot-topic-selector | ✅ 稳定 | 2026-07 |
| hot-topic-radar | ✅ 稳定 | 2026-07 |
| cover-hero | ✅ 稳定 | 2026-07 |
| knowledge-short-video | ✅ v2.2 稳定 | 2026-07 |
| personal-website-builder | ✅ 稳定 | 2026-06 |
| opensource-housekeeper | ✅ v2 稳定 | 2026-07-03 |

---

## 📝 添加新 Skill

在 `todo/` 目录建一个待办文件夹，放设计笔记 + 需求起点。
然后用 `skill-creator` 创建 Skill 目录到 `skills/` 下。

详见 [skills/personal-website-builder/SKILL.md](skills/personal-website-builder/SKILL.md) 内的成熟范式。

---

## 📄 License

MIT