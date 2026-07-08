# Scale 优化指南

> 个人网站从「能访问」到「极致体验」需要做的优化。分 3 个层级：部署平台自带（零成本）→ 构建期 → 内容期。

## 🏆 Tier 0：部署平台自带（0 成本，自动启用）

所有现代部署平台（Netlify / Cloudflare / Vercel）都默认启用以下优化：

| 优化 | 效果 | 触发条件 |
|------|------|---------|
| **全球 CDN** | 首屏 < 100ms（任何地区） | 所有平台 |
| **Brotli 压缩** | 体积 -20% vs gzip | Cloudflare / Vercel / Netlify |
| **HTTP/3 (QUIC)** | TLS 握手省 1 RTT | Cloudflare / Vercel |
| **HTTP/2 多路复用** | 并发请求不阻塞 | 全平台 |
| **TLS 1.3** | 握手省 1 RTT | 全平台 |
| **自动 HTTPS** | 0 配置 | 全平台 |
| **静态资源永久缓存** | 二次访问 0 字节 | 需要自己设 Cache-Control |

**你不需要做任何事**。选择上述平台之一，自动获得。

---

## ⚡ Tier 1：构建期优化（推荐，节省 30-50%）

### 1.1 图片优化（最大收益）

**问题**：图片通常占页面体积的 50-80%。

**优化**：
- PNG/JPG → **WebP**（体积 -30%）
- PNG → **AVIF**（体积 -50%，但兼容性差）
- 响应式图片（`srcset`，移动端流量 -50%）
- lazy load（屏外图不下载）

**本 skill 已做**：`optimize-images.sh` 自动：
- 用 sharp 转 WebP
- 保留原 PNG 作为 fallback
- 更新 HTML 引用

**手动补充**（如果用 Hexo / VitePress 写作）：
```markdown
![alt](image.png)
<!-- 改成 -->
<picture>
  <source srcset="image.webp" type="image/webp">
  <img src="image.png" alt="alt" loading="lazy">
</picture>
```

### 1.2 JS / CSS 优化

**问题**：未压缩的 JS/CSS 比 gzip 后大 3-5 倍。

**本 skill 框架默认**：
- Hexo：构建时 minify
- VitePress / Vue 3 / Hugo：构建时 minify
- 纯 HTML：CSS 已写在 style.css（小项目不需要）

**额外优化**（如需进一步压缩）：
```bash
# 高级 HTML 压缩（作品集/简历）
npm install -g html-minifier-terser
html-minifier-terser --collapse-whitespace --minify-css index.html -o index.min.html
```

### 1.3 代码分割（Vue 3 / 复杂 SPA）

**问题**：单页应用首屏加载所有 JS（>500KB）。

**优化**：路由级代码分割
```js
// Vue Router 懒加载
const Home = () => import('./views/Home.vue')
const Category = () => import('./views/Category.vue')
```

**效果**：首屏 JS 减少 60%。

### 1.4 字体优化

**问题**：中文字体动辄 5-10MB。

**优化**：
1. **子集化**：只打包实际用到的字符（节省 80%）
   ```bash
   pip install fonttools
   pyftsubset font.ttf --text="你好世界" --output-file=font.min.woff2
   ```
2. **格式转换**：TTF → WOFF2（体积 -50%）
3. **预加载**：`<link rel="preload" as="font" crossorigin>`

---

## 🎨 Tier 2：内容期优化（写文章时做）

### 2.1 图片 lazy load

**问题**：屏外图片也下载，浪费流量。

**优化**：
```html
<img src="cat.jpg" alt="猫" loading="lazy" decoding="async">
```

**收益**：首屏跳过 70% 图片。

### 2.2 字体 preload

**问题**：字体文件阻塞首字渲染（FOIT）。

**优化**：
```html
<head>
  <link rel="preload" href="font.woff2" as="font" type="font/woff2" crossorigin>
</head>
```

**收益**：首字渲染早 200ms。

### 2.3 关键 CSS 内联

**问题**：CSS 文件请求阻塞渲染。

**优化**（Vue 3 / VitePress）：
```js
// vite.config.js
import criticalCss from 'vite-plugin-critical-css'

export default {
  plugins: [
    criticalCss({ /* ... */ })
  ]
}
```

**收益**：首屏 0 个 CSS 请求。

### 2.4 DNS 预解析 + Preconnect

**优化**：
```html
<link rel="dns-prefetch" href="//cdn.example.com">
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
```

**收益**：跨域请求快 100ms。

---

## 🇨🇳 Tier 3：国内特化（仅国内用户需要）

### 3.1 ICP 备案

**问题**：国内服务器绑域名必须备案（法律要求）。

**流程**（约 1-2 周）：
1. 买服务器（阿里云 / 腾讯云）
2. 提交 ICP 备案申请
3. 等审核通过
4. 域名解析到国内节点

**避坑**：
- 个人备案比企业简单
- 用海外节点可免备案（Cloudflare 亚太节点、CloudBase 海外节点）

### 3.2 多 CDN 部署

**问题**：单 CDN 在某些地区慢。

**方案**：
- 国内：腾讯云 CloudBase
- 海外：Cloudflare Pages
- DNS 智能解析：阿里云 DNS / Cloudflare DNS

### 3.3 BGP 优化

**工具**：腾讯云 EdgeOne、阿里云 DCDN

**收益**：国内首屏 < 50ms。

---

## 性能指标参考

| 指标 | 优秀 | 及格 | 需优化 |
|------|------|------|--------|
| **首屏渲染** | < 1s | 1-3s | > 3s |
| **LCP**（最大内容渲染） | < 2.5s | 2.5-4s | > 4s |
| **FID**（首次输入延迟） | < 100ms | 100-300ms | > 300ms |
| **CLS**（累计布局偏移） | < 0.1 | 0.1-0.25 | > 0.25 |
| **页面总大小** | < 1MB | 1-3MB | > 3MB |

**测试工具**：
- https://pagespeed.web.dev/（Google）
- https://gtmetrix.com/
- Chrome DevTools → Lighthouse

## 优化优先级（推荐执行顺序）

1. **选好部署平台**（Cloudflare / Netlify / Vercel）→ Tier 0 全部解锁
2. **跑 `optimize-all.sh`** → Tier 1.1 + 1.2 自动做
3. **写文章时**用 `loading="lazy"` → Tier 2.1
4. **加 CDN** → Tier 3（仅国内用户）

## 进一步学习

- [web.dev/learn/performance](https://web.dev/learn/performance/)（Google 官方）
- [Lighthouse 文档](https://developer.chrome.com/docs/lighthouse/overview/)
- [图片优化指南](https://web.dev/articles/serve-images-webp)