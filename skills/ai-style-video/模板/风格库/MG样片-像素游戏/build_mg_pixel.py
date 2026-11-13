#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例选题（虚构）Nimbus 3.0 新版速览 · MG 样片 E（8-bit 像素游戏风）

前四版：A 深色科技 / B 亮色杂志 / C 复古拼贴 / D 故障艺术
本版：全部画面在 360×640 低分辨率渲染，再 ×3 最近邻放大到 1080×1920。
      连官网截图都会变成像素 sprite，等于自带 8-bit 滤镜。

视觉语言：
- 4×4 Bayer 有序抖动渐变背景（真·8-bit 背景）
- 自绘 5×7 点阵字（HUD、英文、数字）
- 程序化像素 sprite（金币、宝箱、闪电、星星、宝箱碎屑）
- 游戏 HUD：关卡、血量、金币数、进度
- 画面抖动、闪白、币雨、碎块爆开

用法：
    python build_mg_pixel.py --preview   # 只出关键帧检查图
    python build_mg_pixel.py             # 渲染无声 MP4
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageOps

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
                     safe_left=22, safe_right=0)

SHOTS = SHOTS_DIR  # 由 mgkit.paths 解析（MG_SHOTS_DIR 可覆盖）
EVID = EVID_DIR    # 由 mgkit.paths 解析（MG_EVID_DIR 可覆盖）

W, H = 1080, 1920

# 内部低分辨率画布（×3 整数放大 = 干净像素块）
LW, LH = 360, 640
SCALE = 3

# 中文没法用 5×7 点阵，小字回退到系统粗黑；字体路径由 mgkit/fonts.py 按角色解析。

# ---- 8-bit 调色板（有限色，像素游戏的味道来自色数少）----
BG0 = (12, 16, 32)        # 深蓝黑
BG1 = (26, 32, 62)        # 渐变亮端
CARD = (22, 28, 52)
LINE = (58, 70, 116)
WHITE = (240, 244, 255)
CYAN = (72, 226, 240)
GOLD = (252, 196, 48)
GREEN = (88, 224, 120)
RED = (240, 88, 96)
MAGENTA = (216, 104, 240)
GREY = (140, 152, 190)

SAFE_L = 22
SAFE_R = LW - 22
CW = SAFE_R - SAFE_L

TOTAL = 24.8
NFRAMES = round(TOTAL * FPS)
YOFF = 130

random.seed(20261112)


# ---------------------------------------------------------------- 5×7 点阵字
FONT5X7 = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.",
    "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####",
    "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.###.",
    "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": ".###.|..#..|..#..|..#..|..#..|..#..|.###.",
    "J": "..###|...#.|...#.|...#.|...#.|#..#.|.##..",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#",
    "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#...#|#...#|#...#|#...#",
    "N": "#...#|##..#|#.#.#|#..##|#...#|#...#|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.",
    "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#",
    "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.",
    "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#...#|#.#.#|##.##|#...#",
    "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
    "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": "..#..|.##..|..#..|..#..|..#..|..#..|.###.",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": "####.|....#|....#|.###.|....#|....#|####.",
    "4": "#..#.|#..#.|#..#.|#####|...#.|...#.|...#.",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": "..##.|.#...|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    "9": ".###.|#...#|#...#|.####|....#|...#.|.##..",
    " ": ".....|.....|.....|.....|.....|.....|.....",
    ".": ".....|.....|.....|.....|.....|.##..|.##..",
    ",": ".....|.....|.....|.....|.##..|.##..|.#...",
    ":": ".....|.##..|.##..|.....|.##..|.##..|.....",
    "!": "..#..|..#..|..#..|..#..|..#..|.....|..#..",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..",
    "-": ".....|.....|.....|#####|.....|.....|.....",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    "/": "....#|....#|...#.|..#..|.#...|#....|#....",
    "=": ".....|.....|#####|.....|#####|.....|.....",
    "%": "##..#|##.#.|..#..|.#...|#..##|.#.##|#....",
    "*": ".....|#.#.#|.###.|#####|.###.|#.#.#|.....",
    "#": ".#.#.|.#.#.|#####|.#.#.|#####|.#.#.|.#.#.",
    ">": ".#...|..#..|...#.|....#|...#.|..#..|.#...",
    "<": "...#.|..#..|.#...|#....|.#...|..#..|...#.",
    "(": "...#.|..#..|.#...|.#...|.#...|..#..|...#.",
    ")": ".#...|..#..|...#.|...#.|...#.|..#..|.#...",
    "[": "..###|..#..|..#..|..#..|..#..|..#..|..###",
    "]": "###..|..#..|..#..|..#..|..#..|..#..|###..",
    "'": "..#..|..#..|.....|.....|.....|.....|.....",
    "_": ".....|.....|.....|.....|.....|.....|#####",
}


