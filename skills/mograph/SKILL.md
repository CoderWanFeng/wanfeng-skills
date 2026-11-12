---
name: mograph
description: 晚枫自动剪辑（mograph）——给「一个人口播」的视频自动加动效包装：根据口播稿讲的内容，卡着讲话的时间点，在人的上下左右（或身前）弹出字卡、数据、图表、对比框、清单、引用卡，再渲染成成片。v1 采用「检索驱动」架构：本 skill 不自带动效素材库，而是内置一套联网检索协议，让你本地 AI 现场拉取社区最新的 Remotion / HyperFrames 动效实现，转成引擎无关的 overlay-spec.json，再落地渲染。触发词：自动剪辑、口播加动画、口播动效、给视频贴片、加花字、加数据卡、上下左右弹卡、Remotion 口播、HyperFrames 叠加、包装视频、动效字幕。
version: 1.0.0
license: MIT-0
allowed-tools: Bash
metadata:
  emoji: "🎬"
  requires:
    bins:
      - python3
---

# 晚枫自动剪辑 · mograph

> **目录名**：`mograph/`
> **中文名**：晚枫自动剪辑
> **一句话**：一条口播视频 + 一份口播稿 → 在人的四周（或前景）按讲话内容定时弹出动效卡片 → 渲染成片。
> **v1 的核心取巧**：**skill 里不塞动效素材库**。社区每个月都在长新的 Remotion / HyperFrames 卡片，硬编码进 skill 就是给自己造过期库存。所以 skill 只沉淀三件不会过期的东西——**位置语义、时间轴契约、检索协议**——把「找最新实现」这一步交给用户本地的 AI 在运行时联网完成。

---

## 〇、三句话看懂架构

```
口播稿 ──┐
         ├─① make_spec.py ─→ overlay-spec.json（时间轴 + 位置 + 动画意图，引擎无关）
视频/音频┘                         │
                                   ├─② research-protocol.md ─→ 联网找可跑的实现 ─→ research-notes.md
                                   │
                                   └─③ engine-remotion.md / engine-hyperframes.md ─→ 渲染 ─→ final.mp4
```

| 层 | 谁负责 | 产物 |
|---|---|---|
| **骨架层** | 本地脚本 `scripts/make_spec.py`（纯标准库，秒出） | `overlay-spec.json` |
| **肌肉层** | 用户本地 AI 联网检索（Step 2 协议） | `research-notes.md` + 可复制代码片段 |
| **落地层** | Remotion（React）或 HyperFrames（HTML+GSAP）或 ffmpeg 兜底 | `final.mp4` |

**为什么分三层**：骨架层必须离线可跑（没网也能出分镜），肌肉层必须在线（保证不落后社区），落地层必须多选一（用户机器上有什么就用什么）。

---

## 一、何时使用 / 不使用

**用它的时机**（用户这么说就触发）：

- 「这条口播视频帮我加点动效」「根据我讲的内容在边上弹一些卡片」
- 「口播稿 + 配音已经有了，做成带数据图的成片」
- 「用 Remotion / HyperFrames 给口播视频做叠加」
- 「自动剪辑：说到数字就出数字、说到对比就分屏」

**不要用它**（明确转介）：

| 需求 | 应该用 |
|---|---|
| 只要字幕，不要动效 | `embedded-captions` |
| 从零做一条无人出镜的科普片 | `knowledge-short-video` |
| 只要一个动效短片头/角标 | `motion-graphics` |
| 改时长、去口水词、重新配音 | 这是 NLE 剪辑，v1 不做（见第八节） |

---

## 二、前置条件

1. **一份口播稿**（`.md` / `.txt`，每句一行或带编号最佳）。
2. **一条口播视频或音频**（`.mp4` / `.mov` / `.wav` / `.mp3`）。
3. 可选但强烈建议：**真实时间戳**，任一形式即可 —— `.srt` 字幕、`[{text,start,end}]` 的 JSON、或 `segments.txt`。
   - **没有时间戳也能跑**，但脚本会按「中文 4 字/秒」估算时长，并在输出里打 `"timing_source": "estimated"`。
   - **硬规则：估算时间绝不能当成实测时间交付**。渲染前必须让用户试听校验（见第七节硬规则 R1）。
4. 落地环境三选一，都没有就走 ffmpeg 兜底：
   - Node 18+ → Remotion / HyperFrames
   - ffmpeg → PNG 序列 + `overlay` 滤镜（最朴素但一定能出片）

---

## 三、7 步流程（agent 按此执行）

