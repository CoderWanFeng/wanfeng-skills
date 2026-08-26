#!/usr/bin/env python3
"""
fetch_hot.py · 自媒体选题雷达 · 多平台热搜聚合 + 关键词过滤 + 记忆去重

⚠️ 当前状态：占位实现（v0.1）。各平台抓取 handler 待补全。
   框架已就位：配置加载 → 多平台抓取 → 归一化 → 关键词打分 → 记忆去重 → 排序输出。

用法：
    python scripts/fetch_hot.py                     # 跑今天
    python scripts/fetch_hot.py --date 2026-07-10   # 指定日期
    python scripts/fetch_hot.py --stdout             # 只打印候选清单，不写文件
    python scripts/fetch_hot.py --with-competitors  # 启用竞品监控
    python scripts/fetch_hot.py --clear-memory       # 清空去重记忆
    python scripts/fetch_hot.py --config /path/to/radar-config.yaml

依赖：
    pip install pyyaml rapidfuzz
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import socket
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:
    sys.stderr.write("[ERROR] 缺少 PyYAML。请先执行：pip install pyyaml\n")
    sys.exit(2)

try:
    from rapidfuzz import fuzz
except ImportError:
    sys.stderr.write("[ERROR] 缺少 rapidfuzz。请先执行：pip install rapidfuzz\n")
    sys.exit(2)


# ---------- 常量 ----------
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parent / "radar-config.yaml"
EXAMPLE_CONFIG = SCRIPT_DIR.parent / "radar-config.example.yaml"

DEFAULT_PLATFORM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


# ---------- 配置 ----------
def load_config(path: Path) -> dict:
    """加载 YAML 配置，未提供字段用默认值补齐。"""
    if not path.exists():
        if EXAMPLE_CONFIG.exists():
            sys.stderr.write(
                f"[ERROR] 配置文件不存在：{path}\n"
                f"        可参考模板：{EXAMPLE_CONFIG}\n"
                f"        复制后修改：cp {EXAMPLE_CONFIG} {path}\n"
            )
        else:
            sys.stderr.write(f"[ERROR] 配置文件不存在：{path}\n")
        sys.exit(2)

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    defaults = {
        "timezone": "Asia/Shanghai",
        "lookback_hours": 24,
        "top_n": 10,
        "keywords": [],
        "exclude_keywords": [],
        "platforms": [],
        "weights": {"hotness": 0.6, "relevance": 0.4},
        "dedup": {
            "enabled": True,
            "window_days": 7,
            "memory_file": "memory/dedup-history.jsonl",
        },
        "competitor_monitor": {"enabled": False, "accounts": [], "platform": "xiaohongshu"},
        "paths": {
            "project_root": ".",
            "output_dir": "workflow/每日热点/",
            "memory_dir": "memory/",
        },
    }
    return _deep_merge(defaults, cfg)


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并 dict，override 优先级高。"""
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# ---------- 网络 ----------
def _available_encodings() -> str:
    """根据已安装的解压库返回可处理的 Accept-Encoding 值。

    gzip/deflate 由标准库支持，brotli 需第三方包；
    未装 brotli 时不再声明 br，避免服务器返回 br 却无法解压。
    """
    encs = ["gzip", "deflate"]
    try:
        import brotli  # noqa: F401
        encs.append("br")
    except ImportError:
        pass
    return ", ".join(encs)


def safe_decode(raw: bytes) -> str:
    """对原始字节做多编码兜底解码，优先 utf-8。

    网络响应偶发声明与实际不符或解压残留，逐个尝试常见中文编码，
    全部失败时用 replace 兜底，保证下游 json.loads 不抛 UnicodeDecodeError。
    """
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def http_get(url: str, headers: dict | None = None, timeout: int = 20) -> bytes:
    """带重试 + 自动解压的 HTTP GET。

    Accept-Encoding 按已安装的解压库动态声明，防止声明了 br 却解不开；
    返回未解码的原始字节，调用方用 safe_decode 兜底解码后再 json.loads。
    """
    ssl_ctx = ssl.create_default_context()
    req_headers = {**DEFAULT_PLATFORM_HEADERS, **(headers or {})}
    # 调用方未显式指定编码时，按本机能力动态声明，避免 br 解压失败
    if not (headers and headers.get("Accept-Encoding")):
        req_headers["Accept-Encoding"] = _available_encodings()
    req = urllib.request.Request(url, headers=req_headers)
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as r:
                raw = r.read()
                enc = r.headers.get("Content-Encoding", "").lower()
                if enc == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                elif enc == "deflate":
                    import zlib
                    raw = zlib.decompress(raw)
                elif enc == "br":
                    try:
                        import brotli
                        raw = brotli.decompress(raw)
                    except ImportError:
                        # 理论不会走到这里（未声明 br），兜底：原样返回
                        pass
                return raw
        except (socket.timeout, ssl.SSLError, ConnectionError) as e:
            last_err = e
            sys.stderr.write(f"[WARN] {url} 请求失败（{attempt + 1}/3）：{e}\n")
            continue
    raise RuntimeError(f"{url} 连续 3 次失败：{last_err}")


