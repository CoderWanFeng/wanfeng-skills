#!/usr/bin/env bash
# deploy.sh — 部署主入口
# Usage:
#   deploy.sh <framework> <project_root> [options]
#
# Options:
#   --platform=netlify|surge|cloudflare|cloudbase|vercel|github_pages
#   --dist=<dist_dir>          显式指定 dist 目录（覆盖自动推断）
#   --domain=<domain>          自定义子域名（Surge/Netlify）
#   --env-id=<env_id>          CloudBase 环境 ID
#   --repo=<repo>              GitHub Pages 仓库名
#   --token=<token>            Cloudflare API token
#   --no-verify                跳过 URL 验证
#   --no-optimize              跳过构建产物优化
#   --anonymous                Netlify 匿名部署（即使已登录）
#
# Examples:
#   deploy.sh hexo /path/to/blog
#   deploy.sh hexo /path/to/blog --platform=netlify
#   deploy.sh hexo /path/to/blog --platform=surge --domain=myblog
#   deploy.sh vue3 /path/to/tools --platform=netlify --anonymous

set -e

FRAMEWORK="$1"
PROJECT_ROOT="$2"
shift 2 || true

# 默认值
PLATFORM=""
DIST_OVERRIDE=""
DOMAIN=""
ENV_ID=""
REPO=""
TOKEN=""
VERIFY="true"
ANONYMOUS="false"
OPTIMIZE="true"

# 解析参数
for arg in "$@"; do
  case "$arg" in
    --platform=*) PLATFORM="${arg#--platform=}" ;;
    --dist=*) DIST_OVERRIDE="${arg#--dist=}" ;;
    --domain=*) DOMAIN="${arg#--domain=}" ;;
    --env-id=*) ENV_ID="${arg#--env-id=}" ;;
    --repo=*) REPO="${arg#--repo=}" ;;
    --token=*) CLOUDFLARE_API_TOKEN="$TOKEN"; export CLOUDFLARE_API_TOKEN ;;
    --no-verify) VERIFY="false" ;;
    --no-optimize) OPTIMIZE="false" ;;
    --anonymous) ANONYMOUS="true" ;;
  esac
done

if [ -z "$FRAMEWORK" ] || [ -z "$PROJECT_ROOT" ]; then
  echo "Usage: deploy.sh <framework> <project_root> [options]" >&2
  echo "" >&2
  echo "Options:" >&2
  echo "  --platform=netlify|surge|cloudflare|cloudbase|vercel|github_pages" >&2
  echo "  --dist=<dir>           dist 目录" >&2
  echo "  --domain=<domain>      子域名" >&2
  echo "  --env-id=<id>          CloudBase 环境 ID" >&2
  echo "  --repo=<repo>          GitHub 仓库名" >&2
  echo "  --token=<token>        Cloudflare API token" >&2
  echo "  --no-verify            跳过 URL 验证" >&2
  echo "  --anonymous            Netlify 匿名部署" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 推断 dist 目录
infer_dist() {
  case "$FRAMEWORK" in
    hexo) echo "public" ;;
    vitepress) echo "docs/.vitepress/dist" ;;
    vue3) echo "dist" ;;
    hugo) echo "public" ;;
    portfolio|resume) echo "." ;;
    *) echo "dist" ;;
  esac
}

if [ -n "$DIST_OVERRIDE" ]; then
  DIST_DIR="$PROJECT_ROOT/$DIST_OVERRIDE"
else
  RELATIVE_DIST="$(infer_dist)"
  DIST_DIR="$PROJECT_ROOT/$RELATIVE_DIST"
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ 部署目录不存在: $DIST_DIR" >&2
  echo "   提示：先跑 init 脚本和 build" >&2
  exit 1
fi

# 优化构建产物（如果启用）
if [ "$OPTIMIZE" = "true" ]; then
  echo "🚀 优化构建产物..."
  "$SCRIPT_DIR/optimize-all.sh" "$FRAMEWORK" "$PROJECT_ROOT"
  echo ""

  # 如果有优化后的目录，自动切换
  REL_DIST="$(infer_dist)"
  OPT_DIST_NAME="$(basename "$REL_DIST")-optimized"
  if [ -d "$PROJECT_ROOT/$OPT_DIST_NAME" ]; then
    DIST_DIR="$PROJECT_ROOT/$OPT_DIST_NAME"
    echo "📦 使用优化后的部署目录: $DIST_DIR"
    echo ""
  fi
