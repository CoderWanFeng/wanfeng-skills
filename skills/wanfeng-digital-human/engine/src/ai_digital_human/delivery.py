"""A-roll 交付包：时间码表与字幕，供剪辑直接对位。

混合剪辑（A-roll 出镜口播 + B-roll 人工/MG 画面）时，剪辑师需要知道两件事：
每段口播在成片时间轴上的位置，以及这段台词的原文。

产出两个文件：
- a_roll.json：逐段时间码表，含镜头类型、画面提示、素材文件名
- a_roll.srt：全局字幕，时间码已按段偏移对齐到成片时间轴
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .pipeline.voice_line import KIND_A, VoiceSegment


@dataclass
class TimelineEntry:
    """一段台词在成片时间轴上的位置。"""

    index: int
    kind: str
    note: str
    text: str
    audio_path: Path
    start: float
    end: float
    video_path: Optional[Path] = None
    shot: int = 0
    emotion: str = ""
    scene: str = ""
    subtitles: list = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def is_a_roll(self) -> bool:
        return self.kind == KIND_A


def build_timeline(
    segments: list[VoiceSegment],
    videos: Optional[dict[int, Path]] = None,
) -> list[TimelineEntry]:
    """按顺序给每段计算全局入出点。

    B-roll 段同样占时间轴位置（它有旁白），只是没有对应的视频文件。
    """
    videos = videos or {}
    entries: list[TimelineEntry] = []
    cursor = 0.0
    for seg in segments:
        entries.append(
            TimelineEntry(
                index=seg.index,
                kind=seg.kind,
                note=seg.note,
                text=seg.text,
                audio_path=Path(seg.audio_path),
                start=round(cursor, 3),
                end=round(cursor + seg.duration, 3),
                video_path=videos.get(seg.index),
                shot=seg.shot,
                emotion=seg.emotion,
                scene=seg.scene,
                subtitles=list(seg.subtitles),
            )
        )
        cursor += seg.duration
    return entries


def _srt_time(seconds: float) -> str:
    """秒 → SRT 时间戳 HH:MM:SS,mmm。"""
    ms = int(round(max(0.0, seconds) * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def build_srt(entries: list[TimelineEntry]) -> str:
    """生成全局字幕文本。

    每段自带的字幕时间码是相对该段音频起点的，这里按段落起点偏移成全局时间码。
    拿不到逐句字幕时退化为整段一条。
    """
    blocks: list[str] = []
    counter = 1
    for entry in entries:
        if entry.subtitles:
            for sub in entry.subtitles:
                begin = entry.start + sub.time_begin / 1000
                end = entry.start + sub.time_end / 1000
                blocks.append(
                    f"{counter}\n{_srt_time(begin)} --> {_srt_time(end)}\n{sub.text}\n"
                )
                counter += 1
        else:
            blocks.append(
                f"{counter}\n{_srt_time(entry.start)} --> {_srt_time(entry.end)}\n{entry.text}\n"
            )
            counter += 1
    return "\n".join(blocks)


def attach_videos(json_path: str | Path, videos: dict[int, Path]) -> dict:
    """把已生成的 A-roll 视频回填到时间码表。

    分阶段流程里，音频与时间码在 B-roll 阶段就写好了，
    数字人视频在后面的阶段才生成——这一步只补 video 字段，不动时间码与字幕。
    """
    path = Path(json_path)
    if not path.is_file():
        raise FileNotFoundError(f"时间码表不存在：{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    for seg in payload.get("segments", []):
        video = videos.get(int(seg.get("index", 0)))
        seg["video"] = video.name if video else None
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def write_delivery(
    segments: list[VoiceSegment],
    out_dir: str | Path,
    *,
    job: str = "",
    videos: Optional[dict[int, Path]] = None,
    script_path: str | Path = "",
) -> dict:
    """写出 A-roll 交付包，返回时间码表数据。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = build_timeline(segments, videos)

    payload = {
        "job": job,
        "script": str(script_path),
        "total_duration": round(entries[-1].end if entries else 0.0, 3),
        "a_roll_duration": round(
            sum(e.duration for e in entries if e.is_a_roll), 3
        ),
        "b_roll_duration": round(
            sum(e.duration for e in entries if not e.is_a_roll), 3
        ),
        "segments": [
            {
                "index": e.index,
                "kind": "a" if e.is_a_roll else "b",
                "shot": e.shot,
                "emotion": e.emotion,
                "scene": e.scene,
                "note": e.note,
                "text": e.text,
                "audio": e.audio_path.name,
                "video": e.video_path.name if e.video_path else None,
                "start": e.start,
                "end": e.end,
                "duration": round(e.duration, 3),
            }
            for e in entries
        ],
    }

    json_path = out_dir / "a_roll.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    srt_path = out_dir / "a_roll.srt"
    srt_path.write_text(build_srt(entries), encoding="utf-8")

    payload["_files"] = {"json": str(json_path), "srt": str(srt_path)}
    return payload
