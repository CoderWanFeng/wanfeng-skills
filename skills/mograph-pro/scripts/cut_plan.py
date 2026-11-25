#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mograph-pro · Step 0：原始口播 → 语义删减计划。

输入一段一口气录完的口播视频，输出「剪掉哪些、为什么」的机器可读计划，
以及一份人可复核的 Markdown 报告。可选直接剪出干净底片。

它做六件事：
  1. 探测       —— ffprobe 取时长/画幅
  2. 静音表     —— ffmpeg silencedetect 实测气口（刀口候选点）
  3. 转写       —— mlx_whisper 逐句带时间戳（缺依赖时降级，只给静音表）
  4. 切块       —— 以**实测静音边界**为刀切分「口播块」（一次连续表达 = 一块）
  5. 语义诊断   —— 识别 废录重录 / 半截句 / 孤立口水 / 长停顿 四类问题
  6. 出计划     —— keep 区间 + drops 刀口（含类别与理由）+ 可选重排 + Markdown 报告

核心设计（都是 2-AI工具/20-混元hy4-flash 的实证结论，不是拍脑袋）：
  * 刀口只落在**实测静音区间**或**整块**上，绝不切半个字 —— whisper 的句子
    边界经常落在词中间，不能拿它当刀口。
  * 气口按「前块拿头部、后块拿尾部」分配，短停顿原样保留，长停顿收紧到 0.7s。
  * 重录保留**最后一次**（口播者后一遍更完整）。
  * 删减是**语义驱动**不是阈值驱动：光靠「删所有 ≥X 秒停顿」只能命中 20-41%。

依据：2-AI工具/20-混元hy4-flash 的实证（184.14s 原片 → 84.36s 底片，
27 个刀口，删除量中 88.65s 是静音、仅 16.15s 是真实语音内容）。
规则细节见 references/cut-rules.md。

依赖：
  必需 —— ffmpeg / ffprobe
  可选 —— mlx_whisper（转写；缺失时只做静音诊断）

用法：
  python3 cut_plan.py --video raw.MOV --out plan.json
  python3 cut_plan.py --video raw.MOV --out plan.json --report plan.md
  python3 cut_plan.py --video raw.MOV --out plan.json --apply base.mov
  python3 cut_plan.py --video raw.MOV --out plan.json --keep 0-5,20-40   # 手工指定保留段
  python3 cut_plan.py --video raw.MOV --out plan.json --reorder 3,1,2,4  # 调片段位置
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import unicodedata

# ---- 经验阈值（来自 71 号实证，见 references/cut-rules.md）----
SILENCE_NOISE_DB = -32      # silencedetect 噪声门限
SILENCE_MIN_DUR = 0.55      # 最短气口 0.55s（低于此的缝不算停顿）
BLOCK_GAP = 1.0             # 相邻发声区间间隔 < 1.0s 视为同一次表达，合为一块
LONG_PAUSE = 2.0            # 超过 2s 的停顿算「长停顿」，保留时收紧
PAUSE_KEEP = 0.35           # 长停顿收紧后，单侧保留的秒数
HEAD_KEEP = 0.35            # 保留块前的气口
TAIL_KEEP = 0.35            # 保留块后的气口
REPEAT_SIM = 0.72           # 两块相似度超过此值判定为「同一句重录」
REPEAT_GAP = 1.2            # 两块间隔超过此值才可能是重录
FRAGMENT_MAX_LEN = 8        # 短于此字数 + 后接长停顿 = 半截句候选

FILLER_WORDS = {
    "而且", "大家", "然后", "就是", "这个", "那个", "对", "啊", "嗯", "哦",
    "哈", "呃", "喂", "对吧", "是吧", "那么", "所以说", "怎么说呢", "好吧",
}

# 「话没说完」的信号词 —— 句子以这些字/词结尾，说明它是被截断的半截句。
# 只靠「短 + 长停顿」会把「一点积分都不花」这种完整结论句误删，
# 必须叠加语义信号：实词结尾 = 可能是完整句；虚词/代词结尾 = 半截句。
DANGLING_TAILS = {"这", "那", "他", "她", "它", "我", "你", "们", "就", "把",
                  "和", "跟", "与", "或", "但", "而", "且", "为", "因", "所",
                  "如", "会", "要", "能", "该", "得", "着", "让", "给", "对",
                  "吧", "呀", "啊", "嗯", "哦", "嘛", "呢", "么", "及", "等"}

DANGLING_SETS = {"大家", "咱们", "我们", "你们", "他们", "这个", "那个",
                 "而且", "然后", "所以", "但是", "不过", "就是说"}

