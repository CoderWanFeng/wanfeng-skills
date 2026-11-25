#!/usr/bin/env python3
"""在当前工作目录初始化一个可用的数字人视频工作区。

Skill 包本身应保持只读：引擎代码复制一份到工作目录，
用户的文稿、形象素材、音色样本、.env 与全部产物都留在工作目录里。

纯本地操作，不调用任何接口、不产生费用。

用法：
    # 云端 H3 + MiniMax 克隆音色（默认，按秒计费）
    python3 scripts/init_digital_workspace.py --target ./dh --script 稿.txt --persona 自拍.mov --voice 录音.mp3

    # 软件积分出镜（零 RMB，画面自己用积分生成后放进 input/credits/）
    python3 scripts/init_digital_workspace.py --target ./dh --video-backend credits --script 稿.txt

    # 自托管 H3 + 本地 Ming 配音
    python3 scripts/init_digital_workspace.py --target ./dh --video-backend compshare --voice-backend local \
      --voice-reference 参考音.wav --ref-text "参考音频的准确逐字文本" \
      --ming-model /path/to/Ming-3.0-tts-0.5B-8bit --compshare-base-url http://实例:8188
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import shlex
import stat
import tarfile
from pathlib import Path, PurePosixPath

SKILL_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = SKILL_ROOT / "engine"
ENV_TEMPLATE = SKILL_ROOT / "templates" / "digital.env.example"
ARCHIVE_SHA256 = ""  # 分发时由打包器填入，源码版按逐文件哈希校验

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


def safe_target(path: Path) -> None:
    """已有父目录也不得是链接，防止只补缺失文件时写出工作区。"""
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"目标含符号链接：{path}")


def engine_payloads():
    """先验证完整来源与所有条目，再允许创建工作区。"""
    expected = json.loads((SKILL_ROOT / 'engine-source.json').read_text())['files']
    for name in expected:
        rel = PurePosixPath(name)
        if name != 'README.md' and (rel.is_absolute() or '..' in rel.parts or '\\' in name
                or rel.as_posix() != name or not rel.parts or rel.parts[0] not in CODE_DIRS):
            raise ValueError(f'来源清单含危险路径：{name}')
    payloads = {}
    archive = SKILL_ROOT / 'engine.tar.gz'
    if ARCHIVE_SHA256:
        data = archive.read_bytes()
        if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256:
            raise ValueError('引擎归档哈希不匹配')
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
            for item in tar.getmembers():
                name = item.name
                rel = PurePosixPath(name)
                if (not item.isfile() or rel.is_absolute() or '..' in rel.parts
                        or '\\' in name or rel.as_posix() != name
                        or not rel.parts or rel.parts[0] not in CODE_DIRS
                        or name in payloads):
                    raise ValueError(f'危险归档条目：{name}')
                payloads[name] = (tar.extractfile(item).read(), item.mode & 0o777)
    else:
        for name in expected:
            if name == 'README.md':
                continue
            path = ENGINE_DIR / name
            safe_target(path)
            payloads[name] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
    wanted = {k: v for k, v in expected.items() if k != 'README.md'}
    if set(payloads) != set(wanted):
        raise ValueError('引擎条目不完整或含额外文件')
    for name, (data, _) in payloads.items():
        if hashlib.sha256(data).hexdigest() != wanted[name]:
            raise ValueError(f'引擎文件损坏：{name}')
    return payloads


def install_engine(root, payloads):
    for name in (*payloads, *RUNTIME_DIRS, '.env'):
        safe_target(root / name)
        if (root / name).exists() and name in payloads and not (root / name).is_file():
            raise ValueError(f'目标不是普通文件：{name}')
    count = 0
    for name, (data, mode) in payloads.items():
        target = root / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(data)
            target.chmod(mode)
            count += 1
    return count


def place_asset(path: Path, dest_dir: Path) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / path.name
    safe_target(target)
    if target.exists():
        return f"已存在，未覆盖：{target}"
    shutil.copy2(path, target)
    return f"已放入：{target}"


def write_env(root: Path, args) -> tuple[str, Path]:
    """按选的后端创建 .env；已有配置逐字保留。"""
    env_path = root / ".env"
    if env_path.exists():
        return "已存在，未修改；以后端配置现值为准", env_path

    template = (ENV_TEMPLATE.read_text(encoding="utf-8") if ENV_TEMPLATE.is_file()
                else "# 填入自己的密钥与服务地址\nMINIMAX_API_KEY=\n")

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
    with os.fdopen(os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                   "w", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), stat.S_IRUSR | stat.S_IWUSR)
        handle.write(template + "\n# 本次初始化选择的组合\n" + "\n".join(extra) + "\n")
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
        steps.append("自托管实例需要另计开机费用；取得用户授权后才启动，本工具不会开机")
    if args.video_backend == "credits":
        steps.append(
            "画面用软件积分生成：先跑一次 --stage digital --video-backend credits，"
            "它会写出 credits-brief.md 清单；照清单生成片段放进 input/credits/ 再重跑"
        )
    steps.append(f"把文稿放进 {root / 'input/script'}，形象素材放进 {root / 'input/persona'}")
    skill_root = Path(__file__).resolve().parent.parent
    script = root / 'input/script' / (Path(args.script).name if args.script else 'marked.txt')
    steps.append('先确认明确标记每段的预分镜，再依次执行 plan → broll 配音试听 → digital 样段 → merge；各生成阶段须单独授权')
    steps.append('体检：' + shlex.join([
        'python3', str(skill_root / 'scripts/preflight_digital.py'), '--root', str(root),
        '--script', str(script), '--video-backend', args.video_backend,
        '--voice-backend', args.voice_backend,
    ]))
    if args.voice_backend == "minimax":
        steps.append("首次克隆音色涉及上传和计费，先说明并获得授权；不要把 clone_voice.py 当零调用体检")
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化数字人视频工作区（纯本地、零费用）")
    parser.add_argument("--target", default="./mograph-task/digital-human",
                        help="工作目录路径，默认 ./mograph-task/digital-human")
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

    try:
        payloads = engine_payloads()
    except (OSError, ValueError, tarfile.TarError) as exc:
        print(f"引擎校验失败：{exc}")
        return 1
    if args.voice_backend == "local" and not (args.voice_reference and args.ref_text):
        print("选了本地配音，就必须同时给 --voice-reference 和 --ref-text。")
        return 2

    root = Path(args.target).expanduser().absolute()
    safe_target(root)
    root = root.resolve()
    if root == SKILL_ROOT or SKILL_ROOT in root.parents:
        raise ValueError('工作区不能位于 Skill 安装目录内')
    existed = root.exists()
    copied = install_engine(root, payloads)
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
