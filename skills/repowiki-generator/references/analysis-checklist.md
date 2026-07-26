# 项目扫描清单

AI Agent 在生成 repowiki 前，必须按本清单对目标项目进行系统性扫描。

## 1. 项目元信息

- [ ] **项目名称**：根目录名 / `package.json#name` / `pyproject.toml#project.name` / `Cargo.toml#package.name`
- [ ] **项目描述**：`README.md` 第一段、`pyproject.toml#project.description`、`package.json#description`
- [ ] **版本号**：`pyproject.toml#project.version`、`package.json#version`、`Cargo.toml#package.version`
- [ ] **许可证**：`LICENSE` 文件存在性 + 内容识别
- [ ] **作者/维护者**：`pyproject.toml#authors`、`package.json#author`、`Cargo.toml#authors`
- [ ] **主页/仓库**：URL 字段
- [ ] **当前语言**：中文项目还是英文项目

## 2. 技术栈识别

按文件后缀/构建文件识别：

| 项目类型 | 关键文件 |
|----------|----------|
| Python 库 / 应用 | `pyproject.toml`、`setup.py`、`setup.cfg`、`requirements.txt`、`Pipfile`、`uv.lock`、`poetry.lock` |
| Node.js / 前端 | `package.json`、`pnpm-lock.yaml`、`yarn.lock`、`package-lock.json` |
| Go | `go.mod`、`go.sum` |
| Rust | `Cargo.toml`、`Cargo.lock` |
| Java / Kotlin | `pom.xml`、`build.gradle`、`build.gradle.kts` |
| Ruby | `Gemfile`、`Gemfile.lock` |
| PHP | `composer.json`、`composer.lock` |
| C# / .NET | `*.csproj`、`*.sln` |
| Flutter / Dart | `pubspec.yaml` |

补充识别：

- 框架：React、Vue、Angular、Next.js、Nuxt、Express、NestJS、Django、Flask、FastAPI、Spring Boot、Gin、Rails 等
- UI 库：Tailwind、Material-UI、Ant Design、Element Plus、shadcn/ui 等
- 数据库：PostgreSQL、MySQL、SQLite、MongoDB、Redis 等
- 部署：Dockerfile、docker-compose.yml、k8s manifests

## 3. 目录结构扫描

执行 `tree -L 3 -I 'node_modules|__pycache__|.git|dist|build|.venv'` 或读取 `Bash` 工具列出结构。

对每个顶层目录，记录：

- 目录名
- 推断用途（基于目录名 + 内部文件）
- 关键文件清单

常见目录用途速查：

| 目录 | 推断用途 |
|------|----------|
| `src/`、`lib/`、`pkg/`、`internal/` | 源代码 |
| `tests/`、`test/`、`__tests__/`、`spec/` | 测试 |
| `docs/`、`doc/`、`documentation/` | 文档 |
| `examples/`、`demo/`、`sample/` | 示例 |
| `scripts/`、`bin/`、`tools/` | 工具脚本 |
| `config/`、`conf/` | 配置 |
| `public/`、`static/`、`assets/` | 静态资源 |
| `api/`、`routes/`、`controllers/`、`views/` | 接口层 |
| `models/`、`entities/`、`schemas/` | 数据模型 |
| `services/`、`core/`、`domain/`、`business/` | 业务层 |
| `utils/`、`helpers/`、`common/`、`shared/` | 工具 |
| `components/`、`widgets/`、`ui/` | UI 组件 |
| `cmd/`、`cli/` | CLI 入口 |
| `migrations/` | 数据库迁移 |
| `web/`、`frontend/`、`client/` | 前端 |
| `server/`、`backend/`、`api/` | 后端 |
| `dist/`、`build/`、`out/` | 构建产物（忽略） |
| `node_modules/`、`vendor/`、`__pycache__/` | 第三方依赖（忽略） |

## 4. 入口点识别

- **Python**：`pyproject.toml#project.scripts`、`[project.entry-points]`、`if __name__ == "__main__":`
- **Node.js**：`package.json#bin`、`package.json#main`、`package.json#scripts`
- **Go**：`cmd/` 下的 `main.go`
- **Rust**：`src/main.rs` 或 `src/bin/`
- **Java**：`src/main/java/.../Main.java`、`@SpringBootApplication`
- **前端**：`src/main.ts`、`src/main.js`、`src/App.tsx`、`src/App.vue`、`index.html` 入口

## 5. 核心模块识别

按以下策略识别：

1. **目录结构归纳**：从 `src/`、`lib/` 等代码目录推断模块划分
2. **业务命名**：识别含业务关键词的文件/目录（`user`、`order`、`payment`、`auth`、`pdf`、`image` 等）
3. **公开 API**：从入口文件向上追溯，看哪些函数/类被导出
4. **README 索引**：很多项目 README 会列出主要功能模块

