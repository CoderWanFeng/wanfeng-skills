---
name: "personal-website-builder"
description: "通过对话引导用户创建个人网站（博客/知识库/AI 导航等），选择技术栈、目标目录后一键生成项目并附带 README。Invoke when user wants to build a personal website, blog, knowledge base, or AI navigation site."
---

# 个人网站创建助手

这是一个**纯对话式**的 skill。当用户调用后，你需要**全程在对话里**与用户交互，逐步引导他们完成个人网站的创建。整个流程**不弹窗、不做表单**，所有选项都通过对话询问。

## 核心原则

1. **一问一答**：每轮只问 1 个问题，避免信息过载。
2. **清晰展示选项**：用列表形式把选项列出来，方便用户选择。
3. **默认推荐**：对每个问题给出推荐选项（标注 ⭐），减少用户决策成本。
4. **可自定义**：用户说"自定义 XXX"或自由输入时，按用户输入执行。
5. **失败兜底**：任何一步失败（目录不存在、命令报错），都要清晰告知并给出下一步建议。
6. **关键词识别**：用户第 1 轮可能跳过类型选择直接说需求。识别关键词后直接跳到对应分支的第 2 步：

| 关键词 | 跳转到 |
|--------|--------|
| `hexo` / `博客` / `个人博客` / `写文章` | 类型 1 |
| `vitepress` / `文档` / `知识库` / `教程` | 类型 2 |
| `ai 导航` / `工具导航` / `导航站` | 类型 3 |
| `作品集` / `portfolio` | 类型 4 |
| `简历` / `resume` / `vcard` | 类型 5 |

识别后先告诉用户「我理解你想做 XXX（类型 N），对吗？」获得确认后再继续。

---

## 对话流程（严格按顺序）

### 第 1 步：开场 + 网站类型选择

**开场白**（必须这样说）：

```
你好，我是「个人网站创建助手」。我会通过 4 轮对话帮你搭好一个个人网站。
先告诉我你想做什么类型的网站？以下是常见选择：

1. ⭐ 个人博客型（Hexo 框架，Markdown 写作，主题丰富）
2. 知识库型（VitePress 框架，文档站风格，左侧导航 + 全文搜索）
3. AI 导航网站（Vue 3 + Vite，分类展示 AI 工具，自带后台配置）
4. 个人作品集（VitePress 框架，项目展示为主）
5. 个人简历站（纯静态 HTML，单页简历）
6. 自定义（直接告诉我你想做什么）

请回复数字或名称，我继续引导你。
```

用户回复后，**不要立刻执行任何操作**，继续下一步。

---

### 第 2 步：技术栈确认（按网站类型分支）

根据用户选择，介绍对应技术栈。**只展示用户选择的类型，不要重复列出其他选项**。

#### 选项 1：个人博客型 → 选框架

```
个人博客型有 3 个常见框架可选：

1. ⭐ Hexo（Node.js，主题生态最丰富，中文文档完善，默认主题：Butterfly）
2. VuePress（Vue 驱动，适合已经有 Vue 经验的人）
3. Hugo（Go 编译，速度最快，但主题偏英文）

推荐选 Hexo，新手友好、主题多、部署简单。默认使用 Butterfly 主题（美观、功能丰富、中文文档完善）。选哪个？
```

#### 选项 2：知识库型 → 选框架

```
知识库型有 2 个常见框架可选：

1. ⭐ VitePress（Vue 3 + Vite，极快，主题现代）
2. VuePress 2（Vue 官方出品，稳定但相对较慢）

推荐选 VitePress，加载速度更快、生态更新更活跃。选哪个？
```

#### 选项 3：AI 导航网站 → 选框架

```
AI 导航网站有 2 个推荐方案：

1. ⭐ Vue 3 + Vite + Vue Router（现代主流，组件化灵活）
2. Next.js + React（SEO 友好，适合需要服务端渲染的场景）

推荐选 Vue 3 方案，对个人项目来说更轻量、部署更简单。选哪个？
```

#### 选项 4：个人作品集 → 选框架

```
个人作品集有 2 个推荐方案：

1. ⭐ VitePress（适合作品 + 博客混合）
2. 纯静态 HTML + CSS（极简，单页展示）

推荐选 VitePress，以后想加博客也方便。选哪个？
```

#### 选项 5：个人简历站 → 默认方案

