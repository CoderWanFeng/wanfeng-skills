"""Synthetic-only validation and real ffmpeg integration tests (no user media)."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image, ImageDraw

MODULE = Path(__file__).resolve().with_name('vlog_render.py')
spec = importlib.util.spec_from_file_location('vlog_render', MODULE)
vr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vr)


class RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            raise unittest.SkipTest('Local ffmpeg/ffprobe required')
        cls.temp = tempfile.TemporaryDirectory(prefix='vlog-tests-')
        cls.root = Path(cls.temp.name).resolve()
        fonts = [Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
                 Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
                 Path('/Library/Fonts/Arial.ttf')]
        cls.font = next((p for p in fonts if p.is_file()), None)
        if cls.font is None:
            cls.temp.cleanup()
            raise unittest.SkipTest('A local TrueType font required')
        cls.font = cls.font.resolve()
        for name, tint, freq in [('red', 'red', 330), ('blue', 'blue', 550)]:
            vr.run([*vr.FF, '-f', 'lavfi', '-i', f'color=c={tint}:s=160x90:r=30:d=4',
                    '-f', 'lavfi', '-i', f'sine=frequency={freq}:sample_rate=48000:duration=4',
                    '-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest',
                    '-n', str(cls.root / f'{name}.mp4')])
        image = Image.new('RGB', (180, 120), '#234567')
        draw = ImageDraw.Draw(image)
        draw.rectangle((20, 20, 120, 80), fill='#abcdef')
        image.save(cls.root / 'photo.png')
        for name, duration in [('narration', 1), ('music', 10)]:
            vr.run([*vr.FF, '-f', 'lavfi', '-i', f'sine=frequency=220:duration={duration}',
                    '-n', str(cls.root / f'{name}.wav')])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def plan(self):
        return {'schema': vr.SCHEMA, 'source_root': str(self.root),
                'canvas': {'width': 160, 'height': 90, 'fps': 30, 'background': '#101010', 'font_path': str(self.font)},
                'scenes': [{'id': 'a', 'source': str(self.root / 'red.mp4'), 'duration': 3, 'fit': 'cover',
                            'effects': [{'type': 'progress', 'start': 0, 'duration': 2, 'x': .15, 'y': .7, 'size_px': 12, 'color': '#ffffff'}]},
                           {'id': 'b', 'source': str(self.root / 'blue.mp4'), 'duration': 3, 'fit': 'contain',
                            'transition_in': {'type': 'fade', 'duration': 1}},
                           {'id': 'c', 'source': str(self.root / 'photo.png'), 'duration': 3, 'fit': 'cover', 'motion': 'push-in',
                            'transition_in': {'type': 'wipeleft', 'duration': 1}}]}

    def invalid(self, edit, message=None):
        plan = self.plan()
        edit(plan)
        with self.assertRaises(ValueError) as caught:
            vr.validate(plan)
        if message:
            self.assertIn(message, str(caught.exception))

    def test_validation_bad_schema_empty_long_unknown_and_numbers(self):
        edits = [lambda p: p.update(scenes=[]), lambda p: p.update(schema='wrong'),
                 lambda p: p.update(unrecognized=True), lambda p: p['scenes'][0].update(duration=5000),
                 lambda p: p['scenes'][0]['effects'][0].update(type='magic'),
                 lambda p: p['scenes'][0]['effects'][0].update(x=-.1),
                 lambda p: p['scenes'][0].update(source_in=-1),
                 lambda p: p['scenes'][0].update(duration=float('nan')),
                 lambda p: p['scenes'][0].update(duration=float('inf')),
                 lambda p: p['scenes'][0]['effects'][0].update(size_px=float('nan')),
                 lambda p: p['canvas'].update(width=159), lambda p: p['canvas'].update(fps=29),
                 lambda p: p['scenes'][1].update(id='a'),
                 lambda p: p.update(soundtrack={'source_volume': -1}),
                 lambda p: p['scenes'][0].update(source_audio=1),
                 lambda p: p['scenes'][0].update(source=str(self.root / 'missing.mp4'))]
        for edit in edits:
            with self.subTest(edit=edit):
                self.invalid(edit)
        self.invalid(lambda p: p['scenes'][0].update(source_in=2), 'real video duration')
        self.invalid(lambda p: p['scenes'][0]['effects'][0].update(start=2), 'beyond scene')
        self.invalid(lambda p: p['scenes'][1]['transition_in'].update(duration=1.6), 'half')
        self.invalid(lambda p: p['scenes'][1]['transition_in'].update(type='unknown'), 'Unknown transition')
        self.invalid(lambda p: p['scenes'][0].update(transition_in={'type': 'fade', 'duration': .5}), 'half')
        self.invalid(lambda p: p['scenes'][2].update(source_in=1), 'Images require')
        self.invalid(lambda p: p.update(soundtrack={'narration': str(self.root / 'music.wav')}), 'Narration exceeds')

    def test_path_boundary_symlinks_and_new_output_guard(self):
        outside = self.root / 'outside'
        outside.mkdir(exist_ok=True)
        source_dir = self.root / 'allowed'
        source_dir.mkdir(exist_ok=True)
        self.invalid(lambda p: p.update(source_root=str(source_dir)), 'outside source_root')
        link = self.root / 'linked.mp4'
        link.symlink_to(self.root / 'red.mp4')
        try:
            self.invalid(lambda p: p['scenes'][0].update(source=str(link)), 'Symlinks')
        finally:
            link.unlink()
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            vr.validate(self.plan(), self.root / 'red.mp4')
        with self.assertRaisesRegex(ValueError, 'finite'):
            vr.validate(self.plan(), preview_seconds=-1)
        with self.assertRaisesRegex(ValueError, 'finite'):
            vr.validate(self.plan(), preview_seconds=float('nan'))
        report = self.root / 'reserved.report.json'
        report.write_text('{}')
        try:
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                vr.validate(self.plan(), self.root / 'reserved.mp4')
        finally:
            report.unlink()
        tiny = self.plan()
        tiny['canvas'].update(width=8, height=8)
        tiny['scenes'][0]['effects'] = [{'type': 'typewriter', 'text': 'this cannot fit', 'duration': 1,
                                       'x': 0, 'y': 0, 'color': '#fff'}]
        with self.assertRaisesRegex(ValueError, 'cannot fit'):
            vr.validate(tiny)

    def test_hdr_rejected_from_probe(self):
        real = vr.probe
        def hdr(path):
            info = real(path)
            info['streams'][0]['color_transfer'] = 'smpte2084'
            return info
        with mock.patch.object(vr, 'probe', side_effect=hdr):
            with self.assertRaisesRegex(ValueError, 'explicit SDR copy'):
                vr.validate(self.plan())

    def test_five_second_selection_and_overlap_duration(self):
        p = vr.validate(self.plan())
        full, duration = vr.timeline(p)
        self.assertEqual(duration, 7)
        prefix, duration = vr.timeline(p, 5)
        self.assertEqual(duration, 5)
        self.assertEqual([i['scene']['id'] for i in prefix], ['a', 'b', 'c'])
        self.assertEqual([i['frames'] for i in prefix], [90, 90, 30])
        self.assertEqual([i['overlap'] for i in prefix], [0, 30, 30])
        p['scenes'][2]['_start'] = 5
        prefix, _ = vr.timeline(p, 5)
        self.assertEqual([i['scene']['id'] for i in prefix], ['a', 'b'])
        # Fractional cumulative boundaries must not accumulate per-scene rounding errors.
        q = self.plan()
        q['scenes'] = [dict(id=str(i), source=str(self.root / 'photo.png'), duration=.101, fit='contain') for i in range(25)]
        normalized = vr.validate(q)
        items, duration = vr.timeline(normalized)
        self.assertLessEqual(abs(duration - normalized['_duration']), 1 / 30)
        self.assertEqual(sum(i['frames'] for i in items), round(duration * 30))

    def test_effects_have_middle_frames_and_clamped_text(self):
        c = self.plan()['canvas']
        for kind in sorted(vr.EFFECTS):
            effect = {'type': kind, 'text': 'Hello!', 'start': 0, 'duration': 1, 'x': .98, 'y': .98,
                      'size_px': 14, 'color': '#fff'}
            scene = {'duration': 1, 'effects': [effect]}
            base = Image.new('RGB', (160, 90), 'black')
            images = [vr.animate(base, scene, c, t).tobytes() for t in (0, .2, .6)]
            with self.subTest(kind=kind):
                self.assertEqual(len(set(images)), 3)
                x, y, w, h, _, _ = vr.effect_layout(effect, c)
                self.assertTrue(0 <= x <= 160 - w and 0 <= y <= 90 - h)

    def test_real_one_second_preview_has_audio_size_duration_and_animation(self):
        p = self.plan()
        p['soundtrack'] = {'narration': str(self.root / 'narration.wav'), 'music': str(self.root / 'music.wav')}
        before = {s['source']: hashlib.sha256(Path(s['source']).read_bytes()).hexdigest() for s in p['scenes']}
        output = self.root / 'preview.mp4'
        called = []
        real_scene = vr.render_scene
        def record(item, *args):
            called.append((item['scene']['id'], item['frames']))
            return real_scene(item, *args)
        with mock.patch.object(vr, 'render_scene', side_effect=record):
            report = vr.render(p, output, 1)
        self.assertEqual(called, [('a', 30)])
        info = vr.probe(output)
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        self.assertEqual((video['width'], video['height']), (160, 90))
        self.assertAlmostEqual(float(info['format']['duration']), 1, delta=1 / 30)
        self.assertTrue(any(s['codec_type'] == 'audio' for s in info['streams']))
        pcm = vr.run([*vr.FF, '-i', str(output), '-vn', '-f', 's16le', '-ac', '1', 'pipe:1'])
        self.assertTrue(any(pcm))
        raw = vr.run([*vr.FF, '-i', str(output), '-an', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'])
        frame_bytes = 160 * 90 * 3
        self.assertNotEqual(raw[3 * frame_bytes:4 * frame_bytes], raw[18 * frame_bytes:19 * frame_bytes])
        self.assertEqual(report['scene_count'], 1)
        self.assertEqual(report['preview_seconds'], 1)
        self.assertEqual(json.loads(output.with_suffix('.report.json').read_text())['duration'], 1)
        self.assertFalse(list(self.root.glob('vlog-work-*')))
        for source, digest in before.items():
            self.assertEqual(hashlib.sha256(Path(source).read_bytes()).hexdigest(), digest)

    def test_real_transitions_partial_boundary_and_image_without_narration(self):
        for transition in sorted(vr.TRANSITIONS):
            p = self.plan()
            p['scenes'][0].update(duration=.6, effects=[])
            p['scenes'][1].update(duration=.6, transition_in={'type': transition, 'duration': 0 if transition == 'cut' else .2})
            p['scenes'][2].update(duration=.6, transition_in={'type': 'cut', 'duration': 0}, source_audio=False)
            for preview in (None, .5 if transition == 'cut' else .5):
                with self.subTest(transition=transition, preview=preview):
                    out = self.root / f'{transition}-{preview}.mp4'
                    report = vr.render(p, out, preview)
                    self.assertAlmostEqual(report['duration'], 1.8 if transition == 'cut' and preview is None else
                                           (1.6 if preview is None else .5), delta=1 / 30)
                    self.assertAlmostEqual(report['actual_duration'], report['duration'], delta=1 / 30)
                    if preview == .5:
                        self.assertEqual(report['scene_count'], 1 if transition == 'cut' else 2)
        p = self.plan()
        p['scenes'] = [p['scenes'][2]]
        p['scenes'][0]['transition_in'] = {'type': 'cut', 'duration': 0}
        report = vr.render(p, self.root / 'image-only.mp4', 1)
        self.assertEqual(report['duration'], 1)
        self.assertEqual(report['scene_count'], 1)

    def test_cli_validate_and_errors_json_no_traceback(self):
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(self.plan()))
        args = [sys.executable, '-B', str(MODULE), '--plan', str(plan), '--out', str(self.root / 'unused.mp4'),
                '--preview-seconds', '5', '--validate-only']
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['duration'], 5)
        self.assertFalse((self.root / 'unused.mp4').exists())
        result = subprocess.run(args + ['--unsupported'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['ok'])
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