对每个核心模块，记录：

- 模块名
- 主要文件（1-3 个）
- 关键类/函数
- 一句话职责描述

## 6. 公开 API 扫描

### Python

- 找 `__init__.py` 中的 `__all__`
- 找 `from xxx import *` 或模块级 `import`
- 用 `Grep` 搜索 `^def `、`^class `、`^    def `、`^    class `
- 找 `@property`、`@staticmethod`、`@classmethod` 装饰的成员

### Node.js / TypeScript

- 找 `export default`、`export const`、`export function`、`export class`
- 找 `module.exports`
- 读 `package.json#exports` 字段
- 读 `package.json#types` / `package.json#typings`

### Go

- 找 `func (xxx *Yyy) Method()` 公开方法
- 找 `func Public(...)`
- 读 `pkg.go.dev` 风格的注释（`// PublicXxx ...`）

### Rust

- `pub fn`、`pub struct`、`pub enum`、`pub trait`、`pub mod`

### Java

- `public` 类与方法
- Spring 的 `@RestController` / `@Service` / `@Repository` 注解

### 通用

记录每个公开 API 的：

- 名称
- 函数签名
- 参数（含类型、是否必填、默认值）
- 返回值类型
- 异常 / 错误处理
- 简短描述

## 7. 数据模型扫描

- **ORM/Schema 文件**：`models/`、`schema.prisma`、`entities/`、`*.entity.ts`、SQL DDL
- **DTO/VO**：`dto/`、`vo/`、`requests/`、`responses/`
- **配置文件中的 schema**：`config.schema.json`、`openapi.yaml`、`swagger.json`
- **数据库迁移**：`migrations/`、`alembic/versions/`

记录每个核心实体的：

- 名称
- 字段（含类型、是否必填、默认值、约束）
- 关系（一对多、多对多等）

## 8. 测试与示例

- 测试目录：`tests/`、`test/`、`__tests__/`、`spec/`
- 测试框架：pytest、unittest、jest、vitest、mocha、go test、cargo test、junit
- 示例目录：`examples/`、`demo/`、`sample/`
- 文档示例：`docs/`、`README.md` 中的代码块

## 9. 部署与运维

- **Docker**：`Dockerfile`、`docker-compose.yml`、`.dockerignore`
- **CI/CD**：`.github/workflows/`、`.gitlab-ci.yml`、`.circleci/`、`Jenkinsfile`
- **环境变量**：`.env.example`、`config/.env.sample`、代码中的 `os.getenv`、`process.env`
- **Helm/K8s**：`charts/`、`k8s/`、`deploy/`
- **云函数/Serverless**：`serverless.yml`、`sam.yaml`、`vercel.json`、`netlify.toml`

## 10. 配置文件

记录所有非源代码配置文件：

- Lint/Format：`.eslintrc`、`pylintrc`、`rustfmt.toml`、`.prettierrc`
- 类型检查：`tsconfig.json`、`mypy.ini`
- 依赖管理：见 §2
- 文档生成：`.readthedocs.yml`、`mkdocs.yml`
- 包发布：`MANIFEST.in`、`Dockerfile`、`package.json#files`

## 11. 文档来源

- `README.md`：几乎每个项目都有
- `CHANGELOG.md`：版本变更
- `CONTRIBUTING.md`：贡献指南
- `LICENSE`：许可证
- `docs/`、`wiki/`：深度文档
- `API_REFERENCE.md`、`API.md`：API 文档

## 12. 上下文与外部依赖

- 项目 README 中提到的外部服务、第三方平台、API
- 配置文件中的 URL、域名
- 环境变量名（推断服务名）

## 13. 评估输出

完成扫描后，输出一份"项目分析报告"（仅供内部使用，不必写入 repowiki），包含：

1. **项目一句话定位**：≤ 30 字
2. **核心模块列表**：每个模块一句话职责
3. **API 分组**：每个组包含哪些 API
4. **特殊功能**：是否包含 GUI / Web / CLI / 批量 / 部署脚本
5. **风险与缺口**：
   - 没有 README → 提示风险
   - 没有测试 → 不写测试策略
   - 没有 LICENSE → 提示
   - 没有 `__init__.py` → 入口识别困难
6. **建议的 repowiki 模块分组**：直接对应 `核心功能详解/` 与 `API参考/` 子目录

## 14. 推荐工具

实际扫描时推荐使用：

- `Bash` 工具运行 `ls`、`find`、`tree`
- `Grep` 工具搜索关键字（如 `def `、`class `、`export `、`func `）
- `Glob` 工具按模式找文件
- `Read` 工具读取关键文件
- `SearchCodebase` 工具做语义搜索

参考脚本：[`scripts/analyze_project.py`](../scripts/analyze_project.py)