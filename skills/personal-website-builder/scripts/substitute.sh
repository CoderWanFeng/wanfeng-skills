#!/usr/bin/env bash
# substitute.sh — 对文件做占位符替换
# Usage:
#   substitute.sh --var KEY=VALUE --var KEY=VALUE ... <files...>
#   substitute.sh --check <files...>     # 检查未登记的占位符
#   substitute.sh --empty-line-delete KEY <files...>   # 留空则删除整行

# 注意：避免 declare -A（macOS bash 3.2 不支持）

set -e

# 用普通变量 + 函数代替关联数组
# 解析参数
VAR_KEYS=()
VAR_VALUES=()
CHECK_ONLY="false"
DELETE_KEYS=()
FILES=()

parse_var() {
  local kv="$1"
  local key="${kv%%=*}"
  local value="${kv#*=}"
  VAR_KEYS+=("$key")
  VAR_VALUES+=("$value")
}

while [ $# -gt 0 ]; do
  case "$1" in
    --var)
      parse_var "$2"
      shift 2
      ;;
    --empty-line-delete)
      DELETE_KEYS+=("$2")
      shift 2
      ;;
    --check)
      CHECK_ONLY="true"
      shift
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "Usage: $0 [--var KEY=VALUE]... [--empty-line-delete KEY]... <files...>" >&2
  exit 1
fi

# 运行时变量
DATE_ISO="$(date +%Y-%m-%d)"
DATE_PATH="$(date +%Y/%m/%d)"
YEAR="$(date +%Y)"

# 框架查表（用 case 代替关联数组）
get_dist() {
  case "$1" in
    hexo) echo "public" ;;
    vitepress) echo "docs/.vitepress/dist" ;;
    vue3) echo "dist" ;;
    hugo) echo "public" ;;
    portfolio) echo "." ;;
    resume) echo "." ;;
    *) echo "dist" ;;
  esac
}
get_port() {
  case "$1" in
    hexo) echo "4000" ;;
    vitepress|vue3) echo "5173" ;;
    hugo) echo "1313" ;;
    *) echo "3000" ;;
  esac
}
get_dev_cmd() {
  case "$1" in
    hexo) echo "npx hexo server" ;;
    vitepress) echo "npx vitepress dev docs" ;;
    vue3) echo "npx vite" ;;
    hugo) echo "hugo server" ;;
    portfolio|resume) echo "open index.html" ;;
    *) echo "npm run dev" ;;
  esac
}
get_build_cmd() {
  case "$1" in
    hexo) echo "npx hexo generate" ;;
    vitepress) echo "npx vitepress build docs" ;;
    vue3) echo "npx vite build" ;;
    hugo) echo "hugo" ;;
    portfolio|resume) echo "echo 'No build step needed'" ;;
    *) echo "npm run build" ;;
  esac
}

# 如果用户提供了 FRAMEWORK，注入框架相关的派生变量
for i in "${!VAR_KEYS[@]}"; do
  key="${VAR_KEYS[$i]}"
  if [ "$key" = "FRAMEWORK" ]; then
    fw="${VAR_VALUES[$i]}"
    VAR_KEYS+=("DIST_DIR"); VAR_VALUES+=("$(get_dist "$fw")")
    VAR_KEYS+=("DEV_PORT"); VAR_VALUES+=("$(get_port "$fw")")
    VAR_KEYS+=("DEV_CMD"); VAR_VALUES+=("$(get_dev_cmd "$fw")")
    VAR_KEYS+=("BUILD_CMD"); VAR_VALUES+=("$(get_build_cmd "$fw")")
    break
  fi
done

# 注入运行时变量
VAR_KEYS+=("DATE_ISO"); VAR_VALUES+=("$DATE_ISO")
VAR_KEYS+=("DATE_PATH"); VAR_VALUES+=("$DATE_PATH")
VAR_KEYS+=("YEAR"); VAR_VALUES+=("$YEAR")

# 自动从 SITE_NAME 派生 SITE_NAME_SLUG（如果用户没显式提供）
has_slug="false"
for j in "${!VAR_KEYS[@]}"; do
  if [ "${VAR_KEYS[$j]}" = "SITE_NAME_SLUG" ]; then
    has_slug="true"
    break
  fi
done
if [ "$has_slug" = "false" ]; then
  for j in "${!VAR_KEYS[@]}"; do
    if [ "${VAR_KEYS[$j]}" = "SITE_NAME" ]; then
      slug="$(echo "${VAR_VALUES[$j]}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')"
      if [ -z "$slug" ]; then
        slug="my-site"
      fi
      VAR_KEYS+=("SITE_NAME_SLUG")
      VAR_VALUES+=("$slug")
      break
    fi
  done
fi

# 检查模式
if [ "$CHECK_ONLY" = "true" ]; then
  REGISTERED='SITE_NAME|SITE_NAME_SLUG|SITE_DESCRIPTION|AUTHOR_NAME|AUTHOR_NAME_OR_DEFAULT|GITHUB_USERNAME|GITHUB_OR_EMPTY|FRAMEWORK|SITE_TYPE|SITE_TYPE_EN|DATE_ISO|DATE_PATH|YEAR|PROJECT_ROOT|DIST_DIR|DEV_PORT|DEV_CMD|BUILD_CMD'
  for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
      found="$(grep -oE '\{\{[A-Z_]+\}\}' "$f" 2>/dev/null | sort -u || true)"
      for ph in $found; do
        clean="$(echo "$ph" | sed 's/[{}]//g')"
        if ! echo "$clean" | grep -qE "^($REGISTERED)$"; then
          echo "❌ 未登记的占位符: $ph （在 $f）" >&2
          exit 1
        fi
      done
    fi
  done
  echo "✅ 所有占位符已登记"
  exit 0
fi

# 替换模式
for f in "${FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "⚠️  跳过不存在的文件: $f" >&2
    continue
  fi

  # 1. 标准占位符替换
  for i in "${!VAR_KEYS[@]}"; do
    key="${VAR_KEYS[$i]}"
    value="${VAR_VALUES[$i]}"
    # 用 | 作为 sed 分隔符（避免路径里的 /）
    if [[ "$(uname -s)" == "Darwin" ]]; then
      sed -i '' "s|{{$key}}|$value|g" "$f"
    else
      sed -i "s|{{$key}}|$value|g" "$f"
    fi
  done

  # 2. 条件删除占位符（如果整行只是这个占位符或包含空值）
  for delete_key in "${DELETE_KEYS[@]}"; do
    # 如果该占位符在文件里且对应变量值为空，删除整行
    found_var_value=""
    for j in "${!VAR_KEYS[@]}"; do
      if [ "${VAR_KEYS[$j]}" = "$delete_key" ]; then
        found_var_value="${VAR_VALUES[$j]}"
        break
      fi
    done
    if [ -z "$found_var_value" ]; then
      if [[ "$(uname -s)" == "Darwin" ]]; then
        sed -i '' "/{{$delete_key}}/d" "$f"
      else
        sed -i "/{{$delete_key}}/d" "$f"
      fi
    fi
  done
done

echo "✅ 占位符替换完成: ${FILES[*]}"