# 叙事角色关键词 —— 用于重排建议
ROLE_RULES = [
    ("成品展示", ["这条视频", "这就是我", "动效", "截图", "标注", "字幕", "我自己剪"]),
    ("行动号召", ["赶紧去试试", "去试试吧", "评论区", "关注", "告诉我", "有问题打在"]),
    ("利益承诺", ["免费", "没有任何", "门槛", "一点积分", "零积分", "不花钱"]),
    ("操作方法", ["第一步", "第二步", "打开", "点击", "选择", "搜索", "链接", "技能"]),
    ("钩子悬念", ["注意了", "今天发布", "看到最后", "告诉你", "是不是", "真的"]),
]


# ---------------------------------------------------------------- 基础探测

def probe(path):
    """ffprobe 取时长/画幅/音轨；失败返回 None。"""
    if not path or not os.path.isfile(path):
        return None
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=20)
        d = json.loads(p.stdout or "{}")
        dur = float(d.get("format", {}).get("duration") or 0) or None
        w = h = sr = None
        for st in d.get("streams", []):
            if st.get("width"):
                w, h = int(st["width"]), int(st["height"])
            if st.get("sample_rate"):
                sr = int(st["sample_rate"])
        return {"duration": dur, "width": w, "height": h, "sample_rate": sr}
    except Exception:
        return None


def silence_table(path, noise_db=SILENCE_NOISE_DB, min_dur=SILENCE_MIN_DUR):
    """silencedetect 实测静音区间 → [(start, end)]，按时间升序。"""
    try:
        p = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
             "-af", "silencedetect=noise=%ddB:d=%.2f" % (noise_db, min_dur),
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=1800)
    except Exception as e:
        print("  [warn] silencedetect 失败: %s" % e, file=sys.stderr)
        return []
    ev = re.findall(r"silence_(start|end):\s*([0-9.]+)", p.stderr or "")
    out, pend = [], None
    for kind, val in ev:
        if kind == "start":
            pend = float(val)
        elif pend is not None:
            out.append((pend, float(val)))
            pend = None
    return out


def extract_audio(path, out_wav, sr=16000):
    """抽 16k 单声道 wav，供 ASR 用。"""
    os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path,
                    "-ac", "1", "-ar", str(sr), out_wav], check=True)
    return out_wav


def transcribe(audio_path, model="mlx-community/whisper-base-mlx"):
    """mlx_whisper 逐句转写 → [{start,end,text}]。依赖缺失返回 []。"""
    try:
        import mlx_whisper
    except ImportError:
        print("  [warn] 未装 mlx_whisper，跳过转写（只做静音诊断）", file=sys.stderr)
        return []
    try:
        r = mlx_whisper.transcribe(
            audio_path, path_or_hf_repo=model, language="zh",
            word_timestamps=True, verbose=False,
            initial_prompt="以下是普通话口播的句子，使用简体中文。")
    except TypeError:
        # 老版本没有 initial_prompt
        r = mlx_whisper.transcribe(audio_path, path_or_hf_repo=model,
                                   language="zh", word_timestamps=True, verbose=False)
    except Exception as e:
        print("  [warn] 转写失败: %s" % e, file=sys.stderr)
        return []
    out = []
    for s in r.get("segments", []):
        t = (s.get("text") or "").strip()
        if t:
            out.append({"start": round(float(s["start"]), 2),
                        "end": round(float(s["end"]), 2), "text": t})
    return out


# ---------------------------------------------------------------- 文本处理

def normalize_text(s):
    """归一化用于相似度比较：去标点、全角转半角、数字统一。"""
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"[，,。.！!？?；;：:、\"'“”‘’（）()【】\[\]…—\-~～\s]+", "", s)
    s = re.sub(r"\d+", "0", s)
    return s


def similarity(a, b):
    """0-1 相似度。"""
    a, b = normalize_text(a), normalize_text(b)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def is_filler(text):
    """孤立语气词 / 口水词（整句只有这些）。"""
    t = normalize_text(text)
    return bool(t) and t in FILLER_WORDS


def is_dangling(text):
    """句子是否「话没说完」——以虚词/代词/连词结尾。"""
    t = normalize_text(text)
    if not t:
        return False
    if t in DANGLING_SETS:
        return True
    return t[-1] in DANGLING_TAILS


def prefix_of(a, b):
    """a 是不是 b 的前缀（短版被长版取代）。

    71 号实证：「这是我发布。」→「这是我发布上来免费给大家使用的一个技能…」
    两句整体相似度只有 0.29，整体相似度抓不到，但前缀关系一目了然。
    """
    na, nb = normalize_text(a), normalize_text(b)
    if len(na) < 4 or len(na) >= len(nb):
        return False
    return nb.startswith(na)


def role_of(text):
    """给口播块打一个叙事角色标签（用于重排建议）。"""
    t = normalize_text(text)
    for role, keys in ROLE_RULES:
        for k in keys:
            if normalize_text(k) in t:
                return role
    return "叙述"


