# repowiki-generator

为任意项目生成结构与风格参考 [popdf repowiki](file:///Users/wanfeng/code/po-projects/popdf/.qoder/repowiki/zh) 的仓库知识库，输出到目标项目自身的 `wiki/<lang>/` 目录下。默认生成中文 `wiki/zh/`，生成前会询问是否同步生成英文。

## 适用场景

- 用户希望为当前项目生成一份完整的、可被 AI Agent 理解的"仓库 Wiki"
- 用户希望以 popdf repowiki 作为参考模板输出结构化文档
- 用户希望文档中包含 mermaid 架构图、`<cite>` 引用块、章节来源标注

## 触发关键词

`生成 repowiki` · `生成项目 wiki` · `生成仓库文档` · `生成项目知识库` · `输出项目概述` · `生成 API 参考文档` · `整理项目文档` · `repowiki` · `生成 wiki 文档` · `为项目生成文档` · `生成项目 README` · `生成开发者指南` · `生成安装文档` · `生成快速入门` · `为任意项目生成 wiki` · `analyze and document this project` · `generate project documentation`

## 目录结构

```
skills/repowiki-generator/
├── SKILL.md                         # 入口与工作流程
├── README.md                        # 本文件：用户级概览
├── references/
│   ├── format-spec.md               # repowiki 格式规范详解
│   ├── doc-templates.md             # 文档结构模板（12 种）
│   ├── mermaid-patterns.md          # mermaid 图表模式参考
│   ├── analysis-checklist.md        # 项目扫描清单
│   └── output-structure.md          # 输出目录结构与命名
├── scripts/
│   ├── analyze_project.py           # 项目结构扫描 → JSON 报告
│   └── generate_metadata.py         # 根据 cite 块生成 metadata.json
└── templates/
    └── (示例模板)
```

## 快速上手

### 调用 skill

向 AI Agent 说：

> "为 /Users/wanfeng/code/<你的项目> 生成 repowiki"

Agent 将：

1. 调用 `scripts/analyze_project.py` 扫描项目结构
2. 按 `references/output-structure.md` 设计文档树
3. 按 `references/doc-templates.md` 撰写每个 .md
4. 调用 `scripts/generate_metadata.py` 生成 `meta/repowiki-metadata.json`
5. 写入 `<project>/wiki/zh/`（若选双语则同时写 `<project>/wiki/en/`）

### 单独使用脚本

```bash
# 1. 扫描项目结构
python3 scripts/analyze_project.py /path/to/project -o report.json

# 2. 撰写 repowiki（手动 / 由 Agent 完成）

# 3. 生成元数据
python3 scripts/generate_metadata.py /path/to/project/wiki/zh/content \
    --project-root /path/to/project \
    --out /path/to/project/wiki/zh/meta/repowiki-metadata.json
```

## 输出示例

调用完成后，目标项目根目录下生成如下结构：

```
<project_root>/wiki/zh/
├── meta/
│   └── repowiki-metadata.json
└── content/
    ├── 项目概述.md
    ├── 快速入门.md
    ├── 安装指南.md
    ├── 命令行使用.md
    ├── 批量处理.md
    ├── 核心功能详解/
    │   ├── 核心功能详解.md
    │   ├── <模块A>/...md
    │   └── <模块B>/...md
    ├── API参考/
    │   ├── API参考.md
    │   └── <API组A>/...md
    └── 开发者指南/
        ├── 开发者指南.md
        ├── 代码结构说明.md
        ├── 测试策略与实践.md
        └── 贡献代码指南.md
```

具体生成哪些顶层文档，由项目实际能力决定（详见 `references/output-structure.md` 的"顶层文档适用矩阵"）。

## 核心约定

1. **每个 `.md` 都必须包含 `<cite>` 块** —— 列出本文引用的源文件
2. **每个 mermaid 图后必须有引用块** —— `**图表来源**` / `**Diagram sources**`
3. **每个章节末尾必须有引用块** —— `**章节来源**` / `**Section sources**`
4. **`file://` 路径必须真实存在** —— 不允许杜撰源文件引用
5. **行号必须可验证** —— 使用 `#L<start>-L<end>` 时确保目标文件行数充足

## 详细文档

- 工作流程：[SKILL.md](SKILL.md)
- 格式规范：[references/format-spec.md](references/format-spec.md)
- 文档模板：[references/doc-templates.md](references/doc-templates.md)
- mermaid 图表：[references/mermaid-patterns.md](references/mermaid-patterns.md)
- 项目扫描：[references/analysis-checklist.md](references/analysis-checklist.md)
- 输出结构：[references/output-structure.md](references/output-structure.md)

## 依赖

- Python 3.8+（仅标准库）
- 无第三方依赖