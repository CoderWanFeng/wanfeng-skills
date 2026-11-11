# 4 种非技术场景模板（个人 wiki / 设计师 / 文档党 / dotfiles）

> SKILL.md 主线 2（发布）在「场景识别」后引用本表，给不同项目类型提供专属的 .gitignore + README + 演示话术。

---

## 场景 1：文档 / 笔记项目

**典型例子**：学习笔记、电子书、手册、博客源文件、个人 wiki

### `.gitignore` 模板

```gitignore
# 临时文件
*.tmp
*.bak
*~
.DS_Store
Thumbs.db

# 编辑器缓存
.vscode/
.idea/
*.swp

# 大型原始素材（如果笔记里有）
*.zip
*.tar.gz
```

### README 模板

```markdown
# {笔记标题}

{一句话介绍：比如「我的机器学习学习笔记，从入门到放弃」}

## 📚 目录

- [第一章：XXX](./01-intro.md)
- [第二章：XXX](./02-basics.md)
- ...

## ✍️ 写作工具

- 用 {Typora / Obsidian / VSCode} 写
- 图片用 {iPic / PicGo} 上传到 {图床}

## 📄 许可证

CC BY-NC-SA 4.0（允许非商用转载，署名即可）
```

### 演示对话

```
你：你这个项目是「笔记/文档/电子书」类的吧？我看目录里都是 .md / .pdf。

我帮你套一个文档专用模板：
- .gitignore 里不传临时文件、编辑器缓存
- README 用「目录式」结构（适合按章节看）
- 许可证用 CC（适合知识内容）

继续吗？
```

---

## 场景 2：图片 / 设计稿 / 摄影集

**典型例子**：摄影作品集、设计稿源文件、PSD 集合、截图归档

### `.gitignore` 模板

```gitignore
# 系统
.DS_Store
Thumbs.db

# 工作文件（用 LFS 或单独存）
*.psd
*.ai
*.sketch
*.fig
*.afdesign
*.tmp

# 视频（如果项目里有）
*.mp4
*.mov
```

> **重要提示**：如果图片是核心内容（如摄影集），**不要**全部 gitignore 掉。告诉用户：
> - 压缩后传（PNG → JPG，> 2MB 的都压缩）
> - 用 Git LFS 存大文件
> - 单图 > 5MB 建议放网盘（OSS / 阿里云 / 蓝奏云）

### README 模板

```markdown
# {项目名：比如「A 城街头摄影 2026」}

{一句话：「用手机拍的 365 张街景，按月份整理」}

## 📷 拍摄信息

- 设备：{iPhone 15 / 富士 X-T5}
- 后期：{Lightroom / 泼辣修图}
- 时间：{2025.01 - 2026.06}

## 🗓️ 按月份浏览

- [一月](./01-jan/)
- [二月](./02-feb/)
- ...

## 📄 许可证

CC BY-NC 4.0（署名 + 非商用）
```

### 演示对话

```
你：这是图片/摄影集吧？我看到一堆 .jpg / .psd。

图片类项目有两个坑要避：
1. **别传原始大文件**（PSD 一个几百 MB，仓库会爆）
2. **版权要标清**（用 CC 协议，别让盗图的人白嫖）

我的建议：
- 摄影成片（.jpg）→ 压缩到 ≤ 2MB 后传
- 工作源文件（.psd/.ai）→ 用 Git LFS 或放网盘
- README 顶部加「拍摄信息 + 许可证」

按这个来吗？
```

---

## 场景 3：配置文件（dotfiles）

**典型例子**：vim / zsh / tmux / vscode 配置、个人脚本集合、.bash_profile

### `.gitignore` 模板

```gitignore
# 系统
.DS_Store

# 敏感信息（绝不能传！）
*.local
.env
*.secret

# 缓存
*.swp
*.swo
*~
```

### README 模板

```markdown
# {你的名字} 的 dotfiles

{一句话：「我的开发环境配置，Mac + iTerm2 + zsh + vim」}

## 🚀 一键安装

```bash
# 克隆到本地
git clone git@github.com:{你的用户名}/dotfiles.git ~/dotfiles

# 跑安装脚本
cd ~/dotfiles && ./install.sh
```

## 🛠️ 工具清单

- **Shell**: zsh + oh-my-zsh + powerlevel10k
- **编辑器**: vim + SpaceVim / VSCode
- **终端**: iTerm2 + tmux
- **Git 别名**: `git lg` 替代 `git log`

## 📄 许可证

MIT
```

### 演示对话

```
你：看你目录里都是 .vimrc / .zshrc / .gitconfig，这是 dotfiles 吧？

dotfiles 上 GitHub 是「晒配置」的标准操作，超多开发者在做。但要注意两点：

1. **千万别传 .env 或含密码的文件**（我会自动加进 .gitignore）
2. **写个 install.sh**（让别人 / 未来的你一键复现你的环境）

你的配置文件里有什么敏感信息吗？告诉我我帮你排除。
```

---

## 场景 4：书籍 / 教程 / 课程资料

**典型例子**：电子书源文件、教程代码 + 配套文档、课程讲义

### `.gitignore` 模板

```gitignore
# 构建产物
dist/
build/
out/
*.pdf
*.epub
*.mobi

# 临时
*.tmp
*.bak

# 系统
.DS_Store
```

### README 模板

```markdown
# {书名 / 教程名}

{一句话：「从零开始学 XXX，覆盖 12 个核心主题」}

## 📖 在线阅读

- GitHub Pages: https://{你的用户名}.github.io/{仓库名}/
- Gitee Pages: https://{你的用户名}.gitee.io/{仓库名}/

## 🗂️ 目录

- [第 1 章：入门](./ch01/)
- [第 2 章：基础](./ch02/)
- ...

## 🔧 配套代码

每章的代码在 `code/` 目录下，按章节组织。

```bash
cd code/ch03-hello-world
npm install
npm run dev
```

## 📄 许可证

- **文字内容**: CC BY-NC-SA 4.0
- **代码**: MIT
```

### 演示对话

```
你：这看起来是「书/教程/课程资料」类的吧？目录里有 chapters / lessons / slides。

这种项目的最佳实践：
1. **启用 GitHub Pages**（白嫖一个静态网站托管）
2. **文字和代码用不同 license**（CC + MIT 组合）
3. **每章独立目录**（方便读者跳着看）

要帮你配 Pages 部署吗？
```

---

## 场景速查决策树

```
用户说项目是 → 看是哪种类型
├── 「我的笔记」「学习资料」「wiki」            → 场景 1：文档
├── 「摄影」「设计稿」「图片」「PSD」          → 场景 2：素材
├── 「我的 vim 配置」「zshrc」「dotfiles」    → 场景 3：配置
├── 「教程」「书」「课程」「讲义」            → 场景 4：教程
└── 「网站」「工具」「APP」「脚本」            → 默认代码模板
```

---

## 通用补充：所有非技术项目都要做的 3 件事

1. **写一个像样的 README**（哪怕是 3 行）：
   - 这东西是啥
   - 谁可以看 / 怎么用
   - 许可证是啥

2. **检查 `.gitignore`**：
   - 临时文件（`*.tmp`、`.DS_Store`）
   - 系统生成（`Thumbs.db`）
   - 敏感信息（`.env`、`*.local`）

3. **选个合适的 license**：
   - 代码 → `MIT`（最宽松）
   - 文档/笔记 → `CC BY-NC-SA 4.0`（署名 + 非商用 + 相同方式共享）
   - 设计稿 → `CC BY 4.0` 或干脆不写（保留所有权利）
   - 配置文件 → `MIT`
