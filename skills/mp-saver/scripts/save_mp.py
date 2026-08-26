#!/usr/bin/env python3
"""
save_mp.py · 公众号文章保存器 · 纯 HTTP 版（v2.0）

不登录 → 用 urllib 抓 HTML（带 WeChat UA + Referer）→ 智能修补 HTML
（unlazy 懒加载图、提取标题、加 <base>）→ 下载图片转 base64 内嵌
→ 写单文件 .mhtml。

v2.0 改动（对比 v1.x）：
- 去 Playwright 依赖：体积从 ~150MB 降到 0（只走 Python 标准库）
- 去 Chromium 下载：install.sh 不再下载浏览器
- 启动速度：秒级（vs Playwright 启动要 5-10 秒）
- 风险：遇到强反爬会拿到验证码壳（curl 拿不到 JS 渲染）

用法：
    python3 save_mp.py <url> [<url2> ...]
    python3 save_mp.py --file urls.txt
    python3 save_mp.py --output <dir> <url>
    python3 save_mp.py --format html <url>             # HTML（图片仍远程，最快）
    python3 save_mp.py --format mhtml --max-images 50  # 只内嵌前 50 张图

设计原则：
- 默认走纯 HTTP，依赖最少
- 失败透明：报错时直接给出可读错误 + 兜底提示「改用浏览器方案」
- 不自动生成截图，干净退出
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ============ 颜色输出 ============
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def info(msg: str) -> None:
    print(f"{GREEN}[✓]{NC} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}[!]{NC} {msg}", file=sys.stderr)


def err(msg: str) -> None:
    print(f"{RED}[✗]{NC} {msg}", file=sys.stderr)


def step(msg: str) -> None:
    print(f"{CYAN}→{NC} {msg}")


# ============ 常量 ============
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_TASK_ROOT = SKILL_ROOT / "task"

# 微信公众号文章 URL 规则（必须校验）
MP_URL_LOOSE = re.compile(r"mp\.weixin\.qq\.com", re.IGNORECASE)

# WeChat 内置浏览器 UA（公众号反爬的关键 UA 之一，含 MicroMessenger NetType 标识）
WECHAT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 "
    "MicroMessenger/NetType/WIFI Language/zh_CN"
)


# ============ URL 校验 ============
def validate_url(url: str) -> tuple[bool, str]:
    """校验 URL 是否是微信公众号文章链接。"""
    if not url or not url.strip():
        return False, "URL 为空"
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, f"协议必须是 http/https，当前是 {parsed.scheme or '空'}"
    if not MP_URL_LOOSE.search(parsed.netloc):
        return False, f"域名必须是 mp.weixin.qq.com，当前是 {parsed.netloc}"
    if not parsed.path.startswith("/s"):
        return False, f"公众号文章路径必须是 /s/...，当前是 {parsed.path}"
    return True, ""


# ============ Slug 工具 ============
_SLUG_BAD = re.compile(r"[^\w\u4e00-\u9fff\-]+", re.UNICODE)
_SLUG_DASH = re.compile(r"-+")


def slugify(text: str, max_len: int = 50) -> str:
    """把标题变成安全的文件名片段。"""
    if not text:
        return ""
    text = re.sub(r"\s+", "-", text.strip())
    text = _SLUG_BAD.sub("", text)
    text = _SLUG_DASH.sub("-", text).strip("-")
    return text[:max_len]


def safe_filename(name: str) -> str:
    """去掉文件系统不合法字符。"""
    bad = re.compile(r'[\\/:\*\?"<>\|\x00-\x1f]')
    return bad.sub("_", name).strip()


# ============ HTTP 抓取 ============
def fetch_html(url: str, timeout: int = 30) -> tuple[str, str]:
    """抓取 URL 返回 HTML 和 final_url。出错抛 FetchError。

    关键 header：
    - User-Agent 必须含 MicroMessenger/NetType/WIFI（公众号识别微信流量）
    - Referer 必须是 mp.weixin.qq.com（同源策略要求）
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": WECHAT_UA,
                "Referer": "https://mp.weixin.qq.com/",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            charset = "utf-8"
            content_type = r.headers.get("Content-Type", "")
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()
            raw = r.read()
            html = raw.decode(charset, errors="replace")
            return html, r.url
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code}：{e.reason}") from e
    except urllib.error.URLError as e:
        raise FetchError(f"网络错误：{e.reason}") from e
    except Exception as e:
        raise FetchError(f"未知错误：{e}") from e


class FetchError(Exception):
    """抓取失败的统一定义。"""


