#!/usr/bin/env python3
"""扫描目标项目结构，输出一份 JSON 报告，供 AI Agent 撰写 repowiki 时参考。

用法：
    python3 analyze_project.py <project_root> [--output <out.json>]

输出字段：
    - project_root: 目标项目绝对路径
    - project_name: 推断的项目名
    - project_type: 项目类型（python_lib / python_cli / node_frontend / go_service ...）
    - tech_stack: 技术栈列表
    - top_dirs: 顶层目录（含用途推断）
    - entry_points: 入口点列表
    - source_files: 源代码文件清单
    - config_files: 配置文件清单
    - has_cli / has_gui / has_web / has_batch / has_api / has_tests / has_examples: 能力标记
    - module_candidates: 候选核心模块（基于目录结构推断）
    - api_groups: 候选 API 分组（基于模块推断）
    - warnings: 风险与缺口

注意：本脚本仅辅助扫描，不写入任何文档；所有内容必须由 Agent 根据报告人工撰写。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------- 配置：忽略目录与文件 ----------
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "out",
    "target",
    ".next",
    ".nuxt",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "coverage",
    ".qoder",  # 兼容旧版产物目录
    "wiki",  # 不扫描自身的产物（生成的 wiki 输出目录）
}

IGNORE_FILES = {
    ".DS_Store",
    ".gitignore",
    ".gitattributes",
    "Thumbs.db",
}

# ---------- 配置：用途推断 ----------
DIR_PURPOSE_HINTS: dict[str, str] = {
    "src": "源代码",
    "lib": "源代码",
    "pkg": "源代码",
    "internal": "源代码（私有）",
    "cmd": "命令行入口",
    "bin": "可执行文件",
    "scripts": "脚本",
    "tools": "工具",
    "tests": "测试",
    "test": "测试",
    "__tests__": "测试",
    "spec": "测试",
    "docs": "文档",
    "doc": "文档",
    "documentation": "文档",
    "examples": "示例",
    "demo": "示例",
    "sample": "示例",
    "public": "静态资源",
    "static": "静态资源",
    "assets": "资源",
    "config": "配置",
    "conf": "配置",
    "configs": "配置",
    "api": "API 层",
    "routes": "路由",
    "controllers": "控制器",
    "views": "视图",
    "models": "数据模型",
    "entities": "实体",
    "schemas": "数据模式",
    "services": "业务服务",
    "core": "核心逻辑",
    "domain": "领域层",
    "business": "业务层",
    "utils": "工具",
    "helpers": "辅助函数",
    "common": "公共代码",
    "shared": "共享代码",
    "components": "UI 组件",
    "widgets": "UI 组件",
    "ui": "UI 层",
    "web": "Web 前端",
    "frontend": "前端",
    "client": "客户端",
    "server": "服务端",
    "backend": "后端",
    "migrations": "数据库迁移",
    "plugins": "插件",
    "extensions": "扩展",
    "hooks": "钩子",
    "locales": "国际化文案",
    "i18n": "国际化",
    "types": "类型定义",
    "interfaces": "接口定义",
    "templates": "模板",
    "layouts": "布局",
    "pages": "页面",
}

# 顶层配置/构建文件识别
CONFIG_FILE_PATTERNS: dict[str, str] = {
    "pyproject.toml": "Python 项目构建配置",
    "setup.py": "Python 安装脚本",
    "setup.cfg": "Python 配置",
    "requirements.txt": "Python 依赖清单",
    "Pipfile": "Python Pipenv 配置",
    "uv.lock": "Python uv 锁定",
    "poetry.lock": "Python Poetry 锁定",
    "package.json": "Node.js 项目配置",
    "pnpm-lock.yaml": "Node.js pnpm 锁定",
    "yarn.lock": "Node.js Yarn 锁定",
    "package-lock.json": "Node.js npm 锁定",
    "tsconfig.json": "TypeScript 配置",
    "go.mod": "Go 模块",
    "go.sum": "Go 模块校验",
    "Cargo.toml": "Rust 项目配置",
    "Cargo.lock": "Rust 依赖锁定",
    "pom.xml": "Maven 项目配置",
    "build.gradle": "Gradle 项目配置",
    "build.gradle.kts": "Gradle Kotlin DSL",
    "Gemfile": "Ruby 项目配置",
    "composer.json": "PHP 项目配置",
    "pubspec.yaml": "Dart/Flutter 项目配置",
    "Dockerfile": "Docker 镜像",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".env.example": "环境变量示例",
    "README.md": "项目说明",
    "README.zh.md": "项目说明（中文）",
    "README.en.md": "Project README (EN)",
    "LICENSE": "许可证",
    "CHANGELOG.md": "变更日志",
    "CONTRIBUTING.md": "贡献指南",
}

# 入口点启发式
CLI_PATTERNS = [
    re.compile(r"^\s*@click\.(group|command)", re.MULTILINE),
    re.compile(r"^\s*@app\.command", re.MULTILINE),
    re.compile(r"def\s+cli\s*\("),
    re.compile(r"argparse\.ArgumentParser"),
    re.compile(r"if\s+__name__\s*==\s*[\"']__main__[\"']"),
    re.compile(r"@main\.command"),
    re.compile(r"program\s*\.\s*(add_argument|parse_args)"),
]

GUI_PATTERNS = [
    re.compile(r"\bPySide6?\b"),
    re.compile(r"\bPyQt[456]?\b"),
    re.compile(r"\bTkinter\b|\btk\.Tk\b"),
    re.compile(r"\bwx\.App\b"),
    re.compile(r"\bElectron\b"),
    re.compile(r"\bTauri\b"),
]

WEB_PATTERNS = [
    re.compile(r"\breact\b", re.IGNORECASE),
    re.compile(r"\bvue\b", re.IGNORECASE),
    re.compile(r"\bangular\b", re.IGNORECASE),
    re.compile(r"\bsvelte\b", re.IGNORECASE),
    re.compile(r"\bnext\.js\b|\bnextjs\b", re.IGNORECASE),
    re.compile(r"\bnuxt\b", re.IGNORECASE),
    re.compile(r"\bexpress\b", re.IGNORECASE),
    re.compile(r"\bnestjs\b|\bnest\.js\b", re.IGNORECASE),
    re.compile(r"\bdjango\b", re.IGNORECASE),
    re.compile(r"\bflask\b", re.IGNORECASE),
    re.compile(r"\bfastapi\b", re.IGNORECASE),
    re.compile(r"\bspring\s+boot\b", re.IGNORECASE),
    re.compile(r"\bgin\.New\(\)"),
]

BATCH_PATTERNS = [
    re.compile(r"\bbatch\b", re.IGNORECASE),
    re.compile(r"\bBatch[A-Z_]?\w*\("),
    re.compile(r"遍历.*目录|scandir|os\.walk"),
]


# ---------- 工具函数 ----------


def safe_read_text(path: Path, max_bytes: int = 1_000_000) -> str:
    """读取文本文件，限制大小并容忍编码错误。"""
    try:
        if path.stat().st_size > max_bytes:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_bytes)
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return ""


def infer_project_name(project_root: Path) -> str:
    """按优先级推断项目名。"""
    # 1. pyproject.toml
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        text = safe_read_text(pyproject)
        m = re.search(r'^\s*name\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        if m:
            return m.group(1)
        m = re.search(r'^\[project\][^\[]*?name\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE | re.DOTALL)
        if m:
            return m.group(1)

    # 2. package.json
    pkg = project_root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(safe_read_text(pkg))
            if isinstance(data, dict) and "name" in data:
                return str(data["name"])
        except json.JSONDecodeError:
            pass

    # 3. Cargo.toml
    cargo = project_root / "Cargo.toml"
    if cargo.is_file():
        text = safe_read_text(cargo)
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            return m.group(1)

    # 4. go.mod
    gomod = project_root / "go.mod"
    if gomod.is_file():
        text = safe_read_text(gomod)
        m = re.search(r"^module\s+(\S+)", text, re.MULTILINE)
        if m:
            return m.group(1)

    # 5. fallback：目录名
    return project_root.resolve().name


def infer_project_type(project_root: Path, top_dirs: list[str], files: list[str]) -> str:
    """根据构建文件与目录推断项目类型。"""
    if "pyproject.toml" in files or "setup.py" in files:
        if "web" in top_dirs or any(d in top_dirs for d in ("frontend", "client")):
            return "python_fullstack"
        return "python_lib"
    if "package.json" in files:
        # 检查是否有 server 目录
        if any(d in top_dirs for d in ("server", "backend", "api")):
            return "node_fullstack"
        # 检查是否有 src/App.tsx 或 src/main.ts
        if (project_root / "src" / "App.tsx").exists() or (project_root / "src" / "main.ts").exists():
            return "node_frontend"
        return "node_lib"
    if "go.mod" in files:
        return "go_service"
    if "Cargo.toml" in files:
        return "rust_lib"
    if "pom.xml" in files or "build.gradle" in files:
        return "java_service"
    if "Gemfile" in files:
        return "ruby_lib"
    if "composer.json" in files:
        return "php_lib"
    if "pubspec.yaml" in files:
        return "flutter_app"
    return "unknown"


def detect_capabilities(project_root: Path, all_text_sample: str) -> dict[str, bool]:
    """检测项目能力（CLI / GUI / Web / Batch / API）。"""
    return {
        "has_cli": any(p.search(all_text_sample) for p in CLI_PATTERNS),
        "has_gui": any(p.search(all_text_sample) for p in GUI_PATTERNS),
        "has_web": any(p.search(all_text_sample) for p in WEB_PATTERNS),
        "has_batch": any(p.search(all_text_sample) for p in BATCH_PATTERNS),
    }


def detect_tech_stack(project_root: Path, files: list[str]) -> list[str]:
    """根据配置文件推断技术栈。"""
    stack: list[str] = []
    file_set = set(files)
    if "pyproject.toml" in file_set or "setup.py" in file_set:
        stack.append("Python")
        # 进一步识别 Python 库
        text = safe_read_text(project_root / "pyproject.toml") if (project_root / "pyproject.toml").exists() else ""
        if "fastapi" in text.lower():
            stack.append("FastAPI")
        if "django" in text.lower():
            stack.append("Django")
        if "flask" in text.lower():
            stack.append("Flask")
        if "pyside" in text.lower() or "pyqt" in text.lower():
            stack.append("Qt (Python)")
    if "package.json" in file_set:
        stack.append("Node.js")
        pkg_text = safe_read_text(project_root / "package.json")
        if "react" in pkg_text.lower():
            stack.append("React")
        if "vue" in pkg_text.lower():
            stack.append("Vue")
        if "next" in pkg_text.lower():
            stack.append("Next.js")
        if "vite" in pkg_text.lower():
            stack.append("Vite")
        if "express" in pkg_text.lower():
            stack.append("Express")
    if "tsconfig.json" in file_set:
        stack.append("TypeScript")
    if "go.mod" in file_set:
        stack.append("Go")
    if "Cargo.toml" in file_set:
        stack.append("Rust")
    if "pom.xml" in file_set or "build.gradle" in file_set:
        stack.append("Java/Kotlin")
    return stack


def scan_project(project_root: Path) -> dict[str, Any]:
    """主扫描函数。"""
    if not project_root.is_dir():
        raise NotADirectoryError(f"{project_root} 不是目录")

    top_dirs: list[str] = []
    files: list[str] = []
    all_paths: list[Path] = []

    for entry in sorted(project_root.iterdir(), key=lambda e: e.name):
        if entry.name in IGNORE_DIRS or entry.name in IGNORE_FILES:
            continue
        if entry.name.startswith(".") and entry.name not in {".env.example", ".github"}:
            # 隐藏目录（除 .env.example 和 .github）通常忽略
            if entry.name != ".github":
                continue
        if entry.is_dir():
            top_dirs.append(entry.name)
            # 递归收集所有源码文件路径（用于统计）
            for sub in entry.rglob("*"):
                if sub.is_dir():
                    if sub.name in IGNORE_DIRS:
                        continue
                    continue
                if sub.name in IGNORE_FILES:
                    continue
                all_paths.append(sub)
        else:
            files.append(entry.name)

    # 读取关键配置 + 部分源代码用于能力检测
    sample_texts: list[str] = []
    for cfg in ("README.md", "pyproject.toml", "package.json", "Cargo.toml", "go.mod"):
        p = project_root / cfg
        if p.is_file():
            sample_texts.append(safe_read_text(p))

    # 抽样读取源代码（最多 50 个、每个最多 200KB）
    src_files = [p for p in all_paths if is_source_file(p)][:50]
    for p in src_files:
        sample_texts.append(safe_read_text(p, max_bytes=200_000))

    all_text_sample = "\n".join(sample_texts)

    # 推断
    project_name = infer_project_name(project_root)
    project_type = infer_project_type(project_root, top_dirs, files)
    capabilities = detect_capabilities(project_root, all_text_sample)
    tech_stack = detect_tech_stack(project_root, files)

    # 顶层目录用途
    top_dirs_info = [
        {
            "name": d,
            "purpose": DIR_PURPOSE_HINTS.get(d, "（待人工判断）"),
        }
        for d in top_dirs
    ]

    # 配置文件
    config_files = [
        {"name": f, "purpose": CONFIG_FILE_PATTERNS.get(f, "（待人工判断）")}
        for f in files
        if f in CONFIG_FILE_PATTERNS
    ]

    # 入口点候选
    entry_points: list[dict[str, Any]] = []
    # Python scripts
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        text = safe_read_text(pyproject)
        for m in re.finditer(r'^\s*([\w-]+)\s*=\s*"([^"]+:\w+)"', text, re.MULTILINE):
            entry_points.append(
                {"name": m.group(1), "target": m.group(2), "kind": "console_script"}
            )
    # package.json bin
    pkg = project_root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(safe_read_text(pkg))
            bin_field = data.get("bin")
            if isinstance(bin_field, str):
                entry_points.append({"name": data.get("name", ""), "target": bin_field, "kind": "npm_bin"})
            elif isinstance(bin_field, dict):
                for name, target in bin_field.items():
                    entry_points.append({"name": name, "target": target, "kind": "npm_bin"})
            main_field = data.get("main")
            if main_field:
                entry_points.append({"name": "main", "target": main_field, "kind": "module_entry"})
        except json.JSONDecodeError:
            pass
    # main 文件
    for candidate in ("src/main.py", "src/main.ts", "src/main.js", "src/main.rs", "cmd/main.go", "src/index.ts", "src/index.js"):
        if (project_root / candidate).is_file():
            entry_points.append({"name": candidate, "target": candidate, "kind": "main_file"})

    # 核心模块候选（基于顶层目录）
    module_candidates = [
        d["name"]
        for d in top_dirs_info
        if d["purpose"] not in ("（待人工判断）", "测试", "示例", "文档")
        and d["name"] not in IGNORE_DIRS
    ]

    # API 分组候选（基于模块候选中的"管理"/"API"/"服务"等关键词）
    api_groups: list[str] = []
    for m in module_candidates:
        if any(kw in m.lower() for kw in ("api", "service", "controller", "endpoint", "管理", "服务")):
            api_groups.append(m)
    if not api_groups and module_candidates:
        # fallback：使用所有候选
        api_groups = module_candidates[:3]

    # 源码统计
    src_count = sum(1 for p in all_paths if is_source_file(p))
    test_files = [p for p in all_paths if is_test_file(p)]
    example_dirs = [d for d in top_dirs if d in ("examples", "demo", "sample")]

    # 风险与缺口
    warnings: list[str] = []
    if not (project_root / "README.md").exists():
        warnings.append("缺少 README.md")
    if not (project_root / "LICENSE").exists():
        warnings.append("缺少 LICENSE")
    if src_count == 0:
        warnings.append("未发现源代码文件")
    if len(test_files) == 0:
        warnings.append("未发现测试文件")
    if not entry_points:
        warnings.append("未识别到入口点（CLI / main / bin）")

    return {
        "project_root": str(project_root.resolve()),
        "project_name": project_name,
        "project_type": project_type,
        "tech_stack": tech_stack,
        "capabilities": capabilities,
        "top_dirs": top_dirs_info,
        "config_files": config_files,
        "entry_points": entry_points,
        "module_candidates": module_candidates,
        "api_groups": api_groups,
        "source_file_count": src_count,
        "test_file_count": len(test_files),
        "has_examples": bool(example_dirs),
        "warnings": warnings,
    }


def is_source_file(path: Path) -> bool:
    """判断是否为源代码文件。"""
    if path.suffix.lower() in (
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".rb",
        ".php",
        ".vue",
        ".svelte",
        ".dart",
    ):
        return True
    return False


def is_test_file(path: Path) -> bool:
    """判断是否为测试文件。"""
    name = path.name.lower()
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    if name.endswith(".test.ts") or name.endswith(".test.tsx") or name.endswith(".test.js") or name.endswith(".spec.ts") or name.endswith(".spec.js"):
        return True
    parts = path.parts
    if any(p in ("tests", "test", "__tests__", "spec") for p in parts):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="扫描目标项目，输出 repowiki 生成所需的元信息")
    parser.add_argument("project_root", help="目标项目根目录")
    parser.add_argument("--output", "-o", default="-", help="输出 JSON 文件路径，默认 stdout")
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists():
        print(f"错误：{project_root} 不存在", file=sys.stderr)
        return 1

    try:
        report = scan_project(project_root)
    except Exception as e:
        print(f"扫描失败：{e}", file=sys.stderr)
        return 2

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"报告已写入 {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())