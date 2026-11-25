#!/usr/bin/env python3
"""数字人分支专用零调用体检；不打印密钥，不联网，不自动安装依赖。"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from digital_contract import validate_marked_script


def read_env(root):
    values = dict(os.environ)
    path = root / '.env'
    if path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('\"\'')
    return values


def configuration(root, args):
    env = read_env(root)
    for key, attr, default in (
        ('DH_VIDEO_BACKEND', 'video_backend', 'minimax'),
        ('DH_VOICE_BACKEND', 'voice_backend', 'minimax'),
        ('DH_MINIMAX_ROUTE', 'minimax_route', 'official'),
        ('MINIMAX_VOICE_ID', 'voice', 'my-clone-voice'),
    ):
        setattr(args, attr, getattr(args, attr, None) or env.get(key) or default)
    if args.video_backend not in ('minimax', 'credits', 'compshare') or args.voice_backend not in ('minimax', 'local') or args.minimax_route not in ('official', 'recommended'):
        raise ValueError('后端或路由配置非法')
    return env


def check(root, script, args, *, generation=False):
    errors = []
    env = configuration(root, args)
    if sys.version_info < (3, 10):
        errors.append('数字人引擎需要 Python 3.10+；本地 Ming 使用已有专用环境')
    if not (root / 'scripts/build.py').is_file():
        errors.append('工作区引擎不存在，请先运行 init_digital_workspace.py')
    if importlib.util.find_spec('requests') is None:
        errors.append('缺少 requests；确认后自行安装 requirements-digital.txt，本工具不自动安装')
    try:
        validate_marked_script(script.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    if generation:
        for program in ('ffmpeg', 'ffprobe'):
            if not shutil.which(program):
                errors.append(f'缺少 {program}')
        mini = (args.stage == 'broll' and args.voice_backend == 'minimax') or (args.stage == 'digital' and args.video_backend == 'minimax')
        if mini:
            if env.get('DH_MINIMAX_ROUTE') and env['DH_MINIMAX_ROUTE'] != args.minimax_route:
                errors.append('命令行路由与 .env 不一致；原引擎鉴权会重读 .env，请统一路由并新建 job')
            key = 'MINIMAX_API_KEY' if args.minimax_route == 'official' else 'MINIMAX_RECOMMENDED_API_KEY'
            if not env.get(key) or env[key] == 'REPLACE_ME':
                errors.append(f'未配置 {key}（不显示其值）')
            if args.minimax_route == 'recommended' and not env.get('MINIMAX_RECOMMENDED_BASE_URL'):
                errors.append('未配置推荐平台地址')
        if args.stage == 'broll' and args.voice_backend == 'local':
            for key in ('MING_TTS_PYTHON', 'MING_TTS_MODEL', 'MING_TTS_REF_AUDIO'):
                if not env.get(key) or not Path(env[key]).expanduser().exists():
                    errors.append(f'{key} 路径不可用')
            if not env.get('MING_TTS_REF_TEXT'):
                errors.append('缺少 MING_TTS_REF_TEXT')
        if args.stage == 'digital' and args.video_backend == 'compshare' and not env.get('COMPSHARE_BASE_URL'):
            errors.append('缺少 COMPSHARE_BASE_URL；不自动启动实例')
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--script', required=True)
    p.add_argument('--stage', choices=('plan', 'broll', 'digital', 'merge'), default='plan')
    p.add_argument('--video-backend', choices=('minimax', 'credits', 'compshare'))
    p.add_argument('--voice-backend', choices=('minimax', 'local'))
    p.add_argument('--minimax-route', choices=('official', 'recommended'))
    args = p.parse_args()
    try:
        errors = check(Path(args.root).resolve(), Path(args.script).resolve(), args, generation=args.stage in ('broll', 'digital'))
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print('阻断：' + error)
    print('体检结束：未请求任何 API、未消耗积分、未启动实例；未检查真实生成效果。')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
