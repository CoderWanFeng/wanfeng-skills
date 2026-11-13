#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes AI 免费使用 · MG 样片 B（亮色杂志风 + 丰富动效）

与样片 A（深色科技风）的差异：
- 配色：米白底 + 靛蓝主色 + 柠檬黄/薄荷绿点缀，亮色杂志感
- 动效：弹性回弹、旋转滑入、遮罩擦除、数字滚动、连线生长、划线删除、光标闪烁

用法：
    python build_mg_bright.py --preview   # 只出关键帧检查图
    python build_mg_bright.py             # 渲染无声 MP4
"""
from __future__ import annotations

import math
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
                   set_content_offset, write_report, load_evidence_or_raw,
                   SHOTS_DIR, EVID_DIR)

GUARD = OverlapGuard(1080, 1920, text_thresh=0.015,
                     safe_top=0, safe_bottom=0,
                     safe_left=84, safe_right=150)

SHOTS = SHOTS_DIR  # 由 mgkit.paths 解析（MG_SHOTS_DIR 可覆盖）
EVID = EVID_DIR    # 由 mgkit.paths 解析（MG_EVID_DIR 可覆盖）

W, H = 1080, 1920

# 亮色杂志版用正体：腾讯 Sans 是动态斜体（适合深色科技风，不适合亮色杂志感）
F7 = "/System/Library/Fonts/Hiragino Sans GB.ttc"   # index=2 → W6 粗体
F3 = "/System/Library/Fonts/Hiragino Sans GB.ttc"   # index=0 → W3 常规
F7_IDX, F3_IDX = 2, 0

# ---- 亮色杂志色卡 ----
BG = (247, 245, 240)       # 米白底
CARD = (255, 255, 255)     # 卡片白
INK = (26, 26, 31)         # 主墨色
MUTED = (132, 129, 122)    # 次要文本
LINE = (228, 224, 216)     # 描边
INDIGO = (79, 70, 229)     # 主色 靛蓝
INDIGO_S = (233, 231, 253)  # 靛蓝浅底
GREEN = (16, 185, 129)     # 免费 薄荷绿
GREEN_S = (214, 244, 235)
YELLOW = (250, 204, 21)    # 点缀 柠檬黄
YELLOW_S = (254, 244, 200)
CORAL = (255, 107, 74)     # 警示 珊瑚橙
CORAL_S = (254, 231, 225)

SAFE_L = 84
SAFE_R = W - 150
CW = SAFE_R - SAFE_L

# 整体内容重心：竖屏下半段要留给平台 UI，正文往下压
YOFF = [210]

TOTAL = 24.6
NFRAMES = round(TOTAL * FPS)


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


def back_out(x, s=1.9):
    """带回弹的 ease-out，元素入场用。"""
    x = clamp(x)
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def soft_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 4


def fin(t, dur=0.30):
    return ease_out(t / dur)


def fout(t, dur=0.22):
    return ease_in(t / dur)


@lru_cache(maxsize=512)
def text_img(s, size, color, bold=False, spacing=1.28):
    f = font(size, bold)
    lines = s.split("\n")
    ws, tops = [], []
    for ln in lines:
        bb = f.getbbox(ln)
        ws.append(bb[2] - bb[0])
        tops.append(bb[1])
    step = int(size * spacing)
    im = Image.new("RGBA", (max(ws) + 18, step * len(lines) + 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((9, i * step + 7 - tops[i]), ln, font=f, fill=color + (255,))
    return mark_text_layer(im, s.replace(chr(10), ' / '))


def card_img(w, h, radius=26, fill=CARD, border=LINE, bw=2):
    """不缓存：调用方会在卡面上绘制内容，共享对象会导致串字。"""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius,
                                         fill=fill + (255,), outline=border + (255,), width=bw)
    return im


@lru_cache(maxsize=256)
def _shadow_layer(w, h, radius, blur, alpha):
    """只缓存阴影部分。阴影本身不会被改写，可以安全缓存。"""
    pad = blur * 2
    sh = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w - 1, pad + h - 1 + 10),
                                         radius, fill=(20, 20, 30, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur)), pad


def shadow_card(w, h, radius=26, fill=CARD, border=LINE, bw=2, blur=18, alpha=34):
    """带柔和投影的卡片。

    每次返回全新对象：调用方会在卡片上绘制文字，
    若共享缓存会导致多张卡片的文字叠在一起。
    """
    sh, pad = _shadow_layer(w, h, radius, blur, alpha)
    im = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    im.alpha_composite(sh)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), radius,
                                        fill=fill + (255,), outline=border + (255,), width=bw)
    im.alpha_composite(c, (pad, pad))
    return im, pad


@lru_cache(maxsize=256)
def chip_img(s, size, fg, fill, radius=None, pad_x=24, pad_y=12):
    t = text_img(s, size, fg, True)
    w, h = t.width + pad_x * 2, t.height + pad_y * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius or h // 2,
                                         fill=fill + (255,))
    im.alpha_composite(t, (pad_x, pad_y))
    return im


@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 brightness=0.97, prefer_light=True)
    return im


@lru_cache(maxsize=64)
def shot_card(name, box, w, h, label=None, accent=INDIGO):
    """白底网页截图：套浏览器窗口 + 深色描边，避免和米白底融掉。"""
    bar_h = 38
    layer, pad = shadow_card(w, h, 22, (252, 251, 249), LINE, 2, blur=16, alpha=30)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((pad, pad, pad + w - 1, pad + h - 1), 22,
                        fill=(252, 251, 249, 255), outline=LINE + (255,), width=2)
    d.rectangle((pad, pad + bar_h, pad + w - 1, pad + bar_h + 1), fill=LINE + (255,))
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((pad + 16 + i * 19, pad + 14, pad + 27 + i * 19, pad + 25), fill=c + (255,))
    if label:
        t = text_img(label, 23, MUTED, True)
        layer.alpha_composite(t, (pad + 88, pad + 7))
    ip = 10
    src = load_shot(name, box, w - 2 * ip, h - bar_h - 2 * ip)
    layer.alpha_composite(src, (pad + ip + (w - 2 * ip - src.width) // 2,
                                pad + bar_h + ip + (h - bar_h - 2 * ip - src.height) // 2))
    return layer


def place(base, layer, x, y, a=1.0, dy=0, scale=1.0, angle=0.0):
    """带 alpha / 位移 / 缩放 / 旋转的合成。"""
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


def wipe(base, layer, x, y, p, axis="x"):
    """遮罩擦除：按进度裁切后合成，用于文字逐行显现、线条生长。"""
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


def roll_number(value, p, fmt="{:.2f}"):
    """数字滚动：p=0 显示初值，p=1 显示终值。"""
    return fmt(value)


# ---------------------------------------------------------------- 背景装饰
def draw_bg(base):
    """米白底 + 柔和色块，杂志感但不抢文字。"""
    d = ImageDraw.Draw(base)
    d.rectangle((0, 0, W, H), fill=BG + (255,))
    blobs = [
        ((-120, 150, 420), YELLOW_S, 70),
        ((760, 1180, 1320), GREEN_S, 76),
        ((-160, 1560, 260), INDIGO_S, 62),
    ]
    for (cx, cy, r), col, a in blobs:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (a,))
        base.alpha_composite(ov)


def top_bar(base, p, label="AGNES AI · 免费使用"):
    """顶部：标签 + 进度条 + 步骤序号。"""
    tag = chip_img(label, 25, INDIGO, INDIGO_S, radius=h2r(25))
    place(base, tag, SAFE_L, 70, 1.0)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((SAFE_L, 142, SAFE_R, 150), 4, fill=LINE + (255,))
    if p > 0:
        d.rounded_rectangle((SAFE_L, 142, SAFE_L + int(CW * p), 150), 4, fill=INDIGO + (255,))
    pct = text_img(f"{int(p*100)}%", 26, MUTED, True)
    place(base, pct, SAFE_R - pct.width, 60, 1.0)


def h2r(size):
    return size + 24


# ---------------------------------------------------------------- 场景
def sc_hook(base, t):
    """钩子：标题回弹入场 + 三个 0 元卡片依次飞入 + 底部长条生长。"""
    d = ImageDraw.Draw(base)

    a1 = back_out((t - 0.10) / 0.55)
    t1 = text_img("文本 · 图片 · 视频", 96, INK, True)
    place(base, t1, SAFE_L, 380, a1, dy=54 * (1 - a1))

    a2 = back_out((t - 0.32) / 0.55)
    t2 = text_img("现在都是 0 元", 96, GREEN, True)
    place(base, t2, SAFE_L, 520, a2, dy=54 * (1 - a2))

    a3 = fin(t - 0.56, 0.32)
    t3 = text_img("Agnes AI Flash 系列 · 官网当前体验价", 38, MUTED)
    place(base, t3, SAFE_L, 680, a3, dy=18 * (1 - a3))

    # 三个 0 元卡片，依次带旋转滑入
    items = [("文本", "Flash ×2"), ("图片", "Flash ×3"), ("视频", "720P")]
    cw = (CW - 2 * 24) // 3
    for i, (a_, b_) in enumerate(items):
        st = 0.72 + i * 0.13
        p = back_out((t - st) / 0.55)
        if p <= 0:
            continue
        c, _ = shadow_card(cw, 250, 24, CARD, LINE, 2, blur=14, alpha=30)
        cd = ImageDraw.Draw(c)
        cd.rounded_rectangle((24, 24, 24 + 58, 82), 16, fill=GREEN_S + (255,))
        zero = text_img("0", 46, GREEN, True)
        c.alpha_composite(zero, (24 + (58 - zero.width) // 2, 24 + (58 - zero.height) // 2))
        ta = text_img(a_, 40, INK, True)
        c.alpha_composite(ta, (24, 108))
        tb = text_img(b_, 28, MUTED)
        c.alpha_composite(tb, (24, 168))
        place(base, c, SAFE_L + i * (cw + 24), 790, p, dy=40 * (1 - p), angle=-4 * (1 - p))

    # 底部彩色长条生长
    p = fin(t - 1.20, 0.50)
    if p > 0:
        bar = Image.new("RGBA", (CW, 12), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bar)
        seg = CW / 3
        for i, c in enumerate((GREEN, YELLOW, INDIGO)):
            bd.rounded_rectangle((i * seg + 3, 0, (i + 1) * seg - 3, 11), 6, fill=c + (255,))
        wipe(base, bar, SAFE_L, 1130, p)


def sc_proof(base, t):
    """兑现：标题左滑入 + 浏览器窗口右滑入 + 高亮框呼吸。"""
    a = back_out((t - 0.02) / 0.5)
    t1 = text_img("免费 API", 92, INK, True)
    place(base, t1, SAFE_L, 330, a, dy=40 * (1 - a), scale=0.9 + 0.1 * a)

    a2 = back_out((t - 0.22) / 0.5)
    t2 = text_img("就挂在官网首页", 92, INDIGO, True)
    place(base, t2, SAFE_L, 460, a2, dy=40 * (1 - a2), scale=0.9 + 0.1 * a2)

    # 浏览器窗口从右侧推入
    shot = shot_card("01-官网首页-免费API与多模态.jpg", (300, 155, 1000, 262),
                     CW, 210, "官网首屏")
    a3 = soft_out((t - 0.42) / 0.6)
    place(base, shot, SAFE_L, 640, a3, dy=60 * (1 - a3), angle=3 * (1 - a3))

    # 高亮框呼吸脉冲 + 指示线
    pa = t - 1.15
    if pa > 0:
        pulse = 1 + 0.06 * math.sin(pa * 5.2)
        hl = Image.new("RGBA", (CW, 210), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hl)
        hd.rounded_rectangle((4, 4, CW - 5, 205), 20, outline=GREEN + (255,), width=6)
        place(base, hl, SAFE_L, 640, fin(pa, 0.3), scale=pulse)

    a4 = fin(t - 1.32, 0.35)
    t4 = text_img("不是营销话术，是官网自己的入口", 38, MUTED)
    place(base, t4, SAFE_L, 900, a4, dy=16 * (1 - a4))

    chip = chip_img("免费 API 入口", 30, GREEN, GREEN_S)
    a5 = back_out((t - 1.50) / 0.5)
    place(base, chip, SAFE_L, 990, a5, dy=26 * (1 - a5), scale=0.9 + 0.1 * a5)


def sc_two_ways(base, t):
    """两种用法：左右卡片带旋转翻入 + 中间圆点脉冲 + 下方说明。"""
    a = back_out((t - 0.02) / 0.5)
    t1 = text_img("两种用法", 88, INK, True)
    place(base, t1, SAFE_L, 300, a, dy=36 * (1 - a))

    cw = (CW - 40) // 2
    blocks = [
        ("普通用户", "Pavo 网页端", "搜索 · 对话\n创作 · 视频", GREEN, GREEN_S, -7),
        ("开发者", "API 接口", "免费额度试用\n接入自有工具", INDIGO, INDIGO_S, 7),
    ]
    for i, (title, sub, body, ac, sc_, ang) in enumerate(blocks):
        st = 0.22 + i * 0.16
        p = back_out((t - st) / 0.55)
        if p <= 0:
            continue
        c, _ = shadow_card(cw, 400, 26, CARD, LINE, 2, blur=16, alpha=30)
        cd = ImageDraw.Draw(c)
        cd.rounded_rectangle((0, 0, cw - 1, 399), 26, fill=CARD + (255,))
        cd.rounded_rectangle((0, 0, 10, 399), 5, fill=ac + (255,))
        badge = chip_img(title, 32, ac, sc_)
        c.alpha_composite(badge, (36, 40))
        t2 = text_img(sub, 46, INK, True)
        c.alpha_composite(t2, (36, 122))
        for j, ln in enumerate(body.split("\n")):
            t3 = text_img(ln, 30, MUTED)
            c.alpha_composite(t3, (36, 212 + j * 46))
        place(base, c, SAFE_L + i * (cw + 40), 470, p,
              dy=50 * (1 - p), angle=ang * (1 - p))

    # 中间“或”
    pa = t - 0.75
    if pa > 0:
        r = 34 + 4 * math.sin(pa * 6)
        dot = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dot)
        dd.ellipse((12, 12, 98, 98), fill=BG + (255,), outline=INK + (255,), width=3)
        o = text_img("或", 36, INK, True)
        dot.alpha_composite(o, (55 - o.width // 2, 55 - o.height // 2))
        place(base, dot, SAFE_L + CW // 2 - 55, 640, fin(pa, 0.3), scale=r / 38)

    a3 = fin(t - 1.05, 0.35)
    t3 = text_img("不写代码也能用，要接工具才走 API", 38, MUTED)
    place(base, t3, SAFE_L, 960, a3, dy=16 * (1 - a3))


def sc_steps(base, t):
    """开发者五步：竖排卡片依次弹入 + 左侧竖线自上而下生长。

    竖排而不是横排：5 个横排在 1080 宽里文字必然挤在一起。
    """
    a = back_out((t - 0.02) / 0.5)
    t1 = text_img("开发者五步", 88, INK, True)
    place(base, t1, SAFE_L, 300, a, dy=36 * (1 - a))

    items = ["注册账户", "生成 API Key", "选 agnes-3.0-flash", "填 Base URL", "发第一条请求"]
    n = len(items)
    row_h = 176
    y0 = 470

    # 左侧竖线生长
    lp = fin(t - 0.42, 1.30)
    if lp > 0:
        line = Image.new("RGBA", (6, row_h * n - 40), (0, 0, 0, 0))
        ImageDraw.Draw(line).rounded_rectangle((0, 0, 5, int((row_h * n - 40) * lp)), 3,
                                                 fill=INDIGO_S + (255,))
        place(base, line, SAFE_L + 32, y0 + 30, 1.0)

    for i, it in enumerate(items):
        st = 0.28 + i * 0.16
        p = back_out((t - st) / 0.45)
        if p <= 0:
            continue
        cy = y0 + i * row_h
        ring = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        rd.ellipse((4, 4, 68, 68), fill=INDIGO + (255,))
        num = text_img(str(i + 1), 30, (255, 255, 255), True)
        ring.alpha_composite(num, (36 - num.width // 2, 36 - num.height // 2))
        place(base, ring, SAFE_L, cy, p, dy=26 * (1 - p), scale=0.5 + 0.5 * p)

        c, _ = shadow_card(CW - 130, 116, 20, CARD, LINE, 2, blur=12, alpha=26)
        tb = text_img(it, 40, INK, True)
        c.alpha_composite(tb, (30, (116 - tb.height) // 2))
        place(base, c, SAFE_L + 100, cy - 22, p, dy=22 * (1 - p), angle=1.6 * (1 - p))


def sc_code(base, t):
    """三行代码：文档窗口上推 + 代码逐行擦除显现 + 光标闪烁 + 底部 chip 弹入。"""
    a = back_out((t - 0.02) / 0.5)
    t1 = text_img("三行就能发出去", 84, INK, True)
    place(base, t1, SAFE_L, 300, a, dy=36 * (1 - a))

    shot = shot_card("03-快速开始-注册Key与首次请求.jpg", (0, 150, 1396, 1420),
                     CW, 400, "官方快速开始")
    a2 = soft_out((t - 0.20) / 0.6)
    place(base, shot, SAFE_L, 450, a2, dy=70 * (1 - a2))

    lines = [
        ("model:", "agnes-3.0-flash", INDIGO),
        ("base:", "api.agnes-ai.cn/v1", INK),
        ("auth:", "Bearer YOUR_API_KEY", INK),
    ]
    code_y = 940
    card_h = 60 * len(lines) + 46
    # 亮色版统一：代码卡用靛蓝浅底 + 靛蓝描边，不再用深色块
    cc, _ = shadow_card(CW, card_h, 22, INDIGO_S, (208, 203, 250), 2, blur=14, alpha=22)
    cp = fin(t - 0.34, 0.4)
    place(base, cc, SAFE_L, code_y, cp, dy=40 * (1 - cp))
    for i, (k, v, col) in enumerate(lines):
        st = 0.52 + i * 0.20
        p = fin(t - st, 0.32)
        if p <= 0:
            continue
        kt = text_img(k, 31, MUTED)
        vt = text_img(v, 31, col, i == 0)
        row = Image.new("RGBA", (CW - 56, 44), (0, 0, 0, 0))
        row.alpha_composite(kt, (0, 0))
        row.alpha_composite(vt, (kt.width + 16, 0))
        wipe(base, row, SAFE_L + 28, code_y + 24 + i * 60, p)

    # 光标闪烁
    cb = t - 1.25
    if cb > 0 and int(cb * 3) % 2 == 0:
        cur = Image.new("RGBA", (6, 34), (0, 0, 0, 0))
        ImageDraw.Draw(cur).rectangle((0, 0, 5, 33), fill=INDIGO + (255,))
        place(base, cur, SAFE_L + 30 + 210, code_y + 24 + 2 * 60 + 5, 1.0)

    chip = chip_img("复制即用", 30, GREEN, GREEN_S)
    a3 = back_out((t - 1.42) / 0.5)
    place(base, chip, SAFE_L, code_y + card_h + 34, a3, dy=24 * (1 - a3), scale=0.9 + 0.1 * a3)


def sc_free_range(base, t):
    """免费范围：三行卡片右滑入 + 每行 0 元标签弹性弹出 + 勾选填充。"""
    a = back_out((t - 0.02) / 0.5)
    t1 = text_img("哪些真的免费", 88, INK, True)
    place(base, t1, SAFE_L, 300, a, dy=36 * (1 - a))

    rows = [
        ("文本 Flash ×2", "输入 / 输出全 0"),
        ("图片 Flash ×3", "各分辨率全 0"),
        ("视频 Flash 720P", "时长 0 元 / 秒"),
    ]
    for i, (k, v) in enumerate(rows):
        st = 0.24 + i * 0.17
        p = back_out((t - st) / 0.5)
        if p <= 0:
            continue
        c, _ = shadow_card(CW, 150, 22, CARD, LINE, 2, blur=14, alpha=28)
        cd = ImageDraw.Draw(c)
        # 勾选圆圈填充
        fillp = clamp((t - st - 0.20) / 0.35)
        cd.ellipse((30, 45, 90, 105), fill=GREEN_S + (255,))
        if fillp > 0:
            ck = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
            kd = ImageDraw.Draw(ck)
            kd.ellipse((0, 0, 60, 60), fill=GREEN + (255,))
            kd.line((16, 31, 26, 43), fill=(255, 255, 255, 255), width=6)
            kd.line((26, 43, 45, 20), fill=(255, 255, 255, 255), width=6)
            c.alpha_composite(ck, (30, 45), )
        tk = text_img(k, 40, INK, True)
        c.alpha_composite(tk, (114, 34))
        tv = text_img(v, 28, MUTED)
        c.alpha_composite(tv, (114, 92))
        # 右侧 0 元标签
        lp = back_out((t - st - 0.28) / 0.45)
        if lp > 0:
            tag = chip_img("¥0", 34, GREEN, GREEN_S, radius=18)
            c.alpha_composite(tag, (CW - tag.width - 30, 55))
        place(base, c, SAFE_L, 470 + i * 175, p, dy=44 * (1 - p), angle=2.5 * (1 - p))


def sc_zero(base, t):
    """0 元证据：刊例价划线删除 + 体验价数字滚动 + 定价页截图。"""
    a = back_out((t - 0.02) / 0.5)
    t1 = text_img("视频 Flash 720P", 76, INK, True)
    place(base, t1, SAFE_L, 290, a, dy=34 * (1 - a))

    # 刊例价 → 划线删除
    a2 = fin(t - 0.28, 0.35)
    old = text_img("刊例价 ¥0.15 / 秒", 44, MUTED, True)
    place(base, old, SAFE_L, 400, a2)
    sp = fin(t - 0.60, 0.4)
    if sp > 0:
        strike = Image.new("RGBA", (old.width + 10, 5), (0, 0, 0, 0))
        ImageDraw.Draw(strike).rectangle((0, 0, old.width + 10, 4), fill=CORAL + (255,))
        wipe(base, strike, SAFE_L, 400 + old.height // 2, sp)

    # 体验价：数字从 0.15 滚到 0
    a3 = fin(t - 0.75, 0.35)
    lab = text_img("当前体验价", 34, MUTED, True)
    place(base, lab, SAFE_L, 500, a3)

    rp = clamp((t - 0.85) / 1.0)
    val = 0.15 * (1 - ease_out(rp))
    if rp >= 0.999:
        num_s = "¥0"
    else:
        num_s = f"¥{val:.3f}"
    num = text_img(num_s, 132, GREEN, True)
    place(base, num, SAFE_L, 560, a3)
    unit = text_img("/ 秒", 46, INK, True)
    place(base, unit, SAFE_L + num.width + 16, 560 + 96, a3)

    # 定价页真实截图
    shot = shot_card("07-模型定价-视频Flash限时免费.jpg", (0, 700, 1396, 822),
                     CW, 150, "官网定价页")
    a4 = soft_out((t - 1.05) / 0.6)
    place(base, shot, SAFE_L, 740, a4, dy=50 * (1 - a4))

    # 证据高亮框呼吸
    pa = t - 1.45
    if pa > 0:
        pulse = 1 + 0.04 * math.sin(pa * 5.6)
        hl = Image.new("RGBA", (CW, 150), (0, 0, 0, 0))
        ImageDraw.Draw(hl).rounded_rectangle((4, 4, CW - 5, 146), 20,
                                             outline=GREEN + (255,), width=6)
        place(base, hl, SAFE_L, 740, fin(pa, 0.3), scale=pulse)

    a5 = fin(t - 1.60, 0.35)
    t5 = text_img("agnes-video-2.5-flash · 官网当前显示", 34, MUTED)
    place(base, t5, SAFE_L, 950, a5, dy=16 * (1 - a5))


def sc_limits(base, t):
    """三条限制：珊瑚橙警示条依次弹入 + 感叹号图标。"""
    a = back_out((t - 0.02) / 0.5)
    t1 = text_img("但有三条限制", 88, CORAL, True)
    place(base, t1, SAFE_L, 300, a, dy=36 * (1 - a))

    rows = [
        "阶段性优惠，不是永久免费",
        "有 TPS 和公平使用配额",
        "Agent Plan 按刊例价折算 Credits",
    ]
    for i, txt in enumerate(rows):
        st = 0.26 + i * 0.19
        p = back_out((t - st) / 0.5)
        if p <= 0:
            continue
        c, _ = shadow_card(CW, 140, 22, CORAL_S, (250, 214, 205), 2, blur=12, alpha=22)
        cd = ImageDraw.Draw(c)
        cd.ellipse((30, 42, 88, 100), fill=CORAL + (255,))
        ex = text_img("!", 40, (255, 255, 255), True)
        c.alpha_composite(ex, (59 - ex.width // 2, 71 - ex.height // 2))
        tb = text_img(txt, 36, INK, True)
        c.alpha_composite(tb, (114, 52))
        place(base, c, SAFE_L, 470 + i * 172, p, dy=44 * (1 - p), angle=-2.5 * (1 - p))

    a2 = fin(t - 1.05, 0.35)
    t2 = text_img("最终以平台公告和你的账户账单为准", 34, MUTED)
    place(base, t2, SAFE_L, 1010, a2, dy=16 * (1 - a2))


def sc_end(base, t):
    """收尾：标题弹性放大 + 下划线擦除 + 按钮脉冲。"""
    a = back_out((t - 0.02) / 0.45)
    t1 = text_img("你最想白嫖哪个？", 92, INK, True)
    place(base, t1, SAFE_L, 480, a, dy=44 * (1 - a), scale=0.88 + 0.12 * a)

    a2 = fin(t - 0.22, 0.32)
    t2 = text_img("评论区告诉我，我下期实测", 44, GREEN, True)
    place(base, t2, SAFE_L, 640, a2, dy=20 * (1 - a2))

    # 下划线擦除
    up = fin(t - 0.36, 0.4)
    if up > 0:
        ul = Image.new("RGBA", (CW, 8), (0, 0, 0, 0))
        ImageDraw.Draw(ul).rounded_rectangle((0, 0, CW, 7), 4, fill=YELLOW + (255,))
        wipe(base, ul, SAFE_L, 730, up)

    a3 = fin(t - 0.55, 0.35)
    t3 = text_img("科技不高冷，AI 很好用 · 我是晚枫", 36, MUTED)
    place(base, t3, SAFE_L, 790, a3, dy=16 * (1 - a3))

    # 按钮脉冲
    pa = t - 0.80
    if pa > 0:
        pulse = 1 + 0.05 * math.sin(pa * 6.0)
        btn = chip_img("关注我 · 只讲真能白嫖的", 36, (255, 255, 255), INDIGO, radius=30)
        place(base, btn, SAFE_L, 900, fin(pa, 0.35), scale=pulse)


SCENES = [
    (0.00, 3.40, sc_hook),
    (3.50, 3.40, sc_proof),
    (7.00, 3.40, sc_two_ways),
    (10.50, 2.50, sc_steps),
    (13.10, 3.40, sc_code),
    (16.60, 1.90, sc_free_range),
    (18.60, 2.30, sc_zero),
    (21.00, 2.30, sc_limits),
    (23.40, 1.20, sc_end),
]


def render_frame(t):
    GUARD.reset()
    base = Image.new("RGBA", (W, H), BG + (255,))
    draw_bg(base)
    for start, dur, fn in SCENES:
        if not (start <= t < start + dur):
            continue
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # 场景内容整体下移，避开顶部进度条、把重心压向中下部
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
    marks = [0.7, 1.6, 2.6, 4.4, 5.6, 8.2, 9.6, 11.4, 12.6, 14.2, 15.6,
             17.2, 19.0, 20.2, 21.8, 23.0, 24.0]
    cw, ch = 260, 462
    cols = 6
    rows = (len(marks) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, ch * rows), (235, 233, 228))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧B-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 30), fill=(26, 26, 31))
        td.text((9, 4), f"{t:.1f}s", font=font(20, True), fill=(250, 204, 21))
        sheet.paste(thumb, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(HERE / "检查图-MG样片B.png")
    write_report(GUARD, HERE, "B 亮色杂志")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片B.png")


def main():
    preview = "--preview" in sys.argv
    make_contact()
    if preview:
        print("--preview，仅生成关键帧检查图")
        return
    out = HERE / "MG-样片B-亮色动效-无声.mp4"
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
