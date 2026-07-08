# Placeholder Registry

> **单一权威表**：所有模板、配置、脚本里的占位符都必须在这个文件里登记。
> `scripts/substitute.sh` 读取此文件做替换；新增占位符时同步更新。

## 命名约定

- 全部用 `{{UPPER_SNAKE_CASE}}`
- 命名要「自解释」，避免缩写歧义
- 同一个字段只能有一个名字（修复 SKILL.md 原版的 `{网站名}` / `{网站名称}` / `{网站名 slug}` 三种叫法问题）

## 标准占位符（必填，从用户输入或默认值）

| 占位符 | 含义 | 来源 | 默认值（用户留空时） |
|--------|------|------|---------------------|
| `{{SITE_NAME}}` | 网站名称 | 第 3 步用户回答 | `My Site`（en）/ `我的网站`（zh） |
| `{{SITE_NAME_SLUG}}` | 网站名称的 slug 形式（kebab-case，ASCII） | 由 `SITE_NAME` 转换 | 从 SITE_NAME 自动生成（小写、空格转 -、去非 ASCII） |
| `{{SITE_DESCRIPTION}}` | 一句话描述 | 第 3 步用户回答 | `A personal website built with {{FRAMEWORK}}` |
| `{{AUTHOR_NAME}}` | 作者姓名 | 第 3 步用户回答 | `Your Name`（en）/ `你的名字`（zh） |
| `{{GITHUB_USERNAME}}` | GitHub 用户名（英文 slug） | 第 3 步用户回答 | 留空 → 触发 `{{GITHUB_OR_EMPTY}}` 删除逻辑 |
| `{{SITE_NAME_SLUG}}` | 网站名称的 slug 形式 | 由 `SITE_NAME` 转换 | 自动从 SITE_NAME 生成（kebab-case） |
| `{{FRAMEWORK}}` | 技术栈 | 第 2 步用户选择 | 由 `init-*.sh` 脚本注入 |
| `{{SITE_TYPE}}` | 网站类型（中文） | 第 1 步用户选择 | `个人博客` / `知识库` / `AI 导航` / `作品集` / `简历` |
| `{{SITE_TYPE_EN}}` | 网站类型（英文） | 由 `SITE_TYPE` 映射 | `Blog` / `Knowledge Base` / `AI Tools` / `Portfolio` / `Resume` |

## 条件删除占位符（用户留空时删除整行）

> 这些占位符通常出现在 YAML / 配置项的「整行」中。当用户输入为空时，
> `substitute.sh` 会删除包含该占位符的**整行**（含缩进）。

| 占位符 | 行为 |
|--------|------|
| `{{GITHUB_OR_EMPTY}}` | 留空 → 删除整行（含 `socialLinks`、`social` 等 GitHub 相关配置） |

## 运行时占位符（执行时由脚本替换）

| 占位符 | 替换逻辑 | 解析时机 |
|--------|---------|---------|
| `{{DATE_ISO}}` | `$(date +%Y-%m-%d)` | substitute.sh 运行时 |
| `{{DATE_PATH}}` | `$(date +%Y/%m/%d)` | substitute.sh 运行时 |
| `{{YEAR}}` | `$(date +%Y)` | substitute.sh 运行时 |
| `{{PROJECT_ROOT}}` | `pick-dirname.sh` 输出 | init 前 |
| `{{DIST_DIR}}` | 按框架查表：`hexo→public`、`vitepress→docs/.vitepress/dist`、`vue3→dist`、`hugo→public`、`static→.` | substitute.sh 运行时 |
| `{{DEV_PORT}}` | 按框架查表：`hexo→4000`、`vitepress→5173`、`vue3→5173`、`hugo→1313` | substitute.sh 运行时 |
| `{{DEV_CMD}}` | 按框架查表：`hexo→"npx hexo server"` 等 | substitute.sh 运行时 |
| `{{BUILD_CMD}}` | 按框架查表：`hexo→"npx hexo generate"` 等 | substitute.sh 运行时 |

## 已废弃占位符（不要在新模板里用）

| 旧名 | 新名 | 原因 |
|------|------|------|
| `{网站名}` | `{{SITE_NAME}}` | 统一命名 |
| `{网站名称}` | `{{SITE_NAME}}` | 统一命名 |
| `{网站名 slug}` | `{{SITE_NAME_SLUG}}`（如需） | 拼写不一致 |
| `{网站描述}` | `{{SITE_DESCRIPTION}}` | 统一命名 |
| `{作者}` | `{{AUTHOR_NAME}}` | 统一命名 |
| `{作者名}` | `{{AUTHOR_NAME}}` | 统一命名 |
| `{GitHub 用户名}` | `{{GITHUB_USERNAME}}` | 统一命名 |
| `{{DATE_PREFIX}}` | `{{DATE_ISO}}` | 与 `{{DATE_ISO}}` 值完全相同，合并 |
| `{dist 或 public 目录}` | `{{DIST_DIR}}` | 不应让 executor 选 |

## 框架映射表（substitute.sh 内部使用）

```bash
declare -A FRAMEWORK_DIST=(
  ["hexo"]="public"
  ["vitepress"]="docs/.vitepress/dist"
  ["vue3"]="dist"
  ["hugo"]="public"
  ["portfolio"]="."
  ["resume"]="."
)

declare -A FRAMEWORK_PORT=(
  ["hexo"]="4000"
  ["vitepress"]="5173"
  ["vue3"]="5173"
  ["hugo"]="1313"
  ["portfolio"]="0"
  ["resume"]="0"
)

declare -A FRAMEWORK_DEV_CMD=(
  ["hexo"]="npx hexo server"
  ["vitepress"]="npx vitepress dev docs"
  ["vue3"]="npx vite"
  ["hugo"]="hugo server"
  ["portfolio"]="open index.html"
  ["resume"]="open index.html"
)

declare -A FRAMEWORK_BUILD_CMD=(
  ["hexo"]="npx hexo generate"
  ["vitepress"]="npx vitepress build docs"
  ["vue3"]="npx vite build"
  ["hugo"]="hugo"
  ["portfolio"]="echo 'No build step needed'"
  ["resume"]="echo 'No build step needed'"
)
```

## 验证规则

1. **不允许出现未登记的占位符**：`scripts/substitute.sh --check` 会扫描所有模板，未登记的占位符报错
2. **不允许使用旧名**：上面「已废弃」表里的名字，模板里出现直接报错
3. **条件占位符必须独立成行**：否则 `留空删除整行` 会误删配置