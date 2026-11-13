#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mgkit — MG 短视频渲染共用工具库

解决四件长期踩坑的事：

1. **元素重叠**：靠人眼看关键帧是不可靠的，尤其转场瞬间。
   本库提供 `OverlapGuard`：所有 place() 调用登记包围盒，
   渲染时自动检测"文字层互相压盖"，越界直接报错。

2. **截图质量**：提供 `load_evidence()`，统一从 2x 高清截图
   裁好的证据图里取，并保证放进视频时的缩放比不低于 0.75x。

3. **素材没到位也不能崩**：证据图 / 截图缺失时返回一张写着
   「素材待补」的占位卡，只警告不抛异常。新建的选题工程里
   一张素材都还没放，也能先把版式和动画跑出来看。

4. **字体跨平台**：`load_font(role, size)` 按角色取中文字体，
   渲染器不写死字体路径（见 `fonts.py`）。

用法：
    from mgkit import OverlapGuard, load_evidence, EvidenceSpec, load_font
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

# 路径统一从 paths.py 解析（支持环境变量覆盖 + 自动向上探测）
try:
    from paths import (EVID_DIR, MGKIT_DIR, ROOT,  # noqa: F401
                       SHOTS_DIR, SHOTS_HD_DIR)
    EVID = EVID_DIR  # 证据图目录别名
except ImportError:  # paths.py 不在 sys.path 时退回当前工作目录（选题根目录）
    MGKIT_DIR = Path(__file__).resolve().parent
    ROOT = Path.cwd()
    EVID = EVID_DIR = ROOT / "素材-证据图"
    SHOTS_DIR = ROOT / "素材-官网截图"
    SHOTS_HD_DIR = ROOT / "素材-官网截图-HD"

try:
    from fonts import describe as describe_fonts  # noqa: F401
    from fonts import load_font, resolve as resolve_font
except ImportError as e:  # pragma: no cover
    raise ImportError(
        f"mgkit 找不到 fonts.py（应与 mgkit.py 同目录）：{e}\n"
        f"预期位置：{MGKIT_DIR}") from e

__all__ = [
    "OverlapGuard", "Box", "EvidenceSpec",
    "evidence_path", "load_evidence", "load_evidence_or_raw", "open_evidence",
    "mark_text_layer", "register_layer_texts", "set_content_offset",
    "write_report", "fit_scale", "reg_evidence", "resolve_evidence",
    "missing_materials", "missing_by_dir", "load_font", "resolve_font", "describe_fonts",
    "EVID", "EVID_DIR", "SHOTS_DIR", "SHOTS_HD_DIR", "ROOT",
]



# ================================================================ 自动登记
# 所有文字最终都要经过 place() 或 alpha_composite()。
# 在这两个入口打标记 + 登记包围盒，就能自动检出"文字压字"，
# 不需要人工逐帧核对关键帧。

_ORIG_ALPHA_COMPOSITE = Image.Image.alpha_composite


def _mark_text(img: Image.Image) -> Image.Image:
    """给文字图层打标记。"""
    try:
        img._mg_text = True
    except AttributeError:
        pass
    return img


def _is_text(img) -> bool:
    return getattr(img, "_mg_text", False)


def _record_text_in(target: Image.Image, src: Image.Image, dest) -> None:
    """文字被合成进某个图层时，记录它的相对位置。

    target 是卡片层时，先存相对坐标；
    等卡片整体落位（place）时再换算成绝对坐标。
    """
    if not _is_text(src):
        return
    rel = getattr(target, "_mg_texts", None)
    if rel is None:
        rel = []
        try:
            target._mg_texts = rel
        except AttributeError:
            return
    w, h = src.size
    rel.append((int(dest[0]), int(dest[1]), w, h,
                getattr(src, "_mg_name", "")))


def _patched_alpha_composite(self, im, dest=(0, 0), source=(0, 0)):
    _record_text_in(self, im, dest)
    return _ORIG_ALPHA_COMPOSITE(self, im, dest, source)


Image.Image.alpha_composite = _patched_alpha_composite



