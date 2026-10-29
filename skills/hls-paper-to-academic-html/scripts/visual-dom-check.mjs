import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

function usage() {
  return [
    "Usage: node scripts/visual-dom-check.mjs <deck.html> [--report report.json]",
    "Checks image/font loading, 1080x1440 slide bounds, overflow, and evidence footer.",
  ].join("\n");
}

async function runSelfTest() {
  const sample = { width: 1080, height: 1440, scrollWidth: 1080, scrollHeight: 1440 };
  if (sample.scrollWidth > sample.width || sample.scrollHeight > sample.height) {
    throw new Error("self-test fixture unexpectedly overflows");
  }
  process.stdout.write("visual-dom-check self-test passed\n");
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--self-test")) {
    await runSelfTest();
    return;
  }
  if (args.includes("--help") || args.length === 0) {
    process.stdout.write(`${usage()}\n`);
    return;
  }

  const htmlPath = path.resolve(args[0]);
  const reportIndex = args.indexOf("--report");
  const reportPath = reportIndex >= 0 ? path.resolve(args[reportIndex + 1]) : null;
  await fs.access(htmlPath);

  const { launchBrowser } = await import("./browser-runtime.mjs");
  const browser = await launchBrowser();
  const page = await browser.newPage({
    viewport: { width: 1080, height: 1440 },
    deviceScaleFactor: 1,
  });
  const issues = [];
  try {
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.waitForFunction(() => window.__HLS_DECK_READY__ === true);
    await page.evaluate(async () => {
      if (document.fonts?.ready) await document.fonts.ready;
      await Promise.all([...document.images].map(image => {
        if (image.complete) return;
        return new Promise((resolve, reject) => {
          image.addEventListener("load", resolve, { once: true });
          image.addEventListener("error", reject, { once: true });
        });
      }));
    });

    const slideCount = await page.locator(".slide").count();
    for (let index = 0; index < slideCount; index += 1) {
      const slideNumber = String(index + 1).padStart(2, "0");
      await page.evaluate(hash => { location.hash = hash; }, `#slide-${slideNumber}`);
      await page.waitForTimeout(20);
      const result = await page.locator(`#slide-${slideNumber}`).evaluate(slide => {
        const rect = slide.getBoundingClientRect();
        const footer = slide.querySelector(".evidence-footer");
        const takeaway = slide.querySelector(".page-takeaway");
        const footerRect = footer?.getBoundingClientRect();
        const takeawayRect = takeaway?.getBoundingClientRect();
        const brokenImages = [...slide.querySelectorAll("img")]
          .filter(image => !image.complete || image.naturalWidth === 0)
          .map(image => image.alt || image.src);
        return {
          id: slide.id,
          width: slide.clientWidth,
          height: slide.clientHeight,
          scrollWidth: slide.scrollWidth,
          scrollHeight: slide.scrollHeight,
          renderedWidth: Math.round(rect.width),
          renderedHeight: Math.round(rect.height),
          footer: Boolean(footer),
          contentFooterOverlap: Boolean(
            footerRect && takeawayRect && takeawayRect.bottom > footerRect.top
          ),
          brokenImages,
        };
      });
      if (result.width !== 1080 || result.height !== 1440) {
        issues.push({ severity: "error", code: "wrong_slide_size", slide: result.id, result });
      }
      if (result.scrollWidth > result.width || result.scrollHeight > result.height) {
        issues.push({ severity: "error", code: "slide_overflow", slide: result.id, result });
      }
      if (!result.footer) {
        issues.push({ severity: "error", code: "missing_evidence_footer", slide: result.id });
      }
      if (result.contentFooterOverlap) {
        issues.push({ severity: "error", code: "content_footer_overlap", slide: result.id });
      }
      for (const image of result.brokenImages) {
        issues.push({ severity: "error", code: "broken_image", slide: result.id, image });
      }
    }

    const report = {
      checked_at: new Date().toISOString(),
      html: htmlPath,
      slide_count: slideCount,
      viewport: { width: 1080, height: 1440, device_scale_factor: 1 },
      issues,
      passed: issues.every(issue => issue.severity !== "error"),
    };
    const text = `${JSON.stringify(report, null, 2)}\n`;
    if (reportPath) {
      await fs.mkdir(path.dirname(reportPath), { recursive: true });
      await fs.writeFile(reportPath, text, "utf8");
    }
    process.stdout.write(text);
    if (!report.passed) process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});
