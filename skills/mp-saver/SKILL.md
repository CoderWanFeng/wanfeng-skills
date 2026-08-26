---
name: mp-saver
description: 公众号文章保存器 — 不登录账号，用 urllib 直接抓 mp.weixin.qq.com/s/... 链接的 HTML（带 WeChat UA + Referer），智能提取标题 + unlazy 修补 + 加 <base href> → 保存为单文件。v2.0 起去掉 Playwright/Chromium 依赖，只用 Python 标准库，秒级启动，零第三方包，输出仍是 .mhtml 文件（HTML 源码 + 所有图片 base64 内嵌，离线双击 Chrome/Edge/Safari 即可看完整图文）。支持批量（一次性保存多篇）、自动生成 index.md 清单、可选 --max-images 限内嵌图片数。触发词：「保存公众号文章」「下载公众号文章」「mp.weixin.qq.com 存一下」「把这几篇文章存下来」「公众号另存为」「不登录保存公众号」。
---

# mp-saver · 公众号保存侠

> **目录名**：`mp-saver/`
> **中文名**：公众号保存侠
> **依赖**：**Python ≥ 3.10**（零第三方包，只用标准库 `urllib` / `re` / `base64` / `mimetypes`）
> **输出**：`.mhtml` 单文件（实际为「HTML + base64 内嵌图片」，v2.0 简化版）

> **不登录账号 → 用 urllib 抓 HTML → 智能修补 → 保存为单文件（含图片样式）**
> 核心：Python 标准库 urllib + WeChat UA → 拿文章页 HTML → 提取 og:title 拿到标题 → unlazy 修补 → 下载所有图片转 base64 → 单文件输出。
> 行为与 Chrome 里手动按 Ctrl+S「另存为网页」一致（图片内嵌、可离线、双击可看）。

---

## v2.0 重大改动（vs v1.x）

| 项目 | v1.x（Playwright） | v2.0（纯 HTTP） |
|---|---|---|
| **依赖** | Playwright + Chromium（~150MB 下载） | Python 标准库（0 第三方包） |
| **启动速度** | 5-10 秒（浏览器冷启） | < 1 秒 |
| **install.sh 时长** | 1-2 分钟（含 Chromium 下载） | **0.1 秒**（仅 dry-run 验证） |
| **反爬对抗** | 完整浏览器可绕过 | 拼 WeChat UA，部分文章会被验证码拦截（兜底页直接报错） |
| **懒加载图片** | 浏览器自动渲染 → src 写真地址 | unlazy 函数把 data-src 提到 src（防御性，多数文章 src 已写真地址） |
| **图片下载** | 浏览器上下文内下载（绕过防盗链） | urllib 单独下（部分图床防盗链会失败） |
| **真文章成功率** | 100%（实战 1/1 命中） | 100%（实战 1/1 命中） |
| **输出文件** | `.mhtml`（HTML+base64 内嵌） | `.mhtml`（HTML+base64 内嵌，跟 v1.x 一致） |
| **mac 上大小** | 490 图 base64 = 77.6 MB | 200 图 base64 = 48 MB |

> 💡 **核心动机**：490 张图 base64 编出来 77 MB，下回来占 150 MB，用户体感太重。v2.0 直接 curl 拿 HTML、让浏览器自己在线加载远端图，秒级保存；想内嵌图片再加 `--max-images`。

---

## 何时使用

✅ **使用本 skill 的场景**：

- 想保存某篇公众号文章到本地（离线可看、含图片样式）
- 收藏夹要存一批文章（一次传多个 URL 即可）
- 把公众号内容喂给其他 skill（如 `doc-speedreader` 转 Markdown）—— 先用本 skill 保存，再用 `markitdown file.mhtml` 转
- 不希望登录任何账号、不希望被反爬盯上
- 公众号文章有时效性（被删 / 被篡改），趁早快照一份
- 不想为了存文章装一个 150 MB 的 Chromium

❌ **不要使用**：

