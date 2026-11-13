#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例选题（虚构）Nimbus 3.0 新版速览 · MG 样片 C（复古杂志 / 剪贴拼贴风）

与样片 A（深色科技）、B（亮色杂志）的差异：
- 底色：牛皮纸 / 旧报纸，含纤维噪点与做旧斑驳
- 主色：油墨黑 + 朱红 + 芥末黄 + 墨绿，全是低饱和印刷色
- 字体：宋体（Songti SC），标题带印刷错位阴影
- 动效：翻页、盖章弹跳、手写圈画、齿轮咬合、墨水晕开

用法：
    python build_mg_retro.py --preview   # 只出关键帧检查图
    python build_mg_retro.py             # 渲染无声 MP4
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
FPS = 30

# --- mgkit: overlap guard ---
import os
import sys as _mg_sys
from pathlib import Path as _mg_Path
# mgkit 位置：环境变量 > 向上探测 > 默认根目录
_mg_env = os.environ.get("MG_MGKIT_DIR")
if _mg_env:
    _mg_sys.path.insert(0, _mg_env)
else:
    _mg_here = _mg_Path(__file__).resolve()
    for _p in _mg_here.parents:
        if (_p / "mgkit" / "mgkit.py").exists():
            _mg_sys.path.insert(0, str(_p / "mgkit"))
            break
        if (_p / "模板" / "mgkit" / "mgkit.py").exists():
            _mg_sys.path.insert(0, str(_p / "模板" / "mgkit"))
            break
    else:
        _mg_sys.path.insert(0, str(_mg_here.parent.parent / "mgkit"))
from mgkit import (OverlapGuard, mark_text_layer, register_layer_texts,  # noqa: E402
                   set_content_offset, write_report, load_evidence_or_raw,
                   load_font, SHOTS_DIR, EVID_DIR)

GUARD = OverlapGuard(1080, 1920, text_thresh=0.015,
                     safe_top=0, safe_bottom=0,
                     safe_left=84, safe_right=150)

SHOTS = SHOTS_DIR  # 由 mgkit.paths 解析（MG_SHOTS_DIR 可覆盖）
EVID = EVID_DIR    # 由 mgkit.paths 解析（MG_EVID_DIR 可覆盖）

W, H = 1080, 1920

# 复古版全程用宋体做衬线；字体不写死路径与 ttc 序号，按角色向 mgkit 要。

# ---- 复古印刷色卡（低饱和油墨色）----
PAPER = (231, 220, 196)      # 牛皮纸底
PAPER_D = (214, 200, 173)    # 纸面暗部
CARD = (240, 232, 212)       # 卡片纸
INK = (38, 32, 26)           # 油墨黑
INK_S = (122, 110, 92)       # 次要墨色
RULE = (176, 162, 138)       # 分隔线
RED = (168, 48, 38)          # 朱红
RED_S = (232, 196, 188)
MUSTARD = (186, 140, 40)     # 芥末黄
MUSTARD_S = (236, 216, 168)
GREEN = (58, 96, 74)         # 墨绿
GREEN_S = (198, 214, 200)

SAFE_L = 84
SAFE_R = W - 150
CW = SAFE_R - SAFE_L

TOTAL = 24.8
NFRAMES = round(TOTAL * FPS)
YOFF = [300]

random.seed(20261112)


def font(size, bold=False):
    return load_font("serif_bold" if bold else "serif_regular", int(size))


