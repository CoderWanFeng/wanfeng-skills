#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 MG 渲染器打"重叠检测 + 高清证据图"补丁。

做四件事（源码级文本替换，保证目标文件行为一致）：

1. 插入 import + 全局 GUARD
2. `text_img(...)` 出口给图层打文字标记（带文字内容做名字）
3. `place(...)` 出口把图层里的文字包围盒登记到 GUARD
4. `render_frame(t)` 出口跑 GUARD.check()，每帧开头 GUARD.reset()

用法：
    cd <选题目录> && python3 "<Skill>/模板/mgkit/patch_renderers.py"
    # 选题根目录也可用 MG_ROOT 指定，默认取当前工作目录
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("MG_ROOT") or Path.cwd())

# 只列"出厂时还没接 mgkit"的旧风格。G 简笔画 / H 工笔画 从第一行代码就带着
# GUARD，不需要也不能再打补丁（MARK 已在源码里，patch 会直接跳过）。
TARGETS = [
    "MG样片/build_mg.py",
    "MG样片-亮色动效/build_mg_bright.py",
    "MG样片-复古拼贴/build_mg_retro.py",
    "MG样片-故障艺术/build_mg_glitch.py",
    "MG样片-像素游戏/build_mg_pixel.py",
    "MG样片-暖色治愈/build_mg_warm.py",
]

MARK = "mgkit: overlap guard"

IMPORT_BLOCK = '''

# --- mgkit: overlap guard ---
import sys as _mg_sys
from pathlib import Path as _mg_Path
_mg_sys.path.insert(0, str(_mg_Path(__file__).resolve().parent.parent / "mgkit"))
from mgkit import (OverlapGuard, mark_text_layer, register_layer_texts,  # noqa: E402
                   set_content_offset)

GUARD = OverlapGuard({W}, {H}, text_thresh=0.015,
                     safe_top={SAFE_TOP}, safe_bottom={SAFE_BOTTOM},
                     safe_left={SAFE_LEFT}, safe_right={SAFE_RIGHT})
'''


def patch(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    if MARK in src:
        print(f"  · 已打补丁 {path.name}")
        return False

    m = re.search(r"^FPS = (\d+)", src, re.M)
    if not m:
        print(f"  ✗ 找不到 FPS 定义 {path.name}")
        return False

    mw = re.search(r"^W, H = (\d+), (\d+)", src, re.M)
    W, H = (mw.group(1), mw.group(2)) if mw else ("1080", "1920")

    sl = re.search(r"^SAFE_L = (\d+)", src, re.M)
    sr = re.search(r"^SAFE_R = W - (\d+)", src, re.M)
    st = re.search(r"^SAFE_T = (\d+)", src, re.M)
    sb = re.search(r"^SAFE_B = (\d+)", src, re.M)
    safe_left = sl.group(1) if sl else "0"
    safe_right = sr.group(1) if sr else "0"
    safe_top = st.group(1) if st else "0"
    safe_bottom = f"{H}-{sb.group(1)}" if sb else "0"

    imp = IMPORT_BLOCK.format(W=W, H=H, SAFE_TOP=safe_top, SAFE_BOTTOM=safe_bottom,
                              SAFE_LEFT=safe_left, SAFE_RIGHT=safe_right)
    src = src[:m.end()] + imp + src[m.end():]

    # 2) text_img 出口打标记
    def patch_text_img(s: str) -> str:
        mm = re.search(r"def text_img\(", s)
        if not mm:
            return s
        rest = s[mm.end():]
        rm = re.search(r"\n(    return im)\n", rest)
        if not rm:
            return s
        pos = mm.end() + rm.start(1)
        return (s[:pos]
                + "    return mark_text_layer(im, s.replace(chr(10), ' / '))\n"
                + s[pos + len("    return im\n"):])

    src = patch_text_img(src)

    # 3) place() 出口登记
    def patch_place(s: str) -> str:
        mm = re.search(r"def place\(", s)
        if not mm:
            return s
        rest = s[mm.end():]
        rm = re.search(r"\n(    base\.alpha_composite\(layer, \(xx, yy\)\))\n", rest)
        if not rm:
            # 像素版 place 用的是 base.alpha_composite(layer, (xx, yy))
            rm = re.search(r"\n(    base\.alpha_composite\(layer, \(xx, yy\)\))\n", rest)
        if not rm:
            return s
        pos = mm.end() + rm.start(1)
        return (s[:pos]
                + "    register_layer_texts(GUARD, layer, x, y, a)\n"
                + s[pos + len("    base.alpha_composite(layer, (xx, yy))\n"):])

    src = patch_place(src)

    # 4) render_frame 出口加检测 + 开头 reset
    def patch_render(s: str) -> str:
        mm = re.search(r"def render_frame\(t\):", s)
        if not mm:
            return s
        # 开头插入 reset
        rest = s[mm.end():]
        rm = re.search(r"\n(    return base\.convert\(\"RGB\"\))\n", rest)
        if not rm:
            return s
        pos = mm.end() + rm.start(1)
        gc = ("    # --- mgkit: overlap check ---\n"
              "    GUARD.check(f\"t={t:.2f}\")\n"
              "    # --- end mgkit ---\n")
        s = s[:pos] + gc + s[pos:]
        # 在函数体第一行后插 reset
        mm2 = re.search(r"(def render_frame\(t\):\n)", s)
        s = s[:mm2.end()] + "    GUARD.reset()\n" + s[mm2.end():]
        return s

    src = patch_render(src)

    path.write_text(src, encoding="utf-8")
    print(f"  ✓ 已打补丁 {path.name}")
    return True


def main():
    print("打补丁：")
    n = 0
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            print(f"  ✗ 不存在 {rel}")
            continue
        if patch(p):
            n += 1
    print(f"完成，新增补丁 {n} 个")


if __name__ == "__main__":
    main()
