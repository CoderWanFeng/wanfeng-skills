#!/usr/bin/env bash
# verify-deploy.sh — 部署后 URL 验证
# Usage: verify-deploy.sh <url> [expected_title] [max_wait_seconds]
# Exit codes:
#   0 — URL 200 + 内容匹配
#   1 — 参数错误
#   2 — URL 持续不可达
#   3 — URL 200 但内容不匹配
#   4 — 部署超时

set -e

URL="$1"
EXPECTED_TITLE="${2:-}"
MAX_WAIT="${3:-300}"  # 默认等 5 分钟

if [ -z "$URL" ]; then
  echo "Usage: $0 <url> [expected_title] [max_wait_seconds]" >&2
  exit 1
fi

echo "🔍 验证部署: $URL"

# 指数退避重试
WAIT=5
ELAPSED=0
HTTP_CODE=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
  # 用 -L 跟随重定向（Netlify 默认 301 → https）
  HTTP_CODE="$(curl -sL -o /dev/null -w "%{http_code}" --max-time 10 "$URL" 2>/dev/null || echo "000")"

  # 200 成功；401 = 站点活着但密码保护（Netlify 匿名部署默认）
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "  ✅ HTTP $HTTP_CODE（等待 ${ELAPSED}s）"
    break
  fi

  echo "  ⏳ HTTP $HTTP_CODE，等待 ${WAIT}s 后重试...（已等 ${ELAPSED}s）"
  sleep $WAIT
  ELAPSED=$((ELAPSED + WAIT))
  WAIT=$((WAIT * 2))
  if [ $WAIT -gt 60 ]; then
    WAIT=60
  fi
done

if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "401" ]; then
  echo ""
  echo "❌ 验证失败：URL 持续返回 $HTTP_CODE（等了 ${ELAPSED}s）" >&2
  exit 2
fi

# 检查 expected title（401 站点跳过标题检查）
if [ -n "$EXPECTED_TITLE" ] && [ "$HTTP_CODE" != "401" ]; then
  CONTENT="$(curl -sL --max-time 10 "$URL" 2>/dev/null || echo "")"
  if echo "$CONTENT" | grep -qF "$EXPECTED_TITLE"; then
    echo "  ✅ 内容包含期望标题: $EXPECTED_TITLE"
  else
    echo "  ⚠️  HTTP 200 但内容不含期望标题: $EXPECTED_TITLE"
    echo "     实际内容前 200 字符:"
    echo "$CONTENT" | head -c 200
    echo ""
    exit 3
  fi
fi

# 额外检查
SIZE="$(curl -sL -o /dev/null -w "%{size_download}" --max-time 10 "$URL" 2>/dev/null || echo "0")"
TIME="$(curl -sL -o /dev/null -w "%{time_total}" --max-time 10 "$URL" 2>/dev/null || echo "0")"
echo "  📊 页面大小: ${SIZE} bytes"
echo "  ⏱️  响应时间: ${TIME}s"

echo ""
echo "🎉 部署验证通过！"
echo "   URL: $URL"