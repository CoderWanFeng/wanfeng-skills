#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/efficiency.py - 效率指标与四象限

对应 `references/hit-methodology.md` §一 / §二 / §三 的代码化。

核心主张（来自方法论，不是这里发明的）：
    判断内容好坏不看播放量，看每千播放涨粉与每千播放收藏。

为什么不用播放量：播放量由分发决定（账号权重、时段、平台活动、热点运气），
由内容决定的只有转化效率。用播放量排序会把「被推了一把」误当成「选题好」。

象限用中位数切，不用绝对阈值：
    「1000 播放」硬切会把「无效爆款」（刚过线、效率极低）和
    「高质量内容」（过线且效率高）划进同一组，中位数才能分开。

小基数防线：
    播放太小的条目涨粉率天然虚高（分母趋近 0），不进效率榜，
    只标「样本过小」。阈值取「账号内播放中位数 × 0.2」与固定下限中更严者。
"""

import pandas as pd

# 效率榜最小分母（绝对下限）
MIN_VIEWS_FLOOR = 100


def _safe_div(num, den):
    """分母为 0 / NaN 时返回 NaN，不返回 inf"""
    num = pd.to_numeric(num, errors='coerce')
    den = pd.to_numeric(den, errors='coerce')
    out = num / den.replace(0, pd.NA)
    return out.astype(float)


def compute_efficiency(df):
    """给统一内容表加效率指标列。

    新增列：
        每千涨粉    涨粉 ÷ 曝光分母 × 1000
        每千收藏    收藏 ÷ 曝光分母 × 1000（无收藏口径时为 NaN）
        每千互动    (点赞+评论+分享+收藏) ÷ 曝光分母 × 1000
        互动率      互动量 ÷ 曝光分母（%，用于分组对比）
        收藏率      收藏 ÷ 曝光分母（%）
        涨粉率      涨粉 ÷ 曝光分母（%）
    分母口径由 platform_key 决定（播放 or 观看），单位统一成「每千」。
    """
    if df is None or len(df) == 0:
        return df
    out = df.copy()
    den = out['views'].replace(0, pd.NA)

    out['涨粉率'] = (_safe_div(out['followers'], den) * 100).astype(float)
    out['收藏率'] = (_safe_div(out['saves'], den) * 100).astype(float)

    interact = out['likes'].fillna(0) + out['comments'].fillna(0) + \
        out['shares'].fillna(0) + out['saves'].fillna(0)
    out['互动量'] = interact
    out['互动率'] = (_safe_div(interact, den) * 100).astype(float)
    out['每千涨粉'] = (_safe_div(out['followers'], den) * 1000).astype(float)
    out['每千收藏'] = (_safe_div(out['saves'], den) * 1000).astype(float)
    out['每千互动'] = (_safe_div(interact, den) * 1000).astype(float)
    return out


def min_views_threshold(df):
    """小基数门槛：账号内播放中位数 × 0.2 与固定下限 100，取更严者"""
    med = pd.to_numeric(df['views'], errors='coerce').median()
    if pd.isna(med):
        return MIN_VIEWS_FLOOR
    return max(MIN_VIEWS_FLOOR, med * 0.2)


def add_quadrant(df, x='views', y='每千涨粉'):
    """按中位数切四象限。

    x = 触达（播放/观看量）  y = 价值（每千涨粉）
    只在同一平台内切分 —— 跨平台分母口径不同，切出来的象限没有可比性。

    象限语义（方法论 §二）：
        高触达 × 高价值 = 真爆款（承接内容，账号护城河）
        高触达 × 低价值 = 伪爆款（放量内容，分发红利，不值得复制）
        低触达 × 高价值 = 埋没好内容（题材有效但分发不足）
        低触达 × 低价值 = 无效内容（不分析）
    """
    if df is None or len(df) == 0:
        return df
    out = df.copy()
    out = out[out[x].notna() & out[y].notna()].copy()
    if len(out) == 0:
        out['象限'] = []
        return out

    x_med = out[x].median()
    y_med = out[y].median()
    out['_x_median'] = x_med
    out['_y_median'] = y_med

    out['触达'] = out[x].apply(lambda v: '高触达' if v >= x_med else '低触达')
    out['价值'] = out[y].apply(lambda v: '高价值' if v >= y_med else '低价值')
    out['象限'] = out['触达'] + ' × ' + out['价值']

    label = {
        '高触达 × 高价值': '真爆款',
        '高触达 × 低价值': '伪爆款',
        '低触达 × 高价值': '埋没好内容',
        '低触达 × 低价值': '无效内容',
    }
    out['象限判定'] = out['象限'].map(label).fillna('')
    return out


def baseline(df, metric='每千涨粉'):
    """同平台基线：中位数 + P75（不用均值 —— 爆款会把均值拉飞）"""
    if df is None or len(df) == 0:
        return {}
    out = {}
    for pk, sub in df.groupby('platform_key'):
        if len(sub) == 0:
            continue
        s = pd.to_numeric(sub[metric], errors='coerce').dropna()
        if len(s) == 0:
            continue
        out[pk] = {
            'n': len(s),
            'median': float(s.median()),
            'p75': float(s.quantile(0.75)),
            'max': float(s.max()),
            'min': float(s.min()),
        }
    return out


def quadrant_summary(df, metric='每千涨粉', value_col='views'):
    """象限汇总：每象限的条数、曝光占比、涨粉占比、效率中位数"""
    if df is None or len(df) == 0 or '象限' not in df.columns:
        return []
    rows = []
    total_v = pd.to_numeric(df[value_col], errors='coerce').sum()
    total_f = pd.to_numeric(df['followers'], errors='coerce').sum()
    order = ['高触达 × 高价值', '高触达 × 低价值', '低触达 × 高价值', '低触达 × 低价值']
    for q in order:
        sub = df[df['象限'] == q]
        if len(sub) == 0:
            continue
        v = pd.to_numeric(sub[value_col], errors='coerce').sum()
        f = pd.to_numeric(sub['followers'], errors='coerce').sum()
        eff = pd.to_numeric(sub[metric], errors='coerce').dropna()
        rows.append({
            '象限': q,
            '判定': sub['象限判定'].iloc[0] if '象限判定' in sub.columns else '',
            '条数': len(sub),
            '曝光': v,
            '曝光占比': (v / total_v * 100) if total_v else float('nan'),
            '涨粉': f,
            '涨粉占比': (f / total_f * 100) if total_f else float('nan'),
            '效率中位数': float(eff.median()) if len(eff) else float('nan'),
            '效率P75': float(eff.quantile(0.75)) if len(eff) else float('nan'),
        })
    return rows


def group_stats(df, by, metric='每千涨粉', min_n=3):
    """按某个维度分组，比较各组的效率中位数与 P75。

    方法论 §八要求：按编码分组后比较的是**中位数与 P75**，不是均值、不跨平台。
    样本 < min_n 的组只标「待验证」，不参与结论。
    """
    if df is None or len(df) == 0:
        return []
    rows = []
    for key, sub in df.groupby(by):
        s = pd.to_numeric(sub[metric], errors='coerce').dropna()
        if len(s) == 0:
            continue
        rows.append({
            '组': key,
            'n': len(s),
            '效率中位数': float(s.median()),
            '效率P75': float(s.quantile(0.75)),
            '效率均值': float(s.mean()),
            '涨粉合计': float(pd.to_numeric(sub['followers'], errors='coerce').sum()),
            '曝光合计': float(pd.to_numeric(sub['views'], errors='coerce').sum()),
            '可下结论': len(s) >= min_n,
        })
    rows.sort(key=lambda r: r['效率中位数'], reverse=True)
    return rows


def efficiency_leaders(df, metric='每千涨粉', top=5, min_n=3):
    """效率榜：按每千涨粉排序，过小基数剔除。

    与「播放榜」的关键差别：这里排出来的是「少量曝光换来高转化」的内容，
    通常播放量并不高 —— 这正是播放榜永远看不到的部分。

    但效率榜有个陷阱必须显式处理：小基数内容的每千涨粉天然虚高
    （118 观看涨 5 粉 = 42/千，远高于 10,205 观看涨 98 粉 = 9.6/千，
    但它的绝对贡献只有 5%）。

    所以每条都同时给出「涨粉贡献占比」，并标记「高效率但低贡献」，
    避免把噪声当成冠军。
    """
    if df is None or len(df) == 0:
        return []
    threshold = min_views_threshold(df)
    work = df[pd.to_numeric(df['views'], errors='coerce') >= threshold].copy()
    if len(work) == 0:
        return []
    work = work[work[metric].notna()]
    if len(work) == 0:
        return []
    total_f = pd.to_numeric(df['followers'], errors='coerce').sum()
    work = work.sort_values(metric, ascending=False).head(top)
    rows = []
    for _, r in work.iterrows():
        contrib = float(r['followers']) / total_f * 100 if total_f else float('nan')
        rows.append({
            '标题': r.get('title', ''),
            '发布': r['publish_time'],
            '曝光': float(r['views']),
            '涨粉': float(r['followers']),
            '每千涨粉': float(r[metric]),
            '每千收藏': float(r.get('每千收藏', float('nan'))),
            '每千互动': float(r.get('每千互动', float('nan'))),
            '完播率': float(r.get('completion', float('nan')))
            if pd.notna(r.get('completion')) else float('nan'),
            '象限': r.get('象限判定', ''),
            '涨粉贡献占比': contrib,
            '小基数': bool(float(r['views']) < threshold * 2),
            '样本': len(df),
        })
    return rows


def overperform_check(df, group_col, metric='每千涨粉'):
    """过度表现检验：某组的绝对贡献是否超过它的样本占比。

    这是小基数陷阱的第二个防线。
    一个组 n 占 10% 却贡献 30% 涨粉，说明它真的更强；
    一个组 n 占 30% 只贡献 5% 涨粉，说明它的「高效率」只是分母小。

    group_col 必须是布尔列（如「含具体额度」）。
    返回 {True: 放大倍数, False: 放大倍数}，>1 表示过度表现。
    """
    if df is None or len(df) == 0 or group_col not in df.columns:
        return {}
    n_total = len(df)
    total_f = pd.to_numeric(df['followers'], errors='coerce').sum()
    out = {}
    for flag, sub in df.groupby(group_col):
        if len(sub) == 0:
            continue
        n_share = len(sub) / n_total
        f_share = (pd.to_numeric(sub['followers'], errors='coerce').sum() / total_f) \
            if total_f else float('nan')
        if n_share and f_share == f_share:
            out[bool(flag)] = float(f_share / n_share)
    return out


def viral_vs_buried(df, metric='每千涨粉'):
    """真爆款与被埋没内容的对照清单 —— 方法论 §四反例的候选来源。

    真爆款：高触达 × 高价值
    埋没好内容：低触达 × 高价值
    反例：高触达 × 低价值（伪爆款），说明「播放高 ≠ 内容好」
    """
    if df is None or len(df) == 0 or '象限' not in df.columns:
        return {}
    out = {}
    for key, q in [('真爆款', '高触达 × 高价值'),
                   ('伪爆款', '高触达 × 低价值'),
                   ('埋没好内容', '低触达 × 高价值'),
                   ('无效内容', '低触达 × 低价值')]:
        sub = df[df['象限'] == q]
        out[key] = sub.sort_values(metric, ascending=False)
    return out
