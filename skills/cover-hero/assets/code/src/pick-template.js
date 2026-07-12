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

// ============= 平台专用模板（v5 新增）=============
// 某些平台（小红书 / 抖音）有专用模板，layout 是竖版（flex column），
// 比通用 cover-template 套适配层效果好（后者会崩布局）。
const PLATFORM_TO_TEMPLATE = {
  'xhs':         'xhs-cover.html',     // 小红书 3:4
  'xhs-story':   'douyin-cover.html',  // 小红书 9:16（沿用抖音竖版布局）
  'douyin':      'douyin-cover.html',  // 抖音 9:16
  'douyin-wide': 'cover-template.html',// 抖音横屏 16:9（用通用横版）
};

function getTemplateName(platformKey, productType) {
  // 平台专用模板优先（v5）
  if (platformKey && PLATFORM_TO_TEMPLATE[platformKey]) {
    return PLATFORM_TO_TEMPLATE[platformKey];
  }
  // 否则用通用模板
  return TYPE_TO_TEMPLATE[productType] || TYPE_TO_TEMPLATE.cover;
}

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
    label: null, article: null, interactive: false, allPlatforms: false,
    kicker: null, hammer: null, sub: null, cards: null,
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
    else if (arg === '--kicker' && args[i + 1]) { opts.kicker = args[++i]; }
    else if (arg === '--hammer' && args[i + 1]) { opts.hammer = args[++i]; }
    else if (arg === '--sub' && args[i + 1]) { opts.sub = args[++i]; }
    else if (arg === '--article' && args[i + 1]) { opts.article = args[++i]; }
    else if (arg === '--interactive' || arg === '-i') { opts.interactive = true; }
    else if (arg === '--all-platforms') { opts.allPlatforms = true; }
    else if (arg === '--help' || arg === '-h') { printHelp(); process.exit(0); }
  }
  return opts;
}

