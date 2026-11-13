#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 2x 高清官网截图里裁出"能看清字"的证据图。

原 1x 截图裁切后放进 1080 宽视频要缩到 0.65x，是二次降采样，所以糊。
这里从 2x（2792 宽）截图裁，并把裁切框收到"刚好装下证据"的宽度，
放进视频是 0.7–1.3x，字口清晰。

每张证据图给两个版本：
  * 原版（官网深色/浅色原样）
  * 亮版（反相 + 青调，适配亮色系的 MG）

输出：素材-证据图/

下面的 SPECS 是示例选题的登记表，**换选题就要改这张表**：源图名、裁切框、
高亮框。裁切框可以写像素坐标，也可以写 0–1 的比例；推荐用比例，
因为每个人截的图分辨率不一样，比例才能怎么截都裁到同一个位置。

路径默认取当前选题根目录（在该目录下运行），可用环境变量覆盖：
    MG_ROOT / MG_SHOTS_HD_DIR / MG_EVID_DIR
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps, ImageStat

ROOT = Path(os.environ.get("MG_ROOT") or Path.cwd())
HD = Path(os.environ.get("MG_SHOTS_HD_DIR") or (ROOT / "素材-官网截图-HD"))
OUT = Path(os.environ.get("MG_EVID_DIR") or (ROOT / "素材-证据图"))
OUT.mkdir(parents=True, exist_ok=True)

RED = (200, 44, 38)
ORANGE = (222, 108, 30)
GREEN = (16, 140, 88)
BLUE = (36, 100, 210)

HERO = "01-官网首页-新版公告.jpg"        # 首页首屏
TRIAL = "02-试用入口与套餐对比.jpg"      # 入口 / 套餐页
QUICK = "03-快速开始-工作区与首次同步.jpg"  # 上手文档页
PLANS = "07-版本能力-离线同步说明.jpg"      # 版本 / 能力说明页

# (输出名, 源文件, 裁切框, 高亮框(相对裁切图 x0,y0,x1,y1)，高亮色, 是否出亮版)
# 下面全是示例值：拿到自己的截图后逐行改裁切框，直到裁出来的图只剩证据本身。
SPECS = [
    # ---- 能力表：每项能力一张，只装下那一行 ----
    ("E01-能力表-离线同步", PLANS, (0.05, 0.50, 0.95, 0.58), None, None, True),
    ("E03-能力表-多人协作", PLANS, (0.05, 0.34, 0.95, 0.42), None, None, True),
    ("E04-能力表-附件版本", PLANS, (0.05, 0.42, 0.95, 0.50), None, None, True),
    ("E05-版本规则说明", PLANS, (0.05, 0.16, 0.95, 0.30), None, None, True),
    # ---- 快速开始：拆成三个步骤图 ----
    ("E06-快速开始-同步地址", QUICK, (0.05, 0.30, 0.95, 0.42), None, None, True),
    ("E07-快速开始-命令示例", QUICK, (0.05, 0.42, 0.95, 0.58), None, None, True),
    ("E08-快速开始-创建工作区", QUICK, (0.05, 0.18, 0.95, 0.30), None, None, True),
    # ---- 入口与限制：首屏 / 套餐卡片 ----
    ("E09-试用额度与限制", TRIAL, (0.05, 0.30, 0.35, 0.50), None, None, True),
    ("E10-套餐对照", TRIAL, (0.35, 0.30, 0.65, 0.50), None, None, True),
    ("E11-网页端入口", TRIAL, (0.65, 0.30, 0.95, 0.50), None, None, True),
    # ---- 首页公告（给只想要一张图的风格用）----
    ("E12-首页新版公告", HERO, (0.0, 0.20, 1.0, 0.36), None, None, True),
]


def crop_box(im, box):
    """四个数全在 0–1 时按比例解释，否则当像素坐标。与 mgkit 里的写法一致。"""
    b = tuple(box)
    if all(0.0 <= v <= 1.0 for v in b) and b[2] > b[0] and b[3] > b[1]:
        return (int(round(b[0] * im.width)), int(round(b[1] * im.height)),
                int(round(b[2] * im.width)), int(round(b[3] * im.height)))
    return b


def light_version(im):
    """把证据图转成"适配亮色系 MG"的版本。

    官网截图有两种底色：
      * 定价页是白底表格 → 亮色 MG 下应该保持浅底（但要压对比、加暖调）
      * campaign 卡片是深色   → 亮色 MG 下应该翻成浅底

    所以要先判断原图是暗底还是亮底，再决定是否反相。
    反相后还要把灰底压成暖白，否则和奶油色画面割裂。
    """
    stat = ImageStat.Stat(im.convert("L"))
    mean = stat.mean[0]
    if mean < 128:
        # 暗底 → 反相成浅底，再把中间调压向暖白
        inv = ImageOps.invert(im).convert("RGB")
        r, g, b = inv.split()
        # 提亮高光、压低中间调，让灰底变暖白
        r = r.point(lambda v: min(255, int(v * 0.88 + 40)))
        g = g.point(lambda v: min(255, int(v * 0.83 + 36)))
        b = b.point(lambda v: min(255, int(v * 0.76 + 30)))
        out = Image.merge("RGB", (r, g, b))
        return ImageEnhance.Brightness(out).enhance(1.0)
    # 亮底 → 保持浅底，略微压对比 + 暖调，避免和米白底融掉
    r, g, b = im.convert("RGB").split()
    warm = Image.merge("RGB", (
        r.point(lambda v: int(v * 0.99)),
        g.point(lambda v: int(v * 0.97)),
        b.point(lambda v: int(v * 0.93)),
    ))
    return ImageEnhance.Brightness(warm).enhance(0.985)




def main():
    missing = [s for _, s, *_ in SPECS if not (HD / s).exists()]
    if missing:
        print(f"✗ 素材-官网截图-HD/ 里缺这些源图（先放图再跑本工具）：")
        for m in sorted(set(missing)):
            print(f"   · {m}")
        raise SystemExit(1)

    cache = {}
    for name, src, box, hl, hcolor, want_light in SPECS:
        if src not in cache:
            cache[src] = Image.open(HD / src).convert("RGB")
        base = cache[src].crop(crop_box(cache[src], box))

        variants = [("原版", base)]
        if want_light:
            variants.append(("亮版", light_version(base)))

        for tag, im in variants:
            im = im.convert("RGB")
            im = ImageEnhance.Contrast(im).enhance(1.08)
            im = ImageEnhance.Sharpness(im).enhance(1.4)
            im = ImageEnhance.Brightness(im).enhance(0.99)

            if hl:
                x0, y0, x1, y1 = hl
                # 必须在 RGBA 图上做 alpha 叠加，直接往 RGB 图上 fill 传 alpha 会被忽略
                ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                od.rounded_rectangle((x0, y0, x1, y1), 10, fill=hcolor + (30,))
                od.rounded_rectangle((x0, y0, x1, y1), 10,
                                     outline=hcolor + (255,), width=5)
                im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")

            suffix = "" if tag == "原版" else "-亮"
            p = OUT / f"{name}{suffix}.png"
            im.save(p)
            w, h = im.size
            r = 912 / w
            flag = "放大" if r >= 1.0 else ("等大" if r > 0.85 else f"缩小{r:.2f}")
            print(f"{p.name:<38} {w:>5}x{h:<4} →{flag:<9} {r:.2f}x")


if __name__ == "__main__":
    main()
