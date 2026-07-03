# 人话版报错解读（12 类常见）

> SKILL.md 在每个失败处理里都会引用本表，把技术报错「翻译」成大白话。
> AI 的标准动作：先念原文，再念人话翻译，最后给 3 步解法。

---

## 1. SSH / 凭证类

### `Permission denied (publickey)`

| 项 | 内容 |
|---|---|
| **人话** | 「GitHub 不认识你家门钥匙」 |
| **为什么** | 你电脑里的 SSH 公钥没贴到 GitHub，或者贴错了 |
| **3 步解决** | 1. 重新复制公钥：`pbcopy < ~/.ssh/id_ed25519.pub`<br>2. 去 https://github.com/settings/keys 删旧 key、贴新 key<br>3. 测一下：`ssh -T git@github.com` |
| **兜底** | 改用 HTTPS+PAT（最简单，不用配 SSH） |

### `Bad permissions`（SSH key 文件权限问题）

| 项 | 内容 |
|---|---|
| **人话** | 「钥匙的存放位置太开放，SSH 不放心用」 |
| **为什么** | 私钥文件必须是 600 权限（只有你能读写） |
| **1 步解决** | `chmod 600 ~/.ssh/id_ed25519` |
| **兜底** | 重新生成：`rm ~/.ssh/id_ed25519*` 然后跑 ssh-keygen |

### `Could not open a connection to your authentication agent`

| 项 | 内容 |
|---|---|
| **人话** | 「钥匙管家没启动」 |
| **为什么** | `ssh-agent` 是管钥匙的后台进程，没启就 add 不进去 |
| **2 步解决** | 1. 启动：`eval "$(ssh-agent -s)"`<br>2. 装上：`ssh-add ~/.ssh/id_ed25519` |

### `Support for password authentication was removed`

| 项 | 内容 |
|---|---|
| **人话** | 「GitHub 不让用密码登录了」 |
| **为什么** | 2021 年起 GitHub 关掉了密码 push，必须用 PAT 或 SSH |
| **2 步解决** | 1. 去 https://github.com/settings/tokens 生成 PAT（勾 `repo` 权限）<br>2. 第一次 push 时用户名填 GitHub 用户名、密码填 PAT |

---

## 2. 网络 / DNS 类

### `Could not resolve host: github.com`

| 项 | 内容 |
|---|---|
| **人话** | 「找不到服务器地址（DNS 不知道 github.com 在哪）」 |
| **为什么** | DNS 解析失败，可能是 ISP 屏蔽 / DNS 污染 |
| **3 步解决** | 1. 测 DNS：`nslookup github.com`<br>2. 换 DNS：网络设置里改成 `223.5.5.5`（阿里）或 `8.8.8.8`（Google）<br>3. 还不行就 ping IP：`ping 140.82.114.3`（GitHub 真实 IP，可能已变） |
| **兜底** | 用国内镜像 `ghfast.top` 绕开 DNS |

### `Failed to connect to github.com port 443: Connection timed out`

| 项 | 内容 |
|---|---|
| **人话** | 「连不上 GitHub 的 443 端口（被防火墙挡住了）」 |
| **为什么** | 国内封了 GitHub 的某些端口 |
| **3 步解决** | 1. 测其他端口：`nc -zv github.com 22`（看 SSH 端口通不通）<br>2. 走代理：设 `HTTPS_PROXY=http://127.0.0.1:7890`<br>3. 改用镜像：`ghfast.top` |
| **兜底** | 切到国内平台：AtomGit / Gitee |

### `Connection refused`

| 项 | 内容 |
|---|---|
| **人话** | 「服务器在那个端口没开服务」 |
| **为什么** | 网络能到，但服务不响应 / 防火墙拦截 / 端口错了 |
| **3 步解决** | 1. 换端口试试<br>2. 关防火墙临时测试：`sudo pfctl -d`（macOS）<br>3. 检查代理：`echo $HTTPS_PROXY` |
| **兜底** | 重新 `git clone` 一次（可能临时网络抖动） |

### `SSL certificate problem: unable to get local issuer certificate`

| 项 | 内容 |
|---|---|
| **人话** | 「HTTPS 证书不被信任」 |
| **为什么** | 系统时间不对 / CA 证书过期 / 用了抓包工具 |
| **3 步解决** | 1. 校准时间：`sudo sntp -sS time.apple.com`（macOS）<br>2. 升 ca-certificates：`brew install ca-certificates`（macOS）<br>3. 临时绕过：`git -c http.sslVerify=false clone ...`（⚠️ 不安全） |
| **兜底** | 重启电脑 / 重装 Git |

---

## 3. Git 冲突 / 状态类

### `Updates were rejected because the remote contains work that you do not have locally`

| 项 | 内容 |
|---|---|
| **人话** | 「网上有你没的改动，本地版本太老」 |
| **为什么** | 你（或者别人） push 过东西，你没 pull 就又 push |
| **3 步解决** | 1. 先拉下来：`git pull origin main --rebase`（把本地提交重新放网上）<br>2. 看冲突文件并解决（搜索 `<<<<<<<`）<br>3. 再 push：`git push origin main` |
| **兜底** | 强推覆盖（⚠️ 会丢网上历史）：`git push -f origin main` |

