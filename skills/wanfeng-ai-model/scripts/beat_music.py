#!/usr/bin/env python3
"""程序化生成「卡点换装」背景音乐 —— 纯 numpy + 标准库，不需要 scipy / pydub / 外部音源。

设计约定：
  - 每个服装片段 = 1 小节（4 拍），画面硬切点落在小节线，音乐 impact 正好压在切点上。
  - 默认 BPM 120 -> 每拍 0.5s -> 每小节 2.0s；3 套服装 = 6.0s 成片。
  - 输出 48kHz / 16bit / 立体声 WAV，时长严格等于 segments * seg_seconds。
  - 峰值限制在 -1 dBFS；成片合成时再走 -14 LUFS 发布归一。

用法：
  python3 beat_music.py --out 卡点音乐.wav --segments 3 --bpm 120
  python3 beat_music.py --out 卡点音乐.wav --segments 5 --bpm 128 --seed 7
"""
import argparse
import json
import wave
import numpy as np

SR = 48000
RNG = np.random.default_rng(20261123)


def _n(sec):
    return max(1, int(round(sec * SR)))


def _env(n, attack, decay):
    t = np.arange(n) / SR
    return np.clip(t / max(attack, 1e-6), 0, 1) * np.exp(-t / max(decay, 1e-6))


def kick(sec=0.30):
    n = _n(sec)
    t = np.arange(n) / SR
    f = 48 + 115 * np.exp(-t * 26)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 12)
    click = RNG.standard_normal(n) * np.exp(-t * 220) * 0.25
    return 0.85 * (body + click)


def snare(sec=0.22):
    n = _n(sec)
    t = np.arange(n) / SR
    noise = RNG.standard_normal(n)
    hp = np.diff(noise, prepend=noise[0])
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28) * 0.35
    return 0.45 * (hp * np.exp(-t * 18) + body)


def hat(sec=0.07, level=0.22):
    n = _n(sec)
    t = np.arange(n) / SR
    hp = np.diff(RNG.standard_normal(n), prepend=0.0)
    return level * hp * np.exp(-t * 70)


def bass(freq, sec=0.45):
    n = _n(sec)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
    return 0.30 * np.tanh(1.4 * x) * _env(n, 0.008, 0.22)


def pad(chord, sec=2.0):
    n = _n(sec)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in chord:
        out += np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.5 * t))
    out /= len(chord)
    w = np.minimum(np.clip(t / 0.25, 0, 1), np.clip((sec - t) / 0.35, 0, 1))
    return 0.16 * out * w


def impact(sec=0.45):
    """切点音效：低频 hit + 上升 whoosh，压在换装硬切那一帧上。"""
    n = _n(sec)
    t = np.arange(n) / SR
    low = np.sin(2 * np.pi * (90 - 40 * t / sec) * t) * np.exp(-t * 8)
    sweep = RNG.standard_normal(n) * (t / sec) ** 2 * np.exp(-t * 4)
    return 0.55 * low + 0.16 * sweep


def _add(buf, sig, at):
    i = int(round(at * SR))
    j = min(len(buf), i + len(sig))
    if i >= len(buf):
        return
    buf[i:j] += sig[: j - i]


def build(segments, seg_seconds, bpm, seed):
    global RNG
    RNG = np.random.default_rng(seed)
    beat = 60.0 / bpm
    total = segments * seg_seconds
    left = np.zeros(_n(total))
    right = np.zeros(_n(total))

    roots = [110.00, 87.31, 130.81, 98.00]          # A2 F2 C3 G2
    chords = [
        [220.00, 261.63, 329.63],                    # Am
        [174.61, 220.00, 261.63],                    # F
        [261.63, 329.63, 392.00],                    # C
        [196.00, 246.94, 293.66],                    # G
    ]

    for s in range(segments):
        t0 = s * seg_seconds
        root = roots[s % 4]
        ch = chords[s % 4]
        p = pad(ch, min(seg_seconds, 4 * beat))
        _add(left, p, t0)
        _add(right, p, t0)

        for b in range(4):
            bt = t0 + b * beat
            if b in (0, 2):
                k = kick()
                _add(left, k, bt)
                _add(right, k, bt)
            if b == 2:
                sn = snare()
                _add(left, sn, bt)
                _add(right, sn, bt)
            h = hat()
            _add(left, h, bt)
            _add(right, h, bt)
            h2 = hat(0.05, 0.13)
            _add(left, h2, bt + beat / 2)
            _add(right, h2, bt + beat / 2)
            bs = bass(root, beat * 0.9)
            _add(left, bs, bt)
            _add(right, bs, bt)

        # 最后一拍后半做 riser 铺垫，切点前蓄力
        rs = impact(0.35)
        _add(left, rs, t0 + 3.5 * beat)
        _add(right, rs, t0 + 3.5 * beat)
        # 切点 impact（首段不加，避免开场突兀）
        if s > 0:
            im = impact()
            _add(left, im, t0)
            _add(right, im, t0)

    # 轻微立体声宽度：右声道整体延迟 3ms
    right = np.roll(right, int(0.003 * SR))

    n = len(left)
    fi, fo = _n(0.04), _n(0.30)
    w = np.ones(n)
    w[:fi] = np.linspace(0, 1, fi)
    w[-fo:] = np.linspace(1, 0, fo)
    left *= w
    right *= w

    peak = max(np.abs(left).max(), np.abs(right).max(), 1e-9)
    g = min((10 ** (-1 / 20)) / peak, 1.0)
    left *= g
    right *= g

    stereo = np.empty(n * 2, dtype=np.float64)
    stereo[0::2] = left
    stereo[1::2] = right
    pcm = np.clip(stereo * 32767, -32768, 32767).astype("<i2")
    return pcm, total, beat


def main():
    ap = argparse.ArgumentParser(description="程序化生成卡点换装音乐")
    ap.add_argument("--out", required=True, help="输出 WAV 路径")
    ap.add_argument("--segments", type=int, default=3, help="服装套数 / 片段数（默认 3）")
    ap.add_argument("--bpm", type=float, default=120, help="BPM（默认 120）")
    ap.add_argument("--seg", type=float, default=None,
                    help="每段秒数；留空则自动 = 4*60/bpm，保证切点落在小节线")
    ap.add_argument("--seed", type=int, default=20261123, help="随机种子（复现用）")
    ap.add_argument("--report", default=None, help="可选：输出 report.json 路径")
    a = ap.parse_args()

    seg = a.seg if a.seg else 4 * 60.0 / a.bpm
    if abs(seg - 4 * 60.0 / a.bpm) > 0.01:
        print(f"[warn] --seg={seg:.3f}s 与小节线 {4*60/a.bpm:.3f}s 不一致，切点可能不卡拍")

    pcm, total, beat = build(a.segments, seg, a.bpm, a.seed)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    report = {
        "out": a.out,
        "sample_rate": SR,
        "channels": 2,
        "segments": a.segments,
        "seg_seconds": round(seg, 3),
        "bpm": a.bpm,
        "beat_seconds": round(beat, 3),
        "total_seconds": round(total, 3),
        "cut_points": [round(i * seg, 3) for i in range(1, a.segments)],
        "seed": a.seed,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[ok] 音乐已生成：{a.out}  ({total:.2f}s)")


if __name__ == "__main__":
    main()
