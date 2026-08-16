---
title: "Ten CI gates, and the failure behind each one"
description: "Every gate in this repository exists because something got through. Three of them because a suite reported success against a broken artifact."
date: 2026-08-16 14:00:00 +0545
last_modified_at: 2026-08-16
type: essay
series: agentic-engineering
series_order: 2
tags: [ai-agents, data-quality]
toc: true
cover:
  base: "/assets/images/editorial-agent-guardrails-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Diagram: produce, review and gate as three stages, with three examples of a suite reporting success while the underlying artifact was broken"
  caption: "Producing a change is cheap now. Believing one is not. The gates are where the difference gets settled."
featured: true
level: intermediate
key_takeaways:
  - "Agents did not remove work, they moved it: producing a diff got cheap and verifying one did not, so review is now the constraint."
  - "Every gate in this repository exists because something got through — four of the ten were added in a single week of agent-assisted work."
  - "A suite reported 12/12 against a build that had failed, a token audit halved itself and printed ok, and a résumé PDF extracted perfectly while rendering blank. All three were green."
  - "A gate that says \"some things differ\" gets switched off; a gate that names the element gets trusted. Precision is an adoption property, not a nicety."
  - "Rules an agent can talk its way past are not rules. Policy has to be executable, and it has to fail the build."
---

## The receipts

[Part one]({{ '/writing/coding-agents-repo-governance/' | relative_url }}) argued that
agents move the bottleneck from writing code to believing it, and that the answer
is policy in the repository rather than a longer prompt. This post is the
evidence for that claim from one repository — mine, this site — where ten CI
gates now run on every build.

**Every one of them exists because something got through.** Four were added in a
single week of agent-assisted work. What follows is each failure, what it cost to
find, and what the pattern says about which gates are worth having.

## Three failures that were green

Start with the uncomfortable ones, because they are the argument.

### The suite passed against a build that had failed

The audit tasks in this repository do not build the site. They inspect whatever is in `_site`. That is fine until a build fails — because then the *previous* `_site` is still sitting there, and the whole suite runs against it happily.

A `{% raw %}{% macro %}{% endraw %}` inside a fenced code block made Jekyll abort with a Liquid syntax error. The build died. `rake default` then reported:

```text
verify: 12 passed, 0 skipped, 0 failed
jsonld: ok — 43 block(s) parsed
tokens: ok — 70 token pair(s) clear AA across both themes
```

Twelve of twelve, for a site that could no longer be generated. The only evidence of the failure was a shell exit code that had been redirected away.

The fix is four lines: compare `_site/index.html` against every source glob that can change a page, and refuse to audit if any is newer.

```text
_site/ is older than 1 source file(s) — the audit would pass on stale output.
  _posts/2024-02-04-iceberg-compaction-snapshots-rollback.md
Rebuild first:  JEKYLL_ENV=production bundle exec jekyll build
```

### The token audit halved itself and printed ok

A Ruby task checks every text colour against every surface it can land on, in both themes. It locates the two theme blocks by finding the first line containing `[data-theme="dark"]` and `[data-theme="light"]`.

I wrote an explanatory comment inside the dark block that *mentioned* the light selector. The comment came first in the file, so the light index landed above the dark index, the dark range inverted, and the audit went from 70 token pairs to 35.

It printed `ok`.

A gate that silently checks half of what it claims is worse than no gate, because it is spending your trust. The matcher is now anchored to the start of a line, and the ordering it had been assuming is asserted rather than assumed.

### The résumé extracted perfectly and rendered blank

I moved a page-chrome callback in a PDF generator to fix an unrelated parsing problem. The callback also drew the page background — an opaque rectangle over the full page — so it painted over every word.

The privacy gate extracts the PDF text and scans it. It read the document happily. `pypdf` returned 5,496 characters. Both were *correct*: the text layer was intact and complete. It was underneath a filled rectangle.

**No text-based check can catch this.** The only thing that sees it is a rasteriser:

```text
FAIL  page 1 is effectively blank (0.2% ink)
FAIL  page 2 is effectively blank (0.2% ink)
```

That gate now runs on every build, and I verified it by reinstating the bug and watching it fail.

## What the three have in common

None of them was an agent hallucinating an API. All three were **the verification surface being narrower than the thing it claimed to verify.**

That is the failure mode that matters when the volume of change goes up. A confident wrong answer is easy to catch — it does not compile, or the test fails. What gets through is the change that satisfies every check you happen to have, in a system where nobody has time to notice which checks you do not have.

Agents make that worse in a specific way: they are very good at satisfying the stated constraint. Point one at a failing gate and it will make the gate pass. Whether it made the underlying thing correct is a separate question, and the only way to keep asking it is to keep widening what the gates actually measure.

## Ten gates, and the shape of a good one

The full set in this repository:

| gate | what it refuses |
| --- | --- |
| `content` | posts missing structure, a cover, or a description in range |
| `privacy` | employer internals, matched against explicit patterns, in source and built output and the PDF |
| `check` | broken internal links, missing images, absent OpenGraph |
| `verify` | the built shape: feed, sitemap, canonical, robots, card affordances |
| `jsonld` | any structured-data block that does not parse |
| `tokens` | any text colour that fails AA on any surface it can land on, both themes |
| `css:literals` | a raw hex colour anywhere in the component layer |
| `css:budget` | a stylesheet over its gzip ceiling |
| `css:deadwood` | a selector matching nothing in the built HTML |
| `resume` | a PDF that parses wrong or has no ink |

