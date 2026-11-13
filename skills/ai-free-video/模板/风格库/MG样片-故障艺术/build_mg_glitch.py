#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes AI 免费使用 · MG 样片 D（故障艺术 Glitch 风）

与前三版的差异：
- A 深色科技（克制、证据链）／B 亮色杂志（亲和、投影卡片）／C 复古拼贴（手作、纸张）
- D 故障艺术：信号干扰视觉语言，全部程序化生成，无外部素材依赖

视觉语言：
- 色差分离（RGB 错位）、扫描线、噪点雪、信号撕裂横条
- 文字解码式显现（乱码收敛到正确字）
- 截图像素化 + 抖动 + 扫描线扫过
- HUD 边框、坐标码、信号强度条

用法：
    python build_mg_glitch.py --preview   # 只出关键帧检查图
    python build_mg_glitch.py             # 渲染无声 MP4
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

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

F7 = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F3 = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F7_IDX, F3_IDX = 2, 0

# ---- 故障艺术色卡 ----
BG = (5, 7, 13)             # 深空底
CARD = (12, 17, 27)         # 面板
LINE = (34, 46, 64)         # 网格线
CYAN = (0, 229, 255)        # 主强调 荧光青
MAGENTA = (255, 46, 136)    # 次强调 洋红
YELLOW = (255, 230, 0)      # 警示 黄
INK = (234, 242, 255)       # 正文
MUTED = (108, 128, 152)     # 次要

SAFE_L = 84
SAFE_R = W - 150
CW = SAFE_R - SAFE_L

TOTAL = 24.8
NFRAMES = round(TOTAL * FPS)
YOFF = [200]

random.seed(31415)

GLITCH_CHARS = "01▚▞█▓▒░#@$%&*<>[]{}/\\|=+-"


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


def back_out(x, s=1.8):
    x = clamp(x)
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def fin(t, dur=0.30):
    return ease_out(t / dur)


def fout(t, dur=0.22):
    return ease_in(t / dur)


@lru_cache(maxsize=512)
def text_img(s, size, color, bold=False, spacing=1.26):
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


def rgb_text(s, size, bold=False, core=INK, split=6, spacing=1.26):
    """RGB 色差分离文字：洋红层左偏、青层右偏、白芯居中。"""
    a = text_img(s, size, MAGENTA, bold, spacing)
    b = text_img(s, size, CYAN, bold, spacing)
    c = text_img(s, size, core, bold, spacing)
    w = a.width + split * 2
    h = max(a.height, b.height, c.height)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(a, (0, 0))
    out.alpha_composite(b, (split * 2, 0))
    out.alpha_composite(c, (split, 0))
    return out


def decode_text(s, size, p, bold=True, color=INK):
    """解码式显现：p<1 时显示乱码字符，p=1 收敛到正确文本。"""
    if p >= 0.999:
        return text_img(s, size, color, bold)
    n = len(s)
    out = ""
    for i, ch in enumerate(s):
        if ch == " ":
            out += " "
            continue
        # 每个字符独立决定是否已解码
        local = clamp((p * (n + 8) - i) / 8.0)
        if local >= 0.999:
            out += ch
        else:
            out += random.choice(GLITCH_CHARS)
    return text_img(out, size, color, bold)


@lru_cache(maxsize=64)
def noise_layer():
    """稀疏噪点雪：大部分透明，只在少量位置打亮点。

    注意：不能直接用 ImageChops.add(base, 全噪点图)，
    全图噪点会淹没画面。必须是稀疏亮点，再按 scale=1 直接叠加。
    """
    im = Image.new("L", (W, H), 0)
    px = im.load()
    for _ in range(9000):
        x, y = random.randint(0, W - 1), random.randint(0, H - 1)
        px[x, y] = random.randint(90, 255)
    return im.filter(ImageFilter.GaussianBlur(0.5))


@lru_cache(maxsize=8)
def scanlines(spacing=4, alpha=42):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, H, spacing):
        d.rectangle((0, y, W, y + 1), fill=(0, 0, 0, alpha))
    return im