# ---------- 平台抓取 ----------
# 已实现：weibo / toutiao / baidu / zhihu / bilibili
# 待实现：douyin（_signature 反爬） / xiaohongshu（风控严）

def fetch_baidu(cfg: dict) -> list[dict]:
    """
    百度热搜（实时榜）。
    接口：https://top.baidu.com/api/board?platform=wise&tab=realtime
    数据（双重嵌套）：
      data.cards[].content[] = [{content: [{word, desc, url, index, ...}]}]
      需向下钻一层取真正的条目。
    """
    url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
    raw = http_get(url, headers={"Referer": "https://top.baidu.com/"})
    payload = json.loads(raw)
    items: list[dict] = []
    for card in payload.get("data", {}).get("cards", []):
        for wrapper in card.get("content", []):
            # 兼容双重嵌套：wrapper.content[] 是真正的条目
            entries = wrapper.get("content", wrapper) if isinstance(wrapper, dict) else wrapper
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                title = (entry.get("word") or "").strip()
                if not title:
                    continue
                # isTop 的条目无 index，用 0 占位
                rank_raw = entry.get("index")
                if rank_raw is None or entry.get("isTop"):
                    rank = 0
                else:
                    try:
                        rank = int(rank_raw)
                    except (ValueError, TypeError):
                        rank = 999
                # hotTag / newHotName 当热度参考
                hot = 0
                try:
                    hot = int(entry.get("hotScore", 0) or 0)
                except (ValueError, TypeError):
                    pass
                items.append(
                    {
                        "title": title,
                        "url": entry.get("url", ""),
                        "rank": rank,
                        "hot": hot,
                        "timestamp": entry.get("showDate", ""),
                        "desc": (entry.get("desc") or "").strip(),
                    }
                )
    return items


def fetch_toutiao(cfg: dict) -> list[dict]:
    """
    今日头条热榜。
    接口：https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc
    数据：data[] = [{Title, Url, HotValue, Label, QueryWord}]
    """
    url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
    raw = http_get(url, headers={"Referer": "https://www.toutiao.com/"})
    payload = json.loads(raw)
    items: list[dict] = []
    for idx, entry in enumerate(payload.get("data", []), 1):
        title = (entry.get("Title") or "").strip()
        if not title:
            continue
        items.append(
            {
                "title": title,
                "url": entry.get("Url", ""),
                "rank": idx,
                "hot": int(entry.get("HotValue", 0) or 0),
                "timestamp": str(entry.get("PublishTime", "") or ""),
                "label": entry.get("Label", ""),
            }
        )
    return items


def fetch_weibo(cfg: dict) -> list[dict]:
    """
    微博热搜榜。
    接口：https://weibo.com/ajax/side/hotSearch
    数据：data.realtime[] = [{word, note, num, realpos, label_name}]
    """
    url = "https://weibo.com/ajax/side/hotSearch"
    raw = http_get(url, headers={"Referer": "https://weibo.com/"})
    payload = json.loads(raw)
    items: list[dict] = []
    for entry in payload.get("data", {}).get("realtime", []):
        title = (entry.get("word") or "").strip()
        if not title:
            continue
        items.append(
            {
                "title": title,
                "url": f"https://s.weibo.com/weibo?q=%23{urllib.parse.quote(title)}%23",
                "rank": int(entry.get("realpos", 999) or entry.get("rank", 999) or 999),
                "hot": int(entry.get("num", 0) or 0),
                "timestamp": "",
                "label": entry.get("label_name", "") or entry.get("icon_desc", ""),
            }
        )
    return items


