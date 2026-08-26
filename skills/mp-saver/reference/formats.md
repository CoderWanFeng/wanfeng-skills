# 输出格式 · MHTML vs HTML

> 本 skill 支持两种保存格式：**MHTML**（默认 ⭐）和 **HTML**（仅源码）。
> v2.0 起 MHTML 模式新增 `--max-images N` 控制内嵌图片数。

---

## 一句话对比

| | MHTML（默认） | HTML |
|---|---|---|
| 单文件 | ✅ | ✅（单 .html） |
| 含图片 | ⚠️ 默认全内嵌（用 `--max-images N` 限制）/ 不限 | ❌（图片仍是远程 URL） |
| 离线打开 | ⚠️ 限图模式：前 N 张图离线；不限：全离线 | ⚠️ 能看但图片需联网 |
| 体积（MHTML 限 200）| 5-50 MB / 篇 | 100-500 KB / 篇 |
| 体积（MHTML 不限） | 20-100 MB / 篇 | 100-500 KB / 篇 |
| 文本提取 | ⚠️ 需先转 MD | ✅ 直接可读 |
| 浏览器兼容性 | ✅ Chrome / Edge / Safari / Firefox | ✅ 所有浏览器 |
| 下载耗时 | 6 秒 + (N 张图 × ~0.5 秒) | 5-6 秒 |

---

## 什么是 MHTML？（v2.0 实际产物）

> **实际不是真 MHTML**，是「HTML + base64 内嵌图片」的单文件。
> 扩展名仍为 `.mhtml`，浏览器双击 Chrome / Edge / Safari 打开效果与 MHTML 一致。
> （v1 原计划走 CDP `Page.saveToMHTML`，但 Chrome 121+ 已被 Google 移除。v2.0 起连 Playwright 都不要了，全程 Python 标准库 `urllib` + `re` + `base64`。）
>
> **MHTML** = MIME HTML（RFC 2557）= 单文件包含 HTML + CSS + 图片 + 字体
>
> **本 skill 的实现** = `urllib` 抓 HTML（WeChat UA）+ 正则提取所有 `<img>` 的 src + `urllib` 下图片 + base64 转 `data:image/...` URI + 替换原 src + 加 `<base href>` 防止相对路径资源 404

**为什么这样设计？**

- ✅ **单文件**：方便管理、复制、备份（不会丢图片）
- ✅ **离线打开**：限图模式下前 N 张图全内嵌，其余走网络；不限模式全离线
- ✅ **保真度高**：所见即所得（包括公众号特有的代码块高亮、图片样式）
- ✅ **跨浏览器**：`.mhtml` 扩展名 + 标准 HTML 内容，所有浏览器都能打开
- ✅ **零依赖**：v2.0 起只走 Python 标准库，5 秒级启动

**坏处**：

- ⚠️ 体积比纯 HTML 大（图片 base64 编码体积增 ~33%）
- ⚠️ 不限图模式单文件可能 60-100 MB，分享不便
- ⚠️ 不便直接文本提取（要先转 Markdown：见下）

---

## `--max-images N`（v2.0 新增）

控制 MHTML 模式最多内嵌多少张图片。`N=0` = 不限（默认），`N=200` 是推荐值。

```bash
# 推荐：限 200 张图 + 远程图床兜底，单文件 5-50 MB
python3 scripts/save_mp.py --max-images 200 "https://mp.weixin.qq.com/s/abc"

# 全文图都内嵌：单文件可能 60-100 MB（分享/邮件不友好）
python3 scripts/save_mp.py --max-images 0 "https://mp.weixin.qq.com/s/abc"

# 只内嵌 50 张图（适合快速预览 / 限速网）
python3 scripts/save_mp.py --max-images 50 "https://mp.weixin.qq.com/s/abc"
```

**实现细节**：

- 不限图：所有 `<img>` 的 src 替换为 `data:image/...` URI
- 限图：前 N 张图的 src 替换；其余图 src 保持原样（远程 URL）—— 浏览器打开后**前 N 张秒开**，**后续图走网络**（mmbiz.qpic.cn 一般不需要权限）
- 失败的图：仍保留原远程 URL（不替换），warn 但不报错退出

