#!/usr/bin/env bash
# init-hexo.sh — 初始化 Hexo 博客项目
# Usage: init-hexo.sh <project_root> <site_name> <site_description> <author_name> <github_username>
# 调用方必须已经决定所有占位符的实际值（默认值由调用方提供，本脚本不负责兜底）

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

# author 留空兜底
if [ -z "$AUTHOR_NAME" ]; then
  AUTHOR_NAME="Your Name"
fi

# ⚠️ 必须先解析 SCRIPT_DIR，再 cd 到 PROJECT_ROOT
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates/hexo"

cd "$PROJECT_ROOT"

echo "🚀 初始化 Hexo 项目到: $PROJECT_ROOT"

# 1. hexo init（注意：必须加 --no-install 避免交互）
npx --yes hexo init . --no-install
echo "✅ Hexo 基础结构已生成"

# 2. 安装依赖
npm install --no-audit --no-fund --loglevel=error
echo "✅ Hexo 默认依赖已安装"

# 3. 安装 Butterfly 主题及其渲染器
npm install --save hexo-theme-butterfly hexo-renderer-pug hexo-renderer-stylus --no-audit --no-fund --loglevel=error
echo "✅ Butterfly 主题已安装"

# 4. 复制 Butterfly 默认配置（保留用户自定义）
if [ -f "node_modules/hexo-theme-butterfly/_config.yml" ]; then
  cp node_modules/hexo-theme-butterfly/_config.yml _config.butterfly.yml
  echo "✅ _config.butterfly.yml 已创建"
fi

# 5. 删除默认 hello-world.md（用 welcome-zh 替换）
rm -f source/_posts/hello-world.md
echo "✅ 默认示例文章已删除"

# 6. 复制欢迎文章（双语）
if [ -f "$TEMPLATE_DIR/source/_posts/welcome-zh.md" ]; then
  cp "$TEMPLATE_DIR/source/_posts/welcome-zh.md" source/_posts/welcome-zh.md
  cp "$TEMPLATE_DIR/source/_posts/welcome-en.md" source/_posts/welcome-en.md

  # 替换占位符
  SUBSTITUTE_ARGS=(
    --var "SITE_NAME=$SITE_NAME"
    --var "SITE_DESCRIPTION=$SITE_DESC"
    --var "AUTHOR_NAME=$AUTHOR_NAME"
    --var "AUTHOR_NAME_OR_DEFAULT=$AUTHOR_NAME"
    --var "FRAMEWORK=hexo"
    --var "SITE_TYPE=个人博客"
    --var "SITE_TYPE_EN=Blog"
  )
  if [ -n "$GITHUB_USER" ]; then
    SUBSTITUTE_ARGS+=(--var "GITHUB_USERNAME=$GITHUB_USER")
  fi
  "$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" \
    source/_posts/welcome-zh.md \
    source/_posts/welcome-en.md
  echo "✅ 欢迎文章已生成（双语）"
fi

# 7. 复制 _config.yml 模板并替换
if [ -f "$TEMPLATE_DIR/_config.yml" ]; then
  cp "$TEMPLATE_DIR/_config.yml" _config.yml
  SUBSTITUTE_ARGS=(
    --var "SITE_NAME=$SITE_NAME"
    --var "SITE_DESCRIPTION=$SITE_DESC"
    --var "AUTHOR_NAME=$AUTHOR_NAME"
    --var "AUTHOR_NAME_OR_DEFAULT=$AUTHOR_NAME"
    --var "FRAMEWORK=hexo"
    --var "SITE_TYPE=个人博客"
    --var "SITE_TYPE_EN=Blog"
  )
  if [ -n "$GITHUB_USER" ]; then
    SUBSTITUTE_ARGS+=(--var "GITHUB_USERNAME=$GITHUB_USER")
  fi
  "$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" _config.yml
  echo "✅ _config.yml 已生成"
fi

# 8. 复制 README.md 模板并替换
if [ -f "$TEMPLATE_DIR/README.md" ]; then
  cp "$TEMPLATE_DIR/README.md" README.md
  SUBSTITUTE_ARGS=(
    --var "SITE_NAME=$SITE_NAME"
    --var "SITE_DESCRIPTION=$SITE_DESC"
    --var "AUTHOR_NAME=$AUTHOR_NAME"
    --var "AUTHOR_NAME_OR_DEFAULT=$AUTHOR_NAME"
    --var "FRAMEWORK=hexo"
    --var "SITE_TYPE=个人博客"
    --var "SITE_TYPE_EN=Blog"
  )
  if [ -n "$GITHUB_USER" ]; then
    SUBSTITUTE_ARGS+=(--var "GITHUB_USERNAME=$GITHUB_USER")
  fi
  "$SCRIPT_DIR/substitute.sh" "${SUBSTITUTE_ARGS[@]}" README.md
  echo "✅ README.md 已生成"
fi

# 9. 复制 .gitignore
if [ -f "$TEMPLATE_DIR/.gitignore" ]; then
  cp "$TEMPLATE_DIR/.gitignore" .gitignore
fi

# 10. git init
"$SCRIPT_DIR/git-init.sh" hexo "$PROJECT_ROOT"

echo ""
echo "🎉 Hexo 博客创建完成！"
echo "📁 项目目录: $PROJECT_ROOT"
echo "🌐 下一步: cd $PROJECT_ROOT && npx hexo server"