# ---------- 暂未实现的平台 ----------
def fetch_douyin(cfg: dict) -> list[dict]:
    """抖音热点榜。⚠️ 待实现：需绕过 _signature 反爬，建议用第三方聚合。"""
    return []


def fetch_zhihu(cfg: dict) -> list[dict]:
    """
    知乎热榜。
    接口：https://api.zhihu.com/topstory/hot-list?limit=50&reverse_order=0
    数据：data[] = [{target: {title, excerpt, url, id}, detail_text, ...}]

    说明：网页版 https://www.zhihu.com/billboard 需登录态，
          但移动端 api.zhihu.com 公开可调，无需 cookie；Referer 带 web 域即可。
    """
    url = "https://api.zhihu.com/topstory/hot-list?limit=50&reverse_order=0"
    raw = http_get(url, headers={"Referer": "https://www.zhihu.com/hot"})
    payload = json.loads(safe_decode(raw))
    items: list[dict] = []
    for idx, entry in enumerate(payload.get("data", []), 1):
        target = entry.get("target", {}) or {}
        title = (target.get("title") or "").strip()
        if not title:
            continue
        # detail_text 形如 "1234 万热度"，非整数时置 0
        detail = entry.get("detail_text", 0)
        hot = int(detail) if isinstance(detail, int) else 0
        qid = target.get("id", "")
        items.append(
            {
                "title": title,
                "url": target.get("url", "") or f"https://www.zhihu.com/question/{qid}",
                "rank": idx,
                "hot": hot,
                "timestamp": "",
                "excerpt": (target.get("excerpt") or "").strip(),
            }
        )
    return items


def fetch_xiaohongshu(cfg: dict) -> list[dict]:
    """小红书热门。⚠️ 待实现：风控严，建议用第三方聚合。"""
    return []


def fetch_bilibili(cfg: dict) -> list[dict]:
    """
    B 站热搜。
    接口：https://app.bilibili.com/x/v2/search/trending/ranking?limit=50
    数据：data.list[] = [{keyword, show_name, hot_score, ...}]

    说明：网页端 API 有 -352 风控需带 cookie，
          APP 端 app.bilibili.com 公开可调，无需 cookie。
    """
    url = "https://app.bilibili.com/x/v2/search/trending/ranking?limit=50"
    raw = http_get(url, headers={"Referer": "https://www.bilibili.com/"})
    payload = json.loads(safe_decode(raw))
    items: list[dict] = []
    for idx, entry in enumerate(payload.get("data", {}).get("list", []) or [], 1):
        # keyword 为主标题，缺时回退 show_name
        title = (entry.get("keyword") or entry.get("show_name") or "").strip()
        if not title:
            continue
        items.append(
            {
                "title": title,
                "url": "https://search.bilibili.com/all?keyword=" + urllib.parse.quote(title),
                "rank": idx,
                "hot": int(entry.get("hot_score", 0) or 0),
                "timestamp": "",
            }
        )
    return items


PLATFORM_HANDLERS = {
    "weibo": fetch_weibo,
    "douyin": fetch_douyin,
    "zhihu": fetch_zhihu,
    "xiaohongshu": fetch_xiaohongshu,
    "bilibili": fetch_bilibili,
    "toutiao": fetch_toutiao,
    "baidu": fetch_baidu,
}


def fetch_all(cfg: dict) -> list[dict]:
    """按 cfg.platforms 分发抓取。"""
    results: list[dict] = []
    for platform in cfg["platforms"]:
        handler = PLATFORM_HANDLERS.get(platform)
        if not handler:
            sys.stderr.write(f"[WARN] 未知平台：{platform}，跳过\n")
            continue
        try:
            items = handler(cfg)
            sys.stdout.write(f"[INFO] {platform}: {len(items)} 条\n")
            for item in items:
                item["platform"] = platform
            results.extend(items)
        except Exception as e:
            sys.stderr.write(f"[ERROR] {platform} 抓取失败：{e}\n")
    return results


# ---------- 归一化 ----------
def normalize(item: dict) -> dict:
    """统一 schema。"""
    return {
        "platform": item.get("platform", "unknown"),
        "title": (item.get("title") or "").strip(),
        "url": item.get("url", ""),
        "hot_raw": int(item.get("hot", 0) or 0),
        "rank": int(item.get("rank", 999) or 999),
        "timestamp": item.get("timestamp", ""),
    }


