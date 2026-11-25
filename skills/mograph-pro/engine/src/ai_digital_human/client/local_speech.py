"""本地 Ming / mlx_audio 语音克隆，按需通过独立 Python 环境调用。"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from .speech import T2AResult


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"本地语音后端需要设置环境变量 {name}")
    return value


def _wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as audio:
        rate = audio.getframerate()
        if not rate:
            return 0
        return round(audio.getnframes() / rate * 1000)


def synthesize_local(text: str, *, timeout: int = 900) -> T2AResult:
    """用本地参考音频克隆音色，返回 WAV 字节与准确时长。

    mlx_audio 不进入主项目依赖；只有显式选择 local 后端时才启动子进程。
    """
    python = os.getenv("MING_TTS_PYTHON", sys.executable).strip()
    model = _required_env("MING_TTS_MODEL")
    ref_audio = _required_env("MING_TTS_REF_AUDIO")
    ref_text = _required_env("MING_TTS_REF_TEXT")
    if not Path(python).is_file() and os.path.sep in python:
        raise RuntimeError(f"MING_TTS_PYTHON 不存在：{python}")
    if not Path(model).exists():
        raise RuntimeError(f"MING_TTS_MODEL 不存在：{model}")
    if not Path(ref_audio).is_file():
        raise RuntimeError(f"MING_TTS_REF_AUDIO 不存在：{ref_audio}")

    with tempfile.TemporaryDirectory(prefix="ming-tts-") as temp_dir:
        command = [
            python, "-m", "mlx_audio.tts.generate",
            "--model", model,
            "--text", text,
            "--lang_code", "zh",
            "--ref_audio", ref_audio,
            "--ref_text", ref_text,
            "--output_path", temp_dir,
            "--file_prefix", "segment",
        ]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout)[-2000:]
            raise RuntimeError(f"本地 Ming 语音合成失败：\n{detail}")
        outputs = sorted(Path(temp_dir).glob("segment*.wav"))
        if len(outputs) != 1:
            raise RuntimeError(f"本地 Ming 未返回唯一 WAV，实际文件：{[p.name for p in outputs]}")
        output = outputs[0]
        return T2AResult(
            audio=output.read_bytes(),
            audio_format="wav",
            duration_ms=_wav_duration_ms(output),
            charged_chars=0,
            trace_id="local-ming",
        )