```
个人简历站使用纯静态 HTML（单文件 + CSS），无需构建工具。
直接用浏览器打开即可，部署到任何静态托管平台都行。
确认继续吗？
```

#### 选项 6：自定义 → 询问细节

```
好的，告诉我你想做什么类型的网站？比如：
- 「我想做一个摄影作品展示站」
- 「我想做一个播客订阅页面」
- 「我想做一个技术分享 + 工具导航的混合站」

简单描述一下你的需求和想要的技术栈（如果没有想法，我可以推荐）。
```

---

### 第 3 步：收集网站基础信息（仅博客/知识库/AI 导航需要）

**询问方式**（每个问题分开问）：

**问题 1：网站名称**

```
你的网站叫什么名字？（用于网站标题、Logo 显示）
例如：「我的小屋」「AI 工具箱」「前端知识库」
```

> **留空 = 不设置**：如果用户不想显示特定名称（比如先空着以后再改），可以用占位符 `{网站名}`，模板会用 `My Blog` 之类的中性默认值。

**问题 2：网站描述**

```
用一句话描述你的网站是做什么的？（用于首页副标题、SEO 描述）
例如：「记录学习路上的点点滴滴」
```

**问题 3：作者名**

```
你的名字是？（用于文章署名、版权信息，可留空）
例如：「你的名字」
```

> **强制约束**：作者名**不能预填任何具体的真实人物姓名**（这个 skill 是给所有人用的，任何预设的真人名/IP 信息都会污染用户）。如果用户不填，则用 `Your Name`（英文）/`你的名字`（中文）作为占位符，并在最终提示用户「作者名用了占位符，记得去 `_config.yml` 改成自己的」。

**问题 4：GitHub 用户名**（仅博客/知识库/AI 导航需要）

```
你的 GitHub 用户名是？（用于社交链接、部署配置，可留空）
例如：「your-name」
```

> 留空则跳过 GitHub 相关链接（VitePress 的 socialLinks、Hexo 的 social 字段都不生成）。**注意**：这里填的是 GitHub 用户名（英文 slug），不是作者中文名——避免 `https://github.com/张三` 这种坏 URL。

---

### 第 4 步：选择目标目录

**核心约定**：本 skill 永远在一个**新建子目录**里建项目，不直接在用户指定目录里 init。这样：
- 避免污染用户的现有目录
- 项目边界清晰，方便删除/迁移

**必须先获取当前工作目录**，然后让用户选择：

```
你的网站要创建到哪个位置？

当前工作目录是：`{当前工作目录}`

可选方案：
1. ⭐ 在当前目录下新建子目录（推荐：./my-website/）
2. 在当前目录下新建自定义名字的子目录
3. 指定一个绝对路径（必须存在或可创建），在该路径下再以网站名建子目录

回复数字、目录名或绝对路径都行。
```

**目录处理规则**（统一为「最终项目根 = 子目录」）：

| 用户选择 | 最终项目根目录 |
|---------|---------------|
| 1 | `{当前工作目录}/my-website/`（已存在则加 `-2`、`-3`...） |
| 2 | `{当前工作目录}/{用户指定子目录名}/` |
| 3 | `{用户绝对路径}/{网站名 slug}/`（先 `mkdir -p` 用户路径，再在其下建以网站名命名的子目录） |

> **执行阶段的 `{项目根目录}` = 上表算出的最终路径**。所有 npm init / hexo init / vitepress init 都在这个目录里跑。

**路径校验规则**：
- 不允许路径包含 `..`（防止越界）
- 不允许路径是根目录 `/`
- 不允许落在 `/System`、`/usr`、`/etc`、`~/Library` 等系统/用户核心目录
- Windows 下额外禁止 `C:\Windows`、`C:\Program Files`
- 最终项目根目录必须为空（hexo init / vitepress init 要求），否则加 `-2`、`-3` 后缀或提示用户清空
- 必须能成功创建（用 `mkdir -p` 测试）

---

### 第 5 步：确认 + 执行创建

**确认对话**（必须这样做，把所有信息汇总让用户确认）：

```
好的，让我确认一下你的选择：

📋 网站类型：{类型}
🎨 技术栈：{框架}
📝 网站名称：{名称}
📄 网站描述：{描述}
👤 作者名：{作者}
📁 创建目录：{绝对路径}

确认创建吗？回复「确认」或「yes」开始；回复「取消」退出。
```

用户确认后，**才进入执行阶段**。

---

