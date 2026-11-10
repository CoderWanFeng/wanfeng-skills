"""MiniMax 开放平台客户端：语音、图像、视频、文件。"""

from .base import API_BASE, MiniMaxError, load_env_file
from .files import mm_ref, upload_file
from .image import download_image, generate_image
from .speech import T2AResult, clone_voice, list_voices, t2a
from .video import (
    content_item_audio,
    content_item_image,
    content_item_text,
    content_item_video,
    create_video_task,
    download_video,
    get_video_task,
    wait_video_task,
)

__all__ = [
    "API_BASE",
    "MiniMaxError",
    "T2AResult",
    "clone_voice",
    "content_item_audio",
    "content_item_image",
    "content_item_text",
    "content_item_video",
    "create_video_task",
    "download_image",
    "download_video",
    "generate_image",
    "get_video_task",
    "list_voices",
    "load_env_file",
    "mm_ref",
    "t2a",
    "upload_file",
    "wait_video_task",
]
