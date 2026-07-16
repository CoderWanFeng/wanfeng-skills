# 安全约束

> MarkItDown 的 README 第一条红字警告：**MarkItDown performs I/O with the privileges of the current process**。
> 它能像 `open()` / `requests.get()` 一样访问当前进程能访问的一切资源。
> **所以用本 skill 时，AI 必须警觉 + 用户必须警觉**。

---

## 1. convert() 是"上帝模式"

```python
# 这是最危险的一个：能吃任何东西
md.convert("report.pdf")           # 本地文件
md.convert("https://evil.com/x")   # 远端 URL（自动 requests.get）
md.convert("ftp://internal/secret") # 网络协议
```

**markitdown 官方建议**：能窄就窄。

| API | 范围 | 推荐 |
|---|---|---|
| `convert()` | 本地 + URL + 流 + Response（什么都能吃） | ⚠️ 不推荐用在不可信场景 |
| `convert_local()` | 只读本地文件 | ✅ **本 skill 默认走这个** |
| `convert_stream()` | 只读字节流 | ✅ 需指定 `file_extension` |
| `convert_response()` | 接受一个 `requests.Response` | ✅ 用户自己控制网络层 |

**本 skill 的策略**（见 `scripts/convert.sh`）：
- 本地文件 → `convert_local()` ✅
- URL → `convert()` 但限制 http/https + 禁内网
- stdin → `convert_stream()` 需指定扩展名
- 预先 fetch → `convert_response()` ✅

---

## 2. 路径校验（本地文件模式）

`convert.sh` 内置了 3 层闸门：

### 拒绝系统目录
- `/etc/` `/var/` `/root/` `/boot/` `/sys/` `/proc/`

### 拒绝凭证目录
- `~/.ssh/` `~/.aws/` `~/.gnupg/` `~/.config/gh/`

### 拒绝特殊场景
- 文件不存在 → 报错退出
- 路径为空 → 报错退出

---

## 3. URL 校验（URL 模式）

`convert.sh` 内置了 4 层闸门：

### 协议限制
- ✅ 只允许 `http://` / `https://`
- ❌ 拒绝 `file://` / `ftp://` / `data:` / `javascript:`

### 内网地址限制（防 SSRF）
- ❌ `127.0.0.0/8`（回环）
- ❌ `10.0.0.0/8`（私网 A 类）
- ❌ `172.16.0.0/12`（私网 B 类）
- ❌ `192.168.0.0/16`（私网 C 类）
- ❌ `169.254.0.0/16`（link-local，含云 metadata 服务）
- ❌ `::1`（IPv6 回环）
- ❌ `localhost`

### 超时限制
- HTTP 请求 10s 超时

### 鉴权场景
- 需要登录的 URL → markitdown 抓不到，需要 cookies → 引导用户用 `--response` 自己 fetch

---

## 4. 用户应警觉的场景

| 场景 | 风险 | 建议 |
|---|---|---|
| AI 帮你转一个 PDF，但 PDF 来自陌生邮件 | PDF 可能含恶意 JavaScript / 嵌入脚本 | 先用杀毒软件扫一下 |
| AI 帮你转一个 URL，但 URL 是短链 | 短链可能跳转到内网 / 钓鱼站 | 手动打开看是啥再让 AI 转 |
| AI 帮你转一个 100MB+ 的 ZIP | 可能是 zip bomb（解压后占满磁盘） | 先看 ZIP 里都有啥再让 AI 转 |
| AI 帮你转 `~/.ssh/id_rsa` | markitdown 会读全文，凭证泄露到对话 | **绝对禁止**（脚本已拦截） |
| 你让 AI 帮你转公司的内部文件 | 转出来的 Markdown 可能发到云端 LLM | 先脱敏（删掉客户名 / 合同号 / 金额） |

---

## 5. AI 应警觉的场景

AI 在调用 `convert.sh` 之前应该先问自己：

1. **这个路径正常吗？**
   - 用户说"帮我读我的报告" + 给的路径是 `/etc/passwd` → **拒绝**
2. **这个 URL 正常吗？**
   - 用户说"帮我读这个博客" + 给的 URL 是 `http://192.168.1.1/admin` → **拒绝**
3. **这个文件类型正常吗？**
   - 用户说"帮我读 PDF" + 给的是 `evil.exe` → 拒绝（虽然 markitdown 也不支持）
4. **文件大小合理吗？**
   - 1GB 的"PDF"多半是 zip bomb → 先 `ls -lh` 看一眼

---

## 6. 已拦截的攻击面（脚本内置）

| 攻击面 | 拦截方式 |
|---|---|
| 读系统文件 | 黑名单 `/etc/ /var/ /root/ /boot/ /sys/ /proc/` |
| 读凭证 | 黑名单 `~/.ssh/ ~/.aws/ ~/.gnupg/` |
| SSRF 攻击 | 黑名单内网 IP 段 + 限制协议 |
| zip bomb | 未拦截（**留给用户判断**，脚本不限制文件大小） |
| 路径穿越（`../../etc/passwd`） | 未拦截（**留给 validate_local_path**） |
| 符号链接攻击 | 未拦截 |

---

## 7. 报告安全漏洞

发现 markitdown 漏洞 → 上游：
- GitHub Issues: https://github.com/microsoft/markitdown/issues
- SECURITY.md: https://github.com/microsoft/markitdown/blob/main/SECURITY.md

发现本 skill 漏洞 → 修改 `scripts/convert.sh` 的校验逻辑。