# wanfeng-skills / skills 目录

> 这是一个**可复用的 AI Skill 集合**。每个子目录都是一个独立的 skill，对应一个具体的工作流。
> Skill 之间**正交**：可单独使用，也可按场景串起来。

---

## 📚 Skill 一览（13 个）

| Skill | 用途 | 适用场景 | 触发词举例 | 在线体验 |
|---|---|---|---|---|
| [**aihot-topic-selector**](aihot-topic-selector/) | 从 AIHOT 热点数据里每天自动选题 | 自媒体日常选题、内容运营 | 「今天 AI 有什么热点」「按热点选个题」 | — |
| [**hot-topic-radar**](hot-topic-radar/) | 7×24h 监控全网热搜，按关键词过滤 + 热度打分 | 自媒体选题雷达、跨平台聚合 | 「监控 XX 话题」「全网热搜」「今天值得跟什么」 | — |
| [**cover-hero**](cover-hero/) | 给公众号文章做封面 + 正文配图（HyperFrames 风格） | 公众号配图、长文视觉 | 「做公众号封面」「配张图」「头图」 | [👉 封面侠](https://qclaw.qq.com/as/BQ2Cw50sNfcy) |
| [**mp-saver**](mp-saver/) | 不登录保存公众号文章为单文件 MHTML（HTML + base64 内嵌图片，离线可看）。v2.0 起零依赖（只用 Python 标准库 urllib） | 公众号文章收藏、批量存档、喂 LLM | 「保存公众号文章」「下载公众号文章」「不登录存公众号」 | — |
| [**knowledge-short-video**](knowledge-short-video/) | 知识类短视频全流程（口播稿 → 视觉 → 动画 → TTS → 渲染） | 短视频制作、知识科普 | 「做条知识视频」「短视频口播稿」 | — |
| [**personal-website-builder**](personal-website-builder/) | 对话式引导创建个人网站（博客/知识库/作品集/简历） | 个人建站、博客搭建 | 「我想做个博客」「搭个个人网站」「建个简历站」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-personal-website-builder) |
| [**opensource-housekeeper**](opensource-housekeeper/) | 晚枫开源管家：给零基础小白做开源项目陪跑——找到项目 → 讲清它是干嘛的 → 拉下来跑起来 → 读懂它 → 改一处、用出效果；也能反向发布项目、生成项目文档 | 开源小白、学用开源项目、跨平台发布 | 「我想学 XX 怎么用」「这项目干嘛」「帮我推到 GitHub」「拉一下 llama.cpp 跑起来」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-opensource-housekeeper) |
| [**free-ai-models**](free-ai-models/) | 搜罗全网可以免费使用的大模型（直接用 / 软件内置 / 平台免费额度） | 找免费 GPT/Claude/Gemini、找软件里能白嫖的模型、找永久免费 API | 「免费大模型」「GPT 免费吗」「Cursor 里哪个免费」「API 免费额度」 | — |
| [**wanfeng-digital-human**](wanfeng-digital-human/) | 把一段视频或一张照片变成 4–10 秒会说话的数字人短片。**零成本**：只扣软件积分，不填密钥、不绑支付；台词由模型用内置音色念出，可事后替换成自己的原声 | 数字人口播、不露脸出镜、照片说话、先花零成本试效果 | 「做个数字人视频」「让我的照片说话」「AI 替我说话」「做一条十秒口播」「用积分做数字人」 | — |
| [**wanfeng-digital-human-pro**](wanfeng-digital-human-pro/) | 💰 **晚枫数字人 Pro**：完整口播长视频生产线。三画面后端（MiniMax H3 / 自托管 H3 / 软件积分）× 两语音后端（MiniMax 克隆 / 本地 Ming），MiniMax 再分官方 API 与推荐平台 API；交付分段配音、出镜片段、`a_roll.json` 时间码表、`a_roll.srt` 与拼接片 | 30 秒以上长口播、要本人克隆音色、批量做系列、有 GPU 实例想压成本 | 「用我自己的声音做口播」「做条 2 分钟的数字人长视频」「批量做矩阵号短视频」 | — |
| [**mograph**](mograph/) | 晚枫自动剪视频：给真人口播视频按讲话内容自动加动效卡（数字滚动 / 图表 / 分屏对比 / 清单 / 引用卡），在人的上下左右定时弹出并渲染成片。通用路径「检索驱动」：运行时由本地 AI 联网拉社区最新的 Remotion / HyperFrames 实现；**晚枫专用路径**：自有风格完整打法（Pillow 自绘 + 手写场景表 + 圆形人头 + 步骤条 + 语速映射 + 响度归一），开工前先选（该路径另已独立成付费版 [mograph-pro](mograph-pro/)，本 skill 内为同源实现、免费可用） | 口播视频包装、出镜科普、lower-third 数据卡、做自己账号的固定调性 | 「自动剪辑」「口播加动画」「给视频贴片」「上下左右弹卡」「加数据卡」「用 Remotion 给口播做叠加」「晚枫专用」「按我们自己的风格剪」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-mograph) |
| [**mograph-pro**](mograph-pro/) | 💰 **晚枫自动剪视频-Pro（付费版）**：一条真人口播 → 有版式的成片 + 封面。10 步一条龙（删减授权 → 定版式 → 配图采集 → 场景表 → 静帧 → 重渲 → 终检 → 响度 → 交接 → 封面换皮），Pillow 2 倍超采样自绘、fs 全屏设计版式、圆形人头、步骤条、手写场景表、语速映射、两遍法响度归一、固定底图封面换皮。**本地没有合适的 logo 会自己从官方源下载**（准确性优先于好看，来源登记进台账）。**自包含，不装 Node、不起浏览器、不联网找现成动效代码** | 做自己账号的固定调性成片、需要封面换皮、要把整套打法单独交付给别人 | 「按我们自己的风格剪」「走晚枫那条路」「Pro 版剪」「做完顺便换张封面」「封面换皮」「换 logo」「产品 logo」 | — |
| [**ai-style-video**](ai-style-video/) | **一句话生成 AI 视频**：任意素材（描述/文档/截图/数据）→ MG 短视频（24–25s / 9 场景）。**开场四问**：选风格（A–H + I 自定义）→ 选画幅（9:16 / 2:3 / 4:5 / 1:1 / 16:9 / 4:3，与风格互相独立）→ 选配音（S 静音 / V1 系统电子音 / V2 本地模型克隆音色）→ 交素材。自带文字重叠检测、缺素材占位、跨平台字体解析、画幅适配层、ffmpeg 混流 | 不出镜的 MG 短视频、产品/功能/事件/教程解读、要横版（B站/YouTube）也要竖版（抖音/小红书）、想克隆自己音色配音 | 「做条不出镜的 MG 视频」「选个风格重做这条」「这条改横屏」「用我的声音念这段」「素材要哪些」「证据图发虚」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-ai-style-video) |

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
- **[wanfeng-digital-human](wanfeng-digital-human/)** — 数字人（零成本）：一段素材 + 一句话，出 4–10 秒会说话的短片，只扣软件积分，模型念台词、可换原声
- **[wanfeng-digital-human-pro](wanfeng-digital-human-pro/)** — 💰 数字人 Pro：完整口播生产线，三画面后端 × 两语音后端，交付时间码表与拼接片
- **[mograph](mograph/)** — 晚枫自动剪视频：真人已出镜的视频 + 口播稿 → 按讲话内容在四周弹卡（不重拍、不剪镜头）
- **[mograph-pro](mograph-pro/)** — 💰 晚枫自动剪视频-Pro（付费版）：晚枫那条线独立成**自包含** skill —— 成片 + 封面一条龙，设计令牌 / 版式库 / 封面固定资产 / 商业授权一起交付
- **[ai-style-video](ai-style-video/)** — 晚枫AI动画，不出镜的风格 MG 片：任何选题 → 选风格（8 种 + 自定义）→ 选画幅（6 种，竖屏到横屏都行）→ 选配音 → 按清单交素材 → 样片

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
| 我想零成本试一条会说话的数字人短片 | [wanfeng-digital-human](wanfeng-digital-human/) |
| 我要用自己的克隆音色做 30 秒以上的口播长视频 | [wanfeng-digital-human-pro](wanfeng-digital-human-pro/) |
| 我想搭个博客 / 个人站 | [personal-website-builder](personal-website-builder/) |
| 我想把代码推到 GitHub | [opensource-housekeeper](opensource-housekeeper/) |
| 我想学一个开源项目、把它真正用起来 | [opensource-housekeeper](opensource-housekeeper/) |
| 我想把公众号文章存本地（不登录） | [mp-saver](mp-saver/) |
| 哪个大模型能白嫖？Cursor 里哪个能白嫖？哪个 API 有免费额度？ | [free-ai-models](free-ai-models/) |
| 视频已经拍好了，只想在讲话时旁边弹出数据卡 / 图表 | [mograph](mograph/) |
| 要一条自己账号固定调性的成片，还要封面换皮 | [mograph-pro](mograph-pro/) |
| 手上有一推资料（官网/公告/数据），想快速出条短视频（竖屏横屏都行），人不出镜 | [ai-style-video](ai-style-video/) |

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