# ============ 反爬检测 ============
#
# 公众号反爬特征（实测，避免误判）：
# - 真正被反爬：URL 跳转 → `mp/wappoc_appmsgcaptcha`，HTML 短（< 30KB），含验证码图
# - 真文章页：URL 仍留在 /s/...，HTML 巨大（>500KB），含 mmbiz.qpic.cn 图床引用
#
# 关键经验：去掉「请在微信中打开」这个 marker —— 公众号所有页面的 JS
# 检测脚本里都会带这个字符串（包括真文章页），用它当标记会**所有文章都误判**。
_MIN_HTML_SIZE = 30_000  # 真文章页通常 > 500KB；验证码兜底页 < 30KB
_VALID_IMG_DOMAIN = "mmbiz.qpic.cn"  # 公众号图床。真文章页一定有


def is_fallback_page(html: str, final_url: str = "") -> bool:
    """检测是不是反爬兜底页 / 验证码页。

    判定规则（任一命中 = 兜底）：
    1. URL 跳到 `/wappoc_appmsgcaptcha` 这种 captcha 路径
    2. HTML 长度 < 30KB（兜底页通常很小）+ 含「环境异常」/「验证身份」
    3. 没有真文章应有的图床域名（mmbiz.qpic.cn）
    """
    # 1. URL 跳 captcha 路径 → 99% 是兜底
    if "wappoc_appmsgcaptcha" in final_url.lower():
        return True

    # 2. HTML 极小 + 命中关键词
    if len(html) < _MIN_HTML_SIZE:
        if "环境异常" in html or "验证身份" in html or "请完成验证" in html:
            return True

    # 3. 没图床 + 有删除/封禁关键词
    if _VALID_IMG_DOMAIN not in html:
        fatal_markers = (
            "该公众号已被屏蔽",
            "该文章已被发布者删除",
            "此公众号已迁移",
            "该公众号已注销",
        )
        if any(m in html for m in fatal_markers):
            return True

    return False


