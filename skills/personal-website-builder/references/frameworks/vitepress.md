# VitePress 框架详解

## 为什么选 VitePress

- **Vite 驱动**：HMR 几乎瞬时，构建速度极快
- **Vue 3 + TypeScript**：现代化栈
- **Markdown 增强**：代码高亮、行号、容器、徽章、LaTeX、Mermaid 都内置
- **本地搜索**：无需 Algolia 即可用
- **SEO 友好**：自动生成 sitemap、SSG

## 核心概念

- **docs/**：所有源文件（Markdown）
- **docs/.vitepress/config.mts**：站点配置（标题、导航、侧边栏）
- **docs/.vitepress/dist/**：构建产物
- **docs/public/**：静态资源（图片、字体等，URL 根路径）

## init-vitepress.sh 做了什么

```bash
1. mkdir -p docs/.vitepress docs/guide docs/en/guide docs/public
2. npm install --save-dev vitepress@^1.5.0 vue@^3.5.0
3. npm pkg set scripts.docs:dev="vitepress dev docs" 等
4. 复制 config.mts / index.md / 指南（中英）模板
5. 替换占位符
6. 复制 README.md
7. git init + .gitignore
```

## 关键配置项

### 顶部导航

```ts
nav: [
  { text: '首页', link: '/' },
  { text: '指南', link: '/guide/getting-started' },
  { text: 'GitHub', link: 'https://github.com/xxx' }
]
```

### 侧边栏

```ts
sidebar: [
  {
    text: '入门',
    items: [
      { text: '开始使用', link: '/guide/getting-started' },
      { text: '进阶', link: '/guide/advanced' }
    ]
  }
]
```

### 多语言

```ts
locales: {
  'zh-CN': {
    label: '简体中文',
    lang: 'zh-CN',
    themeConfig: { /* ... */ }
  },
  'en': {
    label: 'English',
    lang: 'en',
    themeConfig: { /* ... */ }
  }
}
```

## 已知坑

### 1. dead link 检查太严格

VitePress 1.6+ 默认严格检查链接。`http://localhost:5173` 这种本地地址会被误判。

**修复**：
```ts
ignoreDeadLinks: [/^http:\/\/localhost:/]
```

本 skill 已经在模板里加了这个配置。

### 2. 本地搜索不支持中文

VitePress 1.x 的本地搜索默认不支持中文。选项：
- 用 Algolia DocSearch（需申请，免费）
- 接受英文搜索（中文文档至少能搜到英文单词）
- 用第三方搜索如 `vitepress-plugin-search`

### 3. cleanUrls 需要服务器支持

`cleanUrls: true` 会去掉 URL 里的 `.html`。需要服务器支持 fallback：
- Vercel / Netlify：自动支持
- Nginx：需配 `try_files $uri $uri/ $uri.html /404.html`
- CloudBase：默认支持

### 4. 构建后路径问题

本地 dev 用 `/guide/foo`，build 后用 `/guide/foo.html`（如果 cleanUrls 关）。
模板里 `cleanUrls: true`，需要确保部署环境支持。

## Markdown 扩展

VitePress 内置：

````md
::: tip 提示
这是提示容器
:::

::: warning 警告
这是警告
:::

```js{1,3-5}
function highlight() {
  // 第 1 行高亮
  // 第 3-5 行高亮
  return true
}
```

$$E = mc^2$$

```mermaid
graph LR
  A --> B
```
````

详见 [Markdown 扩展](https://vitepress.dev/guide/markdown)。

## 升级版本

```bash
npm install --save-dev vitepress@latest
```

升级前看 [CHANGELOG](https://github.com/vuejs/vitepress/blob/main/CHANGELOG.md)。

## 进一步学习

- [VitePress 官方文档](https://vitepress.dev/)
- [站点配置参考](https://vitepress.dev/reference/site-config)
- [主题配置参考](https://vitepress.dev/reference/theme-config)