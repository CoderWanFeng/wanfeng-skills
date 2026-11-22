#!/usr/bin/env python3
"""在当前工作目录初始化一个可用的数字人视频工作区。

Skill 包本身应保持只读：引擎代码复制一份到工作目录，
用户的文稿、形象素材、音色样本、.env 与全部产物都留在工作目录里。

纯本地操作，不调用任何接口、不产生费用。

用法：
    # 云端 H3 + MiniMax 克隆音色（默认，按秒计费）
    python3 scripts/init_workspace.py --target ./dh --script 稿.txt --persona 自拍.mov --voice 录音.mp3

    # 软件积分出镜（零 RMB，画面自己用积分生成后放进 input/credits/）
    python3 scripts/init_workspace.py --target ./dh --video-backend credits --script 稿.txt

    # 自托管 H3 + 本地 Ming 配音
    python3 scripts/init_workspace.py --target ./dh --video-backend compshare --voice-backend local \
      --voice-reference 参考音.wav --ref-text "参考音频的准确逐字文本" \
      --ming-model /path/to/Ming-3.0-tts-0.5B-8bit --compshare-base-url http://实例:8188
"""

from __future__ import annotations

import argparse
import shutil
import stat
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = SKILL_ROOT / "engine"
ENV_TEMPLATE = SKILL_ROOT / "templates" / "env.example"

RUNTIME_DIRS = (
    "input/script",
    "input/persona",
    "input/voice",
    "input/voice-reference",
    "input/assets",
    "input/credits",
    "output",
    "config",
    "logs",
)
CODE_DIRS = ("scripts", "src", "prompts")


def merge_tree(src: Path, dst: Path) -> int:
    """只补缺失文件，绝不覆盖用户已经改过的代码或产物。"""
    copied = 0
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        if item.name == "__pycache__" or item.suffix == ".pyc":
            continue
        target = dst / item.name
        if item.is_dir():
            copied += merge_tree(item, target)
        elif not target.exists():
            shutil.copy2(item, target)
            copied += 1
    return copied


def place_asset(path: Path, dest_dir: Path) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / path.name
    if target.exists():
        return f"已存在，未覆盖：{target}"
    shutil.copy2(path, target)
    return f"已放入：{target}"


def write_env(root: Path, args) -> tuple[str, Path]:
    """按选的后端写 .env；已存在则只在末尾补注释，不动用户填的值。"""
    env_path = root / ".env"
    if env_path.exists():
        with env_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n# 本次初始化选择的组合：视频 {args.video_backend} / 语音 {args.voice_backend}"
                f" / MiniMax 接入 {args.minimax_route}\n"
            )
        return "已存在，追加了本次选择的注释", env_path

    if ENV_TEMPLATE.is_file():
        shutil.copy2(ENV_TEMPLATE, env_path)
    else:
        env_path.write_text("# 填入自己的密钥与服务地址\nMINIMAX_API_KEY=\n", encoding="utf-8")

    extra = [f"DH_VIDEO_BACKEND={args.video_backend}", f"DH_VOICE_BACKEND={args.voice_backend}"]
    if args.minimax_route:
        extra.append(f"DH_MINIMAX_ROUTE={args.minimax_route}")
    if args.compshare_base_url:
        extra.append(f"COMPSHARE_BASE_URL={args.compshare_base_url}")
    if args.ming_model:
        extra.append(f"MING_TTS_MODEL={args.ming_model}")
    if args.voice_reference:
        extra.append(f"MING_TTS_REF_AUDIO={Path(args.voice_reference).resolve()}")
    if args.ref_text:
        extra.append(f"MING_TTS_REF_TEXT={args.ref_text}")
    with env_path.open("a", encoding="utf-8") as handle:
        handle.write("\n# 本次初始化选择的组合\n" + "\n".join(extra) + "\n")
    env_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return "已从模板创建（权限 600）", env_path


