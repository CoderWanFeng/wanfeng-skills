#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成晚枫数字人（普通版）执行流总览图 → assets/execution-flow.png。

配色是**暖色系**：深暖褐底 + 琥珀橙强调色，用来和 mograph 系列的冷绿区分开。

按项目既有设计铁律走：
- **Pillow 2 倍超采样自绘** → LANCZOS 缩回 1080 宽；
- 所有文字**显式用 anchor="lt" 给字顶**，不踩「text() 的 y 是基线」的坑；
- 卡片：圆角 46、白描边 + 大投影、左侧一道橙色刻度条。

**半透明必须走独立图层**：Pillow 的 ImageDraw 直接画在 RGBA 图上不做 alpha 混合，
会把 fill 的 RGB 原样写死（alpha 被丢弃）。所有半透明元素统一走 overlay()。

用法：
    python3 scripts/make_flow_diagram.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- 设计令牌（暖色系）

SCALE = 2                 # 2 倍超采样
DW = 1080                 # 设计宽（最终成图 1080）
PAD = 60

INK = (14, 9, 6)
TEXT = (255, 246, 238)
DIM = (200, 178, 161)
ACCENT = (255, 140, 66)   # 琥珀橙

FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
IDX_W3, IDX_W6 = 0, 2     # index 0 = W3，index 2 = W6

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "assets", "execution-flow.png")


def font(size, weight=IDX_W3):
    return ImageFont.truetype(FONT_PATH, int(size * SCALE), index=weight)


def measure(s, size, weight=IDX_W3):
    return font(size, weight).getbbox(s)[2] / SCALE


def _assert_fit(s, size, limit, where):
    """文案宽度断言：超出可用宽度就报错，避免文字顶出卡片。"""
    w = measure(s, size)
    if w > limit:
        raise SystemExit("文案溢出（%s）：%.0f > %.0f —— %s" % (where, w, limit, s))


def overlay(img, fn):
    """在独立 RGBA 层上绘制，再 alpha_composite 回去（半透明必须走这条路）。"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    return Image.alpha_composite(img, layer)


def bg_layer(w, h):
    """竖向暖褐渐变 #150E09 → #231810 + 6% 网格 + 左上角橙光。"""
    top = (0x15, 0x0E, 0x09)
    bot = (0x23, 0x18, 0x10)
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    step = 90 * SCALE
    for x in range(0, w, step):
        gd.line([(x, 0), (x, h)], fill=(255, 235, 220, 14))
    for y in range(0, h, step):
        gd.line([(0, y), (w, y)], fill=(255, 235, 220, 14))
    img = Image.alpha_composite(img.convert("RGBA"), grid)

    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gld = ImageDraw.Draw(glow)
    r = 620 * SCALE
    gld.ellipse([-r // 3, -r // 3, r, r], fill=ACCENT + (32,))
    glow = glow.filter(ImageFilter.GaussianBlur(120 * SCALE))
    return Image.alpha_composite(img, glow)


def shadow_rrect(img, box, radius, blur=44, offset=(0, 26), alpha=200):
    """卡片投影。"""
    x0, y0, x1, y1 = [v * SCALE for v in box]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x0, y0 + offset[1] * SCALE,
                          x1, y1 + offset[1] * SCALE],
                         radius=radius * SCALE, fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur * SCALE))
    return Image.alpha_composite(img, layer)


# ---------------------------------------------------------------- 画布

