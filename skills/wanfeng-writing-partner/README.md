# wanfeng-writing-partner · 晚枫写作搭子

> **本文件给维护者看**——用户读 [SKILL.md](SKILL.md)。

---

## 这是什么

把「晚枫每天写公众号文章实际在用的流程」固化成一个 Skill：从一个 AI 热点 / 产品体验 / 官方资料，到一份可以直接复制进编辑器的 Markdown 成稿。

**核心特性**：

- 7 步工作流：选题素材 → 起标题 → 判类型搭结构 → 配图 → 上传图床 → 插入图片与链接 → 发布前检查
- **写法来自 4 篇高互动实证文章**：利益前置标题、第一句给结果、主动亮短板、共情自嘲、决策信息表格化、结尾按类型（见 `references/viral-patterns.md`）
- **按文章类型分叉**：科普 / 教程 / 产品发布 / 免费福利 / 合作公告，不再一刀切「必含 AI 原理段、≤3 小节、Slogan 必写」
- 两套配图方法：暖白风格插图（Pillow 自绘）+ 网页截图（含脱敏）
- 图床流程**通用化**：只讲"上传到你的图床"，不绑定任何人的账号 / 仓库 / 密钥
- 附带按类型判定的文章格式自检脚本，发布前一键过一遍硬性规则

---

## v1.2.1：链接按位置包装

新增两条链接格式硬规则，落在 `references/writing-guide.md` §9.2、SKILL.md 第 6/7 步与文章模板：

| 链接出现的位置 | 写法 |
|---|---|
| 单独成段（一段里只有这一条链接） | `> [标题：完整URL](完整URL)` 引用块 |
| 嵌在正文句子里 | 前后用英文引号 `"` 包住：`规则写在 "[…](…)" 这一页` |

链接本体 `[标题：完整URL](完整URL)` 不变。口诀：**独占一段就上 `>`，夹在话里就上 `""`**。
保持原格式（豁免）：`### 参考链接` / `## 相关阅读` 列表项、图片来源斜体标注、front-matter、代码块内裸 URL、表格单元格内链接、官方原话引用块里原本带的链接。
`check_article.py` 增加两条 WARN 提醒（不硬判 FAIL），并排除上述豁免位置，避免误报。

---

## v1.2.0：高互动写法实证

从 4 篇已发布、被作者标记为高阅读高互动的公众号文章反推写法，新增 `references/viral-patterns.md`（**与 `writing-guide.md` 冲突时以实证为准**）。

修正了旧版三处与实际爆款冲突的一刀切规则：

| 旧规则 | 实证 | 现在 |
|---|---|---|
| 每篇必含一段 AI 原理 | 4 篇里 0 篇讲原理 | 仅科普 / 观点类必含 |
| 主体 ≤ 3 个 `##` | 教程 5 节、发布 7–8 节 | 按类型 3 / 6 / 8 / 5 / 4 |
| Slogan 一字不差 | 合作公告类不写 Slogan | 该类型可省略 |

同步升级 `check_article.py`：新增 `--type`（auto 按标题推断），按类型判定小节上限 / Slogan / 参考链接，并新增亮短板、共情、表格、官方口径等 WARN 提醒。

---

## 首次提示前的示例准备

v1.1.0 将平台入口示例与本地示例库分开：`examples_zh` / `examples_en` 各 3 条；Agent 实际调用 Skill 后，按 SKILL.md 第0步在第一次业务提示或选择前运行 `scripts/init_examples.py`。

- 输出到用户项目的 `workflow/写作搭子/示例/`，不写入 Skill 安装目录。
- 12 个场景文件，中英文各 1 条请求，共 24 条示例；另有 `00-使用说明.md` 索引。
- 纯标准库、离线生成，不执行示例里的写作、截图、绘图或上传请求。
- 重复调用只补缺失文件，保留已有内容；空文件、符号链接、目录占位或权限冲突会报错，不覆盖。
- 仅安装或扫描技能列表不会触发初始化；无执行能力时按 SKILL.md 的文件工具兜底规则处理，无写入权限时如实说明。

场景内容维护在脚本的 `SCENARIOS` 中，增删场景时同步 SKILL.md 的规则与数量。运行产物不放回 Skill 目录，不随发布 ZIP 打包。

---

## 目录结构

```
wanfeng-writing-partner/
├── SKILL.md                       # ⭐ 主入口（7 步工作流 + frontmatter）
├── README.md                      # 本文件（维护说明）
├── references/
│   ├── viral-patterns.md          # ⭐ 高互动写法实证（4 篇样本，冲突时以此为准）
│   ├── writing-guide.md           # 写作规范详解（标题 / 结构 / 排版 / 链接）
│   ├── image-workflow.md          # 配图与图床流程（截图 / 插图 / 上传 / 引用）
│   └── privacy-checklist.md       # 发布前脱敏检查清单
├── scripts/
│   ├── init_examples.py           # 首次提示前准备本地使用示例（纯标准库，只补缺）
│   ├── warm_illustration.py       # 暖白插图生成器（Pillow，跨平台字体探测）
│   └── check_article.py           # 文章格式自检（纯标准库，无依赖）
└── templates/
    └── article-template.md        # 标准文章骨架模板
```

---

## 隐私红线（改这个 Skill 前必读）

本 Skill 面向他人分发，**绝不能携带任何人的隐私**：

- ❌ GitHub 用户名、图床仓库地址、PicGo 配置路径
- ❌ 任何本地绝对路径（`/Users/xxx/...`）、账号 ID、Token、密钥
- ✅ 图床部分统一用"你的图床""`/完整路径/`"占位，只给通用引导

改脚本或文档后，提交前务必跑一次隐私 grep。把下面尖括号替换成你自己的标识符再查（**不要把真实值写进这条命令、更不要提交进仓库**）：

```bash
# 检查是否残留个人信息：本地绝对路径 / 图床配置目录 / 你的用户名 / 你的图床仓库名
grep -rn "/Users/\|\.picgo\|<你的GitHub用户名>\|<你的图床仓库名>" .
```

预期零命中（模板/示例里出现 `example.com`、`os_xxx` 这类占位符是允许的）。

---

## 脚本速查

```bash
# 首次提问前：替换为已存在的用户项目目录；在 Skill 目录中执行此命令
python3 scripts/init_examples.py --project "<用户项目目录>"

# 生成暖白示例插图（需 Pillow）
python3 scripts/warm_illustration.py --out /tmp/illus

# 文章发布前自检（--type 可指定 science/tutorial/release/benefit/announce，默认 auto 推断）
python3 scripts/check_article.py /path/to/article.md
python3 scripts/check_article.py --type tutorial /path/to/article.md
```
