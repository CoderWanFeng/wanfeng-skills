#!/usr/bin/env python3
"""Local, source-led renderer for mograph-vlog.plan/v1; no creative inference."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFont, ImageOps

SCHEMA = 'mograph-vlog.plan/v1'
EFFECTS = {'typewriter', 'stamp', 'arrow', 'progress', 'frame', 'underline', 'pop', 'slide', 'highlight',
           'counter', 'bar', 'hud', 'lens', 'scanline', 'line_boil', 'crosshatch', 'pixel', 'isometric'}
TEXT_EFFECTS = {'typewriter', 'stamp', 'underline', 'pop', 'slide', 'highlight', 'counter', 'line_boil', 'crosshatch', 'pixel', 'isometric'}
TRANSITIONS = {'cut', 'fade', 'wipeleft', 'slideleft', 'smoothup', 'circleopen'}


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_quint(t):
    return 1 - (1 - t) ** 5


def ease_out_back(t, s=1.70158):
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def boil(seed):
    """Deterministic per-frame jitter in [-1, 1] for hand-drawn "line boil".

    Python salts str hashing per process, so integer mixing is used instead —
    the same frame index must always draw the same wobble (same code, same frame, same result).
    """
    x = (int(seed) * 2654435761 + 1013904223) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 2246822519) & 0xFFFFFFFF
    x ^= x >> 13
    return (x % 2001 - 1000) / 1000


def frame_index(t, c):
    return int(round(t * c['fps']))
FF = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error']
LOCAL = ['-protocol_whitelist', 'file,pipe']


def check(ok, message):
    if not ok:
        raise ValueError(message)


def fields(value, allowed, required=()):
    check(isinstance(value, dict), 'Expected a JSON object')
    check(not (set(value) - set(allowed.split())), f'Unknown fields: {set(value) - set(allowed.split())}')
    check(set(required) <= set(value), f'Missing fields: {set(required) - set(value)}')


def number(value, name, low=0, high=21600):
    check(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
          f'{name} must be finite in [{low}, {high}]')
    return value


def local_path(value, root=None, directory=False, exists=True):
    check(isinstance(value, str) and Path(value).is_absolute(), 'Paths must be absolute')
    path = Path(value)
    check(not any(p.is_symlink() for p in (path, *path.parents)), f'Symlinks forbidden: {path}')
    path = path.resolve()
    check(root is None or path.is_relative_to(root), f'Path outside source_root: {path}')
    if exists:
        check(path.is_dir() if directory else path.is_file(), f'Path missing or wrong kind: {path}')
    return path


def run(args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    check(result.returncode == 0, result.stderr.decode(errors='replace')[-1800:] or 'Media command failed')
    return result.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', *LOCAL, '-show_streams', '-show_format',
                           '-of', 'json', str(path)]))


def media(path, audio_only=False):
    if not audio_only:
        try:
            with Image.open(path) as image:
                check(not getattr(image, 'is_animated', False), 'Animated images need an explicit video copy')
                check(image.width * image.height <= 100_000_000, 'Image too large')
                image.verify()
            return {'kind': 'image', 'audio': None}
        except (OSError, SyntaxError):
            pass
    info = probe(path)
    check(not any(s.get('color_transfer') in ('smpte2084', 'arib-std-b67') for s in info['streams']),
          f'HDR source rejected; provide an explicit SDR copy: {path}')
    streams = [s for s in info['streams'] if s.get('codec_type') == ('audio' if audio_only else 'video')
               and not s.get('disposition', {}).get('attached_pic')]
    check(bool(streams), f'No {"audio" if audio_only else "video"} stream: {path}')
    stream = streams[0]
    duration = stream.get('duration') or stream.get('tags', {}).get('DURATION') or info['format'].get('duration')
    if isinstance(duration, str) and ':' in duration:
        parts = [float(v) for v in duration.split(':')]
        duration = parts[0] * 3600 + parts[1] * 60 + parts[2]
    duration = number(float(duration or 0), f'Media duration: {path}', 0.000001, 1e9)
    return {'kind': 'audio' if audio_only else 'video', 'duration': duration, 'video': stream['index'],
            'audio': next((s['index'] for s in info['streams'] if s.get('codec_type') == 'audio'), None)}


def validate(plan, out=None, preview_seconds=None):
    fields(plan, 'schema source_root canvas scenes soundtrack', ('schema', 'source_root', 'canvas', 'scenes'))
    check(plan['schema'] == SCHEMA, f'Expected schema {SCHEMA}')
    p = copy.deepcopy(plan)
    root = local_path(p['source_root'], directory=True)
    c = p['canvas']
    fields(c, 'width height fps background font_path font_index', ('width', 'height', 'fps', 'background', 'font_path'))
    for key in ('width', 'height'):
        check(type(c[key]) is int and 2 <= c[key] <= 4096 and c[key] % 2 == 0, f'{key} must be even, 2..4096')
    check(type(c['fps']) is int and c['fps'] in (24, 25, 30, 60), 'fps must be 24/25/30/60')
    color(c['background'])
    c['font_path'] = str(local_path(c['font_path']))
    check(type(c.get('font_index', 0)) is int and 0 <= c.get('font_index', 0) <= 255, 'Invalid font_index')
    ImageFont.truetype(c['font_path'], 12, index=c.get('font_index', 0))
    scenes = p['scenes']
    check(isinstance(scenes, list) and 0 < len(scenes) <= 1000, 'scenes must contain 1..1000 scenes')
    ids, total, fps = set(), 0, c['fps']
    for i, s in enumerate(scenes):
        fields(s, 'id source source_in duration fit motion source_audio transition_in effects', ('id', 'source', 'duration', 'fit'))
        check(isinstance(s['id'], str) and 0 < len(s['id']) <= 128 and s['id'] not in ids, 'Scene ids must be nonempty and unique')
        ids.add(s['id'])
        s['source'] = str(local_path(s['source'], root))
        s['source_in'] = number(s.get('source_in', 0), 'source_in', 0, 1e9)
        number(s['duration'], 'scene duration', 1 / fps, 3600)
        check(s['fit'] in ('contain', 'cover') and s.get('motion', 'none') in ('none', 'push-in'), 'Unknown fit or motion')
        check(type(s.get('source_audio', True)) is bool, 'source_audio must be bool')
        tr = s.setdefault('transition_in', {'type': 'cut', 'duration': 0})
        fields(tr, 'type duration', ('type', 'duration'))
        check(tr['type'] in TRANSITIONS, 'Unknown transition')
        number(tr['duration'], 'transition duration', 0, 1800)
        check((tr['type'] == 'cut' and tr['duration'] == 0) or
              (tr['type'] != 'cut' and tr['duration'] >= 1 / fps), 'cut requires 0; other transitions require >= one frame')
        check((i > 0 or tr['duration'] == 0) and (i == 0 or
              tr['duration'] <= min(s['duration'], scenes[i - 1]['duration']) / 2), 'Transition exceeds half an adjacent scene')
        effects = s.setdefault('effects', [])
        check(isinstance(effects, list) and len(effects) <= 100, 'Invalid effects list')
        for e in effects:
            fields(e, 'type text start duration x y size_px color fill', ('type', 'duration', 'x', 'y', 'color'))
            check(e['type'] in EFFECTS, 'Unknown effect')
            e['start'] = number(e.get('start', 0), 'effect start', 0, s['duration'])
            number(e['duration'], 'effect duration', 2 / fps, s['duration'])
            check(e['start'] + e['duration'] <= s['duration'] + 1e-9, 'Effect extends beyond scene')
            for key in ('x', 'y'):
                number(e[key], key, 0, 1)
            number(e.get('size_px', 32), 'size_px', 2, 4096)
            if 'fill' in e:
                number(e['fill'], 'fill', 0, 1)
            color(e['color'])
            check(isinstance(e.get('text', ''), str) and len(e.get('text', '')) <= 10000, 'Invalid effect text')
            check(e['type'] != 'typewriter' or bool(e.get('text')), 'typewriter needs text')
            check(e['type'] not in TEXT_EFFECTS or bool(e.get('text')), f'{e["type"]} needs text')
            effect_layout(e, c)  # Fail on unrenderable text before opening output.
        s['_media'] = media(s['source'])
        check((s['_media']['kind'] != 'image' or s['source_in'] == 0), 'Images require source_in=0')
        if s['_media']['kind'] == 'video':
            check(s['source_in'] + s['duration'] <= s['_media']['duration'] + 1e-7,
                  f'Scene {s["id"]} exceeds real video duration; no looping or dialogue truncation')
        s['_start'] = total - tr['duration']
        total = s['_start'] + s['duration']
    number(total, 'total duration', 1 / fps, 21600)
    sound = p.setdefault('soundtrack', {})
    fields(sound, 'narration music narration_volume music_volume source_volume')
    for key, default in (('narration_volume', 1), ('music_volume', .15), ('source_volume', .3)):
        sound[key] = number(sound.get(key, default), key, 0, 4)
    for key in ('narration', 'music'):
        if key in sound:
            sound[key] = str(local_path(sound[key], root))
            m = media(sound[key], audio_only=True)
            check(key != 'narration' or m['duration'] <= total + 1 / fps, 'Narration exceeds timeline; extend the plan instead of truncating speech')
    p['_duration'] = total
    if preview_seconds is not None:
        number(preview_seconds, 'preview_seconds', 1 / fps, 21600)
    if out is not None:
        output = local_path(str(Path(out).absolute()), exists=False)
        check(output.suffix.lower() == '.mp4' and output.parent.is_dir(), 'out needs an existing parent and .mp4 suffix')
        check(not output.exists() and not output.with_suffix('.report.json').exists(), 'Output or report already exists; refusing overwrite')
    return p


def timeline(plan, preview_seconds=None):
    """Quantize cumulative endpoints, not individual durations; never include later scenes."""
    fps = plan['canvas']['fps']
    end = round(plan['_duration'] * fps) if preview_seconds is None else math.floor(min(plan['_duration'], preview_seconds) * fps + 1e-8)
    check(end > 0, 'Timeline has no frames')
    selected = []
    for scene in plan['scenes']:
        start = round(scene['_start'] * fps)
        if start >= end:
            break
        full_end = round((scene['_start'] + scene['duration']) * fps)
        overlap = selected[-1]['full_end'] - start if selected else 0
        selected.append({'scene': scene, 'start': start, 'full_end': full_end,
                         'frames': min(full_end, end) - start, 'overlap': overlap})
    return selected, end / fps


def color(value):
    check(isinstance(value, str) and re.fullmatch(r'#(?:[a-fA-F0-9]{3}|[a-fA-F0-9]{6}|[a-fA-F0-9]{8})', value), 'Colors must be #hex')
    return ImageColor.getrgb(value)


def stroke_args(size):
    """Text needs an outline so it stays readable over bright footage."""
    return {'stroke_width': max(2, size // 16), 'stroke_fill': (0, 0, 0, 175)}


def effect_layout(e, c):
    w, h = c['width'], c['height']
    size = int(e.get('size_px', max(2, min(w, h) * .07)))
    text, font = e.get('text', ''), None
    if e['type'] in TEXT_EFFECTS:
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        for size in range(size, 1, -1):
            font = ImageFont.truetype(c['font_path'], size, index=c.get('font_index', 0))
            box = draw.multiline_textbbox((0, 0), text, font=font, spacing=2)
            bw, bh = max(1, box[2] - box[0]), max(size, box[3] - box[1])
            if bw + 12 <= w / 1.12 and bh + 12 <= h / 1.12:
                break
        else:
            raise ValueError('Text cannot fit canvas, even at 2px; shorten it or enlarge canvas')
        bw, bh = math.ceil((bw + 12) * 1.12), math.ceil((bh + 12) * 1.12)
    elif e['type'] == 'progress':
        bw, bh = min(w, size * 5), min(h, max(4, size // 6))
    elif e['type'] == 'hud':
        bw, bh = min(w, size * 5), min(h, size * 3)
    elif e['type'] == 'bar':
        bw, bh = min(w, size * 2), min(h, size * 5)
    elif e['type'] == 'scanline':
        bw, bh = min(w, size * 6), min(h, size * 3)
    elif e['type'] == 'lens':
        bw = bh = min(w, h, size * 2)
    else:
        bw, bh = min(w, size * (5 if e['type'] == 'frame' else 4)), min(h, size * (3 if e['type'] == 'frame' else 1))
    return min(round(e['x'] * w), w - bw), min(round(e['y'] * h), h - bh), bw, bh, size, font


def animate(image, scene, c, t):
    if scene.get('motion', 'none') == 'push-in':
        zoom = 1 + .06 * min(1, t / scene['duration'])
        image = ImageOps.fit(image.resize((math.ceil(image.width * zoom), math.ceil(image.height * zoom))), image.size)
    layer = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(layer)
    for e in scene['effects']:
        if not e['start'] <= t < e['start'] + e['duration']:
            continue
        q = min(1, (t - e['start']) / min(.8, e['duration'] * .65))
        x, y, w, h, size, font = effect_layout(e, c)
        ink, line = color(e['color']), max(1, size // 10)
        if e['type'] == 'typewriter':
            text = e.get('text', '')
            text = text[:int(len(text) * q)]
            box = draw.multiline_textbbox((0, 0), text, font=font, spacing=2)
            draw.multiline_text((x + 6 - box[0], y + 6 - box[1]), text, font=font, fill=ink, spacing=2, **stroke_args(size))
        elif e['type'] == 'stamp':
            text = e.get('text', '')
            sticker = Image.new('RGBA', (w, h))
            sd = ImageDraw.Draw(sticker)
            sd.rounded_rectangle((3, 3, w - 4, h - 4), radius=max(1, size // 4), outline=ink, width=line)
            box = sd.multiline_textbbox((0, 0), text, font=font, spacing=2)
            sd.multiline_text((6 - box[0], 6 - box[1]), text, font=font, fill=ink, spacing=2)
            scale = max(.01, 1 + 2.70158 * (q - 1) ** 3 + 1.70158 * (q - 1) ** 2)
            sticker = sticker.resize((max(1, round(w * scale / 1.12)), max(1, round(h * scale / 1.12))), Image.Resampling.LANCZOS)
            layer.alpha_composite(sticker, (x + (w - sticker.width) // 2, y + (h - sticker.height) // 2))
        elif e['type'] == 'underline':
            text = e.get('text', '')
            box = draw.multiline_textbbox((0, 0), text, font=font, spacing=2)
            draw.multiline_text((x + 6 - box[0], y + 6 - box[1]), text, font=font, fill=ink, spacing=2, **stroke_args(size))
            ux = x + 6 + min(0, box[0])
            uy = y + 6 + (box[3] - box[1]) + max(2, size // 7)
            draw.rounded_rectangle((ux, uy, ux + max(0, (box[2] - box[0]) * q), uy + max(2, size // 9)),
                                   radius=max(1, size // 18), fill=ink)
        elif e['type'] == 'highlight':
            text = e.get('text', '')
            box = draw.multiline_textbbox((0, 0), text, font=font, spacing=2)
            draw.rounded_rectangle((x, y, x + max(0, (box[2] - box[0]) * q), y + h - 1),
                                   radius=max(1, size // 5), fill=tuple(ink[:3]) + (110,))
            draw.multiline_text((x + 6 - box[0], y + 6 - box[1]), text, font=font, fill=ink, spacing=2, **stroke_args(size))
        elif e['type'] == 'pop':
            text = e.get('text', '')
            pop = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            pd = ImageDraw.Draw(pop)
            box = pd.multiline_textbbox((0, 0), text, font=font, spacing=2)
            pd.multiline_text((6 - box[0], 6 - box[1]), text, font=font, fill=ink, spacing=2, **stroke_args(size))
            scale = max(.01, 1 + 2.70158 * (q - 1) ** 3 + 1.70158 * (q - 1) ** 2)
            pop = pop.resize((max(1, round(w * scale / 1.12)), max(1, round(h * scale / 1.12))), Image.Resampling.LANCZOS)
            layer.alpha_composite(pop, (x + (w - pop.width) // 2, y + (h - pop.height) // 2))
        elif e['type'] == 'slide':
            text = e.get('text', '')
            box = draw.multiline_textbbox((0, 0), text, font=font, spacing=2)
            shift = (1 - min(1, q / .7)) * (image.width * .5 if e['x'] < .5 else -image.width * .5)
            draw.multiline_text((x + 6 - box[0] + shift, y + 6 - box[1]), text, font=font, fill=ink, spacing=2, **stroke_args(size))
        elif e['type'] == 'counter':
            text = e.get('text', '')
            parts = []
            for part in re.split(r'(\d+)', text):
                if part.isdigit():
                    target = int(part)
                    start = max(0, target - 40) if target > 40 else 0
                    value = start + (target - start) * ease_out_quint(q)
                    parts.append(str(int(round(value))).zfill(len(part)))
                else:
                    parts.append(part)
            box = draw.multiline_textbbox((0, 0), ''.join(parts), font=font, spacing=2)
            draw.multiline_text((x + 6 - box[0], y + 6 - box[1]), ''.join(parts), font=font, fill=ink, spacing=2,
                                **stroke_args(size))
        elif e['type'] == 'bar':
            draw.rectangle((x, y, x + w - 1, y + h - 1), outline=ink, width=line)
            grown = h * ease_out_cubic(q) * e.get('fill', 1)
            if grown > 0:
                draw.rectangle((x, y + h - grown, x + w - 1, y + h - 1), fill=ink)
        elif e['type'] == 'hud':
            arm = min(w, h) * .3 * ease_out_cubic(min(1, q * 1.2))
            thick = max(2, size // 10)
            for cx, cy, dx, dy in ((x, y, 1, 1), (x + w - 1, y, -1, 1), (x, y + h - 1, 1, -1), (x + w - 1, y + h - 1, -1, -1)):
                draw.line((cx, cy, cx + dx * arm, cy), fill=ink, width=thick)
                draw.line((cx, cy, cx, cy + dy * arm), fill=ink, width=thick)
            if q > .6:
                gap = max(2, size // 12)
                draw.rectangle((x + w // 2 - gap, y + h // 2 - gap, x + w // 2 + gap, y + h // 2 + gap), outline=ink, width=max(1, thick // 2))
        elif e['type'] == 'scanline':
            step = max(4, size // 8)
            for yy in range(int(y), int(y + h), step):
                draw.line((x, yy, x + w - 1, yy), fill=tuple(ink[:3]) + (70,), width=1)
            band_y = y + ease_out_cubic(q) * (h + size) - size
            draw.rectangle((x, band_y, x + w - 1, band_y + max(2, size // 6)), fill=tuple(ink[:3]) + (55,))
        elif e['type'] == 'lens':
            radius = max(4, w // 2)
            cx = min(max(x + radius, radius), max(radius, image.width - radius))
            cy = min(max(y + radius, radius), max(radius, image.height - radius))
            zoom = 1.2 + 1.0 * ease_out_cubic(min(1, t / max(.001, scene['duration'])))
            src = max(8, radius / zoom)
            region = image.crop((int(cx - src), int(cy - src), int(cx + src), int(cy + src)))
            region = region.resize((radius * 2, radius * 2), Image.Resampling.LANCZOS)
            mask = Image.new('L', (radius * 2, radius * 2), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, radius * 2 - 1, radius * 2 - 1), fill=255)
            layer.paste(region, (int(cx - radius), int(cy - radius)), mask)
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=ink, width=line)
        elif e['type'] == 'line_boil':
            # MG Styles 15 · 01 Line Boil / Anidoodle 手绘：字一个一个落，落下的每一帧都重新抖一遍，
            # 边缘像逐帧手绘那样"沸腾"，而不是贴一张静止的字。
            text = e.get('text', '')
            shown = text[:max(1, math.ceil(len(text) * ease_out_cubic(q)))]
            step = int(round(t * c['fps'] * 0.34))  # boil 每秒约重掷 10 次，靠帧号而不是随机数
            amp = max(2, size // 13)
            line_h = int(font.size * 1.18)
            for row, chunk in enumerate(shown.split('\n')):
                cursor_x = x + 6
                for col, glyph in enumerate(chunk):
                    if glyph != ' ':
                        jx = round(boil(step * 31 + row * 7 + col) * amp)
                        jy = round(boil(step * 57 + row * 11 + col * 3 + 911) * amp)
                        draw.text((cursor_x + jx, y + 6 + row * line_h + jy), glyph, font=font, fill=ink, **stroke_args(size))
                    cursor_x += font.getlength(glyph)
        elif e['type'] == 'crosshatch':
            # Animate · crosshatch：文字压在一块素描排线上，排线按时间由疏到密铺满，整块每秒轻微错位。
            text = e.get('text', '')
            step = int(round(t * c['fps'] * 0.34))
            shift = (round(boil(step * 13) * 2), round(boil(step * 29 + 5) * 2))
            tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            gap = max(4, int(size / (0.9 + 5.5 * ease_out_cubic(q))))  # 排线由疏到密，是"正在画"的过程
            for off in range(0, w + h, gap):
                td.line(((off - h, 0), (off, h)), fill=tuple(ink[:3]) + (115,), width=max(1, size // 22))
            clip = Image.new('L', (w, h), 0)
            ImageDraw.Draw(clip).rounded_rectangle((1, 1, w - 2, h - 2), radius=max(2, size // 6), fill=255)
            tile.putalpha(ImageChops.multiply(tile.getchannel('A'), clip))
            layer.alpha_composite(tile, (x + shift[0], y + shift[1]))
            box = draw.multiline_textbbox((0, 0), text, font=font, spacing=2)
            draw.multiline_text((x + 6 - box[0] + shift[0], y + 6 - box[1] + shift[1]), text, font=font,
                                fill=ink, spacing=2, **stroke_args(size))
        elif e['type'] == 'pixel':
            # MG Styles 15 · 13 Pixel Art / Animate · pixel：先按大色块栅格化，格子随时间变细，
            # 字从马赛克里一格格"解析"清楚；缩放只用最近邻，保证是硬边像素而不是糊字。
            text = e.get('text', '')
            tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            box = td.multiline_textbbox((0, 0), text, font=font, spacing=2)
            td.multiline_text((6 - box[0], 6 - box[1]), text, font=font, fill=ink, spacing=2, **stroke_args(size))
            blocks = max(2, int(round(14 - 12 * ease_out_quint(q))))
            coarse = tile.resize((max(1, w // blocks), max(1, h // blocks)), Image.Resampling.BILINEAR)
            layer.alpha_composite(coarse.resize((w, h), Image.Resampling.NEAREST), (x, y))
        elif e['type'] == 'isometric':
            # MG Styles 15 · 02 Isometric 2.5D / Animate · isometric：文字旁边一块块等距板按时间长出来，
            # 用来表达层级结构；板子是真的逐块画顶面加两侧面，不是整块淡入。
            text = e.get('text', '')
            plates = 3
            unit = max(3, size // 3)
            below = image.height - (y + h) - 2
            if below >= unit * plates:
                top = y + h + unit // 2          # 优先排在文字下方
            else:
                top = max(unit, min(y + h // 2 - unit * plates // 2 + unit // 2, image.height - unit))
            half_w = min(max(1, w // 2), int(size * 1.6))
            cx = x + w // 2
            for k in range(plates):
                grow = ease_out_cubic(min(1, max(0, q * plates - k)))
                if grow <= 0:
                    continue
                cy = top + k * unit
                hw, hh = half_w * grow, max(2, unit // 2) * grow
                draw.polygon([(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)],
                             fill=tuple(ink[:3]) + (int(120 * grow),), outline=ink, width=max(1, size // 22))
                draw.line([(cx - hw, cy), (cx - hw, cy + hh * .55), (cx, cy + hh * 1.55), (cx + hw, cy + hh * .55), (cx + hw, cy)],
                          fill=tuple(ink[:3]) + (int(80 * grow),), width=max(1, size // 26))
            box = draw.multiline_textbbox((0, 0), text, font=font, spacing=2)
            draw.multiline_text((x + 6 - box[0], y + 6 - box[1]), text, font=font, fill=ink, spacing=2, **stroke_args(size))
        elif e['type'] == 'progress':
            draw.rectangle((x, y, x + w - 1, y + h - 1), outline=ink, width=line)
            target = e.get('fill', 1)
            if q > 0:
                draw.rectangle((x, y, x + max(0, (w - 1) * q * target), y + h - 1), fill=ink)
        else:
            points = [(x, y + h // 2), (x + w - 1, y + h // 2)] if e['type'] == 'arrow' else [
                (x, y), (x + w - 1, y), (x + w - 1, y + h - 1), (x, y + h - 1), (x, y)]
            remaining = sum(math.dist(a, b) for a, b in zip(points, points[1:])) * q
            for a, b in zip(points, points[1:]):
                length = math.dist(a, b)
                part = min(1, remaining / max(1, length))
                draw.line((a, (a[0] + (b[0] - a[0]) * part, a[1] + (b[1] - a[1]) * part)), fill=ink, width=line)
                remaining -= length
                if remaining <= 0:
                    break
            if e['type'] == 'arrow' and q > .8:
                tip, half = x + w - 1, (h // 2) * (q - .8) * 5
                draw.line([(tip - half, y + h // 2 - half), (tip, y + h // 2), (tip - half, y + h // 2 + half)], fill=ink, width=line)
    return Image.alpha_composite(image.convert('RGBA'), layer).convert('RGB')


def render_scene(item, canvas, dest, work):
    s, w, h, fps = item['scene'], canvas['width'], canvas['height'], canvas['fps']
    processes, logs, decoder = [], [], None
    try:
        elog = tempfile.TemporaryFile(dir=work); logs.append(elog)
        encoder = subprocess.Popen([*FF, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps),
                                    '-i', 'pipe:0', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                                    '-threads', '1', '-pix_fmt', 'yuv420p', '-n', str(dest)], stdin=subprocess.PIPE, stderr=elog)
        processes.append(encoder)
        if s['_media']['kind'] == 'image':
            with Image.open(s['source']) as original:
                photo = ImageOps.exif_transpose(original).convert('RGBA')
            resized = ImageOps.contain(photo, (w, h)) if s['fit'] == 'contain' else ImageOps.fit(photo, (w, h))
            base = Image.new('RGBA', (w, h), color(canvas['background']))
            base.alpha_composite(resized, ((w - resized.width) // 2, (h - resized.height) // 2))
            base = base.convert('RGB')
        else:
            sizing = (f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={canvas["background"]}'
                      if s['fit'] == 'contain' else f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}')
            dlog = tempfile.TemporaryFile(dir=work); logs.append(dlog)
            decoder = subprocess.Popen([*FF, *LOCAL, '-ss', str(s['source_in']), '-threads', '1', '-i', s['source'],
                                        '-map', f'0:{s["_media"]["video"]}', '-vf', f'scale=trunc(iw*sar/2)*2:ih,setsar=1,{sizing},fps={fps}',
                                        '-filter_threads', '1', '-frames:v', str(item['frames']), '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'],
                                       stdout=subprocess.PIPE, stderr=dlog)
            processes.append(decoder)
        for index in range(item['frames']):
            if decoder:
                data = bytearray()
                while len(data) < w * h * 3:
                    chunk = decoder.stdout.read(w * h * 3 - len(data))
                    check(bool(chunk), f'Decoder ended early in {s["id"]}; no frame looping')
                    data.extend(chunk)
                base = Image.frombytes('RGB', (w, h), bytes(data))
            data = memoryview(animate(base, s, canvas, index / fps).tobytes())
            while data:
                written = encoder.stdin.write(data)
                check(bool(written), 'Encoder stopped accepting frames')
                data = data[written:]
        encoder.stdin.close()
        for process in reversed(processes):
            check(process.wait() == 0, 'Scene codec failed')
    except Exception as error:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        details = []
        for process in processes:
            process.wait()
        for log in logs:
            log.seek(0); details.append(log.read().decode(errors='replace')[-1200:])
        raise ValueError(f'{error}: {"; ".join(details)}') from None
    finally:
        for process in processes:
            for pipe in (process.stdin, process.stdout):
                if pipe and not pipe.closed:
                    pipe.close()
            if process.poll() is None:
                process.terminate(); process.wait()
        for log in logs:
            log.close()


def render(plan, out, preview_seconds=None):
    p = validate(plan, out, preview_seconds)
    selected, duration = timeline(p, preview_seconds)
    c, sound, output = p['canvas'], p['soundtrack'], Path(out).absolute().resolve()
    with tempfile.TemporaryDirectory(prefix='vlog-work-', dir=output.parent) as directory:
        work, inputs, filters = Path(directory), [], []
        def add(args):
            index = sum(v == '-i' for v in inputs)
            inputs.extend(args)
            return index
        elapsed = 0
        for j, item in enumerate(selected):
            scene_file = work / f'scene-{j}.mp4'
            render_scene(item, c, scene_file, work)
            vi = add(['-i', str(scene_file)])
            # Only synthesize padding for the unfinished boundary transition, never decode later footage.
            frames = item['full_end'] - item['start'] if j + 1 < len(selected) else max(item['frames'], item['overlap'])
            length = frames / c['fps']
            # xfade needs a constant frame rate and setpts clears it, so fps must come last on every branch.
            filters.append(f'[{vi}:v]settb=AVTB,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop={frames-item["frames"]},trim=duration={length},setpts=PTS-STARTPTS,fps={c["fps"]}[v{j}]')
            s = item['scene']
            if s.get('source_audio', True) and s['_media']['audio'] is not None:
                ai = add([*LOCAL, '-ss', str(s['source_in']), '-t', str(item['frames'] / c['fps']), '-i', s['source']])
                audio = f'[{ai}:{s["_media"]["audio"]}]aresample=48000,aformat=channel_layouts=stereo'
            else:
                audio = 'anullsrc=r=48000:cl=stereo'
            filters.append(f'{audio},apad,atrim=duration={length},asetpts=PTS-STARTPTS[a{j}]')
            if j:
                overlap = item['overlap'] / c['fps']
                filters.extend([f'[{v}][v{j}]' + (f'xfade=transition={s["transition_in"]["type"]}:duration={overlap}:offset={elapsed-overlap},fps={c["fps"]}' if overlap else 'concat=n=2:v=1:a=0') + f'[vx{j}]',
                                f'[{a}][a{j}]' + (f'acrossfade=d={overlap}:c1=tri:c2=tri' if overlap else 'concat=n=2:v=0:a=1') + f'[ax{j}]'])
                v, a = f'vx{j}', f'ax{j}'
                elapsed += length - overlap
            else:
                v, a, elapsed = 'v0', 'a0', length
        filters.append(f'[{a}]volume={sound["source_volume"]}[source]')
        tracks = ['[source]']
        for key in ('narration', 'music'):
            if key in sound:
                ai = add([*LOCAL, '-t', str(duration), '-i', sound[key]])
                filters.append(f'[{ai}:a:0]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={duration},asetpts=PTS-STARTPTS,volume={sound[key+"_volume"]}[{key}]')
                tracks.append(f'[{key}]')
        filters.append(''.join(tracks) + f'amix=inputs={len(tracks)}:normalize=0,alimiter=limit=0.95:level=0:latency=1,atrim=duration={duration}[mix]')
        final = work / 'final.mp4'
        run([*FF, *inputs, '-filter_complex_threads', '1', '-filter_complex', ';'.join(filters), '-map', f'[{v}]', '-map', '[mix]',
             '-t', str(duration), '-c:v', 'libx264', '-threads', '1', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
             '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', '-n', str(final)])
        info = probe(final)
        actual = float(info['format']['duration'])
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        check(abs(actual - duration) <= 1 / c['fps'] + 1e-6, f'Final duration mismatch: expected {duration}, got {actual}')
        check((video['width'], video['height']) == (c['width'], c['height']) and any(s['codec_type'] == 'audio' for s in info['streams']), 'Final stream verification failed')
        report = {'schema': SCHEMA, 'duration': duration, 'actual_duration': actual, 'planned_duration': p['_duration'],
                  'width': c['width'], 'height': c['height'], 'fps': c['fps'], 'scene_count': len(selected),
                  'animation_types': sorted({e['type'] for i in selected for e in i['scene']['effects']} | {i['scene'].get('motion', 'none') for i in selected} - {'none'}),
                  'sources': [i['scene']['source'] for i in selected], 'source_root': p['source_root'],
                  'soundtrack': sound, 'preview_seconds': preview_seconds, 'transition_types': [i['scene']['transition_in']['type'] for i in selected]}
        report_file = work / 'report.json'
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        report_out = output.with_suffix('.report.json')
        os.link(report_file, report_out)  # Atomic no-clobber publication, including races.
        try:
            os.link(final, output)
        except Exception:
            report_out.unlink()
            raise
    return report


def main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise ValueError(message)
    try:
        parser = Parser(description=__doc__)
        parser.add_argument('--plan', required=True)
        parser.add_argument('--out', required=True)
        parser.add_argument('--preview-seconds', type=float)
        parser.add_argument('--validate-only', action='store_true')
        args = parser.parse_args(argv)
        plan_file = local_path(str(Path(args.plan).absolute()))
        with plan_file.open(encoding='utf-8') as file:
            plan = json.load(file)
        if args.validate_only:
            p = validate(plan, args.out, args.preview_seconds)
            scenes, duration = timeline(p, args.preview_seconds)
            result = {'valid': True, 'duration': duration, 'planned_duration': p['_duration'], 'scene_count': len(scenes)}
        else:
            result = render(plan, args.out, args.preview_seconds)
        print(json.dumps({'ok': True, **result}, ensure_ascii=False))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps({'ok': False, 'error': str(error) or type(error).__name__}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
