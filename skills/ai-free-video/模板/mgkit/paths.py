#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路径解析：让渲染器脚本能从任何位置运行。

优先级：
  1. 环境变量 MG_EVID_DIR / MG_SHOTS_DIR / MG_MGKIT_DIR
  2. 从当前脚本位置向上找 Skill 根目录（找到 mgkit/ 就算）
  3. 回退到 MG_ROOT 指定的选题根目录（未设置则不猜路径，靠前两级）

用法：
    import sys; sys.path.insert(0, "<Skill>/模板/mgkit")
    from paths import EVID_DIR, SHOTS_DIR, MGKIT_DIR

Skill 目录被移动/改名后无需改代码：所有默认值都从本文件位置或环境变量推导。
"""
from __future__ import annotations

import os
from pathlib import Path


def _env_path(name: str):
    """环境变量 → Path；未设置返回 None。"""
    val = os.environ.get(name)
    return Path(val).expanduser() if val else None


# 最后一次兜底用的选题根目录，需由 MG_ROOT 显式指定
DEFAULT_ROOT = _env_path("MG_ROOT")


def _find_root() -> Path:
    """从本文件位置向上找含 mgkit/ 的目录，找不到就用 MG_ROOT 指定的根。"""
    env = _env_path("MG_ROOT")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "mgkit" / "mgkit.py").exists():
            return p
        if (p / "模板" / "mgkit" / "mgkit.py").exists():
            return p.parent
    return DEFAULT_ROOT if DEFAULT_ROOT else Path.cwd()


ROOT = _find_root()
# <Skill>/模板/mgkit/paths.py → <Skill>
SKILL_ROOT = Path(__file__).resolve().parents[2]

MGKIT_DIR = Path(os.environ.get("MG_MGKIT_DIR") or (ROOT / "mgkit"))
EVID_DIR = Path(os.environ.get("MG_EVID_DIR") or (ROOT / "素材-证据图"))
SHOTS_DIR = Path(os.environ.get("MG_SHOTS_DIR") or (ROOT / "素材-官网截图"))
SHOTS_HD_DIR = Path(os.environ.get("MG_SHOTS_HD_DIR") or (ROOT / "素材-官网截图-HD"))


def _resolve_materials(root: Path) -> None:
    """在候选根目录里找素材目录，按「选题自包含 → 上级 → Skill 模板」顺序。

    选题目录结构：<选题>/mgkit/ + <选题>/素材-证据图/ + <选题>/素材-官网截图-HD/
    """
    global EVID_DIR, SHOTS_DIR, SHOTS_HD_DIR

    cands = [root, root.parent, DEFAULT_ROOT, SKILL_ROOT / "模板"]
    for c in cands:
        if not c or not c.exists():
            continue
        # 素材-证据图
        if not EVID_DIR.exists():
            for sub in ("素材-证据图", "素材/证据图"):
                if (c / sub).exists():
                    EVID_DIR = c / sub
                    break
        # 官网截图
        if not SHOTS_DIR.exists():
            for sub in ("素材-官网截图", "素材/官网截图", "素材-官网截图-HD"):
                if (c / sub).exists():
                    SHOTS_DIR = c / sub
                    break
        if not SHOTS_HD_DIR.exists():
            for sub in ("素材-官网截图-HD", "素材/官网截图-HD"):
                if (c / sub).exists():
                    SHOTS_HD_DIR = c / sub
                    break


_resolve_materials(ROOT)


# 素材目录不存在时，回退到 Skill 自带的模板素材
if not EVID_DIR.exists():
    alt = SKILL_ROOT / "模板" / "素材-证据图"
    if alt.exists():
        EVID_DIR = alt
if not SHOTS_DIR.exists():
    alt = SKILL_ROOT / "模板" / "素材-官网截图"
    if alt.exists():
        SHOTS_DIR = alt
