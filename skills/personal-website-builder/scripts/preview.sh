#!/usr/bin/env bash
# preview.sh — 启动 dev server 并自动打开浏览器
# Usage: preview.sh <framework> <project_root>
# framework: hexo | vitepress | vue3 | hugo | portfolio | resume
# project_root: 项目根目录绝对路径

set -e

FRAMEWORK="$1"
PROJECT_ROOT="$2"

if [ -z "$FRAMEWORK" ] || [ -z "$PROJECT_ROOT" ]; then
  echo "Usage: $0 <framework> <project_root>" >&2
  exit 1
fi

# ⚠️ 必须先解析 SCRIPT_DIR，再 cd 到 PROJECT_ROOT
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 加载环境检测
ENV_JSON="$("$SCRIPT_DIR/detect-env.sh" 2>/dev/null)" || ENV_JSON="{}"
HEADLESS="$(echo "$ENV_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("headless","true"))' 2>/dev/null || echo 'true')"
OPEN_CMD="$(echo "$ENV_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("open_cmd",""))' 2>/dev/null || echo '')"

URL=""

case "$FRAMEWORK" in
  hexo)
    URL="http://localhost:4000/"
    cd "$PROJECT_ROOT"
    echo "🚀 启动 Hexo dev server..."
    (npx hexo server > /tmp/pwb-hexo.log 2>&1 &)
    ;;
  vitepress)
    URL="http://localhost:5173/"
    cd "$PROJECT_ROOT"
    echo "🚀 启动 VitePress dev server..."
    (npx vitepress dev docs > /tmp/pwb-vitepress.log 2>&1 &)
    ;;
  vue3)
    URL="http://localhost:5173/"
    cd "$PROJECT_ROOT"
    echo "🚀 启动 Vue 3 + Vite dev server..."
    (npx vite > /tmp/pwb-vue3.log 2>&1 &)
    ;;
  hugo)
    URL="http://localhost:1313/"
    cd "$PROJECT_ROOT"
    echo "🚀 启动 Hugo dev server..."
    (hugo server > /tmp/pwb-hugo.log 2>&1 &)
    ;;
  portfolio|resume)
    URL="file://$PROJECT_ROOT/index.html"
    echo "📄 纯静态项目，直接打开..."
    ;;
  *)
    echo "❌ 未知框架: $FRAMEWORK" >&2
    exit 1
    ;;
esac

# 等服务启动
if [ "$FRAMEWORK" != "portfolio" ] && [ "$FRAMEWORK" != "resume" ]; then
  echo "⏳ 等待服务启动（最多 15 秒）..."
  for i in $(seq 1 15); do
    sleep 1
    # 提取端口
    port="$(echo "$URL" | sed -E 's|.*://[^:]+:([0-9]+)/?.*|\1|')"
    if curl -s -o /dev/null "http://localhost:$port/" 2>/dev/null; then
      echo "✅ 服务已就绪"
      break
    fi
  done
fi

# 打开浏览器
if [ "$HEADLESS" = "true" ] || [ -z "$OPEN_CMD" ]; then
  echo ""
  echo "🖥️  检测到无 GUI 环境，请手动访问："
  echo "   $URL"
  echo ""
  echo "想停就告诉我「停掉预览」"
else
  echo "🌐 自动打开浏览器: $URL"
  if [ "$FRAMEWORK" = "portfolio" ] || [ "$FRAMEWORK" = "resume" ]; then
    "$OPEN_CMD" "$PROJECT_ROOT/index.html" 2>/dev/null &
  else
    "$OPEN_CMD" "$URL" 2>/dev/null &
  fi
fi