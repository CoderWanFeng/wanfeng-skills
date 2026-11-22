"""形象产线：本人素材 → image-01 主体参考 → 克隆人的画面。

MiniMax 图像侧没有独立的「人脸克隆」模型，靠 subject_reference（type=character）
把本人的长相绑定到生成结果上。参考图要求是单人正面照片，所以视频素材会先抽帧。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..client.image import download_image, generate_image
from ..media.ffmpeg import extract_frame, probe, resolve_ratio
from ..pricing import estimate_image_cost

DEFAULT_PROMPT = (
    "{scene}。人物与参考图保持同一张脸、同一发型与五官特征，"
    "照片写实，高清，细节自然。"
)

DEFAULT_SCENES = [
    "正面半身像，纯色浅灰背景，专业影棚布光",
    "坐在办公室书桌前，笔记本电脑旁，自然窗光",
    "站在落地窗前，窗外是夜晚城市灯光",
    "面对镜头做产品分享演讲，手势自然，室内暖光",
]


@dataclass
class PersonaImage:
    """一张克隆人形象图。"""

    index: int
    path: Path
    reference_frame: Path
    prompt: str
    url: str


@dataclass
class PersonaResult:
    """形象产线的产出。"""

    model: str
    aspect_ratio: str
    images: list[PersonaImage] = field(default_factory=list)

    @property
    def cost(self) -> float:
        return estimate_image_cost(len(self.images))


def _frame_timestamps(duration: float, count: int) -> list[float]:
    """在视频中段均匀取帧，避开开头结尾的废片。"""
    if count <= 1 or duration <= 0:
        return [max(duration * 0.5, 0.0)]
    start = duration * 0.1
    span = duration * 0.8
    return [start + span * i / (count - 1) for i in range(count)]


def _prepare_references(persona_asset: Path, frames_dir: Path, count: int,
                        persona_kind: str) -> list[Path]:
    """准备 subject_reference 用的参考图（视频抽帧，图片直接用）。"""
    if persona_kind != "video":
        return [persona_asset]
    frames_dir.mkdir(parents=True, exist_ok=True)
    duration = probe(persona_asset)["duration"]
    return [
        extract_frame(persona_asset, ts, frames_dir / f"ref_{idx:03d}.jpg")
        for idx, ts in enumerate(_frame_timestamps(duration, count), start=1)
    ]


def generate_persona_images(
    persona_asset: str | Path,
    out_dir: str | Path,
    *,
    prompt_template: str = DEFAULT_PROMPT,
    model: str = "image-01",
    aspect_ratio: str = "auto",
    scenes: Optional[list[str]] = None,
    persona_kind: str = "video",
) -> PersonaResult:
    """生成若干张克隆人形象图。"""
    persona_asset = Path(persona_asset)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scene_list = list(scenes or DEFAULT_SCENES)
    if aspect_ratio == "auto":
        aspect_ratio = resolve_ratio("auto", persona_asset)

    references = _prepare_references(persona_asset, out_dir / "reference",
                                     len(scene_list), persona_kind)
    result = PersonaResult(model=model, aspect_ratio=aspect_ratio)

    for idx, (scene, reference) in enumerate(zip(scene_list, references), start=1):
        prompt = prompt_template.replace("{scene}", scene).strip()
        payload = generate_image(prompt, model=model, reference_image=reference,
                                 aspect_ratio=aspect_ratio, n=1)
        urls = ((payload.get("data") or {}).get("image_urls")) or []
        if not urls:
            raise RuntimeError(f"形象图生成失败：{payload}")
        dest = out_dir / f"portrait_{idx:03d}.jpg"
        download_image(urls[0], dest)
        result.images.append(
            PersonaImage(index=idx, path=dest, reference_frame=Path(reference),
                         prompt=prompt, url=urls[0])
        )
    return result