### `fatal: refusing to merge unrelated histories`

| 项 | 内容 |
|---|---|
| **人话** | 「两个完全不同的项目历史，Git 不让合」 |
| **为什么** | 本地仓库和远程仓库是「两个爸爸生的」，没共同祖先 |
| **1 步解决** | 加 `--allow-unrelated-histories`：`git pull origin main --allow-unrelated-histories` |
| **兜底** | 删本地仓库重来（确认远程没东西要保留） |

### `Your branch is ahead of 'origin/main' by N commits`

| 项 | 内容 |
|---|---|
| **人话** | 「本地有 N 个提交没传到网上」 |
| **为什么** | 你 commit 了但忘了 push |
| **1 步解决** | `git push origin main` |
| **预防** | 改完代码就 push，别攒着 |

---

## 4. 端口 / 启动类

### `Error: listen EADDRINUSE: address already in use :::3000`

| 项 | 内容 |
|---|---|
| **人话** | 「3000 端口被别的程序占着」 |
| **为什么** | 上次的服务没正常关 / 有别的项目也用 3000 |
| **3 步解决** | 1. 找占用进程：`lsof -i :3000`（macOS/Linux）<br>2. 杀进程：`kill -9 {PID}`<br>3. 改启动端口：项目里找 `port: 3000` 改成 3001 |
| **预防** | 停服务用 `Ctrl+C`，别直接关终端 |

### `Cannot find module 'xxx'`

| 项 | 内容 |
|---|---|
| **人话** | 「项目要用的包没装上」 |
| **为什么** | 没跑 `npm install` / 装的时候报错但没注意 |
| **3 步解决** | 1. 重装依赖：`rm -rf node_modules && npm install`<br>2. 升 Node：要求 ≥ 18（用 nvm：`nvm install 18`）<br>3. 单独装这个包：`npm install xxx` |
| **兜底** | 删 `package-lock.json` 再 `npm install` |

### `npm ERR! peer dep missing`

| 项 | 内容 |
|---|---|
| **人话** | 「A 包说要 B 包一起用，但 B 没装上（或版本不对）」 |
| **为什么** | 依赖关系没装全 |
| **3 步解决** | 1. `npm install --legacy-peer-deps`（绕开严格检查）<br>2. 升 Node 到最新 LTS<br>3. 删 lockfile 重装：`rm package-lock.json && npm install` |
| **兜底** | 报 issue 问项目作者 |

---

## 5. 大文件 / 容量类

### `remote: error: File xxx is 100.00 MB`

| 项 | 内容 |
|---|---|
| **人话** | 「网上仓库不让单个文件超过 100MB（怕撑爆服务器）」 |
| **为什么** | 误传了大文件（视频、压缩包、设计稿源文件等） |
| **3 步解决** | 1. 看大文件：`du -sh */ | sort -h`（找目录里最大的东西）<br>2. 加进 `.gitignore`：`echo "node_modules/" >> .gitignore`<br>3. 如果已传：`git rm --cached xxx`（从 Git 记忆里删，但保留本地） |
| **兜底** | 用 Git LFS（大文件专用工具）：`git lfs install` 然后 `git lfs track "*.psd"` |

### `fatal: unable to access ... The requested URL returned error: 413`

| 项 | 内容 |
|---|---|
| **人话** | 「上传的东西太大，服务器拒绝接收」 |
| **为什么** | 单次 push 数据量超限 |
| **2 步解决** | 1. 拆 commit：分开 push 几次<br>2. 排除大文件（见上一条） |
| **兜底** | 改用 `git push --no-thin`（不压缩推送） |

---

## 6. Gitee 特有

### `Error: Gitee 仓库创建失败 / push 失败，要求实名`

| 项 | 内容 |
|---|---|
| **人话** | 「Gitee 规定创建公开仓库必须先实名认证」 |
| **为什么** | 2022 年起 Gitee 的合规要求 |
| **2 步解决** | 1. 去 https://gitee.com/profile/account_information 认证（身份证+人脸）<br>2. 等 5 分钟审核通过 |
| **兜底** | 换 AtomGit（不需要实名）或 改用 Private 仓库 |

---

## 报错速查决策树

```
报错里有这些关键词 → 看对应分类
├── "Permission" / "denied" / "publickey" / "authentication"  → SSH/凭证类
├── "Could not resolve" / "Connection timed out" / "SSL"      → 网络/DNS 类
├── "rejected" / "unrelated histories" / "branch is ahead"   → Git 冲突类
├── "EADDRINUSE" / "Cannot find module" / "peer dep"          → 端口/启动类
├── "100 MB" / "413" / "lfs"                                  → 大文件类
└── "实名" / "Gitee"                                          → Gitee 特有
```

> **使用方式**：AI 在 SKILL.md 失败处理里说「人话翻译 + 3 步解法」时，直接复制对应表格到对话里。
