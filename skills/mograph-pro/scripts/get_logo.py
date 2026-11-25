#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""联网获取产品 Logo · mograph-pro Step H 辅助脚本

用途
----
封面换皮要放产品 Logo。本地素材里没有合适的那一个时，用这个脚本从网上取：
下载 → SVG 转 PNG → 白底转透明 → 裁掉多余留白 → 落到工程目录 → 登记来源。

「准确优先于好看」：这个脚本只管**取件与规整**，不管**取哪个**。
选哪个 logo 是判断题，判据见 references/wanfeng-cover.md §1.2。

依赖（渲染期同款解释器，见 wanfeng-path.md §3.2）：
    ~/.workbuddy/binaries/python/envs/default/bin/python3   # PIL 12.x + numpy
系统 /usr/bin/python3 也有 Pillow 11.3 + numpy 2.0，能跑但版本不同；
本脚本不需要 cv2（封面换皮脚本才需要）。

用法
----
    # ① 只下载 + 规整，输出 PNG，屏幕上打印摘要
    python3 scripts/get_logo.py \
      --url "https://cdn.example.com/glm.svg" \
      --out "发布包/logo/glm.png" \
      --brand "GLM"

    # ② 顺带登记来源到素材台账（W15：外部素材必须可追溯）
    python3 scripts/get_logo.py \
      --url "https://cdn.example.com/glm.png" \
      --out "发布包/logo/glm.png" \
      --manifest "mograph-task/assets/asset-manifest.json" \
      --brand "GLM" --note "Step H 封面 logo"

    # ③ 从本地已有的 SVG 起（不联网）
    python3 scripts/get_logo.py --src "/path/to/logo.svg" --out "发布包/logo/logo.png"

退出码
------
    0 成功｜2 参数/用法错｜3 下载失败｜4 格式无法处理｜5 落盘失败
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

UA = "mograph-pro-get-logo/1.0 (+https://github.com/CoderWanFeng/wanfeng-skills)"
MAX_BYTES = 20 * 1024 * 1024
ALLOWED_SCHEMES = ("http", "https")


# ---------------------------------------------------------------- 基础工具
def die(code, msg):
    sys.stderr.write("[get_logo] %s\n" % msg)
    raise SystemExit(code)


