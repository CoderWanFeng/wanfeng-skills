#!/usr/bin/env bash
# install.sh — mp-saver v2.0 一键验证
# v2.0 不再依赖 Playwright / Chromium，只用 Python 标准库。
# 所以本脚本只做一件事：检查 Python 版本是否 ≥ 3.10。
#
# 用法：bash install.sh

set -eo pipefail
# 注：不用 set -u，避免用户缺变量时误报

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" 1>&2; }

# ============ 1. Python 版本检测 ============
echo "=== 第 1 步：检测 Python 版本 ==="

PYTHON_BIN=""
for candidate in python3 python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1; then
        VER=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN="$candidate"
            info "找到 Python $VER（路径：$(command -v "$candidate")）"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    err "【失败】没找到 Python ≥ 3.10"
    echo ""
    echo "📌 人话：mp-saver v2.0 需要 Python 3.10 或更高版本。"
    echo ""
    echo "🔍 根因：你当前的 Python 版本低于 3.10。"
    echo ""
    echo "🛠️ 3 步搞定："
    echo "  1. macOS 用户：brew install python@3.12"
    echo "  2. Linux 用户：sudo apt install python3.12（Ubuntu 22.04+）"
    echo "  3. 装完再跑本脚本"
    echo ""
    echo "🆘 兜底：不想装新 Python？用 conda 装一个虚拟环境："
    echo "     conda create -n mp-saver python=3.12 && conda activate mp-saver"
    echo ""
    exit 1
fi

# ============ 2. 走一遍 dry-run 验证 ============
echo ""
echo "=== 第 2 步：验证脚本能跑起来 ==="
echo "（用 --dry-run 测试，不会真保存）"
echo ""

if "$PYTHON_BIN" "$SKILL_DIR/scripts/save_mp.py" --dry-run \
    "https://mp.weixin.qq.com/s/example-dry-run-test"; then
    info "✅ 验证通过！v2.0 不需要装任何第三方包。"
    echo ""
    echo "📚 你现在可以保存公众号文章了："
    echo ""
    echo "  $PYTHON_BIN $SKILL_DIR/scripts/save_mp.py 'https://mp.weixin.qq.com/s/xxx'"
    echo ""
    echo "  批量保存（多个 URL）："
    echo "  $PYTHON_BIN $SKILL_DIR/scripts/save_mp.py url1 url2 url3"
    echo ""
    echo "  从 urls.txt 读（一行一个 URL，# 开头视为注释）："
    echo "  $PYTHON_BIN $SKILL_DIR/scripts/save_mp.py --file urls.txt"
    echo ""
    echo "  HTML 模式（不内嵌图，最快）："
    echo "  $PYTHON_BIN $SKILL_DIR/scripts/save_mp.py --format html 'https://...'"
    echo ""
    echo "  限内嵌图片数（避免 70MB 单文件）："
    echo "  $PYTHON_BIN $SKILL_DIR/scripts/save_mp.py --format mhtml --max-images 200 'https://...'"
else
    err "【失败】dry-run 都没过，可能是 Python 环境问题"
    echo ""
    echo "📌 人话：dry-run 是最简单测试，应该 1 秒内完成。"
    echo ""
    echo "🛠️ 3 步搞定："
    echo "  1. 确认 python3 + 路径正确：$PYTHON_BIN --version"
    echo "  2. 看上面的具体报错"
    echo "  3. 把 stderr 输出贴给 wanfeng 看看"
    echo ""
    exit 1
fi
