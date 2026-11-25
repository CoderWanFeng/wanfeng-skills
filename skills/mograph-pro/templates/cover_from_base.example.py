# -*- coding: utf-8 -*-
"""封面换皮脚本 · mograph-pro Step H（模板，已用 1-免费AI/24-glm3亿 真实交付验证）

打法：在混元封面底图（1728x2304）上**只换字、只换 logo，人像一像素不动**。
用户原话：「我以后都会穿那个衣服录视频，直接在那张底图上把字改了、把 LOGO 改了就行，人都不用动。」

依赖（托管解释器，见 wanfeng-path.md §3.2/§3.3）：
    ~/.workbuddy/binaries/python/envs/default/bin/python3   # PIL 12.x + numpy + cv2

固定资产（已沉淀进 skill，勿删）：
    底图        cover-assets/封面-底图-混元WB.jpg     # 墙面人像，1:1 像素底
    头发参考帧  cover-assets/hy4-frame7.jpg          # 同段视频第 7 秒帧，补头顶用
    （分发渠道不允许随包上传图片时，本地可能没有这两个文件 —— 脚本会自动下载，见 _download_asset：
      AtomGit 国内源优先，GitHub 原始文件兜底。用户打不开 GitHub 也不影响。）

用法：把本文件复制到 <选题>/AI剪辑输出/src/cover.py，改下面 CONFIG，然后跑。
     只改标着【每期必改】的项；标【勿改】的是配准/版式实测值，动了必翻车（见 wanfeng-cover.md 踩坑表）。
"""
import os
import glob
import json
import urllib.error
import urllib.parse
import urllib.request
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---- 封面固定资产的线上副本（分发渠道不允许随包上传图片时，从这里下载）----
# 两个仓库同源（AtomGit 由 GitHub 同步过来），下载路径一致。
# 国内优先 AtomGit（GitHub 常常打不开），GitHub 兜底；两边都按「新布局 → 旧布局」各试一遍。
ATOMGIT_API = "https://atomgit.com/api/v5/repos/CoderWanFeng1/wanfeng-skills/contents"
ATOMGIT_RAW = "https://atomgit.com/CoderWanFeng1/wanfeng-skills/raw/main"
GH_RAW = "https://raw.githubusercontent.com/CoderWanFeng/wanfeng-skills/main"
GH_PAGE = ("https://github.com/CoderWanFeng/wanfeng-skills/tree/main/"
           "skills/mograph/cover-assets")
AG_PAGE = "https://atomgit.com/CoderWanFeng1/wanfeng-skills"
# ⚠ 平台只允许「根目录/一级目录/文件」，所以封面资产平铺在 cover-assets/ 下（别再套 references/assets/cover）。
# 后两个是旧仓库布局，镜像/远程可能还没同步到新位置，留着兼容；头发帧旧版是 .png 也认。
COVER_DIRS = ("skills/mograph/cover-assets",
              "skills/mograph/references/assets/cover",
              "skills/mograph/reference/assets/cover")
NAME_ALTS = {"hy4-frame7.jpg": "hy4-frame7.png"}


def _http_get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "wanfeng-mograph-cover"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _pct(url):
    """把 URL 里的中文/空格转义（AtomGit 返回的地址里带原始中文文件名）。"""
    return urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%")


def _atomgit_download_url(name):
    """走 AtomGit 的 contents 接口查真实下载地址。

    ⚠ 别指望 https://atomgit.com/<用户>/<仓库>/raw/main/<路径>：那个地址返回的是占位 SVG/HTML，
    真正能下的是接口给的 blobs 地址（带 blob sha）。查不到（镜像还没同步到）就返回 None。
    """
    for _ in range(2):                       # 接口偶尔抽风，重试一次
        for rel in COVER_DIRS:
            api = "%s/%s?ref=main" % (ATOMGIT_API, urllib.parse.quote(rel))
            try:
                items = json.loads(_http_get(api, 15).decode("utf-8"))
            except Exception:
                continue
            if not isinstance(items, list):
                continue
            for nm in (name, NAME_ALTS.get(name)):
                for it in items:
                    if it.get("name") == nm and it.get("download_url"):
                        return _pct(it["download_url"])
    return None


