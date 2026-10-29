import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function readArg(name) {
  const index = process.argv.indexOf(name);
  if (index < 0 || !process.argv[index + 1]) throw new Error(`Missing ${name}`);
  return path.resolve(process.argv[index + 1]);
}

const htmlPath = readArg('--html');
const outputDir = readArg('--output');
const nodeModules = process.env.CODEX_NODE_MODULES || path.join(
  process.env.USERPROFILE || '',
  '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules',
);
const playwrightUrl = pathToFileURL(path.join(nodeModules, 'playwright/index.mjs')).href;
const { chromium } = await import(playwrightUrl);

await fs.access(htmlPath);
await fs.mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ channel: 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1300, height: 1720 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => Promise.all([...document.images].map((img) => img.complete
  ? Promise.resolve()
  : new Promise((resolve, reject) => {
      img.addEventListener('load', resolve, { once: true });
      img.addEventListener('error', () => reject(new Error(`Image failed: ${img.src}`)), { once: true });
    }))));

const slides = page.locator('.page');
const count = await slides.count();
if (count !== 5) throw new Error(`Expected 5 pages, got ${count}`);

for (let index = 0; index < count; index += 1) {
  const file = path.join(outputDir, `${String(index + 1).padStart(2, '0')}.png`);
  await slides.nth(index).screenshot({ path: file });
}

const layoutReport = await page.evaluate(() => [...document.querySelectorAll('.page')].map((slide, index) => {
  const box = slide.getBoundingClientRect();
  const children = [...slide.querySelectorAll('*')].filter((element) => {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== 'none' && rect.width > 0 && rect.height > 0;
  });
  const maxBottom = Math.max(...children.map((element) => element.getBoundingClientRect().bottom - box.top));
  return {
    page: index + 1,
    width: box.width,
    height: box.height,
    scrollWidth: slide.scrollWidth,
    scrollHeight: slide.scrollHeight,
    maxBottom,
    overflow: slide.scrollWidth > slide.clientWidth || slide.scrollHeight > slide.clientHeight || maxBottom > box.height + 0.5,
  };
}));

await fs.writeFile(path.join(outputDir, 'layout-report.json'), JSON.stringify(layoutReport, null, 2), 'utf8');
await browser.close();
console.log(JSON.stringify({ outputDir, count, layoutReport }, null, 2));
