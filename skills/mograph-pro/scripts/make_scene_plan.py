#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口播稿 + 字幕 → 场景骨架（wanfeng-scene-plan.json）。

mograph-pro 唯一的「离线秒级」脚本，只用 Python 标准库。

它只做两件事：
  1. 实测时间轴（有 --srt / --timestamps 用实测；否则按 4 字/秒估算）
  2. 把字幕切成「场景骨架」：时间区间 + 建议版式 + 该段口播原文

它**不做**的事（交给 agent / 下游）：
  - 不做正则命中动效、不做 slot 分配（晚枫成片靠手写场景表，不靠正则）
  - 不写渲染代码（版式与文案按 references/wanfeng-path.md §5/§6 手写）
  - 不核实稿件里的数字真伪

用法：
  python3 scripts/make_scene_plan.py --script 口播稿.md --srt 字幕.srt --stdout
  python3 scripts/make_scene_plan.py --script 口播稿.md --video 口播.mov --out scene-plan.json
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

# ---- 晚枫线参数（不要改：这些是版式节奏的一部分）----
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


def resolve_timeline(args):
    """解析稿件 + 对齐时间 + 探测时长与画幅。"""
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
    """晚枫线：只出场景骨架，不做正则命中，也不做 slot 分配。"""
    if getattr(args, 'source_mode', 'talking-head') == 'digital-human':
        from digital_contract import load_timeline, scene_plan
        if not getattr(args, 'digital_timeline', None):
            raise ValueError('数字人模式必须提供完整 --digital-timeline，不能用 talking.mp4')
        timeline = load_timeline(args.digital_timeline, srt=args.srt)
        return scene_plan(timeline, script=args.script or '',
                          aspect='9:16' if args.aspect == 'auto' else args.aspect)
    if getattr(args, 'digital_timeline', None):
        raise ValueError('--digital-timeline 只用于 --source-mode digital-human')
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
            "note": "待填：按 references/wanfeng-path.md §5/§6 手写这一场的 layers 与文案",
        })

    warnings = []
    if tl["timing_source"] != "measured":
        warnings.append("时间戳为估算（4 字/秒），交付前必须试听对齐 —— 见 SKILL.md 硬规则 W17")
    warnings.append("本文件是**骨架**：场景版式、文案、圆形人头位置须按 references/wanfeng-path.md 手写后才可渲染")
    if args.density != "standard":
        warnings.append("晚枫线不使用 --density，密度由场景表人工控制（该参数已忽略）")

    plan = {
        "$schema": "mograph-pro/wanfeng-scene-plan@1",
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
            "generated_by": "scripts/make_scene_plan.py v1.0.0",
            "spec_ref": "references/wanfeng-path.md",
        },
        "warnings": warnings,
        "scenes": scenes,
    }
    return plan


def main():
    ap = argparse.ArgumentParser(
        description="口播稿 + 字幕 → 场景骨架（mograph-pro 晚枫线）")
    ap.add_argument('--source-mode', choices=('talking-head', 'digital-human'), default='talking-head')
    ap.add_argument('--digital-timeline', help='引擎完整 a_roll.json；保留 A/B 边界')
    ap.add_argument("--script", help="口播稿 .md/.txt；真人模式必填")
    ap.add_argument("--video", help="源视频（探测时长与画幅）")
    ap.add_argument("--audio", help="源音频（无视频时用）")
    ap.add_argument("--duration", type=float, default=None,
                    help="手给成片总时长（秒）。优先级：实测媒体 > 本参数 > 稿件元信息")
    ap.add_argument("--srt", help="SRT 字幕，实测时间戳")
    ap.add_argument("--timestamps", help="JSON 时间戳 [{text,start,end}]")
    ap.add_argument("--density", default="standard", choices=["sparse", "standard", "high"],
                    help="晚枫线不用这个参数（密度由场景表人工控制），保留仅为兼容")
    ap.add_argument("--aspect", default="auto", choices=["auto", "9:16", "16:9"])
    ap.add_argument("--out", default=None, help="输出 wanfeng-scene-plan.json")
    ap.add_argument("--stdout", action="store_true", help="只打印，不写文件")
    ap.add_argument("--emit-png-plan", action="store_true",
                    help="晚枫线不出 ffmpeg 兜底计划，此参数已忽略")
    ap.add_argument("--no-net-hint", action="store_true",
                    help="晚枫线不检索外部动效代码，此参数已忽略")
    ap.add_argument("--keep-meta-lines", action="store_true",
                    help="把标题/表格/元信息行也当口播内容（默认丢弃）")
    args = ap.parse_args()

    if args.source_mode == 'talking-head' and (not args.script or not os.path.isfile(args.script)):
        sys.exit("找不到口播稿：%s" % args.script)

    try:
        plan = build_scene_plan(args)
    except (ValueError, OSError, KeyError) as exc:
        sys.exit('场景契约错误：' + str(exc))
    out = args.out
    if out and not args.stdout:
        d = os.path.dirname(os.path.abspath(out))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

    m = plan["meta"]
    counts = collections.Counter(s["layout"] for s in plan["scenes"])
    print("== mograph-pro · 场景骨架 ==")
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
        print("提示：晚枫线不出 ffmpeg 兜底计划（无 slot 概念），已忽略 --emit-png-plan")
    if out and not args.stdout:
        print("已写出：%s" % out)
    if args.stdout:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
