#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把老选题工程升级到「支持选画幅」。

**为什么需要这个工具**

画幅能力（`mgkit/canvas.py`）是后加的。新建选题脚本会把 Skill 里的 mgkit
复制进工程，所以**老工程里躺着一份过期的 mgkit 副本**，渲染器也没接 CANVAS。
这种工程改 canvas.json 不会有任何效果——尺寸照样是 1080×1920。

**用法**

    cd <选题目录>            # 就是那个含 mgkit/ 和 MG样片-xxx/ 的目录
    python3 "<Skill>/模板/工具-升级画幅.py"           # 只升级，画幅保持默认
    python3 "<Skill>/模板/工具-升级画幅.py" 16:9      # 升级 + 顺便把画幅定成 16:9
    python3 "<Skill>/模板/工具-升级画幅.py" 16:9 "主标题" "副标题"   # 横版右侧标题栏

**做三件事，都可以重复执行**

1. 用 Skill 里的最新 mgkit 覆盖工程的 `mgkit/`（canvas.py 就是这么进去的）
2. 给每个 `build_mg*.py` 接上画幅：`render_frame` 出口、ffmpeg 的 `-s`、检查图缩略图
3. 写 `canvas.json`；命令行给了比例就写，没给就保留现有的

升级完在渲染工程里跑一次 `--preview`，看帧尺寸对不对就算验过了。
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MGKIT_SRC = HERE.parent / "mgkit"   # mgkit 在 Skill 根（模板/ 的上一级）

sys.path.insert(0, str(MGKIT_SRC))
from patch_renderers import patch_canvas  # noqa: E402

VALID = ("9:16", "2:3", "4:5", "1:1", "16:9", "4:3")


def add_canvas_import(src: str) -> tuple[str, bool]:
    """把 CANVAS 加进 `from mgkit import (...)`。返回 (新源码, 是否改动)。"""
    if re.search(r"from mgkit import[^)]*\bCANVAS\b", src, re.S):
        return src, False
    m = re.search(r"from mgkit import \(([^)]*)\)", src, re.S)
    if not m:
        return src, False
    inner = m.group(1).rstrip()
    # 最后一行带行尾注释时，另起一行加，不然 CANVAS 会被注释吃掉
    if "#" in inner.splitlines()[-1]:
        indent = " " * 19
        addition = "\n" + indent + "CANVAS"
    else:
        addition = ", CANVAS"
    return src[:m.end(1)] + addition + src[m.end(1):], True


def find_renderers(root: Path) -> list[Path]:
    """工程里的渲染器：MG样片*/build_mg*.py，也兜底扫根目录下一层。"""
    found = sorted(root.glob("MG样片*/build_mg*.py")) or sorted(root.glob("*/build_mg*.py"))
    return found or sorted(root.glob("build_mg*.py"))


def main() -> int:
    root = Path.cwd()
    args = [a.strip() for a in sys.argv[1:]]
    ratio = (args[0] if args else "").replace("x", ":").replace("X", ":")
    title = args[1] if len(args) > 1 else ""
    subtitle = args[2] if len(args) > 2 else ""
    if ratio and ratio not in VALID:
        print(f"✗ 画幅不认识：{ratio}（可选 {' / '.join(VALID)}）")
        return 1

    if not MGKIT_SRC.exists():
        print(f"✗ 找不到 Skill 的 mgkit 源目录：{MGKIT_SRC}")
        return 1

    print(f"工程根：{root}")

    # 1) 同步 mgkit
    dst = root / "mgkit"
    if dst.exists() or (root / "MG样片").exists() or list(root.glob("MG样片-*")):
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(MGKIT_SRC, dst, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"✓ mgkit 已同步（含 canvas.py）→ {dst}")
    else:
        print(f"✗ 这里不像一个选题工程（没有 mgkit/，也没有 MG样片*/）。\n"
              f"  要新建工程请用 模板/新建选题.sh。")
        return 1

    # 2) 接画幅
    renderers = find_renderers(root)
    if not renderers:
        print("✗ 没找到 build_mg*.py，跳过渲染器接入")
    n_new = n_old = 0
    for p in renderers:
        src = p.read_text(encoding="utf-8")
        if "CANVAS.fit_frame" in src and re.search(r"mgkit import[^)]*\bCANVAS\b", src, re.S):
            n_old += 1
            print(f"  · 已接入画幅  {p.relative_to(root)}")
            continue
        if "from mgkit import" not in src:
            print(f"  ! 没接过 mgkit，先跑：python3 mgkit/patch_renderers.py  "
                  f"（{p.relative_to(root)}）")
            continue
        src, _ = add_canvas_import(src)
        src = patch_canvas(src)
        p.write_text(src, encoding="utf-8")
        n_new += 1
        print(f"  ✓ 已接入画幅  {p.relative_to(root)}")
    print(f"渲染器：新接入 {n_new} 个，原本就有 {n_old} 个，共 {len(renderers)} 个")

    # 3) canvas.json：给了什么就改什么，没给的字段保留原样
    cfg_path = root / "canvas.json"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8")) or {}
        except Exception:
            cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    changed = []
    for k, v in (("ratio", ratio), ("title", title), ("subtitle", subtitle)):
        if v and cfg.get(k) != v:
            cfg[k] = v
            changed.append(f"{k}={v}")
    if not cfg:
        cfg = {"ratio": "9:16"}
        changed.append("ratio=9:16（补建默认）")
    if changed:
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        print("✓ canvas.json 更新：" + "，".join(changed))
    else:
        print(f"· canvas.json 保持不动：{cfg}")

    print("\n验收：")
    for p in renderers:
        print(f"  cd '{p.parent}' && python3 ./{p.name} --preview")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
