#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线扫口播稿 / SRT，列出「口播里点名的品牌」候选 · mograph-pro Step A2-2

用途
----
口播里提到某个品牌（GLM / MiniMax / WorkBuddy / Hy4-Flash / 腾讯云…）时，
要先知道「这段话里到底点了哪些品牌」，才能去取这些品牌的官方 logo 用进成片。

本脚本只做**离线候选识别**：不联网、不判断 logo 对不对、不下载任何东西。
它把「像品牌的名词」按可信度排出来，**由执行 Agent 判断哪些是真品牌**，
再交给 `brand_logo.py` 去取官方件。

用法
----
    # ① 扫口播稿（Markdown / txt）
    python3 scripts/brand_scan.py --script 口播稿.md

    # ② 扫字幕 SRT
    python3 scripts/brand_scan.py --srt 字幕.srt

    # ③ 落盘 Markdown 表 + 顺带标出本地已有的 logo
    python3 scripts/brand_scan.py --script 口播稿.md --out 品牌候选.md \
        --assets-dir "<选题>/mograph-task/assets/logos"

    # ④ 中文品牌名没加引号、扫不出来时手工补
    python3 scripts/brand_scan.py --script 口播稿.md --add 腾讯云 --add 通义千问

    # ⑤ 要 JSON（给下游脚本用）
    python3 scripts/brand_scan.py --script 口播稿.md --json

退出码
------
    0 正常（哪怕一个候选都没有）｜2 参数/用法错｜3 输入读不出或为空
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 停用通用词
# 这些词长得像品牌名（首字母大写 / 全大写 / 纯英文），但口播里不是在说品牌。
STOP_EN = {
    # 通用名词
    "app", "apps", "api", "apis", "ai", "ml", "llm", "url", "urls", "id", "ids",
    "video", "videos", "clip", "clips", "audio", "image", "images", "picture",
    "pictures", "photo", "photos", "screenshot", "screenshots", "data", "code",
    "codes", "model", "models", "tool", "tools", "plugin", "plugins", "template",
    "templates", "file", "files", "step", "steps", "demo", "demos", "doc",
    "docs", "document", "documents", "note", "notes", "tip", "tips", "case",
    "cases", "example", "examples", "feature", "features", "list", "task",
    "tasks", "project", "projects", "team", "teams", "work", "works", "workflow",
    "workflows", "software", "hardware", "product", "products", "service",
    "services", "server", "servers", "cloud", "web", "website", "websites",
    "site", "sites", "blog", "source", "sources", "codebase", "script", "scripts",
    # 常用动词 / 形容词 / 副词
    "use", "used", "using", "make", "made", "making", "get", "got", "new", "old",
    "first", "second", "third", "next", "last", "more", "most", "best", "better",
    "free", "plus", "lite", "basic", "full", "auto", "quick", "fast", "easy",
    "simple", "deep", "real", "live", "true", "false", "open", "close", "start",
    "stop", "run", "runs", "running", "build", "builds", "building", "create",
    "creates", "creating", "add", "adds", "adding", "set", "sets", "setting",
    "all", "any", "can", "will", "just", "also", "very", "much", "many", "some",
    "one", "two", "three", "four", "five", "here", "there", "when", "where",
    "what", "which", "who", "how", "why", "yes", "no", "ok", "okay", "let",
    "let", "because", "but", "and", "for", "with", "from", "into", "about",
    "after", "before", "over", "under", "than", "then", "now", "today", "time",
    "times", "way", "ways", "thing", "things", "people", "user", "users",
    # 技术通用词（说的时候不是在说某个产品）
    "python", "java", "golang", "rust", "node", "npm", "pip", "git", "github",
    "gitlab", "docker", "k8s", "css", "html", "json", "yaml", "toml", "csv",
    "xml", "sql", "http", "https", "tcp", "udp", "pdf", "mp4", "mov", "mp3",
    "wav", "srt", "png", "jpg", "jpeg", "gif", "svg", "webp", "zip", "tar",
    "md", "txt", "api-key", "token", "prompt", "prompts", "agent", "agents",
    "workflow-engine", "config", "configs", "environment", "runtime",
    # 视频剪辑领域通用词
    "video-editor", "editor", "editors", "editing", "edit", "edits", "clipping",
    "subtitle", "subtitles", "caption", "captions", "frame", "frames", "fps",
    "hd", "uhd", "4k", "1080p", "ms", "mb", "gb", "tb", "sec", "second",
    "seconds", "minute", "minutes", "minute-long",
}

