#!/usr/bin/env node
/**
 * First-viewport hero contract. Playwright MCP is not in this workspace;
 * this script is the same check: real Chromium, real layout, screenshots.
 *
 *   node scripts/e2e-hero.mjs [baseUrl]
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { BREAKPOINT_PASSES, HERO_ROUTES, isPhone, routesForPass } from "./e2e-config.mjs";

const BASE = process.argv[2] || "http://127.0.0.1:4000";
const OUT = "/tmp/technobasant-hero-e2e";

const VIEWPORTS = BREAKPOINT_PASSES;
const ROUTES = HERO_ROUTES.map((route) => ({ ...route, search: route.key === "writing" }));

function notSliced(box, vh, pad = 2) {
  if (!box) return true;
  const top = box.y;
  const bottom = box.y + box.height;
  const fullyAbove = bottom <= pad;
  const fullyBelow = top >= vh - pad;
  const fullyIn = top >= -pad && bottom <= vh + pad;
  return fullyAbove || fullyBelow || fullyIn;
}

function boxInFrame(box, vw, vh, pad = 1) {
  if (!box) return { ok: false, reason: "missing" };
  const top = box.y;
  const bottom = box.y + box.height;
  const left = box.x;
  const right = box.x + box.width;
  if (top < -pad) return { ok: false, reason: `clips top (${top.toFixed(1)})` };
  if (bottom > vh + pad) return { ok: false, reason: `clips bottom (${bottom.toFixed(1)} > ${vh})` };
  if (left < -pad) return { ok: false, reason: `clips left (${left.toFixed(1)})` };
  if (right > vw + pad) return { ok: false, reason: `clips right (${right.toFixed(1)} > ${vw})` };
  return { ok: true, top, bottom, height: box.height };
}

async function measure(page, selector) {
  const el = page.locator(selector).first();
  if (!(await el.count())) return null;
  return el.boundingBox();
}

async function auditPage(page, route, vp) {
  const findings = [];
  const vw = vp.width;
  const vh = vp.height;

  const h1 = boxInFrame(await measure(page, "main h1"), vw, vh);
  if (!h1.ok) findings.push(`h1 ${h1.reason}`);

  const ledeBox = await measure(page, "main .lede");
  if (ledeBox) {
    const lede = boxInFrame(ledeBox, vw, vh);
    if (!lede.ok) findings.push(`lede ${lede.reason}`);
  }

  const mark = await measure(page, ".mark");
  if (!mark) findings.push("wordmark missing");
  else if (mark.height < 24) {
    findings.push(`wordmark too small (${mark.width.toFixed(0)}×${mark.height.toFixed(0)})`);
  }

  if (route.key === "home") {
    const actions = boxInFrame(await measure(page, ".portfolio-hero .actions"), vw, vh);
    if (!actions.ok) findings.push(`hero actions ${actions.reason}`);
    if (vw >= 864) {
      for (const sel of [".portfolio-proof", ".portfolio-work"]) {
        const block = await measure(page, sel);
        if (block && !notSliced(block, vh)) {
          findings.push(`${sel} sliced at the fold`);
        }
      }
    }
  }

  if (route.key === "about" && vw >= 864) {
    const list = await measure(page, ".principle-list");
    if (list && !notSliced(list, vh)) {
      findings.push("principle grid sliced at the fold");
    }
  }

  if (route.key === "hire" && vw >= 864) {
    const grid = await measure(page, ".engagement-grid");
    if (grid && !notSliced(grid, vh)) {
      findings.push("engagement grid sliced at the fold");
    }
  }

  if (route.search) {
    const find = boxInFrame(await measure(page, "#writing-find"), vw, vh);
    if (!find.ok) findings.push(`search ${find.reason}`);
    const input = boxInFrame(await measure(page, "#writing-q"), vw, vh);
    if (!input.ok) findings.push(`search input ${input.reason}`);

    const h1Box = await measure(page, "main h1");
    const qBox = await measure(page, "#writing-q");
    if (h1Box && qBox && qBox.y < h1Box.y) {
      findings.push("search sits above the headline");
    }
  }

  return findings;
}

async function searchFlow(page) {
  const input = page.locator("#writing-q");
  await input.click();
  await input.fill("postgres");
  await page.waitForTimeout(180);
  const suggest = page.locator("#writing-suggest");
  const hidden = await suggest.getAttribute("hidden");
  const hits = await page.locator(".writing-suggest__hit").count();
  if (hidden !== null || hits < 1) {
    return [`combobox: expected visible hits, hidden=${hidden} hits=${hits}`];
  }
  return [];
}

mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "chrome" });
const failures = [];
const log = [];

try {
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
      colorScheme: vp.colorScheme,
      hasTouch: isPhone(vp),
    });
    const page = await context.newPage();
    const enabledPaths = new Set(routesForPass(vp).map(({ path }) => path));

    for (const route of ROUTES.filter(({ path }) => enabledPaths.has(path))) {
      const url = route.path.startsWith("http") ? route.path : `${BASE}${route.path}`;
      await page.goto(url, { waitUntil: "networkidle" });
      await page.waitForTimeout(120);

      const shot = join(OUT, `${route.key}--${vp.name}.png`);
      await page.screenshot({ path: shot, fullPage: false });

      const findings = await auditPage(page, route, vp);
      if (route.search && !isPhone(vp)) {
        findings.push(...(await searchFlow(page)));
        await page.screenshot({ path: join(OUT, `${route.key}--${vp.name}--search.png`), fullPage: false });
        await page.locator("#writing-q").fill("");
      }

      const line = `${vp.name} ${route.path}: ${findings.length ? findings.join("; ") : "ok"}`;
      log.push(line);
      if (findings.length) failures.push(line);
    }

    await context.close();
  }
} finally {
  await browser.close();
}

writeFileSync(join(OUT, "report.txt"), log.join("\n") + "\n");
console.log(log.join("\n"));
if (failures.length) {
  console.error(`\n${failures.length} first-viewport failures`);
  process.exit(1);
}
console.log("\nhero first-viewport contract passed");
