# -*- coding: utf-8 -*-
"""公众号横版插图生成器 —— 暖白 · 暖黄设计语言（Pillow 自绘）。

用途：给「功能性描述 / 理论性描述」类文章段落配自制信息图，
替代没有信息量的通用图库图。与「官网/网页截图」类配图互补：
有界面就截图，没界面就画图。

设计语言：
    斜体 eyebrow + 细线  →  斜体黑标题  →  超大橙红强调
    →  白卡 + 橙圆勾  →  冷灰/暖黄面板  →  底部斜体脚注

用法：
    python3 warm_illustration.py --out /tmp/illus
    python3 warm_illustration.py --out /tmp/illus --only cover flow

产出尺寸：1200×675（封面）、1200×640（步骤图）、1200×600（正文图），JPEG q95。

新增一张图：复制任意 fig_* 函数 → 改数据与文案 → 改 save() 的文件名
→ 在 FIGS 字典登记 → 运行 → 逐张目检。
基元函数（card/text/itext/fit_text/badge_num/badge_check/arrow/panel/footer）
保持不变，风格自然一致。
"""
import argparse
import math
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("缺少依赖，请先执行：pip3 install pillow")

# ---------------------------------------------------------------- 基元常量
S = 2                       # 超采样倍数（画 2 倍再 LANCZOS 缩回，边缘更干净）
W = 1200                    # 输出宽度（横版）
PAD = 64                    # 左右安全边距

# 中文字体路径（按平台自动探测，也可通过环境变量 WARM_ILLUS_FONT 覆盖）
_FONT_CANDIDATES = [
    os.environ.get("WARM_ILLUS_FONT", ""),
    "/System/Library/Fonts/Hiragino Sans GB.ttc",   # macOS
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Ubuntu/Debian
    "C:/Windows/Fonts/msyh.ttc",                     # Windows
]

BG     = (250, 247, 241)    # 暖白底
CARD   = (255, 255, 255)    # 白卡
PANEL  = (238, 240, 243)    # 冷灰面板
WARM   = (255, 237, 220)    # 暖黄面板
BLUE   = (222, 234, 254)    # 浅蓝面板
ACCENT = (240, 118, 40)     # 橙红强调
INK    = (28, 32, 38)       # 正文墨
LINE   = (226, 229, 233)    # 描边
DIM    = (126, 134, 144)    # 次要灰
DIM2   = (162, 167, 173)    # 更浅灰（脚注）
WHITE  = (255, 255, 255)

_fc = {}
_font_path = None


def _find_font():
    global _font_path
    if _font_path:
        return _font_path
    for p in _FONT_CANDIDATES:
        if p and os.path.exists(p):
            _font_path = p
            return p
    raise FileNotFoundError(
        "找不到中文字体，请安装支持中文的字体，"
        "或设置环境变量 WARM_ILLUS_FONT=/path/to/font.ttc")


def font(size, bold=True):
    key = (size, bold)
    if key not in _fc:
        fp = _find_font()
        _fc[key] = ImageFont.truetype(fp, int(size * S), index=2 if bold else 0)
    return _fc[key]


def new(h):
    return Image.new("RGBA", (W * S, h * S), BG + (255,))


def glow(img, box, color, alpha=26, blur=16):
    x, y, w, h = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(
        [x * S, y * S, (x + w) * S, (y + h) * S], fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur * S)))


def itext(img, xy, s, size, color, bold=True, angle=12.0):
    """斜体文字（仿射剪切伪斜体）。"""
    f = font(size, bold)
    tlen = int(f.getlength(s))
    asc, desc = f.getmetrics()
    pad = 24
    k = math.tan(math.radians(angle))
    w = tlen + pad * 2 + int(size * abs(k)) + 20
    h = asc + desc + pad * 2
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((pad, pad), s, font=f, fill=color + (255,), anchor="lt")
    sheared = lay.transform((w, h), Image.AFFINE, (1, -k, k * h, 0, 1, 0),
                            resample=Image.BICUBIC)
    img.alpha_composite(sheared, (int(xy[0] * S), int(xy[1] * S)))
    return tlen / S


