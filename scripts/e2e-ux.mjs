#!/usr/bin/env node
/**
 * Main-page UX audit: interact, screenshot, measure against a production
 * first-viewport + footer contract. Playwright MCP is not in this workspace.
 *
 *   NODE_PATH=$HOME/node_modules node scripts/e2e-ux.mjs [baseUrl]
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { BREAKPOINT_PASSES, isPhone, routesForPass } from "./e2e-config.mjs";

const BASE = process.argv[2] || "http://127.0.0.1:4000";
const OUT = "/tmp/technobasant-ux";

function boxInFrame(box, vw, vh, pad = 1) {
  if (!box) return { ok: false, reason: "missing" };
  if (box.y < -pad) return { ok: false, reason: `clips top (${box.y.toFixed(1)})` };
  if (box.y + box.height > vh + pad) {
    return { ok: false, reason: `clips bottom (${(box.y + box.height).toFixed(1)} > ${vh})` };
  }
  if (box.x < -pad) return { ok: false, reason: `clips left (${box.x.toFixed(1)})` };
  if (box.x + box.width > vw + pad) {
    return { ok: false, reason: `clips right (${(box.x + box.width).toFixed(1)} > ${vw})` };
  }
  return { ok: true, ...box };
}

async function metrics(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const header = document.querySelector(".site-header");
    const footer = document.querySelector(".site-footer");
    const mark = document.querySelector(".mark");
    const photo = document.querySelector(".mark__photo");
    const hero = document.querySelector(".hero, .interior-hero");
    const h1 = document.querySelector("main h1");
    const lede = document.querySelector("main .lede");
    const wrapHeader = document.querySelector(".header-inner");
    const wrapFooter = document.querySelector(".site-footer .wrap");
    const overflowX = doc.scrollWidth - window.innerWidth;
    const headerBox = header?.getBoundingClientRect();
    const footerBox = footer?.getBoundingClientRect();
    const markBox = mark?.getBoundingClientRect();
    const h1Box = h1?.getBoundingClientRect();
    const ledeBox = lede?.getBoundingClientRect();
    const heroBox = hero?.getBoundingClientRect();
    const headerWrap = wrapHeader?.getBoundingClientRect();
    const footerWrap = wrapFooter?.getBoundingClientRect();
    const theme = document.documentElement.getAttribute("data-theme");
    const active = document.querySelector(".nav__link.is-active, .nav a[aria-current='page']");
    return {
      theme,
      overflowX,
      hasPhoto: Boolean(photo),
      headerH: headerBox ? Math.round(headerBox.height) : 0,
      footerH: footerBox ? Math.round(footerBox.height) : 0,
      footerY: footerBox ? Math.round(footerBox.y + window.scrollY) : 0,
      pageH: doc.scrollHeight,
      markH: markBox ? Math.round(markBox.height) : 0,
      markY: markBox ? Math.round(markBox.y) : null,
      h1InView: h1Box ? h1Box.bottom <= window.innerHeight + 1 && h1Box.top >= -1 : false,
      ledeInView: ledeBox ? ledeBox.bottom <= window.innerHeight + 1 : !lede,
      heroBottom: heroBox ? Math.round(heroBox.bottom) : null,
      headerWrapX: headerWrap ? Math.round(headerWrap.x) : null,
      footerWrapX: footerWrap ? Math.round(footerWrap.x) : null,
      headerWrapW: headerWrap ? Math.round(headerWrap.width) : null,
      footerWrapW: footerWrap ? Math.round(footerWrap.width) : null,
      hasActiveNav: Boolean(active),
      skipHref: document.querySelector(".skip-link")?.getAttribute("href") || null,
    };
  });
}

async function contractFindings(page, route, viewport) {
  return page.evaluate(({ route, viewport }) => {
    const findings = [];
    const visible = (el) => {
      const style = getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && box.width > 0 && box.height > 0;
    };
    const box = (el) => el.getBoundingClientRect();
    const isPhone = viewport.width <= 390;

    if (isPhone) {
      const h1 = document.querySelector("main h1");
      const prose = document.querySelector(".prose > p:not([class]), .prose > h2");
      if (h1 && parseFloat(getComputedStyle(h1).fontSize) < 26) {
        findings.push(`mobile H1 too small (${getComputedStyle(h1).fontSize})`);
      }
      if (prose && parseFloat(getComputedStyle(prose).fontSize) < 16) {
        findings.push(`mobile prose too small (${getComputedStyle(prose).fontSize})`);
      }
      if (prose) {
        const r = box(prose);
        if (r.left < 15 || r.right > innerWidth - 15) {
          findings.push(`prose gutter ${Math.round(r.left)}/${Math.round(innerWidth - r.right)}px`);
        }
      }

      const touchSelectors = [
        "[data-nav-open]",
        ".theme-toggle",
        ".btn",
        ".writing-find__type > span",
        ".toc-mobile > summary",
        ".series-nav__list a",
        ".author-card__links a",
        ".share a",
        ".case-map a",
      ];
      const touchTargets = [...document.querySelectorAll(touchSelectors.join(","))].filter(visible);
      const undersized = touchTargets
        .map((el) => ({ el, r: box(el) }))
        .filter(({ r }) => r.width < 44 || r.height < 44)
        .slice(0, 3)
        .map(({ el, r }) => `${el.className || el.tagName} ${Math.round(r.width)}×${Math.round(r.height)}`);
      if (undersized.length) findings.push(`touch targets: ${undersized.join(", ")}`);

      const surfaces = [...document.querySelectorAll(
        ".tutorial-header, .series-nav, .author-card, .writing-subscribe, .resume-proof__item, .related .post-card",
      )].filter(visible);
      const badSurfaces = surfaces
        .map((el) => ({ el, r: box(el), border: parseFloat(getComputedStyle(el).borderLeftWidth) }))
        .filter(({ r, border }) => border > 0 && (r.left < 15 || r.right > innerWidth - 15))
        .slice(0, 3)
        .map(({ el, r }) => `${el.className} @${Math.round(r.left)}..${Math.round(r.right)}`);
      if (badSurfaces.length) findings.push(`bordered surfaces miss gutter: ${badSurfaces.join(", ")}`);

      for (const pre of document.querySelectorAll(".highlighter-rouge pre")) {
        const r = box(pre);
        if (r.left < -1 || r.right > innerWidth + 1) findings.push("code block escapes viewport");
      }
      for (const table of document.querySelectorAll(".prose > table")) {
        const r = box(table);
        if (r.left < 15 || r.right > innerWidth - 15) findings.push("table escapes prose gutter");
        if (table.scrollWidth > table.clientWidth && getComputedStyle(table).overflowX !== "auto") {
          findings.push("wide table lacks internal scrolling");
        }
      }

      const caption = document.querySelector(".article-hero__media figcaption");
      if (caption && getComputedStyle(caption).position !== "static") {
        findings.push("cover caption overlays artwork");
      }

      const mobileToc = document.querySelector(".toc-mobile");
      const summary = document.querySelector(".article-summary");
      if (mobileToc && summary && box(mobileToc).top < box(summary).bottom - 1) {
        findings.push("mobile TOC is not after the opening summary");
      }
    }

    if (viewport.width === 863 || viewport.width === 864) {
      const desktopNav = document.querySelector(".nav");
      const menu = document.querySelector("[data-nav-open]");
      const desktopVisible = desktopNav && visible(desktopNav);
      const menuVisible = menu && visible(menu);
      if (viewport.width === 863 && (desktopVisible || !menuVisible)) {
        findings.push("863px nav breakpoint state is wrong");
      }
      if (viewport.width === 864 && (!desktopVisible || menuVisible)) {
        findings.push("864px nav breakpoint state is wrong");
      }
    }

    if (route.kind === "post" && (viewport.width === 1099 || viewport.width === 1100)) {
      const desktopToc = document.querySelector(".toc");
      const mobileToc = document.querySelector(".toc-mobile");
      const desktopVisible = desktopToc && visible(desktopToc);
      const mobileVisible = mobileToc && visible(mobileToc);
      if (viewport.width === 1099 && (desktopVisible || !mobileVisible)) {
        findings.push("1099px TOC breakpoint state is wrong");
      }
      if (viewport.width === 1100 && (!desktopVisible || mobileVisible)) {
        findings.push("1100px TOC breakpoint state is wrong");
      }
    }

    return [...new Set(findings)];
  }, { route, viewport });
}

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ channel: "chrome" });
const log = [];
const failures = [];

function note(line, fail = false) {
  log.push(line);
  if (fail) failures.push(line);
}

try {
  const files = await browser.newPage();
  for (const path of ["/llms.txt", "/ai.txt", "/.well-known/llms.txt", "/robots.txt", "/sitemap.xml", "/writing/feed.xml"]) {
    const res = await files.goto(`${BASE}${path}`, { waitUntil: "domcontentloaded" });
    const ok = res && res.ok();
    note(`file ${path}: ${ok ? res.status() : "FAIL"}`, !ok);
  }
  await files.close();

  const passes = BREAKPOINT_PASSES;

  for (const vp of passes) {
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
      }, vp.colorScheme === "dark" ? "dark" : "light");
      await page.waitForTimeout(160);

      const shot = join(OUT, `${route.key}--${vp.name}.png`);
      await page.screenshot({ path: shot, fullPage: false });

      const m = await metrics(page);
      const prefix = `${vp.name} ${route.path}`;
      for (const finding of await contractFindings(page, route, vp)) {
        note(`${prefix}: ${finding}`, true);
      }

      if (m.hasPhoto) note(`${prefix}: header still has profile photo`, true);
      if (m.overflowX > 1) note(`${prefix}: horizontal overflow ${m.overflowX}px`, true);
      if (!m.h1InView) note(`${prefix}: H1 not fully in first viewport`, true);
      if (!m.ledeInView) note(`${prefix}: lede clips first viewport`, true);
      if (m.headerWrapX != null && m.footerWrapX != null) {
        const dx = Math.abs(m.headerWrapX - m.footerWrapX);
        const dw = Math.abs((m.headerWrapW || 0) - (m.footerWrapW || 0));
        if (dx > 2 || dw > 2) {
          note(`${prefix}: header/footer wrap misaligned dx=${dx} dw=${dw} (header ${m.headerWrapW}@${m.headerWrapX}, footer ${m.footerWrapW}@${m.footerWrapX})`, true);
        }
      }
      if (route.path !== "/" && route.path !== "/hire/" && !m.hasActiveNav && !isPhone(vp)) {
        note(`${prefix}: no active nav state`, true);
      }

      if (route.key === "home") {
        const actions = await page.locator(".portfolio-hero .actions").first().boundingBox();
        const fit = boxInFrame(actions, vp.width, vp.height);
        if (!fit.ok) note(`${prefix}: hero actions ${fit.reason}`, true);
        const proof = await page.locator(".portfolio-proof").first().boundingBox();
        if (proof && proof.y > vp.height + 40) {
          note(`${prefix}: proof line far below fold (y=${Math.round(proof.y)})`);
        }
      }

      if (route.key === "writing") {
        await page.locator("#writing-q").fill("postgres");
        await page.waitForTimeout(200);
        const hits = await page.locator(".writing-suggest__hit").count();
        const hidden = await page.locator("#writing-suggest").getAttribute("hidden");
        if (hidden !== null || hits < 1) {
          note(`${prefix}: search combobox failed hidden=${hidden} hits=${hits}`, true);
        }
        if (!page.url().includes("q=postgres")) {
          note(`${prefix}: search state missing from URL`, true);
        }
        await page.screenshot({ path: join(OUT, `${route.key}--${vp.name}--search.png`), fullPage: false });
        await page.locator("#writing-q").fill("");
      }

      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(80);
      await page.locator(".site-footer").screenshot({ path: join(OUT, `${route.key}--${vp.name}--footer.png`) });
      const footerLinks = await page.locator(".site-footer a").count();
      if (footerLinks < 8) note(`${prefix}: footer looks sparse (${footerLinks} links)`, true);
      await page.evaluate(() => window.scrollTo(0, 0));
    }

    if (vp.name === "desktop-1440-light") {
      await page.goto(`${BASE}/about/`, { waitUntil: "networkidle" });
      const toggle = page.locator(".theme-toggle, [data-theme-toggle], button[aria-label*='theme' i], button[aria-label*='Theme']").first();
      if (await toggle.count()) {
        const before = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
        await toggle.click();
        await page.waitForTimeout(200);
        const after = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
        if (before === after) note("theme toggle did not change data-theme", true);
        else note(`theme toggle ${before} → ${after}`);
        await page.screenshot({ path: join(OUT, "about--after-theme-toggle.png"), fullPage: false });
        await toggle.click();
      } else {
        note("theme toggle control missing", true);
      }

      await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
      const work = page.locator(".nav a[href*='/work/'], .nav__link[href*='/work/']").first();
      await work.click();
      await page.waitForURL(/\/work\//);
      note(`nav Work click → ${page.url()}`);

      await page.goto(`${BASE}/writing/`, { waitUntil: "networkidle" });
      await page.keyboard.press("/");
      if (!(await page.locator("#writing-q").evaluate((el) => el === document.activeElement))) {
        note("writing / shortcut did not focus search", true);
      }
      await page.keyboard.press("Escape");
    }

    if (vp.name === "phone-390-light") {
      await page.goto(`${BASE}/about/`, { waitUntil: "networkidle" });
      const opener = page.locator("[data-nav-open]");
      const dialog = page.locator("#site-nav-dialog");
      await opener.click();
      if (!(await dialog.evaluate((el) => el.open))) {
        note("mobile navigation dialog did not open", true);
      }
      if ((await opener.getAttribute("aria-expanded")) !== "true") {
        note("mobile navigation aria-expanded not true", true);
      }
      await page.keyboard.press("Escape");
      await page.waitForFunction(() => {
        const trigger = document.querySelector("[data-nav-open]");
        const menu = document.querySelector("#site-nav-dialog");
        return menu && !menu.open && trigger?.getAttribute("aria-expanded") === "false";
      });
      if (await dialog.evaluate((el) => el.open)) {
        note("mobile navigation dialog did not close with Escape", true);
      }
      if ((await opener.getAttribute("aria-expanded")) !== "false") {
        note("mobile navigation aria-expanded not restored", true);
      }

      await page.goto(`${BASE}/writing/`, { waitUntil: "networkidle" });
      const kbdVisible = await page.locator(".writing-find__kbd").isVisible();
      if (kbdVisible) note("mobile writing shortcut hint should be hidden", true);
      await page.locator("#writing-q").tap();
      await page.locator("#writing-q").fill("postgres");
      await page.waitForTimeout(180);
      if ((await page.locator(".writing-suggest__hit").count()) < 1) {
        note("mobile writing search returned no suggestions", true);
      }
    }

    await context.close();
  }
} finally {
  await browser.close();
}

const report = log.join("\n") + `\n\n${failures.length} failures\n`;
writeFileSync(join(OUT, "report.txt"), report);
console.log(report);
if (failures.length) process.exit(1);
console.log("ux audit passed");
