"""优云智算 ComfyUI REF2VA/H3 口播产线，严格串行执行。"""

from __future__ import annotations

import copy
import json
import math
import random
from pathlib import Path
from typing import Optional

from ..client.compshare import CompshareClient
from ..media.ffmpeg import (
    concat_videos,
    extract_frame,
    mux_audio,
    normalize_ratio,
    stream_duration,
)
from .talking_line import (
    EMOTION_SCENES,
    SegmentVideo,
    TalkingResult,
    build_prompt,
    mux_is_stale,
)
from .voice_line import VoiceSegment

H3_MODEL = "ComfyUI-H3-REF2VA"
H3_DEFAULT_PROMPT = "角色正面看向镜头，自然口播，口型与音频同步，画面稳定。{scene}"
WORKFLOW_PATH = Path(__file__).with_name("h3_r2v_workflow.json")


def build_h3_workflow(
    *,
    image_name: str,
    audio_name: str,
    duration: float,
    prompt: str,
    seed: int = -1,
) -> dict:
    """基于固定模板生成本段工作流，不修改模板文件。"""
    workflow = copy.deepcopy(json.loads(WORKFLOW_PATH.read_text(encoding="utf-8")))
    workflow["7"]["inputs"]["image"] = image_name
    workflow["1"]["inputs"]["audio"] = audio_name
    workflow["19"]["inputs"]["value"] = max(1, math.ceil(duration))
    workflow["28"]["inputs"]["text"] = prompt
    if seed < 0:
        seed = random.SystemRandom().randint(0, 2**53 - 1)
    workflow["23"]["inputs"]["seed"] = seed
    return workflow


def _upload_persona(
    client: CompshareClient,
    persona_asset: str | Path,
    out_dir: Path,
    persona_kind: str,
    ratio: str,
) -> str:
    """视频形象先按目标比例处理再取首帧；图片直接上传。"""
    if persona_kind != "video":
        return client.upload_image(persona_asset)
    normalized = normalize_ratio(
        persona_asset, out_dir / "h3_persona_normalized.mp4", ratio=ratio
    )
    reference = extract_frame(normalized, 0, out_dir / "h3_persona_reference.jpg")
    return client.upload_image(reference)


def generate_h3_videos(
    segments: list[VoiceSegment],
    *,
    persona_asset: str | Path,
    out_dir: str | Path,
    model: str = H3_MODEL,
    resolution: str = "832x480",
    ratio: str = "16:9",
    prompt_template: str = H3_DEFAULT_PROMPT,
    scene: str = "",
    persona_kind: str = "video",
    transition: float = 0.0,
    resume: bool = True,
    base_url: Optional[str] = None,
    seed: int = -1,
    task_timeout: int = 3600,
) -> TalkingResult:
    """逐段提交 H3，成功后立即替换为原始 TTS 音轨。

    已有成片直接复用；只有原始片时只重新 mux。只有真正需要生成时
    才连接云端并上传形象，完整缓存可离线续跑。
    """
    if ratio != "16:9" or resolution != "832x480":
        raise ValueError("当前 REF2VA 模板固定为 832x480、16:9，请使用 --ratio 16:9")
    out_dir = Path(out_dir)
    raw_dir = out_dir / "raw" / "h3"
    raw_dir.mkdir(parents=True, exist_ok=True)
    result = TalkingResult(model=model, resolution=resolution, ratio=ratio)
    client: Optional[CompshareClient] = None
    persona_ref = ""

    for seg in segments:
        if not seg.is_a_roll:
            continue
        raw_path = raw_dir / f"seg_{seg.index:03d}.mp4"
        final_path = out_dir / f"seg_{seg.index:03d}_h3.mp4"
        seg_scene = seg.scene or scene
        seg_emotion = EMOTION_SCENES.get(seg.emotion or "", "")
        remuxed = False

        if resume and final_path.exists() and not mux_is_stale(final_path):
            print(f"  [seg {seg.index:03d}] 已有成片，跳过生成")
            result.segments.append(
                SegmentVideo(
                    index=seg.index,
                    task_id="reused",
                    raw_path=raw_path,
                    final_path=final_path,
                    duration=stream_duration(final_path, "v") or seg.duration,
                    text=seg.text,
                    reused=True,
                    emotion=seg.emotion,
                    scene=seg_scene,
                )
            )
            continue
        if resume and raw_path.exists():
            print(f"  [seg {seg.index:03d}] 已有原始片，重新替换原始音轨")
            task_id = "reused-raw"
            mux_audio(raw_path, seg.audio_path, final_path)
            reused = True
            remuxed = True
        else:
            if client is None:
                client = CompshareClient(base_url)
                persona_ref = _upload_persona(
                    client, persona_asset, out_dir, persona_kind, ratio
                )
            print(f"  [seg {seg.index:03d}] 串行生成 H3（{seg.duration:.1f}s）…")
            audio_name = client.upload_audio(seg.audio_path)
            prompt = build_prompt(prompt_template, seg.text, seg_scene, seg_emotion)
            workflow = build_h3_workflow(
                image_name=persona_ref,
                audio_name=audio_name,
                duration=seg.duration,
                prompt=prompt,
                seed=seed,
            )
            task_id = client.submit(workflow)
            history = client.wait(task_id, timeout=task_timeout)
            client.download(client.video_output(history), raw_path)
            mux_audio(raw_path, seg.audio_path, final_path)
            reused = False

        duration = stream_duration(final_path, "v") or seg.duration
        print(f"    完成：{duration:.2f}s → {final_path.name}")
        result.segments.append(
            SegmentVideo(
                index=seg.index,
                task_id=task_id,
                raw_path=raw_path,
                final_path=final_path,
                duration=duration,
                text=seg.text,
                reused=reused,
                remuxed=remuxed,
                emotion=seg.emotion,
                scene=seg_scene,
            )
        )
    if result.segments:
        result.final_video = concat_videos(
            [seg.final_path for seg in result.segments],
            out_dir / "talking.mp4",
            transition=transition,
        )
    return result