def draw_grid(base):
    """背景网格 + 中心暗角，给故障风一点结构感。"""
    d = ImageDraw.Draw(base, "RGBA")
    for x in range(0, W, 60):
        d.rectangle((x, 0, x, H), fill=LINE + (34,))
    for y in range(0, H, 60):
        d.rectangle((0, y, W, y), fill=LINE + (34,))
    # 暗角
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.rectangle((150, 200, W - 150, H - 200), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    base.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                                         dark.convert("RGBA"), vig))


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


def panel(w, h, fill=CARD, border=LINE, bw=2):
    """HUD 面板：硬边 + 角标切口。"""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=fill + (255,), outline=border + (255,), width=bw)
    # 四角切口
    for cx, cy in ((0, 0), (w - 18, 0), (0, h - 18), (w - 18, h - 18)):
        d.rectangle((cx, cy, cx + 17, cy + 17), fill=BG + (255,))
    return im


def hud_brackets(base, inset=54):
    """四角 HUD 括号。"""
    d = ImageDraw.Draw(base, "RGBA")
    L = 54
    for cx, cy, sx, sy in ((inset, inset, 1, 1), (W - inset, inset, -1, 1),
                            (inset, H - inset, 1, -1), (W - inset, H - inset, -1, -1)):
        x = cx if sx > 0 else cx - L
        y = cy if sy > 0 else cy - L
        d.rectangle((x, y, x + L, y + 3), fill=CYAN + (190,))
        d.rectangle((x, y, x + 3, y + L), fill=CYAN + (190,))


def signal_bars(base, x, y, n=5, active=4, color=CYAN, w=14, gap=6):
    """信号强度条。"""
    d = ImageDraw.Draw(base, "RGBA")
    for i in range(n):
        h = 10 + i * 8
        on = i < active
        d.rectangle((x + i * (w + gap), y + 40 - h, x + i * (w + gap) + w, y + 40),
                    fill=(color + (235,)) if on else (LINE + (200,)))


@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh, pixel=0):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 pixel=pixel, color=0.85, brightness=0.92)
    return im


