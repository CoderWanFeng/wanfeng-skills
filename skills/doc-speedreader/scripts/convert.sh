#!/usr/bin/env bash
# convert.sh — 调 MarkItDown 的统一入口
# 用法：
#   convert.sh <local-file>
#   convert.sh <url>
#   convert.sh --stream <file-extension>   # 从 stdin 读数据
#   convert.sh --response <url>            # 用 requests.get 自己抓
#
# 安全策略：
#   - 本地文件 → convert_local()（最窄权限）
#   - URL → convert()（带 10s 超时）
#   - stdin → convert_stream()（需指定 file_extension）
#   - --response → convert_response()（用户自控网络层）
#
# 详细路径校验规则见 reference/safety.md

set -eo pipefail
# 注：不用 set -u，因为后续 case 分支里 ${2:-} 等可能没传，避免 unbound variable 误报

INPUT="${1:-}"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
err() { echo -e "${RED}[✗]${NC} $*" 1>&2; }
info() { echo -e "${GREEN}[✓]${NC} $*"; }

# ============ -1. 不需要 markitdown 的命令（先处理）============
# --help 和空参数报错都不依赖 markitdown，放最前面，避免误报"没装"
case "$INPUT" in
    --help|-h)
        cat <<'EOF'
用法：
  convert.sh <local-file>          转本地文件（最安全）
  convert.sh <url>                 转公网 URL（http/https only）
  convert.sh --stream <ext>        从 stdin 读数据，需指定扩展名
  convert.sh --response <url>      用 requests.get 自己抓再转
  convert.sh --help                显示本帮助

示例：
  bash convert.sh report.pdf
  bash convert.sh https://example.com/page.html
  cat slides.pptx | bash convert.sh --stream .pptx
  bash convert.sh --response https://api.example.com/file.docx

详细文档见 ../reference/quickstart.md
EOF
        exit 0
        ;;
    "")
        err "【失败】没传参数"
        echo "  用法：bash convert.sh <local-file | url | --stream | --response>"
        echo "  详细：bash convert.sh --help"
        exit 1
        ;;
esac

# ============ 0. 依赖检测 ============
# 检测两件事：
#   a) markitdown 是否装了（import）
#   b) 是否能 import MarkItDown 类（老版本 0.0.1a1 没这个类）
if ! python3 -c "from markitdown import MarkItDown" 2>/dev/null; then
    if python3 -c "import markitdown" 2>/dev/null; then
        err "【失败】markitdown 版本太老（< 0.1.0），没有 MarkItDown 类"
        echo ""
        echo "📌 人话：你装的是 markitdown 0.0.1a1 老版本，本 skill 需要 0.1.x。"
        echo ""
        echo "🔍 根因：早期版本的 API 是模块级函数，不是 MarkItDown 类。"
        echo ""
        echo "🛠️ 3 步搞定："
        echo "  1. 升级：pip install -U 'markitdown[all]'"
        echo "  2. 验证：python3 -c 'from markitdown import MarkItDown; print(\"OK\")'"
        echo "  3. 再跑本脚本"
        echo ""
        echo "🆘 兜底：如果升级失败，先卸载再装："
        echo "     pip uninstall markitdown -y && pip install 'markitdown[all]'"
    else
        err "【失败】markitdown 没装"
        echo ""
        echo "📌 人话：还没装 markitdown 这个 Python 包。"
        echo ""
        echo "🔍 根因：第一次用这个 skill，需要先装依赖。"
        echo ""
        echo "🛠️ 3 步搞定："
        echo "  1. 跑安装脚本：bash scripts/install.sh"
        echo "  2. 装完再跑本脚本"
        echo "  3. 如果已经装了但还是报，检查 python3 路径（可能装在别的环境里）"
        echo ""
        echo "🆘 兜底：手动装：pip install 'markitdown[all]'"
    fi
    exit 1
fi