def have_pil():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def fetch(url, timeout=30):
    """下载二进制内容。只允许 http/https，带 UA 与体积上限。"""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ALLOWED_SCHEMES:
        die(2, "只支持 http/https 链接，收到：%s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            data = resp.read(MAX_BYTES + 1)
    except Exception as e:
        die(3, "下载失败：%s（%s）" % (url, e))
    if len(data) > MAX_BYTES:
        die(3, "文件超过 %d MB，放弃：%s" % (MAX_BYTES // 1024 // 1024, url))
    return data, ctype


def looks_like_svg(data):
    head = data[:512].lstrip()
    return head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in data[:2048])


def looks_like_png(data):
    return data[:8] == b"\x89PNG\r\n\x1a\n"


def looks_like_jpeg(data):
    return data[:2] == b"\xff\xd8"


# ---------------------------------------------------------------- SVG → PNG
def svg_to_png_bytes(data):
    """SVG → PNG 字节流。三条路，按可靠度排：

    ① cairosvg（装了最准，纯矢量栅格化）；
    ② **sips**（macOS 自带，实测比例正确、不裁切、自带透明通道）；
    ③ qlmanage（macOS 自带，会按高度缩放并**裁掉右侧**，只作最后保底）。

    实测教训：qlmanage 渲染 200×120 的 SVG 会得到 2048×2048 且右侧被裁掉，
    「GLM」的 M 被切一半 —— 所以它排在最后，且用它时要补一层方框裁切。
    """
    tmpdir = tempfile.mkdtemp(prefix="mograph-logo-")
    try:
        svg_path = os.path.join(tmpdir, "logo.svg")
        with open(svg_path, "wb") as f:
            f.write(data)
        outdir = os.path.join(tmpdir, "out")
        os.makedirs(outdir, exist_ok=True)

        # ① cairosvg
        try:
            import cairosvg  # noqa: F401
            png = cairosvg.svg2png(bytestring=data, output_width=2048)
            if png:
                return png
        except Exception:
            pass

        # ② sips（macOS 自带，正确率最高）
        if shutil.which("sips"):
            png_path = os.path.join(outdir, "logo.png")
            try:
                subprocess.run(["sips", "-s", "format", "png", "-Z", "2048",
                                svg_path, "--out", png_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=120, check=False)
                if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
                    with open(png_path, "rb") as f:
                        return f.read()
            except Exception:
                pass

        # ③ qlmanage（保底）
        if shutil.which("qlmanage"):
            try:
                subprocess.run(["qlmanage", "-t", "-s", "2048", "-o", outdir, svg_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=120, check=False)
                for name in sorted(os.listdir(outdir)):
                    if name.lower().endswith(".png"):
                        with open(os.path.join(outdir, name), "rb") as f:
                            return f.read()
            except Exception:
                pass

        die(4, "SVG 无法转 PNG：装 cairosvg（pip install cairosvg）"
               "，或改下 SVG 链接、换 PNG 直链。")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------- 图像规整
def to_rgba(img):
    """统一成 RGBA，并把「与画面边缘连通的近白」转成透明。

    判据用**角点 alpha**，不是「整图有没有透明像素」——
    sips 渲染的 SVG 边角会带一点点半透明（alpha≈182），而白底内部仍是不透明白；
    只看「有没有透明像素」会误判成「本来就是透明底」而跳过去白底，
    结果 logo 贴到封面上露出一块白方块（实测踩过）。

    白底识别用边缘连通：只吃**从四边能走到的近白像素**，logo 内部的白色不受影响。
    """
    from PIL import Image, ImageDraw
    import numpy as np

    im = img.convert("RGBA")
    w, h = im.size

    # 四角都已经是真透明 → 本来就是透明底，别乱动
    corners = [im.getpixel(p)[3] for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    if max(corners) <= 8:
        return im

    rgb = im.convert("RGB")
    px = rgb.load()

    def is_white(c):
        return c[0] >= 238 and c[1] >= 238 and c[2] >= 238

    seed = None
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if is_white(px[xy[0], xy[1]]):
            seed = xy
            break
    if seed is None:
        return im  # 角落不是白底（彩色底/满图），保持原样

    marker = (255, 0, 255)
    ImageDraw.floodfill(rgb, seed, marker, thresh=32)
    arr = np.asarray(rgb).copy()
    is_marker = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 255)

    orig_a = np.asarray(im.getchannel("A")).astype("uint8")
    alpha = np.where(is_marker, 0, orig_a).astype("uint8")
    out = np.dstack([arr[:, :, :3], alpha])
    return Image.fromarray(out, "RGBA")


def trim(img):
    """裁掉四周全透明的留白（保留 1px 保险）。"""
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def fit_max(img, max_side):
    if max(img.size) <= max_side:
        return img
    from PIL import Image
    w, h = img.size
    s = max_side / float(max(w, h))
    return img.resize((max(1, int(round(w * s))), max(1, int(round(h * s)))), Image.LANCZOS)


def classify(img, mode):
    """auto：按宽高比判 icon（近方形）还是 lockup（横排整条）。"""
    w, h = img.size
    ratio = w / float(h) if h else 1.0
    if mode != "auto":
        return mode
    return "lockup" if ratio >= 1.6 else "icon"


# ---------------------------------------------------------------- 台账登记
def append_manifest(path, record):
    data = {"assets": []}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            die(5, "台账读不出来，未登记（%s）：%s" % (path, e))
    if not isinstance(data, dict):
        data = {"assets": []}
    data.setdefault("assets", [])
    data["assets"].append(record)
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(
        description="联网获取产品 Logo（下载 / SVG转PNG / 去白底 / 裁白边 / 登记来源）")
    ap.add_argument("--url", help="logo 直链（http/https）")
    ap.add_argument("--src", help="本地已有的 logo 文件（不走网络）")
    ap.add_argument("--out", required=True, help="输出 PNG 路径")
    ap.add_argument("--brand", default="", help="品牌/产品名，写进台账与摘要")
    ap.add_argument("--mode", default="auto", choices=["auto", "icon", "lockup"],
                    help="auto=按宽高比自动判 icon / lockup")
    ap.add_argument("--max-side", type=int, default=1600, help="最长边上限，默认 1600")
    ap.add_argument("--keep-bg", action="store_true", help="保留白底不去透明")
    ap.add_argument("--manifest", help="素材台账路径，登记来源与抓取日期")
    ap.add_argument("--note", default="", help="台账备注")
    args = ap.parse_args()

    if not have_pil():
        die(2, "缺 Pillow。请用托管解释器："
               "~/.workbuddy/binaries/python/envs/default/bin/python3")

    if bool(args.url) == bool(args.src):
        die(2, "--url 与 --src 只能给一个")

    # ---- 取件
    if args.url:
        data, ctype = fetch(args.url)
        origin = args.url
    else:
        if not os.path.exists(args.src):
            die(2, "本地文件不存在：%s" % args.src)
        with open(args.src, "rb") as f:
            data = f.read(MAX_BYTES + 1)
        ctype = ""
        origin = os.path.abspath(args.src)

    # ---- 规整
    from PIL import Image
    import io

    converted = False
    if looks_like_svg(data):
        data = svg_to_png_bytes(data)
        converted = True
        ctype = "image/png"

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        die(4, "不是可识别的图片（png/jpg/svg）：%s" % e)

    raw_size = img.size
    if not args.keep_bg:
        img = to_rgba(img)
    img = trim(img)
    trimmed_size = img.size
    img = fit_max(img, args.max_side)

    # ---- 落盘
    out = os.path.abspath(args.out)
    d = os.path.dirname(out)
    if d:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            die(5, "建目录失败：%s（%s）" % (d, e))
    try:
        img.save(out, "PNG", optimize=True)
    except Exception as e:
        die(5, "写文件失败：%s（%s）" % (out, e))

    mode = classify(img, args.mode)
    summary = {
        "out": out,
        "brand": args.brand,
        "source": origin,
        "format": "svg→png" if converted else ("png" if looks_like_png(data) else "jpeg/other"),
        "raw_size": list(raw_size),
        "trimmed_size": list(trimmed_size),
        "final_size": list(img.size),
        "mode": mode,
        "has_alpha": img.getchannel("A").getextrema()[0] < 250,
    }
    if raw_size[0] < 256:
        summary["warning"] = "源图只有 %dpx 宽，放大到封面尺寸会糊 —— 换更高清的源" % raw_size[0]

    # ---- 台账
    if args.manifest:
        record = {
            "file": os.path.relpath(out, os.path.dirname(os.path.abspath(args.manifest))),
            "used_at": [],
            "segments": ["Step H 封面 logo：%s" % (args.brand or "未命名品牌")],
            "source": "web-logo" if args.url else "local-logo",
            "url": args.url or "",
            "captured_at": __import__("datetime").date.today().isoformat(),
            "shows": "%s 官方 logo（%s 版式）" % (args.brand or "品牌", mode),
            "proves": "封面上的产品标识",
            "license": "official-brand-asset",
            "note": args.note,
        }
        try:
            append_manifest(args.manifest, record)
            summary["manifest"] = os.path.abspath(args.manifest)
        except SystemExit:
            raise
        except Exception as e:
            summary["manifest_error"] = str(e)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
