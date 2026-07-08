# {{SITE_NAME}}

{{SITE_DESCRIPTION}}

> 基于 **Vue 3 + Vite** 的 AI 工具导航站

## 快速开始

### 安装依赖

```bash
npm install
```

### 本地开发

```bash
npm run dev
```

打开浏览器访问：<http://localhost:5173>

### 构建静态文件

```bash
npm run build
```

构建产物在 `dist/` 目录。

### 预览构建产物

```bash
npm run preview
```

## 目录结构

```
.
├── index.html               # 入口 HTML
├── vite.config.js
├── package.json
├── src/
│   ├── main.js              # 入口 JS
│   ├── App.vue
│   ├── style.css
│   ├── router/
│   │   └── index.js
│   ├── views/
│   │   ├── Home.vue         # 首页（所有分类）
│   │   └── Category.vue     # 分类详情页
│   ├── components/
│   │   ├── HeaderNav.vue
│   │   └── ToolCard.vue
│   └── data/
│       └── tools.js         # ⚠️ 在这里编辑工具数据
└── README.md
```

## 如何添加 / 修改 AI 工具

编辑 `src/data/tools.js`：

```js
export const categories = [
  {
    id: 'your-category',     // 英文 ID，URL 用
    name: '你的分类',         // 显示名称
    icon: '🚀',              // emoji 图标
    tools: [
      {
        name: '工具名',
        desc: '工具描述',
        url: 'https://...'
      }
    ]
  }
]
```

保存后浏览器自动热更新。

## 自定义主题

修改 `src/style.css` 顶部的 CSS 变量：

```css
:root {
  --color-primary: #6366f1;     /* 主色 */
  --color-primary-dark: #4f46e5;
  --radius: 8px;                 /* 圆角 */
}
```

或修改 `src/App.vue`、`src/components/HeaderNav.vue` 等组件。

## 部署方式

### 方案 1：腾讯云 CloudBase 静态托管（推荐 · 国内访问快）

1. 打开 <https://console.cloud.tencent.com/tcb> 创建环境，记下环境 ID
2. 安装 CLI：`npm install -g @cloudbase/cli`
3. 登录：`tcb login`
4. 构建产物：`npm run build`
5. 上传：`tcb hosting deploy dist -e <环境ID>`
6. 拿到默认域名 `https://xxx.tcloudbaseapp.com`

### 方案 2：Vercel（推荐 · 海外访问）

1. 把代码 push 到 GitHub
2. 在 <https://vercel.com> 导入仓库
3. 框架自动识别（Framework: Vite, Build: `npm run build`, Output: `dist`）

### 方案 3：Netlify

1. 在 <https://app.netlify.com> 新建站点，关联 GitHub 仓库
2. Build command: `npm run build`
3. Publish directory: `dist`

### 方案 4：GitHub Pages

1. 修改 `vite.config.js`：`base: '/<仓库名>/'`
2. 安装：`npm install -D gh-pages`
3. 添加 script：`"deploy": "npm run build && gh-pages -d dist"`
4. 运行：`npm run deploy`

## 许可证

MIT License © {{AUTHOR_NAME_OR_DEFAULT}}