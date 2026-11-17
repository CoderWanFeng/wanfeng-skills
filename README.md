# wanfeng-skills

> 一个**可复用的 AI Skill 集合** —— 让 AI Agent 通过对话完成自媒体内容生产、个人建站、开源协作等场景的完整工作流。

[![GitHub](https://img.shields.io/badge/GitHub-CoderWanFeng%2Fwanfeng--skills-blue?logo=github)](https://github.com/CoderWanFeng/wanfeng-skills)
[![AtomGit](https://img.shields.io/badge/AtomGit-CoderWanFeng1%2Fwanfeng--skills-orange?logo=git)](https://atomgit.com/CoderWanFeng1/wanfeng-skills)

---

## ✨ 这是什么？

本仓库沉淀了 **11 个相互独立、可自由组合**的 AI Skill（完整清单见 [skills/README.md](skills/README.md)）。每个 Skill 都是一个针对真实场景的「对话式工作流」，AI 通过读取 Skill 定义，自动完成从「用户开口」到「产物交付」的完整链路。

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
| [**opensource-housekeeper**](skills/opensource-housekeeper/) | 晚枫开源管家：给零基础小白做开源项目陪跑——找到项目 → 讲清它是干嘛的 → 拉下来跑起来 → 读懂它 → 改一处、用出效果；也能反向发布项目、生成项目文档 | 开源小白、学用开源项目、跨平台发布 | [👉 晚枫开源管家](https://qclaw.qq.com/as/4VlrmxmvAnlV) |
| [**wanfeng-digital-human**](skills/wanfeng-digital-human/) | 把一段视频或一张照片变成 4–10 秒会说话的数字人短片。**零成本**：只扣软件积分，不用密钥、不绑支付；台词模型用内置音色念，可换本人原声 | 数字人口播、不露脸出镜、照片说话、零成本试效果 | [👉 数字人](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-digital-human) |
| [**wanfeng-digital-human-pro**](skills/wanfeng-digital-human-pro/) | 💰 **晚枫数字人 Pro**：完整口播长视频生产线。三画面后端（MiniMax H3 / 自托管 H3 / 软件积分）× 两语音后端（MiniMax 克隆 / 本地 Ming），MiniMax 再分官方与推荐平台 API；交付分段配音、出镜片段、时间码表与拼接片 | 30 秒以上长口播、本人克隆音色、批量系列、有 GPU 想压成本 | — |
| [**mograph**](skills/mograph/) | 晚枫自动剪视频：给真人口播视频按讲话内容自动加动效卡（数字滚动 / 图表 / 分屏对比 / 清单 / 引用），在人的上下左右定时弹出并渲染成片。内置两条路径：通用路径走检索驱动；**晚枫专用路径**是自有风格的完整打法（Pillow 自绘 + 手写场景表 + 圆形人头 + 步骤条版式 + 语速映射 + 响度归一），开工前先选 | 口播视频包装、出镜科普、数据 lower-third、做自己账号的固定调性 | — |
| [**mograph-pro**](skills/mograph-pro/) | 💰 **晚枫自动剪视频-Pro（付费版）**：一条真人口播 → 有版式的成片 + 封面。10 步一条龙（删减授权 → 定版式 → 配图采集 → 场景表 → 静帧 → 重渲 → 终检 → 响度 → 交接 → 封面换皮），Pillow 2 倍超采样自绘、fs 全屏设计版式、圆形人头、步骤条、手写场景表、语速映射、两遍法响度归一、固定底图封面换皮。**本地没有合适的 logo 会自己从官方源下载**（准确性优先于好看，来源登记进台账）。**自包含，不装 Node、不起浏览器** | 做自己账号的固定调性成片、需要封面换皮、要把整套打法单独交付给别人 | — |
| [**ai-style-video**](skills/ai-style-video/) | 晚枫AI动画（一句话生成 AI 视频）：把任意选题做成 8 种风格 × 6 种画幅的 MG 短片（24–25s）：开场四问「选风格 → 选画幅 → 选配音 → 交素材」，风格和画幅互相独立，自带文字重叠检测、缺素材占位与 ffmpeg 混流 | 不出镜的 MG 短视频、产品/功能/事件解读、竖屏抖音小红书 + 横屏B站YouTube | — |

📖 详细说明见 [skills/README.md](skills/README.md)

---

## 🚀 快速开始

每个 Skill 都是**独立的**，可以单独使用：

```bash
# 1. 克隆仓库
git clone https://github.com/CoderWanFeng/wanfeng-skills.git

#    国内网络打不开 GitHub？用 AtomGit 镜像（由 GitHub 同步，内容与路径完全一致）
git clone https://atomgit.com/CoderWanFeng1/wanfeng-skills.git

# 2. 在你的 AI Agent（Trae / Cursor / Claude Code 等）中加载对应 Skill 目录
#    例如加载 cover-hero：
#      /skills/cover-hero/SKILL.md
```

然后在对话里说出你的需求，比如：
- 「帮我监控一下 AI 圈今天的热点」 → 触发 `hot-topic-radar`
- 「我想搭一个个人博客」 → 触发 `personal-website-builder`
- 「我想学 XX 这个开源项目怎么用」 → 触发 `opensource-housekeeper`
- 「帮我把这个项目推到 GitHub」 → 触发 `opensource-housekeeper`
- 「这条口播视频帮我自动剪辑，根据讲的内容加点动效卡」 → 触发 `mograph`
- 「这条口播视频按我们自己的风格剪，走晚枫专用」 → 触发 `mograph`（晚枫专用路径）
- 「这条口播视频按晚枫 Pro 版剪，做完顺便换张封面」 → 触发 `mograph-pro`（付费版晚枫自动剪视频-Pro）
- 「这个选题帮我做一条不出镜的 MG 短视频，横屏的」 → 触发 `ai-style-video`

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

### 链路 4 · 学用开源项目（主打）

```
[opensource-housekeeper]   找到项目 → 用人话讲清它是干嘛的
                ↓
            拉取 + 装依赖 + 跑起来
                ↓
      读懂结构 → 改一处 → 用自己的东西跑出效果
```

### 链路 5 · 真人口播视频的动效包装

```
[knowledge-short-video]              出口播稿
            ↓  稿子 + 已拍好的出镜视频
[mograph]                       分镜 → 联网找动效实现 → 渲染弹卡
            ↓
       [cover-hero]                同视觉出封面
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
| wanfeng-digital-human（晚枫数字人） | ✅ v2.0 可用（只走软件积分，零成本、4–10 秒，无需密钥） | 2026-11-17 |
| wanfeng-digital-human-pro（晚枫数字人 Pro） | ✅ v2.0 可用（三画面后端 × 两语音后端；原 wanfeng-h3 已并入，云端 H3 端到端待验收） | 2026-11-17 |
| mograph（晚枫自动剪视频） | 🚧 v1.1（通用路径骨架脚本本地跑通；**晚枫专用路径已跑通全链路并交付成片** —— Pillow 自绘 + 手写场景表 + 圆形人头 + 语速映射 + 两遍法响度归一，见 skills/mograph/reference/wanfeng-path.md） | 2026-11-16 |
| mograph-pro（晚枫自动剪视频-Pro） | ✅ v1.1 **付费版**（自包含：10 步执行流 + 设计令牌 + 版式库 + 封面固定资产 + 商业授权 LICENSE.md；与免费版 mograph 的晚枫线同源）**新增：封面 logo 本地没有合适的就自己从官方源下载（准确性优先于好看，来源登记进 asset-manifest.json）** | 2026-11-17 |
| ai-style-video（晚枫AI动画） | ✅ v2.3 稳定（8 种风格 + I 自定义本地跑通；6 种画幅 9:16/2:3/4:5/1:1/16:9/4:3，与风格互相独立；三档配音 S 静音 / V1 系统电子音 / V2 本地模型克隆；字体跨平台；全程零付费） | 2026-11-16 |

---

## 📝 添加新 Skill

在 `todo/` 目录建一个待办文件夹，放设计笔记 + 需求起点。
然后用 `skill-creator` 创建 Skill 目录到 `skills/` 下。

详见 [skills/personal-website-builder/SKILL.md](skills/personal-website-builder/SKILL.md) 内的成熟范式。

---

## 📄 License

MIT

> 各 skill 目录的授权以该目录自带的说明为准 —— `mograph-pro` 是**付费产品**，
> 适用 [skills/mograph-pro/LICENSE.md](skills/mograph-pro/LICENSE.md) 的商业授权条款，
> 不适用仓库根的 MIT。