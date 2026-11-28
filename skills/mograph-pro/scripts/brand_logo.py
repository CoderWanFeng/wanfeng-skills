#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按品牌名自动取官方 Logo · mograph-pro Step A2-2 辅助脚本

用途
----
口播里点了某个品牌（GLM / MiniMax / WorkBuddy / Hy4-Flash…），就自动去把这个品牌的
**官方 logo** 下载下来、规整好、落到工程目录、并登记来源，供排版时用进画面。

取件顺序（谁在前谁更权威）：
    ① --url   官方直链（用户给的 CDN / GitHub raw 链接，最准）
    ② --site  品牌官网首页（自动扒 og:logo / apple-touch-icon / favicon）
    ③ --commons  Wikimedia Commons 搜索（次选，需人工确认是不是官方件）
    ④ --repo  GitHub 仓库的组织头像（次选，需人工确认）

规整链复用 `get_logo.py`：SVG 转 PNG → 去白底 → 裁留白 → 缩放 → 登记台账。

「准确优先于好看」：本脚本只管**取件与规整**，不管**取哪个**——
是不是这个品牌、是不是官方源、是不是同一版本，三关由执行 Agent 判（`references/brand-logo.md` §3）。
官方源取不到就退成纯文字品牌名，**不许拿近似 logo 硬凑**。

依赖（渲染期同款解释器，见 wanfeng-path.md §3.2）：
    ~/.workbuddy/binaries/python/envs/default/bin/python3   # PIL 12.x + numpy
SVG 转 PNG 优先 cairosvg，回退 macOS 自带 sips / qlmanage。

用法
----
    # ① 从官网扒（最常用）
    python3 scripts/brand_logo.py \
      --brand GLM --site https://glm.cn \
      --out "<选题>/mograph-task/assets/logos/GLM.png" \
      --manifest "<选题>/mograph-task/assets/asset-manifest.json"

    # ② 官方直链
    python3 scripts/brand_logo.py --brand GLM --url "https://cdn.example.com/glm.svg" --out ...

    # ③ 只看候选来源不下载（先看官方源长什么样）
    python3 scripts/brand_logo.py --brand GLM --site https://glm.cn --dry-run

退出码
------
    0 成功｜2 参数/用法错｜3 下载失败｜4 格式无法处理或源图太小｜5 落盘失败｜6 没找到官方源
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import get_logo  # noqa: E402  复用规整链（SVG→PNG / 去白底 / 裁留白 / 台账登记）

UA = "mograph-pro-brand-logo/1.0 (+https://github.com/CoderWanFeng/wanfeng-skills)"
MAX_BYTES = 20 * 1024 * 1024
TIMEOUT = 30
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
GITHUB_API = "https://api.github.com"


def fatal(code, msg):
    """出错退出：写 stderr 后带退出码退出。"""
    sys.stderr.write("[brand_logo] %s\n" % msg)
    raise SystemExit(code)


