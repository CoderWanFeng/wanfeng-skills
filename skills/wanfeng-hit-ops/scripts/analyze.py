#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze.py - 跨平台总览 + 爆款归因

用法：
    python analyze.py --root <数据根目录> [--save]

不落盘时只打印到终端；--save 时写到 <root>/月度报告/YYYY-MM/report_<时间戳>.md
（**不会覆盖**人工撰写的复盘稿——自动稿只落带时间戳的文件）
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths

# ============================================================
# 生成 Markdown 报告
# ============================================================
def gen_markdown(data, result=None):
    lines = []
    lines.append('# 自媒体数据分析报告')
    lines.append(f'\n> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
    if result and result.get('window_note'):
        lines.append(f'> {result["window_note"]}\n')
    lines.append('---\n')

    # 一、粉丝总览
    lines.append('## 一、粉丝总览\n')
    fans_rows = []

    # 微信
    wechat_fans = data.get('wechat_fans', {})
    for account, df in wechat_fans.items():
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            fans_rows.append(['微信公众号', account, int(latest['累积关注人数']), str(latest['时间'].date())])

    # B站：优先用 fans 口径（最新），退回 history 口径（较旧的历史累计）
    df_bili = data.get('bilibili') or {}
    for account, kinds in df_bili.items():
        fans = kinds.get('fans')
        hist = kinds.get('history')
        if fans is not None and len(fans) > 0:
            latest = fans.iloc[-1]
            fans_rows.append(['B站', account, int(latest['粉丝总数']), str(latest['时间'].date())])
        elif hist is not None and len(hist) > 0:
            latest = hist.iloc[-1]
            fans_rows.append(['B站', account, int(latest['累计粉丝']), str(latest['时间'].date())])

    # 视频号
    sh_fans = data.get('shipinhao_fans')
    if sh_fans is not None and len(sh_fans) > 0:
        latest = sh_fans.iloc[-1]
        fans_rows.append(['视频号', '程序员晚枫', int(latest['关注者总数']), str(latest['时间'].date())])

    if fans_rows:
        fans_rows.sort(key=lambda x: x[2], reverse=True)
        lines.append('| 排名 | 平台 | 账号 | 粉丝数 | 数据日期 |')
        lines.append('|------|------|------|--------|----------|')
        for i, row in enumerate(fans_rows):
            lines.append(f'| {i+1} | {row[0]} | {row[1]} | {row[2]:,} | {row[3]} |')
        lines.append('')

    # 二、各平台近期趋势
    lines.append('\n## 二、各平台近期趋势\n')

    # B站
    if df_bili:
        lines.append('### B站\n')
        for account, kinds in df_bili.items():
            hist = kinds.get('history')
            if hist is not None and len(hist) > 0:
                first, last = hist.iloc[0], hist.iloc[-1]
                days = (last['时间'] - first['时间']).days
                fg = int(last['累计粉丝'] - first['累计粉丝'])
                pg = int(last['播放量'] - first['播放量'])
                lines.append(f'**{account}**（历史累计口径，{days}天）')
                lines.append(f'- 粉丝：{int(first["累计粉丝"]):,} → {int(last["累计粉丝"]):,}（净增 {fg:+,}）')
                lines.append(f'- 播放量：{int(first["播放量"]):,} → {int(last["播放量"]):,}（新增 {pg:,}）')
                lines.append(f'- 单粉播放比：{int(last["播放量"]) / int(last["累计粉丝"]):.1f}')
            rec = kinds.get('recent')
            if rec is not None and len(rec) > 0:
                days = (rec['时间'].max() - rec['时间'].min()).days + 1
                lines.append(f'**{account}**（近{days}天日增量口径）')
                lines.append(f'- 播放合计：{int(rec["播放量"].sum()):,}，'
                             f'净增粉丝合计：{int(rec["净增粉丝"].sum()):,}，'
                             f'收藏合计：{int(rec["收藏"].sum()):,}')
            fans = kinds.get('fans')
            if fans is not None and len(fans) > 0:
                days = (fans['时间'].max() - fans['时间'].min()).days + 1
                first, last = fans.iloc[0], fans.iloc[-1]
                net = int(fans['新增关注'].sum() - fans['取消关注'].sum())
                lines.append(f'**{account}**（近{days}天关注口径）')
                lines.append(f'- 粉丝总数：{int(first["粉丝总数"]):,} → {int(last["粉丝总数"]):,}'
                             f'（净增 {net:+,}）')
                lines.append(f'- 新增关注 {int(fans["新增关注"].sum()):,}，'
                             f'取消关注 {int(fans["取消关注"].sum()):,}，'
                             f'取关率 {fans["取消关注"].sum() / fans["新增关注"].sum() * 100:.1f}%')
            lines.append('')

    # 视频号
    sh_fans = data.get('shipinhao_fans')
    if sh_fans is not None and len(sh_fans) > 0:
        lines.append('### 视频号（程序员晚枫）\n')
        first, last = sh_fans.iloc[0], sh_fans.iloc[-1]
        fg = int(last['关注者总数'] - first['关注者总数'])
        lines.append(f'- 关注者：{int(first["关注者总数"]):,} → {int(last["关注者总数"]):,}（净增 {fg:+,}）')
        lines.append(f'- 日均净增：{fg / len(sh_fans):+.0f}/天')
        lines.append('')

    # 抖音
    df_douyin = data.get('douyin')
    dy_fans = data.get('douyin_fans')
    if df_douyin is not None and len(df_douyin) > 0:
        lines.append('### 抖音（程序员晚枫）\n')
        play_col = '总播放量' if '总播放量' in df_douyin.columns else '播放量'
        total_play = df_douyin[play_col].sum()
        lines.append(f'- 统计周期：{df_douyin["日期"].min().date()} ~ {df_douyin["日期"].max().date()}')
        lines.append(f'- 总播放量：{int(total_play):,}')
        lines.append(f'- 日均播放：{int(total_play / len(df_douyin)):,}')
        if dy_fans is not None and len(dy_fans) > 0:
            net = int(dy_fans['总粉丝量'].iloc[-1] - dy_fans['总粉丝量'].iloc[0])
            lines.append(f'- 粉丝：{int(dy_fans["总粉丝量"].iloc[0]):,} → '
                         f'{int(dy_fans["总粉丝量"].iloc[-1]):,}（净增 {net:+,}）')
        lines.append('')

    # 快手
    df_ks = data.get('kuaishou')
    if df_ks is not None and len(df_ks) > 0:
        lines.append('### 快手（程序员晚枫）\n')
        lines.append(f'- 统计周期：{df_ks["日期"].min().date()} ~ {df_ks["日期"].max().date()}')
        lines.append(f'- 总播放量：{int(df_ks["播放量"].sum()):,}'
                     f'（日均 {int(df_ks["播放量"].mean()):,}）')
        lines.append(f'- 净增粉丝：{int(df_ks["净增粉丝量"].sum()):+,}'
                     f'（{len(df_ks)} 天合计）')
        lines.append(f'- 发布作品：{int(df_ks["作品量"].sum())} 条'
                     f'（{int((df_ks["作品量"] > 0).sum())} 天有更新）')
        lines.append(f'- 平均完播率：{df_ks["完播率"].mean():.2f}%')
        lines.append('')

    # 视频号单条（含标题）
    sh_posts = data.get('shipinhao_posts')
    if sh_posts is not None and len(sh_posts) > 0:
        lines.append('### 视频号单条作品（含标题）\n')
        lines.append(f'- 作品数：{len(sh_posts)}')
        lines.append(f'- 总播放：{int(sh_posts["播放量"].sum()):,}')
        lines.append(f'- 总涨粉：{int(sh_posts["关注量"].sum()):,}')
        lines.append('')
        lines.append('| 发布日 | 播放 | 完播率 | 涨粉 | 标题 |')
        lines.append('|--------|------|--------|------|------|')
        for _, r in sh_posts.nlargest(5, '播放量').iterrows():
            t = str(r['标题'])[:20]
            lines.append(f'| {r["发布时间"].date()} | {int(r["播放量"]):,} | '
                         f'{r["完播率"]:.1f}% | {int(r["关注量"])} | {t} |')
        lines.append('')

    # 微信阅读
    wechat_read = data.get('wechat_read', {})
    for account, df in wechat_read.items():
        if df is not None and len(df) > 0:
            lines.append(f'### 微信公众号阅读（{account}）\n')
            total_read = df['阅读人数'].sum()
            avg_read = df.groupby('日期')['阅读人数'].sum().mean()
            lines.append(f'- 统计周期：{df["日期"].min().date()} ~ {df["日期"].max().date()}')
            lines.append(f'- 总阅读人数：{int(total_read):,}')
            lines.append(f'- 日均阅读：{int(avg_read):,}/天')
            lines.append('')

    # 小红书
    df_xhs = data.get('xiaohongshu')
    if df_xhs is not None and len(df_xhs) > 0:
        lines.append('### 小红书（程序员晚枫）\n')
        total_views = df_xhs['观看量'].sum() if '观看量' in df_xhs.columns else 0
        total_likes = df_xhs['点赞'].sum() if '点赞' in df_xhs.columns else 0
        lines.append(f'- 笔记总数：{len(df_xhs)}')
        lines.append(f'- 总观看量：{int(total_views):,}')
        lines.append(f'- 总点赞：{int(total_likes):,}')
        lines.append('')

    # 三、数据发现（由计算层生成，不是建议）
    lines.append('\n## 三、数据发现\n')
    lines.append('> 每条含：**现象 —— 数据 —— 判断 —— 置信度依据 —— 反例/边界**。\n')
    lines.append('> 判断只到「数据说明了什么」，不下内容创作建议（见 SKILL.md 能力边界）。\n')

    if not result or not result.get('findings'):
        lines.append('本期未生成可数据支撑的发现（数据不足或缺少单作品明细）。\n')
    else:
        # 先给跨平台的结构性发现，再给单平台现象
        struct = [f for f in result['findings'] if f.topic == '结构']
        rest = [f for f in result['findings'] if f.topic != '结构' and f.topic != '缺口']
        gaps = [f for f in result['findings'] if f.topic == '缺口']

        idx = 0
        if struct:
            lines.append('### 结构性发现\n')
            for f in struct:
                idx += 1
                lines.append(f'{idx}. {f.to_markdown()}\n')
            lines.append('')
        if rest:
            lines.append('### 平台级发现\n')
            for f in rest:
                idx += 1
                lines.append(f'{idx}. {f.to_markdown()}\n')
            lines.append('')
        if gaps:
            lines.append('### 数据缺口\n')
            for f in gaps:
                idx += 1
                lines.append(f'{idx}. **{f.platform}：** {f.metric} —— {f.judgment}\n')
            lines.append('')

        # 四、效率榜：让「播放榜」和「效率榜」同时可见
        lines.append('### 效率榜（按每千涨粉，非播放量）\n')
        unified = result.get('unified')
        if unified is not None and len(unified) > 0:
            for pk, sub in unified.groupby('platform_key'):
                lines.append(f'\n**{sub["platform"].iloc[0]}**'
                             f'（中位 {result["baseline"].get(pk, {}).get("median", float("nan")):.2f}'
                             f' / 千播放涨粉）\n')
                lines.append('| 发布日 | 标题 | 曝光 | 涨粉 | 每千涨粉 | 象限 |\n')
                lines.append('|---|---|---:|---:|---:|---|\n')
                work = sub.sort_values('每千涨粉', ascending=False).head(5)
                for _, r in work.iterrows():
                    from analysis.schema import title_of
                    lines.append(f'| {r["publish_time"].date()} | {title_of(r, 24)} | '
                                 f'{int(r["views"]):,} | {int(r["followers"]):,} | '
                                 f'{r["每千涨粉"]:.2f} | {r.get("象限判定", "")} |\n')
        else:
            lines.append('本期无单作品明细，无法生成效率榜。\n')

    return '\n'.join(lines)

# ============================================================
# 主函数
# ============================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description='跨平台总览与爆款归因')
    ap.add_argument('--save', action='store_true', help='落盘到 月度报告/YYYY-MM/')
    ap.add_argument('--month', default=None, help='报告月份 YYYY-MM，默认当前月')
    _paths.add_root_arg(ap)
    args = ap.parse_args(argv)

    p = _paths.init(root=args.root)

    print('加载数据...')
    from parse_data import main as parse_main
    data = parse_main()

    print('跑分析计算层...')
    from analysis import pipeline
    month = args.month or datetime.now().strftime('%Y-%m')
    result = pipeline.run(data, month=month)
    print(f'  内容级样本 {len(result.get("unified", []))} 条，'
          f'生成发现 {len(result.get("findings", []))} 条')

    print('生成报告...')
    md = gen_markdown(data, result=result)

    if args.save:
        out = p.month_dir(datetime.now().strftime('%Y-%m'))
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        report_path = out / f'report_{ts}.md'
        report_path.write_text(md, encoding='utf-8')
        print(f'报告已保存：{report_path}')
        print('提示：自动稿已按月归档，人工复盘稿不受影响')

    print('\n===== 报告预览 =====')
    print(md[:3000])


if __name__ == '__main__':
    main()
