#!/usr/bin/env bash
# resolve-template.sh — 定位项目模板目录，兼容「目录形态」与「归档形态」两种分发方式
#
# 背景：WorkBuddy 等平台限制压缩包内最多一层子目录，而各框架模板天生带嵌套目录
# （templates/vue3-vite/src/components/*.vue、templates/hexo/source/_posts/*.md …）。
# 所以打包脚本用 --archive templates 把这些深层文件转成 templates-<框架>.tar.gz 放进包根：
#   · 包内路径只有一层，符合平台限制；
#   · 归档内保留完整目录结构，框架约定不破坏；
#   · .gitignore / .vue 待在平台扫不到的 tar 内部，不会被平台过滤掉。
#
# 本文件由 init-*.sh 用 source 加载，不要直接执行。
#
# 用法：
#   source "$SCRIPT_DIR/resolve-template.sh"
#   TEMPLATE_DIR="$(resolve_template_dir vue3-vite)"   # 框架标识 = templates/ 下的目录名
#
# 归档解包用的临时目录固定为 ${TMPDIR:-/tmp}/pwb-template-$$，
# 调用方用 trap 清理（见 init-*.sh 里的 TEMPLATE_STAGE）。

# 解包归档：优先用 tar，没有 tar 就退回 python3 的 tarfile
extract_template_archive() {
  local archive="$1"
  local target="$2"
  if command -v tar >/dev/null 2>&1; then
    tar -xzf "$archive" -C "$target"
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$archive" "$target" <<'PY'
import sys, tarfile
with tarfile.open(sys.argv[1]) as archive:
    try:
        archive.extractall(sys.argv[2], filter="data")
    except TypeError:          # Python < 3.12 没有 filter 参数
        archive.extractall(sys.argv[2])
PY
  else
    echo "✗ 既没有 tar 也没有 python3，无法解包模板归档：$archive" >&2
    return 1
  fi
}

# 打印模板目录；归档形态优先（避免被就地重建的半套目录遮蔽），目录形态兜底
resolve_template_dir() {
  local framework="$1"
  local skill_root
  skill_root="$(dirname "$SCRIPT_DIR")"
  local dir="$skill_root/templates/$framework"
  local archive="$skill_root/templates-$framework.tar.gz"
  local stage="${TMPDIR:-/tmp}/pwb-template-$$"

  if [ -f "$archive" ]; then
    mkdir -p "$stage"
    if ! extract_template_archive "$archive" "$stage"; then
      rm -rf "$stage"
      return 1
    fi
    if [ ! -d "$stage/$framework" ]; then
      echo "✗ 模板归档结构异常（缺 $framework/）：$archive" >&2
      rm -rf "$stage"
      return 1
    fi
    printf '%s\n' "$stage/$framework"
    return 0
  fi

  if [ -d "$dir" ]; then
    printf '%s\n' "$dir"
    return 0
  fi

  echo "✗ 找不到模板：既没有目录 $dir，也没有归档 $archive" >&2
  return 1
}
