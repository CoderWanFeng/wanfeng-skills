"""声音产线：口播文稿 → 克隆音色合成 → 分段音频。

按句分组后逐段合成，保证「每段音频 ↔ 每段台词」一一对应，
下游视频生成才能把台词写进提示词。

文稿可用标记区分镜头类型（用于 A-roll / B-roll 混合剪辑）：

    大家好，我是这个账号的作者。
    [[BROLL:展示聊天界面录屏]]
    今天这条视频从文稿到成片，只花了几分钟。

`[[BROLL]]` 之后的台词属于 B-roll 段落：只合成音频，不生成出镜画面，
剪辑时用 MG 动画或人工素材盖住。省下的正是视频模型的调用成本。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

from ..client.speech import Subtitle, t2a
from ..pricing import count_charged_chars, estimate_cost

# 中文播报速度约每秒 4 个汉字，留出余量后用于预估分段长度
CHARS_PER_SECOND = 4.0
SENTENCE_PATTERN = re.compile(r"[^。！？!?；;\n]+[。！？!?；;]?")
# 镜头类型标记：[[A]] / [[B]] / [[BROLL:画面提示]]
BLOCK_MARKER = re.compile(r"^\[\[(A|B|BROLL)(?::([^\]]*))?\]\]\s*$", re.IGNORECASE)
MARKER_INLINE = re.compile(r"\[\[(A|B|BROLL)(?::([^\]]*))?\]\]", re.IGNORECASE)

# 平台支持的情绪取值；fluent / whisper 仅 2.6 系列明确可用，2.8 不支持 whisper
EMOTIONS = (
    "happy", "sad", "angry", "fearful", "disgusted",
    "surprised", "calm", "fluent", "whisper",
)

KIND_A = "a"   # 出镜口播（A-roll）
KIND_B = "b"   # 只出声音，画面交给 B-roll


@dataclass
class ScriptBlock:
    """文稿中的一个镜头块。"""

    kind: str
    text: str
    note: str = ""
    shot: int = 0        # 镜头序号，同号即同一镜头（连续同类段落）
    emotion: str = ""    # 该段落的情绪，写进 TTS 的 voice_setting
    scene: str = ""      # 该段落的画面描述，写进视频提示词


@dataclass
class VoiceSegment:
    """一段台词与其对应音频。"""

    index: int
    text: str
    audio_path: Path
    duration: float
    charged_chars: int
    model: str = "speech-2.8-hd"
    kind: str = KIND_A
    note: str = ""
    shot: int = 0
    emotion: str = ""
    scene: str = ""
    subtitles: list[Subtitle] = field(default_factory=list)

    @property
    def is_a_roll(self) -> bool:
        """是否需要生成出镜画面。"""
        return self.kind == KIND_A

    @property
    def billed_cost(self) -> float:
        return estimate_cost(self.text, self.model)


@dataclass
class VoiceResult:
    """声音产线的产出。"""

    voice_id: str
    model: str
    segments: list[VoiceSegment] = field(default_factory=list)
    full_audio: Optional[Path] = None

    @property
    def total_duration(self) -> float:
        return sum(seg.duration for seg in self.segments)

    @property
    def total_chars(self) -> int:
        return sum(seg.charged_chars for seg in self.segments)

    @property
    def cost(self) -> float:
        return sum(seg.billed_cost for seg in self.segments)


def split_sentences(text: str) -> list[str]:
    """按中文标点切句，保留标点。"""
    cleaned = re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n"))
    sentences = [s.strip() for s in SENTENCE_PATTERN.findall(cleaned)]
    return [s for s in sentences if s]


def parse_marker(tag: str, body: str = "") -> tuple[str, dict[str, str]]:
    """解析镜头标记。

    tag 是类型部分（A / B / BROLL），body 是冒号后的字段部分。

    支持的写法：

        [[A]]                              → ("a", {})
        [[A:happy]]                        → ("a", {"emotion": "happy"})
        [[BROLL:展示聊天界面]]              → ("b", {"note": "展示聊天界面"})
        [[A:emotion=happy|scene=办公室]]    → ("a", {"emotion": "happy", "scene": "办公室"})

    第一个不带 `=` 的自由文本按镜头类型解释：A-roll 当作情绪，B-roll 当作画面提示；
    完整写法一律用 `键=值`，键限 emotion / scene / note，未识别的键忽略。
    """
    kind = KIND_B if tag.upper() in ("B", "BROLL") else KIND_A

    fields: dict[str, str] = {}
    free_text = ""
    for part in body.split("|"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, _, value = part.partition("=")
            key = key.strip().lower()
            if key in ("emotion", "scene", "note"):
                fields[key] = value.strip()
        elif not free_text:
            free_text = part

    if free_text:
        fields.setdefault("emotion" if kind == KIND_A else "note", free_text)
    return kind, fields


def split_blocks(text: str) -> list[ScriptBlock]:
    """按镜头标记把文稿切成块。

    标记可以独占一行，也可以内联在行首；未标记的内容沿用当前镜头类型，
    默认是 A-roll（出镜口播）。每个标记自包含——未指定的字段会被清空，
    避免上一段的情绪或场景串到下一段。
    """
    blocks: list[ScriptBlock] = []
    kind, note = KIND_A, ""
    emotion, scene = "", ""
    shot = 0
    buffer: list[str] = []

    def flush() -> None:
        content = " ".join(buffer).strip()
        buffer.clear()
        if content:
            blocks.append(
                ScriptBlock(
                    kind=kind, text=content, note=note,
                    emotion=emotion, scene=scene, shot=shot,
                )
            )

    def apply_marker(tag: str, body: str) -> None:
        nonlocal kind, note, emotion, scene, shot
        kind, fields = parse_marker(tag, body)
        note = fields.get("note", "")
        emotion = fields.get("emotion", "")
        scene = fields.get("scene", "")
        shot += 1

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = BLOCK_MARKER.match(line)
        if match:
            flush()
            apply_marker(match.group(1), match.group(2) or "")
            rest = line[match.end():].strip()
            if rest:
                buffer.append(rest)
            continue
        inline = MARKER_INLINE.match(line)
        if inline:
            flush()
            apply_marker(inline.group(1), inline.group(2) or "")
            line = line[inline.end():].strip()
            if not line:
                continue
        buffer.append(line)
    flush()
    return blocks


def group_sentences(sentences: list[str], max_seconds: float = 13.0) -> list[str]:
    """贪心把句子合并成不超过 max_seconds 的组。"""
    limit = max_seconds * CHARS_PER_SECOND
    groups: list[str] = []
    buffer = ""
    for sentence in sentences:
        candidate = buffer + sentence
        if buffer and count_charged_chars(candidate) / 2 > limit:
            groups.append(buffer)
            buffer = sentence
        else:
            buffer = candidate
    if buffer:
        groups.append(buffer)
    return groups


def estimate_seconds(text: str) -> float:
    """按字数估算朗读时长（秒）。"""
    return count_charged_chars(text) / 2 / CHARS_PER_SECOND


def merge_short_groups(
    groups: list[ScriptBlock],
    min_seconds: float = 4.0,
    max_seconds: float = 15.0,
) -> list[ScriptBlock]:
    """把过短的组并入同一镜头的后继组。

    视频模型单次请求最短 4 秒，一段 1 秒的台词同样按 4 秒计费。
    同镜头内的短段直接并入后一段，既省成本也少一个拼接点。
    """
    merged: list[ScriptBlock] = []
    for group in groups:
        if merged:
            prev = merged[-1]
            same_shot = prev.kind == group.kind and prev.shot == group.shot
            too_short = estimate_seconds(prev.text) < min_seconds
            fits = estimate_seconds(prev.text + group.text) <= max_seconds
            if same_shot and too_short and fits:
                merged[-1] = ScriptBlock(
                    kind=prev.kind,
                    text=prev.text + group.text,
                    note=prev.note,
                    shot=prev.shot,
                    emotion=prev.emotion,
                    scene=prev.scene,
                )
                continue
        merged.append(group)
    return merged


def group_script(text: str, max_seconds: float = 13.0) -> list[ScriptBlock]:
    """把文稿切成与镜头类型对应的台词组。

    分组不跨镜头边界：A-roll 与 B-roll 的台词必须各自独立成段，
    否则视频生成会把两种镜头混在一起。
    """
    groups: list[ScriptBlock] = []
    for block in split_blocks(text):
        for group in group_sentences(split_sentences(block.text), max_seconds=max_seconds):
            groups.append(
                ScriptBlock(
                    kind=block.kind, text=group, note=block.note,
                    emotion=block.emotion, scene=block.scene, shot=block.shot,
                )
            )
    return merge_short_groups(groups)


def synthesize_script(
    text: str,
    *,
    voice_id: str,
    out_dir: str | Path,
    model: str = "speech-2.8-hd",
    max_seconds: float = 13.0,
    emotion: Optional[str] = None,
    speed: float = 1.0,
    subtitles: bool = True,
) -> VoiceResult:
    """把口播文稿合成分段音频。

    subtitles=True 时同时取回逐句时间码，供剪辑对位与 SRT 生成使用。
    emotion 是全局兜底情绪；文稿里用 `[[A:happy]]` 指定的逐段情绪优先级更高。
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    groups = group_script(text, max_seconds=max_seconds)
    result = VoiceResult(voice_id=voice_id, model=model)

    for idx, group in enumerate(groups, start=1):
        if group.emotion and group.emotion not in EMOTIONS:
            print(f"  警告：第 {idx} 段情绪 {group.emotion!r} 不在平台支持列表内，已忽略")
            group = replace(group, emotion="")
        segment_audio = out_dir / f"seg_{idx:03d}.mp3"
        resp = t2a(group.text, model=model, voice_id=voice_id,
                   emotion=group.emotion or emotion,
                   speed=speed, subtitle_enable=subtitles)
        segment_audio.write_bytes(resp.audio)
        duration = resp.duration_ms / 1000 if resp.duration_ms else 0.0
        if duration <= 0:
            duration = count_charged_chars(group.text) / 2 / CHARS_PER_SECOND
        result.segments.append(
            VoiceSegment(
                index=idx,
                text=group.text,
                audio_path=segment_audio,
                duration=duration,
                charged_chars=resp.charged_chars or count_charged_chars(group.text),
                model=model,
                kind=group.kind,
                note=group.note,
                shot=group.shot,
                emotion=group.emotion,
                scene=group.scene,
                subtitles=resp.subtitles,
            )
        )
    return result
