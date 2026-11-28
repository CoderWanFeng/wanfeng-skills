#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/pipeline.py - 计算层编排

把 parse_data 的原始 data 跑成一份完整的分析结果，供 monthly_report.py 与
analyze.py 消费。

输出结构：
    {
        'unified':        统一内容表（含效率指标与象限归属）
        'baseline':       各平台效率基线（中位数 + P75）
        'quadrants':      象限汇总
        'concentration':  各平台帕累托集中度
        'features':       各平台标题特征分组对比
        'keywords':       各平台关键词分组
        'relations':      相关性矩阵
        'surprises':      反直觉发现
        'reach_vs_eff':   触达 vs 效率分组对比
        'growth_path':    涨粉路径拆解
        'findings':       结构化发现条目列表
        'by_platform':    按平台分组的发现
    }
"""

import pandas as pd

from . import schema, efficiency, concentration, relations, findings as F


def run(data, month=None, window_days=90, with_features=True):
    """跑完整分析。

    month: 报告月（YYYY-MM）。决定内容级分析窗口的起点。
    window_days: 滚动窗口天数，默认 90 天往前。
    """
    if month:
        window_start, window_note = schema.content_window(month, days=window_days)
    else:
        window_start, window_note = None, '未指定报告月，未做窗口过滤'

    # 1. 归一：各平台单作品表 → 统一内容表
    unified = schema.collect(data, window_start=window_start)
    if len(unified) == 0:
        return {
            'unified': unified, 'baseline': {}, 'quadrants': [],
            'concentration': {}, 'features': {}, 'keywords': {},
            'relations': [], 'surprises': [], 'reach_vs_eff': [],
            'growth_path': {}, 'findings': [], 'by_platform': {},
            'window_note': window_note,
        }

    # 2. 效率指标 + 四象限（按平台分别切分，不跨平台）
    unified = efficiency.compute_efficiency(unified)
    frames = []
    for pk, sub in unified.groupby('platform_key'):
        frames.append(efficiency.add_quadrant(sub))
    unified = pd.concat(frames, ignore_index=True) if frames else unified

    # 3. 基线与象限汇总
    baseline = efficiency.baseline(unified)
    quad_rows = []
    for pk, sub in unified.groupby('platform_key'):
        for r in efficiency.quadrant_summary(sub):
            r['platform_key'] = pk
            quad_rows.append(r)

    # 4. 集中度
    conc = {}
    for pk, sub in unified.groupby('platform_key'):
        conc[pk] = concentration.pareto(sub)

    # 5. 标题特征与关键词分组
    feature_map = {}
    keyword_map = {}
    overperform_map = {}
    if with_features:
        tagged = concentration.tag_titles(unified)
        for pk, sub in tagged.groupby('platform_key'):
            feature_map[pk] = concentration.feature_groups(sub)
            keyword_map[pk] = concentration.keyword_groups(sub)
            # 过度表现检验：每个特征「命中 / 未命中」两组的贡献放大倍数
            # 结构：{特征名: {True: 放大倍数, False: 放大倍数}}
            # True = 命中该特征，False = 未命中
            op = {}
            for feat in concentration.TITLE_FEATURES:
                if feat not in sub.columns:
                    continue
                sub_op = efficiency.overperform_check(sub, feat)
                if sub_op:
                    op[feat] = sub_op
            overperform_map[pk] = op

    # 6. 相关性
    matrix = relations.correlation_matrix(unified)
    surprise = relations.surprising_findings(unified, matrix)
    reach = relations.efficiency_vs_reach(unified)

    # 7. 涨粉路径（视频号有粉丝表可交叉验证）
    growth = relations.growth_path_split(
        unified[unified['platform_key'] == 'shipinhao'],
        data.get('shipinhao_fans'))

    # 8. 发现条目
    all_findings = F.build_findings(
        data, unified, conc, quad_rows, matrix, surprise, feature_map,
        overperform_map=overperform_map)

    return {
        'unified': unified,
        'baseline': baseline,
        'quadrants': quad_rows,
        'concentration': conc,
        'features': feature_map,
        'keywords': keyword_map,
        'relations': matrix,
        'surprises': surprise,
        'reach_vs_eff': reach,
        'growth_path': growth,
        'findings': all_findings,
        'by_platform': F.group_by_platform(all_findings),
        'window_note': window_note,
    }


def platform_label(pk):
    """platform_key → 中文平台名"""
    return {
        'douyin': '抖音',
        'xiaohongshu': '小红书',
        'shipinhao': '视频号',
    }.get(pk, pk)
