#!/usr/bin/env bash
# git-init.sh — 初始化 git 仓库并复制对应框架的 .gitignore
# Usage: git-init.sh <framework> <project_root>
# framework: hexo | vitepress | vue3 | hugo | portfolio | resume

set -e

FRAMEWORK="$1"
PROJECT_ROOT="$2"

if [ -z "$FRAMEWORK" ] || [ -z "$PROJECT_ROOT" ]; then
  echo "Usage: $0 <framework> <project_root>" >&2
  exit 1
fi

# ⚠️ 必须先解析 SCRIPT_DIR，再 cd 到 PROJECT_ROOT
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates/$FRAMEWORK"

cd "$PROJECT_ROOT"

# 检查是否已经是 git 仓库
if [ -d ".git" ]; then
  echo "⚠️  已经是 git 仓库，跳过 git init"
else
  git init -b main
  echo "✅ git 仓库初始化完成"
fi

# 复制对应框架的 .gitignore
if [ -f "$TEMPLATE_DIR/.gitignore" ]; then
  cp "$TEMPLATE_DIR/.gitignore" .gitignore
  echo "✅ .gitignore 已复制"
fi