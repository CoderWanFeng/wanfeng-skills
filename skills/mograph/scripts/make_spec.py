#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口播稿 → overlay-spec.json（引擎无关的动效时间轴骨架）。

本 skill 唯一的本地脚本，只用 Python 标准库，离线可跑。

它做四件事：
  1. 分句（中文优先，支持 md 编号行 / 每行一句 / 连续段落）
  2. 对齐时间（有 --srt / --timestamps 用实测；否则按 4 字/秒估算，若有源媒体时长则整体缩放）
  3. 关键词命中 → 8 类动画意图 + 位置（slot）分配（避开人脸安全区）
  4. 输出 overlay-spec.json + 中文摘要

两条风格路径（--style-path）：
  - generic（默认）：上面这四件事全做，出 overlay-spec.json，供 Remotion / HyperFrames 渲染。
  - wanfeng（晚枫专用）：只做 1、2，再把字幕切成「场景骨架」（时间区间 + 建议版式），
    出 wanfeng-scene-plan.json；场景内容与文案由 agent 按 reference/wanfeng-path.md 手写，
    渲染器是 Pillow 自绘，不是浏览器。

它不做的事（交给 agent / 下游）：
  - 不联网检索（见 reference/research-protocol.md，由 agent 执行）
  - 不写渲染代码（见 reference/engine-*.md）
  - 不核实稿件里的数字真伪

用法：
  python3 scripts/make_spec.py --script 口播稿.md --video 口播.mp4 --out spec.json
  python3 scripts/make_spec.py --script 口播稿.md --srt 字幕.srt --density high --stdout
  python3 scripts/make_spec.py --script 口播稿.md --srt 字幕.srt --style-path wanfeng --stdout
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import unicodedata

CJK_CPS = 4.0  # 中文口播约 4 字/秒（与 knowledge-short-video 口径一致）

# ---- 8 类动画：命中规则（正则）+ 默认落位偏好 ----
ANIM_RULES = [
    ("number-roll",   r"(?:\d+(?:[.,]\d+)?\s*(?:%|％|倍|万|亿|元|块|秒|分钟|小时|天|次|人|家|款))",
     ["right", "top"]),
    ("bar-chart",     r"(?:比|相比|高于|低于|多|少|贵|便宜|涨|跌|上升|下降|增长|减少)\S{0,12}(?:\d|\一|\二|\三|\半|倍|成)",
     ["right", "left"]),
    ("split-compare", r"(?:而不是|不是.{1,12}(?:而是|是)|对比|VS|vs\.?|前者|后者|两种|三个方案|好 vs|以前.{0,10}现在)",
     ["top", "bottom"]),
    ("checklist",     r"(?:第[一二三四五六七八九十]|[1-9][\.、)]|首先|其次|再次|最后|一是|二是|要么)",
     ["left", "right"]),
    ("quote-card",    r"(?:[「『“\"].{4,60}[」』”\"])",
     ["top", "bottom"]),
    ("timeline",      r"(?:\d{4}\s*年|去年|今年|明年|\d+\s*月|上个季度|这三年|第一阶段|里程碑)",
     ["bottom", "top"]),
    ("logo-card",     r"(?:[A-Z][A-Za-z0-9]{2,}(?:\s?[A-Z][a-z]+)?|ChatGPT|GPT-\d+|Claude|Cursor|Remotion)",
     ["top", "right"]),
    ("keyword-pop",   r"(?:所谓|也就是说|本质上|关键在于|重点是|记住|注意|简单说|叫做|指的是)",
     ["bottom", "right"]),
]

DENSITY_GAP = {"sparse": 8.0, "standard": 5.0, "high": 2.5}
DENSITY_CAP = {"sparse": 1, "standard": 1, "high": 2}  # 同屏并发卡上限

