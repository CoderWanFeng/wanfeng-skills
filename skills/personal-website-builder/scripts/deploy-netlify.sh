#!/usr/bin/env bash
# deploy-netlify.sh — Netlify 部署（支持匿名部署）
# Usage:
#   deploy-netlify.sh <dist_dir> [project_name]
#   deploy-netlify.sh <dist_dir> [project_name] --anonymous
#   deploy-netlify.sh <dist_dir> [project_name] --prod

set -e

DIST_DIR="$1"
PROJECT_NAME="${2:-}"
shift 2 || true
MODE=""
for arg in "$@"; do
  case "$arg" in
    --anonymous) MODE="anonymous" ;;
    --prod) MODE="prod" ;;
  esac
done

if [ -z "$DIST_DIR" ]; then
  echo "Usage: $0 <dist_dir> [project_name] [--anonymous|--prod]" >&2
  exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ 部署目录不存在: $DIST_DIR" >&2
  exit 1
fi

# 检测 netlify CLI
if ! command -v netlify > /dev/null 2>&1; then
  echo "❌ netlify CLI 未安装" >&2
  echo "   安装: npm install -g netlify-cli" >&2
  exit 1
fi

cd "$(dirname "$DIST_DIR")"
ABS_DIST="$(basename "$DIST_DIR")"

# 检测是否已登录
LOGGED_IN="false"
if [ -f "$HOME/Library/Preferences/netlify/config.json" ] || [ -f "$HOME/.config/netlify/config.json" ]; then
  LOGGED_IN="true"
fi

# 默认模式：匿名
if [ -z "$MODE" ]; then
  if [ "$LOGGED_IN" = "true" ]; then
    MODE="prod"
  else
    MODE="anonymous"
  fi
fi

case "$MODE" in
  anonymous)
    echo "🚀 Netlify 匿名部署（1 小时内去 console 认领）..."
    netlify deploy --allow-anonymous --dir="$ABS_DIST" 2>&1 | tee /tmp/pwb-netlify.log
    # 同时匹配 http:// 和 https://
    URL="$(grep -oE 'https?://[a-zA-Z0-9-]+\.netlify\.app' /tmp/pwb-netlify.log | head -1)"
    PASSWORD="$(grep -A2 'Site URL' /tmp/pwb-netlify.log | grep -oE 'Password:\s+\S+' | awk '{print $2}')"
    if [ -z "$URL" ]; then
      echo "❌ 部署失败，查看日志: /tmp/pwb-netlify.log" >&2
      exit 1
    fi
    echo ""
    echo "🌐 部署成功！"
    echo "   URL: $URL"
    if [ -n "$PASSWORD" ]; then
      echo "   🔑 密码（Netlify 保护）: $PASSWORD"
    fi
    echo "   ⚠️  1 小时内去 https://app.netlify.com 登录认领，否则会被清理"
    echo "$URL" > /tmp/pwb-netlify-url.txt
    if [ -n "$PASSWORD" ]; then
      echo "$PASSWORD" > /tmp/pwb-netlify-password.txt
    fi
    ;;

  prod)
    echo "🚀 Netlify 生产部署（已登录）..."
    netlify deploy --dir="$ABS_DIST" --prod
    ;;

  *)
    echo "❌ 未知模式: $MODE" >&2
    exit 1
    ;;
esac