fi

# 检测工具
if [ -z "$PLATFORM" ]; then
  echo "🔍 检测可用部署平台..."
  DETECT_JSON="$("$SCRIPT_DIR/detect-deploy-tools.sh" 2>/dev/null)"
  PLATFORM="$(echo "$DETECT_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['recommended'])" 2>/dev/null || echo "netlify")"
  REASON="$(echo "$DETECT_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['recommend_reason'])" 2>/dev/null || echo "")"
  echo "  推荐平台: $PLATFORM"
  if [ -n "$REASON" ]; then
    echo "  原因: $REASON"
  fi
  echo ""
fi

# 执行对应平台的部署
DEPLOY_URL=""

case "$PLATFORM" in
  netlify)
    ANON_FLAG=""
    if [ "$ANONYMOUS" = "true" ]; then
      ANON_FLAG="--anonymous"
    fi
    if [ -n "$DOMAIN" ]; then
      "$SCRIPT_DIR/deploy-netlify.sh" "$DIST_DIR" "$DOMAIN" $ANON_FLAG
    else
      "$SCRIPT_DIR/deploy-netlify.sh" "$DIST_DIR" "" $ANON_FLAG
    fi
    DEPLOY_URL="$(cat /tmp/pwb-netlify-url.txt 2>/dev/null || echo "")"
    ;;

  surge)
    "$SCRIPT_DIR/deploy-surge.sh" "$DIST_DIR" "$DOMAIN"
    if [ -n "$DOMAIN" ]; then
      DEPLOY_URL="https://$DOMAIN"
    else
      DEPLOY_URL="https://$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]').surge.sh"
    fi
    ;;

  cloudflare)
    "$SCRIPT_DIR/deploy-cloudflare.sh" "$DIST_DIR" "$DOMAIN"
    if [ -n "$DOMAIN" ]; then
      DEPLOY_URL="https://$DOMAIN.pages.dev"
    fi
    ;;

  cloudbase)
    "$SCRIPT_DIR/deploy-cloudbase.sh" "$DIST_DIR" "$ENV_ID"
    DEPLOY_URL="https://$ENV_ID.tcloudbaseapp.com"
    ;;

  vercel)
    "$SCRIPT_DIR/deploy-vercel.sh" "$DIST_DIR" "$DOMAIN"
    ;;

  github_pages)
    if [ -z "$REPO" ]; then
      REPO="$(basename "$PROJECT_ROOT")"
    fi
    "$SCRIPT_DIR/deploy-github-pages.sh" "$DIST_DIR" "$REPO"
    ;;

  *)
    echo "❌ 未知平台: $PLATFORM" >&2
    echo "   支持: netlify, surge, cloudflare, cloudbase, vercel, github_pages" >&2
    exit 1
    ;;
esac

# 验证部署
if [ "$VERIFY" = "true" ] && [ -n "$DEPLOY_URL" ]; then
  # 从 dist 目录里读 title（如果有）
  EXPECTED_TITLE=""
  for f in "$DIST_DIR/index.html" "$DIST_DIR"/public/index.html; do
    if [ -f "$f" ]; then
      EXPECTED_TITLE="$(grep -oE '<title>[^<]+</title>' "$f" | head -1 | sed 's|<title>||;s|</title>||')"
      break
    fi
  done

  echo ""
  "$SCRIPT_DIR/verify-deploy.sh" "$DEPLOY_URL" "$EXPECTED_TITLE" 180
fi

# 保存部署状态
STATE_FILE="$PROJECT_ROOT/.deploy-state.json"
cat > "$STATE_FILE" <<EOF
{
  "platform": "$PLATFORM",
  "url": "$DEPLOY_URL",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "framework": "$FRAMEWORK",
  "dist_dir": "$DIST_DIR"
}
EOF

echo ""
echo "💾 部署状态已保存到: $STATE_FILE"
echo "   重新部署: deploy.sh $FRAMEWORK $PROJECT_ROOT --no-verify"