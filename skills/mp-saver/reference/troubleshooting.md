# 失败兜底 · 6 个常见报错的 5 段式回答

> 当 `save_mp.py` 抛错、urllib 抓取失败、文件无法写入时，AI 按 5 段式回应：
> 1. **原文**：贴报错最后 1-2 行
> 2. **人话**：用 1 句大白话解释「发生了什么」
> 3. **根因**：技术层面的真正原因
> 4. **3 步**：用户能立刻执行的 3 个具体动作
> 5. **兜底**：本 skill 无能为力时的退路
>
> v2.0 起本 skill 零第三方依赖（不用装 playwright/Chromium），所以大部分 v1 的依赖报错都不再适用。新版常见报错集中在 urllib / 反爬兜底页 / 图片防盗链。

---

## 报错 1 · `urllib.error.HTTPError: HTTP Error 302` 或「反爬兜底页」

**1. 原文**：

```
[!] 失败的 URL：https://mp.weixin.qq.com/s/...
  原因：页面是反爬兜底页（验证码/仅微信打开/已删除）
  本 skill（纯 HTTP 版）无法绕过公众号反爬
  兜底：用浏览器手动打开后另存为网页
```

**2. 人话**：公众号给你弹了「请在微信中打开」「环境异常」之类的页面，不是真文章。

**3. 根因**：公众号服务端检测到非微信客户端流量后，会 302 跳到 captcha 页面 / 返兜底 HTML。v2.0 用 urllib 直接抓，没法执行 JS 检测脚本绕过。也可能是文章本身被删除 / 公众号被封禁。

**4. 3 步**：

1. 自己浏览器打开 `https://mp.weixin.qq.com/s/<id>` 看能不能正常加载（如果是验证码页，刷新几次试试）
2. 等半小时再试 —— 公众号封禁 IP 通常是临时的
3. 不行就换文章再试 —— 这篇真的不是公开能看的

**5. 兜底**：用浏览器手动打开 → Ctrl+S 另存为 .mhtml → 本 skill 的核心承诺是不登录，但这篇特例登一次微信才能看，没办法。

---

## 报错 2 · `urllib.error.URLError: <urlopen error [Errno 60] ...>` 或「连接超时」

**1. 原文**：

```
[!] 抓取失败：网络错误：Connection timed out
```

**2. 人话**：连不上 mp.weixin.qq.com（30 秒超时）。

**3. 根因**：可能是网络问题（你上不了外网）、或公众号文章加载慢（大量图片资源）。也可能是 DNS 污染 / 防火墙拦截。

**4. 3 步**：

1. 自己浏览器打开 `https://mp.weixin.qq.com/s/<id>` 看能不能加载
2. 如果不能 → 配代理：`export HTTPS_PROXY=http://127.0.0.1:7890`
3. 如果能但慢 → 加超时：`python3 scripts/save_mp.py --timeout 90 "<url>"`

**5. 兜底**：用浏览器手动打开 → Ctrl+S 另存为；本 skill 在你网络环境不好时无能为力。

---

## 报错 3 · 图片大部分是占位 / `<img src="data:image/...">`

**1. 原文**：

```
[!] unlazy 修补了 245 个 <img> 的 src
```

**2. 人话**：保存出来图片没显示 / 显示不全。

**3. 根因**：公众号使用懒加载模式（`<img src="1x1占位图" data-src="真图">`），v2.0 的 unlazy 函数会把占位图 src 换成 data-src 里的真图地址。但**有时 data-src 反而是占位图**（公众号历史模板）或者 **真图防盗链下载失败**。

**4. 3 步**：

1. 浏览器打开 .mhtml 看前 10 张图 + 后 10 张图显示情况
2. 如果个别图挂了 → 看 warn「图片下载失败 N 张」数量
3. 改用 `--format html` 让图片保持远程 URL（浏览器在线加载更稳）

**5. 兜底**：HTML 模式 + 在线看。彻底离线方案不再适用本 skill（用浏览器另存为）。