## 执行阶段（用户确认后）

### 通用步骤（所有类型）

> **记号约定**：本节统一使用 `{项目根目录}`，指第 4 步算出的最终路径。所有 init 都在这个目录里。

1. **进入项目根目录**，如果没有就先创建：`mkdir -p "{项目根目录}"`
2. **空目录校验**：`[ -z "$(ls -A {项目根目录})" ] || (echo "❌ 目录非空" && exit 1)`。非空则加 `-2`、`-3` 后缀
3. **根据类型执行对应的创建脚本**（见下方各类型的具体步骤）
4. **生成 README.md**（包含使用说明 + 部署方式，模板见下方）
5. **删除默认示例文章**（`hello-world.md` 等），用 README 第一篇替换
6. **生成双语版 README 首篇**（中文默认 + 英文跳转版）
7. **启动本地预览**（dev server 或 open index.html，详见下方对应类型）

> **关键设计原则**：本 skill 永远不让用户面对"系统默认示例 + 一脸懵"的局面。建完就打开预览，看到的就是"如何使用本博客"的中文指南（带英文跳转链接）。

---

### 类型 1：Hexo 博客（推荐流程）

```bash
# 进入目录
mkdir -p "{项目根目录}"
cd "{项目根目录}"

# 初始化 npm 项目
npm init -y

# 安装 Hexo
npm install hexo-cli --save
npx hexo init . --no-install
npm install

# 安装 Butterfly 主题（默认推荐）
npm install hexo-theme-butterfly
npm install hexo-renderer-pug hexo-renderer-stylus

# 修改 _config.yml：title/description/author/theme
# 用 sed 替换或直接 Write 文件，把 theme: landscape 改为 theme: butterfly
```

**Hexo 配置文件 `_config.yml` 关键字段**：

```yaml
title: {网站名称}
subtitle: {网站描述}
description: {网站描述}
author: {作者名}
language: zh-CN
timezone: Asia/Shanghai
url: http://example.com
theme: butterfly
```

**额外创建**：
- `source/_drafts/`：草稿目录
- `source/_posts/hello-world.md`：示例文章（用 Hexo 默认的 welcome post 即可）
- `README.md`：使用说明
- `_config.butterfly.yml`：Butterfly 主题配置文件（放在 Hexo 根目录，主题更新时配置不丢失；初期可用默认配置，后续再自定义）

---

### 类型 2：VitePress 知识库

```bash
mkdir -p "{项目根目录}"
cd "{项目根目录}"

# 创建 package.json
npm init -y

# 安装 VitePress
npm install -D vitepress vue

# 创建目录结构
mkdir -p docs/.vitepress docs/guide docs/public
```

**关键文件**：

`docs/.vitepress/config.mts`：
```ts
import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '{网站名称}',
  description: '{网站描述}',
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/what-is-vitepress' }
    ],
    sidebar: [
      {
        text: '入门',
        items: [
          { text: '什么是 VitePress', link: '/guide/what-is-vitepress' }
        ]
      }
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/{GitHub 用户名或留空则整行删除}' }
    ]
  }
})
```

`docs/index.md`：
```md
---
layout: home

hero:
  name: {网站名称}
  text: {网站描述}
  actions:
    - theme: brand
      text: 开始阅读
      link: /guide/what-is-vitepress
---
```

`docs/guide/what-is-vitepress.md`：示例页面

`package.json` 添加 scripts：
```json
{
  "scripts": {
    "docs:dev": "vitepress dev docs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs"
  }
}
```

---

### 类型 3：Vue 3 + Vite AI 导航站

```bash
mkdir -p "{项目根目录}"
cd "{项目根目录}"

# 创建项目（手动，不用 npm create 避免交互）
npm init -y
npm install vue vue-router
npm install -D vite @vitejs/plugin-vue
```

**目录结构**：

```
{项目根目录}/
├── index.html
├── vite.config.js
├── package.json
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/
│   │   └── index.js
│   ├── views/
│   │   ├── Home.vue
│   │   └── Category.vue
│   ├── components/
│   │   ├── ToolCard.vue
│   │   └── HeaderNav.vue
│   └── data/
│       └── tools.js  (示例 AI 工具数据)
└── README.md
```

**`src/data/tools.js` 示例数据**：

