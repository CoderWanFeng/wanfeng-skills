# 部署详解

> 6 个部署平台，按使用场景排序。所有平台都支持**命令行部署**，不需要手点控制台。

## 平台总览

| 平台 | 匿名部署 | 实名认证 | 免费额度 | 国内速度 | 适用场景 |
|------|---------|---------|---------|---------|---------|
| **Netlify** | ✅ `--allow-anonymous` | ❌ | 100GB/月 | 一般 | ⭐ 临时演示 / 快速分享 |
| **Surge.sh** | ✅ 首次免注册 | ❌ | 无限 `.surge.sh` | 慢 | ⭐ 极简测试 |
| **Cloudflare Pages** | ❌ | ❌ | 500 构建/月，无限流量 | ✅ 快 | 生产级，全球 CDN |
| **腾讯云 CloudBase** | ❌ | ✅ | 免费配额 | ✅✅ 最快 | 国内生产 |
| **Vercel** | ❌ | ❌ | 100GB/月 | 慢 | Next.js / 现代化 |
| **GitHub Pages** | ❌ | ❌ | 100GB/月 | 慢 | 纯静态免费 |

## 平台自动选择

```bash
./scripts/detect-deploy-tools.sh
```

返回 JSON，根据**已安装 CLI + 环境变量 + 登录状态 + 时区**推荐：

```json
{
  "recommended": "netlify",
  "reason": "Netlify 支持匿名部署（1 小时内认领）"
}
```

**优先级**：
1. 用户显式 `--platform=xxx`
2. `CLOUDFLARE_API_TOKEN` 已设置 → Cloudflare
3. `tcb` 已登录 + 中国时区 → CloudBase
4. Vercel 已登录 → Vercel
5. Netlify 已安装 → Netlify（默认）
6. Surge 已安装 → Surge
7. 默认 → Netlify（最稳）

## 通用流程

```bash
# 1. 跑 init 脚本（一次性）
./scripts/init-hexo.sh /path/to/blog "我的博客" "记录学习" "张三" "zhangsan"

# 2. 编辑内容
cd /path/to/blog
npx hexo new "我的第一篇文章"

# 3. 本地预览
npx hexo server  # 浏览器看 http://localhost:4000

# 4. 构建 + 优化 + 部署（一键）
./scripts/deploy.sh hexo /path/to/blog
# → 自动检测平台 + 优化 + 部署 + 验证 + 保存状态
```

---

## 方案 1：Netlify（推荐 · 零门槛）

### 优势
- ✅ **支持匿名部署**（`--allow-anonymous`）—— 不需要账号
- ✅ 拿到真域名 `*.netlify.app`，不是 IP
- ✅ 1 小时内用户可去 console 认领转正
- ✅ 全球 CDN + 自动 HTTPS

### 安装 + 部署

```bash
# 1. 安装 CLI（一次性）
npm install -g netlify-cli

# 2. 匿名部署
./scripts/deploy.sh hexo /path/to/blog --platform=netlify --anonymous

# 输出：
# 🌐 部署成功！
#    URL: https://xxx-abc123.netlify.app
#    ⚠️  1 小时内去 https://app.netlify.com 登录认领，否则会被清理
```

### 升级到正式账号

1. 打开 https://app.netlify.com，用邮箱注册
2. 找到「Unclaimed deployments」
3. 点「Claim」认领
4. 之后用 `netlify login` 登录，部署会到你的账号下

### 持续部署

认领后，关联 GitHub 仓库，每次 push 自动重新部署。

---

## 方案 2：Surge.sh（极简测试）

### 优势
- ✅ 首次免注册
- ✅ 5 秒上线
- ✅ 适合快速 demo / 临时分享

### 安装 + 部署

```bash
# 1. 安装（一次性）
npm install -g surge

# 2. 部署
./scripts/deploy.sh hexo /path/to/blog --platform=surge --domain=myblog
# 首次会提示输入 email + password
# 之后会自动登录

# 输出：
# 🌐 部署成功！
#    URL: https://myblog.surge.sh
```

### 限制
- 慢（无国内 CDN）
- 每次 re-deploy 需要先登录

---

## 方案 3：Cloudflare Pages（生产级 · 全球）

### 优势
- ✅ 全球 CDN（300+ 节点）
- ✅ 无限流量
- ✅ 自动 Brotli 压缩
- ✅ HTTP/3 支持

### 安装 + 配置

