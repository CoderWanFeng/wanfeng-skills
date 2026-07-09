---
name: hot-topic-radar
description: 自媒体选题雷达。7×24h 监控全网热搜（微博/抖音/知乎/小红书/B站/今日头条/百度等），按用户关键词过滤、按领域相关性打分、按热度排序，输出"今天值得跟"的选题清单。配套关键词白名单、记忆去重、跨平台聚合。本 skill 是独立任务，不涉及后续创作/发布等下游流程。
---

# 自媒体热点雷达 · Hot Topic Radar

> **本文件做什么**：监控全网热搜 → 按关键词/领域过滤打分 → 输出今天的 TOP 选题清单 → **到此结束**。
>
> 本 skill 是一个**独立任务**，不涉及任何下游（写公众号/写口播稿/拍视频/发布等）。雷达只负责"告诉你今天发生了什么、哪个值得跟"，**不替你决定写什么、怎么写**。

> **流程顺序**：
> 1. **拉数据**（多平台热搜，按平台分别抓）
> 2. **关键词过滤 + 领域相关性打分**
> 3. **记忆去重**（同一热点 N 天内不重复推送）
> 4. **按 `热度 × 相关度` 排序**，输出 TOP 清单
> 5. **到此结束**

---

## §零、定位与边界

### ✅ 这个 Skill 做什么

| 能力 | 说明 |
|---|---|
| **全平台聚合** | 微博 / 抖音 / 知乎 / 小红书 / 百度 / 今日头条 / B 站 等多源热搜统一拉取 |
| **关键词过滤** | 只推用户配置的关键词/领域相关内容，不喂噪音 |
| **记忆去重** | 已推送过的热点在 N 天内（默认 7 天）不再重复推 |
| **热度 + 相关度打分** | `score = 热度值 × 领域相关度`，综合排序 |
| **选题候选清单** | 按分值倒序输出 TOP N（默认 10），附原文链接 |
| **可选：竞品监控** | 监控指定账号列表的最近动态 |

### ❌ 这个 Skill **不**做什么

| 不做 | 原因 |
|---|---|
| ❌ 不写文章 / 文案 / 视频脚本 | 下游任务，由其他 skill 负责 |
| ❌ 不主动发对外内容 | 雷达只做情报收集，发不发由用户决定 |
| ❌ 不替你消费选题清单 | 推不推、跟不跟由用户决定 |
| ❌ 不爬需要登录才能看的页面 | 公开热搜/公开账号动态即可，登录态一律不碰 |
| ❌ 不编造数据 | 来源不明的标注"待核实" |

---

## §一、配置项（`radar-config.yaml`）

```yaml
# 选题雷达配置

# ---------- 基础 ----------
timezone: Asia/Shanghai          # 时区（默认北京时间）
lookback_hours: 24                # 拉数据时间窗（小时）
top_n: 10                         # 输出 TOP N 条候选

# ---------- 关键词 / 领域 ----------
# 多个关键词用 OR 逻辑；领域关键词做相关度匹配
keywords:
  - AI
  - 大模型
  - ChatGPT
  - Claude
  - Sora
  - 编程
  - 副业

# 排除关键词（命中则直接过滤掉）
exclude_keywords:
  - 娱乐
  - 明星
  - 电视剧

# ---------- 平台 ----------
# 启用的平台列表，按需增删
platforms:
  - weibo         # 微博热搜
  - douyin        # 抖音热搜
  - zhihu         # 知乎热榜
  - xiaohongshu   # 小红书热门
  - bilibili      # B 站热门
  - toutiao       # 今日头条
  - baidu         # 百度热搜

# ---------- 评分权重 ----------
weights:
  hotness: 0.6       # 热度权重（原始热搜排名）
  relevance: 0.4     # 相关度权重（命中关键词的强度）

# ---------- 记忆去重 ----------
dedup:
  enabled: true
  window_days: 7      # N 天内已推过的热点不再出现
  memory_file: memory/dedup-history.jsonl

# ---------- 竞品监控（可选） ----------
competitor_monitor:
  enabled: false      # 默认关闭，需要时手动启用
  accounts: []        # 账号列表，如 ["机器之心", "量子位"]
  platform: xiaohongshu

# ---------- 路径 ----------
paths:
  project_root: .                 # 项目根目录（脚本相对路径基准）
  output_dir: workflow/每日热点/  # 候选清单输出目录
  memory_dir: memory/             # 记忆/去重文件目录
```

