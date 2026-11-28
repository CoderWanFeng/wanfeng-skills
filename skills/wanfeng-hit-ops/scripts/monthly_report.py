#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monthly_report.py - 生成月度报告（数据层自动填充，判断层留人工填写）

用法：
    python monthly_report.py --root <数据根目录>                    # 当月
    python monthly_report.py --root <数据根目录> --month 2026-12    # 指定月份

产出：
    <root>/月度报告/YYYY-MM/月度报告_YYYY-MM.md    数据已填好，判断处留占位符

模板：templates/月度报告模板.md（相对本脚本 ../templates/）
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths
from analysis import pipeline
from analysis import render

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / 'templates' / '月度报告模板.md'

# 各平台在模板里的段落序号与标题
PLATFORM_SECTIONS = [
    ('bilibili', '4.1', 'B站'),
    ('wechat', '4.2', '微信公众号'),
    ('douyin', '4.3', '抖音'),
    ('xiaohongshu', '4.4', '小红书'),
    ('shipinhao', '4.5', '视频号'),
    ('kuaishou', '4.6', '快手'),
]


def fmt(n):
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return '—'
    return f'{int(round(n)):,}'


def pct(n):
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return '—'
    return f'{n:.1f}%'


def safe(n):
    try:
        return float(n)
    except (TypeError, ValueError):
        return None


# ============================================================
# 各平台数据块
# ============================================================
def block_bilibili(data):
    """B站：两个账号 × 三种口径。返回 (整体表现, 关键内容表现)"""
    lines = []
    bili = data.get('bilibili') or {}
    for acc, kinds in bili.items():
        fans = kinds.get('fans')
        rec = kinds.get('recent')
        if fans is None or len(fans) == 0:
            continue
        first, last = fans.iloc[0], fans.iloc[-1]
        days = (fans['时间'].max() - fans['时间'].min()).days + 1
        add = pd.to_numeric(fans['新增关注'], errors='coerce').sum()
        cancel = pd.to_numeric(fans['取消关注'], errors='coerce').sum()
        lines.append(f'#### {acc}（{days} 天）\n')
        lines.append('| 指标 | 本期 | 说明 |')
        lines.append('|---|---:|---|')
        lines.append(f'| 粉丝总数 | {fmt(last["粉丝总数"])} | '
                     f'期初 {fmt(first["粉丝总数"])}，净增 {fmt(last["粉丝总数"] - first["粉丝总数"])} |')
        lines.append(f'| 新增关注 | {fmt(add)} | 累计 |')
        lines.append(f'| 取消关注 | {fmt(cancel)} | 取关率 {pct(cancel / add * 100 if add else None)} |')
        if rec is not None and len(rec) > 0:
            rd = (rec['时间'].max() - rec['时间'].min()).days + 1
            lines.append(f'| 近{rd}天播放 | {fmt(pd.to_numeric(rec["播放量"], errors="coerce").sum())} | 累计 |')
            lines.append(f'| 近{rd}天净增粉 | {fmt(pd.to_numeric(rec["净增粉丝"], errors="coerce").sum())} | 累计 |')
        lines.append('')
    return '\n'.join(lines), ''


def block_wechat(data):
    """公众号：三个账号的关注与阅读"""
    lines = []
    fans = data.get('wechat_fans') or {}
    read = data.get('wechat_read') or {}
    for acc, df in fans.items():
        if df is None or len(df) == 0:
            continue
        last = df.iloc[-1]
        days = (df['时间'].max() - df['时间'].min()).days + 1
        lines.append(f'#### {acc}（{days} 天）\n')
        lines.append('| 指标 | 本期 | 说明 |')
        lines.append('|---|---:|---|')
        lines.append(f'| 累积关注 | {fmt(last["累积关注人数"])} | 截至 {last["时间"].date()} |')
        net = pd.to_numeric(df['净增关注人数'], errors='coerce')
        lines.append(f'| 区间净增关注 | {fmt(net.sum())} | 日均 {net.sum() / max(len(df), 1):.1f} |')
        rd = read.get(acc)
        if rd is not None and len(rd) > 0:
            lines.append(f'| 区间总阅读 | {fmt(rd["阅读人数"].sum())} | '
                         f'日均 {fmt(rd.groupby("日期")["阅读人数"].sum().mean())} |')
        lines.append('')
    return '\n'.join(lines), ''


