#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_data.py - 各平台后台原始文件 → 结构化 DataFrame

用法：
    python parse_data.py [--root <数据根目录>]

数据根目录结构：
    <root>/账号数据/<平台>/<账号>/<YYMMDD>/<文件>

平台目录名按「英文/拼音-中文」约定，但脚本按**前缀模糊匹配**，
所以 `bilibili-B站` / `B站` / `bilibili` 都能认。

解析约定（跨平台通用的硬规则）：
- **同一账号的多个快照按日期合并去重**，旧快照不会被新快照整段覆盖
- **B 站三种口径分开存**（history / recent / fans），混在一起做日期去重会把先到的整段冲掉
- **原始导出与页面摘录分开**，「页面摘录」「近期稿件对比」这类非日趋势文件不参与趋势计算
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths

# 平台标识 → 目录名前缀候选
PLATFORM_PREFIX = {
    'bilibili': ['bilibili', 'b站', '哔哩'],
    'wechat': ['wechat', '公众号'],
    'douyin': ['douyin', '抖音'],
    'shipinhao': ['shipinhao', '视频号'],
    'xiaohongshu': ['xiaohongshu', '小红书', 'rednote'],
    'kuaishou': ['kuaishou', '快手'],
}


def platform_dir(key):
    """在 账号数据/ 下按前缀找到平台目录；找不到返回 None"""
    data = _paths.paths().data
    if not data.exists():
        return None
    prefixes = PLATFORM_PREFIX.get(key, [key])
    for d in sorted(data.iterdir()):
        if not d.is_dir():
            continue
        low = d.name.lower()
        if any(low.startswith(p.lower()) or p.lower() in low for p in prefixes):
            return d
    return None


# ============================================================
# 1. Bilibili CSV
# ============================================================
def parse_bilibili():
    """B站：三种口径分开存 ——
    history = 历史累计口径（播放量/累计粉丝都是累计值）
    recent  = 日增量口径（播放量=当日播放，净增粉丝=当日净增）
    fans    = 关注数口径（粉丝总数/新增关注/取消关注）
    三者字段名互不相同但日期区间高度重叠，按 kind 分开才能各自合并；
    混在一起时日期去重会把先到的整段冲掉。
    """
    result = {}
    base = platform_dir('bilibili')
    if base is None:
        return result
    for f in sorted(base.rglob('*.csv')):
        if f.name.startswith('页面摘录') or f.name.startswith('近期稿件对比'):
            continue  # 页面摘录/稿件对比是另一套字段（指标/稿件维度），不是日趋势
        df = pd.read_csv(f, encoding='utf-8-sig')
        if '时间' not in df.columns:
            continue
        df = df[df['时间'].astype(str).str.match(r'^\d{4}/\d{2}/\d{2}$')].copy()
        if df.empty:
            continue
        df['时间'] = pd.to_datetime(df['时间'])
        df = df.sort_values('时间').reset_index(drop=True)
        account = _account_of(f)
        if '累计粉丝' in df.columns:
            kind = 'history'
        elif '粉丝总数' in df.columns:
            kind = 'fans'
        else:
            kind = 'recent'
        df['账号'] = account
        prev = result.get(account, {}).get(kind)
        if prev is not None:
            df = (pd.concat([prev, df], ignore_index=True)
                    .drop_duplicates(subset=['时间'], keep='last')
                    .sort_values('时间').reset_index(drop=True))
        result.setdefault(account, {})[kind] = df
    return result


# ============================================================
# 2. 视频号 CSV
# ============================================================
def _snapshot_dirs(base):
    """账号目录下的数据快照目录（6 位日期），按新到旧排序"""
    if not base.exists():
        return []
    return sorted((d for d in base.iterdir()
                   if d.is_dir() and d.name.isdigit() and len(d.name) == 6),
                  key=lambda d: d.name, reverse=True)


def _latest_snapshot(base):
    """数据快照目录：优先按日期文件夹名(YYMMDD)取最新，无子文件夹则用 base 本身"""
    snaps = _snapshot_dirs(base)
    return snaps[0] if snaps else base


def _latest_file(base, filename):
    """在账号目录的快照里按新到旧找第一个含该文件的快照；都没有则回退到账号根目录"""
    for d in _snapshot_dirs(base):
        p = d / filename
        if p.exists():
            return p
    p = base / filename
    return p if p.exists() else None


