---
title: "Erasing one person rewrote 31.8 million rows. With their e-mail in one table, 60,000."
seo_title: "GDPR erasure cost: personal data in facts vs one identity table"
description: "Nulling one person's e-mail rewrote all 31.85 million rows of an event table that copied it into each row. In one user table, the same erasure rewrote 60,000."
date: 2026-10-20 03:00:00 +0545
last_modified_at: 2026-10-20
type: essay
pillar: data-platforms
tags:
  - databricks
  - data-modeling
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - data modelling
  - right to erasure
  - Delta Lake
  - personal data
mentions:
  - Databricks
  - UniForm
  - GDPR
  - data-platform-architecture
cover:
  base: "/assets/images/editorial-erasure-model-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Erasing one person's 551 events on Delta with UniForm: with e-mail and name copied into every event row, all 3 files and 31,849,449 rows were rewritten in 7.6 seconds; with them only in a 60,000-row user table, 1 file and 59,999 rows in 1.1 seconds"
  caption: "The delete statement was the same. The model decided what it cost."
faq:
  - q: "How does the data model affect the cost of GDPR erasure?"
    a: "An erasure rewrites every file that holds the person's rows. In a test on Databricks, with one person's e-mail and name copied into every event row, nulling them rewrote all 31,849,449 other rows of a 31.85-million-row table. With them kept only in a 60,000-row user table that the events reference by key, the same erasure rewrote 59,999 rows."
  - q: "Do deletion vectors make erasure cheap?"
    a: "They make the delete cheap and defer the rewrite. On plain Delta the update wrote three deletion vectors and rewrote nothing, but an erasure is not done until the old data is purged, and the purge then rewrote all three files. On UniForm tables, deletion vectors are not allowed at all."
  - q: "Where should personal data live in a lakehouse model?"
    a: "In the raw layer, staging and one identity table per source. Facts and marts carry the person's key, not their e-mail or name, and a CI check fails the build if any mart column is classified personal. Teams that need an identity next to a figure join through a restricted view."
key_takeaways:
  - "With one person's e-mail and name copied into every event row, erasing them rewrote all 31,849,449 other rows of the table."
  - "With the identity kept in one 60,000-row user table, the same erasure rewrote 59,999 rows and took 1.1 seconds instead of 7.6."
  - "Deletion vectors deferred the rewrite to the purge erasure needs; on UniForm tables they are not allowed at all."
  - "In a table laid out by time, every user's rows are in every file, so any per-person change rewrites the whole table."
  - "Keep personal columns in one identity table per source, give facts keys, and fail the build when a mart column is classified personal."
---

A right-to-erasure process is usually designed as a job: find the person, delete or null their data, prove it is gone. The job is the same however the data is modelled. What it costs is not, and the difference is decided long before the first request, by where the model copies an e-mail address.

I measured it for the data model of a B2B SaaS company in [data-platform-architecture](/work/data-platform-architecture/), a scenario common across the industry, whose tables use Delta with UniForm so other engines can read them as Iceberg.

**Operating rule.** Keep personal columns in the raw layer, staging and one identity table per source. Facts and marts carry the person's key, never their identity, and a CI check fails the build if any mart column is classified personal. Anyone who needs a name next to a figure joins through one restricted view.

## The test