def block_douyin(data):
    lines = []
    df = data.get('douyin')
    dyf = data.get('douyin_fans')
    if df is None or len(df) == 0:
        return '', ''
    play_col = '总播放量' if '总播放量' in df.columns else '播放量'
    total = pd.to_numeric(df[play_col], errors='coerce').sum()
    days = (df['日期'].max() - df['日期'].min()).days + 1
    lines.append(f'#### 程序员晚枫（{days} 天）\n')
    lines.append('| 指标 | 本期 | 说明 |')
    lines.append('|---|---:|---|')
    lines.append(f'| 总播放 | {fmt(total)} | 日均 {fmt(total / len(df))} |')
    if '投稿量' in df.columns:
        lines.append(f'| 投稿量 | {fmt(pd.to_numeric(df["投稿量"], errors="coerce").sum())} | 条 |')
    for c, label in [('5秒完播率', '5秒完播率'), ('2秒跳出率', '2秒跳出率'),
                     ('封面点击率', '封面点击率')]:
        if c in df.columns:
            v = pd.to_numeric(df[c], errors='coerce')
            lines.append(f'| {label} | {pct(v.mean())} | 均值 |')
    if dyf is not None and len(dyf) > 0:
        f0, f1 = dyf.iloc[0], dyf.iloc[-1]
        lines.append(f'| 粉丝总数 | {fmt(f1["总粉丝量"])} | '
                     f'期初 {fmt(f0["总粉丝量"])}，净增 {fmt(f1["总粉丝量"] - f0["总粉丝量"])} |')
    lines.append('')

    posts = data.get('douyin_posts')
    top = []
    if posts is not None and len(posts) > 0:
        # 作品列表导出是全量历史（750条，最早到2022年），只取本期窗口内的
        window = posts[posts['发布时间'] >= df['日期'].min()]
        if len(window) == 0:
            window = posts
        top.append('| 发布时间 | 播放 | 完播率 | 涨粉 | 标题 |')
        top.append('|---|---:|---:|---:|---|')
        for _, r in window.nlargest(10, '播放量').iterrows():
            t = str(r['作品名称']).split('#')[0].strip()[:28]
            top.append(f'| {r["发布时间"].date()} | {fmt(r["播放量"])} | '
                       f'{pct(safe(r.get("完播率")))} | {fmt(r.get("粉丝增量"))} | {t} |')
        top.append('')
        top.append(f'> 本期发布 {len(window)} 条，播放合计 '
                   f'{fmt(pd.to_numeric(window["播放量"], errors="coerce").sum())}')
    return '\n'.join(lines), '\n'.join(top)


