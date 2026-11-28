#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/relations.py - 相关性检验与反直觉发现

为什么需要这一层：单看一个数说不清「为什么涨粉」。
把多个指标两两做相关，能找出「哪件事真正在驱动涨粉」。

关键在于**结论方向可能与直觉相反**，这正是最值钱的部分。
2026-10 视频号实测：
    分享量 × 关注量   r = 0.889  → 分享是涨粉最强预测因子
    完播率 × 关注转化 r = -0.076 → 完播率几乎不影响关注
    播放量 × 关注转化 r = 0.345  → 播放只是弱相关
    → 「完播率高 = 涨粉多」是错的。完播决定能不能被推出去，关注决定人家要不要留下。

两条纪律：
1. 小样本（n < 8）不报相关系数，只报「样本不足」，避免把噪声讲成规律
2. 极值点会绑架 r 值 —— 报告「剔除极值后」的结果，两组一起给
"""

import numpy as np
import pandas as pd

MIN_SAMPLE = 12
# 剔除极值后的最小样本（比原始样本低，因为剔极值本身就是在提纯）
MIN_SAMPLE_TRIMMED = 6

# 候选相关对：(指标A, 指标B, 中文名, 假设方向)
# 方向只用于「结果是否符合预期」的措辞，不用于筛选结果
PAIRS = [
    ('views', 'followers', '曝光 × 涨粉', '正'),
    ('shares', 'followers', '分享 × 涨粉', '正'),
    ('likes', 'followers', '点赞 × 涨粉', '正'),
    ('comments', 'followers', '评论 × 涨粉', '正'),
    ('saves', 'followers', '收藏 × 涨粉', '正'),
    ('completion', 'followers', '完播率 × 涨粉', '未知'),
    ('views', 'completion', '曝光 × 完播率', '未知'),
    ('shares', 'views', '分享 × 曝光', '正'),
    ('cover_ctr', 'views', '封面点击率 × 曝光', '正'),
]


def _r(a, b, min_n=MIN_SAMPLE):
    """相关系数；样本不足或方差为 0 时返回 NaN"""
    a = pd.to_numeric(a, errors='coerce')
    b = pd.to_numeric(b, errors='coerce')
    mask = a.notna() & b.notna()
    a, b = a[mask], b[mask]
    if len(a) < min_n:
        return float('nan')
    if a.std() == 0 or b.std() == 0:
        return float('nan')
    return float(np.corrcoef(a, b)[0, 1])


def _drop_outliers(df, cols):
    """剔除极值点：用 IQR 法，避免单条爆款绑架整个 r。

    注意：这里对**参与相关计算的所有列**分别剔，而不是只剔自变量 ——
    否则会出现「A 剔了极值、B 没剔」的错配样本。
    """
    work = df.copy()
    cols = [c for c in cols if c in work.columns]
    for c in cols:
        s = pd.to_numeric(work[c], errors='coerce')
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0 or pd.isna(iqr):
            continue
        work = work[(s >= q1 - 1.5 * iqr) & (s <= q3 + 1.5 * iqr)]
    return work


def _r_reliability(n, r):
    """相关系数的可靠性标记。

    小样本下 r 会剧烈波动：n=11 时两个几乎同向的指标能算出 r=0.99，
    这不是规律，是样本太少。所以必须把 n 一起给出来。
    """
    if n < MIN_SAMPLE:
        return '样本不足'
    if n < 20:
        return '偏弱（小样本波动大）'
    if r != r:
        return '无法计算'
    return '可用'


def correlation_matrix(df, pairs=None):
    """相关性矩阵：同平台内两两相关 + 剔除极值后的稳健版本。

    只在同平台内计算 —— 跨平台分母口径不同，相关性没有意义。
    """
    if df is None or len(df) == 0:
        return []
    pairs = pairs or PAIRS
    rows = []
    for pk, sub in df.groupby('platform_key'):
        n = len(sub)
        trimmed = _drop_outliers(sub, [p[0] for p in pairs] + [p[1] for p in pairs])
        for a, b, name, expect in pairs:
            if a not in sub.columns or b not in sub.columns:
                continue
            valid = pd.to_numeric(sub[a], errors='coerce').notna() & \
                pd.to_numeric(sub[b], errors='coerce').notna()
            if valid.sum() < MIN_SAMPLE:
                continue
            r = _r(sub[a], sub[b])
            rt = _r(trimmed[a], trimmed[b], min_n=MIN_SAMPLE_TRIMMED)
            if r != r and rt != rt:
                continue
            rows.append({
                'platform_key': pk,
                'platform': sub['platform'].iloc[0],
                '关系': name,
                'n': int(valid.sum()),
                'n_去极值': len(trimmed),
                'r': r,
                'r_稳健': rt,
                '极值敏感': bool(r == r and rt == rt and abs(r - rt) > 0.2),
                '可靠性': _r_reliability(int(valid.sum()), r),
                '预期方向': expect,
            })
    return rows


def interpret(r):
    """把 r 值翻译成强度描述（数据层语言，不下因果结论）"""
    if r != r:
        return '样本不足'
    a = abs(r)
    if a >= 0.7:
        s = '强'
    elif a >= 0.4:
        s = '中等'
    elif a >= 0.2:
        s = '弱'
    else:
        s = '几乎无关'
    if r < 0:
        return f'{s}负相关'
    return f'{s}正相关'


def surprising_findings(df, matrix=None):
    """找出「与直觉相反」的关系 —— 这些通常是最有指导性的。

    典型：完播率与涨粉负相关（完播决定分发，不决定关注）、
    播放量与涨粉效率弱相关（播放是分发决定的）。

    两道过滤，缺一不可：
        1. n < MIN_SAMPLE 一律不报 —— 小样本下 r 会剧烈波动，
           n=11 时两个同向指标能算出 r=0.99，那是样本少不是规律
        2. 用稳健 r（剔极值）优先 —— 避免单条爆款造出假相关
    """
    if matrix is None:
        matrix = correlation_matrix(df)
    out = []
    for row in matrix:
        n = row['n']
        if n < MIN_SAMPLE:
            continue
        r = row['r_稳健'] if row['r_稳健'] == row['r_稳健'] else row['r']
        if r != r:
            continue
        # 预期正相关但实际弱或负 → 反直觉
        if row['预期方向'] == '正' and r < 0.25:
            note = '该指标不是涨粉的主要驱动力'
            if row['极值敏感']:
                note += '（该关系对极值敏感，需更多样本确认）'
            out.append({
                'platform': row['platform'],
                '关系': row['关系'],
                'r': r,
                'n': n,
                '强度': interpret(r),
                '说明': f'「{row["关系"]}」预期为正，实际 r={r:.3f}（{interpret(r)}）—— {note}',
            })
        # 预期未知但呈强相关 → 也是信息
        elif row['预期方向'] == '未知' and abs(r) >= 0.5:
            out.append({
                'platform': row['platform'],
                '关系': row['关系'],
                'r': r,
                'n': n,
                '强度': interpret(r),
                '说明': f'「{row["关系"]}」呈{interpret(r)}（r={r:.3f}，n={n}）',
            })
    return out


def efficiency_vs_reach(df):
    """触达与效率的关系：是不是「拿到量就等于有价值」。

    做法：把平台内按曝光分成高/低两半，比较两半的效率中位数。
    比相关系数更好读，也不受极值干扰。

    样本门槛比相关系数宽松（6 条即可分组），
    因为这个比的是**分组中位数**，比 r 值稳；样本不足时用'样本不足'标记，
    而不是直接丢掉这个平台 —— 丢掉会让读者以为该平台没有结论。
    """
    if df is None or len(df) == 0:
        return []
    rows = []
    for pk, sub in df.groupby('platform_key'):
        if len(sub) < 6:
            continue
        med = sub['views'].median()
        hi = sub[sub['views'] >= med]
        lo = sub[sub['views'] < med]
        if len(hi) == 0 or len(lo) == 0:
            continue
        e_hi = pd.to_numeric(hi['每千涨粉'], errors='coerce').dropna()
        e_lo = pd.to_numeric(lo['每千涨粉'], errors='coerce').dropna()
        if len(e_hi) == 0 or len(e_lo) == 0:
            continue
        lo_med = float(e_lo.median())
        hi_med = float(e_hi.median())
        # 低曝光组效率为 0：不是「倍数无限」，而是「低曝光内容基本不转化」
        if lo_med == 0:
            ratio = float('nan')
        else:
            ratio = hi_med / lo_med
        rows.append({
            'platform_key': pk,
            'platform': sub['platform'].iloc[0],
            '高曝光组n': len(hi),
            '低曝光组n': len(lo),
            '高曝光组效率中位数': hi_med,
            '低曝光组效率中位数': lo_med,
            '倍数': ratio,
            '低曝光组零效率': lo_med == 0,
            '样本充足': len(sub) >= MIN_SAMPLE,
            '涨粉合计高曝光': float(pd.to_numeric(hi['followers'], errors='coerce').sum()),
            '涨粉合计低曝光': float(pd.to_numeric(lo['followers'], errors='coerce').sum()),
        })
    return rows


def growth_path_split(df, fans_df, platform_key='shipinhao'):
    """涨粉路径拆解：涨粉有多少来自内容本身 vs 主页访问等其它入口。

    视频号粉丝表有「新增关注」，视频表有「关注」，两者按日对齐可交叉验证。
    """
    if df is None or len(df) == 0 or fans_df is None or len(fans_df) == 0:
        return {}
    work = df.copy()
    if 'publish_time' in work.columns:
        work['日期'] = work['publish_time'].dt.date
    f = fans_df.copy()
    f['日期'] = pd.to_datetime(f['时间']).dt.date

    daily = work.groupby('日期')['followers'].sum().rename('内容带来关注')
    merged = f.set_index('日期').join(daily, how='inner')
    if len(merged) == 0:
        return {}
    total_new = pd.to_numeric(merged['新增关注'], errors='coerce').sum()
    total_content = pd.to_numeric(merged['内容带来关注'], errors='coerce').sum()
    matched_days = len(merged)
    exact = int((pd.to_numeric(merged['新增关注'], errors='coerce')
                 - pd.to_numeric(merged['内容带来关注'], errors='coerce') == 0).sum())
    return {
        '匹配天数': matched_days,
        '完全相等天数': exact,
        '新增关注合计': float(total_new),
        '内容带来关注合计': float(total_content),
        '内容占比': float(total_content / total_new * 100) if total_new else float('nan'),
        '其它入口占比': float((total_new - total_content) / total_new * 100) if total_new else float('nan'),
    }
