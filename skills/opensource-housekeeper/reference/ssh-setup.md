# SSH Key 配置详解（最常卡的一步）

> 为什么需要 SSH Key？——让 GitHub / AtomGit 知道「这台电脑」是「你」控制的。配一次永久免密。

## 1. 一句话配置（推荐 99% 用户）

```bash
# 生成（邮箱用你注册 GitHub/AtomGit 的邮箱）
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519 -N ""

# 启动 ssh-agent 并添加
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 复制公钥到剪贴板（macOS）
pbcopy < ~/.ssh/id_ed25519.pub

# 复制到剪贴板（Linux）
cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard

# 复制到剪贴板（Windows PowerShell）
Get-Content ~/.ssh/id_ed25519.pub | Set-Clipboard
```

然后：
- **GitHub**：打开 https://github.com/settings/keys → New SSH key → 粘贴 → 保存
- **AtomGit**：打开 https://atomgit.com/settings/keys → 添加 SSH 公钥 → 粘贴 → 保存

## 2. 验证是否配通

```bash
# GitHub
ssh -T git@github.com
# 成功显示：Hi {用户名}! You've been successfully authenticated

# AtomGit
ssh -T git@atomgit.com
# 成功显示：Hi {用户名}! You've been successfully authenticated
```

## 3. 一台电脑配多个 GitHub 账号

如果工作和个人是两个 GitHub 账号，需要 `~/.ssh/config`：

```
# 默认账号
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519

# 工作账号（用别的主机名）
Host github-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work
```

然后 clone 用 `git clone git@github-work:company/repo.git`。

## 4. 常见报错

| 报错 | 原因 | 解法 |
|---|---|---|
| `Could not open a connection to your authentication agent` | ssh-agent 没启 | `eval "$(ssh-agent -s)"` 再 `ssh-add` |
| `Bad permissions` | key 文件权限太开放 | `chmod 600 ~/.ssh/id_ed25519` |
| `Permission denied (publickey)` | 平台那边没加公钥 / 加错了 | 重新检查 platforms 的 keys 页面 |
| `ssh: connect to host github.com port 22: Connection timed out` | 网络封了 22 端口 | 改走 443 端口（见下方） |

## 5. 走 443 端口（GitHub 22 端口被封时的兜底）

在 `~/.ssh/config` 加：

```
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519
```

这样 ssh 走 443 端口（和 HTTPS 一样），通常不会被墙。

## 6. HTTPS + PAT 替代方案（不想配 SSH 的人）

```bash
# 让 Git 记住密码（macOS 自带 keychain）
git config --global credential.helper osxkeychain
# Windows
git config --global credential.helper wincred
# Linux
git config --global credential.helper store
```

第一次 push 时输入：
- Username：你的用户名
- Password：**你的 PAT**（不是登录密码！）

**PAT 生成位置**：
- GitHub：https://github.com/settings/tokens → Generate new token (classic) → 勾 `repo` 权限
- AtomGit：https://atomgit.com/settings/tokens → 生成 → 勾 `repository` 权限

⚠️ **PAT 相当于你的账号密码，不要截图、不要发给别人、不要 commit 到代码里。**
