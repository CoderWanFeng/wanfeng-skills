"""晚枫数字人（轻量版）引擎：只做本地媒体处理。

这条技能的画面由软件自带的积分能力生成，声音由模型自己念——**不调用任何接口**，
所以引擎里没有任何 API 客户端、没有计价、没有密钥。留下的只有 ffmpeg 封装：
读素材、抽参考帧、裁比例、贴音轨、挂字幕。
"""

from .media import (
    concat_audio,
    concat_videos,
    detect_silences,
    extract_frame,
    frame_rate,
    mux_audio,
    normalize_ratio,
    probe,
    resolve_ratio,
    split_audio,
    stream_duration,
    transcode_audio,
)

__all__ = [
    "concat_audio",
    "concat_videos",
    "detect_silences",
    "extract_frame",
    "frame_rate",
    "mux_audio",
    "normalize_ratio",
    "probe",
    "resolve_ratio",
    "split_audio",
    "stream_duration",
    "transcode_audio",
]
