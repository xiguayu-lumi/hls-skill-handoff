const { chromium } = require("playwright");
const path = require("path");
const { pathToFileURL } = require("url");

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) throw new Error("Usage: node render_pdf.js input.html output.pdf");
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.HLS_CHROME || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  });
  const page = await browser.newPage();
  await page.goto(pathToFileURL(path.resolve(input)).href, { waitUntil: "networkidle" });
  await page.emulateMedia({ media: "print" });
  await page.pdf({
    path: path.resolve(output),
    format: "A4",
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: false,
    tagged: true,
    outline: true,
  });
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