def _img_ext(data):
    """按文件头判断真实格式。镜像里头发帧可能还是旧的 .png，不能只看扩展名。"""
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    return None


def _cand_urls(name):
    """按优先级列出候选下载地址：(来源, 域名, url)。域名用来「一个源连不上就整站跳过」。"""
    out = []
    ag = _atomgit_download_url(name)
    if ag:
        out.append(("AtomGit 国内源", "raw.atomgit.com", ag))
    # 接口挂了/限流时试一把直链（返回占位图会被文件头校验挡掉，不会写进缓存）
    out.append(("AtomGit 直链", "atomgit.com",
                "%s/%s/%s" % (ATOMGIT_RAW, COVER_DIRS[0], urllib.parse.quote(name))))
    for base, label, host in ((ATOMGIT_RAW, "AtomGit 直链", "atomgit.com"),
                              (GH_RAW, "GitHub 原始文件", "raw.githubusercontent.com")):
        for rel in COVER_DIRS:
            for nm in (name, NAME_ALTS.get(name)):
                if not nm:
                    continue
                url = "%s/%s/%s" % (base, rel, urllib.parse.quote(nm))
                if url not in [u for _, _, u in out]:
                    out.append((label, host, url))
    return out


def _download_asset(name):
    """本地找不到封面固定资产时下载到缓存目录（缓存命中就不重复下）。

    缓存目录：$MOGRAPH_ASSET_CACHE（兼容旧的 $MOGRAPH_PRO_ASSET_CACHE）或 ~/.cache/wanfeng-mograph/cover。
    顺序：AtomGit（国内直连，快）→ GitHub（能连通时兜底）。
    """
    cache = (os.environ.get("MOGRAPH_ASSET_CACHE")
             or os.environ.get("MOGRAPH_PRO_ASSET_CACHE")
             or os.path.expanduser("~/.cache/wanfeng-mograph/cover"))
    stem = os.path.splitext(name)[0]
    for ext in (".jpg", ".png"):                 # 缓存里可能是换过格式的同一张图
        hit = os.path.join(cache, stem + ext)
        if os.path.exists(hit):
            return hit
    os.makedirs(cache, exist_ok=True)

    errs, dead = [], set()
    for label, host, url in _cand_urls(name):
        if host in dead:                         # 这个源连不上，后面的路径不用再试
            continue
        print("封面固定资产本地缺失，正在从 %s 下载：%s" % (label, url))
        try:
            data = _http_get(url, 15)
        except urllib.error.HTTPError as e:      # 404 之类：换个路径继续
            errs.append("%s: HTTP %s" % (label, e.code))
            continue
        except Exception as e:                   # 连不上/DNS 挂了：整站跳过
            errs.append("%s: %s" % (label, e))
            dead.add(host)
            continue
        ext = _img_ext(data)                     # 占位图/错误页一律判失败，别把坏图写进缓存
        if not ext:
            errs.append("%s: 返回 %d 字节的非图片内容" % (label, len(data)))
            continue
        dest = os.path.join(cache, stem + ext)
        tmp = dest + ".part"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dest)
        print("已下载到：%s（%d KB）" % (dest, len(data) // 1024))
        return dest

    raise RuntimeError("；".join(errs) or "没有可用的下载源")


# ============================================================ CONFIG ============================================================
def _skill_asset(name):
    """找封面固定资产：环境变量 → 本机仓库 → 各家 agent 的 skill 安装目录 → 当前目录 → 联网下载。

    这个脚本会被复制到用户的选题工程里跑，不能写死绝对路径。
    新位置是 `cover-assets/`（平铺）；旧包的 `references/assets/cover`、`reference/assets/cover` 也认。
    找不到时先设 MOGRAPH_ASSET_DIR 指向 skill 包内的 cover 目录；仍找不到就自动下载。
    """
    roots = []
    env = os.environ.get("MOGRAPH_ASSET_DIR") or os.environ.get("MOGRAPH_PRO_ASSET_DIR")
    if env:
        roots.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    roots += [
        os.path.expanduser("~/晚枫工作室/code/wanfeng-skills/skills/mograph-pro"),
        os.path.expanduser("~/晚枫工作室/code/wanfeng-skills/skills/mograph"),
        here, os.path.join(here, ".."), os.getcwd(), os.path.join(os.getcwd(), ".."),
    ]
    for pat in ("~/.workbuddy/skills/*", "~/.agents/skills/*",
                "~/.qoder/skills/*", "~/.claude/skills/*"):
        roots += sorted(glob.glob(os.path.expanduser(pat)))

    subs = ("cover-assets", "assets", "references/assets/cover", "reference/assets/cover")
    names = (name, NAME_ALTS.get(name))
    for r in roots:
        for sub in subs:
            for nm in names:
                p = os.path.join(r, sub, nm) if nm else None
                if p and os.path.exists(p):
                    return p
    # 本地全都没有 → 联网下载（AtomGit 优先，GitHub 兜底）
    try:
        return _download_asset(name)
    except Exception as e:
        raise FileNotFoundError(
            "找不到封面固定资产 %s，且自动下载失败（%s）。\n"
            "  1) 设环境变量 MOGRAPH_ASSET_DIR 指向本机已有的 cover-assets 目录；\n"
            "  2) 或手动下载该文件，放进 skill 的 cover-assets/ 再跑：\n"
            "     国内 https://atomgit.com/CoderWanFeng1/wanfeng-skills/tree/main/skills/mograph/cover-assets\n"
            "     海外 %s\n"
            "  （需要 封面-底图-混元WB.jpg 与 hy4-frame7.jpg 两个文件）" % (name, e, GH_PAGE))

BASE = _skill_asset("封面-底图-混元WB.jpg")        # 【勿改】底图
HEAD_SRC = _skill_asset("hy4-frame7.jpg")          # 【勿改】头发参考帧
OUT = "发布包/封面-XXX.jpg"          # 【每期必改】输出路径

# ---- 文案（每期必改）----
# 每行 = (segs, fill, stroke)。segs 是 (文本, 字体kind, 字号) 列表：
#   kind "cn" = TencentSans W7（中文）；"latin" = Arial Bold 直立（拉丁/数字 —— TencentSans 的拉丁是斜的，必须拆段！）
LINE1_SEGS = [("免费用", "cn", 207), ("GLM", "latin", 202)]   # 拉丁字号 = int(中文号*0.98)
LINE1_FILL = (16, 43, 99)            # 蓝，采样自底图原字
LINE2_SEGS = [("每天领", "cn", 262), ("3", "latin", 248), ("亿", "cn", 262)]  # 3 = int(262*0.95)
LINE2_FILL = (160, 19, 21)           # 红，采样自底图原字

# ---- 行位置（已按「行距 82px / 字底距头发顶净空 33px / 投影不蹭头发」三验证调好，勿改）----
LINE1 = dict(cx=862, cy=172, stroke=10, gap=36)
LINE2 = dict(cx=866, cy=490, stroke=11, gap=34)

# ---- logo（每期必改）----
# ERASE_LOGO=False：保留底图原 WorkBuddy 标识，什么都不画（推荐 WorkBuddy 选题用）
# ERASE_LOGO=True ：抹掉原标识，用下面 ICON_DRAWER + WORD_TEXT 画新的
#
# 【新增】LOGO_PATH：外部 logo 文件（联网下载的 / 用户给的 PNG）。
#   留空 = 走 ICON_DRAWER 手绘路径（58 号已验证，max diff = 0）。
#   非空 = 顶替手绘，按宽高比自动分两种落法：
#     · 方形图标（宽/高 < 1.6）→ 顶替 ICON 贴在 (ICON_X, ICON_Y)，字标仍用 WORD_TEXT 画
#     · 横向整条（宽/高 ≥ 1.6）→ 整条贴进 LOGO_BAND，替代 ICON + WORD_TEXT
#   文件用 scripts/get_logo.py 取（自动去白底、裁留白、登记来源）。
ERASE_LOGO = True
ICON_X, ICON_Y, ICON_S = 864, 1150, 300      # 图标位置/尺寸【勿改，底图配准值】
WORD_TEXT, WORD_X, WORD_CY, WORD_SIZE = "ZCODE", 1186, 1301, 152
WORD_TRACK, WORD_FILL = -6, (0, 0, 0)        # 字距收紧、黑色字标
ICON_DRAWER = "z_icon"                       # 本文件里定义的图标绘制函数名；换成你品牌的画法
LOGO_PATH = ""                              # 外部 logo 文件路径；留空 = 用上面的手绘图标
LOGO_BAND = (864, 1150, 1694, 1450)          # 横排整条的落位框【勿改，与底图配准值同源】

# ---- 字体（勿改）----
F_BOLD  = os.path.expanduser(os.environ.get("MOGRAPH_FONT_BOLD", "~/Library/Fonts/TencentSans-W7.ttf"))
F_LATIN = os.path.expanduser(os.environ.get("MOGRAPH_FONT_LATIN", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))

# ---- 头发补回配准（勿改：底图人像 = hy4-frame7 整帧 1:1 像素贴入，位移实测 dx=85 dy=390）----
DX, DY = 85, 390
WHITE = (255, 255, 255)

GAPS = [LINE1["gap"]]


# ============================================================ 以下为引擎，一般不用动 ============================================================
def erase_old(bgr, erase_logo=True):
    """抹掉底图原有文字（+ 可选 logo），只在墙面区域做 inpaint"""
    a = bgr.astype(int)
    r, g, b = a[:, :, 2], a[:, :, 1], a[:, :, 0]
    wall = (r > 175) & (g > 165) & (b > 145)
    mask = np.zeros(a.shape[:2], np.uint8)

    band = np.zeros_like(mask)
    band[90:700, 120:1660] = 255
    mask[(~wall) & (band > 0)] = 255

    if erase_logo:
        mask[ICON_Y - 12:ICON_Y + ICON_S + 12, ICON_X - 12:ICON_X + ICON_S + 12] = 255
        word = np.zeros_like(mask)
        word[1170:1430, 1200:1728] = 255
        dark = (r < 110) & (g < 110) & (b < 110)
        mask[(word > 0) & dark] = 255

    mask = cv2.dilate(mask, np.ones((25, 25), np.uint8), iterations=1)
    out = cv2.inpaint(bgr, mask, 18, cv2.INPAINT_TELEA)
    out = cv2.inpaint(out, mask, 18, cv2.INPAINT_TELEA)
    return out


def mixed_text(canvas, cx, cy, segs, fill, stroke, sheight=13, sblur=16):
    """中英混排：中文 TencentSans、拉丁/数字 Arial Bold（直立），按基线对齐居中。
    ⚠ 投影层必须压在文字层【下】：alpha_composite(投影, 文字)，反过来投影会把字盖暗。"""
    fonts = {"cn": F_BOLD, "latin": F_LATIN}
    parts = []
    for txt, kind, size in segs:
        f = ImageFont.truetype(fonts[kind], size)
        bb = f.getbbox(txt)
        parts.append((txt, f, size, bb))

    total = sum(p[3][2] - p[3][0] for p in parts) + sum(g for g in GAPS[:len(parts) - 1])
    x = cx - total / 2
    base = cy + max(p[2] for p in parts) * 0.225

    img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(img), ImageDraw.Draw(sh)
    for i, (txt, f, size, bb) in enumerate(parts):
        w = bb[2] - bb[0]
        ds.text((x - bb[0], base + sheight), txt, font=f, anchor="ls",
                fill=(40, 30, 22, 120), stroke_width=stroke, stroke_fill=(40, 30, 22, 120))
        d.text((x - bb[0], base), txt, font=f, anchor="ls", fill=fill,
               stroke_width=stroke, stroke_fill=WHITE)
        x += w + (GAPS[i] if i < len(GAPS) else 0)

    img = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(sblur)), img)  # 投影在下
    canvas.alpha_composite(img)
    return total


