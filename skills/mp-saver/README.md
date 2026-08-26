# mp-saver · 公众号保存侠

> 把 `mp.weixin.qq.com/s/...` 链接保存成单文件 `.mhtml` —— 不登录、双击可看。
> **v2.0 起零依赖（Python 标准库），启动秒级。**

---

## 这是什么？

一个 **公众号文章下载工具**，定位是「不想登录、想把公众号文章存本地当参考」。

工作流极简（v2.0 已去掉 Playwright / Chromium）：

```
mp.weixin.qq.com/s/abc123  ─→  urllib 抓 HTML（WeChat UA + Referer）
                                  ↓
                               反爬兜底检测
                                  ↓
                               从 og:title / var msg_title 多源提取标题
                                  ↓
                               unlazy 修补（把 data-src 提到 src）
                                  ↓
                               mhtml 模式：urllib 下图片转 base64 内嵌
                                  ↓
                               加 <base href> + 写 .mhtml 单文件
```

**MHTML** = Chrome / Edge / Safari 原生支持的「网页，另存为单个文件」格式 —— 单文件含 HTML + CSS + 图片（base64 内嵌），离线双击就能看到原文。
v2.0 实际产物是「HTML + base64 内嵌图片」（Chrome 121+ 移除了真 MHTML 接口，详见 [progress.md](progress.md)）。

---

## 适合谁？

| ✅ 适合 | ❌ 不适合 |
|---|---|
| 收藏一篇公众号文章到本地 | 想看评论 / 看留言（需登录） |
| 批量下载某个作者的文章合集 | 想下载付费内容 / 圈子文章 |
| 把公众号文章喂给 LLM / RAG（先存 MHTML 再转 MD） | 想下视频号视频（视频仍远程） |
| 公众号文章即将被删时紧急快照 | 想绕过「仅关注后查看」（本 skill 看不到） |
| 个人学习用 / 不希望登录任何账号 | 想二次发布 / 商业用途（侵权风险） |
| 不想为存文章装 150MB Chromium | |

---

## 30 秒上手

```bash
cd /Users/wanfeng/code/wanfeng-skills/skills/mp-saver

# 一次性验证（0.1 秒，仅检查 Python 版本 + dry-run）
bash scripts/install.sh

# 保存单篇
python3 scripts/save_mp.py "https://mp.weixin.qq.com/s/abc123"

# 批量
python3 scripts/save_mp.py url1 url2 url3

# 从文件
python3 scripts/save_mp.py --file urls.txt

# 限内嵌图片数（推荐，单文件控在 50MB 以内）
python3 scripts/save_mp.py --max-images 200 "https://mp.weixin.qq.com/s/abc123"

# 只跑 HTML（不下载图，最快）
python3 scripts/save_mp.py --format html "https://mp.weixin.qq.com/s/abc123"
```

详细命令见 [SKILL.md](SKILL.md) / [reference/quickstart.md](reference/quickstart.md)。

---

## v2.0 vs v1.x

| 项目 | v1.x（Playwright） | v2.0（纯 HTTP） |
|---|---|---|
| 第三方依赖 | Playwright + Chromium (~150MB) | 0（只用 Python 标准库） |
| install.sh 时长 | 1-2 分钟（含 Chromium 下载） | 0.1 秒（仅 dry-run 验证） |
| 启动速度 | 5-10 秒（浏览器冷启） | < 1 秒 |
| 反爬对抗 | 完整浏览器可绕过 | urllib 直拼 WeChat UA |
| 图片下载 | 浏览器上下文（绕过防盗链） | urllib 单线程下 |
| 写文件耗时 | 6 秒 + 下载 | 6 秒 + 下载（基本一样） |

> 💡 **为什么要换 v2.0**：v1.1 跑实战 1 篇就 77.6 MB（490 张图 base64），为了存文章装 150 MB Chromium 太重。实测 curl 同样 UA 拿同样文章，6.2 MB HTML 直接就有正文 + 真图地址，渲染不是必须。
>
> 📦 **承接关系**：v2.0 完全兼容 v1.x 的输出格式（依然 `HTML + base64 内嵌`），已存的 mhtml 文件不受影响。

---

## 输出示例

跑完会得到：

```
skills/mp-saver/task/20260813-ai-daily/
├── index.md                          ← 清单（标题/大小/链接/失败原因）
├── cursor-深度评测.mhtml               ← 单文件，双击可看（5-50 MB）
├── claude-code-使用心得.mhtml
└── ...更多...
```

每篇 MHTML 是单文件（含图片样式），离线双击 Chrome / Edge / Safari 即可打开。

---

## 核心特性

- 🚫 **不登录** —— 公众号文章不登录也能看，本 skill 不读 cookies、不绕反爬
- 📦 **单文件** —— MHTML 含图片样式，离线可看
- 📚 **批量** —— 一次传多个 URL，失败单篇不影响其它
- 🛡️ **URL 白名单** —— 只接受 `mp.weixin.qq.com/s/...`，其它域名一律拒绝
- 🎛️ **可控大小** —— `--max-images N` 限内嵌图片数（默认不限）
- 🚀 **零依赖** —— 只用 Python 标准库，无需 Playwright/Chromium
- 🐛 **调试友好** —— `--dry-run` 试运行；纯 stderr 报错
- 🌐 **代理友好** —— `HTTPS_PROXY=http://...` 环境变量即可
- 📝 **任务清单** —— 自动生成 `index.md`，方便回顾

---

## 技术栈

- **Python ≥ 3.10**
- **urllib / re / base64 / mimetypes / pathlib** —— Python 标准库
- **og:title 智能提取 + unlazy 修补 + 反爬兜底检测** —— 自研逻辑

无 headless 服务（v2.0 不用浏览器）；无数据库（任务清单写 Markdown 文件）。

---

## 依赖安装

`bash scripts/install.sh` 会做：

1. 检测 Python ≥ 3.10
2. 跑一次 `--dry-run` 自检

**总耗时：0.1 秒**（v1.x 这个步骤要 1-2 分钟下 Chromium）。

详见 [SKILL.md](SKILL.md) 的「核心命令速查」段。

---

## 目录结构

```
mp-saver/
├── SKILL.md                  ← 主入口（必读）
├── README.md                 ← 本文件（仓库级说明）
├── progress.md               ← 封装进度（含 v1/v2 决策记录）
├── scripts/
│   ├── install.sh            ← v2.0 起：仅 Python 版本检测 + dry-run
│   └── save_mp.py            ← 核心脚本（urllib + 智能修补）
├── reference/
│   ├── quickstart.md         ← 命令详解
│   ├── formats.md            ← MHTML（限图 / 不限）/ HTML 对比
│   ├── safety.md             ← 安全约束 + 反爬说明
│   └── troubleshooting.md    ← 6 个常见报错的 5 段式回答
└── templates/                ← 预留（未来加 task-readme 模板）
```

---

## 与其它 skill 的衔接

本 skill **不做下游联动**，但产出的 `.mhtml` 可以喂给：

| 下游 skill | 怎么用 |
|---|---|
| **doc-speedreader** | `bash ../doc-speedreader/scripts/convert.sh xxx.mhtml` → Markdown |
| 任何文本编辑器 | MHTML 双击打开 |

---

## 维护 / 贡献

- 进度日志：[progress.md](progress.md)
- 失败兜底：[reference/troubleshooting.md](reference/troubleshooting.md)
- 安全约束：[reference/safety.md](reference/safety.md)
- 加新功能 → 先改 `SKILL.md`，再补 `scripts/save_mp.py`，最后更新 `progress.md` 的版本日志
