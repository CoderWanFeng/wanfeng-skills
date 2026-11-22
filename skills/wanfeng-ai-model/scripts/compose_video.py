#!/usr/bin/env python3
"""把 N 张试衣图 + 卡点音乐合成一条「卡点换装」短片（全自动，无需网页操作）。

两种画面来源：
  1) 默认：静帧 + 缓慢推近动效（ffmpeg zoompan），零视频生成成本，跑得快，适合先测效果。
  2) --motion：传入 VideoGen 生成的 N 个真动片段，逐段替换，模特真的会走。

无论哪种，切点都硬切在音乐小节线上（见 beat_music.py 的 cut_points）。

用法：
  python3 compose_video.py --images 试衣-01.png 试衣-02.png 试衣-03.png \
      --music 卡点音乐.wav --out 换装成片.mp4
  python3 compose_video.py --images ... --motion clip1.mp4 clip2.mp4 clip3.mp4 \
      --music ... --out ... --bpm 120
  python3 compose_video.py --images ... --out ... --no-music   # 只要画面

依赖：ffmpeg / ffprobe（PATH 内）+ 托管 Python 3（标准库即可）。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def run(cmd, capture=False):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if r.returncode != 0:
        msg = r.stderr[-1500:] if r.stderr else "(no stderr)"
        raise RuntimeError(f"命令失败 rc={r.returncode}\n  {' '.join(map(str, cmd))}\n{msg}")
    return r.stdout if capture else ""


def probe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", str(path)], capture=True)
    return json.loads(out)


def atoms(path):
    import struct
    res, off = [], 0
    with open(path, "rb") as f:
        while off < 200000:
            f.seek(off)
            h = f.read(8)
            if len(h) < 8:
                break
            size, typ = struct.unpack(">I4s", h)
            if size < 8:
                break
            res.append(typ.decode("latin1"))
            off += size
    return res


def main():
    ap = argparse.ArgumentParser(description="合成卡点换装短片")
    ap.add_argument("--images", nargs="+", required=True, help="N 张试衣图（按出场顺序）")
    ap.add_argument("--motion", nargs="+", default=None,
                    help="可选：N 个 VideoGen 真动片段，与 --images 一一对应")
    ap.add_argument("--music", default=None, help="卡点音乐 WAV")
    ap.add_argument("--out", required=True, help="输出 mp4 路径")
    ap.add_argument("--size", default="1080x1920", help="成片分辨率，默认 1080x1920（9:16）")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seg", type=float, default=2.0, help="每段秒数，默认 2.0")
    ap.add_argument("--bpm", type=float, default=120, help="仅写入报告，便于对账")
    ap.add_argument("--no-music", action="store_true", help="不混音乐（输出纯画面）")
    ap.add_argument("--zoom", type=float, default=0.0006, help="静帧推近速度，0=不动")
    ap.add_argument("--report", default=None, help="可选：输出 report.json 路径")
    a = ap.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        sys.exit("[fail] 需要 ffmpeg / ffprobe 在 PATH 内")
    W, H = (int(x) for x in a.size.lower().split("x"))
    n = len(a.images)
    if a.motion and len(a.motion) != n:
        sys.exit(f"[fail] --motion 片段数({len(a.motion)}) 与图片数({n}) 不一致")
    for p in a.images:
        if not os.path.exists(p):
            sys.exit(f"[fail] 试衣图不存在：{p}")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="aimodel-compose-")
    try:
        segs = []
        for i in range(n):
            dst = os.path.join(tmp, f"seg{i:02d}.mp4")
            if a.motion:
                src = a.motion[i]
                if not os.path.exists(src):
                    sys.exit(f"[fail] 真动片段不存在：{src}")
                vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                      f"crop={W}:{H},fps={a.fps},format=yuv420p")
                cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-t", f"{a.seg:.3f}",
                       "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
                       "-crf", "20", "-pix_fmt", "yuv420p", dst]
            else:
                # 先放大 2 倍再 zoompan，避免推近时糊；crop 保证铺满且比例正确
                big_w, big_h = W * 2, H * 2
                z = max(a.zoom, 0.0)
                vf = (f"scale={big_w}:{big_h}:force_original_aspect_ratio=increase,"
                      f"crop={big_w}:{big_h},"
                      f"zoompan=z='min(zoom+{z:.6f},1.10)':d=1:"
                      f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                      f"s={W}x{H}:fps={a.fps},format=yuv420p")
                cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(a.fps),
                       "-t", f"{a.seg:.3f}", "-i", a.images[i], "-vf", vf,
                       "-an", "-c:v", "libx264", "-preset", "veryfast",
                       "-crf", "20", "-pix_fmt", "yuv420p", dst]
            run(cmd)
            segs.append(dst)
            print(f"[seg {i+1}/{n}] ok")

        # 精确 concat：trim 到 seg 秒再拼，避免各段帧数误差累积
        silent = os.path.join(tmp, "silent.mp4")
        ins = []
        for s in segs:
            ins += ["-i", s]
        parts = []
        for i in range(n):
            parts.append(f"[{i}:v]trim=0:{a.seg:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append("".join(f"[v{i}]" for i in range(n)) +
                     f"concat=n={n}:v=1:a=0[vout]")
        run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(parts),
             "-map", "[vout]", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(a.fps), silent])

        total = n * a.seg
        if a.no_music or not a.music:
            run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-c:v", "copy",
                 "-movflags", "+faststart", a.out])
        else:
            if not os.path.exists(a.music):
                sys.exit(f"[fail] 音乐不存在：{a.music}")
            af = (f"[1:a]apad,atrim=start=0:end={total:.3f},"
                  f"alimiter=limit=0.89,loudnorm=I=-14:TP=-1.0:LRA=11[aout]")
            run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", a.music,
                 "-filter_complex", af, "-map", "0:v:0", "-map", "[aout]",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                 "-movflags", "+faststart", "-t", f"{total:.3f}", a.out])

        d = probe(a.out)
        v = next(s for s in d["streams"] if s["codec_type"] == "video")
        au = [s for s in d["streams"] if s["codec_type"] == "audio"]
        ats = atoms(a.out)
        report = {
            "out": a.out,
            "duration": round(float(d["format"]["duration"]), 3),
            "expected_duration": round(total, 3),
            "size": f"{v['width']}x{v['height']}",
            "fps": a.fps,
            "segments": n,
            "seg_seconds": a.seg,
            "bpm": a.bpm,
            "cut_points": [round(i * a.seg, 3) for i in range(1, n)],
            "motion_source": "VideoGen 片段" if a.motion else "静帧推近动效",
            "music": None if (a.no_music or not a.music) else a.music,
            "audio_stream": au[0]["codec_name"] if au else None,
            "faststart": "moov" in ats[:3],
            "atom_head": ats[:4],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if a.report:
            with open(a.report, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

        ok = (abs(report["duration"] - total) < 0.15
              and (v["width"], v["height"]) == (W, H)
              and report["faststart"])
        print("\n[ok] 成片已生成：" + a.out if ok else "\n[warn] 生成完成但校验有偏差，请看 report")
        sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
