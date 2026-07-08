# {{SITE_NAME}}

{{SITE_DESCRIPTION}}

> 个人作品集 · 纯静态 HTML

## 如何使用

直接双击 `index.html` 用浏览器打开即可。

修改 `index.html` 里的内容来更新你的项目展示。

## 部署方式

### 方案 1：腾讯云 CloudBase 静态托管（推荐 · 国内访问快）

1. 打开 <https://console.cloud.tencent.com/tcb> 创建环境，记下环境 ID
2. 安装 CLI：`npm install -g @cloudbase/cli`
3. 登录：`tcb login`
4. 上传整个项目目录：`tcb hosting deploy . -e <环境ID>`

### 方案 2：Netlify 拖拽部署（最快）

1. 打开 <https://app.netlify.com/drop>
2. 把项目文件夹直接拖到页面
3. 立即获得一个临时 URL

### 方案 3：Vercel

1. 把项目 push 到 GitHub
2. 在 <https://vercel.com> 导入
3. 框架选择 "Other"，直接部署

### 方案 4：GitHub Pages

1. 创建一个 `<用户名>.github.io` 仓库
2. 把 `index.html` 等文件 push 上去
3. 访问 `https://<用户名>.github.io`

## 定制

- 修改 `index.html` 里的项目卡片
- 修改 `style.css` 调整颜色和布局
- 替换 `images/` 里的图片

## 许可证

MIT License © {{AUTHOR_NAME_OR_DEFAULT}}