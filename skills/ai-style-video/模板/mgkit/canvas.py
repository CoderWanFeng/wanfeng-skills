#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""canvas — 画幅预设与画布适配

**为什么需要这一层**

8 个渲染器的场景数据（坐标 / 字号 / 卡片尺寸）全是按 **1080×1920** 手调的，
值就写死在各自的 `build_mg_*.py` 里。直接把画布尺寸改掉，版式会整体错位——
坐标、字号、证据卡尺寸是互相咬合的，改一个就得改一片。

所以拆成两层：

* **设计画布** 1080×1920 —— 渲染器内部照旧布局，所有手调坐标一个都不动
* **目标画幅** —— 本模块负责把设计画面映射到目标画布

**三种画幅的处理方式**

| 画幅 | 模式 | 做什么 |
|---|---|---|
| 9:16（默认） | `design` | 原样输出，零改动、零回归 |
| 2:3 / 4:5 / 1:1 | `fit` | 整体等比缩放 + 居中，风格底色补边（底色是纯色，接缝看不出来） |
| 16:9 / 4:3 | `relayout` | 竖版主画面 + 模糊延展背景，横版重排（详见 `参考/画幅适配.md`） |

**画幅来源优先级**

1. 环境变量 `MG_CANVAS`（例：`MG_CANVAS=4:5`）
2. 工程根 `canvas.json`（例 `{"ratio": "16:9"}`），从渲染器所在目录向上找
3. 默认 `9:16`

**canvas.json 完整字段**

```json
{
  "ratio": "16:9",
  "title": "横版右侧主标题（只有横版用得到）",
  "subtitle": "副标题，可省略",
  "title_role": "serif_bold",
  "subtitle_role": "serif_regular",
  "mode": "relayout"
}
```

`title_role` / `subtitle_role` 取 `fonts.py` 里的角色名（sans_bold /
sans_regular / serif_bold / serif_regular / brand_bold / brand_regular），
用来让横版标题栏的字体跟风格调性一致——工笔画配宋体、科技风配黑体。
不给就用 sans_bold / sans_regular。

`mode` 覆盖上面那张表的适配方式，取值 `design` / `fit` / `relayout`，
不给就用画幅预设的默认值。常见用法：1:1 嫌左右底色补边太素，改成
`relayout` 换成模糊延展背景（详见 `参考/画幅适配.md`）。

**用法**

```python
from mgkit import CANVAS          # 已在 mgkit 里导出
frame = CANVAS.fit_frame(frame)              # 输出前映射到目标画布
frame = CANVAS.fit_frame(frame, title="…")   # 横版显式传标题，覆盖配置
x, y, w, h = CANVAS.panel()                  # 横版右侧栏可用区，自己排版用
```
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

# 设计画布：所有渲染器的场景数据都按这个尺寸手调，不要改
DESIGN_W, DESIGN_H = 1080, 1920


@dataclass(frozen=True)
class Preset:
    """一种画幅预设。"""
    key: str
    label: str            # 竖屏 / 横屏 / 方形…
    platforms: str        # 主要投放平台
    W: int                # 目标输出宽
    H: int                # 目标输出高
    mode: str             # design | fit | relayout
    safe: dict = field(default_factory=dict)   # 平台 UI 安全区（占画布比例）
    note: str = ""        # 适配说明