- 用户没说要保存文章，只是普通聊天
- 链接不是 `mp.weixin.qq.com/s/...` 格式（本 skill 强校验，拒绝知乎 / 简书 / 一般博客）
- 用户明确要求登录 / 看评论 / 看留言 / 看付费内容 —— 本 skill 只能抓「不登录能看到的部分」
- 文章被设置了「仅关注后查看」 —— 本 skill 抓不到正文，会报「反爬兜底页」
- 文章是图片视频集合、且视频需要登录 —— 本 skill 默认抓 HTML，视频仍是远程 URL

---

## 交互流程（3 轮强制 + 1 轮可选）

### 第 1 轮 · 开场 + 收集链接

**AI 主动说**：

```
你好，我是「公众号保存侠」。
我能把 mp.weixin.qq.com/s/... 链接保存成单个 .mhtml 文件（自带图片样式，
离线双击就能看），全程不登录任何账号。

请把链接丢给我（一行一个，或直接告诉我）。如果是批量，告诉我批次名（比如
"7月AI日报"），我会用它建任务目录。
```

**用户回答**：给 1 个或多个 URL，可选批次名

**AI 内部动作**：

1. 检查 Python ≥ 3.10：
   ```bash
   bash scripts/install.sh   # 0.1 秒验证完
   ```
2. URL 校验：必须是 `https://mp.weixin.qq.com/s/...`（其它域名 / path 拒绝并提示）
3. 给出"待保存清单"回执：
   ```
   [✓] 共 3 个有效 URL：
     1. https://mp.weixin.qq.com/s/abc...
     2. https://mp.weixin.qq.com/s/def...
     3. https://mp.weixin.qq.com/s/ghi...
   ```

---

### 第 2 轮 · 选格式 + max-images（默认推荐）

**AI 给出选项**：

```
默认走「MHTML 模式 + 限 200 张内嵌」：

A. ⭐ MHTML（默认，--max-images 200）
   - 单文件，前 200 张图 base64 内嵌（~50MB/篇）
   - 其余图片保留远程 URL，浏览器打开自动加载
   - 离线能看前 200 张图，后续图需联网
B. MHTML 不限数量（--max-images 0）
   - 所有图片 base64 内嵌，离线全可看
   - 文件可能 60-100 MB/篇
C. HTML（--format html）
   - 不下载图片，最快（5 秒/篇）
   - 但离线看不到图，需要联网加载
```

**关键决策**：

- 用户说"默认" / "A" / 不回答 → 走 A（推荐）
- 用户说"B" / "全下" / "离线必须全部可看" → 走 B
- 用户说"C" / "只要 HTML" / "我自己处理图" → 走 C

> 💡 **决策参考**：490 张图 base64 编出来 ~77 MB，单文件太大分享不便；用 `A` 既能让浏览器看到完整正文（前 200 图 + 远程后续），又控制单文件大小。

---

### 第 3 轮 · 执行保存 + 交付

**AI 直接调脚本**：

```bash
TASK_DIR="skills/mp-saver/task/$(date +%Y%m%d)-<slug>"
mkdir -p "$TASK_DIR"
python3 scripts/save_mp.py \
  --output "$TASK_DIR" \
  --max-images 200 \
  <url1> <url2> <url3>
```

脚本内部按顺序跑：urllib 抓 HTML（带 WeChat UA + Referer）→ 反爬兜底检测 → 从 og:title 提取标题 → unlazy 修补（把 data-src 提到 src）→ mhtml 模式下载所有 `<img>` 转 base64 → 加 `<base href>` 防止相对资源 404 → 写单文件。

**AI 给出回执**（复制脚本 stdout）：

```
[✓] 共 3 个有效 URL 待保存
[✓] 输出目录：skills/mp-saver/task/20260813-ai-daily/
→ 抓取：https://mp.weixin.qq.com/s/abc...
[✓] 抓到 HTML（5234.5 KB）
[✓] 已保存：cursor-深度评测.mhtml（32104.2 KB，标题：Cursor 深度评测：...）
→ 抓取：https://mp.weixin.qq.com/s/def...
[✓] 抓到 HTML（4123.8 KB）
[✗] 保存失败：https://mp.weixin.qq.com/s/def...（页面是反爬兜底页）

任务完成：成功 2 / 失败 1
清单文件：skills/mp-saver/task/20260813-ai-daily/index.md
```

**任务目录结构**：

