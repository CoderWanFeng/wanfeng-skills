# 快速上手 · mp-saver

> 把 mp.weixin.qq.com/s/... 链接保存为单文件 .mhtml —— 不登录、双击可看。
> **v2.0 起零依赖（只用 Python 标准库），启动秒级。**

---

## 0. 30 秒原理

```
mp.weixin.qq.com/s/abc123  ─→  urllib 抓 HTML（带 WeChat UA + Referer）
                                  ↓
                               反爬兜底检测（3 段式）
                                  ↓
                               从 og:title / var msg_title 等多源提取标题
                                  ↓
                               unlazy 修补（把 data-src 提到 src）
                                  ↓
                               mhtml 模式：下载 <img> 图转 base64 内嵌
                                  ↓
                               加 <base href> + 写单文件 .mhtml
                                  ↓
                               Finder 双击 → Chrome / Edge 打开 → 看到原文
```

**MHTML** = MIME HTML = 单文件包含 HTML + CSS + 图片 = 你在 Chrome 里按 `Ctrl+S` 另存为「网页，单个文件」会得到的格式。
v2.0 实际产物是「HTML + base64 内嵌图片」（跟 Chrome 121+ 移除了真 MHTML 接口有关，详细见 [SKILL.md](../SKILL.md)）。

---

## 1. 一次性验证

```bash
cd /Users/wanfeng/code/wanfeng-skills/skills/mp-saver
bash scripts/install.sh
```

**会做**：

1. 找 Python ≥ 3.10
2. 跑一次 `--dry-run` 自检

**装好后会看到**：

```
[✓] ✅ 验证通过！v2.0 不需要装任何第三方包。
```

> 💡 v2.0 起不再装任何第三方包。`install.sh` 0.1 秒跑完。

---

## 2. 最常用：保存单篇

```bash
python3 scripts/save_mp.py \
  "https://mp.weixin.qq.com/s/abc123xyz"
```

**产出**：

```
skills/mp-saver/task/20260813-default-batch/
├── index.md
└── <标题-slug>.mhtml   ← mhtml 模式（默认），--max-images 0 = 全内嵌
```

`<标题-slug>` 自动从页面 `<meta property="og:title">` 提取（如「Cursor 深度评测」→ `Cursor-深度评测.mhtml`）。

**耗时**：HTML + 标题提取 + unlazy 修补**约 6 秒**；MHTML 模式还要下图片，每张图约 0.5-1 秒。

---

## 3. 批量保存（一次多篇）

```bash
python3 scripts/save_mp.py \
  "https://mp.weixin.qq.com/s/abc" \
  "https://mp.weixin.qq.com/s/def" \
  "https://mp.weixin.qq.com/s/ghi"
```

3 篇顺序保存到同一任务目录。某篇失败不影响其它（失败清单写进 index.md）。

---

## 4. 从文件读 URL

适合文章多到命令行塞不下，或要复用上次清单：

```bash
# urls.txt（每行一个，# 开头视为注释）
cat urls.txt
# # 7 月 AI 日报
# https://mp.weixin.qq.com/s/abc
# https://mp.weixin.qq.com/s/def

python3 scripts/save_mp.py --file urls.txt
```

---

## 5. 自定义输出目录 + 批次名

```bash
python3 scripts/save_mp.py \
  --output /Users/wanfeng/Desktop/mp-saves/ \
  --slug "7月AI日报" \
  "https://mp.weixin.qq.com/s/abc"
```

→ `/Users/wanfeng/Desktop/mp-saves/7月AI日报/`

适合：想把保存的 MHTML 集中放某个目录、跨 skill 引用、不混在 `task/` 里。

---

## 6. 限内嵌图片数（控制单文件大小）

v2.0 起默认不限内嵌图数（`--max-images 0`）。但**全内嵌单文件可能 60-100 MB**，分享不便：

```bash
# 只内嵌前 200 张图（约 50 MB），其余仍是远程 URL
python3 scripts/save_mp.py --max-images 200 \
  "https://mp.weixin.qq.com/s/abc"

# 全部内嵌（默认行为，最完整但单文件大）
python3 scripts/save_mp.py --max-images 0 \
  "https://mp.weixin.qq.com/s/abc"
```

