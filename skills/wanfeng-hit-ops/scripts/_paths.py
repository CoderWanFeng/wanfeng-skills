#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_paths.py - 路径解析：所有脚本共用

数据根目录（--root）的结构约定：
    <root>/
    ├── 临时文件夹/          # 下载收件箱
    ├── 账号数据/            # 平台/账号/YYMMDD快照/文件
    └── 月度报告/            # 按月归档的结论

根目录的确定顺序：
    1. 命令行 --root <path>
    2. 环境变量 WANFENG_DATA_ROOT
    3. 脚本所在 skill 目录的上一级（开发期默认，即 skill 仓库根）
"""

import os
import sys
from pathlib import Path

# skill 根目录（scripts/ 的上一级）
SKILL_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ROOT = SKILL_ROOT.parent

DATA_DIRNAME = '账号数据'
INBOX_DIRNAME = '临时文件夹'
REPORT_DIRNAME = '月度报告'


def resolve_root(argv=None):
    """从命令行/环境变量解析数据根目录"""
    argv = sys.argv if argv is None else argv
    if '--root' in argv:
        i = argv.index('--root')
        if i + 1 < len(argv):
            return Path(argv[i + 1]).expanduser().resolve()
    env = os.environ.get('WANFENG_DATA_ROOT')
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_ROOT


class Paths:
    """一次解析，全局可读"""

    def __init__(self, root=None):
        self.root = Path(root).expanduser().resolve() if root else resolve_root()
        self.data = self.root / DATA_DIRNAME
        self.inbox = self.root / INBOX_DIRNAME
        self.report = self.root / REPORT_DIRNAME

    def month_dir(self, month):
        d = self.report / month
        d.mkdir(parents=True, exist_ok=True)
        return d

    def describe(self):
        return [
            ('数据根目录', self.root),
            ('  账号数据', self.data),
            ('  临时文件夹', self.inbox),
            ('  月度报告', self.report),
        ]


# 模块级单例：脚本 import 后直接用 DATA / INBOX / REPORT
_PATHS = None


def init(argv=None, root=None):
    """初始化全局路径。必须在任何 parse_* 之前调用。"""
    global _PATHS
    _PATHS = Paths(root or resolve_root(argv))
    return _PATHS


def paths():
    if _PATHS is None:
        init()
    return _PATHS


# 便捷别名（延迟到 init() 之后求值）
def _lazy(name):
    return property(lambda self: getattr(paths(), name))


class _Proxy:
    """让 `from _paths import DATA` 拿到的是当前 root 下的路径"""

    def __init__(self, attr):
        self._attr = attr

    def __fspath__(self):
        return str(getattr(paths(), self._attr))

    def __truediv__(self, other):
        return getattr(paths(), self._attr) / other

    def __str__(self):
        return str(getattr(paths(), self._attr))

    def __repr__(self):
        return repr(getattr(paths(), self._attr))

    def exists(self):
        return getattr(paths(), self._attr).exists()

    def iterdir(self):
        return getattr(paths(), self._attr).iterdir()

    def rglob(self, *a):
        return getattr(paths(), self._attr).rglob(*a)


DATA = _Proxy('data')
INBOX = _Proxy('inbox')
REPORT = _Proxy('report')
ROOT = _Proxy('root')


def add_root_arg(parser=None):
    """给 argparse 加上 --root（各脚本共用）"""
    if parser is None:
        return None
    parser.add_argument('--root', default=None,
                        help='数据根目录（含 账号数据/ 临时文件夹/ 月度报告/），'
                             '默认取环境变量 WANFENG_DATA_ROOT 或 skill 上一级')
    return parser
