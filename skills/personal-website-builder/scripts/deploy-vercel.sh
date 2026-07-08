#!/usr/bin/env bash
# deploy-vercel.sh — Vercel 部署
# Usage: deploy-vercel.sh <dist_dir> [project_name]
# 需要: 已登录 vercel CLI

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

# 检查 vercel
if ! command -v vercel > /dev/null 2>&1; then
  echo "❌ vercel CLI 未安装" >&2
  echo "   安装: npm install -g vercel" >&2
  exit 1
fi

# 检查登录
if [ ! -d "$HOME/.vercel" ]; then
  echo "⚠️  vercel 未登录" >&2
  echo "" >&2
  echo "在桌面环境运行: vercel login（会跳浏览器）" >&2
  echo "在 headless 环境：" >&2
  echo "  1. 去 https://vercel.com/account/tokens 创建 token" >&2
  echo "  2. export VERCEL_TOKEN=你的token" >&2
  exit 1
fi

# project name 推断
if [ -z "$PROJECT_NAME" ]; then
  PARENT_DIR="$(basename "$(cd "$(dirname "$DIST_DIR")" && pwd)")"
  PROJECT_NAME="$PARENT_DIR"
fi

echo "🚀 Vercel 部署: $DIST_DIR → $PROJECT_NAME"
cd "$(dirname "$DIST_DIR")"

if [ -n "$PROJECT_NAME" ]; then
  vercel --prod --yes --name "$PROJECT_NAME"
else
  vercel --prod --yes
fi

echo ""
echo "🌐 部署成功！查看 vercel.com/dashboard 拿 URL"