# ============ 标题提取 ============
# 优先级：og:title > og:description > <title> > var msg_desc > var nickname
_TITLE_PATTERNS = [
    # og:title 是最稳的（公众号为了分享会写这个）
    re.compile(
        r"""<meta\b[^>]*?property=["']og:title["'][^>]*?content=["']([^"']+)["']""",
        re.IGNORECASE,
    ),
    # 部分文章没 og:title 但有 og:description 作为描述
    re.compile(
        r"""<meta\b[^>]*?property=["']og:description["'][^>]*?content=["']([^"']+)["']""",
        re.IGNORECASE,
    ),
    # 旧版 JS 变量
    re.compile(r"""var\s+msg_title\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE),
    re.compile(r"""var\s+msg_desc\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE),
    re.compile(r"""var\s+nickname\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE),
    # 兜底：<title>（公众号经常是空的，但有总比没有好）
    re.compile(r"<title>([^<]+)</title>", re.IGNORECASE),
]


def extract_title(html: str) -> str:
    """智能提取公众号文章标题。按优先级找，找到立刻返回。"""
    for pattern in _TITLE_PATTERNS:
        m = pattern.search(html)
        if m:
            title = m.group(1).strip()
            # 过滤掉没意义的占位
            if title and title not in ("微信公众平台", "Wechat", ""):
                return title
    return ""


# ============ HTML 修补 ============
# 公众号正文图片常用模式：
#   <img src="占位图.gif" data-src="https://mmbiz.qpic.cn/真图.png">
#   或现代版：<img src="https://mmbiz.qpic.cn/真图.png" data-src="同地址">
# unlazy 任务：把 data-src 提到 src（仅当 src 是占位图/data: 时）

# 占位图标记（公众号常用 data:image 1x1 GIF 或 res.wx.qq.com 占位）
_PLACEHOLDER_PATTERNS = (
    re.compile(r"^data:image/[a-z]+;base64,", re.IGNORECASE),  # 内嵌 1x1 GIF
    re.compile(r"/res\.wx\.qq\.com/.*\.(gif|png|jpg)\?", re.IGNORECASE),  # 微信域名占位
)

# img 标签的 src / data-src 正则（写得宽松，支持单引号双引号无引号）
_IMG_TAG_RE = re.compile(
    r"<img\b([^>]*?)(/?>)", re.IGNORECASE | re.DOTALL
)
_SRC_ATTR_RE = re.compile(
    r"""(\bsrc\s*=\s*)(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
    re.IGNORECASE,
)
_DATASRC_ATTR_RE = re.compile(
    r"""(\bdata-src\s*=\s*)(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
    re.IGNORECASE,
)


def is_placeholder_url(url: str) -> bool:
    """判断 src 是不是占位图。"""
    if not url:
        return True
    return any(p.search(url) for p in _PLACEHOLDER_PATTERNS)


def _replace_attr(quote_type: str, prefix: str, old_val: str, new_val: str) -> str:
    """构造新属性串。quote_type: '"' | "'" | '' (无引号)."""
    if quote_type == '"':
        return f'{prefix}"{new_val}"'
    elif quote_type == "'":
        return f"{prefix}'{new_val}'"
    else:
        return f"{prefix}{new_val}"


def unlazy_images(html: str) -> tuple[str, int]:
    """把 <img src="占位"> data-src="真图"> 形式的图，data-src 提到 src。

    返回 (新 HTML, 替换数量)。现代公众号 HTML 通常 src 已经是真地址，此函数是防御性的。
    """
    replaced = 0

    def fix_img(m: re.Match) -> str:
        nonlocal replaced
        full_attrs = m.group(1)
        close = m.group(2)

        # 1. 当前 src 值
        src_match = _SRC_ATTR_RE.search(full_attrs)
        if not src_match:
            return m.group(0)  # 没 src，跳过

        prefix = src_match.group(1)
        if src_match.group(2) is not None:
            quote, cur_src = '"', src_match.group(2)
        elif src_match.group(3) is not None:
            quote, cur_src = "'", src_match.group(3)
        else:
            quote, cur_src = "", src_match.group(4)

        # 2. 当前 src 是占位图 → 尝试从 data-src 拿真地址
        if is_placeholder_url(cur_src):
            data_match = _DATASRC_ATTR_RE.search(full_attrs)
            if data_match:
                ds_val = next(
                    (g for g in data_match.groups()[1:] if g is not None), None
                )
                if ds_val and not is_placeholder_url(ds_val):
                    # 替换 src
                    new_src = _replace_attr(quote, prefix, cur_src, ds_val)
                    new_attrs = full_attrs[: src_match.start()] + new_src + full_attrs[src_match.end() :]
                    replaced += 1
                    return f"<img{new_attrs}{close}"

        return m.group(0)

    new_html = _IMG_TAG_RE.sub(fix_img, html)
    return new_html, replaced


# ============ 图片内嵌 ============
# 匹配 <img src="...">（已有 src，包括 mmbiz.qpic.cn 真图）
_IMG_SRC_FINAL_RE = re.compile(
    r"""<img\b[^>]*?\bsrc\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))""",
    re.IGNORECASE | re.DOTALL,
)


def _http_fetch_bytes(url: str, timeout: int = 10) -> bytes | None:
    """下载 URL 返回字节。失败返回 None。"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": WECHAT_UA,
                "Referer": "https://mp.weixin.qq.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def _guess_image_ext(url: str, content_type: str = "") -> str:
    """根据 URL / content-type 猜图片扩展名。"""
    if content_type:
        ct = content_type.split(";", 1)[0].strip().lower()
        ext = mimetypes.guess_extension(ct)
        if ext:
            return ext.lstrip(".")
    path = urlparse(url).path
    if "." in path.split("?", 1)[0].rsplit("/", 1)[-1]:
        ext = path.rsplit(".", 1)[-1].split("?", 1)[0].lower()
        return ext or "png"
    return "png"


def embed_images(
    html: str, page_url: str, max_images: int = 0
) -> tuple[str, int, int]:
    """把所有 <img src="真图"> 里的 URL 下回来转 base64 data: URI。

    Args:
        html: HTML 字符串
        page_url: 页面 URL（用于相对路径转绝对）
        max_images: 限制最多内嵌张数。0 = 不限。

    Returns:
        (新 HTML, 成功内嵌数, 失败数)
    """
    # 收集所有待下载 URL（去重）
    urls_to_fetch: set[str] = set()
    url_quote_pairs: list[tuple[str, str]] = []  # 记录每个 URL 的原始引号风格
    for m in _IMG_SRC_FINAL_RE.finditer(html):
        url = next((g for g in m.groups() if g), None)
        if url and not url.startswith("data:") and not is_placeholder_url(url):
            if url not in urls_to_fetch:
                urls_to_fetch.add(url)

    if not urls_to_fetch:
        return html, 0, 0

    # max_images 限制
    if max_images > 0:
        urls_to_fetch = set(list(urls_to_fetch)[:max_images])

    # 下载 + 转 data: URI
    url_to_data: dict[str, str] = {}
    ok_count = 0
    fail_count = 0
    for url in urls_to_fetch:
        absolute = url if url.startswith("http") else urljoin(page_url, url)
        data = _http_fetch_bytes(absolute)
        if not data:
            fail_count += 1
            continue
        ext = _guess_image_ext(absolute)
        mime = mimetypes.guess_type(f"x.{ext}")[0] or "image/png"
        b64 = base64.b64encode(data).decode("ascii")
        url_to_data[url] = f"data:{mime};base64,{b64}"
        ok_count += 1

    # 替换 HTML（双引号 / 单引号 / 裸 三种形式）
    for old_url, new_uri in url_to_data.items():
        for old_q, new_q in (
            (f'src="{old_url}"', f'src="{new_uri}"'),
            (f"src='{old_url}'", f"src='{new_uri}'"),
        ):
            if old_q in html:
                html = html.replace(old_q, new_q)

    return html, ok_count, fail_count


# ============ 单篇保存 ============
def save_one(
    url: str,
    out_dir: Path,
    fmt: str,
    timeout: int,
    max_images: int,
    dry_run: bool,
) -> dict:
    """保存一篇公众号文章到 out_dir。

    流程：抓 HTML → 智能修补（unlazy 图 + 标题提取 + 加 <base>）
         → mhtml 模式下载图片内嵌 / html 模式保留远程 → 写文件。
    """
    result = {
        "url": url,
        "title": "",
        "path": "",
        "ok": False,
        "error": "",
        "size": 0,
    }

    if dry_run:
        step(f"[dry-run] {url} → {out_dir}/<slug>.{fmt}")
        result["ok"] = True
        return result

    # 1) 抓 HTML
    step(f"抓取：{url}")
    try:
        html, final_url = fetch_html(url, timeout=timeout)
    except FetchError as e:
        result["error"] = f"抓取失败：{e}"
        return result

    if not html or len(html) < 1000:
        result["error"] = "HTML 太小（<1KB），可能不是文章页"
        return result

    # 2) 检测反爬兜底页
    if is_fallback_page(html, final_url):
        result["error"] = (
            "页面是反爬兜底页（验证码/仅微信打开/已删除）\n"
            "  本 skill（纯 HTTP 版）无法绕过公众号反爬\n"
            "  兜底：用浏览器手动打开后另存为网页"
        )
        return result

    info(f"抓到 HTML（{len(html) / 1024:.1f} KB）")

    # 3) 解码
    title = extract_title(html)
    if not title:
        title = "未命名公众号文章"
    result["title"] = title

    # 4) 修补 HTML：unlazy 图 + 加 <base>
    html, n_unlazy = unlazy_images(html)
    if n_unlazy > 0:
        info(f"unlazy 修补了 {n_unlazy} 个 <img> 的 src")

    # 5) mhtml 模式：内嵌图片
    ext = fmt
    if fmt == "mhtml":
        html, n_embedded, n_failed = embed_images(html, final_url, max_images=max_images)
        if n_failed > 0:
            warn(f"图片下载失败 {n_failed} 张（可能防盗链）")
        if n_embedded == 0 and n_failed == 0:
            warn("没找到任何 <img>，可能文章是纯文字")

    # 6) 加 <base href="..."> 让相对路径资源 / <a href> 不 404
    html = re.sub(
        r"<head([^>]*)>",
        r'<head\1><base href="' + final_url + '">',
        html,
        count=1,
    )

    # 7) 写文件
    blob = html.encode("utf-8")
    slug = slugify(title) or "untitled"
    out_path = out_dir / f"{safe_filename(slug)}.{ext}"
    counter = 1
    while out_path.exists():
        out_path = out_dir / f"{safe_filename(slug)}-{counter}.{ext}"
        counter += 1
    out_path.write_bytes(blob)
    result["path"] = str(out_path)
    result["size"] = out_path.stat().st_size
    result["ok"] = True
    info(
        f"已保存：{out_path.name}（{result['size'] / 1024:.1f} KB，标题：{title[:30]}）"
    )
    return result


# ============ index.md 渲染 ============
INDEX_TEMPLATE = """# 公众号文章保存任务 · {date}

> 自动生成于 {timestamp}
> 共保存 {total} 篇（成功 {ok_count}，失败 {fail_count}）
> 输出目录：`{out_dir}`
> 实现：v2.0 纯 HTTP 版（不依赖 Playwright/Chromium）

## 保存清单

{entries}

## 失败清单

{fails}
"""


def render_index(results: list[dict], out_dir: Path) -> Path:
    """把保存结果汇总成 index.md。"""
    date = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().isoformat(timespec="seconds")
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    entries: list[str] = []
    fails: list[str] = []
    for idx, r in enumerate(results, 1):
        if r["ok"]:
            entries.append(
                f"{idx}. **{r['title']}**\n"
                f"   - 路径：`{r['path']}`\n"
                f"   - 大小：{r['size'] / 1024:.1f} KB\n"
                f"   - 链接：{r['url']}\n"
            )
        else:
            fails.append(
                f"{idx}. {r['url']}\n   - 原因：{r['error']}\n"
            )

    md = INDEX_TEMPLATE.format(
        date=date,
        timestamp=timestamp,
        total=len(results),
        ok_count=ok_count,
        fail_count=fail_count,
        out_dir=out_dir,
        entries="\n".join(entries) if entries else "_（无）_",
        fails="\n".join(fails) if fails else "_（无）_",
    )
    index_path = out_dir / "index.md"
    index_path.write_text(md, encoding="utf-8")
    return index_path


# ============ 主流程 ============
def collect_urls(args) -> list[str]:
    """从命令行参数 + --file 文件 收集 URL。"""
    urls = list(args.urls or [])
    if args.file:
        if not Path(args.file).exists():
            err(f"[失败] 文件不存在：{args.file}")
            sys.exit(1)
        with Path(args.file).open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                urls.append(line)
    if not urls:
        err("[失败] 没传任何 URL")
        print("  用法：python3 save_mp.py <url1> [url2 ...]")
        print("        python3 save_mp.py --file urls.txt")
        print("  详细：python3 save_mp.py --help")
        sys.exit(1)
    # 去重，保留顺序
    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def main() -> int:
    parser = argparse.ArgumentParser(
        description="公众号文章保存器（v2.0 纯 HTTP 版 · 零依赖浏览器）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="一个或多个 mp.weixin.qq.com/s/... 链接",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="从文件读 URL 列表（每行一个，# 开头视为注释）",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出目录（默认 skills/mp-saver/task/<日期>-<slug>/）",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=("mhtml", "html"),
        default="mhtml",
        help=(
            "保存格式：mhtml（默认，单文件含图 + base64 内嵌）/ "
            "html（只 HTML，图片仍远程，最快）"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="单页抓取超时秒数（默认 30）",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help=(
            "mhtml 模式最多内嵌几张图（0=不限）。限制后图片仍是远程 URL。"
            "建议 100~200，免爆盘。"
        ),
    )
    parser.add_argument(
        "--slug",
        type=str,
        default="",
        help="任务目录名后缀（默认用首篇标题 slug）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印会做什么，不真保存",
    )
    args = parser.parse_args()

    # 1) 收集 URL
    urls = collect_urls(args)

    # 2) 校验 URL
    valid: list[str] = []
    for u in urls:
        ok, reason = validate_url(u)
        if ok:
            valid.append(u)
        else:
            warn(f"跳过无效 URL：{u}（{reason}）")
    if not valid:
        err("[失败] 没有有效 URL")
        sys.exit(1)
    info(f"共 {len(valid)} 个有效 URL 待保存")

    # 3) 决定输出目录
    if args.output:
        out_dir = Path(args.output).expanduser().resolve()
    else:
        date = datetime.now().strftime("%Y%m%d")
        slug = args.slug or slugify(
            valid[0].rstrip("/").split("/")[-1].split("?")[0][:30] or "batch",
            max_len=30,
        )
        out_dir = DEFAULT_TASK_ROOT / f"{date}-{slug}"
    info(f"输出目录（真跑才会创建）：{out_dir}")

    if args.dry_run:
        for u in valid:
            step(f"[dry-run] {u}")
        return 0

    # 真跑才创建输出目录
    out_dir.mkdir(parents=True, exist_ok=True)

    # 4) 逐个保存（纯 HTTP，无浏览器）
    results: list[dict] = []
    for url in valid:
        r = save_one(
            url=url,
            out_dir=out_dir,
            fmt=args.format,
            timeout=args.timeout,
            max_images=args.max_images,
            dry_run=False,
        )
        results.append(r)

    # 5) 写 index.md
    index_path = render_index(results, out_dir)

    # 6) 回执
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    print()
    info(f"任务完成：成功 {ok_count} / 失败 {fail_count}")
    info(f"清单文件：{index_path}")
    if fail_count > 0:
        print()
        warn("失败的 URL：")
        for r in results:
            if not r["ok"]:
                print(f"  - {r['url']}: {r['error']}")

    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
