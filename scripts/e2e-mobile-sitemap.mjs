#!/usr/bin/env node
/**
 * Sitemap-wide mobile layout contract.
 *
 *   NODE_PATH=$HOME/node_modules node scripts/e2e-mobile-sitemap.mjs [baseUrl]
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BASE = process.argv[2] || "http://127.0.0.1:4000";
const OUT = "/tmp/technobasant-mobile-sitemap";
const PASSES = [
  { name: "phone-320", width: 320, height: 720 },
  { name: "phone-390", width: 390, height: 844 },
];

mkdirSync(OUT, { recursive: true });
const sitemap = await fetch(`${BASE}/sitemap.xml`).then((response) => {
  if (!response.ok) throw new Error(`sitemap returned ${response.status}`);
  return response.text();
});
const paths = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)]
  .map(([, url]) => new URL(url).pathname)
  .filter((path, index, all) => all.indexOf(path) === index);

const browser = await chromium.launch({ channel: "chrome" });
const failures = [];
const log = [];

try {
  for (const pass of PASSES) {
    const context = await browser.newContext({
      viewport: { width: pass.width, height: pass.height },
      colorScheme: "light",
      hasTouch: true,
      isMobile: true,
    });
    const page = await context.newPage();

    for (const path of paths) {
      const response = await page.goto(`${BASE}${path}`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(80);
      const isHtml = path.endsWith("/") || path.endsWith(".html");
      const findings = isHtml ? await page.evaluate(() => {
        const findings = [];
        const doc = document.documentElement;
        const h1 = document.querySelector("main h1");
        if (doc.scrollWidth - innerWidth > 1) {
          findings.push(`horizontal overflow ${doc.scrollWidth - innerWidth}px`);
        }
        if (!document.querySelector("main")) findings.push("main landmark missing");
        if (h1 && parseFloat(getComputedStyle(h1).fontSize) < 26) {
          findings.push(`H1 too small (${getComputedStyle(h1).fontSize})`);
        }
        const broken = [...document.images].filter((image) => image.complete && image.naturalWidth === 0);
        if (broken.length) findings.push(`${broken.length} broken image(s)`);
        const escaped = [...document.querySelectorAll(
          ".tutorial-header, .series-nav, .author-card, .writing-subscribe, .resume-proof__item, .related .post-card",
        )].filter((element) => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return parseFloat(style.borderLeftWidth) > 0 && rect.width > 0 &&
            (rect.left < 15 || rect.right > innerWidth - 15);
        });
        if (escaped.length) findings.push(`${escaped.length} bordered surface(s) miss 16px gutter`);
        return findings;
      }) : [];

      const prefix = `${pass.name} ${path}`;
      const line = `${prefix}: ${response?.ok() && !findings.length ? "ok" : findings.join("; ") || `HTTP ${response?.status()}`}`;
      log.push(line);
      if (!response?.ok() || findings.length) {
        failures.push(line);
        await page.screenshot({
          path: join(OUT, `${pass.name}-${path.replaceAll("/", "-") || "home"}.png`),
          fullPage: false,
        });
      }
    }
    await context.close();
  }
} finally {
  await browser.close();
}

const report = `${log.join("\n")}\n\n${paths.length} routes × ${PASSES.length} mobile widths; ${failures.length} failures\n`;
writeFileSync(join(OUT, "report.txt"), report);
console.log(report);
if (failures.length) process.exit(1);
console.log("sitemap mobile audit passed");
