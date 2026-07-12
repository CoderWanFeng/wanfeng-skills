/**
 * quality-check.js · 渲染后自检（C2 · v4 新增）
 *
 * 检查项：
 *   1. 渲染尺寸 = data-width × 2 × data-height × 2（2× DPI 强制）
 *   2. 主标字数（按平台限制）
 *   3. 文件大小（≤ 2MB for 公众号/抖音 / ≤ 5MB 其他）
 *   4. 安全区（OG/Twitter 中央 1200×600 内）
 *
 * 用法：
 *   const checks = runChecks(htmlPath, pngPath, platform, dims);
 *   for (const c of checks) console.log(c.message);
 */

const fs = require('fs');
const path = require('path');

// 平台字数限制（来自 reference/hard-rules.md）
const TITLE_LIMITS = {
  douyin: 8,
  xhs: 20,
  twitter: 30,
  og: 30,
  default: 14,
};

const FILE_SIZE_LIMITS = {
  wechat: 2 * 1024 * 1024,  // 2MB
  douyin: 2 * 1024 * 1024,  // 2MB
  default: 5 * 1024 * 1024, // 5MB
};

// 提取主标文本（兼容多种选择器）
function extractTitles(html) {
  const titles = [];

  // 1. .title .h 节点（fig-template 配图结构）
  const titleMatch = html.match(/<div\s+class="title">[\s\S]*?<div\s+class="h">([\s\S]*?)<\/div>/);
  if (titleMatch) titles.push(cleanText(titleMatch[1]));

  // 2. .hero .sub 节点（cover-template 封面结构，含"五种创作姿势"等主标文案）
  const subMatch = html.match(/<section\s+class="hero">[\s\S]*?<div\s+class="sub">([\s\S]*?)<\/div>/);
  if (subMatch) titles.push(cleanText(subMatch[1]));

  // 3. .num / .hammer .big 节点（视觉锤大数字）
  const numMatch = html.match(/<div\s+class="num[^"]*">([\s\S]*?)<\/div>/);
  if (numMatch) titles.push(cleanText(numMatch[1]));

  return titles;
}

function cleanText(s) {
  return s.replace(/<[^>]+>/g, '').replace(/<br\s*\/?>/g, '').replace(/\s+/g, '').trim();
}

function checkDimensions(pngPath, dims) {
  // 2× DPI 期望
  const expected = { w: dims.w * 2, h: dims.h * 2 };

  // 从 PNG 文件头读真实尺寸（不需要 sharp，纯二进制解析 IHDR）
  const buf = fs.readFileSync(pngPath);
  if (buf.length < 24) {
    return { name: '尺寸', passed: false, message: `❌ PNG 文件太小，无法读 IHDR` };
  }
  // IHDR 在字节 16-23（width 4 字节 big-endian + height 4 字节）
  const actualW = buf.readUInt32BE(16);
  const actualH = buf.readUInt32BE(20);

  if (actualW === expected.w && actualH === expected.h) {
    return { name: '尺寸', passed: true, message: `✓ 尺寸 ${actualW}×${actualH} = ${dims.w}×${dims.h} × 2× DPI` };
  }
  return {
    name: '尺寸',
    passed: false,
    message: `❌ 尺寸不匹配: PNG=${actualW}×${actualH}，预期=${expected.w}×${expected.h}（${dims.w}×${dims.h} × 2×）`,
  };
}

function checkTitleLength(html, platform) {
  const titles = extractTitles(html);
  if (titles.length === 0) {
    return { name: '主标字数', passed: true, message: `ℹ 未检测到主标（custom 平台）` };
  }
  const limit = TITLE_LIMITS[platform] || TITLE_LIMITS.default;

  const results = [];
  for (const t of titles) {
    const len = t.length;
    const passed = len <= limit;
    results.push({ name: '主标字数', passed, message: passed
      ? `✓ "${t}"（${len} 字 ≤ ${limit} 限制）`
      : `❌ "${t}"（${len} 字 > ${limit} 限制，${platform} 平台）`,
    });
  }
  return results.length === 1 ? results[0] : { name: '主标字数', passed: results.every(r => r.passed), message: results.map(r => r.message).join('\n') };
}

function checkFileSize(pngPath, platform) {
  const stat = fs.statSync(pngPath);
  const limit = FILE_SIZE_LIMITS[platform] || FILE_SIZE_LIMITS.default;
  const mb = (stat.size / 1024 / 1024).toFixed(2);
  const limitMb = (limit / 1024 / 1024).toFixed(0);

  if (stat.size <= limit) {
    return { name: '文件大小', passed: true, message: `✓ ${mb}MB ≤ ${limitMb}MB` };
  }
  return { name: '文件大小', passed: false, message: `❌ ${mb}MB > ${limitMb}MB（${platform} 平台）` };
}

function checkSafeArea(html, platform) {
  // OG / Twitter 平台要求文字在中央 1200×600 安全区内
  if (platform !== 'og' && platform !== 'twitter') {
    return { name: '安全区', passed: true, message: `ℹ ${platform} 平台无安全区限制` };
  }
  // 简单判断：检查 HTML 是否引用 safe-area 类
  if (html.includes('safe-area') || html.includes('safeArea')) {
    return { name: '安全区', passed: true, message: `✓ 检测到 safe-area 标记` };
  }
  return { name: '安全区', passed: false, message: `⚠ ${platform} 平台应在中央 1200×600 加 safe-area 标记（详见 reference/platforms.md）` };
}

function checkCards(html) {
  // 只检查含 .cards 区块的模板（竖版 xhs / douyin）
  const cardsBlock = html.match(/<section\s+class="cards">([\s\S]*?)<\/section>/);
  if (!cardsBlock) {
    return { name: '卡片数', passed: true, message: `ℹ 无 .cards 区块（横版模板）` };
  }
  const count = (cardsBlock[1].match(/class="item(\s+pick)?"/g) || []).length;
  if (count >= 1 && count <= 5) {
    return { name: '卡片数', passed: true, message: `✓ ${count} 张卡片（1-5 合理区间）` };
  }
  if (count === 0) {
    return { name: '卡片数', passed: false, message: `⚠ .cards 区块为空（应有 1-5 张卡片）` };
  }
  return { name: '卡片数', passed: false, message: `⚠ ${count} 张卡片 > 5，竖版易挤（建议 ≤ 5）` };
}

/**
 * 跑所有自检
 * @param {string} htmlPath - 源 HTML 路径
 * @param {string} pngPath - 渲染 PNG 路径
 * @param {string} platform - 平台 key（wechat / xhs / douyin / og / twitter / custom 等）
 * @param {{w: number, h: number}} dims - data-width / data-height
 * @returns {Array<{name: string, passed: boolean, message: string}>}
 */
function runChecks(htmlPath, pngPath, platform, dims) {
  const html = fs.readFileSync(htmlPath, 'utf8');
  const checks = [
    checkDimensions(pngPath, dims),
    checkTitleLength(html, platform),
    checkFileSize(pngPath, platform),
    checkSafeArea(html, platform),
    checkCards(html),
  ];
  return checks;
}

module.exports = { runChecks };

// CLI 入口
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 4) {
    console.error('用法: node quality-check.js <html> <png> <platform> <width> <height>');
    process.exit(1);
  }
  const [htmlPath, pngPath, platform, w, h] = args;
  const checks = runChecks(htmlPath, pngPath, platform, { w: parseInt(w, 10), h: parseInt(h, 10) });
  for (const c of checks) {
    console.log(c.message);
  }
  const failed = checks.filter(c => !c.passed);
  process.exit(failed.length > 0 ? 1 : 0);
}