Three properties separate the ones that get trusted from the ones that get switched off.

**It has to name the thing.** A visual-regression harness here started as a zero-differing-pixel gate. That theory was wrong: a capture-then-immediately-compare run with no code change at all moved 11 of 180 screenshots, some of them on a page with no images, from font antialiasing alone. A gate that fires on 6% of clean runs gets disabled within a week.

The same runs showed zero computed-style changes. So the gate became computed styles and page height, with pixels reported but advisory. That change paid for itself immediately: a rule-stripper of mine deleted `.card-grid` along with `.card-grid--work`, live on eighteen pages. The pixel count said "some things differ." The computed-style diff said `display: grid -> block` and named the element.

**It has to be worth running.** `css:deadwood` is deliberately **not** in the default suite. It reports 48 unreachable selectors, which is a backlog rather than a regression. A gate that fails on the day you add it teaches everyone to pass `--no-verify`.

**It has to be executable, not advisory.** The privacy gate is a set of regular
expressions matched against the source, the built HTML, the feeds and the PDF
text — an explicit list of employer internals that must never ship:

```ruby
CONFIDENTIAL_PATTERNS = {
  "internal platform name"     => /<redacted product name>/i,
  "runtime topology"           => /<redacted deployment shape>/i,
  "internal scale description" => /<redacted volume claim>/i,
}
```

A paragraph in a contributing guide saying "please do not include employer
internals" is a suggestion. This is a policy, and it fails the build.

I know the exact strength of it, because **it caught this article.** The first
draft of the paragraph you are reading quoted the real pattern list, so the
literal string the rule exists to block appeared in a post explaining the rule.
The gate failed the build in four places — the source file, the rendered page,
the JSON feed and the Atom feed — and named the line in each:

```text
FAIL  _posts/…-agents-in-a-real-repository.md:130: internal platform name
FAIL  ./_site/writing/…/index.html:312: internal platform name
FAIL  ./_site/writing/feed.json:22: internal platform name
FAIL  ./_site/writing/feed.xml:135: internal platform name
```

That is the whole argument in one incident. I wrote the rule. I was writing
*about* the rule, with it fresh in mind, and I breached it anyway — and the two
feed hits are places I would never have thought to check by hand. A reviewer
skimming a 1,700-word essay for a product name would have had to be lucky. The
machine was not being clever; it was being exhaustive, which is the only thing
worth automating.

## The part that scales badly: everyone can open a PR now

Everything above is one person and one repository. The harder version is the one showing up in monorepos: designers, QA and product can now produce a working change, and they do. That is genuinely good — the person who noticed the problem can now describe the fix in code.

But it inverts an assumption the pull request was built on. Review was affordable because producing a change was expensive; the ratio held. Remove the cost from one side and the review queue is the only thing absorbing the difference, staffed by the same people as before.

The instinct is to add reviewers. That does not work, for the reason it never worked: review capacity is not fungible, and the reviewers who can catch the subtle problems are the ones already fully committed.

What does work is moving the *mechanical* half of review into the machine, so a human reviewer only ever sees changes that have already cleared everything a rule can decide. Concretely:

**Encode the review comments you repeat.** Any note you have written more than three times is a gate you have not built yet. Colour literals in the component layer were a recurring comment here; now they are `css:literals`, which fails the build and names the file and line.

**Make the boundaries executable.** Confidentiality, licensing, dependency policy, budget ceilings — these are exactly the rules a contributor unfamiliar with the codebase will breach, and exactly the rules an agent will breach confidently. They should be regular expressions and thresholds, not paragraphs.

**Publish the budget rather than the taste.** `css:budget` says the stylesheet must stay under 25 KB gzipped. That is arguable but unambiguous, and a contributor can check it before opening a PR. "Keep the CSS lean" cannot be checked by anyone.

**Let the gate teach.** Every gate in this repository carries a comment explaining the failure that produced it. That is not decoration — it is the only thing that stops a future contributor, human or otherwise, from deleting the rule because it looks arbitrary. The best documentation of a constraint is the scar that created it.

## What I would not do

**I would not gate on style an autoformatter can settle.** Anything a tool can fix should be fixed, not reported.

**I would not add a gate that cannot fail cleanly.** If the answer to a red build is "yes, that is expected sometimes", the gate is noise and will be treated as noise.

**I would not confuse a rules file with a control.** Instructions in a context file shape what an agent attempts. They do not constrain what it merges. Both are useful and only one of them is a boundary.

**And I would not conclude from any of this that review goes away.** Nothing above catches a wrong idea. Gates catch defects that have a decidable definition. Whether a partition scheme suits the query pattern, whether an abstraction earns its indirection, whether the feature should exist — that is the part of review worth protecting, and the entire point of automating the rest is to buy the attention to do it properly.

## The measure

The useful question about an agent-assisted repository is not how much it produced. It is what proportion of a merged change was checked by something other than a person deciding it looked fine.

On this repository that answer moved a long way in a week, and the reason is not that the agent got better. It is that three separate green suites turned out to be lying, and each lie became a gate. Producing code is cheap now. **Green is a claim, and claims are worth checking.**
