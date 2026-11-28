#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/concentration.py - 集中度与分组对比

集中度回答一个问题：**账号的成绩是靠少数内容打透的，还是靠整体铺量？**
这决定了下期该「复制爆款结构」还是「先修整体分发」。

两组指标：
    帕累托   Top K 内容占总量多少（曝光 / 涨粉各算一遍）
    分组对比 按标题特征分组，比较效率中位数与 P75

分组对比为什么用中位数不用均值：一条 10 倍播放的爆款会把该组均值抬高，
让「该组整体效率高」变成假象。方法论 §八 明确要求用中位数 + P75。
"""

import re

import pandas as pd

# 标题特征词典 —— 只用于给已发布内容打标分组，不用于生成标题
# 键名不带「含」前缀，渲染时统一加，避免出现「含含具体额度」这种叠词
TITLE_FEATURES = {
    '具体额度': r'\d+\s*(亿|万|w|W|k|K)?\s*(token|Token|TOKENS|积分|额度|次数|字|条)?',
    '免费': r'免费|白送|0\s*元|不要钱|免费领|免费用',
    '时间承诺': r'今天|今日|限时|限时领|马上|现在|立刻|截至',
    '身份词': r'程序员|打工人|上班族|新手|小白|学生|设计师|运营|自媒体',
    '工具名': r'GLM|智谱|Qwen|通义|混元|豆包|DeepSeek|kimi|Kimi|文心|WorkBuddy|CodeBuddy|nano|Nano|纳米|MCP|Cursor',
    '教程信号': r'教程|怎么|如何|方法|步骤|指南|教你|手把手|一键',
    '反差': r'不用|别再|原来|其实|居然|竟然|反而|不是.{0,4}而是|vs|VS|对比',
    '提问': r'[？?]|为什么|凭什么|如何|是不是|有没有',
}


def pareto(df, value_col='views', top_ks=(1, 2, 3, 5, 10)):
    """帕累托集中度：Top K 占总量比例。

    同时算两个口径，因为它们讲的是不同的故事：
        曝光占比高、涨粉占比低 = 放量内容（流量到了、价值没到）
        涨粉占比比曝光占比高 = 承接内容（少量曝光换来高转化）
    """
    if df is None or len(df) == 0:
        return {}
    work = df.copy()
    work['_v'] = pd.to_numeric(work[value_col], errors='coerce')
    work['_f'] = pd.to_numeric(work['followers'], errors='coerce')
    work = work.dropna(subset=['_v']).sort_values('_v', ascending=False)

    total_v = work['_v'].sum()
    total_f = work['_f'].sum()
    out = {'n': len(work), '总曝光': float(total_v), '总涨粉': float(total_f)}
    for k in top_ks:
        head = work.head(k)
        v = head['_v'].sum()
        f = head['_f'].sum()
        out[f'Top{k}'] = {
            '曝光占比': float(v / total_v * 100) if total_v else float('nan'),
            '涨粉占比': float(f / total_f * 100) if total_f else float('nan'),
            '条数': min(k, len(work)),
        }
    # 集中度判读：Top3 涨粉占比相对 Top3 曝光占比的放大倍数
    if 'Top3' in out:
        ev = out['Top3']['曝光占比']
        ef = out['Top3']['涨粉占比']
        out['Top3涨粉放大倍数'] = float(ef / ev) if ev and ev == ev and ev != 0 else float('nan')
    return out


def concentration_verdict(p):
    """把帕累托数字翻译成一句可用的判断（数据层结论，不下内容建议）"""
    if not p or 'Top3' not in p:
        return ''
    ev = p['Top3']['曝光占比']
    ef = p['Top3']['涨粉占比']
    n = p['n']
    if ev != ev or ef != ef:
        return ''
    parts = [f'Top3 占 {ev:.1f}% 曝光、{ef:.1f}% 涨粉']
    amp = p.get('Top3涨粉放大倍数')
    if amp == amp:
        if amp >= 1.3:
            parts.append(f'涨粉集中度是曝光集中度的 {amp:.1f} 倍 —— 头部内容不只是拿量，是账号的价值来源')
        elif amp <= 0.7:
            parts.append(f'涨粉集中度仅为曝光集中度的 {amp:.2f} 倍 —— 头部内容拿的是量，涨粉靠的是长尾')
        else:
            parts.append('涨粉集中度与曝光集中度接近 —— 头部内容的价值与曝光相当')
    if ev >= 60 and n >= 5:
        parts.append(f'集中度高（{ev:.1f}%），单条波动会直接反映到账号大盘')
    return '；'.join(parts)


def tag_titles(df, feature_col='title'):
    """给已发布标题打特征标签（一条可多标）。

    只看标题字面，不看它后来表现好不好 —— 防止「结果倒推理由」。
    """
    if df is None or len(df) == 0:
        return df
    out = df.copy()
    titles = out[feature_col].astype(str) if feature_col in out.columns else pd.Series([''] * len(out))
    for name, pattern in TITLE_FEATURES.items():
        out[name] = titles.str.contains(pattern, regex=True, na=False)
    return out


def feature_groups(df, metric='每千涨粉', min_n=3):
    """按标题特征分组比较效率。

    输出每组的 n / 效率中位数 / P75 / 涨粉合计，并标注样本是否够下结论。
    """
    if df is None or len(df) == 0:
        return []
    rows = []
    total_f = pd.to_numeric(df['followers'], errors='coerce').sum()
    for name in TITLE_FEATURES:
        for flag in (True, False):
            sub = df[df[name] == flag]
            if len(sub) == 0:
                continue
            s = pd.to_numeric(sub[metric], errors='coerce').dropna()
            if len(s) == 0:
                continue
            rows.append({
                '特征': name,
                '命中': '命中' if flag else '未命中',
                'n': len(s),
                '效率中位数': float(s.median()),
                '效率P75': float(s.quantile(0.75)),
                '涨粉合计': float(pd.to_numeric(sub['followers'], errors='coerce').sum()),
                '涨粉占比': float(pd.to_numeric(sub['followers'], errors='coerce').sum() / total_f * 100)
                if total_f else float('nan'),
                '可下结论': len(s) >= min_n,
            })
    # 只保留「命中 vs 未命中」成对出现的特征，且命中组样本够
    pairs = {}
    for r in rows:
        pairs.setdefault(r['特征'], {})[r['命中']] = r
    out = []
    for feat, d in pairs.items():
        if '命中' in d and '未命中' in d:
            hit, miss = d['命中'], d['未命中']
            out.append({
                '特征': feat,
                '命中n': hit['n'],
                '命中中位数': hit['效率中位数'],
                '命中P75': hit['效率P75'],
                '未命中n': miss['n'],
                '未命中中位数': miss['效率中位数'],
                '未命中P75': miss['效率P75'],
                '倍数': float(hit['效率中位数'] / miss['效率中位数'])
                if miss['效率中位数'] not in (0, None) and miss['效率中位数'] == miss['效率中位数']
                else float('nan'),
                '命中涨粉占比': hit['涨粉占比'],
                '可下结论': hit['n'] >= min_n and miss['n'] >= min_n,
            })
    out.sort(key=lambda r: r['倍数'] if r['倍数'] == r['倍数'] else 0, reverse=True)
    return out


def keyword_groups(df, metric='每千涨粉', min_count=2, min_n=3):
    """按标题里的具体词分组（工具名、模型名等）。

    与 feature_groups 的区别：feature 是「有无某类结构」，
    keyword 是「具体是哪个词」—— 后者能定位到具体题材。
    """
    if df is None or len(df) == 0 or 'title' not in df.columns:
        return []
    rows = []
    titles = df['title'].astype(str)
    words = set()
    for t in titles:
        for w in re.findall(r'[A-Za-z][A-Za-z0-9\.\-]{1,15}|[\u4e00-\u9fff]{2,6}', t):
            words.add(w)
    total_f = pd.to_numeric(df['followers'], errors='coerce').sum()
    for w in sorted(words):
        mask = titles.str.contains(re.escape(w), regex=True, na=False)
        sub = df[mask]
        if len(sub) < min_count:
            continue
        s = pd.to_numeric(sub[metric], errors='coerce').dropna()
        if len(s) == 0:
            continue
        rows.append({
            '关键词': w,
            'n': len(s),
            '效率中位数': float(s.median()),
            '效率P75': float(s.quantile(0.75)),
            '涨粉合计': float(pd.to_numeric(sub['followers'], errors='coerce').sum()),
            '涨粉占比': float(pd.to_numeric(sub['followers'], errors='coerce').sum() / total_f * 100)
                if total_f else float('nan'),
            '曝光合计': float(pd.to_numeric(sub['views'], errors='coerce').sum()),
            '可下结论': len(s) >= min_n,
        })
    rows.sort(key=lambda r: r['涨粉合计'], reverse=True)
    return rows