# ---------------------------------------------------------------- 切块

def voice_spans(silences, dur, gap=BLOCK_GAP):
    """由实测静音表推出「发声区间」——连续有声的一段。

    silencedetect 只报 ≥0.55s 的静音；两段静音之间夹着的极短毛刺（<0.05s）
    直接忽略。相邻发声区间间隔 < gap 的合并成一块（同一口气说完的）。
    """
    spans = []
    cur = 0.0
    for b, e in silences:
        if b - cur > 0.05:
            spans.append([cur, b])
        if e > cur:
            cur = e
    if dur - cur > 0.05:
        spans.append([cur, dur])
    merged = []
    for sp in spans:
        if merged and sp[0] - merged[-1][1] < gap:
            merged[-1][1] = sp[1]
        else:
            merged.append(list(sp))
    return merged


def group_blocks(sents, silences, dur, gap=BLOCK_GAP):
    """切出「口播块」：一次连续表达 = 一块。

    块边界 = 实测静音边界（不是 ASR 句子边界 —— whisper 会切在词中间）。
    ASR 句子按「与发声区间重叠最多」归属到块，块文本 = 归属句拼接。
    """
    spans = voice_spans(silences, dur, gap)
    if not spans:
        return []
    blocks = []
    for sp in spans:
        inside = [s for s in sents
                  if s["end"] > sp[0] + 0.02 and s["start"] < sp[1] - 0.02]
        text = "".join(x["text"] for x in inside)
        blocks.append({
            "start": round(sp[0], 2),
            "end": round(sp[1], 2),
            "text": text,
            "n_sent": len(inside),
            "role": role_of(text),
        })
    # 未归属到任何块的句子（ASR 时间戳漂移）挂到时间最近的块上
    orphan = [s for s in sents
              if not any(s["end"] > b["start"] + 0.02 and s["start"] < b["end"] - 0.02
                         for b in blocks)]
    for s in orphan:
        best = min(blocks, key=lambda b: abs((b["start"] + b["end"]) / 2 - (s["start"] + s["end"]) / 2))
        best["text"] += s["text"]
        best["n_sent"] += 1
        best["role"] = role_of(best["text"])
    return blocks


def silence_between(b_prev, b_next):
    """两个相邻块之间的气口长度（块之间全是静音）。"""
    return max(0.0, b_next["start"] - b_prev["end"])


def head_gas(gap_len):
    """保留块之前分到多少气口。

    短停顿（≤LONG_PAUSE）原样保留，前后各一半；长停顿收紧到 PAUSE_KEEP。
    """
    if gap_len <= 0:
        return 0.0
    if gap_len <= LONG_PAUSE:
        return gap_len / 2.0
    return min(PAUSE_KEEP, gap_len / 2.0)


def tail_gas(gap_len):
    """保留块之后分到多少气口（规则同 head_gas）。"""
    return head_gas(gap_len)


def build_keep(blocks, order, drop_blocks, dur):
    """按「保留块 + 气口分配」构造 keep 区间。

    **气口跟着块走**：每块的气口只从它自己**紧贴的那段静音**里取
    （不管那个原片邻居保不保留），于是：
      - 保序时，被删块两侧的静音自动归给相邻保留块，不会凭空丢一段呼吸；
      - 重排时，气口跟着块一起搬到新位置，接缝仍是自然静音，
        不会出现「跨了 60 秒原片的怪停顿」，也不会出现零长度段。

    早前一版按「order 的前后邻居 + 原片时间单调钳位」算气口，
    保序时碰巧对，重排后原片时间乱序，钳位会把区间压成 [39.34, 39.34]。
    """
    n = len(blocks)
    # 每块前后**紧贴**的那段静音（物理事实，与保留与否无关）
    head_gap = [0.0] * n
    tail_gap = [0.0] * n
    for i in range(n):
        prev_end = blocks[i - 1]["end"] if i > 0 else 0.0
        next_start = blocks[i + 1]["start"] if i + 1 < n else dur
        head_gap[i] = max(0.0, blocks[i]["start"] - prev_end)
        tail_gap[i] = max(0.0, next_start - blocks[i]["end"])

    seg = []
    for i in range(n):
        a = blocks[i]["start"] - head_gas(head_gap[i])
        e = blocks[i]["end"] + tail_gas(tail_gap[i])
        a = max(0.0, min(a, blocks[i]["start"]))   # 气口不会吃进语音
        e = min(dur, max(e, blocks[i]["end"]))
        seg.append([round(a, 2), round(e, 2)])

    keep = [list(seg[i]) for i in order if i not in drop_blocks]
    return keep, head_gap, tail_gap


# ---------------------------------------------------------------- 四类诊断