PRESETS: dict[str, Preset] = {
    "9:16": Preset(
        "9:16", "竖屏", "抖音 / 视频号 / 小红书 / B站竖屏",
        1080, 1920, "design",
        {"top": 0.10, "bottom": 0.22, "left": 0.078, "right": 0.139},
        "默认画幅，与历史样片完全一致",
    ),
    "2:3": Preset(
        "2:3", "竖版", "小红书封面 / 竖版海报",
        1080, 1620, "fit",
        {"top": 0.08, "bottom": 0.16, "left": 0.078, "right": 0.078},
        "竖版内容整体缩放居中，两侧少量底色补边",
    ),
    "4:5": Preset(
        "4:5", "竖版方", "Instagram / 公众号长图",
        1080, 1350, "fit",
        {"top": 0.07, "bottom": 0.14, "left": 0.078, "right": 0.078},
        "竖版内容整体缩放居中，适合信息流竖版方",
    ),
    "1:1": Preset(
        "1:1", "方形", "朋友圈 / 公众号方形配图",
        1080, 1080, "fit",
        {"top": 0.06, "bottom": 0.12, "left": 0.07, "right": 0.07},
        "竖版内容整体缩放居中，方形封面通用",
    ),
    "16:9": Preset(
        "16:9", "横屏", "B站 / YouTube / 公众号横版 / 通用视频",
        1920, 1080, "relayout",
        {"top": 0.06, "bottom": 0.10, "left": 0.06, "right": 0.06},
        "竖版主画面 + 模糊延展背景；按《画幅适配.md》可再加左右分栏标题",
    ),
    "4:3": Preset(
        "4:3", "横版", "老式横版 / 展板 / 培训课件",
        1440, 1080, "relayout",
        {"top": 0.06, "bottom": 0.10, "left": 0.06, "right": 0.06},
        "竖版主画面 + 模糊延展背景",
    ),
}

DEFAULT_RATIO = "9:16"