@lru_cache(maxsize=256)
def pixel_text(s, px=1, color=WHITE):
    """用 5×7 点阵字渲染字符串，px 为像素块大小。"""
    s = s.upper()
    cw = 6 * px
    ch = 8 * px
    im = Image.new("RGBA", (max(1, len(s) * cw), ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, chx in enumerate(s):
        glyph = FONT5X7.get(chx)
        if not glyph:
            continue
        rows = glyph.split("|")
        for ry, row in enumerate(rows):
            for rx, cell in enumerate(row):
                if cell == "#":
                    d.rectangle((i * cw + rx * px, ry * px,
                                 i * cw + rx * px + px - 1, ry * px + px - 1),
                                fill=color + (255,))
    return mark_text_layer(im, s)


def text_w(s, px=1):
    return len(s) * 6 * px


def sysfont(size):
    return load_font("sans_bold", int(size))


# ---------------------------------------------------------------- 精灵
SPRITES = {
    "coin": [
        "..####..",
        ".######.",
        "##.##.##",
        "#.####.#",
        "#.####.#",
        "##.##.##",
        ".######.",
        "..####..",
    ],
    "star": [
        "...#...",
        "..###..",
        ".#####.",
        "#######",
        ".#####.",
        "..###..",
        ".##.##.",
    ],
    "bolt": [
        "...##..",
        "...##..",
        "..###..",
        ".#####.",
        "..###..",
        "####...",
        "###....",
        ".##....",
        ".##....",
    ],
    "chest": [
        "############",
        "#..........#",
        "#.########.#",
        "#.#......#.#",
        "#.#......#.#",
        "#.########.#",
        "#..........#",
        "####....####",
        ".##########.",
    ],
    "heart": [
        ".##.##.",
        "#######",
        "#######",
        "#######",
        ".#####.",
        "..###..",
        "...#...",
    ],
    "key": [
        "##......",
        "###.....",
        "##......",
        "..##....",
        "..##....",
        "..##....",
        "..####..",
        "..####..",
    ],
}


def sprite(name, px=1, tint=None):
    """渲染像素精灵，tint 为可选单色替换。"""
    rows = SPRITES[name]
    h = len(rows)
    w = len(rows[0])
    im = Image.new("RGBA", (w * px, h * px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for ry, row in enumerate(rows):
        for rx, cell in enumerate(row):
            if cell == "#":
                col = tint or WHITE
                d.rectangle((rx * px, ry * px, rx * px + px - 1, ry * px + px - 1),
                            fill=col + (255,))
    return im


# ---------------------------------------------------------------- 背景
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


@lru_cache(maxsize=1)
def bg_dither():
    """4×4 有序抖动垂直渐变，真·8-bit 背景。"""
    im = Image.new("RGB", (LW, LH))
    px = im.load()
    for y in range(LH):
        t = y / (LH - 1)
        for x in range(LW):
            thr = BAYER4[y % 4][x % 4] / 16.0
            # 上半段更亮，形成"地平线"
            v = 1.0 - abs(t - 0.34) * 1.5
            v = max(0.0, min(1.0, v))
            if t < 0.30 and v > thr * 0.5:
                px[x, y] = BG1
            else:
                px[x, y] = BG0
    return im


def draw_bg(base):
    base.paste(bg_dither(), (0, 0))
    d = ImageDraw.Draw(base, "RGBA")
    # 星星（固定位置，每帧一致）
    for _ in range(46):
        x = random.randint(0, LW - 1)
        y = random.randint(0, int(LH * 0.55))
        if 0 <= y < LH:
            d.rectangle((x, y, x, y), fill=(120, 132, 170, 190))
    # 地面网格
    for x in range(0, LW, 24):
        d.rectangle((x, LH - 44, x, LH - 43), fill=LINE + (110,))
    d.rectangle((0, LH - 44, LW, LH - 43), fill=LINE + (150,))


def place(base, layer, x, y, a=1.0, dy=0):
    if a <= 0.002:
        return
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


def clamp(x):
    return max(0.0, min(1.0, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x * x


def back_out(x, s=1.8):
    x = clamp(x)
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def fin(t, dur=0.30):
    return ease_out(t / dur)


def fout(t, dur=0.22):
    return ease_in(t / dur)


def big_text(s, size, color=WHITE, bold=True):
    """系统字渲染在低分辨率画布上 → 天然像素感。"""
    f = sysfont(size)
    im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    bb = f.getbbox(s)
    w, h = max(1, bb[2] - bb[0]), max(1, bb[3] - bb[1])
    im = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((6 - bb[0], 6 - bb[1]), s, font=f, fill=color + (255,))
    return mark_text_layer(im, s.replace("\n", " / "))


def panel(w, h, fill=CARD, border=CYAN, bw=1):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=fill + (255,), outline=border + (255,), width=bw)
    # 四角像素缺口
    for cx, cy in ((0, 0), (w - 3, 0), (0, h - 3), (w - 3, h - 3)):
        d.rectangle((cx, cy, cx + 2, cy + 2), fill=BG0 + (255,))
    return im


def shot_sprite(name, box, w, h, label=None):
    """官网截图放进像素框。

    命中映射表时用 2x 高清证据图（文字清晰 2 倍）。
    低分辨率下白底官网截图会变成刺眼白块，所以统一反相 + 青调，
    从白底纸片变成暗色 CRT 终端窗，和 8-bit 背景同调。
    """
    im, _ = load_evidence_or_raw(SHOTS / name, box, w, h, invert=True,
                                 color=0.88, brightness=0.82)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.rectangle((0, 0, w - 1, h - 1), fill=(8, 10, 20, 255), outline=CYAN + (255,), width=1)
    bar = 10
    d.rectangle((0, 0, w - 1, bar), fill=(30, 38, 66, 255))
    d.rectangle((0, bar, w - 1, bar + 1), fill=CYAN + (200,))
    for i, c in enumerate((RED, GOLD, GREEN)):
        d.rectangle((4 + i * 5, 3, 7 + i * 5, 6), fill=c + (255,))
    if label:
        lt = pixel_text(label, 1, CYAN)
        out.alpha_composite(lt, (20, 1))
    ip = 3
    src = im.convert("RGBA")
    out.alpha_composite(src, (ip + (w - 2 * ip - src.width) // 2,
                               bar + ip + (h - bar - 2 * ip - src.height) // 2))
    return out


# ---------------------------------------------------------------- HUD
# 每个场景的对话框台词（RPG 对话框，填补下方空间）
DIALOG = {
    1: ("旁白", "笔记 附件 网页 三项新能力都放开了"),
    2: ("旁白", "新功能就挂在官网首页，不是宣传话术"),
    3: ("系统", "普通人走网页端，重度用户走命令行"),
    4: ("系统", "五步：注册 建区 装工具 连地址 开同步"),
    5: ("系统", "client / sync / auth，三行就够"),
    6: ("系统", "笔记 ×3 附件 ×5 网页剪藏不限"),
    7: ("系统", "桌面端 离线同步 当前版本 支持三台设备"),
    8: ("系统", "注意：灰度中，有设备数上限，按套餐折算"),
    9: ("旁白", "你最想先试哪个？评论区告诉我，下期实测"),
}


def hud(base, t, stage="STAGE 1", scene=1):
    """游戏 HUD：关卡号、金币数、进度格、血条、RPG 对话框。"""
    d = ImageDraw.Draw(base, "RGBA")
    st = pixel_text(stage, 1, GOLD)
    place(base, st, SAFE_L, 4, 1.0)
    coin = sprite("coin", 1, GOLD)
    place(base, coin, SAFE_R - 92, 2, 1.0)
    cn = pixel_text(f"x{int(t/TOTAL*99):02d}", 1, GOLD)
    place(base, cn, SAFE_R - 76, 5, 1.0)

    # 顶部进度（像素格子）
    p = t / TOTAL
    cells = 30
    for i in range(cells):
        x = SAFE_L + i * ((CW) // cells)
        on = (i / cells) <= p
        d.rectangle((x, 14, x + 6, 16), fill=(CYAN if on else LINE) + (220,))

    # 底部：RPG 对话框
    box_y = LH - 118
    d.rectangle((SAFE_L, box_y, SAFE_R, LH - 26), fill=(10, 14, 28, 255),
                outline=CYAN + (255,), width=1)
    d.rectangle((SAFE_L, box_y, SAFE_R, box_y + 14), fill=(30, 38, 66, 255))
    name, line = DIALOG.get(scene, ("", ""))
    # 名字用系统字（中文点阵字不支持）
    nt = big_text(name, 13, GOLD)
    d.rectangle((SAFE_L + 2, box_y - 1, SAFE_L + 12 + nt.width, box_y + 17),
                fill=(10, 14, 28, 255), outline=GOLD + (255,), width=1)
    base.alpha_composite(nt, (SAFE_L + 7, box_y + 2))
    # 对话正文逐字显现（系统字，低分辨率下自带像素感）
    shown = line[:max(1, int(len(line) * clamp((t % 3.4) / 3.2)))]
    lt = big_text(shown, 14, WHITE)
    base.alpha_composite(lt, (SAFE_L + 8, box_y + 26))
    if int(t * 3) % 2 == 0:
        d.rectangle((SAFE_L + 12 + lt.width, box_y + 28, SAFE_L + 20 + lt.width, box_y + 38),
                    fill=WHITE + (220,))

    # 底部血量
    for i in range(3):
        place(base, sprite("heart", 1, RED if i < 2 else GREY), SAFE_L + i * 10, LH - 18, 1.0)


# ---------------------------------------------------------------- 场景
def sc_hook(base, t):
    """钩子：STAGE 1 标题 + 金币雨 + 数据小面板 + 像素角色。"""
    a = fin(t - 0.05, 0.25)
    t1 = big_text("笔记 附件 网页", 26, WHITE)
    place(base, t1, SAFE_L, 40, a)

    a2 = fin(t - 0.28, 0.25)
    t2 = big_text("全部含在新版", 34, GOLD)
    place(base, t2, SAFE_L, 80, a2)

    # 金币雨
    for i in range(16):
        st = 0.35 + i * 0.05
        p = clamp((t - st) / 1.6)
        if p <= 0:
            continue
        x = 24 + (i * 23) % (LW - 48)
        y = 128 + p * 300
        c = sprite("coin", 1, GOLD)
        if int(p * 8) % 2 == 0:
            c = c.resize((max(1, c.width // 2), c.height), Image.NEAREST)
        place(base, c, x, y, 1.0 - p * 0.25)

    # 三块数据面板
    items = [("TEXT", "x2", "0"), ("IMG", "x3", "0"), ("VID", "720P", "0")]
    cw = (CW - 12) // 3
    for i, (k, sub, v) in enumerate(items):
        st = 0.85 + i * 0.13
        p = back_out((t - st) / 0.4)
        if p <= 0:
            continue
        c = panel(cw, 74)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, cw - 1, 2), fill=(CYAN, MAGENTA, GREEN)[i] + (255,))
        kt = pixel_text(k, 1, (CYAN, MAGENTA, GREEN)[i])
        c.alpha_composite(kt, (6, 9))
        stx = pixel_text(sub, 1, GREY)
        c.alpha_composite(stx, (6, 22))
        vt = pixel_text(v, 3, WHITE)
        c.alpha_composite(vt, (6, 40))
        place(base, c, SAFE_L + i * (cw + 6), 300, p, dy=10 * (1 - p))

    # 钥匙精灵（代表 API Key）
    kp = back_out((t - 1.30) / 0.45)
    if kp > 0:
        place(base, sprite("key", 2, CYAN), SAFE_L + 4, 392, kp, dy=-8 * (1 - kp))

    a3 = fin(t - 1.55, 0.28)
    t3 = pixel_text("CURRENT TRIAL PRICE", 1, GREY)
    place(base, t3, SAFE_L + 60, 404, a3)


def sc_proof(base, t):
    """兑现：宝箱开启 + 官网首页截图弹出 + 星星闪。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("新版功能", 30, WHITE)
    place(base, t1, SAFE_L, 80, a)
    t1b = big_text("就挂在官网首页", 24, CYAN)
    place(base, t1b, SAFE_L, 120, fin(t - 0.14, 0.25))

    # 宝箱
    cp = back_out((t - 0.26) / 0.45)
    if cp > 0:
        ch = sprite("chest", 2, GOLD)
        place(base, ch, SAFE_L + 4, 175, cp, dy=-12 * (1 - cp))

    # 打开时星星迸发
    op = t - 0.70
    if op > 0:
        for i in range(8):
            ang = i * math.pi / 4
            dist = 12 + op * 70
            x = SAFE_L + 4 + 12 + math.cos(ang) * dist
            y = 175 + 8 + math.sin(ang) * dist
            place(base, sprite("star", 1, GOLD), x, y, max(0.0, 1 - op / 1.1))

    shot = shot_sprite("01-官网首页-新版公告.jpg", (300, 155, 1000, 262),
                        CW, 88, "HOME")
    p = back_out((t - 0.40) / 0.45)
    place(base, shot, SAFE_L, 270, p, dy=10 * (1 - p))

    a2 = fin(t - 1.15, 0.28)
    t2 = pixel_text("NOT MARKETING TALK", 1, GREY)
    place(base, t2, SAFE_L, 372, a2)
    t2b = big_text("官网自己的入口", 18, WHITE)
    place(base, t2b, SAFE_L, 388, a2)

    # 状态
    if t > 1.0:
        d = ImageDraw.Draw(base, "RGBA")
        d.rectangle((SAFE_L, 430, SAFE_L + 120, 431), fill=GREEN + (255,))
        d.rectangle((SAFE_L, 434, SAFE_L + 46, 438), fill=GREEN + (255,))
        st = pixel_text("FOUND", 1, GREEN)
        place(base, st, SAFE_L + 52, 430, 1.0)


def sc_two_ways(base, t):
    """两种用法：两个关卡门选择 + 中间 OR 开关。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("两种用法", 28, WHITE)
    place(base, t1, SAFE_L, 80, a)

    cw = (CW - 14) // 2
    blocks = [
        ("普通用户", "PAVO", "编辑 协作\n归档", CYAN),
        ("开发者", "API", "离线同步\n接自己脚本", MAGENTA),
    ]
    for i, (title, tag, body, ac) in enumerate(blocks):
        st = 0.20 + i * 0.16
        p = back_out((t - st) / 0.45)
        if p <= 0:
            continue
        c = panel(cw, 150)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, cw - 1, 3), fill=ac + (255,))
        tb = big_text(title, 18, ac)
        c.alpha_composite(tb, (8, 12))
        tg = pixel_text(tag, 1, GREY)
        c.alpha_composite(tg, (8, 40))
        for j, ln in enumerate(body.split("\n")):
            tt = big_text(ln, 13, WHITE)
            c.alpha_composite(tt, (8, 62 + j * 26))
        place(base, c, SAFE_L + i * (cw + 14), 130, p, dy=12 * (1 - p))

    # OR 开关
    sp = t - 0.70
    if sp > 0:
        sw = Image.new("RGBA", (34, 34), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sw)
        sd.rectangle((0, 0, 33, 33), fill=BG0 + (255,), outline=GOLD + (255,), width=1)
        o = pixel_text("OR", 1, GOLD)
        sw.alpha_composite(o, (17 - o.width // 2, 13))
        place(base, sw, SAFE_L + CW // 2 - 17, 185, fin(sp, 0.3))

    # 底部说明
    a3 = fin(t - 1.00, 0.28)
    t3 = big_text("不写代码也能用", 16, WHITE)
    place(base, t3, SAFE_L, 300, a3)
    t3b = big_text("要接工具才走 API", 16, GREY)
    place(base, t3b, SAFE_L, 326, a3)


def sc_steps(base, t):
    """五步：任务列表 + 星星 + 逐条完成。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("开发者五步", 28, WHITE)
    place(base, t1, SAFE_L, 80, a)

    items = ["注册账户", "创建工作区", "选 3.0-flash", "连同步地址", "开第一次同步"]
    for i, it in enumerate(items):
        st = 0.22 + i * 0.15
        p = fin(t - st, 0.26)
        if p <= 0:
            continue
        cy = 130 + i * 58
        d = ImageDraw.Draw(base, "RGBA")
        # 序号
        d.rectangle((SAFE_L, cy, SAFE_L + 20, cy + 20), fill=CYAN + (255,))
        n = pixel_text(f"{i+1}", 1, BG0)
        base.alpha_composite(n, (SAFE_L + 6, cy + 6))
        # 文字
        tb = big_text(it, 17, WHITE)
        place(base, tb, SAFE_L + 30, cy + 1, p)
        # 进度条
        d.rectangle((SAFE_L + 30, cy + 30, SAFE_R - 46, cy + 32), fill=LINE + (180,))
        d.rectangle((SAFE_L + 30, cy + 30, SAFE_L + 30 + int((CW - 76) * p), cy + 32),
                    fill=CYAN + (255,))
        # 完成星星
        if t > st + 0.42:
            cp = fin(t - st - 0.42, 0.26)
            place(base, sprite("star", 1, GOLD), SAFE_R - 14, cy + 2, cp)


def sc_code(base, t):
    """三行参数：终端框 + 逐行解码 + 闪电施法。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("三行就能发出去", 26, WHITE)
    place(base, t1, SAFE_L, 76, a)

    shot = shot_sprite("03-快速开始-工作区与首次同步.jpg", (0, 150, 1396, 1420),
                        CW, 150, "DOC")
    p = back_out((t - 0.16) / 0.45)
    place(base, shot, SAFE_L, 120, p, dy=12 * (1 - p))

    lines = [
        ("CLIENT", "nimbus-cli 3.0", CYAN),
        ("SYNC", "drive.nimbus.dev", WHITE),
        ("AUTH", "Bearer YOUR_API_KEY", WHITE),
    ]
    code_y = 288
    c = panel(CW, 78, (10, 14, 28), MAGENTA, 1)
    cd = ImageDraw.Draw(c)
    cd.rectangle((0, 0, CW - 1, 11), fill=(30, 38, 66, 255))
    for i, cc in enumerate((RED, GOLD, GREEN)):
        cd.rectangle((4 + i * 5, 3, 7 + i * 5, 6), fill=cc + (255,))
    place(base, c, SAFE_L, code_y, fin(t - 0.34, 0.3), dy=10 * (1 - fin(t - 0.34, 0.3)))

    for i, (k, v, col) in enumerate(lines):
        st = 0.50 + i * 0.18
        p = fin(t - st, 0.26)
        if p <= 0:
            continue
        kt = pixel_text(k, 1, GREY)
        vt = pixel_text(v[:max(1, int(len(v) * clamp((t - st) / 0.45)))], 1, col)
        row = Image.new("RGBA", (CW - 12, 12), (0, 0, 0, 0))
        row.alpha_composite(kt, (6, 2))
        row.alpha_composite(vt, (6 + kt.width + 8, 2))
        place(base, row, SAFE_L + 3, code_y + 16 + i * 20, p)

    # 施法闪电
    bp = t - 1.30
    if bp > 0:
        bol = sprite("bolt", 2, GOLD)
        place(base, bol, SAFE_R - 30, code_y + 24, fin(bp, 0.3),
              dy=-6 * (1 - fin(bp, 0.3)))
        ct = pixel_text("CAST", 1, GOLD)
        place(base, ct, SAFE_L, code_y + 90, fin(bp, 0.25))


def sc_free_range(base, t):
    """能力范围：道具栏 3 件 + 已解锁标记。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("哪些新版能用", 26, WHITE)
    place(base, t1, SAFE_L, 80, a)

    rows = [
        ("NOTE x3", "多人同时编辑", CYAN),
        ("FILE x5", "保留 30 天版本", MAGENTA),
        ("WEB CLIP", "自动打标签", GREEN),
    ]
    for i, (k, v, ac) in enumerate(rows):
        st = 0.22 + i * 0.16
        p = back_out((t - st) / 0.42)
        if p <= 0:
            continue
        cy = 130 + i * 72
        c = panel(CW, 60)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, 3, 59), fill=ac + (255,))
        # 勾
        cd.rectangle((10, 22, 20, 32), outline=ac + (255,), width=1)
        cd.rectangle((17, 27, 21, 31), fill=ac + (255,))
        cd.rectangle((21, 25, 25, 29), fill=ac + (255,))
        kt = big_text(k, 15, WHITE)
        c.alpha_composite(kt, (34, 10))
        vt = big_text(v, 12, GREY)
        c.alpha_composite(vt, (34, 34))
        place(base, c, SAFE_L, cy, p, dy=10 * (1 - p))


def sc_zero(base, t):
    """能力证据：BOSS 血条掉落 + 版本页 + 命中框。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("网页剪藏 不限页", 22, WHITE)
    place(base, t1, SAFE_L, 76, a)

    a2 = fin(t - 0.24, 0.26)
    old = big_text("旧版只能同步 1 台", 15, GREY)
    place(base, old, SAFE_L, 110, a2)
    sp = fin(t - 0.54, 0.34)
    if sp > 0:
        strike = Image.new("RGBA", (old.width + 4, 3), (0, 0, 0, 0))
        ImageDraw.Draw(strike).rectangle((0, 0, old.width + 4, 2), fill=RED + (255,))
        place(base, strike, SAFE_L, 110 + old.height // 2, sp)

    a3 = fin(t - 0.66, 0.24)
    lab = pixel_text("DEVICES", 1, GREY)
    place(base, lab, SAFE_L, 146, a3)

    # BOSS 血条掉落
    rp = clamp((t - 0.76) / 1.0)
    val = 1 + 2 * ease_out(rp)
    num_s = "3" if rp >= 0.999 else f"{val:.1f}"
    num = big_text(num_s, 40, GOLD)
    place(base, num, SAFE_L, 160, a3)
    unit = big_text("台", 16, WHITE)
    place(base, unit, SAFE_L + num.width + 4, 190, a3)

    # 血条
    d = ImageDraw.Draw(base, "RGBA")
    d.rectangle((SAFE_L, 208, SAFE_R, 216), fill=(40, 20, 30, 255))
    bp = int((CW) * rp)
    d.rectangle((SAFE_L, 208, SAFE_L + bp, 216), fill=GOLD + (255,))

    shot = shot_sprite("07-版本能力-离线同步说明.jpg", (0, 700, 1396, 822),
                        CW, 66, "PLANS")
    p = back_out((t - 0.98) / 0.45)
    place(base, shot, SAFE_L, 236, p, dy=10 * (1 - p))

    # 命中框
    hp = t - 1.40
    if hp > 0:
        ha = fin(hp, 0.28)
        d = ImageDraw.Draw(base, "RGBA")
        x, y, w, h = SAFE_R - 92, 244, 74, 26
        for cx, cy, sx, sy in ((x, y, 1, 1), (x + w, y, -1, 1),
                                (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
            px_ = cx if sx > 0 else cx - 7
            py_ = cy if sy > 0 else cy - 7
            d.rectangle((px_, py_, px_ + 6, py_ + 1), fill=GOLD + (int(255 * ha),))
            d.rectangle((px_, py_, px_ + 1, py_ + 6), fill=GOLD + (int(255 * ha),))

    a4 = fin(t - 1.55, 0.26)
    t4 = pixel_text("WEB CLIP UNLIMITED", 1, GREY)
    place(base, t4, SAFE_L, 316, a4)


def sc_limits(base, t):
    """三条限制：受伤提示 + 红色警示 + 血量减少。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("但有三条限制", 26, RED)
    place(base, t1, SAFE_L, 76, a)

    rows = [
        "新版灰度中，还没全量放开",
        "有 TPS 和公平使用配额",
        "Agent Plan 按刊例价折算",
    ]
    for i, txt in enumerate(rows):
        st = 0.22 + i * 0.17
        p = fin(t - st, 0.26)
        if p <= 0:
            continue
        cy = 120 + i * 62
        c = panel(CW, 50, (34, 16, 26), RED, 1)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, 3, 49), fill=RED + (255,))
        cd.text((12, 16), "!", font=sysfont(20), fill=RED + (255,))
        tb = big_text(txt, 14, WHITE)
        c.alpha_composite(tb, (30, 16))
        place(base, c, SAFE_L, cy, p, dy=8 * (1 - p))

    # 警告闪烁条
    wp = t - 1.0
    if wp > 0:
        pulse = 0.4 + 0.6 * abs(math.sin(wp * 4.5))
        d = ImageDraw.Draw(base, "RGBA")
        d.rectangle((SAFE_L, 108, SAFE_R, 110), fill=RED + (int(255 * pulse),))
        wt = pixel_text("WARNING TRIAL ONLY", 1, RED)
        base.alpha_composite(wt, (SAFE_L + 4, 111))

    a2 = fin(t - 1.22, 0.26)
    t2 = big_text("以平台公告和账单为准", 14, GREY)
    place(base, t2, SAFE_L, 312, a2)


def sc_end(base, t):
    """收尾：通关 + 提问 + 关注按钮。"""
    a = fin(t - 0.02, 0.25)
    t1 = big_text("你最想先试哪个？", 26, WHITE)
    place(base, t1, SAFE_L, 150, a)

    a2 = fin(t - 0.22, 0.26)
    t2 = big_text("评论区告诉我，下期实测", 17, GOLD)
    place(base, t2, SAFE_L, 196, a2)

    # 星星装饰
    for i in range(6):
        ang = i * math.pi / 3
        x = SAFE_L + CW // 2 + math.cos(ang) * 110
        y = 260 + math.sin(ang) * 40
        place(base, sprite("star", 1, GOLD), x, y, fin(t - 0.35 - i * 0.04, 0.25))

    a3 = fin(t - 0.55, 0.26)
    t3 = big_text("下期拆一个真实场景 · 记得回来看", 14, GREY)
    place(base, t3, SAFE_L, 300, a3)

    pa = t - 0.78
    if pa > 0:
        blink = 0.7 + 0.3 * abs(math.sin(pa * 5.0))
        label = "FOLLOW"
        ct = pixel_text(label, 2, BG0)
        cw2, ch2 = ct.width + 24, ct.height + 16
        cb = Image.new("RGBA", (cw2, ch2), (0, 0, 0, 0))
        ImageDraw.Draw(cb).rectangle((0, 0, cw2 - 1, ch2 - 1), fill=GOLD + (int(255 * blink),))
        cb.alpha_composite(ct, (12, 8))
        place(base, cb, SAFE_L, 336, fin(pa, 0.3))


SCENES = [
    (0.00, 3.40, sc_hook, "STAGE 1"),
    (3.50, 3.40, sc_proof, "STAGE 2"),
    (7.00, 3.40, sc_two_ways, "STAGE 3"),
    (10.50, 2.60, sc_steps, "STAGE 4"),
    (13.20, 3.50, sc_code, "STAGE 5"),
    (16.80, 1.90, sc_free_range, "STAGE 6"),
    (18.80, 2.40, sc_zero, "STAGE 7"),
    (21.30, 2.30, sc_limits, "STAGE 8"),
    (23.70, 1.10, sc_end, "CLEAR"),
]


def render_lowres(t):
    base = bg_dither().convert("RGBA")
    draw_bg(base)
    scene_idx = 1
    for i, (start, dur, fn, stage) in enumerate(SCENES):
        if not (start <= t < start + dur):
            continue
        scene_idx = i + 1
        layer = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        fn(layer, t - start)
        shifted = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        shifted.alpha_composite(layer, (0, YOFF))
        a = fin(t - start, 0.26)
        if t > start + dur - 0.24:
            a *= fout(t - (start + dur - 0.24), 0.24)
        if a < 0.999:
            shifted.putalpha(shifted.getchannel("A").point([int(i * a) for i in range(256)]))
        base.alpha_composite(shifted)
    stage = next((s for st, du, _, s in SCENES if st <= t < st + du), "CLEAR")
    hud(base, t, stage, scene_idx)
    return base.convert("RGB")


def render_frame(t):
    low = render_lowres(t)
    # ×3 最近邻放大 = 干净像素块
    up = low.resize((W, H), Image.NEAREST)

    # 画面抖动（信号不稳的轻微位移）
    if (t % 2.3) < 0.07:
        random.seed(int(t * 60))
        dx = random.randint(-3, 3) * SCALE
        dy = random.randint(-2, 2) * SCALE
        up = ImageChops.offset(up, dx, dy)

    # 偶发闪白
    if (t % 1.7) < 0.05:
        up = Image.blend(up, Image.new("RGB", (W, H), (255, 255, 255)), 0.16)
    return up


def make_contact():
    marks = [0.6, 1.3, 2.2, 3.1, 4.2, 5.4, 7.8, 9.2, 11.0, 12.6, 14.0, 15.4,
             17.2, 19.0, 20.2, 21.8, 23.0, 24.2]
    cw, ch = 240, 427
    cols = 6
    rows = (len(marks) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, ch * rows), (10, 12, 20))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧E-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 26), fill=(12, 16, 32))
        td.text((8, 4), f"{t:.1f}s", font=sysfont(17), fill=(252, 196, 48))
        sheet.paste(thumb, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(HERE / "检查图-MG样片E.png")
    write_report(GUARD, HERE, "E 像素游戏")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片E.png")


def main():
    preview = "--preview" in sys.argv
    make_contact()
    if preview:
        print("--preview，仅生成关键帧检查图")
        return
    out = HERE / "MG-样片E-像素游戏-无声.mp4"
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
