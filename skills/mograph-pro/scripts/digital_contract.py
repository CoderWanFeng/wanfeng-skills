#!/usr/bin/env python3
"""数字人混剪契约：纯标准库、零网络，不按文件名猜测出镜类型。"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

SCHEMA = 'mograph-pro/wanfeng-scene-plan@2'
EPS = 0.002  # 引擎时间码保留三位小数
MARKER = re.compile(r'^\[\[(A|B|BROLL)(?::([^\]]*))?\]\]', re.I)


def validate_marked_script(text):
    """每个非空段落显式标记；连续文本行属于同一镜头块。"""
    if not text.strip():
        raise ValueError('标记稿为空')
    active = False
    body = False
    kinds = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            if active and not body:
                raise ValueError('镜头标记后缺台词')
            active = False
            continue
        match = MARKER.match(line)
        if match:
            if active and not body:
                raise ValueError('镜头标记后缺台词')
            kinds.append('a' if match[1].upper() == 'A' else 'b')
            active, body = True, False
            line = line[match.end():].strip()
        elif not active:
            raise ValueError('每段须以 [[A]] 或 [[BROLL:画面提示]] 开始；不要单括号')
        if '[[' in line or ']]' in line or re.search(r'\[(?:A|B|BROLL)(?::[^\]]*)?\]', line, re.I):
            raise ValueError('非法/内嵌镜头标记；每个标记须位于行首')
        body = body or bool(line)
    if not body or not kinds:
        raise ValueError('缺少明确标记或台词')
    return kinds


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label} 必须是有限数值')
    return float(value)


def read_subtitles(path, total):
    content = Path(path).read_text(encoding='utf-8-sig').strip()
    cues = []
    previous = 0.0
    pattern = re.compile(r'^(\d+):(\d{2}):(\d{2})[,.](\d{3})$')
    def seconds(raw):
        match = pattern.fullmatch(raw.strip())
        if not match:
            raise ValueError('SRT 时间码格式错误')
        h, m, s, ms = map(int, match.groups())
        if m >= 60 or s >= 60:
            raise ValueError('SRT 时间码越界')
        return h * 3600 + m * 60 + s + ms / 1000
    for block in re.split(r'\n\s*\n', content):
        lines = block.splitlines()
        if len(lines) < 3 or '-->' not in lines[1]:
            raise ValueError('SRT 条目不完整')
        start, end = map(seconds, lines[1].split('-->'))
        text = ' '.join(lines[2:]).strip()
        if not text or start < previous - EPS or end <= start or end > total + EPS:
            raise ValueError('SRT 顺序、时长或总长不匹配')
        cues.append({'start': start, 'end': end, 'text': text})
        previous = end
    if not cues:
        raise ValueError('缺少有效字幕')
    return cues


def media_path(value, timeline, kind):
    if not isinstance(value, str) or not value:
        raise ValueError(f'缺少 {kind} 路径')
    path = Path(value).expanduser()
    if not path.is_absolute():
        if kind == 'audio' and len(path.parts) == 1:
            path = timeline.parents[2] / 'voice' / timeline.parent.name / path
        else:
            path = timeline.parent / path
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'缺少有效 {kind} 文件：{path}')
    return str(path.resolve())


def load_timeline(path, require_video=True, srt=None):
    timeline = Path(path).resolve()
    payload = json.loads(timeline.read_text(encoding='utf-8'))
    segments = payload.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('完整时间轴必须含非空 segments')
    total = number(payload.get('total_duration'), 'total_duration')
    cursor, seen, result = 0.0, set(), []
    for raw in segments:
        seg = dict(raw)
        index = seg.get('index')
        if type(index) is not int or index < 1 or index in seen:
            raise ValueError('段编号须为不重复的正整数')
        seen.add(index)
        if seg.get('kind') not in ('a', 'b'):
            raise ValueError(f'段 {index} 的 kind 非法')
        start, end, duration = (number(seg.get(k), k) for k in ('start', 'end', 'duration'))
        if start < 0 or duration <= 0 or end <= start or abs(end - start - duration) > EPS:
            raise ValueError(f'段 {index} 时长非法')
        if abs(start - cursor) > EPS:
            raise ValueError(f'段 {index} 有时间轴间隙或重叠')
        seg['audio'] = media_path(seg.get('audio'), timeline, 'audio')
        if seg['kind'] == 'a' and require_video:
            seg['video'] = media_path(seg.get('video'), timeline, 'video')
        elif seg['kind'] == 'b':
            if seg.get('video'):
                raise ValueError(f'B 段 {index} 不允许绑定数字人视频')
            seg['video'] = None
        cursor = end
        result.append(seg)
    if abs(cursor - total) > EPS:
        raise ValueError('时间轴总长不匹配')
    for kind, key in (('a', 'a_roll_duration'), ('b', 'b_roll_duration')):
        if key in payload and abs(sum(s['duration'] for s in result if s['kind'] == kind) - number(payload[key], key)) > EPS * len(result):
            raise ValueError(f'{key} 不匹配')
    cues = read_subtitles(srt or timeline.with_suffix('.srt'), total)
    for seg in result:
        if not any(c['end'] > seg['start'] and c['start'] < seg['end'] for c in cues):
            raise ValueError(f"段 {seg['index']} 缺字幕")
    return {**payload, 'segments': result, 'subtitles': cues, 'timeline_path': str(timeline)}


def scene_plan(timeline, *, script='', aspect='9:16'):
    scenes = []
    for seg in timeline['segments']:
        b = seg['kind'] == 'b'
        scenes.append({
            'id': seg['index'], 'segment_index': seg['index'],
            'start': seg['start'], 'end': seg['end'], 'duration': seg['duration'],
            'roll': seg['kind'], 'presenter': 'none' if b else 'full',
            'mode': 'fs' if b else 'overlay', 'head': False,
            'layout': 'evidence' if b else 'statement',
            'layout_hint': '纯素材或自绘说明画面，无人像' if b else '数字人底片 + 原有动效',
            'audio': seg['audio'], 'video': seg.get('video'), 'text': seg.get('text', ''),
            'cues': [c['text'] for c in timeline['subtitles'] if c['end'] > seg['start'] and c['start'] < seg['end']],
            'visual_hint': seg.get('note', ''), 'layers': [], 'assets': [],
            'visual_status': 'pending' if b else 'presenter-ready',
            'note': 'B 段必须实现全屏 layers 后才可交付' if b else '人物裁切按本片实测',
        })
    return {'$schema': SCHEMA, 'meta': {
        'style_path': 'wanfeng', 'source_mode': 'digital-human', 'renderer_hint': 'pillow-frame',
        'source_script': str(script), 'source_video': '', 'digital_timeline': timeline['timeline_path'],
        'aspect': aspect, 'duration': timeline['total_duration'], 'duration_source': 'digital-timeline',
        'timing_source': 'measured', 'scenes': len(scenes), 'speed': 1.0,
        'generated_by': 'scripts/make_scene_plan.py v1.3.0', 'spec_ref': 'references/digital-human.md',
    }, 'warnings': ['底片中的 B 段背景只是占位，禁止直接作为成片交付'], 'scenes': scenes}


def normalize_plan(plan):
    """只在读取时升级旧 @1；不改变旧脚本的默认输出或时间映射。"""
    result = copy.deepcopy(plan)
    if result.get('$schema') == 'mograph-pro/wanfeng-scene-plan@1':
        result['$schema'] = SCHEMA
        result['meta']['source_mode'] = 'talking-head'
        for scene in result['scenes']:
            scene['roll'] = 'a'
            scene['roll_status'] = 'pending-semantic-review'
            scene['presenter'] = 'circle' if scene.get('head') else 'full'
    if result.get('$schema') != SCHEMA:
        raise ValueError('未知场景契约版本')
    return result


def validate_render_plan(plan, implemented_layers=(), final=False):
    plan = normalize_plan(plan)
    source = plan['meta'].get('source_mode')
    if source not in ('talking-head', 'digital-human'):
        raise ValueError('未知 source_mode')
    digital = source == 'digital-human'
    total = number(plan['meta'].get('duration'), 'duration')
    if total <= 0 or not isinstance(plan.get('scenes'), list) or not plan['scenes']:
        raise ValueError('场景表不能为空，总长须为正数')
    cursor, seen = 0.0, set()
    for scene in plan['scenes']:
        index = scene.get('id')
        if type(index) is not int or index < 1 or index in seen:
            raise ValueError('场景编号须为不重复的正整数')
        seen.add(index)
        start, end, duration = (number(scene.get(k), k) for k in ('start', 'end', 'duration'))
        tolerance = EPS if digital else 0.021  # 旧真人骨架各字段独立保留两位小数
        if start < 0 or end <= start or duration <= 0 or abs(end - start - duration) > tolerance:
            raise ValueError('场景时长非法')
        roll, presenter = scene.get('roll'), scene.get('presenter')
        if roll not in ('a', 'b') or presenter not in ('full', 'circle', 'none'):
            raise ValueError('场景缺少有效 roll / presenter')
        if scene.get('head', False) != (presenter == 'circle'):
            raise ValueError('head 与 presenter 不一致')
        mode = scene.get('mode')
        if mode not in ('overlay', 'fs'):
            raise ValueError('未知场景版式')
        if mode == 'fs' and presenter == 'full':
            raise ValueError('全屏设计需圆形人头；数字人 B 段才可无人头')
        if not digital and presenter == 'none':
            raise ValueError('真人分支必须始终可见人物')
        if final:
            layers, assets = scene.get('layers', []), scene.get('assets', [])
            if not isinstance(layers, list) or any(not isinstance(k, str) or k not in implemented_layers for k in layers):
                raise ValueError('layers 尚未在任务渲染器中实现')
            if not isinstance(assets, list) or any(not isinstance(p, str) or not Path(p).is_file() for p in assets):
                raise ValueError('场景缺少引用素材')
        if digital:
            if abs(start - cursor) > EPS:
                raise ValueError('数字人镜头不得留空档或重叠')
            cursor = scene['end']
            if (roll == 'b') != (presenter == 'none'):
                raise ValueError('数字人 A 段须有人，B 段须无人')
            if roll == 'b':
                if scene.get('mode') != 'fs':
                    raise ValueError('数字人 B 段必须全屏覆盖底片')
                if final:
                    layers = scene.get('layers', [])
                    if scene.get('visual_status') != 'ready' or not layers or not scene.get('full_frame'):
                        raise ValueError('B 段仍是占位或未完成全屏 layers')
    if digital and abs(cursor - total) > EPS:
        raise ValueError('数字人场景总长不匹配')
    return plan
