# 文件完整性自检与还原指南

> **适用场景**：本 skill 通过 ZIP 包安装到第三方平台（WorkBuddy / SkillHub / 插件市场）后，
> 平台的文件白名单可能丢弃三类文件 ——
> **以 `.` 开头的隐藏文件**（如 `.gitignore`）、
> **带 `.template` 后缀的文件**（如 `package.json.template`）、
> **带 `.vue` 后缀的组件文件**（如 `App.vue`）。
>
> 本文档回答三件事：
> 1. 下载后怎么检查文件是否完整（**第 1 节**）
> 2. 这三类文件遵循什么生成规律、内容规律（**第 2 节**，含 12 个文件的完整原文）
> 3. 怎么让 AI 在跑正式流程**之前**把它们还原回来（**第 3 节**）

---

## 0. 背景：为什么偏偏是这三类文件

| 文件类型 | 本 skill 里的实例 | 为什么会丢 | 丢失后果 |
|---|---|---|---|
| 点号开头的隐藏文件 | `templates/*/.gitignore`（5 个） | 打包器 / 上传接口常按「隐藏文件」过滤；手动拖拽上传时也容易被忽略 | 🔴 **阻断级**：4 个 init 脚本 `cp` 失败后被 `set -e` 中止 |
| `.template` 后缀文件 | `templates/*/package.json.template`（2 个） | 平台白名单通常只放行 `.md / .sh / .js / .json / .html` 等后缀，`.template` 不在其中 | 🟡 **非阻断**：项目仍能生成，只是失去依赖清单的离线权威副本 |
| `.vue` 后缀组件文件 | `templates/vue3-vite/src/**/*.vue`（5 个） | 平台白名单里没有前端框架的组件后缀 | 🔴 **阻断级 + 类型级**：AI 导航站（Vue 3 + Vite）**整类不可用**；源码主体结构有强规律，可用 `scripts/gen-restricted-files.py` 重建 |

> **一句话结论**：`.gitignore` 与 `.vue` 必须在跑正式流程前还原，`.template` 建议还原。

### 0.1 根因与当前的对策

平台限制是**路径层级**：「压缩包内最多一层子目录」（`根目录/一级目录/文件`）。
而框架模板天生带嵌套目录（`templates/vue3-vite/src/components/*.vue`、
`templates/hexo/source/_posts/*.md`、`templates/vitepress/docs/.vitepress/config.mts`），
直接放进包里必然超限。

当前的对策是**归档分发**：

```
打包时：  templates/  →  templates-<框架>.tar.gz  （包根一级，路径合规）
装包后：  init-*.sh 自动解包到临时目录再复制，目录结构原样还原
```

归档带来三重收益：

1. **层级合规** —— 包内所有路径都 ≤ 3 段，平台不会报「目录层级超限」；
2. **隐藏文件安全** —— `.gitignore` / `.vitepress/` 待在 tar 内部，平台扫不到也就过滤不掉；
3. **框架约定不破坏** —— `src/components/`、`source/_posts/`、`docs/.vitepress/` 原样保留。

所以本 skill 在平台上的**正常形态就是归档形态**，不是「文件丢了」。
第 1 节的 `find` 自检只适用于目录形态（开发态 / GitHub 安装）。


---

## 1. 第 1 步：下载后检查完整性

### 1.1 一键自检命令

> **首选**：直接跑随包附带的生成器自检（一条命令，覆盖全部 12 个文件 + 三项交叉校验）：
>
> ```bash
> python3 scripts/gen-restricted-files.py --check
> ```
>
> 退出码 `0` = 12/12 齐全；`1` = 有缺失或漂移（脚本会列出具体文件）。
> 它同时校验 `.vue` 引用的 CSS 变量、`.gitignore` 的产物目录、`package.json.template` 的依赖版本，
> 比单纯数文件更可靠。**下面的 `find` 命令是等价的纯手工兜底**（生成器脚本本身若也被平台过滤，
> 用 `find` 判断，再按第 2.4 节原文手工还原）。

```bash
cd <skill 根目录>   # 即包含 SKILL.md 的那一层目录

# A. 受平台限制的高危文件（期望恰好 12 个）
find . -type f -name ".gitignore" | sort
find . -type f -name "*.template" | sort
find . -type f -name "*.vue" | sort

# B. 合并计数（期望输出 12）
find . -type f \( -name ".gitignore" -o -name "*.template" -o -name "*.vue" \) | wc -l
```

