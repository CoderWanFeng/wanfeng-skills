#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/findings.py - 结构化发现条目

这一层解决 skill 目前最大的问题：**报告里没有分析**。

现在 `monthly_report.py` 是从「整体表现」表格里 grep「净增」两个字拼出判断句，
结果五个平台的判断文字一模一样。有了 findings，每条发现都带：

    现象   看到了什么（客观描述）
    数据   支撑它的数字（带单位）
    判断   这说明了什么（推论，与现象分开）
    依据   置信度为什么是高/中/低（样本量、口径、交叉验证）
    反例   能推翻这条的样本或数据缺口

**重要边界**：findings 只输出「数据能支撑的事实 + 有限的推论」，
不下内容创作建议（不写标题、不写选题、不写排期）。
方法论 §八 与 SKILL.md L0 边界对此有硬性要求。
"""

from dataclasses import dataclass, field, asdict
from typing import Any

import pandas as pd

from . import efficiency


@dataclass
class Finding:
    """一条结构化发现"""
    platform: str                      # 平台
    topic: str                         # 主题：效率 / 集中度 / 象限 / 相关性 / 节奏 / 结构
    phenomenon: str                    # 现象（客观）
    data: str                          # 数据（带单位）
    judgment: str                      # 判断（推论）
    confidence: str = '中'             # 高 / 中 / 低
    basis: str = ''                    # 置信度依据
    counter: str = ''                  # 反例或推翻条件
    metric: str = ''                   # 核心指标名
    value: float = float('nan')        # 核心指标数值（便于排序）
    tags: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def to_markdown(self, index=None):
        head = f'**{index}. {self.platform}：{self.phenomenon}**' if index else \
            f'**{self.platform}：{self.phenomenon}**'
        lines = [head, f'{self.data}。{self.judgment}']
        meta = f'（置信度：{self.confidence}）'
        if self.basis:
            meta += f' —— 依据：{self.basis}'
        lines.append(meta)
        if self.counter:
            lines.append(f'> **反例/边界：** {self.counter}')
        return '\n\n'.join(lines)


# ============================================================
# 置信度判定
# ============================================================
def confidence_by_sample(n, has_counter=False, has_crosscheck=False):
    """按方法论 §五 的标准判定置信度。

    高 = 完整口径 + 可交叉验证 + 有反例检验过 + 样本 ≥ 10
    中 = 单数据源 / 样本有限 / 有未排除干扰
    低 = 样本 < 3 / 窗口重叠 / 口径不明
    """
    if n < 3:
        return '低'
    if n >= 10 and has_counter and has_crosscheck:
        return '高'
    if n >= 10:
        return '中'
    return '低'


def _fmt(n, unit='', digits=1):
    """数字格式化。

    计数类（曝光/涨粉/条数）必须是整数 —— 「涨粉 346.0」会让人以为
    数据有问题。带小数的只保留给效率指标这类连续量。
    """
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
# 各类发现生成器
# ============================================================
def efficiency_findings(unified, min_n=3):
    """效率发现：哪些内容是真爆款，哪些是伪爆款。"""
    out = []
    if unified is None or len(unified) == 0 or '象限' not in unified.columns:
        return out

    for pk, sub in unified.groupby('platform_key'):
        platform = sub['platform'].iloc[0]
        n = len(sub)
        if n < 2:
            continue

        # 最高效率内容
        eff = pd.to_numeric(sub['每千涨粉'], errors='coerce').dropna()
        if len(eff) == 0:
            continue
        med = eff.median()
        top = sub.nlargest(1, '每千涨粉').iloc[0]
        top_eff = float(top['每千涨粉'])
        total_f = pd.to_numeric(sub['followers'], errors='coerce').sum()
        top_contrib = float(top['followers']) / total_f * 100 if total_f else float('nan')

        # 最高效率那条是不是同时也是「被埋没」那条？
        # 是的话合并成一条判断 —— 同一条内容说两遍会稀释重点，
        # 而且「效率最高」这个说法本身会误导（读者以为它是效率冠军）
        is_buried = (top.get('触达') == '低触达' and top.get('价值') == '高价值')

        if med > 0 and top_eff > med:
            ratio = top_eff / med
            # 小基数陷阱：效率最高但绝对贡献很低 → 不是真冠军
            # 判定要同时看两个信号：
            #   曝光低于平台中位数的 25%（分母小，率必然虚高）
            #   涨粉贡献占比低于 10%（绝对价值也小）
            # 只满足其一不足以判定，两者同时成立才说明是「假效率」
            view_med = pd.to_numeric(sub['views'], errors='coerce').median()
            # 小基数判定要同时看相对比例和绝对分母：
            #   相对 —— 曝光低于曝光中位线的 25%
            #   绝对 —— 曝光低于 500（这个量级算出的「每千」几乎没有统计意义）
            # 只看相对比例会漏掉「整平台曝光都低」的情况：
            # 小红书曝光中位数只有 150，118 曝光就已经是「低于中位线」，
            # 但 118 这个绝对量本身太小，每千涨粉 42 是分母噪声。
            tiny_base = (float(top['views']) < view_med * 0.25
                         or float(top['views']) < efficiency.MIN_VIEWS_FLOOR * 5)
            low_contrib = top_contrib < 10
            tags = ['效率', '头部']
            if tiny_base and low_contrib:
                phenomenon = f'效率数字最高的一条（每千涨粉 {top_eff:.2f}）实际是低基数假象'
                judgment = (f'该条曝光仅 {_count(top["views"])}（平台中位数的 '
                            f'{float(top["views"])/view_med:.2f} 倍），涨粉 {_count(top["followers"])}，'
                            f'占平台总涨粉仅 {_pct(top_contrib)} —— '
                            f'每千涨粉被小分母抬高了，绝对贡献却很小，'
                            f'不能当作效率冠军')
                conf = '低'
                counter = '需补更多同量级样本，才能判断该内容是题材有效还是偶然'
                tags = ['效率', '低基数']
            elif is_buried and tiny_base:
                # 埋在低触达象限，且分母极小 → 仍是低基数假象
                # 注意：只判 tiny_base 不判 low_contrib ——
                # 抖音那条曝光虽低但接近曝光中位线（0.97 倍），
                # 它是真发现（内容能打但没拿到分发），不该降级
                phenomenon = (f'效率数字最高的一条（每千涨粉 {top_eff:.2f}）'
                              f'实际是低基数假象')
                judgment = (f'该条曝光仅 {_count(top["views"])}（平台中位数的 '
                            f'{float(top["views"])/view_med:.2f} 倍），'
                            f'涨粉 {_count(top["followers"])}，'
                            f'占平台总涨粉仅 {_pct(top_contrib)} —— '
                            f'每千涨粉被小分母抬高了，不能当作效率冠军')
                conf = '低'
                counter = '需补更多同量级样本，才能判断该内容是题材有效还是偶然'
                tags = ['效率', '低基数']
            elif is_buried:
                # 合并：这条既是效率最高，也落在「低触达」象限
                phenomenon = (f'效率最高的一条落在低触达象限 —— '
                              f'内容能打但没拿到分发')
                judgment = (f'该条每千涨粉 {top_eff:.2f}，是平台中位数的 {ratio:.1f} 倍，'
                            f'但曝光只有 {_count(top["views"])}（平台中位数的 '
                            f'{float(top["views"])/view_med:.2f} 倍，'
                            f'即低于曝光中位线），'
                            f'涨粉 {_count(top["followers"])}，'
                            f'仅占平台总涨粉 {_pct(top_contrib)} —— '
                            f'题材本身能打，问题出在曝光环节。'
                            f'这是本期最值得追查的一条：'
                            f'同样的单位价值如果能拿到正常曝光，'
                            f'账号涨粉结构会明显不同')
                conf = '中'
                counter = ('曝光低也可能是发布后统计窗口不足，'
                           '需先核对各条统计日是否统一')
            elif low_contrib:
                phenomenon = f'效率最高的一条绝对贡献偏低，效率优势不等于影响力'
                judgment = (f'该条每千涨粉 {top_eff:.2f} 是中位数的 {ratio:.1f} 倍，'
                            f'但只贡献 {_pct(top_contrib)} 的涨粉 —— '
                            f'它的单位价值高，体量却小，'
                            f'说明这类内容「有效但不被分发」，'
                            f'账号大盘仍由放量内容撑起')
                conf = '低'
                counter = '需确认该条是题材有效还是偶然；样本量小，暂不下结论'
            else:
                phenomenon = f'单条内容效率达到平台中位数的 {ratio:.1f} 倍'
                judgment = (f'这条内容用 {_count(top["views"])} 曝光换到 {_count(top["followers"])} 涨粉，'
                            f'单位曝光的价值产出明显高于账号常态，'
                            f'是本期最有效的转化样本')
                conf = confidence_by_sample(n, has_counter=True)
                counter = '需确认该条是否含投流或平台活动加成，否则效率归因会被高估'
            out.append(Finding(
                platform=platform,
                topic='效率',
                phenomenon=phenomenon,
                data=f'每千涨粉 {_fmt(top_eff, "", 2)}，平台中位数 {_fmt(med, "", 2)}；'
                     f'曝光 {_count(top["views"])}，涨粉 {_count(top["followers"])}，'
                     f'占平台总涨粉 {_pct(top_contrib)}',
                judgment=judgment,
                confidence=conf,
                basis=f'n={n} 条内容，同平台内中位数切分',
                counter=counter,
                metric='每千涨粉', value=top_eff,
                tags=tags,
            ))

        # 伪爆款：曝光高但效率低
        hi_reach = sub[sub['触达'] == '高触达']
        if len(hi_reach) >= 2:
            fake = hi_reach.nsmallest(1, '每千涨粉').iloc[0]
            fake_eff = float(fake['每千涨粉'])
            if med > 0 and fake_eff < med * 0.6:
                hi_eff = pd.to_numeric(hi_reach['每千涨粉'], errors='coerce').median()
                out.append(Finding(
                    platform=platform,
                    topic='效率',
                    phenomenon='存在高曝光但转化效率显著低于中位数的「伪爆款」',
                    data=f'该条曝光 {_count(fake["views"])}，每千涨粉仅 {_fmt(fake_eff, "", 2)}，'
                         f'平台中位数 {_fmt(med, "", 2)}；'
                         f'高触达组整体效率中位数 {_fmt(hi_eff, "", 2)}',
                    judgment='流量拿到了但没转化成关注 —— 这类内容属于触达型，'
                             '它的曝光规模不能当作内容价值证据，复制它不会带来同等涨粉',
                    confidence=confidence_by_sample(len(hi_reach)),
                    basis=f'高触达组 n={len(hi_reach)}',
                    counter='若该条为商单内容，投放流量会天然压低自然转化率，需先做商单/自然分层',
                    metric='每千涨粉', value=fake_eff,
                    tags=['效率', '伪爆款'],
                ))

        # 埋没内容：效率高但曝光低
        # 若最高效率那条就是它，已在上面合并成一条判断，不重复输出
        buried = sub[(sub['触达'] == '低触达') & (sub['价值'] == '高价值')]
        if len(buried) >= 1 and not is_buried:
            b = buried.nlargest(1, '每千涨粉').iloc[0]
            b_eff = float(b['每千涨粉'])
            b_contrib = float(b['followers']) / total_f * 100 if total_f else float('nan')
            out.append(Finding(
                platform=platform,
                topic='效率',
                phenomenon='存在效率达标但曝光不足的内容（被分发埋没）',
                data=f'该条曝光仅 {_count(b["views"])}，每千涨粉 {_fmt(b_eff, "", 2)}，'
                     f'为平台中位数的 {b_eff/med:.1f} 倍，'
                     f'但占平台总涨粉仅 {_pct(b_contrib)}（n={len(buried)} 条落入该象限）',
                judgment='题材本身能打，但没拿到分发 —— 这类内容的问题在曝光环节，'
                         '不在内容质量环节，与「伪爆款」是两类相反的问题',
                confidence='低' if len(buried) < 2 else '中',
                basis=f'低触达×高价值象限 n={len(buried)}',
                counter='曝光低也可能是发布后统计窗口不足，需核对统计日是否统一',
                metric='每千涨粉', value=b_eff,
                tags=['效率', '埋没'],
            ))
    return out


def concentration_findings(unified, conc):
    """集中度发现：成绩靠少数内容还是整体铺量。"""
    out = []
    for pk, sub in unified.groupby('platform_key'):
        platform = sub['platform'].iloc[0]
        p = conc.get(pk)
        if not p or 'Top3' not in p:
            continue
        ev = p['Top3']['曝光占比']
        ef = p['Top3']['涨粉占比']
        if ev != ev or ef != ef:
            continue
        amp = p.get('Top3涨粉放大倍数')
        amp_s = f'{amp:.2f}' if amp == amp else '—'
        n = p['n']

        # 判断分四种情况，不能一律说「高度依赖头部」：
        #   1. 涨粉集中度显著高于曝光集中度 → 头部不只是拿量，是价值来源
        #   2. 涨粉绝对占比高但与曝光集中度相当 → 集中是结构性的，不是效率差
        #   3. 曝光集中但涨粉没跟上 → 触达型集中，价值没沉淀
        #   4. 都不高 → 整体铺量
        if amp == amp and amp >= 1.25:
            judgment = (f'涨粉集中度（{amp:.2f} 倍）高于曝光集中度 —— '
                        f'头部内容不只是拿到了量，单位曝光的价值产出也更高，'
                        f'是账号涨粉的主要来源')
        elif ef >= 50 and n >= 5:
            judgment = (f'账号成绩高度依赖头部内容：Top3 一组就贡献了 {_pct(ef)} 的涨粉。'
                        f'这种结构下，单条内容的波动会直接放大到账号大盘，'
                        f'样本一旦收窄结论就会失真')
        elif ev >= 60 and ef <= ev:
            judgment = (f'曝光集中在头部，但涨粉没有跟着集中 —— 流量分布与价值分布脱钩，'
                        f'说明头部内容带来的是触达而非沉淀')
        else:
            judgment = (f'涨粉未过度集中（Top3 {_pct(ef)}），账号增长来自整体铺量，'
                        f'不存在单条依赖风险')
        out.append(Finding(
            platform=platform,
            topic='集中度',
            phenomenon=f'Top3 内容占 {_pct(ev)} 曝光、{_pct(ef)} 涨粉',
            data=f'涨粉集中度是曝光集中度的 {amp_s} 倍；'
                 f'总曝光 {_count(p["总曝光"])}，总涨粉 {_count(p["总涨粉"])}，n={n}',
            judgment=judgment,
            confidence=confidence_by_sample(n),
            basis=f'n={n} 条内容',
            counter='若头部包含商单内容，其涨粉来自投放而非内容，需分层后重算',
            metric='Top3涨粉占比', value=ef,
            tags=['集中度'],
        ))
    return out


def quadrant_findings(unified, quad_rows):
    """象限发现：流量与价值是否同向。"""
    out = []
    # 按 (平台, 象限) 去重 —— quad_rows 是逐平台算的，同一象限名会出现多次
    seen = set()
    for row in quad_rows:
        pk = row.get('platform_key', '')
        q = row['象限']
        key = (pk, q)
        if key in seen:
            continue
        seen.add(key)
        if row['条数'] < 2:
            continue
        # 必须同时按象限和平台筛 —— 只按象限筛会把别的平台的象限数据算进来
        sub = unified[(unified['象限'] == q) & (unified['platform_key'] == pk)]
        if len(sub) == 0:
            continue
        platform = sub['platform'].iloc[0]
        # 高触达低价值：吃掉大部分曝光，贡献少量涨粉
        if q == '高触达 × 低价值':
            out.append(Finding(
                platform=platform,
                topic='象限',
                phenomenon='高触达低价值的「放量内容」吃掉了大部分曝光',
                data=f'该象限 {row["条数"]} 条，占 {_pct(row["曝光占比"])} 曝光，'
                     f'只带来 {_pct(row["涨粉占比"])} 涨粉；'
                     f'效率中位数 {_fmt(row["效率中位数"], "", 2)}',
                judgment='这部分曝光是分发给的，不是内容挣来的 —— '
                         '把它当成「内容有效」的证据会高估选题能力',
                confidence='中',
                basis=f'象限 n={row["条数"]}',
                counter='若该象限含商单内容，曝光占比天然偏高，需分层后重算',
                metric='曝光占比', value=row['曝光占比'],
                tags=['象限', '放量'],
            ))
        if q == '高触达 × 高价值':
            out.append(Finding(
                platform=platform,
                topic='象限',
                phenomenon='高触达高价值的「承接内容」同时拿到量与转化',
                data=f'该象限 {row["条数"]} 条，占 {_pct(row["曝光占比"])} 曝光、'
                     f'{_pct(row["涨粉占比"])} 涨粉；'
                     f'效率中位数 {_fmt(row["效率中位数"], "", 2)}，P75 {_fmt(row["效率P75"], "", 2)}',
                judgment='这是账号真正的护城河 —— 同样的曝光结构下，'
                         '这组内容的单位价值产出显著高于其它象限',
                confidence='中',
                basis=f'象限 n={row["条数"]}',
                counter='样本量偏小时中位数不稳定，需补样本复算',
                metric='涨粉占比', value=row['涨粉占比'],
                tags=['象限', '承接'],
            ))
    return out


def relation_findings(matrix, surprise):
    """相关性发现：哪个指标真正驱动涨粉。"""
    out = []
    for s in surprise:
        n = s.get('n', 0)
        conf = '中' if n >= 20 else '低'
        out.append(Finding(
            platform=s['platform'],
            topic='相关性',
            phenomenon=f'「{s["关系"]}」与预期不符',
            data=f'r = {s["r"]:.3f}（{s["强度"]}，n={n}，同平台内）',
            judgment=s['说明'],
            confidence=conf,
            basis=f'同平台内 Pearson 相关，n={n}，已剔除 IQR 极值点',
            counter='相关不等于因果；需控制发布时段、内容类型等混杂变量后复算',
            metric=s['关系'], value=s['r'],
            tags=['相关性'],
        ))
    return out


def feature_findings(feature_rows, platform, min_n=3, overperform=None):
    """标题特征分组发现：哪类结构在效率上真的更高。

    两道检验，缺一不可：
        1. 效率中位数对比（命中组 vs 未命中组）
        2. 过度表现检验（该组占多少条、贡献多少涨粉）

    只有第 1 道会被小基数骗：某个特征命中 2 条、每千涨粉很高，
    但两条加起来只贡献 5% 涨粉 —— 那不是「这个结构有效」，
    只是「这两条恰好分母小」。
    """
    out = []
    overperform = overperform or {}
    for row in feature_rows:
        if not row['可下结论']:
            continue
        ratio = row['倍数']
        if ratio != ratio:
            continue
        if ratio >= 1.3:
            direction = '更高'
        elif ratio <= 0.77:
            direction = '更低'
        else:
            continue

        # 过度表现检验：命中组的涨粉贡献 vs 条数占比
        hit = overperform.get(row['特征'], {})
        amp_hit = hit.get(True)
        amp_s = ''
        strong = None
        if amp_hit is not None and amp_hit == amp_hit:
            amp_s = f'；命中组涨粉贡献是样本占比的 {amp_hit:.2f} 倍'
            strong = amp_hit >= 1.5

        if strong:
            conf = '中'
            judgment = (f'该结构在本平台样本内不仅效率{direction}，'
                        f'贡献的涨粉份额也超过其内容条数占比 —— '
                        f'是本期最值得下期验证的结构方向（当前为相关，非因果）')
        else:
            conf = '低'
            judgment = (f'该结构在本平台样本内与效率{direction}相关，'
                        f'但其涨粉贡献份额未超过样本占比，'
                        f'可能只是小基数波动，仅列为待验证方向')

        out.append(Finding(
            platform=platform,
            topic='结构',
            phenomenon=f'标题含「{row["特征"]}」的内容，每千涨粉中位数{direction}',
            data=f'命中组 n={row["命中n"]}，效率中位数 {_fmt(row["命中中位数"], "", 2)}，'
                 f'贡献 {_pct(row["命中涨粉占比"])} 涨粉；'
                 f'未命中组 n={row["未命中n"]}，效率中位数 {_fmt(row["未命中中位数"], "", 2)}；'
                 f'相差 {ratio:.2f} 倍{amp_s}',
            judgment=judgment,
            confidence=conf,
            basis=f'命中 n={row["命中n"]}，未命中 n={row["未命中n"]}，'
                  f'同平台内中位数 + P75 比较，并做过度表现检验',
            counter='需回到全量内容确认该特征不是只在头部出现；'
                    '若全量内容都有，则不是有效因子',
            metric=row['特征'], value=ratio,
            tags=['结构'],
        ))
    return out


def rhythm_findings(unified):
    """发布节奏发现：频率与效率的关系（只作观察变量，不给排期建议）。"""
    out = []
    if unified is None or len(unified) == 0:
        return out
    for pk, sub in unified.groupby('platform_key'):
        platform = sub['platform'].iloc[0]
        if len(sub) < 6:
            continue
        work = sub.dropna(subset=['publish_time']).copy()
        if len(work) < 6:
            continue
        work = work.sort_values('publish_time')
        gaps = work['publish_time'].diff().dt.total_seconds().div(86400)
        work['间隔天数'] = gaps
        work = work[work['间隔天数'].notna() & (work['间隔天数'] <= 60)]
        if len(work) < 5:
            continue

        med_gap = work['间隔天数'].median()
        fast = work[work['间隔天数'] <= med_gap]
        slow = work[work['间隔天数'] > med_gap]
        e_fast = pd.to_numeric(fast['每千涨粉'], errors='coerce').dropna()
        e_slow = pd.to_numeric(slow['每千涨粉'], errors='coerce').dropna()
        if len(e_fast) < 2 or len(e_slow) < 2:
            continue
        if e_slow.median() == 0:
            continue
        ratio = float(e_fast.median() / e_slow.median())
        if 0.8 <= ratio <= 1.25:
            continue

        out.append(Finding(
            platform=platform,
            topic='节奏',
            phenomenon='发布间隔与单条效率存在差异',
            data=f'发布间隔中位数 {_fmt(med_gap, " 天", 1)}；'
                 f'密发组（n={len(e_fast)}）每千涨粉中位数 {_fmt(e_fast.median(), "", 2)}，'
                 f'疏发组（n={len(e_slow)}）{_fmt(e_slow.median(), "", 2)}，'
                 f'相差 {ratio:.2f} 倍',
            judgment=f'本期样本内，发布更密的内容单位价值产出{direction_word(ratio)}'
                     f'（仅观察变量，不构成排期建议）',
            confidence='低',
            basis=f'样本 n={len(work)}，分组后各约 {len(e_fast)}/{len(e_slow)} 条',
            counter='发布时段与内容类型常与节奏强相关，存在混杂；'
                    '本期未做时段与类型分层，不足以下结论',
            metric='间隔效率倍数', value=ratio,
            tags=['节奏'],
        ))
    return out


def direction_word(ratio):
    return '更高' if ratio > 1 else '更低'


def account_level_findings(data):
    """账号级发现：粉丝留存、取关率、账号间对比。

    这些不需要单作品数据，是各平台都能给的硬指标。
    """
    out = []

    # 取关率：涨粉质量
    bili = data.get('bilibili') or {}
    for acc, kinds in bili.items():
        fans = kinds.get('fans')
        if fans is None or len(fans) == 0:
            continue
        add = pd.to_numeric(fans['新增关注'], errors='coerce').sum()
        cancel = pd.to_numeric(fans['取消关注'], errors='coerce').sum()
        if not add or add != add:
            continue
        rate = float(cancel / add * 100)
        conf = confidence_by_sample(len(fans))
        if rate >= 30:
            judgment = (f'每 100 个新粉换来 {rate:.0f} 个取关 —— '
                        f'拉新质量偏低，涨粉没有沉淀成存量')
        elif rate <= 10:
            judgment = (f'取关率仅 {rate:.1f}% —— 拉来的粉丝留得住，'
                        f'这批存量的价值高于粉丝总数本身')
        else:
            judgment = f'取关率 {rate:.1f}%，处于常规区间'
        out.append(Finding(
            platform='B站',
            topic='留存',
            phenomenon=f'B站·{acc} 的取关率为 {rate:.1f}%',
            data=f'区间新增关注 {_count(add)}，取消关注 {_count(cancel)}，'
                 f'净增粉 {_count(add - cancel)}',
            judgment=judgment,
            confidence=conf,
            basis=f'粉丝趋势表 n={len(fans)} 天',
            counter='取关可能滞后于关注发生时间，跨月区间存在归属偏差',
            metric='取关率', value=rate,
            tags=['留存'],
        ))

    # 视频号取关率
    vf = data.get('shipinhao_fans')
    if vf is not None and len(vf) > 0:
        add = pd.to_numeric(vf['新增关注'], errors='coerce').sum()
        cancel = pd.to_numeric(vf['取消关注'], errors='coerce').sum()
        if add and add == add:
            rate = float(cancel / add * 100)
            out.append(Finding(
                platform='视频号',
                topic='留存',
                phenomenon=f'视频号取关率 {rate:.1f}%',
                data=f'区间新增关注 {_count(add)}，取消关注 {_count(cancel)}',
                judgment=(f'新粉留存显著优于其它平台（多数平台取关率在 20%~50% 区间），'
                          f'说明视频号的粉丝与内容匹配度更高，'
                          f'同等曝光下沉淀下来的存量更多')
                if rate <= 10 else
                f'取关率 {rate:.1f}%，需关注涨粉是否与内容承诺一致',
                confidence=confidence_by_sample(len(vf)),
                basis=f'关注者增长表 n={len(vf)} 天',
                counter='视频号新增关注含其它入口带入，非全部来自内容',
                metric='取关率', value=rate,
                tags=['留存'],
            ))

    # 快手净增粉丝为负
    ks = data.get('kuaishou')
    if ks is not None and len(ks) > 0:
        net = pd.to_numeric(ks['净增粉丝量'], errors='coerce').sum()
        play = pd.to_numeric(ks['播放量'], errors='coerce').sum()
        if net == net and play:
            per = float(net / play * 1000)
            out.append(Finding(
                platform='快手',
                topic='效率',
                phenomenon='快手本期净增粉丝为非正数',
                data=f'区间净增粉丝 {_count(net)}，总播放 {_count(play)}，'
                     f'每千播放净增 {_fmt(per, "", 2)}',
                judgment='有播放但没有净增粉丝，属于纯触达无沉淀 —— '
                         '本期该平台不构成有效的涨粉来源',
                confidence='低',
                basis=f'日粒度表 n={len(ks)} 天，单一账号',
                counter='样本仅一个账号、单一窗口，无法区分内容问题与冷启动阶段',
                metric='每千播放净增', value=per,
                tags=['效率', '负增长'],
            ))
    return out


def missing_data_findings(unified, data):
    """数据缺口发现：哪些结论本期答不了。"""
    out = []
    got = set(unified['platform_key'].unique()) if len(unified) else set()
    missing = [
        ('B站', 'bilibili', '单稿播放 / 涨粉 / 投币明细',
         '无法做内容级四象限与爆款识别，只能给账号级趋势',
         '在后台导出「稿件数据」明细（单稿维度），落盘到 '
         '`账号数据/bilibili-B站/<账号>/<YYMMDD>/`'),
        ('微信公众号', 'wechat', '单篇 `read_subscribe_user`（阅读后关注人数）与 `read_user_source`',
         '无法定位涨粉漏斗卡在哪一跳，也无法区分存量粉与增量曝光，'
         '只能用账号级退化公式',
         '发布后 **7 天内**导出单篇图文分析（须带 `统计日` 列），'
         '落盘为 `图文分析_YYYYMMDD.xlsx`'),
        ('快手', 'kuaishou', '单稿播放 / 涨粉明细',
         '无法做内容级归因，只能给账号级日粒度趋势',
         '在后台导出单作品数据明细，落盘到 '
         '`账号数据/kuaishou-快手/程序员晚枫/<YYMMDD>/`'),
    ]
    for platform, key, need, impact, fix in missing:
        if key not in got:
            out.append(Finding(
                platform=platform,
                topic='缺口',
                phenomenon=f'{platform} 缺少 {need}',
                data='本期原始导出未包含该文件',
                judgment=f'影响：{impact}。相关结论本期一律降级为低置信度',
                confidence='低',
                basis='文件清单核对',
                counter=fix,
                metric=need, value=float('nan'),
                tags=['缺口'],
            ))
    return out


# ============================================================
# 汇总
# ============================================================
def build_findings(data, unified, conc, quad_rows, matrix, surprise, feature_map,
                   overperform_map=None):
    """把所有来源的发现汇总、去重、按重要性排序。"""
    overperform_map = overperform_map or {}
    findings = []
    findings += efficiency_findings(unified)
    findings += concentration_findings(unified, conc)
    findings += quadrant_findings(unified, quad_rows)
    findings += relation_findings(matrix, surprise)
    for pk, rows in feature_map.items():
        label = unified[unified['platform_key'] == pk]['platform'].iloc[0] \
            if len(unified[unified['platform_key'] == pk]) else pk
        findings += feature_findings(rows, label, overperform=overperform_map.get(pk))
    findings += rhythm_findings(unified)
    findings += account_level_findings(data)
    findings += missing_data_findings(unified, data)

    # 排序：效率类优先，其次集中度、象限、相关性、结构、留存，最后缺口
    order = {'效率': 0, '集中度': 1, '象限': 2, '相关性': 3,
             '结构': 4, '留存': 5, '节奏': 6, '缺口': 7}
    findings.sort(key=lambda f: (order.get(f.topic, 9), -abs(f.value)
                                  if f.value == f.value else 0))
    return findings


def group_by_platform(findings):
    """按平台分组，报告里每节只显示相关发现。"""
    out = {}
    for f in findings:
        out.setdefault(f.platform, []).append(f)
    return out
