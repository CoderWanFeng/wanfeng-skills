"""软件积分（credits）出镜后端：本地对齐与拼接，不调用任何接口。

Pro 的数字人画面有三种来源，这是成本为 0 的那一种：

1. 用户（或 AI）用软件自带的积分能力，逐段生成口播画面；
2. 片段按 `seg_001.mp4`、`seg_002.mp4` 的规则放进工作区的 `input/credits/`；
3. 本模块负责把每段片段对齐到对应的配音、按顺序拼接，产出和其他后端一致的
   `seg_XXX.mp4` + `talking.mp4` + `a_roll.json`。

它不做的事：不生成画面、不克隆声音、不改写台词。画面质量由积分模型决定，
口型只做时长对齐，做不到逐帧音素同步——这条边界必须向用户讲清楚。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from ..media.ffmpeg import concat_videos, mux_audio, probe, stream_duration
from .talking_line import SegmentVideo, TalkingResult
from .voice_line import VoiceSegment

CREDITS_MODEL = "credits"
CLIP_SUFFIXES = (".mp4", ".mov", ".m4v")
# 片段比配音短时，tpad 最多补 2 秒静帧；超过这个余量就只能重生成
TAIL_TOLERANCE = 1.8


class CreditsClipsMissing(RuntimeError):
    """缺失片段时抛出，附带可直接念给用户看的清单。"""

    def __init__(self, missing: list[dict], credits_dir: Path) -> None:
        self.missing = missing
        self.credits_dir = credits_dir
        names = "、".join(item["file"] for item in missing)
        super().__init__(f"{credits_dir} 里缺少 {len(missing)} 个片段：{names}")


@dataclass
class CreditsClip:
    index: int
    path: Path
    duration: float
    text: str
    audio_seconds: float

    @property
    def short_by(self) -> float:
        return round(self.audio_seconds - self.duration, 2)


def find_clip(credits_dir: Path, index: int) -> Optional[Path]:
    """按段号找片段，容忍 seg_001 / 001 / seg_1 三种命名。"""
    stems = (f"seg_{index:03d}", f"{index:03d}", f"seg_{index}", f"{index}")
    for stem in stems:
        for suffix in CLIP_SUFFIXES:
            candidate = credits_dir / f"{stem}{suffix}"
            if candidate.is_file():
                return candidate
    return None


def collect_clips(
    segments: Iterable[VoiceSegment], credits_dir: str | Path
) -> list[CreditsClip]:
    """把所有 A-roll 段对应的片段收齐；缺任何一个都抛 CreditsClipsMissing。"""
    credits_dir = Path(credits_dir)
    clips: list[CreditsClip] = []
    missing: list[dict] = []
    for seg in segments:
        if not seg.is_a_roll:
            continue
        path = find_clip(credits_dir, seg.index)
        if path is None:
            missing.append({
                "index": seg.index,
                "file": f"seg_{seg.index:03d}.mp4",
                "text": seg.text,
                "seconds": round(seg.duration, 1),
            })
            continue
        info = probe(path)
        clips.append(CreditsClip(
            index=seg.index,
            path=path,
            duration=info["duration"],
            text=seg.text,
            audio_seconds=seg.duration,
        ))
    if missing:
        raise CreditsClipsMissing(missing, credits_dir)
    return clips


def render_brief(segments: Iterable[VoiceSegment], dest: str | Path) -> Path:
    """写一份「用积分生成这些片段」的清单，文件名和时长都写死，照抄即可。"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 用软件积分生成这些片段",
        "",
        "每条都按下面的文件名保存到本工作区的 `input/credits/`，生成完重跑 `--stage digital`。",
        "",
        "| 保存为 | 需要时长 | 台词 |",
        "| --- | --- | --- |",
    ]
    for seg in segments:
        if not seg.is_a_roll:
            continue
        seconds = max(4, min(10, int(round(seg.duration + 0.4))))
        lines.append(f"| `seg_{seg.index:03d}.mp4` | ≥ {seconds} 秒 | {seg.text} |")
    lines += [
        "",
        "生成要求：",
        "",
        "- 用同一个形象参考帧，保证每段是同一张脸、同一件衣服、同一个背景；",
        "- 时长宁长不短：片段短于配音时只能补 2 秒静帧，再短就要重生成；",
        "- 台词只用来引导口型，最终音轨会被克隆音色覆盖，念错不影响成片声音。",
    ]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def generate_credits_videos(
    segments: list[VoiceSegment],
    *,
    credits_dir: str | Path,
    out_dir: str | Path,
    transition: float = 0.0,
    resume: bool = True,
) -> TalkingResult:
    """把 `input/credits/` 里的片段对齐配音并拼接，全程本地、零调用。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    clips = collect_clips(segments, credits_dir)
    by_index = {clip.index: clip for clip in clips}
    result = TalkingResult(model=CREDITS_MODEL, resolution="源片", ratio="源片")

    for seg in segments:
        if not seg.is_a_roll:
            continue
        clip = by_index[seg.index]
        final_path = out_dir / f"seg_{seg.index:03d}.mp4"
        reused = resume and final_path.exists()
        if reused:
            print(f"  [seg {seg.index:03d}] 已对齐过，跳过")
        else:
            if clip.short_by > TAIL_TOLERANCE:
                raise RuntimeError(
                    f"段 {seg.index:03d} 的片段只有 {clip.duration:.1f}s，"
                    f"配音需要 {clip.audio_seconds:.1f}s，短了 {clip.short_by:.1f}s。"
                    "补帧只能补 2 秒，请重新生成这一段（或把稿子这段拆短）。"
                )
            if clip.short_by > 0:
                print(f"  [seg {seg.index:03d}] 片段短 {clip.short_by:.1f}s，补末帧对齐")
            mux_audio(clip.path, seg.audio_path, final_path)
            if clip.duration < clip.audio_seconds - 0.2:
                print(f"  [seg {seg.index:03d}] 警告：成片可能提前收尾，建议重生成更长的片段")
            else:
                print(f"  [seg {seg.index:03d}] 对齐完成 {clip.audio_seconds:.1f}s")

        result.segments.append(SegmentVideo(
            index=seg.index,
            task_id="credits",
            raw_path=clip.path,
            final_path=final_path,
            duration=stream_duration(final_path, "v") or clip.audio_seconds,
            text=seg.text,
            reused=reused,
            emotion=seg.emotion,
            scene=seg.scene or "",
        ))

    if result.segments:
        result.final_video = concat_videos(
            [seg.final_path for seg in result.segments],
            out_dir / "talking.mp4",
            transition=transition,
        )
    return result
