#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例选题（虚构）Nimbus 3.0 新版速览 · MG 样片 G（简笔画风）

前六版：A 深色科技 / B 亮色杂志 / C 复古拼贴 / D 故障艺术 / E 像素游戏 / F 暖色治愈
本版：白板简笔画——纸白底 + 铅笔黑细线 + 一支马克笔强调色，所有框线都是手绘抖动线。

视觉语言：
- 纸白底 + 极淡点阵格（草稿本感）
- 一切元素靠细线勾勒，不填充、不投影，最多用斜排铅笔线做阴影
- 线条每 4 帧换一次随机种子（boil 效果），画面像在自己一笔笔画出来
- 强调色只有两支马克笔：蓝（讲事实）+ 橙（讲价格），其余全灰
- 证据图套手绘双线框 + 一段胶带，保持"贴在草稿本上"的感觉

用法：
    python build_mg_sketch.py --preview   # 只出关键帧检查图
    python build_mg_sketch.py             # 渲染无声 MP4
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
                   set_content_offset, write_report, open_evidence,
                   load_font, SHOTS_DIR, EVID_DIR)

GUARD = OverlapGuard(1080, 1920, text_thresh=0.015,
                     safe_top=0, safe_bottom=0, safe_left=0, safe_right=0)

SHOTS = SHOTS_DIR  # 由 mgkit.paths 解析（MG_SHOTS_DIR 可覆盖）
EVID = EVID_DIR    # 由 mgkit.paths 解析（MG_EVID_DIR 可覆盖）

W, H = 1080, 1920

# 字体不写死路径与 ttc 序号：按角色向 mgkit 要（见 mgkit/fonts.py）。

# ---- 简笔画色卡：一支铅笔 + 两支马克笔 ----
PAPER = (252, 251, 248)      # 纸白底
GRID = (214, 220, 228)       # 点阵格
INK = (56, 58, 62)           # 铅笔黑 正文/线稿
INK_S = (150, 154, 160)      # 淡灰 次要
BLUE = (40, 104, 214)        # 马克笔蓝 事实/强调
BLUE_S = (223, 234, 250)
ORANGE = (232, 96, 12)       # 马克笔橙 价格/数字
ORANGE_S = (252, 233, 214)
GREEN = (44, 152, 100)       # 少量绿 只用于"能用"标记
RED = (206, 62, 58)          # 少量红 只用于"限制"

SAFE_L = 84
SAFE_R = W - 150
CW = SAFE_R - SAFE_L

TOTAL = 24.8
NFRAMES = round(TOTAL * FPS)
YOFF = [210]

_BOIL = [0]          # 每 4 帧换一次，线条才会"抖"
random.seed(20261113)


def font(size, bold=False):
    return load_font("sans_bold" if bold else "sans_regular", int(size))


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


def back_out(x, s=1.9):
    """手绘元素落位时的轻微过冲，像笔尖压下去又弹起。"""
    x = clamp(x)
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def fin(t, dur=0.32):
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


# ---------------------------------------------------------------- 手绘线稿
def _seed(*args) -> int:
    """同一次 boil 内稳定、不同 boil 之间变化的种子。

    不用内置 hash()——字符串的 hash 每个进程都带随机盐，跨进程不可复现。
    """
    h = _BOIL[0] * 1000003
    for a in args:
        if isinstance(a, str):
            v = sum(ord(c) * (i + 7) for i, c in enumerate(a))
        else:
            v = int(a)
        h = (h * 131 + v) % 2 ** 30
    return h