> ⚠️ **只有目录形态才适用上面的 `find` 命令**。归档形态（第三方平台安装）下
> `templates/` 目录并不存在，12 个文件都在 `templates-<框架>.tar.gz` 内部 ——
> 此时 `find` 会输出 0，**但文件并没有丢**。判断当前形态：
>
> ```bash
> ls -d templates 2>/dev/null && echo "目录形态" || ls templates-*.tar.gz
> ```
>
> 归档形态下用 `python3 scripts/gen-restricted-files.py --check` 判定，
> 它会直接读归档内部并报「12/12 齐全 · 归档形态」。

**期望输出（齐全时）**：

```
./templates/hexo/.gitignore
./templates/portfolio/.gitignore
./templates/resume/.gitignore
./templates/vitepress/.gitignore
./templates/vitepress/package.json.template
./templates/vue3-vite/.gitignore
./templates/vue3-vite/package.json.template
./templates/vue3-vite/src/App.vue
./templates/vue3-vite/src/components/HeaderNav.vue
./templates/vue3-vite/src/components/ToolCard.vue
./templates/vue3-vite/src/views/Category.vue
./templates/vue3-vite/src/views/Home.vue
```

### 1.2 逐项核对表

12 个文件的**权威形态**（字节数含 UTF-8 多字节字符，末尾一律不带换行符）：

| # | 相对路径 | 字节数 | 行数 | 末行内容 | 缺失影响 |
|---|---|---|---|---|---|
| 1 | `templates/hexo/.gitignore` | 174 | 23 | `.cache/` | ⚠️ 静默：hexo 项目不带忽略规则 |
| 2 | `templates/vitepress/.gitignore` | 129 | 13 | `.env.local` | 🔴 阻断：init 第 6 步中止 |
| 3 | `templates/vue3-vite/.gitignore` | 182 | 20 | `pnpm-debug.log*` | 🔴 阻断：init 第 6 步中止 |
| 4 | `templates/portfolio/.gitignore` | 57 | 5 | `.idea/` | 🔴 阻断：init 第 2 步中止 |
| 5 | `templates/resume/.gitignore` | 43 | 4 | `.idea/` | 🔴 阻断：init 第 1 步中止 |
| 6 | `templates/vitepress/package.json.template` | 356 | 16 | `}` | 🟡 非阻断：失去依赖清单副本 |
| 7 | `templates/vue3-vite/package.json.template` | 390 | 20 | `}` | 🟡 非阻断：失去依赖清单副本 |
| 8 | `templates/vue3-vite/src/App.vue` | 732 | 44 | `</style>` | 🔴 阻断：init 第 2 步中止，AI 导航站类型不可用 |
| 9 | `templates/vue3-vite/src/components/HeaderNav.vue` | 1691 | 93 | `</style>` | 🔴 阻断：同上 |
| 10 | `templates/vue3-vite/src/components/ToolCard.vue` | 1099 | 57 | `</style>` | 🔴 阻断：同上 |
| 11 | `templates/vue3-vite/src/views/Home.vue` | 1414 | 70 | `</style>` | 🔴 阻断：同上 |
| 12 | `templates/vue3-vite/src/views/Category.vue` | 1627 | 78 | `</style>` | 🔴 阻断：同上 |

> 字节数只用于快速判断「内容是否完整到同一版本」，**允许 ±2 字节误差**
> （末行是否补换行符会差 1 字节，不同编辑器的行尾风格也可能带来差异）。

### 1.3 辅助核对（不受平台限制影响的部分）

```bash
ls scripts/*.sh | wc -l                      # 期望 22（21 个脚本 + deploy.sh）
find references -type f -name "*.md" | wc -l  # 期望 12（含本文件）
ls templates | tr '\n' ' '                   # 期望 hexo portfolio resume vitepress vue3-vite
```

### 1.4 判定与后续动作

| 自检结果 | 判定 | 动作 |
|---|---|---|
| 12/12 齐全 | ✅ 完整 | 直接进入**第 3 节**流程（跳过还原） |
| 缺 `.gitignore`（任一份） | 🔴 阻断级 | **必须**还原（优先跑生成器，见第 3.1 节），重跑自检直到 12/12，**再**开始正式流程 |
| 缺 `.vue`（任一份） | 🔴 阻断级 + 类型级 | **必须**还原（优先跑生成器，见第 3.1 节）；若生成器不可用则按第 2.4 节逐字还原；若确实无法还原，第 2 步技术栈选择时**主动排除「AI 导航网站」**，改推 VitePress / 纯静态 |
| 缺 `.template`（任一份） | 🟡 非阻断 | 建议同样还原（保持与上游一致、依赖清单可查），然后开始正式流程 |

### 1.5 可忽略的噪声

- skill 目录下若出现字面量目录 `~/Library/`（含 `~` 和斜杠的空目录），是 `validate-path.sh`
  历史测试的残留，**与本流程无关，忽略即可**，不需要删除。
