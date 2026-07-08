# {{SITE_NAME}}

{{SITE_DESCRIPTION}}

> 基于 **Hexo + Butterfly 主题** 的个人博客

## 快速开始

### 安装依赖

```bash
npm install
```

### 本地开发

```bash
npx hexo server
```

打开浏览器访问：<http://localhost:4000>

### 构建静态文件

```bash
npx hexo generate
```

构建产物在 `public/` 目录。

### 清理 + 重新生成

```bash
npx hexo clean && npx hexo generate
```

## 目录结构

```
.
├── _config.yml          # 主配置
├── _config.butterfly.yml  # Butterfly 主题配置
├── package.json
├── source/
│   ├── _posts/         # 文章（Markdown）
│   └── _drafts/        # 草稿
├── themes/             # 主题（git submodule）
├── public/             # 构建产物
└── scaffolds/          # 文章模板
```

## 如何写文章

```bash
# 新建文章
npx hexo new "文章标题"

# 编辑 source/_posts/文章标题.md

# 预览效果
npx hexo server
```

frontmatter 示例：

```markdown
---
title: 文章标题
date: 2026-01-01 12:00:00
tags:
  - 标签1
  - 标签2
categories:
  - 分类
---
```

## 主题自定义

修改 `_config.butterfly.yml`：

- 导航菜单
- 首页大图
- 社交链接（GitHub / 邮箱 / RSS）
- 代码高亮主题
- 暗黑模式开关

详细配置见 [Butterfly 文档](https://butterfly.js.org/)

## 部署方式

### 方案 1：腾讯云 CloudBase 静态托管（推荐 · 国内访问快）

零代码部署，免费额度够个人项目用：

1. 打开 <https://console.cloud.tencent.com/tcb> 创建环境（实名 + 创建环境，记下环境 ID）
2. 安装 CLI：`npm install -g @cloudbase/cli`
3. 登录：`tcb login`
4. 构建产物：`npx hexo generate`
5. 上传：`tcb hosting deploy public -e <环境ID>`
6. 拿到默认域名 `https://xxx.tcloudbaseapp.com`，即可访问

绑定自定义域名：控制台 → CloudBase → 静态托管 → 自定义域名 → 添加。国内节点需 ICP 备案（海外节点免备案）。

### 方案 2：Vercel（推荐 · 海外访问）

1. 把代码 push 到 GitHub
2. 在 <https://vercel.com> 导入仓库
3. 框架自动识别（Build Command: `hexo generate`，Output: `public`）

### 方案 3：GitHub Pages

1. 安装部署插件：`npm install hexo-deployer-git --save`
2. 修改 `_config.yml`：

   ```yaml
   deploy:
     type: git
     repo: https://github.com/<用户名>/<用户名>.github.io.git
     branch: main
   ```

3. 部署：`npx hexo deploy`

### 方案 4：Netlify

1. 在 <https://app.netlify.com> 新建站点，关联 GitHub 仓库
2. Build command: `hexo generate`
3. Publish directory: `public`

### 方案 5：自己的服务器

```bash
npx hexo generate
rsync -avz public/ user@server:/var/www/blog/
```

## 许可证

MIT License © {{AUTHOR_NAME_OR_DEFAULT}}