def block_xiaohongshu(data):
    lines = []
    posts = data.get('xiaohongshu')
    watch = data.get('xhs_watch')
    if posts is None or len(posts) == 0:
        return '', ''
    lines.append(f'#### 程序员晚枫（本期 {len(posts)} 篇笔记）\n')
    lines.append('| 指标 | 本期 | 说明 |')
    lines.append('|---|---:|---|')
    for col, label in [('曝光', '曝光'), ('观看量', '观看'), ('点赞', '点赞'),
                       ('评论', '评论'), ('收藏', '收藏'), ('涨粉', '涨粉')]:
        if col in posts.columns:
            v = pd.to_numeric(posts[col], errors='coerce').sum()
            lines.append(f'| {label} | {fmt(v)} | 合计 |')
    if '观看量' in posts.columns:
        med = pd.to_numeric(posts['观看量'], errors='coerce').median()
        lines.append(f'| 观看中位数 | {fmt(med)} | 均值受爆款拉高 |')
    if watch:
        s = watch.get('summary', {})
        if s:
            lines.append(f'| 曝光（账号30天） | {fmt(s.get("曝光"))} | '
                         f'环比 {s.get("曝光环比(%)", "—")}% |')
            lines.append(f'| 观看（账号30天） | {fmt(s.get("观看"))} | '
                         f'环比 {s.get("观看环比(%)", "—")}% |')
    lines.append('')
    top = ['| 观看 | 点赞 | 收藏 | 涨粉 | 标题 |',
           '|---:|---:|---:|---:|---|']
    for _, r in posts.nlargest(10, '观看量').iterrows():
        t = str(r['笔记标题']).split('#')[0].strip()[:28]
        top.append(f'| {fmt(r["观看量"])} | {fmt(r["点赞"])} | {fmt(r["收藏"])} | '
                   f'{fmt(r["涨粉"])} | {t} |')
    return '\n'.join(lines), '\n'.join(top)


def block_shipinhao(data):
    lines = []
    vf = data.get('shipinhao_fans')
    vv = data.get('shipinhao_video')
    if vf is None or len(vf) == 0:
        return '', ''
    first, last = vf.iloc[0], vf.iloc[-1]
    days = (vf['时间'].max() - vf['时间'].min()).days + 1
    lines.append(f'#### 程序员晚枫（{days} 天）\n')
    lines.append('| 指标 | 本期 | 说明 |')
    lines.append('|---|---:|---|')
    lines.append(f'| 关注者总数 | {fmt(last["关注者总数"])} | '
                 f'期初 {fmt(first["关注者总数"])}，净增 {fmt(last["关注者总数"] - first["关注者总数"])} |')
    if vv is not None and len(vv) > 0:
        play = pd.to_numeric(vv['播放'], errors='coerce')
        lines.append(f'| 总播放 | {fmt(play.sum())} | 日均 {fmt(play.mean())} |')
        for col, label in [('分享', '分享'), ('喜欢', '喜欢'), ('评论', '评论'),
                           ('关注', '关注')]:
            if col in vv.columns:
                lines.append(f'| {label} | {fmt(pd.to_numeric(vv[col], errors="coerce").sum())} | 合计 |')
        if play.sum():
            follow = pd.to_numeric(vv['关注'], errors='coerce').sum()
            lines.append(f'| 每千播放关注 | {follow / play.sum() * 1000:.2f} | 转化效率 |')
    lines.append('')
    posts = data.get('shipinhao_posts')
    top = []
    if posts is not None and len(posts) > 0:
        top.append('| 发布日 | 播放 | 完播率 | 涨粉 | 标题 |')
        top.append('|---|---:|---:|---:|---|')
        for _, r in posts.nlargest(5, '播放量').iterrows():
            t = str(r['标题']).split('#')[0].strip()[:28]
            top.append(f'| {r["发布时间"].date()} | {fmt(r["播放量"])} | '
                       f'{pct(safe(r["完播率"]))} | {fmt(r["关注量"])} | {t} |')
    return '\n'.join(lines), '\n'.join(top)


def block_kuaishou(data):
    df = data.get('kuaishou')
    if df is None or len(df) == 0:
        return '', ''
    days = (df['日期'].max() - df['日期'].min()).days + 1
    lines = [f'#### 程序员晚枫（{days} 天）\n']
    lines.append('| 指标 | 本期 | 说明 |')
    lines.append('|---|---:|---|')
    lines.append(f'| 总播放 | {fmt(pd.to_numeric(df["播放量"], errors="coerce").sum())} | '
                 f'日均 {fmt(pd.to_numeric(df["播放量"], errors="coerce").mean())} |')
    lines.append(f'| 净增粉丝 | {fmt(pd.to_numeric(df["净增粉丝量"], errors="coerce").sum())} | 区间合计 |')
    lines.append(f'| 发布作品 | {fmt(pd.to_numeric(df["作品量"], errors="coerce").sum())} | 条 |')
    lines.append(f'| 平均完播率 | {pct(pd.to_numeric(df["完播率"], errors="coerce").mean())} | 均值 |')
    lines.append('')
    return '\n'.join(lines), ''


