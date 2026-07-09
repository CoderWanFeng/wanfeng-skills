#!/usr/bin/env python3
"""
weekly_report.py · 本周热点周报生成器

直接复用 fetch_hot.py 的抓取与打分逻辑，按 7 天窗口逐日跑 TOP N，
汇总到一个 Markdown 周报文件。

用法：
    python scripts/weekly_report.py                  # 默认 7 天窗口，今天为末日
    python scripts/weekly_report.py --days 7         # 指定窗口天数
    python scripts/weekly_report.py --config /path/to/radar-config.yaml
    python scripts/weekly_report.py --end 2026-07-10 # 指定结束日（默认今天）
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import fetch_hot  # noqa: E402


def collect_top_n_for_date(cfg: dict, target_date, top_n: int) -> list[dict]:
    """拉取 + 打分，返回单日 TOP N（不去重、不写文件、不追加记忆）。"""
    raw_items = fetch_hot.fetch_all(cfg)
    items = [fetch_hot.normalize(it) for it in raw_items if it.get("title")]
    items = [it for it in items if it["title"]]

    weights = cfg["weights"]
    keywords = cfg["keywords"]
    exclude = cfg["exclude_keywords"]
    scored: list[dict] = []
    for it in items:
        r = fetch_hot.relevance_score(it["title"], keywords, exclude)
        if r == 0.0 and exclude:
            continue
        h = fetch_hot.hotness_score(it["rank"], it["hot_raw"])
        it["hotness"] = h
        it["relevance"] = r
        it["final_score"] = round(h * weights["hotness"] + r * weights["relevance"], 3)
        scored.append(it)
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:top_n]


def render_weekly_md(
    daily_tops: list[tuple[object, list[dict]]],
    cfg: dict,
    start_date,
    end_date,
    cross_day_items: list[dict],
) -> str:
    """生成周报 Markdown。"""
    date_range = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    time_str = datetime.now().strftime("%H:%M:%S")
    keywords = cfg["keywords"]
    exclude = cfg["exclude_keywords"]
    platforms = cfg["platforms"]

    out: list[str] = []
    out.append("---")
    out.append(f"title: 本周热点周报 · {date_range}")
    out.append(f"date: {end_date.strftime('%Y-%m-%d')} {time_str}")
    out.append("tags: [本周热点, 周报, 自媒体, 内部文档]")
    out.append("categories: [工作流程, 选题雷达]")
    out.append(f"description: hot-topic-radar 本周热点周报 {date_range}")
    out.append("---")
    out.append("")
    out.append(f"# 本周热点周报 · {date_range}")
    out.append("")
    out.append("> 由 `hot-topic-radar` skill 自动生成")
    out.append(f"> 生成时间：{end_date.strftime('%Y-%m-%d')} {time_str}")
    out.append(f"> 关键词：**{' / '.join(keywords) if keywords else '（无）'}**")
    if exclude:
        out.append(f"> 排除：**{' / '.join(exclude)}**")
    out.append(f"> 平台：**{' / '.join(platforms)}**")
    out.append("")
    out.append("---")
    out.append("")

    # 汇总统计
    total_hits = sum(len(tops) for _, tops in daily_tops)
    days_with_hits = sum(1 for _, tops in daily_tops if tops)
    out.append("## 📊 一周概览")
    out.append("")
    out.append(f"- **统计窗口**：{len(daily_tops)} 天")
    out.append(f"- **抓取原始条数**：{sum(len(t) for _, t in daily_tops)} 条（含跨天重复）")
    out.append(f"- **跨天去重后命中**：{len(cross_day_items)} 条")
    out.append(f"- **有命中天数**：{days_with_hits} / {len(daily_tops)} 天")
    out.append(f"- **TOP N / 天**：{cfg['top_n']}")
    out.append("")

    out.append("---")
    out.append("")

    # 跨日聚合 TOP 列表（按综合分 + 出现天数排序）
    cross_sorted = sorted(
        cross_day_items,
        key=lambda x: (x["appearances"], x["final_score"]),
        reverse=True,
    )
    out.append("## 🔥 本周 AI 热点综合榜（跨天去重 · 按综合分 + 出现天数排序）")
    out.append("")
    out.append("| # | 主题 | 平台 | 综合分 | 出现天数 | 首次出现 | 末次出现 |")
    out.append("|---|------|------|--------|----------|----------|----------|")
    for idx, item in enumerate(cross_sorted[:30], 1):
        title = item["title"].replace("|", "\\|")
        first = item["first_seen"].strftime("%m-%d")
        last = item["last_seen"].strftime("%m-%d")
        out.append(
            f"| {idx} | {title} | {item['platform']} | "
            f"{item['final_score']:.3f} | {item['appearances']} | {first} | {last} |"
        )
    out.append("")
    if cross_sorted:
        top1 = cross_sorted[0]
        out.append("### ⭐ 本周最热 AI 话题")
        out.append("")
        out.append(f"**{top1['title']}**")
        out.append("")
        out.append(f"- 平台：{top1['platform']}")
        out.append(f"- 出现在本周 {top1['appearances']} / {len(daily_tops)} 天榜单")
        out.append(f"- 首次出现：{top1['first_seen']}，末次：{top1['last_seen']}")
        if top1.get("url"):
            out.append(f"- 链接：{top1['url']}")
        out.append("")

    out.append("---")
    out.append("")

    # 每天的详情
    out.append("## 📅 每日 TOP N")
    out.append("")
    for date_obj, tops in daily_tops:
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
        out.append(f"### {date_obj.strftime('%Y-%m-%d')}（{weekday}）")
        out.append("")
        if not tops:
            out.append("（当天无 AI 相关候选）")
            out.append("")
            continue
        for idx, item in enumerate(tops, 1):
            out.append(f"#### {idx}. {item['title']}")
            out.append("")
            out.append(
                f"- **平台**：{item['platform']}"
            )
            out.append(
                f"- **综合分**：{item['final_score']:.3f}（热度 {item['hotness']:.2f} × 相关度 {item['relevance']:.2f}）"
            )
            if item.get("url"):
                out.append(f"- **链接**：{item['url']}")
            if item.get("desc"):
                out.append(f"- **简介**：{item['desc'][:200]}")
            out.append("")

    out.append("---")
    out.append("")
    out.append("## 💡 下一步")
    out.append("")
    out.append("- 这些候选是**情报弹药**，不是文章。")
    out.append("- 推不推、跟不跟、写不写 → 由用户决定。")
    out.append("- 选定具体主题后，进入下游 skill（公众号 / 口播稿 / 视频）继续。")
    out.append("")
    out.append(f"> 本周报由 `skills/hot-topic-radar/scripts/weekly_report.py` 生成")
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="hot-topic-radar 本周热点周报")
    parser.add_argument("--config", type=Path, default=fetch_hot.DEFAULT_CONFIG)
    parser.add_argument("--days", type=int, default=7, help="统计窗口天数（默认 7）")
    parser.add_argument("--end", type=str, default=None, help="结束日期 YYYY-MM-DD（默认今天）")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录（默认走 cfg.paths.output_dir）",
    )
    args = parser.parse_args()

    cfg = fetch_hot.load_config(args.config)

    from zoneinfo import ZoneInfo

    tz = ZoneInfo(cfg["timezone"])
    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
    else:
        end_date = datetime.now(tz).date()
    start_date = end_date - timedelta(days=args.days - 1)

    sys.stdout.write(
        f"[INFO] 周报窗口：{start_date} ~ {end_date}（{args.days} 天）\n"
    )

    daily_tops: list[tuple[object, list[dict]]] = []
    # 跨天聚合：同一 (title, platform) 只保留综合分最高的，并记录首次/末次出现日期
    cross_day: dict[tuple[str, str], dict] = {}

    for offset in range(args.days):
        day = start_date + timedelta(days=offset)
        sys.stdout.write(f"[INFO] 抓取 {day} ...\n")
        tops = collect_top_n_for_date(cfg, day, cfg["top_n"])
        sys.stdout.write(f"[INFO]   → {len(tops)} 条\n")
        daily_tops.append((day, tops))

        for item in tops:
            key = (item["title"], item["platform"])
            if key not in cross_day:
                cross_day[key] = {
                    **item,
                    "first_seen": day,
                    "last_seen": day,
                    "appearances": 1,
                    "platform_dates": [day],
                }
            else:
                rec = cross_day[key]
                rec["appearances"] += 1
                rec["last_seen"] = day
                rec["platform_dates"].append(day)
                # 保留综合分最高的版本
                if item["final_score"] > rec["final_score"]:
                    cross_day[key] = {
                        **item,
                        "first_seen": rec["first_seen"],
                        "last_seen": day,
                        "appearances": rec["appearances"],
                        "platform_dates": rec["platform_dates"],
                    }

    md = render_weekly_md(
        daily_tops, cfg, start_date, end_date, list(cross_day.values())
    )

    # 输出路径
    if args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        root = fetch_hot.resolve_project_root(cfg)
        out_dir = (root / cfg["paths"]["output_dir"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}-hot-topic-radar-weekly.md"
    out_path = out_dir / file_name
    out_path.write_text(md, encoding="utf-8")
    sys.stdout.write(f"[INFO] 已写入 → {out_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())