# Git 命令速查（给完全不懂的人看）

> 这是一份「人话版」Git 命令速查表。SKILL.md 在执行时如果用户卡住，可以把对应段落贴给他看。

## 核心 6 个命令（记住这几个就能用 80%）

```bash
git init              # 把当前目录变成「git 能管理的仓库」
git add .             # 把所有改动「标记」为「准备提交」
git commit -m "说明"  # 把这些改动「打包」，写一句话说明改了什么
git push              # 把本地的包「上传」到 GitHub/AtomGit
git pull              # 把远程的新改动「下载」到本地
git clone 地址        # 把远程仓库「完整下载」到本地
```

## 配置身份（每个电脑第一次用 git 都要做）

```bash
git config --global user.name "你的名字"
git config --global user.email "your@email.com"
```

## 仓库的 3 个区域（理解了这个就懂 Git 了）

```
工作区（Working Directory）  → 你看到的文件夹
暂存区（Stage / Index）      → add 之后到这里
仓库区（Repository）         → commit 之后到这里
```

| 命令 | 作用 | 区域 |
|---|---|---|
| `git status` | 看现在有哪些文件被改过 | — |
| `git add 文件` | 把文件从工作区放到暂存区 | 工作区 → 暂存区 |
| `git commit` | 把暂存区打包成一次提交 | 暂存区 → 仓库区 |
| `git push` | 把仓库区的提交上传到远程 | 本地 → 远程 |

## 常用排查

```bash
git status          # 看当前状态（最常用，迷了就跑这个）
git log --oneline   # 看历史提交
git remote -v       # 看远程仓库地址
git branch          # 看当前在哪个分支
```

## 撤销操作（小心用）

```bash
# 撤销工作区的修改（未 add）
git checkout -- 文件名

# 撤销暂存（已 add 未 commit）
git reset HEAD 文件名

# 撤销最近一次 commit（保留改动）
git reset --soft HEAD^

# ⚠️ 危险：丢弃所有未提交的改动
git reset --hard
```

## .gitignore 是什么

放在项目根目录的一个文件，告诉 Git「**这些文件不要管**」。
典型需要忽略的：
- `node_modules/`（Node 依赖包，巨大）
- `.env`（环境变量，常含密码）
- `dist/` `build/`（构建产物，可重新生成）
- `.DS_Store`（macOS 自动生成）

## 第一次 push 报错速查

| 报错关键词 | 原因 | 解法 |
|---|---|---|
| `Permission denied (publickey)` | SSH Key 没配 | 重新配 SSH，或改用 HTTPS+PAT |
| `Could not resolve host` | 网络问题 | 检查网络 / VPN |
| `rejected because the remote contains work` | 远程有 README 冲突 | 在网站上删仓库重建，或 `git pull --allow-unrelated-histories` |
| `File xxx is 100 MB` | 误传大文件 | 加进 `.gitignore` 后 `git rm --cached xxx` |
| `Support for password authentication was removed` | GitHub 不再支持密码 push | 改用 PAT 或 SSH |
