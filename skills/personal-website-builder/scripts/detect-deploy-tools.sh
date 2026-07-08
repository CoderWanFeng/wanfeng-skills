#!/usr/bin/env bash
# detect-deploy-tools.sh — 检测已安装的部署工具和环境
# Usage: source scripts/detect-deploy-tools.sh
# Output (stdout): JSON 状态

set -e

# 检测工具是否安装
is_installed() {
  command -v "$1" > /dev/null 2>&1
}

# 检测 Node 全局包
is_node_global() {
  npm list -g --depth=0 2>/dev/null | grep -q "$1@" && echo "true" || echo "false"
}

# 检测时区是否在中国大陆
is_china_timezone() {
  case "${TZ:-$(date +%Z)}" in
    Asia/Shanghai|Asia/Chongqing|Asia/Harbin|Asia/Urumqi|Asia/Hong_Kong|CST|CST-8)
      echo "true"
      ;;
    *)
      echo "false"
      ;;
  esac
}

# 检测系统语言
is_chinese_locale() {
  case "${LANG:-}" in
    zh*|zh_CN*|zh_TW*|zh_HK*)
      echo "true"
      ;;
    *)
      echo "false"
      ;;
  esac
}

# Netlify
NETLIFY_INSTALLED="false"
NETLIFY_LOGGED_IN="false"
NETLIFY_ANON_CAPABLE="false"
if is_installed netlify; then
  NETLIFY_INSTALLED="true"
  # 检查 netlify 是否已登录（有 config.json）
  if [ -f "$HOME/Library/Preferences/netlify/config.json" ] || [ -f "$HOME/.config/netlify/config.json" ]; then
    NETLIFY_LOGGED_IN="true"
  fi
  # 匿名部署需要 CLI 17.x+
  NETLIFY_VERSION="$(netlify --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo "0")"
  NETLIFY_ANON_CAPABLE="true"
fi

# Surge
SURGE_INSTALLED="false"
if is_installed surge; then
  SURGE_INSTALLED="true"
fi

# Cloudflare (wrangler)
CF_INSTALLED="false"
CF_TOKEN_SET="false"
if is_installed wrangler; then
  CF_INSTALLED="true"
  if [ -n "$CLOUDFLARE_API_TOKEN" ]; then
    CF_TOKEN_SET="true"
  fi
fi

# 腾讯云 CloudBase (tcb)
TCB_INSTALLED="false"
TCB_LOGGED_IN="false"
if is_installed tcb; then
  TCB_INSTALLED="true"
  # 检查 tcb 是否已登录
  if [ -d "$HOME/.tcb" ]; then
    TCB_LOGGED_IN="true"
  fi
fi

# Vercel
VERCEL_INSTALLED="false"
VERCEL_LOGGED_IN="false"
if is_installed vercel; then
  VERCEL_INSTALLED="true"
  if [ -d "$HOME/.vercel" ]; then
    VERCEL_LOGGED_IN="true"
  fi
fi

# GitHub CLI (gh)
GH_INSTALLED="false"
GH_AUTHED="false"
if is_installed gh; then
  GH_INSTALLED="true"
  if gh auth status > /dev/null 2>&1; then
    GH_AUTHED="true"
  fi
fi

# 智能推荐
CHINA_TZ="$(is_china_timezone)"
CHINA_LANG="$(is_chinese_locale)"

# 优先级：用户显式 > 登录账号 > 匿名 > 不推荐
if [ -n "$DEPLOY_PLATFORM_OVERRIDE" ]; then
  RECOMMENDED="$DEPLOY_PLATFORM_OVERRIDE"
elif [ "$TCB_INSTALLED" = "true" ] && [ "$TCB_LOGGED_IN" = "true" ] && [ "$CHINA_TZ" = "true" ]; then
  RECOMMENDED="cloudbase"
elif [ "$CF_TOKEN_SET" = "true" ]; then
  RECOMMENDED="cloudflare"
elif [ "$VERCEL_LOGGED_IN" = "true" ]; then
  RECOMMENDED="vercel"
elif [ "$NETLIFY_INSTALLED" = "true" ]; then
  RECOMMENDED="netlify"
elif [ "$SURGE_INSTALLED" = "true" ]; then
  RECOMMENDED="surge"
else
  RECOMMENDED="netlify"  # 默认推荐：Netlify（匿名部署能力）
fi

RECOMMEND_REASON=""
case "$RECOMMENDED" in
  cloudbase)
    RECOMMEND_REASON="CloudBase 已登录 + 中国时区，国内访问最快"
    ;;
  cloudflare)
    RECOMMEND_REASON="检测到 CLOUDFLARE_API_TOKEN，全球 CDN"
    ;;
  vercel)
    RECOMMEND_REASON="Vercel 已登录"
    ;;
  netlify)
    if [ "$NETLIFY_LOGGED_IN" = "true" ]; then
      RECOMMEND_REASON="Netlify 已登录"
    else
      RECOMMEND_REASON="Netlify 支持匿名部署（1 小时内认领）"
    fi
    ;;
  surge)
    RECOMMEND_REASON="Surge 已安装，首次免注册"
    ;;
esac

# 输出 JSON
cat <<EOF
{
  "platforms": {
    "netlify": {
      "installed": $NETLIFY_INSTALLED,
      "logged_in": $NETLIFY_LOGGED_IN,
      "anonymous_capable": $NETLIFY_ANON_CAPABLE
    },
    "surge": {
      "installed": $SURGE_INSTALLED
    },
    "cloudflare": {
      "installed": $CF_INSTALLED,
      "token_set": $CF_TOKEN_SET
    },
    "cloudbase": {
      "installed": $TCB_INSTALLED,
      "logged_in": $TCB_LOGGED_IN
    },
    "vercel": {
      "installed": $VERCEL_INSTALLED,
      "logged_in": $VERCEL_LOGGED_IN
    },
    "github_pages": {
      "gh_installed": $GH_INSTALLED,
      "gh_authed": $GH_AUTHED
    }
  },
  "context": {
    "china_timezone": $CHINA_TZ,
    "chinese_locale": $CHINA_LANG,
    "cwd": "$(pwd)"
  },
  "recommended": "$RECOMMENDED",
  "recommend_reason": "$RECOMMEND_REASON"
}
EOF