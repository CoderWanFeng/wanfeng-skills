# wanfeng-skills / skills 目录

> 这是一个**可复用的 AI Skill 集合**。每个子目录都是一个独立的 skill，对应一个具体的工作流。
> Skill 之间**正交**：可单独使用，也可按场景串起来。

---

## 📚 开源 Skill 一览（17 个）

| Skill | 用途 | 适用场景 | 触发词举例 | 在线体验 |
|---|---|---|---|---|
| [**aihot-topic-selector**](aihot-topic-selector/) | 从 AIHOT 热点数据里每天自动选题 | 自媒体日常选题、内容运营 | 「今天 AI 有什么热点」「按热点选个题」 | — |
| [**hot-topic-radar**](hot-topic-radar/) | 7×24h 监控全网热搜，按关键词过滤 + 热度打分 | 自媒体选题雷达、跨平台聚合 | 「监控 XX 话题」「全网热搜」「今天值得跟什么」 | — |
| [**cover-hero**](cover-hero/) | 给公众号文章做封面 + 正文配图（HyperFrames 风格） | 公众号配图、长文视觉 | 「做公众号封面」「配张图」「头图」 | [👉 封面侠](https://qclaw.qq.com/as/BQ2Cw50sNfcy) |
| [**wanfeng-writing-partner**](wanfeng-writing-partner/) | 晚枫写作搭子：把 AI 热点 / 产品体验 / 官方资料变成一篇可直接发布的中文长文，7 步走完全流程（选题→起标题→搭结构→配图→传图床→插引用→发布前检查），含暖白插图脚本、截图脱敏方法与文章自检脚本 | 公众号 / 知乎长文写作、教程评测、配图与图床 | 「写篇文章」「帮我写教程」「这个产品写个评测」「起个标题」「配图怎么做」「上传图床」 | — |
| [**mp-saver**](mp-saver/) | 不登录保存公众号文章为单文件 MHTML（HTML + base64 内嵌图片，离线可看）。v2.0 起零依赖（只用 Python 标准库 urllib） | 公众号文章收藏、批量存档、喂 LLM | 「保存公众号文章」「下载公众号文章」「不登录存公众号」 | — |
| [**doc-speedreader**](doc-speedreader/) | 把 PDF、Word、PPT、Excel、图片、音频等文档转成 Markdown，并生成摘要或完整副本 | 文档速读、资料整理、喂 LLM | 「速读这份 PDF」「转成 Markdown」「给我摘要」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-doc-speedreader) |
| [**knowledge-short-video**](knowledge-short-video/) | 知识类短视频全流程（口播稿 → 视觉 → 动画 → TTS → 渲染） | 短视频制作、知识科普 | 「做条知识视频」「短视频口播稿」 | — |
| [**personal-website-builder**](personal-website-builder/) | 对话式引导创建个人网站（博客/知识库/作品集/简历） | 个人建站、博客搭建 | 「我想做个博客」「搭个个人网站」「建个简历站」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-personal-website-builder) |
| [**opensource-housekeeper**](opensource-housekeeper/) | 晚枫开源管家：给零基础小白做开源项目陪跑——找到项目 → 讲清它是干嘛的 → 拉下来跑起来 → 读懂它 → 改一处、用出效果；也能反向发布项目、生成项目文档 | 开源小白、学用开源项目、跨平台发布 | 「我想学 XX 怎么用」「这项目干嘛」「帮我推到 GitHub」「拉一下 llama.cpp 跑起来」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-opensource-housekeeper) |
| [**repowiki-generator**](repowiki-generator/) | 为任意项目生成结构化 Wiki，帮助用户和 Agent 快速理解项目 | 项目文档、知识库、代码导览 | 「给这个项目生成 Wiki」「帮我整理项目文档」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-repowiki-generator) |
| [**free-ai-models**](free-ai-models/) | 搜罗全网可以免费使用的大模型（直接用 / 软件内置 / 平台免费额度） | 找免费 GPT/Claude/Gemini、找软件里能白嫖的模型、找永久免费 API | 「免费大模型」「GPT 免费吗」「Cursor 里哪个免费」「API 免费额度」 | — |
| [**workbuddy-daily-credits**](workbuddy-daily-credits/) | WorkBuddy 成长中心每日积分领取、猫猫旅行和盲盒操作 | WorkBuddy 日常任务、积分管理 | 「领取每日积分」「帮我签到」「开盲盒」 | — |
| [**wanfeng-digital-human**](wanfeng-digital-human/) | 把一段视频或一张照片变成 4–10 秒会说话的数字人短片。**零成本**：只扣软件积分，不填密钥、不绑支付；台词由模型用内置音色念出，可事后替换成自己的原声 | 数字人口播、不露脸出镜、照片说话、先花零成本试效果 | 「做个数字人视频」「让我的照片说话」「AI 替我说话」「做一条十秒口播」「用积分做数字人」 | — |
| [**wanfeng-digital-human-pro**](wanfeng-digital-human-pro/) | **开源、不单独售卖的数字人开工前工作台**：长稿切段、参考素材体检、每段提示词排版。平台无关，主流程零 API 调用；产出 `segments.json`、分段提示词、素材清单和施工说明，不直接生成视频或音频。第三方平台生成费用另计 | 30 秒以上长口播开工前、跨平台批量做系列、生成前把素材和脚本列清楚 | 「帮我把稿子切成 <平台> 能用的分段」「数字人开工前需要准备哪些素材」「按 MiniMax 规范给我 prompt」 | — |
| [**mograph**](mograph/) | 晚枫自动剪视频开源基础版：通用路径按内容生成口播包装；现有晚枫专用路径和封面示例继续作为基础体验保留。需要完整维护版、配套资产、持续更新与交付支持时，选择文末的旗舰开源版 mograph-pro | 口播视频包装、出镜科普、lower-third 数据卡、体验晚枫固定调性 | 「自动剪辑」「口播加动画」「给视频贴片」「上下左右弹卡」「加数据卡」「晚枫专用」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-mograph) |
| [**mograph-vlog**](mograph-vlog/) | 晚枫自动剪vlog：**素材先行的日常碎片 vlog 线**。只给一个装随手拍视频 / 照片的目录，AI 真看镜头（扫描时长 / 旋转 / 音轨 + 抽帧接触表）→ 选叙事形式 → 写第一人称旁白 → 排转场与丰富动效 → 先出几秒样片再出成片。**不要求口播视频、稿子、字幕、数字人或固定封面**；旁白不逐条念画面花字；可用本人既有克隆音色（加速只做一次并按实测时长回填）；画幅按发布平台单独排（视频号 9:16） | 出差 / 旅行 / 活动记录、日常随手拍、照片视频混剪、只想发视频号竖版 | 「把这些随手拍剪成vlog」「没有稿子只有视频和照片」「你先选形式，动画丰富一点」「先出5秒看转场」「用我的克隆声音配音」「只要竖版」 | — |
| [**ai-style-video**](ai-style-video/) | **一句话生成 AI 视频**：任意素材（描述/文档/截图/数据）→ MG 短视频（24–25s / 9 场景）。**开场四问**：选风格（A–H + I 自定义）→ 选画幅（9:16 / 2:3 / 4:5 / 1:1 / 16:9 / 4:3，与风格互相独立）→ 选配音（S 静音 / V1 系统电子音 / V2 本地模型克隆音色）→ 交素材。自带文字重叠检测、缺素材占位、跨平台字体解析、画幅适配层、ffmpeg 混流 | 不出镜的 MG 短视频、产品/功能/事件/教程解读、要横版（B站/YouTube）也要竖版（抖音/小红书）、想克隆自己音色配音 | 「做条不出镜的 MG 视频」「选个风格重做这条」「这条改横屏」「用我的声音念这段」「素材要哪些」「证据图发虚」 | [👉 SkillHub](https://skillhub.cn/skills/user_bf8c5b73/wanfeng-ai-style-video) |
| [**wanfeng-ai-model**](wanfeng-ai-model/) | 晚枫模特换装：模特图 + 服装图 → 分步确认参数，自动换装、生成卡点音乐、合成 9:16 短片并逐帧质检 | AI 试衣、模特走秀、一套模特 × N 套服装批量生产 | 「晚枫模特换装」「AI 模特」「试衣视频」「换装视频」「服装上身」「模特走秀」 | — |

---

## 旗舰完整版（已开源）

**mograph-pro**：真人口播 / 文稿生成数字人混剪的完整维护版，提供成片、封面、配套资产、持续更新和交付支持。源码、文档、引擎与配套资产全部开源（MIT-0），可直接从 [`mograph-pro/`](mograph-pro/) 安装或自行打包。

免费 `mograph` 的现有通用路径、晚枫专用路径与封面示例保持不变；Pro 转为 MIT-0 开源不追溯改变这些公开内容原有的授权。

---

## 🗂️ 按场景分类

### 🔍 内容创作 / 自媒体

```
每日选题 → 写长文 → 配图 → 发布
  ↓         ↓        ↓      ↓
hot-topic-radar /  wanfeng-writing-  cover-hero  公众号
aihot-topic-selector  partner
```

```
要保存别人写的公众号文章（不登录）？
  ↓
mp-saver
```

- **[aihot-topic-selector](aihot-topic-selector/)** — AI 领域专属：每天从 AIHOT 拉热点，按 2 问选 1 条，建 task 目录
- **[hot-topic-radar](hot-topic-radar/)** — 全网通用：自定义关键词 + 多平台 + 记忆去重，适合任何垂直领域
- **[cover-hero](cover-hero/)** — 配图：6 套模板 + 严格视觉 DNA + Puppeteer 渲染
- **[wanfeng-writing-partner](wanfeng-writing-partner/)** — 长文写作搭子：从选题到成稿 7 步全流程，含暖白插图、截图脱敏、图床上传与格式自检（不携带任何人的图床信息）
- **[mp-saver](mp-saver/)** — 公众号文章保存器：v2.0 纯 HTTP 版 → MHTML 单文件，不登录、双击可看；v2.0 起只需 Python 标准库
- **[knowledge-short-video](knowledge-short-video/)** — 短视频：覆盖 20+ 步骤，从口播稿到渲染产物
- **[wanfeng-digital-human](wanfeng-digital-human/)** — 数字人（零成本）：一段素材 + 一句话，出 4–10 秒会说话的短片，只扣软件积分，模型念台词、可换原声
- **[wanfeng-digital-human-pro](wanfeng-digital-human-pro/)** — 开源数字人 Pro：开工前的本地工作台，把长稿切段 + 素材体检 + 每段提示词，产出平台施工图；不单独售卖，第三方生成费用另计
- **[mograph](mograph/)** — 晚枫自动剪视频开源基础版：真人已出镜的视频 + 口播稿 → 按讲话内容在四周弹卡，保留现有晚枫路径与封面示例
- **[mograph-vlog](mograph-vlog/)** — 晚枫自动剪vlog：随手拍的视频 / 照片目录 → AI 看素材选形式、写第一人称旁白、排转场与动效，先出几秒样片；不需要口播或稿子
- **[ai-style-video](ai-style-video/)** — 晚枫AI动画，不出镜的风格 MG 片：任何选题 → 选风格（8 种 + 自定义）→ 选画幅（6 种，竖屏到横屏都行）→ 选配音 → 按清单交素材 → 样片
- **[wanfeng-ai-model](wanfeng-ai-model/)** — 晚枫模特换装：分步确认素材与出片参数，自动完成换装、卡点音乐、短片合成和逐帧质检；生成前确认积分

### 🌐 个人项目 / 建站

- **[personal-website-builder](personal-website-builder/)** — 对话式建站：5 种类型（博客/知识库/AI 导航/作品集/简历）

### 🚀 开源协作

- **[opensource-housekeeper](opensource-housekeeper/)** — 晚枫开源管家：主打「学用开源项目」（找到 → 讲清 → 跑通 → 读懂 → 改一处用出效果）；**v2.1.0 起每次打开先问「今天想找哪方面的 AI 项目？」，选完方向自动跑遍国内外所有主流开源平台找项目**，也能反向发布项目、生成项目文档

---

## 🎯 如何选用 skill？

| 你想做的事 | 用这个 skill |
|---|---|
| 我要做自媒体，从哪开始找选题？ | [hot-topic-radar](hot-topic-radar/) |
| AI 领域怎么选今天的话题？ | [aihot-topic-selector](aihot-topic-selector/) |
| 文章写完了，给它配个封面 | [cover-hero](cover-hero/) |
| 我有个 AI 热点 / 产品，想写成一篇公众号长文 | [wanfeng-writing-partner](wanfeng-writing-partner/) |
| 长文要配图 / 截图脱敏 / 传图床 / 发布前查格式 | [wanfeng-writing-partner](wanfeng-writing-partner/) |
| 我想做短视频，怎么起步？ | [knowledge-short-video](knowledge-short-video/) |
| 我想零成本试一条会说话的数字人短片 | [wanfeng-digital-human](wanfeng-digital-human/) |
| 30 秒以上的口播长稿开工前，先把分段、素材、提示词准备好 | [wanfeng-digital-human-pro](wanfeng-digital-human-pro/) |
| 我想搭个博客 / 个人站 | [personal-website-builder](personal-website-builder/) |
| 我想把代码推到 GitHub | [opensource-housekeeper](opensource-housekeeper/) |
| 我想学一个开源项目、把它真正用起来 | [opensource-housekeeper](opensource-housekeeper/) |
| 今天想找点 AI 项目看看（不知道具体名字） | [opensource-housekeeper](opensource-housekeeper/) |
| 我想把公众号文章存本地（不登录） | [mp-saver](mp-saver/) |
| 哪个大模型能白嫖？Cursor 里哪个能白嫖？哪个 API 有免费额度？ | [free-ai-models](free-ai-models/) |
| 视频已经拍好了，只想在讲话时旁边弹出数据卡 / 图表 | [mograph](mograph/) |
| 要一条自己账号固定调性的成片，还要封面换皮 | [mograph-pro（旗舰开源版）](mograph-pro/) |
| 只有一堆随手拍的视频和照片，没录口播也没写稿，想剪成 vlog | [mograph-vlog（晚枫自动剪vlog）](mograph-vlog/) |
| 手上有一推资料（官网/公告/数据），想快速出条短视频（竖屏横屏都行），人不出镜 | [ai-style-video](ai-style-video/) |
| 我想让 AI 模特穿上我的服装走秀，并批量做多套 | [wanfeng-ai-model](wanfeng-ai-model/) |

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
| opensource-housekeeper | ✅ v2.1.0（**新增：每次打开必问「今天想找哪方面的 AI 项目？」+ 选完方向自动跑遍国内外所有主流开源平台找项目** —— Step 00 开场提问 / 主线 1A / Step A0 全平台检索 / 新增 `references/platform-coverage.md` 全平台清单含实测可达性；发布仍主推三家，「找」与「发」分离；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / version / author / examples） | 2026-11-25 |
| doc-speedreader（晚枫速读侠） | ✅ v1.0.0 已上架（frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples；reference/ 已改名 references/） | 2026-11-17 |
| repowiki-generator（晚枫知识库） | ✅ v1.0.0 可用（frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples） | 2026-11-17 |
| free-ai-models | ✅ v1 稳定 | 2026-07-12 |
| wanfeng-digital-human（晚枫数字人） | ✅ v2.0 可用（只走软件积分，零成本、4–10 秒，无需密钥；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples） | 2026-11-17 |
| wanfeng-digital-human-pro（晚枫数字人-Pro） | ✅ v3.0.0 定位收窄（主版本 breaking）：从「三后端×两语音的完整生产线」改为**平台无关的数字人施工图生成器**——只做切段、素材体检、每段提示词排版三件事，零 API 调用，不再交付 mp4 / mp3 / srt / `talking.mp4`。v2 遗留代码（`engine/`、`init_workspace.py`、`preflight.py`、`env.example`）**保留不删**，见 `references/legacy-integration.md`；references/ 重写为 `platform-notes / material-prep / delivery-spec / legacy-integration` 4 份新档 + 精简 `troubleshooting.md`，删除 `setup / engines / cost-and-delivery` 3 份旧档；frontmatter 已按 WorkBuddy 上架标准补齐 | 2026-11-19 |
| mograph（晚枫自动剪视频） | ✅ v1.3.3 **纯体验版（免费）**：新增**第一步「素材来源与口播稿」**（原 Step 0 的 7 开关顺延为 Step 0.1）——运行时第一件事只问素材来源，A. 我有口播视频 / B. 我没有或不懂什么是口播视频；选 B 或用户没稿时**直接调用内置默认口播稿** `templates/default-script.md`（8 句约 40 秒：「大家好我是程序员晚枫」+ 自我介绍 + 说明这是普通版效果 + 引导去 WorkBuddy 搜「晚枫自动剪视频-Pro」），**不重新生成、不改写、不联网找稿**；该稿同时是演示稿（留「8 张卡 / 26% / 对比 / 首先其次最后 / Python」），实测 `make_spec.py` 自动命中 5–7 张卡，覆盖率不足 40% 时按 Step 3 补卡。前置条件与 frontmatter 三描述同步补默认稿说明；诚实边界写死：体验版不生成视频，无源媒体时先出分镜与动效效果（Step 1–4 离线可跑）再请用户给视频/音频。上游沿用 v1.3.2 的「3 条真片对照」开场与 Python zipfile 打包器 | 2026-11-25 |
| mograph-pro（晚枫自动剪视频-Pro） | ✅ **开源版（MIT-0）**：在 v1.2.x 真人/数字人双分支成片线之上，新增三项核心能力 —— **W24「说什么出什么」通用语义→效果引擎**（任意文稿逐句配真动的效果，参数从句子抽、不写死，见 `semantic-to-effect.md`）、**W25「宽屏可选」**（成片前一次选定仅竖版/横竖双版/仅宽屏，横版左右分栏独立重排，见 `aspect-ratio.md`）、**动画优先两阶段支线**（纯动画 Demo 确认后才叠真人层，见 `animation-first.md`）；W22 圆头规则加强为多帧包络实测；新增 **Step I 小绿书贴图**（发布包整理时问一次，3:4 竖版贴图套装，见 `xiaolvshu.md`）。W1–W25 共 25 条硬规则、22 条踩坑。数字人真实人脸/口型/云端效果待实跑验收；Step I 已落地未实跑验收。**v1.5.0**：日常碎片 vlog 分支移出，独立为同级技能 `mograph-vlog`，本 Pro 回到真人口播 / 数字人两条路径（见其 `CHANGELOG.md`） | 2026-11-27 |
| mograph-vlog（晚枫自动剪vlog） | ✅ v1.0.0 可用（从 mograph-pro 的 daily-vlog 分支独立：`references/vlog-workflow.md` + `vlog_scan.py` / `vlog_render.py`，**39 条测试全绿**——含修掉的 xfade 恒定帧率缺陷，此前该渲染器端到端跑不通）；已写入本会话实测口径：旁白不逐条念花字、贴纸与旁白语义相关、同一句话不重复烧底部字幕、克隆配音只加速一次并按实测时长回填、画幅按平台单独排（视频号 9:16 1080×1920）。真机手机碎片的批量出片仍需抽帧试听；未打包上架 | 2026-11-27 |
| ai-style-video（晚枫AI动画） | ✅ v2.3 稳定（一句话生成 AI 视频：8 种内置风格 + I 自定义；6 种画幅 9:16/2:3/4:5/1:1/16:9/4:3，与风格互相独立；三档配音方案 S/V1/V2；全程本地零付费；逐字级字幕对齐、横版自动重排不在范围内；frontmatter 已按 WorkBuddy 开放平台标准补齐：display_name / display_name_en / description_zh / description_en / author / examples） | 2026-11-17 |
| wanfeng-writing-partner（晚枫写作搭子） | ✅ v1.1.0 可用（首次提问前离线生成 12 类、24 条中英文使用示例，只补缺不覆盖；平台入口示例各 3 条；保留公众号长文 7 步、暖白插图、截图脱敏、图床上传与文章自检；不携带私人配置） | 2026-11-19 |
| wanfeng-ai-model（晚枫模特换装） | ✅ v1.1.0 可用（全自动 A1–A5：素材归位 / 代生成 → 自动换装 → 卡点音乐 → 合成短片 → 质检发布；开源） | 2026-11-23 |

---

## 📝 添加新 skill

在仓库根的 `todo/` 目录建一个待办文件夹，放设计笔记 + 需求起点。
然后用 `skill-creator` 创建 skill 目录到 `skills/` 下。

详见：[personal-website-builder/SKILL.md](personal-website-builder/SKILL.md) 内的成熟范式。
