# mermaid 图表模式参考

popdf repowiki 中大量使用 mermaid 图表，本文档归纳各类图表的适用场景与编写模式。

## 通用规则

1. **必须使用代码块包裹**：用 ` ```mermaid ` 开头，` ``` ` 结束。
2. **图后必须有引用块**：每个 mermaid 图后紧跟一个 `**图表来源**` / `**Diagram sources**` 等引用块。
3. **禁用样式定义**：不要使用 `style` 或 `classDef`（部分渲染器支持不全）。
4. **节点 ID 简洁**：使用简短 ID（如 `A`、`API`、`Core`），避免长字符串。
5. **标签清晰**：节点标签用 `["文本"]` 包裹，可包含 HTML `<br/>` 换行。
6. **方向选择**：`TB` (top-bottom)、`LR` (left-right)、`RL` (right-left)、`BT` (bottom-top)。

## 图表类型与适用场景

### 1. `graph TB / LR`：分层与依赖

**适用场景**：
- 描述目录结构、模块分层
- 描述数据流向
- 描述调用关系

**模式 A：基础分层图**

```mermaid
graph TB
    subgraph "API 层"
        A1["api 模块"]
    end
    subgraph "Core 层"
        C1["core 模块"]
    end
    subgraph "Util 层"
        U1["utils 模块"]
    end
    A1 --> C1
    C1 --> U1
```

**模式 B：依赖关系图**

```mermaid
graph LR
    P["project"] --> D1["dep1"]
    P --> D2["dep2"]
    P --> D3["dep3"]
```

**模式 C：分组架构图**

```mermaid
graph TB
    subgraph "前端"
        W["Web UI"]
    end
    subgraph "后端"
        API["REST API"]
        Core["Core Service"]
    end
    subgraph "存储"
        DB[("Database")]
    end
    W --> API
    API --> Core
    Core --> DB
```

### 2. `classDiagram`：类与接口

**适用场景**：
- 描述类的属性与方法
- 描述类之间的继承、依赖、关联关系

**模式 A：单类展示**

```mermaid
classDiagram
    class MainPDF {
        +pdf_suffix : str
        +pdf2docx(input_file, output_file)
        +pdf2imgs(input_file, output_file, merge)
        +txt2pdf(input_file, output_file)
    }
```

**模式 B：多类关系**

```mermaid
classDiagram
    class MainPDF {
        +pdf2docx()
        +pdf2imgs()
    }
    class Batch_PDFType {
        +pdf2docx()
        +split4pdfs()
    }
    class Util {
        <<utility>>
        +convert()
        +split()
    }
    MainPDF --> Util
    Batch_PDFType --> Util
```

**关系符号**：
- `-->` 依赖
- `--*` 组合
- `--o` 聚合
- `--|> ` 继承 / 实现
- `..>` 弱依赖
- `--` 关联

### 3. `sequenceDiagram`：时序流程

**适用场景**：
- 描述用户 → API → 服务 → DB 的调用时序
- 描述跨模块协作流程

**模式 A：基础时序**

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API 层
    participant Core as Core 层
    participant Util as Util 层
    U->>API : 调用方法
    API->>Core : 转发请求
    Core->>Util : 执行操作
    Util-->>Core : 返回结果
    Core-->>API : 返回状态
    API-->>U : 返回数据
```

**模式 B：带分支（alt/else）**

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as API
    U->>A : 调用
    alt 单文件模式
        A->>A : 走 Single 分支
    else 批量模式
        A->>A : 走 Batch 分支
    end
    A-->>U : 返回
```

**模式 C：带循环（loop）**

```mermaid
sequenceDiagram
    participant B as Batch
    loop 对每个文件
        B->>B : 处理
    end
```

**注意**：mermaid `sequenceDiagram` 中 `participant` 后的别名使用 `as`。

### 4. `flowchart TD`：流程判断

**适用场景**：
- 描述参数校验流程
- 描述异常分支处理
- 描述工作流

**模式 A：判断流程**

```mermaid
flowchart TD
    Start(["开始"]) --> Check{"参数有效?"}
    Check --> |是| Process["执行处理"]
    Check --> |否| LogErr["记录错误"]
    Process --> End(["结束"])
    LogErr --> End
```

**模式 B：节点命名**

```mermaid
flowchart TD
    A["输入"] --> B{"判断"}
    B --> |"分支1"| C["处理1"]
    B --> |"分支2"| D["处理2"]
    C --> E["结束"]
    D --> E
```

**节点形状**：
- `["text"]` 矩形（默认）
- `("text")` 圆角矩形
- `{"text"}` 菱形（判断）
- `(["text"])` 胶囊形
- `[("text")]` 圆柱形（数据库）
- `[/"text"/]` 平行四边形
- `[\"text"\]` 反平行四边形
- `{{"text"}}` 六边形

### 5. `stateDiagram-v2`：状态机

**适用场景**：
- 描述异常状态流转
- 描述业务对象生命周期

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : 接收到请求
    Processing --> Success : 处理成功
    Processing --> Failed : 处理失败
    Success --> [*]
    Failed --> Retry
    Retry --> Processing