BLOCK_FUNCS = {
    'bilibili': block_bilibili,
    'wechat': block_wechat,
    'douyin': block_douyin,
    'xiaohongshu': block_xiaohongshu,
    'shipinhao': block_shipinhao,
    'kuaishou': block_kuaishou,
}


# ============================================================
# 报告组装
# ============================================================
def data_file_list():
    """列出本期用到的归档文件"""
    lines = ['| 平台 | 文件 | 归档路径 |', '|---|---|---|']
    p = _paths.paths()
    data_dir = p.data
    if not data_dir.exists():
        return '\n'.join(lines)
    for plat_dir in sorted(data_dir.iterdir()):
        if not plat_dir.is_dir():
            continue
        for acc_dir in sorted(plat_dir.iterdir()):
            if not acc_dir.is_dir():
                continue
            snaps = [d for d in acc_dir.iterdir()
                     if d.is_dir() and d.name.isdigit() and len(d.name) == 6]
            if not snaps:
                continue
            latest = max(snaps, key=lambda d: d.name)
            for f in sorted(latest.iterdir()):
                if f.is_file() and not f.name.startswith('.'):
                    rel = f.relative_to(p.root)
                    lines.append(f'| {plat_dir.name} | `{f.name}` | `{rel.parent}` |')
    return '\n'.join(lines)


def fan_table(data):
    """粉丝总览表（自动填充）"""
    rows = []
    bili = data.get('bilibili') or {}
    for acc, kinds in bili.items():
        fans = kinds.get('fans')
        hist = kinds.get('history')
        if fans is not None and len(fans) > 0:
            last = fans.iloc[-1]
            rows.append(['B站', acc, int(last['粉丝总数']), str(last['时间'].date()), '关注数口径'])
        elif hist is not None and len(hist) > 0:
            last = hist.iloc[-1]
            rows.append(['B站', acc, int(last['累计粉丝']), str(last['时间'].date()), '历史累计口径'])
    for acc, df in (data.get('wechat_fans') or {}).items():
        if df is not None and len(df) > 0:
            last = df.iloc[-1]
            rows.append(['微信公众号', acc, int(last['累积关注人数']),
                         str(last['时间'].date()), '累积关注'])
    vf = data.get('shipinhao_fans')
    if vf is not None and len(vf) > 0:
        rows.append(['视频号', '程序员晚枫', int(vf.iloc[-1]['关注者总数']),
                     str(vf.iloc[-1]['时间'].date()), '关注者总数'])
    dyf = data.get('douyin_fans')
    if dyf is not None and len(dyf) > 0:
        rows.append(['抖音', '程序员晚枫', int(dyf.iloc[-1]['总粉丝量']),
                     str(dyf.iloc[-1]['日期'].date()), '总粉丝量'])
    rows.sort(key=lambda x: x[2], reverse=True)
    lines = ['| 排名 | 平台 | 账号 | 粉丝数 | 数据日期 | 数据口径 |',
             '|---|---|---|---:|---|---|']
    for i, r in enumerate(rows, 1):
        lines.append(f'| {i} | {r[0]} | {r[1]} | {fmt(r[2])} | {r[3]} | {r[4]} |')
    return '\n'.join(lines), rows


def fan_missing_note(data, rows, scope_rows):
    """列出有数据但拿不到粉丝总数的账号，避免读者以为漏填"""
    have = {(r[0], r[1]) for r in rows}
    miss = sorted({(r[0], r[1]) for r in scope_rows} - have)
    if not miss:
        return ''
    txt = '、'.join(f'{p}·{a}' for p, a in miss)
    return (f'\n> ⚠ {txt} 本期未取得粉丝总数数据，未列入上表；'
            f'其涨粉情况见对应平台的「整体表现」小节。\n')


