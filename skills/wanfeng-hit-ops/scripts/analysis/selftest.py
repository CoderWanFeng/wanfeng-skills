#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/selftest.py - 计算层自检

用历史报告里已人工核对过的数字做回归验证。
如果这些数字变了，说明计算层口径被改坏了 —— 必须先查清原因再改。

跑法：
    uv run --with pandas --with xlrd --with openpyxl python3 scripts/analysis/selftest.py \
        --root <数据根目录> --month 2026-11
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from analysis import pipeline

# 历史核对基准（来源：月度报告/2026-10/report_2026-10-30.md 等人工复核稿）
# 每项：(说明, 实际值, 期望值, 容差)
BASELINES = [
    ('抖音近90天作品数', 'douyin', 'n', 36, 0),
    ('抖音总播放', 'douyin', '总曝光', 751930, 0),
    ('抖音总涨粉', 'douyin', '总涨粉', 2936, 0),
    ('视频号作品数', 'shipinhao', 'n', 22, 0),
    ('视频号总播放', 'shipinhao', '总曝光', 393842, 0),
    ('视频号总涨粉', 'shipinhao', '总涨粉', 2354, 0),
    ('视频号 Top3 涨粉占比', 'shipinhao', 'Top3涨粉占比', 60.1, 0.5),
    ('小红书笔记数', 'xiaohongshu', 'n', 11, 0),
    ('小红书总观看', 'xiaohongshu', '总曝光', 15409, 0),
    ('小红书总涨粉', 'xiaohongshu', '总涨粉', 127, 0),
    ('小红书 Top3 涨粉占比', 'xiaohongshu', 'Top3涨粉占比', 93.7, 0.5),
]


def check(result):
    passed, failed = 0, []
    for desc, pk, key, expected, tol in BASELINES:
        conc = result.get('concentration', {}).get(pk)
        if not conc:
            failed.append(f'{desc}: 无该平台数据')
            continue
        if key == 'n':
            actual = conc['n']
        elif key == '总曝光':
            actual = conc['总曝光']
        elif key == '总涨粉':
            actual = conc['总涨粉']
        elif key == 'Top3涨粉占比':
            actual = conc['Top3']['涨粉占比']
        else:
            actual = None
        if actual is None:
            failed.append(f'{desc}: 基准项 {key} 未定义')
            continue
        if abs(float(actual) - expected) <= tol:
            passed += 1
            print(f'  ✓ {desc}: {actual:,.2f}')
        else:
            failed.append(f'{desc}: 实际 {actual:,.2f}，期望 {expected:,.2f}')

    # 效率指标抽查：视频号 GLM-5.3 那条
    unified = result.get('unified')
    if unified is not None and len(unified) > 0:
        sh = unified[unified['platform_key'] == 'shipinhao']
        hit = sh[sh['views'] == 82368]
        if len(hit) == 1:
            r = hit.iloc[0]
            # 历史报告：播放 82,368，涨粉 813，每千播放涨粉 9.87
            for desc, actual, expected, tol in [
                ('GLM-5.3 播放量', r['views'], 82368, 0),
                ('GLM-5.3 涨粉', r['followers'], 813, 0),
                ('GLM-5.3 每千涨粉', r['每千涨粉'], 9.87, 0.02),
            ]:
                if abs(float(actual) - expected) <= tol:
                    passed += 1
                    print(f'  ✓ {desc}: {actual:,.2f}')
                else:
                    failed.append(f'{desc}: 实际 {actual:,.2f}，期望 {expected:,.2f}')

        # 纳米Work 商单：播放 75,988，每千涨粉 1.83（历史报告验证过）
        nw = sh[sh['views'] == 75988]
        if len(nw) == 1:
            r = nw.iloc[0]
            for desc, actual, expected, tol in [
                ('纳米Work 播放量', r['views'], 75988, 0),
                ('纳米Work 每千涨粉', r['每千涨粉'], 1.83, 0.02),
            ]:
                if abs(float(actual) - expected) <= tol:
                    passed += 1
                    print(f'  ✓ {desc}: {actual:,.2f}')
                else:
                    failed.append(f'{desc}: 实际 {actual:,.2f}，期望 {expected:,.2f}')

    # 四象限一致性：高触达高价值的效率中位数必须高于低触达低价值
    for row in result.get('quadrants', []):
        if row['象限'] == '高触达 × 高价值':
            hh = row['效率中位数']
        elif row['象限'] == '低触达 × 低价值':
            ll = row['效率中位数']
    if 'hh' in dir() and 'll' in dir() and hh == hh and ll == ll:
        if hh >= ll:
            passed += 1
            print(f'  ✓ 象限单调性: 高价值象限效率中位数 {hh:.2f} ≥ 低价值象限 {ll:.2f}')
        else:
            failed.append(f'象限单调性被破坏: 高价值 {hh:.2f} < 低价值 {ll:.2f}')

    return passed, failed


def main(argv=None):
    ap = argparse.ArgumentParser(description='计算层自检')
    ap.add_argument('--month', default='2026-11')
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import _paths
    _paths.add_root_arg(ap)
    args = ap.parse_args(argv)

    _paths.init(root=args.root)
    from parse_data import main as parse_main
    data = parse_main()

    print('\n===== 计算层自检 =====')
    result = pipeline.run(data, month=args.month)
    passed, failed = check(result)

    print(f'\n通过 {passed} 项，失败 {len(failed)} 项')
    for f in failed:
        print(f'  ✗ {f}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
