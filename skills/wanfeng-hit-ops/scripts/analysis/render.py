#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/render.py - 把分析结果渲染成报告章节

报告模板（templates/月度报告模板.md）负责章节骨架，这一层负责把
计算层产出的结构化发现填进对应章节。

对应关系：
    一、结论摘要      ← 全局 top findings（跨平台）
    四、单平台分析    ← 按平台分组的 findings + 效率榜
    五、跨平台综合    ← 跨平台的效率/结构 findings
    七、数据缺口      ← 缺口类 findings

边界（SKILL.md L0 / hit-methodology §八）：
    这里只渲染**数据结论**，不生成任何内容创作建议。
    「验证方向」章节由 report-spec 的人工判断层负责。
"""

import pandas as pd

from . import schema


def _fmt(n, unit='', digits=1):
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return '—'
    if digits == 0:
        return f'{n:,.0f}{unit}'
    return f'{n:,.{digits}f}{unit}'


def _count(n):
    """计数类数字：整数 + 千分位"""
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return '—'
    return f'{int(round(n)):,}'


def _pct(n, digits=1):
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return '—'
    return f'{n:.{digits}f}%'


# ============================================================
# 一、结论摘要
# ============================================================
def summary_section(result, max_items=5):
    """结论摘要：每条格式「平台 —— 现象 —— 数据 —— 判断」。

    挑选策略：**指导性优先**，不按发现顺序硬取。
    摘要要回答的是「本期最该知道什么」，所以优先给：
        1. 跨平台都成立的结论（集中度、平台分工的结构性差异）
        2. 能改变下期判断的结论（伪爆款、留存、过度表现检验通过的结构）
    纯「埋没内容」这类单平台的现象只在小节里出现，不占摘要位。
    """
    findings = [f for f in result.get('findings', []) if f.topic != '缺口']
    if not findings:
        return ('## 一、结论摘要\n\n'
                '> **本期未能生成可数据支撑的结论**：'
                '缺少单作品明细或账号级数据不足以支撑任何效率类判断。'
                '请见第七章数据缺口。\n\n---\n')

    # 优先级：结构性 > 可执行 > 现象级
    def priority(f):
        if f.topic == '结构' and f.confidence in ('高', '中'):
            return 0
        if f.topic == '留存':
            return 1
        if '伪爆款' in f.tags or '放量' in f.tags:
            return 2
        if f.topic == '集中度':
            return 3
        if f.topic == '相关性':
            return 4
        if f.topic == '效率':
            return 5
        return 6

    picked = sorted(findings, key=priority)
    # 两个约束：同一平台最多 2 条、同一 topic 最多 1 条
    # （否则摘要会被「集中度高」这类同质结论占满）
    per_platform = {}
    per_topic = {}
    chosen = []
    for f in picked:
        c = per_platform.get(f.platform, 0)
        if c >= 2:
            continue
        t = per_topic.get(f.topic, 0)
        if t >= 1:
            continue
        per_platform[f.platform] = c + 1
        per_topic[f.topic] = t + 1
        chosen.append(f)
        if len(chosen) >= max_items:
            break
    # 不足则放宽 topic 限制补齐
    if len(chosen) < max_items:
        for f in picked:
            if f in chosen:
                continue
            c = per_platform.get(f.platform, 0)
            if c >= 2:
                continue
            per_platform[f.platform] = c + 1
            chosen.append(f)
            if len(chosen) >= max_items:
                break

    lines = ['## 一、结论摘要\n\n',
             '> 以下每条由计算层从原始数据自动生成，格式：**平台 —— 现象 —— 数据 —— 判断**。\n',
             '> 置信度依据见各平台小节；样本量不足的结论一律降级。\n']
    for i, f in enumerate(chosen, 1):
        lines.append(f'{i}. **{f.platform}：{f.phenomenon}。** {f.data}。{f.judgment}'
                     f'（置信度：{f.confidence}）\n')
    lines.append('\n---\n')
    return '\n'.join(lines)


# ============================================================
# 四、单平台分析
# ============================================================
def efficiency_table(result, pk, top=8):
    """关键内容表现表：带效率指标，让「播放榜」和「效率榜」同时可见。"""
    unified = result.get('unified')
    if unified is None or len(unified) == 0:
        return ''
    sub = unified[unified['platform_key'] == pk]
    if len(sub) == 0:
        return ''

    has_saves = sub['每千收藏'].notna().any()
    head = '| 发布日 | 标题 | 播放/观看 | 涨粉 | 每千涨粉 |'
    sep = '|---|---|---:|---:|---:|'
    if has_saves:
        head += ' 每千收藏 |'
        sep += '---:|'
    head += ' 象限判定 |'
    sep += '---|'

    rows = [head, sep]
    # 按曝光排序展示全部（截断），因为「放量内容」也要看
    work = sub.sort_values('views', ascending=False).head(top)
    for _, r in work.iterrows():
        title = schema.title_of(r, 26)
        line = (f'| {r["publish_time"].date()} | {title} | {_count(r["views"])} | '
                f'{_count(r["followers"])} | {_fmt(r["每千涨粉"], "", 2)} |')
        if has_saves:
            line += f' {_fmt(r["每千收藏"], "", 2)} |'
        line += f' {r.get("象限判定", "")} |'
        rows.append(line)
    return '\n'.join(rows)


def platform_findings_block(result, pk, platform_label, topics=None):
    """平台小节的「分析判断 + 结构拆解」内容块。

    只放该平台的发现，按 topic 分组：
        效率/集中度/象限/相关性 → 分析判断
        结构/节奏            → 结构拆解
    """
    findings = result.get('by_platform', {}).get(platform_label, [])
    if topics:
        findings = [f for f in findings if f.topic in topics]
    if not findings:
        return '', ''

    judged = [f for f in findings if f.topic in ('效率', '集中度', '象限', '相关性', '留存')]
    structure = [f for f in findings if f.topic in ('结构', '节奏')]

    judge_lines = []
    for f in judged:
        judge_lines.append(
            f'**{f.phenomenon}。** {f.data}。{f.judgment}\n\n'
            f'（置信度：{f.confidence} —— 依据：{f.basis}）\n\n'
            f'> **反例 / 边界：** {f.counter}')

    struct_lines = []
    for f in structure:
        struct_lines.append(f'- **{f.phenomenon}：** {f.data}。{f.judgment}'
                            f'（置信度：{f.confidence}）')

    return '\n\n'.join(judge_lines), '\n'.join(struct_lines)


def counterexample_block(result, pk, platform_label):
    """反例块：优先取「伪爆款 / 无效内容」类的发现。"""
    findings = result.get('by_platform', {}).get(platform_label, [])
    candidates = [f for f in findings
                  if any(t in f.tags for t in ('伪爆款', '放量', '无效', '低基数', '负增长'))]
    if not candidates:
        candidates = [f for f in findings if f.topic in ('效率', '象限')]
    if not candidates:
        return ''
    f = candidates[0]
    return (f'**反例（同样重要）：** {f.phenomenon}。{f.data}。{f.judgment}\n\n'
            f'> 推翻条件：{f.counter}')


def data_facts_block(result, pk, platform_label, overall=None):
    """数据事实：只写数字与倍数关系，不写判断。

    有内容级数据 → 给出效率分布的事实；
    没有 → 回退到账号级事实（粉丝净增、取关率），不返回空串。
    """
    unified = result.get('unified')
    facts = []
    if unified is not None and len(unified) > 0:
        sub = unified[unified['platform_key'] == pk]
        if len(sub) > 0:
            base = result.get('baseline', {}).get(pk, {})
            total_v = pd.to_numeric(sub['views'], errors='coerce').sum()
            total_f = pd.to_numeric(sub['followers'], errors='coerce').sum()
            eff = pd.to_numeric(sub['每千涨粉'], errors='coerce').dropna()
            facts.append(
                f'本期样本 {len(sub)} 条内容，合计曝光 {_count(total_v)}，'
                f'合计涨粉 {_count(total_f)}；'
                f'每千涨粉中位数 {_fmt(base.get("median"), "", 2)}，'
                f'P75 {_fmt(base.get("p75"), "", 2)}，'
                f'最高 {_fmt(base.get("max"), "", 2)}，最低 {_fmt(base.get("min"), "", 2)}。')
            if len(eff) > 1 and eff.median() > 0:
                extra = f'效率最高值为中位数的 {eff.max() / eff.median():.1f} 倍'
                if eff.min() and eff.min() > 0:
                    extra += f'，最高与最低相差 {eff.max() / eff.min():.1f} 倍'
                facts.append(extra + '。')

    # 账号级事实：所有平台都能给
    if overall:
        for line in overall.split('\n'):
            if line.startswith('|') and ('净增' in line or '取关率' in line):
                cells = [c.strip() for c in line.strip('|').split('|')]
                if len(cells) >= 2 and cells[0] and not cells[0].startswith('-'):
                    label = cells[0]
                    value = cells[1]
                    note = cells[2] if len(cells) > 2 else ''
                    facts.append(f'{label} {value}'
                                 + (f'（{note}）' if note else '') + '。')
    if not facts:
        return ''
    return '**数据事实：** ' + ''.join(facts)


# ============================================================
# 五、跨平台综合
# ============================================================
def cross_platform_section(result):
    """跨平台综合：只做定性分工与结构规律，不做数值排名。"""
    lines = ['## 五、跨平台综合分析\n\n']

    # 5.1 结构规律：跨平台都成立的编码
    lines.append('## 5.1 内容结构规律\n\n')
    lines.append('> 只描述**已发布内容**的共同结构，不给选题清单、不给新标题。\n\n')
    lines.append('| 结构编码 | 跨平台证据 | 当前判断 |')
    lines.append('|---|---|---|')
    struct = [f for f in result.get('findings', [])
              if f.topic == '结构' and f.confidence in ('高', '中')]
    if struct:
        for f in struct:
            lines.append(f'| 标题含「{f.metric}」 | {f.data} | {f.judgment} '
                         f'（置信度：{f.confidence}） |')
    else:
        lines.append('| 本期无达到中置信度的跨平台结构规律 | '
                     '各平台样本量均不足以支撑结构结论 | '
                     '需补样本后复算，不写成规律 |')
    lines.append('')

    # 5.2 平台分工：定性
    lines.append('## 5.2 平台分工\n\n')
    lines.append('> 只做**定性**分工，不做跨平台数值排名（各平台分母口径不同）。\n\n')
    roles = []
    for pk, label in (('douyin', '抖音'), ('shipinhao', '视频号'), ('xiaohongshu', '小红书')):
        unified = result.get('unified')
        if unified is None or len(unified) == 0:
            break
        sub = unified[unified['platform_key'] == pk]
        if len(sub) == 0:
            continue
        base = result.get('baseline', {}).get(pk, {})
        reach = [x for x in result.get('reach_vs_eff', []) if x['platform_key'] == pk]
        role = ''
        if reach:
            r = reach[0]
            amp = r['倍数']
            hi_eff = r['高曝光组效率中位数']
            lo_eff = r['低曝光组效率中位数']
            if r.get('低曝光组零效率'):
                role = ('低曝光内容的单位价值产出为 0 —— **全部涨粉来自高曝光内容**，'
                        '曝光不足的内容基本不产生转化')
            elif amp == amp and amp >= 1.2:
                role = '高曝光内容的单位价值产出也更高 —— **承接与放量兼具**，是涨粉主阵地'
            elif amp == amp and amp <= 0.85:
                role = ('高曝光内容的单位价值产出反而更低 —— **以触达为主**，'
                        '涨粉更依赖少数爆款拉平均值')
            else:
                role = '高曝光与低曝光内容的效率接近 —— **触达规模与价值产出基本解耦**'
            if not r.get('样本充足', True):
                role += '（样本不足，仅作方向性参考）'
        conc = result.get('concentration', {}).get(pk, {})
        if conc.get('Top3'):
            role += f'（Top3 占 {_pct(conc["Top3"]["涨粉占比"])} 涨粉）'
        roles.append(f'- **{label}：** {role} —— '
                     f'每千涨粉中位数 {_fmt(base.get("median"), "", 2)}，'
                     f'样本 {base.get("n", 0)} 条')
    lines.append('\n'.join(roles) + '\n' if roles else '- 本期无可用于分工判定的数据\n')
    lines.append('\n')

    # 5.3 本期最重要的数据问题
    lines.append('## 5.3 本期最重要的数据问题\n\n')
    lines.append('> 每条格式：**问题名 —— 现象+数据 → 需补采的数据 / 待验证的假设**。\n'
                 '> 箭头右边**只写数据侧动作**，不写「该做什么内容」。\n\n')
    # 挑选策略：
    #   1. 置信度优先 —— 「最重要的数据问题」不该由一条低置信度的待验证项领衔
    #   2. 同一 topic 最多 1 条 —— 否则三条都是「集中度高」，没有信息量
    #   3. 主题优先级：结构规律 → 留存差异 → 相关性反直觉 → 集中度 → 效率 → 缺口
    topic_order = ['结构', '留存', '相关性', '集中度', '效率', '缺口']
    conf_rank = {'高': 0, '中': 1, '低': 2}
    candidates = []
    for topic in topic_order:
        group = [f for f in result.get('findings', [])
                 if f.topic == topic
                 # 排除低基数假象 —— 那是平台小节里的细节，
                 # 提到「本期最重要的问题」级别会误导
                 and '低基数' not in f.tags]
        if not group:
            continue
        best = min(group, key=lambda f: (conf_rank.get(f.confidence, 3),
                                        -abs(f.value) if f.value == f.value else 0))
        candidates.append((topic, best))
    candidates.sort(key=lambda t: (conf_rank.get(t[1].confidence, 3),
                                   topic_order.index(t[0])))
    problems = [f for _, f in candidates[:5]]
    for i, f in enumerate(problems, 1):
        lines.append(f'{i}. **{f.phenomenon}：** {f.data} → {f.counter}\n')
    lines.append('\n---\n\n')
    return '\n'.join(lines)


# ============================================================
# 七、数据缺口
# ============================================================
def limitations_block(result, scope_rows):
    """第二章「统一限制」：自动列出本期所有会影响解读的口径限制。

    这些限制必须逐条写明 —— 混用口径得出的结论是错的，
    而读者往往默认「表里的数可以直接比」。
    """
    limits = []

    # 1. 内容级窗口限制
    if result and result.get('window_note'):
        note = result['window_note']
        # 去掉 window_note 自带的「内容级分析窗口：」前缀，避免重复
        note = note.replace('内容级分析窗口：', '').strip()
        limits.append(f'- **内容级分析窗口：** {note}。'
                      f'窗口内的内容是「滚动区间内发布的全部作品」，'
                      f'不是报告月新发作品')

    # 2. 各数据源区间不一致
    if scope_rows:
        spans = {}
        for plat, acc, s, e, prefix, src, concl in scope_rows:
            spans.setdefault(f'{plat}·{acc}', []).append((s, e))
        for key, se in sorted(spans.items()):
            if len(se) < 2:
                continue
            ends = [x[1] for x in se if x[1] != '—']
            starts = [x[0] for x in se if x[0] != '—']
            if not ends or not starts:
                continue
            earliest = min(starts)
            latest = max(ends)
            if earliest != latest:
                limits.append(
                    f'- **{key}：** 存在 {len(se)} 套不同口径的导出，'
                    f'覆盖区间 {earliest} ~ {latest} 不一致，'
                    f'各口径数值不可直接相加或互相比较')

    # 3. 缺粉丝总数的平台由 fan_missing_note 单独提示，不重复
    return '\n'.join(limits) if limits else \
        '- 本期各数据源口径一致，无特殊限制'


def experiment_section(result):
    """第六章「验证方向」：从计算层的结构发现生成**候选实验设计**。

    严格遵守方法论 §七 与 §八：
      - 只写**编码变量**（哪个结构要验证），不写标题、选题、脚本
      - 样本条数是「需要的样本量」，不是要产出的内容条数
      - 判断指标必须是效率指标，不是播放量
      - 每条都给观察窗口与止损条件

    这里生成的是**候选方向**，是否采纳仍需人工判断。
    """
    struct = [f for f in result.get('findings', [])
              if f.topic == '结构' and f.confidence in ('高', '中')]
    if not struct:
        return ('> **本期未生成候选验证方向**：'
                '没有达到中置信度的结构发现可供验证。'
                '需先补样本，再重算分组效率。')

    lines = ['| 待验证的编码方向 | 名额（样本条数） | 验证设计（只描述变量） '
             '| 主要判断指标 | 观察窗口 | 止损条件 |',
             '|---|---:|---|---|---|---|']
    for f in struct:
        # 名额按命中组现有样本量决定：至少 3 条才能观察中位数差异
        n_hit = 3
        for part in f.data.split('，'):
            if part.startswith('命中组 n='):
                try:
                    n_hit = int(part.split('=')[1].split()[0])
                except (ValueError, IndexError):
                    pass
        need = max(3, min(5, n_hit))
        lines.append(
            f'| 标题含「{f.metric}」 | {need} | '
            f'同一选题类型，只改变标题是否包含 {f.metric} 这一变量，其余编码不变 | '
            f'每千涨粉（辅看每千收藏） | 30 天 | '
            f'连续 2~3 期判断指标未优于基线即停 |')
    lines.append('')
    lines.append('> 表中「名额」是**需要的样本条数**，不是本 skill 要产出的内容条数。')
    lines.append('> 以上为候选方向，是否采纳、具体如何执行由人工判断。')
    return '\n'.join(lines)
    lines.append('')
    lines.append('> 表中「名额」是**需要的样本条数**，不是本 skill 要产出的内容条数。')
    lines.append('> 以上为候选方向，是否采纳、具体如何执行由人工判断。')
    return '\n'.join(lines)


def todo_section(result):
    """第六章「必做事项」：只写数据侧动作，可验收。"""
    items = []
    for f in result.get('findings', []):
        if f.topic == '缺口':
            items.append(f'补采{f.platform}的「{f.metric}」并落盘到对应账号快照目录')
    # 始终必做的：商单/自然分层
    items.append('给每条内容补「商单 / 自然」标记（可从 `商单投放/` 目录按发布时间反查），'
                 '完成后重算分组效率')
    items.append('核对各平台单作品明细的统计日是否统一，不统一的分组不可直接比较')
    lines = [f'- [ ] {i}' for i in items]
    return '\n'.join(lines)


def not_do_section(result):
    """第六章「明确不做」：写下这期不做什么，附原因。

    只从数据出发（如「某结构被判低置信度，本期不改」），不写创作决策。
    """
    items = []
    seen = set()
    # 低置信度的结构 → 本期不作为方向（同一特征只写一次，跨平台合并）
    for f in result.get('findings', []):
        if f.topic != '结构' or f.confidence != '低':
            continue
        if f.metric in seen:
            continue
        seen.add(f.metric)
        plats = [x.platform for x in result.get('findings', [])
                 if x.topic == '结构' and x.metric == f.metric and x.confidence == '低']
        plat_s = '、'.join(sorted(set(plats)))
        items.append(f'不把「标题含{f.metric}」当作已验证结论 —— '
                     f'{plat_s} 上的效率差异未通过过度表现检验，本期只作待验证')
    # 单平台样本不足的
    if any('低基数' in ' '.join(f.tags) for f in result.get('findings', [])):
        items.append('不把单条「高每千涨粉」内容当作效率标杆 —— '
                     '其分母过小，绝对贡献极低')
    items.append('不做跨平台的内容效率排名 —— 各平台分母口径不同，'
                 '排名没有可比性')
    if not items:
        items.append('本期无明确的不做项')
    return '\n'.join(f'- {i}' for i in items)


def collection_note(result, scope_rows):
    """附录「采集说明」：本期数据是怎么来的、有什么限制。

    从数据范围表推导，不手写。
    """
    lines = []
    if scope_rows:
        plats = sorted({r[0] for r in scope_rows})
        accs = sorted({f'{r[0]}·{r[1]}' for r in scope_rows})
        lines.append(f'- 本期共 {len(scope_rows)} 个数据源，覆盖 {len(accs)} 个平台·账号'
                     f'（{ "、".join(plats) }），全部来自各平台后台原始导出，'
                     f'已按「平台 / 账号 / 快照日期」三层归档至 `账号数据/`。')
        multi = [f'{r[0]}·{r[1]}' for r in scope_rows
                 if len([x for x in scope_rows
                         if (x[0], x[1]) == (r[0], r[1])]) > 1]
        if multi:
            lines.append(f'- { "、".join(sorted(set(multi))) } 存在多套口径的导出，'
                         f'报告内已按口径分列，不做跨口径相加。')
    if result and result.get('window_note'):
        lines.append(f'- {result["window_note"]}。')
    lines.append('- 页面摘录类文件（如「近期稿件对比」）不参与趋势计算，'
                 '仅在需要人工核对时查看。')
    lines.append('- 所有效率指标均在**同平台内**计算并比较；'
                 '跨平台的每千涨粉数值因分母口径不同，不做排名。')
    return '\n'.join(lines)


def gap_section(result):
    gaps = [f for f in result.get('findings', []) if f.topic == '缺口']
    lines = ['| 缺口 | 影响 | 补齐方式 | 优先级 |', '|---|---|---|---|']
    for f in gaps:
        pri = '高' if f.platform in ('微信公众号', 'B站') else '中'
        # judgment 里带「影响：」前缀，表格里去掉
        impact = f.judgment.replace('影响：', '').strip()
        lines.append(f'| {f.platform} 缺少 {f.metric} | {impact} | '
                     f'{f.counter} | {pri} |')
    if len(gaps) == 0:
        lines.append('| 本期各平台数据齐备 | — | — | — |')
    return '\n'.join(lines)


def confidence_section(result):
    """结论置信度分级。"""
    findings = result.get('findings', [])
    high = [f for f in findings if f.confidence == '高']
    mid = [f for f in findings if f.confidence == '中']
    low = [f for f in findings if f.confidence == '低']
    lines = []
    lines.append(f'- **高置信度：** ' + ('；'.join(f'{f.platform}·{f.phenomenon}'
                                            for f in high) if high else '本期无'))
    lines.append(f'- **中置信度：** ' + ('；'.join(f'{f.platform}·{f.phenomenon}'
                                            for f in mid[:6]) if mid else '本期无'))
    lines.append(f'- **待验证：** ' + ('；'.join(f'{f.platform}·{f.phenomenon}'
                                          for f in low[:6]) if low else '本期无'))
    lines.append('- **不可判断：** 跨平台的内容效率对比（各平台分母口径不同）；'
                 '商单与自然内容的分层效果（原始数据无商单标记，本期未分层）')
    return '\n'.join(lines)
