#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_env.py - 环境自检：依赖、数据根目录、目录结构、模板

用法：
    python check_env.py [--root <数据根目录>]

退出码：0 = 全部就绪；1 = 有阻塞项
"""

import argparse
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths

REQUIRED_PKGS = {
    'pandas': '数据处理核心',
    'openpyxl': '读 .xlsx（抖音/小红书/快手）',
    'xlrd': '读公众号 .xls（阅读趋势）',
}

SKILL_ROOT = Path(__file__).resolve().parent.parent

ok = True


def chk(name, cond, detail=''):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f'  — {detail}' if detail else ''))
    if not cond:
        ok = False


def main(argv=None):
    ap = argparse.ArgumentParser(description='环境自检')
    _paths.add_root_arg(ap)
    args = ap.parse_args(argv)
    p = _paths.init(root=args.root)

    print('【1】Python 依赖')
    for pkg, why in REQUIRED_PKGS.items():
        found = importlib.util.find_spec(pkg) is not None
        chk(f'{pkg} 已安装（{why}）', found,
            '' if found else '用 uv run --with pandas --with xlrd --with openpyxl 执行')
    if importlib.util.find_spec('pandas') is None:
        print('\n  ⚠ 缺依赖时的执行方式：')
        print('     uv run --with pandas --with xlrd --with openpyxl python3 <脚本>')
        print('     （本机系统 Python 没有 pandas，不要直接 python3 跑）')

    print('\n【2】数据根目录')
    for k, v in p.describe():
        print(f'  {k}: {v}')
    chk('数据根目录存在', p.root.exists(), str(p.root))

    print('\n【3】目录结构')
    chk('账号数据/ 存在', p.data.is_dir(), str(p.data))
    chk('临时文件夹/ 存在', p.inbox.is_dir(), str(p.inbox))
    chk('月度报告/ 存在', p.report.is_dir(), str(p.report))

    if p.data.is_dir():
        plats = sorted(d.name for d in p.data.iterdir()
                       if d.is_dir() and not d.name.startswith('.'))
        accs = sum(len([a for a in (p.data / pl).iterdir() if a.is_dir()])
                   for pl in plats if (p.data / pl).is_dir())
        chk('至少识别到 1 个平台目录', bool(plats), '、'.join(plats) or '无')
        print(f'  平台 {len(plats)} 个 / 账号 {accs} 个')
        # 平台层不能省：同名账号跨平台存在
        names = {}
        for pl in plats:
            for a in (p.data / pl).iterdir():
                if a.is_dir():
                    names.setdefault(a.name, []).append(pl)
        dup = {k: v for k, v in names.items() if len(v) > 1}
        if dup:
            print(f'  ⚠ 跨平台同名账号（说明平台层是必需的）：')
            for k, v in dup.items():
                print(f'     {k} → {len(v)} 个平台')

    print('\n【4】skill 自身')
    tpl = SKILL_ROOT / 'templates' / '月度报告模板.md'
    chk('模板存在', tpl.is_file(), str(tpl))
    for s in ('classify.py', 'parse_data.py', 'analyze.py', 'monthly_report.py'):
        chk(f'scripts/{s} 存在', (SKILL_ROOT / 'scripts' / s).is_file())

    print('\n' + '=' * 50)
    print('自检结果：' + ('全部就绪 ✅' if ok else '有阻塞项 ❌'))
    if not ok:
        print('\n下一步：')
        print('  1. 装依赖：uv run --with pandas --with xlrd --with openpyxl ...')
        print('  2. 准备目录：<root>/{账号数据,临时文件夹,月度报告}')
        print('  3. 新下载的文件先丢进 <root>/临时文件夹/')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
