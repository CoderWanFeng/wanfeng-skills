# -*- coding: utf-8 -*-
"""封面换皮脚本 · 晚枫专用路径 Step H（模板，已用 58-glm3亿 真实交付验证）

打法：在混元封面底图（1728x2304）上**只换字、只换 logo，人像一像素不动**。
用户原话：「我以后都会穿那个衣服录视频，直接在那张底图上把字改了、把 LOGO 改了就行，人都不用动。」

依赖（托管解释器，见 wanfeng-path.md §3.2/§3.3）：
    ~/.workbuddy/binaries/python/envs/default/bin/python3   # PIL 12.x + numpy + cv2

固定资产（已沉淀进 skill，勿删）：
    底图        reference/assets/cover/封面-底图-混元WB.jpg     # 墙面人像，1:1 像素底
    头发参考帧  reference/assets/cover/hy4-frame7.png          # 同段视频第 7 秒帧，补头顶用

用法：把本文件复制到 <选题>/AI剪辑输出/src/cover.py，改下面 CONFIG，然后跑。
     只改标着【每期必改】的项；标【勿改】的是配准/版式实测值，动了必翻车（见 wanfeng-cover.md 踩坑表）。
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================ CONFIG ============================================================
def _skill_asset(name):
    """按「本机 skill 仓库 → SkillHub 安装目录」顺序找固定资产，找到第一个为止。"""
    cands = [
        "/Users/wanfeng/晚枫工作室/code/wanfeng-skills/skills/mograph/reference/assets/cover",   # 晚枫本机仓库
        os.path.expanduser("~/.workbuddy/skills/wanfeng-mograph__skillhub/reference/assets/cover"),  # SkillHub 安装版
    ]
    for d in cands:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("找不到封面固定资产 %s，请检查 skill 是否完整安装" % name)

BASE = _skill_asset("封面-底图-混元WB.jpg")        # 【勿改】底图
HEAD_SRC = _skill_asset("hy4-frame7.png")          # 【勿改】头发参考帧
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
ERASE_LOGO = True
ICON_X, ICON_Y, ICON_S = 864, 1150, 300      # 图标位置/尺寸【勿改，底图配准值】
WORD_TEXT, WORD_X, WORD_CY, WORD_SIZE = "ZCODE", 1186, 1301, 152
WORD_TRACK, WORD_FILL = -6, (0, 0, 0)        # 字距收紧、黑色字标
ICON_DRAWER = "z_icon"                       # 本文件里定义的图标绘制函数名；换成你品牌的画法

# ---- 字体（勿改）----
F_BOLD  = "/Users/wanfeng/Library/Fonts/TencentSans-W7.ttf"
F_LATIN = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

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
        icon = globals()[ICON_DRAWER](ICON_S)
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [ICON_X + 6, ICON_Y + 14, ICON_X + ICON_S + 6, ICON_Y + ICON_S + 14],
            radius=68, fill=(60, 45, 30, 110))
        canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(18)))
        canvas.alpha_composite(icon, (ICON_X, ICON_Y))

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

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    canvas.convert("RGB").save(OUT, quality=95, subsampling=1)
    print("saved", OUT, "word_w", word_w)


if __name__ == "__main__":
    build()
