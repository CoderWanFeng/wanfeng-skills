# 晚枫个人网站

> **晚枫个人网站**：通过对话引导用户创建个人网站（博客/知识库/AI 导航/作品集/简历）的 AI skill。

## 这是什么

一个**纯对话式** skill。AI agent 调用后，会通过 5 轮对话引导用户从零搭建一个个人网站，并自动打开本地预览。

支持 6 种网站类型：

| # | 类型 | 推荐技术栈 | 模板目录 |
|---|------|----------|---------|
| 1 | 个人博客 | Hexo + Butterfly | `templates/hexo/` |
| 2 | 知识库 | VitePress | `templates/vitepress/` |
| 3 | AI 导航站 | Vue 3 + Vite | `templates/vue3-vite/` |
| 4 | 个人作品集 | 纯 HTML | `templates/portfolio/` |
| 5 | 个人简历站 | 单文件 HTML | `templates/resume/` |
| 6 | 自定义 | 决策树自动推荐 | - |

## 目录结构

```
personal-website-builder/
├── SKILL.md                # ⚠️ 主入口：对话流程（AI agent 读这个）
├── README.md               # 本文件
├── references/             # 详细参考文档
│   ├── placeholders.md     # 占位符登记表
│   ├── tech-stacks.md      # 技术栈对比
│   ├── deployment.md       # 5 种部署方式
│   ├── troubleshooting.md
│   └── frameworks/         # 各框架详解
├── templates/              # 项目模板（init 脚本从这里复制）
├── scripts/                # 初始化 + 辅助脚本
└── tests/
    └── smoke.sh            # 端到端冒烟测试
```

## 给 AI agent 看的使用说明

### 1. 加载 skill

读取 `SKILL.md`（对话流程入口）。如果用户做了非标准选择（如自定义类型），按需查阅 `references/tech-stacks.md`。

### 2. 对话流程

按 `SKILL.md` 的 5 步流程：开场 → 技术栈 → 基础信息 → 目录 → 确认 → 执行。

**关键约束**：
- 每轮只问 1 个问题
- 给用户推荐选项（标 ⭐）
- 第 5 步必须等用户说「确认」才能继续
- 路径必须用 `validate-path.sh` 校验
- 作者名**不能预填真实姓名**

### 3. 执行阶段

确认后，按类型调用对应脚本：

```bash
# 路径校验
./scripts/validate-path.sh "$USER_PATH"

# 选择最终目录（自动加 -2/-3 后缀）
PROJECT_ROOT="$(./scripts/pick-dirname.sh "$PARENT_DIR" "$BASENAME")"

# 调对应类型的 init
./scripts/init-hexo.sh "$PROJECT_ROOT" "$SITE_NAME" "$SITE_DESC" "$AUTHOR" "$GITHUB"
# 或 init-vitepress.sh / init-vue3.sh / init-portfolio.sh / init-resume.sh

# 启动预览
./scripts/preview.sh <framework> "$PROJECT_ROOT"
```

### 4. 必读约束

- **占位符只能用 `references/placeholders.md` 里登记的**——不要在对话中自由发挥占位符名字
- **作者名留空时用 `Your Name` / `你的名字`**——绝对不能预填真实人名
- **路径必须在系统目录外**——`validate-path.sh` 会自动拒绝

## 给开发者看的扩展说明

### 添加新的网站类型

1. 在 `templates/<type>/` 创建模板文件
2. 在 `references/placeholders.md` 确认占位符（不新增时跳过）
3. 创建 `scripts/init-<type>.sh`
4. 在 `tests/smoke.sh` 添加 e2e 测试
5. 在 `SKILL.md` 的「第 2 步」添加分支选项

### 修改占位符

1. 更新 `references/placeholders.md`
2. 用 `./scripts/substitute.sh --check` 验证所有模板合规
3. 更新 `scripts/substitute.sh` 的 REGEX

### 测试

```bash
# 端到端冒烟测试
./tests/smoke.sh

# 单个脚本测试
./scripts/validate-path.sh /tmp/test
./scripts/detect-env.sh
./scripts/substitute.sh --check templates/hexo/README.md
```

## 设计原则

1. **真实可执行**——每个 init 脚本都跑过，不是占位
2. **路径安全**——拒绝系统目录、越界、符号链接
3. **占位符单一权威**——所有占位符在 `placeholders.md` 登记
4. **双语首篇**——`{{DATE_ISO}}` 动态生成，避免 404
5. **可验证**——`tests/smoke.sh` 端到端验证
6. **headless 友好**——`detect-env.sh` 检测 GUI / CLI 差异
7. **macOS 兼容**——避免 `declare -A` 等 bash 4+ 特性

## 已知限制

- 只支持 Unix-like 系统（macOS / Linux），Windows 通过 WSL
- 默认 bash 3.2 兼容（macOS 自带），不依赖 bash 4+ 关联数组
- CloudBase 部署需要 GUI 或预配置 API Key
- VitePress 1.6+ 的死链检查可能误伤文档里的 `localhost` 引用，模板已加 `ignoreDeadLinks`

## License

MIT