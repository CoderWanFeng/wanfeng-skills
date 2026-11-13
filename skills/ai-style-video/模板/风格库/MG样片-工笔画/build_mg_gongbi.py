#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例选题（虚构）Nimbus 3.0 新版速览 · MG 样片 H（工笔重彩画风）

前七版：A 深色科技 / B 亮色杂志 / C 复古拼贴 / D 故障艺术 / E 像素游戏 / F 暖色治愈 / G 简笔画
本版：绢本工笔重彩——不是水墨写意，是矿物颜料一层层染出来的那种颜色。

视觉语言：
- 绢本米黄底（细横纹 + 极淡分幅线 + 四边做旧压暗）
- 石青 / 石绿 / 朱砂 / 赭石 / 藤黄 / 胭脂 六色矿物颜料，全部低透明度多层叠染
  （"三矾九染"：prog 控制染了几遍，颜色由淡到浓长出来）
- 游丝描勾线：2px 细线，带极轻的笔锋抖动，只勾轮廓不填色
- 描金线做分隔与装裱边，证据图装裱成立轴（上下绫边 + 轴杆）
- 朱砂印章落印动效：1.35 倍落下压到 1.0，印泥边缘不规则
- 落款竖排、折枝花叶、花瓣飘落

用法：
    python build_mg_gongbi.py --preview   # 只出关键帧检查图
    python build_mg_gongbi.py             # 渲染无声 MP4
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

# 标题用宋体（画题、碑帖感），小字用黑体保清晰——宋体小字号在视频里会糊；
# 字体路径与 ttc 序号不写死，由 mgkit/fonts.py 按角色解析。

# ---- 工笔重彩色卡：矿物颜料，全部按"染"的方式叠 ----
# 重彩的要害是颜料本身不透明、饱和，叠上去要看得见。比淡彩/水墨写意浓一档。
SILK = (242, 234, 216)        # 绢本米黄底
SILK_D = (226, 212, 186)      # 绢本暗部 / 做旧
LINING = (206, 186, 150)      # 装裱绫边
AZURE = (30, 86, 152)         # 石青
AZURE_L = (158, 200, 228)     # 淡青
GREEN = (34, 128, 92)         # 石绿
GREEN_L = (166, 216, 186)     # 淡绿
CINNABAR = (202, 52, 36)      # 朱砂
CINNABAR_L = (248, 168, 148)  # 淡朱
OCHRE = (152, 90, 40)         # 赭石
OCHRE_L = (230, 190, 144)     # 淡赭
GOLD = (216, 164, 30)         # 藤黄 / 描金
GOLD_L = (250, 220, 138)
ROSE = (176, 40, 78)          # 胭脂
INK = (58, 51, 44)            # 浓墨 正文
INK_S = (120, 108, 92)        # 淡墨 次要
PAPER_CARD = (251, 246, 234)  # 笺纸卡面

SAFE_L = 84
SAFE_R = W - 150
CW = SAFE_R - SAFE_L

TOTAL = 24.8
NFRAMES = round(TOTAL * FPS)
YOFF = [210]

random.seed(20261113)


def font(size, title=False):
    return load_font("serif_bold" if title else "sans_bold", int(size))


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


def back_out(x, s=1.5):
    """落印、贴笺的过冲——比暖色风收敛，工笔讲究稳。"""
    x = clamp(x)
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def fin(t, dur=0.34):
    return ease_out(t / dur)


def fout(t, dur=0.24):
    return ease_in(t / dur)


@lru_cache(maxsize=512)
def text_img(s, size, color, title=False, spacing=1.34):
    f = font(size, title)
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


@lru_cache(maxsize=64)
def vertical_text(s, size, color, gap=14):
    """竖排落款：一字一格往下排，中国画题款的排法。"""
    f = font(size, True)
    boxes = [f.getbbox(ch) for ch in s]
    ws = [b[2] - b[0] for b in boxes]
    hs = [b[3] - b[1] for b in boxes]
    w = max(ws) + 16
    h = sum(hs) + gap * (len(s) - 1) + 16
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 8
    for ch, bb, bw, bh in zip(s, boxes, ws, hs):
        d.text(((w - bw) // 2 - bb[0], y - bb[1]), ch, font=f, fill=color + (255,))
        y += bh + gap
    return mark_text_layer(im, s)


# ---------------------------------------------------------------- 勾线与叠染
def brush_line(layer, pts, color=INK, width=2, alpha=225):
    """游丝描：把点列连成一条细线，末端略收。"""
    if len(pts) < 2:
        return
    ImageDraw.Draw(layer, "RGBA").line(pts, fill=color + (alpha,), width=width)


def outline_rect(layer, x0, y0, x1, y1, color=INK, width=2, prog=1.0, amp=1.1, seed=0):
    """细线勾框：四条边按顺序"长"出来，每边带极轻的笔锋抖动。"""
    if prog <= 0.002:
        return
    rng = random.Random(seed)
    edges = [[(x0, y0), (x1, y0)], [(x1, y0), (x1, y1)],
             [(x1, y1), (x0, y1)], [(x0, y1), (x0, y0)]]
    for i, (a, b) in enumerate(edges):
        e0, e1 = i / 4, (i + 1) / 4
        p = clamp((prog - e0) / (e1 - e0))
        if p <= 0:
            continue
        n = max(6, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 34))
        m = max(2, int((n + 1) * p))
        pts = []
        for k in range(n + 1):
            u = k / n
            j = rng.uniform(-amp, amp) * math.sin(u * math.pi)
            pts.append((a[0] + (b[0] - a[0]) * u + (b[1] - a[1]) * 0,
                        a[1] + (b[1] - a[1]) * u + j))
        brush_line(layer, pts[:m], color, width)


def wash(layer, box, color, depth=0.85, steps=7, prog=1.0, radius=0, inset_step=1.1):
    """三矾九染：低透明度一层层叠上去，prog 决定染了几遍。

    工笔的颜色不是刷出来的平涂，是染出来的——所以每遍都留一点底，
    并且逐遍往里收一点 inset，边缘自然形成深浅过渡。

    注意：不能用 ImageDraw.Draw(layer, "RGBA") 直接画——那样会把 RGBA 值
    **写进去而不是叠上去**，底下已染的颜色会被括掉。所以每一遍都画在
    一张透明胶子上，再 alpha_composite 合回 layer，才是真正的"罩染"。
    """
    x0, y0, x1, y1 = box
    n = int(clamp(prog) * steps + 0.5)
    if n <= 0:
        return
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(layer.width - 1, int(x1)), min(layer.height - 1, int(y1))
    w, h = x1 - x0 + 1, y1 - y0 + 1
    if w <= 1 or h <= 1:
        return
    max_ins = min(w, h) // 2 - 1
    for i in range(n):
        a = int(255.0 * depth / steps * (1 + 0.30 * i / steps))
        a = max(6, min(255, a))
        ins = min(i * inset_step, max_ins)
        glaze = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glaze)
        if radius:
            gd.rounded_rectangle((ins, ins, w - 1 - ins, h - 1 - ins),
                                 radius, fill=color + (a,))
        else:
            gd.rectangle((ins, ins, w - 1 - ins, h - 1 - ins), fill=color + (a,))
        # 胶子不是文字层，走这里不会重复登记坐标
        layer.alpha_composite(glaze, (x0, y0))