def z_icon(size):
    """示例图标：ZCODE 的 Z（深色圆角方块 + 白色 Z，照票券标志手绘）。换成你品牌时照这个结构画。"""
    S = 4
    n = size * S
    ic = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(ic)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.225), fill=(20, 22, 25, 255))
    u = n / 100.0
    x0, y0 = 26 * u, 24 * u
    w, h, bar = 48 * u, 52 * u, 13 * u
    d.polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + bar),
               (x0 + bar * 1.5, y0 + bar), (x0, y0 + bar * 0.5)], fill=(255, 255, 255, 255))
    d.polygon([(x0 + w - bar * 1.6, y0 + bar * 0.9), (x0 + w, y0 + bar * 0.9),
               (x0 + bar * 1.2, y0 + h), (x0 - bar * 0.4, y0 + h)], fill=(255, 255, 255, 255))
    d.polygon([(x0, y0 + h - bar), (x0 + w - bar * 0.7, y0 + h - bar),
               (x0 + w, y0 + h - bar * 0.3), (x0 + w, y0 + h), (x0, y0 + h)],
              fill=(255, 255, 255, 255))
    return ic.resize((size, size), Image.LANCZOS)


def restore_hair(img):
    """把被原文字抹掉的头顶，用同一帧原片补回来（1:1 像素对齐 + 色调增益 + 羽化）。
    ⚠ 顺序不能反：先铺平 inpaint 残留暗雾，再贴头发，否则暗雾会从发缝透出来。"""
    fr = Image.open(HEAD_SRC).convert("RGB")
    a = np.asarray(img).astype(float)
    f = np.asarray(fr).astype(float)
    H, W = a.shape[:2]

    # 已有头发的区域求 per-channel 增益，避免补上去偏色
    c_hair = a[790:1000, 280:860]
    f_hair = f[790 - DY:1000 - DY, 280 - DX:860 - DX]
    gain = c_hair.reshape(-1, 3).mean(axis=0) / f_hair.reshape(-1, 3).mean(axis=0)
    f2 = Image.fromarray(np.clip(f * gain, 0, 255).astype(np.uint8))

    # 1) 残留暗雾铺成干净墙（逐行取右侧 y1020-1300 中位数墙色，保留竖向渐变；别取左侧，椅子会渗进来）
    work = a.copy()
    y0, y1 = 470, 800
    for y in range(y0, y1):
        work[y, 0:1080] = np.median(work[y, 1020:1300], axis=0)
    work = Image.fromarray(np.clip(work, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))

    alpha = np.full((H, W), 0, np.float32)
    alpha[y0:y1, 0:1080] = 1.0
    ramp = 45
    for i in range(ramp):
        k = i / ramp
        alpha[y0 + i, :1080] *= k
        alpha[y1 - 1 - i, :1080] *= k
    for i in range(380):                        # 右边长羽化接回原墙
        alpha[y0:y1, 700 + i] *= 1 - i / 380
    alpha = np.clip(alpha, 0, 1)[..., None]
    base = Image.fromarray((np.asarray(work).astype(float) * alpha +
                            a * (1 - alpha)).astype(np.uint8)).convert("RGB")

    # 2) 只贴头发区域（暗色且偏暖的像素），边缘羽化 + 底边渐隐
    fa = np.asarray(f2).astype(int)
    hair = ((fa.max(axis=2) < 178) & (fa[:, :, 0] >= fa[:, :, 2] - 8)).astype(np.uint8) * 255
    hair = Image.fromarray(hair).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))
    layer = Image.new("RGB", (W, H), (232, 212, 194))
    layer.paste(f2, (DX, DY))
    mask = Image.new("L", (W, H), 0)
    mask.paste(hair, (DX, DY))
    m = np.asarray(mask).astype(np.float32)
    m[:470] = 0
    for y in range(800, 906):                  # 底边渐隐，和原有头发融到一起
        m[y] *= max(0.0, (906 - y) / 106.0)
    m[906:] = 0
    return Image.composite(layer, base, Image.fromarray(m.astype(np.uint8)))