STOP_ZH = {
    "视频", "画面", "剪辑", "模板", "插件", "数据", "模型", "视频号", "小红书",
    "公众号", "封面", "字幕", "配图", "动效", "场景", "步骤", "品牌", "产品",
    "工具", "软件", "平台", "系统", "项目", "版本", "官网", "官方", "功能",
    "效果", "内容", "素材", "片段", "节奏", "文案", "脚本", "接口", "方案",
}

# 出现在这些词附近，多半是真的在「用 / 提」一个品牌
TRIGGER_WORDS = [
    "用", "使用", "用了", "用上", "打开", "装", "装个", "搜", "搜索", "查",
    "基于", "切到", "切换到", "换成", "接入", "调用", "跑", "跑一下", "支持",
    "推荐", "提到", "介绍", "对比", "下载", "登录", "部署", "安装", "换成",
    "选", "选择", "用起", "接到", "接进", "换成", "套用", "改用",
]

# 品牌名后面跟这些词，多半是「XX 的官网 / XX 的 logo / XX 模型」
TAIL_WORDS = [
    "的", "官网", "官方", "logo", "Logo", "LOGO", "logo 文件", "里", "中",
    "API", "版本", "模型", "账号", "社区", "教程",
]

# ---------------------------------------------------------------- 识别规则
QUOTE_PATTERNS = [
    re.compile(r"[「『【]([^」』】]{1,24})[」』】]"),
    re.compile(r'"([^"\n]{1,24})"'),
    re.compile(r"'([^'\n]{1,24})'"),
]
LATIN_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[.\-_][A-Za-z0-9]+)*")
SENT_SPLIT = re.compile(r"(?<=[。！？!?；;\n])")


def normalize(name):
    """归一化品牌名：去空格 / 连字符 / 下划线 / 点，用于比较与匹配本地文件。"""
    return re.sub(r"[\s\-_.]+", "", name).lower()


def is_product_shape(tok):
    """产品名形态：含数字 / 含连字符点 / 驼峰 / 全大写。"""
    if re.search(r"\d", tok):
        return True
    if re.search(r"[.\-_]", tok):
        return True
    if len(tok) > 2 and any(c.isupper() for c in tok[1:]):
        return True
    if len(tok) >= 2 and tok.isupper():
        return True
    return False


def latin_candidates(sentence):
    """从一句里抽拉丁字母形态的产品名候选。

    相邻的两个首字母大写词（中间只有空格 / 连字符）才合并成词组；
    中间隔了中文或别的词就不合（否则「用「GLM」跑分镜，MiniMax」会被并成 "GLM MiniMax"）。
    """
    out = []
    toks = [(m.group(0), m.start(), m.end()) for m in LATIN_TOKEN.finditer(sentence)]
    i = 0
    while i < len(toks):
        tok, s0, e0 = toks[i]
        if tok.lower() in STOP_EN:
            i += 1
            continue
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        pair = None
        if nxt is not None:
            ntok, ns0, ne0 = nxt
            gap = sentence[e0:ns0]
            adjacent = re.fullmatch(r"[\s·\-—/]?", gap) is not None
            if (adjacent
                    and tok[:1].isupper() and tok.isalpha() and len(tok) >= 2
                    and ntok[:1].isupper() and ntok.isalpha() and len(ntok) >= 2
                    and tok.lower() not in STOP_EN and ntok.lower() not in STOP_EN):
                pair = tok + " " + ntok
        if pair:
            out.append(pair)
            i += 2
            continue
        shape = is_product_shape(tok)
        cap = tok[:1].isupper() and tok[1:].isalpha() and len(tok) >= 3
        if shape or cap:
            out.append(tok)
        i += 1
    return out


def quoted_candidates(sentence):
    out = []
    for pat in QUOTE_PATTERNS:
        for m in pat.finditer(sentence):
            out.append((m.group(1).strip(), m.start()))
    return out