def find_repeats(blocks, sim_thr=REPEAT_SIM, min_gap=REPEAT_GAP):
    """废录/重录：不同时间出现的同一句话。

    规则（71 号实证）：
      - 文本相似度 >= sim_thr，**或** 短句是长句的前缀（前缀规则能抓到
        「这是我发布。」→「这是我发布上来…」这种整体相似度只有 0.29 的情况）
      - 两块间隔 >= min_gap（同一口气里不会隔 1 秒说同一句）
      - 保留 **最后一次** 出现（口播者重录时后一遍更完整）
      - 被删方的文本必须**可信**（语速正常）。转写幻觉块语速爆表，
        拿它当「重录」会把「点击。」这类真实指令删掉。
    """
    hits, skipped = [], {}
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            gap = blocks[j]["start"] - blocks[i]["end"]
            if gap < min_gap:
                continue
            if not normalize_text(blocks[i]["text"]) or not normalize_text(blocks[j]["text"]):
                continue
            if not is_trustworthy(blocks[i]):
                skipped.setdefault(i, {"i": i, "text": blocks[i]["text"][:40],
                                       "rate": round(speech_rate(blocks[i]), 1),
                                       "why": "语速 %.0f 字/秒，文本被转写污染，不可作删除依据"
                                              % speech_rate(blocks[i])})
                continue
            s = similarity(blocks[i]["text"], blocks[j]["text"])
            pref = prefix_of(blocks[i]["text"], blocks[j]["text"])
            if s >= sim_thr or pref:
                hits.append({"i": i, "j": j, "sim": round(s, 3),
                             "prefix": pref,
                             "text": blocks[j]["text"][:40]})
    drop = set()
    for h in hits:
        drop.add(h["i"])          # 保留最后一次
    return hits, sorted(drop), [skipped[k] for k in sorted(skipped)]


def find_fragments(blocks, gap_after, max_len=FRAGMENT_MAX_LEN, long_pause=LONG_PAUSE):
    """半截句：话说了一半就停住，后面是大停顿。

    判定需要**语义信号**，不能只看「短 + 长停顿」——
    「一点积分都不花」也是 7 字 + 4.8s 停顿，但它是完整结论句，不能删。
    两条规则满足其一即判半截句：
      A. 结尾是虚词/代词/连词（话没说完）且后面有停顿
      B. 极短（≤5 字）且后面是长停顿
    """
    out = []
    for i, b in enumerate(blocks):
        t = normalize_text(b["text"])
        if not t or len(t) > max_len:
            continue
        if not is_trustworthy(b):
            continue
        pa = gap_after[i]
        if is_dangling(b["text"]) and pa >= 0.8:
            out.append({"i": i, "text": b["text"][:40], "pause_after": round(pa, 2),
                        "why": "话没说完（结尾「%s」）就停 %.1fs" % (t[-1], pa)})
        elif len(t) <= 5 and pa >= long_pause:
            out.append({"i": i, "text": b["text"][:40], "pause_after": round(pa, 2),
                        "why": "说完半句后停 %.1fs" % pa})
    return out


# ------------------------------------------------- 文本可信度（识别转写幻觉）

# 正常中文口播语速约 4-6 字/秒。转写模型有「重复转写」幻觉——把上一句的
# 文本贴到下一段上，导致字数与时长严重不符（71 号实测：0.36s 的块里塞了
# 14 个字 = 39 字/秒）。这种块的文本不可信，**不能作为删除依据**，
# 否则会把「点击。」「点进去之后。」这类真实操作指令误删。
#
# 注：曾试过用 log-mel 倒谱指纹做音频层面的复核，但实测正负样本完全重叠
# （真重录 0.19-0.36 vs 不同内容 0.18-0.37）——重录时语调、语速、麦距
# 都变了，短片段的声学指纹没有区分度。语速判据反而干净可靠。
SPEECH_RATE_MAX = 12.0      # 字/秒，超过即判定文本被转写污染
SPEECH_RATE_MIN = 1.2       # 字/秒，低于即这块几乎没有有效语音


def speech_rate(block):
    """块的语速（字/秒）。"""
    dur = max(0.01, block["end"] - block["start"])
    return len(normalize_text(block["text"])) / dur


def is_trustworthy(block):
    """块的转写文本是否可信（能否作为删除依据）。"""
    n = len(normalize_text(block["text"]))
    if n == 0:
        return True           # 没有文本的块（纯气口）不参与语义判定
    return speech_rate(block) <= SPEECH_RATE_MAX


def find_fillers(blocks, gap_before, gap_after):
    """孤立口水词：整句只有语气词，且两侧都有停顿。"""
    out = []
    for i, b in enumerate(blocks):
        if not is_filler(b["text"]):
            continue
        if not is_trustworthy(b):
            continue
        pa = gap_before[i]
        pb = gap_after[i]
        if pa >= 0.6 or pb >= 0.6:
            out.append({"i": i, "text": b["text"][:20], "pause_before": round(pa, 2),
                        "pause_after": round(pb, 2), "why": "孤立语气词，两侧都有停顿"})
    return out


