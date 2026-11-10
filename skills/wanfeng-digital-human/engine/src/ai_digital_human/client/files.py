"""文件上传。

purpose=video_generation_input 的素材（首帧图/参考图/参考视频/参考音频）
会以 mm_file://{file_id} 形式在生成请求里引用，有效期 7 天。
"""

from __future__ import annotations

from pathlib import Path

import requests

from .base import API_BASE, TIMEOUT, headers, params, raise_for_status

SUPPORTED_PURPOSES = {
    "voice_clone",
    "prompt_audio",
    "t2a_async_input",
    "video_understanding",
    "video_generation_input",
}


def upload_file(path: str | Path, purpose: str = "video_generation_input") -> str:
    """上传文件，返回 file_id。

    - voice_clone：mp3/m4a/wav，10 秒 ~ 5 分钟，≤ 20MB
    - prompt_audio：mp3/m4a/wav，< 8 秒，≤ 20MB
    - video_generation_input：图片 ≤ 30MB / 视频 ≤ 50MB / 音频 ≤ 15MB，上传即校验规格
    """
    if purpose not in SUPPORTED_PURPOSES:
        raise ValueError(f"不支持的 purpose：{purpose}")

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"文件不存在：{path}")

    with path.open("rb") as fh:
        resp = requests.post(
            f"{API_BASE}/v1/files/upload",
            headers=headers(),
            params=params(),
            data={"purpose": purpose},
            files={"file": (path.name, fh)},
            timeout=TIMEOUT,
        )
    resp.raise_for_status()
    payload = raise_for_status(resp.json())
    return str(payload["file"]["file_id"])


def mm_ref(file_id: str | int) -> str:
    """生成 mm_file:// 引用串。"""
    return f"mm_file://{file_id}"
