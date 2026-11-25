#!/usr/bin/env python3
"""按完整 A/B 时间轴本地组装底片与场景计划；B 背景为占位，不能直接交付。"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
from digital_contract import load_timeline, scene_plan


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise ValueError('ffmpeg/ffprobe 失败：' + result.stderr[-1800:])
    return result.stdout


def probe(path, kind):
    data = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    streams = [s for s in data['streams'] if s['codec_type'] == kind]
    if not streams:
        raise ValueError(f'{path} 没有 {kind} 流')
    return float(streams[0].get('duration') or data['format']['duration'])


def assemble(timeline_path, out, plan_out, width=1080, height=1920, fps=30):
    if min(width, height, fps) <= 0 or width % 2 or height % 2:
        raise ValueError('尺寸须为正偶数，fps 须为正整数')
    out, plan_out = Path(out).resolve(), Path(plan_out).resolve()
    if out == plan_out or out.exists() or plan_out.exists():
        raise ValueError('输出已存在或同名，请另存；不覆盖已有产物')
    timeline = load_timeline(timeline_path)
    # 先探测全部输入，不允许缺片后静默生成/补齐。
    for seg in timeline['segments']:
        audio_duration = probe(seg['audio'], 'audio')
        if abs(audio_duration - seg['duration']) > 0.12:
            raise ValueError(f"段 {seg['index']} 音频实测时长与时间轴不符")
        if seg['kind'] == 'a' and probe(seg['video'], 'video') < seg['duration'] - 0.08:
            raise ValueError(f"段 {seg['index']} 视频不足；不能拉伸改变口型")
    out.parent.mkdir(parents=True, exist_ok=True)
    plan_out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='digital-base-', dir=out.parent) as work:
        work = Path(work)
        video_list, audio_list = [], []
        previous_frame = 0
        previous_sample = 0
        for position, seg in enumerate(timeline['segments']):
            end_frame = round(seg['end'] * fps)
            frames = end_frame - previous_frame
            end_sample = round(seg['end'] * 48000)
            samples = end_sample - previous_sample
            if frames <= 0 or samples <= 0:
                raise ValueError('段时长小于输出帧分辨率')
            previous_frame, previous_sample = end_frame, end_sample
            video = work / f'v{position:05d}.mp4'
            audio = work / f'a{position:05d}.wav'
            cmd = ['ffmpeg', '-v', 'error', '-nostdin']
            if seg['kind'] == 'a':
                cmd += ['-i', seg['video']]
                vf = (f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
                      f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x0A0E13,'
                      f'setsar=1,fps={fps},tpad=stop_mode=clone:stop_duration=0.12')
            else:
                cmd += ['-f', 'lavfi', '-i', f'color=c=0x0A0E13:s={width}x{height}:r={fps}']
                vf = 'setsar=1'
            run(cmd + ['-map', '0:v:0', '-vf', vf, '-frames:v', str(frames), '-an',
                       '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', str(video)])
            run(['ffmpeg', '-v', 'error', '-nostdin', '-i', seg['audio'], '-map', '0:a:0',
                 '-af', f'aresample=48000,apad,atrim=end_sample={samples},asetpts=PTS-STARTPTS',
                 '-ac', '2', '-c:a', 'pcm_s16le', str(audio)])
            video_list.append(f"file '{video.name}'")
            audio_list.append(f"file '{audio.name}'")
        (work / 'video.txt').write_text('\n'.join(video_list) + '\n')
        (work / 'audio.txt').write_text('\n'.join(audio_list) + '\n')
        result = work / 'base.mp4'
        run(['ffmpeg', '-v', 'error', '-nostdin', '-f', 'concat', '-safe', '1', '-i', str(work / 'video.txt'),
             '-f', 'concat', '-safe', '1', '-i', str(work / 'audio.txt'), '-map', '0:v:0', '-map', '1:a:0',
             '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(result)])
        if abs(probe(result, 'video') - timeline['total_duration']) > 1 / fps + 0.003:
            raise ValueError('底片视频总时长校验失败')
        if abs(probe(result, 'audio') - timeline['total_duration']) > 0.05:
            raise ValueError('底片音轨总时长校验失败')
        run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(result), '-f', 'null', '-'])
        plan = scene_plan(timeline, script=timeline.get('script', ''), aspect='9:16' if height >= width else '16:9')
        plan['meta'].update(source_video=str(out), base_only=True, fps=fps, width=width, height=height)
        result.replace(out)
        plan_out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'完整底片：{out}；场景计划：{plan_out}；B 段待设计，禁止直接交付。')
    return plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--digital-timeline', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--plan-out', required=True)
    p.add_argument('--width', type=int, default=1080)
    p.add_argument('--height', type=int, default=1920)
    p.add_argument('--fps', type=int, default=30)
    args = p.parse_args()
    try:
        assemble(args.digital_timeline, args.out, args.plan_out, args.width, args.height, args.fps)
    except (ValueError, OSError, KeyError) as exc:
        print('阻断：' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