def ctx_score(sentence, name):
    """上下文打分：紧邻动词 / 后面跟「的、官网、logo」等 → 更像真品牌。"""
    score = 0
    reasons = []
    idx = sentence.find(name)
    if idx < 0:
        return score, reasons
    left = sentence[max(0, idx - 8):idx]
    for w in TRIGGER_WORDS:
        if w in left:
            score += 2
            reasons.append("紧邻动词「%s」" % w)
            break
    right = sentence[idx + len(name):idx + len(name) + 8]
    for w in TAIL_WORDS:
        if right.startswith(w):
            score += 2
            reasons.append("后接「%s」" % w)
            break
    return score, reasons


def load_text(args):
    """读入正文；SRT 只取文本行（去掉序号与时间轴）。"""
    chunks = []
    sources = []
    if args.script:
        sources.append(args.script)
        chunks.append(read_plain(args.script))
    if args.srt:
        sources.append(args.srt)
        chunks.append(read_srt(args.srt))
    if args.text:
        sources.append("<命令行文本>")
        chunks.append(args.text)
    return sources, "\n".join(chunks)


def read_plain(path):
    p = Path(path)
    if not p.is_file():
        fatal(3, "读不到文件：%s" % path)
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        fatal(3, "读取失败：%s（%s）" % (path, e))


def read_srt(path):
    p = Path(path)
    if not p.is_file():
        fatal(3, "读不到字幕文件：%s" % path)
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        fatal(3, "读取失败：%s（%s）" % (path, e))
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or "-->" in s or s.isdigit():
            continue
        lines.append(s)
    return "\n".join(lines)


def fatal(code, msg):
    """出错退出：写 stderr 后带退出码退出。"""
    sys.stderr.write("[brand_scan] %s\n" % msg)
    raise SystemExit(code)


def collect(text, extra_names):
    """返回候选列表。"""
    hits = {}  # name -> dict

    def touch(name):
        return hits.setdefault(name, {"name": name, "count": 0, "quoted": False,
                                     "ctx": 0, "reasons": [], "first": 0,
                                     "first_text": "", "shape": False})

    sentences = [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]
    for si, sent in enumerate(sentences, start=1):
        quoted_names = set()
        for name, _pos in quoted_candidates(sent):
            if not name or name.lower() in STOP_EN or name in STOP_ZH:
                continue
            if not re.search(r"[A-Za-z一-鿿0-9]", name):
                continue
            quoted_names.add(name)
            rec = touch(name)
            rec["count"] += 1
            rec["quoted"] = True
            if not rec["first_text"]:
                rec["first"] = si
                rec["first_text"] = sent
            if "被引号包裹" not in rec["reasons"]:
                rec["reasons"].append("被引号包裹")
            sc, rs = ctx_score(sent, name)
            if sc > rec["ctx"]:
                rec["ctx"] = sc
                for r in rs:
                    if r not in rec["reasons"]:
                        rec["reasons"].append(r)

        for name in latin_candidates(sent):
            if not name or name.lower() in STOP_EN:
                continue
            if name in quoted_names:
                continue          # 同一句里已被引号计过，不重复计数
            rec = touch(name)
            rec["count"] += 1
            if is_product_shape(name.replace(" ", "")):
                rec["shape"] = True
            if not rec["first_text"]:
                rec["first"] = si
                rec["first_text"] = sent
            sc, rs = ctx_score(sent, name)
            if sc > rec["ctx"]:
                rec["ctx"] = sc
                for r in rs:
                    if r not in rec["reasons"]:
                        rec["reasons"].append(r)

    for name in extra_names:
        name = name.strip()
        if not name:
            continue
        rec = touch(name)
        rec["count"] += 1
        rec["manual"] = True
        if "手工指定" not in rec["reasons"]:
            rec["reasons"].append("手工指定")
        if not rec["first_text"]:
            rec["first"] = 0
            rec["first_text"] = "（--add 手工补入）"

    out = []
    for rec in hits.values():
        score = rec["ctx"]
        reasons = list(rec["reasons"])
        if rec["quoted"]:
            score += 3
            if re.search(r"[一-鿿]", rec["name"]):
                score += 1          # 引号里的中文名是很强的信号
        if rec["shape"]:
            score += 3
            if "产品名形态（数字 / 连字符 / 驼峰）" not in reasons:
                reasons.append("产品名形态（数字 / 连字符 / 驼峰）")
        if rec["count"] >= 2:
            score += 2
            if "出现多次" not in reasons:
                reasons.append("出现多次")
        if rec["first"] == 1:
            score += 1
            if "句首首次出现" not in reasons:
                reasons.append("句首首次出现")
        if rec.get("manual"):
            score = max(score, 5)  # 人工点名的直接进候选，不被阈值滤掉
        conf = "high" if score >= 7 else ("mid" if score >= 4 else "low")
        out.append({
            "name": rec["name"],
            "count": rec["count"],
            "first_sentence": rec["first"],
            "first_text": rec["first_text"],
            "score": score,
            "confidence": conf,
            "reasons": reasons,
            "manual": bool(rec.get("manual")),
            "local_logo": "",
        })
    out.sort(key=lambda r: (-r["score"], -r["count"], r["name"]))
    return out, len(sentences)