- macOS 的 `.DS_Store` 出现在任意目录都属正常噪声，不计入完整性判定。

---

## 2. 第 2 步：生成规律与内容规律

### 2.1 `.gitignore` 的生成规律

#### 2.1.1 位置与命名规律

- 路径固定为 `templates/<框架标识>/.gitignore`，**每个模板根目录恰好一份**，共 5 份。
- `<框架标识>` = `git-init.sh` 的 `$FRAMEWORK` 入参 = `init-<type>.sh` 里 `TEMPLATE_DIR` 的末段，
  取值集合固定：`hexo | vitepress | vue3 | portfolio | resume`。
- 文件名恒为 `.gitignore`（无框架后缀），因为它由「框架目录」+「固定文件名」两级定位，
  与内容无关。

#### 2.1.2 职责与消费方式（这决定了缺失后果）

`.gitignore` 不留在模板目录里，而是由 init 脚本**复制到用户项目根目录**，
让新建仓库第一次 `git add` 之前就带上正确的忽略规则。

| 消费脚本 | 复制方式 | `.gitignore` 缺失时的实际行为 |
|---|---|---|
| `scripts/init-vitepress.sh`（第 74 行） | `cp "$TEMPLATE_DIR/.gitignore" .gitignore` 裸执行 | 🔴 脚本头 `set -e` → **整个 init 中止**：依赖已装、README 未生成、git 未初始化 |
| `scripts/init-vue3.sh`（第 80 行） | 同上 | 🔴 同上 |
| `scripts/init-portfolio.sh`（第 35 行） | 同上 | 🔴 中止在第 2 步，连占位符替换都没跑 |
| `scripts/init-resume.sh`（第 31 行） | 同上 | 🔴 同上 |
| `scripts/init-hexo.sh`（第 117 行） | `if [ -f ... ]` 守卫 | ⚠️ **静默跳过** → 生成的 hexo 项目没有忽略规则，`node_modules/`、`public/` 会被提交进 git |
| `scripts/git-init.sh`（第 31 行） | `if [ -f ... ]` 守卫 | ⚠️ 静默跳过 → 兜底也没兜住 |

> **为什么 hexo 与 git-init.sh 有守卫、其余 4 个没有**：`init-hexo.sh` 与 `git-init.sh`
> 里那段是后来补的兼容写法；`init-vitepress.sh` / `init-vue3.sh` / `init-portfolio.sh` /
> `init-resume.sh` 里的 `cp` 仍是早期裸写法。**这正是「先还原再执行」不可跳过的原因。**

#### 2.1.3 内容结构规律（4 段式，从上到下）

1. **标题注释**：首行 `# <框架名>`，框架名与目录标识一一对应
   （`# Hexo`、`# VitePress`、`# Vue 3 + Vite`、`# 个人作品集`、`# 个人简历站`）。
2. **通用块**：`.DS_Store`、`node_modules/`、`.vscode/`、`.idea/`
   （纯静态的 `resume` 连 `node_modules/` 都不需要）。
3. **框架专属块**：见 2.1.4 对照表。
4. **分组注释块**：`# IDE`、`# 环境`、`# 日志`、`# 临时`；
   每个分组前用**一个空行**分隔，组内条目不再空行。

#### 2.1.4 框架专属块对照表

| 模板 | 专属忽略项 | 推导来源 |
|---|---|---|
| `hexo` | `Thumbs.db`、`db.json`、`*.log`、`public/`、`.deploy*/`、`_multiconfig.yml`、`*.swp`、`*.swo`、`.env`、`.env.local`、`*.tmp`、`.cache/` | `db.json`=Hexo 数据缓存；`public/`=构建产物目录；`.deploy*/`=部署状态前缀（`deploy.sh` 写 `.deploy-state.json`）；`_multiconfig.yml`=Hexo 多配置；`*.swp/*.swo`=vim 临时文件 |
| `vitepress` | `docs/.vitepress/dist/`、`docs/.vitepress/cache/`、`.env`、`.env.local` | `docs/.vitepress/dist` = 构建产物目录（**必须写全路径**） |
| `vue3-vite` | `dist/`、`dist-ssr/`、`*.log`、`npm-debug.log*`、`yarn-debug.log*`、`yarn-error.log*`、`pnpm-debug.log*`、`.env`、`.env.local` | `dist` = 构建产物目录；`dist-ssr` = Vite SSR 产物；后面是各包管理器的日志 |
| `portfolio` | 仅通用块 | 纯静态 HTML，无构建步骤、无产物目录 |
| `resume` | 仅 `.DS_Store`、`.vscode/`、`.idea/` | 单文件 HTML，连 `node_modules/` 都不产生 |

