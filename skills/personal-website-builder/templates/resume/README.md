# {{SITE_NAME}}

{{SITE_DESCRIPTION}}

> 单页个人简历 · 纯静态 HTML

## 如何使用

直接用浏览器打开 `index.html` 即可打印为 PDF。

## 自定义

修改 `index.html` 里的内容（个人信息、教育、经历、项目、技能）。

打印建议：浏览器 → 打印 → 保存为 PDF（勾选"背景图形"）。

## 部署方式

### 方案 1：Netlify 拖拽部署（最快）

1. 打开 <https://app.netlify.com/drop>
2. 把项目文件夹直接拖到页面
3. 立即获得一个临时 URL

### 方案 2：Vercel

1. push 到 GitHub
2. 在 Vercel 导入，选择 "Other"
3. 自动部署

### 方案 3：腾讯云 CloudBase

1. `tcb login`
2. `tcb hosting deploy . -e <环境ID>`

### 方案 4：GitHub Pages

1. 创建 `<用户名>.github.io` 仓库
2. push `index.html`
3. 访问 `https://<用户名>.github.io`

## 许可证

MIT License © {{AUTHOR_NAME_OR_DEFAULT}}