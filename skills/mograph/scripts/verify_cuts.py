#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""71 号回归校验：把工具算出的刀口跟人工标注（config.py 的 CUTS）逐条对。

人工标注是「金标准」——它就是晚枫本人手工剪这条片子时的取舍。
工具改了阈值、改了气口规则之后跑一遍这个脚本，就知道有没有跑偏。

用法：
    python3 verify_cuts.py /tmp/cutplan/plan71.json
"""

import json
import sys

# 71-混元hy4-flash 的人工 CUTS 标注（来自 mograph-task/src/config.py）
# 注意：这里的 CUTS 里既有「删内容」也有「收紧停顿」两类，人工用同一张表记。
CUTS = [
    (22.30, 25.20, "5.4s 长停顿收紧"),
    (40.50, 41.70, "3.2s 长停顿收紧"),
    (46.00, 53.50, "「看到最后我告诉大家怎么」连录 3 遍，保留第 3 遍"),
    (79.30, 81.70, "孤立语气词「啊？」+ 3.2s 停顿"),
    (101.00, 105.60, "半截句「这是我发布。」"),
    (114.20, 125.20, "半截句「他就会。」+ 重复的「大家点进这个技能。去使用。」+ 6s 停顿"),
    (135.00, 154.60, "8.6s 停顿 + 「而且。」/「不仅这个技能免费…」/「…刚才给大家分享的」三次废录"),
    (156.90, 158.10, "句间停顿收紧"),
    (163.90, 170.90, "5.1s 停顿 + 孤立「大家。」"),
    (175.30, 180.90, "6.6s 尾段停顿收紧"),
]


def overlap(a, b, c, d):
    return max(a, c) < min(b, d)


def main(path):
    plan = json.load(open(path, encoding="utf-8"))
    drops = plan["drops"]
    print("工具刀口 %d 个，人工标注 %d 条\n" % (len(drops), len(CUTS)))

    hit_cuts = set()
    for i, d in enumerate(drops, 1):
        matched = [j for j, (s, e, _w) in enumerate(CUTS)
                   if overlap(d["from"], d["to"], s, e)]
        hit_cuts.update(matched)
        print("刀口 %d  %7.2f – %7.2f  %-14s  %s"
              % (i, d["from"], d["to"], "/".join(d.get("kinds", [d["kind"]])),
                 (d.get("text") or "")[:28]))
        for j in matched:
            print("        ↳ 人工 CUTS[%d] (%.2f–%.2f) %s"
                  % (j, CUTS[j][0], CUTS[j][1], CUTS[j][2]))
        if not matched:
            print("        ↳ **未匹配任何人工标注**")

    print("\n人工标注未被工具命中的（多为「停顿收紧」类，工具只提示不删）：")
    for j, (s, e, why) in enumerate(CUTS):
        if j not in hit_cuts:
            print("  CUTS[%d] (%.2f–%.2f) %s" % (j, s, e, why))

    st = plan["stats"]
    print("\nkeep: %d 段 / %.2fs（%s%%）"
          % (len(plan["keep"]), st["kept"], st["kept_pct"]))
    zero = [i for i, (a, b) in enumerate(plan["keep"]) if b - a < 0.05]
    print("零长段: %d 个 %s" % (len(zero), zero))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cutplan/plan71.json"))