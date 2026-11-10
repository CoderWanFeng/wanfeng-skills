"""ai-digital-human：基于 MiniMax 开放平台的「声音 + 形象 + 口播」一体化生产工具。"""

from .client import (
    MiniMaxError,
    clone_voice,
    create_video_task,
    generate_image,
    list_voices,
    t2a,
    upload_file,
    wait_video_task,
)
from .pipeline import generate_persona_images, generate_talking_videos, synthesize_script
from .pricing import (
    count_charged_chars,
    estimate_cost,
    estimate_image_cost,
    estimate_video_cost,
)

__all__ = [
    "MiniMaxError",
    "clone_voice",
    "count_charged_chars",
    "create_video_task",
    "estimate_cost",
    "estimate_image_cost",
    "estimate_video_cost",
    "generate_image",
    "generate_persona_images",
    "generate_talking_videos",
    "list_voices",
    "synthesize_script",
    "t2a",
    "upload_file",
    "wait_video_task",
]