```
skills/mp-saver/task/20260813-ai-daily/
├── index.md                    ← 清单（含标题/大小/链接）
├── cursor-深度评测.mhtml
├── claude-code-使用心得.mhtml
└── (失败的那篇：见 index.md 的「失败清单」段)
```

**AI 给出交付总结**：

```
✅ 已保存到 skills/mp-saver/task/20260813-ai-daily/
   - cursor-深度评测.mhtml（32.1 MB）
   - claude-code-使用心得.mhtml（失败：反爬兜底页，见 index.md）

打开方式：Finder 双击 .mhtml 文件 → 用 Chrome / Edge / Safari 打开即可。
或命令行：open cursor-深度评测.mhtml
```

**不要**主动把 MHTML 喂给别的 skill（除非用户主动要求）。

---

### 第 4 轮（可选）· 追问 / 续保存

- 用户说「再存几篇」 → 跳回第 1 轮
- 用户说「失败那篇再试」 → AI 重跑单 URL（无需开新批次，--output 指同一目录即可）
- 用户说「把它们转成 Markdown」 → **明确告知**：本 skill 不做下游联动，可推荐用 `doc-speedreader`：
  ```
  python3 scripts/save_mp.py ...       # 先保存
  bash doc-speedreader/scripts/convert.sh .../cursor.mhtml  # 再转 Markdown
  ```
- 用户说「够了」 / 「谢谢」 → 收工

---

## 核心命令速查

```bash
# 1. 一次性验证（0.1 秒，仅检查 Python 版本 + dry-run）
bash scripts/install.sh

# 2. 保存单篇（最常用）
python3 scripts/save_mp.py \
  "https://mp.weixin.qq.com/s/abc123"

# 3. 批量保存（多 URL）
python3 scripts/save_mp.py \
  "https://mp.weixin.qq.com/s/abc" \
  "https://mp.weixin.qq.com/s/def" \
  "https://mp.weixin.qq.com/s/ghi"

# 4. 从文件读 URL（每行一个，# 开头是注释）
python3 scripts/save_mp.py --file urls.txt

# 5. 指定输出目录 + 自定义批次名
python3 scripts/save_mp.py \
  --output /Users/wanfeng/Desktop/mp-saves/ \
  --slug "7月AI日报" \
  "https://mp.weixin.qq.com/s/abc"

# 6. MHTML 不限内嵌图数（--max-images 0）
python3 scripts/save_mp.py \
  --format mhtml --max-images 0 \
  "https://mp.weixin.qq.com/s/abc"

# 7. 限内嵌图片数（默认就是 0 不限，但用 --max-images 200 可控大小）
python3 scripts/save_mp.py \
  --format mhtml --max-images 200 \
  "https://mp.weixin.qq.com/s/abc"

# 8. 只跑 HTML（不含图片，文件更小，离线无图，最快）
python3 scripts/save_mp.py --format html \
  "https://mp.weixin.qq.com/s/abc"

# 9. 慢网环境加超时（默认 30 秒）
python3 scripts/save_mp.py --timeout 60 \
  "https://mp.weixin.qq.com/s/abc"

# 10. 试运行（不真保存，只看会做什么）
python3 scripts/save_mp.py --dry-run \
  "https://mp.weixin.qq.com/s/abc"

# 11. 通过代理（如果上不了外网）
HTTPS_PROXY=http://127.0.0.1:7890 python3 scripts/save_mp.py \
  "https://mp.weixin.qq.com/s/abc"
```

详细文档见 [reference/quickstart.md](reference/quickstart.md)。

---

## 输出格式速查

| 格式 | 命令 | 体积 | 离线图片 | 文本提取 | 浏览器打开 |
|---|---|---|---|---|---|
| **MHTML 限图**（默认 ⭐） | `--format mhtml --max-images 200` | 5-50 MB/篇 | ⚠️ 前 200 张 | ⚠️ 需先转 MD | ✅ 双击 |
| **MHTML 全部** | `--format mhtml --max-images 0` | 20-100 MB/篇 | ✅ | ⚠️ 需先转 MD | ✅ 双击 |
| HTML | `--format html` | 100-500 KB/篇（纯 HTML） | ❌（远程 URL） | ✅ 直接读 | ✅ 双击 |