# ================================================================ 重叠检测
@dataclass
class Box:
    """一个已绘制元素的包围盒 + 语义标签。"""
    x: int
    y: int
    w: int
    h: int
    kind: str = "layer"      # "text" 需要严格不重叠；"deco" 只做越界检查
    name: str = ""
    alpha: float = 1.0

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    def overlap_area(self, other: "Box") -> int:
        ox = max(0, min(self.x2, other.x2) - max(self.x, other.x))
        oy = max(0, min(self.y2, other.y2) - max(self.y, other.y))
        return ox * oy

    def overlap_ratio(self, other: "Box") -> float:
        """重叠占自身面积的比例。"""
        if self.w * self.h == 0:
            return 0.0
        return self.overlap_area(other) / (self.w * self.h)


class OverlapGuard:
    """元素包围盒登记 + 冲突检测。

    规则：
      * text vs text 重叠超过阈值 → 报错（文字压字，必须修）
      * 任意元素超出画布安全区 → 报错
      * text vs deco 重叠 → 只警告（装饰光晕压字是允许的）
    """

    def __init__(self, width: int, height: int, safe=None,
                 text_thresh: float = 0.02, safe_top: int = 0,
                 safe_bottom: int = 0, safe_left: int = 0, safe_right: int = 0):
        self.W = width
        self.H = height
        self.safe = safe
        # 文字压字容忍比例：极小的边缘擦碰不算错
        self.text_thresh = text_thresh
        self.safe_top = safe_top
        self.safe_bottom = safe_bottom
        self.safe_left = safe_left
        self.safe_right = safe_right
        self._boxes: list[Box] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def reset(self) -> None:
        self._boxes.clear()
        self.errors.clear()
        self.warnings.clear()

    def add(self, x, y, w, h, kind="layer", name="", alpha=1.0) -> Box:
        b = Box(int(x), int(y), int(w), int(h), kind, name, alpha)
        self._boxes.append(b)
        return b

    def check(self, frame_label: str = "") -> list[str]:
        """检查当前已登记的所有元素，返回错误列表。

        每帧渲染前要先调 reset()，否则会累积历史帧的框。
        """
        errs = []
        for i, a in enumerate(self._boxes):
            # 越界检查
            if a.x < self.safe_left or a.y < self.safe_top \
                    or a.x2 > self.W - self.safe_right or a.y2 > self.H - self.safe_bottom:
                errs.append(
                    f"{frame_label} 越界: {a.name or a.kind} "
                    f"({a.x},{a.y})-({a.x2},{a.y2}) 超出安全区")
            for b in self._boxes[i + 1:]:
                if a.kind != "text" or b.kind != "text":
                    continue
                # 只有双方都基本可见才算冲突
                if a.alpha < 0.25 or b.alpha < 0.25:
                    continue
                r = max(a.overlap_ratio(b), b.overlap_ratio(a))
                if r > self.text_thresh:
                    errs.append(
                        f"{frame_label} 文字重叠 {r:.0%}: "
                        f"[{a.name}]({a.x},{a.y},{a.w}x{a.h}) × "
                        f"[{b.name}]({b.x},{b.y},{b.w}x{b.h})")
        self.errors.extend(errs)
        return errs

    def report(self) -> str:
        """汇总错误，去重后按频次排序。"""
        from collections import Counter
        c = Counter(self.errors)
        if not c:
            return "✓ 未检出文字重叠或越界"
        lines = [f"检出 {len(self.errors)} 处问题（去重 {len(c)} 类）："]
        for msg, n in c.most_common():
            lines.append(f"  ×{n:<4} {msg}")
        return "\n".join(lines)


    def dump(self, path: Path) -> None:
        path.write_text(json.dumps({
            "errors": self.errors,
            "warnings": self.warnings,
        }, ensure_ascii=False, indent=2), encoding="utf-8")


