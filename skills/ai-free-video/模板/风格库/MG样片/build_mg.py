#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes AI 免费使用 · MG 样片渲染器

风格：深色科技风（对齐账号色卡），画面全部走深色底 + 荧光绿强调。
结构：按《内容编排方法论》四段式（钩子 / 兑现 / 正文 / 收尾）。
素材：官网截图只做裁切 + 高亮框，不改原图文字与价格。

用法：
    python build_mg.py --preview   # 只出关键帧检查图
    python build_mg.py             # 渲染无声 MP4
"""
from __future__ import annotations

import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

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
                     safe_top=210, safe_bottom=1920-1450,
                     safe_left=84, safe_right=150)

SHOTS = SHOTS_DIR  # 由 mgkit.paths 解析（MG_SHOTS_DIR 可覆盖）
EVID = EVID_DIR    # 由 mgkit.paths 解析（MG_EVID_DIR 可覆盖）

W, H = 1080, 1920

F7 = "/Users/wanfeng/Library/Fonts/TencentSans-W7.ttf"
F3 = "/Users/wanfeng/Library/Fonts/TencentSans-W3.ttf"

# ---- 账号色卡（深色科技风）----
BG = (10, 14, 20)          # 背景底色 #0A0E14
CARD = (20, 26, 36)        # 卡片面 #141A24
LINE = (35, 43, 57)        # 描边 #232B39
ACCENT = (0, 229, 160)     # 主强调 荧光绿 #00E5A0
BLUE = (59, 130, 246)      # 次强调 蓝 #3B82F6
ORANGE = (255, 122, 69)    # 警示 橙 #FF7A45
INK = (232, 236, 242)      # 正文 #E8ECF2
MUTED = (138, 147, 163)    # 次要文本 #8A93A3

# 竖屏安全区：顶部 10% 不放字，右侧 15% 不放字，底部 22% 不放正文
SAFE_L = 84
SAFE_R = W - 150
SAFE_T = 210
SAFE_B = 1450

# 全片总时长（无声样片，按口播节奏排布）
TOTAL = 24.0
NFRAMES = round(TOTAL * FPS)


def font(size, bold=False):
    return ImageFont.truetype(F7 if bold else F3, int(size))


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = max(0.0, min(1.0, x))
    return x * x


def fin(t, dur=0.28):
    return ease_out(t / dur)


def fout(t, dur=0.20):
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
    im = Image.new("RGBA", (max(ws) + 16, step * len(lines) + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((8, i * step + 6 - tops[i]), ln, font=f, fill=color + (255,))
    return mark_text_layer(im, s.replace(chr(10), ' / '))


@lru_cache(maxsize=128)
def card_img(w, h, radius=24, fill=CARD, border=LINE, bw=2):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius,
                                         fill=fill + (255,), outline=border + (255,), width=bw)
    return im


@lru_cache(maxsize=128)
def chip_img(s, size, fg, fill=None, pad_x=26, pad_y=14):
    t = text_img(s, size, fg, True)
    w, h = t.width + pad_x * 2, t.height + pad_y * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), h // 2,
                                         fill=(fill or fg) + (255,))
    im.alpha_composite(t, (pad_x, pad_y))
    return im


@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 brightness=0.88, color=0.92)
    return im


@lru_cache(maxsize=64)
def shot_card(name, box, w, h, label=None, label_color=ACCENT):
    """截图证据卡：浏览器窗口外观 + 描边，可选左上角标签。

    白底官网页用"浏览器窗口"包装后不会像贴图块一样割裂，
    这是深色 MG 里处理白底网页截图的通用手法。
    """
    bar_h = 34
    layer = card_img(w, h, 20, (16, 21, 30), LINE, 2).copy()
    d = ImageDraw.Draw(layer)
    # 浏览器顶栏
    d.rounded_rectangle((0, 0, w - 1, h - 1), 20, fill=(16, 21, 30, 255),
                        outline=LINE + (255,), width=2)
    d.rectangle((0, bar_h, w - 1, bar_h + 1), fill=LINE + (255,))
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((16 + i * 18, 13, 26 + i * 18, 23), fill=c + (255,))
    if label:
        t = text_img(label, 22, MUTED, True)
        layer.alpha_composite(t, (84, 6))
    # 截图主体
    pad = 10
    src = load_shot(name, box, w - 2 * pad, h - bar_h - 2 * pad)
    layer.alpha_composite(src, (pad + (w - 2 * pad - src.width) // 2,
                                bar_h + pad + (h - bar_h - 2 * pad - src.height) // 2))
    return layer


@lru_cache(maxsize=32)
def num_card(w, h, num, unit, label, color=ACCENT):
    im = card_img(w, h, 26).copy()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 10, h), 5, fill=color + (255,))
    n = text_img(num, 150, color, True)
    im.alpha_composite(n, (46, 46))
    u = text_img(unit, 52, INK, True)
    im.alpha_composite(u, (46 + n.width + 18, 46 + n.height - 62))
    lb = text_img(label, 32, MUTED)
    im.alpha_composite(lb, (46, 46 + n.height + 18))
    d.line((46, h - 46, w - 46, h - 46), fill=LINE + (255,), width=2)
    return im


@lru_cache(maxsize=64)
def kv_row(w, h, key, val, accent=ACCENT):
    im = card_img(w, h, 18, (16, 21, 30), LINE, 2).copy()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 8, h), 4, fill=accent + (255,))
    k = text_img(key, 34, MUTED, True)
    v = text_img(val, 36, INK, True)
    im.alpha_composite(k, (32, (h - k.height) // 2))
    im.alpha_composite(v, (32 + k.width + 24, (h - v.height) // 2))
    return im


def paste(base, layer, x, y, a, dy=0):
    """带 alpha 与位移的合成。"""
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


# ---------------------------------------------------------------- 顶部进度条
def progress(base, p, color=ACCENT):
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((SAFE_L, 150, SAFE_R, 158), 4, fill=LINE + (255,))
    if p > 0:
        d.rounded_rectangle((SAFE_L, 150, SAFE_L + int((SAFE_R - SAFE_L) * p), 158), 4,
                            fill=color + (255,))


def kicker(base, text, color=ACCENT):
    tag = chip_img(text, 26, color, (14, 20, 30))
    paste(base, tag, SAFE_L, 62, 1.0)


# ---------------------------------------------------------------- 场景元素
# 每个场景：start(绝对秒) / dur(时长) / els
# 每个元素：delay(相对场景起点的入场秒数)
def build_scenes():
    S = []

    # ---- 场景 1：钩子（0-3.3s）----
    S.append((0.15, 3.15, [
        dict(k="headline", y=400, s="文本 · 图片 · 视频", size=104, delay=0.0),
        dict(k="headline", y=550, s="现在都是 0 元", size=104, color=ACCENT, delay=0.16),
        dict(k="sub", y=710, s="Agnes AI Flash 系列 · 官网当前体验价", delay=0.32),
        dict(k="rule", y=850, delay=0.44),
    ]))
    S.append((0.15, 3.15, [
        dict(k="shot", y=930, name="01-官网首页-免费API与多模态.jpg",
             box=(740, 155, 980, 225), w=880, h=200, label="官网首页 · 免费 API", delay=0.55),
    ]))

    # ---- 场景 2：兑现（3.4-7.0s）----
    S.append((3.40, 3.60, [
        dict(k="headline", y=340, s="免费 API 就挂在首页", size=84, delay=0.0),
        dict(k="shot", y=520, name="01-官网首页-免费API与多模态.jpg",
             box=(300, 155, 1000, 260), w=912, h=190, label="官网首屏", delay=0.12),
        dict(k="sub", y=790, s="不是营销话术，是官网自己的入口", delay=0.28),
    ]))

    # ---- 场景 3：两类入口（7.2-10.4s）----
    S.append((7.20, 3.20, [
        dict(k="headline", y=320, s="两种用法", size=88, delay=0.0),
        dict(k="pair", y=470, a="普通用户", b="开发者",
             ad="Pavo 网页端\n搜索 · 对话 · 创作", bd="API 接口\n免费额度试用", delay=0.14),
        dict(k="sub", y=980, s="不写代码也能用，要接工具才走 API", delay=0.30),
    ]))

    # ---- 场景 4：五步（10.6-13.0s）----
    S.append((10.60, 2.40, [
        dict(k="headline", y=300, s="开发者五步", size=88, delay=0.0),
        dict(k="steps", y=470, items=["注册账户", "生成 Key", "选 Flash", "填地址", "发请求"],
             delay=0.14),
    ]))

    # ---- 场景 5：快速开始 + 请求参数（13.1-16.4s）----
    S.append((13.10, 3.30, [
        dict(k="headline", y=300, s="三行就能发出去", size=84, delay=0.0),
        dict(k="shot", y=480, name="03-快速开始-注册Key与首次请求.jpg",
             box=(0, 150, 1396, 1420), w=912, h=430, label="官方快速开始", delay=0.12),
        dict(k="code", y=970, lines=[
            "model:  agnes-3.0-flash",
            "base:   api.agnes-ai.cn/v1",
            "auth:   Bearer YOUR_API_KEY",
        ], delay=0.28),
    ]))

    # ---- 场景 6：免费范围（16.6-18.1s）----
    S.append((16.60, 1.50, [
        dict(k="headline", y=300, s="哪些真的免费", size=88, delay=0.0),
        dict(k="rows", y=480, rows=[
            ("文本 Flash ×2", "输入输出全 0", ACCENT),
            ("图片 Flash ×3", "各分辨率全 0", ACCENT),
            ("视频 Flash 720P", "时长 0 元/秒", ACCENT),
        ], delay=0.14),
    ]))

    # ---- 场景 7：视频 0 元证据（18.2-20.0s）----
    S.append((18.20, 1.80, [
        dict(k="shot", y=330, name="07-模型定价-视频Flash限时免费.jpg",
             box=(0, 700, 1396, 820), w=912, h=132, label="官网定价页 · 视频", delay=0.0),
        dict(k="num", y=530, num="¥0", unit="/ 秒", h=290,
             label="agnes-video-2.5-flash · 720P 视频时长", delay=0.16),
    ]))

    # ---- 场景 8：三条限制（20.2-22.6s）----
    S.append((20.20, 2.40, [
        dict(k="headline", y=300, s="但有三条限制", size=88, color=ORANGE, delay=0.0),
        dict(k="warn", y=480, rows=[
            "阶段性优惠，不是永久免费",
            "有 TPS 和公平使用配额",
            "Agent Plan 按刊例价折算 Credits",
        ], delay=0.14),
    ]))

    # ---- 场景 9：收尾（22.8-24.0s）----
    S.append((22.80, 1.20, [
        dict(k="headline", y=520, s="你最想白嫖哪个？", size=96, delay=0.0),
        dict(k="sub", y=700, s="评论区告诉我，我下期实测", color=ACCENT, size=44, delay=0.12),
        dict(k="rule", y=830, delay=0.22),
        dict(k="sub", y=880, s="科技不高冷，AI 很好用 · 我是晚枫", size=38, delay=0.30),
    ]))
    return S


SCENES = build_scenes()


# ---------------------------------------------------------------- 元素渲染
def render_el(el, t):
    k = el["k"]
    if k == "headline":
        return text_img(el["s"], el["size"], el.get("color", INK), True, 1.18)
    if k == "sub":
        return text_img(el["s"], el.get("size", 40), el.get("color", MUTED))
    if k == "rule":
        im = Image.new("RGBA", (SAFE_R - SAFE_L, 4), (0, 0, 0, 0))
        ImageDraw.Draw(im).rectangle((0, 0, SAFE_R - SAFE_L, 3), fill=ACCENT + (255,))
        return im
    if k == "shot":
        return shot_card(el["name"], el["box"], el["w"], el["h"], el.get("label"))
    if k == "code":
        lines = el["lines"]
        cw = SAFE_R - SAFE_L
        im = card_img(cw, 54 * len(lines) + 56, 20, (14, 19, 28), LINE, 2).copy()
        d = ImageDraw.Draw(im)
        for i, ln in enumerate(lines):
            t2 = text_img(ln, 32, ACCENT if i == 0 else INK, i == 0)
            im.alpha_composite(t2, (30, 28 + i * 54))
        return im
    if k == "pair":
        cw = (SAFE_R - SAFE_L - 36) // 2
        a = card_img(cw, 430, 26).copy()
        b = card_img(cw, 430, 26).copy()
        ta = text_img(el["a"], 46, ACCENT, True)
        a.alpha_composite(ta, ((cw - ta.width) // 2, 44))
        sa = text_img(el["ad"], 32, MUTED, spacing=1.5)
        a.alpha_composite(sa, ((cw - sa.width) // 2, 140))
        tb = text_img(el["b"], 46, BLUE, True)
        b.alpha_composite(tb, ((cw - tb.width) // 2, 44))
        sb = text_img(el["bd"], 32, MUTED, spacing=1.5)
        b.alpha_composite(sb, ((cw - sb.width) // 2, 140))
        out = Image.new("RGBA", (SAFE_R - SAFE_L, 430), (0, 0, 0, 0))
        out.alpha_composite(a, (0, 0))
        out.alpha_composite(b, (cw + 36, 0))
        return out
    if k == "steps":
        items = el["items"]
        cw = SAFE_R - SAFE_L
        out = Image.new("RGBA", (cw, 100 * len(items)), (0, 0, 0, 0))
        for i, it in enumerate(items):
            row = card_img(cw, 80, 16, (16, 21, 30), LINE, 2).copy()
            d = ImageDraw.Draw(row)
            d.ellipse((26, 20, 66, 60), fill=ACCENT + (255,))
            n = text_img(str(i + 1), 26, (10, 14, 20), True)
            row.alpha_composite(n, (46 - n.width // 2, 40 - n.height // 2))
            t2 = text_img(it, 38, INK, True)
            row.alpha_composite(t2, (92, 40 - t2.height // 2))
            out.alpha_composite(row, (0, i * 100))
        return out
    if k == "rows":
        rows = el["rows"]
        cw = SAFE_R - SAFE_L
        out = Image.new("RGBA", (cw, 150 * len(rows)), (0, 0, 0, 0))
        for i, (key, val, ac) in enumerate(rows):
            out.alpha_composite(kv_row(cw, 120, key, val, ac), (0, i * 150))
        return out
    if k == "warn":
        rows = el["rows"]
        cw = SAFE_R - SAFE_L
        out = Image.new("RGBA", (cw, 140 * len(rows)), (0, 0, 0, 0))
        for i, r in enumerate(rows):
            row = card_img(cw, 112, 16, (30, 22, 18), (60, 40, 30), 2).copy()
            d = ImageDraw.Draw(row)
            d.rounded_rectangle((0, 0, 8, 112), 4, fill=ORANGE + (255,))
            t2 = text_img(r, 34, INK, True)
            row.alpha_composite(t2, (32, (112 - t2.height) // 2))
            out.alpha_composite(row, (0, i * 140))
        return out
    if k == "num":
        return num_card(SAFE_R - SAFE_L, el.get("h", 300), el["num"], el["unit"], el["label"])
    raise ValueError(f"未知元素 {k}")


def render_frame(t):
    GUARD.reset()
    base = Image.new("RGBA", (W, H), BG + (255,))
    kicker(base, "AGNES AI · 免费使用")
    progress(base, t / TOTAL)

    for start, dur, els in SCENES:
        if not (start <= t < start + dur):
            continue
        for el in els:
            at = start + el.get("delay", 0)
            if t < at:
                continue
            # 入场淡入，场景结束前 0.22s 淡出，避免场景间元素重叠
            a = fin(t - at, 0.26)
            fade_out_at = start + dur - 0.22
            if t > fade_out_at:
                a *= fout(t - fade_out_at, 0.22)
            if a <= 0.002:
                continue
            layer = render_el(el, t)
            dy = 22 * (1 - fin(t - at, 0.26))
            paste(base, layer, el.get("x", SAFE_L), el["y"], a, dy)
    # --- mgkit: overlap check ---
    GUARD.check(f"t={t:.2f}")
    # --- end mgkit ---
    return base.convert("RGB")


def make_contact():
    marks = [0.6, 2.8, 4.2, 6.0, 8.0, 11.2, 13.8, 17.2, 18.8, 20.8, 23.2]
    cw, ch = 300, 533
    sheet = Image.new("RGB", (cw * 4, ch * 3), (18, 18, 22))
    for i, t in enumerate(marks):
        fr = render_frame(t)
        fr.save(HERE / f"帧-{i+1:02d}-{t:.1f}s.png")
        thumb = fr.resize((cw, ch), Image.LANCZOS)
        td = ImageDraw.Draw(thumb)
        td.rectangle((0, 0, cw, 34), fill=(10, 14, 20))
        td.text((10, 6), f"{t:.1f}s", font=font(22, True), fill=(0, 229, 160))
        sheet.paste(thumb, ((i % 4) * cw, (i // 4) * ch))
    sheet.save(HERE / "检查图-MG样片.png")
    write_report(GUARD, HERE, "A 深色科技")
    print(f"检查图 {len(marks)} 格 → 检查图-MG样片.png")


def main():
    preview = "--preview" in sys.argv
    make_contact()
    if preview:
        print("--preview，仅生成关键帧检查图")
        return
    out = HERE / "MG-样片-无声.mp4"
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
