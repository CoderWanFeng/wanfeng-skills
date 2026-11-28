# 晚枫爆款数据分析（wanfeng-hit-ops）

> 把各平台后台导出的原始文件，变成「下期做什么选题」的结论。

## 为什么有它

自媒体账号后台数据有个普遍问题：**表格攒了一堆，但从来看不出「什么选题好」。**

原因通常不是没数据，而是三个：

1. **看错指标** —— 盯着播放量排榜，而播放量是分发决定的，不是内容决定的
2. **口径混用** —— 累计值和当日增量混在一起算，原始导出和页面摘录混在一起用，结论直接失真
3. **只看成功案例** —— 报告里全是「这条爆了」，没有反例，读者学不到边界

这个 skill 把这三件事做成流程：强制用效率指标、强制声明口径、强制写反例。

## 核心主张

**判断内容好坏不看播放量，看每千播放涨粉与每千播放收藏。**

实证：2026-10 视频号两条内容播放量差 8%，但每千播放涨粉差 5 倍（9.87 vs 1.83）。按播放量看是并列的两个爆款，按涨粉效率看是两类完全不同的内容。

## 快速开始

```bash
# 1. 环境自检（第一次用先跑这个）
uv run --with pandas --with xlrd --with openpyxl python3 scripts/check_env.py --root <数据根目录>

# 2. 新下载的文件丢进 <数据根目录>/临时文件夹/，然后归类
uv run --with pandas --with openpyxl python3 scripts/classify.py --root <数据根目录>          # 预览
uv run --with pandas --with openpyxl python3 scripts/classify.py --root <数据根目录> --apply  # 执行

# 3. 解析校验
uv run --with pandas --with xlrd --with openpyxl python3 scripts/parse_data.py --root <数据根目录>

# 4. 爆款归因
uv run --with pandas --with xlrd --with openpyxl --with numpy python3 scripts/analyze.py --root <数据根目录> --month 2026-11

# 5. 出月度报告
uv run --with pandas --with xlrd --with openpyxl python3 scripts/monthly_report.py --root <数据根目录> --month 2026-11

# 6. 改了计算层后跑自检
uv run --with pandas --with xlrd --with openpyxl python3 scripts/analysis/selftest.py --root <数据根目录> --month 2026-11
```

数据根目录的结构：

```
<root>/
├── 临时文件夹/          # 下载收件箱
├── 账号数据/<平台>/<账号>/<YYMMDD>/   # 原始数据
└── 月度报告/YYYY-MM/   # 结论
```

## 设计要点

| 机制 | 为什么这么设计 |
|---|---|
| **平台层不能省** | 同名账号跨 6 个平台存在，平铺会导致路径无法反推账号名 |
| **归类判不准就不动** | 归错账号比不归更危险——错误会被后续脚本当成事实 |
| **B站三口径分离** | 混在一起做日期去重会把先到的整段冲掉（踩过：90 天播放数据整段消失） |
| **数据层/判断层分离** | 能算出来的不让人写，需要判断的不让脚本编 |
| **每节必写反例** | 只列成功案例的报告没有信息量 |
| **指标用效率不用绝对值** | 绝对值受分发影响，效率才反映内容价值 |
| **只分析不创作** | 借来的标题公式、价值类型只用于给已发布内容打标评估；不生成标题、脚本、选题、封面文案或排期 |

## 目录

```
wanfeng-hit-ops/
├── SKILL.md                      # 主定义：流程 + 核心口径 + 硬规则
├── references/
│   ├── data-pipeline.md          # 目录约定、归类打分、解析口径、数据源清单
│   ├── hit-methodology.md        # 爆款归因方法论、指标定义、反例与置信度规则
│   ├── report-spec.md            # 月度报告章节规范、判断层写法、交付清单
│   └── platforms/                # 按平台扩展的分析模块（一个平台一个文件）
│       ├── README.md             # 模块索引 + 四层规则 + 扩展契约
│       ├── _template.md          # 新平台模块的 8 节骨架
│       └── wechat.md             # 微信公众号涨粉分析（已实现）
├── scripts/
│   ├── check_env.py              # 环境自检
│   ├── classify.py               # 临时文件夹 → 账号数据 自动归类
│   ├── parse_data.py             # 各平台原始文件 → 结构化 DataFrame
│   ├── analyze.py                # 跨平台总览 + 归因（读计算层结果）
│   ├── monthly_report.py         # 月度报告生成（读计算层发现填入章节）
│   └── analysis/                 # 计算层
│       ├── schema.py             # 各平台单作品表 → 统一内容表
│       ├── efficiency.py         # 效率指标 + 四象限 + 基线 + 小基数防线
│       ├── concentration.py      # 帕累托集中度 + 标题特征/关键词分组
│       ├── relations.py          # 相关性矩阵 + 反直觉发现 + 涨粉路径
│       ├── findings.py           # 结构化发现条目
│       ├── render.py             # 发现 → 报告章节
│       ├── pipeline.py           # 编排层
│       └── selftest.py           # 回归自检
└── templates/
    └── 月度报告模板.md             # 报告章节骨架
```