# ============ 1. 安全闸门：路径校验 ============
validate_local_path() {
    local path="$1"

    # 空路径
    if [ -z "$path" ]; then
        err "【失败】路径为空"
        exit 1
    fi

    # 不存在的路径
    if [ ! -e "$path" ]; then
        err "【失败】文件不存在：$path"
        echo ""
        echo "📌 人话：找不到这个文件。"
        echo "🔍 根因：路径写错 / 文件被删了 / 用了相对路径但当前目录不对"
        echo "🛠️ 3 步："
        echo "  1. 用 ls 看一下文件在不在"
        echo "  2. 用绝对路径（以 / 开头的）再试"
        echo "  3. 检查文件名是不是中文 / 含特殊字符"
        exit 1
    fi

    # 系统敏感目录（防止 AI 误把用户的命令搞成读 /etc/）
    case "$path" in
        /etc/*|/var/*|/root/*|/boot/*|/sys/*|/proc/*)
            err "【拒绝】禁止访问系统目录：$path"
            echo ""
            echo "📌 人话：这个路径太敏感了，我不读。"
            echo "🔍 根因：AI 不应该主动读 /etc/passwd 这类系统文件"
            echo "🛠️ 1 步：换个安全路径（你自己的文件）"
            exit 1
            ;;
    esac

    # 用户敏感目录
    case "$path" in
        ~/.ssh/*|~/.aws/*|~/.gnupg/*|~/.config/gh/*)
            err "【拒绝】禁止访问凭证目录：$path"
            echo ""
            echo "📌 人话：这是你的密钥目录，我不读（防止泄露）。"
            echo "🔍 根因：markitdown 会读文件全文，凭证文件不该过 AI"
            echo "🛠️ 1 步：换个非凭证目录的文件"
            exit 1
            ;;
    esac
}

# ============ 2. URL 校验 ============
validate_url() {
    local url="$1"
    if [[ ! "$url" =~ ^https?:// ]]; then
        err "【失败】URL 必须以 http:// 或 https:// 开头"
        echo "  收到的：$url"
        exit 1
    fi
    # 阻止 file:// ftp:// data: 等协议
    if [[ "$url" =~ ^(file|ftp|data|javascript|file):// ]]; then
        err "【拒绝】协议不安全：${url%%://*}"
        exit 1
    fi
    # 阻止内网地址（防 SSRF）
    if [[ "$url" =~ (127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|169\.254\.|::1|localhost) ]]; then
        err "【拒绝】禁止访问内网 / 回环地址"
        echo "  收到的：$url"
        echo ""
        echo "📌 人话：markitdown 会用进程权限发请求，内网地址有 SSRF 风险。"
        echo "🛠️ 1 步：用公网 URL 或本地文件路径"
        exit 1
    fi
}

# ============ 3. 模式分发（--help 和空参数已在前面处理）============
case "$INPUT" in
    --stream)
        # stdin 模式
        EXT="${2:-}"
        if [ -z "$EXT" ]; then
            err "【失败】--stream 模式必须指定 file_extension"
            echo "  用法：cat file.pdf | convert.sh --stream .pdf"
            exit 1
        fi
        info "模式：stdin（扩展名 $EXT）"
        python3 -c "
import sys
from markitdown import MarkItDown
result = MarkItDown().convert_stream(sys.stdin.buffer, file_extension='$EXT')
sys.stdout.write(result.text_content)
" || {
            err "【失败】转换失败"
            echo "  可能是文件格式损坏 / 不支持 / 数据流不完整"
            exit 1
        }
        ;;

    --response)
        # 用户已经 requests.get 过
        URL="${2:-}"
        if [ -z "$URL" ]; then
            err "【失败】--response 必须给 URL"
            exit 1
        fi
        validate_url "$URL"
        info "模式：response（自己抓，URL：$URL）"
        python3 -c "
import sys
from markitdown import MarkItDown
import requests
try:
    resp = requests.get('$URL', timeout=10)
    resp.raise_for_status()
    result = MarkItDown().convert_response(resp)
    sys.stdout.write(result.text_content)
except requests.exceptions.Timeout:
    print('[错误] 请求超时（10s）', file=sys.stderr)
    sys.exit(2)
except requests.exceptions.RequestException as e:
    print(f'[错误] 请求失败: {e}', file=sys.stderr)
    sys.exit(3)
" || exit $?
        ;;

    http://*|https://*)
        # URL 模式
        validate_url "$INPUT"
        info "模式：URL（$INPUT）"
        python3 -c "
import sys
from markitdown import MarkItDown
import requests
try:
    # 先试 convert()（markitdown 内部会 requests.get）
    result = MarkItDown().convert('$INPUT')
    sys.stdout.write(result.text_content)
except Exception as e:
    print(f'[错误] URL 转换失败: {e}', file=sys.stderr)
    print('可能：超时 / URL 无效 / 需要鉴权 / 服务端 5xx', file=sys.stderr)
    sys.exit(4)
" || exit $?
        ;;

    *)
        # 本地文件模式（默认）
        validate_local_path "$INPUT"
        info "模式：local file（$INPUT）"
        python3 -c "
import sys
from markitdown import MarkItDown
try:
    result = MarkItDown().convert_local('$INPUT')
    sys.stdout.write(result.text_content)
except Exception as e:
    print(f'[错误] 转换失败: {e}', file=sys.stderr)
    print('', file=sys.stderr)
    print('可能原因：', file=sys.stderr)
    print('  1. 文件格式不支持（详见 ../reference/formats.md）', file=sys.stderr)
    print('  2. 文件已损坏（PDF 扫描件需要 OCR 插件）', file=sys.stderr)
    print('  3. 文件被加密 / 加密文档', file=sys.stderr)
    print('  4. 权限不够', file=sys.stderr)
    sys.exit(5)
" || exit $?
        ;;
esac