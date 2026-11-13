#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes AI 免费使用 · MG 样片 F（暖色治愈风）

前五版：A 深色科技 / B 亮色杂志 / C 复古拼贴 / D 故障艺术 / E 像素游戏
本版：暖色系，奶油底 + 蜜桃橙 + 焦糖棕，柔和圆角，蒸汽波柔光，缓慢呼吸感。

视觉语言：
- 奶油纸底 + 大面积柔光晕（径向渐变）
- 圆角软卡片，无描边，靠柔和阴影分层
- 暖橙主色 + 焦糖棕正文 + 抹茶绿点缀
- 动效：Q 弹缩放、软体挤压、柔光脉冲、毛玻璃光斑、丝带飘落

用法：
    python build_mg_warm.py --preview   # 只出关键帧检查图
    python build_mg_warm.py             # 渲染无声 MP4
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

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
                   set_content_offset, write_report, evidence_path,
                   SHOTS_DIR, EVID_DIR)

GUARD = OverlapGuard(1080, 1920, text_thresh=0.015,
                     safe_top=0, safe_bottom=0, safe_left=0, safe_right=0)

SHOTS = SHOTS_DIR  # 由 mgkit.paths 解析（MG_SHOTS_DIR 可覆盖）
EVID = EVID_DIR    # 由 mgkit.paths 解析（MG_EVID_DIR 可覆盖）

W, H = 1080, 1920

F7 = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F3 = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F7_IDX, F3_IDX = 2, 0

# ---- 暖色治愈色卡 ----
CREAM = (253, 246, 238)      # 奶油底
CREAM_D = (246, 233, 219)    # 底色暗部
CARD = (255, 252, 248)       # 卡片
INK = (74, 51, 40)           # 焦糖棕正文
INK_S = (146, 116, 98)       # 次要
PEACH = (247, 138, 92)       # 主色 蜜桃橙
PEACH_S = (253, 228, 214)    # 浅橙
CARAMEL = (186, 122, 68)     # 焦糖
MATCHA = (138, 178, 122)     # 抹茶绿
MATCHA_S = (222, 238, 216)
CREAMY = (250, 206, 120)     # 奶黄
CREAMY_S = (253, 238, 204)
ROSE = (226, 122, 138)       # 玫瑰粉
ROSE_S = (251, 222, 226)

SAFE_L = 84
SAFE_R = W - 150
CW = SAFE_R - SAFE_L

TOTAL = 24.8
NFRAMES = round(TOTAL * FPS)
YOFF = [210]

random.seed(20261112)


def font(size, bold=False):
    return ImageFont.truetype(F7 if bold else F3, int(size), index=F7_IDX if bold else F3_IDX)


def clamp(x):
    return max(0.0, min(1.0, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x * x


def soft_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 4


def back_out(x, s=2.4):
    """强回弹：暖色风的软萌感来源。"""
    x = clamp(x)
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def spring(x, freq=2.6, damp=5.0):
    """阻尼振荡：元素落位时的轻微过冲。"""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1 - math.exp(-damp * x) * math.cos(freq * math.pi * x)


def fin(t, dur=0.34):
    return ease_out(t / dur)


def fout(t, dur=0.24):
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


@lru_cache(maxsize=128)
def soft_shadow(w, h, radius=32, blur=26, alpha=40):
    """柔和投影：暖色风靠影子分层，不用描边。"""
    pad = blur * 2
    sh = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + w - 1, pad + h - 1 + 14),
                                         radius, fill=(150, 110, 85, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur)), pad


def card(w, h, fill=CARD, radius=32):
    """软卡片：只投影，不描边。"""
    sh, pad = soft_shadow(w, h, radius)
    im = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    im.alpha_composite(sh)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=fill + (255,))
    im.alpha_composite(c, (pad, pad))
    # 内容区相对图层左上角的偏移，供重叠检测换算
    set_content_offset(im, pad, pad)
    return im, pad


@lru_cache(maxsize=128)
def chip(s, size, fg, fill, pad_x=26, pad_y=14, radius=None):
    t = text_img(s, size, fg, True)
    w, h = t.width + pad_x * 2, t.height + pad_y * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius or h // 2,
                                         fill=fill + (255,))
    im.alpha_composite(t, (pad_x, pad_y))
    return im