def shot_panel(name, box, w, h, label=None, pixel=0):
    """截图 HUD 面板 + 定位框 + 扫描带。"""
    layer = panel(w, h, (10, 14, 22), LINE, 2)
    d = ImageDraw.Draw(layer)
    bar_h = 34
    d.rectangle((0, 0, w - 1, bar_h), fill=(16, 22, 34, 255))
    d.rectangle((0, bar_h, w - 1, bar_h + 1), fill=CYAN + (150,))
    for i, c in enumerate(((255, 70, 110), (255, 210, 60), (60, 240, 190))):
        d.ellipse((14 + i * 18, 12, 24 + i * 18, 22), fill=c + (255,))
    if label:
        t = text_img(label, 21, CYAN, True)
        layer.alpha_composite(t, (78, 5))
    ip = 10
    src = load_shot(name, box, w - 2 * ip, h - bar_h - 2 * ip, pixel)
    layer.alpha_composite(src, (ip + (w - 2 * ip - src.width) // 2,
                                bar_h + ip + (h - bar_h - 2 * ip - src.height) // 2))
    # 四角定位框
    for cx, cy, sx, sy in ((4, bar_h + 4, 1, 1), (w - 22, bar_h + 4, -1, 1),
                            (4, h - 22, 1, -1), (w - 22, h - 22, -1, -1)):
        x = cx if sx > 0 else cx - 18
        y = cy if sy > 0 else cy - 18
        d.rectangle((x, y, x + 17, y + 2), fill=YELLOW + (220,))
        d.rectangle((x, y, x + 2, y + 17), fill=YELLOW + (220,))
    return layer


def scan_sweep(base, t, y0=0, h=200, color=CYAN, alpha=60):
    """一条扫描亮带自上而下扫过。"""
    p = (t * 0.55) % 1.0
    y = int(y0 + p * (H + h) - h / 2)
    band = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for i in range(h):
        a = int(alpha * (1 - abs(i - h / 2) / (h / 2)))
        bd.rectangle((0, i, W, i + 1), fill=color + (a,))
    base.alpha_composite(band, (0, y))


def glitch_tear(base, t, strength=1.0):
    """信号撕裂：随机横条水平错位。"""
    if strength <= 0.01:
        return base
    random.seed(int(t * 24) * 7919)
    for _ in range(int(3 * strength)):
        y = random.randint(0, H - 1)
        h = random.randint(8, 46)
        band = base.crop((0, y, W, min(H, y + h)))
        dx = random.randint(-46, 46) * int(strength)
        base.paste(band, (dx, y))
        # 色度加倍
        if random.random() < 0.45:
            r = band.getchannel("R").point(lambda v: min(255, int(v * 1.5)))
            g = band.getchannel("G")
            b = band.getchannel("B").point(lambda v: int(v * 0.6))
            band = Image.merge("RGB", (r, g, b)).convert("RGBA")
            base.paste(band, (dx - random.randint(3, 11), y))
    return base


# ---------------------------------------------------------------- 场景
def sc_hook(base, t):
    """钩子：解码式标题 + 色差分离 + 扫描带 + 三块数据卡。"""
    p = clamp((t - 0.05) / 0.75)
    t1 = decode_text("文本 图片 视频", 92, p)
    place(base, t1, SAFE_L, 350, fin(t - 0.05, 0.25))

    p2 = clamp((t - 0.45) / 0.8)
    t2 = decode_text("全部 0 元", 104, p2, color=CYAN)
    place(base, t2, SAFE_L, 480, fin(t - 0.45, 0.25))

    a3 = fin(t - 0.85, 0.30)
    t3 = rgb_text("AGNES AI FLASH · 当前体验价", 32, split=4, core=MUTED)
    place(base, t3, SAFE_L, 640, a3)

    # 三块数据卡，扫描带扫过时短暂上移
    items = [("文本", "FLASH×2", "¥0"), ("图片", "FLASH×3", "¥0"), ("视频", "720P", "¥0")]
    cw = (CW - 2 * 20) // 3
    for i, (k, sub, v) in enumerate(items):
        st = 1.00 + i * 0.14
        pa = back_out((t - st) / 0.45)
        if pa <= 0:
            continue
        c = panel(cw, 210)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, cw - 1, 5), fill=(CYAN, MAGENTA, YELLOW)[i] + (255,))
        tk = text_img(k, 34, INK, True)
        c.alpha_composite(tk, (20, 26))
        ts = text_img(sub, 22, MUTED)
        c.alpha_composite(ts, (20, 74))
        tv = text_img(v, 58, (CYAN, MAGENTA, YELLOW)[i], True)
        c.alpha_composite(tv, (20, 122))
        place(base, c, SAFE_L + i * (cw + 20), 730, pa, dy=34 * (1 - pa))

    # 扫描带扫过卡片
    if t > 1.0:
        scan_sweep(base, t, 700, 260, CYAN, 46)

    a4 = fin(t - 1.55, 0.30)
    t4 = rgb_text("非营销话术 · 官网实拍", 28, split=4, core=MUTED)
    place(base, t4, SAFE_L, 990, a4)