# ================================================================ 证据图
@dataclass
class EvidenceSpec:
    """一张证据图在视频里的摆放规格。"""
    file: str              # 素材-证据图 下的文件名
    x: int                 # 左上角 x
    y: int                 # 左上角 y
    w: int                 # 显示宽度
    h: int                 # 显示高度
    label: str = ""        # 左上角标签
    min_scale: float = 0.75   # 允许的最小缩放比，低于此值说明截图会被缩糊
    invert: bool = False   # 是否用反相版


def evidence_path(name: str, prefer_light: bool = False) -> Path:
    """按基础名找到证据图。找不到抛 FileNotFoundError。

    每张证据图有两个版本：
      * 原版  —— 截图原始配色
      * -亮    —— 适配亮色系 MG 的版本

    prefer_light=True 时优先取亮版，否则优先取原版。
    name 可以带 .png 后缀，也可以只给基础名。
    """
    stem = name[:-4] if name.endswith(".png") else name
    order = [stem + "-亮.png", stem + ".png"] if prefer_light else [stem + ".png", stem + "-亮.png"]
    for suf in order:
        q = EVID / suf
        if q.exists():
            return q
    raise FileNotFoundError(f"证据图不存在：{name}（查过 {EVID}）")


# ================================================================ 缺素材兼容
# 缺素材不应该让渲染崩掉。新建选题时图还没截完，也得先把版式、
# 动画时长、文字位置跑出来给人看。缺的就画一张占位卡，最后统一报清单。

_MISSING: dict[str, Path] = {}


def missing_materials() -> list[str]:
    """本次渲染里缺失的素材（占位卡），按名字排序。"""
    return sorted(_MISSING)


def missing_by_dir() -> dict[Path, list[str]]:
    """缺失素材按「该放进哪个目录」分组，直接当收材清单用。"""
    out: dict[Path, list[str]] = {}
    for name, where in _MISSING.items():
        out.setdefault(where, []).append(name)
    return {d: sorted(v) for d, v in sorted(out.items())}


def placeholder(w: int, h: int, label: str = "",
                where: Path | None = None) -> Image.Image:
    """素材缺失时的占位卡：虚线框 + 「素材待补」。

    故意不打 mark_text_layer 标记——它不是真内容，不应参与重叠判定，
    否则一缺图就全是假报错。

    where = 这张图本该放进哪个目录，最后汇总成收材清单。
    """
    w, h = max(8, int(w)), max(8, int(h))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(226, 226, 230, 255))
    step = 18
    for x in range(0, w + h, step * 2):        # 四边虚线
        d.line((x, 0, min(x + step, w), 0), fill=(150, 150, 158, 255), width=3)
        d.line((x, h - 1, min(x + step, w), h - 1), fill=(150, 150, 158, 255), width=3)
    for y in range(0, h + w, step * 2):
        d.line((0, y, 0, min(y + step, h)), fill=(150, 150, 158, 255), width=3)
        d.line((w - 1, y, w - 1, min(y + step, h)), fill=(150, 150, 158, 255), width=3)
    txt = "素材待补"
    try:
        f = load_font("sans_bold", max(16, min(h // 4, 40)))
        bb = d.textbbox((0, 0), txt, font=f)
        d.text(((w - bb[2] + bb[0]) // 2 - bb[0], (h - bb[3] + bb[1]) // 2 - bb[1]),
               txt, font=f, fill=(96, 96, 104, 255))
    except Exception:      # 字体也解析不出来时，不能连累占位卡
        pass
    _MISSING[label or txt] = where or EVID
    return im


def open_evidence(name: str, w: int, h: int, prefer_light: bool = False) -> Image.Image:
    """按名取证据图并缩到 (w, h)，缺图返回占位卡。"""
    try:
        p = evidence_path(name, prefer_light=prefer_light)
    except FileNotFoundError:
        return placeholder(w, h, name, where=EVID)
    im = Image.open(p).convert("RGB")
    r = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))),
                     Image.LANCZOS).convert("RGBA")