# ---- 晚枫专用路径（--style-path wanfeng）----
# 通用路径靠正则把句子命中成 8 类动效；晚枫路径不这么做 ——
# 晚枫的成片是「手写场景表」：一段口播 = 一个场景，版式由内容决定。
# 所以脚本在 wanfeng 模式下只做两件事：
#   1. 实测时间轴（与通用路径完全一致）
#   2. 切出场景骨架（时间区间 + 建议版式 + 该段口播原文）
# 场景内容与文案留给 agent 按 reference/wanfeng-path.md 手写。
WF_SCENE_MIN = 5.0      # 单场最短时长（秒）
WF_SCENE_MAX = 12.0     # 单场最长时长（秒）
WF_BOUNDARY = re.compile(
    r"(第[一二三四五六七八九十]步|首先|其次|再次|最后|然后|接下来|所以|但是|不过|而且|"
    r"重点是|关键是|一句话|总结一下|说白了|打个比方|举个例子)")
WF_LAYOUTS = {
    "hook":      "开场钩子（fs 全屏设计版式 + 圆形人头）",
    "statement": "观点卡（overlay 真人打底 + 单卡）",
    "evidence":  "证据卡 / 数字卡（overlay）",
    "step":      "操作步骤（fs 全屏 + 截图 + 步骤条 + 圆形人头）",
    "reveal":    "揭晓卡（overlay，强调结论）",
    "cta":       "行动号召（片尾 CTA）",
}

# 人脸安全区（归一化）：卡片一律不得与此区相交（见 reference/overlay-layout.md）
FACE_SAFE = {
    "9:16": {"x": (0.30, 0.70), "y": (0.18, 0.76)},
    "16:9": {"x": (0.28, 0.72), "y": (0.18, 0.70)},
}
SLOT_NORM = {  # slot -> 建议包围盒（归一化 x0,y0,x1,y1）
    "top":    (0.06, 0.03, 0.94, 0.16),
    "bottom": (0.06, 0.78, 0.94, 0.96),
    "left":   (0.03, 0.24, 0.26, 0.72),
    "right":  (0.74, 0.24, 0.91, 0.72),  # 右边留 9% 给平台互动按钮（见 overlay-layout.md §5）
    "center": (0.30, 0.20, 0.70, 0.62),  # 仅 layer=front（抠图遮挡）时允许
}
LABELS = {
    "number-roll": "数字滚动卡", "bar-chart": "对比柱图", "split-compare": "分屏对比",
    "checklist": "清单逐条", "quote-card": "引用卡", "timeline": "时间轴",
    "logo-card": "品牌/产品名卡", "keyword-pop": "关键词弹字", "none": "纯口播无卡",
}


def strip_md(line):
    line = re.sub(r"^[\s>#*\-\u2022\d]+(?=[\.、\)])?", "", line).strip()
    line = re.sub(r"[ \t]+", " ", line)
    return unicodedata.normalize("NFKC", line)


def detect_duration_hint(text):
    """从稿件元信息里抓标称时长（如「> 时长：~85s」），抓不到返回 None。"""
    m = re.search(r"时长[^\d]{0,6}[~～约]?\s*(\d+(?:\.\d+)?)\s*(?:s\b|秒)", text)
    return float(m.group(1)) if m else None


def split_sentences(text, keep_meta=False):
    """中文优先分句：先按行，再按句末标点切碎。返回句子列表。

    默认丢掉非口播内容：blockquote 元信息（> 时长：~85s）、表格行、标题、代码块、
    分隔线、以及 `**依赖**：` 这类字段行。需要连标题一起读时传 keep_meta=True。
    """
    out = []
    in_fence = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not keep_meta:
            st = line.lstrip()
            if st.startswith(">") or st.startswith("|") or st.startswith("#") \
               or st.startswith("---") or st.startswith("===") or st.startswith("!["):
                continue
        s = strip_md(line)
        if not s or re.match(r"^\*{0,2}[^：]{1,6}\*{0,2}：\s*[\*~～]?\d", s):
            continue  # 「字数：390」这类字段行
        parts = re.split(r"(?<=[。？！?!；;])", s)
        for p in parts:
            p = p.strip()
            if len(p) >= 2:
                out.append(p)
    return out