def find_long_pauses(blocks, gap_after, thr=LONG_PAUSE):
    """长停顿：两侧都有内容的空白，保留时需要收紧。"""
    out = []
    for i in range(len(blocks)):
        g = gap_after[i]
        if g < thr:
            continue
        out.append({"i": i, "from": blocks[i]["end"], "to": blocks[i + 1]["start"] if i + 1 < len(blocks)
                    else blocks[i]["end"] + g,
                    "dur": round(g, 2),
                    "why": "%.1fs 长停顿，保留时收紧到 %.2fs" % (g, PAUSE_KEEP * 2)})
    return out


# ---------------------------------------------------------------- 计划生成

def build_plan(video, args):
    meta = probe(video) or {}
    dur = meta.get("duration") or 0.0
    print("[1/6] 探测：%s 时长 %s" % (os.path.basename(video),
                                    ("%.2fs" % dur) if dur else "未知"))
    if not dur:
        print("  [error] 拿不到时长，退出", file=sys.stderr)
        return None

    sil = silence_table(video, args.noise_db, args.silence_min)
    sil_total = sum(e - b for b, e in sil)
    print("[2/6] 静音表：%d 段，合计 %.2fs（占全片 %.1f%%）"
          % (len(sil), sil_total, sil_total / dur * 100))

    sents = []
    if not args.no_asr:
        wav = args.audio or os.path.join(args.work, "audio16k.wav")
        print("[3/6] 转写：%s" % wav)
        try:
            # 已有 wav 就复用（重复调参时省一次抽音）
            if not (os.path.isfile(wav) and os.path.getsize(wav) > 1024):
                extract_audio(video, wav)
            sents = transcribe(wav, args.asr_model)
        except Exception as e:
            print("  [warn] 抽音轨失败: %s" % e, file=sys.stderr)
        print("      %d 句" % len(sents))
    else:
        print("[3/6] 转写：已跳过")

    blocks = group_blocks(sents, sil, dur, args.block_gap)
    print("[4/6] 切块：%d 块" % len(blocks))
    if not blocks:
        print("  [error] 没切出任何块（静音参数是否过严？）", file=sys.stderr)
        return None

    # 块间气口
    gap_after = [silence_between(blocks[i], blocks[i + 1]) if i + 1 < len(blocks) else 0.0
                 for i in range(len(blocks))]
    gap_before = [0.0] + gap_after[:-1]

    reps, rep_drop, reps_skipped = find_repeats(blocks, args.repeat_sim, args.repeat_gap)
    frags = find_fragments(blocks, gap_after, args.fragment_len, args.long_pause)
    fillers = find_fillers(blocks, gap_before, gap_after)
    pauses = find_long_pauses(blocks, gap_after, args.long_pause)
    untrusted = [i for i, b in enumerate(blocks) if not is_trustworthy(b)]

    # ---- 组装刀口（块级删除 + 停顿收紧）----
    drops = []
    for h in reps:
        b = blocks[h["i"]]
        if h.get("prefix"):
            why = "「%s」是后面那句的截短版，保留完整的那一遍" % b["text"][:20]
        else:
            why = "「%s」重复录制（相似度 %.0f%%），保留最后一次" % (h["text"], h["sim"] * 100)
        drops.append({"block": h["i"], "from": b["start"], "to": b["end"],
                      "kind": "重录废稿", "text": b["text"][:40], "why": why,
                      "keep_hint": h["j"]})
    for f in frags:
        b = blocks[f["i"]]
        drops.append({"block": f["i"], "from": b["start"], "to": b["end"],
                      "kind": "半截句", "text": b["text"][:40], "why": f["why"]})
    for f in fillers:
        b = blocks[f["i"]]
        drops.append({"block": f["i"], "from": b["start"], "to": b["end"],
                      "kind": "孤立口水词", "text": b["text"][:20], "why": f["why"]})

    # 同一块命中多类 → 合并，取最强理由
    by_block = {}
    for d in drops:
        if d["block"] in by_block:
            old = by_block[d["block"]]
            old["kinds"] = old.get("kinds", [old["kind"]]) + [d["kind"]]
            old["why"] += "；" + d["why"]
        else:
            d = dict(d)
            d["kinds"] = [d["kind"]]
            by_block[d["block"]] = d
    drop_blocks = sorted(by_block)
    drops = [by_block[i] for i in drop_blocks]

    # ---- 保留顺序（默认保序，可重排）----
    n = len(blocks)
    alive = [i for i in range(n) if i not in drop_blocks]
    if args.reorder:
        order = [int(x) - 1 for x in args.reorder.split(",") if x.strip()]
        if sorted(order) != alive:
            print("  [warn] --reorder 必须是**保留块**的完整排列，共 %d 个：%s（已忽略）"
                  % (len(alive), ",".join(str(i + 1) for i in alive)), file=sys.stderr)
            order = list(range(n))
    else:
        order = list(range(n))

    # ---- keep 区间：按「保留块 + 气口分配」构造 ----
    # 气口跟着块走，与顺序无关；重排只改变 keep 的排列。
    keep, head_gap, tail_gap = build_keep(blocks, order, drop_blocks, dur)
    keep_dur = sum(b - a for a, b in keep)

    # ---- 重排建议 ----
    reorder_suggestion = suggest_reorder(blocks, drop_blocks)

    plan = {
        "$schema": "mograph/cut-plan@2",
        "meta": {
            "source": os.path.basename(video),
            "duration": round(dur, 2),
            "silence_count": len(sil),
            "silence_total": round(sil_total, 2),
            "silence_pct": round(sil_total / dur * 100, 1),
            "sentences": len(sents),
            "blocks": n,
            "params": {"noise_db": args.noise_db, "silence_min": args.silence_min,
                       "block_gap": args.block_gap, "long_pause": args.long_pause,
                       "repeat_sim": args.repeat_sim, "repeat_gap": args.repeat_gap,
                       "fragment_len": args.fragment_len},
            "generated_by": "scripts/cut_plan.py v2.0.0",
        },
        "sentences": sents,
        "blocks": blocks,
        "gaps": {"before": [round(g, 2) for g in gap_before],
                 "after": [round(g, 2) for g in gap_after]},
        "drops": drops,
        "drop_blocks": drop_blocks,
        "untrusted_blocks": untrusted,
        "repeats_skipped": reps_skipped,
        "long_pauses": pauses,
        "order": order,
        "reorder_applied": bool(args.reorder),
        "reorder_suggestion": reorder_suggestion,
        "keep": keep,
        "stats": {
            "removed": round(dur - keep_dur, 2),
            "kept": round(keep_dur, 2),
            "kept_pct": round(keep_dur / dur * 100, 1),
            "cuts": len(drops),
            "long_pauses": len(pauses),
        },
    }
    print("[5/6] 诊断：%d 刀（重录 %d / 半截句 %d / 口水词 %d）· %d 处长停顿待收紧"
          % (len(drops), len(reps), len(frags), len(fillers), len(pauses)))
    print("[6/6] 计划：保留 %.2fs / %.2fs（%.1f%%），%d 段"
          % (keep_dur, dur, plan["stats"]["kept_pct"], len(keep)))
    return plan