不出镜的版本（MG 样片，可选本地配音 / 音色克隆）：

```
[aihot-topic-selector 或 hot-topic-radar] 选题
    ↓
[ai-style-video] 选风格 → 选画幅（6 种） → 选配音（S 静音 / V1 电子音 / V2 克隆音色） → 按清单交素材 → 渲染 MG + 混音
    ↓
[wanfeng-digital-human] 需要真人出镜时再叠数字人
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
| personal-website-builder | ✅ v2.3 稳定（对话式建站，6 种类型；**Step 0 文件完整性自检与还原** —— 针对安装平台过滤 `.gitignore` 隐藏文件、`.template` 后缀文件与 `.vue` 组件文件；新增 `scripts/gen-restricted-files.py` 生成器，把 12 个受限文件的生成规律固化成代码，一键重建 + 三项自检；**新增归档分发** —— 平台限制包内最多一层子目录，`templates/` 转成 `templates-<框架>.tar.gz` 进包，归档内保留完整目录结构与隐藏文件（平台扫不到也就过滤不掉），`init-*.sh` 经 `scripts/resolve-template.sh` 自动解包；已实测装包后 5 种类型建站 + `npm run build` 全部通过；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples） | 2026-11-17 |
| opensource-housekeeper | ✅ v2.0 稳定（已优化可用性；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / version / author / examples；reference/ 已改名 references/） | 2026-11-17 |
| doc-speedreader（晚枫速读侠） | ✅ v1.0.0 已上架（frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples；reference/ 已改名 references/） | 2026-11-17 |
| repowiki-generator（晚枫知识库） | ✅ v1.0.0 可用（frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples） | 2026-11-17 |
| free-ai-models | ✅ v1 稳定 | 2026-07-12 |
| wanfeng-digital-human（晚枫数字人） | ✅ v2.0 可用（只走软件积分，零成本、4–10 秒，无需密钥；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples） | 2026-11-17 |
| wanfeng-digital-human-pro（晚枫数字人 Pro） | ✅ v2.0 可用（三画面后端 × 两语音后端；原 wanfeng-h3 已并入，云端 H3 端到端待验收） | 2026-11-17 |
| mograph（晚枫自动剪视频） | 🚧 v1.3（通用路径骨架脚本本地跑通；**晚枫专用路径已跑通全链路并交付成片** —— Pillow 自绘 + 手写场景表 + 圆形人头 + 语速映射 + 两遍法响度归一，见 mograph/references/wanfeng-path.md；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples；reference/ 已改名 references/） | 2026-11-17 |
| mograph-pro（晚枫自动剪视频-Pro） | ✅ v1.1 **付费版**（自包含：10 步执行流 + 设计令牌 + 版式库 + 封面固定资产 + 商业授权 LICENSE.md；与免费版 mograph 的晚枫线同源）**新增：封面 logo 本地没有合适的就自己从官方源下载（准确性优先于好看，来源登记进 asset-manifest.json）**；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples；reference/ 已改名 references/（指向免费版 mograph 的 GitHub 路径 7 处已同步为 references/，与 mograph 改名联动，需一同推送 GitHub） | 2026-11-17 |
| ai-style-video（晚枫AI动画） | ✅ v2.3 稳定（一句话生成 AI 视频：8 种内置风格 + I 自定义；6 种画幅 9:16/2:3/4:5/1:1/16:9/4:3，与风格互相独立；三档配音方案 S/V1/V2；全程本地零付费；逐字级字幕对齐、横版自动重排不在范围内；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples） | 2026-11-17 |

---

## 📝 添加新 skill

在仓库根的 `todo/` 目录建一个待办文件夹，放设计笔记 + 需求起点。
然后用 `skill-creator` 创建 skill 目录到 `skills/` 下。

详见：[personal-website-builder/SKILL.md](personal-website-builder/SKILL.md) 内的成熟范式。