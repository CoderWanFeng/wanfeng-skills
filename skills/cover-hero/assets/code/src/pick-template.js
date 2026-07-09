#!/usr/bin/env node
/**
 * pick-template.js · 多平台模板选择器（v4 · 2026 增强版）
 *
 * 用法：
 *   1. 预设平台
 *      node pick-template.js --platform wechat --type cover --output <html>
 *
 *   2. 自定义尺寸（NEW · v4）
 *      node pick-template.js --width 1440 --height 600 --label landing --type cover --output <html>
 *      node pick-template.js --ratio "21:9" --base-width 1920 --label wide-hero --type cover --output <html>
 *
 *   3. 多平台一键（NEW · v4）
 *      node pick-template.js --platform wechat,xhs,douyin --type cover --output imgs/
 *
 *   4. 自动读 MD frontmatter（NEW · v4 · 恢复 v2）
 *      node pick-template.js --article task/<slug>/<slug>.md
 *
 *   5. 交互模式（NEW · v4）
 *      node pick-template.js --interactive   # 逐步问答
 *      node pick-template.js -i
 *
 * 参数：
 *   --platform    : wechat | xhs | douyin | ... | custom | 逗号分隔多平台
 *   --type        : cover | figure | frame
 *   --style       : default | compact | bold
 *   --output      : 单 HTML 路径 或 目录（多平台时必为目录）
 *   --width N     : 自定义宽度（NEW）
 *   --height N    : 自定义高度（NEW）
 *   --ratio W:H   : 自定义比例（NEW）
 *   --base-width N   : 给比例时作为基准宽度
 *   --base-height N  : 给比例时作为基准高度
 *   --label X     : 自定义平台标签（输出命名用，NEW）
 *   --article MD  : 自动读 MD frontmatter（NEW）
 *   --interactive : 交互问答模式（NEW）
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// ============= 平台规格 =============

const PLATFORMS = {
  'wechat':        { label: '公众号',      mode: 'standard',       width: 900,  height: 383,  ratio: '2.35:1' },
  'xhs':           { label: '小红书笔记',  mode: 'high-contrast',  width: 1080, height: 1440, ratio: '3:4'  },
  'xhs-story':     { label: '小红书故事',  mode: 'high-contrast',  width: 1080, height: 1920, ratio: '9:16' },
  'douyin':        { label: '抖音视频封面', mode: 'theatrical',    width: 1080, height: 1920, ratio: '9:16' },
  'douyin-wide':   { label: '抖音横屏帧',  mode: 'theatrical',     width: 1280, height: 720,  ratio: '16:9' },
  'zhihu':         { label: '知乎头图',    mode: 'standard',       width: 1200, height: 675,  ratio: '16:9' },
  'zhihu-fig':     { label: '知乎配图',    mode: 'standard',       width: 1200, height: 900,  ratio: '4:3'  },
  'bilibili':      { label: 'B 站封面',    mode: 'standard',       width: 1146, height: 717,  ratio: '16:10'},
  'weibo':         { label: '微博头条',    mode: 'standard',       width: 1280, height: 1024, ratio: '5:4'  },
  'weibo-fig':     { label: '微博配图',    mode: 'standard',       width: 1200, height: 675,  ratio: '16:9' },
  'og':            { label: 'OG Card',     mode: 'standard',       width: 1200, height: 630,  ratio: '1.91:1'},
  'twitter':       { label: 'Twitter Card', mode: 'standard',      width: 1200, height: 600,  ratio: '2:1'  },
  'custom':        { label: '自定义',      mode: 'standard',       width: null, height: null, ratio: null  },
};

// 平台别名（容错）
const ALIASES = {
  'wechat': 'wechat', 'wx': 'wechat', '公众号': 'wechat', 'gzh': 'wechat',
  'xhs': 'xhs', 'rednote': 'xhs', '小红书': 'xhs', '小红书笔记': 'xhs',
  'xhs-story': 'xhs-story', 'rednote-story': 'xhs-story', '小红书故事': 'xhs-story',
  'douyin': 'douyin', 'dy': 'douyin', 'tiktok': 'douyin', '抖音': 'douyin',
  'douyin-wide': 'douyin-wide', 'dy-wide': 'douyin-wide', '抖音横屏': 'douyin-wide',
  'zhihu': 'zhihu', '知乎': 'zhihu', '知乎头图': 'zhihu',
  'zhihu-fig': 'zhihu-fig', '知乎配图': 'zhihu-fig',
  'bilibili': 'bilibili', 'b站': 'bilibili', '哔哩哔哩': 'bilibili', 'b站封面': 'bilibili',
  'weibo': 'weibo', '微博': 'weibo', '微博头条': 'weibo',
  'weibo-fig': 'weibo-fig', '微博配图': 'weibo-fig',
  'og': 'og', 'og-card': 'og', 'OG Card': 'og',
  'twitter': 'twitter', 'twitter-card': 'twitter', 'Twitter Card': 'twitter',
  'custom': 'custom', '自定义': 'custom',
};

// ============= 类型 × 模板映射 =============

const TYPE_TO_TEMPLATE = {
  cover: 'cover-template.html',
  figure: 'fig-template-1-card-row.html',
  frame: 'cover-template.html',
};

// ============= 风格档位覆盖 =============

const STYLE_OVERRIDES = {
  default: '',
  compact: `
.compact-mode .info .title { font-size: 36px !important; }
.compact-mode .cards { gap: 8px !important; }
.compact-mode .card { padding: 10px 12px !important; }
`,
  bold: `
.bold-mode .hammer .big { font-size: 200px !important; }
.bold-mode .info .title { font-size: 52px !important; }
.bold-mode .badge { padding: 8px 16px !important; }
`,
};

// ============= 核心函数 =============

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    platform: null, type: 'cover', style: 'default', output: null,
    width: null, height: null, ratio: null, baseWidth: null, baseHeight: null,
    label: null, article: null, interactive: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--platform' && args[i + 1]) { opts.platform = args[++i]; }
    else if (arg === '--type' && args[i + 1]) { opts.type = args[++i]; }
    else if (arg === '--style' && args[i + 1]) { opts.style = args[++i]; }
    else if (arg === '--output' && args[i + 1]) { opts.output = args[++i]; }
    else if (arg === '--width' && args[i + 1]) { opts.width = parseInt(args[++i], 10); }
    else if (arg === '--height' && args[i + 1]) { opts.height = parseInt(args[++i], 10); }
    else if (arg === '--ratio' && args[i + 1]) { opts.ratio = args[++i]; }
    else if (arg === '--base-width' && args[i + 1]) { opts.baseWidth = parseInt(args[++i], 10); }
    else if (arg === '--base-height' && args[i + 1]) { opts.baseHeight = parseInt(args[++i], 10); }
    else if (arg === '--label' && args[i + 1]) { opts.label = args[++i]; }
    else if (arg === '--article' && args[i + 1]) { opts.article = args[++i]; }
    else if (arg === '--interactive' || arg === '-i') { opts.interactive = true; }
    else if (arg === '--help' || arg === '-h') { printHelp(); process.exit(0); }
  }
  return opts;
}

function printHelp() {
  console.log('用法：');
  console.log('  # 1. 预设平台');
  console.log('  node pick-template.js --platform wechat --type cover --output <html>');
  console.log('');
  console.log('  # 2. 自定义尺寸（NEW · v4）');
  console.log('  node pick-template.js --width 1440 --height 600 --label landing --type cover --output <html>');
  console.log('  node pick-template.js --ratio "21:9" --base-width 1920 --label wide-hero --type cover --output <html>');
  console.log('');
  console.log('  # 3. 多平台一键（NEW · v4）');
  console.log('  node pick-template.js --platform wechat,xhs,douyin --type cover --output imgs/');
  console.log('');
  console.log('  # 4. 自动读 MD frontmatter（NEW · v4）');
  console.log('  node pick-template.js --article task/<slug>/<slug>.md');
  console.log('');
  console.log('  # 5. 交互模式（NEW · v4）');
  console.log('  node pick-template.js -i');
  console.log('');
  console.log('平台 (--platform):');
  for (const [k, v] of Object.entries(PLATFORMS)) {
    console.log(`  ${k.padEnd(15)} ${v.label.padEnd(15)} ${v.ratio ? v.ratio.padEnd(8) : '(custom)'.padEnd(8)} ${v.width || '-'}×${v.height || '-'}`);
  }
  console.log('');
  console.log('产物类型 (--type): cover / figure / frame');
  console.log('风格档位 (--style): default / compact / bold');
}

// ===== 自定义尺寸解析 =====
function resolveDimensions(opts) {
  // 优先级：--width/--height → --ratio + base → PLATFORMS[platform]
  if (opts.width && opts.height) {
    return { width: opts.width, height: opts.height };
  }
  if (opts.ratio) {
    const match = opts.ratio.match(/^(\d+(?:\.\d+)?)\s*[:/]\s*(\d+(?:\.\d+)?)$/);
    if (!match) {
      console.error(`❌ --ratio 格式错误: ${opts.ratio}（应该是 "W:H"，如 "21:9" 或 "16:10"）`);
      process.exit(1);
    }
    const w = parseFloat(match[1]);
    const h = parseFloat(match[2]);
    if (opts.baseWidth) {
      return { width: opts.baseWidth, height: Math.round(opts.baseWidth * h / w) };
    }
    if (opts.baseHeight) {
      return { width: Math.round(opts.baseHeight * w / h), height: opts.baseHeight };
    }
    // 都没指定 → base-width = 1200（默认横向基准）
    return { width: 1200, height: Math.round(1200 * h / w) };
  }
  // 用 platform 的预设
  if (opts.platform && opts.platform !== 'custom') {
    const p = PLATFORMS[opts.platform];
    if (p && p.width && p.height) return { width: p.width, height: p.height };
  }
  console.error('❌ 必须提供 --platform / --width+--height / --ratio 中至少一种');
  printHelp();
  process.exit(1);
}

function resolvePlatformKey(opts) {
  if (!opts.platform) return null;
  return ALIASES[opts.platform] || opts.platform;
}

function buildSpec(opts) {
  const platformKey = resolvePlatformKey(opts);
  const platform = (platformKey && PLATFORMS[platformKey]) || PLATFORMS['custom'];
  const dims = resolveDimensions(opts);
  const mode = platform.mode || 'standard';
  const label = opts.label || platform.label;

  return {
    platformKey,
    platform,
    dims,
    mode,
    label,
    compositionId: `${platformKey || 'custom'}-${opts.type}-v1`,
  };
}

// ===== MD frontmatter 解析（恢复 v2）=====
function parseArticle(articlePath) {
  if (!fs.existsSync(articlePath)) {
    console.error(`❌ 文章不存在: ${articlePath}`);
    process.exit(1);
  }
  const content = fs.readFileSync(articlePath, 'utf8');
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) {
    console.error(`❌ 文章无 frontmatter: ${articlePath}`);
    console.error(`   需要在文章开头加 --- ... --- 块，示例:`);
    console.error(`   ---`);
    console.error(`   type: tutorial`);
    console.error(`   platform: wechat xhs`);
    console.error(`   ---`);
    process.exit(1);
  }
  const fm = fmMatch[1];

  const opts = {};

  // type: 解析第一个 type 字段
  const typeMatch = fm.match(/^type:\s*['"]?([^'"\s|]+)['"]?/m);
  if (typeMatch) opts.type = typeMatch[1];

  // platform: 解析第一个 platform 字段（可能空格 / 逗号 / 数组分隔）
  // 统一在 main() 里再 split 一次
  const platformMatch = fm.match(/^platform:\s*['"]?\[?([^'"\]\n]+)/m);
  if (platformMatch) opts.platform = platformMatch[1].trim().replace(/[\[\]]/g, '');

  // hammer (optional): 视觉锤
  const hammerMatch = fm.match(/^hammer:\s*['"]?([^'"\n]+)['"]?/m);
  if (hammerMatch) opts.hammer = hammerMatch[1].trim();

  // mention (optional): 名人/公司
  const mentionMatch = fm.match(/^mention:\s*['"]?([^'"\n]+)['"]?/m);
  if (mentionMatch) opts.mention = mentionMatch[1].trim();

  // label (optional): 自定义标签
  const labelMatch = fm.match(/^label:\s*['"]?([^'"\n]+)['"]?/m);
  if (labelMatch) opts.label = labelMatch[1].trim();

  return { source: articlePath, ...opts, fromFrontmatter: true };
}

// ===== HTML 注入 =====
function applyAdaptation(html, mode, style) {
  // 读 CSS 文件而非字符串
  // pick-template.js 位置: assets/code/src/pick-template.js
  // CSS 位置: assets/code/adaptations/<mode>.css
  const adaptationsDir = path.resolve(__dirname, '..', 'adaptations');
  const cssFile = `${mode}.css`;
  const cssPath = path.join(adaptationsDir, cssFile);
  let cssContent = '';
  if (fs.existsSync(cssPath)) {
    cssContent = fs.readFileSync(cssPath, 'utf8');
  }
  const styleOverride = STYLE_OVERRIDES[style] || '';

  // 注入到 </head> 之前：用 <style> 包裹适配层（保留原行为，便于用户看 CSS）
  const block = `<style>\n/* Adaptation: ${mode} + Style: ${style} */\n${cssContent}\n${styleOverride}\n</style>`;
  if (html.includes('</head>')) {
    return html.replace('</head>', `${block}\n</head>`);
  }
  return block + '\n' + html;
}

function setDimensions(html, width, height, platformKey, type, label) {
  let updated = html;
  const dataAttrs = `data-width="${width}" data-height="${height}" data-platform="${platformKey || 'custom'}" data-mode="${type}"`;

  // 模板里已经写死了 data-width="900" data-height="383"
  // 1) 删掉模板里的旧 data-width / data-height
  updated = updated.replace(/\s*data-width="\d+"/, '');
  updated = updated.replace(/\s*data-height="\d+"/, '');

  // 2) 在 class="cover" 或 class="canvas" 后面插入新的 data attrs
  if (updated.includes('class="cover"')) {
    updated = updated.replace(
      /(class="cover")/,
      `$1\n           ${dataAttrs}`,
    );
  } else if (updated.includes('class="canvas"')) {
    updated = updated.replace(
      /(class="canvas")/,
      `$1\n           ${dataAttrs}`,
    );
  }

  // 3) 同步更新 CSS 变量 --w 和 --h（自定尺寸 / 平台预设时都需要）
  updated = updated.replace(/(--w:\s*)\d+px/, `$1${width}px`);
  updated = updated.replace(/(--h:\s*)\d+px/, `$1${height}px`);

  return updated;
}

// ===== 交互模式 =====
function prompt(rl, question) {
  return new Promise((resolve) => rl.question(question, (answer) => resolve(answer.trim())));
}

async function interactiveMode() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  console.log('\n=== cover-hero · 交互模式 ===\n');
  console.log('逐步选择（直接回车走默认）：\n');

  const platformInput = await prompt(rl, `平台 (wechat/xhs/douyin/zhihu/.../custom 或逗号分隔多平台，默认 wechat): `);
  const typeInput = await prompt(rl, `产物类型 (cover/figure/frame，默认 cover): `);
  const styleInput = await prompt(rl, `风格档位 (default/compact/bold，默认 default): `);
  const outputInput = await prompt(rl, `输出路径 (HTML 文件或目录): `);

  // 自定义尺寸可选
  const customSize = await prompt(rl, `是否自定义尺寸 (y/N): `);
  let width = null, height = null, ratio = null, label = null;
  if (/^y(es)?$/i.test(customSize)) {
    ratio = await prompt(rl, `  比例 (W:H，如 21:9，留空用 width/height): `) || null;
    if (!ratio) {
      const w = await prompt(rl, `  width (px): `);
      const h = await prompt(rl, `  height (px): `);
      width = w ? parseInt(w, 10) : null;
      height = h ? parseInt(h, 10) : null;
    } else {
      ratio = ratio.trim();
    }
    label = await prompt(rl, `  label (输出命名用，可选): `) || null;
  }

  rl.close();

  const opts = {
    platform: platformInput || 'wechat',
    type: typeInput || 'cover',
    style: styleInput || 'default',
    output: outputInput,
    width, height, ratio, label,
    interactive: false,  // 防止递归
  };

  console.log('');
  generate(opts);
}

// ===== 单平台生成 =====
function generateSingle(opts) {
  const spec = buildSpec(opts);
  const { platformKey, platform, dims, mode, label, compositionId } = spec;

  // 选模板
  const templateName = TYPE_TO_TEMPLATE[opts.type];
  const templatePath = path.resolve(__dirname, '..', 'templates', templateName);
  if (!fs.existsSync(templatePath)) {
    console.error(`❌ 模板不存在: ${templatePath}`);
    process.exit(1);
  }

  let html = fs.readFileSync(templatePath, 'utf8');

  // 应用适配层 + 风格覆盖
  html = applyAdaptation(html, mode, opts.style);

  // 设置尺寸 + data 标签
  html = setDimensions(html, dims.width, dims.height, platformKey, opts.type, label);

  // 输出路径：判断 --output 是文件还是目录
  let outPath;
  const output = opts.output;
  // 判定为"文件"：有 .html/.htm/.png/.svg 后缀 → 文件
  // 判定为"目录"：以 / 结尾 OR 没有文件后缀
  const hasFileExt = /\.(html?|png|svg)$/i.test(output);
  const hasDirSlash = output.endsWith('/') || output.endsWith('\\');
  const isFilePath = hasFileExt && !hasDirSlash;

  if (platformKey === 'custom') {
    const name = opts.label ? `${opts.label}-${opts.type}-v1.html` : `custom-${dims.width}x${dims.height}-${opts.type}-v1.html`;
    outPath = isFilePath ? output : path.join(output, name);
  } else {
    const name = `${platformKey}-${opts.type}-v1.html`;
    outPath = isFilePath ? output : path.join(output, name);
  }

  const outDir = path.dirname(outPath);
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  fs.writeFileSync(outPath, html);

  console.log(`✓ ${outPath}`);
  console.log(`  平台: ${label}${platformKey === 'custom' ? ' (custom)' : ''}`);
  console.log(`  尺寸: ${dims.width}×${dims.height}`);
  console.log(`  适配: ${mode} + ${opts.style}`);
  console.log(`  模板: ${templateName}`);
}

// ===== 多平台批量 =====
function generateMulti(platforms, opts) {
  if (!opts.output || !platforms.length) {
    console.error('❌ 多平台模式必须指定 --output 为目录');
    process.exit(1);
  }
  // 确保是目录
  if (!fs.existsSync(opts.output)) fs.mkdirSync(opts.output, { recursive: true });

  for (const p of platforms) {
    opts.platform = p;
    generateSingle(opts);
  }
}

// ===== 主入口 =====
function generate(opts) {
  // 没指定 platform 但有 --width/--ratio → 自动归类为 custom
  if (!opts.platform && (opts.width || opts.ratio)) {
    opts.platform = 'custom';
  }

  // 检查多平台（逗号分隔）
  if (opts.platform && opts.platform.includes(',')) {
    const platforms = opts.platform.split(',').map(s => s.trim()).filter(Boolean);
    generateMulti(platforms, opts);
    return;
  }

  // 自动确定 type
  if (!opts.type) opts.type = 'cover';

  // 单平台生成
  if (!opts.output) {
    console.error('❌ 必须指定 --output');
    process.exit(1);
  }
  generateSingle(opts);
}

async function main() {
  const opts = parseArgs();

  // 交互模式优先
  if (opts.interactive) {
    return interactiveMode();
  }

  // --article 模式（自动读 frontmatter）
  if (opts.article) {
    const fm = parseArticle(opts.article);
    // 注意：只 copy 非 product-type 字段，避免 frontmatter type 污染 opts.type
    if (fm.platform) opts.platform = fm.platform;
    if (fm.hammer) opts.hammer = fm.hammer;
    if (fm.mention) opts.mention = fm.mention;
    if (fm.label) opts.label = fm.label;
    if (fm.type) opts.contentType = fm.type;  // 内容类型，不影响产品类型
    if (!opts.output) {
      const articlePath = path.resolve(opts.article);
      const taskDir = path.dirname(articlePath);
      opts.output = path.join(taskDir, 'imgs');
      console.log(`[--article] 自动推断输出目录: ${opts.output}`);
    }
    // platform 字段可能空格分隔，统一转成逗号（generateMulti 用）
    if (opts.platform && !opts.platform.includes(',')) {
      opts.platform = opts.platform.split(/\s+/).filter(Boolean).join(',');
    }
  }

  // product type 默认值
  if (!opts.type) opts.type = 'cover';

  // 没传任何参数 → 打印帮助
  if (!opts.platform && !opts.article && !opts.interactive && Object.keys(opts).every(k => opts[k] === null || (Array.isArray(opts[k]) && opts[k].length === 0))) {
    printHelp();
    return;
  }

  generate(opts);
}

main().catch(e => { console.error(e); process.exit(1); });