class Canvas(object):
    """持有图对象；每次取 draw 都重新绑定，避免 alpha_composite 换图后画到旧图上。"""

    def __init__(self, w, h):
        self.img = bg_layer(w, h)
        self.y = PAD

    @property
    def d(self):
        return ImageDraw.Draw(self.img)

    def text(self, x, y, s, size, fill=TEXT, weight=IDX_W3, anchor="lt"):
        self.d.text((x * SCALE, y * SCALE), s, font=font(size, weight),
                    fill=fill, anchor=anchor)

    def rrect(self, box, radius, fill=None, outline=None, width=1.0):
        """半透明圆角矩形：走 overlay 做 alpha 混合。"""
        def fn(d):
            d.rounded_rectangle([v * SCALE for v in box], radius=radius * SCALE,
                                fill=fill, outline=outline,
                                width=max(1, int(width * SCALE)))
        self.img = overlay(self.img, fn)

    def rect(self, box, **kw):
        self.d.rectangle([v * SCALE for v in box], **kw)

    def arrow_down(self, cx, y, h=24, color=ACCENT):
        x = cx * SCALE
        y0, y1 = y * SCALE, (y + h) * SCALE
        self.d.line([(x, y0), (x, y1 - 6 * SCALE)], fill=color, width=int(2.4 * SCALE))
        self.d.polygon([(x - 7 * SCALE, y1 - 8 * SCALE),
                        (x + 7 * SCALE, y1 - 8 * SCALE),
                        (x, y1)], fill=color)

    def badge(self, x, y, s, bg=ACCENT + (85,), fg=INK, size=19, pad_x=11, h=26):
        """小徽章。橙底配深色字，跨明度。"""
        w = measure(s, size, IDX_W6) + pad_x * 2
        self.rrect((x, y, x + w, y + h), h / 2, fill=bg)
        self.text(x + pad_x, y + (h - size * 1.15) / 2, s, size, fg, IDX_W6)
        return w

    def card(self, x, y, w, h, radius=46):
        """卡片：投影 + 半透明底 + 13% 白描边 + 左侧橙色刻度条。"""
        self.img = shadow_rrect(self.img, (x, y, x + w, y + h), radius)
        self.rrect((x, y, x + w, y + h), radius,
                   fill=(20, 13, 9, 245), outline=(255, 235, 220, 34), width=3.2)
        seg = (h - 34) / 6.0
        for i in range(6):
            a = int(215 - i * 30)
            sy = y + 17 + i * seg
            self.rrect((x + 22, sy, x + 28, sy + seg - 5), 4, fill=ACCENT + (a,))
        return self


# ---------------------------------------------------------------- 版面

