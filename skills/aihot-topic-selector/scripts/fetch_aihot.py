#!/usr/bin/env python3
"""
fetch_aihot.py · AIHOT 每日热点拉取与选题候选生成

用法：
    python scripts/fetch_aihot.py                    # 跑今天
    python scripts/fetch_aihot.py --dry-run          # 只打印不写文件
    python scripts/fetch_aihot.py --date 20260701    # 指定日期
    python scripts/fetch_aihot.py --config /path/to/topic-config.yaml

依赖（缺失时脚本会给出 pip install 提示）：
    - rapidfuzz  (pip install rapidfuzz)
    - pyyaml     (pip install pyyaml)

配置项见 ../topic-config.example.yaml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "[ERROR] 缺少 PyYAML。请先执行：pip install pyyaml\n"
    )
    sys.exit(2)

try:
    from rapidfuzz import fuzz
except ImportError:
    sys.stderr.write(
        "[ERROR] 缺少 rapidfuzz。请先执行：pip install rapidfuzz\n"
    )
    sys.exit(2)


# ---------- 常量 ----------
BASE = "https://aihot.virxact.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    # 不主动声明 Accept-Encoding：避免服务端返回 gzip/br 后 brotli 解码缺失炸掉
    "Connection": "keep-alive",
    "Referer": "https://aihot.virxact.com/",
}
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parent / "topic-config.yaml"
EXAMPLE_CONFIG = SCRIPT_DIR.parent / "topic-config.example.yaml"


# ---------- 配置 ----------
def load_config(path: Path) -> dict:
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
        "daily_dir": "workflow/每日热点/",
        "min_score": 50,
        "lookback_hours": 30,
        "fuzzy_match_threshold": 90,
        "timezone": "Asia/Shanghai",
        "project_root": ".",
    }
    return {**defaults, **cfg}


# ---------- 网络 ----------
def http_get(path: str, params: dict | None = None) -> dict:
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    import ssl
    import socket
    ssl_ctx = ssl.create_default_context()
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as r:
                raw = r.read()
                # 处理 gzip / deflate / br 压缩
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
                        pass  # brotli 未装时跳过（极少见）
                return json.loads(raw)
        except (socket.timeout, ssl.SSLError, ConnectionError) as e:
            last_err = e
            sys.stderr.write(f"[WARN] 网络异常（{attempt + 1}/3）：{e}\n")
            continue
    raise RuntimeError(f"AIHOT 网络请求 3 次失败：{last_err}")


# ---------- 时间 ----------
def to_local(iso: str, tz: ZoneInfo) -> datetime | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone(tz)
    except Exception:
        return None


def filter_today(items: list[dict], target_date: datetime.date, tz: ZoneInfo) -> list[dict]:
    out = []
    for item in items:
        pub = item.get("publishedAt", "")
        local = to_local(pub, tz)
        if local is None:
            continue
        if local.date() == target_date:
            item["_cst_time"] = local.strftime("%H:%M")
            item["_score_num"] = item.get("score") or 0
            out.append(item)
    return out


# ---------- 文本清洗 & 去重 ----------
_BRACKETS = re.compile(r"[\【\】\[\]\(\)（）：:]")
_SUFFIX_HINTS = re.compile(
    r"\s*[-—–]\s*(IT之家|Hacker\s*News|公众号[:：]?.*|量子位|机器之心|"
    r"36[氪Kr]|雷锋网|infoQ|新智元|智东西)\s*$",
    re.IGNORECASE,
)


def clean_title(title: str) -> str:
    if not title:
        return ""
    t = _BRACKETS.sub("", title)
    t = _SUFFIX_HINTS.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_duplicate(title: str, existing: list[str], threshold: int) -> bool:
    cleaned = clean_title(title)
    if not cleaned:
        return False
    for prev in existing:
        if fuzz.ratio(cleaned, prev) >= threshold:
            return True
    return False


# ---------- 拉取 ----------
def fetch_items(lookback_hours: int) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    data = http_get("/api/public/items", {"mode": "all", "since": since})
    return data.get("items", [])


# ---------- 写文件 ----------
def render_front_matter(date_str: str, time_str: str, total: int) -> str:
    return (
        "---\n"
        f"title: 每日AI热点汇总 · {date_str}\n"
        f"date: {date_str} {time_str}\n"
        "tags: [每日AI热点, 内部文档]\n"
        "categories: [工作流程, AI热点汇总]\n"
        "cover: https://images.unsplash.com/photo-1611162600?w=1200&auto=format&fit=crop\n"
        f"description: AIHOT 每日热点自动汇总，{date_str} 当天共采集 {total} 条\n"
        "---\n"
    )


def render_section(time_str: str, new_items: list[dict], dup_count: int) -> str:
    lines = [f"## 更新于 {time_str}", ""]
    for idx, item in enumerate(new_items, 1):
        title = item.get("title", "(无标题)")
        score = item.get("_score_num", 0)
        pub_time = item.get("_cst_time", "")
        source = item.get("source", "") or "未知来源"
        link = item.get("url", "") or item.get("link", "")
        desc = item.get("description", "") or item.get("summary", "")
        lines.append(f"### {idx}. {title}")
        lines.append("")
        lines.append(f"- **AIHOT 评分**：{score}")
        lines.append(f"- **发布时间**：{pub_time}")
        lines.append(f"- **来源**：{source}")
        if link:
            lines.append(f"- **链接**：{link}")
        if desc:
            lines.append(f"- **简介**：{desc}")
        lines.append("")
    lines.append(f"> 本次新增 {len(new_items)} 条，跳过重复 {dup_count} 条")
    lines.append("")
    return "\n".join(lines)


def render_no_topic_section(date_str: str, total: int) -> str:
    return (
        f"## 今日无合适选题\n"
        f"> 原因：{date_str} 当日 {total} 条热点全部不符合核心 2 问\n"
        f"> 操作：跳过今日选题，下一个工作日继续\n"
    )


def resolve_project_root(cfg: dict) -> Path:
    """project_root 相对路径基于 cwd 解析（用户运行脚本时所在目录）。"""
    root = Path(cfg["project_root"])
    if not root.is_absolute():
        root = Path.cwd() / root
    return root.resolve()


def write_daily_file(
    cfg: dict,
    target_date: datetime.date,
    new_items: list[dict],
    dup_count: int,
    dry_run: bool,
) -> Path:
    date_str = target_date.strftime("%Y%m%d")
    display_date = target_date.strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    file_name = f"{date_str}.md"
    out_dir = (resolve_project_root(cfg) / cfg["daily_dir"]).resolve()
    out_path = out_dir / file_name

    section = render_section(time_str, new_items, dup_count)
    fm = render_front_matter(display_date, time_str, len(new_items))
    h1 = f"# 每日AI热点汇总 · {display_date}\n\n"
    meta = (
        f"> 自动收集于 {display_date} {time_str}\n"
        f"> 文件用途：每日选题参考，可直接用作内部追溯\n\n\n"
    )
    new_block = fm + h1 + meta + section

    if dry_run:
        sys.stdout.write("\n========== DRY RUN: 新增区块预览 ==========\n")
        sys.stdout.write(new_block)
        sys.stdout.write(f"目标文件：{out_path}\n")
        sys.stdout.write("===========================================\n")
        return out_path

    out_dir.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        with out_path.open("r", encoding="utf-8") as f:
            old = f.read()
        if old.startswith("---"):
            end = old.find("\n---\n", 4)
            front_matter = old[: end + 5] if end != -1 else ""
            body = old[end + 5 :] if end != -1 else old
        else:
            front_matter, body = "", old
        body = body.rstrip() + "\n\n" + section
        merged = front_matter + body.lstrip()
    else:
        merged = new_block

    with out_path.open("w", encoding="utf-8") as f:
        f.write(merged)
    return out_path


def append_no_topic(cfg: dict, target_date: datetime.date, total: int, dry_run: bool) -> Path:
    date_str = target_date.strftime("%Y%m%d")
    file_name = f"{date_str}.md"
    out_dir = (resolve_project_root(cfg) / cfg["daily_dir"]).resolve()
    out_path = out_dir / file_name
    block = render_no_topic_section(target_date.strftime("%Y-%m-%d"), total)

    if dry_run:
        sys.stdout.write("\n========== DRY RUN: 无选题区块预览 ==========\n")
        sys.stdout.write(block)
        sys.stdout.write(f"目标文件：{out_path}\n")
        sys.stdout.write("==============================================\n")
        return out_path

    out_dir.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        with out_path.open("a", encoding="utf-8") as f:
            f.write("\n" + block + "\n")
    else:
        fm = render_front_matter(
            target_date.strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M:%S"),
            0,
        )
        h1 = f"# 每日AI热点汇总 · {target_date.strftime('%Y-%m-%d')}\n\n"
        meta = (
            "> 自动收集于 "
            f"{target_date.strftime('%Y-%m-%d')} {datetime.now().strftime('%H:%M:%S')}\n"
            "> 文件用途：每日选题参考，可直接用作内部追溯\n\n\n"
        )
        with out_path.open("w", encoding="utf-8") as f:
            f.write(fm + h1 + meta + block + "\n")
    return out_path


# ---------- 选题候选打印 ----------
def print_candidates(items: list[dict], threshold: int) -> None:
    passed = [i for i in items if i["_score_num"] >= threshold]
    passed.sort(key=lambda x: x["_score_num"], reverse=True)

    sys.stdout.write("\n========== 选题候选清单（评分 ≥ %d） ==========\n" % threshold)
    if not passed:
        sys.stdout.write("（无符合 min_score 阈值的条目）\n")
    for idx, item in enumerate(passed, 1):
        title = item.get("title", "(无标题)")
        score = item["_score_num"]
        pub = item.get("_cst_time", "")
        sys.stdout.write(f"{idx:2d}. [{score:>3}] {pub}  {title}\n")
    sys.stdout.write("================================================\n")


# ---------- 主流程 ----------
def run(cfg: dict, target_date: datetime.date, dry_run: bool) -> int:
    tz = ZoneInfo(cfg["timezone"])
    threshold = int(cfg["fuzzy_match_threshold"])
    min_score = int(cfg["min_score"])
    lookback = int(cfg["lookback_hours"])

    sys.stdout.write(f"[INFO] 时区={cfg['timezone']} 目标日期={target_date} lookback={lookback}h\n")

    # 拉数据
    try:
        items = fetch_items(lookback)
    except Exception as e:
        sys.stderr.write(f"[ERROR] 拉取 AIHOT 失败：{e}\n")
        return 1
    sys.stdout.write(f"[INFO] 本次拉取 {len(items)} 条\n")

    # 过滤今天
    today_items = filter_today(items, target_date, tz)
    sys.stdout.write(f"[INFO] {target_date} 当天条目 {len(today_items)} 条\n")

    # 去重（与已有 daily 文件中的标题模糊比对）
    out_dir = (resolve_project_root(cfg) / cfg["daily_dir"]).resolve()
    existing_titles: list[str] = []
    if out_dir.exists():
        for fp in out_dir.glob("*.md"):
            if fp.name == f"{target_date.strftime('%Y%m%d')}.md":
                continue
            try:
                text = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            for line in text.splitlines():
                if line.startswith("### ") and "." in line:
                    title = line.split(".", 1)[1].strip()
                    if title:
                        existing_titles.append(clean_title(title))

    new_items: list[dict] = []
    dup_count = 0
    for it in today_items:
        title = it.get("title", "")
        if is_duplicate(title, existing_titles + [i.get("title", "") for i in new_items], threshold):
            dup_count += 1
            continue
        new_items.append(it)

    sys.stdout.write(f"[INFO] 去重后新增 {len(new_items)} 条（重复 {dup_count} 条）\n")

    # Fallback：当天无任何新增 → 拉 7 天窗口，写无选题段
    if not new_items:
        sys.stdout.write("[WARN] 当天无新增热点，触发 fallback\n")
        try:
            wide_items = fetch_items(168)
        except Exception as e:
            sys.stderr.write(f"[ERROR] fallback 拉取失败：{e}\n")
            wide_items = []
        wide_today = filter_today(wide_items, target_date, tz)
        path = append_no_topic(cfg, target_date, len(wide_today), dry_run)
        sys.stdout.write(f"[INFO] 无选题区块 → {path}\n")
        return 0

    # 写 daily 文件
    path = write_daily_file(cfg, target_date, new_items, dup_count, dry_run)
    sys.stdout.write(f"[INFO] 已写入 → {path}\n")

    # 打印选题候选
    print_candidates(today_items, min_score)

    # 提示
    passed = [i for i in today_items if i["_score_num"] >= min_score]
    if not passed:
        sys.stdout.write(
            f"[HINT] 今日无评分 ≥ {min_score} 的条目；"
            "可考虑降低 min_score 或放宽核心 2 问\n"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIHOT 每日热点拉取 + 选题候选生成"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"配置文件路径（默认：{DEFAULT_CONFIG}）",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="目标日期 YYYY-MM-DD（默认今天，按 timezone）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印不写文件",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    tz = ZoneInfo(cfg["timezone"])

    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target = datetime.now(tz).date()

    return run(cfg, target, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())