#### 2.1.5 核心不变量（改模板 / 还原时必须守住）

- **构建产物目录必须与 `scripts/substitute.sh` 的 `get_dist()` 查表一致**：
  `hexo→public`、`vitepress→docs/.vitepress/dist`、`vue3→dist`、`portfolio→.`、`resume→.`
  写错的后果：`deploy.sh` 找不到产物（部署失败），或把产物提交进 git。
- 依赖目录恒为 `node_modules/`（纯静态站除外）。
- IDE 目录恒为 `.vscode/`、`.idea/`。
- 环境变量文件恒为 `.env`、`.env.local`。
- 纯静态站（portfolio / resume）不应出现任何构建产物行。
- 全部使用 Unix 换行（LF），**末尾不带换行符**，无行尾空格。

### 2.2 `.template` 的生成规律

#### 2.2.1 位置与命名规律

- 路径固定为 `templates/<框架标识>/package.json.template`，
  **只在需要 npm 依赖的框架上存在**：`vitepress`、`vue3-vite`。
- `portfolio` / `resume` / `hexo` 没有这个文件 ——
  前两者是纯静态无依赖，后者由 `npx hexo init` 现场生成 `package.json`。
- 命名规律：`<最终文件名> + .template`。
  `.template` 后缀的作用是**防止包管理器 / 编辑器把它当成真的 `package.json` 解析**
  （同名真包会让 `npm install` 在模板目录里装出一堆无关依赖）。

#### 2.2.2 内容规律

标准 `package.json` 字段顺序：

| 字段 | vitepress | vue3-vite |
|---|---|---|
| `name` | `{{SITE_NAME_SLUG}}` | `{{SITE_NAME_SLUG}}` |
| `version` | `"0.0.0"` | `"0.0.0"` |
| `private` | `true` | `true` |
| `description` | `{{SITE_DESCRIPTION}}` | `{{SITE_DESCRIPTION}}` |
| `type` | `"module"` | `"module"` |
| `scripts` | `docs:dev` / `docs:build` / `docs:preview` | `dev` / `build` / `preview` |
| `dependencies` | —— | `vue ^3.5.0`、`vue-router ^4.4.0` |
| `devDependencies` | `vitepress ^1.5.0`、`vue ^3.5.0` | `@vitejs/plugin-vue ^5.1.0`、`vite ^5.4.0` |

- **占位符只允许两个**：`{{SITE_NAME_SLUG}}` 与 `{{SITE_DESCRIPTION}}`，
  且都在 `scripts/substitute.sh` 的白名单内（`substitute.sh --check` 可校验）。
- **`{{SITE_NAME_SLUG}}` 的派生规则**（`substitute.sh` 第 126–138 行）：
  `SITE_NAME` → 转小写 → 非 `[a-z0-9-]` 一律替换为 `-` → 连续 `-` 折叠为一个 →
  去首尾 `-`；结果为空时兜底为 `my-site`。
- **版本约束**：全部 `^` 语义化版本范围，且与 init 脚本里 `npm install` 的版本一一对应
  （`vitepress ^1.5.0`、`vue ^3.5.0`、`vue-router ^4.4.0`、`vite ^5.4.0`、`@vitejs/plugin-vue ^5.1.0`）。

#### 2.2.3 运行时真相（避免误判严重性）

`init-vitepress.sh` 与 `init-vue3.sh` **并不读取** `.template` 文件，
它们用 `npm init -y` + `npm pkg set` + `npm install` **现场生成**真 `package.json`。

因此：

- `.template` 缺失 **不会** 影响项目生成结果，**不是阻断项**；
- 但它是「离线可读的依赖与脚本权威副本」—— 缺了它，AI 要回答
  「这个项目用了哪些依赖、scripts 长什么样」时只能去翻 init 脚本；
- 它也是 `package.json` **完整字段布局**（含 `private` / `type` / `version` 等非依赖字段）
  的唯一书面载体 —— 没有它，这套布局只能靠推断。

### 2.3 `.vue` 的生成规律与内容规律

> **与前两类的本质差别**：`.gitignore` / `.template` 是「规则类」文件，可以靠规律推导；
> `.vue` 是**源码主体**，但它的**结构**同样有强规律（SFC 三段式 + 组件契约 + 数据驱动），
> 所以能靠 `scripts/gen-restricted-files.py` 按规格表重建 —— 不必手抄。
> 本节讲清规律，脚本把规律落成代码；脚本不可用时再用第 2.4 节原文照抄。

#### 2.3.1 位置与命名规律