def clamp(x):
    return max(0.0, min(1.0, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x * x


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.7):
    x = clamp(x)
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def fin(t, dur=0.30):
    return ease_out(t / dur)


def fout(t, dur=0.22):
    return ease_in(t / dur)


@lru_cache(maxsize=512)
def text_img(s, size, color, bold=False, spacing=1.30):
    f = font(size, bold)
    lines = s.split("\n")
    ws, tops = [], []
    for ln in lines:
        bb = f.getbbox(ln)
        ws.append(bb[2] - bb[0])
        tops.append(bb[1])
    step = int(size * spacing)
    im = Image.new("RGBA", (max(ws) + 20, step * len(lines) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((10, i * step + 8 - tops[i]), ln, font=f, fill=color + (255,))
    return mark_text_layer(im, s.replace(chr(10), ' / '))


@lru_cache(maxsize=512)
def paper_bg():
    """牛皮纸底：纤维噪点 + 做旧斑驳 + 四边压暗。"""
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im, "RGBA")

    # 大块色斑（不规则，模拟纸张不匀）
    for _ in range(26):
        cx, cy = random.randint(-100, W + 100), random.randint(-100, H + 100)
        r = random.randint(90, 300)
        shade = random.choice([(196, 182, 154), (240, 232, 212), (210, 194, 164)])
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=shade + (random.randint(14, 30),))

    # 纤维噪点
    px = im.load()
    for _ in range(42000):
        x, y = random.randint(0, W - 1), random.randint(0, H - 1)
        r, g, b = px[x, y]
        k = random.randint(-9, 8)
        px[x, y] = (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)))

    # 四边压暗（做旧，幅度要克制，否则像烛光）
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.rectangle((58, 70, W - 58, H - 70), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(200))
    dark = Image.new("RGB", (W, H), (176, 162, 134))
    im = Image.composite(im, dark, vig)
    return im.convert("RGBA")


def card(w, h, fill=CARD, border=RULE, bw=2, shadow=True):
    """纸片卡片：可选投影 + 硬边描边 + 轻微倾斜。"""
    pad = 16 if shadow else 0
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad + 5, pad + 8, pad + w + 5, pad + h + 8),
                                             3, fill=(70, 58, 42, 60))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(c).rectangle((0, 0, w - 1, h - 1), fill=fill + (255,),
                                outline=border + (255,), width=bw)
    im.alpha_composite(c, (pad, pad))
    return im, pad


def wipe(base, layer, x, y, p, axis="x"):
    """遮罩擦除：按进度裁切后合成，用于下划线生长、文字显现。"""
    p = clamp(p)
    if p <= 0.002:
        return
    if p >= 0.999:
        base.alpha_composite(layer, (int(x), int(y)))
        return
    if axis == "x":
        box = (0, 0, max(1, int(layer.width * p)), layer.height)
    else:
        box = (0, 0, layer.width, max(1, int(layer.height * p)))
    base.alpha_composite(layer.crop(box), (int(x), int(y)))


def place(base, layer, x, y, a=1.0, dy=0, scale=1.0, angle=0.0):
    if a <= 0.002:
        return
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))),
                             Image.LANCZOS)
    if a < 0.999:
        layer = layer.copy()
        layer.putalpha(layer.getchannel("A").point([int(i * a) for i in range(256)]))
    xx, yy = int(x), int(y + dy)
    if xx < 0 or yy < 0 or xx + layer.width > base.width or yy + layer.height > base.height:
        bx0, by0 = max(0, xx), max(0, yy)
        bx1, by1 = min(base.width, xx + layer.width), min(base.height, yy + layer.height)
        if bx1 <= bx0 or by1 <= by0:
            return
        layer = layer.crop((bx0 - xx, by0 - yy, bx1 - xx, by1 - yy))
        xx, yy = bx0, by0
    base.alpha_composite(layer, (xx, yy))
    register_layer_texts(GUARD, layer, x, y, a)


