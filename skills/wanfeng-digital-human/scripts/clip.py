#!/usr/bin/env python3
"""一句话 → 一条 10 秒以内的数字人片段。

输入一个形象素材（视频或图片）和一段台词，输出一条用这张脸、这个声音说这句话的视频。

    # 第一步：只体检 + 报价，零调用、零费用
    python3 scripts/clip.py --face 我的视频.mp4 --text "大家好，这是第一条测试。"

    # 第二步：先听声音，只花音色和 TTS 的钱
    python3 scripts/clip.py --face 我的视频.mp4 --text "..." --run --stop-at voice

    # 第三步：确认声音没问题，再生成画面
    python3 scripts/clip.py --face 我的视频.mp4 --text "..." --run

安全设计：不加 --run 就绝对不会调用任何付费接口。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ENGINE_SRC = SKILL_ROOT / "engine" / "src"
sys.path.insert(0, str(ENGINE_SRC))

CHARS_PER_SECOND = 4.0   # 中文口播约 240 字/分钟
VIDEO_MIN_SECONDS = 4    # 接口硬下限：不足 4 秒也按 4 秒计费
VIDEO_MAX_SECONDS = 15   # 接口硬上限
VOICE_SOURCE_MIN = 10.0  # 音色复刻要求的音源最短时长
VOICE_SOURCE_MAX = 300.0
REF_VIDEO_MAX = 15.0     # 参考视频单片上限
REF_AUDIO_MIN = 2.0      # 参考音频下限

ERROR_HINTS = {
    1004: "账号未完成实名认证。去 MiniMax 开放平台 → 账户管理 → 实名认证，通过后再跑。",
    2038: "当前账号没有音色复刻权限（多为未实名）。先完成实名认证；或用 --system-voice 先用内置音色试跑。",
    2049: "账户余额不足。去开放平台充值，或把 --resolution 换成 480P 降一档成本。",
    1002: "触发限流。等 30 秒再跑，不要并发多个任务。",
    1026: "文案或素材触发了内容审核。换一种说法，或换一张形象素材。",
    1027: "文案或素材触发了内容审核。换一种说法，或换一张形象素材。",
    2013: "输入参数不合法。多半是参考音频/视频时长越界，看上面报的具体字段。",
}


# --------------------------------------------------------------------------- 输出


def say(msg: str = "") -> None:
    print(msg, flush=True)


def head(title: str) -> None:
    say("")
    say(f"── {title} " + "─" * max(0, 46 - len(title)))


def ok(label: str, detail: str = "") -> None:
    say(f"  [ OK ] {label}" + (f"  {detail}" if detail else ""))


def warn(label: str, detail: str = "") -> None:
    say(f"  [ !  ] {label}" + (f"  {detail}" if detail else ""))


def bad(label: str, detail: str = "") -> None:
    say(f"  [ X  ] {label}" + (f"  {detail}" if detail else ""))


# --------------------------------------------------------------------------- 校验


def inspect_face(path: Path) -> dict:
    """读取形象素材规格。图片和视频都走 ffprobe。"""
    from ai_digital_human.media import probe

    info = probe(path)
    info["is_video"] = info["has_video"] and info["duration"] > 0.5
    return info


def estimate_speech_seconds(text: str) -> float:
    """按中文口播速度粗估朗读时长（不含标点停顿，偏乐观）。"""
    spoken = "".join(ch for ch in text if ch.strip() and ch not in "，。！？、；：…—,.!?;:")
    return len(spoken) / CHARS_PER_SECOND


def text_problems(text: str, max_seconds: int) -> list[str]:
    """文案层面能在本地拦下的问题。"""
    problems: list[str] = []
    stripped = text.strip()
    if not stripped:
        problems.append("台词是空的")
        return problems
    if estimate_speech_seconds(stripped) > max_seconds:
        limit = int(max_seconds * CHARS_PER_SECOND)
        problems.append(
            f"文案太长：约 {len(stripped)} 字，按中文口播估算要 {estimate_speech_seconds(stripped):.1f} 秒，"
            f"超过上限 {max_seconds} 秒。删到 {limit} 字以内，或者拆成两条分别生成"
        )
    if len(stripped) < 8:
        problems.append(
            f"文案太短：只有 {len(stripped)} 字，合成后不足 {REF_AUDIO_MIN:.0f} 秒，接口不接受短于 2 秒的参考音频。至少 10 个字"
        )
    for ch in ("[[", "]]", "[A]", "[B]", "[BROLL"):
        if ch in stripped:
            problems.append(f"文案里出现了文稿标记 {ch}，会被原样念出来。这里只要纯台词")
    return problems


def face_problems(info: dict, path: Path) -> tuple[list[str], list[str]]:
    """返回 (硬性问题, 提醒)。"""
    errors: list[str] = []
    notes: list[str] = []
    size_mb = info["bytes"] / 1024 / 1024
    if info["is_video"]:
        if info["duration"] < 2:
            errors.append(f"参考视频只有 {info['duration']:.1f} 秒，接口要求 2–15 秒")
        if info["duration"] > REF_VIDEO_MAX:
            notes.append(
                f"视频 {info['duration']:.1f} 秒，超过参考视频上限 15 秒，会自动取前 {int(min(info['duration'], 12))} 秒"
            )
        if size_mb > 50:
            notes.append(f"视频 {size_mb:.0f}MB 超过 50MB，会自动重新压缩")
    else:
        if size_mb > 30:
            errors.append(f"图片 {size_mb:.1f}MB 超过 30MB 上限，先压缩一下")
    w, h = info["display_width"], info["display_height"]
    if w and h:
        if min(w, h) < 480:
            notes.append(f"画面只有 {w}×{h}，生成结果会偏糊，建议至少 720×720")
        if not info["is_video"]:
            notes.append("给的是图片：画面不会有说话时的头部动作和表情变化，更像一张会动的照片")
    if info["is_video"] and not info["has_audio"]:
        notes.append("视频没有音轨，只能用 --voice-source 指定音源，或加 --system-voice 用内置音色")
    return errors, notes


# --------------------------------------------------------------------------- 预处理


def prepare_face(face: Path, out_dir: Path, ratio: str) -> tuple[Path, str]:
    """归一化形象素材，返回 (可用路径, 视频/图片)。"""
    from ai_digital_human.media import normalize_ratio
    from ai_digital_human.media.ffmpeg import run

    info = inspect_face(face)
    kind = "video" if info["is_video"] else "image"
    if kind == "image":
        return face, kind

    target = out_dir / "face_normalized.mp4"
    if info["duration"] > REF_VIDEO_MAX:
        # 先截到 12 秒，再归一化：参考视频只需要提供神态和外观，不需要整段
        trimmed = out_dir / "face_trimmed.mp4"
        run(["-i", str(face), "-t", "12", "-c:v", "libx264", "-crf", "20",
             "-pix_fmt", "yuv420p", "-an", str(trimmed)])
        normalize_ratio(trimmed, target, ratio=ratio)
        trimmed.unlink(missing_ok=True)
        return target, kind
    normalize_ratio(face, target, ratio=ratio)
    return target, kind


def extract_voice_source(
    face: Path, voice_source: Path | None, out_dir: Path, *, dry_run: bool = False
) -> tuple[Path | None, str]:
    """拿到可用的音源：优先显式指定的，其次从形象视频里抽音轨。

    dry_run=True 时只读时长、不转码不落盘，保证预演零副作用。
    """
    from ai_digital_human.media import probe, transcode_audio

    source = voice_source
    origin = "指定的音源"
    if source is None:
        info = probe(face)
        if not info["has_audio"]:
            return None, "形象素材里没有音轨"
        source = face
        origin = "从形象视频里抽的音轨"
    if not source.is_file():
        raise FileNotFoundError(f"音源文件不存在：{source}")

    if dry_run:
        duration = probe(source)["duration"]
        if duration < VOICE_SOURCE_MIN or duration > VOICE_SOURCE_MAX:
            return None, f"{origin}时长 {duration:.1f} 秒，不够 10 秒"
        ok("音源够用", f"{origin}，{duration:.1f} 秒")
        return source, origin

    target = out_dir / "voice_source.mp3"
    transcode_audio(source, target)
    duration = probe(target)["duration"]
    if duration < VOICE_SOURCE_MIN or duration > VOICE_SOURCE_MAX:
        say("")
        bad("音源时长不合规", f"{origin} {duration:.1f} 秒，接口要求 10 秒–5 分钟")
        return None, f"{origin}时长 {duration:.1f} 秒"
    ok("音源就绪", f"{origin}，{duration:.1f} 秒")
    return target, origin


# --------------------------------------------------------------------------- 三步主链路


def do_clone(source: Path, voice_id: str, out_dir: Path) -> dict:
    """复刻音色，返回接口响应。"""
    from ai_digital_human import clone_voice, upload_file

    head("复刻音色")
    say("  上传音源…")
    file_id = upload_file(source, purpose="voice_clone")
    say("  调用复刻接口（约 10–30 秒）…")
    started = time.time()
    payload = clone_voice(file_id, voice_id, text="这是音色复刻的试听。")
    say(f"  完成，耗时 {time.time() - started:.1f}s")
    return payload


def do_tts(text: str, voice_id: str, out_dir: Path) -> tuple[Path, float, list]:
    """合成台词，返回 (mp3, 秒数, 字幕)。"""
    from ai_digital_human import t2a

    head("合成台词")
    result = t2a(text, voice_id=voice_id, subtitle_enable=True)
    audio_path = out_dir / f"line{result.file_suffix}"
    audio_path.write_bytes(result.audio)
    seconds = (result.duration_ms or 0) / 1000.0
    ok("台词音频", f"{seconds:.2f} 秒 → {audio_path.name}")
    return audio_path, seconds, result.subtitles


def do_video(
    *, face: Path, kind: str, audio: Path, text: str,
    out_dir: Path, model: str, resolution: str, ratio: str, duration: int,
    prompt_extra: str, timeout: int,
) -> tuple[Path, str]:
    """调 H3 生成口播画面，返回 (带音轨的成片, task_id)。"""
    from ai_digital_human import create_video_task, upload_file, wait_video_task
    from ai_digital_human.client.video import (
        content_item_audio, content_item_image, content_item_text, content_item_video,
    )
    from ai_digital_human.client.video import download_video
    from ai_digital_human.media import mux_audio

    head("生成画面")
    say(f"  上传形象素材…")
    face_ref = f"mm_file://{upload_file(face, purpose='video_generation_input')}"
    say("  上传参考音频…")
    audio_ref = f"mm_file://{upload_file(audio, purpose='video_generation_input')}"

    prompt = f"角色说：{text} 音色参考音频1，画面稳定，角色正面看向镜头，自然口播。{prompt_extra}".strip()
    content = [
        content_item_text(prompt),
        content_item_video(face_ref, role="reference_video") if kind == "video"
        else content_item_image(face_ref, role="reference_image"),
        content_item_audio(audio_ref, role="reference_audio"),
    ]
    task_id = create_video_task(
        prompt=prompt, model=model, content=content,
        resolution=resolution, duration=duration, ratio=ratio,
    )
    say(f"  任务已提交：{task_id}（通常 40–120 秒）")
    task = wait_video_task(task_id, timeout=timeout)
    url = ((task.get("content") or {}).get("url")) or ""
    if not url:
        raise RuntimeError(f"任务 {task_id} 成功但没有返回视频链接")

    raw = out_dir / "raw.mp4"
    download_video(url, raw)
    # 模型会自己生成一条音轨，但那是它二次合成的声音；用原始 TTS 音频覆盖，
    # 保证成片里是克隆音色逐字念出来的版本。
    final = out_dir / "clip.mp4"
    mux_audio(raw, audio, final)
    ok("画面就绪", f"{final.name}")
    return final, task_id


def write_srt(subtitles: list, dest: Path) -> Path | None:
    """把 TTS 返回的时间码写成 SRT。"""
    if not subtitles:
        return None

    def stamp(ms: float) -> str:
        total = int(round(ms))
        h, rem = divmod(total, 3_600_000)
        m, rem = divmod(rem, 60_000)
        s, milli = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"

    lines: list[str] = []
    for idx, item in enumerate(subtitles, 1):
        lines += [str(idx), f"{stamp(item.time_begin)} --> {stamp(item.time_end)}", item.text.strip(), ""]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


# --------------------------------------------------------------------------- 主流程


def main() -> int:
    parser = argparse.ArgumentParser(
        description="一句话生成 10 秒以内的数字人片段",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--face", default="", help="形象素材：一段自拍视频或一张正脸照片")
    parser.add_argument("--text", default="", help="要说的那句话（10 秒内约 40 字）")
    parser.add_argument("--text-file", default="", help="从文件读台词，替代 --text")
    parser.add_argument("--voice-source", default="", help="单独的音源（10 秒以上）；不给就从形象视频里抽")
    parser.add_argument("--voice-id", default="", help="复用已复刻的音色 ID，跳过复刻")
    parser.add_argument("--system-voice", action="store_true", help="用平台内置音色，不克隆（音源不够长时兜底）")
    parser.add_argument("--out", default="", help="输出目录，默认 output/clip-<时间戳>")
    parser.add_argument("--max-seconds", type=int, default=10, help="成片上限秒数，默认 10，范围 4–15")
    parser.add_argument("--resolution", default="768P", choices=["480P", "768P"], help="输出分辨率")
    parser.add_argument("--model", default="MiniMax-H3-Lite", help="视频模型")
    parser.add_argument("--ratio", default="auto", help="宽高比，auto 跟随素材")
    parser.add_argument("--prompt-extra", default="", help="附加画面描述，如「背景是书房」")
    parser.add_argument("--voice-model", default="speech-2.8-hd", help="TTS 模型")
    parser.add_argument("--timeout", type=int, default=900, help="等待视频任务的秒数")
    parser.add_argument("--inspect", action="store_true",
                        help="只体检形象素材，打印一行结论后退出（零费用）")
    parser.add_argument("--check-key", action="store_true",
                        help="只检查 API Key 是否配好，打印一行结论后退出（零费用，不要求 --face）")
    parser.add_argument("--stop-at", default="video", choices=["voice", "video"],
                        help="voice=只做到试听音频就停（不花钱生成画面）")
    parser.add_argument("--run", action="store_true", help="真的调用接口；不加只体检报价")
    args = parser.parse_args()

    from ai_digital_human.pricing import (
        VOICE_FEE, count_charged_chars, estimate_cost, estimate_video_cost,
    )

    # 工作目录：显式告诉引擎去哪里找 .env，否则它会顺着 engine/ 命中 engine/scripts/build.py
    env_dirs = [SKILL_ROOT]
    if args.out:
        env_dirs.insert(0, Path(args.out).expanduser().resolve().parent)
    for candidate in env_dirs:
        if (candidate / ".env").is_file():
            os.environ["DH_WORK_ROOT"] = str(candidate)
            break

    from ai_digital_human.client import MiniMaxError, load_env_file
    load_env_file()

    api_key = os.getenv("MINIMAX_API_KEY", "").strip()
    env_path = Path(os.environ.get("DH_WORK_ROOT") or SKILL_ROOT) / ".env"

    if args.check_key:
        # 区分三种状态：没配 / 配的是订阅 Key / 配对了。
        # 只看"有没有值"会给出假绿灯——shell 里常残留 sk-cp- 订阅 Key，
        # 那种 Key 到生成那步才报 2049，白跑一轮。
        from_file = False
        if env_path.is_file():
            for line in env_path.read_text(errors="ignore").splitlines():
                name, _, value = line.strip().partition("=")
                if name.strip() == "MINIMAX_API_KEY":
                    from_file = bool(value.strip().strip('"').strip("'"))
                    break
        if not api_key:
            print("未配置")
            return 1
        if api_key.startswith("sk-cp-"):
            print("Key 类型不对：这是订阅套餐的 Key（sk-cp- 开头），用不了")
            return 1
        if not from_file:
            print("已配置，但只在这次有效，建议长期保存")
            return 0
        print(f"已配置（{len(api_key)} 位，未显示值）")
        return 0

    if not args.face:
        bad("缺形象素材", "要传 --face（视频或照片）；只查密钥用 --check-key")
        return 2

    face = Path(args.face).expanduser().resolve()
    if not face.is_file():
        bad("找不到形象素材", str(face))
        return 2

    text = args.text
    if args.text_file:
        text = Path(args.text_file).expanduser().read_text(encoding="utf-8").strip()
    text = text.strip()

    max_seconds = max(VIDEO_MIN_SECONDS, min(VIDEO_MAX_SECONDS, args.max_seconds))

    # ---------------------------------------------------------------- 体检报告
    if not args.inspect:
        head("素材体检")
    try:
        info = inspect_face(face)
    except Exception as exc:
        bad("读不了这个文件", f"{exc}")
        return 2

    kind = "视频" if info["is_video"] else "图片"
    if not args.inspect:
        ok("形象素材", f"{kind} {info['display_width']}×{info['display_height']}"
                      f"，{info['duration']:.1f} 秒，{info['bytes'] / 1024 / 1024:.1f}MB")
        if info["rotation"]:
            warn("素材带旋转元数据", f"rotation={info['rotation']}，会自动摆正")

    errors, notes = face_problems(info, face)
    if not args.inspect:
        for note in notes:
            warn("提醒", note)
    for err in errors:
        bad("素材不合规", err)
    if errors:
        return 2

    if args.inspect:
        # 只回一行结论，供对话里"拿到素材立刻反馈"用
        if not info["is_video"]:
            voice_note = "图片没有音轨，必须另外给音源"
        elif not info["has_audio"]:
            voice_note = "视频没有音轨，必须另外给音源"
        elif info["duration"] >= VOICE_SOURCE_MIN:
            voice_note = "音源可直接从视频抽取，不用另给录音"
        else:
            voice_note = f"音源不足 10 秒（只有 {info['duration']:.1f} 秒），需要另给录音或用内置声音"
        print(f"{kind} {info['display_width']}×{info['display_height']}，"
              f"{info['duration']:.1f} 秒，{info['bytes'] / 1024 / 1024:.1f}MB；{voice_note}")
        return 0

    head("文案体检")
    text_errs = text_problems(text, max_seconds)
    for err in text_errs:
        bad("文案有问题", err)
    if text_errs:
        return 2
    ok("字数", f"{len(text)} 字，估算 {estimate_speech_seconds(text):.1f} 秒（上限 {max_seconds} 秒）")

    # ---------------------------------------------------------------- 音源预案
    out_dir = Path(args.out).expanduser().resolve() if args.out else \
        SKILL_ROOT / "output" / f"clip-{time.strftime('%Y%m%d-%H%M%S')}"

    head("声音来源")
    reuse_voice = bool(args.voice_id)
    voice_source: Path | None = None
    if args.system_voice:
        warn("使用内置音色", "成片里的人声不是你自己的声音")
        voice_id = args.voice_id or "male-qn-qingse"
    elif reuse_voice:
        voice_id = args.voice_id
        ok("复用已有音色", f"{voice_id[:4]}…（不复刻，省 9.90 元）")
    else:
        voice_id = f"clip-{time.strftime('%Y%m%d%H%M%S')}"
        src_arg = Path(args.voice_source).expanduser().resolve() if args.voice_source else None
        if args.run:
            out_dir.mkdir(parents=True, exist_ok=True)
        try:
            voice_source, detail = extract_voice_source(
                face, src_arg, out_dir, dry_run=not args.run
            )
        except Exception as exc:
            bad("音源准备失败", str(exc))
            return 2
        if voice_source is None:
            say("")
            say("  这条素材没法复刻音色，有两条路：")
            say("    1) 单独给一段 10 秒以上的说话录音：--voice-source 录音.m4a")
            say("    2) 先用平台内置音色把画面跑通：加 --system-voice")
            say(f"    原因：{detail}")
            return 2

    # ---------------------------------------------------------------- 费用
    video_seconds = max(VIDEO_MIN_SECONDS, min(max_seconds, int(round(estimate_speech_seconds(text) + 1))))
    tts_cost = estimate_cost(text, args.voice_model)
    video_cost = estimate_video_cost(args.model, args.resolution, video_seconds)
    voice_cost = 0.0 if (reuse_voice or args.system_voice) else VOICE_FEE

    head("这一步会花多少钱")
    if args.system_voice:
        voice_label = "用内置音色，0 元"
    elif reuse_voice:
        voice_label = "已复用，0 元"
    else:
        voice_label = f"{voice_cost:.2f} 元（一次性）"
    say(f"  音色复刻      {voice_label}")
    say(f"  台词合成      {tts_cost:.4f} 元（{count_charged_chars(text)} 计费字符）")
    say(f"  数字人画面    {video_cost:.2f} 元（{video_seconds} 秒 × {args.resolution}）")
    say(f"  {'-' * 40}")
    total = voice_cost + tts_cost + video_cost
    say(f"  合计约        {total:.2f} 元")
    if args.stop_at == "voice":
        say(f"  本次只到试听  约 {voice_cost + tts_cost:.2f} 元（不生成画面）")

    key_problem = ""
    if not api_key:
        say("")
        key_problem = "missing"
        bad("缺少 API Key", "这个技能要调 MiniMax 开放平台，得先开通拿 Key")
        say("  1. 打开 https://platform.minimaxi.com 注册并登录")
        say("  2. 账户管理 → 实名认证（克隆音色必须，可能要等审核）")
        say("  3. 账户管理 → 余额 → 充值，先充 20–30 元够跑两条")
        say("  4. 账户管理 → 接口密钥 → 创建新的 API Key，复制")
        say("  拿到后发给我，我存到本机，不会外传。")
        say("  注意：订阅套餐的 Key（sk-cp- 开头）用不了，要用按量付费的。")
        say("  一步步的说明见 references/onboarding.md")
        if args.run:
            return 2
    elif api_key.startswith("sk-cp-"):
        say("")
        key_problem = "type"
        bad("Key 类型不对", "这是 sk-cp- 开头的订阅套餐 Key，调不通这些接口")
        say("  去 platform.minimaxi.com → 账户管理 → 接口密钥，建一个按量付费的 Key")
        say("  订阅 Key 只对套餐内调用有效，和按量付费不是同一套。")
        say("  说明见 references/onboarding.md")
        if args.run:
            return 2

    if not args.run:
        if key_problem:
            head("素材和文案没问题，卡在 Key 上")
            say("  上面那几条就是还不能开工的原因，处理好就能跑。")
            say("  这次是预演，一个接口都没调，没花钱。")
        else:
            head("体检通过，但没有真的调用")
            say("  这次只是预演，一个接口都没调，没花钱。")
            say("  下一步加 --run 才会开始：先加 --stop-at voice，听完自己的声音再决定。")
        return 0

    # ---------------------------------------------------------------- 实际执行
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    say("")
    say(f"  产出目录：{out_dir}")

    record: dict = {
        "created_at": started_at,
        "face": face.name,
        "face_kind": kind,
        "text": text,
        "voice_id": voice_id,
        "voice_cloned": bool(voice_cost),
        "system_voice": args.system_voice,
        "model": args.model,
        "resolution": args.resolution,
        "max_seconds": max_seconds,
    }

    try:
        # 1. 音色
        if voice_cost:
            payload = do_clone(voice_source, voice_id, out_dir)
            demo = payload.get("demo_audio") or ""
            if demo:
                import requests
                demo_path = out_dir / "voice_demo.mp3"
                demo_path.write_bytes(requests.get(demo, timeout=60).content)
                ok("试听音频", demo_path.name)

        # 2. 台词
        audio_path, audio_seconds, subtitles = do_tts(text, voice_id, out_dir)
        if audio_seconds > max_seconds:
            say("")
            bad("实际朗读超出上限", f"{audio_seconds:.1f} 秒 > {max_seconds} 秒")
            say(f"  文案要再删约 {int((audio_seconds - max_seconds) * CHARS_PER_SECOND) + 1} 个字。")
            say("  台词音频已保留，改完文案重跑即可，不会重复收音色费。")
            return 3
        if audio_seconds < REF_AUDIO_MIN:
            bad("朗读太短", f"{audio_seconds:.1f} 秒，接口要求参考音频至少 2 秒")
            return 3

        if args.stop_at == "voice":
            head("停在这一步")
            say(f"  台词音频：{audio_path}")
            record["actual_seconds"] = round(audio_seconds, 2)
            record["status"] = "stopped_at_voice"
            (out_dir / "job.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
            say("  先去听一遍。听着没问题，去掉 --stop-at 再跑一次就出画面。")
            say("  注意：音色 7 天内没被正式用于合成会被系统删除，别放太久。")
            return 0

        # 3. 形象
        head("准备形象素材")
        ratio_for_face = args.ratio
        face_ready, face_kind = prepare_face(face, out_dir, ratio_for_face)
        ok("形象素材就绪", face_ready.name)

        # 4. 画面
        duration = max(VIDEO_MIN_SECONDS, min(max_seconds, int(round(audio_seconds + 0.5))))
        final, task_id = do_video(
            face=face_ready, kind=face_kind, audio=audio_path, text=text,
            out_dir=out_dir, model=args.model,
            resolution=args.resolution, ratio=ratio_for_face, duration=duration,
            prompt_extra=args.prompt_extra, timeout=args.timeout,
        )

        # 5. 交付
        srt = write_srt(subtitles, out_dir / "clip.srt")
        record.update({
            "task_id": task_id,
            "actual_seconds": round(audio_seconds, 2),
            "video_duration": duration,
            "cost_voice": round(voice_cost, 4),
            "cost_tts": round(tts_cost, 4),
            "cost_video": round(estimate_video_cost(args.model, args.resolution, duration), 4),
            "status": "done",
        })
        record["cost_total"] = round(
            record["cost_voice"] + record["cost_tts"] + record["cost_video"], 4
        )
        (out_dir / "job.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))

        head("完成")
        say(f"  成片      {final}")
        say(f"  时长      {duration} 秒（台词 {audio_seconds:.1f} 秒）")
        if srt:
            say(f"  字幕      {srt.name}（可直接拖进剪辑软件）")
        say(f"  本次花费  约 {record['cost_total']:.2f} 元")
        say("")
        say("  成片里是你自己的声音和形象，但画面是模型重新生成的，")
        say("  不是把你原视频换了个音轨——所以构图、口型会有轻微变化，属于正常。")
        return 0

    except MiniMaxError as exc:
        say("")
        bad(f"接口报错 {exc.code}", exc.message)
        hint = ERROR_HINTS.get(int(exc.code) if str(exc.code).lstrip("-").isdigit() else 0)
        if hint:
            say(f"  → {hint}")
        record["status"] = "failed"
        record["error"] = f"{exc.code}: {exc.message}"
        (out_dir / "job.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
        return 4
    except Exception as exc:
        say("")
        bad("执行中断", f"{type(exc).__name__}: {exc}")
        record["status"] = "failed"
        record["error"] = str(exc)
        (out_dir / "job.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