- 全部集中在 `templates/vue3-vite/src/` 一个模板下，共 5 个：

  | 文件 | 角色 |
  |---|---|
  | `src/App.vue` | 应用外壳（入口组件） |
  | `src/components/HeaderNav.vue` | 顶部导航 |
  | `src/components/ToolCard.vue` | 工具卡片 |
  | `src/views/Home.vue` | 首页（按分类铺开全部工具） |
  | `src/views/Category.vue` | 分类详情页 |

- **目录约定**与 `init-vue3.sh` 第 29 行的 `mkdir -p src/router src/views src/components src/data` 一一对应：
  - `views/` = 路由页面（与 `src/router/index.js` 的 routes 一一对应）
  - `components/` = 无路由的可复用组件
  - `data/` = 数据源（`tools.js`，纯 `.js`，不受平台限制）
- **命名规律**：PascalCase 文件名 = 组件名（`App.vue` → `App`、`Home.vue` → `Home`），
  沿用 Vue 官方约定，便于 IDE 跳转。

#### 2.3.2 内容规律

- **Vue 3 SFC 三段式**，块顺序统一为 `<script setup>` → `<template>` → `<style scoped>`：
  - `<script setup>`：组合式 API 写法，不写 `export default`
  - `<template>`：模板
  - `<style scoped>`：样式，作用域限定到本组件
- **占位符只有 3 个**，且都在 `substitute.sh` 白名单内：
  - `{{SITE_NAME}}` —— `App.vue` 页脚、`HeaderNav.vue` logo、`Home.vue` H1
  - `{{SITE_DESCRIPTION}}` —— `Home.vue` 副标题
  - `{{YEAR}}` —— `App.vue` 页脚年份
  - ⚠️ `init-vue3.sh` 第 71–75 行的 substitute 只作用于 `index.html`、`src/App.vue`、
    `src/components/HeaderNav.vue`、`src/views/Home.vue` 四个文件；
    `ToolCard.vue` 与 `Category.vue` **不含占位符**（纯展示逻辑），所以不参与替换。
- **数据驱动**：`src/data/tools.js` 导出 `categories` 数组，结构为
  `{ id, name, icon, tools: [{ name, desc, url }] }`。
  `HeaderNav.vue` 读它生成导航、`Home.vue` 读它铺开全部工具、
  `Category.vue` 用 `route.params.id` 从中 `find` 出单个分类。
  → **用户改导航内容只改 `tools.js`，不用动组件**。
- **组件契约**：
  - `ToolCard.vue` 用 `defineProps({ tool: { type: Object, required: true } })` 接单个工具对象，
    渲染 `tool.name / tool.desc / tool.url`，外链带 `target="_blank" rel="noopener noreferrer"`
  - `HeaderNav.vue` 用 `RouterLink` + `v-for="cat in categories"` 生成导航项，路径 `/category/${cat.id}`
  - `Category.vue` 用 `computed` + `useRoute().params.id` 匹配分类，匹配不到渲染「分类不存在」
  - `App.vue` 挂 `<HeaderNav />` + `<router-view />` + 页脚
- **路由契约**：`src/router/index.js` 两条路由 —— `/` → `Home.vue`、`/category/:id` → `Category.vue`，
  使用 `createWebHashHistory()`（hash 模式，部署到 CloudBase / Netlify 等静态托管更稳）。
- **样式契约**：颜色、圆角、阴影一律走 CSS 变量
  （`--color-primary`、`--color-bg`、`--color-bg-alt`、`--color-border`、`--color-text`、
  `--color-text-muted`、`--radius`、`--shadow`），定义在 `src/style.css`（`.css` 后缀，不受平台限制）。
  新增组件请沿用变量，不要写死颜色。
- **依赖版本**：`vue ^3.5.0`、`vue-router ^4.4.0`、`@vitejs/plugin-vue ^5.1.0`、`vite ^5.4.0`
  （与 `templates/vue3-vite/package.json.template` 完全一致）。
- 全部 LF 换行、无行尾空格、**末尾不带换行符**。

#### 2.3.3 缺失后果

- `init-vue3.sh` 第 36–41 行是**裸 `cp`**（无 `if [ -f ]` 守卫），脚本头 `set -e`，
  任一 `.vue` 缺失 → **第 2 步「复制所有源码文件」就中止**，
  此时目录已建、依赖未装、git 未初始化。
- **业务影响**：`.vue` 缺失 ⇒ 「AI 导航网站（Vue 3 + Vite）」这一**类型整体不可用**。
  必须在第 2 步技术栈选择阶段就改推 VitePress（知识库型）或纯静态类型，
  而不是等执行阶段才炸。

