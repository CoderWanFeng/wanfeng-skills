# doc-speedreader · 维护说明

> **本文件给维护者看**——用户不会读这个。用户看 [SKILL.md](SKILL.md)。

---

## 这是什么

`doc-speedreader`（速读侠）是一个**纯对话式、独立**的 skill，把 Microsoft **MarkItDown** 封装成"任意文档 → Markdown → 摘要/全文"的对话工作流。

**核心特性**：
- 15+ 格式一键转 Markdown
- 3 类产物：TL;DR（一句话）/ 结构化摘要 / 完整副本
- 默认 3 轮对话结束，最快 10 秒拿到结论
- **完全独立**——不与其他 skill 做任何联动

---

## 目录结构

```
doc-speedreader/
├── SKILL.md                # ⭐ 主入口（对话流程 + frontmatter）
├── README.md               # 本文件（维护说明）
├── scripts/
│   ├── install.sh          # 一键装 markitdown[all]
│   └── convert.sh          # 4 种模式调 markitdown
├── reference/
│   ├── quickstart.md       # 5 分钟跑通
│   ├── formats.md          # 15+ 格式支持矩阵
│   ├── safety.md           # 路径安全约束
│   └── troubleshooting.md  # 8 个常见报错 + 5 段式
├── templates/
│   └── summary-template.md # 结构化摘要模板
└── task/                   # 用户的历史 task（自动生成）
    └── README.md
```

---

## 维护职责

| 任务 | 频率 | 谁做 |
|---|---|---|
| MarkItDown 主版本升级测试 | 每次 PyPI 发布新版 | 维护者 |
| 新格式支持（如新加的 Office 365 格式） | 出现即加 | 维护者 |
| 修复脚本 bug | 即时 | 维护者 |
| 新增 troubleshooting 案例 | 用户报上来就加 | 维护者 |
| `reference/formats.md` 表格更新 | MarkItDown 升级时 | 维护者 |

---

## 依赖

- **Python ≥ 3.10**（markitdown 硬要求）
- **MarkItDown ≥ 0.1.x**（最新稳定版）
- **PDF / Word / PPT / Excel** 的可选 extras（推荐装 `[all]` 一劳永逸）

装依赖一行命令：

```bash
pip install 'markitdown[all]'
```

或用本 skill 自带的：

```bash
bash scripts/install.sh
```

---

## scripts/convert.sh 调用模式

| 模式 | 命令 | 调用的 markitdown API | 安全级别 |
|---|---|---|---|
| 本地文件 | `convert.sh <path>` | `convert_local()` | 🟢 最窄权限 |
| URL | `convert.sh https://...` | `convert()` | 🟡 带 10s 超时 |
| stdin | `cat x.pdf \| convert.sh --stream .pdf` | `convert_stream()` | 🟡 需指定扩展名 |
| Response | `convert.sh --response <url>` | `convert_response()` | 🟢 用户自己控制网络层 |

**安全原则**：能窄就窄。本地文件永远走 `convert_local()`。

---

## 常见问题排查

### 安装失败

```bash
# 1. Python 版本不够
python3 --version  # 必须 ≥ 3.10

# 2. pip 慢 → 切阿里源
pip install -i https://mirrors.aliyun.com/pypi/simple/ 'markitdown[all]'

# 3. M1/M2 Mac 上某些 extras 编译失败
#    装预编译 wheel：
pip install --only-binary=:all: 'markitdown[all]'
```

详见 [reference/troubleshooting.md](reference/troubleshooting.md)。

### 转 PDF 没文字

PDF 可能是**扫描件**（图片 PDF）。MarkItDown 默认不识别扫描件。

3 种解法：
1. 装 OCR 插件：`pip install markitdown-ocr` + 配 `llm_client`
2. 用 Azure Document Intelligence（要 Azure 账号）
3. 换工具：PaddleOCR / Tesseract

### 转 PPT 没图描述

默认不调 LLM。要开就：

```python
from markitdown import MarkItDown
from openai import OpenAI
md = MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o")
```

但 v1 默认不引导用户这么做（要 OpenAI key 是门槛）。

---

## changelog

# 2026-07-16 · v1

**新发布**
- 第 1 版上线
- 4 模式调 markitdown（local / URL / stream / response）
- 3 类产物（TL;DR / 结构化摘要 / 完整副本）
- 8 个常见报错的 5 段式兜底
- **完全独立**——不与其他 skill 联动

---

## 已知边界（v1 不做）

- ❌ 多文件批量（一次一个）
- ❌ 默认 LLM 图像描述（要 OpenAI key 是门槛）
- ❌ 默认 Azure 集成
- ❌ 默认 OCR 插件（扫描件 PDF 走不通）
- ❌ 与其他 skill 联动（**用户明确要求独立**）

---

## 未来候选功能（v2+）

- 批量速读（一次 10 个文件，每个自动 TL;DR）
- "对比模式"（速读两份文档，AI 自动出对比表）
- LLM 图像描述开关（让用户传 OpenAI key）
- 与其他 skill 的硬链接（**前提：用户主动要求**）