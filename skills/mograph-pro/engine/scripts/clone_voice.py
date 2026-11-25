#!/usr/bin/env python3
"""复刻你的音色，并产出一段试听音频。

流程：预处理音频 → 上传待复刻音频 → （可选）上传示例音频 → 复刻 → 下载试听音频。

用法：
    python3 scripts/clone_voice.py input/my_voice.m4a
    python3 scripts/clone_voice.py input/my_voice.mp3 --voice-id my-clone-voice --text "这是我的声音克隆试听。"
    python3 scripts/clone_voice.py input/my_voice.mp3 --prompt-audio input/sample.mp3 --prompt-text "示例音频对应的文本"

注意：
- 复刻接口要求账号已完成个人或企业认证，否则返回 2038（无复刻权限）。
- 复刻得到的音色若 7 天内未正式调用会被系统删除，克隆后请尽快正式合成一次。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import requests  # noqa: E402

from ai_digital_human import clone_voice, upload_file  # noqa: E402
from ai_digital_human.client import load_env_file  # noqa: E402
from ai_digital_human.media import probe, transcode_audio  # noqa: E402
from ai_digital_human.pricing import estimate_cost  # noqa: E402

DEFAULT_TEXT = "这是我的声音克隆试听，听起来像不像我？"


def prepare_source(path: Path) -> Path:
    """确保音频满足平台规范：mp3/m4a/wav、10 秒 ~ 5 分钟、≤ 20MB。"""
    info = probe(path)
    ext = path.suffix.lower().lstrip(".")
    need_transcode = ext not in {"mp3", "m4a", "wav"} or info["bytes"] > 20 * 1024 * 1024
    if need_transcode:
        target = path.with_name(f"{path.stem}_prepared.mp3")
        transcode_audio(path, target)
        path = target
        info = probe(path)

    problems = []
    if info["duration"] < 10:
        problems.append(f"时长 {info['duration']:.1f}s < 10s")
    if info["duration"] > 300:
        problems.append(f"时长 {info['duration']:.1f}s > 300s")
    if info["bytes"] > 20 * 1024 * 1024:
        problems.append(f"体积 {info['bytes'] / 1024 / 1024:.1f}MB > 20MB")
    if problems:
        raise SystemExit("音频不符合平台要求：" + "；".join(problems))
    return path


def save_voice_record(voice_id: str, record: dict) -> Path:
    """把音色信息记录到 config/voices.json，方便后续复用。"""
    path = ROOT / "config" / "voices.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    data[voice_id] = record
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return path


def main() -> int:
    load_env_file()
    parser = argparse.ArgumentParser(description="MiniMax 音色快速复刻")
    parser.add_argument("audio", help="待复刻音频（本人录音）")
    parser.add_argument("--voice-id", default=os.environ.get("MINIMAX_VOICE_ID", "my-clone-voice"),
                        help="自定义音色 ID（8-256 位，字母开头），默认读环境变量 MINIMAX_VOICE_ID")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="试听文本")
    parser.add_argument("--model", default="speech-2.8-hd", help="试听合成模型")
    parser.add_argument("--prompt-audio", default=None, help="可选示例音频（< 8 秒），用于提升相似度")
    parser.add_argument("--prompt-text", default=None, help="示例音频对应的准确文本")
    args = parser.parse_args()

    source = prepare_source(Path(args.audio))
    info = probe(source)
    print(f"待复刻音频：{source}（{info['duration']:.1f}s，{info['bytes'] / 1024 / 1024:.2f}MB）")
    print(f"计费：音色 9.90 元 + 试听文本约 {estimate_cost(args.text, args.model):.4f} 元")

    print("上传待复刻音频…")
    file_id = upload_file(source, purpose="voice_clone")
    print(f"file_id = {file_id}")

    prompt_file_id = None
    if args.prompt_audio:
        print("上传示例音频…")
        prompt_file_id = upload_file(Path(args.prompt_audio), purpose="prompt_audio")
        print(f"prompt_audio file_id = {prompt_file_id}")

    print("调用复刻接口…")
    started = time.time()
    payload = clone_voice(
        file_id,
        args.voice_id,
        text=args.text,
        model=args.model,
        prompt_audio=prompt_file_id,
        prompt_text=args.prompt_text,
    )
    print(f"复刻完成，耗时 {time.time() - started:.1f}s")

    demo_url = payload.get("demo_audio") or ""
    out_path = None
    if demo_url:
        out_dir = ROOT / "output" / "final"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"clone_{args.voice_id}.mp3"
        out_path.write_bytes(requests.get(demo_url, timeout=60).content)
        print(f"试听音频：{out_path}")

    extra = payload.get("extra_info") or {}
    record = {
        "voice_id": args.voice_id,
        "source_audio": str(source),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "demo_audio": str(out_path) if out_path else demo_url,
        "usage_characters": extra.get("usage_characters"),
    }
    record_path = save_voice_record(args.voice_id, record)
    print(f"音色已记录：{record_path}")
    print(f"voice_id = {args.voice_id}（7 天内需正式调用一次，否则会被系统删除）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
