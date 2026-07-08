#!/usr/bin/env bash
# init-portfolio.sh — 初始化个人作品集（纯静态 HTML）

set -e

PROJECT_ROOT="$1"
SITE_NAME="$2"
SITE_DESC="$3"
AUTHOR_NAME="$4"
GITHUB_USER="$5"

if [ -z "$PROJECT_ROOT" ] || [ -z "$SITE_NAME" ]; then
  echo "Usage: $0 <project_root> <site_name> <site_desc> <author_name> <github_user>" >&2
  exit 1
fi

if [ -z "$AUTHOR_NAME" ]; then
  AUTHOR_NAME="Your Name"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates/portfolio"

cd "$PROJECT_ROOT"

echo "🚀 初始化作品集项目到: $PROJECT_ROOT"

# 1. 创建目录
mkdir -p projects

# 2. 复制文件
cp "$TEMPLATE_DIR/index.html" index.html
cp "$TEMPLATE_DIR/style.css" style.css
cp "$TEMPLATE_DIR/README.md" README.md
cp "$TEMPLATE_DIR/.gitignore" .gitignore

# 3. 替换占位符
SUBSTITUTE_ARGS=(
  --var "SITE_NAME=$SITE_NAME"
  --var "SITE_DESCRIPTION=$SITE_DESC"
  --var "AUTHOR_NAME=$AUTHOR_NAME"
  --var "AUTHOR_NAME_OR_DEFAULT=$AUTHOR_NAME"
  --var "FRAMEWORK=portfolio"
  --var "SITE_TYPE=作品集"
  --var "SITE_TYPE_EN=Portfolio"
  --empty-line-delete "GITHUB_OR_EMPTY"
)
if [ -n "$GITHUB_USER" ]; then
  SUBSTITUTE_ARGS+=(--var "GITHUB_USERNAME=$GITHUB_USER")
fi

"$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" \
  index.html \
  README.md
echo "✅ 模板占位符已替换"

# 4. git init
"$SCRIPT_DIR/git-init.sh" portfolio "$PROJECT_ROOT"

echo ""
echo "🎉 作品集创建完成！"
echo "📁 项目目录: $PROJECT_ROOT"
echo "🌐 下一步: open $PROJECT_ROOT/index.html"