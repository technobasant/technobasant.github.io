#!/usr/bin/env node
/**
 * First-viewport screenshot pack for visual e2e.
 *
 *   NODE_PATH=$HOME/node_modules node scripts/e2e-screenshots.mjs [baseUrl]
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { BREAKPOINT_PASSES, isPhone, routesForPass } from "./e2e-config.mjs";

const BASE = process.argv[2] || "http://127.0.0.1:4000";
const OUT = "/tmp/technobasant-e2e-shots";

const PASSES = BREAKPOINT_PASSES;

function notSliced(box, vh, pad = 2) {
  if (!box) return true;
  const top = box.y;
  const bottom = box.y + box.height;
  return bottom <= pad || top >= vh - pad || (top >= -pad && bottom <= vh + pad);
}

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ channel: "chrome" });
const log = [];
const failures = [];

try {
  for (const vp of PASSES) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
      colorScheme: vp.colorScheme,
      hasTouch: isPhone(vp),
    });
    const page = await context.newPage();

    for (const route of routesForPass(vp)) {
      await page.goto(`${BASE}${route.path}`, { waitUntil: "networkidle" });
      await page.evaluate((theme) => {
        document.documentElement.dataset.theme = theme;
        document.documentElement.style.colorScheme = theme;
        try { localStorage.setItem("theme", theme); } catch {}
      }, vp.colorScheme);
      await page.waitForTimeout(180);

      const file = `${route.key}--${vp.name}.png`;
      await page.screenshot({ path: join(OUT, file), fullPage: false });

      const audit = await page.evaluate((vh) => {
        const box = (sel) => {
          const el = document.querySelector(sel);
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return { y: r.y, height: r.height, bottom: r.bottom };
        };
        const h1 = document.querySelector("main h1");
        const lede = document.querySelector("main .lede");
        const h1r = h1?.getBoundingClientRect();
        const leder = lede?.getBoundingClientRect();
        return {
          h1In: h1r ? h1r.top >= -1 && h1r.bottom <= vh + 1 : false,
          ledeIn: leder ? leder.bottom <= vh + 1 : !lede,
          overflowX: document.documentElement.scrollWidth - window.innerWidth,
          photo: Boolean(document.querySelector(".mark__photo")),
          outcomes: box(".portfolio-proof"),
          path: box(".home-path"),
          principles: box(".principle-list"),
          engagements: box(".engagement-grid"),
        };
      }, vp.height);

      const prefix = `${vp.name} ${route.path}`;
      const notes = [];
      if (audit.photo) notes.push("header still has profile photo");
      if (audit.overflowX > 1) notes.push(`horizontal overflow ${Math.round(audit.overflowX)}px`);
      if (!audit.h1In) notes.push("H1 not fully in first viewport");
      if (!audit.ledeIn) notes.push("lede clips first viewport");
      if (route.key === "home" && vp.width >= 864) {
        if (!notSliced(audit.outcomes, vp.height)) notes.push("outcomes sliced");
        if (!notSliced(audit.path, vp.height)) notes.push("operating path sliced");
      }
      if (route.key === "about" && vp.width >= 864 && !notSliced(audit.principles, vp.height)) {
        notes.push("principles sliced");
      }
      if (route.key === "hire" && vp.width >= 864 && !notSliced(audit.engagements, vp.height)) {
        notes.push("engagements sliced");
      }

      if (route.key === "about" && vp.name === "desktop-1440-dark") {
        const list = page.locator(".principle-list");
        if (await list.count()) {
          await list.scrollIntoViewIfNeeded();
          await page.waitForTimeout(120);
          await page.screenshot({ path: join(OUT, "about--desktop-dark--principles.png"), fullPage: false });
          await page.evaluate(() => window.scrollTo(0, 0));
        }
      }
      if (route.key === "home" && vp.name === "desktop-1440-dark") {
        const outcomes = page.locator(".portfolio-proof");
        if (await outcomes.count()) {
          await outcomes.scrollIntoViewIfNeeded();
          await page.waitForTimeout(120);
          await page.screenshot({ path: join(OUT, "home--desktop-dark--outcomes.png"), fullPage: false });
          await page.evaluate(() => window.scrollTo(0, 0));
        }
      }

      const line = `${prefix}  ${file}  ${notes.length ? notes.join("; ") : "ok"}`;
      log.push(line);
      if (notes.length) failures.push(line);
    }

    await context.close();
  }
} finally {
  await browser.close();
}

writeFileSync(join(OUT, "report.txt"), log.join("\n") + `\n\n${failures.length} failures\n`);
console.log(log.join("\n"));
console.log(`\nscreenshots → ${OUT}`);
if (failures.length) {
  console.error(`\n${failures.length} screenshot-audit failures`);
  process.exit(1);
}
console.log("screenshot e2e passed");
