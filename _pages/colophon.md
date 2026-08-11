---
title: Colophon
eyebrow: Meta
headline: "Small, inspectable, and owned end to end."
hero_code: "BUILD / NOTES"
permalink: /colophon/
description: "How this site is built: Jekyll, hand-written SCSS, self-hosted fonts, GitHub Actions — no analytics, no trackers, no cookies, and AI crawlers allowed."
---

## Build

Jekyll, with kramdown for markdown and Rouge for syntax highlighting. The styles are hand-written SCSS on a small set of design tokens — no CSS framework, no utility classes, no build step beyond Jekyll's own. There is a little vanilla JavaScript for the theme toggle, the table of contents and the copy-code buttons, and nothing that runs if it fails to load.

Type is Fraunces for display, Inter for body text and JetBrains Mono for code, all self-hosted from `/assets/fonts/`. Content lives in markdown; the numbers on this site come from a single data file so a figure cannot say one thing on one page and something else on another.

GitHub Actions builds and deploys on push. html-proofer runs as a gate, so a broken internal link fails the build rather than the reader.

## Privacy

No analytics. No tag manager. No trackers, no pixels, no A/B testing, no third-party scripts of any kind. This site sets no cookies and there is nothing to consent to, which is why you were not asked. Server logs belong to GitHub Pages; I do not read them and could not identify you from them.

## AI crawlers

`robots.txt` explicitly allows GPTBot, ClaudeBot, PerplexityBot, Google-Extended and CCBot. That is a decision rather than an oversight: if a language model is going to answer a question about my work, I would rather it read the current version than a stale scrape or somebody else's summary. There is also an [llms.txt](/llms.txt) with the canonical numbers and the method behind each one, for the same reason.

## Source

The whole site is public at [github.com/technobasant/technobasant.github.io](https://github.com/technobasant/technobasant.github.io). If something here is wrong, an issue is welcome.