def _account_of(path):
    """文件所属账号：向上找到最近的非日期目录名（快照目录名是 6 位数字）"""
    d = path.parent
    while d != d.parent and d.name.isdigit() and len(d.name) == 6:
        d = d.parent
    return d.name


def parse_shipinhao():
    base = platform_dir('shipinhao')
    if base is None:
        return {}
    result = {}
    # 视频号账号目录：取该平台下第一个账号目录（多账号时逐个解析）
    acc_dirs = [d for d in sorted(base.iterdir()) if d.is_dir()]
    f1 = f2 = f3 = None
    for acc in acc_dirs:
        f1 = f1 or _latest_file(acc, '视频号关注者增长详情数据.csv')
        f2 = f2 or _latest_file(acc, '视频号视频详情数据.csv')
        f3 = f3 or _latest_file(acc, '视频号动态数据明细.csv')
    if not (f1 or f2 or f3):
        return result

    if f1:
        df = pd.read_csv(f1, encoding='utf-8-sig', skiprows=2)
        for c in df.columns:
            df[c] = df[c].astype(str).str.replace('"', '').str.replace(',', '')
        df.columns = ['时间', '净增关注', '新增关注', '取消关注', '关注者总数']
        df['时间'] = pd.to_datetime(df['时间'])
        for col in ['净增关注', '新增关注', '取消关注', '关注者总数']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.sort_values('时间').reset_index(drop=True)
        result['fans'] = df
    if f2:
        df = pd.read_csv(f2, encoding='utf-8-sig', skiprows=2)
        for c in df.columns:
            df[c] = df[c].astype(str).str.replace('"', '').str.replace(',', '')
        df.columns = ['时间', '播放', '推荐', '喜欢', '评论', '分享', '关注']
        df['时间'] = pd.to_datetime(df['时间'])
        for col in ['播放', '推荐', '喜欢', '评论', '分享', '关注']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.sort_values('时间').reset_index(drop=True)
        result['video'] = df
    # 单条视频明细（含标题、完播率）—— 唯一带内容标题的数据源
    if f3:
        df = pd.read_csv(f3, encoding='utf-8-sig')
        df['完播率'] = df['完播率'].astype(str).str.rstrip('%').astype(float)
        df['平均播放时长秒'] = (df['平均播放时长'].astype(str)
                            .str.replace('秒', '', regex=False).astype(float))
        df['发布时间'] = pd.to_datetime(df['发布时间'])
        for col in ['播放量', '推荐', '喜欢', '评论量', '分享量', '关注量']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        df = df.sort_values('发布时间').reset_index(drop=True)
        df['标题'] = df['视频描述'].astype(str).str.split('#').str[0].str.strip()
        df['哈希标签'] = df['视频描述'].astype(str).apply(
            lambda s: [t.strip() for t in s.split('#')[1:]])
        result['posts'] = df
    return result


# ============================================================
# 3. 抖音 Excel
# ============================================================
def parse_douyin():
    """抖音：优先新格式（粉丝/短视频全量指标 + 作品列表），兼容旧的单播放量文件"""
    base = platform_dir('douyin')
    if base is None:
        return {}
    result = {}
    acc_dirs = [d for d in sorted(base.iterdir()) if d.is_dir()]
    f1 = f2 = f3 = None
    for acc in acc_dirs:
        f1 = f1 or _latest_file(acc, '数据表现_粉丝全量指标.xlsx')
        f2 = f2 or _latest_file(acc, '数据表现_短视频全量指标.xlsx')
        f3 = f3 or _latest_file(acc, '作品列表导出.xlsx')
    if not (f1 or f2 or f3):
        return result

    if f1:
        df = pd.read_excel(f1)
        df['日期'] = pd.to_datetime(df['日期'])
        result['fans'] = df.sort_values('日期').reset_index(drop=True)
    if f2:
        df = pd.read_excel(f2)
        df['日期'] = pd.to_datetime(df['日期'])
        for c in ['5秒完播率', '2秒跳出率', '封面点击率']:
            if c in df.columns:
                df[c] = df[c].astype(str).str.rstrip('%').astype(float)
        result['daily'] = df.sort_values('日期').reset_index(drop=True)
    if f3:
        df = pd.read_excel(f3)
        df['发布时间'] = pd.to_datetime(df['发布时间'])
        # 后台导出含 '-' 占位，统一转数值
        for c in ['播放量', '点赞量', '分享量', '评论量', '收藏量',
                  '主页访问量', '粉丝增量', '平均播放时长']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        for c in ['完播率', '5s完播率', '2s跳出率', '封面点击率']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce') * 100
        result['posts'] = df.sort_values('发布时间').reset_index(drop=True)
    return result


