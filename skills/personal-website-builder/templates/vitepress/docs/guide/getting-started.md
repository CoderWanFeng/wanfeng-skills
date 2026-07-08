# 入门指南

> [English version →](/en/guide/getting-started)

# 欢迎来到 {{SITE_NAME}}

这是一个基于 **VitePress** 构建的知识库。下面 3 步开始用：

## 1. 本地预览

```bash
npm run docs:dev
```

浏览器打开 <http://localhost:5173>

## 2. 写第一篇文档

在 `docs/` 下新建 `.md` 文件，例如 `docs/guide/my-first-doc.md`：

```markdown
# 我的第一篇文档

这是正文内容。
```

然后在 `docs/.vitepress/config.mts` 的 `sidebar` 里添加导航：

```ts
sidebar: [
  {
    text: '指南',
    items: [
      { text: '我的第一篇文档', link: '/guide/my-first-doc' }
    ]
  }
]
```

## 3. 部署上线

参考 README.md 里的 Vercel / 腾讯云 CloudBase / GitHub Pages 步骤。

## VitePress 优势

- **极快**：基于 Vite，HMR 几乎是即时的
- **现代**：Vue 3 + Vite + TypeScript
- **Markdown 优先**：用熟悉的 Markdown 写文档
- **内置搜索**：本地全文搜索，无需 Algolia 等服务

## 常用命令

| 命令 | 作用 |
|------|------|
| `npm run docs:dev` | 启动开发服务器 |
| `npm run docs:build` | 构建静态文件 |
| `npm run docs:preview` | 预览构建产物 |

## 下一步

- 阅读 [VitePress 官方文档](https://vitepress.dev/)
- 探索 [Markdown 扩展语法](https://vitepress.dev/guide/markdown)
- 自定义 [主题配置](https://vitepress.dev/reference/site-config)