> 所有路径默认相对 `project_root`。脚本读取时优先用 `--config` 指定，否则默认读脚本同级目录的 `radar-config.yaml`。

---

## §二、数据源与抓取策略

### 2.1 平台数据源

| 平台 | 推荐数据源 | 实现难度 |
|---|---|---|
| **微博** | 微博热搜公开接口 / 第三方聚合站（如新榜、清博） | ⭐ 简单 |
| **抖音** | 抖音热点榜公开页面 | ⭐⭐ 中等 |
| **知乎** | 知乎热榜 API（公开） | ⭐ 简单 |
| **小红书** | 小红书热门页面 / 第三方聚合 | ⭐⭐⭐ 较难（反爬严） |
| **B 站** | B 站热门排行榜公开 API | ⭐ 简单 |
| **今日头条** | 今日头条热榜（公开接口） | ⭐ 简单 |
| **百度** | 百度热搜公开接口 | ⭐ 简单 |

### 2.2 抓取脚本（`scripts/fetch_hot.py`）

主流程：

```python
import json, re, time
from datetime import datetime, timedelta
from pathlib import Path

def fetch_platform(platform: str, cfg: dict) -> list[dict]:
    """按平台分发到不同抓取函数。"""
    handler = PLATFORM_HANDLERS.get(platform)
    if not handler:
        return []
    return handler(cfg)

def normalize(item: dict, platform: str) -> dict:
    """把不同平台的热搜条目归一化为统一 schema。"""
    return {
        "platform": platform,
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "hot_value": item.get("hot", 0),
        "timestamp": item.get("timestamp", ""),
        "raw": item,
    }
```

每个平台一个 handler，按 JSON / HTML 解析分别实现。

### 2.3 反爬与重试

- 每个抓取函数必须有 **3 次重试**（`timeout=20s`、指数退避）
- 加 `User-Agent`（真实浏览器 UA）+ `Accept-Language` + `Referer`（参考 `aihot-topic-selector/scripts/fetch_aihot.py` 的修复经验）
- 处理 **gzip/deflate** 响应（urllib 不自动解压）
- 403 / SSL handshake timeout 必须走 retry，不直接报失败

---

## §三、关键词过滤 + 相关度打分

### 3.1 关键词命中逻辑

```python
def relevance_score(title: str, keywords: list[str], exclude: list[str]) -> float:
    # 排除关键词命中 → 直接 0
    for ex in exclude:
        if ex.lower() in title.lower():
            return 0.0
    # 命中得分：每命中一个 +0.25，封顶 1.0
    score = 0.0
    for kw in keywords:
        if kw.lower() in title.lower():
            score += 0.25
    return min(score, 1.0)
```

### 3.2 综合打分

```
final_score = hotness × weights.hotness + relevance × weights.relevance
```

热度归一化：

| 平台原始热度 | 归一化（0-1） |
|---|---|
| 热搜第 1 位 | 1.0 |
| 热搜第 10 位 | 0.5 |
| 热搜第 50 位 | 0.1 |
| 不在热搜前列 | 按对数衰减 |

---

## §四、记忆去重（避免重复推送）

### 4.1 原理

- 维护一个 `memory/dedup-history.jsonl` 文件，每行一条已推送过的热点记录
- 字段：`{ "title": "...", "platform": "...", "pushed_at": "YYYY-MM-DD HH:MM:SS", "url": "..." }`
- 每次运行：先读历史 → 对今天的新热搜做模糊匹配 → `window_days` 天内已存在的跳过

### 4.2 模糊匹配

用 `rapidfuzz.fuzz.ratio` ≥ 85（标题 15% 以内的差异视为同一条），避免小幅改写也算"新热点"。

### 4.3 清理机制

每 30 天自动清理 `window_days` 之外的旧记录，防止文件无限膨胀。

---

## §五、输出格式（候选清单）

### 5.1 控制台输出（`--stdout`）

```
========== 今日选题候选（TOP 10）==========
[87.3] 微博 / 00:15
  「OpenAI 推出 GPT-6，多模态能力大幅提升」
  → https://weibo.com/...
  → 命中关键词：AI、ChatGPT
  → 热度 92 × 相关度 0.75 = 87.3

[76.1] 知乎 / 09:42
  「Claude 4.5 在编程任务上首次超越 GPT-6」
  → https://zhihu.com/...
  → 命中关键词：AI、Claude
  → 热度 81 × 相关度 0.75 = 76.1
============================================
```