---

## 报错 4 · `Permission denied: '/Users/.../.../'` 或「没法写到指定目录」

**1. 原文**：

```
[!] 创建输出目录失败：PermissionError
```

**2. 人话**：脚本没法写到 `--output` 指定的目录。

**3. 根因**：目录不存在 / 父目录没写权限 / macOS 沙盒限制（如 Downloads 在某些系统版本下需要权限）/ 路径里有空格或特殊字符。

**4. 3 步**：

1. 检查目录存在 + 有写权限：`ls -ld <dir>`、`mkdir -p <dir> && touch <dir>/test`
2. 不指定 `--output`，用默认 `skills/mp-saver/task/2026<日期>-<slug>/`（脚本一定创建得到）
3. 改到你确定能写的目录：`--output /tmp/mp-saves/`

**5. 兜底**：完全换路径：`--output $HOME/Documents/mp-saves/`，或先 `cd /tmp && pwd && python3 ...` 跑在 /tmp 下。

---

## 报错 5 · 抓到 HTML 但 `<meta property="og:title">` 为空 / 标题乱码

**1. 原文**：

```
[!] 未命名公众号文章-mhtml
```

**2. 人话**：保存成功了，但文件名是「未命名公众号文章」（即从 HTML 里没抠到标题）。

**3. 根因**：极个别公众号文章没写 `<meta property="og:title">` 也没 `var msg_title` 等老 JS 变量，v2.0 的 `extract_title()` 多源提取全空，兜底用「未命名公众号文章」。

**4. 3 步**：

1. 用浏览器打开原 URL → 看实际标题
2. 把 mhtml 文件重命名（手动改 slug）
3. 把这个 case 报给 wanfeng，下次加更多提取源（如 JSON-LD、`<meta name="twitter:title">` 等）

**5. 兜底**：手动改 slug，或者用 `mv <UID>.mhtml <实际标题>.mhtml`。

---

## 报错 6 · `UnicodeEncodeError: 'ascii' codec can't encode ...`

**1. 原文**：

```
UnicodeEncodeError: 'ascii' codec can't encode character '\u4e2d' in position 0
```

**2. 人话**：终端默认编码不是 UTF-8，输出中文时报错。

**3. 根因**：macOS / Linux 默认终端 locale 是 `en_US.UTF-8` 但某些 SSH 会话会变成 `POSIX`；Windows cmd 默认 GBK。

**4. 3 步**：

1. macOS / Linux：`export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8`
2. Windows cmd：`chcp 65001`
3. 重跑脚本

**5. 兜底**：把 stdout 重定向到文件（绕开终端编码）：`python3 scripts/save_mp.py "<url>" > out.log 2>&1`

---

## 通用排查清单

跑任何报错前先看这 3 项：

```bash
# 1. Python 版本够吗？
python3 --version  # 必须 ≥ 3.10

# 2. 能上 mp.weixin.qq.com 吗？
curl -I https://mp.weixin.qq.com/s/test  # 应该返回 200 / 404，不会超时

# 3. 用 urllib 能拿到文章 HTML 吗？
python3 -c "
import urllib.request
req = urllib.request.Request('https://mp.weixin.qq.com/s/test-id', headers={
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 '
                'MicroMessenger/NetType/WIFI Language/zh_CN',
  'Referer': 'https://mp.weixin.qq.com/',
})
print(urllib.request.urlopen(req, timeout=10).status)
"
```

3 项都通过 → 跑 dry-run 测一次：

```bash
python3 scripts/save_mp.py --dry-run "https://mp.weixin.qq.com/s/abc"
```

dry-run 正常 → 拿掉 `--dry-run` 真跑一次。

---

## 报新错怎么办？

1. 把报错最后 5-10 行贴出来（去掉敏感信息）
2. 看是不是上面 6 个之一
3. 不是的话 —— 跑 `bash scripts/install.sh`（重检 Python 版本）
4. 还不行的话 —— 报 issue / 找 wanfeng 看看
