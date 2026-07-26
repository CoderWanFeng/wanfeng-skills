---
name: repowiki-generator
description: 为任意项目生成结构化的 `wiki/` 知识库文档（风格参考 popdf 的 repowiki）。当用户希望 (1) 为当前项目生成仓库 Wiki / 项目知识库；(2) 把代码仓库结构化整理为可浏览的 Markdown 文档；(3) 输出项目概述、核心功能、API 参考、开发者指南；(4) 在某个项目下生成 `repowiki-metadata.json` 元数据；(5) 让 AI Agent 自动读懂项目整体架构并写出带 mermaid 图、cite 块、章节来源的 Markdown 文档时，使用此 skill。触发关键词：生成 repowiki、生成项目 wiki、生成仓库文档、生成项目知识库、输出项目概述、生成 API 参考文档、整理项目文档、repowiki、生成 wiki 文档、为项目生成文档、生成项目 README、生成开发者指南、生成安装文档、生成快速入门、为任意项目生成 wiki、analyze and document this project、generate project documentation。
---

# repowiki-generator

为任意项目生成结构与风格参考 [popdf repowiki](file:///Users/wanfeng/code/po-projects/popdf/.qoder/repowiki/zh) 的仓库知识库，输出到目标项目自身的 `wiki/<lang>/` 目录下。

## 适用场景

- 用户希望为当前项目生成一份完整的、可被 AI Agent 理解的"仓库 Wiki"
- 用户希望以 popdf repowiki 作为参考模板输出结构化文档
- 用户希望文档中包含 mermaid 架构图、`<cite>` 引用块、章节来源标注
- 用户希望覆盖：项目概述、快速入门、安装指南、命令行使用、核心功能详解、API 参考、开发者指南
- 用户希望产物可直接放入 `wiki/zh/content/`，并附带 `repowiki-metadata.json`

## 不适用场景

- 用户只想要单个 README —— 直接用项目自身 README 即可，不必引入 repowiki
- 用户希望生成博客、公众号文章或其他非 Wiki 形态内容 —— 使用 `cover-hero` / `notion-infographic` 等其他 skill
- 目标项目无法访问（远程 GitHub 仓库未克隆到本地）—— 需要先 clone 后再处理

## 工作流程

### 阶段 0：读取参考与定位目标

1. **读取参考规范**：先打开 [`references/format-spec.md`](references/format-spec.md) 与 [`references/doc-templates.md`](references/doc-templates.md)，确认 repowiki 的目录结构、Markdown 语法、引用格式、mermaid 模式。
2. **确认目标项目根目录**：从用户输入中解析目标项目路径。默认参数 `project_root` = 用户当前工作目录或会话上下文中提到的项目根目录；如果用户未指定，向用户询问一次。
3. **确认语言（必须询问用户一次）**：默认只生成中文 `zh`。在开始撰写前，向用户提问一次，确定生成范围：

   ```
   文档语言你想怎么生成？
   1. ⭐ 只生成中文（默认）        → 产出 wiki/zh/
   2. 中文 + 英文都生成（同步双语）  → 产出 wiki/zh/ + wiki/en/
   3. 只生成英文                  → 产出 wiki/en/
   ```

   | 用户选择 | `lang` 取值 | 输出目录 |
   |------|------|------|
   | 1（默认 / 未回答） | `zh` | `wiki/zh/` |
   | 2（双语） | `zh` + `en` | `wiki/zh/` 与 `wiki/en/` |
   | 3（只英文） | `en` | `wiki/en/` |

   > 双语模式下，先完整生成中文版，再据此翻译出英文版；英文版的 `<cite>` 引用路径、行号、mermaid 结构与中文版保持一致，仅正文文案翻译。技术名词、代码标识符、文件名、API 名称在两种语言下都保持原样。

### 阶段 1：扫描目标项目

按 [`references/analysis-checklist.md`](references/analysis-checklist.md) 提供的清单逐项扫描项目。可调用 [`scripts/analyze_project.py`](scripts/analyze_project.py) 辅助扫描，但所有内容必须人工核对，不允许脚本结果直接写入最终文档。

**扫描维度**：

| 维度 | 关键产出 |
|------|----------|
| 项目元信息 | 名称、描述、技术栈、版本号 |
| 目录结构 | 各目录用途、关键文件清单 |
| 构建配置 | `pyproject.toml` / `package.json` / `pom.xml` / `Cargo.toml` / `go.mod` 等 |
| 代码入口 | `__main__`、`cli`、`App.tsx`、`main.py` 等 |
| 核心模块 | 按"业务功能"或"分层架构"识别 |
| 公开 API | 函数签名、参数、返回值、异常 |
| 测试与示例 | 测试目录、示例代码 |
| 部署配置 | Dockerfile、CI/CD、环境变量 |
| 外部依赖 | 第三方库清单 |

### 阶段 2：设计文档结构

根据扫描结果，对照 [`references/output-structure.md`](references/output-structure.md) 设计本文档的具体产出：

- 顶层文档：`项目概述.md`、`快速入门.md`、`安装指南.md`、`命令行使用.md`、`GUI使用指南.md`（如适用）、`Web界面使用.md`（如适用）、`批量处理.md`（如适用）
- `核心功能详解/`：按功能大类分子目录（如 `PDF转换/`、`用户管理/`、`订单系统/`）
- `API参考/`：按 API 大类分子目录
- `开发者指南/`：分层说明、代码结构、测试策略、贡献指南
- 元数据：`meta/repowiki-metadata.json`

> 注意：并非每个项目都需要全部顶层文档——按项目实际功能裁剪。例如纯 CLI 工具不需要 GUI/Web 文档；纯前端项目不需要命令行文档。

### 阶段 3：按模板撰写文档

每个 `.md` 文件必须遵循 [`references/doc-templates.md`](references/doc-templates.md) 中的标准模板：

1. **H1 标题**：文档名
2. **`<cite>` 块**：列出本文引用的所有源文件（带 `file://` 路径）
3. **目录**：H2 标题 + 有序列表（带锚点链接）
4. **简介**：H2 标题，一段或两段说明
5. **章节正文**：按模板指定的章节展开
6. **章节末尾**：标注 `**Section sources**` / `**章节来源**` / `**图表来源**`，引用相关源文件路径与行号

**图表规则**：每个 mermaid 图后必须紧跟一段引用块，列出图表对应的源文件路径。

**引用规则**：所有引用文件必须使用 `[name](file://path/to/file)` 或 `[name](file://path/to/file#L1-L100)` 格式，行号仅在确知时使用。

### 阶段 4：生成元数据

调用 [`scripts/generate_metadata.py`](scripts/generate_metadata.py)，或在文档撰写完毕后手工编写 `meta/repowiki-metadata.json`，格式参考 [`references/format-spec.md`](references/format-spec.md) 第 5 节。

### 阶段 5：写入与校验

1. 在目标项目的 `wiki/<lang>/` 下创建完整目录结构
2. 写入所有 `.md` 文档与 `meta/repowiki-metadata.json`
3. 校验清单：
   - [ ] 每个文档都有 `<cite>` 引用块
   - [ ] 每个文档都有目录
   - [ ] 每个 mermaid 图都有 `**图表来源**` 块
   - [ ] 每个章节末尾都有 `**章节来源**` 或等价块
   - [ ] 所有 `file://` 路径真实存在
   - [ ] 行号范围（如有）与文件实际行数一致
   - [ ] `repowiki-metadata.json` 是合法 JSON 且 `code_snippets` 数组非空
   - [ ] 中英文标点、空格符合中文排版习惯

## 关键参考

- **格式规范详解**：[`references/format-spec.md`](references/format-spec.md)
- **文档结构模板**：[`references/doc-templates.md`](references/doc-templates.md)
- **mermaid 图表模式**：[`references/mermaid-patterns.md`](references/mermaid-patterns.md)
- **项目扫描清单**：[`references/analysis-checklist.md`](references/analysis-checklist.md)
- **输出目录结构**：[`references/output-structure.md`](references/output-structure.md)
- **辅助脚本**：
  - [`scripts/analyze_project.py`](scripts/analyze_project.py) —— 扫描项目结构
  - [`scripts/generate_metadata.py`](scripts/generate_metadata.py) —— 生成元数据 JSON

## 风格与质量要求

- **语言**：默认中文（与 popdf 一致）。技术名词、代码标识符、文件名、API 名称保持原样不翻译。
- **图表**：每个核心概念必须有至少一个 mermaid 图。`<mermaid>` 块使用 `graph TB` / `graph LR` / `classDiagram` / `sequenceDiagram` / `flowchart TD` / `stateDiagram-v2` 等常用类型，按内容选择。
- **不省略细节**：模块名、类名、方法名必须精确写出，与代码保持一致；行号引用必须可验证。
- **不杜撰**：没有的源码文件不要写进 `<cite>`；没有的功能不要写入文档。
- **中英文混排**：中文文案中夹英文文件名/类名/方法名时，前后保留一个空格。

## 输入参数

调用此 skill 时，Agent 应从用户消息中识别以下参数：

| 参数 | 默认值 | 说明 |
|------|---------|------|
| `project_root` | 当前工作目录 | 目标项目根路径 |
| `lang` | `zh` | 文档语言；`zh`（默认）/ `en` / `zh`+`en`（双语），开始前询问用户 |
| `out_dir` | `<project_root>/wiki/<lang>` | 输出目录 |
| `modules` | 自动推断 | 核心功能大类，决定 `核心功能详解/` 下的子目录 |
| `api_groups` | 自动推断 | API 大类，决定 `API参考/` 下的子目录 |

如果用户没有明确 `modules` / `api_groups`，按扫描结果智能分组，并在最终回复中列出推断结果，请用户确认或修正。

## 输出示例

调用完成后，应当在目标项目根目录下生成如下结构（以 Python 库项目为例）：

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
    │   └── <模块A>/<功能1>.md ...
    ├── API参考/
    │   ├── API参考.md
    │   └── <API组A>/...md ...
    └── 开发者指南/
        ├── 开发者指南.md
        ├── 代码结构说明.md
        ├── 测试策略与实践.md
        └── 贡献代码指南.md
```

完成后，回复用户：

1. 生成的文档清单
2. `repowiki-metadata.json` 中包含的代码片段数量
3. 待用户确认的关键假设（如模块划分、API 分组）
4. 已知信息缺口（用户可补全的细节）

## 注意事项

- **行号必须真实存在**：使用 `L1-L100` 格式时，确保目标文件至少有 100 行；否则改为 `L1-L<实际行数>` 或省略行号。
- **不要复制 popdf 内容**：模板与格式可以复用，但所有内容必须基于目标项目实际代码生成，不允许复读 popdf 的具体业务描述。
- **不创建冗余文档**：项目没有 GUI 就不要写 `GUI使用指南.md`；项目没有 Web 前端就不要写 `Web界面使用.md`；项目没有 CLI 入口就不要写 `命令行使用.md`。
- **不修改项目源代码**：本 skill 只在 `wiki/` 目录下创建文件，绝不允许触碰源代码。
- **保持中立语气**：客观描述架构与功能，不写营销文案或主观评价。