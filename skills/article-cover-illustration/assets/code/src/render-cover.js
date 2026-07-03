// 通用 HTML → PNG 渲染器（HyperFrames composition 风格）
// 用法（在仓库根 公众号/ 目录内）：
//   node src/render-cover.js <path-to-html>
//   - 相对路径：相对"公众号/"根目录，例如：
//       node src/render-cover.js task/netflix-headroom-save-token/20260622-netflix-headroom-save-token.html
//   - 也支持绝对路径
// 产物：同名 .png，与 .html 同目录
//
// 自动读 .cover / .canvas 上的 data-width / data-height，2× 输出。

const path = require('path');
const url = require('url');

// 优先走标准 node_modules 解析（项目根或全局），找不到再走 npx 缓存兜底
let puppeteer;
try {
  puppeteer = require('puppeteer-core');
} catch (_) {
  // 兜底：扫 npx 缓存目录找 puppeteer-core
  const fs = require('fs');
  const npxCache = path.join(process.env.HOME || '/Users/wanfeng', '.npm/_npx');
  if (fs.existsSync(npxCache)) {
    for (const sub of fs.readdirSync(npxCache)) {
      const candidate = path.join(npxCache, sub, 'node_modules', 'puppeteer-core');
      if (fs.existsSync(candidate)) {
        puppeteer = require(candidate);
        break;
      }
    }
  }
  if (!puppeteer) {
    console.error('找不到 puppeteer-core，请先跑：');
    console.error('  cd /path/to/code && npm install puppeteer-core');
    console.error('  或：npm install -g puppeteer-core');
    process.exit(1);
  }
}

// 根目录：code/src/ 上两级 → 公众号/
const ROOT_DIR = path.resolve(__dirname, '../..');

(async () => {
  const arg = process.argv[2];
  if (!arg) {
    console.error('用法: node src/render-cover.js <html 相对或绝对路径>');
    process.exit(1);
  }
  const htmlPath = path.isAbsolute(arg)
    ? arg
    : path.join(ROOT_DIR, arg);
  const outPath = htmlPath.replace(/\.html$/, '.png');

  // 直接复用 HyperFrames 通过 `hyperframes browser path` 拿到的浏览器
  const { execSync } = require('child_process');
  let executablePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  try {
    const out = execSync('npx -y --no-install hyperframes browser path', {
      encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']
    }).trim();
    if (out) executablePath = out;
  } catch {}

  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath,
    args: ['--no-sandbox', '--font-render-hinting=none'],
  });
  const page = await browser.newPage();
  // 先粗略导航，再读 HTML 里 .cover / .canvas 的 data-width / data-height
  await page.goto(url.pathToFileURL(htmlPath).href, { waitUntil: 'networkidle0' });
  const dims = await page.evaluate(() => {
    const el = document.querySelector('.cover, .canvas');
    if (!el) return null;
    const w = parseInt(el.getAttribute('data-width') || el.offsetWidth, 10);
    const h = parseInt(el.getAttribute('data-height') || el.offsetHeight, 10);
    return { w, h };
  });
  if (!dims) throw new Error('找不到 .cover 或 .canvas 元素');
  await page.setViewport({ width: dims.w, height: dims.h, deviceScaleFactor: 2 });
  // 视口变化后重新载入，确保布局按新尺寸排好
  await page.goto(url.pathToFileURL(htmlPath).href, { waitUntil: 'networkidle0' });
  const el = await page.$('.cover, .canvas');
  await el.screenshot({ path: outPath, omitBackground: false });
  await browser.close();
  console.log('OK ->', outPath, `(${dims.w}x${dims.h} @2x)`);
})().catch(e => { console.error(e); process.exit(1); });