def suggest_reorder(blocks, drop_blocks):
    """给一个「调片段位置」的候选方案 —— 只提建议，不自动执行。

    规则：短视频最稳的重排是「把成品展示提到最前当钩子」——
    先让人看到结果，再讲怎么做到的。71 号原片没有这么做（保持保序），
    但这是短平快口播里收益最高的一种重排。
    """
    alive = [i for i in range(len(blocks)) if i not in drop_blocks]
    demo = [i for i in alive if blocks[i]["role"] == "成品展示"]
    if not demo:
        return None
    first = demo[0]
    if alive.index(first) <= 1:
        return {"suggestion": "无需重排：成品展示已经在开头",
                "order": [i + 1 for i in alive], "reason": ""}
    new = [first] + [i for i in alive if i != first]
    return {
        "suggestion": "把第 %d 块（成品展示）提到最前做钩子" % (first + 1),
        "order": [i + 1 for i in new],
        "reason": "短视频先给结果再讲过程，完播率更高；原片是「先讲原理→再展示」，"
                  "改成「先展示→再拆解」点击意愿更强",
        "apply_cmd": "--reorder %s" % ",".join(str(i + 1) for i in new),
    }


def parse_ranges(spec, dur):
    """'0-5,20-40' → [[0,5],[20,40]]，超出片长自动截断。"""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = float(a), float(b)
        else:
            a = float(part); b = dur
        a = max(0.0, min(a, dur)); b = max(0.0, min(b, dur))
        if b > a:
            out.append([round(a, 2), round(b, 2)])
    return out


# ---------------------------------------------------------------- 执行

