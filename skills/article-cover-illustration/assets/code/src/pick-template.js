#!/usr/bin/env node
/**
 * pick-template.js · 按文章类型自动推荐封面 + 配图模板清单
 *
 * 用法：
 *   node pick-template.js <type>                       直接按 type 推荐
 *   node pick-template.js --article <md 文件>           自动读 frontmatter 的 type: 字段
 *
 * type 取值：
 *   review | 横评      → 5-6 张配图（横评清单 + 对比 + 总结）
 *   tutorial | 教程   → 3-5 张配图（流水线 + 决策树）
 *   story | 故事       → 2-3 张配图（卡片 + 总结）
 *   decision | 决策   → 3-4 张配图（决策树 + 对比矩阵）
 *   comparison | 对比 → 1-2 张配图（对比矩阵）
 *
 * 输出：纯文本推荐清单，可直接复制到发布包 README。
 */

const fs = require('fs');
const path = require('path');

const TYPES = {
  review:     { label: '横评',      figCount: '4-6 张', cover: 'cover-template', figs: ['fig-template-1-card-row', 'fig-template-2-matrix', 'fig-template-5-summary'] },
  tutorial:   { label: '教程',      figCount: '3-5 张', cover: 'cover-template', figs: ['fig-template-4-pipeline', 'fig-template-3-decision-tree', 'fig-template-5-summary'] },
  story:      { label: '故事',      figCount: '2-3 张', cover: 'cover-template', figs: ['fig-template-1-card-row', 'fig-template-5-summary'] },
  decision:   { label: '决策',      figCount: '3-4 张', cover: 'cover-template', figs: ['fig-template-3-decision-tree', 'fig-template-2-matrix'] },
  comparison: { label: '对比',      figCount: '1-2 张', cover: 'cover-template', figs: ['fig-template-2-matrix'] },
};

// 别名映射
const ALIASES = {
  '横评': 'review', 'review': 'review',
  '教程': 'tutorial', 'tutorial': 'tutorial', '入门': 'tutorial',
  '故事': 'story', 'story': 'story', '经验': 'story',
  '决策': 'decision', 'decision': 'decision', '选型': 'decision',
  '对比': 'comparison', 'comparison': 'comparison',
};

function detectTypeFromArticle(articlePath) {
  if (!fs.existsSync(articlePath)) {
    console.error(`❌ 文章文件不存在: ${articlePath}`);
    process.exit(1);
  }
  const content = fs.readFileSync(articlePath, 'utf8');
  // 解析 YAML frontmatter
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) {
    console.error(`❌ 文章无 frontmatter: ${articlePath}`);
    console.error(`   需要在文章开头加 --- ... --- 块，示例:`);
    console.error(`   ---`);
    console.error(`   type: review`);
    console.error(`   ---`);
    process.exit(1);
  }
  const fm = match[1];
  const typeMatch = fm.match(/^type:\s*['"]?([^'"\s]+)['"]?/m);
  if (!typeMatch) {
    console.error(`❌ frontmatter 没有 type 字段: ${articlePath}`);
    console.error(`   示例: type: review`);
    process.exit(1);
  }
  return typeMatch[1];
}

function printRecommendation(type) {
  const normType = ALIASES[type] || type;
  if (!TYPES[normType]) {
    console.error(`❌ 未知 type: ${type}`);
    console.error(`   支持的 type: ${Object.keys(TYPES).join(' / ')}`);
    console.error(`   别名: ${Object.keys(ALIASES).filter(k => k !== normType).join(' / ')}`);
    process.exit(1);
  }

  const info = TYPES[normType];
  console.log(`✓ 检测到 type: ${normType} (${info.label})\n`);
  console.log('推荐产物清单：');
  console.log(`  封面   cover-v1.html                   ← 复用 cover-template.html（${normType === 'review' ? '大数字视觉锤' : normType === 'tutorial' ? '动词符号视觉锤' : normType === 'story' ? '短主标视觉锤' : '大问号视觉锤'}）`);
  info.figs.forEach((fig, i) => {
    const templateNum = fig.match(/(\d+)/)?.[1] || '?';
    const templateNames = {
      1: 'N 卡片横排',
      2: '对比矩阵',
      3: '决策树',
      4: '流水线',
      5: '总结大数字',
    };
    console.log(`  配图${i + 1}  fig-0${i + 1}-section?-${info.label}.html    ← ${fig}.html（${templateNames[templateNum]}）`);
  });
  console.log('');
  console.log(`配图数量建议：${info.figCount}`);
  console.log('');
  console.log('下一步：');
  console.log('  1. cp code/templates/cover-template.html <你的-task>/imgs/cover-v1.html');
  console.log('  2. 按上面模板名复制配图模板，改 5 区内容');
  console.log('  3. cd assets && node code/src/render-cover.js <你的-task>/imgs/cover-v1.html');
}

// 解析 CLI 参数
const args = process.argv.slice(2);
if (args.length === 0) {
  console.log('用法：');
  console.log('  node pick-template.js <type>');
  console.log('  node pick-template.js --article <md 文件>');
  console.log('');
  console.log('支持的 type:');
  for (const [key, info] of Object.entries(TYPES)) {
    console.log(`  ${key.padEnd(12)} ${info.label.padEnd(8)} ${info.figCount}`);
  }
  process.exit(0);
}

let type;
if (args[0] === '--article') {
  type = detectTypeFromArticle(args[1]);
} else {
  type = args[0];
}

printRecommendation(type);