# ---------------------------------------------------------------- 下载
def fetch(url, timeout=TIMEOUT, accept="*/*"):
    """下载二进制内容。只允许 http/https，带 UA 与体积上限。"""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        fatal(2, "只支持 http/https 链接，收到：%s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            data = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        fatal(3, "HTTP %s：%s" % (e.code, url))
    except Exception as e:
        fatal(3, "下载失败：%s（%s）" % (url, e))
    if len(data) > MAX_BYTES:
        fatal(3, "文件超过 %d MB，放弃：%s" % (MAX_BYTES // 1024 // 1024, url))
    return data, ctype


def fetch_text(url):
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        fatal(2, "只支持 http/https 链接，收到：%s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        fatal(3, "HTTP %s：%s" % (e.code, url))
    except Exception as e:
        fatal(3, "打开官网失败：%s（%s）" % (url, e))
    return raw.decode("utf-8", errors="replace")


# ---------------------------------------------------------------- 官网解析
class _HeadParser(HTMLParser):
    """只抓 head 里的 link / meta，不做整页解析。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []   # (rel, href, type)
        self.metas = []   # (key, content)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        d = {}
        for k, v in attrs:
            d[k.lower()] = (v or "")
        if tag == "link" and d.get("href"):
            self.links.append((d.get("rel", "").lower(), d["href"], d.get("type", "").lower()))
        elif tag == "meta" and d.get("content"):
            key = (d.get("property") or d.get("name") or "").lower()
            self.metas.append((key, d["content"]))


# 排名越小越权威
META_RANK = {
    "og:logo": 0,
    "og:logo:secure_url": 0,
    "og:image": 4,
    "og:image:secure_url": 4,
    "twitter:image": 5,
    "twitter:image:src": 5,
}
LINK_RANK = {
    "apple-touch-icon": 1,
    "apple-touch-icon-precomposed": 1,
    "mask-icon": 3,
    "icon": 2,
    "shortcut icon": 2,
    "fluid-icon": 2,
}


def site_candidates(html_text, base_url):
    """从官网首页扒出 logo 候选，按权威度排序。"""
    p = _HeadParser()
    try:
        p.feed(html_text)
    except Exception:
        pass

    found = []

    def absu(h):
        return urllib.parse.urljoin(base_url, h.strip())

    for key, content in p.metas:
        if key in META_RANK and content.strip():
            found.append({"kind": key, "url": absu(content), "rank": META_RANK[key]})
    for rel, href, typ in p.links:
        if "icon" not in rel:
            continue
        rank = LINK_RANK.get(rel, 3)
        if "svg" in typ:
            rank = min(rank, 2)
        found.append({"kind": "link[%s]" % rel, "url": absu(href), "rank": rank})

    # 去重（同 URL 只留排名最靠前的那个）
    best = {}
    for c in found:
        if c["url"] not in best or c["rank"] < best[c["url"]]["rank"]:
            best[c["url"]] = c
    out = sorted(best.values(), key=lambda c: (c["rank"], c["url"]))
    for c in out:
        c["host"] = urllib.parse.urlparse(c["url"]).netloc
    return out


# ---------------------------------------------------------------- 其它来源
def commons_candidates(brand):
    """Wikimedia Commons 文件搜索（次选来源，需人工确认是不是官方件）。"""
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "list": "search",
        "srsearch": "%s logo" % brand, "srnamespace": 6, "srlimit": 12,
    })
    url = "%s?%s" % (COMMONS_API, q)
    raw = fetch_text(url)
    try:
        data = json.loads(raw)
    except Exception:
        fatal(3, "Commons 返回的不是 JSON")
    hits = data.get("query", {}).get("search", [])
    key = re.sub(r"[\s\-_.]+", "", brand).lower()
    out = []
    for h in hits:
        title = h.get("title", "")
        if not title:
            continue
        iq = urllib.parse.urlencode({
            "action": "query", "format": "json", "titles": title,
            "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 1024,
        })
        try:
            info = json.loads(fetch_text("%s?%s" % (COMMONS_API, iq)))
        except SystemExit:
            continue
        pages = info.get("query", {}).get("pages", {})
        for _, page in pages.items():
            ii = (page.get("imageinfo") or [{}])[0]
            link = ii.get("thumburl") or ii.get("url")
            if not link:
                continue
            rank = 0 if key in re.sub(r"[\s\-_.]+", "", title).lower() else 2
            out.append({"kind": "commons", "url": link, "rank": rank, "title": title})
    out.sort(key=lambda c: (c["rank"], c["title"]))
    return out


def github_candidates(repo):
    """GitHub 仓库的组织/作者头像（次选来源，需人工确认是不是官方件）。"""
    api = "%s/repos/%s" % (GITHUB_API, repo.strip("/"))
    raw = fetch_text(api)
    try:
        data = json.loads(raw)
    except Exception:
        fatal(3, "GitHub 返回的不是 JSON")
    owner = (data.get("owner") or {}).get("login", "")
    avatar = (data.get("owner") or {}).get("avatar_url", "")
    out = []
    if avatar:
        out.append({"kind": "github-owner-avatar", "url": avatar, "rank": 1, "title": owner})
    return out


# ---------------------------------------------------------------- 取件
def load_image(data):
    """字节流 → PIL Image（SVG 先转 PNG）。返回 (img, 是否转过)。"""
    converted = False
    if get_logo.looks_like_svg(data):
        try:
            data = get_logo.svg_to_png_bytes(data)
        except SystemExit:
            fatal(4, "SVG 无法转 PNG：装 cairosvg（pip install cairosvg），或改用 PNG 直链")
        converted = True
    from PIL import Image
    import io
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        return None, converted, str(e)
    return img, converted, ""


def pick_candidate(cands, min_side, allow_small):
    """按排名依次尝试，返回 (候选, PIL 图, 警告列表)。"""
    too_small = []
    for c in cands:
        try:
            data, _ctype = fetch(c["url"])
        except SystemExit:
            continue
        img, _converted, err = load_image(data)
        if img is None:
            too_small.append({"candidate": c, "why": "不是可识别的图片：%s" % err})
            continue
        w, h = img.size
        short = min(w, h)
        if short < min_side and not allow_small:
            too_small.append({"candidate": c, "why": "最小边只有 %dpx（< %d），放大到画面里会糊" % (short, min_side)})
            continue
        return c, img, too_small
    if too_small:
        detail = "；".join("%s → %s" % (t["candidate"]["url"], t["why"]) for t in too_small[:4])
        fatal(4, "官方源候选都不可用：%s。→ 退成纯文字品牌名，或让用户给更高清的官方直链" % detail)
    fatal(6, "没有找到可用的官方 logo 源")


def register(manifest, out_path, brand, mode, source_url, source_kind, note, segment):
    """登记素材台账（字段与 visual-assets.md §6 一致）。"""
    if not manifest:
        return None
    record = {
        "file": os.path.relpath(out_path, os.path.dirname(os.path.abspath(manifest))),
        "used_at": [],
        "segments": [segment or ("视频内品牌 logo：%s" % brand)],
        "source": "web-logo",
        "url": source_url or "",
        "captured_at": date.today().isoformat(),
        "shows": "%s 官方 logo（%s 版式）" % (brand, mode),
        "proves": "口播里点名 %s 的那句" % brand,
        "license": "official-brand-asset",
        "note": note or "",
        "logo_source_kind": source_kind or "",
    }
    get_logo.append_manifest(manifest, record)
    return record


def main():
    ap = argparse.ArgumentParser(
        description="按品牌名自动取官方 logo（扒官网 / 直链 / Commons / GitHub，规整 + 登记来源）")
    ap.add_argument("--brand", required=True, help="品牌/产品名，写进台账与摘要")
    ap.add_argument("--url", help="官方直链（http/https）")
    ap.add_argument("--site", help="品牌官网首页，自动扒 og:logo / favicon")
    ap.add_argument("--commons", action="store_true", help="从 Wikimedia Commons 搜（次选）")
    ap.add_argument("--repo", help="GitHub 仓库 owner/repo，取组织头像（次选）")
    ap.add_argument("--out", help="输出 PNG 路径（--dry-run 时可省）")
    ap.add_argument("--manifest", help="素材台账路径，登记来源与抓取日期")
    ap.add_argument("--note", default="", help="台账备注")
    ap.add_argument("--segment", default="", help="台账里的用途说明（挂在哪句）")
    ap.add_argument("--mode", default="auto", choices=["auto", "icon", "lockup"],
                    help="auto=按宽高比自动判 icon / lockup")
    ap.add_argument("--max-side", type=int, default=1600, help="最长边上限，默认 1600")
    ap.add_argument("--min-side", type=int, default=96,
                    help="源图最小边下限，低于此值判「太小会糊」（默认 96）")
    ap.add_argument("--allow-small", action="store_true", help="允许使用小于下限的小图")
    ap.add_argument("--keep-bg", action="store_true", help="保留白底不去透明")
    ap.add_argument("--dry-run", action="store_true", help="只列候选来源，不下载不落盘")
    args = ap.parse_args()

    if not (args.url or args.site or args.commons or args.repo):
        fatal(2, "至少给一个来源：--url / --site / --commons / --repo")
    if not args.dry_run and not args.out:
        fatal(2, "缺少 --out（要落盘 PNG）")
    if args.site and not re.match(r"^https?://", args.site.strip()):
        fatal(2, "--site 要带 http:// 或 https://")

    # ---- 候选来源
    kind, cands = "", []
    if args.url:
        kind = "direct-url"
        cands = [{"kind": "direct-url", "url": args.url, "rank": 0}]
        if args.site:
            host = urllib.parse.urlparse(args.site).netloc
            for c in cands:
                c["host"] = urllib.parse.urlparse(c["url"]).netloc
                c["same_host_as_site"] = (c["host"] == host)
    elif args.site:
        kind = "official-site"
        html = fetch_text(args.site)
        cands = site_candidates(html, args.site)
        if not cands:
            fatal(6, "官网 %s 上没扒到 logo 候选（og:logo / favicon 都没有）→ 退成纯文字品牌名" % args.site)
    elif args.commons:
        kind = "commons"
        cands = commons_candidates(args.brand)
        if not cands:
            fatal(6, "Commons 上没搜到「%s logo」→ 退成纯文字品牌名" % args.brand)
    else:
        kind = "github-org"
        cands = github_candidates(args.repo)
        if not cands:
            fatal(6, "GitHub 仓库 %s 没取到头像 → 退成纯文字品牌名" % args.repo)

    # ---- dry-run：只列候选
    if args.dry_run:
        print(json.dumps({
            "brand": args.brand,
            "source_kind": kind,
            "candidates": [{"rank": c["rank"], "kind": c.get("kind", ""),
                            "url": c["url"], "title": c.get("title", "")}
                           for c in cands[:12]],
            "note": "只列候选，没有下载任何文件。",
        }, ensure_ascii=False, indent=2))
        return

    # ---- 取件 + 规整
    chosen, img, skipped = pick_candidate(cands, args.min_side, args.allow_small)
    raw_size = img.size
    if not args.keep_bg:
        img = get_logo.to_rgba(img)
    img = get_logo.trim(img)
    trimmed_size = img.size
    img = get_logo.fit_max(img, args.max_side)
    mode = get_logo.classify(img, args.mode)

    # ---- 落盘
    out = os.path.abspath(args.out)
    d = os.path.dirname(out)
    try:
        if d:
            os.makedirs(d, exist_ok=True)
        img.save(out, "PNG", optimize=True)
    except Exception as e:
        fatal(5, "写文件失败：%s（%s）" % (out, e))

    # ---- 台账
    manifest_path = None
    if args.manifest:
        try:
            register(args.manifest, out, args.brand, mode, chosen["url"], kind,
                     args.note, args.segment)
            manifest_path = os.path.abspath(args.manifest)
        except SystemExit:
            raise
        except Exception as e:
            manifest_path = "登记失败：%s" % e

    warnings = []
    if chosen.get("kind") in ("og:image", "link[icon]") or chosen.get("kind", "").startswith("og:image"):
        warnings.append("取到的是社交预览图/普通图标，可能带文字，logo 形状不一定干净")
    if chosen.get("kind") == "commons":
        warnings.append("Commons 不是官方源，务必人工确认是官方件（W26 三关）")
    if chosen.get("kind") == "github-owner-avatar":
        warnings.append("GitHub 头像不是官方 logo，务必人工确认是官方件（W26 三关）")
    if kind == "direct-url" and not chosen.get("same_host_as_site", False):
        warnings.append("直链域名与官网不一致，官方性需人工确认（W26 三关）")
    if raw_size[0] < 256:
        warnings.append("源图只有 %dpx 宽，放到画面里会糊 —— 换更高清的源" % raw_size[0])
    if trimmed_size[0] < 120:
        warnings.append("裁完只剩 %dpx 宽，做不了上屏 icon，建议换横排整条或更高清的源" % trimmed_size[0])

    summary = {
        "out": out,
        "brand": args.brand,
        "source_kind": kind,
        "source": chosen["url"],
        "source_title": chosen.get("title", ""),
        "raw_size": list(raw_size),
        "trimmed_size": list(trimmed_size),
        "final_size": list(img.size),
        "mode": mode,
        "has_alpha": img.getchannel("A").getextrema()[0] < 250,
        "skipped": skipped,
        "manifest": manifest_path or "",
    }
    if warnings:
        summary["warnings"] = warnings
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
