/**
 * 用 2x 像素密度重截官网高清截图（可选工具，自己手动截也行）。
 *
 * 为什么要 2x：原截图是 1x（1396 宽），放进 1080 宽的视频里还要缩到 0.65x，
 * 等于二次降采样，文字必然糊。用 deviceScaleFactor=2 重截，宽度变成 2792，
 * 同样的裁切区域放进视频是 1.3x 放大，字口清晰。
 *
 * 用法：
 *   cd <选题目录>
 *   MG_SITE_BASE=https://你的域名 node "<Skill>/模板/工具-重截高清图.mjs" [输出目录]
 *
 *   默认输出到当前目录的 素材-官网截图-HD/。文件名要和下面 PAGES 里写的对上，
 *   因为渲染器是按名字取图的。换选题时只改 PAGES 和 MG_SITE_BASE，不用动其他代码。
 *   没装 Playwright 会报错：npm i -D playwright && npx playwright install chromium
 */
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const OUT = process.argv[2] || path.resolve('素材-官网截图-HD');
const BASE = process.env.MG_SITE_BASE;
if (!BASE) {
  console.error('✗ 先告诉我截哪个站：MG_SITE_BASE=https://你的域名 node 本脚本');
  console.error('  （也可以直接在下面 PAGES 里写完整 URL，就不需要这个环境变量）');
  process.exit(1);
}

// 示例配置：每个选题改成自己的页面。file 名字不要改（渲染器靠它对号），url 随便换。
const PAGES = [
  { file: '01-官网首页-新版公告.jpg', url: `${BASE}/`, full: true },
  { file: '02-试用入口与套餐对比.jpg', url: `${BASE}/pricing`, full: true },
  { file: '03-快速开始-工作区与首次同步.jpg', url: `${BASE}/docs/quickstart`, full: true },
  { file: '04-产品新版-能力与接口.jpg', url: `${BASE}/docs/features`, full: true },
  { file: '05-版本定价-能力与试用规则.jpg', url: `${BASE}/docs/pricing`, full: true },
  { file: '07-版本能力-离线同步说明.jpg', url: `${BASE}/docs/sync`, full: true },
];

await mkdir(OUT, { recursive: true });

// 默认用 Playwright 自带的 chromium；想复用本机已装的浏览器，用 CHROME_PATH 指定可执行文件
const CHROME = process.env.CHROME_PATH;

const browser = await chromium.launch(CHROME && existsSync(CHROME) ? { executablePath: CHROME } : {});
const ctx = await browser.newContext({
  viewport: { width: 1396, height: 900 },
  deviceScaleFactor: 2,          // 2x 像素密度 → 输出 2792 宽
  locale: 'zh-CN',
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    + '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
});
const page = await ctx.newPage();

for (const p of PAGES) {
  console.log(`→ ${p.url}`);
  await page.goto(p.url, { waitUntil: 'networkidle', timeout: 60000 });
  // 等字体和动画稳定
  await page.waitForTimeout(1800);
  // 触发懒加载：滚动到底再回顶
  await page.evaluate(async () => {
    await new Promise((res) => {
      let y = 0;
      const step = () => {
        y += 600;
        window.scrollTo(0, y);
        if (y < document.body.scrollHeight + 1200) setTimeout(step, 60);
        else { window.scrollTo(0, 0); setTimeout(res, 400); }
      };
      step();
    });
  });
  await page.waitForTimeout(1200);
  const target = path.join(OUT, p.file);
  await page.screenshot({ path: target, fullPage: p.full, type: 'jpeg', quality: 92 });
  console.log(`  ✓ ${p.file}`);
}

await browser.close();
console.log('完成 →', OUT);