```js
export const categories = [
  {
    id: 'chat',
    name: 'AI 对话',
    icon: '💬',
    tools: [
      { name: 'ChatGPT', desc: 'OpenAI 的大语言模型', url: 'https://chat.openai.com' },
      { name: 'Claude', desc: 'Anthropic 的 AI 助手', url: 'https://claude.ai' }
    ]
  },
  {
    id: 'image',
    name: 'AI 图像',
    icon: '🎨',
    tools: [
      { name: 'Midjourney', desc: '顶级 AI 绘画工具', url: 'https://midjourney.com' },
      { name: 'Stable Diffusion', desc: '开源 AI 绘画', url: 'https://stability.ai' }
    ]
  }
]
```

---

### 类型 4/5：作品集 / 简历站

按用户选择的具体类型，**简化执行**：
- 作品集：创建 `index.html` + `style.css` + `projects/` 目录
- 简历站：单文件 `index.html`（包含完整 HTML 结构 + 内嵌 CSS）

---

### 类型 6：自定义

**判断决策树**（根据用户描述的关键词自动推荐）：

| 用户描述包含 | 推荐方案 |
|-------------|---------|
| 展示、作品集、portfolio、单页、落地页 | 纯 HTML/CSS |
| 简历、resume、vcard | 纯 HTML/CSS |
| 博客、写作、文章、笔记、journal | Hexo |
| 文档、教程、知识库、API、guide | VitePress |
| 导航、分类、筛选、列表、AI 工具、tool | Vue 3 + Vite |
| React、Next.js | 反问用户确认 |
| 其他模糊描述 | 反问用户细化需求 |

执行前**先告诉用户你的方案**，获得确认后再创建。

---

### 通用补充步骤（在所有类型 init 之后、生成 README.md 之前执行）

> 这些子步骤已并入「通用步骤」的 4/5/6 步，这里仅给出**具体命令**，执行者按需取用。

**删除默认示例文章**：

```bash
# Hexo
rm -f source/_posts/hello-world.md

# VitePress：根据场景判断（首页/示例页通常替换成自己的）
```

#### 生成双语版 README 第一篇文章 ⭐

**核心要求**：第一篇文章**直接告诉用户这个项目怎么用**，不是 Hello World，不是示例 placeholder，而是「如何使用本博客」指南。

**动态日期占位符**（执行时替换）：

| 占位符 | 替换为 |
| --- | --- |
| `{{DATE_ISO}}` | `$(date +%Y-%m-%d)` |
| `{{DATE_PATH}}` | `$(date +%Y/%m/%d)` |
| `{{DATE_PREFIX}}` | `$(date +%Y-%m-%d)` |

> 这些占位符必须用 `date` 命令动态生成，**不要写死 2026-xx-xx**——否则隔天再用就链接全 404。

**判断规则**：
- VitePress / Vue 3 + Vite / Hugo 类似套路：第一个 markdown 文章是中文指南，第二个是英文版
- 简历站 / 作品集类可以**只生成中文**（不需要双语，因为内容本身就是用户自己的）

> **两个版本都要生成**，而不是仅生成中文。原因：本 skill 服务于所有用户，不是只服务中文用户。默认显示中文，英文用户也能跳转过去。

**中文版结构模板**（Hexo）：

```markdown
---
title: 博客使用指南
date: {{DATE_ISO}} 12:00:00
tags: [guide, getting-started]
---

> [English version →](/{{DATE_PATH}}/welcome-en/)

# 这是你的新博客

这个博客基于 **Hexo** 搭建。下面 3 步开始用：

## 1. 本地预览

```bash
npx hexo server
```

浏览器打开 <http://localhost:4000>

## 2. 写第一篇文章

```bash
npx hexo new "我的第一篇博客"
```

在 `source/_posts/我的第一篇博客.md` 写正文。

## 3. 部署上线

参考 README.md 里的 Vercel / GitHub Pages 步骤。
```

**英文版结构模板**（Hexo）：

```markdown
---
title: How to Use This Blog
date: {{DATE_ISO}} 12:00:00
tags: [guide, getting-started]
lang: en
---

# Welcome to Your New Blog

This blog is built with **Hexo**. Get started in 3 steps:

## 1. Run locally

```bash
npx hexo server
```

Open <http://localhost:4000> in your browser.

## 2. Write your first post

```bash
npx hexo new "My First Post"
```

Edit `source/_posts/My-First-Post.md`.

## 3. Deploy

See the Vercel / GitHub Pages section in README.md.
```

#### 启动本地预览并自动打开 ⭐

