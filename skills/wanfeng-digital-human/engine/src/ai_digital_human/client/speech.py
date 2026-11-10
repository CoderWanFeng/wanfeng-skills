"""语音相关接口：同步合成、音色复刻、音色查询。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

from .base import API_BASE, TIMEOUT, MiniMaxError, headers, params, raise_for_status


@dataclass
class Subtitle:
    """一条带时间码的字幕（时间码相对所属音频的起点，单位毫秒）。"""

    text: str
    time_begin: float
    time_end: float


@dataclass
class T2AResult:
    """一次语音合成的结果。"""

    audio: bytes
    audio_format: str
    duration_ms: int
    charged_chars: int
    trace_id: str
    subtitles: list[Subtitle] = field(default_factory=list)

    @property
    def file_suffix(self) -> str:
        return {"mp3": ".mp3", "pcm": ".pcm", "flac": ".flac"}.get(self.audio_format, ".bin")


def t2a(
    text: str,
    *,
    model: str = "speech-2.8-hd",
    voice_id: str = "male-qn-qingse",
    speed: float = 1.0,
    vol: float = 1.0,
    pitch: int = 0,
    emotion: Optional[str] = None,
    audio_format: str = "mp3",
    sample_rate: int = 32000,
    bitrate: int = 128000,
    language_boost: Optional[str] = "Chinese",
    subtitle_enable: bool = False,
    output_format: str = "hex",
    retries: int = 2,
) -> T2AResult:
    """同步语音合成。

    文本长度需小于 10000 字符；超过 3000 字符建议改用异步长文本接口。
    """
    if len(text) >= 10_000:
        raise ValueError("单次文本长度需小于 10000 字符，请改用异步长文本语音合成接口")

    voice_setting: dict[str, Any] = {
        "voice_id": voice_id,
        "speed": speed,
        "vol": vol,
        "pitch": pitch,
    }
    if emotion:
        voice_setting["emotion"] = emotion

    body: dict[str, Any] = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": voice_setting,
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
            "channel": 1,
        },
        "subtitle_enable": subtitle_enable,
        "output_format": output_format,
    }
    if language_boost:
        body["language_boost"] = language_boost

    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                f"{API_BASE}/v1/t2a_v2",
                headers=headers({"Content-Type": "application/json"}),
                params=params(),
                json=body,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return _parse_t2a(raise_for_status(resp.json()), audio_format)
        except (requests.RequestException, MiniMaxError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise last_error  # type: ignore[misc]


def _parse_t2a(payload: dict, audio_format: str) -> T2AResult:
    data = payload.get("data") or {}
    extra = payload.get("extra_info") or {}
    raw = data.get("audio") or ""
    if not raw:
        raise MiniMaxError(-1, "响应中没有音频数据", payload.get("trace_id", ""))
    if raw.startswith("http"):
        audio = requests.get(raw, timeout=TIMEOUT).content
    else:
        audio = bytes.fromhex(raw)
    return T2AResult(
        audio=audio,
        audio_format=extra.get("audio_format") or audio_format,
        duration_ms=int(extra.get("audio_length") or 0),
        charged_chars=int(extra.get("usage_characters") or 0),
        trace_id=payload.get("trace_id", ""),
        subtitles=_fetch_subtitles(data.get("subtitle_file") or ""),
    )


def _fetch_subtitles(url: str) -> list[Subtitle]:
    """下载并解析字幕文件。

    字幕接口返回一组带毫秒级时间码的片段，时间码相对该条音频的起点，
    是剪辑对位与 SRT 生成的直接依据。
    """
    if not url:
        return []
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    try:
        items = resp.json()
    except ValueError:
        return []
    subtitles: list[Subtitle] = []
    for item in items or []:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        subtitles.append(
            Subtitle(
                text=text,
                time_begin=float(item.get("time_begin") or 0),
                time_end=float(item.get("time_end") or 0),
            )
        )
    return subtitles


def clone_voice(
    file_id: str | int,
    voice_id: str,
    *,
    text: str,
    model: str = "speech-2.8-hd",
    prompt_audio: Optional[str | int] = None,
    prompt_text: Optional[str] = None,
) -> dict:
    """音色快速复刻，并返回试听结果。

    file_id 为待复刻音频的 file_id；voice_id 为自定义音色 ID（8-256 位，字母开头）。
    prompt_audio / prompt_text 为可选的示例音频及其准确文本，用于提升相似度。
    注意：复刻得到的音色若 7 天内未正式调用会被系统删除。
    """
    body: dict[str, Any] = {
        "file_id": int(file_id),
        "voice_id": voice_id,
        "text": text,
        "model": model,
    }
    if prompt_audio:
        body["clone_prompt"] = {"prompt_audio": int(prompt_audio)}
        if prompt_text:
            body["clone_prompt"]["prompt_text"] = prompt_text

    resp = requests.post(
        f"{API_BASE}/v1/voice_clone",
        headers=headers({"Content-Type": "application/json"}),
        params=params(),
        json=body,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return raise_for_status(resp.json())


def list_voices(voice_type: str = "all") -> dict:
    """查询当前账号下可调用的音色。

    voice_type 取值：system / voice_cloning / voice_generation / all。
    注意：快速复刻得到的音色需正式调用一次才会出现在这里。
    """
    resp = requests.post(
        f"{API_BASE}/v1/get_voice",
        headers=headers({"Content-Type": "application/json"}),
        params=params(),
        json={"voice_type": voice_type},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return raise_for_status(resp.json())
