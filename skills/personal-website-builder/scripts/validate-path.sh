#!/usr/bin/env bash
# validate-path.sh — 校验用户提供的路径是否安全
# Usage: scripts/validate-path.sh <path>
# Output (stdout): 规范化后的绝对路径
# Exit codes:
#   0  — 路径安全
#   1  — 参数错误
#   2  — 路径在系统目录黑名单内
#   3  — 路径解析后越界（含 ..）
#   4  — 路径不可写
#   5  — 路径是符号链接到非法目标

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <path>" >&2
  exit 1
fi

INPUT_PATH="$1"

# 先做 tilde 展开（realpath -m 不一定展开 ~）
INPUT_PATH="${INPUT_PATH/#\~/$HOME}"

# 系统目录黑名单（绝对匹配前缀）
SYSTEM_DIRS=(
  "/System"
  "/usr"
  "/etc"
  "/bin"
  "/sbin"
  "/var"
  "/private"
  "/boot"
  "$HOME/Library"
  "C:\\Windows"
  "C:\\Program Files"
  "C:\\Program Files (x86)"
)

# 1. 解析为绝对路径
if command -v realpath > /dev/null 2>&1; then
  ABS_PATH="$(realpath -m "$INPUT_PATH" 2>/dev/null || echo "$INPUT_PATH")"
else
  # macOS 默认没有 GNU realpath（BSD readlink 没有 -f），用 Python 兜底
  if command -v python3 > /dev/null 2>&1; then
    ABS_PATH="$(python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$INPUT_PATH" 2>/dev/null || echo "$INPUT_PATH")"
  else
    ABS_PATH="$INPUT_PATH"
  fi
fi

# 2. 检查是否包含 ..（规范化后就不该有了）
if [[ "$ABS_PATH" == *".."* ]]; then
  echo "❌ 路径包含 '..' 越界: $ABS_PATH" >&2
  exit 3
fi

# 3. 检查是否是根目录
if [ "$ABS_PATH" = "/" ] || [ -z "$ABS_PATH" ]; then
  echo "❌ 不允许使用根目录作为项目目录" >&2
  exit 3
fi

# 4. 检查系统目录黑名单
for sys_dir in "${SYSTEM_DIRS[@]}"; do
  if [[ "$ABS_PATH" == "$sys_dir"* ]]; then
    echo "❌ 路径落在系统/用户核心目录: $sys_dir（不允许）" >&2
    exit 2
  fi
done

# 5. 检查符号链接（如果是 symlink，解析后再次校验）
if [ -L "$INPUT_PATH" ]; then
  LINK_TARGET="$(readlink -f "$INPUT_PATH" 2>/dev/null || python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$INPUT_PATH" 2>/dev/null)"
  for sys_dir in "${SYSTEM_DIRS[@]}"; do
    if [[ "$LINK_TARGET" == "$sys_dir"* ]]; then
      echo "❌ 符号链接指向系统目录: $LINK_TARGET" >&2
      exit 5
    fi
  done
fi

# 6. 检查是否可创建（mkdir -p 测试）
TEST_DIR="$ABS_PATH"
if [ ! -d "$TEST_DIR" ]; then
  if ! mkdir -p "$TEST_DIR" 2>/dev/null; then
    echo "❌ 路径不可创建（权限不足或父目录不存在）: $ABS_PATH" >&2
    exit 4
  fi
  # 测试用完就删除（保持原状）
  rmdir "$TEST_DIR" 2>/dev/null || true
fi

# 7. 检查父目录是否可写
PARENT_DIR="$(dirname "$ABS_PATH")"
if [ -d "$PARENT_DIR" ] && [ ! -w "$PARENT_DIR" ]; then
  echo "❌ 父目录无写权限: $PARENT_DIR" >&2
  exit 4
fi

# 通过
echo "$ABS_PATH"