### 2.4 十二个文件的完整原文（还原用，请逐字照抄）

> 路径均相对 skill 根目录。**所有文件末尾不带换行符**；
> 若写入工具强制补了换行，功能不受影响（gitignore 按行解析、JSON / SFC 解析器容忍尾随换行）。

#### ① `templates/hexo/.gitignore`（174 字节 / 23 行）

```
# Hexo
.DS_Store
Thumbs.db
db.json
*.log
node_modules/
public/
.deploy*/
_multiconfig.yml

# IDE
.vscode/
.idea/
*.swp
*.swo

# 环境
.env
.env.local

# 临时
*.tmp
.cache/
```

#### ② `templates/vitepress/.gitignore`（129 字节 / 13 行）

```
# VitePress
.DS_Store
node_modules/
docs/.vitepress/dist/
docs/.vitepress/cache/

# IDE
.vscode/
.idea/

# 环境
.env
.env.local
```

#### ③ `templates/vue3-vite/.gitignore`（182 字节 / 20 行）

```
# Vue 3 + Vite
.DS_Store
node_modules/
dist/
dist-ssr/

# IDE
.vscode/
.idea/

# 环境
.env
.env.local

# 日志
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
```

#### ④ `templates/portfolio/.gitignore`（57 字节 / 5 行）

```
# 个人作品集
.DS_Store
node_modules/
.vscode/
.idea/
```

#### ⑤ `templates/resume/.gitignore`（43 字节 / 4 行）

```
# 个人简历站
.DS_Store
.vscode/
.idea/
```

#### ⑥ `templates/vitepress/package.json.template`（356 字节 / 16 行）

```json
{
  "name": "{{SITE_NAME_SLUG}}",
  "version": "0.0.0",
  "private": true,
  "description": "{{SITE_DESCRIPTION}}",
  "type": "module",
  "scripts": {
    "docs:dev": "vitepress dev docs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs"
  },
  "devDependencies": {
    "vitepress": "^1.5.0",
    "vue": "^3.5.0"
  }
}
```

#### ⑦ `templates/vue3-vite/package.json.template`（390 字节 / 20 行）

```json
{
  "name": "{{SITE_NAME_SLUG}}",
  "version": "0.0.0",
  "private": true,
  "description": "{{SITE_DESCRIPTION}}",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "vite": "^5.4.0"
  }
}
```

#### ⑧ `templates/vue3-vite/src/App.vue`（732 字节 / 44 行）

```vue
<script setup>
import HeaderNav from './components/HeaderNav.vue'
</script>

<template>
  <div class="app">
    <HeaderNav />
    <main class="main">
      <router-view />
    </main>
    <footer class="footer">
      <div class="container">
        <p>{{SITE_NAME}} · {{YEAR}}</p>
        <p>Made with Vue 3 + Vite</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main {
  flex: 1;
  padding: 2rem 0;
}

.footer {
  background: var(--color-bg-alt);
  border-top: 1px solid var(--color-border);
  padding: 2rem 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.footer p {
  margin: 0.25rem 0;
}
</style>
```

#### ⑨ `templates/vue3-vite/src/components/HeaderNav.vue`（1691 字节 / 93 行）

```vue
<script setup>
import { categories } from '../data/tools.js'
import { RouterLink } from 'vue-router'
</script>

<template>
  <header class="header">
    <div class="container header-inner">
      <RouterLink to="/" class="logo">{{SITE_NAME}}</RouterLink>
      <nav class="nav">
        <RouterLink
          v-for="cat in categories"
          :key="cat.id"
          :to="`/category/${cat.id}`"
          class="nav-link"
        >
          {{ cat.icon }} {{ cat.name }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
  background-color: rgba(255, 255, 255, 0.8);
}

@media (prefers-color-scheme: dark) {
  .header {
    background-color: rgba(15, 23, 42, 0.8);
  }
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  gap: 2rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
}

.logo:hover {
  color: var(--color-primary);
}

.nav {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.nav-link {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
  text-decoration: none;
  transition: all 0.15s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--color-primary);
  background: var(--color-bg-alt);
  text-decoration: none;
}

@media (max-width: 640px) {
  .header-inner {
    flex-direction: column;
    height: auto;
    padding: 1rem 0;
  }

  .nav {
    gap: 0.5rem;
  }
}
</style>
```

#### ⑩ `templates/vue3-vite/src/components/ToolCard.vue`（1099 字节 / 57 行）