def apply_plan(video, keep, out_path):
    """按保留区间 trim + concat 出底片（视频与音频同时切，顺序即 keep 顺序）。"""
    if not keep:
        print("没有保留区间，拒绝执行", file=sys.stderr)
        return False
    # ffmpeg 的 `-t 0` 表示「不限时长」，零长段会把剩下的整片都吃进来。
    # 这里硬拦一道，别让一个算错的区间毁掉整条片子。
    bad = [i for i, (a, b) in enumerate(keep) if b - a < 0.05]
    if bad:
        print("保留区间里有 %d 段长度 < 0.05s（零长段会让 ffmpeg 吞掉整片），拒绝执行："
              % len(bad), file=sys.stderr)
        for i in bad[:5]:
            print("  段 %d: %.3f – %.3f" % (i, keep[i][0], keep[i][1]), file=sys.stderr)
        return False
    tmp = out_path + ".parts"
    os.makedirs(tmp, exist_ok=True)
    pieces = []
    for i, (a, b) in enumerate(keep):
        p = os.path.join(tmp, "p%03d.mp4" % i)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % a,
                        "-t", "%.3f" % (b - a), "-i", video,
                        "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", p], check=True)
        pieces.append(p)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for p in pieces:
            f.write("file '%s'\n" % os.path.abspath(p))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", out_path], check=True)
    print("底片已出：%s（%.2fs）" % (out_path, sum(b - a for a, b in keep)))
    return True


# ---------------------------------------------------------------- 报告

