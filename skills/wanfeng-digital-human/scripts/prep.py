#!/usr/bin/env python3
"""零成本的本地预处理：体检素材、抽参考帧、裁竖屏、贴音轨、挂字幕。

这条技能只用软件积分出画面，不调任何付费接口。本脚本负责**画面之外的脏活**，
全部用本地 ffmpeg 完成，不联网、不花钱。

    # 体检：时长、尺寸、有没有音轨
    python3 scripts/prep.py inspect --face 自拍.mov

    # 抽 3 张候选参考帧（挑睁眼、嘴闭合、正脸的那张）
    python3 scripts/prep.py frames --face 自拍.mov --out output/frames

    # 把选中的帧裁成竖屏参考图
    python3 scripts/prep.py crop --frame output/frames/frame_2.jpg --ratio 9:16 --out output/reference.jpg

    # 把用户自己录的台词贴到成片上（口型只对齐时长）
    python3 scripts/prep.py audio --video 成片.mp4 --audio 录音.m4a --out 成片-原声.mp4

    # 挂软字幕（播放器可开关）
    python3 scripts/prep.py subtitle --video 成片.mp4 --srt 字幕.srt --out 成片-字幕.mp4
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "engine" / "src"))

RATIOS = {
    "9:16": (9, 16),
    "16:9": (16, 9),
    "1:1": (1, 1),
    "4:3": (4, 3),
    "3:4": (3, 4),
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".avi"}


def ok(label: str, detail: str = "") -> None:
    print(f"  [ OK ] {label}" + (f"  {detail}" if detail else ""))


def warn(label: str, detail: str = "") -> None:
    print(f"  [ !  ] {label}" + (f"  {detail}" if detail else ""))


def bad(label: str, detail: str = "") -> None:
    print(f"  [ X  ] {label}" + (f"  {detail}" if detail else ""))


def need_ffmpeg() -> None:
    for exe in ("ffmpeg", "ffprobe"):
        if not shutil.which(exe):
            raise SystemExit(f"缺少 {exe}。macOS: brew install ffmpeg；Windows 需把 ffmpeg 加进 PATH")


def read_media(path: Path) -> dict:
    from ai_digital_human.media import probe

    return probe(path)


def cmd_check(_args) -> int:
    need_ffmpeg()
    ok("ffmpeg", shutil.which("ffmpeg") or "")
    ok("ffprobe", shutil.which("ffprobe") or "")
    ok("Python", sys.version.split()[0])
    print("\n这条技能不需要密钥、不联网、不产生费用。")
    return 0


def cmd_inspect(args) -> int:
    need_ffmpeg()
    path = Path(args.face).expanduser().resolve()
    if not path.is_file():
        bad("找不到素材", str(path))
        return 2
    info = read_media(path)
    is_image = path.suffix.lower() in IMAGE_SUFFIXES
    kind = "图片" if is_image else "视频"
    w, h = info["display_width"], info["display_height"]
    shape = "竖屏" if h > w else ("方屏" if h == w else "横屏")
    if is_image:
        print(f"{kind} {w}×{h}，{shape}，1.4MB 量级即可；没有音轨。")
        return 0
    audio = "有音轨" if info["has_audio"] else "无音轨"
    print(f"{kind} {w}×{h}，{shape}，{info['duration']:.1f} 秒，{audio}。")
    if info["duration"] < 3:
        warn("偏短", "不足 3 秒，画面会不够稳；能换一段更长的更好")
    if min(w, h) < 480:
        warn("分辨率偏低", "低于 480，成片容易糊")
    return 0


def cmd_frames(args) -> int:
    need_ffmpeg()
    from ai_digital_human.media import extract_frame

    path = Path(args.face).expanduser().resolve()
    if not path.is_file():
        bad("找不到素材", str(path))
        return 2
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() in IMAGE_SUFFIXES:
        print(f"{path.name} 是图片，本身就是参考帧，不用抽。直接裁切：")
        print(f"  python3 scripts/prep.py crop --frame \"{path}\" --ratio 9:16 --out output/reference.jpg")
        return 0

    info = read_media(path)
    duration = info["duration"]
    if duration <= 0:
        bad("读不到时长", "换一个文件试试")
        return 2
    # 避开开头结尾：15% / 40% / 65%，中间那张最常用
    stamps = [round(duration * r, 2) for r in (0.15, 0.40, 0.65)]
    saved = []
    for idx, stamp in enumerate(stamps, start=1):
        dest = out_dir / f"frame_{idx}.jpg"
        extract_frame(path, stamp, dest)
        saved.append((dest, stamp))
        ok(f"frame_{idx}.jpg", f"第 {stamp} 秒")

    print("\n挑一张：睁眼、嘴闭合、正脸、不歪头。别默认第一张。")
    print("选好后导出竖屏参考图：")
    print(f'  python3 scripts/prep.py crop --frame "{saved[1][0]}" --ratio 9:16 --out output/reference.jpg')
    return 0


def cmd_crop(args) -> int:
    need_ffmpeg()
    src = Path(args.frame).expanduser().resolve()
    if not src.is_file():
        bad("找不到图片", str(src))
        return 2
    ratio = args.ratio
    if ratio not in RATIOS:
        bad("不支持的比例", f"{ratio}，可选 {', '.join(RATIOS)}")
        return 2
    info = read_media(src)
    src_w, src_h = info["display_width"], info["display_height"]
    if not src_w or not src_h:
        bad("读不到尺寸", str(src))
        return 2
    rw, rh = RATIOS[ratio]
    target = rw / rh
    if src_w / src_h > target:
        out_w, out_h = src_h * target, src_h
    else:
        out_w, out_h = src_w, src_w / target
    out_w, out_h = int(round(out_w)) // 2 * 2, int(round(out_h)) // 2 * 2

    dest = Path(args.out).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    vf = (f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
          f"crop={out_w}:{out_h}")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf,
         "-frames:v", "1", "-q:v", "2", str(dest)],
        check=True,
    )
    ok("参考图", f"{dest}（{out_w}×{out_h}，{ratio}）")
    return 0


def cmd_audio(args) -> int:
    need_ffmpeg()
    from ai_digital_human.media import mux_audio, probe

    video = Path(args.video).expanduser().resolve()
    audio = Path(args.audio).expanduser().resolve()
    for path, label in ((video, "视频"), (audio, "录音")):
        if not path.is_file():
            bad(f"找不到{label}", str(path))
            return 2
    dest = Path(args.out).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    before = probe(video)["duration"]
    mux_audio(video, audio, dest)
    after_v = probe(dest)["duration"]
    after_a = probe(dest)["has_audio"]
    ok("已贴音轨", f"{dest.name}，成片 {after_v:.1f} 秒（原画面 {before:.1f} 秒）")
    if not after_a:
        bad("结果没有音轨", "检查录音文件是否正常")
        return 1
    warn("口型说明", "这是把你的原声贴上去，画面只按音频时长对齐，不保证逐字同步")
    return 0


def cmd_subtitle(args) -> int:
    need_ffmpeg()
    video = Path(args.video).expanduser().resolve()
    srt = Path(args.srt).expanduser().resolve()
    for path, label in ((video, "视频"), (srt, "字幕")):
        if not path.is_file():
            bad(f"找不到{label}", str(path))
            return 2
    dest = Path(args.out).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(srt),
         "-map", "0", "-map", "1", "-c", "copy",
         "-c:s", "mov_text", "-metadata:s:s:0", "language=chi", str(dest)],
        check=True,
    )
    ok("已挂字幕", f"{dest.name}（软字幕，播放器里可开关）")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="数字人短片的本地预处理（零成本、不联网）")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="检查本机依赖")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("inspect", help="体检形象素材")
    p.add_argument("--face", required=True, help="视频或图片路径")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("frames", help="从视频里抽 3 张候选参考帧")
    p.add_argument("--face", required=True)
    p.add_argument("--out", default="output/frames")
    p.set_defaults(func=cmd_frames)

    p = sub.add_parser("crop", help="把选中的帧裁成目标比例")
    p.add_argument("--frame", required=True)
    p.add_argument("--ratio", default="9:16", choices=sorted(RATIOS))
    p.add_argument("--out", default="output/reference.jpg")
    p.set_defaults(func=cmd_crop)

    p = sub.add_parser("audio", help="把用户录音贴到成片上")
    p.add_argument("--video", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("--out", default="output/成片-原声.mp4")
    p.set_defaults(func=cmd_audio)

    p = sub.add_parser("subtitle", help="挂软字幕")
    p.add_argument("--video", required=True)
    p.add_argument("--srt", required=True)
    p.add_argument("--out", default="output/成片-字幕.mp4")
    p.set_defaults(func=cmd_subtitle)

    args = parser.parse_args()
    try:
        return args.func(args)
    except subprocess.CalledProcessError as exc:
        bad("ffmpeg 执行失败", f"退出码 {exc.returncode}，命令：{' '.join(exc.cmd)}")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
