#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classify.py - 把「临时文件夹/」里新下载的原始文件归类到「账号数据/<平台>/<账号>/<YYMMDD>/」

用法：
    python classify.py --root <数据根目录>            # 只预览归类方案，不移动
    python classify.py --root <数据根目录> --apply    # 按方案执行移动

判定方式（对每个候选账号打分，取唯一最高分）：
    1. 粉丝数指纹   —— 候选文件的粉丝末值与该账号归档数据的粉丝末值比对（+100）
    2. 净增一致性   —— 同一时间窗内，候选文件的净增与该账号归档数据的净增是否吻合（+90）
    3. 整表数值     —— 无日期列的小表（渠道分布/文章排行）逐行比对（+85）
    4. 内容重合     —— 稿件标题 / 内容文本与该账号归档文件的重合（+80）
    5. 字面账号名   —— 文件名或内容里直接出现账号名（+60）
    6. 量级包含     —— 候选文件里的单条播放量是否落在该账号当日总播放量之下（+45）

得分不够（<45）或多个账号并列（次高分 ≥ 最高分 80%）时，文件留在原地并说明原因，不猜。
**归错账号比不归更危险**——错误会被后续所有脚本当成事实。
"""

import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths

# 平台关键词（文件名 / 表头里出现即视为该平台）
PLATFORM_HINTS = {
    'bilibili': ['b站', 'bilibili', '哔哩', '花火', '创作中心', '稿件', '投币', '弹幕'],
    'douyin': ['抖音', 'douyin', '投稿量', '完播率', '跳出率'],
    'kuaishou': ['快手', 'kuaishou', '帐号数据分析'],
    'shipinhao': ['视频号', 'shipinhao', '视频详情'],
    'wechat': ['公众号', 'wechat', '订阅号', '服务号', 'user_analysis', 'tendency',
             '阅读人数', '搜一搜', '推荐'],
    'xiaohongshu': ['小红书', 'xiaohongshu', '笔记标题', '近30日', '封面点击率'],
}

# 内容里出现即锁定平台
STRONG_PLATFORM = {
    'bilibili': ['游客播放占比', '粉丝观看率', '投币量', '空间访客', '净增粉丝'],
    'douyin': ['投稿量', '2秒跳出率', '主页访问量'],
    'kuaishou': ['作品量', '完播率'],
    'shipinhao': ['视频号', '关注者总数'],
    'wechat': ['阅读人数', '累计关注', '累积关注人数', '新增关注人数'],
    'xiaohongshu': ['笔记标题', '观看量', '涨粉', '首次发布时间'],
}

# 平台 key → 账号数据/ 下目录名前缀
PLATFORM_PREFIX = {
    'bilibili': ['bilibili', 'b站', '哔哩'],
    'wechat': ['wechat', '公众号'],
    'douyin': ['douyin', '抖音'],
    'shipinhao': ['shipinhao', '视频号'],
    'xiaohongshu': ['xiaohongshu', '小红书'],
    'kuaishou': ['kuaishou', '快手'],
}


def read_table(p):
    if p.suffix.lower() == '.csv':
        for enc in ('utf-8-sig', 'gbk', 'utf-8'):
            try:
                return pd.read_csv(p, encoding=enc)
            except Exception:
                continue
        return None
    if p.suffix.lower() in ('.xlsx', '.xls'):
        for hdr in (0, 1):
            try:
                return pd.read_excel(p, header=hdr)
            except Exception:
                continue
    return None


def to_num(v):
    s = str(v).strip().replace(',', '')
    try:
        if '万' in s:
            return float(s.replace('万', '')) * 10000
        return float(s)
    except Exception:
        return None


def parse_dates(df, col):
    """把各种日期写法转成 datetime 序列"""
    s = df[col].astype(str)
    s = s.str.replace('年', '-').str.replace('月', '-').str.replace('日', ' ')
    return pd.to_datetime(s, errors='coerce')


def body_rows(df):
    """取掉「累计 / 历史累计」这类汇总行，只留日期行"""
    if '时间' not in df.columns:
        return df
    mask = df['时间'].astype(str).str.match(r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}')
    return df[mask]


def read_wechat_tendency(p):
    """公众号 tendency_*.xls 是真 xls，多列块布局，取 日期/渠道/阅读人数 三列"""
    try:
        sheets = pd.read_excel(p, sheet_name=None, engine='xlrd')
    except Exception:
        return None
    for _, df in sheets.items():
        if df.shape[1] < 4:
            continue
        cols = df.iloc[:, 1:4].copy()
        cols.columns = ['日期', '渠道', '阅读人数']
        cols['日期'] = pd.to_datetime(cols['日期'], errors='coerce')
        cols = cols.dropna(subset=['日期'])
        if len(cols):
            return cols
    return None


# ============================================================
# 各账号的归档指纹
# ============================================================
def account_fingerprints(plat, acc):
    """读该账号所有归档文件，提取可比对特征"""
    acc_dir = _paths.paths().data / plat / acc
    fps = {
        'fan_ends': [],      # 各文件里的粉丝末值
        'net_series': [],    # (日期, 净增) 序列
        'play_series': [],   # (日期, 当日总播放) 序列
        'titles': set(),     # 内容里的标题/文本
        'value_rows': [],    # 整表行（用于渠道分布/文章排行这类无日期表的比对）
        'fans_path': acc_dir,
    }
    if not acc_dir.exists():
        return fps
    for f in sorted(acc_dir.rglob('*.csv')) + sorted(acc_dir.rglob('*.xlsx')):
        df = read_table(f)
        if df is None:
            continue
        body = body_rows(df)
        fan_col = next((c for c in ['粉丝总数', '累计粉丝', '累积关注人数', '累计关注',
                                    '总粉丝量', '关注者总数'] if c in df.columns), None)
        if fan_col:
            v = pd.to_numeric(body[fan_col], errors='coerce').dropna()
            if len(v):
                fps['fan_ends'].append(int(v.iloc[-1]))
        net_col = next((c for c in ['净增粉丝', '净增关注', '粉丝净增'] if c in df.columns), None)
        date_col = '时间' if '时间' in df.columns else ('日期' if '日期' in df.columns else None)
        if net_col and date_col:
            d = pd.to_datetime(body[date_col], errors='coerce')
            ser = pd.DataFrame({'d': d, 'v': pd.to_numeric(body[net_col], errors='coerce')}) \
                .dropna()
            if len(ser):
                fps['net_series'].append((ser['d'], ser['v']))
        play_col = next((c for c in ['播放量', '总播放量'] if c in df.columns), None)
        if play_col and date_col:
            d = pd.to_datetime(body[date_col], errors='coerce')
            ser = pd.DataFrame({'d': d, 'v': pd.to_numeric(body[play_col], errors='coerce')}) \
                .dropna()
            if len(ser):
                fps['play_series'].append((ser['d'], ser['v']))
        for col in ['视频标题', '标题', '笔记标题']:
            if col in df.columns:
                fps['titles'].update(df[col].astype(str).tolist())
        # 无日期列的小表（渠道分布/文章排行）用整表行做指纹
        if '时间' not in df.columns and '日期' not in df.columns and len(df) <= 60:
            fps['value_rows'].append({tuple(r) for r in df.astype(str).values.tolist()})
    return fps


def score_candidate(df, path, fps, plat, acc):
    """给候选账号打分，返回 (分数, 依据列表)"""
    score, why = 0, []
    body = body_rows(df) if df is not None else None

    # 1. 粉丝末值精确匹配（+100）
    if df is not None and fps['fan_ends']:
        fan_col = next((c for c in ['粉丝总数', '累计粉丝', '累积关注人数', '累计关注',
                                    '总粉丝量', '关注者总数'] if c in df.columns), None)
        if fan_col:
            v = pd.to_numeric(body[fan_col], errors='coerce').dropna()
            if len(v):
                end = int(v.iloc[-1])
                if end in fps['fan_ends']:
                    score += 100
                    why.append(f'粉丝末值 {end:,} 精确命中该账号归档数据')

    # 2. 净增一致性（同窗口内净增吻合）（+90 / +60）
    if df is not None and fps['net_series']:
        net_col = next((c for c in ['净增粉丝', '净增关注', '粉丝净增'] if c in df.columns), None)
        date_col = '时间' if '时间' in df.columns else ('日期' if '日期' in df.columns else None)
        if net_col and date_col:
            d = pd.to_datetime(body[date_col], errors='coerce')
            cand = pd.DataFrame({'d': d, 'v': pd.to_numeric(body[net_col], errors='coerce')}) \
                .dropna().set_index('d')['v']
            if len(cand):
                for sd, sv in fps['net_series']:
                    common = cand.index.intersection(sd.index)
                    if len(common) < 10:
                        continue
                    a = cand.loc[common].astype(float)
                    b = sv.loc[common].astype(float)
                    if (a == b).mean() >= 0.95:
                        score += 90
                        why.append(f'净增序列在 {len(common)} 天上与该账号完全一致')
                        break
                    if abs(a.sum() - b.sum()) <= max(5, abs(b.sum()) * 0.02):
                        score += 60
                        why.append(f'净增合计与该账号接近（{a.sum():,.0f} vs {b.sum():,.0f}）')
                        break

    # 3. 整表数值逐行吻合（+85）
    if df is not None and fps['value_rows']:
        cand_rows = {tuple(r) for r in df.astype(str).values.tolist()}
        for ref_rows in fps['value_rows']:
            common = cand_rows & ref_rows
            if len(common) >= 3 and len(common) / len(cand_rows) >= 0.6:
                score += 85
                why.append(f'{len(common)}/{len(cand_rows)} 行数值与该账号归档文件完全相同')
                break

    # 4. 内容（稿件标题）重合（+80）
    if df is not None and fps['titles']:
        for col in ['视频标题', '标题', '笔记标题']:
            if col in df.columns:
                hit = sum(1 for t in df[col].astype(str) if t in fps['titles'])
                if hit:
                    score += 80
                    why.append(f'{hit} 条内容标题与该账号归档文件重合')
                break

    # 5. 字面账号名（+60）
    text = path.name
    if df is not None:
        text += ' ' + ' '.join(df.columns.astype(str)) + ' ' + \
                ' '.join(df.head(3).astype(str).values.flatten())
    if acc in text:
        score += 60
        why.append(f'文件名或内容出现账号名「{acc}」')

    # 6. 量级包含（单条播放量 <= 该账号当日总播放）（+45）
    if df is not None and fps['play_series']:
        date_col = next((c for c in ['发布时间', '时间', '日期', '首次发布时间']
                         if c in df.columns), None)
        play_col = next((c for c in ['播放量', '播放', '观看量'] if c in df.columns), None)
        if date_col and play_col:
            d = parse_dates(df, date_col).dt.normalize()
            total = None
            for sd, sv in fps['play_series']:
                total = sv.groupby(sd.dt.normalize()).sum()
                break
            if total is not None:
                ok = tot = 0
                for i in range(len(df)):
                    dv = d.iloc[i]
                    pv = to_num(df[play_col].iloc[i])
                    if pd.isna(dv) or pv is None:
                        continue
                    tot += 1
                    if dv in total.index and pv <= float(total.loc[dv]) + 1:
                        ok += 1
                if tot >= 3 and ok / tot >= 0.8:
                    score += 45
                    why.append(f'{ok}/{tot} 条单稿播放量落在该账号当日总播放之下')

    return score, why


def detect_platform(path, df):
    """返回平台 key（bilibili/wechat/...），识别不出返回 None"""
    text = (path.name + ' ' + (' '.join(df.columns.astype(str)) if df is not None else '')).lower()
    best, best_score = None, 0
    for plat, keys in STRONG_PLATFORM.items():
        s = sum(1 for k in keys if k.lower() in text)
        if s > best_score:
            best, best_score = plat, s
    if best:
        return best
    for plat, hints in PLATFORM_HINTS.items():
        if any(h.lower() in text for h in hints):
            return plat
    return None


def platform_key_of_dir(name):
    """平台目录名 → 平台 key（bilibili/wechat/...），认不出返回 None"""
    low = name.lower()
    for key, prefixes in PLATFORM_PREFIX.items():
        if any(low.startswith(p.lower()) or p.lower() in low for p in prefixes):
            return key
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description='临时文件夹 → 账号数据 自动归类')
    ap.add_argument('--apply', action='store_true', help='执行移动（默认只预览）')
    _paths.add_root_arg(ap)
    args = ap.parse_args(argv)

    p = _paths.init(root=args.root)
    data, inbox = p.data, p.inbox
    if not inbox.exists():
        print(f'临时文件夹不存在：{inbox}')
        print('请先创建该目录，或用 --root 指定数据根目录')
        return
    files = sorted([f for f in inbox.iterdir()
                    if f.is_file() and not f.name.startswith('.')
                    and f.suffix.lower() not in ('.md', '.txt')])
    if not files:
        print('临时文件夹是空的，没有待归类文件')
        return

    # 候选账号 = 账号数据/ 下所有平台 + 账号
    candidates = []
    if data.exists():
        for plat_dir in sorted(data.iterdir()):
            if not plat_dir.is_dir():
                continue
            pkey = platform_key_of_dir(plat_dir.name)
            for acc_dir in sorted(plat_dir.iterdir()):
                if acc_dir.is_dir() and not acc_dir.name.isdigit():
                    candidates.append((plat_dir.name, acc_dir.name, pkey))
    print(f'候选账号 {len(candidates)} 个：' +
          '、'.join(f'{pd}/{a}' for pd, a, _ in candidates))
    print()

    fps_cache = {(pd, a): account_fingerprints(pd, a) for pd, a, _ in candidates}
    snapshot = datetime.now().strftime('%y%m%d')
    plan, unresolved = [], []

    for f in files:
        df = read_table(f)
        plat = detect_platform(f, df)
        scores = []
        for pd_name, a, pkey in candidates:
            if plat and pkey and pkey != plat:
                continue  # 平台已确定，只在该平台内比账号
            sc, why = score_candidate(df, f, fps_cache[(pd_name, a)], pd_name, a)
            if sc:
                scores.append((sc, pd_name, a, why))
        scores.sort(reverse=True, key=lambda x: x[0])

        if not scores:
            unresolved.append((f, '未识别到平台特征，需人工确认'))
            print(f'[待确认] {f.name}\n         未识别到平台特征，需人工确认')
            continue

        top = scores[0]
        second = scores[1] if len(scores) > 1 else (0, None, None, [])
        if top[0] < 45:
            unresolved.append((f, f'最高分 {top[0]} 不足以判定（{top[1]}/{top[2]}）'))
            print(f'[待确认] {f.name}\n         最高分 {top[0]} 不足以判定')
        elif len(scores) > 1 and second[0] >= top[0] * 0.8:
            unresolved.append((f, f'多个账号得分接近：{top[1]}/{top[2]} {top[0]} 分 vs '
                                  f'{second[1]}/{second[2]} {second[0]} 分'))
            print(f'[待确认] {f.name}\n         多个账号得分接近，需人工确认')
        else:
            plan.append((f, top[1], top[2], top[3]))
            print(f'[可归类] {f.name}')
            print(f'         → {top[1]}/{top[2]}/{snapshot}/')
            for w in top[3]:
                print(f'         依据：{w}')

    print()
    if not plan:
        print('没有可自动归类的文件')
        return
    if not args.apply:
        print(f'预览模式：{len(plan)} 个可归类，{len(unresolved)} 个需人工确认')
        print('加 --apply 执行移动')
        return

    for f, plat, acc, why in plan:
        dest_dir = data / plat / acc / snapshot
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f.name
        if dest.exists():
            stem, suffix = dest.stem, dest.suffix
            i = 2
            while dest.exists():
                dest = dest_dir / f'{stem}_{i}{suffix}'
                i += 1
        shutil.move(str(f), str(dest))
        print(f'已移动 {f.name} → {dest.relative_to(p.root)}')

    if unresolved:
        print(f'\n{len(unresolved)} 个文件留在临时文件夹待人工确认：')
        for f, reason in unresolved:
            print(f'  {f.name} —— {reason}')


if __name__ == '__main__':
    main()