```

## mermaid 标签中的特殊字符

### 换行

使用 `<br/>`：

```mermaid
graph TB
    A["第一行<br/>第二行"]
```

### 括号

在 `["..."]` 内部，括号是安全的：

```mermaid
graph TB
    A["config (YAML)"]
```

### 引号

在 `["..."]` 内部，引号是安全的：

```mermaid
graph TB
    A["name = \"foo\""]
```

### 特殊符号

避免在标签中使用 mermaid 关键字（如 `end`、`subgraph`、`graph`），如必须使用，加引号或换词。

## popdf repowiki 中的实际案例

### 案例 1：项目分层架构（项目概述.md）

```mermaid
graph TB
    subgraph "API 层"
        A1["popdf/api/pdf.py<br/>对外函数与CLI入口"]
    end
    subgraph "核心层"
        C1["popdf/core/PDFType.py<br/>MainPDF 单文件操作"]
        C2["popdf/core/Batch_PDFType.py<br/>Batch_PDFType 批量操作"]
    end
    subgraph "工具层"
        T1["popdf/lib/pdf2docx_utils.py"]
        T2["popdf/lib/pdf2imgs_utils.py"]
    end
    A1 --> C1
    A1 --> C2
    C1 --> T1
    C1 --> T2
```

### 案例 2：CLI 时序（项目概述.md）

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as CLI popdf
    participant API as popdf.api.pdf
    participant Core as MainPDF/Batch_PDFType
    participant Utils as 工具函数
    participant Ext as 外部库
    User->>CLI : 执行 popdf 命令
    CLI->>API : 调用对应函数
    API->>Core : 选择单文件或批量
    Core->>Utils : 调用工具函数
    Utils->>Ext : 使用 PyMuPDF/PyPDF2 等
    Ext-->>Utils : 返回处理结果
    Utils-->>Core : 写入输出文件
    Core-->>API : 返回状态
    API-->>CLI : 日志/返回值
    CLI-->>User : 显示结果
```

### 案例 3：核心类继承（核心功能详解.md）

```mermaid
classDiagram
    class MainPDF {
        +pdf_suffix : str
        +pdf2docx(input_file, output_file)
        +pdf2imgs(input_file, output_file, merge)
    }
    class Batch_PDFType {
        +pdf_suffix : str
        +docx_suffix : str
        +pdf2docx(input_path, output_path)
        +split4pdfs(input_path, output_path, from_page, to_page)
    }
    MainPDF <|-- Batch_PDFType : 继承
    MainPDF : 单文件处理
    Batch_PDFType : 批量处理
```

### 案例 4：异常处理流程（API参考.md）

```mermaid
stateDiagram-v2
    [*] --> NormalOperation
    NormalOperation --> ParameterError : 参数无效
    NormalOperation --> FileNotFoundError : 文件不存在
    NormalOperation --> EncryptionError : 加密/解密失败
    NormalOperation --> VersionError : 依赖版本不满足
    ParameterError --> LogError : 记录错误日志
    FileNotFoundError --> LogError
    EncryptionError --> LogError
    VersionError --> RaiseException : 抛出SystemExit
    LogError --> ReturnResult
    RaiseException --> ReturnResult
    ReturnResult --> [*]
```

### 案例 5：工具函数流程（核心功能详解.md）

```mermaid
flowchart TD
    Start(["进入工具函数"]) --> CheckInput["校验输入参数/文件存在性"]
    CheckInput --> Valid{"参数有效?"}
    Valid --> |否| LogErr["记录错误日志并返回"]
    Valid --> |是| CallDep["调用外部库实现功能"]
    CallDep --> WriteOut["写入输出文件/目录"]
    WriteOut --> Done(["完成"])
    LogErr --> Done
```

### 案例 6：参数路由流程（PDF转Word.md）

```mermaid
flowchart TD
    A["调用pdf2docx(...)"] --> B{"是否满足旧版参数：<br/>input_file + output_path?"}
    B --> |是| C["委托MainPDF，将output_path作为输出文件名"]
    B --> |否| D{"是否满足新版参数：<br/>input_file + output_file?"}
    D --> |是| E["委托MainPDF"]
    D --> |否| F{"是否满足批量参数：<br/>input_path + output_path?"}
    F --> |是| G["委托Batch_PDFType"]
    F --> |否| H["记录错误并返回"]
```

## 选型决策

| 想要表达的内容 | 推荐图表 |
|----------------|----------|
| 目录结构、模块分层 | `graph TB` |
| 数据流向、调用顺序 | `graph LR` 或 `sequenceDiagram` |
| 类与方法签名 | `classDiagram` |
| 跨模块协作时序 | `sequenceDiagram` |
| 业务流程 / 条件分支 | `flowchart TD` |
| 状态机 / 生命周期 | `stateDiagram-v2` |
| 简单的依赖清单 | `graph LR` |
| 异常处理流程 | `flowchart TD` 或 `stateDiagram-v2` |

每篇文档至少包含 2 个 mermaid 图（项目概述 5+ 个，核心功能详解 4+ 个，API 参考 3+ 个）。