# wanfeng-writing-partner · 晚枫写作搭子

> **本文件给维护者看**——用户读 [SKILL.md](SKILL.md)。

---

## 这是什么

把「晚枫每天写公众号文章实际在用的流程」固化成一个 Skill：从一个 AI 热点 / 产品体验 / 官方资料，到一份可以直接复制进编辑器的 Markdown 成稿。

**核心特性**：

- 7 步工作流：选题素材 → 起标题 → 搭结构 → 配图 → 上传图床 → 插入引用 → 发布前检查
- 两套配图方法：暖白风格插图（Pillow 自绘）+ 网页截图（含脱敏）
- 图床流程**通用化**：只讲"上传到你的图床"，不绑定任何人的账号 / 仓库 / 密钥
- 附带文章格式自检脚本，发布前一键过一遍硬性规则

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

# 文章发布前自检
python3 scripts/check_article.py /path/to/article.md
```