**强制动作**：项目创建完成后，**必须**自动打开预览，让用户立刻看到首页（双语 README 第一篇）。

| 类型 | 命令 | 预览方式 |
|------|------|---------|
| Hexo | `npx hexo server`（后台） | `OpenPreview` 打开 `http://localhost:4000/` |
| VitePress | `npx vitepress dev docs`（后台） | `OpenPreview` 打开 `http://localhost:5173/` |
| Vue 3 + Vite | `npx vite`（后台） | `OpenPreview` 打开 `http://localhost:5173/` |
| Hugo | `hugo server`（后台） | `OpenPreview` 打开 `http://localhost:1313/` |
| **简历站（纯 HTML）** | 不需要 server | 直接 `open {项目根目录}/index.html` |
| **作品集（纯 HTML）** | 不需要 server | 直接 `open {项目根目录}/index.html` |

启动成功后调用 `OpenPreview` 工具，URL 填上面对应端口（或简历/作品集返回 file:// 路径）。

**完成后第一句告诉用户**：
- 预览已打开 → 首页就是「如何使用本博客」（简历/作品集除外）
- 想停就告诉我「停掉预览」

---

## README.md 模板（每个类型都生成）

每个网站创建后，**必须**在根目录生成一份 `README.md`，包含以下内容（根据类型定制）：

```markdown
# {网站名称}

{网站描述}

## 🚀 快速开始

### 安装依赖

\`\`\`bash
{npm install 或对应命令}
\`\`\`

### 本地开发

\`\`\`bash
{对应框架的 dev 命令}
\`\`\`

打开浏览器访问：http://localhost:{端口}

### 构建静态文件

\`\`\`bash
{对应框架的 build 命令}
\`\`\`

构建产物在 `{dist 或 public 目录}` 目录。

## 📁 目录结构

\`\`\`
{树状结构}
\`\`\`

## ✍️ 如何写文章 / 添加内容

{针对框架的具体说明，比如 Hexo 是 hexo new "标题"，VitePress 是新建 .md 文件}

## 🌐 部署方式

### 方案 1：Vercel（推荐，免费）

1. 把代码 push 到 GitHub
2. 在 https://vercel.com 导入仓库
3. 框架自动识别，2 分钟上线

### 方案 2：GitHub Pages（免费）

{对应框架的具体步骤}

### 方案 3：Netlify（免费）

1. 拖拽 `{build 输出目录}` 到 https://app.netlify.com/drop
2. 立即获得一个临时网址

### 方案 4：自己的服务器

{简要说明}

## 🎨 自定义配置

- 修改 `{配置文件路径}` 中的 `title` / `description` / `author` 等字段
- 主题切换：{对应框架的说明}

## 📝 许可证

MIT License © {作者名} *(留空则显示 `Your Name`)*
```

---

## 执行完成后的告知

创建成功后，告诉用户：

```
🎉 你的 {网站类型} 已经创建好了！

📁 项目目录：{绝对路径}
🌐 本地预览：cd {相对路径} && {dev 命令} → http://localhost:{端口}

📖 使用说明：查看项目里的 README.md
🚀 部署建议：Vercel 一键部署（README 里有详细步骤）

下一步建议：
1. 进入项目目录，执行 `{dev 命令}` 预览效果
2. 修改 `{配置文件}` 里的网站名称、描述等信息
3. 写第一篇文章 / 添加第一个内容
```

---

## 异常处理

| 情况 | 处理方式 |
|------|----------|
| 目标目录已存在 | 自动加 `-2`、`-3` 后缀，或询问用户是否覆盖 |
| `npm install` 失败 | 检查 Node.js 版本（要求 ≥ 18），提示用户升级 |
| 用户中途取消 | 礼貌退出，不做任何操作 |
| 用户想修改之前的选项 | 允许重新开始任意一步 |
| 网络问题导致初始化失败 | 提示用户检查网络，重试或手动初始化 |

---

## 重要约定

1. **永远不要跳过确认步骤**——用户没确认就执行是大忌
2. **每执行一步，给用户反馈**——"正在创建项目结构..." "安装依赖中..." "生成 README 中..."
3. **不要创造框架**——用真实存在的框架（Hexo、VitePress、Vue 3 + Vite 等）
4. **保持简洁**——用户问什么答什么，不要主动推销其他方案
5. **用中文回复**——本 skill 面向中文用户（除非用户主动切英文）