def probe_media(path):
    """ffprobe 实测时长与画幅；拿不到返回 None（不报错）。"""
    if not path or not os.path.isfile(path):
        return None
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=15)
        d = json.loads(p.stdout or "{}")
        dur = float(d.get("format", {}).get("duration") or 0) or None
        w = h = None
        for st in d.get("streams", []):
            if st.get("width"):
                w, h = int(st["width"]), int(st["height"])
                break
        return {"duration": dur, "width": w, "height": h}
    except Exception:
        return None


def parse_srt(path):
    """解析 SRT → [(text, start, end)]；解析失败返回 []。"""
    try:
        with open(path, encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []
    def t2s(x):
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", x.strip())
        if not m:
            return None
        h, mi, s, ms = map(int, m.groups())
        return h * 3600 + mi * 60 + s + ms / 1000.0
    out = []
    for blk in re.split(r"\n\s*\n", content):
        lines = [l for l in blk.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        rng = next((l for l in lines if "-->" in l), None)
        if not rng:
            continue
        a, b = rng.split("-->")
        st, en = t2s(a), t2s(b)
        txt = " ".join(l.strip() for l in lines if "-->" not in l and not l.strip().isdigit())
        if st is not None and en is not None and txt:
            out.append((txt, st, en))
    return out


def load_timestamps(path):
    """[{text,start,end}] JSON；也兼容 {"words":[...]} 与 segments 形式。"""
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return []
    items = d if isinstance(d, list) else (d.get("segments") or d.get("items") or [])
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        txt = (it.get("text") or "").strip()
        st, en = it.get("start"), it.get("end")
        if txt and st is not None and en is not None:
            out.append((txt, float(st), float(en)))
    return out


def match_animation(text):
    """命中第一个动画类型 + 关键词；都不中则 None。"""
    for kind, pat, slots in ANIM_RULES:
        m = re.search(pat, text)
        if m:
            kw = m.group(0).strip()
            if kind == "number-roll":
                kw = re.sub(r"\s+", "", kw)
            return kind, kw, slots
    return None, None, None


def slot_conflicts(slot, aspect):
    """落位是否与人脸安全区相交。"""
    fx0, fx1 = FACE_SAFE[aspect]["x"]
    fy0, fy1 = FACE_SAFE[aspect]["y"]
    sx0, sy0, sx1, sy1 = SLOT_NORM[slot]
    return not (sx1 <= fx0 or sx0 >= fx1 or sy1 <= fy0 or sy0 >= fy1)


def choose_slot(pref, aspect, occupied):
    """按偏好顺序选一个不撞脸、且未被同屏卡片占用的位置。"""
    order = list(pref or []) + [s for s in SLOT_NORM if s not in (pref or [])]
    for s in order:
        if s == "center":            # 前景遮挡位默认排除（R3：v1 不做抠图）
            continue
        if slot_conflicts(s, aspect):
            continue
        if s in occupied:
            continue
        return s
    for s in order:
        if s != "center" and not slot_conflicts(s, aspect):
            return s
    return None


def assign_slots(segs, aspect, cap):
    """按时间顺序落位：避脸 → 避同屏占位 → 超并发上限则弃卡（并回写 animation=None）。"""
    result = []
    prev = None
    for i, seg in enumerate(segs):
        if not seg["animation"]:
            result.append(None)
            continue
        live = [result[j] for j in range(i)
                if segs[j]["animation"] and result[j] and vis_overlap(segs[i], segs[j])]
        if len(live) >= cap:
            result.append(None)
            seg["animation"] = None
            seg["dropped"] = "同屏已达上限（%d 张），本条弃卡" % cap
            continue
        cand = choose_slot(ANIM_SLOTS[seg["animation"]], aspect, live)
        if cand and cand == prev:
            cand = choose_slot(ANIM_SLOTS[seg["animation"]], aspect, live + [prev]) or cand
        if cand:
            prev = cand
        result.append(cand)
    return result


def vis_overlap(a, b):
    """两张卡的可见窗口是否同屏（留 0.05s 空档，不做叠化打架）。"""
    if not a.get("vis") or not b.get("vis"):
        return False
    a0, a1 = a["vis"]
    b0, b1 = b["vis"]
    return a0 < b1 - 0.05 and b0 < a1 - 0.05


ANIM_SLOTS = {}


def resolve_timeline(args):
    """解析稿件 + 对齐时间 + 探测时长与画幅。通用路径与晚枫专用路径共用这一段。"""
    with open(args.script, encoding="utf-8") as f:
        text = f.read()

    sentences = split_sentences(text, keep_meta=args.keep_meta_lines)

    real = []
    if args.srt:
        real = parse_srt(args.srt)
    if not real and args.timestamps:
        real = load_timestamps(args.timestamps)

    # 有实测时间戳时不需要稿件分句（时间轴与文案都以字幕为准），
    # 只有既没稿件句子、也没时间戳才真的没东西可用。
    if not sentences and not real:
        sys.exit("口播稿里没解析出任何句子，检查格式（每句一行或按。！？分句），"
                 "或用 --srt / --timestamps 提供实测时间戳")

    media = probe_media(args.video or args.audio)
    hint = detect_duration_hint(text)
    # 时长优先级：实测媒体 > --duration 手给 > 稿件元信息 > 无（按字数硬估）
    total, duration_source = None, "chars-only"
    if media and media.get("duration"):
        total, duration_source = media["duration"], "probed"
    elif args.duration:
        total, duration_source = args.duration, "given"
    elif hint:
        total, duration_source = hint, "script-hint"

    segs = []
    if real:
        for txt, st, en in real:
            segs.append({"start": round(st, 2), "end": round(max(en, st + 0.4), 2), "text": txt})
        timing_source = "measured"
    else:
        pos = 0.0
        for s in sentences:
            dur = max(1.0, len(s) / CJK_CPS)
            segs.append({"start": round(pos, 2), "end": round(pos + dur, 2), "text": s})
            pos += dur
        timing_source = "estimated"
        if total and pos > 0:
            k = total / pos
            for sg in segs:
                sg["start"] = round(sg["start"] * k, 2)
                sg["end"] = round(sg["end"] * k, 2)

    if not total and segs:
        total = segs[-1]["end"]

    aspect = args.aspect
    if aspect == "auto":
        if media and media.get("width") and media.get("height"):
            aspect = "9:16" if media["height"] >= media["width"] else "16:9"
        else:
            aspect = "9:16"

    return {"text": text, "segs": segs, "total": total,
            "duration_source": duration_source, "timing_source": timing_source,
            "aspect": aspect, "media": media}


def build_spec(args):
    tl = resolve_timeline(args)
    segs = tl["segs"]
    total = tl["total"]
    timing_source = tl["timing_source"]
    duration_source = tl["duration_source"]
    aspect = tl["aspect"]
    media = tl["media"]

    # ---- 命卡：密度 + 类型 ----
    gap = DENSITY_GAP[args.density]
    last_hit = -999.0
    for sg in segs:
        kind, kw, _ = match_animation(sg["text"])
        if kind and (sg["start"] - last_hit) >= gap:
            sg["animation"] = kind
            sg["keywords"] = [kw] if kw else []
            # 卡片可见窗口：晚于句首 0.2s 入场，最长 3.0s，句尾留 0.2s 出场
            sg["vis"] = (round(sg["start"] + 0.2, 2),
                         round(min(sg["end"] - 0.2, sg["start"] + 3.2), 2))
            last_hit = sg["start"]
        else:
            sg["animation"] = None
            sg["keywords"] = []

    for kind, _p, slots in ANIM_RULES:
        ANIM_SLOTS[kind] = slots
    cap = args.max_slots or DENSITY_CAP[args.density]
    slots_out = assign_slots(segs, aspect, cap)

    spec_segs = []
    type_count = {}
    slot_count = {}
    dropped = 0
    covered = 0.0
    for sg, slot in zip(segs, slots_out):
        entry = {"id": len(spec_segs) + 1, "start": sg["start"], "end": sg["end"],
                 "text": sg["text"], "animation": None}
        if sg["animation"]:
            vs, ve = sg["vis"]
            entry["animation"] = {
                "type": sg["animation"], "slot": slot, "layer": "behind",
                "visible": {"start": vs, "end": ve},
                "keywords": sg["keywords"], "brief": "",
            }
            type_count[sg["animation"]] = type_count.get(sg["animation"], 0) + 1
            slot_count[slot or "?"] = slot_count.get(slot or "?", 0) + 1
            covered += max(0.0, ve - vs)
        elif sg.get("dropped"):
            entry["dropped"] = sg["dropped"]
            dropped += 1
        spec_segs.append(entry)

    spec = {
        "$schema": "mograph/overlay-spec@1",
        "meta": {
            "source_script": os.path.basename(args.script),
            "source_video": os.path.basename(args.video or args.audio or ""),
            "aspect": aspect,
            "duration": round(total or 0, 2),
            "duration_source": "timeline" if (timing_source == "measured"
                                             and duration_source == "chars-only") else duration_source,
            "timing_source": timing_source,
            "density": args.density,
            "engine_hint": args.engine,
            "face_safe_zone": FACE_SAFE[aspect],
            "generated_by": "scripts/make_spec.py v1.0.0",
        },
        "warnings": (
            [] if timing_source == "measured"
            else ["时间戳为估算（4 字/秒），交付前必须试听对齐 —— 见 SKILL.md 硬规则 R1"]
        ) + (["本次未联网检索，动效实现使用内置最小方案 —— R4"] if args.no_net_hint else [])
        + (["%d 条命中动画但因同屏上限 %d 被弃卡，可改 --density 或 --max-slots" % (dropped, cap)]
           if dropped else []),
        "segments": spec_segs,
    }
    summary = {
        "cards": sum(type_count.values()),
        "coverage": round(covered / total * 100, 1) if total else 0.0,
        "by_type": type_count,
        "by_slot": slot_count,
        "dropped": dropped,
        "max_concurrent": cap,
    }
    return spec, summary, media


def group_scenes(segs):
    """把字幕切成场景骨架：每场 5–12s，遇到结构词提前断场，末场太短并入上一场。"""
    groups = []
    cur = []
    for i, cue in enumerate(segs):
        cur.append(cue)
        dur = cue["end"] - cur[0]["start"]
        if dur < WF_SCENE_MIN:
            continue
        nxt = segs[i + 1] if i + 1 < len(segs) else None
        if nxt is not None and dur < WF_SCENE_MAX and WF_BOUNDARY.search(nxt["text"]):
            groups.append(cur)
            cur = []
            continue
        if dur >= WF_SCENE_MAX:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    # 末场太短（不足最短时长）并入上一场，避免出现 1 秒的碎场
    if len(groups) >= 2 and (groups[-1][-1]["end"] - groups[-1][0]["start"]) < WF_SCENE_MIN:
        groups[-2].extend(groups.pop())
    return groups


def guess_layout(text, idx, n):
    """按内容猜建议版式。只是建议 —— 最终版式由 agent 按 wanfeng-path.md §5 定。"""
    if idx == 0:
        return "hook"
    if idx == n - 1:
        return "cta"
    if re.search(r"第[一二三四五六七八九十]步|打开|选择|点击|点「|搜「|去试试|丢进|上传", text):
        return "step"
    if re.search(r"\d+\s*(?:块|元|万|亿|倍|%|％|秒|分钟|款|个|人)", text) or "免费" in text:
        return "evidence"
    if re.search(r"答案|最后告诉你|结果|你看|揭晓", text):
        return "reveal"
    return "statement"


def build_scene_plan(args):
    """晚枫专用路径：只出场景骨架，不做正则命中，也不做 slot 分配。"""
    tl = resolve_timeline(args)
    segs = tl["segs"]
    groups = group_scenes(segs)

    scenes = []
    for i, group in enumerate(groups):
        txt = "".join(c["text"] for c in group)
        layout = guess_layout(txt, i, len(groups))
        st, en = group[0]["start"], group[-1]["end"]
        scenes.append({
            "id": i + 1,
            "start": round(st, 2),
            "end": round(en, 2),
            "duration": round(en - st, 2),
            "layout": layout,
            "layout_hint": WF_LAYOUTS[layout],
            "mode": "fs" if layout in ("hook", "step") else "overlay",
            "head": layout in ("hook", "step"),
            "head_pos": "bottom-left" if layout == "hook" else "top-right",
            "cues": [c["text"] for c in group],
            "text": txt,
            "note": "待填：按 reference/wanfeng-path.md §5/§6 手写这一场的 layers 与文案",
        })

    warnings = []
    if tl["timing_source"] != "measured":
        warnings.append("时间戳为估算（4 字/秒），交付前必须试听对齐 —— 见 SKILL.md 硬规则 R1")
    warnings.append("本文件是**骨架**：场景版式、文案、圆形人头位置须按 reference/wanfeng-path.md 手写后才可渲染")
    if args.density != "standard":
        warnings.append("晚枫专用路径不使用 --density，密度由场景表人工控制（该参数已忽略）")

    plan = {
        "$schema": "mograph/wanfeng-scene-plan@1",
        "meta": {
            "style_path": "wanfeng",
            "renderer_hint": "pillow-frame",
            "source_script": os.path.basename(args.script),
            "source_video": os.path.basename(args.video or args.audio or ""),
            "aspect": tl["aspect"],
            "duration": round(tl["total"] or 0, 2),
            "duration_source": ("timeline" if (tl["timing_source"] == "measured"
                                               and tl["duration_source"] == "chars-only")
                                else tl["duration_source"]),
            "timing_source": tl["timing_source"],
            "scenes": len(scenes),
            "generated_by": "scripts/make_spec.py v1.1.0",
            "spec_ref": "reference/wanfeng-path.md",
        },
        "warnings": warnings,
        "scenes": scenes,
    }
    return plan


def emit_png_plan(spec, out_dir):
    plan = []
    for sg in spec["segments"]:
        a = sg.get("animation")
        if not a:
            continue
        vis = a.get("visible") or {}
        x0, y0 = SLOT_NORM[a["slot"]][:2] if a["slot"] in SLOT_NORM else (0.06, 0.03)
        plan.append({"frame_png": "cards/card-%02d.png" % sg["id"],
                     "start": vis.get("start", sg["start"]),
                     "end": vis.get("end", sg["end"]),
                     "slot": a["slot"], "xy": [x0, y0],
                     "ffmpeg_xy": "x=W*%.2f:y=H*%.2f" % (x0, y0),
                     "text": sg["text"][:40]})
    p = os.path.join(out_dir, "ffmpeg-plan.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"note": "每张 card-XX.png 由 agent 用 HTML 截图生成，再用 ffmpeg overlay 合成",
                   "items": plan}, f, ensure_ascii=False, indent=2)
    return p


def main_wanfeng(args):
    """晚枫专用路径的终端输出：打印场景骨架表。"""
    plan = build_scene_plan(args)
    out = args.out
    if out and not args.stdout:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

    m = plan["meta"]
    counts = collections.Counter(s["layout"] for s in plan["scenes"])
    print("== 晚枫专用路径 · 场景骨架 ==")
    print("源视频：%s｜%ss（时长来源：%s）｜%s"
          % (m["source_video"] or "未提供", m["duration"], m["duration_source"], m["aspect"]))
    print("时间戳：%s｜场景：%d 场｜渲染器：pillow-frame"
          % ("实测" if m["timing_source"] == "measured" else "估算（4 字/秒）", m["scenes"]))
    print("版式：" + "｜".join("%s %d" % (k, v) for k, v in sorted(counts.items())))
    for s in plan["scenes"]:
        print("  #%-2d %6.2f–%6.2fs  %-9s %-7s %s"
              % (s["id"], s["start"], s["end"], s["layout"], s["mode"], s["layout_hint"]))
    for w in plan["warnings"]:
        print("⚠️ %s" % w)
    if args.emit_png_plan:
        print("提示：晚枫专用路径不出 ffmpeg 兜底计划（无 slot 概念），已忽略 --emit-png-plan")
    if out and not args.stdout:
        print("已写出：%s" % out)
    if args.stdout:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description="口播稿 → overlay-spec.json")
    ap.add_argument("--script", required=True, help="口播稿 .md/.txt")
    ap.add_argument("--video", help="源视频（探测时长与画幅）")
    ap.add_argument("--audio", help="源音频（无视频时用）")
    ap.add_argument("--duration", type=float, default=None,
                    help="手给成片总时长（秒）。优先级：实测媒体 > 本参数 > 稿件元信息")
    ap.add_argument("--srt", help="SRT 字幕，实测时间戳")
    ap.add_argument("--timestamps", help="JSON 时间戳 [{text,start,end}]")
    ap.add_argument("--density", default="standard", choices=list(DENSITY_GAP))
    ap.add_argument("--style-path", default="generic", choices=["generic", "wanfeng"],
                    help="风格路径：generic=正则命中出 overlay-spec.json；"
                         "wanfeng=出场景骨架（见 reference/wanfeng-path.md）")
    ap.add_argument("--aspect", default="auto", choices=["auto", "9:16", "16:9"])
    ap.add_argument("--engine", default="auto", choices=["auto", "remotion", "hyperframes", "none"])
    ap.add_argument("--max-slots", type=int, default=None, help="同屏并发卡上限（默认按密度：克制/标准 1、高密度 2）")
    ap.add_argument("--out", default=None, help="输出 overlay-spec.json")
    ap.add_argument("--stdout", action="store_true", help="只打印，不写文件")
    ap.add_argument("--emit-png-plan", action="store_true", help="额外输出 ffmpeg 兜底计划")
    ap.add_argument("--no-net-hint", action="store_true", help="声明本次未联网（写进 warnings）")
    ap.add_argument("--keep-meta-lines", action="store_true",
                    help="把标题/表格/元信息行也当口播内容（默认丢弃）")
    args = ap.parse_args()

    if not os.path.isfile(args.script):
        sys.exit("找不到口播稿：%s" % args.script)

    if args.style_path == "wanfeng":
        return main_wanfeng(args)

    spec, summary, media = build_spec(args)

    out = args.out
    if out and not args.stdout:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)

    m = spec["meta"]
    print("== 口播动效骨架 ==")
    print("源视频：%s｜%ss（时长来源：%s）｜%s"
          % (m["source_video"] or "未提供", m["duration"], m["duration_source"], m["aspect"]))
    print("时间戳：%s｜动画卡：%d 张｜覆盖 %.1f%%｜单屏最多 %d 张｜弃卡 %d 条"
          % ("实测" if m["timing_source"] == "measured" else "估算（4 字/秒）",
             summary["cards"], summary["coverage"], summary["max_concurrent"],
             summary["dropped"]))
    if summary["by_slot"]:
        print("分布：" + "｜".join("%s %d" % (k, v) for k, v in sorted(summary["by_slot"].items())))
    if summary["by_type"]:
        print("类型：" + "｜".join("%s(%s) %d" % (LABELS.get(k, k), k, v)
                                  for k, v in sorted(summary["by_type"].items(),
                                                     key=lambda x: -x[1])))
    for w in spec["warnings"]:
        print("⚠️ %s" % w)
    if summary["cards"] == 0:
        print("提示：一句都没命中动画。要么稿件太叙述化，要么把 --density 调成 high 再看。")
    elif summary["coverage"] < 40.0:
        print("提示：覆盖率 %.1f%%，低于 Step 6 的 40%% 交付闸 —— 回 Step 3 手工补卡（SKILL.md）"
              % summary["coverage"])
    if args.emit_png_plan:
        d = os.path.dirname(os.path.abspath(out or "overlay-spec.json"))
        print("ffmpeg 兜底计划：%s" % emit_png_plan(spec, d))
    if out and not args.stdout:
        print("已写出：%s" % out)
    if args.stdout:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