# ---------- 关键词打分 ----------
def relevance_score(title: str, keywords: list[str], exclude: list[str]) -> float:
    """相关度 0-1。命中排除关键词直接 0。"""
    t = title.lower()
    for ex in exclude:
        if ex.lower() in t:
            return 0.0
    score = 0.0
    for kw in keywords:
        if kw.lower() in t:
            score += 0.25
    return min(score, 1.0)


def hotness_score(rank: int, hot_raw: int) -> float:
    """热度 0-1。rank 越小越高；hot_raw 兜底用对数衰减。"""
    if rank <= 1:
        return 1.0
    if rank <= 10:
        return 1.0 - (rank - 1) * 0.05      # 1.0 → 0.55
    if rank <= 50:
        return 0.5 - (rank - 10) * 0.01     # 0.5 → 0.1
    if hot_raw > 0:
        import math
        return max(0.1, 1.0 - math.log10(hot_raw) / 5.0)
    return 0.1


def final_score(item: dict, weights: dict, keywords: list[str], exclude: list[str]) -> float:
    h = hotness_score(item["rank"], item["hot_raw"])
    r = relevance_score(item["title"], keywords, exclude)
    return round(h * weights["hotness"] + r * weights["relevance"], 3)


# ---------- 记忆去重 ----------
def load_dedup_history(memory_file: Path, window_days: int) -> list[str]:
    """加载 N 天内的历史标题列表。"""
    if not memory_file.exists():
        return []
    cutoff = datetime.now() - timedelta(days=window_days)
    titles: list[str] = []
    with memory_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pushed = rec.get("pushed_at", "")
            if not pushed:
                continue
            try:
                pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            except ValueError:
                continue
            if pushed_dt.replace(tzinfo=None) >= cutoff:
                titles.append(rec.get("title", ""))
    return titles


def is_dup(title: str, history: list[str], threshold: int = 85) -> bool:
    if not title:
        return False
    for prev in history:
        if fuzz.ratio(title, prev) >= threshold:
            return True
    return False


