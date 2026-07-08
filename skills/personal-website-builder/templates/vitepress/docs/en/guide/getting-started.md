---
title: Getting Started
---

# Getting Started

> [中文版 →](/guide/getting-started)

# Welcome to {{SITE_NAME}}

This knowledge base is built with **VitePress**. Get started in 3 steps:

## 1. Run locally

```bash
npm run docs:dev
```

Open <http://localhost:5173>

## 2. Write your first doc

Create `.md` files under `docs/`, e.g. `docs/guide/my-first-doc.md`:

```markdown
# My First Doc

Content here.
```

Then add it to `docs/.vitepress/config.mts`:

```ts
sidebar: [
  {
    text: 'Guide',
    items: [
      { text: 'My First Doc', link: '/guide/my-first-doc' }
    ]
  }
]
```

## 3. Deploy

See README.md for Vercel / Tencent CloudBase / GitHub Pages options.

## Why VitePress?

- **Fast**: Vite-based, HMR is near-instant
- **Modern**: Vue 3 + Vite + TypeScript
- **Markdown-first**: Write in familiar Markdown
- **Built-in search**: Local full-text search, no Algolia needed

## Common commands

| Command | Description |
|---------|-------------|
| `npm run docs:dev` | Start dev server |
| `npm run docs:build` | Build static files |
| `npm run docs:preview` | Preview build output |

## Next steps

- Read [VitePress docs](https://vitepress.dev/)
- Explore [Markdown extensions](https://vitepress.dev/guide/markdown)
- Customize [theme config](https://vitepress.dev/reference/site-config)