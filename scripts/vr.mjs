#!/usr/bin/env node
/**
 * Visual regression: capture, or compare against a stored baseline.
 *
 *   NODE_PATH=$HOME/node_modules node scripts/vr.mjs accept   [baseUrl]
 *   NODE_PATH=$HOME/node_modules node scripts/vr.mjs compare  [baseUrl]
 *
 * What gates, and why it is not pixels.
 *
 * This started as a zero-differing-pixel gate, on the theory that same machine
 * + same Chrome + same CSS must produce byte-identical PNGs. That theory is
 * wrong here. A capture-then-immediately-compare run with no code change at all
 * moved 11 of 180 shots — mostly 0.001–0.2%, and including `/colophon/`, which
 * has no images: a 40x8px run of footer text differing by antialiasing alone.
 * A gate that fires on 6% of runs for no reason is a gate people switch off.
 *
 * The same run had **0 computed-style changes across all 180 shots**. So the
 * gate is computed styles plus page height:
 *
 *   - computed styles — deterministic, and the direct measure of "did this
 *     refactor change what applies to an element". This is what catches a
 *     specificity slip during a fold, including the half pixels cannot see
 *     (cursor, touch-action, pointer-events, transition, scroll-margin).
 *   - page height — catches anything structural that styles alone might miss.
 *   - pixels — always measured, always written to _vr/diff/ for review, but
 *     advisory. Read them; do not let a robot fail a build on them.
 *
 * This is not a weaker gate than the original intent. When the `.card-grid`
 * rule was over-deleted during the dead-CSS pass, the computed-style dump
 * reported `display: grid -> block` on nine shots and named the exact element.
 * The pixel count said "some things differ".
 *
 * Diffing happens inside Chromium via OffscreenCanvas, so there is no pngjs /
 * pixelmatch dependency and therefore no package.json. Same pixel semantics.
 *
 * Deliberately NOT in CI. CI is ubuntu-24.04; `--font-prose` resolves through
 * `ui-serif, "Iowan Old Style", Charter, …` and `--font-display` through a
 * metric-override fallback, all of which fontconfig answers differently. macOS
 * baselines would red-flag every CI run inside a week, and a gate that cries
 * wolf gets switched off. `rake css:deadwood` and `rake css:budget` are the
 * platform-independent gates that belong in CI.
 *
 * Do not edit files in the repo while a run is in flight. `jekyll serve`
 * watches, and a rebuild landing mid-capture makes `networkidle` flaky — the
 * first baseline run here lost 8 of 180 shots exactly that way.
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs";
import { join } from "node:path";

const MODE = process.argv[2] || "compare";
const BASE = process.argv[3] || "http://127.0.0.1:4000";
const ROOT = "_vr";
const GOLDEN = join(ROOT, "baseline");
const DIFF = join(ROOT, "diff");

// Chosen for component coverage, not traffic. Every route below is the only
// place some component renders; drop one and that component goes unwatched.
const ROUTES = [
  ["home", "/"],                                    // .portfolio-hero, .portfolio-proof, .portfolio-note, .portfolio-contact
  ["work", "/work/"],                               // .interior-hero--index, capability rail, .portfolio-work__list--index
  ["case-practice", "/work/data-platform-practice/"], // .case-scan, .case-glance, .case-impact, .stats, .system-flow, .case-map, .strip*
  ["case-lab", "/work/multi-engine-ha-lab/"],       // where the failover ledger lands
  ["writing", "/writing/"],                         // .writing-find, .writing-feed, .writing-subscribe
  ["writing-query", "/writing/?q=postgres"],        // .writing-suggest__*, .is-hit, .is-filtering — JS-only classes
  ["post-tutorial", "/writing/failover-lab-six-engines-eight-scenarios/"], // cover + toc + series + tutorial-header
  ["post-essay", "/writing/building-data-platforms-and-ai-products/"],     // the no-cover branch
  ["tag", "/writing/tags/postgres/"],               // .card-grid + the base .post-card panel — only route it is reachable
  ["tags", "/writing/tags/"],                       // .topic-index
  ["about", "/about/"],                             // .about-profile, .principle-list
  ["hire", "/hire/"],                               // .engagement-grid, .decline-list, .briefing-list
  ["resume", "/resume/"],                           // .resume-proof, .capability-map, .page-actions
  ["colophon", "/colophon/"],                       // bare .page--body prose
  ["404", "/404.html"],
];

// Six widths, each one a real hinge in the stylesheet rather than a device name.
const WIDTHS = [
  [1440, 900],
  [1280, 800],
  [1104, 800],  // 68.75rem — post shell + TOC rail
  [1024, 768],  // 64rem — article/media two-column
  [768, 1024],  // 48rem — the dominant breakpoint
  [390, 844],
];
const THEMES = ["light", "dark"];

async function diffInPage([aB64, bB64]) {
  const load = async (b64) =>
    createImageBitmap(await (await fetch("data:image/png;base64," + b64)).blob());
  const [A, B] = await Promise.all([load(aB64), load(bB64)]);
  if (A.width !== B.width || A.height !== B.height) {
    return { sizeMismatch: true, a: [A.width, A.height], b: [B.width, B.height] };
  }
  const c = new OffscreenCanvas(A.width, A.height);
  const x = c.getContext("2d", { willReadFrequently: true });
  x.drawImage(A, 0, 0);
  const da = x.getImageData(0, 0, A.width, A.height).data;
  x.clearRect(0, 0, A.width, A.height);
  x.drawImage(B, 0, 0);
  const db = x.getImageData(0, 0, A.width, A.height).data;
  const out = x.createImageData(A.width, A.height);
  let n = 0;
  for (let i = 0; i < da.length; i += 4) {
    const d = Math.abs(da[i] - db[i]) + Math.abs(da[i + 1] - db[i + 1]) + Math.abs(da[i + 2] - db[i + 2]);
    if (d > 0) {
      n++;
      out.data[i] = 255; out.data[i + 1] = 0; out.data[i + 2] = 0; out.data[i + 3] = 255;
    } else {
      out.data[i] = da[i]; out.data[i + 1] = da[i + 1]; out.data[i + 2] = da[i + 2]; out.data[i + 3] = 36;
    }
  }
  x.putImageData(out, 0, 0);
  const blob = await c.convertToBlob({ type: "image/png" });
  const png = await new Promise((r) => {
    const fr = new FileReader();
    fr.onload = () => r(fr.result);
    fr.readAsDataURL(blob);
  });
  return { n, total: da.length / 4, png };
}

// Computed styles pixels cannot see. Folding an override changes exactly these.
const SAMPLE = [
  "color", "background-color", "border-color", "border-width", "outline-color",
  "font-size", "font-family", "font-weight", "line-height", "letter-spacing",
  "padding", "margin", "min-height", "max-width", "display", "position",
  "grid-template-columns", "grid-area", "gap", "overflow", "z-index",
  "transition", "pointer-events", "touch-action", "box-shadow", "aspect-ratio",
  "scroll-margin-block-start",
];

const key = (name, w, h, theme) => `${name}--${w}x${h}--${theme}`;

// The computed-style dump walks every [class] element (~900 on a long post) and
// is the slowest part of a run. Specificity slips show up identically at every
// width, so sample the two extremes rather than all six.
const STYLE_WIDTHS = new Set([1440, 390]);

async function shoot(page, url) {
  await page.goto(BASE + url, { waitUntil: "networkidle", timeout: 45000 });
  // Without fonts.ready you sample mid-swap and every text pixel differs.
  await page.evaluate(() => document.fonts.ready);

  // Every post cover is loading="lazy", and a fullPage screenshot captures far
  // past the viewport, so whether a given cover has decoded at capture time is
  // a race. It first showed up as 11% of a tag page differing, then as 18% of
  // the writing index — in both cases solid blocks exactly the shape of the
  // covers, with every text pixel identical.
  //
  // Scrolling to trigger the loads is not enough: an image the lazy loader
  // deprioritised after we scrolled back is left `complete === false` and never
  // fires `load`, so an un-timed `Promise.all` over them hangs until the goto
  // timeout — which is what turned one slow route into a cascade of failures.
  // Opt out of lazy loading altogether instead, and give every wait a deadline.
  await page.evaluate(async () => {
    const imgs = [...document.images];
    for (const img of imgs) img.loading = "eager";

    const settled = (img) =>
      new Promise((resolve) => {
        const done = () => resolve();
        if (img.complete && img.naturalWidth > 0) return img.decode().then(done, done);
        img.addEventListener("load", () => img.decode().then(done, done), { once: true });
        img.addEventListener("error", done, { once: true });
        setTimeout(done, 8000);
      });

    await Promise.all(imgs.map(settled));

    // The reading-progress bar is driven by `animation-timeline: scroll()` and
    // the TOC spy by an IntersectionObserver. Neither has moved here, but a
    // frame pair costs nothing and keeps them pinned at the top of the page.
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  });

  // The writing index hydrates from a JSON island; let the filter settle.
  await page.waitForTimeout(250);
  return page.screenshot({ fullPage: true });
}

async function styles(page) {
  return page.evaluate((props) => {
    const path = (el) => {
      const parts = [];
      for (let e = el; e && e.nodeType === 1 && parts.length < 8; e = e.parentElement) {
        const i = e.parentElement ? [...e.parentElement.children].indexOf(e) : 0;
        parts.unshift(`${e.tagName.toLowerCase()}:${i}`);
      }
      return parts.join(">");
    };
    const out = {};
    for (const el of document.querySelectorAll("[class]")) {
      const cs = getComputedStyle(el);
      const rec = {};
      for (const p of props) rec[p] = cs.getPropertyValue(p);
      out[path(el)] = rec;
    }
    return out;
  }, SAMPLE);
}

(async () => {
  const accepting = MODE === "accept";
  if (accepting) {
    rmSync(GOLDEN, { recursive: true, force: true });
    mkdirSync(GOLDEN, { recursive: true });
  } else {
    if (!existsSync(GOLDEN)) {
      console.error(`no baseline at ${GOLDEN}/ — run: make vr-accept`);
      process.exit(2);
    }
    rmSync(DIFF, { recursive: true, force: true });
    mkdirSync(DIFF, { recursive: true });
  }

  const browser = await chromium.launch({ channel: "chrome" });
  // A scratch page that only ever runs the comparator, so the diff never
  // executes in a context that has the site's own CSS or JS loaded.
  const scratch = await (await browser.newContext()).newPage();

  let shots = 0, moved = 0, styleDrift = 0, worstCls = 0;
  const failures = [];   // gate: computed-style + page-height changes
  const notes = [];      // advisory: pixel deltas, reviewed by a human

  for (const theme of THEMES) {
    for (const [w, h] of WIDTHS) {
      const ctx = await browser.newContext({
        viewport: { width: w, height: h },
        deviceScaleFactor: 1,
        colorScheme: theme,
        // Mandatory: .portfolio-hero runs an 8s infinite `portrait-scan`
        // keyframe. Without this every home-page diff is animation noise.
        reducedMotion: "reduce",
        isMobile: w < 500,
        hasTouch: w < 500,
      });
      // Set the theme before first paint. Setting data-theme after goto
      // repaints, and the repaint is what you end up diffing.
      await ctx.addInitScript((t) => {
        try { localStorage.setItem("theme", t); } catch {}
      }, theme);

      let page = await ctx.newPage();

      for (const [name, url] of ROUTES) {
        const k = key(name, w, h, theme);
        let png;
        try {
          png = await shoot(page, url);
        } catch (e) {
          failures.push(`${k}: load failed — ${e.message.split("\n")[0]}`);
          // A goto that threw can still have a navigation in flight, and it
          // will interrupt the *next* route's goto — one slow page cascades
          // into every route after it. A fresh page is a cleaner reset than
          // parking on about:blank, which just becomes the next interrupt.
          await page.close().catch(() => {});
          page = await ctx.newPage();
          continue;
        }
        shots++;

        const cls = await page.evaluate(() => new Promise((res) => {
          let v = 0;
          new PerformanceObserver((l) => {
            for (const e of l.getEntries()) if (!e.hadRecentInput) v += e.value;
          }).observe({ type: "layout-shift", buffered: true });
          setTimeout(() => res(+v.toFixed(4)), 250);
        }));
        if (cls > worstCls) worstCls = cls;
        // 0.02 is 5x stricter than the web.dev "good" bound of 0.1, and loose
        // enough not to fire on sub-thousandth jitter. The site sits at exactly
        // 0 on almost every route; /resume/ at 768 is the one that moves, at
        // ~0.006 — real, but 1/16th of this budget and 1/16th of "good".
        if (cls > 0.02) failures.push(`${k}: CLS ${cls} (budget 0.02)`);

        const st = STYLE_WIDTHS.has(w) ? await styles(page) : null;

        if (accepting) {
          writeFileSync(join(GOLDEN, `${k}.png`), png);
          if (st) writeFileSync(join(GOLDEN, `${k}.json`), JSON.stringify(st));
          continue;
        }

        const goldPng = join(GOLDEN, `${k}.png`);
        if (!existsSync(goldPng)) {
          failures.push(`${k}: no baseline (new route or viewport?)`);
          continue;
        }
        const d = await scratch.evaluate(diffInPage, [
          readFileSync(goldPng).toString("base64"),
          png.toString("base64"),
        ]);
        if (d.sizeMismatch) {
          failures.push(`${k}: page height changed ${d.a.join("x")} -> ${d.b.join("x")}`);
        } else if (d.n > 0) {
          moved++;
          const pct = ((d.n / d.total) * 100).toFixed(3);
          notes.push(`${k}: ${d.n} px differ (${pct}%)`);
          writeFileSync(join(DIFF, `${k}.png`),
            Buffer.from(d.png.split(",")[1], "base64"));
        }

        // Style drift catches what pixels cannot: cursor, touch-action,
        // pointer-events, transition, scroll-margin. A fold changes those
        // silently, which is exactly the failure mode of a specificity slip.
        const goldJson = join(GOLDEN, `${k}.json`);
        if (st && existsSync(goldJson)) {
          const before = JSON.parse(readFileSync(goldJson, "utf8"));
          const diffs = [];
          for (const [p, rec] of Object.entries(st)) {
            const old = before[p];
            if (!old) continue;
            for (const prop of SAMPLE) {
              if (old[prop] !== rec[prop]) diffs.push(`${p} ${prop}: ${old[prop]} -> ${rec[prop]}`);
            }
          }
          if (diffs.length) {
            styleDrift += diffs.length;
            failures.push(`${k}: ${diffs.length} computed-style changes\n      ` +
              diffs.slice(0, 4).join("\n      "));
          }
        }
      }
      await ctx.close();
    }
  }

  await browser.close();

  const label = accepting ? "captured" : "compared";
  console.log(`\nvr: ${label} ${shots} shots (${ROUTES.length} routes x ${WIDTHS.length} widths x ${THEMES.length} themes)`);
  console.log(`vr: worst CLS ${worstCls}`);

  if (accepting) {
    // A silently-short baseline is worse than no baseline: every later compare
    // run reports "no baseline" for the gaps and you learn to skim past it.
    const want = ROUTES.length * WIDTHS.length * THEMES.length;
    console.log(`vr: baseline written to ${GOLDEN}/`);
    if (shots !== want) {
      console.log(`\nvr: INCOMPLETE — captured ${shots}/${want}, baseline is not usable`);
      for (const f of failures) console.log(`  ${f}`);
      process.exit(1);
    }
    // Budget breaches are worth surfacing during a capture, but they describe
    // the site as it stands, not a broken baseline. Report, do not fail.
    if (failures.length) {
      console.log(`\nvr: ${failures.length} budget note(s) on the captured build`);
      for (const f of failures) console.log(`  ${f}`);
    }
    return;
  }

  if (moved) {
    console.log(`\nvr: ${moved}/${shots} shot(s) differ in pixels (advisory — see ${DIFF}/)`);
    for (const n of notes) console.log(`  ${n}`);
  }

  if (!failures.length) {
    console.log(`\nvr: 0 computed-style changes, 0 page-height changes — PASS`);
    return;
  }
  console.log(`\nvr: FAIL — ${styleDrift} computed-style change(s)`);
  for (const f of failures) console.log(`  ${f}`);
  process.exit(1);
})();
