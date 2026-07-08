#!/usr/bin/env bash
# deploy-surge.sh — Surge.sh 部署
# Usage: deploy-surge.sh <dist_dir> [domain]
# 首次运行：只输入 email + password 注册，之后会记住
# 后续运行：自动登录

set -e

DIST_DIR="$1"
DOMAIN="${2:-}"

if [ -z "$DIST_DIR" ]; then
  echo "Usage: $0 <dist_dir> [domain]" >&2
  exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ 部署目录不存在: $DIST_DIR" >&2
  exit 1
fi

# 检测 surge CLI
if ! command -v surge > /dev/null 2>&1; then
  echo "❌ surge CLI 未安装" >&2
  echo "   安装: npm install -g surge" >&2
  exit 1
fi

# 检查 surge 凭据
SURGE_LOGIN_ENV="$HOME/.netrc"
SURGE_HAS_CREDS="false"
if [ -f "$SURGE_LOGIN_ENV" ] && grep -q "surge.surge.sh" "$SURGE_LOGIN_ENV" 2>/dev/null; then
  SURGE_HAS_CREDS="true"
fi

if [ "$SURGE_HAS_CREDS" = "false" ]; then
  echo ""
  echo "⚠️  Surge 首次部署需要注册（输入 email + password）"
  echo "    之后凭据会保存到 ~/.netrc，不再需要输入"
  echo ""
fi

# 自动生成 domain（如果不指定）
if [ -z "$DOMAIN" ]; then
  # 从 dist_dir 推断
  BASENAME="$(basename "$(cd "$(dirname "$DIST_DIR")" && pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g')"
  if [ -z "$BASENAME" ]; then
    BASENAME="site-$(date +%s)"
  fi
  DOMAIN="${BASENAME}.surge.sh"
fi

echo "🚀 Surge 部署: $DIST_DIR → https://$DOMAIN"
surge "$DIST_DIR" "$DOMAIN"

echo ""
echo "🌐 部署成功！"
echo "   URL: https://$DOMAIN"