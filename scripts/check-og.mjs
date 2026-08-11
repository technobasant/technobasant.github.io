// Social-card validator. Offline, zero dependencies, runs against _site/.
//
// Why this exists: html-proofer's OpenGraph check inspects only og:url and
// og:image, matches property= but not name=, and is not enabled by default. It
// verifies nothing about titles, descriptions, card type, image dimensions,
// aspect ratio or file size — all of which silently degrade a shared link.
//
// Platform limits encoded below (documented values, Aug 2026):
//   Facebook  >= 1200x630, min 200x200, max 8MB, 1.91:1, JPEG/GIF/PNG only
//   LinkedIn  min 1200x627, max 5MB, 1.91:1
//   X         min 300x157, max 5MB, 2:1
// PNG/JPEG only: Facebook and LinkedIn document no WebP, and nobody documents
// AVIF. Serve modern formats to browsers via <picture>; never via og:image.
//
// Usage: node scripts/check-og.mjs   (exits 1 on any error)

import { readFileSync, readdirSync, statSync, openSync, readSync, closeSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const ROOT = '_site';
const SITE = (process.env.SITE_URL || 'https://technobasant.github.io').replace(/\/$/, '');
const MAX_BYTES = 5 * 1024 * 1024; // strictest of the documented caps

const walk = (d) =>
  readdirSync(d, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(join(d, e.name)) : e.name.endsWith('.html') ? [join(d, e.name)] : []
  );

// Key on property= OR name= — generators emit both, and a validator that only
// reads one silently passes pages it never actually checked.
function metas(html) {
  const out = {};
  for (const m of html.matchAll(/<meta\b[^>]*>/gi)) {
    const t = m[0];
    const k = (t.match(/\b(?:property|name)\s*=\s*["']([^"']+)["']/i) || [])[1];
    const v = (t.match(/\bcontent\s*=\s*["']([^"']*)["']/i) || [])[1];
    if (k) (out[k.toLowerCase()] ??= []).push(v ?? '');
  }
  return out;
}

// Real pixel dimensions from the file header — no image library needed.
function dims(p) {
  const fd = openSync(p, 'r');
  const b = Buffer.alloc(65536);
  const n = readSync(fd, b, 0, 65536, 0);
  closeSync(fd);
  if (b.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])))
    return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), fmt: 'png' };
  if (b[0] === 0xff && b[1] === 0xd8) {
    let o = 2;
    while (o < n - 9) {
      if (b[o] !== 0xff) { o++; continue; }
      const mk = b[o + 1];
      if (mk >= 0xc0 && mk <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(mk))
        return { h: b.readUInt16BE(o + 5), w: b.readUInt16BE(o + 7), fmt: 'jpeg' };
      o += 2 + b.readUInt16BE(o + 2);
    }
  }
  if (b.subarray(0, 4).toString() === 'RIFF' && b.subarray(8, 12).toString() === 'WEBP')
    return { w: 0, h: 0, fmt: 'webp' };
  return { w: 0, h: 0, fmt: 'unknown' };
}

const REQUIRED = ['og:title', 'og:description', 'og:url', 'og:image', 'og:type', 'og:site_name', 'twitter:card'];
const CARDS = new Set(['summary', 'summary_large_image', 'app', 'player']);

let errors = 0, warnings = 0, files = 0;

for (const f of walk(ROOT)) {
  const html = readFileSync(f, 'utf8');
  if (/name=["']robots["'][^>]*noindex/i.test(html)) continue; // 404 and friends
  files++;

  const M = metas(html);
  const rel = '/' + relative(ROOT, f).split(sep).join('/');
  const err = (m) => { errors++; console.log(`ERROR ${rel}: ${m}`); };
  const warn = (m) => { warnings++; console.log(`warn  ${rel}: ${m}`); };

  for (const k of REQUIRED) if (!M[k]?.[0]) err(`missing ${k}`);
  for (const k of ['og:title', 'og:description', 'og:url', 'og:image', 'twitter:card'])
    if ((M[k] || []).length > 1) err(`duplicate ${k} (${M[k].length})`);

  const card = M['twitter:card']?.[0];
  if (card && !CARDS.has(card)) err(`twitter:card="${card}" is not a valid type`);

  // Every platform truncates around these lengths.
  if ((M['og:title']?.[0] || '').length > 70) warn(`og:title ${M['og:title'][0].length} chars — truncates`);
  if ((M['og:description']?.[0] || '').length > 200) warn(`og:description too long — truncates`);

  const ogUrl = M['og:url']?.[0];
  if (ogUrl && !/^https:\/\//.test(ogUrl)) err(`og:url not absolute https — ${ogUrl}`);

  const img = M['og:image']?.[0];
  if (img) {
    if (!/^https:\/\//.test(img)) {
      err(`og:image not absolute https — ${img}`);
    } else if (img.startsWith(SITE)) {
      const p = join(ROOT, decodeURIComponent(img.slice(SITE.length)));
      let st = null;
      try { st = statSync(p); } catch { err(`og:image does not exist locally — ${img}`); }
      if (st) {
        if (st.size > MAX_BYTES) err(`og:image ${(st.size / 1048576).toFixed(2)}MB exceeds 5MB`);
        const { w, h, fmt } = dims(p);
        if (fmt === 'webp' || fmt === 'unknown')
          err(`og:image is ${fmt} — Facebook and LinkedIn document PNG/JPEG only`);
        if (w && h) {
          if (w < 600 || h < 315) err(`og:image ${w}x${h} below the 600x315 floor`);
          else if (w < 1200 || h < 630) warn(`og:image ${w}x${h} below the recommended 1200x630`);
          const ar = w / h;
          if (ar < 1.8 || ar > 2.0) warn(`og:image aspect ${ar.toFixed(2)}:1 outside 1.8–2.0`);
          const dw = +(M['og:image:width']?.[0] || 0);
          const dh = +(M['og:image:height']?.[0] || 0);
          if (dw && dh && (dw !== w || dh !== h)) err(`declared ${dw}x${dh} but file is ${w}x${h}`);
          if (!dw || !dh) warn(`missing og:image:width/height — delays first render`);
        }
      }
    }
  }

  if (!M['og:image:alt']?.[0] && !M['twitter:image:alt']?.[0]) warn(`no og:image:alt`);
  if (M['og:type']?.[0] === 'article' && !M['article:published_time']?.[0])
    warn(`og:type=article without article:published_time`);
}

console.log(`\nog: ${files} pages · ${errors} error(s) · ${warnings} warning(s)`);
process.exit(errors ? 1 : 0);
