#!/usr/bin/env bash
# optimize-all.sh — 构建后优化主入口
# Usage: optimize-all.sh <framework> <project_root>
# 输出: <project_root>/<dist>-optimized/
#
# 优化项：
#   1. 图片（PNG/JPG → WebP + 压缩）
#   2. CSS/JS minify（框架已默认 minify，跳过）
#   3. 字体（仅当有 @font-face 且存在 ttf/woff 时）

set -e

FRAMEWORK="$1"
PROJECT_ROOT="$2"

if [ -z "$FRAMEWORK" ] || [ -z "$PROJECT_ROOT" ]; then
  echo "Usage: $0 <framework> <project_root>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 推断 dist 目录
case "$FRAMEWORK" in
  hexo) DIST_DIR="$PROJECT_ROOT/public" ;;
  vitepress) DIST_DIR="$PROJECT_ROOT/docs/.vitepress/dist" ;;
  vue3) DIST_DIR="$PROJECT_ROOT/dist" ;;
  hugo) DIST_DIR="$PROJECT_ROOT/public" ;;
  portfolio|resume) DIST_DIR="$PROJECT_ROOT" ;;
  *) DIST_DIR="$PROJECT_ROOT/dist" ;;
esac

if [ ! -d "$DIST_DIR" ]; then
  echo "⚠️  dist 目录不存在: $DIST_DIR，跳过优化"
  exit 0
fi

echo "🚀 优化构建产物: $DIST_DIR"

# 1. 图片优化
echo ""
echo "━━━ 1. 图片优化 ━━━"
"$SCRIPT_DIR/optimize-images.sh" "$DIST_DIR" || echo "  ⚠️  图片优化失败（继续）"

# 2. CSS/JS minify（VitePress/Vue 3 已默认 minify，Hexo 也已压缩）
echo ""
echo "━━━ 2. CSS/JS minify ━━━"
case "$FRAMEWORK" in
  hexo)
    echo "  Hexo 已在构建时 minify CSS/JS"
    ;;
  vitepress|vue3|hugo)
    echo "  $FRAMEWORK 已在构建时 minify CSS/JS"
    ;;
  portfolio|resume)
    # 纯 HTML/CSS：检查是否有未压缩的 CSS
    CSS_FILES=$(find "$DIST_DIR" -type f -name "*.css" 2>/dev/null)
    if [ -n "$CSS_FILES" ]; then
      echo "  发现 CSS 文件，保持原样（如需压缩可用 cssnano）"
    fi
    ;;
esac

# 3. 字体优化（仅 Vue 3 / VitePress / 作品集 有字体时）
echo ""
echo "━━━ 3. 字体优化 ━━━"
FONT_FILES=$(find "$DIST_DIR" -type f \( -iname "*.ttf" -o -iname "*.otf" \) 2>/dev/null | head -5)
if [ -n "$FONT_FILES" ]; then
  echo "  发现字体文件："
  echo "$FONT_FILES" | while read f; do
    SIZE=$(du -h "$f" | cut -f1)
    echo "    $f ($SIZE)"
  done
  echo "  提示：可用 fonttools 做子集化（npm install -g fonttools）"
else
  echo "  未发现 TTF/OTF 字体文件"
fi

# 4. 检查 dist 总体积
echo ""
echo "━━━ 4. 体积统计 ━━━"
if [ -d "$PROJECT_ROOT/$(basename "$DIST_DIR")-optimized" ]; then
  OPT_DIR="$PROJECT_ROOT/$(basename "$DIST_DIR")-optimized"
  ORIG_SIZE=$(du -sk "$DIST_DIR" 2>/dev/null | cut -f1)
  OPT_SIZE=$(du -sk "$OPT_DIR" 2>/dev/null | cut -f1)
  echo "  原始: ${ORIG_SIZE}KB"
  echo "  优化: ${OPT_SIZE}KB"
  if [ "$ORIG_SIZE" -gt 0 ]; then
    RATIO=$(python3 -c "print(f'{(1 - $OPT_SIZE / $ORIG_SIZE) * 100:.1f}')" 2>/dev/null || echo "0")
    echo "  节省: ${RATIO}%"
  fi
  echo ""
  echo "  💡 部署时用优化后的目录："
  echo "     deploy.sh $FRAMEWORK $PROJECT_ROOT --dist=$(basename "$OPT_DIR")"
else
  echo "  原始: $(du -sh "$DIST_DIR" 2>/dev/null | cut -f1)"
fi

echo ""
echo "✅ 优化完成"