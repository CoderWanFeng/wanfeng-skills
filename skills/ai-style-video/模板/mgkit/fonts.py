#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fonts — 跨平台中文字体解析

渲染器不写死字体路径。角色分两档：

系统档（每个平台都有，风格之间靠它区分）：

    sans_bold      黑体粗（标题、强调）
    sans_regular   黑体常规（正文、小字）
    serif_bold     宋体粗（复古、国风标题）
    serif_regular  宋体常规

品牌档（可选，没装就自动退回对应的系统档）：

    brand_bold     品牌黑体粗，如腾讯 Sans W7
    brand_regular  品牌黑体常规，如腾讯 Sans W3

为什么要分两档：品牌字体是"某个风格的设计选择"，不是通用需求。
如果让所有黑体角色都优先去找品牌字体，装了腾讯 Sans 的机器会把
本来该用系统黑体的风格悄悄换掉，字形宽度一变，版式就得重排。

解析顺序（命中即停）：

1. 环境变量      `MG_FONT_SANS_BOLD=/path/to.ttf:2`（冒号后的 index 可省）
2. 系统字体      macOS / Windows / Linux 常见候选逐个探测
3. 项目字体目录   <选题>/fonts、<Skill>/模板/fonts、用户字体目录，按文件名匹配
4. 品牌档还没命中  退回对应的系统档
5. 都没有        抛错并告诉用户该设哪个环境变量

`.ttc` 是字体集合，必须带 index 才能选到具体字面；不同系统 index 不同，
所以下面每个候选都自带 index。

用法：
    from fonts import load_font
    f = load_font("sans_bold", 96)

自查：
    python3 fonts.py        # 打印四个角色各命中了哪个字体
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

ROLES = ("sans_bold", "sans_regular", "serif_bold", "serif_regular",
         "brand_bold", "brand_regular")

# 环境变量名（大写角色名加前缀）
ENV_KEY = {r: "MG_FONT_" + r.upper() for r in ROLES}

# 品牌档没装对应字体时退回哪里
BRAND_FALLBACK = {"brand_bold": "sans_bold", "brand_regular": "sans_regular"}

# 用户可能自己下载的同类字体，按文件名在这些目录里找
USER_FONT_DIRS = [
    Path.home() / "Library/Fonts",
    Path.home() / ".local/share/fonts",
    Path("/usr/local/share/fonts"),
    Path("/Library/Fonts"),
    Path(os.environ.get("LOCALAPPDATA", "") or "/nonexistent") / "Microsoft/Windows/Fonts",
]
# 相对本文件与选题根目录的项目字体目录
PROJECT_FONT_DIRS = [
    Path(__file__).resolve().parent / "fonts",
    Path.cwd() / "fonts",
]

# 品牌档按文件名匹配的关键字（用户自己放的字体，谁的都行）
BRAND_HINTS = {
    "brand_bold": ("tencentsans-w7", "tencentsans-bold"),
    "brand_regular": ("tencentsans-w3", "tencentsans-regular"),
    # 系统档在候选全落空时才用这些关键字兜底找
    "sans_bold": ("pingfangsc-semibold", "sourcehansanssc-bold", "notosanscjksc-bold"),
    "sans_regular": ("pingfangsc-regular", "sourcehansanssc-regular", "notosanscjksc-regular"),
    "serif_bold": ("sourcehanserifsc-bold", "notoserifcjksc-bold", "songti"),
    "serif_regular": ("sourcehanserifsc-regular", "notoserifcjksc-regular", "songti"),
}

# 系统候选：(路径, ttc index)
if sys.platform == "darwin":
    _HIRAGINO = "/System/Library/Fonts/Hiragino Sans GB.ttc"
    _SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"
    _PINGFANG = "/System/Library/Fonts/PingFang.ttc"
    SYSTEM_CANDIDATES = {
        "sans_bold": [(_HIRAGINO, 2), (_PINGFANG, 6), ("/System/Library/Fonts/STHeiti Medium.ttc", 0)],
        "sans_regular": [(_HIRAGINO, 0), (_PINGFANG, 2), ("/System/Library/Fonts/STHeiti Light.ttc", 0)],
        "serif_bold": [(_SONGTI, 1), ("/System/Library/Fonts/Supplemental/STSong.ttf", 0)],
        "serif_regular": [(_SONGTI, 6), ("/System/Library/Fonts/Supplemental/STSong.ttf", 0)],
    }