**为什么默认不限**：

v2.0 还没想清楚默认更应该是「可控大小」还是「完整离线」。当前默认不限（`--max-images 0`）逻辑上最简单，但用户大概率会想改 `200` 控制大小。建议：

- 想分享 / 放进 zip：传 `--max-images 200`
- 想要完整离线快照：传 `--max-images 0`

---

## 什么是 HTML 模式？

`--format html` 时，脚本保存 `urllib` 抓的 HTML 源码（未经任何修改，含原始 `<script>`、`<link>` 等）。

**为什么不用 HTML？**

HTML 模式不含图片资源！图片引用仍然是 `https://mmbiz.qpic.cn/...` 这种远程 URL。

**结果**：

- 在本地双击打开 → 能看到文字，但图片加载需要联网
- 不能算「真正的离线快照」

**什么时候用 HTML**：

- 你只想提取文字（不关心图片）
- 你打算自己写脚本下载图片再嵌入
- 你想把 HTML 喂给别的解析工具（如 BeautifulSoup）
- 5-6 秒拿到，批量筛选时最快

⚠️ **本 skill 默认 MHTML 模式**，HTML 模式仅作辅助选项。

---

## 哪种格式适合我？

| 你的目标 | 推荐 |
|---|---|
| 离线收藏 / 双击可看（前 200 张图） | **MHTML 限 200** ⭐ |
| 完整离线快照（含所有图） | **MHTML 不限**（默认 0） |
| 转 Markdown 后用 | **MHTML 限 200**（先存 MHTML，再用 doc-speedreader 转） |
| 只看文字、即时分享 | HTML |
| 自己解析 / 二次开发 | HTML |
| 文章是纯视频 | 都一样（视频都是远程 URL） |

---

## 怎么打开 MHTML？

### macOS

```bash
# 命令行
open xxx.mhtml

# Finder 双击默认用 Safari 打开
# 想用 Chrome / Edge 打开：右键 → 打开方式 → Google Chrome
```

### Windows

```bash
# 命令行
start xxx.mhtml

# 双击默认 Chrome / Edge 打开
# 想换浏览器：右键 → 打开方式
```

### Linux

```bash
# Chrome
google-chrome xxx.mhtml

# Firefox
firefox xxx.mhtml
```

---

## 体积参考（v2.0 实测）

| 文章类型 | 文字量 | 图片数 | MHTML 限 200 | MHTML 不限 | HTML |
|---|---|---|---|---|---|
| 短资讯 | < 1000 字 | 1-3 | 100-500 KB | 200 KB - 2 MB | 50 KB |
| 普通长文 | 2000-5000 字 | 5-15 | 500 KB - 5 MB | 1-20 MB | 100-200 KB |
| 图文长文（设计 / 摄影类） | 1000-3000 字 | 20-50 | 5-15 MB | 20-60 MB | 200-500 KB |
| 含代码块的技术文 | 3000-8000 字 | 3-8 | 200 KB - 5 MB | 500 KB - 30 MB | 100-300 KB |
| 图文长文 + emoji/小图标 | 3000+ 字 | 300+ | 30-50 MB（实测）| 60-100 MB | 200-500 KB |

> 💡 **v2.0 实测**：「3万字长文带你WorkBuddy 从入门到精通」（334 张图）
> - HTML 模式：6 MB（HTTP 200 拿到 6.2 MB HTML）
> - MHTML 限 200：48 MB（200 内嵌 + 127 远程）
> - MHTML 不限：估算 70-80 MB（未实测）

---

## 转 Markdown（MHTML → MD）

本 skill 不做下游联动。需要的话用 `doc-speedreader`：

```bash
# 1) 保存 MHTML
python3 scripts/save_mp.py --max-images 0 "https://mp.weixin.qq.com/s/abc"

# 2) 转 Markdown
bash ../doc-speedreader/scripts/convert.sh \
  task/20260813-default-batch/<标题>.mhtml
```

产物是 `<标题>.md`，含：

- 标题层级（# ## ###）
- 段落 + 列表
- 图片（base64 内嵌或 markdown 引用）
- 代码块（带语言标记）

→ 可直接喂给 LLM / 笔记软件 / RAG。