def text(img, xy, s, size, color, bold=True, anchor="lt"):
    f = font(size, bold)
    ImageDraw.Draw(img).text((xy[0] * S, xy[1] * S), s, font=f,
                             fill=color + (255,), anchor=anchor)


def tw(s, size, bold=True):
    return font(size, bold).getlength(s) / S


def fit_text(img, xy, s, size, color, bold=True, maxw=10**6, minsize=15):
    """按可用宽度自适应字号，避免文字溢出卡片。"""
    while size > minsize and tw(s, size, bold) > maxw:
        size -= 1
    text(img, xy, s, size, color, bold)
    return size


def card(img, box, radius=26, fill=CARD, border=LINE, shadow=True, sw=1):
    x, y, w, h = box
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [x * S, (y + 9) * S, (x + w) * S, (y + h + 9) * S],
            radius=radius * S, fill=(28, 32, 38, 26))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9 * S)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        [x * S, y * S, (x + w) * S, (y + h) * S],
        radius=radius * S, fill=fill + (255,))
    img.alpha_composite(layer)
    if border:
        ImageDraw.Draw(img).rounded_rectangle(
            [x * S, y * S, (x + w) * S, (y + h) * S], radius=radius * S,
            outline=border + (255,), width=int(sw * S))


def badge_check(img, cx, cy, r=22):
    d = ImageDraw.Draw(img)
    d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
              fill=ACCENT + (255,))
    lw = max(3, int(r * 0.22 * S))
    d.line([((cx - r * 0.40) * S, (cy + r * 0.02) * S),
            ((cx - r * 0.08) * S, (cy + r * 0.34) * S),
            ((cx + r * 0.44) * S, (cy - r * 0.34) * S)],
           fill=WHITE + (255,), width=lw, joint="curve")


def badge_num(img, cx, cy, n, r=22):
    d = ImageDraw.Draw(img)
    d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
              fill=ACCENT + (255,))
    text(img, (cx, cy + r * 0.02), str(n), int(r * 1.05), WHITE, True, anchor="mm")


def arrow(img, x, y, w=26, color=DIM2):
    d = ImageDraw.Draw(img)
    ym = y * S
    d.line([x * S, ym, (x + w * 0.62) * S, ym], fill=color + (255,), width=2 * S)
    d.line([((x + w * 0.34) * S, ym - 5 * S), ((x + w * 0.62) * S, ym),
            ((x + w * 0.34) * S, ym + 5 * S)], fill=color + (255,), width=2 * S)


def eyebrow(img, y, s, color=DIM2):
    itext(img, (PAD, y), s, 29, color, bold=False)
    d = ImageDraw.Draw(img)
    d.line([PAD * S, (y + 52) * S, (W - PAD) * S, (y + 52) * S],
           fill=LINE + (255,), width=1 * S)


def footer(img, h, s):
    itext(img, (PAD, h - 48), s, 26, DIM2, bold=False)


def panel(img, box, s, color=DIM, size=25, bold=True, radius=16, border=None, fill=None):
    x, y, w, h = box
    if fill is None:
        fill = PANEL if color is DIM else WARM
    card(img, box, radius=radius, fill=fill, border=border, shadow=False)
    text(img, (x + w / 2, y + h / 2), s, size, color, bold, anchor="mm")


