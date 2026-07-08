# {{SITE_NAME}}

{{SITE_DESCRIPTION}}

> 基于 **VitePress** 的知识库 / 文档站

## 快速开始

### 安装依赖

```bash
npm install
```

### 本地开发

```bash
npm run docs:dev
```

打开浏览器访问：<http://localhost:5173>

### 构建静态文件

```bash
npm run docs:build
```

构建产物在 `docs/.vitepress/dist/` 目录。

### 预览构建产物

```bash
npm run docs:preview
```

## 目录结构

```
.
├── docs/
│   ├── .vitepress/
│   │   └── config.mts     # VitePress 配置
│   ├── guide/              # 指南文档
│   │   └── getting-started.md
│   ├── en/                 # 英文文档
│   ├── index.md            # 首页
│   └── public/             # 静态资源
├── package.json
└── README.md
```

## 如何写文档

在 `docs/` 下新建 `.md` 文件，然后在 `docs/.vitepress/config.mts` 的 `sidebar` 里注册：

```ts
sidebar: [
  {
    text: '入门',
    items: [
      { text: '新文档', link: '/new-doc' }
    ]
  }
]
```

## 主题自定义

修改 `docs/.vitepress/config.mts`：

- `themeConfig.nav` — 顶部导航
- `themeConfig.sidebar` — 左侧导航
- `themeConfig.socialLinks` — 社交链接
- `themeConfig.footer` — 页脚

## 部署方式

### 方案 1：腾讯云 CloudBase 静态托管（推荐 · 国内访问快）

1. 打开 <https://console.cloud.tencent.com/tcb> 创建环境，记下环境 ID
2. 安装 CLI：`npm install -g @cloudbase/cli`
3. 登录：`tcb login`
4. 构建产物：`npm run docs:build`
5. 上传：`tcb hosting deploy docs/.vitepress/dist -e <环境ID>`
6. 拿到默认域名 `https://xxx.tcloudbaseapp.com`

### 方案 2：Vercel（推荐 · 海外访问）

1. 把代码 push 到 GitHub
2. 在 <https://vercel.com> 导入仓库
3. 框架自动识别（Build Command: `npm run docs:build`，Output: `docs/.vitepress/dist`）

### 方案 3：GitHub Pages

1. 在 GitHub 仓库设置 → Pages → Source: GitHub Actions
2. 新建 `.github/workflows/deploy.yml`：

   ```yaml
   name: Deploy VitePress
   on:
     push:
       branches: [main]
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with:
             node-version: 20
         - run: npm install
         - run: npm run docs:build
         - uses: actions/upload-pages-artifact@v3
           with:
             path: docs/.vitepress/dist
     deploy:
       needs: build
       runs-on: ubuntu-latest
       environment:
         name: github-pages
         url: ${{ steps.deployment.outputs.page_url }}
       steps:
         - id: deployment
           uses: actions/deploy-pages@v4
   ```

### 方案 4：Netlify

1. 在 <https://app.netlify.com> 新建站点，关联 GitHub 仓库
2. Build command: `npm run docs:build`
3. Publish directory: `docs/.vitepress/dist`

## 许可证

MIT License © {{AUTHOR_NAME_OR_DEFAULT}}