def next_steps(args, env_path: Path, root: Path) -> list[str]:
    steps = []
    if args.video_backend == "minimax" or args.voice_backend == "minimax":
        if args.minimax_route == "recommended":
            steps.append(
                f"填 {env_path} 里的 MINIMAX_RECOMMENDED_API_KEY 和 "
                "MINIMAX_RECOMMENDED_BASE_URL（推荐平台的地址与密钥）"
            )
        else:
            steps.append(
                f"填 {env_path} 里的 MINIMAX_API_KEY（sk-api- 开头的按量付费密钥，不是 sk-cp- 订阅通道）"
            )
    if args.voice_backend == "local":
        steps.append(
            "确认本地 Ming 就绪：MING_TTS_PYTHON / MING_TTS_MODEL / "
            "MING_TTS_REF_AUDIO / MING_TTS_REF_TEXT 四项都要有值"
        )
    if args.video_backend == "compshare":
        steps.append("开工前把自托管实例开机，并确认 COMPSHARE_BASE_URL 可访问")
    if args.video_backend == "credits":
        steps.append(
            "画面用软件积分生成：先跑一次 --stage digital --video-backend credits，"
            "它会写出 credits-brief.md 清单；照清单生成片段放进 input/credits/ 再重跑"
        )
    steps.append(f"把文稿放进 {root / 'input/script'}，形象素材放进 {root / 'input/persona'}")
    skill_root = Path(__file__).resolve().parent.parent
    steps.append(
        f"体检：python3 {skill_root / 'scripts/preflight.py'} --root {root} "
        f"--video-backend {args.video_backend} --voice-backend {args.voice_backend}"
    )
    if args.voice_backend == "minimax":
        steps.append("首次使用先克隆音色：python3 scripts/clone_voice.py input/voice/xxx.mp3 --voice-id my-clone-voice")
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化数字人视频工作区（纯本地、零费用）")
    parser.add_argument("--target", default="./digital-human-work",
                        help="工作目录路径，默认 ./digital-human-work")
    parser.add_argument("--script", default=None, help="口播稿 .txt，复制到 input/script/")
    parser.add_argument("--persona", default=None, help="形象视频或图片，复制到 input/persona/")
    parser.add_argument("--voice", default=None, help="本人录音，复制到 input/voice/（克隆音色用）")
    parser.add_argument("--video-backend", choices=("credits", "minimax", "compshare"),
                        default="minimax", help="出镜画面后端，默认 minimax")
    parser.add_argument("--voice-backend", choices=("minimax", "local"),
                        default="minimax", help="语音后端，默认 minimax")
    parser.add_argument("--minimax-route", choices=("official", "recommended"), default=None,
                        help="MiniMax 接入方式：official 官方 / recommended 推荐平台")
    parser.add_argument("--voice-reference", default=None,
                        help="本地 Ming 用的参考音频（10 秒以上单人说话）")
    parser.add_argument("--ref-text", default=None, help="参考音频的准确逐字文本")
    parser.add_argument("--ming-model", default=None, help="本地 Ming 模型目录")
    parser.add_argument("--compshare-base-url", default=None, help="自托管 ComfyUI 实例地址")
    args = parser.parse_args()

    if not ENGINE_DIR.is_dir():
        print(f"找不到引擎目录：{ENGINE_DIR}\nSkill 包可能不完整，请重新解压。")
        return 1
    if args.voice_backend == "local" and not (args.voice_reference and args.ref_text):
        print("选了本地配音，就必须同时给 --voice-reference 和 --ref-text。")
        return 2

    root = Path(args.target).expanduser().resolve()
    existed = root.exists()
    root.mkdir(parents=True, exist_ok=True)

    copied = 0
    for name in CODE_DIRS:
        copied += merge_tree(ENGINE_DIR / name, root / name)
    for name in RUNTIME_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)

    env_status, env_path = write_env(root, args)

    print(f"工作区：{root}")
    print(f"{'已存在，补齐缺失文件' if existed else '新建完成'}；引擎补入 {copied} 个文件")
    print(f".env：{env_status}")
    print(f"后端：画面 {args.video_backend} / 语音 {args.voice_backend}"
          + (f" / MiniMax 接入 {args.minimax_route}" if args.minimax_route else ""))

    for label, value, subdir in (
        ("口播稿", args.script, "input/script"),
        ("形象素材", args.persona, "input/persona"),
        ("本人录音", args.voice, "input/voice"),
        ("参考音频", args.voice_reference, "input/voice-reference"),
    ):
        if not value:
            continue
        src = Path(value).expanduser().resolve()
        if not src.is_file():
            print(f"{label}不存在，跳过：{src}")
            continue
        print(f"{label}：{place_asset(src, root / subdir)}")

    print("\n下一步：")
    for idx, step in enumerate(next_steps(args, env_path, root), start=1):
        print(f"  {idx}. {step}")
    print("\n本脚本没有发起任何网络请求，也没有产生费用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
