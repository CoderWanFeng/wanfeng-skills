# Vue 3 + Vite 详解

## 为什么选 Vue 3 + Vite（用于 AI 导航站）

- **Vue 3 组件化**：适合做工具卡片、分类筛选、搜索等复杂交互
- **Vite 极快**：HMR 几乎瞬时
- **Vue Router**：hash 模式部署简单
- **响应式数据**：改 `tools.js` 自动热更新

## 核心概念

- **src/main.js**：入口 JS
- **src/App.vue**：根组件
- **src/router/index.js**：路由
- **src/views/**：页面级组件
- **src/components/**：复用组件
- **src/data/tools.js**：⚠️ 工具数据在这里

## init-vue3.sh 做了什么

```bash
1. mkdir -p src/{router,views,components,data}
2. 复制所有 .vue / .js / .css 文件
3. npm install --save vue@^3 vue-router@^4
4. npm install --save-dev vite@^5 @vitejs/plugin-vue@^5
5. npm pkg set scripts.{dev,build,preview}
6. 替换占位符
7. 复制 README.md
8. git init + .gitignore
```

## 数据驱动：改 `src/data/tools.js`

```js
export const categories = [
  {
    id: 'chat',
    name: 'AI 对话',
    icon: '💬',
    tools: [
      {
        name: '工具名',
        desc: '工具描述',
        url: 'https://...'
      }
      // 添加更多
    ]
  }
  // 添加更多分类
]
```

保存后浏览器自动热更新。

## 已知坑

### 1. 默认用 hash 模式

`createWebHashHistory()` → URL 是 `/#/category/chat`

**优势**：部署到任何静态托管都直接工作，不需要 fallback 配置。
**劣势**：URL 不漂亮（带 `#`）。

如果想用 history 模式：
```js
import { createWebHistory } from 'vue-router'
// ...
history: createWebHistory(),
```
**但**部署到 CloudBase / Netlify 需配 SPA fallback（所有未知路径重定向到 index.html）。

### 2. base 路径

模板里 `base: './'`。这意味着相对路径，可以部署到任意子路径。
如果要部署到 `https://xxx.com/blog/`：
```js
base: '/blog/'
```

### 3. SCSS / Less 等预处理器

默认 Vite 不带。如果要用：
```bash
npm install --save-dev sass
```
然后在组件里 `<style lang="scss">`。

### 4. 暗色模式

模板用 CSS `@media (prefers-color-scheme: dark)`。如需手动切换：
```bash
npm install --save @vueuse/core
```
然后用 `useDark()` / `useToggle()`。

## 升级版本

```bash
npm install --save vue@latest vue-router@latest
npm install --save-dev vite@latest @vitejs/plugin-vue@latest
```

升级前看各包的 CHANGELOG。

## 进一步学习

- [Vue 3 文档](https://cn.vuejs.org/)
- [Vue Router 4 文档](https://router.vuejs.org/zh/)
- [Vite 文档](https://cn.vitejs.dev/)