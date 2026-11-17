# 作品集（纯 HTML）详解

## 为什么选纯 HTML

- **零构建**：双击 `index.html` 就能看
- **部署简单**：上传到任何静态托管都行
- **加载快**：没有 JS 框架开销
- **可定制**：HTML + CSS 完全可控

## 适用场景

- 作品数量固定（< 20 个）
- 不需要搜索 / 分类
- 想要极简风格

## init-portfolio.sh 做了什么

```bash
1. mkdir -p projects
2. cp {index.html, style.css, README.md, .gitignore}
3. 替换占位符
4. git init
```

## 模板结构

```html
<header class="hero">
  <h1>网站名</h1>
  <p class="tagline">描述</p>
  <p class="author">作者</p>
</header>

<section class="about">
  <h2>关于我</h2>
  <p>自我介绍</p>
</section>

<section class="projects">
  <h2>项目作品</h2>
  <div class="project-grid">
    <article class="project-card">...</article>
  </div>
</section>

<section class="contact">
  <h2>联系我</h2>
</section>
```

## 自定义

### 改颜色

`style.css` 顶部 CSS 变量：

```css
:root {
  --color-primary: #6366f1;     /* 主色 */
  --color-primary-dark: #4f46e5;
  --color-bg: #ffffff;
  --color-bg-alt: #f9fafb;
  --color-text: #111827;
  --radius: 12px;                /* 圆角大小 */
}
```

### 改项目卡片

在 `index.html` 找到 `<article class="project-card">`，修改：
- `class="project-image" style="background: ..."`：项目封面（可用 CSS 渐变 / 在线图片）
- `<h3>`：项目标题
- `<p>`：项目描述
- `.project-tags`：技术标签
- `.project-links`：演示 / 源码链接

### 加项目

复制一个 `<article class="project-card">...</article>` 块，粘贴修改。

### 加图片

把图片放到 `projects/` 目录，然后：
```html
<div class="project-image">
  <img src="projects/my-project.png" alt="项目截图">
</div>
```
需要在 `style.css` 里加：
```css
.project-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

## 暗色模式

模板已经用 CSS `@media (prefers-color-scheme: dark)` 自动适配系统设置。

## 部署

最简单的方案：Netlify 拖拽。

1. 打开 <https://app.netlify.com/drop>
2. 拖整个项目文件夹
3. 拿到临时 URL

## 升级考虑

如果你之后：
- 项目数 > 20 → 考虑升级到 VitePress（自动列表 + 搜索）
- 想加评论 / 访问统计 → 仍是纯 HTML，加第三方 JS 即可
- 想做成博客 → 升级到 Hexo

## 进一步学习

- [MDN HTML 教程](https://developer.mozilla.org/zh-CN/docs/Learn/HTML)
- [CSS Tricks](https://css-tricks.com/)（英文）
- [现代 CSS 布局](https://moderncss.dev/)