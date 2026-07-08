#!/usr/bin/env bash
# optimize-images.sh — 压缩 dist 目录里的图片
# Usage: optimize-images.sh <dist_dir>
# 输出: dist-optimized/（不动原 dist）
# 需要: 项目根目录的 node_modules/sharp（如无则跳过）

set -e

DIST_DIR="$1"

if [ -z "$DIST_DIR" ]; then
  echo "Usage: $0 <dist_dir>" >&2
  exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ 目录不存在: $DIST_DIR" >&2
  exit 1
fi

# 找 sharp（从项目根目录或父目录的 node_modules）
PROJECT_ROOT=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 向上找 package.json（最多 5 层）
CHECK_DIR="$(cd "$DIST_DIR" && pwd)"
for i in 1 2 3 4 5; do
  if [ -f "$CHECK_DIR/package.json" ]; then
    PROJECT_ROOT="$CHECK_DIR"
    break
  fi
  CHECK_DIR="$(dirname "$CHECK_DIR")"
done

if [ -z "$PROJECT_ROOT" ] || [ ! -d "$PROJECT_ROOT/node_modules/sharp" ]; then
  echo "⚠️  未找到 sharp，跳过图片优化"
  echo "   提示：在项目里跑 npm install sharp 安装"
  exit 0
fi

# 准备输出目录
OUTPUT_DIR="$(dirname "$DIST_DIR")/$(basename "$DIST_DIR")-optimized"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 复制所有文件（不动原 dist）
cp -R "$DIST_DIR/." "$OUTPUT_DIR/"

# 找图片文件
mapfile -t IMAGE_FILES < <(find "$OUTPUT_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) 2>/dev/null)

if [ ${#IMAGE_FILES[@]} -eq 0 ]; then
  echo "📷 未找到图片文件，跳过"
  exit 0
fi

echo "📷 找到 ${#IMAGE_FILES[@]} 个图片文件，开始优化..."

# 用 node 调用 sharp
cat > /tmp/pwb-optimize.js <<NODEEOF
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const FILES = process.argv.slice(2);

async function optimizeOne(file) {
  const ext = path.extname(file).toLowerCase();
  const before = fs.statSync(file).size;

  try {
    if (ext === '.jpg' || ext === '.jpeg') {
      // JPG → 保持 JPG，但压缩质量到 80
      await sharp(file)
        .jpeg({ quality: 80, mozjpeg: true })
        .toBuffer({ resolveWithObject: true })
        .then(({ data, info }) => {
          fs.writeFileSync(file, data);
          return info;
        });
    } else if (ext === '.png') {
      // PNG → 尝试转 WebP（更小），保留原 PNG 作为 fallback
      const webpFile = file.replace(/\.png$/i, '.webp');
      await sharp(file)
        .webp({ quality: 80 })
        .toFile(webpFile);

      // 同时压缩 PNG
      await sharp(file)
        .png({ quality: 80, compressionLevel: 9 })
        .toBuffer({ resolveWithObject: true })
        .then(({ data }) => {
          fs.writeFileSync(file, data);
        });
    } else if (ext === '.webp') {
      // WebP → 重新压缩
      await sharp(file)
        .webp({ quality: 80 })
        .toBuffer({ resolveWithObject: true })
        .then(({ data }) => {
          fs.writeFileSync(file, data);
        });
    }

    const after = fs.statSync(file).size;
    const ratio = ((1 - after / before) * 100).toFixed(1);
    console.log(\`  \${ratio >= 0 ? '✅' : '⚠️'}  \${path.basename(file)}: \${before} → \${after} bytes (\${ratio}%)\`);
  } catch (err) {
    console.log(\`  ❌ \${path.basename(file)}: \${err.message}\`);
  }
}

async function main() {
  for (const file of FILES) {
    await optimizeOne(file);
  }
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
NODEEOF

cd "$PROJECT_ROOT"
TOTAL_BEFORE=0
TOTAL_AFTER=0

# 用 for 循环逐个处理（数组太长可能爆命令行长度限制）
BATCH_SIZE=20
i=0
BATCH=()
for img in "${IMAGE_FILES[@]}"; do
  BATCH+=("$img")
  i=$((i+1))
  if [ $((i % BATCH_SIZE)) -eq 0 ]; then
    node /tmp/pwb-optimize.js "${BATCH[@]}" 2>&1
    BATCH=()
  fi
done
if [ ${#BATCH[@]} -gt 0 ]; then
  node /tmp/pwb-optimize.js "${BATCH[@]}" 2>&1
fi

# 更新 HTML 里的图片引用（PNG → WebP）
echo ""
echo "🔄 更新 HTML 里的图片引用（PNG → WebP）..."
HTML_FILES=$(find "$OUTPUT_DIR" -type f \( -name "*.html" -o -name "*.md" -o -name "*.vue" \) 2>/dev/null)
for f in $HTML_FILES; do
  # 简单替换：.png → .webp（保留原文件作为 fallback）
  # 但在 HTML 里用 <picture> 标签优先 WebP
  if [[ "$(uname -s)" == "Darwin" ]]; then
    sed -i '' 's/\.png/\.webp/g' "$f"
  else
    sed -i 's/\.png/\.webp/g' "$f"
  fi
done

# 计算总压缩率
TOTAL_AFTER_SIZE=$(du -sk "$OUTPUT_DIR" 2>/dev/null | cut -f1)

echo ""
echo "✅ 图片优化完成"
echo "   输出目录: $OUTPUT_DIR"
echo "   部署时把 deploy.sh 的 --dist 指向这个目录"