def scope_table(data):
    """数据范围与可信度表：自动从各平台归档文件推导统计范围与来源

    返回 (markdown, rows)，rows 每项为 (平台, 账号, 起始日, 截止日, 前缀, 来源, 能支持的结论)
    """
    rows = []
    bili = data.get('bilibili') or {}
    for acc, kinds in bili.items():
        for kind, label in [('fans', '关注趋势'), ('recent', '播放日增量'),
                            ('history', '历史累计')]:
            df = kinds.get(kind)
            if df is None or len(df) == 0:
                continue
            s = df['时间'].min().date().isoformat()
            e = df['时间'].max().date().isoformat()
            rows.append(['B站', acc, s, e, '',
                         f'后台原始导出（{label}口径）',
                         '日趋势、总量、粉丝净增'])
    for acc, df in (data.get('wechat_fans') or {}).items():
        if df is None or len(df) == 0:
            continue
        s = df['时间'].min().date().isoformat()
        e = df['时间'].max().date().isoformat()
        rd = (data.get('wechat_read') or {}).get(acc)
        extra = '、阅读趋势' if rd is not None and len(rd) else ''
        rows.append(['微信公众号', acc, s, e, '',
                     f'后台原始导出（关注趋势{extra}）',
                     '关注净增、阅读量、渠道分布'])
    vf = data.get('shipinhao_fans')
    if vf is not None and len(vf) > 0:
        s = vf['时间'].min().date().isoformat()
        e = vf['时间'].max().date().isoformat()
        rows.append(['视频号', '程序员晚枫', s, e, '',
                     '后台原始CSV（关注者增长 + 视频详情）',
                     '日趋势、总量、峰值、关注转化'])
    dy = data.get('douyin')
    if dy is not None and len(dy) > 0:
        s = dy['日期'].min().date().isoformat()
        e = dy['日期'].max().date().isoformat()
        rows.append(['抖音', '程序员晚枫', s, e, '',
                     '后台原始Excel（粉丝全量指标 + 短视频全量指标）',
                     '账号汇总、粉丝净增、完播与跳出率'])
    xh = data.get('xiaohongshu')
    if xh is not None and len(xh) > 0:
        pub = pd.to_datetime(
            xh['首次发布时间'].astype(str)
              .str.replace('年', '-', regex=False)
              .str.replace('月', '-', regex=False)
              .str.replace('日', ' ', regex=False)
              .str.replace(r'(\d+)时(\d+)分(\d+)秒',
                           lambda m: f'{m.group(1)}:{m.group(2)}:{m.group(3)}',
                           regex=True),
              errors='coerce')
        s = pub.min().date().isoformat() if pub.notna().any() else '—'
        e = pub.max().date().isoformat() if pub.notna().any() else '—'
        rows.append(['小红书', '程序员晚枫', s, e, '发布筛选 ',
                     '后台原始Excel（笔记明细 + 近30日系列）',
                     '本期笔记累计表现；不等于账号30天总流量'])
    ks = data.get('kuaishou')
    if ks is not None and len(ks) > 0:
        s = ks['日期'].min().date().isoformat()
        e = ks['日期'].max().date().isoformat()
        rows.append(['快手', '程序员晚枫', s, e, '',
                     '后台原始Excel（帐号数据分析明细表）',
                     '日播放、完播率、净增粉丝'])
    lines = ['| 平台·账号 | 本期统计范围 | 数据来源与保存状态 | 能支持的结论 |',
             '|---|---|---|---|']
    for plat, acc, s, e, prefix, src, concl in rows:
        lines.append(f'| {plat}·{acc} | {prefix}{s} ~ {e} | '
                     f'{src}，已归档至 `账号数据/` | {concl} |')
    return '\n'.join(lines), rows


