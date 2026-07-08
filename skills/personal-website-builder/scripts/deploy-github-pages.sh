#!/usr/bin/env bash
# deploy-github-pages.sh — GitHub Pages 部署
# Usage: deploy-github-pages.sh <dist_dir> <repo_name>
# 需要: gh CLI 已认证 + 仓库已存在（或 gh 可以创建）
#
# 流程：
#   1. 检查 gh 登录
#   2. 检查仓库是否存在，不存在则创建
#   3. 创建临时分支 gh-pages
#   4. 推送 dist 内容
#   5. 设置 Pages 源为 gh-pages 分支

set -e

DIST_DIR="$1"
REPO_NAME="${2:-}"

if [ -z "$DIST_DIR" ] || [ -z "$REPO_NAME" ]; then
  echo "Usage: $0 <dist_dir> <repo_name>" >&2
  exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ 部署目录不存在: $DIST_DIR" >&2
  exit 1
fi

# 检查 gh
if ! command -v gh > /dev/null 2>&1; then
  echo "❌ gh CLI 未安装" >&2
  echo "   macOS: brew install gh" >&2
  echo "   Linux: 见 https://github.com/cli/cli#installation" >&2
  exit 1
fi

# 检查认证
if ! gh auth status > /dev/null 2>&1; then
  echo "❌ gh 未认证" >&2
  echo "   运行: gh auth login" >&2
  exit 1
fi

GH_USER="$(gh api user -q .login)"
FULL_REPO="$GH_USER/$REPO_NAME"

# 检查仓库是否存在
if ! gh repo view "$FULL_REPO" > /dev/null 2>&1; then
  echo "📦 仓库 $FULL_REPO 不存在，正在创建..."
  gh repo create "$FULL_REPO" --public --source=. --remote=origin
fi

# 准备 gh-pages 分支
WORK_DIR="$(mktemp -d)"
cp -r "$DIST_DIR/." "$WORK_DIR/"
cd "$WORK_DIR"

git init -q
git checkout -q --orphan gh-pages
git add -A
git -c user.email=deploy@local -c user.name=Deployer commit -q -m "Deploy to GitHub Pages"
git remote add origin "https://github.com/$FULL_REPO.git"
git push -q -f origin gh-pages

cd - > /dev/null
rm -rf "$WORK_DIR"

# 启用 GitHub Pages（如果还没启用）
echo "📝 启用 GitHub Pages..."
gh repo edit "$FULL_REPO" --enable-pages --pages-source-branch=gh-pages 2>/dev/null || true

echo ""
echo "🌐 部署成功！"
echo "   URL: https://$GH_USER.github.io/$REPO_NAME/"
echo "   （首次访问可能需要等 1-2 分钟）"