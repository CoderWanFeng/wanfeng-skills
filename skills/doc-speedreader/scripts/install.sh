#!/usr/bin/env bash
# install.sh — 一键安装 MarkItDown
# 用法：bash install.sh
# 失败兜底：国内 pip 慢 → 切阿里源；Python 版本不够 → 引导装新版

set -eo pipefail
# 注：不用 set -u，避免用户缺变量时误报

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
    echo "📌 人话：MarkItDown 必须用 Python 3.10 或更高版本。"
    echo ""
    echo "🔍 根因：你当前的 Python 版本低于 3.10。"
    echo ""
    echo "🛠️ 3 步搞定："
    echo "  1. macOS 用户：brew install python@3.12"
    echo "  2. Linux 用户：sudo apt install python3.12（Ubuntu 22.04+）"
    echo "  3. 装完再跑本脚本"
    echo ""
    echo "🆘 兜底：不想装新 Python？用 conda 装一个虚拟环境："
    echo "     conda create -n markitdown python=3.12 && conda activate markitdown"
    echo "     然后在虚拟环境里跑本脚本"
    echo ""
    exit 1
fi

# ============ 2. 检测是否已装 ============
echo ""
echo "=== 第 2 步：检测 markitdown 是否已装 ==="

if "$PYTHON_BIN" -c "import markitdown; print(markitdown.__version__)" 2>/dev/null; then
    info "markitdown 已装，无需重复安装"
    exit 0
fi

warn "markitdown 未装，开始安装..."

# ============ 3. 检测网络环境，决定 pip 源 ============
echo ""
echo "=== 第 3 步：检测 pip 源（国内切阿里） ==="

PIP_INDEX="https://pypi.org/simple"
if "$PYTHON_BIN" -c "
import socket, sys
try:
    socket.create_connection(('pypi.org', 443), timeout=3)
except (OSError, socket.timeout):
    print('BLOCKED', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    info "PyPI 可达，用官方源"
else
    warn "PyPI 不可达（国内网络？），切阿里源"
    PIP_INDEX="https://mirrors.aliyun.com/pypi/simple/"
fi

# ============ 4. 安装 ============
echo ""
echo "=== 第 4 步：安装 markitdown[all] ==="
echo "（这可能需要 1-3 分钟，依赖较多）"
echo ""

if "$PYTHON_BIN" -m pip install -i "$PIP_INDEX" 'markitdown[all]'; then
    info "安装完成！"
    echo ""
    echo "=== 第 5 步：验证安装 ==="
    "$PYTHON_BIN" -c "import markitdown; print('  markitdown 版本：', markitdown.__version__)"
    echo ""
    info "✅ 全部搞定！你现在可以试试："
    echo "  bash scripts/convert.sh <某个 PDF 文件>"
else
    err "【失败】pip install 报错"
    echo ""
    echo "📌 人话：装包失败了，最常见是国内 pip 还是慢 / 网络抖动。"
    echo ""
    echo "🔍 根因：可能是网络问题、依赖冲突、或者二进制 wheel 装不上。"
    echo ""
    echo "🛠️ 3 步搞定："
    echo "  1. 重试一次本脚本（网络问题）"
    echo "  2. 如果是 M1/M2 Mac，加 --only-binary=:all:"
    echo "     pip install --only-binary=:all: 'markitdown[all]'"
    echo "  3. 如果报 'Microsoft Visual C++ 14.0 is required'（Windows）"
    echo "     去 https://visualstudio.microsoft.com/visual-cpp-build-tools/ 装编译工具"
    echo ""
    echo "🆘 兜底：实在装不上，临时用 Docker 跑："
    echo "     docker run --rm -i markitdown:latest < file.pdf > out.md"
    exit 1
fi