```vue
<script setup>
defineProps({
  tool: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <a :href="tool.url" target="_blank" rel="noopener noreferrer" class="card">
    <h3 class="card-name">{{ tool.name }}</h3>
    <p class="card-desc">{{ tool.desc }}</p>
    <span class="card-link">访问 →</span>
  </a>
</template>

<style scoped>
.card {
  display: block;
  padding: 1.5rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--color-text);
  transition: all 0.2s;
  box-shadow: var(--shadow);
}

.card:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  text-decoration: none;
}

.card-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.card-desc {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.card-link {
  color: var(--color-primary);
  font-size: 0.85rem;
  font-weight: 500;
}
</style>
```

#### ⑪ `templates/vue3-vite/src/views/Home.vue`（1414 字节 / 70 行）

```vue
<script setup>
import { categories } from '../data/tools.js'
import ToolCard from '../components/ToolCard.vue'
</script>

<template>
  <div class="container">
    <header class="hero">
      <h1>{{SITE_NAME}}</h1>
      <p class="hero-tagline">{{SITE_DESCRIPTION}}</p>
    </header>

    <div v-for="cat in categories" :key="cat.id" class="category-section">
      <h2 class="category-title">
        <span class="category-icon">{{ cat.icon }}</span>
        {{ cat.name }}
      </h2>
      <div class="tools-grid">
        <ToolCard v-for="tool in cat.tools" :key="tool.name" :tool="tool" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 3rem 0 4rem;
}

.hero h1 {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-tagline {
  font-size: 1.25rem;
  color: var(--color-text-muted);
  max-width: 600px;
  margin: 0 auto;
}

.category-section {
  margin-bottom: 4rem;
}

.category-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.category-icon {
  font-size: 2rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}
</style>
```

#### ⑫ `templates/vue3-vite/src/views/Category.vue`（1627 字节 / 78 行）

```vue
<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { categories } from '../data/tools.js'
import ToolCard from '../components/ToolCard.vue'

const route = useRoute()
const router = useRouter()

const category = computed(() => {
  return categories.find(c => c.id === route.params.id)
})
</script>

<template>
  <div class="container">
    <button class="back-btn" @click="router.push('/')">← 返回首页</button>

    <div v-if="category" class="category-page">
      <h1>
        <span class="icon">{{ category.icon }}</span>
        {{ category.name }}
      </h1>
      <p class="count">共 {{ category.tools.length }} 个工具</p>
      <div class="tools-grid">
        <ToolCard v-for="tool in category.tools" :key="tool.name" :tool="tool" />
      </div>
    </div>

    <div v-else class="not-found">
      <h2>分类不存在</h2>
    </div>
  </div>
</template>

<style scoped>
.back-btn {
  background: none;
  border: 1px solid var(--color-border);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--color-text);
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.back-btn:hover {
  background: var(--color-bg-alt);
}

.category-page h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.icon {
  font-size: 2.5rem;
  margin-right: 0.5rem;
}

.count {
  color: var(--color-text-muted);
  margin-bottom: 2rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.not-found {
  text-align: center;
  padding: 4rem 0;
  color: var(--color-text-muted);
}
</style>
```

> **找不到原文时的兜底**：从上游仓库按同名路径取
> `https://github.com/CoderWanFeng/wanfeng-skills/tree/main/skills/personal-website-builder`
> （GitHub 保留点号开头的文件，也不会过滤 `.vue`，不会被部分安装平台那样丢掉）。

---

## 3. 第 3 步：在 AI 中运行本 Skill 的正确姿势

### 3.1 给用户的一句话说明（可直接照说）

```
我先做一次文件完整性自检 —— 有些安装平台会过滤掉以 . 开头的隐藏文件（如 .gitignore）、
带 .template 后缀的文件和 .vue 组件文件。这三类文件本 skill 的建站脚本依赖，
缺失会导致建站中断，所以我先确认并在必要时还原，再开始正式流程。
```

### 3.2 AI 侧执行顺序（强制，不可跳过）

```
Step 0  自检
        python3 scripts/gen-restricted-files.py --check
        ↓
        ├─ 退出码 0（12/12 齐全） → 报告「完整性自检通过」 → 进入第 1 步（网站类型选择）
        ↓
        └─ 退出码 1（有缺失/漂移）
                ↓
                方式 A（首选）：跑生成器补齐
                    python3 scripts/gen-restricted-files.py
                    → 自动重建缺失文件（幂等，只补缺的，不动已正确的）
                    → 重跑 --check，必须变 12/12
                    → 报告「已还原 N 个文件：…」 → 进入第 1 步
                    ↓
                方式 B（生成器脚本本身不可用时）：
                    按本文件第 2.4 节逐字写回
                    → 重跑 --check 或 find 命令，必须变 12/12
                    → 报告「已还原 N 个文件：…」 → 进入第 1 步
                    ↓
                若 .vue 仍缺失且无法还原：
                    第 2 步技术栈选择时排除「AI 导航网站」，改推 VitePress / 纯静态
```