def sc_proof(base, t):
    """兑现：HUD 面板切入 + 定位框 + 信号锁定。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("免费 API 就在首页", 82, clamp((t - 0.02) / 0.7))
    place(base, t1, SAFE_L, 330, a)

    shot = shot_panel("01-官网首页-免费API与多模态.jpg", (300, 155, 1000, 262),
                      CW, 220, "HOME / 免费 API")
    p = back_out((t - 0.30) / 0.5)
    place(base, shot, SAFE_L, 470, p, dy=44 * (1 - p))

    # 锁定框扫描
    lp = t - 0.95
    if lp > 0:
        d = ImageDraw.Draw(base, "RGBA")
        la = fin(lp, 0.35)
        x, y, ww, hh = SAFE_L + 120, 520, 420, 90
        for cx, cy, sx, sy in ((x, y, 1, 1), (x + ww, y, -1, 1),
                                (x, y + hh, 1, -1), (x + ww, y + hh, -1, -1)):
            px_ = cx if sx > 0 else cx - 30
            py_ = cy if sy > 0 else cy - 30
            d.rectangle((px_, py_, px_ + 29, py_ + 3), fill=YELLOW + (int(235 * la),))
            d.rectangle((px_, py_, px_ + 3, py_ + 29), fill=YELLOW + (int(235 * la),))

    a2 = fin(t - 1.20, 0.30)
    t2 = rgb_text("官网首页首屏 · 免费 API 入口", 30, split=4, core=MUTED)
    place(base, t2, SAFE_L, 760, a2)

    # 状态行
    if t > 1.0:
        d = ImageDraw.Draw(base, "RGBA")
        d.rectangle((SAFE_L, 850, SAFE_L + 300, 850 + 3), fill=CYAN + (200,))
        d.text((SAFE_L, 862), "STATUS: FOUND", font=font(24, True), fill=CYAN + (255,))
        signal_bars(base, SAFE_R - 130, 852, 5, 4, CYAN)


def sc_two_ways(base, t):
    """两种用法：双通道面板 + 中间切换开关 + 信号分流示意。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("两种用法", 88, clamp((t - 0.02) / 0.6))
    place(base, t1, SAFE_L, 320, a)

    cw = (CW - 40) // 2
    blocks = [
        ("普通用户", "PAVO WEB", "搜索 对话\n创作 视频", CYAN),
        ("开发者", "API", "免费额度\n接入自有工具", MAGENTA),
    ]
    for i, (title, tag, body, ac) in enumerate(blocks):
        st = 0.20 + i * 0.16
        p = back_out((t - st) / 0.5)
        if p <= 0:
            continue
        c = panel(cw, 400)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, cw - 1, 5), fill=ac + (255,))
        tb = text_img(title, 40, ac, True)
        c.alpha_composite(tb, (28, 36))
        tg = text_img(tag, 20, MUTED, True)
        c.alpha_composite(tg, (28, 92))
        cd.rectangle((28, 132, cw - 28, 133), fill=LINE + (255,))
        for j, ln in enumerate(body.split("\n")):
            t3 = text_img(ln, 28, INK)
            c.alpha_composite(t3, (28, 168 + j * 46))
        # 底部信号条
        signal_bars(c, cw - 120, 320, 4, 3 if i == 0 else 4, ac, 10, 5)
        place(base, c, SAFE_L + i * (cw + 40), 460, p, dy=40 * (1 - p))

    # 中间切换开关
    sp = t - 0.70
    if sp > 0:
        sw = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sw)
        sd.ellipse((6, 6, 104, 104), fill=BG + (255,), outline=CYAN + (220,), width=3)
        o = text_img("OR", 26, INK, True)
        sw.alpha_composite(o, (55 - o.width // 2, 55 - o.height // 2))
        place(base, sw, SAFE_L + CW // 2 - 55, 600, fin(sp, 0.3))

    a3 = fin(t - 1.00, 0.30)
    t3 = rgb_text("不写代码也能用 · 要接工具才走 API", 28, split=4, core=MUTED)
    place(base, t3, SAFE_L, 930, a3)


def sc_steps(base, t):
    """五步：终端风格逐条输出 + 行号 + 光标。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("开发者五步", 88, clamp((t - 0.02) / 0.6))
    place(base, t1, SAFE_L, 310, a)

    items = ["注册账户", "生成 API Key", "选 agnes-3.0-flash", "填 Base URL", "发第一条请求"]
    row_h = 158
    y0 = 450

    for i, it in enumerate(items):
        st = 0.24 + i * 0.15
        p = fin(t - st, 0.28)
        if p <= 0:
            continue
        cy = y0 + i * row_h
        d = ImageDraw.Draw(base, "RGBA")
        # 行号
        d.text((SAFE_L, cy + 6), f"{i+1:02d}", font=font(28, True), fill=MUTED + (200,))
        # 提示符
        d.text((SAFE_L + 52, cy + 4), ">", font=font(32, True), fill=CYAN + (255,))
        # 文字（打字机）
        f = font(38, True)
        shown = it[:max(1, int(len(it) * clamp((t - st) / 0.40)))]
        tb = decode_text(shown, 38, 1.0, color=INK)
        place(base, tb, SAFE_L + 92, cy)
        # 进度
        d.rectangle((SAFE_L + 92, cy + 58, SAFE_R, cy + 60), fill=LINE + (140,))
        d.rectangle((SAFE_L + 92, cy + 58, SAFE_L + 92 + int((CW - 92) * p), cy + 60),
                    fill=CYAN + (230,))
        # 完成标记
        if t > st + 0.45:
            cp = fin(t - st - 0.45, 0.28)
            ck = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
            kd = ImageDraw.Draw(ck)
            kd.line((10, 25, 20, 35), fill=YELLOW + (255,), width=5)
            kd.line((20, 35, 40, 12), fill=YELLOW + (255,), width=5)
            place(base, ck, SAFE_R - 52, cy + 8, cp)


def sc_code(base, t):
    """请求参数：终端块逐行解码 + 复制提示 + 扫描带。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("三行就能发出去", 82, clamp((t - 0.02) / 0.65))
    place(base, t1, SAFE_L, 310, a)

    shot = shot_panel("03-快速开始-注册Key与首次请求.jpg", (0, 150, 1396, 1420),
                      CW, 380, "DOC / 快速开始", pixel=2)
    p = back_out((t - 0.18) / 0.5)
    place(base, shot, SAFE_L, 450, p, dy=44 * (1 - p))

    lines = [
        ("model:", "agnes-3.0-flash", CYAN),
        ("base:", "api.agnes-ai.cn/v1", INK),
        ("auth:", "Bearer YOUR_API_KEY", INK),
    ]
    code_y = 890
    card_h = 56 * len(lines) + 40
    c = panel(CW, card_h, (8, 12, 20), CYAN, 2)
    cd = ImageDraw.Draw(c)
    cd.rectangle((0, 0, CW - 1, 30), fill=(14, 20, 32, 255))
    for i, cc in enumerate((MAGENTA, YELLOW, CYAN)):
        cd.ellipse((14 + i * 17, 10, 24 + i * 17, 20), fill=cc + (255,))
    tlab = text_img("bash", 19, MUTED, True)
    c.alpha_composite(tlab, (76, 5))
    place(base, c, SAFE_L, code_y, fin(t - 0.34, 0.32), dy=30 * (1 - fin(t - 0.34, 0.32)))

    for i, (k, v, col) in enumerate(lines):
        st = 0.52 + i * 0.20
        p = fin(t - st, 0.28)
        if p <= 0:
            continue
        kt = text_img(k, 30, MUTED)
        vt = decode_text(v, 30, clamp((t - st) / 0.45), color=col)
        row = Image.new("RGBA", (CW - 60, 40), (0, 0, 0, 0))
        row.alpha_composite(kt, (0, 0))
        row.alpha_composite(vt, (kt.width + 14, 0))
        wipe(base, row, SAFE_L + 30, code_y + 40 + i * 56, p)

    # 复制提示
    a3 = back_out((t - 1.35) / 0.45)
    if a3 > 0:
        chip = text_img("COPY & RUN", 26, BG, True)
        cw2, ch2 = chip.width + 40, chip.height + 22
        cb = Image.new("RGBA", (cw2, ch2), (0, 0, 0, 0))
        ImageDraw.Draw(cb).rectangle((0, 0, cw2 - 1, ch2 - 1), fill=CYAN + (255,))
        cb.alpha_composite(chip, (20, 11))
        place(base, cb, SAFE_L, code_y + card_h + 26, a3, dy=18 * (1 - a3))

    if t > 0.9:
        scan_sweep(base, t, 850, 220, CYAN, 40)


def sc_free_range(base, t):
    """免费范围：三行终端输出 + 右侧 0 元跳变。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("哪些真的免费", 86, clamp((t - 0.02) / 0.6))
    place(base, t1, SAFE_L, 310, a)

    rows = [
        ("文本 FLASH×2", "输入 / 输出全 0"),
        ("图片 FLASH×3", "各分辨率全 0"),
        ("视频 FLASH 720P", "时长 0 元 / 秒"),
    ]
    for i, (k, v) in enumerate(rows):
        st = 0.22 + i * 0.17
        p = fin(t - st, 0.28)
        if p <= 0:
            continue
        cy = 470 + i * 168
        c = panel(CW, 142)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, 5, 141), fill=(CYAN, MAGENTA, YELLOW)[i] + (255,))
        tk = decode_text(k, 38, clamp((t - st) / 0.45), color=INK)
        c.alpha_composite(tk, (28, 26))
        tv = text_img(v, 26, MUTED)
        c.alpha_composite(tv, (28, 86))
        # 右侧 0 元
        lp = back_out((t - st - 0.25) / 0.4)
        if lp > 0:
            tv2 = text_img("¥0", 36, (CYAN, MAGENTA, YELLOW)[i], True)
            c.alpha_composite(tv2, (CW - tv2.width - 32, 52))
        place(base, c, SAFE_L, cy, p, dy=34 * (1 - p))


def sc_zero(base, t):
    """0 元证据：数值跳变 + 扫描带扫过定价页 + 锁定框。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("视频 FLASH 720P", 72, clamp((t - 0.02) / 0.6))
    place(base, t1, SAFE_L, 300, a)

    a2 = fin(t - 0.26, 0.28)
    old = text_img("刊例价 ¥0.15 / 秒", 40, MUTED, True)
    place(base, old, SAFE_L, 400, a2)
    sp = fin(t - 0.56, 0.36)
    if sp > 0:
        strike = Image.new("RGBA", (old.width + 10, 6), (0, 0, 0, 0))
        ImageDraw.Draw(strike).rectangle((0, 0, old.width + 10, 5), fill=MAGENTA + (255,))
        wipe(base, strike, SAFE_L, 400 + old.height // 2, sp)

    a3 = fin(t - 0.68, 0.26)
    lab = text_img("当前体验价", 30, MUTED, True)
    place(base, lab, SAFE_L, 490, a3)

    rp = clamp((t - 0.78) / 1.0)
    val = 0.15 * (1 - ease_out(rp))
    num_s = "¥0" if rp >= 0.999 else f"¥{val:.3f}"
    num = text_img(num_s, 128, CYAN, True)
    place(base, num, SAFE_L, 540, a3)
    unit = text_img("/ 秒", 42, INK, True)
    place(base, unit, SAFE_L + num.width + 14, 540 + 94, a3)

    # 定价页面板（低像素模拟信号劣化）
    shot = shot_panel("07-模型定价-视频Flash限时免费.jpg", (0, 700, 1396, 822),
                      CW, 170, "PRICING / 视频")
    p = back_out((t - 1.00) / 0.5)
    place(base, shot, SAFE_L, 730, p, dy=36 * (1 - p))

    # 扫描带精确扫过 0 元标签位置
    if t > 1.25:
        scan_sweep(base, t - 0.6, 720, 200, CYAN, 70)
        la = fin(t - 1.45, 0.3)
        d = ImageDraw.Draw(base, "RGBA")
        x, y, ww, hh = SAFE_R - 260, 745, 190, 90
        for cx, cy, sx, sy in ((x, y, 1, 1), (x + ww, y, -1, 1),
                                (x, y + hh, 1, -1), (x + ww, y + hh, -1, -1)):
            px_ = cx if sx > 0 else cx - 28
            py_ = cy if sy > 0 else cy - 28
            d.rectangle((px_, py_, px_ + 27, py_ + 3), fill=YELLOW + (int(230 * la),))
            d.rectangle((px_, py_, px_ + 3, py_ + 27), fill=YELLOW + (int(230 * la),))

    a4 = fin(t - 1.58, 0.28)
    t4 = rgb_text("agnes-video-2.5-flash · 官网当前显示", 28, split=4, core=MUTED)
    place(base, t4, SAFE_L, 950, a4)


def sc_limits(base, t):
    """三条限制：红色告警块 + 抖动提示 + 警告边框脉冲。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("但有三条限制", 84, clamp((t - 0.02) / 0.6), color=YELLOW)
    place(base, t1, SAFE_L, 310, a)

    rows = [
        "阶段性优惠，不是永久免费",
        "有 TPS 和公平使用配额",
        "Agent Plan 按刊例价折算 Credits",
    ]
    for i, txt in enumerate(rows):
        st = 0.24 + i * 0.18
        p = fin(t - st, 0.28)
        if p <= 0:
            continue
        cy = 470 + i * 168
        c = panel(CW, 136, (26, 14, 20), (96, 34, 58), 2)
        cd = ImageDraw.Draw(c)
        cd.rectangle((0, 0, 6, 135), fill=MAGENTA + (255,))
        tb = decode_text(txt, 34, clamp((t - st) / 0.45), color=INK)
        c.alpha_composite(tb, (30, 48))
        # 右侧感叹号
        cd.text((CW - 52, 44), "!", font=font(40, True), fill=MAGENTA + (255,))
        place(base, c, SAFE_L, cy, p, dy=34 * (1 - p))

    # 顶部警告条脉冲
    wp = t - 1.0
    if wp > 0:
        pulse = 0.45 + 0.45 * abs(math.sin(wp * 4.2))
        d = ImageDraw.Draw(base, "RGBA")
        d.rectangle((SAFE_L, 230, SAFE_R, 232), fill=MAGENTA + (int(255 * pulse),))
        d.text((SAFE_L, 244), "WARNING: 阶段性优惠", font=font(24, True),
               fill=MAGENTA + (int(255 * pulse),))

    a2 = fin(t - 1.25, 0.28)
    t2 = rgb_text("最终以平台公告和账户账单为准", 28, split=4, core=MUTED)
    place(base, t2, SAFE_L, 990, a2)


def sc_end(base, t):
    """收尾：解码大字 + 扫描带 + 关注按钮（闪烁提示）。"""
    a = fin(t - 0.02, 0.28)
    t1 = decode_text("你最想白嫖哪个？", 88, clamp((t - 0.02) / 0.7))
    place(base, t1, SAFE_L, 470, a)

    a2 = fin(t - 0.24, 0.28)
    t2 = rgb_text("评论区告诉我，我下期实测", 40, split=5, core=CYAN)
    place(base, t2, SAFE_L, 620, a2)

    a3 = fin(t - 0.52, 0.28)
    t3 = text_img("科技不高冷，AI 很好用 · 我是晚枫", 30, MUTED)
    place(base, t3, SAFE_L, 730, a3)

    # 关注按钮（闪烁）
    pa = t - 0.78
    if pa > 0:
        blink = 0.72 + 0.28 * abs(math.sin(pa * 5.0))
        label = "关注我 · 只讲真能白嫖的"
        chip = text_img(label, 32, BG, True)
        cw2, ch2 = chip.width + 44, chip.height + 24
        cb = Image.new("RGBA", (cw2, ch2), (0, 0, 0, 0))
        ImageDraw.Draw(cb).rectangle((0, 0, cw2 - 1, ch2 - 1), fill=CYAN + (int(255 * blink),))
        cb.alpha_composite(chip, (22, 12))
        place(base, cb, SAFE_L, 840, fin(pa, 0.3))

    if t > 0.6:
        scan_sweep(base, t, 400, 240, MAGENTA, 34)


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
    base = Image.new("RGBA", (W, H), BG + (255,))
    draw_grid(base)

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

    # HUD 边框 + 顶栏
    hud_brackets(base)
    d = ImageDraw.Draw(base, "RGBA")
    tag = text_img("AGNES AI / 免费使用", 24, CYAN, True)
    place(base, tag, SAFE_L, 66, 1.0)
    pct = text_img(f"{int(t/TOTAL*100):03d}%", 24, MUTED, True)
    place(base, pct, SAFE_R - pct.width, 66, 1.0)
    d.rectangle((SAFE_L, 116, SAFE_R, 118), fill=CYAN + (220,))
    if t > 0:
        d.rectangle((SAFE_L, 124, SAFE_L + int(CW * t / TOTAL), 127), fill=MAGENTA + (255,))

    base = base.convert("RGB")
    # 噪点雪：稀疏亮点直接叠加，幅度靠亮点密度控制，不改变整体亮度
    nl = noise_layer()
    base = ImageChops.add(base, Image.merge("RGB", (nl, nl, nl)))
    # 扫描线
    base = base.convert("RGBA")
    base.alpha_composite(scanlines(4, 26))
    base = base.convert("RGB")
    # 随机信号撕裂
    base = glitch_tear(base, t, 1.0 if (t % 3.1) < 0.12 else 0.0)
    return base


def make_contact():
    marks = [0.6, 1.3, 2.2, 3.1, 4.2, 5.4, 7.8, 9.2, 11.0, 12.6, 14.0, 15.4,
             17.2, 19.0, 20.2, 21.8, 23.0, 24.2]
    cw, ch = 240, 427
    cols = 6
    rows = (len(marks) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, ch * rows), (10, 12, 18))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧D-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 28), fill=(5, 7, 13))
        td.text((8, 3), f"{t:.1f}s", font=font(18, True), fill=(0, 229, 255))
        sheet.paste(thumb, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(HERE / "检查图-MG样片D.png")
    write_report(GUARD, HERE, "D 故障艺术")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片D.png")


def main():
    preview = "--preview" in sys.argv
    make_contact()
    if preview:
        print("--preview，仅生成关键帧检查图")
        return
    out = HERE / "MG-样片D-故障艺术-无声.mp4"
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