def build(template, data, month, result=None):
    """把数据层填进模板。

    result: analysis.pipeline.run() 的输出。提供时，判断层会用计算层的
            结构化发现填充；不提供时保留占位符（供人工填写）。
    """
    tpl = template

    # 头部占位符
    tbl, rows = fan_table(data)
    scope_md, scope_rows = scope_table(data)
    # 平台数按「有数据的平台·账号」计，粉丝总览缺的平台（如小红书、快手没粉丝总数）
    # 也在范围内，否则标题会漏掉实际覆盖的平台
    covered = {(r[0], r[1]) for r in rows} | {(r[0], r[1]) for r in scope_rows}
    n_platforms = len({p for p, _ in covered})
    accounts = '、'.join(sorted({f'{p}·{a}' for p, a in covered}))

    # 统计周期 = 报告月份本身；各数据源的实际覆盖区间在「数据范围」表里逐条列明
    ends = [r[3] for r in scope_rows if r[3] != '—']
    end_date = max(ends) if ends else '—'
    start = f'{month}-01'
    span = max(1, (pd.Timestamp(end_date) - pd.Timestamp(start)).days + 1) \
        if ends else '—'

    tpl = tpl.replace('{平台数}', str(n_platforms))
    tpl = tpl.replace('{YYYY-MM}', month)
    tpl = tpl.replace('{YYYY-MM-DD}', datetime.now().strftime('%Y-%m-%d'))
    tpl = tpl.replace('{账号清单}', accounts)
    tpl = tpl.replace('{数据截止日}', end_date)
    tpl = tpl.replace('{开始日}', start)
    tpl = tpl.replace('{截止日}', end_date)
    # 只替换统计周期里的 {N}，避免污染「{N} 个运营问题」这类占位
    tpl = tpl.replace('，{N} 天', f'，{span} 天')

    # 一、结论摘要：用计算层的发现填充
    if result:
        tpl = re.sub(r'## 一、结论摘要\n\n>.*?\n\n---\n',
                     render.summary_section(result) + '\n', tpl, flags=re.S)

    # 粉丝总览表
    tpl = re.sub(r'## 二、粉丝总览\n\n<!--.*?-->\n\n\| 排名.*?\n\n',
                 '## 二、粉丝总览\n\n' + tbl + '\n'
                 + fan_missing_note(data, rows, scope_rows) + '\n',
                 tpl, flags=re.S)

    # 统一限制：自动列出本期所有会影响解读的口径限制
    limits = render.limitations_block(result, scope_rows)
    tpl = re.sub(r'\*\*统一限制：\*\*\n\n- \{列出本期所有口径限制[^}]*\}',
                 '**统一限制：**\n\n' + limits,
                 tpl)

    # 各平台段落：模板里若有 4.x 小节就替换其内容，否则整段追加
    for key, num, name in PLATFORM_SECTIONS:
        overall, top = BLOCK_FUNCS[key](data)
        if not overall.strip():
            continue

        # 计算层有该平台的内容级数据 → 填效率表与发现；否则留空表让人工补
        judged = struct = counter = facts = ''
        eff_table = top
        has_content_data = False
        if result:
            judged, struct = render.platform_findings_block(result, key, name)
            counter = render.counterexample_block(result, key, name)
            facts = render.data_facts_block(result, key, name, overall=overall)
            tbl_eff = render.efficiency_table(result, key)
            if tbl_eff:
                eff_table = tbl_eff
                has_content_data = True

        if eff_table and eff_table.strip():
            key_contents = eff_table + '\n'
        elif has_content_data or not result:
            key_contents = ('| 内容 | 播放/观看 | 互动 | 涨粉 | 转化率 |\n'
                            '|---|---:|---:|---:|---:|\n'
                            '| {标题} | {值} | {值} | {值} | {值} |\n')
        else:
            # 该平台没有单作品数据：明确写出「本期未取得」，不留空占位符
            key_contents = ('> **本期未取得单作品明细**，无法列出内容级表现。\n'
                            '> 需要的字段：'
                            + ('单篇 `read_subscribe_user`（阅读后关注人数）、`read_user_source`'
                               if key == 'wechat' else
                               '单稿播放/涨粉/互动明细')
                            + '。补齐方式与影响见第七章。\n')

        # 判断层：有发现就用发现填；没有发现时，
        # 若该平台本就无内容级数据 → 写明原因（不留占位符）
        # 若该平台有数据但计算层没产出发现 → 留占位符给人工
        no_content = (not has_content_data) and result is not None

        if judged.strip():
            judge_block = judged
        elif no_content:
            judge_block = ('**分析判断：** 本平台本期只有账号级聚合数据，'
                           '可做的判断限于粉丝净增与取关率；'
                           '内容级判断（哪类内容更涨粉）本期无法给出。')
        else:
            judge_block = ('**分析判断（置信度：{高/中/低}）：** '
                           '{这段数字说明了什么问题、可能的原因、下一步}')

        if struct.strip():
            struct_block = struct
        elif no_content:
            struct_block = ('- 本平台本期只有账号级聚合数据（粉丝趋势 / 日趋势），'
                            '无单作品明细，因此**无法做内容级结构拆解**')
        else:
            struct_block = '- {发现1，带数据}\n- {发现2，带数据}'

        if facts.strip():
            facts_block = facts
        else:
            facts_block = '**数据事实：** {只写数字与倍数关系，不写判断}'

        if counter.strip():
            counter_block = counter
        elif no_content:
            counter_block = ('**反例（同样重要）：** 本期无单作品明细，'
                             '无法给出内容级反例；'
                             '账号级反例见「分析判断」中的留存与效率数据')
        else:
            counter_block = ('**反例（同样重要）：** '
                             '{表现不如预期但值得记住的案例，以及原因}')

        body = (f'### 整体表现\n\n{overall}\n\n'
                f'{facts_block}\n\n'
                f'### 分析判断\n\n{judge_block}\n\n'
                f'### 结构拆解\n\n{struct_block}\n\n'
                f'### 关键内容表现\n\n{key_contents}\n\n'
                f'{counter_block}\n')
        # 平台小节标题里的「一句话判断」：用该平台最强的一条发现
        # 缺口类不适合当标题（那是问题不是判断）
        headline = '{一句话判断}'
        if result:
            pf = [f for f in result.get('by_platform', {}).get(name, [])
                  if f.topic != '缺口']
            if pf:
                headline = pf[0].phenomenon
            else:
                gap = [f for f in result.get('by_platform', {}).get(name, [])
                       if f.topic == '缺口']
                if gap:
                    headline = f'{name}本期仅有账号级数据，无法做内容级归因'
        pat = re.compile(r'## ' + re.escape(num) + r' [^\n]*\n.*?\n---\n\n## 五、', re.S)
        section = f'## {num} {name}：{headline}\n\n{body}\n---\n\n## 五、'
        if pat.search(tpl):
            tpl = pat.sub(section, tpl, count=1)
        else:
            # 模板没有该小节，插到「四、单平台分析」之后，按平台序号顺序排列
            insert = f'## {num} {name}：{headline}\n\n{body}'
            anchor = re.search(r'## ' + re.escape(num) + r' [^\n]*\n', tpl)
            if anchor:
                tpl = tpl[:anchor.start()] + insert + tpl[anchor.start():]
            else:
                tpl = tpl.replace('\n---\n\n## 五、', '\n\n' + insert + '---\n\n## 五、')

    # 五、跨平台综合：整章替换
    if result:
        tpl = re.sub(r'## 五、跨平台综合分析.*?\n---\n\n## 六、',
                     render.cross_platform_section(result) + '\n## 六、',
                     tpl, flags=re.S)

    # 六、下期行动：候选验证方向 + 数据侧必做 + 明确不做
    if result:
        tpl = re.sub(r'### 验证方向（\{N\} 个样本名额，控制变量）\n\n'
                     r'\| 待验证的编码方向.*?\n\n',
                     '### 验证方向（候选，来自计算层发现）\n\n'
                     + render.experiment_section(result) + '\n\n',
                     tpl, flags=re.S)
        tpl = re.sub(r'### 必做事项\n\n.*?\n\n### 明确不做',
                     '### 必做事项\n\n' + render.todo_section(result) + '\n\n### 明确不做',
                     tpl, flags=re.S)
        tpl = re.sub(r'### 明确不做\n\n- \{事项\} —— \{原因\}',
                     '### 明确不做\n\n' + render.not_do_section(result),
                     tpl)

    # 七、数据缺口表 + 置信度分级
    if result:
        tpl = re.sub(r'## 七、数据缺口与下一步采集\n\n\| 缺口.*?\n\n',
                     '## 七、数据缺口与下一步采集\n\n' + render.gap_section(result) + '\n\n',
                     tpl, flags=re.S)
        tpl = re.sub(r'### 结论置信度\n\n.*?(?=\n---)',
                     '### 结论置信度\n\n' + render.confidence_section(result),
                     tpl, flags=re.S)

    # 附录数据文件清单
    tpl = re.sub(r'## 附录：本期数据文件清单\n\n\|.*?\n\n',
                 '## 附录：本期数据文件清单\n\n' + data_file_list() + '\n\n',
                 tpl, flags=re.S)

    # 采集说明
    if result:
        tpl = re.sub(r'\*\*采集说明：\*\* \{本期数据是怎么来的、有什么限制\}',
                     '**采集说明：**\n\n' + render.collection_note(result, scope_rows),
                     tpl)

    # 数据范围与可信度表
    tpl = re.sub(r'## 三、数据范围与可信度\n\n>.*?\n\n\| 平台·账号.*?\n\n',
                 '## 三、数据范围与可信度\n\n' + scope_md + '\n\n',
                 tpl, flags=re.S)

    # 本期缺口：从计算层的缺口发现自动填
    if result:
        gap_lines = []
        for f in result.get('findings', []):
            if f.topic == '缺口':
                gap_lines.append(f'- **{f.platform}** —— {f.metric}未取得；'
                                 f'{f.judgment.replace("影响：", "")}')
        if gap_lines:
            tpl = re.sub(r'\*\*本期缺口：\*\*\n\n- \{账号或平台\} —— \{未取得的原因与影响\}',
                         '**本期缺口：**\n\n' + '\n'.join(gap_lines),
                         tpl)
    return tpl


