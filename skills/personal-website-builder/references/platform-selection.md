# 部署平台选择决策树

> 当用户对部署平台没概念时，根据他的情况自动推荐。

## 自动选择优先级（v2 - 2026-07）

`scripts/detect-deploy-tools.sh` 按以下顺序推荐：

```
用户没指定平台（DEPLOY_PLATFORM_OVERRIDE 未设）
│
├─ 中国时区 + CloudBase 已登录？→ CloudBase（国内访问最快）
│
├─ Netlify CLI 已安装？→ Netlify（未登录自动匿名模式）
├─ Vercel CLI 已安装？→ Vercel
├─ Cloudflare (wrangler) 已安装？→ Cloudflare
├─ CloudBase CLI 已安装？→ CloudBase（非例外条件）
├─ Surge CLI 已安装？→ Surge
├─ gh CLI 已安装？→ GitHub Pages
│
└─ 都没装 → 推荐 Netlify（装上就用，最简单）
```

**关键点**：
- 通用 6 个平台**只看「已安装」**作为信号（不要求已登录）
- 唯独 CloudBase **特殊**：没有匿名模式，没登录部署不了。所以例外条件需要 `installed + logged_in`
- Netlify 即使未登录也能走 `--allow-anonymous` 路径

## 按用户场景的具体推荐

## 按用户场景的具体推荐

### 场景 1：第一次部署 / 临时分享给朋友

**推荐**：Netlify 匿名

```bash
./scripts/deploy.sh hexo /path/to/blog --platform=netlify --anonymous
```

**原因**：
- ✅ 0 账号
- ✅ 1 分钟拿到 URL
- ✅ 真域名（`*.netlify.app`）
- ⚠️ 1 小时内可认领转正

### 场景 2：5 分钟内部测试

**推荐**：Surge

```bash
./scripts/deploy.sh hexo /path/to/blog --platform=surge --domain=mytest
```

**原因**：
- ✅ 5 秒上线
- ✅ 首次免注册
- ⚠️ 慢 + 后续部署要登录

### 场景 3：国内生产环境

**推荐**：CloudBase

```bash
./scripts/deploy.sh hexo /path/to/blog --platform=cloudbase --env-id=xxx
```

**原因**：
- ✅ 国内访问快
- ✅ 免费额度够个人项目
- ⚠️ 需实名认证（几小时）+ 环境 ID

### 场景 4：全球生产 / 长期运营

**推荐**：Cloudflare Pages

```bash
./scripts/deploy.sh hexo /path/to/blog --platform=cloudflare
```

**原因**：
- ✅ 全球 CDN（300+ 节点）
- ✅ 无限流量
- ✅ 自动 HTTPS + Brotli
- ⚠️ 需 API token

### 场景 5：Next.js / 复杂 SPA

**推荐**：Vercel

```bash
./scripts/deploy.sh hexo /path/to/blog --platform=vercel
```

**原因**：
- ✅ Next.js 一等公民
- ✅ Edge Functions
- ⚠️ 国内访问慢

### 场景 6：开源项目文档 / 个人主页

**推荐**：GitHub Pages

```bash
./scripts/deploy.sh hexo /path/to/blog --platform=github_pages --repo=blog
```

**原因**：
- ✅ 完全免费
- ✅ 跟 GitHub 仓库绑定
- ⚠️ 公开仓库才能用

## 按框架的推荐

| 框架 | 推荐平台 | 原因 |
|------|---------|------|
| Hexo（博客） | Netlify / Cloudflare | 静态站，平台无差别 |
| VitePress（知识库） | Cloudflare / Vercel | 文档站通常需要搜索 + 全球访问 |
| Vue 3（AI 导航） | Netlify / Vercel | SPA 需要 history fallback，平台支持好 |
| Hugo | Cloudflare / Netlify | Hugo 输出静态，平台无差别 |
| 作品集 | Netlify 拖拽 | 纯 HTML，最快 |
| 简历 | Netlify 拖拽 | 单文件，零配置 |

## 平台限制速查

### Netlify
- 流量：100GB/月
- 构建：300 分钟/月
- 团队：5 人
- 单文件：≤ 100MB

### Surge
- 流量：无限制
- 项目数：无限制
- 单文件：≤ 400MB
- 历史版本：最多 50 个

### Cloudflare Pages
- 构建：500 次/月（Free）
- 流量：无限
- 文件：≤ 25MB / 文件
- Functions：100k requests/day（Free）

### CloudBase
- 存储：5GB
- 流量：5GB/月
- CDN：5GB/月
- 超额按量计费

### Vercel
- 流量：100GB/月
- 构建：100 小时/月
- Serverless：100GB-小时

### GitHub Pages
- 仓库：1GB
- 流量：100GB/月
- 单文件：≤ 100MB

## 何时升级

如果遇到以下情况，考虑升级平台或加 CDN：

| 现象 | 原因 | 解法 |
|------|------|------|
| 国内访问慢 | 没有国内 CDN | 加 CloudBase 或腾讯云 EdgeOne |
| 月流量超 100GB | 内容多 | 升级到 Cloudflare Pro（$20/月，unlimited） |
| 构建失败 | 内存不够 | Vercel Pro（更多资源） |
| 需要后端 | 纯静态不够 | 改用 Vercel + Functions / Cloudflare Workers |

## 一句话总结

> **不熟就 Netlify 匿名**（最稳），**国内就 CloudBase**（最快），**长期就 Cloudflare**（最省）。