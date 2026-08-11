---
title: "{{TITLE}}"
# 120–165 characters. Lead with the failure and the verified repair.
description: ""
date: {{DATE}}
type: tutorial
tags:
  - distributed-databases
toc: true
featured: false
level: intermediate
time_estimate: "~30 min hands-on"
what_youll_build: ""
prerequisites:
  - ""
  - ""
tested_on: "Exact product and version · environment · resource boundary"
# Three to five complete results, caveats, or failure boundaries.
key_takeaways:
  - ""
  - ""
  - ""
# ── optional ──────────────────────────────────────────────────────────────
# last_modified_at: {{DATE}}
# series: ""
# series_order: 1
# repo: "https://github.com/technobasant/..."
# work: ""
# seo_title: ""
---

## What failed

Open with the observed symptom, the expected result, and why the obvious repair
was misleading. State the answer early enough for a reader who only needs the
fix.

## Step 1 — Establish the boundary

Show the exact environment and the smallest reproducible setup. Keep prose
outside the code block and label files explicitly.

```text
exact command, configuration, or error
```
{: data-file="path/to/file"}

**Verify.** State the observable success condition, not merely that the command
returned zero.
{: .verify}

## Step 2 — Apply the repair

Explain why each load-bearing line exists before showing the final command.

<div class="callout callout--gotcha" markdown="1">
**Failure boundary.** Name the nearby case where this repair is unsafe or does
not apply.
</div>

## Step 3 — Prove the result

Verify data, state, or behavior from the consumer side. Include measured output
and distinguish the rig result from a production promise.

**Verify.** Give the exact query, status field, counter, or log line the reader
should see.
{: .verify}

## Failure modes

| Symptom | Cause | Repair |
| --- | --- | --- |
| Exact observed message | Root cause | Smallest safe correction |

## Clean up and operating consequence

Provide cleanup for the lab, then close with the operational rule that belongs
in a runbook, alert, or architecture review.
