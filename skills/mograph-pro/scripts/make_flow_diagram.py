#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 mograph-pro 执行流总览图 → assets/execution-flow.png。

按本项目的设计铁律走：
- **Pillow 2 倍超采样自绘** → LANCZOS 缩回 1080 宽（与成片同宽）；
- 所有文字**显式用 anchor="lt" 给字顶**，不踩「text() 的 y 是基线」的坑；
- 配色取 §4.1 的设计令牌：INK / TEXT / DIM / ACCENT；AMBER 与 RED 不用于流程图（按令牌铁律）；
- 卡片：圆角 46、白描边 + 大投影、左侧一道绿色刻度条（§4.1 卡片规范）。

**半透明必须走独立图层**：Pillow 的 ImageDraw 直接画在 RGBA 图上**不做 alpha 混合**，
会把 fill 的 RGB 原样写死（alpha 被丢弃），半透明白描边会变成实白边。所以
所有半透明元素统一走 `overlay()` 画在独立 RGBA 层再 alpha_composite 回去。

用法：
    ~/.workbuddy/binaries/python/envs/default/bin/python3 scripts/make_flow_diagram.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- 设计令牌

SCALE = 2                 # 2 倍超采样
DW = 1080                 # 设计宽（最终成图 1080，与成片同宽）
PAD = 60

INK = (8, 11, 15)
TEXT = (243, 246, 248)
DIM = (168, 178, 188)
ACCENT = (0, 214, 147)
WHITE = (255, 255, 255)

FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
IDX_W3, IDX_W6 = 0, 2    # Hiragino Sans GB.ttc：index 0 = W3，index 2 = W6

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
    """竖向渐变 #0A0E13 → #101720 + 6% 网格 + 左上角品牌绿晕光（§4.1）。"""
    top = (0x0A, 0x0E, 0x13)
    bot = (0x10, 0x17, 0x20)
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
        gd.line([(x, 0), (x, h)], fill=(255, 255, 255, 15))
    for y in range(0, h, step):
        gd.line([(0, y), (w, y)], fill=(255, 255, 255, 15))
    img = Image.alpha_composite(img.convert("RGBA"), grid)

    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gld = ImageDraw.Draw(glow)
    r = 620 * SCALE
    gld.ellipse([-r // 3, -r // 3, r, r], fill=ACCENT + (26,))
    glow = glow.filter(ImageFilter.GaussianBlur(120 * SCALE))
    return Image.alpha_composite(img, glow)


def shadow_rrect(img, box, radius, blur=44, offset=(0, 26), alpha=190):
    """卡片投影（§4.1 卡片规范）。"""
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

    def badge(self, x, y, s, bg=ACCENT + (70,), fg=INK, size=19, pad_x=11, h=26):
        """小徽章（如「必须过这关」「可以剪」）。绿底配深色字，跨明度（§5.7 铁律）。"""
        w = measure(s, size, IDX_W6) + pad_x * 2
        self.rrect((x, y, x + w, y + h), h / 2, fill=bg)
        self.text(x + pad_x, y + (h - size * 1.15) / 2, s, size, fg, IDX_W6)
        return w

    def card(self, x, y, w, h, radius=46):
        """卡片：投影 + 半透明底 + 13% 白描边 + 左侧绿色刻度条。"""
        self.img = shadow_rrect(self.img, (x, y, x + w, y + h), radius)
        self.rrect((x, y, x + w, y + h), radius,
                   fill=(10, 13, 18, 245), outline=(255, 255, 255, 34), width=3.2)
        seg = (h - 34) / 6.0
        for i in range(6):
            a = int(210 - i * 30)
            sy = y + 17 + i * seg
            self.rrect((x + 22, sy, x + 28, sy + seg - 5), 4, fill=ACCENT + (a,))
        return self


# ---------------------------------------------------------------- 版面

def build():
    # 画布高度必须大于内容最终高度：crop 越界时 Pillow 用纯黑填充，
    # 会在底部留一条黑带。留足余量，裁剪前另有断言兜底。
    c = Canvas(DW * SCALE, 2600 * SCALE)

    # ── 标题区 ────────────────────────────────────────────────────────────
    c.text(PAD, c.y, "晚枫自动剪视频-Pro · 怎么做一条成片", 46, TEXT, IDX_W6)
    c.y += 62
    c.text(PAD, c.y, "真人口播 / 文稿生成数字人 → 语义 A/B 分镜 → 成片 + 封面", 25, DIM)
    c.y += 46
    c.rect((PAD, c.y, PAD + 120, c.y + 5), fill=ACCENT)
    c.y += 34

    # ── 输入 ──────────────────────────────────────────────────────────────
    cx = PAD
    for label in ("真人口播视频：人物始终可见", "文稿生成数字人：B 段无人像"):
        capw = measure(label, 22) + 44
        c.rrect((cx, c.y, cx + capw, c.y + 52), 26,
                fill=(255, 255, 255, 14), outline=(255, 255, 255, 40), width=1.6)
        c.text(cx + 22, c.y + 14, label, 22, TEXT)
        cx += capw + 14
    c.y += 52 + 18
    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    # ── 阶段标 ────────────────────────────────────────────────────────────
    def stage(title, en=""):
        c.rect((PAD, c.y, PAD + 4, c.y + 26), fill=ACCENT)
        c.text(PAD + 16, c.y + 1, title, 24, TEXT, IDX_W6)
        if en:
            c.text(PAD + 16 + measure(title, 24, IDX_W6) + 12, c.y + 6, en, 17, DIM)
        c.y += 38

    def step(no, title, sub, note=None, badge_text=None, h=84):
        """一张步骤卡：编号 + 标题 + 副行产出；徽章与右侧注统一放标题行右端。"""
        c.card(PAD, c.y, DW - PAD * 2, h)

        # 先算右侧注与徽章占掉的宽度，标题不能压到它们
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

    stage("① 来源选择与预分镜")
    step("入口", "①有无口播 → ②有无数字人 → ③生成方式 → ④素材",
         "生成方式一次列全选一次；原生 H3，其他模型走自备片段")
    step("画幅", "先确认要不要生成宽屏",
         "只做竖版 / 横竖都做 / 只做宽屏；已明确不重问")

    # Step 0 是决策卡，单独画
    c.card(PAD, c.y, DW - PAD * 2, 134)
    c.text(PAD + 44, c.y + 20, "Step 0", 26, ACCENT, IDX_W6)
    c.text(PAD + 44 + measure("Step 0", 26, IDX_W6) + 14, c.y + 20,
           "真人线：剪掉废话前先问你", 27, TEXT, IDX_W6)
    c.text(PAD + 44, c.y + 52, "不能自作主张剪掉你说的话，要先问过你", 21, DIM)
    bx = PAD + 44
    for tag, desc in (("可以剪", "剪掉重录的废稿和长停顿"),
                      ("不能剪", "原话原样，一个字不动")):
        bw = measure(tag, 19, IDX_W6) + 22
        c.badge(bx, c.y + 88, tag)
        c.text(bx + bw + 12, c.y + 92, desc, 20, DIM)
        bx += bw + 12 + measure(desc, 20) + 34
    c.y += 134 + 14

    step("预分镜", "两条线都按语义判断 A / B", "确定内容和素材需求，不硬套比例；估时不是正式时间")
    step("数字人", "确认分镜 → 配音试听 → 出镜样段", "只生成 A 段，B 段保留旁白；每个生成阶段先确认费用")
    step("底片", "完整时间轴 → A/B 素材对齐", "不使用只拼 A 段的 talking.mp4；B 占位须补真实画面")
    step("A", "定卡片长什么样、放哪儿",
         "照着定好的样式来做，保证每期看着一样")
    step("A2", "配图：找截图、找插图",
         "按讲的内容配图，标好来源，以后查得到出处")

    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    stage("② 制作")
    step("B", "把稿子拆成一段段画面",
         "按实测时间定 layers；真人全程有人，数字人 B 禁止人头")
    step("C", "先看单张画面",
         "先导出几张图看一眼，改干净再往下",
         note="改一下样式只要几秒", badge_text="必须过这关")
    step("D", "把整条片子做出来",
         "一张一张画出来，再拼成一条", note="约 6 分钟")
    step("E", "最后检查一遍",
         "每个画面挑一张图，一张一张看有没有问题")

    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    stage("③ 交付")
    step("F", "音量调成统一标准",
         "量一遍音量，对齐平台要求", note="两个版本音量一致")
    step("G", "写交付说明",
         "写清这期用了什么样式，下期直接抄", note="存档版 + 上传版")
    step("H", "做封面：竖横各用自己的版式",
         "竖版换字与 logo；宽屏沿用同一肖像、单独排版", note="不换人像")

    c.arrow_down(DW / 2, c.y, 22)
    c.y += 30

    # ── 输出 ──────────────────────────────────────────────────────────────
    c.rrect((PAD, c.y, DW - PAD, c.y + 96), 24,
            fill=(255, 255, 255, 12), outline=ACCENT + (120,), width=1.8)
    c.text(PAD + 26, c.y + 16, "输出", 20, ACCENT, IDX_W6)
    c.text(PAD + 26, c.y + 44,
           "存档版视频  ｜  上传版视频（音量已对齐）  ｜  封面图  ｜  交付说明文档",
           21, TEXT)
    c.y += 96 + 18

    # ── 底部规则条 ────────────────────────────────────────────────────────
    c.rrect((PAD, c.y, DW - PAD, c.y + 58), 18,
            fill=(255, 255, 255, 12), outline=(255, 255, 255, 30), width=1.4)
    c.rect((PAD, c.y, PAD + 4, c.y + 58), fill=ACCENT)
    c.text(PAD + 20, c.y + 17,
           "C 步没过别急着做 D 步 —— 整条片子要 6 分钟，画面问题在单张图上改只要几秒", 20, TEXT)
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
    parent = os.path.dirname(out)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    img = build()
    img.save(out, "PNG", optimize=True)
    print("== mograph-pro · 执行流总览图 ==")
    print("输出：%s" % out)
    print("尺寸：%dx%d" % img.size)


if __name__ == "__main__":
    sys.exit(main())
