"""画面拆解：把口播稿拆成分镜表。

分镜表是两份信息合一的产物：

- **时间契约**（每段的 start / end / duration）——驱动 B-roll 渲染与剪辑对位。
  时间轴由真实音频驱动，改稿、换音色后重新合成即可自动重排。
- **画面需求**（这段要表达什么、用什么素材、什么风格、逐拍动作）——驱动 B-roll 制作。

分镜表是纯 JSON，可以直接手写或用 AI 细化。重新生成时，
人工填过的字段会被保留，只刷新时间轴与台词。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .pipeline.voice_line import (
    KIND_A,
    ScriptBlock,
    VoiceSegment,
    count_charged_chars,
    estimate_seconds,
    split_sentences,
)

# 人工细化时会被保留的字段：这些是创作决策，重新生成时不该被覆盖
MANUAL_FIELDS = ("purpose", "style", "assets", "beats")


@dataclass
class Beat:
    """段内的一拍：一个动作 / 一条信息点。"""

    at: float = 0.0     # 段内相对时间（秒）
    action: str = ""    # 这一拍画面上发生什么


@dataclass
class Shot:
    """一段镜头的完整拆解。"""

    index: int
    kind: str           # a 出镜口播 / b 只出声音
    text: str
    shot: int = 0       # 镜头序号，同号即同一镜头
    emotion: str = ""
    scene: str = ""
    note: str = ""
    purpose: str = ""   # 这段画面要表达什么
    style: str = ""     # 视觉风格
    assets: list[str] = field(default_factory=list)   # 素材清单（文件名）
    beats: list[Beat] = field(default_factory=list)   # 段内逐拍
    duration: float = 0.0
    start: float = 0.0
    end: float = 0.0
    audio: str = ""     # 分段音频文件名

    @property
    def is_a_roll(self) -> bool:
        return self.kind == KIND_A


def default_purpose(group: ScriptBlock) -> str:
    """给一段镜头写出默认的画面职责。"""
    if group.kind == KIND_A:
        emotion = group.emotion or "中性"
        scene = group.scene or "正面口播"
        return f"数字人出镜：{scene}，语气{emotion}"
    return group.note or "MG 动画：把这一段的信息讲清楚"


def build_beats(group: ScriptBlock, duration: float) -> list[Beat]:
    """按句子拆出段内的逐拍动作。

    一句话一拍是「完整意思」的最细粒度：每个信息点对应画面上一次变化，
    素材挂在口播讲到它的那一刻，而不是场景开始时全部摆出来。
    """
    sentences = split_sentences(group.text) or [group.text]
    weights = [max(estimate_seconds(s), 0.1) for s in sentences]
    total = sum(weights)
    span_total = duration if duration > 0 else estimate_seconds(group.text)

    beats: list[Beat] = []
    cursor = 0.0
    for sentence, weight in zip(sentences, weights):
        beats.append(Beat(at=round(cursor, 3), action=sentence))
        cursor += span_total * weight / total
    return beats


def match_assets(group: ScriptBlock, assets_dir: str | Path | None) -> list[str]:
    """按画面提示里的文件名，在素材目录里找对应的素材。

    匹配规则很严：提示里必须完整出现文件名（不含扩展名）。
    宁可不匹配，也不要错配——错配的素材比没有素材更糟。
    """
    if not assets_dir:
        return []
    folder = Path(assets_dir)
    if not folder.is_dir():
        return []
    hint = (group.note or "").strip()
    if not hint:
        return []
    hits = []
    for item in sorted(folder.iterdir()):
        if not item.is_file():
            continue
        if item.stem and item.stem in hint:
            hits.append(item.name)
    return hits


def build_storyboard(
    groups: list[ScriptBlock],
    *,
    durations: Optional[dict[int, float]] = None,
    assets_dir: str | Path | None = None,
) -> list[Shot]:
    """从分组台词生成一份分镜表初稿。

    durations 是「段序号 → 真实音频时长」。给了就用真实值（时间轴由音频驱动），
    没给就用字数估算，等合成声音后再刷新一次。
    """
    shots: list[Shot] = []
    cursor = 0.0
    for idx, group in enumerate(groups, start=1):
        duration = 0.0
        if durations:
            duration = durations.get(idx, 0.0)
        if duration <= 0:
            duration = estimate_seconds(group.text)
        shots.append(
            Shot(
                index=idx,
                kind=group.kind,
                text=group.text,
                shot=group.shot,
                emotion=group.emotion,
                scene=group.scene,
                note=group.note,
                purpose=default_purpose(group),
                assets=match_assets(group, assets_dir),
                beats=build_beats(group, duration),
                duration=round(duration, 3),
                start=round(cursor, 3),
                end=round(cursor + duration, 3),
            )
        )
        cursor += duration
    return shots


def shot_to_dict(shot: Shot) -> dict:
    return {
        "index": shot.index,
        "kind": "a" if shot.is_a_roll else "b",
        "shot": shot.shot,
        "text": shot.text,
        "emotion": shot.emotion,
        "scene": shot.scene,
        "note": shot.note,
        "purpose": shot.purpose,
        "style": shot.style,
        "assets": list(shot.assets),
        "beats": [{"at": b.at, "action": b.action} for b in shot.beats],
        "duration": shot.duration,
        "start": shot.start,
        "end": shot.end,
        "audio": shot.audio,
    }


def dict_to_shot(data: dict) -> Shot:
    return Shot(
        index=int(data.get("index", 0)),
        kind=data.get("kind", KIND_A),
        text=data.get("text", ""),
        shot=int(data.get("shot", 0)),
        emotion=data.get("emotion", ""),
        scene=data.get("scene", ""),
        note=data.get("note", ""),
        purpose=data.get("purpose", ""),
        style=data.get("style", ""),
        assets=list(data.get("assets") or []),
        beats=[Beat(at=float(b.get("at", 0)), action=b.get("action", ""))
               for b in (data.get("beats") or [])],
        duration=float(data.get("duration", 0)),
        start=float(data.get("start", 0)),
        end=float(data.get("end", 0)),
        audio=data.get("audio", ""),
    )


def load_storyboard(path: str | Path) -> Optional[dict]:
    """读回已有分镜表；文件不存在或损坏时返回 None。"""
    file = Path(path)
    if not file.is_file():
        return None
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def merge_storyboard(shots: list[Shot], existing: Optional[dict]) -> list[Shot]:
    """保留人工细化过的字段。

    重新生成时，时间轴和台词会变（改稿、换音色都会导致），
    但「这段要表达什么、挂什么素材、怎么动」是创作决策，不该被覆盖。
    """
    if not existing:
        return shots
    old = {int(item.get("index", 0)): item for item in existing.get("segments", [])}
    for shot in shots:
        prev = old.get(shot.index)
        if not prev:
            continue
        for key in MANUAL_FIELDS:
            value = prev.get(key)
            if not value:
                continue
            if key == "beats":
                shot.beats = [Beat(at=float(b.get("at", 0)), action=b.get("action", ""))
                              for b in value]
            elif key == "assets":
                shot.assets = list(value)
            else:
                setattr(shot, key, value)
    return shots


def restore_segments(shots: list[Shot], voice_dir: str | Path) -> list[VoiceSegment]:
    """从分镜表恢复分段，让各阶段之间靠磁盘产物衔接。

    B-roll 阶段写下的分镜表就是后续阶段的输入：数字人阶段直接读它，
    不需要重新合成声音（省掉一次 TTS 调用，也避免时间轴漂移）。
    """
    voice_dir = Path(voice_dir)
    segments: list[VoiceSegment] = []
    for shot in shots:
        audio = voice_dir / shot.audio if shot.audio else None
        segments.append(
            VoiceSegment(
                index=shot.index,
                text=shot.text,
                audio_path=audio,
                duration=shot.duration,
                charged_chars=count_charged_chars(shot.text),
                kind=shot.kind,
                note=shot.note,
                shot=shot.shot,
                emotion=shot.emotion,
                scene=shot.scene,
            )
        )
    return segments


def write_storyboard(
    shots: list[Shot],
    out_dir: str | Path,
    *,
    job: str = "",
    script_path: str | Path = "",
    voice: str = "",
    model: str = "",
) -> dict:
    """写出分镜表与时间契约。

    - `storyboard.json`：分镜表全文，含画面需求，可直接手改
    - `timeline.json`：纯时间契约，给外部 B-roll 渲染器消费
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = round(sum(s.duration for s in shots), 3)
    a_total = round(sum(s.duration for s in shots if s.is_a_roll), 3)
    b_total = round(sum(s.duration for s in shots if not s.is_a_roll), 3)

    payload = {
        "job": job,
        "script": str(script_path),
        "voice": voice,
        "model": model,
        "total_duration": total,
        "a_roll_duration": a_total,
        "b_roll_duration": b_total,
        "segments": [shot_to_dict(s) for s in shots],
    }
    storyboard_path = out_dir / "storyboard.json"
    storyboard_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    timeline = {
        "total_duration": total,
        "a_roll_duration": a_total,
        "b_roll_duration": b_total,
        "segments": [
            {
                "kind": "A" if s.is_a_roll else "B",
                "index": s.index,
                "text": s.text,
                "duration": s.duration,
                "audio": s.audio,
                "start": s.start,
                "end": s.end,
            }
            for s in shots
        ],
    }
    timeline_path = out_dir / "timeline.json"
    timeline_path.write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "payload": payload,
        "storyboard": storyboard_path,
        "timeline": timeline_path,
    }