def load_logo_image(path):
    """载入外部 logo 文件（透明底 PNG），裁掉四周透明留白。

    文件通常由 scripts/get_logo.py 产出（已去白底、已裁留白）。
    这里再裁一次是兜底：用户自己丢进来的图多半带边。
    """
    if not os.path.exists(path):
        raise SystemExit("LOGO_PATH 指向的文件不存在：%s" % path)
    im = Image.open(path).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop(bbox)
    if im.size[0] < 8 or im.size[1] < 8:
        raise SystemExit("logo 图片太小或内容为空：%s（%s）" % (path, im.size))
    return im


def paste_with_shadow(canvas, icon, ox, oy, offset=(6, 14), blur=18, tint=(60, 45, 30, 110)):
    """按 logo 自身轮廓投影后贴上去（外部 logo 用）。

    阴影色/偏移/模糊半径与 58 号手绘版一致，所以两种 logo 在封面上的「浮起感」相同。
    """
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    tint_layer = Image.new("RGBA", icon.size, tint)
    tint_layer.putalpha(icon.getchannel("A"))
    sh.alpha_composite(tint_layer, (ox + offset[0], oy + offset[1]))
    canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(icon, (ox, oy))
    return canvas


def build():
    bgr = cv2.imread(BASE, cv2.IMREAD_COLOR)
    clean = erase_old(bgr, erase_logo=ERASE_LOGO)
    canvas = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB)).convert("RGBA")
    canvas = restore_hair(canvas.convert("RGB")).convert("RGBA")

    global GAPS
    GAPS = [LINE1["gap"]]
    mixed_text(canvas, LINE1["cx"], LINE1["cy"], LINE1_SEGS, LINE1_FILL, LINE1["stroke"])
    GAPS = [LINE2["gap"], LINE2["gap"]]
    mixed_text(canvas, LINE2["cx"], LINE2["cy"], LINE2_SEGS, LINE2_FILL, LINE2["stroke"])

    if ERASE_LOGO:
        word_w = 0
        draw_word = True
        if LOGO_PATH.strip():
            # ---- 外部 logo（联网下载 / 用户给的）：按宽高比自动落位 ----
            img = load_logo_image(LOGO_PATH.strip())
            iw, ih = img.size
            if iw / float(ih) < 1.6:
                # 方形图标 → 顶替手绘 ICON，字标仍用 WORD_TEXT 画
                s = ICON_S / float(max(iw, ih))
                nw, nh = max(1, int(round(iw * s))), max(1, int(round(ih * s)))
                icon = img.resize((nw, nh), Image.LANCZOS)
                ox = ICON_X + (ICON_S - nw) // 2
                oy = ICON_Y + (ICON_S - nh) // 2
                canvas = paste_with_shadow(canvas, icon, ox, oy)
            else:
                # 横排整条（图标+字标一体）→ 整体进 LOGO_BAND，自带字标，不再画 WORD_TEXT
                bx0, by0, bx1, by1 = LOGO_BAND
                bw, bh = bx1 - bx0, by1 - by0
                s = min(bw / float(iw), bh / float(ih))
                nw, nh = max(1, int(round(iw * s))), max(1, int(round(ih * s)))
                icon = img.resize((nw, nh), Image.LANCZOS)
                ox = bx0 + (bw - nw) // 2
                oy = by0 + (bh - nh) // 2
                canvas = paste_with_shadow(canvas, icon, ox, oy)
                draw_word = False
        else:
            # ---- 手绘图标（58 号已验证路径，勿改）----
            icon = globals()[ICON_DRAWER](ICON_S)
            sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle(
                [ICON_X + 6, ICON_Y + 14, ICON_X + ICON_S + 6, ICON_Y + ICON_S + 14],
                radius=68, fill=(60, 45, 30, 110))
            canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(18)))
            canvas.alpha_composite(icon, (ICON_X, ICON_Y))

        if draw_word:
            fw = ImageFont.truetype(F_LATIN, WORD_SIZE)
            d = ImageDraw.Draw(canvas)
            x = WORD_X
            for ch in WORD_TEXT:
                bb = fw.getbbox(ch)
                d.text((x - bb[0], WORD_CY - (bb[1] + bb[3]) / 2), ch, font=fw, fill=WORD_FILL + (255,))
                x += bb[2] - bb[0] + WORD_TRACK
            word_w = x - WORD_X - WORD_TRACK
    else:
        word_w = 0

    out_dir = os.path.dirname(OUT)
    if out_dir:                              # OUT 只写文件名时别 makedirs('')
        os.makedirs(out_dir, exist_ok=True)
    canvas.convert("RGB").save(OUT, quality=95, subsampling=1)
    print("saved", OUT, "word_w", word_w)


if __name__ == "__main__":
    build()
