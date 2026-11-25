"""占位预览片：在生成数字人之前，先用零成本的方式审节奏与分镜。

这一步对应「先做 B-roll 并确认效果」——把不花钱的部分做完整、审到位，
确认后才为数字人掏钱，避免「数字人生成了、B-roll 却要推翻重做」的白花钱。

画面规则：
- **A 段**（数字人出镜位）画成暖白留白，一眼能看出「这是留给数字人的座位」
- **B 段**（MG / 素材位）画成深灰；若该段匹配到素材，直接把素材放进去

音轨是完整的，所以可以直接审整片的节奏。
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from .ffmpeg import concat_audio, concat_videos, mux_audio, probe, run

# A 段留白位：暖白。刻意不用黑屏——黑屏容易被误认为渲染失败
A_ROLL_COLOR = "0xF5F0E8"
# B 段素材位：深灰，与留白位拉开对比
B_ROLL_COLOR = "0x2E3338"

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v"}

RATIO_SIZES = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:3": (1440, 1080),
    "3:4": (1080, 1440),
    "21:9": (2560, 1080),
}


def _even(value: int) -> int:
    return value - (value % 2)


def _size_for(ratio: str) -> tuple[int, int]:
    width, height = RATIO_SIZES.get(ratio, RATIO_SIZES["9:16"])
    return _even(width), _even(height)


def _scale_filter(width: int, height: int, fps: int) -> str:
    """cover 模式铺满画布，避免素材比例不同留下黑边。"""
    return (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},fps={fps}")


def _make_color_clip(dest: Path, color: str, duration: float,
                     width: int, height: int, fps: int) -> Path:
    run(["-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}:r={fps}:d={duration:.3f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(dest)])
    return dest


def _make_asset_clip(src: Path, dest: Path, duration: float,
                     width: int, height: int, fps: int) -> Path:
    """把一张图片或一段视频铺成指定时长的画面。"""
    vf = _scale_filter(width, height, fps)
    if src.suffix.lower() in IMAGE_SUFFIXES:
        run(["-loop", "1", "-i", str(src), "-t", f"{duration:.3f}", "-vf", vf,
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(dest)])
    else:
        run(["-i", str(src), "-t", f"{duration:.3f}", "-vf", vf,
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(dest)])
    return dest


def _concat_audio(audios: Iterable[Path], dest: Path) -> Path:
    """把各段音频拼成一条完整音轨。

    走 concat filter 而不是 concat demuxer：mp3 帧长可变且带 bit reservoir，
    demuxer 直接把多段 mp3 喂给编码器会在帧边界处崩。
    """
    return concat_audio(audios, dest)


def make_placeholder(
    shots,
    dest: str | Path,
    *,
    audio_paths: Optional[dict[int, Path]] = None,
    assets_dir: str | Path | None = None,
    ratio: str = "9:16",
    fps: int = 30,
    work_dir: Optional[str | Path] = None,
) -> Path:
    """生成占位预览片。

    shots 只用到 index / kind / duration / assets 四个字段，
    因此既接受分镜表里的 Shot，也接受任何同形的对象。
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    work = Path(work_dir) if work_dir else dest.parent / "placeholder"
    work.mkdir(parents=True, exist_ok=True)
    width, height = _size_for(ratio)
    assets_root = Path(assets_dir) if assets_dir else None

    clips: list[Path] = []
    used_assets: dict[int, str] = {}
    for shot in shots:
        duration = float(getattr(shot, "duration", 0.0) or 0.0)
        if duration <= 0:
            continue
        index = int(getattr(shot, "index", 0))
        kind = str(getattr(shot, "kind", "a"))
        clip = work / f"slot_{index:03d}.mp4"

        # 该段如果有匹配到的素材，优先放素材；否则画占位色
        source = None
        for name in getattr(shot, "assets", []) or []:
            candidate = assets_root / name if assets_root else None
            if candidate and candidate.is_file():
                source = candidate
                used_assets[index] = name
                break

        if source is not None:
            _make_asset_clip(source, clip, duration, width, height, fps)
        else:
            color = A_ROLL_COLOR if kind == "a" else B_ROLL_COLOR
            _make_color_clip(clip, color, duration, width, height, fps)
        clips.append(clip)

    if not clips:
        raise ValueError("没有可用的分段，无法生成占位片")

    silent = work / "silent.mp4"
    concat_videos(clips, silent, transition=0)

    if not audio_paths:
        return silent

    audios = [Path(audio_paths[i]) for i in sorted(audio_paths) if audio_paths[i]]
    if not audios:
        return silent
    # 中间音轨用 wav（PCM 无损），最终 mux 时由 mux_audio 统一转 aac，
    # 避免 aac → aac 二次有损编码
    full_audio = work / "audio.wav"
    _concat_audio(audios, full_audio)

    mux_audio(silent, full_audio, dest)
    return dest