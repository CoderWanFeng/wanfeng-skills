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

PRICING = "05-模型定价-文本模型与试用规则.jpg"
QUICK = "03-快速开始-注册Key与首次请求.jpg"
CAMP = "02-免费访问入口与套餐对比.jpg"

# (输出名, 源文件, 裁切框, 高亮框(相对裁切图 x0,y0,x1,y1)，高亮色, 是否出亮版)
SPECS = [
    # ---- 视频 Flash ¥0/秒（核心证据）----
    ("E01-视频Flash-0元每秒", PRICING, (640, 8460, 1810, 8600),
     (1030, 22, 1160, 102), GREEN, True),
    # ---- 普通视频模型对照（仍收费）----
    ("E02-视频普通模型-仍收费", PRICING, (640, 8060, 1810, 8230),
     (1030, 24, 1160, 104), ORANGE, True),
    # ---- 文本 Flash 体验价 ----
    ("E03-文本Flash-体验价全0", PRICING, (640, 5700, 1810, 5960),
     (1030, 122, 1160, 202), GREEN, True),
    # ---- 图片 Flash 体验价 ----
    ("E04-图片Flash-各分辨率全0", PRICING, (640, 5150, 1810, 5400),
     (1030, 122, 1160, 202), GREEN, True),
    # ---- 当前优惠规则说明 ----
    ("E05-当前优惠-规则说明", PRICING, (330, 4300, 2470, 4700), None, None, True),
    # ---- 快速开始：Base URL ----
    ("E06-快速开始-BaseURL", QUICK, (280, 1560, 2520, 2010), None, None, True),
    # ---- 快速开始：curl 示例 ----
    ("E07-快速开始-curl示例", QUICK, (280, 2010, 2520, 2500), None, None, True),
    # ---- 快速开始：创建 API Key ----
    ("E08-快速开始-创建Key", QUICK, (280, 1060, 2520, 1560), None, None, True),
    # ---- campaign：免费访问卡片（免费试用 / TPS / 配额）----
    ("E09-免费访问-额度与限制", CAMP, (150, 780, 830, 1240), None, None, True),
    # ---- campaign：Token 套餐对照 ----
    ("E10-Token套餐-对照", CAMP, (830, 780, 1510, 1240), None, None, True),
    # ---- campaign：Pavo 普通用户入口 ----
    ("E11-Pavo-普通用户入口", CAMP, (1560, 780, 2320, 1240), None, None, True),
]


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
    cache = {}
    for name, src, box, hl, hcolor, want_light in SPECS:
        if src not in cache:
            cache[src] = Image.open(HD / src).convert("RGB")
        base = cache[src].crop(box)

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