# ============================================================
# 4. 微信 user_analysis（HTML伪xls）
# ============================================================
def parse_wechat_html_user_analysis():
    """公众号关注数（HTML 伪 xls）。同一账号可能有多个时段的快照，按日期合并去重。"""
    result = {}
    base = platform_dir('wechat')
    if base is None:
        return result
    for f in sorted(base.rglob('user_analysis.xls')):
        account = _account_of(f)
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read()
        cells = re.findall(r'<th[^>]*>(.*?)</th>', content)
        data = []
        i = 0
        while i < len(cells):
            cell = cells[i].strip()
            if re.match(r'\d{4}-\d{2}-\d{2}', cell) and i + 4 < len(cells):
                row = [cell] + [cells[i+j].strip() for j in range(1, 5)]
                if all(re.match(r'^-?\d+$', row[j]) for j in range(1, 5)):
                    data.append(row)
                i += 5
            else:
                i += 1
        if data:
            df = pd.DataFrame(data, columns=['时间', '新关注人数', '取消关注人数',
                                             '净增关注人数', '累积关注人数'])
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['时间']).reset_index(drop=True)
            df['时间'] = pd.to_datetime(df['时间'])
            df['账号'] = account
            prev = result.get(account)
            if prev is not None:
                df = (pd.concat([prev, df], ignore_index=True)
                        .drop_duplicates(subset=['时间'], keep='last')
                        .sort_values('时间').reset_index(drop=True))
            result[account] = df
    return result


# ============================================================
# 5. 微信 tendency（阅读数据，old .xls 用 xlrd）
# ============================================================
def parse_wechat_tendency():
    """公众号阅读趋势（xls）。同一账号多个时段的快照按日期合并去重。"""
    result = {}
    base = platform_dir('wechat')
    if base is None:
        return result
    for f in sorted(base.rglob('tendency_*.xls')):
        account = _account_of(f)
        try:
            df_dict = pd.read_excel(f, sheet_name=None, engine='xlrd')
            ws_name = list(df_dict.keys())[0]
            df = df_dict[ws_name]
            data = []
            for _, row in df.iterrows():
                date_val = row.iloc[1]
                if pd.isna(date_val):
                    continue
                date_str = str(date_val)
                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                    channel = row.iloc[2] if len(row) > 2 else ''
                    readers = row.iloc[3] if len(row) > 3 else 0
                    data.append([date_str, channel, readers])
            if data:
                out = pd.DataFrame(data, columns=['日期', '渠道', '阅读人数'])
                out['日期'] = pd.to_datetime(out['日期'])
                out['阅读人数'] = pd.to_numeric(out['阅读人数'],
                                                errors='coerce').fillna(0).astype(int)
                out['账号'] = account
                prev = result.get(account)
                if prev is not None:
                    out = (pd.concat([prev, out], ignore_index=True)
                             .drop_duplicates(subset=['日期', '渠道'], keep='last')
                             .sort_values('日期').reset_index(drop=True))
                result[account] = out
        except Exception as e:
            print(f'  [WARN] {f.name}: {e}')
    return result


# ============================================================
# 6. 快手 Excel（帐号数据分析明细表）
# ============================================================
def parse_kuaishou():
    """快手：帐号数据分析明细表 —— 日播放/完播率/净增粉丝/互动/作品量"""
    base = platform_dir('kuaishou')
    if base is None:
        return {}
    result = {}
    f = None
    for acc in [d for d in sorted(base.iterdir()) if d.is_dir()]:
        cands = sorted(acc.rglob('帐号数据分析明细表*.xlsx'), reverse=True)
        if cands:
            f = cands[0]
            break
    if not f:
        return result

    df = pd.read_excel(f)
    df['日期'] = pd.to_datetime(df['日期'].astype(str).str.replace('年', '-')
                               .str.replace('月', '-').str.replace('日', ''))
    for c in ['播放量', '完播率', '净增粉丝量', '评论量', '点赞量', '分享量', '作品量']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.rstrip('%'),
                                  errors='coerce').fillna(0)
    result['daily'] = df.sort_values('日期').reset_index(drop=True)
    return result


# ============================================================
# 7. 小红书 Excel
# ============================================================
def _pct(s):
    """'43.25%' / 0.4325 -> 43.25"""
    return pd.to_numeric(s.astype(str).str.rstrip('%'), errors='coerce')


