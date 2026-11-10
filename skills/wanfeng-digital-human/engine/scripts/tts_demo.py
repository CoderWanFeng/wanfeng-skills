#!/usr/bin/env python3
"""用系统音色合成一句话，产出音频文件。

用法：
    python3 scripts/tts_demo.py
    python3 scripts/tts_demo.py --text "今天天气不错" --voice female-yujie --emotion happy
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ai_digital_human import estimate_cost, t2a  # noqa: E402
from ai_digital_human.pricing import count_charged_chars  # noqa: E402

DEFAULT_TEXT = "你好，我是你的 AI 声音分身。"


def main() -> int:
    parser = argparse.ArgumentParser(description="MiniMax 语音合成试听")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="待合成文本")
    parser.add_argument("--voice", default="female-tianmei", help="系统音色 voice_id")
    parser.add_argument("--model", default="speech-2.8-hd", help="模型：speech-2.8-hd / speech-2.8-turbo")
    parser.add_argument("--emotion", default=None, help="情绪：happy/sad/calm 等")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--out", default=None, help="输出文件路径，默认写入 output/final/")
    args = parser.parse_args()

    cost = estimate_cost(args.text, args.model)
    print(f"待合成：{args.text}")
    print(f"计费字符：{count_charged_chars(args.text)}，预计费用：{cost:.4f} 元")

    started = time.time()
    result = t2a(
        args.text,
        model=args.model,
        voice_id=args.voice,
        emotion=args.emotion,
        speed=args.speed,
    )
    elapsed = time.time() - started

    out_path = Path(args.out) if args.out else ROOT / "output" / "final" / "voice" / f"tts_{args.voice}{result.file_suffix}"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(result.audio)

    print(f"完成：{out_path}")
    print(f"时长 {result.duration_ms / 1000:.2f}s，平台计费字符 {result.charged_chars}，耗时 {elapsed:.2f}s")
    print(f"trace_id: {result.trace_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