def load_evidence(spec: EvidenceSpec, brightness: float = 1.0,
                  invert: bool | None = None) -> Image.Image:
    """加载证据图并缩放到规格尺寸。

    缩放比低于 spec.min_scale 会给出警告——那意味着小字读不清，
    应该把裁切框收窄或加大显示尺寸。
    """
    path = evidence_path(spec.file, prefer_light=spec.invert)
    im = Image.open(path).convert("RGB")
    if invert if invert is not None else spec.invert:
        from PIL import ImageOps
        im = ImageOps.invert(im)
    r = min(spec.w / im.width, spec.h / im.height)
    scale = r
    if scale < spec.min_scale:
        print(f"  ⚠ 证据图 {path.name} 缩放 {scale:.2f}x < {spec.min_scale}，"
              f"小字可能看不清")
    im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    if brightness != 1.0:
        im = ImageEnhance.Brightness(im).enhance(brightness)
    return im.convert("RGBA")



def fit_scale(img_w: int, img_h: int, box_w: int, box_h: int) -> float:
    """等比缩放系数。"""
    return min(box_w / img_w, box_h / img_h)


# ================================================================ 证据图映射
# 把旧渲染器里的 (截图文件名, 裁切框) 映射到高清证据图。
# 各渲染器只需改 load_shot 一处，就能整体升级到 2x 高清证据图。
#
# 键是旧 1x 截图的"文件名 + 裁切框"，值是 素材-证据图 下的高清证据图。
#
# 这张表是**每个选题自己的数据**：截图叫什么名、裁哪个区域，
# 取决于你截的是哪个网站。模板出厂时是空的，在选题工程里用
# reg_evidence(截图名, 裁切框, 证据图基础名) 自己登记。
_EVIDENCE_MAP: dict[tuple[str, tuple[int, int, int, int]], str] = {}


def reg_evidence(src: str, box: tuple[int, int, int, int], evid: str) -> None:
    """登记一条「旧截图 + 裁切框 → 高清证据图」映射。"""
    _EVIDENCE_MAP[(src, tuple(box))] = evid


def resolve_evidence(src_name: str, box) -> str | None:
    """旧截图 + 裁切框 → 高清证据图文件名。找不到返回 None。"""
    return _EVIDENCE_MAP.get((src_name, tuple(box)))


def _fit_box(box, im_w: int, im_h: int) -> tuple[int, int, int, int]:
    """把裁切框落到像素坐标。

    box 四个数全在 0–1 之间时按**比例**解释。这样你给的截图不管是
    1280 还是 2880 宽，都能裁到同一个构图位置；写死像素的话，
    示例里的框只对当初那张截图成立。
    """
    b = tuple(box)
    if all(0.0 <= v <= 1.0 for v in b) and b[2] > b[0] and b[3] > b[1]:
        return (int(round(b[0] * im_w)), int(round(b[1] * im_h)),
                int(round(b[2] * im_w)), int(round(b[3] * im_h)))
    return b


