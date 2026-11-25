# -*- coding: utf-8 -*-
"""Step I · 小绿书贴图模板（xiaolvshu.md 配套，3-10「AI模特换装」期实证）。

用法：整个文件复制到 <选题>/mograph-task/src/cover_xiaolvshu.py，只改「每期必改」CONFIG 区。
每期必改：
  1. OUT_DIR / 标题两行文案（从口播抽词）
  2. 金字利益点文案（本期「30 秒学会」）
  3. POLAS 拍立得照片清单（人物图/效果帧路径 + 中心 + 角度）
  4. TAGS 口播原词胶囊
  5. 内页 TITLES 映射（页序号 → 标题文字，title() 必须从本表取文字，禁止页内硬编码——
     本期实证：页序重排后硬编码映射不同步 = 标题错位）
  6. URL 条文字（GitHub / SkillHub 地址，必须先核实再上图）
  7. 浏览器实拍截图（assets/web/，browser_card 保顶裁切）
  8. WorkBuddy 页 iShot 红框坐标（每期界面不同，重新目测 + 读图核对）
依赖：Pillow 12+；polaroid()/paste_with_shadow()/mixed_text() 来自同目录的
cover_v4.py 与 cover.py（渲染主封面的脚本）——复制本模板时把这两个文件一并
带到 <选题>/mograph-task/src/ 即可直接跑；或把这三个函数拷进本文件。
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = f"{TOP}/发布包/小绿书"

W, H = 1080, 1440
BG_TOP = (205, 195, 180)
BG_BOT = (226, 218, 203)
ACCENT = (0, 214, 147)
TEXT = (243, 246, 248)

L1 = [("免费用", "cn", 118), ("AI", "latin", 115)]
L1_FILL, L1_CY, L1_STROKE = (16, 43, 99), 138, 10
L2 = [("AI", "latin", 146), ("模特换装", "cn", 150)]
L2_FILL, L2_CY, L2_STROKE = (160, 19, 21), 316, 12

GOLD = (206, 132, 30)
MODELS = [f"{TOP}/俯拍换装视频/人物/人物-02-杏碎花.png",
          f"{TOP}/俯拍换装视频/后两套/人物-04-薄荷绿碎花.png",
          f"{TOP}/俯拍换装视频/人物/人物-03-雾蓝碎花.png",
          f"{TOP}/俯拍换装视频/人物/人物-01-紫碎花.png"]
POLAS = [  # 右列 4 张，自下而上叠放：img_w / 中心 / 角度
    dict(path=MODELS[0], img_w=240, center=(640, 700), angle=5),
    dict(path=MODELS[1], img_w=240, center=(720, 915), angle=-5),
    dict(path=MODELS[2], img_w=240, center=(650, 1130), angle=5),
    dict(path=MODELS[3], img_w=240, center=(730, 1345), angle=-6),
]
TAGS = ["零门槛", "免费", "国产大模型"]


def build():
    # 背景：竖向渐变 + 淡网格 + 左上绿晕
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        p = y / (H - 1)
        c = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * p) for i in range(3))
        for x in range(W):
            px[x, y] = c
    canvas = im.convert("RGBA")
    gd = ImageDraw.Draw(canvas, "RGBA")
    for x in range(0, W + 1, 90):
        gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 26), width=1)
    for y in range(0, H + 1, 90):
        gd.line([(0, y), (W, y)], fill=(255, 255, 255, 26), width=1)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([-180, -220, 520, 300], fill=ACCENT + (40,))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(110)))

    # 标题（居中，蓝红同款字体打法）
    cover_base.mixed_text(canvas, W / 2, L1_CY, L1, L1_FILL, L1_STROKE)
    cover_base.mixed_text(canvas, W / 2, L2_CY, L2, L2_FILL, L2_STROKE)

    # 「30 秒学会」金色小字（行 2 下方居中）
    d = ImageDraw.Draw(canvas)
    f30 = ImageFont.truetype(v4.F_LATIN, int(30 * 0.95))
    fc = ImageFont.truetype(cover_base.F_BOLD, 30)
    s30, sc = "30", " 秒学会"
    w30 = d.textlength(s30, font=f30)
    wc = d.textlength(sc, font=fc)
    x30 = W / 2 - (w30 + wc) / 2
    for txt, fnt, xx in ((s30, f30, x30), (sc, fc, x30 + w30)):
        bb = fnt.getbbox(txt)
        d.text((xx - 2, 452 - (bb[1] + bb[3]) / 2 - 2), txt, font=fnt, fill=(255, 255, 255, 255))
        d.text((xx, 452 - (bb[1] + bb[3]) / 2), txt, font=fnt, fill=GOLD + (255,))

    # 拍立得照片堆（右侧，自下而上）
    for ph in POLAS:
        card = v4.polaroid(ph["path"], ph["img_w"], ph["angle"])
        v4.paste_with_shadow(canvas, card, ph["center"])

    # 左列三枚口播原词胶囊（放大，占满左侧）
    ty = 620
    for i, tag in enumerate(TAGS):
        y = ty + i * 150
        f = ImageFont.truetype(cover_base.F_BOLD, 60)
        tw = d.textlength(tag, font=f)
        x0 = 70
        if i == 1:
            bgc, fgc = (255, 194, 75, 255), (38, 27, 2, 255)      # 免费 = AMBER 利益点
        else:
            bgc, fgc = (0, 214, 147, 235), (8, 14, 12, 255)       # 零门槛 / 国产大模型 = ACCENT
        d.rounded_rectangle([x0, y, x0 + tw + 108, y + 116], radius=58, fill=bgc)
        d.text((x0 + 54, y + 58), tag, font=f, fill=fgc, anchor="lm")

    # 左下 WorkBuddy 品牌角标（icon + 右侧字标）
    logo = Image.open(LOGO).convert("RGBA").resize((130, 130), Image.LANCZOS)
    lx, ly = 70, 1160
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    a = logo.getchannel("A").point(lambda v: int(v * 0.5))
    tint = Image.new("RGBA", logo.size, (40, 30, 18, 255))
    tint.putalpha(a)
    sh.alpha_composite(tint, (lx + 5, ly + 8))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    canvas.alpha_composite(logo, (lx, ly))
    fw = ImageFont.truetype(v4.F_LATIN, 44)
    d.text((lx + 160, ly + 43), "WorkBuddy", font=fw, fill=(30, 34, 40, 255))

    os.makedirs(OUT_DIR, exist_ok=True)
    canvas.convert("RGB").save(OUT, quality=92)
    print("saved:", OUT)




# ---------------------------------------------------------------- 内页
def tool_pills(canvas, y):
    """「各类 AI 工具都能装」+ 四枚文字胶囊（Claude Code / Trae / Codex / WorkBuddy）。"""
    d = ImageDraw.Draw(canvas)
    fc = ImageFont.truetype(cover_base.F_BOLD, 34)
    label = "各类 AI 工具都能装 →"
    d.text((70, y + 30), label, font=fc, fill=(90, 84, 74, 255), anchor="lm")
    tools = [("Claude Code", 216), ("Trae", 140), ("Codex", 150), ("WorkBuddy", 220)]
    x = 70
    for name, w in tools:
        d.rounded_rectangle([x, y + 62, x + w, y + 142], radius=40,
                            fill=(36, 40, 48, 255), outline=(255, 255, 255, 200), width=2)
        d.text((x + w / 2, y + 102), name, font=font_lat(32), fill=(240, 243, 246, 255),
               anchor="mm")
        x += w + 24


def page_effects():
    """效果图集中展示：左侧五套对比联络表 + 右侧三张姿势拍立得。"""
    cv = bg()
    d = ImageDraw.Draw(cv)
    d.text((80, 118), "1", font=font_lat(140), fill=ACCENT + (255,), anchor="lm")
    cover_base.mixed_text(canvas=cv, cx=580, cy=128,
                          segs=[("先看效果", "cn", 78), (" · 5 套衣服", "cn", 78)],
                          fill=(16, 43, 99), stroke=8)
    cover_base.mixed_text(canvas=cv, cx=540, cy=258,
                          segs=[("同一张脸，多款裙颜色、姿势随便换。", "cn", 48)],
                          fill=RED, stroke=6)
    logo_corner(cv)
    # 左：五套对比联络表（竖长图）
    sheet = Image.open(f"{TOP}/俯拍换装视频/后两套/质检-五套对比联络表.png").convert("RGB")
    sw, sh_ = sheet.size            # 580×1995
    th = 1030
    tw = int(sw * th / sh_)
    sheet = sheet.resize((tw, th), Image.LANCZOS)
    sh = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([76, 372, 76 + tw + 8, 372 + th + 8],
                                         radius=20, fill=(40, 30, 18, 150))
    cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    m = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, tw - 1, th - 1], radius=18, fill=255)
    cv.paste(sheet, (70, 366), m)
    d.rounded_rectangle([66, 362, 76 + tw, 372 + th], radius=20,
                        outline=(255, 255, 255, 235), width=6)
    # 右：三张姿势帧拍立得（斜叠）
    poses = [
        (f"{TOP}/俯拍换装视频/C档片段/质检/t0000.png", (600, 585), -5),
        (f"{TOP}/俯拍换装视频/C档片段/质检/t0300.png", (860, 890), 6),
        (f"{TOP}/俯拍换装视频/C档片段/质检/t0450.png", (640, 1160), -6),
    ]
    for path, center, angle in poses:
        card = v4.polaroid(path, 265, angle)
        v4.paste_with_shadow(cv, card, center)
    return cv


# ---------------------------------------------------------------- 内页
def page_github():
    cv = bg()
    title(cv, "2")
    logo_corner(cv)
    shot = f"{ASSETS}/web/github-wanfeng-ai-model.png"
    box = browser_card(cv, shot, (60, 350, W - 60, 1130))
    # 红框框住左栏的 wanfeng-ai-model 目录项（真实元素：源图 (60,770)-(320,800) 区）
    url_bar(cv, 1142, "github.com/CoderWanFeng/wanfeng-skills")
    tool_pills(cv, 1268)
    return cv


def page_skillhub():
    cv = bg()
    title(cv, "3")
    logo_corner(cv)
    shot = f"{ASSETS}/web/skillhub-wanfeng-ai-model.png"
    browser_card(cv, shot, (60, 350, W - 60, 1130))
    url_bar(cv, 1142, "skillhub.cn/skills/user_bf8c5b73/")
    tool_pills(cv, 1268)
    return cv


def page_workbuddy():
    cv = bg()
    title(cv, "4")
    logo_corner(cv)
    shot = ISHOT
    box = browser_card(cv, shot, (60, 330, 1020, 940))
    # 完整界面上的红框（真实元素位置，映射到卡内）
    x0, y0, x1, y1 = box
    sw, sh_ = 1568, 987
    iw, ih = x1 - x0, y1 - y0

    def mp(r):
        return (x0 + r[0] / sw * iw, y0 + r[1] / sh_ * ih,
                x0 + r[2] / sw * iw, y0 + r[3] / sh_ * ih)

    d = ImageDraw.Draw(cv)
    for r in (ISHOT_RECTS["skill_tab"], ISHOT_RECTS["search"],
              ISHOT_RECTS["hub_tab"], ISHOT_RECTS["card"]):
        rx0, ry0, rx1, ry1 = mp(r)
        d.rounded_rectangle([rx0 - 4, ry0 - 4, rx1 + 4, ry1 + 4], radius=8,
                            outline=(255, 93, 93, 255), width=5)
    # 四个局部放大镜（2×2），取自同一张真实截图
    zw, zh = 440, 185
    zones = [("skill_tab", (75, 958)), ("search", (595, 958)),
             ("hub_tab", (75, 1158)), ("card", (595, 1158))]
    img = Image.open(shot).convert("RGB")
    for key, (zx, zy) in zones:
        r = ISHOT_RECTS[key]
        px = 40
        crop = img.crop((max(0, r[0] - px), max(0, r[1] - px),
                         min(sw, r[2] + px), min(sh_, r[3] + px)))
        crop = crop.resize((zw, zh), Image.LANCZOS)
        sh2 = Image.new("RGBA", cv.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh2).rounded_rectangle([zx + 6, zy + 10, zx + zw + 6, zy + zh + 10],
                                              radius=16, fill=(40, 30, 18, 150))
        cv.alpha_composite(sh2.filter(ImageFilter.GaussianBlur(12)))
        m = Image.new("L", (zw, zh), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, zw - 1, zh - 1], radius=16, fill=255)
        cv.paste(crop, (zx, zy), m)
        d.rounded_rectangle([zx - 3, zy - 3, zx + zw + 2, zy + zh + 2], radius=18,
                            outline=(255, 93, 93, 255), width=4)
    d.text((W / 2, 1408), "WorkBuddy → 专家·技能·连接器 → 技能 → 搜「晚枫模特换装」→ 安装",
           font=font_cn(32), fill=(60, 55, 48, 255), anchor="mm")
    return cv


OUTS = [
    (page_effects, f"{OUT_DIR}/内页-1-先看效果.jpg"),
    (page_github, f"{OUT_DIR}/内页-2-GitHub开源地址.jpg"),
    (page_skillhub, f"{OUT_DIR}/内页-3-SkillHub技能页.jpg"),
    (page_workbuddy, f"{OUT_DIR}/内页-4-WorkBuddy安装路径.jpg"),
]

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for fn, out in OUTS:
        fn().convert("RGB").save(out, quality=92)
        print("saved:", out)


if __name__ == "__main__":
    build()
    for fn, out in OUTS:
        fn().convert("RGB").save(out, quality=92)
        print("saved:", out)
