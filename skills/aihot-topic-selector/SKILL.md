---
name: aihot-topic-selector
description: 从 AIHOT 热点里选题。每天跑一次：拉数据 → 写每日热点汇总 → 按核心 2 问选 1 条 → 建 task 目录。配套 scripts/fetch_aihot.py 拉数据。本 skill 独立运行，不涉及后续公众号/口播稿等下游流程。
---

# 选题指南 · AIHOT 每日选题 skill

> **本文件做什么**：从 AIHOT 热点里选题 → 在 `task/` 目录里创建工作目录 → **到此结束**。
>
> 本 skill 是一个**独立任务**，不涉及任何下游（公众号/口播稿/视频/其他）。选题结束后，由用户自行决定如何消费 `task/` 目录里的产物。

> **流程顺序**：
> 1. **拉 AIHOT 数据** → **立刻写当日 `每日热点/YYYYMMDD.md` 汇总**
> 2. **过滤今天 + 评分 ≥ `min_score` + 按核心 2 问选 1 条**
> 3. **建 task 目录**（目录名 = `YYYYMMDD-<slug>`，**新任务强删日期前缀**，历史 task 不动）
> 4. **到此结束**

---

## §一、每日热点汇总规范

> **每次拉 AIHOT 数据后，必须先在用户配置的「每日热点目录」下写当天的汇总文件**，再去选题。

### §一·0 配置项（`topic-config.yaml`）

```yaml
daily_dir: workflow/每日热点/        # 每日热点目录（相对项目根）
min_score: 50                       # 选题阶段最低 AIHOT 评分
lookback_hours: 30                  # 拉数据时间窗（小时）
fuzzy_match_threshold: 90           # 标题去重阈值（0-100）
timezone: Asia/Shanghai             # 选题时区
project_root: .                     # 项目根目录（脚本相对路径基准）
```

> 所有路径默认相对 `project_root`。脚本读取时优先用 `--config` 指定，否则默认读脚本同级目录的上一级 `../topic-config.yaml`（即本 skill 根目录）。

### 文件命名
- **格式**：`YYYYMMDD.md`（如 `20260623.md`）
- **目录**：`daily_dir` 配置项（默认 `workflow/每日热点/`）
- **每天一个文件**：多次运行自动追加到同一文件的「## 更新于 HH:MM:SS」区块

### 文件 Front Matter

```yaml
---
title: 每日AI热点汇总 · YYYY-MM-DD
date: YYYY-MM-DD HH:MM:SS
tags: [每日AI热点, 内部文档]
categories: [工作流程, AI热点汇总]
cover: https://images.unsplash.com/photo-1611162600?w=1200&auto=format&fit=crop
description: AIHOT 每日热点自动汇总，YYYY-MM-DD 当天共采集 N 条
---
```

### 文件内容结构

```markdown
# 每日AI热点汇总 · {date}

> 自动收集于 {date} {time}
> 文件用途：每日选题参考，可直接用作内部追溯

## 更新于 HH:MM:SS

### 1. 热点标题
- **AIHOT 评分**：XX
- **发布时间**：HH:MM
- **来源**：xxx
- **链接**：xxx
- **简介**：xxx

### 2. ...

> 本次新增 N 条，跳过重复 M 条
```

> ⚠️ **历史文件遗留问题**：20260623.md 实际 H1 写的是 `# 每日热点汇总 · {date}`（少 "AI"），与本规范不一致。本规范以 `# 每日AI热点汇总 · {date}` 为准；后续新文件统一按规范写，旧文件后续 review 时一并统一。

### 重复处理
- **去重**：对标题做正则清洗（去 `【】`、`()`、`[]`、公众号名后缀、`- IT之家` 等）后用 `rapidfuzz.fuzz.ratio` ≥ `fuzzy_match_threshold`（默认 90）模糊匹配
- **重复**：跳过，不更新评分
- **全部重复**：写入"⚠️ 本次采集的 N 条热点全部已存在，无新增内容"

---

## §二、选题原则

### 核心 2 问（必须同时满足）

| 问题 | 说明 | 示例 |
|---|---|---|
| **大众能听懂吗？** | 不需要专业背景，新闻本身有传播性 | "Netflix 省了 95% 的 AI 字费" ✅ / "transformer 注意力机制数学推导" ❌ |
| **能解释一个热门 AI 知识/原理吗？** | 借新闻讲清 Token / LLM / RAG / Agent / 思维链 / 上下文窗口等热门概念 | "Headroom 这个工具讲清了 Token 压缩原理" ✅ / "某公司融资了" ❌ |

**这 2 个都答"是"再继续，否则换题。**

### 选题核心方向：以读者为中心的"占便宜"型机会