### Step 0 · 一次性确认 4 个开关（只问一轮）

| 开关 | 选项 | 默认推荐 |
|---|---|---|
| **画幅** | 竖屏 9:16 / 横屏 16:9 | 按源视频自动探测 |
| **动效密度** | 克制（每 8s 一张，同屏 1 张）/ 标准（每 5s 一张，同屏 1 张）/ 高密度（每 2.5s 一张，同屏 2 张） | ⭐ 标准 |
| **渲染引擎** | Remotion / HyperFrames / 自动选 | ⭐ 自动（装了哪个用哪个） |
| **要不要前景遮挡**（卡片压在人身前） | 要 / 不要 | ⭐ 不要（需人像抠图，v1 不承诺，见 R3） |

问完直接进入 Step 1，不要逐条追问。

### Step 1 · 出骨架（本地，离线可跑）

```bash
python3 scripts/make_spec.py \
  --script 口播稿.md \
  --video  口播.mp4 \
  --srt    字幕.srt \
  --density standard \
  --out    task/<时间戳>_motion/overlay-spec.json

# 没有视频文件、也没字幕时，至少把总时长钉准，别让字数硬估：
#   --duration 85        （优先级：实测媒体 > --duration > 稿件元信息 > 字数硬估）
```

产物就是**引擎无关的时间轴契约**：每个 `segment` 含 `start / end / text / keywords / animation.type / slot / layer`。字段含义见 `templates/overlay-spec.example.json`。

跑完先把摘要念给用户听（几张卡、分布在哪些位置、总时长覆盖度），确认没问题再往下走。**不要跳过这个确认**。

### Step 2 · ⭐ 联网补肌肉（本 skill 的核心）

按 `reference/research-protocol.md` 执行，**这一步是 agent 现场联网**：

1. 用协议里的**检索词矩阵**（8 类动画 × 中英双轨 + 限定词）搜，**硬预算：≤8 次搜索、≤4 次全文抓取**，超预算直接降级；
2. 命中候选后按**四维评分卡**（能跑 / 许可 / 引擎匹配 / 迁移成本）筛，**至少留 3 个可复制的实现**（≥7 分才入库）；
3. 每个候选落到 `research-notes.md`：来源 URL、许可、许可证边界、最小可跑片段、迁移到本项目要改哪几行；
4. **搜不到就如实降级**：走 `reference/animation-brief.md` 里自带的纯 CSS/GSAP 最小实现，绝不假装搜到了。

> 这一步的产物允许为空（离线场景），但**必须显式写明「本次未联网，使用内置最小实现」**。

### Step 3 · 逐条填动画描述

对 `overlay-spec.json` 里每个 segment，按 `reference/animation-brief.md` 的 8 类模板把「动画意图」写成具体描述（进出场、时长、缓动、元素级动画顺序），写回 `animation.brief` 字段。

分类靠关键词自动命中，agent 只做**校正**：数字类必须真的用数据组件，别退化成纯文字。

### Step 4 · 落位校验（防遮挡）

按 `reference/overlay-layout.md` 检查每张卡的 `slot`：

- **人脸安全区**（竖屏 `x 0.30–0.70`、`y 0.18–0.76`；横屏 `x 0.28–0.72`、`y 0.18–0.70`）内不得放任何卡；
- 同一时刻同屏卡片数受密度上限约束（克制/标准 1 张、高密度 2 张），**超上限的那条直接弃卡**并在 spec 里留 `dropped` 原因，而不是挤进安全区；
- 相邻两卡切换至少留 0.2s 空档，不做叠化打架。

有冲突就挪位置，不要缩卡片尺寸硬塞。

### Step 5 · 选引擎并实现

```bash
# 探测
command -v node >/dev/null && node -v; command -v ffmpeg >/dev/null && ffmpeg -version | head -1
```

| 情况 | 走哪条 |
|---|---|
| 有 Node，且用户装了 Remotion 生态 | `reference/engine-remotion.md` |
| 有 Node，且已在用 HyperFrames（含本仓库其他 skill 的链路） | `reference/engine-hyperframes.md` |
| 只有 ffmpeg | 兜底：`make_spec.py --emit-png-plan` 出计划，agent 生成 HTML → 截图 PNG 序列 → `ffmpeg -filter_complex overlay` 合成 |
| 都没有 | 只交付 `overlay-spec.json` + `research-notes.md`，明确说「本机无渲染环境，已交付分镜与检索结果」 |

**实现要求**：每张卡的文案来自 `segment.text` / `keywords`，**不许自己编数据**（R2）。