def stamp_img(text, size=54, color=RED, ring=True):
    """圆形印章：外圈 + 内部文字，像盖上去的。"""
    f = font(size, True)
    bb = f.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    r = max(tw, th) // 2 + int(size * 0.55) + 18
    im = Image.new("RGBA", (r * 2 + 24, r * 2 + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = r + 12
    if ring:
        d.ellipse((c - r, c - r, c + r, c + r), outline=color + (235,), width=7)
        d.ellipse((c - r + 14, c - r + 14, c + r - 14, c + r - 14), outline=color + (180,), width=2)
    t = text_img(text, size, color, True)
    im.alpha_composite(t, (c - t.width // 2, c - t.height // 2))
    # 盖章不匀：随机抠掉一些像素
    px = im.load()
    for _ in range(int(im.width * im.height * 0.012)):
        x, y = random.randint(0, im.width - 1), random.randint(0, im.height - 1)
        r0, g0, b0, a0 = px[x, y]
        if a0:
            px[x, y] = (r0, g0, b0, max(0, a0 - random.randint(60, 150)))
    return im


def underline_hand(s, size, color, width_ratio=0.86):
    """手绘感下划线：两段抖动笔画。"""
    f = font(size, True)
    bb = f.getbbox(s)
    w = int((bb[2] - bb[0]) * width_ratio)
    h = int(size * 0.30)
    im = Image.new("RGBA", (w + 20, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    x = 6
    while x < w:
        pts.append((x, h // 2 + random.randint(-3, 3)))
        x += random.randint(14, 26)
    if len(pts) > 1:
        d.line(pts, fill=color + (240,), width=max(4, size // 16), joint="curve")
    return im


def circle_hand(w, h, color, width=6):
    """手绘圈画：椭圆不闭合，模拟笔迹。"""
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(0, 61):
        a = math.radians(-8 + i * 6.2)
        r = 1.0 + random.uniform(-0.05, 0.05)
        pts.append((w / 2 + math.cos(a) * w / 2 * r + 10,
                    h / 2 + math.sin(a) * h / 2 * r + 10))
    d.line(pts, fill=color + (235,), width=width, joint="curve")
    return im


@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 color=0.55, contrast=0.88, brightness=0.96)
    return im


def shot_card(name, box, w, h, label=None, tape=True):
    """老照片 / 剪报：白底截图做旧 + 胶带 + 略微倾斜。"""
    bar_h = 36
    layer, pad = card(w, h, (238, 230, 210), RULE, 2, shadow=True)
    d = ImageDraw.Draw(layer)
    d.rectangle((pad, pad, pad + w - 1, pad + h - 1), fill=(238, 230, 210, 255),
                outline=RULE + (255,), width=2)
    d.rectangle((pad, pad + bar_h, pad + w - 1, pad + bar_h + 1), fill=RULE + (255,))
    for i, c in enumerate(((196, 110, 96), (196, 168, 96), (130, 150, 118))):
        d.ellipse((pad + 15 + i * 18, pad + 13, pad + 25 + i * 18, pad + 23), fill=c + (255,))
    if label:
        t = text_img(label, 22, INK_S, True)
        layer.alpha_composite(t, (pad + 82, pad + 6))
    ip = 10
    src = load_shot(name, box, w - 2 * ip, h - bar_h - 2 * ip)
    layer.alpha_composite(src, (pad + ip + (w - 2 * ip - src.width) // 2,
                                pad + bar_h + ip + (h - bar_h - 2 * ip - src.height) // 2))
    if tape:
        tape = Image.new("RGBA", (150, 46), (0, 0, 0, 0))
        td = ImageDraw.Draw(tape)
        td.polygon([(0, 6), (150, 0), (146, 42), (4, 46)], fill=(228, 214, 176, 170))
        td.line([(0, 6), (150, 0)], fill=(198, 182, 142, 190), width=2)
        place(layer, tape, w // 2 - 75, -18, 0.95, angle=-4)
    return layer


# ---------------------------------------------------------------- 顶栏
def top_bar(base, p, label="NIMBUS · 新版速览"):
    """复古刊头：左侧标签 + 细双线 + 右侧期号。"""
    d = ImageDraw.Draw(base)
    tag = text_img(label, 26, INK, True)
    place(base, tag, SAFE_L, 66, 1.0)
    issue = text_img(f"NO.{int(p*100):02d}", 24, INK_S, True)
    place(base, issue, SAFE_R - issue.width, 66, 1.0)
    d.rectangle((SAFE_L, 118, SAFE_R, 120), fill=INK + (255,))
    d.rectangle((SAFE_L, 126, SAFE_R, 127), fill=INK + (170,))
    if p > 0:
        d.rectangle((SAFE_L, 132, SAFE_L + int(CW * p), 136), fill=RED + (255,))


# ---------------------------------------------------------------- 场景
def sc_hook(base, t):
    """钩子：报纸大标题 + 手写下划线 + 印章砸下 + 三张价签纸片。"""
    d = ImageDraw.Draw(base)

    a = fin(t - 0.05, 0.35)
    t1 = text_img("新版速览", 108, INK, True)
    place(base, t1, SAFE_L, 330, a, dy=34 * (1 - a))

    a2 = fin(t - 0.22, 0.35)
    t2 = text_img("笔记 · 附件 · 网页", 66, INK, True)
    place(base, t2, SAFE_L, 470, a2, dy=28 * (1 - a2))

    a3 = fin(t - 0.40, 0.32)
    t3 = text_img("离线同步能用了", 88, RED, True)
    place(base, t3, SAFE_L, 570, a3, dy=30 * (1 - a3))

    # 手写下划线（划到重点词下面）
    ul = underline_hand("离线同步能用了", 88, RED)
    p = fin(t - 0.62, 0.40)
    if p > 0:
        wipe(base, ul, SAFE_L, 690, p)

    # 印章砸下
    st = stamp_img("实测", 50, RED)
    sa = back_out((t - 0.85) / 0.40)
    if sa > 0:
        place(base, st, SAFE_R - st.width + 40, 300, sa,
              dy=-30 * (1 - sa), scale=1.25 - 0.25 * sa, angle=-14)

    # 三张价签纸片，错落贴上
    tags = [("笔记", "含在新版"), ("附件", "含在新版"), ("网页", "含在新版")]
    for i, (k, v) in enumerate(tags):
        stt = 1.05 + i * 0.15
        p = back_out((t - stt) / 0.45)
        if p <= 0:
            continue
        c, _ = card(250, 206, CARD, RULE, 2)
        cd = ImageDraw.Draw(c)
        tk = text_img(k, 38, INK, True)
        c.alpha_composite(tk, (26, 20))
        tv = text_img(v, 70, RED, True)
        c.alpha_composite(tv, (26, 84))
        d2 = ImageDraw.Draw(c)
        d2.line((26, 72, 224, 72), fill=RULE + (255,), width=2)
        place(base, c, SAFE_L + i * 264, 780, p, dy=40 * (1 - p), angle=(-3, 2, -1)[i] * (1 - p))

    # 底部小字
    a4 = fin(t - 1.50, 0.35)
    t4 = text_img("Nimbus 3.0 系列 · 官网当前版本说明", 32, INK_S)
    place(base, t4, SAFE_L, 1040, a4, dy=14 * (1 - a4))


def sc_proof(base, t):
    """兑现：翻页式切入 + 剪报截图 + 红笔圈画。"""
    a = fin(t - 0.02, 0.30)
    t1 = text_img("新版功能", 92, INK, True)
    place(base, t1, SAFE_L, 320, a, dy=28 * (1 - a))

    a2 = fin(t - 0.16, 0.30)
    t2 = text_img("就挂在官网首页", 76, INK, True)
    place(base, t2, SAFE_L, 440, a2, dy=24 * (1 - a2))

    # 剪报从上方翻入
    shot = shot_card("01-官网首页-新版公告.jpg", (300, 155, 1000, 262),
                     CW, 230, "官网首屏")
    p = ease_in_out((t - 0.30) / 0.65)
    if p > 0:
        # 模拟翻页：上边下压 + 透视缩放
        place(base, shot, SAFE_L, 640 - 50 * (1 - p), p,
              scale=0.92 + 0.08 * p, angle=(1 - p) * 6)

    # 红笔圈画「新版功能」位置
    cp = t - 1.05
    if cp > 0:
        cir = circle_hand(300, 70, RED, 7)
        ca = fin(cp, 0.45)
        place(base, cir, SAFE_L + 250, 655, ca, scale=0.85 + 0.15 * ca)

    a3 = fin(t - 1.28, 0.32)
    t3 = text_img("不是营销话术，是官网自己的入口", 34, INK_S)
    place(base, t3, SAFE_L, 930, a3, dy=14 * (1 - a3))

    # 批注便签（胶带贴）
    st = stamp_img("真的", 44, RED)
    sa = back_out((t - 1.50) / 0.42)
    if sa > 0:
        place(base, st, SAFE_R - st.width + 30, 930, sa, scale=1.2 - 0.2 * sa, angle=10)


def sc_two_ways(base, t):
    """两种用法：两张剪报卡片错位贴上 + 中缝虚线 + 打字机说明。"""
    a = fin(t - 0.02, 0.30)
    t1 = text_img("两种用法", 88, INK, True)
    place(base, t1, SAFE_L, 320, a, dy=26 * (1 - a))

    cw = (CW - 46) // 2
    blocks = [
        ("普通用户", "Nimbus 网页端", "编辑 · 协作\n搜索 · 归档", GREEN, GREEN_S, -2.5),
        ("开发者", "API 接口", "离线增量\n接入自有脚本", RED, RED_S, 2.5),
    ]
    for i, (title, sub, body, ac, sc_, ang) in enumerate(blocks):
        st = 0.20 + i * 0.18
        p = back_out((t - st) / 0.5)
        if p <= 0:
            continue
        c, _ = card(cw, 420, CARD, RULE, 2)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, cw - 1, 419), fill=CARD + (255,))
        cd.rectangle((0, 0, cw - 1, 12), fill=ac + (255,))
        badge = text_img(title, 40, ac, True)
        c.alpha_composite(badge, (30, 42))
        t2 = text_img(sub, 38, INK, True)
        c.alpha_composite(t2, (30, 118))
        cd.line((30, 182, cw - 30, 182), fill=RULE + (255,), width=2)
        for j, ln in enumerate(body.split("\n")):
            t3 = text_img(ln, 28, INK_S)
            c.alpha_composite(t3, (30, 214 + j * 48))
        place(base, c, SAFE_L + i * (cw + 46), 480, p, dy=44 * (1 - p), angle=ang * (1 - p))

    # 中缝虚线（撕纸感）
    mp = t - 0.70
    if mp > 0:
        d = ImageDraw.Draw(base)
        x = SAFE_L + cw + 23
        for i in range(14):
            yy = 500 + i * 30
            d.rectangle((x, yy, x + 2, yy + 14), fill=INK_S + (150,))

    a3 = fin(t - 1.00, 0.32)
    t3 = text_img("不写代码也能用，要接工具才走 API", 34, INK_S)
    place(base, t3, SAFE_L, 970, a3, dy=14 * (1 - a3))


def sc_steps(base, t):
    """开发者五步：打字机逐行出现 + 序号印章 + 左侧竖线。"""
    a = fin(t - 0.02, 0.30)
    t1 = text_img("开发者五步", 88, INK, True)
    place(base, t1, SAFE_L, 310, a, dy=26 * (1 - a))

    items = ["注册账户", "创建工作区", "装 nimbus 命令行", "连同步地址", "开第一次同步"]
    row_h = 168
    y0 = 470

    lp = fin(t - 0.38, 1.30)
    if lp > 0:
        d = ImageDraw.Draw(base)
        d.rectangle((SAFE_L + 30, y0 + 30, SAFE_L + 34, y0 + 30 + int((row_h * 5 - 40) * lp)),
                    fill=MUSTARD + (255,))

    for i, it in enumerate(items):
        st = 0.24 + i * 0.16
        p = fin(t - st, 0.30)
        if p <= 0:
            continue
        cy = y0 + i * row_h

        # 序号：方形墨印
        num = Image.new("RGBA", (62, 62), (0, 0, 0, 0))
        nd = ImageDraw.Draw(num)
        nd.rectangle((2, 2, 60, 60), outline=INK + (220,), width=3)
        nt = text_img(str(i + 1), 34, INK, True)
        num.alpha_composite(nt, (32 - nt.width // 2, 32 - nt.height // 2))
        place(base, num, SAFE_L, cy, p, dy=18 * (1 - p))

        # 文字逐字打字机
        f = font(38, True)
        shown = it[:max(1, int(len(it) * clamp((t - st) / 0.42)))]
        tb = text_img(shown, 38, INK, True)
        place(base, tb, SAFE_L + 96, cy + 8, p)

        # 已完成步骤打勾
        if t > st + 0.5:
            cp = fin(t - st - 0.5, 0.3)
            ck = Image.new("RGBA", (56, 56), (0, 0, 0, 0))
            kd = ImageDraw.Draw(ck)
            kd.line((12, 29, 23, 41), fill=GREEN + (255,), width=6)
            kd.line((23, 41, 46, 15), fill=GREEN + (255,), width=6)
            place(base, ck, SAFE_R - 58, cy + 4, cp)


def sc_code(base, t):
    """请求参数：打字机代码 + 纸张便签 + 盖章确认。"""
    a = fin(t - 0.02, 0.30)
    t1 = text_img("三行就能发出去", 80, INK, True)
    place(base, t1, SAFE_L, 310, a, dy=26 * (1 - a))

    # 剪报文档
    shot = shot_card("03-快速开始-工作区与首次同步.jpg", (0, 150, 1396, 1420),
                     CW, 380, "官方快速开始")
    p = ease_in_out((t - 0.16) / 0.60)
    if p > 0:
        place(base, shot, SAFE_L, 450 - 40 * (1 - p), p, scale=0.93 + 0.07 * p, angle=(1 - p) * -4)

    # 代码纸条
    lines = [
        ("model:", "nimbus-cli 3.0"),
        ("base:", "drive.nimbus.dev"),
        ("auth:", "Bearer YOUR_API_KEY"),
    ]
    code_y = 890
    card_h = 56 * len(lines) + 40
    c, _ = card(CW, card_h, (246, 240, 224), RULE, 2)
    cd = ImageDraw.Draw(c)
    cd.rectangle((0, 0, 12, card_h - 1), fill=RED + (255,))
    place(base, c, SAFE_L, code_y, fin(t - 0.34, 0.35), dy=30 * (1 - fin(t - 0.34, 0.35)),
          angle=-0.8)
    for i, (k, v) in enumerate(lines):
        st = 0.52 + i * 0.20
        p = fin(t - st, 0.30)
        if p <= 0:
            continue
        f = font(30, False)
        shown = (k + v)[:max(1, int(len(k + v) * clamp((t - st) / 0.45)))]
        kt = text_img(k, 30, INK_S)
        vt = text_img(shown[len(k):], 30, RED if i == 0 else INK, i == 0)
        row = Image.new("RGBA", (CW - 60, 40), (0, 0, 0, 0))
        row.alpha_composite(kt, (0, 0))
        row.alpha_composite(vt, (kt.width + 14, 0))
        place(base, row, SAFE_L + 34, code_y + 22 + i * 56, p)

    # 盖章"可复制"
    st = stamp_img("可复制", 42, GREEN)
    sa = back_out((t - 1.35) / 0.42)
    if sa > 0:
        place(base, st, SAFE_R - st.width + 20, code_y + 30, sa,
              scale=1.25 - 0.25 * sa, angle=12)


def sc_free_range(base, t):
    """能力范围：清单式打钩 + 朱红勾 + 墨绿标签。"""
    a = fin(t - 0.02, 0.30)
    t1 = text_img("哪些新版能用", 86, INK, True)
    place(base, t1, SAFE_L, 310, a, dy=26 * (1 - a))

    rows = [
        ("笔记协作 ×3", "多人同时编辑"),
        ("附件版本 ×5", "保留 30 天版本"),
        ("网页剪藏 不限页", "自动打标签"),
    ]
    for i, (k, v) in enumerate(rows):
        st = 0.22 + i * 0.18
        p = back_out((t - st) / 0.45)
        if p <= 0:
            continue
        c, _ = card(CW, 148, CARD, RULE, 2)
        cd = ImageDraw.Draw(c)
        # 左侧方框 + 朱红勾（手绘）
        cd.rectangle((28, 44, 88, 104), outline=INK + (200,), width=3)
        cp = clamp((t - st - 0.22) / 0.4)
        if cp > 0:
            ck = Image.new("RGBA", (70, 70), (0, 0, 0, 0))
            kd = ImageDraw.Draw(ck)
            kd.line((14, 36, 28, 50), fill=RED + (255,), width=8)
            kd.line((28, 50, 56, 18), fill=RED + (255,), width=8)
            place(c, ck, 22, 34, cp)
        tk = text_img(k, 40, INK, True)
        c.alpha_composite(tk, (116, 32))
        tv = text_img(v, 28, INK_S)
        c.alpha_composite(tv, (116, 90))
        tag = text_img("NEW", 34, GREEN, True)
        c.alpha_composite(tag, (CW - tag.width - 34, 52))
        place(base, c, SAFE_L, 470 + i * 172, p, dy=36 * (1 - p), angle=(-1.6, 1.4, -1.0)[i] * (1 - p))


def sc_zero(base, t):
    """能力证据：旧版本号划掉 + 数字滚动 + 剪报版本说明页 + 红圈。"""
    a = fin(t - 0.02, 0.30)
    t1 = text_img("网页剪藏 不限页", 74, INK, True)
    place(base, t1, SAFE_L, 300, a, dy=24 * (1 - a))

    a2 = fin(t - 0.26, 0.30)
    old = text_img("旧版只能同步 1 台", 42, INK_S, True)
    place(base, old, SAFE_L, 400, a2)
    sp = fin(t - 0.56, 0.38)
    if sp > 0:
        strike = Image.new("RGBA", (old.width + 10, 6), (0, 0, 0, 0))
        ImageDraw.Draw(strike).rectangle((0, 0, old.width + 10, 5), fill=RED + (255,))
        wipe(base, strike, SAFE_L, 400 + old.height // 2, sp)

    a3 = fin(t - 0.70, 0.30)
    lab = text_img("当前版本说明", 32, INK_S, True)
    place(base, lab, SAFE_L, 490, a3)

    rp = clamp((t - 0.80) / 1.0)
    val = 1 + 2 * ease_out(rp)
    num_s = "3" if rp >= 0.999 else f"{val:.1f}"
    num = text_img(num_s, 128, RED, True)
    place(base, num, SAFE_L, 545, a3)
    unit = text_img("台设备", 44, INK, True)
    place(base, unit, SAFE_L + num.width + 14, 545 + 94, a3)

    # 剪报版本说明页
    shot = shot_card("07-版本能力-离线同步说明.jpg", (0, 700, 1396, 822),
                     CW, 160, "官网版本说明页")
    p = ease_in_out((t - 1.00) / 0.60)
    if p > 0:
        place(base, shot, SAFE_L, 730 - 34 * (1 - p), p, scale=0.94 + 0.06 * p, angle=(1 - p) * 5)

    # 红圈标注重点位置
    cp = t - 1.42
    if cp > 0:
        cir = circle_hand(150, 76, RED, 6)
        ca = fin(cp, 0.45)
        place(base, cir, SAFE_R - 210, 745, ca, scale=0.85 + 0.15 * ca)

    a4 = fin(t - 1.58, 0.30)
    t4 = text_img("nimbus-desktop-3.0 · 官网当前说明", 30, INK_S)
    place(base, t4, SAFE_L, 940, a4, dy=12 * (1 - a4))


def sc_limits(base, t):
    """三条限制：撕纸条依次落下 + 红色警告印章。"""
    a = fin(t - 0.02, 0.30)
    t1 = text_img("但有三条限制", 86, RED, True)
    place(base, t1, SAFE_L, 310, a, dy=26 * (1 - a))

    rows = [
        "新版灰度中，还没全量放开",
        "有 TPS 和公平使用配额",
        "Agent Plan 按刊例价折算 Credits",
    ]
    for i, txt in enumerate(rows):
        st = 0.24 + i * 0.18
        p = back_out((t - st) / 0.45)
        if p <= 0:
            continue
        c, _ = card(CW, 138, (238, 222, 214), (196, 128, 118), 2)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, 10, 137), fill=RED + (255,))
        tb = text_img(txt, 36, INK, True)
        c.alpha_composite(tb, (36, 50))
        place(base, c, SAFE_L, 470 + i * 170, p, dy=40 * (1 - p), angle=(-2, 1.5, -1)[i] * (1 - p))

    # 警告印章
    st = stamp_img("注意", 48, RED)
    sa = back_out((t - 1.05) / 0.42)
    if sa > 0:
        place(base, st, SAFE_R - st.width + 30, 300, sa, scale=1.25 - 0.25 * sa, angle=-13)

    a2 = fin(t - 1.25, 0.30)
    t2 = text_img("最终以平台公告和你的账户账单为准", 30, INK_S)
    place(base, t2, SAFE_L, 1000, a2, dy=12 * (1 - a2))


def sc_end(base, t):
    """收尾：宋体大字 + 手绘下划线 + 印钞机式关注条。"""
    a = back_out((t - 0.02) / 0.42)
    t1 = text_img("你最想先试哪个？", 90, INK, True)
    place(base, t1, SAFE_L, 470, a, dy=34 * (1 - a), scale=0.92 + 0.08 * a)

    a2 = fin(t - 0.20, 0.30)
    t2 = text_img("评论区告诉我，我下期实测", 44, RED, True)
    place(base, t2, SAFE_L, 620, a2, dy=18 * (1 - a2))

    ul = underline_hand("评论区告诉我，我下期实测", 44, MUSTARD, 0.9)
    up = fin(t - 0.34, 0.40)
    if up > 0:
        wipe(base, ul, SAFE_L, 700, up)

    a3 = fin(t - 0.52, 0.30)
    t3 = text_img("下期拆一个真实场景 · 记得回来看", 32, INK_S)
    place(base, t3, SAFE_L, 770, a3, dy=14 * (1 - a3))

    # 关注条（像印刷标签）
    pa = t - 0.78
    if pa > 0:
        bar, _ = card(520, 96, RED, RED, 0, shadow=True)
        bd = ImageDraw.Draw(bar)
        bd.rectangle((0, 0, 519, 95), fill=RED + (255,))
        bt = text_img("关注我 · 只测官网写得清的", 34, (246, 240, 224), True)
        bar.alpha_composite(bt, ((520 - bt.width) // 2, 30))
        place(base, bar, SAFE_L, 880, fin(pa, 0.35), angle=-1.5)


SCENES = [
    (0.00, 3.40, sc_hook),
    (3.50, 3.40, sc_proof),
    (7.00, 3.40, sc_two_ways),
    (10.50, 2.60, sc_steps),
    (13.20, 3.50, sc_code),
    (16.80, 1.90, sc_free_range),
    (18.80, 2.40, sc_zero),
    (21.30, 2.30, sc_limits),
    (23.70, 1.10, sc_end),
]


def render_frame(t):
    GUARD.reset()
    base = paper_bg().copy()
    for start, dur, fn in SCENES:
        if not (start <= t < start + dur):
            continue
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(layer, t - start)
        shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shifted.alpha_composite(layer, (0, YOFF[0]))
        a = fin(t - start, 0.26)
        if t > start + dur - 0.24:
            a *= fout(t - (start + dur - 0.24), 0.24)
        if a < 0.999:
            shifted.putalpha(shifted.getchannel("A").point([int(i * a) for i in range(256)]))
        base.alpha_composite(shifted)
    top_bar(base, t / TOTAL)
    # --- mgkit: overlap check ---
    GUARD.check(f"t={t:.2f}")
    # --- end mgkit ---
    return base.convert("RGB")


def make_contact():
    marks = [0.6, 1.4, 2.4, 3.0, 4.2, 5.6, 7.8, 9.4, 11.2, 12.8, 14.2, 15.6,
             17.4, 19.0, 20.4, 22.0, 23.2, 24.2]
    cw, ch = 240, 427
    cols = 6
    rows = (len(marks) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, ch * rows), (60, 52, 42))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧C-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 28), fill=(38, 32, 26))
        td.text((8, 3), f"{t:.1f}s", font=font(18, True), fill=(231, 220, 196))
        sheet.paste(thumb, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(HERE / "检查图-MG样片C.png")
    write_report(GUARD, HERE, "C 复古拼贴")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片C.png")


def main():
    preview = "--preview" in sys.argv
    make_contact()
    if preview:
        print("--preview，仅生成关键帧检查图")
        return
    out = HERE / "MG-样片C-复古拼贴-无声.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(NFRAMES):
        p.stdin.write(render_frame(i / FPS).tobytes())
        if i % 240 == 0:
            print(f"  渲染 {i}/{NFRAMES}", flush=True)
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg 失败")
    print(f"完成 {out.name}  {NFRAMES} 帧 / {NFRAMES/FPS:.2f}s")


if __name__ == "__main__":
    main()