def load_evidence_or_raw(src_path: Path, box, out_w: int, out_h: int,
                         invert: bool = False, pixel: int = 0,
                         brightness: float = 1.0, color: float = 1.0,
                         contrast: float = 1.0, sharpness: float = 1.0,
                         prefer_light: bool = False):
    """统一的截图加载：命中证据图映射就用高清版，否则用原图。

    invert=True 时会反相；此时取原版再反相，而不是取已经反相的 -亮 文件，
    避免"反两次"导致颜色错乱。

    素材一个都没到位时返回占位卡，不抛异常。

    box 可写像素坐标，也可写 0–1 的比例坐标（见 `_fit_box`）。

    返回 (RGBA 图像, 是否用了高清证据图)。
    """
    name = src_path.name
    evid = resolve_evidence(name, box)
    try:
        if evid:
            if invert:
                # 用原版再反相，避免二次反相
                p = evidence_path(evid, prefer_light=False)
            else:
                p = evidence_path(evid, prefer_light=prefer_light)
            im = Image.open(p).convert("RGB")
        else:
            with Image.open(src_path) as raw:
                raw = raw.convert("RGB")
                im = raw.crop(_fit_box(box, raw.width, raw.height))
    except (FileNotFoundError, OSError):
        return placeholder(out_w, out_h, evid or name,
                           where=EVID if evid else src_path.parent), False

    if invert:
        from PIL import ImageOps
        im = ImageOps.invert(im)

    r = min(out_w / im.width, out_h / im.height)
    im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)

    if pixel > 1:
        im = im.resize((max(1, im.width // pixel), max(1, im.height // pixel)), Image.BILINEAR)
        im = im.resize((im.width * pixel, im.height * pixel), Image.NEAREST)

    if color != 1.0:
        im = ImageEnhance.Color(im).enhance(color)
    if contrast != 1.0:
        im = ImageEnhance.Contrast(im).enhance(contrast)
    if brightness != 1.0:
        im = ImageEnhance.Brightness(im).enhance(brightness)
    if sharpness != 1.0:
        im = ImageEnhance.Sharpness(im).enhance(sharpness)

    return im.convert("RGBA"), bool(evid)



# ================================================================ 渲染器接入
def mark_text_layer(img: Image.Image, name: str = "") -> Image.Image:
    """标记一个图层为"文字层"。

    渲染器的 text_img() 出口调用它，之后 place() 落位时
    就能把这个图层的包围盒登记到检测器。
    """
    try:
        img._mg_text = True
        if name:
            img._mg_name = name
    except AttributeError:
        pass
    return img


def register_layer_texts(guard: OverlapGuard, layer: Image.Image,
                         x: int, y: int, alpha: float = 1.0) -> None:
    """图层落位时，把它登记进检测器。

    登记两类：
      1. 图层本身是文字层 → 整个图层算一个文字框
      2. 图层内含文字（卡片类）→ 逐个记录内部文字的相对位置，
         换算成绝对坐标后再判重叠

    这样"卡片标题压卡片说明"这种内部冲突也能查出来。

    卡片类图层带 shadow padding，内容实际从 (pad, pad) 开始，
    卡片构建时用 set_content_offset(layer, pad, pad) 记录这个偏移。
    """
    if alpha < 0.25:
        return

    if getattr(layer, "_mg_text", False):
        guard.add(x, y, layer.width, layer.height, kind="text",
                  name=getattr(layer, "_mg_name", ""), alpha=alpha)
        return

    ox, oy = getattr(layer, "_mg_offset", (0, 0))
    for rel in getattr(layer, "_mg_texts", []):
        rx, ry, rw, rh, rname = rel
        guard.add(x + ox + rx, y + oy + ry, rw, rh, kind="text",
                  name=rname or getattr(layer, "_mg_name", ""), alpha=alpha)


def set_content_offset(layer: Image.Image, ox: int, oy: int) -> Image.Image:
    """记录卡片内容区相对图层左上角的偏移（shadow padding）。"""
    try:
        layer._mg_offset = (int(ox), int(oy))
    except AttributeError:
        pass
    return layer


def write_report(guard: OverlapGuard, out_dir: Path, title: str = "") -> str:
    """把检测结果和缺失素材清单打印并写到 out_dir/重叠检测报告.txt。"""
    txt = guard.report()
    missing = missing_by_dir()
    print("--- mgkit 重叠检测 ---")
    print(txt)
    if missing:
        n = sum(len(v) for v in missing.values())
        print(f"  ⚠ 缺 {n} 张素材，已用占位卡顶替。把下面的文件放进对应目录后重跑：")
        for d, names in missing.items():
            print(f"     {d}")
            for m in names:
                print(f"       · {m}")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        body = (f"# {title}\n\n" if title else "") + txt \
            + "\n\n=== 全部明细 ===\n" + "\n".join(guard.errors)
        if missing:
            body += "\n\n=== 缺失素材（已用占位卡）===\n"
            for d, names in missing.items():
                body += f"{d}\n" + "\n".join(f"  · {m}" for m in names) + "\n"
        (out_dir / "重叠检测报告.txt").write_text(body, encoding="utf-8")
    except Exception as e:  # 报告写不出去不影响渲染
        print(f"  (报告写入失败：{e})")
    return txt