> 每个选题都要回答：
> - **读者能得到什么具体利益**？（省钱 / 免费 / 工作机会 / 学习资源）
> - **读者能立即做什么**？（点击链接 / 注册 / 申请 / 学习）
> - **有什么限制或截止日期**？（限时 / 限地区 / 限人群 / 名额）

#### 4 大优先方向

**🥇 方向 1：AI 工具免费薅羊毛（最高优先级）**
- 免费资格 / 注册步骤 / 访问要求 / 使用限制 / 避坑提示

**🥈 方向 2：AI 产品限时优惠/试用（次高优先级）**
- 优惠力度 / 时间限制 / 参与条件 / 使用步骤 / 风险提示

**🥉 方向 3：AI 公司招聘机会（中优先级）**
- 岗位信息 / 任职要求 / 申请流程 / 截止时间 / 公司福利

**🏅 方向 4：AI 学习资源/课程免费学（基础优先级）**
- 资源类型 / 价格说明 / 学习路径 / 时长难度 / 证书价值

### 评分 None 处理

- `AIHOT 评分 = None` 的条目按 **0** 计算，不参与 `min_score` 阈值过滤
- 如果被人工选入主题，需在 task 目录的 `00-选题依据.md` 中明确注明"无评分 / 主观选入"

### 加分项

| 问题 | 说明 |
|---|---|
| 能跑通代码/有截图？ | 教程感更强 |
| 有省钱/免费属性？ | 传播力强 |
| 有大厂名（OpenAI / Google / 字节 / 美团）？ | 搜索友好 |
| 能在 2 小时内写完？ | 节奏可控 |

---

## §三、选题流程（5 步）

### 步骤 1：拉 AIHOT 数据

```bash
python scripts/fetch_aihot.py                # 跑今日
python scripts/fetch_aihot.py --dry-run     # 只打印不写
python scripts/fetch_aihot.py --date 20260701 --config /path/to/config.yaml
```

脚本核心逻辑（详见 `scripts/fetch_aihot.py`）：

```python
import urllib.request, json, urllib.parse
from datetime import datetime, timedelta, timezone

BASE = 'https://aihot.virxact.com'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

def get(path, params=None):
    url = BASE + path
    if params: url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

since = (datetime.now(timezone.utc) - timedelta(hours=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
data = get('/api/public/items', {'mode': 'all', 'since': since})
items = data.get('items', [])
```

### 步骤 2：过滤"今天"（北京时间）

```python
import re
from zoneinfo import ZoneInfo

CST = ZoneInfo('Asia/Shanghai')

def to_cst(iso):
    dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return dt.astimezone(CST)

today = datetime.now(CST).date()  # date 对象，不转字符串
today_items = []
for item in items:
    pub = item.get('publishedAt', '')
    if not pub:
        continue
    cst = to_cst(pub)
    if cst.date() == today:                       # 对象比较，避免字符串格式细节翻车
        item['cst_time'] = cst.strftime('%H:%M')
        item['score'] = item.get('score') or 0    # None → 0
        today_items.append(item)
```

### 步骤 3：按"核心 2 问" + 评分门槛筛选

**先过评分门槛**：从 `today_items` 里筛 `score >= min_score`（默认 50）。
> 阈值在 `topic-config.yaml` 的 `min_score` 配置项里调整；可根据实际数据密度上下浮动。

**再过核心 2 问**：人工从评分达标的条目里选 **1 条主题**，记录：

| 信息 | 填什么 |
|---|---|
| 日期 | YYYY-MM-DD |
| slug | 英文短横线，如 `netflix-headroom-save-token` |
| 主题一句话 | 用 1 句话说清楚这条热点是什么 |
| 对应 AI 知识 | Token / 上下文窗口 / RAG / Agent / ...（选一个热门概念） |
| AIHOT 评分 | XX（None 时注明"主观选入"） |

### 步骤 4：Fallback 分支

如果 `today_items` 中没有符合核心 2 问的条目：

1. **优先放宽窗口**：脚本会自动把 `lookback_hours` 从 30 拉到 168（7 天）重试一次
2. **仍无合适选题**：在 `workflow/每日热点/YYYYMMDD.md` 末尾追加：
   ```markdown
   ## 今日无合适选题
   > 原因：YYYY-MM-DD 当日 N 条热点全部不符合核心 2 问
   > 操作：跳过今日选题，下一个工作日继续
   ```
3. **不要硬选**：宁可跳过，也不要把不达标的条目塞进选题

### 步骤 5：建 task 目录（**新任务强删日期前缀**）

> ⚠️ **历史 task 目录（如 `netflix-headroom-save-token`）暂不动**；仅从本文档生效日起，**新创建的 task 目录必须带 `YYYYMMDD-` 前缀**。
>
> ⚠️ **task 根目录**：本 skill 的所有 task 放在 `<skill 根目录>/task/` 下（如 `todo/选题/task/`），与公众号解耦。

最小骨架：

