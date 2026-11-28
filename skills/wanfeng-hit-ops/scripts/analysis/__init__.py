#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/ - 计算层

方法论（references/hit-methodology.md）说「怎么判断」，这一层负责「算出来」。

分层：
    schema.py       各平台单作品表 → 统一内容表（口径归一）
    efficiency.py   效率指标 + 四象限 + 基线 + 分组统计
    concentration.py 帕累托集中度 + 标题特征/关键词分组对比
    relations.py    相关性矩阵 + 反直觉发现 + 涨粉路径拆解
    findings.py     结构化发现条目（现象/数据/判断/依据/反例）

纪律（对应 SKILL.md L1）：
    - 一切计算在同平台内进行，不跨平台相加、不跨平台排名
    - 基线用中位数 + P75，不用均值
    - 样本不足的结论自动降级置信度，不硬下判断
"""

from . import schema, efficiency, concentration, relations, findings  # noqa: F401

__all__ = ['schema', 'efficiency', 'concentration', 'relations', 'findings']