elif os.name == "nt":
    _WIN = "C:/Windows/Fonts"
    SYSTEM_CANDIDATES = {
        "sans_bold": [(f"{_WIN}/msyhbd.ttc", 0), (f"{_WIN}/simhei.ttf", 0), (f"{_WIN}/Dengb.ttf", 0)],
        "sans_regular": [(f"{_WIN}/msyh.ttc", 0), (f"{_WIN}/simhei.ttf", 0), (f"{_WIN}/Deng.ttf", 0)],
        "serif_bold": [(f"{_WIN}/simsun.ttc", 0), (f"{_WIN}/SIMYOU.ttf", 0)],
        "serif_regular": [(f"{_WIN}/simsun.ttc", 0), (f"{_WIN}/SIMYOU.ttf", 0)],
    }
else:
    _NOTO = "/usr/share/fonts/opentype/noto"
    _WQY = "/usr/share/fonts/truetype/wqy"
    SYSTEM_CANDIDATES = {
        "sans_bold": [(f"{_NOTO}/NotoSansCJK-Bold.ttc", 2),
                      ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
                      (f"{_WQY}/wqy-zenhei.ttc", 0)],
        "sans_regular": [(f"{_NOTO}/NotoSansCJK-Regular.ttc", 2),
                         (f"{_WQY}/wqy-microhei.ttc", 0),
                         (f"{_WQY}/wqy-zenhei.ttc", 0)],
        "serif_bold": [(f"{_NOTO}/NotoSerifCJK-Bold.ttc", 2),
                       ("/usr/share/fonts/truetype/arphic/uming.ttc", 0)],
        "serif_regular": [(f"{_NOTO}/NotoSerifCJK-Regular.ttc", 2),
                          ("/usr/share/fonts/truetype/arphic/uming.ttc", 0)],
    }


def _parse_spec(spec: str) -> tuple[Path, int]:
    """`/path/to.ttf:2` → (Path, 2)。index 缺省为 0。"""
    p = spec.strip()
    # Windows 盘符也有冒号，只在末段是纯数字时当 index
    if ":" in p and p.rsplit(":", 1)[1].isdigit() and len(p.split(":")[0]) > 1:
        path, idx = p.rsplit(":", 1)
        return Path(path), int(idx)
    return Path(p), 0


def _scan_user_fonts(hints: tuple[str, ...]) -> tuple[Path, int] | None:
    """在项目目录 / 用户字体目录里按文件名找同类字体。"""
    for d in [*PROJECT_FONT_DIRS, *USER_FONT_DIRS]:
        if not d.is_dir():
            continue
        try:
            files = sorted(d.rglob("*"))
        except OSError:
            continue
        by_name = {f.name.lower(): f for f in files if f.suffix.lower() in {".ttf", ".otf", ".ttc"}}
        for hint in hints:
            for name, f in by_name.items():
                if hint in name:
                    return f, 0
    return None


@lru_cache(maxsize=None)
def resolve(role: str) -> tuple[Path, int]:
    """角色名 → (字体文件, ttc index)。找不到直接抛错，不静默降级成方块字。"""
    if role not in ROLES:
        raise ValueError(f"未知字体角色：{role}（可选 {'/'.join(ROLES)}）")

    env = os.environ.get(ENV_KEY[role])
    if env:
        path, idx = _parse_spec(env)
        if path.exists():
            return path, idx
        raise FileNotFoundError(f"{ENV_KEY[role]} 指向的字体不存在：{path}")

    # 品牌档先找用户字体目录——它本来就是指"用户自己下的那个字体"
    if role in BRAND_FALLBACK:
        hit = _scan_user_fonts(BRAND_HINTS[role])
        if hit:
            return hit
        return resolve(BRAND_FALLBACK[role])

    # 系统档先用系统候选，全落空再按关键字兜底找
    for cand, idx in SYSTEM_CANDIDATES[role]:
        p = Path(cand)
        if p.exists():
            return p, idx

    hit = _scan_user_fonts(BRAND_HINTS[role])
    if hit:
        return hit

    raise FileNotFoundError(
        f"找不到中文字体（角色 {role}）。已试过：\n  "
        + "\n  ".join(c for c, _ in SYSTEM_CANDIDATES[role])
        + f"\n请装一个中文字体，或用环境变量指定：\n  export {ENV_KEY[role]}=/路径/字体.ttf[:ttc序号]"
    )


@lru_cache(maxsize=512)
def load_font(role: str, size: int):
    """按角色取字体对象，带缓存（渲染器每帧都会调）。"""
    from PIL import ImageFont
    path, idx = resolve(role)
    return ImageFont.truetype(str(path), int(size), index=idx)


def describe() -> str:
    """打印当前四个角色各命中了哪个字体，排查用。"""
    lines = []
    for r in ROLES:
        try:
            p, i = resolve(r)
            lines.append(f"  {r:<14} {p.name}  index={i}")
        except FileNotFoundError as e:
            lines.append(f"  {r:<14} ✗ {e}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("当前字体解析结果：")
    print(describe())
