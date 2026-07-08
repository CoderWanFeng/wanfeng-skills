---
title: How to Use This Blog
date: {{DATE_ISO}} 12:00:00
tags:
  - guide
  - getting-started
lang: en
---

# Welcome to Your New Blog

This blog is built with **Hexo + Butterfly theme**. Get started in 3 steps:

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

See the Vercel / Tencent CloudBase / GitHub Pages section in README.md.

## Common commands

| Command | Description |
|---------|-------------|
| `npx hexo new "title"` | Create new post |
| `npx hexo generate` | Generate static files |
| `npx hexo server` | Start local server |
| `npx hexo deploy` | Deploy (configure `deploy` first) |
| `npx hexo clean` | Clean cache |

## Writing tips

- Frontmatter in YAML format: `title` / `date` / `tags` / `categories`
- Put images in a same-named asset folder (enable `post_asset_folder: true` in `_config.yml`)
- Tags and categories auto-generate archive pages

---

For more, see [Hexo docs](https://hexo.io/docs/).