@lru_cache(maxsize=4)
def glow_bg():
    """奶油底 + 大面积柔光晕（径向渐变），暖色治愈感的底子。"""
    im = Image.new("RGB", (W, H), CREAM)
    # 暖光斑
    blobs = [
        ((200, 260, 620), PEACH, 58),
        ((900, 760, 560), CREAMY, 66),
        ((180, 1420, 600), ROSE, 44),
        ((820, 1700, 520), MATCHA, 40),
    ]
    for (cx, cy, r), col, a in blobs:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        steps = 42
        for i in range(steps, 0, -1):
            rr = r * i / steps
            aa = int(a * (1 - i / steps) ** 1.7)
            od.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col + (aa,))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    im = im.filter(ImageFilter.GaussianBlur(26))
    return im.convert("RGBA")


def place(base, layer, x, y, a=1.0, dy=0, scale=1.0, angle=0.0, squeeze=1.0):
    """带 alpha / 位移 / 缩放 / 旋转 / 挤压的合成。"""
    if a <= 0.002:
        return
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    if squeeze != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)),
                              max(1, int(layer.height * scale * squeeze))),
                             Image.LANCZOS)
    elif scale != 1.0:
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


def wipe(base, layer, x, y, p, axis="x"):
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


def evid_card(name, w, h, label=None, accent=PEACH, radius=26):
    """证据图卡：暖色风里截图用米白底 + 柔和投影，不再是浏览器窗口。

    官网截图是白底，放在奶油色画面上要提亮才有对比。
    """
    im = Image.open(evidence_path(name, prefer_light=True)).convert("RGB")
    r = min(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    im = ImageEnhance.Brightness(im).enhance(1.10)
    im = ImageEnhance.Contrast(im).enhance(1.05)

    layer, pad = card(w, h, CARD, radius)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((pad, pad, pad + w - 1, pad + h - 1), radius,
                        fill=CARD + (255,))
    ip = 14
    layer.alpha_composite(im.convert("RGBA"),
                          (pad + ip + (w - 2 * ip - im.width) // 2,
                           pad + ip + (h - 2 * ip - im.height) // 2))
    if label:
        tag = chip(label, 24, accent, PEACH_S)
        layer.alpha_composite(tag, (pad + 16, pad + 14))
    return layer


def top_bar(base, p, label="AGNES AI · 免费使用"):
    """顶部：柔和标签 + 圆角进度点。"""
    tag = chip(label, 25, PEACH, PEACH_S, pad_x=24, pad_y=12)
    place(base, tag, SAFE_L, 66, 1.0)
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle((SAFE_L, 146, SAFE_R, 152), 3, fill=CREAM_D + (255,))
    if p > 0:
        d.rounded_rectangle((SAFE_L, 146, SAFE_L + int(CW * p), 152), 3, fill=PEACH + (255,))
    # 暖色小圆点
    for i in range(3):
        d.ellipse((SAFE_R - 66 + i * 22, 70, SAFE_R - 54 + i * 22, 82),
                  fill=(PEACH, CREAMY, MATCHA)[i] + (230,))


# ---------------------------------------------------------------- 场景
def sc_hook(base, t):
    """钩子：柔光标题 + 三颗软糖徽章 + 呼吸光晕。"""
    # 呼吸光晕
    bp = t - 0.05
    if bp > 0:
        pulse = 1 + 0.05 * math.sin(bp * 2.4)
        hal = Image.new("RGBA", (W, 900), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hal)
        hd.ellipse((60, 120, W - 60, 820), fill=CREAMY + (70,))
        place(base, hal.filter(ImageFilter.GaussianBlur(90)), 0, 0, fin(bp, 0.6), scale=pulse)

    a = spring((t - 0.05) / 0.7)
    t1 = text_img("文本 · 图片 · 视频", 88, INK, True, 1.20)
    place(base, t1, SAFE_L, 340, clamp(a), dy=26 * (1 - clamp(a)),
          scale=0.94 + 0.06 * clamp(a))

    a2 = spring((t - 0.28) / 0.7)
    t2 = text_img("现在都是 0 元", 104, PEACH, True, 1.20)
    place(base, t2, SAFE_L, 460, clamp(a2), dy=26 * (1 - clamp(a2)),
          scale=0.94 + 0.06 * clamp(a2))

    a3 = fin(t - 0.55, 0.34)
    t3 = text_img("Agnes AI Flash 系列 · 官网当前体验价", 36, INK_S)
    place(base, t3, SAFE_L, 640, a3, dy=14 * (1 - a3))

    # 三颗软糖徽章（Q 弹缩放）
    items = [("文本", "×2"), ("图片", "×3"), ("视频", "720P")]
    cw = (CW - 2 * 26) // 3
    for i, (k, v) in enumerate(items):
        st = 0.75 + i * 0.16
        p = clamp(spring((t - st) / 0.62, freq=2.2, damp=4.2))
        if p <= 0:
            continue
        c, _ = card(cw, 230, CARD, 30)
        cd = ImageDraw.Draw(c)
        cd.ellipse((cw // 2 - 44, 24, cw // 2 + 44, 112), fill=PEACH_S + (255,))
        z = text_img("0", 58, PEACH, True)
        c.alpha_composite(z, (cw // 2 - z.width // 2, 24 + (88 - z.height) // 2))
        tk = text_img(k, 40, INK, True)
        c.alpha_composite(tk, ((cw - tk.width) // 2, 134))
        tv = text_img(v, 26, INK_S)
        c.alpha_composite(tv, ((cw - tv.width) // 2, 186))
        # 挤压回弹
        sq = 1.0 + 0.10 * math.sin(p * 7.5) * (1 - p)
        place(base, c, SAFE_L + i * (cw + 26), 740, p, dy=24 * (1 - p),
              squeeze=sq)

    # 底部柔光带
    lp = fin(t - 1.35, 0.55)
    if lp > 0:
        band = Image.new("RGBA", (CW, 14), (0, 0, 0, 0))
        bd = ImageDraw.Draw(band)
        seg = CW / 3
        for i, c in enumerate((PEACH, CREAMY, MATCHA)):
            bd.rounded_rectangle((i * seg + 4, 0, (i + 1) * seg - 4, 13), 7, fill=c + (255,))
        wipe(base, band, SAFE_L, 1030, lp)


def sc_proof(base, t):
    """兑现：免费 API 官网证据 + 柔光圈强调。"""
    a = spring((t - 0.02) / 0.66)
    t1 = text_img("免费 API", 96, INK, True, 1.18)
    place(base, t1, SAFE_L, 320, clamp(a), dy=28 * (1 - clamp(a)),
          scale=0.92 + 0.08 * clamp(a))

    a2 = fin(t - 0.20, 0.34)
    t2 = text_img("就挂在官网首页", 80, PEACH, True, 1.18)
    place(base, t2, SAFE_L, 460, a2, dy=22 * (1 - a2))

    ev = evid_card("E09-免费访问-额度与限制.png", CW, 380, "官网 · 免费 API 入口", PEACH, 26)
    a3 = soft_out((t - 0.36) / 0.62)
    place(base, ev, SAFE_L, 580, a3, dy=34 * (1 - a3))

    # 柔光圈强调
    lp = t - 1.00
    if lp > 0:
        glow = Image.new("RGBA", (CW, 380), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle((6, 6, CW - 7, 373), 26, outline=CREAMY + (255,), width=8)
        pulse = 1 + 0.03 * math.sin(lp * 3.2)
        place(base, glow, SAFE_L, 580, fin(lp, 0.4), scale=pulse)

    a4 = fin(t - 1.22, 0.32)
    t4 = text_img("不是营销话术，是官网自己的入口", 34, INK_S)
    place(base, t4, SAFE_L, 1000, a4, dy=14 * (1 - a4))


def sc_two_ways(base, t):
    """两种用法：两张软卡左右 Q 弹入场 + 中间柔软连接。"""
    a = spring((t - 0.02) / 0.66)
    t1 = text_img("两种用法", 92, INK, True, 1.20)
    place(base, t1, SAFE_L, 310, clamp(a), dy=24 * (1 - clamp(a)))

    cw = (CW - 44) // 2
    blocks = [
        ("普通用户", "Pavo 网页端", "搜索 · 对话\n创作 · 视频", PEACH, PEACH_S),
        ("开发者", "API 接口", "免费额度试用\n接入自有工具", MATCHA, MATCHA_S),
    ]
    for i, (title, sub, body, ac, sc_) in enumerate(blocks):
        st = 0.20 + i * 0.17
        p = clamp(spring((t - st) / 0.68, freq=2.0, damp=4.0))
        if p <= 0:
            continue
        c, _ = card(cw, 400, CARD, 30)
        cd = ImageDraw.Draw(c)
        badge = chip(title, 32, ac, sc_, pad_x=22, pad_y=11)
        c.alpha_composite(badge, (32, 34))
        t2 = text_img(sub, 44, INK, True)
        c.alpha_composite(t2, (32, 110))
        cd.rounded_rectangle((32, 178, cw - 32, 180), 1, fill=CREAM_D + (255,))
        for j, ln in enumerate(body.split("\n")):
            t3 = text_img(ln, 29, INK_S)
            c.alpha_composite(t3, (32, 210 + j * 46))
        sq = 1.0 + 0.08 * math.sin(p * 7.0) * (1 - p)
        place(base, c, SAFE_L + i * (cw + 44), 470, p, dy=32 * (1 - p), squeeze=sq)

    # 中间柔和的"或"
    sp = t - 0.72
    if sp > 0:
        p = clamp(spring((sp) / 0.5, freq=2.4, damp=4.6))
        dot = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dot)
        dd.ellipse((10, 10, 110, 110), fill=CREAM + (255,))
        o = text_img("或", 40, INK, True)
        dot.alpha_composite(o, (60 - o.width // 2, 60 - o.height // 2))
        place(base, dot, SAFE_L + CW // 2 - 60, 640, p,
              scale=0.85 + 0.15 * p, squeeze=1.0 + 0.12 * math.sin(p * 8) * (1 - p))

    a3 = fin(t - 1.05, 0.32)
    t3 = text_img("不写代码也能用，要接工具才走 API", 34, INK_S)
    place(base, t3, SAFE_L, 960, a3, dy=14 * (1 - a3))


def sc_steps(base, t):
    """开发者五步：竖排软卡依次 Q 弹入场 + 左侧渐变竖线。"""
    a = spring((t - 0.02) / 0.66)
    t1 = text_img("开发者五步", 92, INK, True, 1.20)
    place(base, t1, SAFE_L, 300, clamp(a), dy=24 * (1 - clamp(a)))

    items = ["注册账户", "生成 API Key", "选 agnes-3.0-flash", "填 Base URL", "发第一条请求"]
    row_h = 172
    y0 = 470

    lp = fin(t - 0.42, 1.28)
    if lp > 0:
        line = Image.new("RGBA", (10, row_h * 5 - 44), (0, 0, 0, 0))
        ld = ImageDraw.Draw(line)
        ld.rounded_rectangle((0, 0, 9, int((row_h * 5 - 44) * lp)), 5, fill=PEACH_S + (255,))
        place(base, line, SAFE_L + 28, y0 + 34, 1.0)

    for i, it in enumerate(items):
        st = 0.26 + i * 0.15
        p = clamp(spring((t - st) / 0.56, freq=2.4, damp=4.8))
        if p <= 0:
            continue
        cy = y0 + i * row_h

        dot = Image.new("RGBA", (66, 66), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dot)
        dd.ellipse((3, 3, 63, 63), fill=PEACH + (255,))
        n = text_img(str(i + 1), 30, (255, 255, 255), True)
        dot.alpha_composite(n, (33 - n.width // 2, 33 - n.height // 2))
        place(base, dot, SAFE_L, cy, p, dy=18 * (1 - p), scale=0.5 + 0.5 * p)

        c, _ = card(CW - 130, 112, CARD, 24)
        tb = text_img(it, 38, INK, True)
        c.alpha_composite(tb, (30, (112 - tb.height) // 2))
        place(base, c, SAFE_L + 96, cy - 20, p, dy=18 * (1 - p),
              squeeze=1.0 + 0.08 * math.sin(p * 7) * (1 - p))


def sc_code(base, t):
    """三行参数：Base URL 证据 + 代码卡 + 光标柔和闪烁。"""
    a = spring((t - 0.02) / 0.66)
    t1 = text_img("三行就能发出去", 84, INK, True, 1.20)
    place(base, t1, SAFE_L, 300, clamp(a), dy=22 * (1 - clamp(a)))

    ev = evid_card("E06-快速开始-BaseURL.png", CW, 200, "官方快速开始", MATCHA, 24)
    a2 = soft_out((t - 0.18) / 0.6)
    place(base, ev, SAFE_L, 420, a2, dy=28 * (1 - a2))

    lines = [
        ("model:", "agnes-3.0-flash"),
        ("base:", "api.agnes-ai.cn/v1"),
        ("auth:", "Bearer YOUR_API_KEY"),
    ]
    code_y = 680
    card_h = 58 * len(lines) + 46
    c, _ = card(CW, card_h, CARD, 26)
    cd = ImageDraw.Draw(c)
    cd.rounded_rectangle((0, 0, 10, card_h - 1), 5, fill=PEACH + (255,))
    place(base, c, SAFE_L, code_y, fin(t - 0.36, 0.4), dy=24 * (1 - fin(t - 0.36, 0.4)))
    for i, (k, v) in enumerate(lines):
        st = 0.52 + i * 0.19
        p = fin(t - st, 0.32)
        if p <= 0:
            continue
        kt = text_img(k, 31, INK_S)
        vt = text_img(v, 31, PEACH if i == 0 else INK, i == 0)
        row = Image.new("RGBA", (CW - 60, 42), (0, 0, 0, 0))
        row.alpha_composite(kt, (0, 0))
        row.alpha_composite(vt, (kt.width + 16, 0))
        wipe(base, row, SAFE_L + 30, code_y + 26 + i * 58, p)

    cb = t - 1.22
    if cb > 0 and int(cb * 2.4) % 2 == 0:
        cur = Image.new("RGBA", (7, 34), (0, 0, 0, 0))
        ImageDraw.Draw(cur).rounded_rectangle((0, 0, 6, 33), 3, fill=PEACH + (255,))
        place(base, cur, SAFE_L + 34 + 210, code_y + 26 + 2 * 58 + 4, 1.0)

    tag = chip("复制即用", 28, MATCHA, MATCHA_S)
    a3 = spring((t - 1.40) / 0.58)
    place(base, tag, SAFE_L, code_y + card_h + 28, clamp(a3), dy=18 * (1 - clamp(a3)),
          scale=0.92 + 0.08 * clamp(a3))


def sc_free_range(base, t):
    """免费范围：三张高清证据图直接铺满，卡片只做标签条。

    证据图高度给到 150px 才能读清小字，之前缩到 116px 仍偏小。
    """
    a = spring((t - 0.02) / 0.66)
    t1 = text_img("哪些真的免费", 88, INK, True, 1.20)
    place(base, t1, SAFE_L, 270, clamp(a), dy=22 * (1 - clamp(a)))

    rows = [
        ("E03-文本Flash-体验价全0", "文本 Flash ×2", "输入 / 输出全 0", MATCHA),
        ("E04-图片Flash-各分辨率全0", "图片 Flash ×3", "各分辨率全 0", PEACH),
        ("E01-视频Flash-0元每秒", "视频 Flash 720P", "时长 0 元 / 秒", CARAMEL),
    ]
    for i, (ev_name, k, v, ac) in enumerate(rows):
        st = 0.22 + i * 0.17
        p = clamp(spring((t - st) / 0.58, freq=2.2, damp=4.4))
        if p <= 0:
            continue
        cy = 400 + i * 246
        c, _ = card(CW, 222, CARD, 26)
        cd = ImageDraw.Draw(c)
        cd.rounded_rectangle((0, 0, 9, 221), 5, fill=ac + (255,))
        # 标题行
        tk = text_img(k, 38, INK, True)
        c.alpha_composite(tk, (28, 16))
        tv = text_img(v, 26, INK_S)
        c.alpha_composite(tv, (28 + tk.width + 18, 24))
        # 证据图铺满剩余高度（150px，小字才读得清）
        ev = Image.open(evidence_path(ev_name, prefer_light=True)).convert("RGB")
        r = min((CW - 56) / ev.width, 150 / ev.height)
        ev = ev.resize((max(1, int(ev.width * r)), max(1, int(ev.height * r))), Image.LANCZOS)
        ev = ImageEnhance.Brightness(ev).enhance(1.04)
        c.alpha_composite(ev.convert("RGBA"), (28, 60))
        # 右侧软标
        lp = clamp(spring((t - st - 0.24) / 0.5, freq=2.6, damp=4.8))
        if lp > 0:
            tag = chip("¥0", 36, MATCHA, MATCHA_S, pad_x=20, pad_y=9)
            c.alpha_composite(tag, (CW - tag.width - 26, 22))
        place(base, c, SAFE_L, cy, p, dy=26 * (1 - p),
              squeeze=1.0 + 0.06 * math.sin(p * 7) * (1 - p))


def sc_zero(base, t):
    """0 元证据：高清证据图 + 刊例价划线 + 大字 ¥0。"""
    a = spring((t - 0.02) / 0.66)
    t1 = text_img("视频 Flash 720P", 74, INK, True, 1.20)
    place(base, t1, SAFE_L, 290, clamp(a), dy=20 * (1 - clamp(a)))

    # 刊例价 → 划掉
    a2 = fin(t - 0.26, 0.32)
    old = text_img("刊例价 ¥0.15 / 秒", 42, INK_S, True)
    place(base, old, SAFE_L, 390, a2)
    sp = fin(t - 0.58, 0.4)
    if sp > 0:
        strike = Image.new("RGBA", (old.width + 10, 6), (0, 0, 0, 0))
        ImageDraw.Draw(strike).rounded_rectangle((0, 0, old.width + 10, 5), 3,
                                                 fill=ROSE + (255,))
        wipe(base, strike, SAFE_L, 390 + old.height // 2, sp)

    # 体验价大字（数字滚动）
    a3 = fin(t - 0.68, 0.32)
    lab = text_img("当前体验价", 32, INK_S, True)
    place(base, lab, SAFE_L, 470, a3)

    rp = clamp((t - 0.78) / 1.0)
    val = 0.15 * (1 - soft_out(rp))
    num_s = "¥0" if rp >= 0.999 else f"¥{val:.3f}"
    num = text_img(num_s, 132, PEACH, True)
    place(base, num, SAFE_L, 520, a3)
    unit = text_img("/ 秒", 46, INK, True)
    place(base, unit, SAFE_L + num.width + 14, 520 + 96, a3)

    # 高清证据图（这张是重截的 2x，文字清楚）
    ev = evid_card("E01-视频Flash-0元每秒.png", CW, 165, "官网定价页", MATCHA, 24)
    a4 = soft_out((t - 1.00) / 0.6)
    place(base, ev, SAFE_L, 710, a4, dy=26 * (1 - a4))

    # 柔光圈强调 ¥0
    lp = t - 1.40
    if lp > 0:
        glow = Image.new("RGBA", (CW, 165), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle((6, 6, CW - 7, 158), 24, outline=CREAMY + (255,), width=8)
        pulse = 1 + 0.03 * math.sin(lp * 3.4)
        place(base, glow, SAFE_L, 710, fin(lp, 0.4), scale=pulse)

    a5 = fin(t - 1.58, 0.3)
    t5 = text_img("agnes-video-2.5-flash · 官网当前显示", 32, INK_S)
    place(base, t5, SAFE_L, 920, a5, dy=14 * (1 - a5))


def sc_limits(base, t):
    """三条限制：暖警示软卡 + 玫瑰色强调。"""
    a = spring((t - 0.02) / 0.66)
    t1 = text_img("但有三条限制", 88, ROSE, True, 1.20)
    place(base, t1, SAFE_L, 290, clamp(a), dy=22 * (1 - clamp(a)))

    rows = [
        "阶段性优惠，不是永久免费",
        "有 TPS 和公平使用配额",
        "Agent Plan 按刊例价折算 Credits",
    ]
    for i, txt in enumerate(rows):
        st = 0.24 + i * 0.18
        p = clamp(spring((t - st) / 0.58, freq=2.2, damp=4.4))
        if p <= 0:
            continue
        cy = 430 + i * 172
        c, _ = card(CW, 138, ROSE_S, 26)
        cd = ImageDraw.Draw(c)
        cd.ellipse((28, 40, 90, 102), fill=ROSE + (255,))
        ex = text_img("!", 40, (255, 255, 255), True)
        c.alpha_composite(ex, (59 - ex.width // 2, 71 - ex.height // 2))
        tb = text_img(txt, 35, INK, True)
        c.alpha_composite(tb, (114, 50))
        place(base, c, SAFE_L, cy, p, dy=24 * (1 - p),
              squeeze=1.0 + 0.06 * math.sin(p * 7) * (1 - p))

    a2 = fin(t - 1.20, 0.3)
    t2 = text_img("最终以平台公告和你的账户账单为准", 32, INK_S)
    place(base, t2, SAFE_L, 990, a2, dy=14 * (1 - a2))


def sc_end(base, t):
    """收尾：柔光大问句 + 丝带飘落 + 关注按钮。"""
    # 丝带
    for i in range(9):
        st = 0.05 + i * 0.07
        p = clamp((t - st) / 3.0)
        if p <= 0:
            continue
        x = 60 + (i * 121) % (W - 120)
        y = -30 + p * (H + 80)
        sway = math.sin(t * 1.6 + i) * 22
        rb = Image.new("RGBA", (18, 42), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rb)
        rd.rounded_rectangle((0, 0, 17, 41), 8,
                             fill=(PEACH, CREAMY, MATCHA, ROSE)[i % 4] + (210,))
        place(base, rb, x + sway, y, 0.9 - p * 0.45, angle=math.sin(t * 2 + i) * 22)

    a = spring((t - 0.05) / 0.62)
    t1 = text_img("你最想白嫖哪个？", 92, INK, True, 1.18)
    place(base, t1, SAFE_L, 470, clamp(a), dy=26 * (1 - clamp(a)),
          scale=0.92 + 0.08 * clamp(a))

    a2 = fin(t - 0.26, 0.32)
    t2 = text_img("评论区告诉我，我下期实测", 44, PEACH, True)
    place(base, t2, SAFE_L, 620, a2, dy=18 * (1 - a2))

    lp = fin(t - 0.40, 0.42)
    if lp > 0:
        ul = Image.new("RGBA", (CW, 12), (0, 0, 0, 0))
        ImageDraw.Draw(ul).rounded_rectangle((0, 0, CW, 11), 6, fill=CREAMY + (255,))
        wipe(base, ul, SAFE_L, 720, lp)

    a3 = fin(t - 0.56, 0.3)
    t3 = text_img("科技不高冷，AI 很好用 · 我是晚枫", 34, INK_S)
    place(base, t3, SAFE_L, 790, a3, dy=14 * (1 - a3))

    pa = t - 0.80
    if pa > 0:
        pulse = 1 + 0.04 * math.sin(pa * 4.2)
        btn, _ = card(500, 92, PEACH, 28)
        bt = text_img("关注我 · 只讲真能白嫖的", 33, (255, 255, 255), True)
        btn.alpha_composite(bt, ((500 - bt.width) // 2, 30))
        place(base, btn, SAFE_L, 880, fin(pa, 0.38), scale=pulse)


SCENES = [
    (0.00, 3.20, sc_hook),
    (3.46, 3.24, sc_proof),
    (6.96, 3.24, sc_two_ways),
    (10.46, 2.54, sc_steps),
    (13.26, 3.24, sc_code),
    (16.76, 1.84, sc_free_range),
    (18.86, 2.24, sc_zero),
    (21.36, 2.24, sc_limits),
    (23.76, 1.04, sc_end),
]


def render_frame(t):
    GUARD.reset()
    base = glow_bg().copy()
    for start, dur, fn in SCENES:
        if not (start <= t < start + dur):
            continue
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(layer, t - start)
        shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shifted.alpha_composite(layer, (0, YOFF[0]))
        # 出场先淡完（0.26s），入场再起（0.26s），两者不重叠，避免文字重影
        a = fin(t - start, 0.26)
        if t > start + dur - 0.26:
            a *= fout(t - (start + dur - 0.26), 0.26)
        if a < 0.999:
            shifted.putalpha(shifted.getchannel("A").point([int(i * a) for i in range(256)]))
        base.alpha_composite(shifted)
    top_bar(base, t / TOTAL)
    # --- mgkit: overlap check ---
    GUARD.check(f"t={t:.2f}")
    # --- end mgkit ---
    return base.convert("RGB")


def make_contact():
    marks = [0.6, 1.4, 2.4, 3.2, 4.2, 5.6, 7.8, 9.4, 11.2, 12.8, 14.2, 15.6,
             17.2, 19.0, 20.2, 21.8, 23.0, 24.2]
    cw, ch = 240, 427
    cols = 6
    rows = (len(marks) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, ch * rows), (246, 233, 219))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧F-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 28), fill=(74, 51, 40))
        td.text((8, 3), f"{t:.1f}s", font=font(18, True), fill=(253, 246, 238))
        sheet.paste(thumb, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(HERE / "检查图-MG样片F.png")
    write_report(GUARD, HERE, "F 暖色治愈")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片F.png")
    print("--- mgkit 重叠检测 ---")
    print(GUARD.report())
    (HERE / "重叠检测报告.txt").write_text(
        GUARD.report() + "\n\n=== 全部明细 ===\n" + "\n".join(GUARD.errors),
        encoding="utf-8")


def main():
    preview = "--preview" in sys.argv
    make_contact()
    if preview:
        print("--preview，仅生成关键帧检查图")
        return
    out = HERE / "MG-样片F-暖色治愈-无声.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
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
