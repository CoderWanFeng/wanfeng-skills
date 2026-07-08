#!/usr/bin/env bash
# detect-env.sh — 检测运行环境，输出 JSON 状态
# Usage: source scripts/detect-env.sh
# Output: NODE_OK, NODE_VERSION, NPM_OK, NPM_VERSION, GIT_OK, OPEN_CMD, HEADLESS

set -e

NODE_OK="false"
NODE_VERSION=""
NPM_OK="false"
NPM_VERSION=""
GIT_OK="false"
CURL_OK="false"
OPEN_CMD=""
HEADLESS="false"

# Node
if command -v node > /dev/null 2>&1; then
  NODE_VERSION="$(node --version 2>/dev/null | sed 's/^v//')"
  # Hexo 7+ / VitePress / Vue 3 + Vite 都要求 Node 18+
  MAJOR="$(echo "$NODE_VERSION" | cut -d. -f1)"
  if [ -n "$MAJOR" ] && [ "$MAJOR" -ge 18 ] 2>/dev/null; then
    NODE_OK="true"
  fi
fi

# npm
if command -v npm > /dev/null 2>&1; then
  NPM_VERSION="$(npm --version 2>/dev/null)"
  NPM_OK="true"
fi

# git
if command -v git > /dev/null 2>&1; then
  GIT_OK="true"
fi

# curl
if command -v curl > /dev/null 2>&1; then
  CURL_OK="true"
fi

# 检测打开浏览器的命令（按平台）
case "$(uname -s 2>/dev/null)" in
  Darwin*)
    if command -v open > /dev/null 2>&1; then
      OPEN_CMD="open"
    fi
    ;;
  Linux*)
    if command -v xdg-open > /dev/null 2>&1; then
      OPEN_CMD="xdg-open"
    fi
    ;;
  MINGW*|CYGWIN*|MSYS*)
    if command -v start > /dev/null 2>&1; then
      OPEN_CMD="start"
    fi
    ;;
esac

# 检测是否无 GUI（CI / SSH / 容器）
if [ -z "$DISPLAY" ] && [ "$(uname -s)" != "Darwin" ] && [ -z "$OPEN_CMD" ]; then
  HEADLESS="true"
fi
# WSL / 容器内即使有 DISPLAY 也不一定有真实浏览器
if [ -n "$WSL_DISTRO_NAME" ] || [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
  HEADLESS="true"
fi

# 输出 JSON
cat <<EOF
{
  "node_ok": $NODE_OK,
  "node_version": "$NODE_VERSION",
  "npm_ok": $NPM_OK,
  "npm_version": "$NPM_VERSION",
  "git_ok": $GIT_OK,
  "curl_ok": $CURL_OK,
  "open_cmd": "$OPEN_CMD",
  "headless": $HEADLESS,
  "os": "$(uname -s)",
  "pwd": "$(pwd)"
}
EOF