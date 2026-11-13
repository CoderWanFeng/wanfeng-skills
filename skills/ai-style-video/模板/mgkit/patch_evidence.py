#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把旧渲染器的截图加载切到 2x 高清证据图。

各版本的 load_shot 签名和处理参数不同，这里按版本定制替换成
统一调用 mgkit.load_evidence_or_raw()，命中映射表就用高清证据图。

G 简笔画 / H 工笔画不在表里：它们没有 load_shot，出厂就直接调
mgkit.evidence_path() 拿证据图，再跑这个脚本反而会把它们报成
"找不到 load_shot"。

用法：
    cd <选题目录> && python3 "<Skill>/模板/mgkit/patch_evidence.py"
    # 选题根目录也可用 MG_ROOT 指定，默认取当前工作目录
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("MG_ROOT") or Path.cwd())

# 每个版本的 load_shot 替换体
REPLACEMENTS = {
    # A 深色科技：降亮度降饱和
    "MG样片/build_mg.py": '''@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 brightness=0.88, color=0.92)
    return im
''',
    # B 亮色杂志
    "MG样片-亮色动效/build_mg_bright.py": '''@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh, brightness=0.97)
    return im
''',
    # C 复古拼贴：褪色做旧
    "MG样片-复古拼贴/build_mg_retro.py": '''@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 color=0.55, contrast=0.88, brightness=0.96)
    return im
''',
    # D 故障艺术：可像素化
    "MG样片-故障艺术/build_mg_glitch.py": '''@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh, pixel=0):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。"""
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 pixel=pixel, color=0.85, brightness=0.92)
    return im
''',
    # E 像素游戏：反相成暗色终端窗
    "MG样片-像素游戏/build_mg_pixel.py": '''@lru_cache(maxsize=64)
def load_shot(name, box, bw, bh):
    """加载官网截图。命中映射表时用 2x 高清证据图，文字清晰 2 倍。

    像素风下官网白底截图会变成刺眼白块，统一反相 + 青调，
    变成暗色 CRT 终端窗，和 8-bit 背景同调。
    """
    im, _ = load_evidence_or_raw(SHOTS / name, box, bw, bh,
                                 invert=True, color=0.90, brightness=0.82)
    return im
''',
}


def patch(rel: str, body: str) -> bool:
    p = ROOT / rel
    if not p.exists():          # 选题只会用到其中一种风格，缺的跳过就行
        print(f"  · 跳过（不存在）{rel}")
        return False
    s = p.read_text(encoding="utf-8")

    # 1) import
    if "load_evidence_or_raw" not in s.split("GUARD = OverlapGuard")[0]:
        s = s.replace(
            "from mgkit import (OverlapGuard, mark_text_layer, register_layer_texts,  # noqa: E402\n"
            "                   set_content_offset, write_report)",
            "from mgkit import (OverlapGuard, mark_text_layer, register_layer_texts,  # noqa: E402\n"
            "                   set_content_offset, write_report, load_evidence_or_raw)")

    # 2) 替换 load_shot 整个函数
    m = re.search(r"(@lru_cache\(maxsize=64\)\n)?def load_shot\(", s)
    if not m:
        print(f"  ✗ 找不到 load_shot: {rel}")
        return False
    start = m.start()
    # 找函数结束：从 def 行往后找下一个顶层 def
    nm = re.search(r"\n(?=def |@lru_cache|# ---)", s[m.end():])
    if not nm:
        print(f"  ✗ 找不到 load_shot 结尾: {rel}")
        return False
    end = m.end() + nm.start() + 1

    s = s[:start] + body + "\n\n" + s[end:]
    p.write_text(s, encoding="utf-8")
    print(f"  ✓ {rel}")
    return True


def main():
    print("切换高清证据图：")
    n = 0
    for rel, body in REPLACEMENTS.items():
        if patch(rel, body):
            n += 1
    print(f"完成，改动 {n} 个")


if __name__ == "__main__":
    main()