function printHelp() {
  console.log('用法：');
  console.log('  # 1. 预设平台');
  console.log('  node pick-template.js --platform wechat --type cover --output <html>');
  console.log('');
  console.log('  # 2. 自定义尺寸（v4）');
  console.log('  node pick-template.js --width 1440 --height 600 --label landing --type cover --output <html>');
  console.log('  node pick-template.js --ratio "21:9" --base-width 1920 --label wide-hero --type cover --output <html>');
  console.log('');
  console.log('  # 3. 多平台一键（v4）');
  console.log('  node pick-template.js --platform wechat,xhs,douyin --type cover --output imgs/');
  console.log('');
  console.log('  # 4. 自动读 MD frontmatter（v4）');
  console.log('  node pick-template.js --article task/<slug>/<slug>.md');
  console.log('');
  console.log('  # 5. 交互模式（v4）');
  console.log('  node pick-template.js -i');
  console.log('');
  console.log('  # 6. 一键 8 平台（v5.3 新增）');
  console.log('  node pick-template.js --all-platforms --output imgs/');
  console.log('     自动跑：wechat / xhs / douyin / zhihu / bilibili / weibo / og / twitter');
  console.log('     产物：<output>/<platform>/cover-v1.html  按平台分子目录');
  console.log('');
  console.log('  # 7. 输出路径规则（v5.3）');
  console.log('  --output <dir>/        → 目录，按平台分 <dir>/<platform>/cover-v1.html');
  console.log('  --output <dir>/foo.html → 文件路径，原样输出（不分子目录）');
  console.log('');
  console.log('  # 8. 注入内容（v5.4 新增 · 免手改 HTML）');
  console.log('  node pick-template.js --platform xhs \\');
  console.log('    --kicker "6 个 <em>AI Skill</em>" --hammer "6 合一" \\');
  console.log('    --sub \'AI 从<span class="hl">噪声</span>中<br/>长出合影\' --output imgs/');
  console.log('  # 或 frontmatter：kicker / hammer / sub / cards（缩进列表）');
  console.log('  # 或交互模式 -i 会逐步问 kicker / hammer / sub / 卡片');
  console.log('');
  console.log('平台 (--platform):');
  for (const [k, v] of Object.entries(PLATFORMS)) {
    console.log(`  ${k.padEnd(15)} ${v.label.padEnd(15)} ${v.ratio ? v.ratio.padEnd(8) : '(custom)'.padEnd(8)} ${v.width || '-'}×${v.height || '-'}`);
  }
  console.log('');
  console.log('产物类型 (--type): cover / figure / frame');
  console.log('风格档位 (--style): default / compact / bold');
  console.log('内容注入 (v5.4): --kicker / --hammer / --sub，或 frontmatter kicker/hammer/sub/cards');
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

  // kicker (optional): 顶标小字（v5.4）
  const kickerMatch = fm.match(/^kicker:\s*['"]?([^'\n]+?)['"]?\s*$/m);
  if (kickerMatch) opts.kicker = kickerMatch[1].trim();

  // sub (optional): 主副标（v5.4，允许含 <br/> / <span> / <em>）
  const subMatch = fm.match(/^sub:\s*['"]?([^'\n]+?)['"]?\s*$/m);
  if (subMatch) opts.sub = subMatch[1].trim();

  // cards (optional): 卡片数组（v5.4，YAML 缩进列表子集）
  const cards = parseCardsBlock(fm);
  if (cards.length) opts.cards = cards;

  return { source: articlePath, ...opts, fromFrontmatter: true };
}

// ===== cards YAML 子集解析（v5.4）=====
/**
 * 解析 frontmatter 里的 cards 缩进列表，例如：
 *   cards:
 *     - name: aihot-topic
 *       role: 热点选题
 *       step: SKILL 01
 *     - name: cover-hero
 *       role: 封面 + 配图
 *       pick: true
 * 只支持 name / role / step / icon / pick 五个键。
 */
function parseCardsBlock(fm) {
  const lines = fm.split('\n');
  const startIdx = lines.findIndex(l => /^cards:\s*$/.test(l));
  if (startIdx === -1) return [];

  const cards = [];
  let current = null;
  for (let i = startIdx + 1; i < lines.length; i++) {
    const line = lines[i];
    // 遇到顶层新键（无缩进且是 key:）→ cards 区块结束
    if (/^\S/.test(line) && /^[\w-]+:/.test(line)) break;
    if (!line.trim()) continue;

    const itemMatch = line.match(/^\s*-\s*(.*)$/);
    if (itemMatch) {
      // 新卡片开始
      if (current) cards.push(current);
      current = {};
      const inline = itemMatch[1].trim();
      if (inline) applyCardKV(current, inline);
    } else if (current) {
      applyCardKV(current, line.trim());
    }
  }
  if (current) cards.push(current);
  return cards.filter(c => c.name);
}

function applyCardKV(card, kv) {
  const m = kv.match(/^([\w-]+):\s*['"]?(.*?)['"]?$/);
  if (!m) return;
  const key = m[1].trim();
  const val = m[2].trim();
  if (key === 'pick') {
    card.pick = /^(true|yes|1)$/i.test(val);
  } else if (['name', 'role', 'step', 'icon'].includes(key)) {
    card[key] = val;
  }
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

// ===== 内容注入（v5.4 新增 · 打通 内容→HTML）=====

/**
 * 把 opts 里的文案 / 卡片注入到模板 HTML。
 * 支持字段：kicker（顶标）/ hammer（视觉锤大字）/ sub（主副标）/ cards（卡片数组）。
 * 未提供的字段保留模板占位，不动。
 *
 * 注意：kicker / sub / hammer 的值允许含原始 HTML（如 <br/>、<span class="hl">、<em>），
 * 由调用方 / frontmatter 作者负责，injectContent 不转义（视觉锤 hammer 会转义避免属性破坏）。
 */
function injectContent(html, opts) {
  let updated = html;

  // 1. hammer（视觉锤）→ 整段替换 .num（含 data-hammer 属性），根治重复 data-hammer 冲突
  if (opts.hammer) {
    const attrSafe = String(opts.hammer).replace(/["\\]/g, '');
    updated = updated.replace(
      /<div class="num"[^>]*>[\s\S]*?<\/div>/,
      `<div class="num" data-hammer="${attrSafe}">${opts.hammer}</div>`,
    );
  }

  // 2. kicker（顶标小字）→ 替换 .kicker 内容
  if (opts.kicker) {
    updated = updated.replace(
      /(<div class="kicker">)[\s\S]*?(<\/div>)/,
      `$1${opts.kicker}$2`,
    );
  }

  // 3. sub（主副标）→ 替换 .sub 内容（横版模板用 .h，见 4）
  if (opts.sub) {
    updated = updated.replace(
      /(<div class="sub">)[\s\S]*?(<\/div>)/,
      `$1${opts.sub}$2`,
    );
    // 横版 cover-template 用 <div class="h">，同步支持
    updated = updated.replace(
      /(<div class="h">)[\s\S]*?(<\/div>)/,
      `$1${opts.sub}$2`,
    );
  }

  // 4. cards（卡片数组）→ 重写 .cards 区块（保留 <section> 外壳）
  if (Array.isArray(opts.cards) && opts.cards.length) {
    const cardsHtml = opts.cards.map((c, i) => {
      const pick = c.pick ? ' pick' : '';
      const stepNum = String(i + 1).padStart(2, '0');
      const icon = c.icon || (c.pick ? '★' : String(i + 1));
      const step = c.step || `STEP ${stepNum}`;
      const role = c.role || '';
      return `      <div class="item${pick}">\n` +
             `        <div class="ico">${icon}</div>\n` +
             `        <div class="step">${step}</div>\n` +
             `        <div class="name">${c.name || ''}</div>\n` +
             `        <div class="role">${role}</div>\n` +
             `      </div>`;
    }).join('\n');
    updated = updated.replace(
      /(<section class="cards">)[\s\S]*?(<\/section>)/,
      `$1\n${cardsHtml}\n    $2`,
    );
  }

  return updated;
}

// ===== 交互模式 =====
function prompt(rl, question) {
  return new Promise((resolve) => rl.question(question, (answer) => resolve(answer.trim())));
}

// 非 TTY（管道 / heredoc / 测试）时：一次性读完 stdin，按行出队，保证确定性
function makeLineQueue() {
  const data = fs.readFileSync(0, 'utf8');
  const lines = data.split('\n');
  return {
    next() { return lines.length ? lines.shift().trim() : ''; },
  };
}

async function interactiveMode() {
  const isTTY = process.stdin.isTTY;
  let rl = null, queue = null;
  if (isTTY) {
    rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  } else {
    queue = makeLineQueue();
  }
  const ask = async (q) => {
    if (isTTY) return prompt(rl, q);
    const ans = queue.next();
    console.log(q + ans);
    return ans;
  };
  const closeInput = () => { if (rl) rl.close(); };

  console.log('\n=== cover-hero · 交互模式 ===\n');
  console.log('逐步选择（直接回车走默认）：\n');

  const platformInput = await ask(`平台 (wechat/xhs/douyin/zhihu/.../custom 或逗号分隔多平台，默认 wechat): `);
  const typeInput = await ask(`产物类型 (cover/figure/frame，默认 cover): `);
  const styleInput = await ask(`风格档位 (default/compact/bold，默认 default): `);
  const outputInput = await ask(`输出路径 (HTML 文件或目录): `);

  // 内容填写（v5.4）：kicker / hammer / sub / 卡片
  let kicker = null, hammer = null, sub = null, cards = null;
  const wantsContent = await ask(`现在填封面内容 (y/N，默认 N → 用模板占位): `);
  if (/^y(es)?$/i.test(wantsContent)) {
    kicker = await ask(`  kicker（顶标小字，如 6 个 AI Skill，可空）: `) || null;
    hammer = await ask(`  hammer（视觉锤大字，如 6 或 穿越，可空）: `) || null;
    sub = await ask(`  sub（主副标，可含 <br/> 换行 / <span class="hl">高亮</span>，可空）: `) || null;
    const cardsCount = await ask(`  卡片数 (1-5，默认 3，0 = 不改卡片): `);
    const n = cardsCount === '' ? 3 : parseInt(cardsCount, 10);
    if (n > 0) {
      cards = [];
      const cap = Math.min(5, n);
      for (let i = 0; i < cap; i++) {
        console.log(`  ── 卡片 ${i + 1}/${cap} ──`);
        const name = await ask(`    name（留空结束）: `);
        if (!name) break;
        const role = await ask(`    role: `);
        const step = await ask(`    step（如 STEP 01 / SKILL 03，可空）: `) || null;
        const pick = await ask(`    高亮这张? (y/N): `);
        cards.push({ name, role, step, pick: /^y(es)?$/i.test(pick) });
      }
      if (!cards.length) cards = null;
    }
  }

  // 自定义尺寸可选
  const customSize = await ask(`是否自定义尺寸 (y/N): `);
  let width = null, height = null, ratio = null, label = null;
  if (/^y(es)?$/i.test(customSize)) {
    ratio = await ask(`  比例 (W:H，如 21:9，留空用 width/height): `) || null;
    if (!ratio) {
      const w = await ask(`  width (px): `);
      const h = await ask(`  height (px): `);
      width = w ? parseInt(w, 10) : null;
      height = h ? parseInt(h, 10) : null;
    } else {
      ratio = ratio.trim();
    }
    label = await ask(`  label (输出命名用，可选): `) || null;
  }

  closeInput();

  const opts = {
    platform: platformInput || 'wechat',
    type: typeInput || 'cover',
    style: styleInput || 'default',
    output: outputInput,
    kicker, hammer, sub, cards,
    width, height, ratio, label,
    interactive: false,  // 防止递归
  };

  console.log('');
  generate(opts);
}

// ===== 输出路径解析（v5.2 新增 · 自动按平台分目录）=====

/**
 * 决定输出路径
 * @param {string} platformKey - 平台 key（wechat / xhs / douyin / custom 等）
 * @param {object} opts - 命令行参数
 * @returns {string} 完整输出路径
 *
 * 规则：
 * 1. --output 以 .html/.htm 结尾 → 文件路径，原样输出（用户显式指定）
 * 2. --output 是目录（或无后缀）→ 按平台分子目录输出 `<dir>/<platform>/cover-v1.html`
 * 3. custom 平台（无 platformKey）→ 输出 `<dir>/custom-<wxh>-cover-v1.html`（不分目录）
 * 4. fig 类型（如 `fig-01-v1.html`）→ 仍按平台分目录，命名用 fig-NN
 */
function resolveOutputPath(platformKey, opts) {
  const output = opts.output;
  // 判定：--output 是文件路径（带 .html/.htm 后缀）vs 目录路径
  const hasFileExt = /\.(html?|png|svg)$/i.test(output);
  const hasDirSlash = output.endsWith('/') || output.endsWith('\\');
  const isFilePath = hasFileExt && !hasDirSlash;

  // 1. 用户显式指定文件路径 → 原样输出
  if (isFilePath) {
    return output;
  }

  // 2. custom 平台（无 platformKey，custom 是特殊）→ 不分目录
  if (!platformKey || platformKey === 'custom') {
    const name = opts.label
      ? `${opts.label}-${opts.type}-v1.html`
      : `custom-${opts.dims?.width || ''}x${opts.dims?.height || ''}-${opts.type}-v1.html`.replace('x-', '-');
    return path.join(output, name);
  }

  // 3. 平台子目录（v5.2 新增约定）
  // 注意：fig-01-v1.html 这种不是 <platform>- 前缀，也进平台子目录
  const typePrefix = opts.type === 'cover' ? '' : `${opts.type}-`;
  const fileName = `${typePrefix}cover-v1.html`;
  return path.join(output, platformKey, fileName);
}

// ===== 单平台生成 =====
function generateSingle(opts) {
  const spec = buildSpec(opts);
  const { platformKey, platform, dims, mode, label, compositionId } = spec;

  // 选模板：v5 平台专用模板优先（如 xhs → xhs-cover.html）
  const templateName = getTemplateName(platformKey, opts.type);
  const templatePath = path.resolve(__dirname, '..', 'templates', templateName);
  if (!fs.existsSync(templatePath)) {
    console.error(`❌ 模板不存在: ${templatePath}`);
    process.exit(1);
  }

  let html = fs.readFileSync(templatePath, 'utf8');

  // 应用适配层 + 风格覆盖
  html = applyAdaptation(html, mode, opts.style);

  // 注入内容（v5.4：kicker / hammer / sub / cards）
  html = injectContent(html, opts);

  // 设置尺寸 + data 标签
  html = setDimensions(html, dims.width, dims.height, platformKey, opts.type, label);

  // 输出路径：v5.2 自动按平台分目录
  const outPath = resolveOutputPath(platformKey, { ...opts, dims });

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
    // CLI flag 优先级高于 frontmatter：只在 CLI 没显式传时才用 frontmatter 值
    if (fm.platform && !opts.platform) opts.platform = fm.platform;
    if (fm.hammer && !opts.hammer) opts.hammer = fm.hammer;
    if (fm.mention && !opts.mention) opts.mention = fm.mention;
    if (fm.label && !opts.label) opts.label = fm.label;
    if (fm.kicker && !opts.kicker) opts.kicker = fm.kicker;
    if (fm.sub && !opts.sub) opts.sub = fm.sub;
    if (fm.cards && !opts.cards) opts.cards = fm.cards;
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
  if (!opts.platform && !opts.article && !opts.interactive && !opts.allPlatforms && Object.keys(opts).every(k => opts[k] === null || (Array.isArray(opts[k]) && opts[k].length === 0))) {
    printHelp();
    return;
  }

  // --all-platforms 模式（v5.2 新增）：一键 8 平台
  if (opts.allPlatforms) {
    if (!opts.output) {
      console.error('❌ --all-platforms 必须指定 --output 目录');
      console.error('   例: pick-template.js --all-platforms --output imgs/');
      process.exit(1);
    }
    if (opts.platform) {
      console.error('⚠ --all-platforms 会覆盖 --platform，跳过自定义值');
    }
    // 8 个预设平台（排除 custom + size 变体 xhs-story / douyin-wide / weibo-fig）
    // 完整 8 = 公众号 / 小红书 / 抖音 / 知乎 / B站 / 微博 / OG Card / Twitter Card
    const allPlatforms = ['wechat', 'xhs', 'douyin', 'zhihu', 'bilibili', 'weibo', 'og', 'twitter'];
    console.log(`[--all-platforms] 一键生成 ${allPlatforms.length} 平台 → ${opts.output}`);
    generateMulti(allPlatforms, opts);
    return;
  }

  generate(opts);
}

main().catch(e => { console.error(e); process.exit(1); });