# 故障排查

> 常见问题与解决方案。按场景分类。

## 错误码表

| 退出码 | 含义 | 触发脚本 |
|--------|------|---------|
| 0 | 成功 | - |
| 1 | 参数错误 | 所有 |
| 2 | 路径在系统目录黑名单 | validate-path.sh |
| 3 | 路径越界（含 ..）或根目录 | validate-path.sh |
| 4 | 路径不可写 | validate-path.sh |
| 5 | 符号链接指向非法目标 | validate-path.sh |

## 初始化阶段

### `npm install` 失败

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `npm: command not found` | Node.js 未安装 | 安装 Node.js 18+ |
| `EACCES: permission denied` | 全局包权限不足 | 用 `nvm` 或 `n` 安装 Node，避开 sudo |
| `ETARGET: No matching version` | Node 版本过低 | 升级到 Node 18+ |
| `ENOSPC: no space left` | 磁盘满 | 清理磁盘，至少留 2GB |
| `ECONNRESET` | 网络问题 | 检查代理 / 切换 npm 源（淘宝镜像） |

### Node 版本检查

```bash
node --version   # 必须 ≥ 18
```

如果版本低：
- macOS: `brew install node@20` 或用 nvm
- Linux: 用 nvm（推荐）或 apt
- Windows: 从 nodejs.org 下载安装

### 切换 npm 源（中国大陆）

```bash
npm config set registry https://registry.npmmirror.com
```

## Hexo 特定问题

### `hexo init` 卡在 git clone

原因：网络问题无法从 GitHub 拉取 hexo-starter。
解决：hexo-cli 会自动 fallback 到「Copying data instead」，可以继续。

如果还是失败：
```bash
git clone https://github.com/hexojs/hexo-starter.git . --depth 1
# 然后 npx hexo init . --no-install
```

### Butterfly 主题样式丢失

检查 `_config.yml`：
```yaml
theme: butterfly
```

如果还是没样式，确认安装了渲染器：
```bash
npm install --save hexo-renderer-pug hexo-renderer-stylus
```

## VitePress 特定问题

### Build 报 "dead link"

VitePress 1.6+ 默认严格检查链接。`http://localhost:5173` 这种本地地址会被误判。

**修复**：在 `docs/.vitepress/config.mts` 添加：
```ts
ignoreDeadLinks: [/^http:\/\/localhost:/]
```

### 中文搜索不工作

VitePress 1.x 的本地搜索默认不支持中文。解决：
```ts
search: {
  provider: 'local',
  options: {
    detailedView: true
  }
}
```
或者改用 Algolia DocSearch（需要申请，免费）。

## Vue 3 特定问题

### `import vue from 'vue'` 报错

确认安装的是 Vue 3 不是 Vue 2：
```bash
npm ls vue   # 应该显示 3.x
```

如果显示 2.x，卸载重装：
```bash
npm uninstall vue
npm install --save vue@^3.5.0
```

### 路由 hash 模式 vs history 模式

模板默认用 `createWebHashHistory`（hash 模式），适合静态托管。
如果想用 history 模式（URL 干净）：
```js
import { createWebHistory } from 'vue-router'
// ...
history: createWebHistory(),
```
**但**：history 模式部署到 CloudBase / Netlify 需要配置 fallback 规则。

## 路径问题

### `path must be a string` 错误

路径包含特殊字符（中文 / 空格）。解决：
- 避免在项目路径用中文
- 用 `~/projects/` 之类的纯英文路径

### `EACCES` 权限错误

目标目录无写权限。解决：
```bash
sudo chown -R $USER {目录}
# 或选择其他目录
```

## 网络问题

### `npm install` 超时

```bash
# 1. 切淘宝镜像
npm config set registry https://registry.npmmirror.com

# 2. 清理缓存重试
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### GitHub clone 失败

```bash
# 配置代理（如果有）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

## 部署问题

### `tcb login` 跳不出浏览器

这是 headless 环境常见问题。解决：
1. 引导用户去 <https://console.cloud.tencent.com/cam/capi> 创建 API Key
2. 用 `tcb login --apiKey`，输入 SecretId 和 SecretKey
3. 或者在本地登录后导出凭证

### CloudBase 上传后 404

1. 控制台 → 静态托管 → 默认域名 → 检查状态是否为「已启动」
2. 首次启动需要 1-3 分钟
3. 检查上传的目录是否正确（Hexo 应是 `public/`）

### Vercel 部署失败

1. 检查 Build Command 和 Output Directory 设置
2. 看 build log 具体报错
3. 本地先跑 `npm run build` 验证

## 用户中途想改选项

| 想改什么 | 怎么办 |
|---------|--------|
| 改网站名 / 描述 | 改 `_config.yml`（Hexo/VitePress）或 `index.html`（作品集/简历） |
| 换主题 | Hexo: 改 `_config.yml` 的 `theme` 字段；VitePress: 自定义 CSS |
| 加文章 | Hexo: `npx hexo new "标题"`；VitePress: 新建 `.md` |
| 换框架 | 删项目重来（不同框架目录结构不兼容） |
| 改部署平台 | 重新部署到新平台（项目代码不变） |

## 磁盘空间

npm install 通常需要 500MB - 2GB。如果磁盘满：
```bash
# 清理 npm 缓存
npm cache clean --force

# 清理旧版本
npx npx-clean

# 删除 .git 历史中的大文件
git gc --aggressive --prune=now
```

## 完全重置

如果项目损坏，最快的恢复方式是删了重建：

```bash
rm -rf {项目根目录}
# 然后重新走对话流程
```

skill 设计上总是创建新目录，所以重置很安全。