The company's product events at today's scale, 31.85 million rows for 60,000 users (the lab copy's 31.5 million plus the day the cost test appended), on Databricks SQL 2026.39, built three ways:

- **Identity in every event.** The events with each user's e-mail and name copied into every row, as a convenient wide table would have them. Delta with UniForm, which allows no deletion vectors.
- **The same on plain Delta**, with deletion vectors on.
- **Identity in one table.** The events carry `user_id`; e-mail and name live in a 60,000-row user table. UniForm.

One user, with 551 events, asks to be erased. Each table gets the same statement, `UPDATE … SET email = NULL, full_name = NULL WHERE user_id = 7`, and the table history says what it rewrote.

## What it rewrote

| Where the identity lived | Files rewritten | Rows rewritten | Time |
|---|---:|---:|---:|
| Copied into every event row (UniForm) | 3 of 3 | **31,849,449** | 7.6 s |
| The same, plain Delta with deletion vectors | 0, then 3 of 3 at the purge | deferred to the purge | 3.8 s, plus the purge |
| One user table of 60,000 rows | 1 of 1 | **59,999** | 1.1 s |
{: aria-label="What erasing one person rewrote, by where the model kept their identity" }

To change 551 rows, the wide table rewrote all of its data. The user table rewrote one small file.

## Why every file

The events are written in the order they happen, and any one user's events are spread across the whole period. So every data file holds some of every user's rows, and a change to one person's rows touches every file. Without deletion vectors, a touched file is rewritten in full. Smaller files would not help; the person is in all of them.

Deletion vectors do not change the arithmetic, only the timing. The update marked rows deleted and wrote the new versions, rewriting nothing. But an erasure is not done while the old values are still in the files (time travel returns them, as [the erasure write-up](/writing/delta-delete-is-not-erasure/) showed), so a purge has to follow, and the purge rewrote all three files. On UniForm the question does not arise: Databricks refused to create the table with deletion vectors.

Today that is a few seconds a week. At 36 months the company's event table holds about 3.8 billion rows, and with identities in every row, every weekly erasure batch would rewrite all of it. With identities in one table, the cost stays the size of the user table.

## What it means for the model

- **Identity tables, one per source.** The product's users, the billing system's customers. They are the only modelled tables with personal columns, besides `raw` and `staging`.
- **Facts carry keys.** `user_id` and `account_id`, not e-mail or name. Once the person's identity rows are erased, nothing in the platform links the key back to them. Whether the remaining key counts as anonymous is for the data protection officer to confirm, and belongs in the data processing agreement.
- **A check, not a convention.** Every column carries a classification from its contract, and CI fails the build when a mart column is classified personal. Conventions erode the first time someone adds a convenient join.
- **One restricted view** for the team that genuinely needs identities, customer success here, granted to that role and recorded in the access audit like every other read.

A tokenisation vault, which replaces identities with tokens at ingestion, isolates them further, at the price of a service that has to be available whenever data lands. For a team of two to four, one identity table per source gets most of the benefit.

<div class="callout callout--note" markdown="1">
**Boundary.** One table of 31.85 million rows in three large files, on Databricks Free Edition; one person at a time. A batch of erasures costs the same as one in the wide table, since every file is rewritten anyway. In a table clustered by user rather than by time, a person's rows would sit in fewer files, but the company's tables are clustered for the reads that matter, by date and account. The decision record is [0017 in the repository](https://github.com/technobasant/data-platform-architecture/blob/main/decisions/0017-personal-data-in-one-place.md).
</div>

## Checks for a model that has to support erasure

- List every table with a personal column; the list should be short and its tables small.
- Give facts the person's key, not their identity, and keep identities in one table per source.
- Classify every column in its contract, and fail the build when a mart column is classified personal.
- Measure what one erasure rewrites, on your table format, before the first request arrives.
- Remember that time travel and deletion vectors keep the old values until a purge and the retention have passed.

## Frequently asked questions

### How does the data model affect the cost of GDPR erasure?

An erasure rewrites every file that holds the person's rows. In a test on Databricks, with one person's e-mail and name copied into every event row, nulling them rewrote all 31,849,449 other rows of a 31.85-million-row table. With them kept only in a 60,000-row user table that the events reference by key, the same erasure rewrote 59,999 rows.

### Do deletion vectors make erasure cheap?

They make the delete cheap and defer the rewrite. On plain Delta the update wrote three deletion vectors and rewrote nothing, but an erasure is not done until the old data is purged, and the purge then rewrote all three files. On UniForm tables, deletion vectors are not allowed at all.

### Where should personal data live in a lakehouse model?

In the raw layer, staging and one identity table per source. Facts and marts carry the person's key, not their e-mail or name, and a CI check fails the build if any mart column is classified personal. Teams that need an identity next to a figure join through a restricted view.

The runner and its results are in [data-platform-architecture](https://github.com/technobasant/data-platform-architecture/tree/main/poc/databricks), with the data model in its [data model document](https://github.com/technobasant/data-platform-architecture/blob/main/docs/06-data-model.md). More on [Databricks](/writing/tags/databricks/).