def render_markdown(plan, path):
    m, s = plan["meta"], plan["stats"]
    L = []
    L.append("# 语义删减计划 · %s" % m["source"])
    L.append("")
    L.append("> 原片 **%.2fs** → 计划保留 **%.2fs**（%.1f%%），共 **%d 刀**"
             % (m["duration"], s["kept"], s["kept_pct"], s["cuts"]))
    L.append("> 原片实测静音 %d 段 / 合计 %.2fs（占 %.1f%%）—— **一半时间是废话停顿**"
             % (m["silence_count"], m["silence_total"], m["silence_pct"]))
    L.append("> 转写 %d 句 / 切出 %d 个口播块" % (m["sentences"], m["blocks"]))
    L.append("")
    L.append("## 一、刀口清单（按时间序）")
    L.append("")
    L.append("| # | 原片区间 | 时长 | 类别 | 被删的原文 | 理由 |")
    L.append("|---|---|---|---|---|---|")
    for i, d in enumerate(plan["drops"], 1):
        L.append("| %d | %.2f – %.2f | %.2fs | %s | %s | %s |"
                 % (i, d["from"], d["to"], d["to"] - d["from"],
                    "/".join(d.get("kinds", [d["kind"]])),
                    (d.get("text") or "").replace("|", "/"), d["why"]))
    if not plan["drops"]:
        L.append("| — | — | — | — | — | 未检出语义问题，只做长停顿收紧 |")
    L.append("")
    rej = plan.get("repeats_skipped") or []
    if rej:
        L.append("### 文本被转写污染的块（%d 处，不作为删除依据）" % len(rej))
        L.append("")
        L.append("| 原片区间 | 时长 | 语速 | 转写文本 |")
        L.append("|---|---|---|---|")
        for h in rej:
            b = plan["blocks"][h["i"]]
            L.append("| %.2f – %.2f | %.2fs | %.0f 字/秒 | %s |"
                     % (b["start"], b["end"], b["end"] - b["start"], h.get("rate", 0),
                        (b["text"] or "").replace("|", "/")))
        L.append("")
        L.append("> 这些块的**语速爆表**（字数远超时长能承载的量），说明转写模型把上一句"
                 "贴到了这一段上。它们多半是真实内容（例如「点击。」「点进去之后。」），"
                 "拿它们的文本当删除依据会丢信息，所以排除。")
        L.append("")
    L.append("## 二、保留区间（可直接喂给 ffmpeg，顺序即成片顺序）")
    L.append("")
    L.append("```")
    L.append(",".join("%.2f-%.2f" % (a, b) for a, b in plan["keep"]))
    L.append("```")
    L.append("")
    if plan.get("long_pauses"):
        L.append("## 三、长停顿收紧（%d 处）" % len(plan["long_pauses"]))
        L.append("")
        L.append("| 原片区间 | 时长 | 处理 |")
        L.append("|---|---|---|")
        for p in plan["long_pauses"]:
            L.append("| %.2f – %.2f | %.2fs | %s |" % (p["from"], p["to"], p["dur"], p["why"]))
        L.append("")
    L.append("## 四、口播块全文（复核用）")
    L.append("")
    L.append("| # | 原片区间 | 角色 | 被删 | 原文 |")
    L.append("|---|---|---|---|---|")
    drop_set = set(plan["drop_blocks"])
    for i, b in enumerate(plan["blocks"], 1):
        L.append("| %d | %.2f–%.2f | %s | %s | %s |"
                 % (i, b["start"], b["end"], b["role"],
                    "**删**" if (i - 1) in drop_set else "留",
                    b["text"].replace("|", "/")))
    L.append("")
    sug = plan.get("reorder_suggestion")
    L.append("## 五、片段重排")
    L.append("")
    if plan.get("reorder_applied"):
        L.append("**已按 `--reorder` 重排**（原序 → 新序，1-based 块号）：")
        L.append("")
        L.append("```")
        L.append(" → ".join(str(i + 1) for i in range(len(plan["blocks"]))))
        L.append("```")
        L.append("```")
        L.append(" → ".join(str(i + 1) for i in plan["order"]))
        L.append("```")
        L.append("")
        L.append("> **气口跟着块走**：每块自带它原片前后的那点静音，搬到哪里就在哪里，"
                 "所以重排后的接缝仍是自然换气，不会出现跨了整段原片的怪停顿。")
        L.append("> 代价：**字幕时间轴全部失效**，重排后必须重做字幕与动效落位。")
    elif sug:
        L.append("**可用的重排方案（工具只给建议，不自动执行）**")
        L.append("")
        L.append("- 建议：%s" % sug["suggestion"])
        L.append("- 理由：%s" % sug["reason"])
        L.append("- 块号顺序：`%s`" % ",".join(str(x) for x in sug["order"]))
        L.append("- 执行：`python3 scripts/cut_plan.py --video %s --out plan.json %s`"
                 % (m["source"], sug["apply_cmd"]))
    else:
        L.append("无需重排。")
    L.append("")
    L.append("## 六、执行前必看")
    L.append("")
    L.append("- 刀口只是**候选**。先读第四节，确认每刀删掉的内容你认可，再 `--apply`。")
    L.append("- 刀口只落在实测静音区间或整块上，**不会切到半个字**。")
    L.append("- 长停顿不一定该删：句间的停顿是「换气」，全砍会让语速失真。本计划只把 "
             "**>%.1fs** 的停顿收紧到 %.1fs，短停顿原样保留。"
             % (m["params"]["long_pause"], 0.7))
    L.append("- 重录保留的是**最后一次**；若你更想用第一遍（通常更自然），改 `keep`。")
    L.append("- 本计划**默认不改变片段顺序**。要重排请显式写 `--reorder`，"
             "`--apply` 会按新顺序拼，气口跟着块走（不会重排成怪停顿）。")
    L.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("报告已出：%s" % path)


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="原始口播 → 语义删减计划")
    ap.add_argument("--video", required=True, help="原始口播视频")
    ap.add_argument("--out", default="cut-plan.json", help="计划 JSON 输出")
    ap.add_argument("--report", default=None, help="Markdown 报告输出（默认与 out 同名 .md）")
    ap.add_argument("--apply", default=None, help="按计划剪出底片，填目标路径")
    ap.add_argument("--keep", default=None,
                    help="手工指定保留段，如 '0-5,20-40'；给了就覆盖自动结果")
    ap.add_argument("--reorder", default=None,
                    help="片段重排，如 '3,1,2,4,5'（1-based 块号，必须是完整排列）")
    ap.add_argument("--no-asr", action="store_true", help="跳过转写，只做静音诊断")
    ap.add_argument("--asr-model", default="mlx-community/whisper-base-mlx")
    ap.add_argument("--audio", default=None, help="复用已有的 16k wav（省一次抽音）")
    ap.add_argument("--work", default=".cutwork", help="中间文件目录")
    ap.add_argument("--noise-db", type=int, default=SILENCE_NOISE_DB)
    ap.add_argument("--silence-min", type=float, default=SILENCE_MIN_DUR)
    ap.add_argument("--long-pause", type=float, default=LONG_PAUSE)
    ap.add_argument("--repeat-sim", type=float, default=REPEAT_SIM)
    ap.add_argument("--repeat-gap", type=float, default=REPEAT_GAP)
    ap.add_argument("--block-gap", type=float, default=BLOCK_GAP)
    ap.add_argument("--fragment-len", type=int, default=FRAGMENT_MAX_LEN)
    ap.add_argument("--rate-max", type=float, default=SPEECH_RATE_MAX,
                    help="语速上限（字/秒），超过即判定转写文本被污染，不作删除依据")
    args = ap.parse_args()

    plan = build_plan(args.video, args)
    if plan is None:
        sys.exit(1)

    if args.keep:
        plan["keep"] = parse_ranges(args.keep, plan["meta"]["duration"])
        plan["stats"]["kept"] = round(sum(b - a for a, b in plan["keep"]), 2)
        plan["stats"]["removed"] = round(plan["meta"]["duration"] - plan["stats"]["kept"], 2)
        plan["stats"]["kept_pct"] = round(plan["stats"]["kept"] / plan["meta"]["duration"] * 100, 1)
        plan["manual_keep"] = True

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print("计划已出：%s" % args.out)

    report = args.report or os.path.splitext(args.out)[0] + ".md"
    render_markdown(plan, report)

    if args.apply:
        apply_plan(args.video, plan["keep"], args.apply)


if __name__ == "__main__":
    main()
