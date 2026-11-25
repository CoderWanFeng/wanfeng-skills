#!/usr/bin/env python3
"""mograph-pro 安全编排：显式阶段/job；授权、试听、样段关卡，不透传 all/yes/no-resume。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

sys.dont_write_bytecode = True
from digital_contract import EPS, load_timeline, number
from assemble_digital_base import probe
from preflight_digital import check, configuration
from init_digital_workspace import safe_target, SKILL_ROOT


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(args, env):
    fields = {k: getattr(args, k) for k in (
        'video_backend', 'voice_backend', 'minimax_route', 'voice', 'voice_model',
        'video_model', 'resolution', 'ratio', 'scene', 'emotion', 'segment_seconds')}
    fields['script'] = digest(Path(args.script).read_bytes())
    fields['persona'] = digest(Path(args.persona).read_bytes()) if args.persona else ''
    fields['config'] = {k: v for k, v in env.items() if k.startswith(('MING_', 'COMPSHARE_', 'MINIMAX_', 'DH_')) and k != 'DH_WORK_ROOT'}
    ref = env.get('MING_TTS_REF_AUDIO')
    if ref and Path(ref).is_file():
        fields['reference'] = digest(Path(ref).read_bytes())
    return digest(json.dumps(fields, sort_keys=True).encode())


def engine_command(args, root, dry=False):
    command = [sys.executable, '-B', str(root / 'scripts/build.py'), '--stage', args.stage,
               '--job', args.job, '--script', args.script, '--transition', '0']
    for key in ('persona', 'voice', 'voice_backend', 'video_backend', 'minimax_route',
                'voice_model', 'video_model', 'resolution', 'ratio', 'scene', 'emotion',
                'segment_seconds', 'limit_segments'):
        value = getattr(args, key)
        if value is not None and value != '':
            command += ['--' + key.replace('_', '-'), str(value)]
    if dry:
        command.append('--dry-run')
    return command


def run_engine(args, root, dry=False):
    env = {**os.environ, 'DH_WORK_ROOT': str(root), 'PYTHONDONTWRITEBYTECODE': '1'}
    return subprocess.run(engine_command(args, root, dry), cwd=root, env=env, stdin=subprocess.DEVNULL).returncode


def valid_video(path, minimum=0):
    if not path.is_file():
        return False
    result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                             '-show_entries', 'stream=duration', '-of', 'json', str(path)],
                            capture_output=True, text=True)
    try:
        duration = float(json.loads(result.stdout)['streams'][0]['duration'])
        if result.returncode or not duration > 0 or duration < minimum - 0.08:
            return False
        return subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-nostdin', '-i', str(path),
                               '-map', '0:v:0', '-f', 'null', '-'], capture_output=True).returncode == 0
    except (ValueError, KeyError, IndexError):
        return False


def expected_videos(timeline, root, args):
    folder = root / 'output/final/talking' / args.job
    suffix = '_h3' if args.video_backend == 'compshare' else ''
    # 类型来自完整时间轴，文件名仅用于定位已经确认的 A 段产物。
    return [folder / f"seg_{seg['index']:03d}{suffix}.mp4"
            for seg in timeline['segments'] if seg['kind'] == 'a']


def storyboard_identity(board):
    keys = ('index', 'kind', 'text', 'shot', 'emotion', 'scene', 'note')
    return digest(json.dumps([{k: s.get(k) for k in keys} for s in board['segments']], sort_keys=True).encode())


def check_measured(timeline, board, root, job, state):
    """生成端读分镜，剪辑端读完整时间轴；二者必须指向同一段声音。"""
    shots = board['segments']
    if len(shots) != len(timeline['segments']):
        raise ValueError('实测分镜与完整时间轴段数不同')
    for shot, seg in zip(shots, timeline['segments']):
        if any(shot.get(k) != seg.get(k) for k in ('index', 'kind', 'text', 'shot', 'emotion', 'scene', 'note')):
            raise ValueError('实测分镜与完整时间轴内容或 A/B 类型不一致')
        if any(abs(number(shot.get(k), k) - seg[k]) > EPS for k in ('start', 'end', 'duration')):
            raise ValueError('实测分镜与完整时间轴时间不一致')
        audio = root / 'output/final/voice' / job / shot.get('audio', '')
        if audio.resolve() != Path(seg['audio']).resolve():
            raise ValueError('实测分镜与完整时间轴音频路径不一致')
        actual = number(probe(seg['audio'], 'audio'), '音频实测时长')
        if actual <= 0 or abs(actual - seg['duration']) > 0.12:
            raise ValueError('音频实测时长与时间轴不符；先修正实测分镜和字幕，禁止先生成画面')
    stable = [{k: v for k, v in s.items() if k != 'video'} for s in timeline['segments']]
    measured = digest(json.dumps({
        'segments': stable, 'subtitles': timeline['subtitles'],
        'audio_hashes': [digest(Path(s['audio']).read_bytes()) for s in timeline['segments']],
    }, sort_keys=True).encode())
    if state.get('measured') and state['measured'] != measured:
        raise ValueError('已确认的配音、字幕或时间轴被改动；请恢复原文件或新建 job')
    state['measured'] = measured


@contextmanager
def job_lock(path):
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('同一 job 正在运行，或上次中断留下锁；确认无进程后人工移走 .lock')
    try:
        os.close(fd)
        yield
    finally:
        path.unlink()


def execute(args):
    root = Path(args.root).expanduser().absolute()
    safe_target(root)
    root = root.resolve()
    if root == SKILL_ROOT or SKILL_ROOT in root.parents:
        raise ValueError('不得在 Skill 安装目录运行引擎')
    for folder in ('plan', 'voice', 'talking'):
        output = root / 'output/final' / folder / args.job
        safe_target(output)
        for path in output.rglob('*'):
            if path.is_symlink():
                raise ValueError('任务产物目录含符号链接，禁止通过引擎写出工作区')
    args.script = str(Path(args.script).resolve())
    env = configuration(root, args)
    if args.persona:
        args.persona = str(Path(args.persona).resolve())
    else:
        candidates = sorted(p for p in (root / 'input/persona').glob('*') if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.mov', '.mp4', '.m4v'))
        args.persona = str(candidates[0]) if candidates else None
    args.segment_seconds = args.segment_seconds or (10.0 if args.video_backend == 'credits' else 13.0)
    if not 0 < args.segment_seconds <= 15 or args.limit_segments is not None and args.limit_segments < 1:
        raise ValueError('分段时长必须在 (0,15]，样段数量必须为正数')
    errors = check(root, Path(args.script), args, generation=False)
    if errors:
        raise ValueError('；'.join(errors))
    if args.dry_run:
        return run_engine(args, root, dry=True)

    state_path = root / 'config' / f'mograph-{args.job}.json'
    safe_target(state_path)
    safe_target(state_path.with_suffix('.lock'))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with job_lock(state_path.with_suffix('.lock')):
        identity = fingerprint(args, env)
        if not state_path.exists() and any(any((root / 'output/final' / folder / args.job).glob('*')) for folder in ('plan', 'voice', 'talking')):
            raise ValueError('此 job 已有来源不明的产物；请新建 job，不自动认领旧文件')
        state = json.loads(state_path.read_text()) if state_path.exists() else {'fingerprint': identity}
        if state['fingerprint'] != identity:
            raise ValueError('稿件、音色、形象或后端配置已改变：请新建 job，不复用旧产物')
        talking = root / 'output/final/talking' / args.job
        timeline_path = talking / 'a_roll.json'
        def save():
            temp = state_path.with_suffix('.tmp')
            safe_target(temp)
            temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
            temp.replace(state_path)
        timeline = None
        board_path = root / 'output/final/plan' / args.job / 'storyboard.json'
        if args.stage != 'plan' and not state.get('plan'):
            raise ValueError('先用同一 job 执行 plan')
        if args.stage != 'plan':
            board = json.loads(board_path.read_text())
            if storyboard_identity(board) != state.get('storyboard'):
                raise ValueError('分镜的台词或 A/B 分类已改变；需改标记稿并新建 job')
        if args.stage == 'plan' and state.get('broll'):
            print('已完成配音，保留实测分镜，不重新写估算时间；改稿请新建 job。')
            return 0
        if args.stage == 'broll':
            if timeline_path.exists():
                timeline = load_timeline(timeline_path, require_video=False)
                check_measured(timeline, board, root, args.job, state)
                state['broll'] = True
                save()
                print('复用已有完整配音与时间码，未调用 TTS。')
                return 0
            voice_dir = root / 'output/final/voice' / args.job
            if any(voice_dir.glob('*')):
                raise ValueError('检测到中断配音，阻止整批重跑收费；保留现有音频，先人工恢复时间码')
            if not args.approve_plan:
                raise ValueError('需用户确认预分镜后传 --approve-plan')
        if args.stage in ('digital', 'merge'):
            if not state.get('broll'):
                raise ValueError('先完成 broll 配音和完整时间轴')
            timeline = load_timeline(timeline_path, require_video=False)
            check_measured(timeline, board, root, args.job, state)
            videos = expected_videos(timeline, root, args)
            durations = {p: s['duration'] for p, s in zip(videos, (s for s in timeline['segments'] if s['kind'] == 'a'))}
            def ready(path):
                return valid_video(path, durations[path])
            if args.stage == 'digital':
                if not args.approve_audio:
                    raise ValueError('需用户试听确认后传 --approve-audio')
                if not videos:
                    state['digital'] = True
                    save()
                    print('全部为 B 段，不调用任何数字人后端。')
                    return 0
                if not state.get('sample'):
                    if args.limit_segments not in (None, 1):
                        raise ValueError('首次只允许第一段样段，--limit-segments 1')
                    args.limit_segments = 1
                elif args.limit_segments != 1 and (not args.approve_sample or not ready(videos[0])):
                    raise ValueError('先确认实际第一段样段，再传 --approve-sample 补齐')
                selected = videos[:args.limit_segments] if args.limit_segments else videos
                if all(ready(p) for p in selected):
                    state.update(sample=True, digital=all(ready(p) for p in videos), status='ready')
                    save()
                    print('复用已完成且可解码的出镜片段，未调用后端或上传。')
                    return 0
                for path in selected:
                    if path.exists() and not ready(path):
                        raise ValueError('已有出镜片段损坏或时长不足；保留文件，先人工检查再继续')
                    if args.video_backend == 'minimax' and path.exists() and not (talking / 'raw' / path.name).is_file():
                        raise ValueError('MiniMax 续跑缺少已完成片段的 raw 缓存；先恢复缓存，避免重复计费')
            elif videos and not all(ready(p) for p in videos):
                print('等待 A 段素材，merge 未执行。')
                return 3
        if args.stage in ('broll', 'digital'):
            if args.approve_stage != args.stage:
                raise ValueError('未授权本阶段生成/费用：需用户同意后传 --approve-stage ' + args.stage)
            upload = args.stage == 'broll' and args.voice_backend == 'minimax' or args.stage == 'digital' and args.video_backend != 'credits'
            if upload and not args.approve_upload:
                raise ValueError('文稿/人像/语音将上传选定服务，需 --approve-upload')
            errors = check(root, Path(args.script), args, generation=True)
            if errors:
                raise ValueError('；'.join(errors))
            print('本阶段授权已提供；首次音色克隆不由本入口自动执行。')
            print('费用口径：MiniMax 按调用计费；积分画面不调用云视频；自托管按实例时长；本地 Ming 消耗本机算力。')
            if args.video_backend == 'credits' and args.voice_backend == 'minimax':
                print('注意：积分只覆盖画面，MiniMax 配音另计费。')
        save()  # 失败/中断也固定输入指纹，避免换稿复用收费产物
        rc = run_engine(args, root)
        if rc:
            return rc
        if args.stage == 'plan':
            if not board_path.is_file():
                raise ValueError('引擎未产出分镜表')
            state['storyboard'] = storyboard_identity(json.loads(board_path.read_text()))
            state['plan'] = True
        elif args.stage == 'broll':
            timeline = load_timeline(timeline_path, require_video=False)
            measured_board = json.loads(board_path.read_text())
            if storyboard_identity(measured_board) != state['storyboard']:
                raise ValueError('配音后分镜与预分镜内容不同')
            check_measured(timeline, measured_board, root, args.job, state)
            state['broll'] = True
        elif args.stage == 'digital':
            selected = videos[:args.limit_segments] if args.limit_segments else videos
            if not all(ready(p) for p in selected):
                state['status'] = 'waiting-media'
                save()
                print('等待有效画面：引擎退出 0 不等于素材齐全；未自动补生成。')
                return 3
            state['sample'] = True
            state['digital'] = all(ready(p) for p in videos)
        elif args.stage == 'merge':
            check_measured(load_timeline(timeline_path), board, root, args.job, state)
            state['merge'] = True
        state['status'] = 'ready'
        save()
        print('阶段完成；talking.mp4 不是混剪底片，请用 assemble_digital_base.py。')
        return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--root', required=True)
    p.add_argument('--script', required=True)
    p.add_argument('--stage', required=True, choices=('plan', 'broll', 'digital', 'merge'))
    p.add_argument('--job', required=True)
    p.add_argument('--persona')
    p.add_argument('--voice')
    p.add_argument('--voice-backend', choices=('minimax', 'local'))
    p.add_argument('--video-backend', choices=('minimax', 'credits', 'compshare'))
    p.add_argument('--minimax-route', choices=('official', 'recommended'))
    p.add_argument('--voice-model', default='speech-2.8-hd')
    p.add_argument('--video-model')
    p.add_argument('--resolution', default='768P')
    p.add_argument('--ratio', default='auto', choices=('auto', '9:16', '16:9'))
    p.add_argument('--scene', default='')
    p.add_argument('--emotion')
    p.add_argument('--segment-seconds', type=float)
    p.add_argument('--limit-segments', type=int)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--approve-stage', choices=('broll', 'digital'))
    for gate in ('plan', 'audio', 'sample', 'upload'):
        p.add_argument('--approve-' + gate, action='store_true')
    args = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', args.job):
        p.error('job 仅允许字母、数字、下划线和连字符，最长 80 位')
    try:
        return execute(args)
    except (OSError, ValueError, KeyError) as exc:
        print('阻断：' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
