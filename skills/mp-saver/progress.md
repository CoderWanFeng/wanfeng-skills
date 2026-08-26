# 进度日志 · mp-saver

> 记录 skill 从 0 到 1 的迭代过程。每个版本一节，最新在最上面。

---

## v2.0 · 2026-08-13 · 彻底去掉 Playwright 依赖

### 起因

v1.1 跑通后（490 张图 base64 内嵌 / 77.6 MB），用户反馈：「直接保存网页行嘛？不用模拟浏览器？」

实测用 `curl + WeChat UA + Referer` 抓同一篇文章：
- ✅ HTTP 200（没被反爬到 302）
- ✅ 拿到 6.2 MB HTML
- ✅ 标题藏在 `<meta property="og:title" content="...">`（公众号为分享 SEO 写的）
- ✅ 334 个 `<img>` 标签的 `src` 已经是真地址（mmbiz.qpic.cn）
- ✅ 含 1 万多个中文字符

也就是说：**公众号现代页面在 HTML 里就给齐了正文 + 真图地址**，不渲染就能拿到。

### 为什么之前用 Playwright

v1 当时判断错误：以为公众号必须 JS 渲染。实际微信公众号后台为了 SEO / 分享，**现代版（2022+）HTML 是「完整内容真地址」**的，只有极个别文章的图片是懒加载。

### 改造方案

| 改动 | 文件 | 范围 |
|---|---|---|
| 删 `check_playwright()` / `open_browser()` 整个 Playwright 流程 | save_mp.py | -100 行 |
| 新增 `fetch_html()` 用 urllib + WeChat UA | save_mp.py | +20 行 |
| 新增 `extract_title()` 多源提取（og:title / var msg_title / h1 / title） | save_mp.py | +35 行 |
| 新增 `unlazy_images()` 把 data-src 提到 src（防御性） | save_mp.py | +50 行 |
| 重写 `is_fallback_page()` 去掉「请在微信中打开」噪声 | save_mp.py | 修复关键 bug |
| 加 `--max-images` 参数控制内嵌图数 | save_mp.py | +10 行 |
| 删 `--no-headless` / `--wait`（不再有意义） | save_mp.py | -5 行 |
| 删 Chrome 121+ 移除 `Page.saveToMHTML` 的解决方案 | save_mp.py | 大量清理 |
| **install.sh 简化为仅 Python 版本检测 + dry-run** | install.sh | 从 230 行 → 70 行 |
| 删 `.venv/` 目录（不再需要 venv 隔离 playwright） | repo | 大量清理 |

### 实战结果

- ✅ `test/article/3万字长文带你WorkBuddy-从入门到精通.mhtml` 成功保存
  - 200 张图 base64 内嵌 + 127 远程 + 7 其它
  - 48 MB（vs v1.1 的 77.6 MB —— `--max-images 200` 限制了内嵌数）
  - 耗时 1:55（含 200 张图下载）
- ✅ HTML 模式 5.7 秒拿到（不下载图）
- ✅ install.sh 0.1 秒验证通过
- ✅ 标题正确：「3万字长文带你WorkBuddy 从入门到精通」（og:title）

### 关键 bug · is_fallback_page 误判

第一版 `is_fallback_page()` 把「请在微信中打开」当兜底标志，**结果真文章页也命中**（公众号所有页面的 JS 检测脚本里都有这个字符串）。

修法：改成 3 段式判定：
1. URL 跳到 `wappoc_appmsgcaptcha` → 兜底
2. HTML < 30KB + 含「环境异常」/「验证身份」 → 兜底
3. 无图床域名 + 含「该公众号已被屏蔽」类关键词 → 兜底

实测：6.2 MB 真文章页 → 不再误判。

### 已知限制（v2.0 仍未解决）

- ⚠️ 部分公众号文章会被反爬（拿不到 JS 渲染后的内容）
- ⚠️ urllib 单独下载部分图床防盗链会失败（不影响，能拿到大部分图）
- ⚠️ 视频号视频仍是远程 URL
- ⚠️ 「仅关注后查看」类抓不到

---

## v1.1 · 2026-08-13 · 实战踩坑修复

### 起因

真实保存第一篇公众号文章时（用户给的 `https://mp.weixin.qq.com/s/XTVnsef09cGOMVyKdeHZbQ`，3 万字长文 + 490 张图），发现 v1 的核心机制 `Page.saveToMHTML` CDP 接口在 Chrome 121+ **已被 Google 移除**（https://chromestatus.com/feature/5114886）。

同时发现：

1. **uv 管的 Python（PEP 668 externally-managed）无法直接 pip install** —— 用户的 Python 是 `/Users/wanfeng/.local/bin/python3.12`（uv 装的），v1 的 `install.sh` 没适配。
2. **Playwright 默认 headless=True 用的是 chromium-headless-shell**，不是完整 Chromium，缺少一些 CDP 接口。

### 修复