def main(argv=None):
    ap = argparse.ArgumentParser(description='生成月度报告（数据层自动填、判断层留空）')
    ap.add_argument('--month', default=None, help='报告月份 YYYY-MM，默认当前月')
    _paths.add_root_arg(ap)
    args = ap.parse_args(argv)

    p = _paths.init(root=args.root)
    month = args.month or datetime.now().strftime('%Y-%m')

    print('加载数据...')
    from parse_data import main as parse_main
    data = parse_main()

    if not TEMPLATE.exists():
        print(f'模板不存在：{TEMPLATE}')
        return

    template = TEMPLATE.read_text(encoding='utf-8')

    # 跑计算层：把原始数据变成结构化发现
    print('跑分析计算层...')
    result = pipeline.run(data, month=month)
    n_findings = len(result.get('findings', []))
    print(f'  内容级样本 {len(result.get("unified", []))} 条，'
          f'生成发现 {n_findings} 条')
    if result.get('window_note'):
        print(f'  {result["window_note"]}')

    md = build(template, data, month, result=result)

    out_dir = p.month_dir(month)
    out = out_dir / f'月度报告_{month}.md'
    out.write_text(md, encoding='utf-8')
    print(f'报告已生成：{out}')
    if n_findings:
        print('提示：结论摘要/分析判断/结构拆解/反例已由计算层自动填入；'
              '第六章「下期行动」与跨平台定性判断仍需人工补充')
    else:
        print('提示：未生成可支撑的发现（数据不足）；花括号占位处需人工填写')


if __name__ == '__main__':
    main()
