# 晚枫个人网站

> **晚枫个人网站**：通过对话引导用户创建个人网站（博客/知识库/AI 导航/作品集/简历）的 AI skill。
>
> SkillHub 安装：https://skillhub.cn/skills/user_bf8c5b73/wanfeng-personal-website-builder

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
│   ├── file-integrity-check.md  # 文件完整性自检与还原（安装后先读）
│   ├── tech-stacks.md      # 技术栈对比
│   ├── deployment.md       # 5 种部署方式
│   ├── troubleshooting.md
│   ├── framework-*.md      # 各框架详解
├── templates/              # 项目模板（init 脚本从这里复制）
├── scripts/                # 初始化 + 辅助脚本
│   └── gen-restricted-files.py  # 按规律重建受限文件（自检用）
└── tests/
    └── smoke.sh            # 端到端冒烟测试
```

## 给 AI agent 看的使用说明

### 0. 文件完整性自检（强制，先于一切）

部分安装平台会过滤掉**以 `.` 开头的隐藏文件**、**带 `.template` 后缀的文件**
和**带 `.vue` 后缀的组件文件**。本 skill 有 12 个文件受此影响：
5 个 `templates/*/.gitignore` + 2 个 `templates/*/package.json.template`
+ 5 个 `templates/vue3-vite/src/**/*.vue`。

**首选做法：跑随包附带的生成器**（一条命令自检 + 一条命令补齐）：

```bash
python3 scripts/gen-restricted-files.py --check   # 只检查，退出码 0 = 12/12 齐全
python3 scripts/gen-restricted-files.py            # 补齐缺失的文件（幂等）
python3 scripts/gen-restricted-files.py --force    # 强制重建全部 12 个
python3 scripts/gen-restricted-files.py --extract  # 归档形态 → 展开成 templates/ 目录
```

生成器把 `references/file-integrity-check.md` 里的**生成规律固化成代码**（三张规格表 +
渲染函数），纯 Python 3 标准库、不联网。写入前必过三项自检：
CSS 变量闭环、产物目录对齐 `substitute.sh` 的 `get_dist()`、依赖版本对齐 init 脚本 ——
任一不通过则一个文件都不写。

> **归档形态**：第三方平台限制压缩包内最多一层子目录，而框架模板天生带嵌套目录，
> 所以打包时 `templates/` 会转成 `templates-<框架>.tar.gz` 放进包根。
> 归档内部保留完整目录结构，`.gitignore` / `.vue` 待在平台扫不到的 tar 里，不会被过滤。
> `init-*.sh`（经 `scripts/resolve-template.sh`）会自动解包再复制，**用户无感知**。
> 生成器能自动识别当前形态，不会误报「文件全丢」。

若不足 12 个，**先还原再干活** —— `.gitignore` 缺失会让 4 个 init 脚本 `cp` 失败并被
`set -e` 中止；`.vue` 缺失会让「AI 导航站」类型整体不可用。
生成器不可用时的兜底（按原文逐字写回）见
[`references/file-integrity-check.md`](references/file-integrity-check.md)。

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
- 部分安装平台会过滤隐藏文件、`.template` 后缀文件与 `.vue` 组件文件，安装后需按 `references/file-integrity-check.md` 自检并还原
- CloudBase 部署需要 GUI 或预配置 API Key
- VitePress 1.6+ 的死链检查可能误伤文档里的 `localhost` 引用，模板已加 `ignoreDeadLinks`

## License

MIT