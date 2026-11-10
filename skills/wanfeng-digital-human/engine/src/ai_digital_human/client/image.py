"""图像生成接口。

subject_reference（type=character）用于保持人物主体特征一致，
是 MiniMax 图像侧唯一的「形象克隆」能力。
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import requests

from .base import API_BASE, TIMEOUT, request_json


def _image_reference(image: str | Path) -> str:
    """接受公网 URL、Base64 Data URL，或本地图片路径（转 Data URL）。"""
    text = str(image)
    if text.startswith("http") or text.startswith("data:"):
        return text
    path = Path(image)
    if not path.is_file():
        raise FileNotFoundError(f"参考图不存在：{path}")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp"}.get(path.suffix.lower().lstrip("."), "image/jpeg")
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def generate_image(
    prompt: str,
    *,
    model: str = "image-01",
    reference_image: Optional[str | Path] = None,
    aspect_ratio: str = "16:9",
    style_type: Optional[str] = None,
    n: int = 1,
    seed: Optional[int] = None,
    response_format: str = "url",
) -> dict:
    """生成图片。

    reference_image 传入后即为主体参考（人物形象一致性）。
    style_type 仅在 model=image-01-live 时生效，可选：漫画、元气、中世纪、水彩。
    """
    body: dict = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "n": n,
        "response_format": response_format,
    }
    if reference_image:
        body["subject_reference"] = [
            {"type": "character", "image_file": _image_reference(reference_image)}
        ]
    if style_type:
        body["style"] = {"style_type": style_type, "style_weight": 0.8}
    if seed is not None:
        body["seed"] = seed

    return request_json("POST", f"{API_BASE}/v1/image_generation", json_body=body)


def download_image(url: str, dest: str | Path) -> Path:
    """下载生成的图片（链接有时效，生成后应立即转存）。"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest
