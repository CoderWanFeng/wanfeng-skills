#!/usr/bin/env python3
"""分阶段生产：口播稿 → 画面拆解 → 声音与 B-roll 预览 → 数字人 → 合成。

**为什么分阶段**：数字人视频按秒计费（0.26 元/秒），是整条链路上唯一的大头。
先把不花钱的部分做完并审到位，确认后才为数字人掏钱，
避免「数字人生成了、B-roll 却要推翻重做」的白花钱。

    # 阶段 1-2：画面拆解（零花费，不调用任何接口）
    python3 scripts/build.py --stage plan

    # 阶段 3-4：合成声音 + 定时间契约 + 出占位预览片（约 0.2 元）
    python3 scripts/build.py --stage broll

    # 阶段 5：逐段生成数字人（花钱；先只出 1 段看效果）
    python3 scripts/build.py --stage digital --limit-segments 1

    # 阶段 6：合成与交付包
    python3 scripts/build.py --stage merge

    # 可选旁支：克隆人形象图（封面 / 静帧用），不在主流程里
    python3 scripts/build.py --stage persona

    # 或者一次跑完（plan → broll → digital → merge，中间有确认关卡）
    python3 scripts/build.py --stage all

输入：
    input/script/*.txt        口播文稿（按句切分后逐段合成）
    input/persona/*           形象素材（视频或图片，作为 H3 参考）
    input/assets/*            B-roll 素材（可选，用于占位预览片）
产物：
    output/final/plan/<job>/       分镜表 storyboard.json + 时间契约 timeline.json
    output/final/voice/<job>/      分段音频
    output/final/talking/<job>/    分段视频、拼接成片、a_roll.json / a_roll.srt
    output/manifest.json          每次运行的模型、参数与成本追溯
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ai_digital_human.pipeline.talking_line import DEFAULT_PROMPT  # noqa: E402
from ai_digital_human.pipeline.persona_line import DEFAULT_SCENES  # noqa: E402
from ai_digital_human.pipeline.voice_line import (  # noqa: E402
    EMOTIONS, KIND_A, estimate_seconds, group_script,
)
from ai_digital_human.pricing import estimate_cost, estimate_image_cost, estimate_video_cost  # noqa: E402
from ai_digital_human.media import resolve_ratio  # noqa: E402
from ai_digital_human.client import load_env_file  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v"}

# 阶段顺序。all = 按这个顺序全跑一遍
STAGE_SEQUENCE = ("plan", "broll", "digital", "merge")
# persona 是可选旁支，不在 all 里，只有显式 --stage persona 才跑
STAGE_CHOICES = (*STAGE_SEQUENCE, "persona", "all")

STAGE_TITLES = {
    "plan": "画面拆解",
    "broll": "声音与 B-roll 预览",
    "digital": "数字人出镜画面",
    "merge": "合成与交付",
    "persona": "克隆人形象图（可选）",
}


@dataclass
class Context:
    """一次运行的全部上下文，各阶段共享。"""

    args: argparse.Namespace
    script_path: Path
    text: str
    groups: list
    job: str
    persona_path: Path | None
    ratio: str
    plan_dir: Path
    voice_dir: Path
    talking_dir: Path
    assets_dir: Path


def find_script(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise SystemExit(f"文稿不存在：{path}")
        return path
    candidates = sorted(p for p in (ROOT / "input" / "script").glob("*.txt"))
    if not candidates:
        raise SystemExit("input/script/ 下没有 .txt 文稿，请放入文稿或用 --script 指定")
    return candidates[0]


def find_persona(explicit: str | None, required: bool = True) -> Path | None:
    """形象素材。只有数字人阶段真的需要它。"""
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise SystemExit(f"形象素材不存在：{path}")
        return path
    folder = ROOT / "input" / "persona"
    candidates = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES | VIDEO_SUFFIXES
    ) if folder.exists() else []
    if not candidates:
        if required:
            raise SystemExit("input/persona/ 下没有形象素材，请放入参考视频或图片")
        return None
    return candidates[0]


def persona_kind(path: Path) -> str:
    return "image" if path.suffix.lower() in IMAGE_SUFFIXES else "video"


def load_prompt_template() -> str:
    template_path = ROOT / "prompts" / "video" / "talking.txt"
    if template_path.is_file():
        return template_path.read_text(encoding="utf-8").strip()
    return DEFAULT_PROMPT


def load_persona_template() -> str:
    template_path = ROOT / "prompts" / "persona" / "portrait.txt"
    if template_path.is_file():
        return template_path.read_text(encoding="utf-8").strip()
    from ai_digital_human.pipeline.persona_line import DEFAULT_PROMPT as PERSONA_PROMPT
    return PERSONA_PROMPT


def parse_scenes(raw: str | None, count: int) -> list[str]:
    if raw:
        scenes = [s.strip() for s in raw.split(",") if s.strip()]
        if scenes:
            return scenes[:count] if count else scenes
    return DEFAULT_SCENES[:count] if count else list(DEFAULT_SCENES)


def append_manifest(entry: dict) -> Path:
    path = ROOT / "output" / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    data.append(entry)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def confirm_gate(args, lines: list[str]) -> bool:
    """审片关卡：确认无误才进入花钱的阶段。

    --yes 跳过；非交互环境（管道、CI）自动放行并留下提示。
    """
    print("\n" + "═" * 60)
    for line in lines:
        print(f"  {line}")
    print("═" * 60)
    if args.yes:
        print("  已用 --yes 跳过确认，继续执行。")
        return True
    if not sys.stdin.isatty():
        print("  非交互环境，自动继续（如需人工把关请用分阶段执行）。")
        return True
    try:
        answer = input("  确认无误？输入 yes 继续：").strip().lower()
    except EOFError:
        return True
    if answer in ("y", "yes", "是", "好", "确认"):
        return True
    print("  已中止。可改稿后重跑，或用 --stage plan / --stage broll 单独推进。")
    return False


def print_storyboard(shots, payload: dict) -> None:
    """把分镜表打印成人能直接审的清单。"""
    total = payload.get("total_duration", 0)
    a_total = payload.get("a_roll_duration", 0)
    b_total = payload.get("b_roll_duration", 0)
    print(f"\n分镜表  共 {len(shots)} 段 / 总 {total:.1f}s"
          f"（A-roll {a_total:.1f}s / B-roll {b_total:.1f}s）")
    for shot in shots:
        tag = "A" if shot.is_a_roll else "B"
        head = f"  {shot.index:02d} [{tag}] {shot.start:6.2f}–{shot.end:6.2f}s ({shot.duration:.1f}s)"
        extras = []
        if shot.emotion:
            extras.append(f"情绪 {shot.emotion}")
        if shot.scene:
            extras.append(f"场景 {shot.scene}")
        if extras:
            head += "  " + "，".join(extras)
        print(head)
        print(f"      台词：{shot.text}")
        print(f"      职责：{shot.purpose or '（未填写）'}")
        if shot.style:
            print(f"      风格：{shot.style}")
        if shot.assets:
            print(f"      素材：{'、'.join(shot.assets)}")
        if shot.beats:
            beats = "  ".join(f"{b.at:.1f}s {b.action}" for b in shot.beats)
            print(f"      逐拍：{beats}")
    print()


def stage_plan(ctx: Context) -> dict:
    """阶段 1-2：口播稿 → 画面拆解。零花费，不调用任何接口。"""
    from ai_digital_human.plan import build_storyboard, load_storyboard, merge_storyboard, write_storyboard

    args = ctx.args
    print(f"\n[{STAGE_TITLES['plan']}] 把口播稿拆成画面需求…")
    shots = build_storyboard(ctx.groups, assets_dir=ctx.assets_dir)
    existing = load_storyboard(ctx.plan_dir / "storyboard.json")
    shots = merge_storyboard(shots, existing)
    result = write_storyboard(
        shots, ctx.plan_dir, job=ctx.job, script_path=ctx.script_path,
        voice=args.voice, model=args.voice_model,
    )
    payload = result["payload"]
    print_storyboard(shots, payload)
    print(f"  分镜表   {result['storyboard']}")
    print(f"  时间契约 {result['timeline']}")
    print("  提示：可以直接改 storyboard.json 里的 purpose / style / assets / beats，"
          "重跑本阶段会保留这些人工细化的字段。")
    return {"plan": payload, "files": {
        "storyboard": str(result["storyboard"]),
        "timeline": str(result["timeline"]),
    }}


def stage_broll(ctx: Context) -> dict:
    """阶段 3-4：合成声音 → 定时间契约 → 出占位预览片。

    声音是唯一必须花钱的一步，但只占成本 0.1% 左右；
    真正贵的是后面的数字人视频，所以这一步值得先把时间轴钉死。
    """
    from ai_digital_human.plan import build_storyboard, load_storyboard, merge_storyboard, write_storyboard
    from ai_digital_human.pipeline.voice_line import synthesize_script

    args = ctx.args
    print(f"\n[{STAGE_TITLES['broll']}] 合成声音，钉死时间轴…")
    voice_result = synthesize_script(
        ctx.text,
        voice_id=args.voice,
        out_dir=ctx.voice_dir,
        model=args.voice_model,
        max_seconds=args.segment_seconds,
        emotion=args.emotion,
    )
    print(f"  完成：{len(voice_result.segments)} 段，共 {voice_result.total_duration:.1f}s，"
          f"计费 {voice_result.total_chars} 字符，{voice_result.cost:.3f} 元")

    durations = {seg.index: seg.duration for seg in voice_result.segments}
    shots = build_storyboard(ctx.groups, durations=durations, assets_dir=ctx.assets_dir)
    existing = load_storyboard(ctx.plan_dir / "storyboard.json")
    shots = merge_storyboard(shots, existing)
    for shot, seg in zip(shots, voice_result.segments):
        shot.audio = seg.audio_path.name
    result = write_storyboard(
        shots, ctx.plan_dir, job=ctx.job, script_path=ctx.script_path,
        voice=args.voice, model=args.voice_model,
    )
    payload = result["payload"]
    print_storyboard(shots, payload)

    # 交付包（时间码表 + 全局字幕）——此时还没有视频，video 字段先为空
    from ai_digital_human.delivery import write_delivery
    delivery = write_delivery(
        voice_result.segments, ctx.talking_dir, job=ctx.job, script_path=ctx.script_path
    )
    print(f"  时间码表 {delivery['_files']['json']}")
    print(f"  字幕     {delivery['_files']['srt']}")

    # 占位预览片：A 段暖白留白位，B 段深灰素材位，带完整音轨
    preview = ctx.plan_dir / "preview.mp4"
    try:
        from ai_digital_human.media.placeholder import make_placeholder
        audio_paths = {seg.index: seg.audio_path for seg in voice_result.segments}
        make_placeholder(
            shots, preview, audio_paths=audio_paths,
            assets_dir=ctx.assets_dir, ratio=ctx.ratio,
        )
        print(f"  预览片   {preview}")
    except Exception as exc:                      # 占位片失败不该挡住主流程
        print(f"  预览片生成失败（不影响后续）：{exc}")

    return {
        "broll": {
            "voice_id": args.voice,
            "model": args.voice_model,
            "segments": len(voice_result.segments),
            "duration": round(voice_result.total_duration, 2),
            "charged_chars": voice_result.total_chars,
            "cost": round(voice_result.cost, 4),
            "default_emotion": args.emotion,
            "emotions": sorted({s.emotion for s in voice_result.segments if s.emotion}),
        },
        "files": {
            "storyboard": str(result["storyboard"]),
            "timeline": str(result["timeline"]),
            "timeline_json": delivery["_files"]["json"],
            "subtitles": delivery["_files"]["srt"],
            "preview": str(preview),
        },
    }


def stage_digital(ctx: Context) -> dict:
    """阶段 5：逐段生成数字人出镜画面。唯一花钱的环节。"""
    from ai_digital_human.plan import dict_to_shot, load_storyboard, restore_segments
    from ai_digital_human.pipeline.talking_line import generate_talking_videos

    args = ctx.args
    if ctx.persona_path is None:
        raise SystemExit("数字人阶段需要形象素材：放到 input/persona/ 或用 --persona 指定")

    storyboard = load_storyboard(ctx.plan_dir / "storyboard.json")
    if not storyboard:
        raise SystemExit(
            f"找不到分镜表：{ctx.plan_dir / 'storyboard.json'}\n"
            f"请先执行：python3 scripts/build.py --stage broll --job {ctx.job}"
        )
    shots = [dict_to_shot(item) for item in storyboard.get("segments", [])]
    segments = restore_segments(shots, ctx.voice_dir)
    missing = [s.index for s in segments if not s.audio_path or not s.audio_path.is_file()]
    if missing:
        raise SystemExit(
            f"分段音频缺失（段 {missing}）：{ctx.voice_dir}\n"
            f"请先执行：python3 scripts/build.py --stage broll --job {ctx.job}"
        )

    # 试跑：只出前 N 段 A-roll，其余 A-roll 段先不做
    if args.limit_segments:
        picked = 0
        limited = []
        for seg in segments:
            if seg.is_a_roll:
                if picked >= args.limit_segments:
                    continue
                picked += 1
            limited.append(seg)
        segments = limited
        print(f"  试跑模式：只生成前 {args.limit_segments} 段 A-roll")

    print(f"\n[{STAGE_TITLES['digital']}] 逐段生成数字人画面…")
    talking_result = generate_talking_videos(
        segments,
        persona_asset=ctx.persona_path,
        out_dir=ctx.talking_dir,
        model=args.video_model,
        resolution=args.resolution,
        ratio=ctx.ratio,
        prompt_template=load_prompt_template(),
        scene=args.scene,
        persona_kind=persona_kind(ctx.persona_path),
        max_workers=args.max_workers,
        transition=args.transition,
        resume=not args.no_resume,
    )
    reused = [seg.index for seg in talking_result.segments if seg.reused]
    if reused:
        print(f"  复用已有分段：{reused}（未重复计费）")
    remuxed = [seg.index for seg in talking_result.segments if seg.remuxed]
    if remuxed:
        print(f"  重做音轨对齐：{remuxed}")

    # 复用与重做音轨的段没有产生新的模型调用，不计入本次计费时长
    paid = [seg for seg in talking_result.segments if not seg.reused]
    video_seconds = sum(
        max(4, min(15, int(round(seg.duration + 0.5)))) for seg in paid
    )
    video_cost = estimate_video_cost(args.video_model, args.resolution, video_seconds)
    print(f"  完成：{len(talking_result.segments)} 段视频，视频计费时长 {video_seconds}s，"
          f"预计 {video_cost:.3f} 元")

    return {
        "digital": {
            "model": args.video_model,
            "resolution": args.resolution,
            "ratio": ctx.ratio,
            "persona": str(ctx.persona_path),
            "segments": len(talking_result.segments),
            "billed_seconds": video_seconds,
            "duration": round(talking_result.total_duration, 2),
            "cost": round(video_cost, 4),
            "max_workers": args.max_workers,
            "transition": args.transition,
            "reused_segments": reused,
            "remuxed_segments": remuxed,
            "output": str(talking_result.final_video),
        }
    }


def stage_merge(ctx: Context) -> dict:
    """阶段 6：把数字人画面拼成片，并把视频路径回填到时间码表。"""
    from ai_digital_human.delivery import attach_videos

    args = ctx.args
    print(f"\n[{STAGE_TITLES['merge']}] 合成成片…")
    videos = {}
    for path in sorted(ctx.talking_dir.glob("seg_*.mp4")):
        try:
            index = int(path.stem.split("_")[-1])
        except ValueError:
            continue
        videos[index] = path

    timeline_json = ctx.talking_dir / "a_roll.json"
    if timeline_json.is_file():
        payload = attach_videos(timeline_json, videos)
        print(f"  时间码表 {timeline_json}（已回填 {len(videos)} 段视频路径）")
    else:
        payload = {}
        print(f"  警告：找不到时间码表 {timeline_json}，跳过回填")

    final = ctx.talking_dir / "talking.mp4"
    if final.is_file():
        print(f"  成片     {final}")
    else:
        print(f"  警告：找不到成片 {final}，请先执行 --stage digital")

    return {
        "merge": {
            "timeline": str(timeline_json),
            "videos": len(videos),
            "final": str(final) if final.is_file() else "",
            "a_roll_duration": payload.get("a_roll_duration", 0),
            "b_roll_duration": payload.get("b_roll_duration", 0),
            "total_duration": payload.get("total_duration", 0),
        }
    }


def stage_persona(ctx: Context) -> dict:
    """可选旁支：生成克隆人形象图（封面 / 静帧用）。

    不在六步主流程里：数字人画面直接用 reference_video，不需要形象图。
    只有显式 `--stage persona` 才会跑，避免误花钱。
    """
    from ai_digital_human.pipeline.persona_line import generate_persona_images

    args = ctx.args
    if ctx.persona_path is None:
        raise SystemExit("形象图阶段需要形象素材：放到 input/persona/ 或用 --persona 指定")

    print(f"\n[{STAGE_TITLES['persona']}] 生成克隆人形象图…")
    scenes = parse_scenes(args.persona_scenes, args.persona_count)
    result = generate_persona_images(
        ctx.persona_path,
        ctx.talking_dir / "persona",
        prompt_template=load_persona_template(),
        model=args.persona_model,
        aspect_ratio=ctx.ratio,
        scenes=scenes,
        persona_kind=persona_kind(ctx.persona_path),
    )
    print(f"  形象图   {len(result.images)} 张，计费 {result.cost:.3f} 元")
    for image in result.images:
        print(f"    {image.path.name}  ← {image.reference_frame.name}")

    return {
        "persona": {
            "model": args.persona_model,
            "aspect_ratio": result.aspect_ratio,
            "scenes": scenes,
            "images": [str(img.path) for img in result.images],
            "cost": round(result.cost, 4),
        }
    }


def run_stage(stage: str, ctx: Context) -> dict | None:
    if stage == "plan":
        return stage_plan(ctx)
    if stage == "broll":
        return stage_broll(ctx)
    if stage == "digital":
        return stage_digital(ctx)
    if stage == "merge":
        return stage_merge(ctx)
    if stage == "persona":
        return stage_persona(ctx)
    raise SystemExit(f"未知阶段：{stage}")


def main() -> int:
    load_env_file()
    parser = argparse.ArgumentParser(description="ai-digital-human 分阶段生产")
    parser.add_argument("--script", default=None, help="口播文稿路径")
    parser.add_argument("--persona", default=None, help="形象素材路径（视频或图片）")
    parser.add_argument("--voice", default=os.environ.get("MINIMAX_VOICE_ID", "my-clone-voice"),
                        help="克隆音色 voice_id，默认读环境变量 MINIMAX_VOICE_ID")
    parser.add_argument("--voice-model", default="speech-2.8-hd", help="语音合成模型")
    parser.add_argument("--persona-model", default="image-01", help="克隆人形象图模型")
    parser.add_argument("--persona-count", type=int, default=4, help="生成多少张克隆人形象图")
    parser.add_argument("--persona-scenes", default=None, help="逗号分隔的场景描述")
    parser.add_argument("--video-model", default="MiniMax-H3-Lite", help="视频模型")
    parser.add_argument("--resolution", default="768P", help="视频分辨率")
    parser.add_argument("--ratio", default="auto", help="视频宽高比，auto = 跟随素材")
    parser.add_argument("--scene", default="", help="场景描述，会拼进视频提示词")
    parser.add_argument("--emotion", default=None,
                        help="全局兜底情绪（happy/sad/angry/fearful/disgusted/surprised/calm/fluent/whisper）；"
                             "文稿里用 [[A:happy]] 指定的逐段情绪优先级更高")
    parser.add_argument("--job", default=None, help="任务名，默认用时间戳")
    parser.add_argument("--max-workers", type=int, default=4,
                        help="视频生成并发数，长视频用 4-6 可显著缩短等待时间")
    parser.add_argument("--transition", type=float, default=0.25,
                        help="分段接缝的交叉淡化时长（秒），0 表示硬接")
    parser.add_argument("--no-resume", action="store_true",
                        help="不复用已生成的分段，强制重新调用接口")
    parser.add_argument("--skip-persona", action="store_true",
                        help="不生成克隆人形象图（默认行为，保留此参数只为兼容旧命令）")
    parser.add_argument("--skip-video", action="store_true", help="只生成声音，不生成视频")
    parser.add_argument("--limit-segments", type=int, default=None, help="只处理前 N 段 A-roll（试跑省钱）")
    parser.add_argument("--segment-seconds", type=float, default=13.0,
                        help="单段台词的目标时长上限（秒），调小可获得更细的字幕时间码")
    parser.add_argument("--stage", choices=STAGE_CHOICES, default="all",
                        help="执行到哪一步：plan 画面拆解 / broll 声音与预览 / "
                             "digital 数字人画面 / merge 合成 / persona 形象图（可选旁支） / all 全跑")
    parser.add_argument("--assets", default=None,
                        help="B-roll 素材目录，默认 input/assets；用于占位预览片")
    parser.add_argument("--yes", action="store_true", help="跳过审片确认关卡")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划与预计花费")
    args = parser.parse_args()

    script_path = find_script(args.script)
    text = script_path.read_text(encoding="utf-8").strip()
    groups = group_script(text, max_seconds=args.segment_seconds)

    job = args.job or time.strftime("%Y%m%d-%H%M%S")
    persona_path = find_persona(args.persona, required=False)
    ratio = resolve_ratio(args.ratio, persona_path) if persona_path else "9:16"
    assets_dir = Path(args.assets) if args.assets else ROOT / "input" / "assets"

    ctx = Context(
        args=args,
        script_path=script_path,
        text=text,
        groups=groups,
        job=job,
        persona_path=persona_path,
        ratio=ratio,
        plan_dir=ROOT / "output" / "final" / "plan" / job,
        voice_dir=ROOT / "output" / "final" / "voice" / job,
        talking_dir=ROOT / "output" / "final" / "talking" / job,
        assets_dir=assets_dir,
    )

    a_roll_groups = [g for g in groups if g.kind == KIND_A]
    b_roll_groups = [g for g in groups if g.kind != KIND_A]

    stages = list(STAGE_SEQUENCE) if args.stage == "all" else [args.stage]
    if args.skip_video:
        stages = [s for s in stages if s not in ("digital", "merge")]

    # 预估只算本次真正会跑到的阶段，避免「plan 是免费的却报 6.5 元」这种误导
    tts_cost = sum(estimate_cost(g.text, args.voice_model) for g in groups) if "broll" in stages else 0.0
    a_seconds = sum(
        max(4, min(15, int(round(estimate_seconds(g.text) + 0.5))))
        for g in a_roll_groups
    ) if "digital" in stages else 0

    print(f"任务 {job}")
    print(f"  阶段     {' → '.join(stages)}")
    print(f"  文稿     {script_path}（{len(groups)} 段："
          f"A-roll {len(a_roll_groups)} / B-roll {len(b_roll_groups)}）")
    print(f"  音色     {args.voice} / {args.voice_model}")
    if persona_path:
        print(f"  形象素材 {persona_path}（{persona_kind(persona_path)}）")
    print(f"  视频     {args.video_model} @ {args.resolution} {ratio}")

    # 预估只算本次真正会跑到的阶段
    cost_parts = []
    if "broll" in stages:
        cost_parts.append(f"TTS {tts_cost:.3f} 元")
    if "digital" in stages:
        cost_parts.append(
            f"视频约 {estimate_video_cost(args.video_model, args.resolution, a_seconds):.3f} 元")
    if "persona" in stages:
        cost_parts.append(f"形象图 {estimate_image_cost(args.persona_count):.3f} 元")
    print(f"  预计花费 {'，'.join(cost_parts) if cost_parts else '0 元（本次不调用任何付费接口）'}")

    bad_emotions = sorted({g.emotion for g in groups if g.emotion and g.emotion not in EMOTIONS})
    if bad_emotions:
        print(f"警告：文稿里有平台不支持的情绪 {bad_emotions}，这些段落会按无情绪处理。"
              f"可选：{', '.join(EMOTIONS)}")
    if args.emotion and args.emotion not in EMOTIONS:
        print(f"警告：--emotion {args.emotion!r} 不在平台支持列表内，已忽略。"
              f"可选：{', '.join(EMOTIONS)}")
        args.emotion = None

    if args.dry_run:
        print("\n--dry-run，未执行任何调用。")
        for idx, group in enumerate(groups, start=1):
            tag = "A-roll" if group.kind == KIND_A else "B-roll"
            extra = []
            if group.emotion:
                extra.append(f"情绪={group.emotion}")
            if group.scene:
                extra.append(f"场景={group.scene}")
            if group.note:
                extra.append(f"提示={group.note}")
            suffix = f"（{'，'.join(extra)}）" if extra else ""
            print(f"  {idx:02d}. [{tag}]{suffix} {group.text}")
        return 0

    entry = {
        "job": job,
        "stage": args.stage,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "script": str(script_path),
        "persona_source": str(persona_path) if persona_path else "",
    }

    for stage in stages:
        result = run_stage(stage, ctx)
        if result:
            for key, value in result.items():
                if key == "files":
                    entry.setdefault("files", {}).update(value)
                else:
                    entry[key] = value

        # 审片关卡：B-roll 之后、数字人之前
        if stage == "broll" and "digital" in stages:
            ok = confirm_gate(args, [
                "审片关卡 —— 请确认三件事：",
                "  1. B-roll 画面内容与风格（占位片里 B 段是深灰素材位，A 段是暖白留白位）",
                "  2. 口播稿文案",
                "  3. 整片节奏（占位片带完整音轨，可直接听）",
                "",
                "确认无误后再生成数字人——那是唯一花钱的环节。",
            ])
            if not ok:
                entry["aborted_at"] = stage
                append_manifest(entry)
                return 1

    cost = 0.0
    for key in ("broll", "digital", "persona"):
        cost += float(entry.get(key, {}).get("cost", 0))
    if entry.get("broll"):
        entry.setdefault("voice", entry["broll"])
    entry["total_cost"] = round(cost, 4)
    manifest_path = append_manifest(entry)
    print(f"\n完成，总花费约 {entry['total_cost']:.3f} 元，追溯记录：{manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())