def _corner_bg(frame: Image.Image) -> tuple:
    """从设计帧的四角取底色。

    风格背景几乎都是纯色或纯纹理，四角取中位数就能拿到接近的底色——
    这样补边时不用让每个渲染器都把自己的 BG 常量传进来。
    """
    w, h = frame.size
    pts = [(2, 2), (max(0, w - 3), 2), (2, max(0, h - 3)), (max(0, w - 3), max(0, h - 3))]
    px = [frame.convert("RGB").getpixel(p)[:3] for p in pts]
    return tuple(sorted(c[i] for c in px)[len(px) // 2] for i in range(3))


def _wrap(text: str, width: int, font, size: int, max_lines: int = 4) -> list[str]:
    """按像素宽度折行。中文逐字断行，英文优先在空格处断。

    超过 max_lines 行就截断并加省略号——标题栏不是放正文的地方。
    """
    text = (text or "").strip()
    if not text:
        return []
    lines: list[str] = []
    i, n = 0, len(text)
    while i < n and len(lines) < max_lines:
        j = i
        while j < n and _text_w(text[i:j + 1], font, size) <= width:
            j += 1
        if j == i:                      # 一个字都放不下，至少塞一个，避免死循环
            j = i + 1
        line = text[i:j]
        # 英文单词被从中间切断时，退到上一个空格
        if j < n and " " in line and line[-1] != " ":
            head = line.rsplit(" ", 1)[0]
            if head:
                line, j = head, i + len(head)
        lines.append(line.strip())
        i = j
    if i < n and lines:                 # 还有没排下的内容，末行加省略号
        lines[-1] = lines[-1].rstrip(" \u3000,，。") + "\u2026"
    return [ln for ln in (l.strip() for l in lines) if ln]


def _text_w(s: str, font, size: int = 32) -> int:
    """字符串像素宽度。拿不到 font 对象时按字号估（中日韩 1em，其它 0.55em）。"""
    if font is not None:
        try:
            return int(font.getlength(s))
        except Exception:
            try:
                return int(font.getsize(s)[0])
            except Exception:
                pass
    return int(sum(size if ord(c) > 0x2E80 else size * 0.55 for c in s))



MODES = ("design", "fit", "relayout")


class Canvas:
    """目标画幅。渲染器拿它决定「输出多大」和「怎么映射」。"""

    def __init__(self, preset: Preset, title: str = "", subtitle: str = "",
                 title_role: str = "sans_bold", subtitle_role: str = "sans_regular",
                 mode: str = ""):
        self.preset = preset
        self.ratio = preset.key
        self.label = preset.label
        self.platforms = preset.platforms
        # mode 允许工程覆盖预设的适配方式（见 canvas.json 的 "mode"）：
        # 竖版系嫌左右补边太素，可以改成 relayout 用模糊延展背景。
        self.mode = mode if mode in MODES else preset.mode
        self.safe = dict(preset.safe)
        self.note = preset.note

        # 横版右侧标题栏。留空时横版走「主画面居中」的通用兜底。
        self.title = title
        self.subtitle = subtitle
        # 字体角色，跟 fonts.py 的 ROLES 一致。想和风格调性统一就改这两个值。
        self.title_role = title_role or "sans_bold"
        self.subtitle_role = subtitle_role or "sans_regular"

        # 目标输出尺寸
        self.W = preset.W
        self.H = preset.H

        # 渲染器内部布局画布——恒为设计画布，所有画幅都一样。
        # 渲染器里的手调坐标因此永远不用改。
        self.DW, self.DH = DESIGN_W, DESIGN_H

    # ---------------------------------------------------------------- 安全区
    def safe_px(self) -> dict:
        """目标画布上的安全区（像素）。重排版式时按这个留白。"""
        s = self.safe
        return {
            "top": int(self.H * s.get("top", 0.08)),
            "bottom": int(self.H * s.get("bottom", 0.12)),
            "left": int(self.W * s.get("left", 0.07)),
            "right": int(self.W * s.get("right", 0.07)),
        }

    # ---------------------------------------------------------------- 缩略图
    def thumb(self, w: int, h: int) -> tuple:
        """检查图缩略图尺寸。

        9:16 直接给原值（保证默认路径下检查图和以前一模一样），
        其它画幅按目标宽高比重算，避免把横版画面压扁。
        """
        if self.mode == "design":
            return w, h
        return w, max(1, int(round(w * self.H / self.W)))

    # ---------------------------------------------------------------- 整帧映射
    def fit_frame(self, frame: Image.Image, title: str | None = None,
                  subtitle: str | None = None) -> Image.Image:
        """把设计画布上的整帧映射到目标画布。

        * design 模式：原样返回（零回归）
        * fit 模式：等比缩放 + 居中，底色补边
        * relayout 模式：竖版主画面 + 模糊延展背景（横版重排的自动底板）

        title / subtitle 只在横版（relayout）生效：给了标题，主画面左置、
        右侧排标题栏；不给就居中。竖版系传了也不报错，只是忽略。

        **不传 = 用 canvas.json 里的标题；传空串 = 明确不要标题**。
        想只要底板、自己往右侧栏画东西（《画幅适配.md》§3.3），就传 `title=""`
        再配 `panel()` 拿可用区。
        """
        if self.mode == "design":
            return frame
        if frame.size == (self.W, self.H):
            return frame
        if self.mode == "relayout":
            return self._relayout_frame(
                frame,
                self.title if title is None else title,
                self.subtitle if subtitle is None else subtitle,
            )
        return self._fit_frame(frame)

    # ---- fit：等比缩放 + 补边
    def _fit_frame(self, frame: Image.Image) -> Image.Image:
        bg = _corner_bg(frame)
        k = min(self.W / frame.width, self.H / frame.height)
        nw = max(1, int(round(frame.width * k)))
        nh = max(1, int(round(frame.height * k)))
        small = frame.resize((nw, nh), Image.LANCZOS)
        out = Image.new("RGB", (self.W, self.H), bg)
        out.paste(small, ((self.W - nw) // 2, (self.H - nh) // 2))
        return out

    # ---- 横版右侧可用区（画标题 / 卖点 / 数据用）
    def panel(self) -> tuple:
        """横版重排时，主画面右侧留给标题栏的矩形 (x, y, w, h)。

        竖版系没有侧栏概念，返回整幅画布。
        """
        if self.mode != "relayout":
            return (0, 0, self.W, self.H)
        s = self.safe_px()
        ph = self.H - s["top"] - s["bottom"]
        pw = int(round(ph * DESIGN_W / DESIGN_H))
        px = s["left"] + pw + int(self.W * 0.03)
        return (px, s["top"], max(0, self.W - s["right"] - px), ph)

    # ---- relayout：竖版主画面 + 模糊延展背景
    def _relayout_frame(self, frame: Image.Image, title: str = "",
                        subtitle: str = "") -> Image.Image:
        """横版重排的自动底板。

        做法：
          1. 把竖版画面放大裁切铺满横版画布 → 高斯模糊 → 压暗，得到延展背景
          2. 竖版主画面按高度等比缩放：
             · 有标题 → 贴左侧，右侧留给标题栏（真正的横版左右分栏）
             · 无标题 → 居中（通用兜底，不会出错）
          3. 主画面加一圈细边框 + 轻微投影，做出「卡片感」

        这是**自动底板**：想要更贴内容的横版版式，按《画幅适配.md》改。
        """
        # 1) 模糊延展背景
        scale = max(self.W / frame.width, self.H / frame.height)
        bw = max(self.W, int(round(frame.width * scale)))
        bh = max(self.H, int(round(frame.height * scale)))
        big = frame.resize((bw, bh), Image.LANCZOS)
        left = (bw - self.W) // 2
        top = (bh - self.H) // 2
        bg = big.crop((left, top, left + self.W, top + self.H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=max(8, self.W // 60)))
        # 压暗，让前景主画面跳出来
        from PIL import ImageEnhance
        bg = ImageEnhance.Brightness(bg).enhance(0.42)

        # 2) 主画面按高度缩放（留出上下安全区 + 一点呼吸）
        s = self.safe_px()
        pad = max(int(self.H * 0.035), s["top"], s["bottom"])
        k = (self.H - 2 * pad) / frame.height
        nw = max(1, int(round(frame.width * k)))
        nh = max(1, int(round(frame.height * k)))
        main = frame.resize((nw, nh), Image.LANCZOS)

        if title or subtitle:
            mx = s["left"]
        else:
            mx = (self.W - nw) // 2
        my = (self.H - nh) // 2

        out = bg.convert("RGBA")
        # 3) 投影 + 主画面 + 细边框
        shadow = Image.new("RGBA", (nw + 40, nh + 40), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle((20, 20, nw + 19, nh + 19), fill=(0, 0, 0, 150))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
        out.alpha_composite(shadow, (mx - 20, my - 20))
        out.alpha_composite(main.convert("RGBA"), (mx, my))
        d = ImageDraw.Draw(out)
        d.rectangle((mx - 1, my - 1, mx + nw, my + nh), outline=(255, 255, 255, 40), width=2)

        # 4) 右侧标题栏
        if title or subtitle:
            px, py, pw, ph = self.panel()
            if pw > 80:
                # 左右分栏的细分隔线，让「两个区」读得出来
                lx = px - int(self.W * 0.015)
                d.line((lx, py, lx, py + ph), fill=(255, 255, 255, 28), width=2)
                self._draw_title(d, px, py, pw, ph, title, subtitle)

        return out.convert("RGB")

    def _draw_title(self, d: ImageDraw.ImageDraw, x: int, y: int,
                    w: int, h: int, title: str, subtitle: str) -> None:
        """在横版右侧栏画标题。字号按画布高度推，不跟风格走。"""
        try:
            from fonts import load_font
        except Exception:  # 字体库不可用时退回 PIL 默认字体，不拦渲染
            load_font = None

        def fnt(size, bold):
            if not load_font:
                return None
            try:
                return load_font(self.title_role if bold else self.subtitle_role, size)
            except Exception:
                return None

        # 主标题：占栏高约 6%，最多 4 行，垂直居中
        t_size = max(28, int(self.H * 0.062))
        t_lines = _wrap(title, w, fnt(t_size, True), t_size)
        s_size = max(22, int(t_size * 0.52))
        s_lines = _wrap(subtitle, w, fnt(s_size, False), s_size) if subtitle else []

        gap = int(t_size * 0.30)
        block = len(t_lines) * int(t_size * 1.3) + (int(s_size * 1.7) if s_lines else 0) \
            + (gap if s_lines else 0)
        cy = y + max(0, (h - block) // 2)

        for ln in t_lines:
            d.text((x, cy), ln, font=fnt(t_size, True), fill=(242, 244, 248))
            cy += int(t_size * 1.3)
        if s_lines:
            cy += gap
            for ln in s_lines:
                d.text((x, cy), ln, font=fnt(s_size, False), fill=(176, 182, 194))
                cy += int(s_size * 1.7)

    def __repr__(self) -> str:
        return (f"<Canvas {self.ratio} {self.W}x{self.H} "
                f"mode={self.mode} layout={self.DW}x{self.DH}>")


def _normalize(raw: str) -> str:
    """`16x9` / `16：9` / `16:9` 都归一成 `16:9`。"""
    return (raw or "").strip().replace("x", ":").replace("X", ":").replace("：", ":")


def _find_canvas_json() -> Path | None:
    """从渲染器所在目录向上找工程根的 canvas.json。"""
    for p in Path(__file__).resolve().parents:
        q = p / "canvas.json"
        if q.exists():
            return q
    q = Path.cwd() / "canvas.json"
    return q if q.exists() else None


def load_cfg() -> dict:
    """读工程根 canvas.json。读不到就返回空表，不让配置问题把渲染搞崩。"""
    cfg = _find_canvas_json()
    if not cfg:
        return {}
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ⚠ canvas.json 读不动（{e}），按默认画幅走")
        return {}
    return data if isinstance(data, dict) else {}


def resolve_ratio() -> str:
    """按优先级解析目标画幅。"""
    raw = _normalize(os.environ.get("MG_CANVAS", ""))
    if not raw:
        raw = _normalize(str(load_cfg().get("ratio", "")))
    return raw or DEFAULT_RATIO


def get_canvas(ratio: str | None = None,
               title: str | None = None,
               subtitle: str | None = None,
               title_role: str | None = None,
               subtitle_role: str | None = None,
               mode: str | None = None) -> Canvas:
    """拿目标画幅。画幅不认识时退回 9:16 并提示，不让渲染直接崩。

    横版标题栏的文字与字体角色，来源优先级都是：
    显式传参 > 环境变量（MG_TITLE / MG_SUBTITLE / MG_TITLE_ROLE /
    MG_SUBTITLE_ROLE）> canvas.json 同名字段。
    标题都没给就不画标题栏，横版退回主画面居中。

    `mode` 同理（MG_CANVAS_MODE / canvas.json 的 "mode"），用来把竖版的
    `fit` 补边换成横版那套模糊延展背景；给了不认识的值就按预设走。
    """
    key = _normalize(ratio) if ratio else resolve_ratio()
    if key not in PRESETS:
        print(f"  ⚠ 未知画幅 {key!r}，退回 {DEFAULT_RATIO}；"
              f"可选：{' / '.join(PRESETS)}")
        key = DEFAULT_RATIO
    cfg = load_cfg()

    def pick(explicit, env, field, default=""):
        if explicit is not None:
            return explicit
        return os.environ.get(env) or str(cfg.get(field, default))

    m = pick(mode, "MG_CANVAS_MODE", "mode")
    if m and m not in MODES:
        print(f"  ⚠ 未知适配方式 {m!r}，按 {key} 预设的 {PRESETS[key].mode} 走；"
              f"可选：{' / '.join(MODES)}")
        m = ""

    return Canvas(
        PRESETS[key],
        pick(title, "MG_TITLE", "title"),
        pick(subtitle, "MG_SUBTITLE", "subtitle"),
        pick(title_role, "MG_TITLE_ROLE", "title_role", "sans_bold"),
        pick(subtitle_role, "MG_SUBTITLE_ROLE", "subtitle_role", "sans_regular"),
        m,
    )


def describe() -> str:
    """给用户看的一行摘要。"""
    c = get_canvas()
    return (f"{c.ratio}（{c.label}）{c.W}×{c.H} · {c.platforms} · 模式 {c.mode}")


def table() -> str:
    """所有画幅的对照表，给用户做选择题用。"""
    lines = ["| 画幅 | 尺寸 | 适合平台 | 适配方式 |", "|---|---|---|---|"]
    for p in PRESETS.values():
        lines.append(f"| {p.key} | {p.W}×{p.H} | {p.platforms} | {p.note} |")
    return "\n".join(lines)


CANVAS = get_canvas()

__all__ = ["Canvas", "Preset", "PRESETS", "MODES", "CANVAS", "get_canvas",
           "resolve_ratio", "load_cfg", "describe", "table",
           "DESIGN_W", "DESIGN_H", "DEFAULT_RATIO"]
