#!/usr/bin/env python3
"""根据已撰写完成的 Markdown 文件集合，生成 repowiki-metadata.json。

用法：
    python3 generate_metadata.py <content_dir> [--out <metadata.json>]

行为：
    1. 递归扫描 <content_dir> 下所有 .md 文件
    2. 解析每个文件中的 <cite> 块，提取所有 file:// 引用
    3. 对每个 (path, line_range) 生成一条 code_snippets 记录
    4. 输出 meta/repowiki-metadata.json

注意：本脚本要求 repowiki 文档已经按格式撰写完毕，仅作为收尾工具。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

CITE_PATTERN = re.compile(r"<cite>(.*?)</cite>", re.DOTALL | re.IGNORECASE)
FILE_REF_PATTERN = re.compile(r"\[([^\]]+)\]\(file://([^)]+)\)")
LINE_RANGE_PATTERN = re.compile(r"#L(\d+)(?:-L(\d+))?")

CST = timezone(timedelta(hours=8))


def parse_cite_block(cite_text: str) -> list[dict[str, str]]:
    """解析 <cite> 块内的引用条目。

    每条形如：[filename](file://path/to/file#L1-L100)
    """
    entries: list[dict[str, str]] = []
    for m in FILE_REF_PATTERN.finditer(cite_text):
        name = m.group(1)
        path_with_anchor = m.group(2)
        line_match = LINE_RANGE_PATTERN.search(path_with_anchor)
        if line_match:
            start = line_match.group(1)
            end = line_match.group(2) or start
            line_range = f"{start}-{end}"
            path = path_with_anchor[: line_match.start()]
        else:
            line_range = "1-1"
            path = path_with_anchor
        entries.append({"name": name, "path": path, "line_range": line_range})
    return entries


def make_id(path: str, line_range: str) -> str:
    """生成 snippet ID。"""
    h = hashlib.md5(f"{path}:{line_range}".encode("utf-8")).hexdigest()
    return h


def generate_metadata(content_dir: Path, project_root: Path | None = None) -> dict[str, Any]:
    """生成 repowiki-metadata.json 内容。"""
    if not content_dir.is_dir():
        raise NotADirectoryError(f"{content_dir} 不是目录")

    now = datetime.now(CST).isoformat()

    seen: dict[tuple[str, str], dict[str, Any]] = {}
    md_files = sorted(content_dir.rglob("*.md"))
    for md in md_files:
        text = md.read_text(encoding="utf-8", errors="ignore")
        for cite_match in CITE_PATTERN.finditer(text):
            entries = parse_cite_block(cite_match.group(1))
            for entry in entries:
                key = (entry["path"], entry["line_range"])
                if key not in seen:
                    # 处理 path：如果是绝对路径，转为相对项目根
                    path = entry["path"]
                    if project_root and Path(path).is_absolute():
                        try:
                            path = str(Path(path).resolve().relative_to(project_root.resolve()))
                        except ValueError:
                            # 不在项目根内，保留绝对路径
                            pass
                    seen[key] = {
                        "id": make_id(path, entry["line_range"]),
                        "path": path,
                        "line_range": entry["line_range"],
                        "gmt_create": now,
                        "gmt_modified": now,
                    }

    snippets = sorted(seen.values(), key=lambda x: (x["path"], x["line_range"]))
    return {"code_snippets": snippets}


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 repowiki-metadata.json")
    parser.add_argument("content_dir", help="repowiki content 目录（包含所有 .md）")
    parser.add_argument("--out", default="-", help="输出 JSON 路径，默认 stdout")
    parser.add_argument("--project-root", default=None, help="项目根目录，用于将 file:// 绝对路径转为相对路径")
    args = parser.parse_args()

    content_dir = Path(args.content_dir).expanduser().resolve()
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else None

    try:
        meta = generate_metadata(content_dir, project_root)
    except Exception as e:
        print(f"生成失败：{e}", file=sys.stderr)
        return 1

    output = json.dumps(meta, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(output)
    else:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"已写入 {out_path}（{len(meta['code_snippets'])} 条 code_snippets）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())