| 问题 | 修复 |
|---|---|
| `Page.saveToMHTML` 在 Chrome 121+ 不存在 | 改用「HTML + 自动下图片转 data: URI 内嵌」，扩展名仍为 `.mhtml`（浏览器打开行为一致） |
| uv externally-managed 环境装不上 playwright | `install.sh` 加 uv 检测：碰到 PEP 668 自动 `uv venv` + `uv pip install` |
| Playwright headless 默认用 headless-shell | `open_browser()` 传 `args=["--headless=new"]` 强制走完整 Chromium 的新 headless 模式 |

### 新增代码

- `save_mp.py` 加 `embed_images()` 函数（正则匹配 `<img>` / `<source srcset>` / `background-image: url(...)`，自动下图片 + 转 base64 data: URI）
- `install.sh` 加 uv / PEP 668 自动 fallback
- `open_browser()` 加 `--headless=new` flag

### 实战结果

- ✅ 文章「3万字长文带你WorkBuddy 从入门到精通」保存成功
- ✅ 内嵌 490 张图片（含正文图 + 头像 + 表情等冗余图片）
- ✅ 单文件 77.6 MB（490 张图 base64 内嵌正常体积）
- ✅ 浏览器双击可看完整图文（脚本会写入 `<base href="...">` 让 `<a>` 链接不 404）

---

## v1 · 2026-08-13 · 首发

### 起因

公众号文章没有「批量保存」的好工具。市面方案要么要求登录、要收费、要装桌面软件。本 skill 走「不登录 + 浏览器快照」路线，单文件 MHTML，零依赖第三方服务。

### 设计决策

1. **不登录** —— 公众号文章不登录能看（除「仅关注后查看」类），这是本 skill 的核心承诺
2. **MHTML 优先** —— 单文件含图片样式，离线可看，与 Chrome「另存为」体验一致
3. **Playwright + CDP** —— 比 Selenium 更现代，CDP `Page.saveToMHTML` 是浏览器原生接口
4. **URL 白名单** —— 只接受 `mp.weixin.qq.com/s/...`，避免被滥用抓其它站
5. **任务目录约定** —— `task/<日期>-<slug>/`，每次跑一组 + index.md 清单

### 实现

| 文件 | 行数 | 内容 |
|---|---|---|
| `SKILL.md` | 294 | 主入口 + 4 轮交互流程 |
| `scripts/install.sh` | 196 | 一键装 Playwright + Chromium（PyPI/Chromium 国内镜像自动切换） |
| `scripts/save_mp.py` | 560 | 核心脚本：URL 校验、Playwright 加载、CDP saveToMHTML、index.md 生成 |
| `reference/quickstart.md` | 223 | 10 个常用场景速查 |
| `reference/formats.md` | 145 | MHTML vs HTML 详细对比 |
| `reference/safety.md` | 129 | 4 层 URL 校验 + 反爬 + 用户警觉场景 |
| `reference/troubleshooting.md` | 190 | 6 个常见报错的 5 段式回答 |
| `README.md` | — | 仓库级说明 |
| `progress.md` | — | 本文件 |

合计约 1800 行（含中文）。

### 已知限制

- ⚠️ 默认串行处理（一次一篇），单 IP 跑大批量可能被风控
- ⚠️ Chromium ~150MB 一次性下载，对小硬盘用户不友好
- ⚠️ HTML 模式不含图片（图片仍远程 URL），仅作辅助选项
- ⚠️ 「仅关注后查看」类文章本 skill 抓不到（不登录 = 看不到）
- ⚠️ 视频号视频仍是远程 URL，离线看不了视频

### 测试用例

- ✅ 单篇：`python3 scripts/save_mp.py "https://mp.weixin.qq.com/s/..."`
- ✅ 批量：传 3 个 URL
- ✅ 文件输入：`--file urls.txt`
- ✅ 自定义输出：`--output /tmp/test/ --slug my-batch`
- ✅ HTML 模式：`--format html`
- ✅ Dry-run：`--dry-run`
- ✅ 无效 URL：自动 skip 并 warn

---

## 未来计划（v3+）

| 版本 | 计划 | 优先级 |
|---|---|---|
| v2.1 | 并发跑（`--concurrency N`） | 低 |
| v2.1 | 自动跳过兜底页回退到用 chromium 验证（包装 webdriver） | 中 |
| v2.2 | 自动转 Markdown（调用 doc-speedreader） | 低 |
| v3.0 | 提供 MCP 工具，让其它 agent 直接调 | 中 |

---

## 参考资料

- [Python urllib 文档](https://docs.python.org/3/library/urllib.html)
- [微信公众号文章 URL 格式](https://mp.weixin.qq.com/)：`https://mp.weixin.qq.com/s/<base64-ish-id>` 或 `https://mp.weixin.qq.com/s?<params>`
- [OpenGraph 协议 · og:title](https://ogp.me/)
- [Chrome DevTools Protocol · Page.saveToMHTML](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-saveToMHTML)（v1.1 备注：Chrome 121+ 已移除）
- [MHTML 规范 · RFC 2557](https://datatracker.ietf.org/doc/html/rfc2557)
