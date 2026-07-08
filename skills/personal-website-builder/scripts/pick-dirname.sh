#!/usr/bin/env bash
# pick-dirname.sh — 选择最终的项目目录（自动加 -2/-3 后缀）
# Usage: pick-dirname.sh <parent_dir> <base_name>
# Output: 最终目录的绝对路径（保证是空目录或可创建）

set -e

PARENT_DIR="$1"
BASE_NAME="$2"

if [ -z "$PARENT_DIR" ] || [ -z "$BASE_NAME" ]; then
  echo "Usage: $0 <parent_dir> <base_name>" >&2
  exit 1
fi

# 确保 parent 存在
mkdir -p "$PARENT_DIR"

CANDIDATE="$PARENT_DIR/$BASE_NAME"
SUFFIX=1

while [ -e "$CANDIDATE" ]; do
  if [ -z "$(ls -A "$CANDIDATE" 2>/dev/null)" ]; then
    # 目录存在但是空 → 直接用
    break
  fi
  SUFFIX=$((SUFFIX + 1))
  CANDIDATE="$PARENT_DIR/${BASE_NAME}-$SUFFIX"
done

# 如果目录不存在，创建
if [ ! -d "$CANDIDATE" ]; then
  mkdir -p "$CANDIDATE"
fi

# 用 realpath 输出绝对路径
if command -v realpath > /dev/null 2>&1; then
  realpath "$CANDIDATE"
else
  if command -v python3 > /dev/null 2>&1; then
    python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$CANDIDATE"
  else
    echo "$CANDIDATE"
  fi
fi