def gold_rule(layer, x0, y0, x1, prog=1.0, width=3):
    """描金横线：一条金线 + 下面一道淡影，像泥金。"""
    if prog <= 0.002:
        return
    xe = x0 + (x1 - x0) * clamp(prog)
    d = ImageDraw.Draw(layer, "RGBA")
    d.line((x0, y0, xe, y0), fill=GOLD + (235,), width=width)
    d.line((x0, y0 + width, xe, y0 + width), fill=GOLD + (70,), width=1)


def corner_brackets(layer, box, color=CINNABAR, prog=1.0, size=34, width=5):
    """朱笔圈点：只在四角画 L 形括号，中间不涂面。

    证据图上要标重点，用涂色会把截图盖住；圈点既是中国画的批注语汇，
    又不破坏截图可读性。
    """
    if prog <= 0.002:
        return
    x0, y0, x1, y1 = box
    s = size * clamp(prog)
    d = ImageDraw.Draw(layer, "RGBA")
    for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1),
                           (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((cx, cy, cx + sx * s, cy), fill=color + (240,), width=width)
        d.line((cx, cy, cx, cy + sy * s), fill=color + (240,), width=width)


def ruyi_corner(layer, x, y, size, color=GOLD, flip_x=1, flip_y=1):
    """如意角花：卡片四角的小纹样，工笔笺纸的标配装饰。"""
    d = ImageDraw.Draw(layer, "RGBA")
    pts = []
    for i in range(13):
        u = i / 12
        ang = u * math.pi * 0.92
        r = size * (0.55 + 0.45 * math.sin(ang * 2))
        pts.append((x + flip_x * r * math.cos(ang) * 0.9,
                    y + flip_y * r * math.sin(ang) * 0.9))
    brush_line(layer, pts, color, 2, 200)


# ---------------------------------------------------------------- 印章与纹样
@lru_cache(maxsize=32)
def seal(text, size=112, color=CINNABAR):
    """朱砂印：白文（字抠出来），印面边缘磕碰不规则，印泥有浓淡。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = int(size * 0.06)
    d.rounded_rectangle((pad, pad, size - pad, size - pad), int(size * 0.10),
                        fill=color + (238,))
    # 印泥浓淡：再叠一层偏心的淡红
    wash(im, (pad, pad, size - pad, size - pad), (214, 84, 62), 0.20, 3, 1.0,
         int(size * 0.10))
    # 文字：两字竖排或单字居中
    chars = list(text)[:2]
    if len(chars) == 1:
        t = text_img(chars[0], int(size * 0.56), (255, 252, 244), True)
        im.alpha_composite(t, ((size - t.width) // 2, (size - t.height) // 2))
    else:
        # 两字按现代读法从左往右排（传统印章右起，但短视频里会被读反）
        half = size // 2
        for i, ch in enumerate(chars):
            t = vertical_text(ch, int(size * 0.40), (255, 252, 244))
            im.alpha_composite(t, (half * i + (half - t.width) // 2 + 2,
                                   (size - t.height) // 2))
    # 磕碰：只啃外圈一条窄边，次数收紧——印要旧，但不能把字啃残
    rng = random.Random(sum(ord(c) * (i + 3) for i, c in enumerate(text)) + size * 977)
    px = im.load()
    rim = max(3, int(size * 0.07))
    for _ in range(int(size * 0.55)):
        side = rng.randrange(4)
        if side == 0:
            x, y = rng.randrange(size), rng.randrange(rim)
        elif side == 1:
            x, y = rng.randrange(size), rng.randrange(size - rim, size)
        elif side == 2:
            x, y = rng.randrange(rim), rng.randrange(size)
        else:
            x, y = rng.randrange(size - rim, size), rng.randrange(size)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                xx, yy = x + dx, y + dy
                if 0 <= xx < size and 0 <= yy < size:
                    r, g, b, a = px[xx, yy]
                    px[xx, yy] = (r, g, b, int(a * 0.34))
    return im


@lru_cache(maxsize=8)
def roundel(size=150, color=AZURE):
    """团花：双层花瓣圈 + 中心开光，用来放“含”“新”这类单点信息。

    带缓存，往里写字之前必须先 .copy()，否则污染缓存。
    """
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = size / 2
    r_out = size * 0.46
    for k in range(12):
        a = k / 12 * 2 * math.pi
        px_, py_ = cx + math.cos(a) * r_out * 0.86, cy + math.sin(a) * r_out * 0.86
        rr = size * 0.11
        d.ellipse((px_ - rr, py_ - rr, px_ + rr, py_ + rr), fill=color + (60,))
    d.ellipse((cx - r_out, cy - r_out, cx + r_out, cy + r_out), outline=color + (200,), width=2)
    r_in = size * 0.30
    d.ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), fill=PAPER_CARD + (250,))
    d.ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), outline=GOLD + (220,), width=2)
    return im


@lru_cache(maxsize=8)
def petal(size=44, color=CINNABAR_L):
    """五瓣梅：工笔小花，花瓣淡染 + 深一点的花心 + 花蕊点。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = size / 2
    pr = size * 0.30
    for k in range(5):
        a = -math.pi / 2 + k / 5 * 2 * math.pi
        px_, py_ = cx + math.cos(a) * size * 0.20, cy + math.sin(a) * size * 0.20
        d.ellipse((px_ - pr, py_ - pr, px_ + pr, py_ + pr), fill=color + (215,))
        d.ellipse((px_ - pr, py_ - pr, px_ + pr, py_ + pr), outline=ROSE + (120,), width=1)
    d.ellipse((cx - size * 0.07, cy - size * 0.07, cx + size * 0.07, cy + size * 0.07),
              fill=GOLD + (240,))
    return im


@lru_cache(maxsize=4)
def branch(w=340, h=520, seed=7):
    """折枝：一条主梗 + 几片石绿叶 + 两朵梅。用来压画面一角。"""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rng = random.Random(seed)
    # 主梗：从底部往上弯
    pts = []
    for i in range(25):
        u = i / 24
        x = w * 0.18 + math.sin(u * 2.4) * w * 0.22 + u * w * 0.10
        y = h * (1 - u * 0.94)
        pts.append((x, y + rng.uniform(-2, 2)))
    brush_line(im, pts, OCHRE, 4, 225)
    # 侧枝 + 叶 + 花
    for k in (4, 9, 14, 19):
        bx, by = pts[k]
        dirx = 1 if k % 2 == 0 else -1
        sp = [(bx, by)]
        for j in range(1, 9):
            sp.append((bx + dirx * j * w * 0.045, by - j * h * 0.012 + math.sin(j) * 4))
        brush_line(im, sp, OCHRE, 2, 190)
        # 叶：两头尖的披针形
        for j in (2, 5):
            lx, ly = sp[j]
            leaf = Image.new("RGBA", (int(w * 0.16), int(h * 0.06)), (0, 0, 0, 0))
            ld = ImageDraw.Draw(leaf, "RGBA")
            lw, lh = leaf.width, leaf.height
            ld.polygon([(0, lh / 2), (lw * 0.30, 0), (lw * 0.72, 0),
                        (lw, lh / 2), (lw * 0.72, lh), (lw * 0.30, lh)],
                       fill=GREEN + (150,))
            ld.line((0, lh / 2, lw, lh / 2), fill=GREEN + (230,), width=1)
            im.alpha_composite(leaf.rotate(-24 * dirx, expand=True,
                                           resample=Image.BICUBIC),
                               (int(lx - lw // 2), int(ly - lh // 2)))
        if k in (9, 19):
            im.alpha_composite(petal(int(w * 0.16)), (int(sp[-1][0] - w * 0.08),
                                                      int(sp[-1][1] - w * 0.08)))
    return im


# ---------------------------------------------------------------- 卡片与合成
def card(w, h, fill=PAPER_CARD, edge=INK, radius=6, seed=0, corner=True):
    """笺纸卡：淡色绢底 + 描金细边 + 四角如意纹。

    工笔风不投影，靠"纸与绢的色差"分层，所以 pad 取 0，
    重叠检测拿到的坐标和肉眼看到的完全一致。
    """
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if fill:
        # 纸面先铺实，再罩一遍淡色做绢纹；wash 是真叠合，铺完再染不会把底擦掉
        base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(base).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=fill + (255,))
        im.alpha_composite(base)
        wash(im, (4, 4, w - 5, h - 5), SILK_D, 0.10, 2, 1.0, radius)
    outline_rect(im, 3, 3, w - 4, h - 4, edge, 3, 1.0, 0.8, seed)
    if h > 90:
        cs = min(26, w // 6, h // 6)
        if corner:
            ruyi_corner(im, 8, 8, cs, GOLD)
            ruyi_corner(im, w - 9, 8, cs, GOLD, -1, 1)
            ruyi_corner(im, 8, h - 9, cs, GOLD, 1, -1)
            ruyi_corner(im, w - 9, h - 9, cs, GOLD, -1, -1)
    set_content_offset(im, 0, 0)
    return im, 0


@lru_cache(maxsize=128)
def chip(s, size, fg, fill, pad_x=24, pad_y=12):
    """题签：一条色底 + 细勾边 + 字，像贴在画上的签条。"""
    t = text_img(s, size, fg, True)
    w, h = t.width + pad_x * 2, t.height + pad_y * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle((0, 0, w - 1, h - 1), fill=fill + (255,))
    wash(im, (2, 2, w - 3, h - 3), SILK_D, 0.10, 2, 1.0)
    outline_rect(im, 1, 1, w - 2, h - 2, fg, 2, 1.0, 0.6, 5)
    im.alpha_composite(t, (pad_x, pad_y))
    return im


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


def stamp(base, text, x, y, t, size=112):
    """落印：从 1.34 倍压到 1.0，带一点旋转，落地后不回弹——盖章是有重量的。"""
    p = clamp((t) / 0.34)
    if p <= 0:
        return
    sc = 1.34 - 0.34 * ease_out(p)
    a = min(1.0, p * 1.8)
    place(base, seal(text, size), x, y, a, scale=sc, angle=-3.5 + 3.5 * ease_out(p))


# ---------------------------------------------------------------- 背景与装裱
@lru_cache(maxsize=4)
def silk_bg():
    """绢本底：米黄 + 细横纹（丝织）+ 极淡竖向分幅 + 四边做旧压暗 + 淡染云气。"""
    im = Image.new("RGB", (W, H), SILK)
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, H, 3):
        d.line((0, y, W, y), fill=SILK_D + (28,), width=1)
    for x in range(0, W, 340):
        d.line((x, 0, x, H), fill=SILK_D + (22,), width=1)
    # 两团石青/赭石云气，重彩的底子不能空
    for (cx, cy, r, col) in [(220, 300, 460, AZURE_L), (880, 1500, 420, OCHRE_L)]:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for i in range(26, 0, -1):
            rr = r * i / 26
            od.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col + (13,))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    # 做旧：四边压暗
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    ed.rectangle((0, 0, W, H), outline=(120, 96, 62, 60), width=40)
    im = Image.alpha_composite(im.convert("RGBA"),
                               edge.filter(ImageFilter.GaussianBlur(36)))
    # 一层极淡的麻点
    rng = random.Random(11)
    speck = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(speck)
    for _ in range(1400):
        sd.point((rng.randrange(W), rng.randrange(H)), fill=(110, 92, 66, rng.randrange(18, 46)))
    im = Image.alpha_composite(im, speck)
    return im.convert("RGB").convert("RGBA")


def evid_card(name, w, h, label=None, accent=AZURE, prog=1.0):
    """证据图装裱成立轴：上下绫边 + 描金轴杆，截图居中开光。

    官网截图是纯白底，直接放在绢本上会"跳"出来，所以先降饱和、
    提亮，再罩一层极淡的米黄，让它像被画进绢里。
    """
    band = 34
    ih = h - band * 2
    im = open_evidence(name, w - 28, ih, prefer_light=True).convert("RGB")
    im = ImageEnhance.Color(im).enhance(0.82)
    im = ImageEnhance.Brightness(im).enhance(1.02)
    tint = Image.new("RGB", im.size, SILK)
    im = Image.blend(im.convert("RGB"), tint, 0.07)

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # 上下绫边：用石青淡染，立轴一裱，重彩感就立住了
    wash(layer, (0, 0, w - 1, band), AZURE_L, 1.0, 3, prog)
    wash(layer, (0, h - band, w - 1, h - 1), AZURE_L, 1.0, 3, prog)
    # 开光底
    wash(layer, (0, band, w - 1, h - band - 1), PAPER_CARD, 1.0, 2, prog)
    # 轴杆：描金双线
    gold_rule(layer, 0, band, w, prog, 3)
    gold_rule(layer, 0, h - band - 3, w, prog, 3)
    ix = (w - im.width) // 2
    iy = band + (ih - im.height) // 2
    layer.alpha_composite(im.convert("RGBA"), (ix, iy))
    outline_rect(layer, 5, 5, w - 6, h - 6, INK, 2, prog, 0.9, 3)
    if label:
        tag = chip(label, 24, accent, GOLD_L if accent == GOLD else AZURE_L)
        layer.alpha_composite(tag, (16, h - band - tag.height - 10))
    return layer


def top_bar(base, p, label="NIMBUS · 新版速览"):
    """顶部：题签 + 一条正在被染满的进度带 + 右上三枚小色点。"""
    tag = chip(label, 25, CINNABAR, CINNABAR_L, pad_x=22, pad_y=11)
    place(base, tag, SAFE_L, 66, 1.0)
    bar = Image.new("RGBA", (CW, 16), (0, 0, 0, 0))
    wash(bar, (0, 4, CW - 1, 12), LINING, 0.7, 2, 1.0)
    outline_rect(bar, 0, 3, CW - 1, 13, INK_S, 1, 1.0, 0.4, 60)
    place(base, bar, SAFE_L, 148, 1.0)
    if p > 0:
        fill = Image.new("RGBA", (CW, 16), (0, 0, 0, 0))
        wash(fill, (2, 5, max(3, int(CW * p)), 11), CINNABAR, 0.85, 3, 1.0)
        place(base, fill, SAFE_L, 148, 1.0)
    d = ImageDraw.Draw(base, "RGBA")
    for i, c in enumerate((AZURE, CINNABAR, GREEN)):
        d.ellipse((SAFE_R - 66 + i * 22, 70, SAFE_R - 54 + i * 22, 82), fill=c + (225,))


def rain_petals(base, t, n=9, y0=-60, speed=3.2, scale=0.9):
    """花瓣飘落：全片通用的收尾氛围。"""
    for i in range(n):
        st = 0.04 + i * 0.09
        p = clamp((t - st) / speed)
        if p <= 0:
            continue
        x = 60 + (i * 137) % (W - 180)
        y = y0 + p * (H + 120)
        sway = math.sin(t * 1.3 + i * 0.9) * 26
        place(base, petal(int(40 * scale) + (i % 3) * 8,
                          (CINNABAR_L, (246, 214, 224), GOLD_L)[i % 3]),
              x + sway, y, 0.9 - p * 0.45, angle=t * 46 + i * 33,
              squeeze=0.65 + 0.35 * abs(math.sin(t * 2 + i)))


# ---------------------------------------------------------------- 场景
def sc_hook(base, t):
    """钩子：宋体画题 + 朱砂主句 + 三张笺卡 + 落印。"""
    # 右上角一枝折枝压角
    bp = clamp(fin(t - 0.10, 0.9))
    if bp > 0:
        br = branch(320, 480)
        crop = br.crop((0, 0, br.width, int(br.height * bp)))
        place(base, crop, SAFE_R - 250, 150, 0.92)

    a = fin(t - 0.05, 0.44)
    t1 = text_img("笔记 · 附件 · 网页", 86, INK, True, 1.22)
    place(base, t1, SAFE_L, 340, a, dy=22 * (1 - a))

    a2 = fin(t - 0.26, 0.44)
    t2 = text_img("离线同步能用了", 104, CINNABAR, True, 1.20)
    if a2 > 0:
        hl = Image.new("RGBA", (t2.width + 28, t2.height + 16), (0, 0, 0, 0))
        wash(hl, (0, 0, hl.width - 1, hl.height - 1), CINNABAR_L, 0.66, 4,
             clamp((t - 0.40) / 0.7), 8)
        place(base, hl, SAFE_L - 14, 470, a2)
    place(base, t2, SAFE_L, 462, a2, dy=22 * (1 - a2))

    # 主句下的描金线，从左往右"描"出来
    up = clamp((t - 0.46) / 0.66)
    if up > 0:
        gl = Image.new("RGBA", (int(t2.width * 0.94), 12), (0, 0, 0, 0))
        gold_rule(gl, 0, 5, t2.width * 0.94, 1.0, 4)
        wipe(base, gl, SAFE_L, 600, up)

    a3 = fin(t - 0.58, 0.36)
    t3 = text_img("Nimbus 3.0 系列 · 官网当前版本说明", 34, INK_S)
    place(base, t3, SAFE_L, 648, a3, dy=14 * (1 - a3))

    # 三张笺卡：文本 / 图片 / 视频
    items = [("笔记", "×2"), ("附件", "×3"), ("网页", "720P")]
    tones = [AZURE, GREEN, GOLD]
    cw = (CW - 2 * 26) // 3
    for i, (k, v) in enumerate(items):
        st = 0.74 + i * 0.18
        p = clamp(back_out((t - st) / 0.58))
        if p <= 0:
            continue
        c, _ = card(cw, 232, PAPER_CARD, INK, 6, seed=80 + i)
        wash(c, (10, 10, cw - 11, 124), tones[i], 0.82, 5,
             clamp((t - st - 0.14) / 0.5), 6)
        z = text_img("0", 62, (255, 250, 240) if tones[i] != GOLD else INK, True)
        c.alpha_composite(z, ((cw - z.width) // 2, 16 + (108 - z.height) // 2))
        tk = text_img(k, 40, INK, True)
        c.alpha_composite(tk, ((cw - tk.width) // 2, 132))
        tv = text_img(v, 26, INK_S)
        c.alpha_composite(tv, ((cw - tv.width) // 2, 188))
        place(base, c, SAFE_L + i * (cw + 26), 736, p, dy=28 * (1 - p),
              scale=0.92 + 0.08 * p, angle=(i - 1) * 1.0)

    # 一道三色染带
    lp = fin(t - 1.40, 0.6)
    if lp > 0:
        band = Image.new("RGBA", (CW, 20), (0, 0, 0, 0))
        seg = CW / 3
        for i, c in enumerate((AZURE, GREEN, CINNABAR)):
            wash(band, (i * seg + 3, 3, (i + 1) * seg - 3, 17), c, 0.95, 3, 1.0)
        wipe(base, band, SAFE_L, 1040, lp)

    stamp(base, "新版", SAFE_R - 130, 1080, t - 1.66, 120)


def sc_proof(base, t):
    """兑现：立轴装裱的官网证据 + 朱砂批印。"""
    a = fin(t - 0.02, 0.42)
    t1 = text_img("新版功能", 94, INK, True, 1.20)
    place(base, t1, SAFE_L, 320, a, dy=24 * (1 - a))

    a2 = fin(t - 0.20, 0.36)
    t2 = text_img("就挂在官网首页", 78, AZURE, True, 1.20)
    place(base, t2, SAFE_L, 452, a2, dy=18 * (1 - a2))

    ep = clamp((t - 0.36) / 0.78)
    ev = evid_card("E09-试用额度与限制.png", CW, 400, "官网 · 新版公告入口", AZURE, prog=ep)
    if ep > 0:
        place(base, ev, SAFE_L, 576, 1.0)

    # 重点用朱笔圈点，只框不涂，截图里的字不能被盖住
    hp = clamp((t - 1.10) / 0.6)
    if hp > 0:
        br = Image.new("RGBA", (CW - 240, 214), (0, 0, 0, 0))
        corner_brackets(br, (6, 6, CW - 247, 207), CINNABAR, hp, 40, 6)
        place(base, br, SAFE_L + 120, 616, 1.0)

    a4 = fin(t - 1.34, 0.34)
    t4 = text_img("不是营销话术，是官网自己的入口", 34, INK_S)
    place(base, t4, SAFE_L, 1000, a4, dy=12 * (1 - a4))

    stamp(base, "真", SAFE_R - 118, 1040, t - 1.52, 104)


def sc_two_ways(base, t):
    """两种用法：两张笺卡 + 中间一枚团花压着"或"字。"""
    a = fin(t - 0.02, 0.42)
    t1 = text_img("两种用法", 90, INK, True, 1.22)
    place(base, t1, SAFE_L, 310, a, dy=20 * (1 - a))

    cw = (CW - 44) // 2
    blocks = [
        ("普通用户", "Nimbus 网页端", "编辑 · 协作\n搜索 · 归档", AZURE, AZURE_L),
        ("开发者", "API 接口", "离线增量\n接入自有脚本", GREEN, GREEN_L),
    ]
    for i, (title, sub, body, ac, sc_) in enumerate(blocks):
        st = 0.18 + i * 0.18
        p = clamp(back_out((t - st) / 0.62))
        if p <= 0:
            continue
        c, _ = card(cw, 402, PAPER_CARD, INK, 6, seed=120 + i)
        badge = chip(title, 32, ac, sc_, pad_x=20, pad_y=10)
        c.alpha_composite(badge, (26, 28))
        gold_rule(c, 26, 96, cw - 26, clamp((t - st - 0.2) / 0.5), 2)
        t2 = text_img(sub, 44, INK, True)
        c.alpha_composite(t2, (26, 116))
        for j, line in enumerate(body.split("\n")):
            t3 = text_img(line, 29, INK_S)
            c.alpha_composite(t3, (26, 214 + j * 46))
        place(base, c, SAFE_L + i * (cw + 44), 468, p, dy=30 * (1 - p),
              angle=(1 if i == 0 else -1) * 1.1 * (1 - p))

    sp = t - 0.74
    if sp > 0:
        p = clamp(back_out(sp / 0.5))
        rd = roundel(124, LINING).copy()
        o = text_img("或", 42, INK, True)
        rd.alpha_composite(o, (62 - o.width // 2, 62 - o.height // 2))
        place(base, rd, SAFE_L + CW // 2 - 62, 636, p, scale=0.82 + 0.18 * p)

    a3 = fin(t - 1.12, 0.34)
    t3 = text_img("不写代码也能用，要接工具才走 API", 34, INK_S)
    place(base, t3, SAFE_L, 958, a3, dy=12 * (1 - a3))


def sc_steps(base, t):
    """开发者五步：描金连线 + 团花序号 + 五张窄笺。"""
    a = fin(t - 0.02, 0.42)
    t1 = text_img("开发者五步", 90, INK, True, 1.22)
    place(base, t1, SAFE_L, 300, a, dy=18 * (1 - a))

    items = ["注册账户", "创建工作区", "装 nimbus 命令行", "连同步地址", "开第一次同步"]
    row_h = 172
    y0 = 468

    # 连线：一条金线自上而下染出来
    lp = clamp((t - 0.36) / 1.1)
    if lp > 0:
        line = Image.new("RGBA", (10, row_h * 5 - 60), (0, 0, 0, 0))
        n = int((row_h * 5 - 60) * lp)
        ImageDraw.Draw(line, "RGBA").line((5, 0, 5, n), fill=GOLD + (215,), width=3)
        place(base, line, SAFE_L + 34, y0 + 42, 1.0)

    for i, it in enumerate(items):
        st = 0.24 + i * 0.16
        p = clamp(back_out((t - st) / 0.5))
        if p <= 0:
            continue
        cy = y0 + i * row_h
        rd = roundel(70, AZURE if i < 4 else GOLD).copy()
        num = text_img(str(i + 1), 32, INK if i < 4 else CINNABAR, True)
        rd.alpha_composite(num, (35 - num.width // 2, 35 - num.height // 2))
        place(base, rd, SAFE_L, cy, p, dy=16 * (1 - p), scale=0.6 + 0.4 * p)

        c, _ = card(CW - 130, 114, PAPER_CARD, INK, 4, seed=160 + i, corner=False)
        tb = text_img(it, 38, INK, True)
        c.alpha_composite(tb, (26, (114 - tb.height) // 2))
        place(base, c, SAFE_L + 96, cy - 20, p, dy=16 * (1 - p))


def sc_code(base, t):
    """三行参数：立轴证据 + 青绢代码笺 + 逐行擦除显现。"""
    a = fin(t - 0.02, 0.42)
    t1 = text_img("三行就能发出去", 82, INK, True, 1.22)
    place(base, t1, SAFE_L, 300, a, dy=18 * (1 - a))

    ep = clamp((t - 0.18) / 0.62)
    ev = evid_card("E06-快速开始-同步地址.png", CW, 226, "官方快速开始", GREEN, prog=ep)
    if ep > 0:
        place(base, ev, SAFE_L, 414, 1.0)

    lines = [
        ("model:", "nimbus-cli 3.0"),
        ("base:", "drive.nimbus.dev"),
        ("auth:", "Bearer YOUR_API_KEY"),
    ]
    code_y = 678
    card_h = 58 * len(lines) + 46
    c, _ = card(CW, card_h, (216, 236, 248), INK, 4, seed=180, corner=False)
    gold_rule(c, 14, 10, CW - 14, fin(t - 0.40, 0.5), 2)
    place(base, c, SAFE_L, code_y, fin(t - 0.34, 0.42), dy=20 * (1 - fin(t - 0.34, 0.42)))
    for i, (k, v) in enumerate(lines):
        st = 0.50 + i * 0.20
        p = fin(t - st, 0.36)
        if p <= 0:
            continue
        kt = text_img(k, 31, INK_S)
        vt = text_img(v, 31, AZURE if i == 0 else INK, i == 0)
        row = Image.new("RGBA", (CW - 60, 42), (0, 0, 0, 0))
        row.alpha_composite(kt, (0, 0))
        row.alpha_composite(vt, (kt.width + 16, 0))
        wipe(base, row, SAFE_L + 26, code_y + 24 + i * 58, p)

    cb = t - 1.26
    if cb > 0 and int(cb * 2.2) % 2 == 0:
        cur = Image.new("RGBA", (7, 32), (0, 0, 0, 0))
        ImageDraw.Draw(cur).rectangle((0, 0, 6, 31), fill=CINNABAR + (225,))
        place(base, cur, SAFE_L + 30 + 210, code_y + 24 + 2 * 58 + 5, 1.0)

    tag = chip("复制即用", 28, GREEN, GREEN_L)
    a3 = fin(t - 1.44, 0.36)
    place(base, tag, SAFE_L, code_y + card_h + 30, a3, dy=16 * (1 - a3))


def sc_free_range(base, t):
    """能力范围：三行立轴证据 + 右侧朱砂圆印 NEW。"""
    a = fin(t - 0.02, 0.42)
    t1 = text_img("哪些新版能用", 86, INK, True, 1.22)
    place(base, t1, SAFE_L, 268, a, dy=18 * (1 - a))

    rows = [
        ("E03-能力表-多人协作", "笔记协作 ×3", "多人同时编辑", AZURE),
        ("E04-能力表-附件版本", "附件版本 ×5", "保留 30 天版本", GREEN),
        ("E01-能力表-离线同步", "网页剪藏 不限页", "自动打标签", CINNABAR),
    ]
    for i, (ev_name, k, v, ac) in enumerate(rows):
        st = 0.20 + i * 0.18
        p = clamp(back_out((t - st) / 0.56))
        if p <= 0:
            continue
        cy = 398 + i * 246
        c, _ = card(CW, 224, PAPER_CARD, INK, 6, seed=190 + i, corner=False)
        # 标题区染一条主色，三行用石青/石绿/朱砂区分，颜色本身就是信息
        wash(c, (10, 10, CW - 11, 60), ac, 0.46, 4, clamp((t - st - 0.10) / 0.5), 4)
        tk = text_img(k, 38, INK, True)
        c.alpha_composite(tk, (26, 14))
        tv = text_img(v, 26, INK_S)
        c.alpha_composite(tv, (26 + tk.width + 18, 26))
        gold_rule(c, 26, 62, CW - 150, clamp((t - st - 0.18) / 0.4), 2)
        ev = open_evidence(ev_name, CW - 56, 148, prefer_light=True).convert("RGB")
        ev = ImageEnhance.Color(ev).enhance(0.86)
        tint = Image.new("RGB", ev.size, SILK)
        ev = Image.blend(ev, tint, 0.07)
        c.alpha_composite(ev.convert("RGBA"), (26, 72))
        lp = clamp(fin(t - st - 0.28, 0.44))
        if lp > 0:
            tag = roundel(106, ac).copy()
            z = text_img("含", 36, INK, True)
            tag.alpha_composite(z, ((106 - z.width) // 2, (106 - z.height) // 2))
            c.alpha_composite(tag, (CW - 126, 14))
        place(base, c, SAFE_L, cy, p, dy=24 * (1 - p), angle=(i - 1) * 0.7)


def sc_zero(base, t):
    """能力证据：旧版本号被胭脂划掉 + 字色由淡染到浓 + 立轴 + 落印。"""
    a = fin(t - 0.02, 0.42)
    t1 = text_img("网页剪藏 不限页", 72, INK, True, 1.22)
    place(base, t1, SAFE_L, 288, a, dy=16 * (1 - a))

    a2 = fin(t - 0.24, 0.34)
    old = text_img("旧版只能同步 1 台", 42, INK_S, True)
    place(base, old, SAFE_L, 388, a2)
    sp = clamp((t - 0.56) / 0.44)
    if sp > 0:
        strike = Image.new("RGBA", (old.width + 18, 12), (0, 0, 0, 0))
        ImageDraw.Draw(strike, "RGBA").line((0, 6, old.width + 18, 6), fill=ROSE + (235,),
                                            width=5)
        wipe(base, strike, SAFE_L - 4, 388 + old.height // 2 - 8, sp)

    a3 = fin(t - 0.66, 0.34)
    lab = text_img("当前版本说明", 32, INK_S, True)
    place(base, lab, SAFE_L, 468, a3)

    rp = clamp((t - 0.78) / 1.0)
    val = 1 + 2 * soft_out(rp)
    num_s = "3" if rp >= 0.999 else f"{val:.1f}"
    num = text_img(num_s, 130, CINNABAR, True)
    place(base, num, SAFE_L, 518, a3)
    unit = text_img("台设备", 44, INK, True)
    place(base, unit, SAFE_L + num.width + 14, 596, a3)

    ep = clamp((t - 1.02) / 0.62)
    ev = evid_card("E01-能力表-离线同步.png", CW, 190, "官网版本说明页", GOLD, prog=ep)
    if ep > 0:
        place(base, ev, SAFE_L, 706, 1.0)

    # 朱笔圈点定价那一行，不涂面
    hp = clamp((t - 1.38) / 0.6)
    if hp > 0:
        br = Image.new("RGBA", (CW - 180, 104), (0, 0, 0, 0))
        corner_brackets(br, (6, 6, CW - 187, 97), CINNABAR, hp, 32, 5)
        place(base, br, SAFE_L + 80, 752, 1.0)

    a5 = fin(t - 1.58, 0.32)
    t5 = text_img("nimbus-desktop-3.0 · 官网当前说明", 32, INK_S)
    place(base, t5, SAFE_L, 918, a5, dy=12 * (1 - a5))

    stamp(base, "零", SAFE_R - 116, 1000, t - 1.70, 104)


def sc_limits(base, t):
    """三条限制：胭脂题头 + 三张淡赭笺 + 各压一枚朱砂小印。"""
    a = fin(t - 0.02, 0.42)
    t1 = text_img("但有三条限制", 86, ROSE, True, 1.22)
    place(base, t1, SAFE_L, 288, a, dy=18 * (1 - a))

    rows = [
        ("新版灰度中，还没全量放开", "时"),
        ("有 TPS 和公平使用配额", "额"),
        ("Agent Plan 按刊例价折算 Credits", "折"),
    ]
    for i, (txt, ch) in enumerate(rows):
        st = 0.22 + i * 0.18
        p = clamp(back_out((t - st) / 0.54))
        if p <= 0:
            continue
        cy = 428 + i * 172
        c, _ = card(CW, 140, OCHRE_L, ROSE, 6, seed=230 + i, corner=False)
        # 左侧一条胭脂色标，"限制"的分量靠色块而不是靠文字加大
        wash(c, (10, 10, 22, 129), ROSE, 0.95, 3, 1.0)
        # 印章直接贴进卡面：走 alpha_composite 才能被 mgkit 登记到卡内相对坐标，
        # 用 place() 会以卡片局部坐标去查全屏网格，坐标错位。
        c.alpha_composite(seal(ch, 92), (CW - 122, 24))
        tb = text_img(txt, 35, INK, True)
        c.alpha_composite(tb, (44, (140 - tb.height) // 2))
        place(base, c, SAFE_L, cy, p, dy=22 * (1 - p), angle=(i - 1) * 0.8)

    a2 = fin(t - 1.22, 0.32)
    t2 = text_img("最终以平台公告和你的账户账单为准", 32, INK_S)
    place(base, t2, SAFE_L, 988, a2, dy=12 * (1 - a2))


def sc_end(base, t):
    """收尾：花瓣飘落 + 大问句 + 竖排落款 + 匾额关注条 + 压角印。"""
    rain_petals(base, t, n=10, speed=3.0, scale=1.0)

    a = fin(t - 0.05, 0.44)
    t1 = text_img("你最想先试哪个？", 90, INK, True, 1.20)
    place(base, t1, SAFE_L, 468, a, dy=24 * (1 - a))

    a2 = fin(t - 0.26, 0.34)
    t2 = text_img("评论区告诉我，我下期实测", 42, AZURE, True)
    place(base, t2, SAFE_L, 618, a2, dy=16 * (1 - a2))

    lp = clamp((t - 0.42) / 0.52)
    if lp > 0:
        gl = Image.new("RGBA", (CW, 12), (0, 0, 0, 0))
        gold_rule(gl, 0, 5, CW, 1.0, 4)
        wipe(base, gl, SAFE_L, 722, lp)

    # 右侧竖排落款
    vp = clamp((t - 0.50) / 0.9)
    if vp > 0:
        vt = vertical_text("下期继续拆", 44, INK)
        crop = vt.crop((0, 0, vt.width, int(vt.height * vp)))
        place(base, crop, SAFE_R - 68, 790, 1.0)
        vt2 = vertical_text("AI 很好用", 44, INK)
        crop2 = vt2.crop((0, 0, vt2.width, int(vt2.height * clamp((vp - 0.3) / 0.7))))
        place(base, crop2, SAFE_R - 136, 790, 1.0)

    a3 = fin(t - 0.62, 0.32)
    t3 = text_img("下期实测", 34, INK_S)
    place(base, t3, SAFE_L, 790, a3, dy=12 * (1 - a3))

    pa = t - 0.84
    if pa > 0:
        p = clamp(back_out(pa / 0.44))
        btn, _ = card(520, 96, CINNABAR_L, CINNABAR, 6, seed=250, corner=False)
        wash(btn, (0, 0, 519, 95), CINNABAR, 0.20, 3, 1.0)
        bt = text_img("关注我 · 只测官网写得清的", 33, (255, 250, 242), True)
        btn.alpha_composite(bt, ((520 - bt.width) // 2, (96 - bt.height) // 2))
        place(base, btn, SAFE_L, 880, p, scale=0.95 + 0.05 * p)

    stamp(base, "实测", SAFE_L + 546, 872, t - 1.10, 112)


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
    base = silk_bg().copy()
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
    sheet = Image.new("RGB", (cw * cols, ch * rows), (232, 228, 218))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧H-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 28), fill=(58, 51, 44))
        td.text((8, 3), f"{t:.1f}s", font=font(18, True), fill=(242, 234, 216))
        sheet.paste(thumb, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(HERE / "检查图-MG样片H.png")
    write_report(GUARD, HERE, "H 工笔画")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片H.png")
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
    out = HERE / "MG-样片H-工笔画-无声.mp4"
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