## 版本

| 版本 | 说明 |
|---|---|
| v1.3.0 | **计算层落地**。新增 `scripts/analysis/` 包：口径归一（`schema.py`）、效率指标与四象限（`efficiency.py`）、帕累托与特征分组（`concentration.py`）、相关性与涨粉路径（`relations.py`）、结构化发现条目（`findings.py`）、报告渲染（`render.py`）、编排（`pipeline.py`）、回归自检（`selftest.py`）。`monthly_report.py` 与 `analyze.py` 改为读计算层结果自动填入结论摘要、数据事实、分析判断、结构拆解、关键内容表现（带每千涨粉）、反例、跨平台结构规律、平台分工、缺口表、置信度分级、候选验证方向。两道防误判机制落地：**小基数陷阱**（效率最高但绝对贡献低 → 不当冠军）与**过度表现检验**（效率差异 + 贡献超配同时成立才给中置信度）。`hit-methodology.md` §8.6/8.7 同步更新实现状态 |
| v1.2.0 | **钉死「只做数据分析、不创作内容」能力边界**（SKILL.md 开头 L0，frontmatter 同步）。把内容方法论里的逻辑**改造成评估编码**：`hit-methodology.md` 新增 §八（标题结构 `T1~T6` + 价值类型 `V1~V4` + 三个附加字段 / 指标异常排查索引 / 商单·自然分层与辛普森悖论检查 / 发布节奏作为观察变量 / 实验止损条件）；全仓把「动作型措辞」统一改成数据判定口径（重发/改标题、写成某标题、系列化、实验命名、可复用的打法等），并把报告模板与交付清单同步加上「不产出内容」检查项。**只改文档，不改任何脚本，编码统计仍待代码落地** |
| v1.1.0 | 新增 `references/platforms/` 按平台扩展的分析层；首个模块落地**微信公众号涨粉分析**（涨粉漏斗、口径字典、单篇归因、来源分层、反例对照、对标与体检）。只加分析逻辑，不改脚本、不联网、不依赖 API Key |
| v1.0.0 | 首次发布。目录重构后的四步流水线（归类→解析→归因→成稿）+ 爆款归因方法论 + 月度报告规范 |

> 后续按平台逐个补能力：复制 `references/platforms/_template.md`，写满 8 节，再更新 `platforms/README.md` 的模块清单。规则见 `SKILL.md` 第四章。

## 改计算层后必跑自检

```bash
uv run --with pandas --with xlrd --with openpyxl python3 scripts/analysis/selftest.py \
    --root <数据根目录> --month 2026-11
```

自检用历史人工核对过的数字做回归验证（抖音 36 条 / 751,930 播放 / 2,936 涨粉、
视频号 Top3 占 60.1% 涨粉、GLM-5.3 每千涨粉 9.87、纳米Work 1.83 等 17 项）。
**这些数字变了说明口径被改坏**，必须先查清原因再改。

## 与其他 skill 的关系

```
[wanfeng-hit-ops] 账号数据 → 爆款归因 → 月度报告 → 下期验证方向
    ↓ 结论回流
[hot-topic-radar] / [aihot-topic-selector]  按结论去选题
    ↓
[wanfeng-writing-partner]  公众号长文
    ↓
[cover-hero]  配图
```

这个 skill 站在内容生产链路的「起点之后」：它不产生内容，它产生**「哪类已发布内容有效、下期该验证哪个结构」的数据判断**。

> ⛔ **只做数据分析，不创作内容。** 标题公式、价值类型等外部方法论只被用作**给已发布内容打标与评估**的编码维度，不用于生成标题、脚本、正文、封面文案、选题清单、排期或变现方案。详见 `SKILL.md` 开头「能力边界」与 `references/hit-methodology.md` §八。