def wobble_pts(p0, p1, amp=2.6, seg=None, seed=0):
    """把直线打散成带垂直抖动的手绘点列。"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    n = seg or max(4, int(ln / 26))
    nx, ny = (-dy / ln, dx / ln) if ln else (0.0, 0.0)
    rng = random.Random(seed)
    pts = []
    for i in range(n + 1):
        u = i / n
        # 端点抖动小、中段抖动大，更像手腕发力
        k = math.sin(u * math.pi) ** 0.7
        j = rng.uniform(-amp, amp) * k
        pts.append((p0[0] + dx * u + nx * j, p0[1] + dy * u + ny * j))
    return pts


def sketch_line(layer, p0, p1, color=INK, width=3, amp=2.6, passes=1,
                seed=0, prog=1.0, overshoot=0.0):
    """画一条（或两遍）手绘线。prog<1 时只画前半段——线在"长出来"。"""
    if prog <= 0.002:
        return
    d = ImageDraw.Draw(layer, "RGBA")
    for k in range(passes):
        pts = wobble_pts(p0, p1, amp, seed=seed + k * 97)
        if overshoot:
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            ln = math.hypot(dx, dy) or 1
            pts[-1] = (pts[-1][0] + dx / ln * overshoot, pts[-1][1] + dy / ln * overshoot)
        m = max(2, int(len(pts) * clamp(prog)))
        d.line(pts[:m], fill=color + (235,), width=width)


def sketch_rect(layer, x0, y0, x1, y1, color=INK, width=3, amp=2.6,
               passes=2, seed=0, prog=1.0):
    """手绘矩形框：四条线各自出头一点，转角不闭合——简笔画的精髓。"""
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    # 四条线的绘制顺序固定，prog 按 0→1 均分给四条边
    edges = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    for i, (a, b) in enumerate(edges):
        e0, e1 = i / 4, (i + 1) / 4
        p = clamp((prog - e0) / (e1 - e0))
        if p <= 0:
            continue
        sketch_line(layer, a, b, color, width, amp, passes, seed + i * 31, p, overshoot=7)


def sketch_ellipse(layer, box, color=INK, width=3, amp=2.2, seed=0, prog=1.0, turns=1.06):
    """手绘圈：一圈半的螺旋，起笔和收笔错开，像随手圈住重点。"""
    if prog <= 0.002:
        return
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    rng = random.Random(seed)
    n = 72
    pts = []
    for i in range(n + 1):
        u = i / n
        ang = -math.pi / 2 + u * 2 * math.pi * turns
        jx = rng.uniform(-amp, amp)
        jy = rng.uniform(-amp, amp)
        pts.append((cx + rx * math.cos(ang) + jx, cy + ry * math.sin(ang) + jy))
    m = max(3, int(len(pts) * clamp(prog)))
    ImageDraw.Draw(layer, "RGBA").line(pts[:m], fill=color + (230,), width=width)


def hatch(layer, x0, y0, x1, y1, color=INK_S, gap=13, width=2, angle=-38, prog=1.0):
    """斜排铅笔线：唯一允许的"填充"，用来做进度条和阴影。"""
    if prog <= 0.002:
        return
    rng = random.Random(_seed(x0, y0, x1))
    tan = math.tan(math.radians(angle))
    d = ImageDraw.Draw(layer, "RGBA")
    total = (x1 - x0) + (y1 - y0) * tan
    i, done = 0, int(clamp(prog) * (total / gap))
    x = x0 - (y1 - y0) * tan
    while x < x1 + 2:
        if i >= done:
            break
        xa, ya = max(x0, x), y1 if x < x0 else y0
        xb, yb = min(x1, x + (y1 - y0) * tan), y0 if x + (y1 - y0) * tan > x1 else y1
        j = rng.uniform(-2, 2)
        d.line((xa + j, ya, xb + j, yb), fill=color + (150,), width=width)
        x += gap
        i += 1


def card(w, h, fill=None, color=INK, width=3, seed=0):
    """手绘框卡：不投影、不圆角，只两遍抖动线。返回 (layer, 0)。

    简笔画没有 shadow padding，内容坐标就是图层坐标，
    重叠检测拿到的框和肉眼看到的完全一致。
    """
    pad = 10
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if fill:
        ImageDraw.Draw(im).rectangle((pad, pad, pad + w - 1, pad + h - 1), fill=fill + (255,))
    sketch_rect(im, pad, pad, pad + w - 1, pad + h - 1, color, width, 2.4, 2, seed)
    set_content_offset(im, 0, 0)
    return im, 0


@lru_cache(maxsize=128)
def chip(s, size, fg, fill, pad_x=24, pad_y=12):
    """手绘标签：淡色底 + 抖动框 + 字。"""
    t = text_img(s, size, fg, True)
    w, h = t.width + pad_x * 2, t.height + pad_y * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle((0, 0, w - 1, h - 1), fill=fill + (255,))
    sketch_rect(im, 1, 1, w - 2, h - 2, fg, 2, 1.8, 2, 5)
    im.alpha_composite(t, (pad_x, pad_y))
    return im


# ---------------------------------------------------------------- 涂鸦小图标
@lru_cache(maxsize=32)
def doodle_bulb(size=120, color=ORANGE):
    """灯泡：想到了。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy = size // 2, int(size * 0.42)
    r = int(size * 0.26)
    sketch_ellipse(im, (cx - r, cy - r, cx + r, cy + r), INK, max(2, size // 42), 1.6, 11)
    # 灯座
    sketch_line(im, (cx - r * 0.55, cy + r * 0.95), (cx - r * 0.55, cy + r * 1.5), INK,
                max(2, size // 48), 1.2, 1, 12)
    sketch_line(im, (cx + r * 0.55, cy + r * 0.95), (cx + r * 0.55, cy + r * 1.5), INK,
                max(2, size // 48), 1.2, 1, 13)
    sketch_line(im, (cx - r * 0.6, cy + r * 1.5), (cx + r * 0.6, cy + r * 1.5), INK,
                max(2, size // 48), 1.2, 1, 14)
    # 光芒
    for k in range(6):
        a = -math.pi / 2 + (k - 2.5) * 0.42
        x0 = cx + math.cos(a) * (r * 1.35)
        y0 = cy + math.sin(a) * (r * 1.35)
        x1 = cx + math.cos(a) * (r * 1.72)
        y1 = cy + math.sin(a) * (r * 1.72)
        sketch_line(im, (x0, y0), (x1, y1), color, max(2, size // 52), 1.0, 1, 20 + k)
    return im


@lru_cache(maxsize=32)
def doodle_num(n, size=76, color=INK, fg=(252, 251, 248)):
    """手绘序号圈：圈里一个数字。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((3, 3, size - 4, size - 4), fill=color + (255,))
    sketch_ellipse(im, (2, 2, size - 3, size - 3), INK, 3, 1.8, 7, turns=1.1)
    t = text_img(str(n), int(size * 0.46), fg, True)
    im.alpha_composite(t, ((size - t.width) // 2, (size - t.height) // 2))
    return im


@lru_cache(maxsize=16)
def doodle_warn(size=76):
    """手绘警告：三角 + 感叹号。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sketch_line(im, (size * 0.5, size * 0.12), (size * 0.92, size * 0.86), RED, 3, 1.6, 1, 31)
    sketch_line(im, (size * 0.92, size * 0.86), (size * 0.08, size * 0.86), RED, 3, 1.6, 1, 32)
    sketch_line(im, (size * 0.08, size * 0.86), (size * 0.5, size * 0.12), RED, 3, 1.6, 1, 33)
    sketch_line(im, (size * 0.5, size * 0.36), (size * 0.5, size * 0.66), RED, 4, 0.8, 1, 34)
    ImageDraw.Draw(im).ellipse((size * 0.46, size * 0.72, size * 0.54, size * 0.80),
                               fill=RED + (255,))
    return im


@lru_cache(maxsize=16)
def doodle_arrow(size=140, color=BLUE):
    """手绘弯箭头：从 A 指到 B。"""
    im = Image.new("RGBA", (size, size // 2), (0, 0, 0, 0))
    rng = random.Random(41)
    pts = []
    for i in range(13):
        u = i / 12
        x = u * size * 0.82
        y = size * 0.42 - math.sin(u * math.pi) * size * 0.24 + rng.uniform(-1.6, 1.6)
        pts.append((x, y))
    ImageDraw.Draw(im, "RGBA").line(pts, fill=color + (230,), width=3)
    sketch_line(im, (size * 0.82, size * 0.30), (size * 0.90, size * 0.42), color, 3, 1.0, 1, 42)
    sketch_line(im, (size * 0.90, size * 0.42), (size * 0.78, size * 0.46), color, 3, 1.0, 1, 43)
    return im


@lru_cache(maxsize=16)
def doodle_star(size=60, color=ORANGE):
    """手绘五角星（一笔画）。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy, r = size / 2, size / 2, size * 0.42
    pts = []
    for k in range(11):
        a = -math.pi / 2 + (k * 4 % 10) / 10 * 2 * math.pi
        rr = r if k % 2 == 0 else r * 0.44
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    ImageDraw.Draw(im, "RGBA").line(pts, fill=color + (225,), width=3)
    return im


# ---------------------------------------------------------------- 合成
def place(base, layer, x, y, a=1.0, dy=0, scale=1.0, angle=0.0, squeeze=1.0):
    """带 alpha / 位移 / 缩放 / 旋转的合成。"""
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


@lru_cache(maxsize=4)
def paper_bg():
    """纸白底 + 淡点阵格 + 顶部一道很淡的铅笔横向擦痕。"""
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(60, H, 60):
        for x in range(60, W, 60):
            d.ellipse((x, y, x + 3, y + 3), fill=GRID + (120,))
    # 边缘轻微压暗，纸才有厚度
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    ed.rectangle((0, 0, W, H), outline=(120, 126, 134, 40), width=26)
    im = Image.alpha_composite(im.convert("RGBA"), edge.filter(ImageFilter.GaussianBlur(30)))
    return im.convert("RGB").convert("RGBA")


def evid_card(name, w, h, label=None, accent=BLUE, prog=1.0):
    """证据图：原色截图 + 手绘双线框 + 左上角一段胶带。

    简笔画底是纸白，官网白底截图直接贴最协调，不做反相。
    """
    im = open_evidence(name, w - 34, h - 34, prefer_light=False)
    im = ImageEnhance.Contrast(im).enhance(1.06)

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sketch_rect(layer, 4, 4, w - 5, h - 5, INK, 3, 2.6, 2, 3, prog=prog)
    ix = (w - im.width) // 2
    iy = (h - im.height) // 2
    layer.alpha_composite(im.convert("RGBA"), (ix, iy))
    # 胶带
    tape = Image.new("RGBA", (150, 46), (0, 0, 0, 0))
    td = ImageDraw.Draw(tape)
    td.rectangle((0, 0, 149, 45), fill=(214, 220, 228, 175))
    for x in range(0, 150, 9):
        td.line((x, 0, x + 14, 45), fill=(255, 255, 255, 70), width=3)
    layer.alpha_composite(tape.rotate(-6, expand=True, resample=Image.BICUBIC), (-18, -20))
    if label:
        tag = chip(label, 24, accent, BLUE_S if accent == BLUE else ORANGE_S)
        layer.alpha_composite(tag, (18, h - tag.height - 16))
    return layer


def top_bar(base, p, label="NIMBUS · 新版速览"):
    """顶部：手绘标签 + 一条正在被涂满的进度线。"""
    tag = chip(label, 25, BLUE, BLUE_S, pad_x=22, pad_y=11)
    place(base, tag, SAFE_L, 66, 1.0)
    # 进度：底是淡线，上面用斜排铅笔线填过去
    base_line = Image.new("RGBA", (CW, 10), (0, 0, 0, 0))
    sketch_line(base_line, (0, 5), (CW, 5), INK_S, 2, 1.2, 1, 61)
    place(base, base_line, SAFE_L, 150, 1.0)
    if p > 0:
        fill = Image.new("RGBA", (CW, 14), (0, 0, 0, 0))
        hatch(fill, 0, 0, int(CW * p), 13, ORANGE, gap=9, width=3)
        place(base, fill, SAFE_L, 144, 1.0)
    # 右上角三个涂鸦点
    d = ImageDraw.Draw(base, "RGBA")
    for i, c in enumerate((BLUE, ORANGE, GREEN)):
        d.ellipse((SAFE_R - 66 + i * 22, 72, SAFE_R - 54 + i * 22, 84), fill=c + (230,))


# ---------------------------------------------------------------- 场景
def sc_hook(base, t):
    """钩子：标题被一笔笔写出来 + 三个手绘圈 + 底部划线。"""
    a = fin(t - 0.05, 0.42)
    t1 = text_img("笔记 · 附件 · 网页", 88, INK, True, 1.20)
    place(base, t1, SAFE_L, 340, a, dy=20 * (1 - a))

    a2 = fin(t - 0.26, 0.42)
    t2 = text_img("离线同步能用了", 104, ORANGE, True, 1.20)
    place(base, t2, SAFE_L, 460, a2, dy=20 * (1 - a2))

    # 标题下的手绘波浪线，从左往右"画"出来
    up = clamp((t - 0.42) / 0.62)
    if up > 0:
        ul = Image.new("RGBA", (int(t2.width * 0.92), 22), (0, 0, 0, 0))
        sketch_line(ul, (0, 12), (t2.width * 0.92, 12), ORANGE, 5, 3.4, 2, 71)
        wipe(base, ul, SAFE_L, 596, up)

    a3 = fin(t - 0.55, 0.34)
    t3 = text_img("Nimbus 3.0 系列 · 官网当前版本说明", 36, INK_S)
    place(base, t3, SAFE_L, 650, a3, dy=14 * (1 - a3))

    # 三个手绘圈：文本 / 图片 / 视频
    items = [("笔记", "×2"), ("附件", "×3"), ("网页", "720P")]
    cw = (CW - 2 * 26) // 3
    for i, (k, v) in enumerate(items):
        st = 0.72 + i * 0.18
        p = clamp(back_out((t - st) / 0.56))
        if p <= 0:
            continue
        c, _ = card(cw, 230, None, INK, 3, seed=80 + i)
        cd = ImageDraw.Draw(c)
        cd.ellipse((cw // 2 - 44, 24, cw // 2 + 44, 112), fill=ORANGE_S + (255,))
        sketch_ellipse(c, (cw // 2 - 48, 20, cw // 2 + 48, 116), ORANGE, 3, 1.8, 81 + i)
        z = text_img("0", 58, ORANGE, True)
        c.alpha_composite(z, (cw // 2 - z.width // 2, 24 + (88 - z.height) // 2))
        tk = text_img(k, 40, INK, True)
        c.alpha_composite(tk, ((cw - tk.width) // 2, 134))
        tv = text_img(v, 26, INK_S)
        c.alpha_composite(tv, ((cw - tv.width) // 2, 186))
        place(base, c, SAFE_L + i * (cw + 26), 740, p, dy=26 * (1 - p),
              scale=0.9 + 0.1 * p, angle=(i - 1) * 1.2)

    # 右下角一个"想到了"灯泡
    bp = clamp(fin(t - 1.50, 0.5))
    if bp > 0:
        place(base, doodle_bulb(150, ORANGE), SAFE_R - 150, 1000, bp,
              scale=0.86 + 0.14 * bp, angle=-8 + 4 * bp)

    lp = fin(t - 1.35, 0.55)
    if lp > 0:
        band = Image.new("RGBA", (CW, 16), (0, 0, 0, 0))
        seg = CW / 3
        for i, c in enumerate((BLUE, ORANGE, GREEN)):
            hatch(band, i * seg + 4, 0, (i + 1) * seg - 4, 15, c, gap=8, width=3)
        wipe(base, band, SAFE_L, 1040, lp)


def sc_proof(base, t):
    """兑现：官网证据 + 手绘圈把重点圈出来。"""
    a = fin(t - 0.02, 0.4)
    t1 = text_img("新版功能", 96, INK, True, 1.18)
    place(base, t1, SAFE_L, 320, a, dy=22 * (1 - a))

    a2 = fin(t - 0.20, 0.34)
    t2 = text_img("就挂在官网首页", 80, BLUE, True, 1.18)
    place(base, t2, SAFE_L, 460, a2, dy=18 * (1 - a2))

    ep = clamp((t - 0.36) / 0.72)
    ev = evid_card("E09-试用额度与限制.png", CW, 380, "官网 · 新版公告入口", BLUE, prog=ep)
    place(base, ev, SAFE_L, 580, 1.0 if ep > 0 else 0.0)

    # 手绘圈：像老师批注那样把入口圈住
    cp = clamp((t - 1.05) / 0.7)
    if cp > 0:
        cir = Image.new("RGBA", (CW, 380), (0, 0, 0, 0))
        sketch_ellipse(cir, (26, 30, CW - 60, 350), ORANGE, 5, 4.2, 91, prog=cp, turns=1.14)
        place(base, cir, SAFE_L, 580, 1.0)

    a4 = fin(t - 1.30, 0.32)
    t4 = text_img("不是营销话术，是官网自己的入口", 34, INK_S)
    place(base, t4, SAFE_L, 1000, a4, dy=12 * (1 - a4))


def sc_two_ways(base, t):
    """两种用法：两张手绘卡 + 中间一个圈起来的"或"。"""
    a = fin(t - 0.02, 0.4)
    t1 = text_img("两种用法", 92, INK, True, 1.20)
    place(base, t1, SAFE_L, 310, a, dy=20 * (1 - a))

    cw = (CW - 44) // 2
    blocks = [
        ("普通用户", "Nimbus 网页端", "编辑 · 协作\n搜索 · 归档", BLUE, BLUE_S),
        ("开发者", "API 接口", "离线增量\n接入自有脚本", GREEN, (222, 240, 231)),
    ]
    for i, (title, sub, body, ac, sc_) in enumerate(blocks):
        st = 0.18 + i * 0.18
        p = clamp(back_out((t - st) / 0.6))
        if p <= 0:
            continue
        c, _ = card(cw, 400, None, INK, 3, seed=120 + i)
        badge = chip(title, 32, ac, sc_, pad_x=20, pad_y=10)
        c.alpha_composite(badge, (26, 28))
        t2 = text_img(sub, 44, INK, True)
        c.alpha_composite(t2, (26, 116))
        ln = Image.new("RGBA", (cw - 52, 8), (0, 0, 0, 0))
        sketch_line(ln, (0, 4), (cw - 52, 4), INK_S, 2, 1.4, 1, 130 + i)
        c.alpha_composite(ln, (26, 182))
        for j, line in enumerate(body.split("\n")):
            t3 = text_img(line, 29, INK_S)
            c.alpha_composite(t3, (26, 214 + j * 46))
        place(base, c, SAFE_L + i * (cw + 44), 470, p, dy=30 * (1 - p),
              angle=(1 if i == 0 else -1) * 1.4 * (1 - p))

    sp = t - 0.72
    if sp > 0:
        p = clamp(back_out(sp / 0.5))
        dot = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        ImageDraw.Draw(dot).ellipse((14, 14, 106, 106), fill=PAPER + (255,))
        sketch_ellipse(dot, (8, 8, 112, 112), INK, 3, 2.0, 141)
        o = text_img("或", 40, INK, True)
        dot.alpha_composite(o, (60 - o.width // 2, 60 - o.height // 2))
        place(base, dot, SAFE_L + CW // 2 - 60, 640, p, scale=0.8 + 0.2 * p)

    a3 = fin(t - 1.10, 0.32)
    t3 = text_img("不写代码也能用，要接工具才走 API", 34, INK_S)
    place(base, t3, SAFE_L, 960, a3, dy=12 * (1 - a3))


def sc_steps(base, t):
    """开发者五步：手绘序号圈 + 虚线连线 + 五张框卡。"""
    a = fin(t - 0.02, 0.4)
    t1 = text_img("开发者五步", 92, INK, True, 1.20)
    place(base, t1, SAFE_L, 300, a, dy=18 * (1 - a))

    items = ["注册账户", "创建工作区", "装 nimbus 命令行", "连同步地址", "开第一次同步"]
    row_h = 172
    y0 = 470

    # 连线：一段一段画出来的虚线
    lp = clamp((t - 0.36) / 1.1)
    if lp > 0:
        line = Image.new("RGBA", (12, row_h * 5 - 60), (0, 0, 0, 0))
        n = int((row_h * 5 - 60) * lp)
        for y in range(0, n, 22):
            sketch_line(line, (6, y), (6, min(y + 12, n)), INK_S, 3, 1.0, 1, 150)
        place(base, line, SAFE_L + 34, y0 + 40, 1.0)

    for i, it in enumerate(items):
        st = 0.24 + i * 0.16
        p = clamp(back_out((t - st) / 0.5))
        if p <= 0:
            continue
        cy = y0 + i * row_h
        place(base, doodle_num(i + 1, 66, BLUE if i < 4 else ORANGE), SAFE_L, cy, p,
              dy=16 * (1 - p), scale=0.55 + 0.45 * p)

        c, _ = card(CW - 130, 112, None, INK, 3, seed=160 + i)
        tb = text_img(it, 38, INK, True)
        c.alpha_composite(tb, (26, (112 - tb.height) // 2))
        place(base, c, SAFE_L + 96, cy - 20, p, dy=16 * (1 - p), angle=(i % 2 - 0.5) * 0.8)


def sc_code(base, t):
    """三行参数：证据图 + 手绘代码框 + 铅笔光标闪。"""
    a = fin(t - 0.02, 0.4)
    t1 = text_img("三行就能发出去", 84, INK, True, 1.20)
    place(base, t1, SAFE_L, 300, a, dy=18 * (1 - a))

    ep = clamp((t - 0.18) / 0.6)
    ev = evid_card("E06-快速开始-同步地址.png", CW, 200, "官方快速开始", GREEN, prog=ep)
    place(base, ev, SAFE_L, 420, 1.0 if ep > 0 else 0.0)

    lines = [
        ("model:", "nimbus-cli 3.0"),
        ("base:", "drive.nimbus.dev"),
        ("auth:", "Bearer YOUR_API_KEY"),
    ]
    code_y = 680
    card_h = 58 * len(lines) + 46
    c, _ = card(CW, card_h, None, INK, 3, seed=180)
    place(base, c, SAFE_L, code_y, fin(t - 0.34, 0.4), dy=20 * (1 - fin(t - 0.34, 0.4)))
    for i, (k, v) in enumerate(lines):
        st = 0.50 + i * 0.20
        p = fin(t - st, 0.34)
        if p <= 0:
            continue
        kt = text_img(k, 31, INK_S)
        vt = text_img(v, 31, BLUE if i == 0 else INK, i == 0)
        row = Image.new("RGBA", (CW - 60, 42), (0, 0, 0, 0))
        row.alpha_composite(kt, (0, 0))
        row.alpha_composite(vt, (kt.width + 16, 0))
        wipe(base, row, SAFE_L + 26, code_y + 24 + i * 58, p)

    cb = t - 1.24
    if cb > 0 and int(cb * 2.4) % 2 == 0:
        cur = Image.new("RGBA", (8, 34), (0, 0, 0, 0))
        ImageDraw.Draw(cur).rectangle((0, 0, 7, 33), fill=ORANGE + (230,))
        place(base, cur, SAFE_L + 30 + 210, code_y + 24 + 2 * 58 + 4, 1.0)

    tag = chip("复制即用", 28, GREEN, (222, 240, 231))
    a3 = fin(t - 1.42, 0.34)
    place(base, tag, SAFE_L, code_y + card_h + 30, a3, dy=16 * (1 - a3), angle=-2.2)


def sc_free_range(base, t):
    """能力范围：三行证据图 + 手绘 NEW 圈。"""
    a = fin(t - 0.02, 0.4)
    t1 = text_img("哪些新版能用", 88, INK, True, 1.20)
    place(base, t1, SAFE_L, 270, a, dy=18 * (1 - a))

    rows = [
        ("E03-能力表-多人协作", "笔记协作 ×3", "多人同时编辑", GREEN),
        ("E04-能力表-附件版本", "附件版本 ×5", "保留 30 天版本", BLUE),
        ("E01-能力表-离线同步", "网页剪藏 不限页", "自动打标签", ORANGE),
    ]
    for i, (ev_name, k, v, ac) in enumerate(rows):
        st = 0.20 + i * 0.18
        p = clamp(back_out((t - st) / 0.56))
        if p <= 0:
            continue
        cy = 400 + i * 246
        c, _ = card(CW, 222, None, INK, 3, seed=190 + i)
        tk = text_img(k, 38, INK, True)
        c.alpha_composite(tk, (26, 16))
        tv = text_img(v, 26, INK_S)
        c.alpha_composite(tv, (26 + tk.width + 18, 26))
        ev = open_evidence(ev_name, CW - 56, 150, prefer_light=False)
        ev = ImageEnhance.Contrast(ev).enhance(1.05)
        c.alpha_composite(ev.convert("RGBA"), (26, 62))
        lp = clamp(fin(t - st - 0.26, 0.4))
        if lp > 0:
            tag = Image.new("RGBA", (104, 104), (0, 0, 0, 0))
            ImageDraw.Draw(tag).ellipse((10, 10, 94, 94), fill=(255, 255, 255, 235))
            sketch_ellipse(tag, (6, 6, 98, 98), ac, 3, 2.2, 200 + i)
            z = text_img("含", 38, ac, True)
            tag.alpha_composite(z, ((104 - z.width) // 2, (104 - z.height) // 2))
            c.alpha_composite(tag, (CW - 124, 14))
        place(base, c, SAFE_L, cy, p, dy=24 * (1 - p), angle=(i - 1) * 0.9)


def sc_zero(base, t):
    """能力证据：旧版本号被划掉 + 大字 NEW + 证据图。"""
    a = fin(t - 0.02, 0.4)
    t1 = text_img("网页剪藏 不限页", 74, INK, True, 1.20)
    place(base, t1, SAFE_L, 290, a, dy=16 * (1 - a))

    a2 = fin(t - 0.24, 0.32)
    old = text_img("旧版只能同步 1 台", 42, INK_S, True)
    place(base, old, SAFE_L, 390, a2)
    sp = clamp((t - 0.56) / 0.42)
    if sp > 0:
        strike = Image.new("RGBA", (old.width + 16, 14), (0, 0, 0, 0))
        sketch_line(strike, (0, 7), (old.width + 16, 7), RED, 5, 2.6, 2, 210)
        wipe(base, strike, SAFE_L - 4, 390 + old.height // 2 - 8, sp)

    a3 = fin(t - 0.66, 0.32)
    lab = text_img("当前版本说明", 32, INK_S, True)
    place(base, lab, SAFE_L, 470, a3)

    rp = clamp((t - 0.76) / 1.0)
    val = 1 + 2 * soft_out(rp)
    num_s = "3" if rp >= 0.999 else f"{val:.1f}"
    num = text_img(num_s, 132, ORANGE, True)
    place(base, num, SAFE_L, 520, a3)
    unit = text_img("台设备", 46, INK, True)
    place(base, unit, SAFE_L + num.width + 14, 520 + 96, a3)

    ep = clamp((t - 1.00) / 0.6)
    ev = evid_card("E01-能力表-离线同步.png", CW, 165, "官网版本说明页", ORANGE, prog=ep)
    place(base, ev, SAFE_L, 710, 1.0 if ep > 0 else 0.0)

    # 把关键数字圈起来
    cp = clamp((t - 1.36) / 0.66)
    if cp > 0:
        cir = Image.new("RGBA", (CW, 165), (0, 0, 0, 0))
        sketch_ellipse(cir, (10, 14, CW - 40, 152), ORANGE, 5, 4.0, 221, prog=cp, turns=1.12)
        place(base, cir, SAFE_L, 710, 1.0)

    a5 = fin(t - 1.56, 0.3)
    t5 = text_img("nimbus-desktop-3.0 · 官网当前说明", 32, INK_S)
    place(base, t5, SAFE_L, 920, a5, dy=12 * (1 - a5))


def sc_limits(base, t):
    """三条限制：手绘警告三角 + 淡红框卡。"""
    a = fin(t - 0.02, 0.4)
    t1 = text_img("但有三条限制", 88, RED, True, 1.20)
    place(base, t1, SAFE_L, 290, a, dy=18 * (1 - a))

    rows = [
        "新版灰度中，还没全量放开",
        "有 TPS 和公平使用配额",
        "Agent Plan 按刊例价折算 Credits",
    ]
    for i, txt in enumerate(rows):
        st = 0.22 + i * 0.18
        p = clamp(back_out((t - st) / 0.54))
        if p <= 0:
            continue
        cy = 430 + i * 172
        c, _ = card(CW, 138, (252, 238, 236), INK, 3, seed=230 + i)
        c.alpha_composite(doodle_warn(76), (26, 32))
        tb = text_img(txt, 35, INK, True)
        c.alpha_composite(tb, (116, 50))
        place(base, c, SAFE_L, cy, p, dy=22 * (1 - p), angle=(i - 1) * 1.1)

    a2 = fin(t - 1.20, 0.3)
    t2 = text_img("最终以平台公告和你的账户账单为准", 32, INK_S)
    place(base, t2, SAFE_L, 990, a2, dy=12 * (1 - a2))


def sc_end(base, t):
    """收尾：大问句 + 手绘下划线 + 星星飘落 + 关注框。"""
    for i in range(9):
        st = 0.04 + i * 0.08
        p = clamp((t - st) / 3.0)
        if p <= 0:
            continue
        x = 60 + (i * 121) % (W - 160)
        y = -40 + p * (H + 90)
        sway = math.sin(t * 1.5 + i) * 20
        place(base, doodle_star(46 + (i % 3) * 12, (BLUE, ORANGE, GREEN)[i % 3]),
              x + sway, y, 0.85 - p * 0.4, angle=t * 40 + i * 25)

    a = fin(t - 0.05, 0.42)
    t1 = text_img("你最想先试哪个？", 92, INK, True, 1.18)
    place(base, t1, SAFE_L, 470, a, dy=22 * (1 - a))

    a2 = fin(t - 0.26, 0.32)
    t2 = text_img("评论区告诉我，我下期实测", 44, BLUE, True)
    place(base, t2, SAFE_L, 620, a2, dy=16 * (1 - a2))

    lp = clamp((t - 0.40) / 0.5)
    if lp > 0:
        ul = Image.new("RGBA", (CW, 20), (0, 0, 0, 0))
        sketch_line(ul, (0, 10), (CW, 10), BLUE, 5, 3.2, 2, 240)
        wipe(base, ul, SAFE_L, 724, lp)

    a3 = fin(t - 0.56, 0.3)
    t3 = text_img("下期拆一个真实场景 · 记得回来看", 34, INK_S)
    place(base, t3, SAFE_L, 790, a3, dy=12 * (1 - a3))

    pa = t - 0.80
    if pa > 0:
        p = clamp(back_out(pa / 0.42))
        btn, _ = card(500, 92, ORANGE_S, ORANGE, 4, seed=250)
        bt = text_img("关注我 · 只测官网写得清的", 33, INK, True)
        btn.alpha_composite(bt, ((500 - bt.width) // 2, 26))
        place(base, btn, SAFE_L, 880, p, scale=0.94 + 0.06 * p)
        place(base, doodle_arrow(150, BLUE), SAFE_L + 520, 900, clamp((pa - 0.2) / 0.4))


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
    _BOIL[0] = int(t * FPS) // 4
    base = paper_bg().copy()
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
    sheet = Image.new("RGB", (cw * cols, ch * rows), (232, 234, 238))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧G-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 28), fill=(56, 58, 62))
        td.text((8, 3), f"{t:.1f}s", font=font(18, True), fill=(252, 251, 248))
        sheet.paste(thumb, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(HERE / "检查图-MG样片G.png")
    write_report(GUARD, HERE, "G 简笔画")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片G.png")
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
    out = HERE / "MG-样片G-简笔画-无声.mp4"
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
