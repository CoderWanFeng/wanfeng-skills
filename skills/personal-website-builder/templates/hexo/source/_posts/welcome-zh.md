---
title: 博客使用指南
date: {{DATE_ISO}} 12:00:00
tags:
  - guide
  - getting-started
categories:
  - 入门
---

> [English version →](/{{DATE_PATH}}/welcome-en/)

# 欢迎来到你的新博客

这个博客基于 **Hexo + Butterfly 主题** 搭建。下面 3 步开始用：

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

参考 README.md 里的 Vercel / 腾讯云 CloudBase / GitHub Pages 步骤。

## 常用命令速查

| 命令 | 作用 |
|------|------|
| `npx hexo new "标题"` | 新建文章 |
| `npx hexo generate` | 生成静态文件 |
| `npx hexo server` | 启动本地预览 |
| `npx hexo deploy` | 部署（需先配 deploy 字段） |
| `npx hexo clean` | 清理缓存 |

## 写文章小贴士

- frontmatter 用 YAML 格式：`title` / `date` / `tags` / `categories`
- 图片放在同名的资源文件夹里（需 `_config.yml` 开启 `post_asset_folder: true`）
- 标签和分类会自动生成归档页

---

如有问题，查看 [Hexo 官方文档](https://hexo.io/docs/)。