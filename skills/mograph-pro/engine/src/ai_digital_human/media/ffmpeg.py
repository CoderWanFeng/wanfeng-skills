"""基于 ffmpeg 的本地媒体处理。

只做三件事：探针、抽帧、音视频切分与拼接。
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Optional


def _require(tool: str) -> str:
    if not shutil.which(tool):
        raise RuntimeError(f"未找到 {tool}，请先安装 ffmpeg")
    return tool


def _read_rotation(stream: dict) -> int:
    """读取视频的旋转角（度）。iPhone 竖拍素材常带 ±90 度旋转元数据。"""
    for side in stream.get("side_data_list") or []:
        if "rotation" in side:
            try:
                return int(side["rotation"])
            except (TypeError, ValueError):
                return 0
    try:
        return int((stream.get("tags") or {}).get("rotate", 0))
    except (TypeError, ValueError):
        return 0


def probe(path: str | Path) -> dict:
    """读取媒体信息，返回时长、体积、编码、分辨率等。

    width/height 是容器里的存储尺寸；display_width/display_height 是应用旋转元数据后
    实际观看的尺寸（手机竖拍素材两者相反）。
    """
    _require("ffprobe")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(out.stdout)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = info.get("format", {})
    width = int(video.get("width", 0)) if video else 0
    height = int(video.get("height", 0)) if video else 0
    rotation = _read_rotation(video) if video else 0
    display_w, display_h = (height, width) if abs(rotation) % 180 == 90 else (width, height)
    return {
        "duration": float(fmt.get("duration", 0)),
        "bytes": int(fmt.get("size", Path(path).stat().st_size)),
        "codec": (video or audio or {}).get("codec_name"),
        "sample_rate": int(audio.get("sample_rate", 0)) if audio else 0,
        "channels": int(audio.get("channels", 0)) if audio else 0,
        "width": width,
        "height": height,
        "rotation": rotation,
        "display_width": display_w,
        "display_height": display_h,
        "has_video": video is not None,
        "has_audio": audio is not None,
    }


def run(args: list[str]) -> None:
    """执行 ffmpeg 命令，失败时抛出带 stderr 的异常。"""
    _require("ffmpeg")
    proc = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败：{' '.join(args[:6])}...\n{proc.stderr[-800:]}")


def extract_frame(video: str | Path, timestamp: float, dest: str | Path) -> Path:
    """从视频中抽取一帧存为 JPG。"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["-ss", f"{timestamp:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(dest)])
    return dest


def transcode_audio(src: str | Path, dest: str | Path,
                    sample_rate: int = 32000, bitrate: str = "128k") -> Path:
    """转成单声道 mp3（MiniMax 参考音频要求 WAV/MP3）。"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["-i", str(src), "-vn", "-ac", "1", "-ar", str(sample_rate),
         "-b:a", bitrate, str(dest)])
    return dest


RATIOS = {
    "21:9": (21, 9),
    "16:9": (16, 9),
    "4:3": (4, 3),
    "1:1": (1, 1),
    "3:4": (3, 4),
    "9:16": (9, 16),
}


def resolve_ratio(ratio: str, src: str | Path) -> str:
    """把 auto 解析成素材自身的宽高比（竖屏素材 → 9:16，横屏 → 16:9）。"""
    if ratio != "auto":
        if ratio not in RATIOS:
            raise ValueError(f"不支持的宽高比：{ratio}")
        return ratio
    info = probe(src)
    width, height = info["display_width"], info["display_height"]
    if not width or not height:
        return "16:9"
    best = min(RATIOS.items(), key=lambda item: abs(item[1][0] / item[1][1] - width / height))
    return best[0]


def normalize_ratio(src: str | Path, dest: str | Path, ratio: str = "auto",
                    max_width: int = 1440) -> Path:
    """把视频统一成目标宽高比（cover 居中裁切），并抹平旋转元数据。

    H3 会把参考素材放进固定比例的内容区，素材比例与输出画布不一致就会留黑边，
    因此上传前先在本地裁到目标比例。ffmpeg 默认已应用旋转元数据，滤镜看到的是观感尺寸。
    """
    ratio = resolve_ratio(ratio, src)
    ratio_w, ratio_h = RATIOS[ratio]
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    info = probe(src)
    src_w, src_h = info["display_width"], info["display_height"]
    if not src_w or not src_h:
        raise RuntimeError(f"读不到视频尺寸：{src}")
    target = ratio_w / ratio_h
    source_ratio = src_w / src_h
    if source_ratio > target:          # 源更宽，裁掉左右
        out_w, out_h = src_h * target, src_h
    else:                              # 源更高（或等比），裁掉上下
        out_w, out_h = src_w, src_w / target
    out_w, out_h = int(round(out_w)), int(round(out_h))
    out_w -= out_w % 2
    out_h -= out_h % 2
    if out_w > max_width:
        out_h = int(round(out_h * max_width / out_w))
        out_w = max_width

    vf = (f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
          f"crop={out_w}:{out_h}")
    run(["-i", str(src), "-map", "0:v:0", "-vf", vf, "-an",
         "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(dest)])
    return dest


def detect_silences(src: str | Path, noise_db: int = -32, min_duration: float = 0.3) -> list[tuple[float, float]]:
    """检测静音区间 [(开始, 结束), ...]。"""
    _require("ffmpeg")
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(src), "-af",
         f"silencedetect=noise={noise_db}dB:d={min_duration}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    silences: list[tuple[float, float]] = []
    start: Optional[float] = None
    for line in proc.stderr.splitlines():
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].split()[0])
        elif "silence_end:" in line and start is not None:
            end = float(line.split("silence_end:")[1].split()[0])
            silences.append((start, end))
            start = None
    return silences


def split_audio(src: str | Path, out_dir: str | Path, *,
                max_seconds: float = 14.0, prefix: str = "seg") -> list[Path]:
    """把音频按静音点切成不超过 max_seconds 的片段。

    MiniMax H3 的参考音频单段上限 15 秒，因此这里留 1 秒余量。
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = probe(src)["duration"]
    if duration <= max_seconds:
        dest = out_dir / f"{prefix}_001.mp3"
        return [transcode_audio(src, dest)]

    cuts = [(s + e) / 2 for s, e in detect_silences(src) if (e - s) >= 0.25]
    spans: list[tuple[float, float]] = []
    start = 0.0
    while start < duration - 0.05:
        target = start + max_seconds
        if target >= duration - 0.05:
            spans.append((start, duration))
            break
        candidates = [c for c in cuts if start + 1.0 < c < target]
        end = max(candidates) if candidates else target
        spans.append((start, end))
        start = end

    segments: list[Path] = []
    for idx, (begin, end) in enumerate(spans, start=1):
        dest = out_dir / f"{prefix}_{idx:03d}.mp3"
        run(["-ss", f"{begin:.3f}", "-t", f"{end - begin:.3f}", "-i", str(src),
             "-vn", "-ac", "1", "-ar", "32000", "-b:a", "128k", str(dest)])
        segments.append(dest)
    return segments


