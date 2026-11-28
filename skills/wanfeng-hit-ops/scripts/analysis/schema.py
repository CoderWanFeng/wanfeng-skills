#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/schema.py - 各平台单作品明细 → 统一内容表

为什么要有这一层：抖音叫「粉丝增量」、小红书叫「涨粉」、视频号叫「关注量」，
但它们问的是同一个问题 —— 这条内容带来多少涨粉，相对于它拿到的曝光是否值得。

归一之后，效率指标、四象限、集中度、相关性只写一遍，
也避免「每个平台各写一套算式，口径悄悄跑偏」。

统一字段（口径写在 basis / window_note 里，不靠猜）：
    platform      平台标识
    account       账号
    title         标题
    publish_time  发布时间
    views         播放/观看 —— 效率指标的分母
    impressions   曝光（仅小红书有，其余为 NaN）
    followers     本条内容带来的涨粉
    saves         收藏
    likes         点赞
    comments      评论
    shares        分享
    completion    完播率（%）
    cover_ctr     封面点击率（%）
    basis         分母口径名：每千播放 / 每千观看
    window_note   统计窗口提醒（累计口径时条目之间不可直接比较）
"""

import re

import pandas as pd

# ============================================================
# 平台字段映射
# ============================================================
PLATFORM_SCHEMA = {
    'douyin': {
        'label': '抖音',
        'posts_key': 'douyin_posts',
        'title': '作品名称',
        'publish_time': '发布时间',
        'views': '播放量',
        'followers': '粉丝增量',
        'saves': '收藏量',
        'likes': '点赞量',
        'comments': '评论量',
        'shares': '分享量',
        'completion': '完播率',
        'cover_ctr': '封面点击率',
        'basis': '每千播放',
        'window_note': '累计口径（统计日为导出日），条目间比较需统一统计日',
    },
    'xiaohongshu': {
        'label': '小红书',
        'posts_key': 'xiaohongshu',
        'title': '笔记标题',
        'publish_time': '首次发布时间',
        'views': '观看量',
        'impressions': '曝光',
        'followers': '涨粉',
        'saves': '收藏',
        'likes': '点赞',
        'comments': '评论',
        'shares': '分享',
        'cover_ctr': '封面点击率',
        'basis': '每千观看',
        'window_note': '内容累计值（发布时长不同则累计窗口不同）',
    },
    'shipinhao': {
        'label': '视频号',
        'posts_key': 'shipinhao_posts',
        'title': '标题',
        'publish_time': '发布时间',
        'views': '播放量',
        'followers': '关注量',
        'saves': None,          # 视频号没有收藏口径
        'likes': '喜欢',
        'comments': '评论量',
        'shares': '分享量',
        'completion': '完播率',
        'basis': '每千播放',
        'window_note': '累计口径（统计日为导出日），条目间比较需统一统计日',
    },
}

# 没有单作品明细、只能做账号级效率的平台
ACCOUNT_ONLY = {
    'bilibili': 'B站（无单稿明细，只有日粒度聚合）',
    'wechat': '微信公众号（无单篇明细，只有账号级关注与阅读趋势）',
    'kuaishou': '快手（无单稿明细，日粒度聚合）',
}

UNIFIED_COLUMNS = [
    'platform', 'account', 'title', 'publish_time', 'views', 'impressions',
    'followers', 'saves', 'likes', 'comments', 'shares',
    'completion', 'cover_ctr', 'basis', 'window_note',
]


def _to_datetime(series):
    """小红书的「首次发布时间」是「2026年10月20日 12:30:00」这种中文格式"""
    s = series.astype(str)
    s = (s.str.replace('年', '-', regex=False)
          .str.replace('月', '-', regex=False)
          .str.replace('日', ' ', regex=False))
    s = s.str.replace(r'(\d+)时(\d+)分(\d+)秒',
                      lambda m: f'{m.group(1)}:{m.group(2)}:{m.group(3)}',
                      regex=True)
    return pd.to_datetime(s, errors='coerce')


def _num(df, col):
    """取数值列；列不存在返回全 NaN"""
    if col and col in df.columns:
        return pd.to_numeric(df[col], errors='coerce')
    return pd.Series(float('nan'), index=df.index)


def normalize(data, platform, window_start=None):
    """把某平台的单作品表转成统一内容表。

    window_start: 只保留该日期之后发布的作品（抖音全量 750 条含两年历史，
                  不按窗口过滤会把旧作品混进本期榜单）
    返回统一表；无数据返回空表（列齐全，方便下游直接判断）
    """
    schema = PLATFORM_SCHEMA.get(platform)
    if not schema:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    src = data.get(schema['posts_key'])
    if src is None or len(src) == 0:
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    df = src.copy()

    # 时间
    pt = df[schema['publish_time']]
    if not pd.api.types.is_datetime64_any_dtype(pt):
        pt = _to_datetime(pt)
    df['publish_time'] = pt

    # 窗口过滤
    if window_start is not None:
        df = df[df['publish_time'] >= pd.Timestamp(window_start)]

    out = pd.DataFrame(index=df.index)
    out['platform'] = schema['label']
    out['account'] = '程序员晚枫'
    out['title'] = df[schema['title']].astype(str) if schema['title'] in df.columns else ''
    out['publish_time'] = df['publish_time']
    out['views'] = _num(df, schema['views'])
    out['impressions'] = _num(df, schema.get('impressions'))
    out['followers'] = _num(df, schema['followers']).fillna(0)
    out['saves'] = _num(df, schema.get('saves'))
    out['likes'] = _num(df, schema.get('likes')).fillna(0)
    out['comments'] = _num(df, schema.get('comments')).fillna(0)
    out['shares'] = _num(df, schema.get('shares')).fillna(0)
    out['completion'] = _num(df, schema.get('completion'))
    out['cover_ctr'] = _num(df, schema.get('cover_ctr'))
    out['basis'] = schema['basis']
    out['window_note'] = schema['window_note']

    out = out.dropna(subset=['publish_time'])
    out = out.sort_values('publish_time').reset_index(drop=True)
    return out


def collect(data, window_start=None):
    """收集所有有单作品明细的平台，统一成一张表，加 platform_key 列"""
    frames = []
    for key in PLATFORM_SCHEMA:
        t = normalize(data, key, window_start=window_start)
        if len(t) == 0:
            continue
        t['platform_key'] = key
        frames.append(t)
    if not frames:
        return pd.DataFrame(columns=UNIFIED_COLUMNS + ['platform_key'])
    return pd.concat(frames, ignore_index=True)


def content_window(month, days=90):
    """内容级分析窗口。

    为什么不用「报告月当月」：
      - 单作品明细是**累计值**，一条 10 月发布的内容在 11 月仍在贡献数据，
        按发布月过滤会漏掉月初之前发布、但表现仍在累积的内容
      - 后台导出的单条明细更新滞后（本期视频号最新只到 10-29），
        卡死当月会让该平台内容级分析直接归零

    所以用「报告月往前 N 天」的滚动窗口，并在报告里显式声明这个窗口。
    抖音作品表是全量 750 条历史，这个过滤同时把 2022 年的老作品排除掉了。

    返回 (window_start, 说明文字)
    """
    start = pd.Timestamp(f'{month}-01')
    ws = start - pd.Timedelta(days=days)
    note = (f'内容级分析窗口：{ws.date().isoformat()} ~ '
            f'发布（滚动 {days} 天，报告月往前）；'
            f'单作品明细为累计值，非当月新发')
    return ws, note


def title_of(row, limit=30):
    """标题清洗：去掉话题标签与尾部符号"""
    t = str(row.get('title') or '')
    t = re.sub(r'#\S+', '', t)
    t = re.sub(r'[\s　]+', ' ', t).strip(' -—·|')
    return t[:limit]
