#!/usr/bin/env bash
# deploy-cloudflare.sh — Cloudflare Pages 部署
# Usage: deploy-cloudflare.sh <dist_dir> [project_name]
# 需要: CLOUDFLARE_API_TOKEN 环境变量
# 获取 token: https://dash.cloudflare.com/profile/api-tokens

set -e

DIST_DIR="$1"
PROJECT_NAME="${2:-}"

if [ -z "$DIST_DIR" ]; then
  echo "Usage: $0 <dist_dir> [project_name]" >&2
  exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ 部署目录不存在: $DIST_DIR" >&2
  exit 1
fi

# 检查 token
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  echo "❌ 未设置 CLOUDFLARE_API_TOKEN" >&2
  echo "" >&2
  echo "获取步骤：" >&2
  echo "  1. 打开 https://dash.cloudflare.com/profile/api-tokens" >&2
  echo "  2. Create Token → Edit Cloudflare Pages template" >&2
  echo "  3. 复制 token" >&2
  echo "  4. 终端: export CLOUDFLARE_API_TOKEN=你的token" >&2
  exit 1
fi

# 检查 wrangler
if ! command -v wrangler > /dev/null 2>&1; then
  echo "❌ wrangler CLI 未安装" >&2
  echo "   安装: npm install -g wrangler" >&2
  exit 1
fi

# project name 推断
if [ -z "$PROJECT_NAME" ]; then
  PARENT_DIR="$(basename "$(cd "$(dirname "$DIST_DIR")" && pwd)")"
  PROJECT_NAME="$(echo "$PARENT_DIR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g')"
fi

echo "🚀 Cloudflare Pages 部署: $DIST_DIR → $PROJECT_NAME"
wrangler pages deploy "$DIST_DIR" --project-name="$PROJECT_NAME"

echo ""
echo "🌐 部署成功！"
echo "   URL: https://$PROJECT_NAME.pages.dev"