### 3.3 方式 A：跑生成器脚本（首选）

随包附带 `scripts/gen-restricted-files.py`，把第 2 节的**生成规律固化成代码**。
它不依赖任何第三方包、不联网、纯标准库，在用户的本地机器上直接跑。

```bash
cd <skill 根目录>

# 1) 只检查，不写文件
python3 scripts/gen-restricted-files.py --check
#    退出码 0 = 12/12 齐全；1 = 有缺失或漂移

# 2) 补齐缺失文件（默认行为，幂等 —— 已正确的文件一个字节都不动）
python3 scripts/gen-restricted-files.py

# 3) 强制重建全部 12 个（怀疑文件被平台改坏时用）
python3 scripts/gen-restricted-files.py --force

# 4) 指定 skill 根目录（脚本不在标准位置时）
python3 scripts/gen-restricted-files.py --target /path/to/skill
```

**写文件前必过的三项自检**（任一不通过则一个文件都不写，避免把坏模板写进包里）：

| 自检 | 校验内容 | 失败含义 |
|---|---|---|
| ① CSS 变量闭环 | 每个 `.vue` 里 `var(--x)` 引用的变量，都必须在 `src/style.css` 里定义过 | 组件与样式脱节，构建出来是白底黑字无主题 |
| ② 产物目录对齐 | `.gitignore` 忽略的构建产物目录，必须等于 `substitute.sh` 的 `get_dist()` 查表结果（vitepress 要写全 `docs/.vitepress/dist/`） | `npm run build` 产物会被误提交进 git |
| ③ 依赖版本对齐 | `package.json.template` 的版本范围，必须等于 `init-*.sh` 里 `npm install` 的版本 | 模板与实际安装的依赖对不上 |

**验证过的等价性**：删除全部 12 个文件 → 跑生成器 → 产物与仓库原文件**逐字节一致**
（`git status` 干净，blob hash 与 `HEAD` 相同）；生成的 `.vue` 经 `init-vue3.sh` 初始化后
`npm run build` **真实构建通过**，5 个组件与工具数据均正确进入产物 bundle。

### 3.4 方式 B：按第 2.4 节逐字照抄（生成器不可用时的兜底）

- **写回路径**：`templates/<框架>/` 下的原路径，例如
  `templates/hexo/.gitignore`、`templates/vue3-vite/package.json.template`、
  `templates/vue3-vite/src/views/Home.vue`。
- **内容**：照抄第 2.4 节原文，**不要**自行改写、增删注释、调整顺序或"优化"分组。
- **`.vue` 特殊要求**：这是源码主体，**必须逐字照抄**，不要凭印象重写模板或样式；
  照抄后确认 `<script setup>` / `<template>` / `<style scoped>` 三段齐全、缩进为 2 空格。
- **末尾换行**：不必纠结。原文末行不带换行符；工具若强制补了换行，功能不受影响。
- **不要**把还原后的文件写进用户的目标项目目录 —— 那是 init 脚本的职责。
- **只写 `templates/` 目录**，不要改动 `scripts/`、`SKILL.md`、`references/`。
- 还原属于「补齐安装包缺失内容」，不改变 skill 的功能定义，**不需要**升级版本号。

### 3.5 还原后的可选深检

```bash
./tests/smoke.sh
```

该脚本会跑 `npm install` 与真实构建，耗时几分钟。
**只在你怀疑 `scripts/` 也被平台改动过时才需要**；正常情况下第 1 节的自检 12/12 即代表可用。

---

## 4. 速查表

| 场景 | 结论 |
|---|---|
| `.gitignore` 丢了 | 🔴 阻断级：必须先还原，否则 4/5 类型 init 中止、hexo 静默留下脏仓库 |
| `.vue` 丢了 | 🔴 阻断级 + 类型级：必须还原；优先跑生成器，还原不了就把「AI 导航网站」从选项里去掉 |
| `.template` 丢了 | 🟡 非阻断，但建议还原：它是 package.json 字段布局与依赖版本的离线权威副本 |
| 还原到哪 | `templates/<框架>/` 下的原路径 |
| 什么时候还原 | **在第 1 步（网站类型选择）之前** |
| 内容从哪来 | **首选** `python3 scripts/gen-restricted-files.py`；兜底用本文件第 2.4 节原文 |
| 怎么验证还原成功 | `python3 scripts/gen-restricted-files.py --check` 退出码为 `0`（等价于 `find ... \| wc -l` 输出 `12`） |
