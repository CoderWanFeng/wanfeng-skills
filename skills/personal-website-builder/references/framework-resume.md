# 简历站（单文件 HTML）详解

## 为什么选单文件 HTML

- **零依赖**：打开就能看，能打印为 PDF
- **打印友好**：内置 `@media print` 样式
- **隐私可控**：不上传也能分享（PDF / 截图）
- **修改容易**：所有内容在一个文件

## 适用场景

- 找工作用
- 留作个人品牌
- 不想被 GitHub Pages 复杂部署卡住

## init-resume.sh 做了什么

```bash
1. cp {index.html, README.md, .gitignore}
2. 替换占位符
3. git init
```

## 模板结构

```html
<header>          <!-- 姓名 + 一句话定位 + 联系方式 -->
<section>个人简介  <!-- 3-4 句话 -->
<section>工作经历  <!-- 时间倒序 -->
<section>教育背景
<section>项目经历  <!-- 重要项目 + 量化成果 -->
<section>技能     <!-- 网格展示 + 熟练度 -->
<section>荣誉/证书
```

## 自定义清单

修改 `index.html` 时，按顺序检查：

### 必改项
- [ ] 邮箱 / 电话 / 城市
- [ ] 个人简介（3-4 句话）
- [ ] 工作经历（每段 2-4 个 bullet）
- [ ] 项目经历（突出个人贡献 + 量化成果）
- [ ] 技能（分熟练度）

### 建议保留
- [ ] GitHub 链接（如有公开代码）
- [ ] 个人网站（如有）

### 可选
- [ ] 教育背景：GPA / 主修课程
- [ ] 荣誉 / 证书

## 写简历的 5 个原则

1. **量化成果**：不用「优化了性能」，用「首屏加载从 3s 降到 1.2s」
2. **动词开头**：「负责 / 主导 / 设计 / 优化 / 引入 / 重构」
3. **STAR 法则**：情境 (Situation) → 任务 (Task) → 行动 (Action) → 结果 (Result)
4. **针对 JD**：每个岗位要微调简历，强调相关经验
5. **一页为佳**：少于 10 年经验保持一页

## 打印为 PDF

1. 用 Chrome / Safari 打开 `index.html`
2. `Cmd/Ctrl + P` 打开打印对话框
3. 目标：保存为 PDF
4. 边距：默认 / 自定义
5. **勾选「背景图形」**（重要：让 CSS 颜色保留）
6. 保存

## 在线版本 vs PDF

- **PDF**：投简历用，HR 不会点链接
- **在线版**：放 GitHub / 个人网站，加深印象

## 暗色模式

模板用 `@media print` 区分屏幕 / 打印。屏幕下：
- 默认浅色
- 系统暗色时自动暗色（@media prefers-color-scheme: dark）

打印时强制浅色（节省墨水 + 打印清晰）。

## 部署

最快：Netlify 拖拽整个文件夹。

或者：
- CloudBase: `tcb hosting deploy . -e <环境ID>`
- GitHub Pages: push 到 `<username>.github.io`
- Vercel: 关联 GitHub 仓库

## 进一步优化

如果你想升级到「动态简历」（有访客统计、联系表单）：

```html
<form action="https://formspree.io/f/xxx" method="POST">
  <input name="email" type="email" required>
  <textarea name="message" required></textarea>
  <button>发送</button>
</form>
```

Formspree / Netlify Forms / Tally 等都提供免费表单后端。

## 反爬（可选）

如果不想被搜索引擎收录，在 `<head>` 加：
```html
<meta name="robots" content="noindex">
```

## 进一步学习

- [Google 简历指南](https://www.google.com/search/howsearchworks/crawling-indexing/)
- [Markdown 简历模板](https://github.com/therealsaumil/resume/)（参考结构）