```
YYYYMMDD-<slug>/
├── 00-选题依据.md       # 必填：核心 2 问答案 + 对应 AI 概念 + 评分
├── 01-资料收集.md       # 选填：原文链接、截图、补充信息
└── imgs/                # 选填：原始截图（任何后续阶段可复用）
```

建好后，在 `00-选题依据.md` 写入：

```markdown
# 选题依据 · YYYY-MM-DD <slug>

## 主题
<一句话说明这条热点是什么>

## 核心 2 问
- 大众能听懂吗？ ✅/❌ <理由>
- 能解释一个热门 AI 知识/原理吗？ ✅/❌ <理由>

## 对应 AI 知识
<Token / 上下文窗口 / RAG / Agent / ...>

## AIHOT 评分
<XX 或 "None · 主观选入">

## 资料
- 原文链接：<url>
- 截图：<imgs/ 下文件列表>
```

---

## §四、本 skill 范围到此结束

**本 skill 的产出物**：
- 1 份 `每日热点/YYYYMMDD.md`（AIHOT 当日全部热点快照 + 选题候选清单）
- 1 个 task 目录（`task/YYYYMMDD-<slug>/`），含 `00-选题依据.md` + 可选资料

**本 skill 不负责**：
- ❌ 公众号长文写作（自行决定是否消费 task 目录）
- ❌ 口播稿 / 短视频脚本
- ❌ 任何下游产出物的具体形式

> **设计哲学**：选题是独立任务，**不预设下游消费者**。用户拿到 `task/YYYYMMDD-<slug>/` 后，自行决定走哪个流程（写公众号 / 做口播 / 发博客 / 仅作内部参考 / ...）。

---

## §五、选题参考表

### ✅ 强推选题（4 大方向）

#### 🥇 方向 1：AI 工具免费薅羊毛
- 大模型免费用（GPT / Claude / Gemini / 文心 / 通义 / DeepSeek）
- AI 编程工具免费（Cursor / Claude Code / Copilot / Qoder）
- AI 绘图/视频免费（Midjourney / Sora / Runway / 即梦 / 可灵）
- 开源模型本地部署（Llama / GLM / Qwen / DeepSeek）
- 免费 API 额度（新用户送 tokens）

#### 🥈 方向 2：AI 产品限时优惠/试用
- 首月/首年免费（订阅服务首月 0 元）
- 新用户优惠（新人折扣、1 元体验）
- 学生/教师优惠（教育免费/折扣）
- 老用户回归礼
- 节日大促（618 / 双11 / 黑五）

#### 🥉 方向 3：AI 公司招聘机会
- 大厂 AI Lab 招聘（字节、阿里、腾讯、百度、美团）
- AI 独角兽招聘（智谱、月之暗面、MiniMax、零一万物）
- 海外大厂中国团队（OpenAI / Anthropic / Google）
- 校招/实习
- 内推码/专场

#### 🏅 方向 4：AI 学习资源/课程免费学
- 大厂免费课（Google / Microsoft / AWS / 阿里云）
- 顶尖教授免费课（吴恩达 / 李宏毅 / 李沐）
- 认证免费/折扣（AWS/Azure/GCP）
- 训练营/挑战赛（Kaggle / 天池 / Datawhale）
- 开源教材

### ❌ 不写选题

| 标签 | 原因 |
|---|---|
| 纯人事变动 | 无知识角度，无读者利益 |
| 医疗/健康问答 | 合规禁忌 |
| 纯政策/法案 | 无技术切入点 |
| 硬件发布（芯片/显卡） | 读者无法参与 |
| 太底层的技术细节 | 大众听不懂 |
| 纯观点/纯评论 | 无事实锚点 |
| AI 公司融资新闻 | 除非附带招聘或产品免费信息 |
| AI 产品发布但无免费/优惠 | 读者无法立即参与 |

### 边界澄清

| 易混对 | 区分规则 |
|---|---|
| "纯人事变动" ❌ vs "AI 公司招聘机会" 🥉 | **人事变动**特指任免/离职/跳槽等组织行为；**AI 招聘**特指岗位信息开放、任职要求、申请流程、截止时间——后者对读者是「工作机会」，可写 |
| "硬件发布（芯片/显卡）" ❌ vs "AI 工具免费薅羊毛" 🥇 | **单纯规格/价格新闻**不写；但**硬件免费送/抽奖/试用**仍归"🥇 方向 1" |
| "AI 产品发布但无免费/优惠" ❌ vs "🥇 方向 1" | 若产品对应读者核心利益（如**开源模型权重可下载**、**开源工具可自部署**），仍按"🥇 方向 1"写 |
| "AI 公司融资" ❌ vs "AI 公司招聘" 🥉 | 单纯融资不写；但融资新闻**附带招聘专场/内推码**时可按"🥉 方向 3"写 |