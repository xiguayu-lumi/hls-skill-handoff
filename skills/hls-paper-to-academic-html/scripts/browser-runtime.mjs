export async function launchBrowser() {
  const { chromium } = await import("playwright");
  const attempts = [
    { channel: "msedge", headless: true },
    { channel: "chrome", headless: true },
    { headless: true },
  ];
  const errors = [];
  for (const options of attempts) {
    try {
      return await chromium.launch(options);
    } catch (error) {
      errors.push(`${options.channel || "bundled chromium"}: ${error.message}`);
    }
  }
  throw new Error(`No usable Chromium browser found.\n${errors.join("\n")}`);
}
