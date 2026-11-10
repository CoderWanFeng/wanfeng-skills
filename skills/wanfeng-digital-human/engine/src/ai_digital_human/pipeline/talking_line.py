"""口播产线：克隆人形象素材 + 克隆音色音频 → H3 口播视频。

每个音频片段单独生成一段视频（参考音频单段 ≤ 15 秒），
拼接后再用原始 TTS 音频覆盖音轨，保证最终声音是克隆音色的无损版本。
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..client.files import mm_ref, upload_file
from ..client.video import (
    content_item_audio,
    content_item_image,
    content_item_text,
    content_item_video,
    create_video_task,
    download_video,
    wait_video_task,
)
from ..media.ffmpeg import (
    concat_videos,
    frame_rate,
    mux_audio,
    normalize_ratio,
    probe,
    resolve_ratio,
    stream_duration,
)
from .voice_line import VoiceSegment

DEFAULT_PROMPT = "角色说：{line} 音色参考音频1，画面稳定，角色正面看向镜头，自然口播。{scene}"

# 情绪 → 画面表情与语气的中文描述。
# 逐段生成时把情绪同步写进提示词，声音有起伏的同时画面表情也跟上。
EMOTION_SCENES = {
    "happy": "语气轻快，语调上扬，面带微笑，眼神明亮",
    "sad": "语气低落，语调下沉，神情落寞",
    "angry": "语气强烈，语调加重，表情严肃有力",
    "fearful": "语气紧张，语速略快，神情不安",
    "disgusted": "语气嫌弃，语调下压，表情不悦",
    "surprised": "语气惊讶，语调上扬，睁大双眼",
    "calm": "语气沉稳，语速平稳，表情放松自然",
    "fluent": "语气自然流畅，节奏明快",
    "whisper": "气声低语，音量偏轻，微微前倾",
}


def mux_is_stale(video: str | Path, tolerance_frames: int = 2) -> bool:
    """判断已 mux 的分段是否需要重做。

    视频流比音频流短超过若干帧，说明音轨与画面对不齐（唇音不同步），
    这种情况多半来自旧版 mux 逻辑，应当重新替换音轨。
    """
    try:
        video_len = stream_duration(video, "v")
        audio_len = stream_duration(video, "a")
    except Exception:
        return True
    if not video_len or not audio_len:
        return True
    rate = frame_rate(video)
    return abs(video_len - audio_len) > tolerance_frames / rate


@dataclass
class SegmentVideo:
    """一段视频的生成结果。"""

    index: int
    task_id: str
    raw_path: Path
    final_path: Path
    duration: float
    text: str
    reused: bool = False
    remuxed: bool = False
    emotion: str = ""
    scene: str = ""


@dataclass
class TalkingResult:
    """口播产线的产出。"""

    model: str
    resolution: str
    ratio: str
    segments: list[SegmentVideo] = field(default_factory=list)
    final_video: Optional[Path] = None

    @property
    def total_duration(self) -> float:
        return sum(seg.duration for seg in self.segments)


def build_prompt(template: str, line: str, scene: str = "", emotion: str = "") -> str:
    """拼装视频提示词。

    模板带 `{emotion}` 占位符时情绪单独占位；没有则并入 `{scene}`，
    这样旧模板不改动也能吃到情绪描述。
    """
    if "{emotion}" in template:
        text = template.replace("{emotion}", emotion).replace("{scene}", scene)
    else:
        merged = "，".join(part for part in (emotion, scene) if part)
        text = template.replace("{scene}", merged)
    return text.replace("{line}", line).strip()


def _persona_content(persona_ref: str, persona_kind: str) -> dict:
    if persona_kind == "video":
        return content_item_video(persona_ref, role="reference_video")
    return content_item_image(persona_ref, role="reference_image")


def _upload_persona(persona_asset: str | Path, out_dir: Path, persona_kind: str, ratio: str) -> str:
    """上传形象素材；视频先在本地裁到目标比例，避免 H3 输出留黑边。"""
    if persona_kind == "video":
        normalized = normalize_ratio(persona_asset, out_dir / "persona_normalized.mp4", ratio=ratio)
        return mm_ref(upload_file(normalized, purpose="video_generation_input"))
    return mm_ref(upload_file(persona_asset, purpose="video_generation_input"))


def generate_talking_videos(
    segments: list[VoiceSegment],
    *,
    persona_asset: str | Path,
    out_dir: str | Path,
    model: str = "MiniMax-H3-Lite",
    resolution: str = "768P",
    ratio: str = "auto",
    prompt_template: str = DEFAULT_PROMPT,
    scene: str = "",
    persona_kind: str = "video",
    wait_timeout: int = 900,
    max_workers: int = 4,
    transition: float = 0.0,
    resume: bool = True,
) -> TalkingResult:
    """逐段生成口播视频并拼接。

    max_workers>1 时并发提交视频任务，长视频的等待时间能压到串行的 1/max_workers；
    resume=True 时复用已存在的分段文件（跳过接口调用），中途失败重跑不会白等。
    """
    out_dir = Path(out_dir)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # B-roll 段只出旁白、不生成画面，这里直接跳过，省下的是视频模型的调用成本
    roll_segments = [seg for seg in segments if seg.is_a_roll]

    # H3-Lite 不支持 adaptive，必须显式指定比例；auto 时按素材自身的观感比例取。
    ratio = resolve_ratio(ratio, persona_asset)
    persona_ref = _upload_persona(persona_asset, out_dir, persona_kind, ratio)
    result = TalkingResult(model=model, resolution=resolution, ratio=ratio)

    def produce(seg: VoiceSegment) -> SegmentVideo:
        """生成一段视频；已存在且允许续跑时复用。"""
        final_path = out_dir / f"seg_{seg.index:03d}.mp4"
        raw_path = raw_dir / f"seg_{seg.index:03d}.mp4"
        # 逐段取场景与情绪：文稿里指定的优先于全局默认值
        seg_scene = seg.scene or scene
        seg_emotion = EMOTION_SCENES.get(seg.emotion or "", "")
        if resume and final_path.is_file() and raw_path.is_file():
            if mux_is_stale(final_path):
                # 旧版 mux 留下的音画不对齐，只重做换音轨这一步，不重新生成视频
                mux_audio(raw_path, seg.audio_path, final_path)
                return SegmentVideo(
                    index=seg.index, task_id="", raw_path=raw_path, final_path=final_path,
                    duration=probe(final_path)["duration"], text=seg.text,
                    reused=True, remuxed=True,
                    emotion=seg.emotion, scene=seg_scene,
                )
            return SegmentVideo(
                index=seg.index, task_id="", raw_path=raw_path, final_path=final_path,
                duration=probe(final_path)["duration"], text=seg.text, reused=True,
                emotion=seg.emotion, scene=seg_scene,
            )

        audio_ref = mm_ref(upload_file(seg.audio_path, purpose="video_generation_input"))
        prompt = build_prompt(prompt_template, seg.text, seg_scene, seg_emotion)
        content = [
            content_item_text(prompt),
            _persona_content(persona_ref, persona_kind),
            content_item_audio(audio_ref, role="reference_audio"),
        ]
        duration = max(4, min(15, int(round(seg.duration + 0.5))))
        task_id = create_video_task(
            prompt=prompt,
            model=model,
            content=content,
            resolution=resolution,
            duration=duration,
            ratio=ratio,
        )
        task = wait_video_task(task_id, timeout=wait_timeout)
        url = ((task.get("content") or {}).get("url")) or ""
        if not url:
            raise RuntimeError(f"任务 {task_id} 没有返回视频链接")

        download_video(url, raw_path)
        mux_audio(raw_path, seg.audio_path, final_path)
        return SegmentVideo(
            index=seg.index, task_id=task_id, raw_path=raw_path, final_path=final_path,
            duration=probe(final_path)["duration"], text=seg.text,
            emotion=seg.emotion, scene=seg_scene,
        )

    workers = max(1, min(max_workers, len(roll_segments)))
    produced: dict[int, SegmentVideo] = {}
    failures: list[tuple[int, Exception]] = []

    if workers == 1:
        for seg in roll_segments:
            produced[seg.index] = produce(seg)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(produce, seg): seg for seg in roll_segments}
            done = 0
            for future in as_completed(futures):
                seg = futures[future]
                try:
                    produced[seg.index] = future.result()
                except Exception as exc:  # 收集全部失败项后再统一抛出
                    failures.append((seg.index, exc))
                done += 1
                state = "失败" if any(i == seg.index for i, _ in failures) else "完成"
                print(f"  视频段 {done}/{len(roll_segments)} {state}（seg_{seg.index:03d}）", flush=True)

    if failures:
        detail = "；".join(f"seg_{i:03d}: {exc}" for i, exc in failures)
        raise RuntimeError(f"{len(failures)} 段生成失败：{detail}")

    result.segments = [produced[seg.index] for seg in roll_segments]
    if result.segments:
        result.final_video = concat_videos(
            [seg.final_path for seg in result.segments],
            out_dir / "talking.mp4",
            transition=transition,
        )
    return result
