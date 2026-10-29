const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { createCanvas } = require("@napi-rs/canvas");
const sharp = require("sharp");

async function main() {
  const [input, output, pagesDirArg] = process.argv.slice(2);
  if (!input || !output) throw new Error("Usage: node render_contact_sheet.js input.pdf output.png [pages-dir]");
  const pdfjsEntry = require.resolve("pdfjs-dist/legacy/build/pdf.mjs");
  const pdfjs = await import(pathToFileURL(pdfjsEntry).href);
  const data = new Uint8Array(fs.readFileSync(path.resolve(input)));
  const pdf = await pdfjs.getDocument({ data, disableWorker: true }).promise;
  const pagesDir = path.resolve(pagesDirArg || path.join(path.dirname(output), "pages"));
  fs.mkdirSync(pagesDir, { recursive: true });
  const thumbs = [];

  for (let index = 1; index <= pdf.numPages; index += 1) {
    const page = await pdf.getPage(index);
    const viewport = page.getViewport({ scale: 1.6 });
    const canvas = createCanvas(Math.ceil(viewport.width), Math.ceil(viewport.height));
    const context = canvas.getContext("2d");
    await page.render({ canvasContext: context, viewport }).promise;
    const pagePath = path.join(pagesDir, `page-${String(index).padStart(2, "0")}.png`);
    const buffer = canvas.toBuffer("image/png");
    fs.writeFileSync(pagePath, buffer);
    thumbs.push(await sharp(buffer).resize({ width: 460 }).png().toBuffer());
  }

  const columns = 2;
  const gap = 28;
  const labelHeight = 34;
  const metadata = await sharp(thumbs[0]).metadata();
  const cellWidth = metadata.width;
  const cellHeight = metadata.height + labelHeight;
  const rows = Math.ceil(thumbs.length / columns);
  const composites = [];
  for (let index = 0; index < thumbs.length; index += 1) {
    const left = gap + (index % columns) * (cellWidth + gap);
    const top = gap + Math.floor(index / columns) * (cellHeight + gap);
    composites.push({ input: thumbs[index], left, top });
    const label = Buffer.from(
      `<svg width="${cellWidth}" height="${labelHeight}"><text x="${cellWidth / 2}" y="24" text-anchor="middle" font-family="Arial" font-size="18" fill="#24334f">Page ${index + 1}</text></svg>`
    );
    composites.push({ input: label, left, top: top + metadata.height });
  }
  await sharp({
    create: {
      width: columns * cellWidth + (columns + 1) * gap,
      height: rows * cellHeight + (rows + 1) * gap,
      channels: 3,
      background: "#e9edf5",
    },
  }).composite(composites).png().toFile(path.resolve(output));
  console.log(JSON.stringify({ pages: pdf.numPages, output: path.resolve(output), pagesDir }));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
