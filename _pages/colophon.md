---
title: Colophon
last_modified_at: 2026-10-14
seo_title: "How this site is built — Basant Bhattarai"
eyebrow: Meta
headline: "Small, inspectable, and owned end to end."
hero_code: "BUILD / NOTES"
permalink: /colophon/
description: "How this site is built: Jekyll, hand-written SCSS, self-hosted fonts, GitHub Actions — no analytics, no trackers, no cookies, and AI crawlers allowed."
---

## Build

Jekyll, with kramdown for markdown and Rouge for syntax highlighting. The styles are hand-written SCSS on a small set of design tokens — no CSS framework, no utility classes, no build step beyond Jekyll's own. There is a little vanilla JavaScript for the theme toggle, the table of contents, the copy-code buttons and the writing search, and nothing that depends on it: every page reads in full with scripts off.

Type is Fraunces for display and JetBrains Mono for code, both self-hosted from `/assets/fonts/`. Running text is a system serif stack — Iowan Old Style, Charter, Georgia — which costs no bytes and no requests; Inter carries the interface chrome around it. Content lives in markdown; public metrics come from a single data file so a figure cannot say one thing on one page and something else on another.

GitHub Actions builds and deploys on push. The same gate checks internal links, structured data, feeds, code-fence language labels, whole-card link semantics, an editorial contract for every post (description length, takeaways, a subject group, a cover), contrast for every colour token in both themes, a size budget for the stylesheet, the résumé PDF, and a privacy denylist for retired employer details. A broken link or confidential legacy phrase fails the build rather than reaching the reader.

## Figures and diagrams

The cover images are schematics, drawn by a script from each piece's own topology and measured numbers in the site's type and palette, not stock photography or generated imagery. They ship as AVIF and WebP with a JPEG fallback, at the width they are shown. The architecture diagrams on the case studies are not images at all: each is a short data file rendered as HTML and CSS, so it follows the theme, reflows on a phone, and reads to a screen reader.

## Privacy

No analytics. No tag manager. No trackers, no pixels, no A/B testing, no third-party scripts of any kind. This site sets no cookies and there is nothing to consent to, which is why you were not asked. Server logs belong to GitHub Pages; I do not read them and could not identify you from them.

## AI crawlers

`robots.txt` explicitly allows the major search and AI crawlers (Googlebot, Bingbot, GPTBot, ClaudeBot, PerplexityBot, Google-Extended, and others). That is a decision rather than an oversight: if a language model is going to answer a question about my work, I would rather it read the current version than a stale scrape or somebody else's summary. There is an [llms.txt](/llms.txt) with recommended citations, approved public figures, and the method behind each one, an [ai.txt](/ai.txt) discovery pointer, and both files are listed in [sitemap.xml](/sitemap.xml).

## Source

The whole site is public at [github.com/technobasant/technobasant.github.io](https://github.com/technobasant/technobasant.github.io). If something here is wrong, an issue is welcome.
