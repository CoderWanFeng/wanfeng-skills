#!/usr/bin/env bash
# init-vue3.sh — 初始化 Vue 3 + Vite AI 导航站项目

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
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates/vue3-vite"

cd "$PROJECT_ROOT"

echo "🚀 初始化 Vue 3 + Vite 项目到: $PROJECT_ROOT"

# 1. 创建目录结构
mkdir -p src/router src/views src/components src/data

# 2. 复制所有源码文件
cp "$TEMPLATE_DIR/index.html" index.html
cp "$TEMPLATE_DIR/vite.config.js" vite.config.js
cp "$TEMPLATE_DIR/src/main.js" src/main.js
cp "$TEMPLATE_DIR/src/style.css" src/style.css
cp "$TEMPLATE_DIR/src/App.vue" src/App.vue
cp "$TEMPLATE_DIR/src/router/index.js" src/router/index.js
cp "$TEMPLATE_DIR/src/views/Home.vue" src/views/Home.vue
cp "$TEMPLATE_DIR/src/views/Category.vue" src/views/Category.vue
cp "$TEMPLATE_DIR/src/components/HeaderNav.vue" src/components/HeaderNav.vue
cp "$TEMPLATE_DIR/src/components/ToolCard.vue" src/components/ToolCard.vue
cp "$TEMPLATE_DIR/src/data/tools.js" src/data/tools.js

# 3. 安装依赖
npm init -y > /dev/null 2>&1
npm install --save vue@^3.5.0 vue-router@^4.4.0 --no-audit --no-fund --loglevel=error
npm install --save-dev vite@^5.4.0 @vitejs/plugin-vue@^5.1.0 --no-audit --no-fund --loglevel=error
echo "✅ 依赖已安装"

# 4. 用 npm pkg set 设置 scripts
npm pkg set scripts.dev="vite"
npm pkg set scripts.build="vite build"
npm pkg set scripts.preview="vite preview"
npm pkg set type="module"
echo "✅ package.json scripts 已配置"

# 5. 替换占位符（仅在含占位符的文件中）
SUBSTITUTE_ARGS=(
  --var "SITE_NAME=$SITE_NAME"
  --var "SITE_DESCRIPTION=$SITE_DESC"
  --var "AUTHOR_NAME=$AUTHOR_NAME"
  --var "AUTHOR_NAME_OR_DEFAULT=$AUTHOR_NAME"
  --var "FRAMEWORK=vue3"
  --var "SITE_TYPE=AI 导航"
  --var "SITE_TYPE_EN=AI Tools"
)
if [ -n "$GITHUB_USER" ]; then
  SUBSTITUTE_ARGS+=(--var "GITHUB_USERNAME=$GITHUB_USER")
fi

"$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" \
  index.html \
  src/App.vue \
  src/components/HeaderNav.vue \
  src/views/Home.vue
echo "✅ Vue 文件占位符已替换"

# 6. 复制 README.md 和 .gitignore
cp "$TEMPLATE_DIR/README.md" README.md
cp "$TEMPLATE_DIR/.gitignore" .gitignore

"$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" README.md
echo "✅ README.md 已生成"

# 7. git init
"$SCRIPT_DIR/git-init.sh" vue3 "$PROJECT_ROOT"

echo ""
echo "🎉 Vue 3 导航站创建完成！"
echo "📁 项目目录: $PROJECT_ROOT"
echo "🌐 下一步: cd $PROJECT_ROOT && npm run dev"