def build():
    # 画布高度必须大于内容最终高度：crop 越界时 Pillow 用纯黑填充。
    c = Canvas(DW * SCALE, 2400 * SCALE)

    # ── 标题区 ────────────────────────────────────────────────────────────
    c.text(PAD, c.y, "晚枫数字人 · 怎么做一条短片", 46, TEXT, IDX_W6)
    c.y += 62
    c.text(PAD, c.y, "一段你的视频 + 一句台词 → 画面里的你在说话 → 4–10 秒短片", 25, DIM)
    c.y += 46
    c.rect((PAD, c.y, PAD + 120, c.y + 5), fill=ACCENT)
    c.y += 34

    # ── 输入 ──────────────────────────────────────────────────────────────
    cx = PAD
    for label in ("你的视频（3 秒以上）或一张正脸照片", "一句台词（30 字以内）"):
        capw = measure(label, 22) + 44
        c.rrect((cx, c.y, cx + capw, c.y + 52), 26,
                fill=(255, 235, 220, 16), outline=(255, 235, 220, 46), width=1.6)
        c.text(cx + 22, c.y + 14, label, 22, TEXT)
        cx += capw + 14
    c.y += 52 + 18
    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    # ── 阶段标 ────────────────────────────────────────────────────────────
    def stage(title):
        c.rect((PAD, c.y, PAD + 4, c.y + 26), fill=ACCENT)
        c.text(PAD + 16, c.y + 1, title, 24, TEXT, IDX_W6)
        c.y += 38

    def step(no, title, sub, note=None, badge_text=None, h=84):
        """一张步骤卡：编号 + 标题 + 副行产出；徽章与右侧注统一放标题行右端。"""
        c.card(PAD, c.y, DW - PAD * 2, h)

        xr = DW - PAD - 24
        if badge_text:
            xr -= measure(badge_text, 19, IDX_W6) + 22 + 14
        if note:
            xr -= measure(note, 19)
        tx = PAD + 44 + measure(no, 26, IDX_W6) + 14
        _assert_fit(title, 27, xr - 12 - tx, "标题 %s" % no)
        _assert_fit(sub, 21, DW - PAD * 2 - 88, "副行 %s" % no)

        c.text(PAD + 44, c.y + 20, no, 26, ACCENT, IDX_W6)
        c.text(tx, c.y + 20, title, 27, TEXT, IDX_W6)
        c.text(PAD + 44, c.y + 52, sub, 21, DIM)

        xr = DW - PAD - 24
        if badge_text:
            bw = measure(badge_text, 19, IDX_W6) + 22
            c.badge(xr - bw, c.y + 18, badge_text)
            xr -= bw + 14
        if note:
            nw = measure(note, 19)
            c.text(xr - nw, c.y + 23, note, 19, DIM)
        c.y += h + 14

    # ── 先说边界（这条线做什么、不做什么）────────────────────────────────
    c.card(PAD, c.y, DW - PAD * 2, 138)
    c.text(PAD + 44, c.y + 20, "0", 26, ACCENT, IDX_W6)
    c.text(PAD + 44 + measure("0", 26, IDX_W6) + 14, c.y + 20,
           "先分清这条线能做什么", 27, TEXT, IDX_W6)
    c.text(PAD + 44, c.y + 52, "4–10 秒、模型配音、全程零成本只扣积分", 21, DIM)
    bx = PAD + 44
    for tag, desc, hot in (("这条线做", "一句话的短片", True),
                           ("走 Pro", "克隆音色、30 秒以上长片", False)):
        bw = measure(tag, 19, IDX_W6) + 22
        c.badge(bx, c.y + 88, tag,
                bg=ACCENT + (85,) if hot else (255, 235, 220, 30),
                fg=INK if hot else TEXT)
        c.text(bx + bw + 12, c.y + 92, desc, 20, DIM)
        bx += bw + 12 + measure(desc, 20) + 34
    if bx > DW - PAD - 20:
        raise SystemExit("边界卡分支行溢出右边界：%.0f > %.0f" % (bx, DW - PAD - 20))
    c.y += 138 + 14

    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    # ── 收素材 ────────────────────────────────────────────────────────────
    stage("① 收素材")
    step("1", "收到素材先体检",
         "多长、有没有正脸，一句话告诉你够不够用")
    step("2", "抽 3 张候选帧，挑正脸",
         "挑睁眼、嘴闭合的那张，别默认第一张")
    step("2.5", "裁成竖屏参考图",
         "裁好先给你看一眼，你点头再往下")

    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    # ── 出片子 ────────────────────────────────────────────────────────────
    stage("② 出片子")
    step("3", "台词先估时长",
         "按 4 字/秒算，超过 30 字就删掉或拆成两条")
    step("4", "生成一条 5 秒短片",
         "画幅跟着素材走，生成完先自己看一遍",
         badge_text="先看成片")

    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    # ── 交付 ──────────────────────────────────────────────────────────────
    stage("③ 交付")
    step("5", "交三样东西，说三句话",
         "视频给你 / 声音是模型念的 / 一共没花钱")
    step("5.5", "可选：换成你的原声",
         "你录同一句台词发来，我贴上去",
         note="只对齐时长")
    step("5.6", "可选：挂上字幕",
         "有字幕文件就挂，没有就按台词长度均分")

    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    # ── 输出 ──────────────────────────────────────────────────────────────
    c.rrect((PAD, c.y, DW - PAD, c.y + 96), 24,
            fill=(255, 235, 220, 14), outline=ACCENT + (130,), width=1.8)
    c.text(PAD + 26, c.y + 16, "输出", 20, ACCENT, IDX_W6)
    c.text(PAD + 26, c.y + 44,
           "数字人短片  ｜  可选原声版  ｜  可选字幕版",
           21, TEXT)
    c.y += 96 + 18

    # ── 底部规则条 ────────────────────────────────────────────────────────
    c.rrect((PAD, c.y, DW - PAD, c.y + 58), 18,
            fill=(255, 235, 220, 14), outline=(255, 235, 220, 34), width=1.4)
    c.rect((PAD, c.y, PAD + 4, c.y + 58), fill=ACCENT)
    c.text(PAD + 20, c.y + 17,
           "声音是模型念的，别说是你的声音 —— 全程不花钱，只扣账号里的积分", 20, TEXT)
    c.y += 58 + PAD

    # ── 裁到实际高度 ──────────────────────────────────────────────────────
    final_h = int(c.y * SCALE)
    if final_h > c.img.height:
        raise SystemExit("内容高度 %d 超出画布 %d：请调大 build() 里的画布高度"
                         % (final_h, c.img.height))
    img = c.img.crop((0, 0, DW * SCALE, final_h))
    return img.convert("RGB").resize((DW, int(final_h / SCALE)), Image.LANCZOS)


def main():
    out = os.path.abspath(OUT)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img = build()
    img.save(out, "PNG", optimize=True)
    print("== 晚枫数字人 · 执行流总览图 ==")
    print("输出：%s" % out)
    print("尺寸：%dx%d" % img.size)


if __name__ == "__main__":
    sys.exit(main())
