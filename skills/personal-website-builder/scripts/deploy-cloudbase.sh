#!/usr/bin/env bash
# deploy-cloudbase.sh — 腾讯云 CloudBase 静态托管部署
# Usage: deploy-cloudbase.sh <dist_dir> [env_id]
# 需要: 已登录 tcb CLI + 环境 ID

set -e

DIST_DIR="$1"
ENV_ID="${2:-}"

if [ -z "$DIST_DIR" ]; then
  echo "Usage: $0 <dist_dir> [env_id]" >&2
  exit 1
fi

if [ -z "$ENV_ID" ]; then
  echo "❌ 需要环境 ID (env_id)" >&2
  echo "" >&2
  echo "获取步骤：" >&2
  echo "  1. 打开 https://console.cloud.tencent.com/tcb" >&2
  echo "  2. 创建环境（实名认证 + 免费配额）" >&2
  echo "  3. 复制环境 ID（形如 myenv-1234567890）" >&2
  echo "  4. 重新运行并传入 env_id" >&2
  exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ 部署目录不存在: $DIST_DIR" >&2
  exit 1
fi

# 检查 tcb CLI
if ! command -v tcb > /dev/null 2>&1; then
  echo "❌ tcb CLI 未安装" >&2
  echo "   安装: npm install -g @cloudbase/cli" >&2
  exit 1
fi

# 检查 tcb 登录状态
if [ ! -d "$HOME/.tcb" ]; then
  echo "⚠️  tcb 未登录" >&2
  echo "" >&2
  echo "在桌面环境运行: tcb login（会跳浏览器）" >&2
  echo "在 headless 环境：" >&2
  echo "  1. 去 https://console.cloud.tencent.com/cam/capi 创建 API 密钥" >&2
  echo "  2. 运行: tcb login --apiKey" >&2
  echo "  3. 输入 SecretId 和 SecretKey" >&2
  exit 1
fi

echo "🚀 CloudBase 部署: $DIST_DIR → env $ENV_ID"
tcb hosting deploy "$DIST_DIR" -e "$ENV_ID"

echo ""
echo "🌐 部署成功！"
echo "   控制台查看默认域名: https://console.cloud.tencent.com/tcb"