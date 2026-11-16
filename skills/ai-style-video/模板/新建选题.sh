#!/usr/bin/env bash
# 新建一条 MG 风格短视频的工程目录。
#
# 用法：
#   ./新建选题.sh <选题名> <风格代号>
#
# 例：
#   ./新建选题.sh "某产品新版速览" D
#
# 工程目录建在当前工作目录下（可用环境变量 MG_TOPIC_ROOT 指定另一个根目录）。
# 风格代号 A–H 见下面 case 分支，或直接不带参数运行本脚本查用法。
#
# 自定义风格（代号 I）：用户自己描述风格要求时用。靠两个环境变量指定：
#   MG_STYLE_BASE  借哪个内置风格当渲染底子（代号，默认 F）
#   MG_STYLE_NAME  自定义风格名（工程目录叫 MG样片-<风格名>，默认「自定义」）
# 例：MG_STYLE_BASE=D MG_STYLE_NAME=赛博霓虹 ./新建选题.sh "某产品新版速览" I
# 用户的原始风格要求由 Agent 写进工程的 选题资料.md，脚本不接收这段内容。
#
# 产出结构：
#   <选题名>/
#   ├── 素材-官网截图-HD/     2x 高清官网截图
#   ├── 素材-证据图/          裁好的证据图（原版 + 亮版）
#   ├── MG样片-<风格名>/      渲染工程
#   ├── 内容编排方法论.md
#   └── 选题资料.md
set -euo pipefail

TOPIC="${1:-}"
STYLE="${2:-F}"
# 选题工程落地根目录：默认当前目录，不依赖任何固定路径
SHORT="${MG_TOPIC_ROOT:-$PWD}"
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "$TOPIC" ]]; then
  echo "用法：$0 <选题名> <风格代号>"
  echo "风格代号：A 深色科技 / B 亮色杂志 / C 复古拼贴 / D 故障艺术 / E 像素游戏 / F 暖色治愈 / G 简笔画 / H 工笔画 / I 自定义"
  echo "自定义（I）：MG_STYLE_BASE=<底子代号，默认 F> MG_STYLE_NAME=<风格名，默认 自定义>"
  exit 1
fi

# 选题名里的斜杠会造成路径问题，去掉
TOPIC="${TOPIC//\//-}"

style_src() {
  case "$1" in
    A) echo "$SKILL/模板/风格库/MG样片" ;;
    B) echo "$SKILL/模板/风格库/MG样片-亮色动效" ;;
    C) echo "$SKILL/模板/风格库/MG样片-复古拼贴" ;;
    D) echo "$SKILL/模板/风格库/MG样片-故障艺术" ;;
    E) echo "$SKILL/模板/风格库/MG样片-像素游戏" ;;
    F) echo "$SKILL/模板/风格库/MG样片-暖色治愈" ;;
    G) echo "$SKILL/模板/风格库/MG样片-简笔画" ;;
    H) echo "$SKILL/模板/风格库/MG样片-工笔画" ;;
    *) return 1 ;;
  esac
}

case "$STYLE" in
  A) STYLE_NAME="深色科技" ;;
  B) STYLE_NAME="亮色动效" ;;
  C) STYLE_NAME="复古拼贴" ;;
  D) STYLE_NAME="故障艺术" ;;
  E) STYLE_NAME="像素游戏" ;;
  F) STYLE_NAME="暖色治愈" ;;
  G) STYLE_NAME="简笔画" ;;
  H) STYLE_NAME="工笔画" ;;
  I)
    # 自定义风格：借一个内置风格当渲染底子，版式/配色/动效由 Agent 按用户要求改
    BASE="${MG_STYLE_BASE:-F}"
    STYLE_NAME="${MG_STYLE_NAME:-自定义}"
    SRC="$(style_src "$BASE")" || SRC=""
    if [[ -z "$SRC" ]]; then
      echo "自定义风格的底子代号不认识：MG_STYLE_BASE=${BASE}（可选 A/B/C/D/E/F/G/H）"; exit 1
    fi
    echo "自定义风格「${STYLE_NAME}」：以 ${BASE} 为渲染底子，请按用户要求在工程里改配色/字体/动效"
    ;;
  *) echo "未知风格：$STYLE（可选 A/B/C/D/E/F/G/H/I）"; exit 1 ;;
esac
[[ "$STYLE" == "I" ]] || SRC="$(style_src "$STYLE")"

DEST="$SHORT/$TOPIC"

if [[ -d "$DEST" ]]; then
  echo "目录已存在：$DEST"
  read -r -p "覆盖同名子目录？(y/N) " ans
  [[ "$ans" == "y" ]] || exit 1
fi

mkdir -p "$DEST/素材-官网截图-HD" "$DEST/素材-证据图" "$DEST/MG样片-$STYLE_NAME"
cp "$SRC"/*.py "$DEST/MG样片-$STYLE_NAME/"
cp "$SKILL/参考/内容编排方法论.md" "$DEST/"

# mgkit 复制进选题目录，渲染器自包含，不依赖任何外部路径
mkdir -p "$DEST/mgkit"
cp "$SKILL/模板/mgkit/"*.py "$DEST/mgkit/"

cat > "$DEST/选题资料.md" <<EOF
# $TOPIC · 选题资料

> 风格：${STYLE_NAME}（${STYLE}）
> 状态：待补充

## 一、核心结论

（用一句话说清这条视频要让观众记住什么）

## 二、事实与证据

| 事实 | 证据图 | 来源链接 | 截图时间 |
|---|---|---|---|
|  |  |  |  |

## 三、口径边界

- 哪些是官方原话
- 哪些是推断
- 哪些**不能**说（避免夸大）

## 四、口播稿

（静音发布可不写；要配音时先写口播稿再对版式）

EOF

echo ""
echo "已创建：$DEST"
echo "  MG样片-$STYLE_NAME/  ← 渲染工程"
echo "  素材-证据图/        ← 放这里"
echo "  素材-官网截图-HD/   ← 2x 高清原图放这里"
echo ""
echo "下一步："
echo "  1. 先空跑一次，让工具把这条风格需要的素材清单报出来："
echo "     cd '$DEST/MG样片-$STYLE_NAME' && python3 *.py --preview"
echo "     （缺的素材会画占位卡，渲染完打印「缺失素材」清单）"
echo "  2. 用 2x 像素密度截取官网/新闻图，放进 素材-官网截图-HD/"
echo "     （自己截也行，不非得用工具）"
echo "  3. cd '$DEST' 后裁成证据图（见 '$SKILL/模板/工具-切证据图.py' 的 SPECS 写法）"
echo "  4. 重跑第 1 步，直到占位卡全部换成真图"
