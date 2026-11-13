#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mgkit — MG 短视频渲染共用工具库

解决两件长期踩坑的事：

1. **元素重叠**：靠人眼看关键帧是不可靠的，尤其转场瞬间。
   本库提供 `OverlapGuard`：所有 place() 调用登记包围盒，
   渲染时自动检测"文字层互相压盖"，越界直接报错。

2. **截图质量**：提供 `load_evidence()`，统一从 2x 高清截图
   裁好的证据图里取，并保证放进视频时的缩放比不低于 0.75x。

用法：
    from mgkit import OverlapGuard, load_evidence, EvidenceSpec
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageEnhance

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
    """按基础名找到证据图。

    每张证据图有两个版本：
      * 原版  —— 官网原始配色（深色卡片版 / 浅色表格版）
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
_EVIDENCE_MAP: dict[tuple[str, tuple[int, int, int, int]], str] = {}


def _reg(src: str, box: tuple[int, int, int, int], evid: str) -> None:
    _EVIDENCE_MAP[(src, tuple(box))] = evid


# 首页（免费 API 入口证据）
_reg("01-官网首页-免费API与多模态.jpg", (740, 155, 980, 225), "E09-免费访问-额度与限制")
_reg("01-官网首页-免费API与多模态.jpg", (300, 155, 1000, 260), "E09-免费访问-额度与限制")
_reg("01-官网首页-免费API与多模态.jpg", (300, 155, 1000, 262), "E09-免费访问-额度与限制")
_reg("01-官网首页-免费API与多模态.jpg", (0, 170, 1396, 640), "E09-免费访问-额度与限制")
_reg("01-官网首页-免费API与多模态.jpg", (0, 60, 1396, 1150), "E09-免费访问-额度与限制")

# 快速开始文档
_reg("03-快速开始-注册Key与首次请求.jpg", (0, 150, 1396, 1420), "E06-快速开始-BaseURL")
_reg("03-快速开始-注册Key与首次请求.jpg", (0, 150, 1396, 1400), "E06-快速开始-BaseURL")

# 定价页 · 视频 Flash
_reg("07-模型定价-视频Flash限时免费.jpg", (0, 700, 1396, 820), "E01-视频Flash-0元每秒")
_reg("07-模型定价-视频Flash限时免费.jpg", (0, 700, 1396, 822), "E01-视频Flash-0元每秒")
_reg("07-模型定价-视频Flash限时免费.jpg", (0, 690, 1396, 830), "E01-视频Flash-0元每秒")
_reg("07-模型定价-视频Flash限时免费.jpg", (0, 700, 1396, 830), "E01-视频Flash-0元每秒")


def resolve_evidence(src_name: str, box) -> str | None:
    """旧截图 + 裁切框 → 高清证据图文件名。找不到返回 None。"""
    return _EVIDENCE_MAP.get((src_name, tuple(box)))


def load_evidence_or_raw(src_path: Path, box, out_w: int, out_h: int,
                         invert: bool = False, pixel: int = 0,
                         brightness: float = 1.0, color: float = 1.0,
                         contrast: float = 1.0, sharpness: float = 1.0,
                         prefer_light: bool = False):
    """统一的截图加载：命中证据图映射就用高清版，否则用原图。

    invert=True 时会反相；此时取原版再反相，而不是取已经反相的 -亮 文件，
    避免"反两次"导致颜色错乱。

    返回 (RGBA 图像, 是否用了高清证据图)。
    """
    name = src_path.name
    evid = resolve_evidence(name, box)
    if evid:
        if invert:
            # 用原版再反相，避免二次反相
            p = evidence_path(evid, prefer_light=False)
        else:
            p = evidence_path(evid, prefer_light=prefer_light)
        im = Image.open(p).convert("RGB")
    else:
        im = Image.open(src_path).convert("RGB").crop(box)

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
    """把检测结果打印并写到 out_dir/重叠检测报告.txt。"""
    txt = guard.report()
    print("--- mgkit 重叠检测 ---")
    print(txt)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "重叠检测报告.txt").write_text(
            (f"# {title}\n\n" if title else "") + txt
            + "\n\n=== 全部明细 ===\n" + "\n".join(guard.errors),
            encoding="utf-8")
    except Exception as e:  # 报告写不出去不影响渲染
        print(f"  (报告写入失败：{e})")
    return txt