```bash
# 1. 安装 wrangler（一次性）
npm install -g wrangler

# 2. 获取 API token
# 打开 https://dash.cloudflare.com/profile/api-tokens
# Create Token → Edit Cloudflare Pages template
# 复制 token

# 3. 设置环境变量
export CLOUDFLARE_API_TOKEN=你的token

# 4. 部署
./scripts/deploy.sh hexo /path/to/blog --platform=cloudflare
# 项目名自动从目录名推断，或用 --domain=myblog 指定
```

### 持续部署
- 关联 GitHub 仓库后，push 触发自动部署
- Preview deployments：每个 PR 一个 URL

---

## 方案 4：腾讯云 CloudBase（国内生产）

### 优势
- ✅ 国内访问最快
- ✅ 免费额度够个人项目
- ✅ 静态托管 + HTTPS + CDN 一体

### 前置准备（用户手动操作）
1. 打开 https://console.cloud.tencent.com/tcb 注册
2. 完成实名认证（个人项目几小时）
3. 创建 CloudBase 环境（选「免费配额」）
4. 记下环境 ID（形如 `myenv-1234567890`）

### 部署

```bash
# 1. 安装 tcb CLI（一次性）
npm install -g @cloudbase/cli

# 2. 登录（桌面环境）
tcb login

# Headless / SSH 环境：
# 1. 去 https://console.cloud.tencent.com/cam/capi 创建 API 密钥
# 2. tcb login --apiKey
# 3. 输入 SecretId 和 SecretKey

# 3. 部署
./scripts/deploy.sh hexo /path/to/blog --platform=cloudbase --env-id=myenv-1234567890
```

### 默认域名
- 形如 `https://myenv-1234567890-1234567890.tcloudbaseapp.com`
- 控制台 → 静态托管 → 默认域名 查看

### 自定义域名
- 控制台 → 静态托管 → 自定义域名 → 添加
- 国内节点**需 ICP 备案**（海外节点免备案）

---

## 方案 5：Vercel（海外 · 现代化）

### 优势
- ✅ 部署 Next.js / Vue / React 都很顺
- ✅ 全球 CDN
- ✅ Preview deployments（每个 PR 一个 URL）

### 安装 + 部署

```bash
# 1. 安装（一次性）
npm install -g vercel

# 2. 登录（桌面环境）
vercel login

# Headless：export VERCEL_TOKEN=你的token

# 3. 部署
./scripts/deploy.sh hexo /path/to/blog --platform=vercel
```

---

## 方案 6：GitHub Pages（免费 · 静态）

### 优势
- ✅ 完全免费
- ✅ 适合个人项目 / 开源项目文档

### 限制
- 公开仓库才能用 Pages（私有仓库需 GitHub Pro）
- 国内访问慢

### 安装 + 部署

```bash
# 1. 安装 gh CLI（一次性）
brew install gh   # macOS
# Linux: 见 https://github.com/cli/cli#installation

# 2. 登录
gh auth login

# 3. 部署
./scripts/deploy.sh hexo /path/to/blog --platform=github_pages --repo=myblog
# 自动创建仓库（如果不存在）+ 推送到 gh-pages 分支
```

---

## 重新部署

第一次部署后，状态保存在 `<项目>/.deploy-state.json`：

```json
{
  "platform": "netlify",
  "url": "https://xxx.netlify.app",
  "deployed_at": "2026-07-04T22:00:00Z",
  "framework": "hexo",
  "dist_dir": "/path/to/blog/public"
}
```

用户说「重新部署」时：

```bash
# 直接跑同一条命令
./scripts/deploy.sh hexo /path/to/blog
# 跳过平台选择，直接用上次的状态
```

## 部署后自动优化

`deploy.sh` 默认会在部署前调 `optimize-all.sh`：
- PNG/JPG → WebP（节省 30%）
- 资源压缩
- 输出到 `dist-optimized/`

跳过：加 `--no-optimize`。

## Scale 优化清单

详见 `references/optimization.md`：
- 部署平台自带：CDN / Brotli / HTTP/3 / 静态资源永久缓存
- 构建期：图片 WebP / Tree shaking / 代码分割
- 内容期：lazy load / 字体 preload / 关键 CSS 内联

## 选哪个？

| 你的情况 | 推荐 |
|---------|------|
| 第一次部署 / 临时分享 | Netlify 匿名 |
| 快速 5 秒测试 | Surge |
| 国内用户为主 | CloudBase |
| 全球用户 + 长期 | Cloudflare Pages |
| 已有 Vercel 账号 | Vercel |
| 已有 GitHub 仓库 | GitHub Pages |