详细对比见 [reference/formats.md](reference/formats.md)。

---

## 边界 & 安全

| 行为 | 是否执行 | 说明 |
|---|---|---|
| 不登录任何账号 | ✅ | **核心原则** —— 公众号文章不登录也能看（除非被设为「仅关注后查看」） |
| 保存 `mp.weixin.qq.com/s/...` 链接 | ✅ | 唯一支持的 URL 模式 |
| 保存其他域名文章 | ❌ | 知乎 / 简书 / 一般博客不在本 skill 范围（拒绝并提示） |
| 保存需要登录的文章 | ❌ | 「仅关注后查看」类会被反爬，兜底页直接报错退出 |
| 保存含付费 / 视频号视频的文章 | ⚠️ | 视频仍为远程 URL，离线看不了视频 |
| 安装 150 MB Chromium | ❌ | v2.0 起不再装任何第三方包 |
| 走代理保存 | ✅ | `HTTPS_PROXY=http://...` 环境变量 |
| 自动把 MHTML 转 Markdown | ❌ | 本 skill 只做保存，不做下游联动 |
| 自动推荐其他 skill | ❌ | 用户没问就不主动推 |

### URL 校验（脚本内置）

- ✅ 只接受 `https://mp.weixin.qq.com/s/...`（HTTP 也接受，但不推荐）
- ❌ 拒绝非 `mp.weixin.qq.com` 域名（防误保存其它站点）
- ❌ 拒绝 `mp.weixin.qq.com` 但非 `/s/` 路径（如 `/cgi-bin/...`）
- ❌ 拒绝空 URL / 协议不是 http(s)

详见 [reference/safety.md](reference/safety.md)。

### 反爬兜底页检测（v2.0 新增）

| 兜底页判定条件 | 行为 |
|---|---|
| URL 跳到 `wappoc_appmsgcaptcha` | 报错退出，提示「用浏览器手动另存为」 |
| HTML < 30KB + 含「环境异常」「验证身份」「请完成验证」 | 报错退出 |
| 没图床域名 (`mmbiz.qpic.cn`) + 含「该公众号已被屏蔽」「该文章已被发布者删除」 | 报错退出 |

> 💡 **关键经验**：v2.0 不再用「请在微信中打开」当兜底标记 —— 这个字符串出现在公众号所有页面的 JS 检测脚本里，真文章也会命中，会**误判所有文章**。

---

## 失败兜底（5 段式）

> 当 `save_mp.py` 抛错、urllib 抓取失败、文件无法写入时，AI 按 5 段式回应用户：

1. **原文**：贴出报错最后 1-2 行
2. **人话**：用 1 句大白话解释「发生了什么」
3. **根因**：技术层面的真正原因
4. **3 步**：用户能立刻执行的 3 个具体动作
5. **兜底**：本 skill 无能为力时的退路

完整 6 个常见报错的 5 段式回答见 [reference/troubleshooting.md](reference/troubleshooting.md)。

---

## 目录结构

```
mp-saver/
├── SKILL.md                          ← 本文件（入口 + 交互流）
├── README.md                         ← 仓库级说明
├── progress.md                       ← 封装进度记录
├── scripts/
│   ├── install.sh                    ← v2.0 起：仅 Python 版本检测 + dry-run 验证
│   └── save_mp.py                    ← 核心保存脚本（urllib + 智能修补）
├── reference/
│   ├── quickstart.md                 ← 快速上手 + 命令详解
│   ├── formats.md                    ← MHTML 限图/全图/HTML 详细对比
│   ├── safety.md                     ← 安全约束（不登录 / URL 校验 / 反爬）
│   └── troubleshooting.md            ← 6 个常见报错的 5 段式回答
└── templates/
    └── (预留：未来加 task-readme 模板)
```

---

## 相关文档（仅本 skill 内部）

- **快速上手**：[reference/quickstart.md](reference/quickstart.md)
- **输出格式对比**：[reference/formats.md](reference/formats.md)
- **安全约束**：[reference/safety.md](reference/safety.md)
- **失败兜底 6 例**：[reference/troubleshooting.md](reference/troubleshooting.md)
- **维护说明**：[README.md](README.md)
- **进度日志**：[progress.md](progress.md)