def append_dedup_history(memory_file: Path, items: list[dict]) -> None:
    """追加推送记录。"""
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")
    with memory_file.open("a", encoding="utf-8") as f:
        for item in items:
            rec = {
                "title": item["title"],
                "platform": item["platform"],
                "url": item["url"],
                "pushed_at": now,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def clear_memory(memory_file: Path) -> None:
    if memory_file.exists():
        memory_file.unlink()
        sys.stdout.write(f"[INFO] 已清空记忆：{memory_file}\n")


# ---------- 输出 ----------
def render_output(items: list[dict], cfg: dict, target_date) -> str:
    """生成 Markdown 候选清单。"""
    date_str = target_date.strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    keywords = cfg["keywords"]
    exclude = cfg["exclude_keywords"]

    out = [
        "---",
        f"title: 每日选题候选 · {date_str}",
        f"date: {date_str} {time_str}",
        "tags: [每日选题, 自媒体, 内部文档]",
        "categories: [工作流程, 选题雷达]",
        f"description: 选题雷达 {date_str} 自动汇总，共 {len(items)} 条候选",
        "---",
        "",
        f"# 每日选题候选 · {date_str}",
        "",
        f"> 自动生成于 {date_str} {time_str}",
        f"> 关键词：{' / '.join(keywords) if keywords else '（无）'}",
        f"> 排除：{' / '.join(exclude) if exclude else '（无）'}",
        f"> TOP N：{len(items)}",
        "",
    ]

    for idx, item in enumerate(items, 1):
        out.append(f"## {idx}. {item['title']}")
        out.append("")
        out.append(f"- **平台**：{item['platform']}")
        out.append(f"- **发布时间**：{item.get('timestamp', '-')}")
        out.append(f"- **热度分**：{item.get('hotness', 0):.2f}")
        out.append(f"- **相关度**：{item.get('relevance', 0):.2f}")
        out.append(f"- **综合分**：{item.get('final_score', 0):.3f}")
        if item.get("url"):
            out.append(f"- **链接**：{item['url']}")
        out.append("")

    out.append(f"> 本次采集候选 {len(items)} 条")
    out.append("")
    return "\n".join(out)


def print_console(items: list[dict]) -> None:
    """控制台友好打印。"""
    sep = "=" * 60
    sys.stdout.write(f"\n{sep}\n")
    sys.stdout.write(f"今日选题候选（TOP {len(items)}）\n")
    sys.stdout.write(f"{sep}\n")
    for idx, item in enumerate(items, 1):
        sys.stdout.write(
            f"[{item['final_score']:.1f}] {item['platform']} / {item.get('timestamp', '-')}\n"
        )
        sys.stdout.write(f"  「{item['title']}」\n")
        if item.get("url"):
            sys.stdout.write(f"  → {item['url']}\n")
        sys.stdout.write("\n")
    sys.stdout.write(f"{sep}\n")


# ---------- 主流程 ----------
def resolve_project_root(cfg: dict) -> Path:
    root = Path(cfg["paths"]["project_root"])
    if not root.is_absolute():
        root = Path.cwd() / root
    return root.resolve()


def run(cfg: dict, target_date, stdout: bool, clear: bool, with_competitors: bool) -> int:
    tz = ZoneInfo(cfg["timezone"])
    sys.stdout.write(f"[INFO] 时区={cfg['timezone']} 目标日期={target_date}\n")

    # 1) 抓取
    raw_items = fetch_all(cfg)
    sys.stdout.write(f"[INFO] 共拉取 {len(raw_items)} 条\n")

    # 2) 归一化
    items = [normalize(it) for it in raw_items if it.get("title")]
    items = [it for it in items if it["title"]]

    # 3) 关键词打分 + 综合排序
    weights = cfg["weights"]
    keywords = cfg["keywords"]
    exclude = cfg["exclude_keywords"]
    scored: list[dict] = []
    for it in items:
        r = relevance_score(it["title"], keywords, exclude)
        if r == 0.0 and exclude:
            continue  # 命中排除词
        h = hotness_score(it["rank"], it["hot_raw"])
        it["hotness"] = h
        it["relevance"] = r
        it["final_score"] = round(h * weights["hotness"] + r * weights["relevance"], 3)
        scored.append(it)
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    sys.stdout.write(f"[INFO] 打分后剩 {len(scored)} 条\n")

    # 4) 记忆去重
    root = resolve_project_root(cfg)
    # 记忆文件路径：skill 内 memory 目录（相对脚本位置），不混到项目根
    skill_root = SCRIPT_DIR.parent
    # cfg["dedup"]["memory_file"] 可能是 "memory/dedup-history.jsonl" 这种相对路径
    # 保留子目录，不直接取 .name
    memory_file = (skill_root / cfg["dedup"]["memory_file"]).resolve()

    if clear:
        clear_memory(memory_file)
        return 0

    dedup_enabled = cfg["dedup"]["enabled"]
    if dedup_enabled:
        history = load_dedup_history(memory_file, cfg["dedup"]["window_days"])
        before = len(scored)
        scored = [it for it in scored if not is_dup(it["title"], history)]
        sys.stdout.write(f"[INFO] 去重：{before} → {len(scored)}（已去 {before - len(scored)} 条）\n")

    # 5) 取 TOP N
    top = scored[: cfg["top_n"]]

    # 6) 竞品监控（可选）
    if with_competitors and cfg["competitor_monitor"]["enabled"]:
        sys.stdout.write("[INFO] 启用竞品监控（待实现）\n")

    # 7) 输出
    if stdout:
        print_console(top)
    else:
        out_dir = (root / cfg["paths"]["output_dir"]).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{target_date.strftime('%Y-%m-%d')}-hot-topics.md"
        out_path.write_text(render_output(top, cfg, target_date), encoding="utf-8")
        sys.stdout.write(f"[INFO] 已写入 → {out_path}\n")
        print_console(top)

    # 8) 写记忆
    if dedup_enabled and top:
        append_dedup_history(memory_file, top)
        sys.stdout.write(f"[INFO] 记忆追加 {len(top)} 条 → {memory_file}\n")

    if not top:
        sys.stdout.write("[HINT] 今日无候选：可能关键词太严 / 数据源全空 / 都被去重\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="自媒体选题雷达")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--stdout", action="store_true", help="只打印候选清单")
    parser.add_argument("--clear-memory", action="store_true", help="清空去重记忆")
    parser.add_argument("--with-competitors", action="store_true", help="启用竞品监控")
    args = parser.parse_args()

    cfg = load_config(args.config)
    tz = ZoneInfo(cfg["timezone"])

    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target = datetime.now(tz).date()

    return run(cfg, target, args.stdout, args.clear_memory, args.with_competitors)


if __name__ == "__main__":
    sys.exit(main())