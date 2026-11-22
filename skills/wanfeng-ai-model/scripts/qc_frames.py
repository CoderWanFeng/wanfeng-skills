#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qc_frames.py —— 模特视频抽帧质检工具

ffprobe 验证媒体 + 均匀抽帧，输出帧图片与 report.json，供 Agent Read 逐帧质检
（脸部漂移 / 服装漂移 / 动作还原 / 崩坏帧）。纯标准库 + ffmpeg。

用法：
    python3 qc_frames.py --video 成片.mp4 --out 抽帧/ --n 8                 # 默认全自动版
    python3 qc_frames.py --video 成片.mp4 --out 抽帧/ --n 8 --mode action   # 指定动作版
    python3 qc_frames.py --video 成片.mp4 --out 抽帧/ --n 8 --width 540     # 缩宽省 token
"""
import argparse
import json
import os
import subprocess
import sys


def ffprobe(path: str) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.exit(f"[FAIL] ffprobe 无法读取：{path}\n{r.stderr.strip()}")
    return json.loads(r.stdout)


def main() -> None:
    ap = argparse.ArgumentParser(description="模特视频抽帧质检")
    ap.add_argument("--video", required=True, help="成片/白膜视频路径")
    ap.add_argument("--out", required=True, help="帧输出目录")
    ap.add_argument("--n", type=int, default=8, help="抽帧数量（默认 8）")
    ap.add_argument("--width", type=int, default=None, help="缩放宽度（可选，省读取成本）")
    ap.add_argument("--mode", choices=["auto", "action"], default="auto",
                    help="auto=默认全自动版（静帧动效/卡点）；action=指定动作版（白膜驱动走秀）")
    args = ap.parse_args()

    CHECKS = {
        "auto": ["脸部一致", "服装还原与跨套串色", "卡点切点是否干净", "黑帧/闪烁", "音画同步"],
        "action": ["脸部漂移", "服装漂移", "动作还原", "崩坏帧"],
    }

    video = os.path.abspath(args.video)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    # 1) 验媒体（时长 / 分辨率 / 双流）
    meta = ffprobe(video)
    streams = meta.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(meta.get("format", {}).get("duration", 0) or 0)
    if not v:
        sys.exit("[FAIL] 无视频流")
    w, h = v.get("width"), v.get("height")
    print(f"[OK] 时长 {duration:.2f}s | {w}x{h} | {v.get('r_frame_rate')} fps | "
          f"音频 {'有 ' + a.get('codec_name') if a else '无（纯画面属正常）'}")

    # 2) 均匀抽帧（避开首尾 5% 黑帧/转场）
    margin = duration * 0.05
    span = max(duration - 2 * margin, 0.1)
    frames = []
    for i in range(args.n):
        t = margin + span * i / max(args.n - 1, 1)
        out = os.path.join(out_dir, f"frame_{i+1:02d}_t{t:05.2f}s.png")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1"]
        if args.width:
            cmd += ["-vf", f"scale={args.width}:-2"]
        cmd += [out]
        subprocess.run(cmd, check=True)
        frames.append({"frame": os.path.basename(out), "t": round(t, 2)})
    print(f"[OK] 抽帧 {len(frames)} 张 -> {out_dir}")

    # 3) report.json（供台账归档）
    report = {
        "video": video,
        "duration_s": round(duration, 2),
        "resolution": f"{w}x{h}",
        "fps": v.get("r_frame_rate"),
        "has_audio": bool(a),
        "frames": frames,
        "mode": args.mode,
        "qc_checklist": CHECKS[args.mode],
    }
    rp = os.path.join(out_dir, "report.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[OK] report -> {rp}")
    print("下一步：Read 逐张读 frame_*.png，按 report.json 的 qc_checklist 逐项给结论（见 qc-gates.md）。")


if __name__ == "__main__":
    main()