def stream_duration(path: str | Path, kind: str = "v") -> float:
    """读取单条流的时长。

    容器 duration 与视频流时长可能略有出入（mux 后的分段视频比音频短几十毫秒），
    计算转场偏移时以视频流时长为准，避免淡入淡出在尾部重叠。
    """
    _require("ffprobe")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", f"{kind}:0",
         "-show_entries", "stream=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    lines = [line for line in out.stdout.strip().splitlines() if line]
    if not lines:
        return 0.0
    try:
        return float(lines[0])
    except ValueError:
        return 0.0


def frame_rate(path: str | Path, default: float = 24.0) -> float:
    """读取视频帧率。

    xfade 要求输入是恒定帧率，而 settb/setpts 会把帧率重置成未知值，
    因此转场前必须按源帧率显式固定。
    """
    _require("ffprobe")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=avg_frame_rate", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    lines = [line for line in out.stdout.strip().splitlines() if line]
    if not lines or "/" not in lines[0]:
        return default
    num, _, den = lines[0].partition("/")
    try:
        rate = float(num) / float(den)
    except (ValueError, ZeroDivisionError):
        return default
    return rate if rate > 0 else default


def concat_videos(videos: Iterable[str | Path], dest: str | Path,
                  transition: float = 0.0) -> Path:
    """按顺序拼接视频。

    transition=0 时用 concat demuxer 无损拼接（各段编码参数一致时生效）；
    transition>0 时改用 xfade 做交叉淡化：视频与音频同步淡化（acrossfade），
    消除分段生成留下的取景位移与口型突变。
    """
    videos = [Path(v) for v in videos]
    if not videos:
        raise ValueError("没有待拼接的视频")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(videos) == 1:
        run(["-i", str(videos[0]), "-c", "copy", str(dest)])
        return dest
    if transition > 0:
        _concat_with_transition(videos, dest, transition)
        return dest

    list_file = dest.parent / f"{dest.stem}_concat.txt"
    list_file.write_text("".join(f"file '{v.resolve()}'\n" for v in videos))
    try:
        run(["-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(dest)])
    except RuntimeError:
        run(["-f", "concat", "-safe", "0", "-i", str(list_file),
             "-c:v", "libx264", "-crf", "18", "-c:a", "aac", str(dest)])
    finally:
        list_file.unlink(missing_ok=True)
    return dest


def _concat_with_transition(videos: list[Path], dest: Path, transition: float) -> None:
    """用 xfade / acrossfade 拼接，相邻段在接缝处交叉淡化。

    两个细节决定了这条链能不能跑通：
    - xfade 要求输入是恒定帧率，且**不能**在前面接 setpts（PTS-STARTPTS 会让帧率
      标记失效，后续 xfade 直接报 "The inputs needs to be a constant frame rate"）；
    - xfade 的输出同样会丢掉帧率标记，所以每次淡化后要再接一个 fps 节点。
    偏移量按容器时长递推，保证每次淡化正好落在两段交界处；音频用同样时长的
    acrossfade 淡化，保证音画同步。
    """
    container_durations = [probe(v)["duration"] for v in videos]
    video_durations = [stream_duration(v, "v") for v in videos]
    audio_durations = [stream_duration(v, "a") for v in videos]
    if not all(container_durations) or not all(video_durations) or not all(audio_durations):
        raise RuntimeError("读不到分段时长，无法计算转场偏移")
    transition = min(transition, min(container_durations) * 0.5, min(audio_durations) * 0.5)

    args: list[str] = []
    for path in videos:
        args += ["-i", str(path)]

    rate = frame_rate(videos[0])
    filters: list[str] = []
    for idx in range(len(videos)):
        filters.append(f"[{idx}:v]format=yuv420p,fps={rate},settb=AVTB[v{idx}]")
        filters.append(f"[{idx}:a]asetpts=PTS-STARTPTS[a{idx}]")

    for k in range(1, len(videos)):
        offset = sum(container_durations[:k]) - k * transition
        prev_v = "v0" if k == 1 else f"vx{k - 1}"
        prev_a = "a0" if k == 1 else f"ax{k - 1}"
        filters.append(
            f"[{prev_v}][v{k}]xfade=transition=fade:duration={transition:.3f}"
            f":offset={offset:.3f}[xf{k}]"
        )
        filters.append(
            f"[xf{k}]format=yuv420p,fps={rate},settb=AVTB[vx{k}]"
        )
        filters.append(
            f"[{prev_a}][a{k}]acrossfade=d={transition:.3f}:c1=tri:c2=tri[ax{k}]"
        )

    last = len(videos) - 1
    run([*args, "-filter_complex", ";".join(filters),
         "-map", f"[vx{last}]", "-map", f"[ax{last}]",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dest)])


def concat_audio(audios: Iterable[str | Path], dest: str | Path,
                 *, sample_rate: int = 44100, channels: int = 2) -> Path:
    """把多段音频首尾相接成一条完整音轨。

    用 concat filter 而不是 concat demuxer：mp3 是可变帧长编码且带 bit reservoir，
    demuxer 把多段 mp3 直接喂给编码器时会在帧边界处崩
    （`inadequate AVFrame plane padding` / `Error submitting audio frame`）。
    filter 走的是「先解码再拼接」，并用 aformat 统一采样率与声道——
    参数不一致的段落直接拼接会错位。

    输出编码跟随目标扩展名：`.wav` 走 PCM（无损中间文件），
    其余走 aac（可直接当最终音轨）。
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    paths = [Path(a) for a in audios]
    if not paths:
        raise RuntimeError("没有可拼接的音频")

    codec = (["-c:a", "pcm_s16le"] if dest.suffix.lower() == ".wav"
             else ["-c:a", "aac", "-b:a", "192k"])
    if len(paths) == 1:
        run(["-i", str(paths[0]), *codec, str(dest)])
        return dest

    layout = "stereo" if channels == 2 else "mono"
    args: list[str] = []
    for path in paths:
        args += ["-i", str(path)]

    filters: list[str] = []
    for idx in range(len(paths)):
        filters.append(
            f"[{idx}:a]aformat=sample_fmts=fltp:sample_rates={sample_rate}"
            f":channel_layouts={layout}[a{idx}]"
        )
    inputs = "".join(f"[a{idx}]" for idx in range(len(paths)))
    filters.append(f"{inputs}concat=n={len(paths)}:v=0:a=1[out]")

    run(args + ["-filter_complex", ";".join(filters), "-map", "[out]", *codec, str(dest)])
    return dest


def mux_audio(video: str | Path, audio: str | Path, dest: str | Path) -> Path:
    """用给定音频替换视频音轨（保证最终声音是克隆音色的原始无损版本）。

    视频流末尾用 tpad 克隆最后一帧补到音频长度：否则 -shortest 会按最后一个包的
    结束时刻截断，画面比声音早结束一百多毫秒，分段越多累计偏移越大（唇音不同步）。
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    audio_duration = probe(audio)["duration"]
    rate = frame_rate(video)
    # tpad 克隆末帧补足尾部，trim 再按音频时长精确裁断，使视频流与音频流等长
    vf = (f"[0:v]tpad=stop_mode=clone:stop_duration=2,"
          f"trim=0:{audio_duration:.3f},setpts=PTS-STARTPTS,fps={rate}[v]")
    run(["-i", str(video), "-i", str(audio),
         "-filter_complex", vf,
         "-map", "[v]", "-map", "1:a:0",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", str(dest)])
    return dest