**推荐**：先用 `--max-images 200`，浏览器打开时前 200 张图快速显示（已下载到本地），后面图片走网络加载，体验跟全内嵌差不多但单文件小。

---

## 7. 只跑 HTML（不下载图片，最快）

```bash
python3 scripts/save_mp.py --format html \
  "https://mp.weixin.qq.com/s/abc"
```

**优势**：
- 5-6 秒拿到（不下载任何图片）
- 单文件 100-500 KB（只有 HTML 源码）
- 适合：只想先看看是不是要存、批量筛选、用 `markitdown` 转 Markdown

**代价**：浏览器打开后图片仍走网络加载（mmbiz.qpic.cn 远程 URL），离线无图。

---

## 8. 通过代理

如果上不了 mp.weixin.qq.com：

```bash
HTTPS_PROXY=http://127.0.0.1:7890 \
  python3 scripts/save_mp.py \
    "https://mp.weixin.qq.com/s/abc"
```

或全局设：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
python3 scripts/save_mp.py "https://mp.weixin.qq.com/s/abc"
```

---

## 9. 慢网环境（超时调整）

```bash
python3 scripts/save_mp.py --timeout 60 \
  "https://mp.weixin.qq.com/s/abc"
```

默认 `--timeout 30` 秒。慢网/文章图非常多时可加到 60-90。

---

## 10. 试运行

```bash
python3 scripts/save_mp.py --dry-run \
  "https://mp.weixin.qq.com/s/abc"
```

→ 只打印「会做什么」，不真抓取 / 写文件。**首次使用**可以先 dry-run 一下确认 URL 校验逻辑没问题。

---

## 完整参数清单

```text
usage: save_mp.py [-h] [--file FILE] [--output OUTPUT]
                  [--format {mhtml,html}] [--timeout TIMEOUT]
                  [--max-images MAX_IMAGES] [--slug SLUG]
                  [--dry-run]
                  [urls ...]

positional arguments:
  urls                       一个或多个 mp.weixin.qq.com/s/... 链接

optional arguments:
  --file FILE, -f FILE       从文件读 URL 列表
  --output OUTPUT, -o OUTPUT 输出目录
  --format {mhtml,html}      保存格式（默认 mhtml）
  --timeout TIMEOUT          单页抓取超时秒数（默认 30）
  --max-images MAX_IMAGES    mhtml 模式最多内嵌几张图（0=不限）
  --slug SLUG                任务目录名后缀
  --dry-run                  只打印不保存
```

---

## 常见场景速查

| 场景 | 命令 |
|---|---|
| 第一次用 | `bash scripts/install.sh` |
| 存 1 篇 | `python3 scripts/save_mp.py "<url>"` |
| 存一批 | `python3 scripts/save_mp.py url1 url2 url3` |
| 文件清单 | `python3 scripts/save_mp.py -f urls.txt` |
| 自定义路径 | `python3 scripts/save_mp.py -o /path/ --slug xxx "<url>"` |
| 限内嵌图片数 | `python3 scripts/save_mp.py --max-images 200 "<url>"` |
| 只存 HTML（无图）| `python3 scripts/save_mp.py --format html "<url>"` |
| 慢网 | `python3 scripts/save_mp.py --timeout 60 "<url>"` |
| 上不去 | `HTTPS_PROXY=... python3 scripts/save_mp.py "<url>"` |
| 先试一下 | `python3 scripts/save_mp.py --dry-run "<url>"` |

---

## 下一步：保存后想转 Markdown？

本 skill 不做下游联动。手动两步：

```bash
# 1) 先保存 MHTML
python3 scripts/save_mp.py "https://mp.weixin.qq.com/s/abc"

# 2) 用 doc-speedreader 转 Markdown
bash ../doc-speedreader/scripts/convert.sh \
  task/20260813-default-batch/<标题>.mhtml
```

`doc-speedreader` 基于 Microsoft MarkItDown，MHTML 能解析成 Markdown（含图片引用）。