### Step 6 · 自检三闸

渲染完必须跑，且把结果如实汇报：

1. **覆盖闸**：动效总时长 / 视频总时长 ≥ 40%（低于此说明包装太薄，回 Step 3 补卡）；
2. **遮挡闸**：抽 6 帧（均匀取样），确认无卡片压脸、无卡片超出安全边距；
3. **节奏闸**：任意连续 5 秒画面内至少 1 个可见变化（新卡出现 / 已有卡数值变化）。

抽帧：`ffmpeg -ss <t> -i final.mp4 -frames:v 1 check.png`（看完即删，不在 task 目录留验证图）。

### Step 7 · 交付

```
task/<时间戳>_motion/
├── overlay-spec.json     # ⭐ 可复跑：换引擎不用重做分镜
├── research-notes.md     # 联网检索结果（来源 + 许可 + 片段）
├── src/                  # 引擎实现代码
└── final.mp4             # 成片
```

交付时必带三句话：**时间戳是实测还是估算**、**本次有没有联网**、**前景遮挡做没做**。

---

## 四、`make_spec.py` 参数

| 参数 | 作用 |
|---|---|
| `--script` | 口播稿路径（必需） |
| `--video` / `--audio` | 源媒体，用于实测时长与画幅探测 |
| `--duration` | 手给成片总时长（秒）。时长优先级：**实测媒体 > `--duration` > 稿件元信息（「时长：~85s」）> 字数硬估**，来源会打进输出摘要 |
| `--srt` / `--timestamps` | 真实时间戳（`.srt` 或 `[{text,start,end}]` JSON） |
| `--density` | `sparse` / `standard` / `high`（默认 standard，见 Step 0 的间隔/同屏数） |
| `--aspect` | `9:16` / `16:9` / `auto`（默认按视频探测） |
| `--max-slots` | **同屏并发卡上限**，覆盖密度默认值。超出上限的那条命中项会被弃卡并在 spec 里写 `dropped` 原因 |
| `--engine` | `auto` / `remotion` / `hyperframes` / `none`（写进 spec 供下游参考） |
| `--keep-meta-lines` | 把标题 / 表格 / 元信息行也当口播内容（**默认丢弃**，否则分镜时长会被非口播内容灌水） |
| `--no-net-hint` | 显式声明本次未联网，写进 `warnings`（R4） |
| `--emit-png-plan` | 额外输出 ffmpeg 兜底路线的 `ffmpeg-plan.json` |
| `--out` / `--stdout` | 写出 `overlay-spec.json` / 只打印不写文件（预览用） |

---

## 五、目录结构

```
mograph/
├── SKILL.md                          # 本文件
├── README.md                         # 30 秒上手 + 拍视频走位 + FAQ
├── scripts/
│   └── make_spec.py                  # 唯一本地脚本（Python 标准库，零依赖）
├── reference/
│   ├── research-protocol.md          # ⭐ 联网检索协议（取巧核心）
│   ├── overlay-layout.md             # 位置语义 / 人脸安全区 / 避让规则
│   ├── animation-brief.md            # 8 类动画 × 描述模板 × 内置最小实现
│   ├── engine-remotion.md            # Remotion 路线最小工程
│   └── engine-hyperframes.md         # HyperFrames 路线最小工程
└── templates/
    └── overlay-spec.example.json     # 引擎无关时间轴契约（含注释说明）
```

**依赖原则**：与仓库其他 skill 一致 —— Python 只用标准库；不引入 `requirements.txt`；ffmpeg 作为系统依赖在文档里说明安装方式；**本 skill 不调用任何付费生成 API**。

---

## 六、输出示例

下面两段是**本仓库真实稿件跑出来的**（`test/video/20260629_210000_什么是Token/01-Script/script.md`），不是示意。

**A. 只有稿件 + 手给时长（估算时间戳）**

```
$ python3 scripts/make_spec.py --script script.md --duration 85
== 口播动效骨架 ==
源视频：未提供｜85.0s（时长来源：given）｜9:16
时间戳：估算（4 字/秒）｜动画卡：8 张｜覆盖 26.1%｜单屏最多 1 张｜弃卡 0 条
分布：bottom 1｜left 1｜right 3｜top 3
类型：分屏对比(split-compare) 3｜清单逐条(checklist) 2｜品牌/产品名卡(logo-card) 2｜数字滚动卡(number-roll) 1
⚠️ 时间戳为估算（4 字/秒），交付前必须试听对齐 —— 见 SKILL.md 硬规则 R1
提示：覆盖率 26.1%，低于 Step 6 的 40% 交付闸 —— 回 Step 3 手工补卡（SKILL.md）
```

