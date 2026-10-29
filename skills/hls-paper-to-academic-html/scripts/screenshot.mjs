import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

function usage() {
  return [
    "Usage: node scripts/screenshot.mjs <deck.html> <output-dir> [--device-scale-factor 1]",
    "Captures every slide at 1080x1440 and writes output/render-manifest.json.",
  ].join("\n");
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--help") || args.length === 0) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  if (args.length < 2) throw new Error(usage());

  const htmlPath = path.resolve(args[0]);
  const outputDir = path.resolve(args[1]);
  const scaleIndex = args.indexOf("--device-scale-factor");
  const deviceScaleFactor = scaleIndex >= 0 ? Number(args[scaleIndex + 1]) : 1;
  if (!Number.isFinite(deviceScaleFactor) || deviceScaleFactor <= 0) {
    throw new Error("device-scale-factor must be a positive number");
  }
  await fs.access(htmlPath);
  const slidesDir = path.join(outputDir, "slides");
  await fs.mkdir(slidesDir, { recursive: true });

  const { launchBrowser } = await import("./browser-runtime.mjs");
  const browser = await launchBrowser();
  const page = await browser.newPage({
    viewport: { width: 1080, height: 1440 },
    deviceScaleFactor,
  });
  const files = [];
  try {
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.waitForFunction(() => window.__HLS_DECK_READY__ === true);
    await page.evaluate(async () => {
      if (document.fonts?.ready) await document.fonts.ready;
      await Promise.all([...document.images].map(image => image.decode?.().catch(() => undefined)));
    });
    const broken = await page.evaluate(() => [...document.images]
      .filter(image => !image.complete || image.naturalWidth === 0)
      .map(image => image.alt || image.src));
    if (broken.length) throw new Error(`Broken images: ${broken.join(", ")}`);

    const slideCount = await page.locator(".slide").count();
    for (let index = 0; index < slideCount; index += 1) {
      const number = String(index + 1).padStart(2, "0");
      await page.evaluate(hash => { location.hash = hash; }, `#slide-${number}`);
      await page.waitForTimeout(30);
      const fileName = `${number}.png`;
      const filePath = path.join(slidesDir, fileName);
      await page.screenshot({ path: filePath, type: "png", animations: "disabled" });
      files.push({ slide_id: `S${number}`, file: `slides/${fileName}`, width: 1080, height: 1440 });
    }

    const manifest = {
      generated_at: new Date().toISOString(),
      html: htmlPath,
      viewport: { width: 1080, height: 1440, device_scale_factor: deviceScaleFactor },
      slide_count: files.length,
      files,
    };
    const manifestPath = path.join(outputDir, "render-manifest.json");
    await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
    process.stdout.write(`${JSON.stringify(manifest, null, 2)}\n`);
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});