### 5.2 文件输出（默认）

文件路径：`{output_dir}/YYYY-MM-DD-hot-topics.md`

格式：

```markdown
---
title: 每日选题候选 · YYYY-MM-DD
date: YYYY-MM-DD HH:MM:SS
tags: [每日选题, 自媒体, 内部文档]
categories: [工作流程, 选题雷达]
---

# 每日选题候选 · YYYY-MM-DD

> 自动生成于 YYYY-MM-DD HH:MM:SS
> 关键词：AI / 大模型 / ChatGPT / Claude / ...
> TOP N：10

## 1. OpenAI 推出 GPT-6，多模态能力大幅提升
- **平台**：微博
- **发布时间**：00:15
- **热度值**：92 / 100
- **相关度**：0.75（命中：AI、ChatGPT）
- **综合分**：87.3
- **链接**：https://weibo.com/...

## 2. ...
```

### 5.3 不要输出的东西

- ❌ 不要写"为什么这个选题值得跟"——这是下游的事
- ❌ 不要写选题对应的 AI 概念（Token/RAG/Agent 等）——下游脚本会用核心 2 问筛
- ❌ 不要写文章大纲/标题候选——下游 skill 的事
- ❌ 不要给选题打分"易写度/传播力"等主观维度——避免幻觉

---

## §六、运行方式

```bash
# 跑今天
python scripts/fetch_hot.py

# 指定日期
python scripts/fetch_hot.py --date 2026-07-10

# 只打印候选清单，不写文件
python scripts/fetch_hot.py --stdout

# 指定配置
python scripts/fetch_hot.py --config /path/to/radar-config.yaml

# 启用竞品监控（仅当 competitor_monitor.enabled = true 时生效）
python scripts/fetch_hot.py --with-competitors

# 清空记忆（强制重推）
python scripts/fetch_hot.py --clear-memory
```

---

## §七、与其他 Skill 的衔接

| 下游 Skill | 用途 | 参考 |
|---|---|---|
| **aihot-topic-selector** | 同样做"选题"，但专注 AI 圈（AIHOT 数据源） | `skills/aihot-topic-selector/` |
| **写公众号** | 写公众号长文 | 用户自有流程 |
| **写口播稿** | 写短视频脚本 | 用户自有流程 |
| **content-calendar** | 选题进选题日历管理 | 用户自有流程 |

> 本 skill 与 `aihot-topic-selector` 是**互补关系**：
> - **本 skill**：跨平台通用自媒体雷达，关心"今天全网什么火"
> - **aihot-topic-selector**：专注 AI 圈，关心"AI 圈什么火"+ 按核心 2 问筛 1 条
>
> 两个 skill 都输出"候选清单"，但**不冲突**，可并行使用。

---

## §八、目录结构

```
skills/hot-topic-radar/
├── SKILL.md                  ← 本文件
├── scripts/
│   └── fetch_hot.py          ← 主抓取脚本（占位，待实现）
├── memory/                   ← 记忆/去重数据
│   └── dedup-history.jsonl   ← 历史推送记录
├── task/                     ← 选题任务目录（可选）
├── radar-config.example.yaml ← 配置示例
└── radar-config.yaml         ← 当前默认配置
```

---

## §九、故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 某个平台 0 条 | 抓取被反爬 / 接口变了 | 换数据源，或从配置里临时禁用该平台 |
| SSL handshake timeout | urllib 默认 UA 被判反爬 | 改用真实浏览器 UA + Accept-Language（参考 §2.3） |
| 全是重复热点 | 记忆没清空 | `python scripts/fetch_hot.py --clear-memory` |
| 候选清单质量差 | 关键词太宽或太窄 | 调 `keywords` / `exclude_keywords` / `weights.relevance` |
| 抓取失败 403 Forbidden | 缺 `mode=all` 或 Referer | 补 Header，参考 `aihot-topic-selector` 修复经验 |

---

## §十、版本历史

- **v0.1（2026-07-10）** · 初版
  - 定义 Skill 定位与边界
  - 7 步流程：拉数据 → 过滤打分 → 记忆去重 → 排序输出
  - 配置文件 `radar-config.yaml` 规范
  - 与 `aihot-topic-selector` 的关系说明
  - 抓取脚本 `scripts/fetch_hot.py` 待实现（占位）