**B. 有真实时间戳（`[{text,start,end}]`）**

```
$ python3 scripts/make_spec.py --script script.md --timestamps timeline.json
== 口播动效骨架 ==
源视频：未提供｜85.0s（时长来源：script-hint）｜9:16
时间戳：实测｜动画卡：4 张｜覆盖 14.0%｜单屏最多 1 张｜弃卡 0 条
分布：right 2｜top 2
类型：品牌/产品名卡(logo-card) 3｜分屏对比(split-compare) 1
提示：覆盖率 14.0%，低于 Step 6 的 40% 交付闸 —— 回 Step 3 手工补卡（SKILL.md）
```

**怎么读这两段**：

- **卡少 ≠ 出错**。正则只吃显式结构（阿拉伯数字+单位、「不是 A 而是 B」、「第一/第二」）。中文数字、隐含对比、抽象概念**留给 Step 3 由 agent 补卡**——所以「覆盖率低于 40%」是骨架阶段的正常状态，不是交付状态。
- **B 比 A 更少是正常的**：实测模式下分句粒度跟着字幕走，不再按稿件重新切句。**不要因为数字好看就退回估算**（R1）。
- 出现「弃卡 N 条」时，说明这些句子命中了动画但同屏已满，spec 里对应段会有 `"dropped": "同屏已达上限（1 张），本条弃卡"`。想留卡就放宽上限（`--density high`，或直接 `--max-slots 2`）——但**上限是安全阀不是数字游戏**，放宽后必须回 Step 4 复核两张卡是否真的错开了。

---

## 七、硬规则（v1 不许违反）

| # | 规则 | 违反的后果 |
|---|---|---|
| **R1** | 估算时长必须标注 `estimated`，交付前必须让用户试听对齐 | 卡点和讲话错位，整片废 |
| **R2** | 卡上所有数字 / 名称 / 引语只能来自口播稿或用户提供的资料 | 编造数据，发出去就是事故 |
| **R3** | 不做人像抠图 / 前景遮挡，除非用户明确要求且接受降级（默认 `layer=behind`） | 抠图质量差会直接毁掉真人出镜 |
| **R4** | 检索失败必须显式写明「本次未联网/未命中」，不得假装引用了社区实现 | 许可与来源不可追溯 |
| **R5** | 引入任何外部代码前先确认许可；GPL / 不明许可的模板**不用**，MIT-0 / Apache-2.0 优先，并记进 `research-notes.md` | 商单成片有法律风险 |
| **R6** | 不调用任何付费接口（TTS / 生成 / 云渲染）；纯本地渲染 | 试错成本 |
| **R7** | 验证用截图看完即删，task 目录只留最终产物 | 目录脏 |

---

## 八、已知限制（v1 的坦白）

1. **不自带动效库** —— 这是设计选择，不是没做完。代价是首次运行要花 3–8 分钟联网检索；收益是不用追库存。想换成自带库，见 README「进阶：把检索结果固化成缓存」。
2. **不做剪辑** —— 去口水词、重配音、改时长都不在 v1 范围；`overlay-spec.json` 的时间轴严格按输入走。
3. **不做前景遮挡** —— 需要抠图（R3），默认卡片一律在人后面或画面空白处。
4. **图表数据不核实** —— 只搬运稿件里的数字，不联网查证、也不算账。
5. **中文优先** —— 分句、字数估算、关键词命中都按中文调；英文稿能跑但切分质量下降。
6. **渲染质量取决于本机环境** —— 没有 Node 只能走 ffmpeg 兜底，动效会明显朴素一档。
7. **`--timestamps` 模式不重新分句** —— 给了真实时间戳后，句子粒度完全跟着字幕走，命中率可能低于估算模式（估算会把稿件重新切成更细的句子）。这是取舍而非 bug：时间准确性 > 卡片数量，缺的卡在 Step 3 补。

---

## 九、与仓库其他 skill 的衔接

```
knowledge-short-video（写口播稿）
        ↓  稿子 + segments.txt
[mograph] ← 真人出镜的动效包装（本 skill）
        ↓  overlay-spec.json
cover-hero / hyperframes 生态 ← 封面与视觉风格复用同一套设计令牌
```

- 输入侧可直接吃 `knowledge-short-video` 的 `script.md` 与 `segments.txt`（已支持该格式）。
- 无真人出镜、整条片都要生成的场景 → 继续用 `knowledge-short-video`，不要用本 skill。
