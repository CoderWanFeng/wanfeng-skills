"""计费字符数与费用估算。

计费口径（见 MiniMax 定价文档）：
- 语音：1 个汉字计 2 个字符，其余字符各计 1 个；单位为「元 / 万字符」。
- 音色：每个音色首次用于合成时一次性收取「元 / 音色」。
- 视频：按输出视频时长计费，单位为「元 / 秒」，随模型与分辨率变化。
- 图像：按张计费。

以下三种出口不计 RMB，这里统一记 0：
- 软件积分（credits）：扣的是账号积分，不是钱；
- 自托管 H3（compshare）：API 费 0，实例费按开机时长另算；
- 本地 Ming：API 字符费 0。
"""

from __future__ import annotations

CREDITS_MODEL = "credits"
COMPSHARE_MODEL = "ComfyUI-H3-REF2VA"
LOCAL_TTS_MODEL = "Ming-3.0-tts"

# 各 TTS 模型单价，单位：元 / 万字符
UNIT_PRICE_PER_10K_CHARS = {
    "speech-2.8-hd": 3.50,
    "speech-2.6-hd": 3.50,
    "speech-02-hd": 3.50,
    "speech-01-hd": 3.50,
    "speech-2.8-turbo": 2.00,
    "speech-2.6-turbo": 2.00,
    "speech-02-turbo": 2.00,
    "speech-01-turbo": 2.00,
    # 本地模型不计 API 字符费；设备与电费不属于此处的外部 API 报价。
    "Ming-3.0-tts": 0.0,
}

# 每个音色首次用于合成时一次性收取的费用，单位：元 / 音色
VOICE_FEE = 9.90

# 视频单价，单位：元 / 秒，键为 (模型, 输出分辨率)
VIDEO_PRICE_PER_SECOND = {
    ("MiniMax-H3", "2K"): 0.80,
    ("MiniMax-H3", "768P"): 0.50,
    ("MiniMax-H3-Highspeed", "768P"): 0.40,
    ("MiniMax-H3-Highspeed", "480P"): 0.26,
    ("MiniMax-H3-Lite", "768P"): 0.26,
    ("MiniMax-H3-Lite", "480P"): 0.16,
    ("MiniMax-H3-Max", "768P"): 0.50,
    ("MiniMax-H3-Max", "480P"): 0.33,
}

# 图像单价，单位：元 / 张
IMAGE_PRICE_PER_IMAGE = 0.025

# 语音识别单价，单位：元 / 小时
ASR_PRICE_PER_HOUR = 2.50


def count_charged_chars(text: str) -> int:
    """返回按平台口径计算的计费字符数。"""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in text)


def estimate_cost(text: str, model: str = "speech-2.8-hd") -> float:
    """估算合成给定文本的费用，单位：元。"""
    price = UNIT_PRICE_PER_10K_CHARS.get(model)
    if price is None:
        raise KeyError(f"未知模型的计价单价：{model}")
    return count_charged_chars(text) / 10_000 * price


def estimate_video_cost(model: str, resolution: str, seconds: float) -> float:
    """估算外部 API 费用；积分、自托管 H3、本地合成的钱不在这里算。"""
    if model in (COMPSHARE_MODEL, CREDITS_MODEL):
        return 0.0
    price = VIDEO_PRICE_PER_SECOND.get((model, resolution))
    if price is None:
        raise KeyError(f"未知计价档位：{model} @ {resolution}")
    return seconds * price


def estimate_image_cost(count: int = 1) -> float:
    """估算图像生成费用，单位：元。"""
    return count * IMAGE_PRICE_PER_IMAGE
