/**
 * 2x 重截官网高清截图（下面 PAGES 是 Agnes AI 的示例配置，每个选题改成自己的官网 URL）。
 *
 * 原截图是 1x 像素密度（1396 宽），放进 1080 宽的视频里还要缩到 0.65x，
 * 等于二次降采样，文字必然糊。
 * 这里用 deviceScaleFactor=2 重截，宽度变成 2792，
 * 同样的裁切区域放进视频是 1.3x 放大，字口清晰。
 *
 * 用法：cd <选题目录> && node "<Skill>/模板/工具-重截高清图.mjs" [输出目录]
 *   默认输出到当前目录的 素材-官网截图-HD/；浏览器路径可用 CHROME_PATH 覆盖。
 */
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const OUT = process.argv[2] || path.resolve('素材-官网截图-HD');
const BASE = 'https://agnes-ai.cn';

const PAGES = [
  { file: '01-官网首页-免费API与多模态.jpg', url: `${BASE}/`, full: true },
  { file: '02-免费访问入口与套餐对比.jpg', url: `${BASE}/campaign`, full: true },
  { file: '03-快速开始-注册Key与首次请求.jpg', url: `${BASE}/zh-Hans/docs/quickstart`, full: true },
  { file: '04-Agnes3.0Flash-模型能力与API接口.jpg', url: `${BASE}/zh-Hans/docs/agnes-30-flash`, full: true },
  { file: '05-模型定价-文本模型与试用规则.jpg', url: `${BASE}/zh-Hans/docs/pricing`, full: true },
];

await mkdir(OUT, { recursive: true });

// 用本机已有的 Chrome for Testing，避免再下一份 chromium；不存在则用 Playwright 自带浏览器
const CHROME = process.env.CHROME_PATH || '/Users/wanfeng/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/'
  + 'Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';

const browser = await chromium.launch(existsSync(CHROME) ? { executablePath: CHROME } : {});
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
