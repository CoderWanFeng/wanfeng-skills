#!/usr/bin/env bash
# init-vitepress.sh — 初始化 VitePress 知识库项目

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
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates/vitepress"

cd "$PROJECT_ROOT"

echo "🚀 初始化 VitePress 项目到: $PROJECT_ROOT"

# 1. 创建目录结构
mkdir -p docs/.vitepress docs/guide docs/en/guide docs/public

# 2. 安装依赖
npm init -y > /dev/null 2>&1
npm install --save-dev vitepress@^1.5.0 vue@^3.5.0 --no-audit --no-fund --loglevel=error
echo "✅ VitePress 依赖已安装"

# 3. 用 npm pkg set 设置 scripts
npm pkg set scripts.docs:dev="vitepress dev docs"
npm pkg set scripts.docs:build="vitepress build docs"
npm pkg set scripts.docs:preview="vitepress preview docs"
npm pkg set type="module"
echo "✅ package.json scripts 已配置"

# 4. 复制模板文件
cp "$TEMPLATE_DIR/docs/.vitepress/config.mts" docs/.vitepress/config.mts
cp "$TEMPLATE_DIR/docs/index.md" docs/index.md
cp "$TEMPLATE_DIR/docs/guide/getting-started.md" docs/guide/getting-started.md
cp "$TEMPLATE_DIR/docs/en/guide/getting-started.md" docs/en/guide/getting-started.md

# 5. 替换占位符
SUBSTITUTE_ARGS=(
  --var "SITE_NAME=$SITE_NAME"
  --var "SITE_DESCRIPTION=$SITE_DESC"
  --var "AUTHOR_NAME=$AUTHOR_NAME"
  --var "AUTHOR_NAME_OR_DEFAULT=$AUTHOR_NAME"
  --var "FRAMEWORK=vitepress"
  --var "SITE_TYPE=知识库"
  --var "SITE_TYPE_EN=Knowledge Base"
  --empty-line-delete "GITHUB_OR_EMPTY"
)
if [ -n "$GITHUB_USER" ]; then
  SUBSTITUTE_ARGS+=(--var "GITHUB_USERNAME=$GITHUB_USER")
fi

# 在首页加 GitHub 链接时也要处理空用户名
"$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" \
  docs/.vitepress/config.mts \
  docs/index.md \
  docs/guide/getting-started.md \
  docs/en/guide/getting-started.md
echo "✅ 模板占位符已替换"

# 6. 复制 README.md 和 .gitignore
cp "$TEMPLATE_DIR/README.md" README.md
cp "$TEMPLATE_DIR/.gitignore" .gitignore

"$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" README.md
echo "✅ README.md 已生成"

# 7. git init
"$SCRIPT_DIR/git-init.sh" vitepress "$PROJECT_ROOT"

echo ""
echo "🎉 VitePress 知识库创建完成！"
echo "📁 项目目录: $PROJECT_ROOT"
echo "🌐 下一步: cd $PROJECT_ROOT && npm run docs:dev"