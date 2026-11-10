"""视频生成接口（MiniMax H3 系列）。

支持三类任务：
- t2va：content 仅含 text
- i2va：content 含 first_frame / last_frame 图片
- r2va：content 含 reference_image / reference_video / reference_audio

r2va 是「克隆人的画面 + 我的声音」的关键：把克隆音色的音频作为 reference_audio
喂进去，提示词里写明「角色说话：…」，即可生成角色说话的画面。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

import requests

from .base import API_BASE, TIMEOUT, MiniMaxError, request_json

MODEL_RESOLUTIONS = {
    "MiniMax-H3": ("768P", "2K"),
    "MiniMax-H3-Highspeed": ("480P", "768P"),
    "MiniMax-H3-Lite": ("480P", "768P"),
    "MiniMax-H3-Max": ("480P", "768P"),
}

MODEL_DURATIONS = {
    "MiniMax-H3": range(4, 16),
    "MiniMax-H3-Highspeed": range(4, 16),
    "MiniMax-H3-Lite": range(4, 16),
    "MiniMax-H3-Max": range(5, 16),
}


def create_video_task(
    *,
    prompt: str,
    model: str = "MiniMax-H3-Lite",
    content: Optional[list] = None,
    resolution: str = "768P",
    duration: int = 5,
    ratio: str = "16:9",
    prompt_expansion_mode: Optional[str] = None,
) -> str:
    """创建视频生成任务，返回 task_id。"""
    if model not in MODEL_RESOLUTIONS:
        raise ValueError(f"未知视频模型：{model}")
    if resolution not in MODEL_RESOLUTIONS[model]:
        raise ValueError(f"{model} 不支持分辨率 {resolution}，可选：{MODEL_RESOLUTIONS[model]}")
    if duration not in MODEL_DURATIONS[model]:
        raise ValueError(f"{model} 不支持时长 {duration}s，可选：{list(MODEL_DURATIONS[model])}")
    if not prompt.strip():
        raise ValueError("prompt 不能为空")

    body: dict[str, Any] = {
        "model": model,
        "content": content or [{"type": "text", "text": prompt}],
        "resolution": resolution,
        "duration": duration,
        "ratio": ratio,
    }
    if prompt_expansion_mode:
        body["extra"] = {"prompt_expansion_mode": prompt_expansion_mode}

    payload = request_json("POST", f"{API_BASE}/v2/video_generation", json_body=body)
    return str(payload["task_id"])


def get_video_task(task_id: str) -> dict:
    """查询任务状态与结果。"""
    payload = request_json("GET", f"{API_BASE}/v2/query/video_generation/{task_id}", retries=1)
    return payload.get("task") or {}


def wait_video_task(task_id: str, *, timeout: int = 900, interval: int = 5) -> dict:
    """轮询直到任务成功或失败。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        task = get_video_task(task_id)
        status = task.get("status")
        if status == "succeeded":
            return task
        if status in ("failed", "cancelled"):
            raise MiniMaxError(-2, f"视频任务 {status}：{task.get('fail_code') or task.get('error') or '未知原因'}")
        time.sleep(interval)
    raise TimeoutError(f"等待视频任务超时（{timeout}s）：{task_id}")


def download_video(url: str, dest: str | Path) -> Path:
    """下载生成的视频（下载链接有时效，生成后应立即转存）。"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def content_item_text(text: str) -> dict:
    return {"type": "text", "text": text}


def content_item_image(url: str, role: str = "reference_image") -> dict:
    return {"type": "image_url", "image_url": {"url": url}, "role": role}


def content_item_video(url: str, role: str = "reference_video") -> dict:
    return {"type": "video_url", "video_url": {"url": url}, "role": role}


def content_item_audio(url: str, role: str = "reference_audio") -> dict:
    return {"type": "audio_url", "audio_url": {"url": url}, "role": role}
