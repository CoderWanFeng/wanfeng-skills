#!/usr/bin/env python3
"""开工前体检：把「小白会踩的坑」在花钱之前全部挡下来。

纯本地、零接口调用、零费用。只读取工作目录里的配置与素材，不修改任何文件，
也不会打印 .env 里的密钥内容。

用法：
    python3 scripts/preflight.py --root ./digital-human-work
    python3 scripts/preflight.py --root . --stage digital --video-backend compshare --voice-backend local

退出码：0 = 可以继续（可能有提醒），1 = 有阻断项，2 = 脚本自身异常。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

EMOTIONS_FALLBACK = (
    "happy", "sad", "angry", "fearful", "disgusted",
    "surprised", "calm", "fluent", "whisper",
)
PLACEHOLDERS = ("REPLACE_ME", "xxxx", "XXXX", "sk-api-xxxxxxxx", "your-", "changeme", "/path/to/")
FORBIDDEN_WORDS = ("二维码", "扫码", "点击链接", "http://", "https://", "www.")
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_SUFFIXES = {".mp3", ".m4a", ".wav"}

OK, WARN, FAIL = "通过", "提醒", "阻断"


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, level: str, item: str, detail: str) -> None:
        self.rows.append((level, item, detail))

    @property
    def blocked(self) -> bool:
        return any(level == FAIL for level, _, _ in self.rows)

    def render(self) -> str:
        icon = {OK: "[ OK ]", WARN: "[ ! ]", FAIL: "[ X ]"}
        lines = ["=" * 62, "开工前体检（本地检查，未调用任何接口，未产生费用）", "=" * 62]
        for level, item, detail in self.rows:
            lines.append(f"{icon[level]} {item}：{detail}")
        lines.append("-" * 62)
        if self.blocked:
            lines.append("结论：有阻断项，请先修好再继续。此时不要执行任何付费阶段。")
        elif any(level == WARN for level, _, _ in self.rows):
            lines.append("结论：可以继续，但请先看完上面的提醒。")
        else:
            lines.append("结论：环境、素材、文稿都就绪，可以开始。")
        return "\n".join(lines)


def probe(path: Path, entries: str) -> dict:
    exe = shutil.which("ffprobe")
    if not exe:
        return {}
    try:
        proc = subprocess.run(
            [exe, "-v", "error", "-show_entries", entries, "-of", "json", str(path)],
            capture_output=True, text=True, timeout=20, check=False,
        )
        if proc.returncode != 0:
            return {}
        return json.loads(proc.stdout or "{}")
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check_environment(root: Path, args, rep: Report) -> dict[str, str]:
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        rep.add(OK, "Python", f"{ver}（{sys.executable}）")
    else:
        rep.add(FAIL, "Python", f"{ver} 太低，需要 3.9 以上")

    if importlib.util.find_spec("requests"):
        rep.add(OK, "requests", "已安装")
    else:
        rep.add(FAIL, "requests",
                "当前解释器没有 requests。先执行 pip3 install requests，"
                "或改用已装依赖的解释器运行脚本")

    for exe in ("ffmpeg", "ffprobe"):
        found = shutil.which(exe)
        if found:
            rep.add(OK, exe, found)
        else:
            rep.add(FAIL, exe, "未找到。macOS: brew install ffmpeg；Windows 需加入 PATH")

    env_path = root / ".env"
    if not env_path.is_file():
        rep.add(FAIL, ".env", f"不存在：{env_path}。先运行 init_workspace.py 初始化")
        return {}
    mode = stat.S_IMODE(env_path.stat().st_mode)
    if mode & 0o077:
        rep.add(WARN, ".env 权限", f"当前 {oct(mode)}，建议 chmod 600（含密钥）")
    else:
        rep.add(OK, ".env 权限", oct(mode))

    values = read_env(env_path)
    route = args.minimax_route or values.get("DH_MINIMAX_ROUTE", "official") or "official"
    video_backend = args.video_backend or values.get("DH_VIDEO_BACKEND", "minimax") or "minimax"
    voice_backend = args.voice_backend or values.get("DH_VOICE_BACKEND", "minimax") or "minimax"
    rep.add(OK, "后端组合",
            f"画面 {video_backend} / 语音 {voice_backend} / MiniMax 接入 {route}")

    needs_minimax = "minimax" in (video_backend, voice_backend)
    if needs_minimax:
        if route == "recommended":
            key_env = "MINIMAX_RECOMMENDED_API_KEY"
            base_env = "MINIMAX_RECOMMENDED_BASE_URL"
            base = values.get(base_env, "")
            if not base or any(p in base for p in PLACEHOLDERS):
                rep.add(FAIL, "推荐平台地址", f"未配置 {base_env}，推荐平台需要显式指定接口地址")
            else:
                rep.add(OK, "推荐平台地址", base)
        else:
            key_env = "MINIMAX_API_KEY"
        key = values.get(key_env, "")
        if not key or any(p in key for p in PLACEHOLDERS):
            rep.add(FAIL, "API Key", f"{key_env} 还是空的或占位符，请填入自己的密钥")
        elif key.startswith("sk-cp-"):
            rep.add(FAIL, "API Key",
                    "这是订阅/中转通道 Key，调按量接口会报 2049 invalid api key。"
                    "去账户管理 → 接口密钥，换按量付费的 Key")
        else:
            rep.add(OK, "API Key", f"{key_env} 已填（长度 {len(key)}，未显示内容）")
    else:
        rep.add(OK, "API Key", "本次两条线都不走 MiniMax，无需密钥")

    if voice_backend == "minimax":
        voice = values.get("MINIMAX_VOICE_ID", "")
        if not voice or any(p in voice for p in PLACEHOLDERS):
            rep.add(FAIL, "音色 ID",
                    "未配置。先克隆音色，或在 .env 里把 MINIMAX_VOICE_ID 改成已有 voice_id")
        elif voice == "my-clone-voice":
            rep.add(WARN, "音色 ID",
                    "还是模板默认值 my-clone-voice。若尚未克隆过音色，先跑 clone_voice.py，否则合成立刻失败")
        else:
            rep.add(OK, "音色 ID", f"已配置（{voice[:3]}…，未显示全值）")
    else:
        python = values.get("MING_TTS_PYTHON", "").strip()
        model = values.get("MING_TTS_MODEL", "").strip()
        ref_audio = values.get("MING_TTS_REF_AUDIO", "").strip()
        ref_text = values.get("MING_TTS_REF_TEXT", "").strip()
        for label, value, must_exist in (
            ("本地合成解释器", python, True),
            ("Ming 模型目录", model, True),
            ("参考音频", ref_audio, True),
        ):
            if not value or any(p in value for p in PLACEHOLDERS):
                rep.add(FAIL, label, "未配置（本地配音需要）")
            elif must_exist and not Path(value).expanduser().exists():
                rep.add(FAIL, label, f"路径不存在：{value}")
            else:
                rep.add(OK, label, value)
        if not ref_text or any(p in ref_text for p in PLACEHOLDERS):
            rep.add(FAIL, "参考文本", "未配置 MING_TTS_REF_TEXT（必须与参考音频逐字一致）")
        else:
            rep.add(OK, "参考文本", f"{len(ref_text)} 字")

    if video_backend == "compshare":
        base = values.get("COMPSHARE_BASE_URL", "")
        if not base or any(p in base for p in PLACEHOLDERS):
            rep.add(FAIL, "自托管实例", "未配置 COMPSHARE_BASE_URL；开工前把实例开机并填地址")
        else:
            rep.add(OK, "自托管实例", base)
        rep.add(WARN, "自托管计费",
                f"实例按开机时长计费，预算单价 {values.get('COMPSHARE_HOURLY_PRICE', '2.15')} 元/小时，"
                "以平台账单为准")

    rep.add(OK, "密钥保密", "检查过程未打印任何密钥原文")
    return values


def check_assets(root: Path, args, rep: Report) -> list[Path]:
    scripts = sorted((root / "input" / "script").glob("*.txt")) if (root / "input" / "script").is_dir() else []
    if not scripts:
        rep.add(FAIL, "口播稿", "input/script/ 下没有 .txt 文稿")
    else:
        rep.add(OK, "口播稿", f"{scripts[0].name}（{scripts[0].stat().st_size} 字节）")
        if len(scripts) > 1:
            rep.add(WARN, "口播稿", f"共 {len(scripts)} 份，引擎默认取排序第一个：{scripts[0].name}。"
                    "建议每次只留一份，或用 --script 明确指定")

    persona_files = []
    persona_dir = root / "input" / "persona"
    if persona_dir.is_dir():
        persona_files = sorted(
            p for p in persona_dir.iterdir()
            if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES | IMAGE_SUFFIXES
        )
    if not persona_files:
        level = FAIL if args.stage in ("digital", "all") and args.video_backend != "credits" else WARN
        rep.add(level, "形象素材",
                "input/persona/ 为空。只配音的阶段不需要；生成数字人前必须放入本人参考视频或图片")
    else:
        p = persona_files[0]
        rep.add(OK, "形象素材", f"{p.name}")
        data = probe(p, "stream=width,height,duration:stream_tags=rotate")
        streams = data.get("streams") or []
        if streams:
            s = streams[0]
            wh = f"{s.get('width', '?')}×{s.get('height', '?')}"
            rep.add(OK, "形象规格", f"{wh}，时长 {s.get('duration', '?')}s")
            if "rotate" in (s.get("tags") or {}):
                rep.add(WARN, "形象规格",
                        "带旋转元数据，可能出现尺寸判定错误或黑边；引擎已用 display 尺寸处理，请留意成片")
        if len(persona_files) > 1:
            rep.add(WARN, "形象素材", f"共 {len(persona_files)} 个，引擎默认取排序第一个：{p.name}")

    voice_files = []
    voice_dir = root / "input" / "voice"
    if voice_dir.is_dir():
        voice_files = sorted(
            p for p in voice_dir.iterdir()
            if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES
        )
    if voice_files:
        v = voice_files[0]
        dur = (probe(v, "format=duration").get("format") or {}).get("duration", "?")
        rep.add(OK, "本人录音", f"{v.name}，时长 {dur}s（首次克隆音色用）")
    elif args.voice_backend == "minimax":
        rep.add(WARN, "本人录音",
                "input/voice/ 为空。如果已有可用 voice_id 可忽略；首次使用需一段 10 秒~5 分钟本人清晰说话录音")

    if args.video_backend == "credits":
        credits_dir = root / "input" / "credits"
        clips = sorted(p for p in credits_dir.glob("*") if p.suffix.lower() in VIDEO_SUFFIXES) \
            if credits_dir.is_dir() else []
        if clips:
            rep.add(OK, "积分片段", f"已有 {len(clips)} 个：{', '.join(p.name for p in clips[:4])}")
        else:
            rep.add(WARN, "积分片段",
                    "input/credits/ 还是空的。先跑 digital 阶段拿清单，用软件积分生成后按 "
                    "seg_001.mp4 命名放进来")
    return scripts


def check_script(scripts: list[Path], rep: Report) -> str:
    if not scripts:
        return ""
    text = scripts[0].read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        rep.add(FAIL, "文稿内容", "文件是空的")
        return ""
    rep.add(OK, "文稿内容", f"{len(text)} 字")

    if re.search(r"(?<!\[)\[(?:A|B)\](?!\])", text):
        rep.add(FAIL, "稿件标记",
                "发现单括号 [A] / [B] 标记。本引擎只认 [[A:happy]] 和 [[BROLL:提示]]，"
                "单括号会被当成正文念出来。请改成双括号，或显式取正文再合成")
    broll_count = len(re.findall(r"\[\[BROLL", text))
    if broll_count == 0:
        rep.add(WARN, "镜头分配",
                "全文没有 [[BROLL]]，默认全部按出镜 A-roll 生成，视频费用最高。"
                "演示、录屏、图表类段落建议标成 B-roll")
    else:
        rep.add(OK, "镜头分配", f"{broll_count} 段标为 B-roll（这些段不生成数字人，不按秒计费）")

    emotions = re.findall(r"\[\[A:([a-zA-Z_]+)", text)
    bad = sorted({e for e in emotions if e not in EMOTIONS_FALLBACK})
    if bad:
        rep.add(WARN, "情绪取值", f"{bad} 不是平台支持的情绪，会被忽略。合法值：{', '.join(EMOTIONS_FALLBACK)}")
    elif emotions:
        rep.add(OK, "情绪取值", f"已标注 {len(emotions)} 处，取值合法")

    hits = [w for w in FORBIDDEN_WORDS if w in text]
    if hits:
        rep.add(WARN, "合规用语", f"文稿里出现 {hits}，链接/二维码/扫码类表述不应进稿也不应进画面")
    else:
        rep.add(OK, "合规用语", "未见链接、二维码、扫码字样")

    long_lines = [line for line in text.splitlines() if len(line.strip()) > 45 and not line.strip().startswith("[[")]
    if long_lines:
        rep.add(WARN, "口播句式", f"{len(long_lines)} 行超过 45 字，长句念起来吃力，建议拆成短句")
    else:
        rep.add(OK, "口播句式", "句子长度合适")
    return text


def quote(root: Path, text: str, args, rep: Report) -> None:
    """复用引擎自己的计价与分段逻辑，给出零调用报价。"""
    if not text:
        return
    src = root / "src"
    if not src.is_dir():
        rep.add(WARN, "费用预估", "工作区里找不到引擎 src/，跳过报价")
        return
    sys.path.insert(0, str(src))
    try:
        from ai_digital_human.pipeline.voice_line import KIND_A, estimate_seconds, group_script
        from ai_digital_human.pricing import COMPSHARE_MODEL, LOCAL_TTS_MODEL, estimate_cost, estimate_video_cost
    except Exception as exc:
        rep.add(WARN, "费用预估", f"引擎导入失败（{type(exc).__name__}），跳过报价；先装好 requests")
        return

    segment_seconds = 10.0 if args.video_backend == "credits" else 13.0
    groups = group_script(text, max_seconds=segment_seconds)
    a_groups = [g for g in groups if g.kind == KIND_A]

    if args.voice_backend == "local":
        tts = 0.0
        tts_note = "配音走本地 Ming，API 字符费 0"
    else:
        tts = sum(estimate_cost(g.text, "speech-2.8-hd") for g in groups)
        tts_note = f"配音约 ¥{tts:.3f}"

    seconds = sum(max(4, min(15, int(round(estimate_seconds(g.text) + 0.5)))) for g in a_groups)
    if args.video_backend == "credits":
        video_note = "出镜画面用软件积分，0 元"
    elif args.video_backend == "compshare":
        video_note = (f"出镜 {len(a_groups)} 段共 {seconds}s，API 费 0，"
                      "实例费按开机时长另计")
    else:
        video_note = (f"出镜 {len(a_groups)} 段共 {seconds}s，"
                      f"数字人约 ¥{estimate_video_cost('MiniMax-H3-Lite', '768P', seconds):.2f}")

    rep.add(OK, "费用预估",
            f"共 {len(groups)} 段（出镜 {len(a_groups)} / B-roll {len(groups) - len(a_groups)}）；"
            f"{tts_note}；{video_note}。这是估算，不是官方账单")


def main() -> int:
    parser = argparse.ArgumentParser(description="数字人视频开工前体检（零调用、零费用）")
    parser.add_argument("--root", default=os.getenv("DH_WORK_ROOT") or ".",
                        help="工作目录，默认当前目录或 DH_WORK_ROOT")
    parser.add_argument("--stage", default="plan",
                        choices=("plan", "broll", "digital", "merge", "all"),
                        help="打算执行到哪一步，用于调整必检项")
    parser.add_argument("--video-backend", choices=("credits", "minimax", "compshare"), default=None,
                        help="出镜画面后端；不填则读 .env 的 DH_VIDEO_BACKEND")
    parser.add_argument("--voice-backend", choices=("minimax", "local"), default=None,
                        help="语音后端；不填则读 .env 的 DH_VOICE_BACKEND")
    parser.add_argument("--minimax-route", choices=("official", "recommended"), default=None,
                        help="MiniMax 接入方式；不填则读 .env 的 DH_MINIMAX_ROUTE")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"工作目录不存在：{root}\n先运行 init_workspace.py 初始化。")
        return 2

    rep = Report()
    values = check_environment(root, args, rep)
    # 未显式指定时，从 .env 推导，保证后续检查与真实运行一致
    args.video_backend = args.video_backend or values.get("DH_VIDEO_BACKEND", "minimax") or "minimax"
    args.voice_backend = args.voice_backend or values.get("DH_VOICE_BACKEND", "minimax") or "minimax"
    scripts = check_assets(root, args, rep)
    text = check_script(scripts, rep)
    quote(root, text, args, rep)

    print(rep.render())
    print(f"\n工作目录：{root}    检查阶段：{args.stage}")
    print("提示：本脚本只读，不会替你修改文稿、素材或 .env。")
    return 1 if rep.blocked else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