def parse_xiaohongshu():
    """小红书：笔记明细 + 近30日系列（观看/互动/涨粉/发布）
    各文件可能来自不同导出批次，逐个文件在快照里回溯查找，避免只看最新快照导致缺文件。
    """
    base = platform_dir('xiaohongshu')
    if base is None:
        return {}
    result = {}
    acc_dirs = [d for d in sorted(base.iterdir()) if d.is_dir()]
    if not acc_dirs:
        return result
    acc = acc_dirs[0]

    f = _latest_file(acc, '笔记列表明细表.xlsx')
    if f:
        # 第0行：导出说明（"最多导出..."），跳过
        # 第1行（Excel行号2）：真正列名
        df = pd.read_excel(f, header=1)
        df = df.dropna(how='all').reset_index(drop=True)
        num_cols = ['曝光', '观看量', '点赞', '评论', '收藏', '涨粉', '分享', '弹幕']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        result['posts'] = df

    # 近30日系列：账号总览 + 各指标日趋势
    series_files = {
        'watch': '近30日观看数据.xlsx',
        'engage': '近30日互动数据.xlsx',
        'fans': '近30日涨粉数据.xlsx',
        'publish': '近30日发布数据.xlsx',
    }
    for key, fname in series_files.items():
        fp = _latest_file(acc, fname)
        if not fp:
            continue
        xl = pd.ExcelFile(fp)
        summary = {}
        trends = {}
        for sn in xl.sheet_names:
            d = pd.read_excel(fp, sheet_name=sn)
            if '指标' in d.columns and '数值' in d.columns:
                for _, r in d.iterrows():
                    summary[str(r['指标'])] = r['数值']
            elif '日期' in d.columns:
                dd = d.copy()
                dd['日期'] = pd.to_datetime(dd['日期'].astype(str).str.replace('年', '-')
                                           .str.replace('月', '-').str.replace('日', ''))
                trends[sn] = dd.sort_values('日期').reset_index(drop=True)
        result[key] = {'summary': summary, 'trends': trends}
    return result


# ============================================================
# 主函数：解析所有
# ============================================================
def main(argv=None):
    print('===== 开始解析 =====')
    data = {}
    data['bilibili'] = parse_bilibili()
    for acc, kinds in data['bilibili'].items():
        print(f'  B站({acc}): ' + ' '.join(f'{k}={len(v)}行' for k, v in kinds.items()))
    sh = parse_shipinhao()
    data['shipinhao_fans'] = sh.get('fans')
    data['shipinhao_video'] = sh.get('video')
    data['shipinhao_posts'] = sh.get('posts')
    print(f'  视频号(关注): {len(sh.get("fans", []))}行')
    print(f'  视频号(视频): {len(sh.get("video", []))}行')
    print(f'  视频号(单条): {len(sh.get("posts", []))}行')
    dy = parse_douyin()
    data['douyin'] = dy.get('daily')
    data['douyin_fans'] = dy.get('fans')
    data['douyin_posts'] = dy.get('posts')
    print(f'  抖音(日): {len(dy.get("daily", []))}行 粉丝:{len(dy.get("fans", []))}行 '
          f'作品:{len(dy.get("posts", []))}行')
    wechat_fans = parse_wechat_html_user_analysis()
    data['wechat_fans'] = wechat_fans
    for k, v in wechat_fans.items():
        print(f'  微信粉丝({k}): {len(v)}行, 最新:{v["累积关注人数"].iloc[-1]}')
    wechat_read = parse_wechat_tendency()
    data['wechat_read'] = wechat_read
    for k, v in wechat_read.items():
        print(f'  微信阅读({k}): {len(v)}行')
    xhs = parse_xiaohongshu()
    data['xiaohongshu'] = xhs.get('posts')
    data['xhs_watch'] = xhs.get('watch')
    data['xhs_engage'] = xhs.get('engage')
    data['xhs_fans'] = xhs.get('fans')
    data['xhs_publish'] = xhs.get('publish')
    print(f'  小红书: {len(xhs.get("posts", []))}行')
    ks = parse_kuaishou()
    data['kuaishou'] = ks.get('daily')
    print(f'  快手(日): {len(ks.get("daily", []))}行')
    print('===== 完成 =====')
    return data


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='各平台后台原始文件 → 结构化数据')
    _paths.add_root_arg(ap)
    args = ap.parse_args()
    p = _paths.init(root=args.root)
    for k, v in p.describe():
        print(f'{k}: {v}')
    main()