def find_local(name, assets_dir):
    """在本地素材目录里找同名 logo 文件。"""
    if not assets_dir:
        return ""
    d = Path(assets_dir)
    if not d.is_dir():
        return ""
    key = normalize(name)
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        if normalize(p.stem) == key or key in normalize(p.stem):
            return str(p)
    return ""


def to_markdown(cands, sources, sentence_count):
    lines = []
    lines.append("# 品牌候选（口播点名扫描 · brand_scan.py）")
    lines.append("")
    lines.append("- 输入：%s" % ("、".join(sources) or "（无）"))
    lines.append("- 句子数：%d" % sentence_count)
    lines.append("- 候选数：%d" % len(cands))
    lines.append("")
    if not cands:
        lines.append("**没有扫到候选。** 中文品牌名不加引号时扫不出来，用 `--add` 手工补。")
        return "\n".join(lines) + "\n"
    lines.append("| 品牌 | 次数 | 首现句 | 置信度 | 判据 | 本地已有 logo |")
    lines.append("|---|---|---|---|---|---|")
    for c in cands:
        lines.append("| %s | %d | 第 %s 句 | %s | %s | %s |" % (
            c["name"], c["count"],
            c["first_sentence"] if c["first_sentence"] else "-",
            {"high": "高", "mid": "中", "low": "低"}[c["confidence"]],
            "；".join(c["reasons"]) or "-",
            c["local_logo"] or "无"))
    lines.append("")
    lines.append("> 置信度只代表「像不像品牌名」，**不代表 logo 找对了**。"
                 "取件后仍要过三关：① 是这个品牌 ② 官方源 ③ 同一版本（`references/brand-logo.md` §3）。")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="离线扫口播稿 / SRT，列出点名的品牌候选（不联网、不下载）")
    ap.add_argument("--script", help="口播稿路径（.md / .txt）")
    ap.add_argument("--srt", help="字幕文件路径（.srt）")
    ap.add_argument("--text", help="直接给一段文字（不用文件）")
    ap.add_argument("--out", help="把 Markdown 表写到该文件")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而不是 Markdown")
    ap.add_argument("--assets-dir", help="本地 logo 目录，用来标「本地已有」")
    ap.add_argument("--add", action="append", default=[],
                    help="手工补一个品牌候选（可重复），中文品牌名靠它")
    ap.add_argument("--min-score", type=int, default=3,
                    help="最低分，低于此分不输出（默认 3）")
    args = ap.parse_args()

    if not (args.script or args.srt or args.text):
        ap.error("至少给一个输入：--script / --srt / --text")

    sources, text = load_text(args)
    if not text.strip():
        fatal(3, "输入是空的，没有可扫的内容")

    cands, sentence_count = collect(text, args.add)
    cands = [c for c in cands
             if c["score"] >= args.min_score or c.get("manual")]
    for c in cands:
        c["local_logo"] = find_local(c["name"], args.assets_dir)

    md = to_markdown(cands, sources, sentence_count)

    if args.json:
        payload = {
            "sources": sources,
            "sentences": sentence_count,
            "min_score": args.min_score,
            "candidates": cands,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(md, end="")

    if args.out:
        try:
            p = Path(args.out)
            if p.parent and str(p.parent):
                p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(md, encoding="utf-8")
        except OSError as e:
            fatal(5, "写文件失败：%s（%s）" % (args.out, e))


if __name__ == "__main__":
    main()