def save(img, name, out=None):
    path = os.path.join(out or ".", name)
    img.convert("RGB").resize((img.width // S, img.height // S),
                              Image.LANCZOS).save(path, quality=95)
    print("saved %s  %dx%d" % (path, img.width // S, img.height // S), flush=True)
    return path


# ---------------------------------------------------------------- 示例图

def fig_cover(out=None):
    """封面示例：超大橙红强调 + 右侧流程条。"""
    H = 675
    img = new(H)
    glow(img, (-180, -260, 900, 620), ACCENT, 20, 26)
    glow(img, (760, 300, 620, 560), (255, 214, 170), 24, 26)
    itext(img, (PAD, 54), "你的副标题写在这里", 29, DIM2, bold=False)
    d = ImageDraw.Draw(img)
    d.line([PAD * S, 106 * S, (W - PAD) * S, 106 * S], fill=LINE + (255,), width=1 * S)
    itext(img, (PAD, 148), "你的文章", 74, INK, bold=True)
    itext(img, (PAD, 246), "核心数字", 116, ACCENT, bold=True)
    itext(img, (PAD, 412), "副标题说明写在这里", 40, DIM, bold=False)
    footer(img, H, "自制封面 · 暖白风格")
    return save(img, "example-cover.jpg", out)


def fig_flow(out=None):
    """流程图示例：编号卡 + 箭头 + 底部说明条。"""
    H = 600
    img = new(H)
    glow(img, (-200, -240, 880, 560), ACCENT, 18, 24)
    eyebrow(img, 56, "完整流程")
    itext(img, (PAD, 132), "五个环节讲清楚", 58, INK, bold=True)
    steps = [
        ("第一步", "先做什么\n说明文字"),
        ("第二步", "再做什么\n说明文字"),
        ("第三步", "继续做\n说明文字"),
        ("第四步", "然后做\n说明文字"),
        ("第五步", "最后做\n说明文字"),
    ]
    n = len(steps)
    gap = 18
    cw = (W - PAD * 2 - gap * (n - 1)) / n
    y, ch = 240, 190
    for i, (t1, t2) in enumerate(steps):
        x = PAD + i * (cw + gap)
        card(img, (x, y, cw, ch), radius=22)
        badge_num(img, x + 34, y + 40, i + 1, r=19)
        fit_text(img, (x + 24, y + 74), t1, 29, INK, True, maxw=cw - 44)
        yy = y + 118
        for ln in t2.split("\n"):
            fit_text(img, (x + 24, yy), ln, 21, DIM, False, maxw=cw - 40)
            yy += 32
        if i < n - 1:
            arrow(img, x + cw + 3, y + ch / 2, 12)
    panel(img, (PAD, 456, W - PAD * 2, 62), "底部说明文字写在这里", size=27, radius=18)
    footer(img, H, "一张图讲清楚整个流程")
    return save(img, "example-flow.jpg", out)


def fig_why(out=None):
    """数据图示例：超大橙红数字 + 四宫格指标卡。"""
    H = 600
    img = new(H)
    glow(img, (-200, -240, 880, 560), ACCENT, 18, 24)
    eyebrow(img, 56, "关键数字")
    itext(img, (PAD, 126), "核心结论", 58, INK, bold=True)
    itext(img, (PAD, 196), "0 元", 104, ACCENT, bold=True)
    data = [("0.00x", "指标一"), ("0", "指标二"), ("150+", "指标三"), ("1M", "指标四")]
    n = len(data)
    gap = 18
    cw = (W - PAD * 2 - gap * (n - 1)) / n
    y, ch = 348, 122
    for i, (v, k) in enumerate(data):
        x = PAD + i * (cw + gap)
        card(img, (x, y, cw, ch), radius=22)
        text(img, (x + cw / 2, y + 48), v, 50, ACCENT, True, anchor="mm")
        text(img, (x + cw / 2, y + 90), k, 24, DIM, False, anchor="mm")
    panel(img, (PAD, 486, W - PAD * 2, 52), "数据来源说明",
          color=(176, 106, 46), size=25, radius=16, border=(250, 224, 200))
    footer(img, H, "数字要当场实测再落笔")
    return save(img, "example-why.jpg", out)


FIGS = {
    "cover": fig_cover,
    "flow": fig_flow,
    "why": fig_why,
}


def main():
    ap = argparse.ArgumentParser(description="公众号横版插图生成器（暖白暖黄风格）")
    ap.add_argument("--out", default="./out", help="输出目录，默认 ./out")
    ap.add_argument("--only", nargs="*", choices=list(FIGS), help="只生成指定的几张")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name in (a.only or list(FIGS)):
        FIGS[name](a.out)
    print("done -> %s" % os.path.abspath(a.out))


if __name__ == "__main__":
    main()
