---
title: "Wrong data and missing data are caught by different checks"
seo_title: "Data quality checks in dbt: nine defects, block vs quarantine, measured"
description: "A month of deliveries with nine defects. Row tests caught wrong values; only control totals, volume and platform share saw rows that never arrived."
date: 2026-10-18 18:45:00 +0545
last_modified_at: 2026-10-18
type: essay
pillar: data-platforms
series: data-stack-lab
series_order: 3
tags:
  - data-quality
  - data-modeling
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - data quality
  - data testing
  - data contracts
  - quarantine
mentions:
  - dbt
  - DuckDB
  - data-stack-lab
cover:
  base: "/assets/images/editorial-data-quality-defects-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Nine defects delivered over a month and the check that caught each: deduplication absorbed a duplicate file; row tests caught nulls, local time, a new event type and orphan keys; the contract caught a renamed column; manifest, volume and platform share caught the three defects where rows were missing"
  caption: "Three of the nine defects left no bad row to find. Only checks on the day as a whole saw them."
faq:
  - q: "What is the difference between data tests and data quality checks on volume?"
    a: "Row tests (not null, unique, relationships, accepted values) find bad values in rows that arrived. They cannot see rows that never arrived. In a month of deliveries with nine defects, a truncated upload, a platform that stopped sending and a third of a day arriving late left no bad rows at all; only control totals against the producer's manifest, a volume band and a per-platform share caught them."
  - q: "Should bad data be blocked or quarantined?"
    a: "It is a trade. Blocking the whole day on any failure let 0 of 3,198 bad rows through and held 19,545 good rows for a person. Quarantining only the failing rows let 87 bad rows through and held 12,865 good rows. Missing-data failures still have to hold the whole day under either policy."
  - q: "Why does a unique test on raw events fail every day?"
    a: "Because event delivery is at least once. On an ordinary day 0.8% of events arrived twice, some across midnight. Deduplicate first, in the model, and test uniqueness on what is left; a test that fails every day is soon ignored."
key_takeaways:
  - "Row tests find wrong values in rows that arrived; rows that never arrived need control totals, volume and per-group shares."
  - "A platform going silent moved total volume 19%, inside a 30% band, and moved its own share from about 18% to zero."
  - "A fixed volume band is a coin toss at its edge: the same late third was caught in one run and missed by 12 rows in the other."
  - "Blocking let 0 of 3,198 bad rows through and held 19,545 good ones; quarantine let 87 through and held 12,865."
  - "Rule checks cannot tell a defect from a product change: a legitimate new event type held a day or set aside 92 good rows."
---

Most data-quality checks in a dbt project are row tests: not null, unique, relationships, accepted values. They answer one question well: is anything wrong with the rows that arrived? Some of the most expensive data incidents are rows that never arrived: an upload that stopped halfway, a client that stopped sending, a file that came two days late. A row test has nothing to look at.

I delivered a month of daily event files with one realistic defect every three days, checked them in dbt, and scored two policies against what each defect actually did to each row. Three of the nine defects left no bad row to find. Only checks on the day as a whole, against what the producer said it sent and what earlier days looked like, caught them.

**Operating rule.** Test rows for wrong values, and test the day for missing ones: control totals against the producer's manifest, volume against recent accepted days, and the share of each group that can go silent on its own. Deduplicate before testing uniqueness, and decide per check whether a failure blocks the day or quarantines rows.

The code is the data-quality project in [data-stack-lab](https://github.com/technobasant/data-stack-lab/tree/main/quality), on the same synthetic SaaS data as the [dbt](/writing/type-1-dimension-revenue-wrong-plan/) and [Airflow](/writing/airflow-3-daily-no-data-interval/) projects. Every figure is in its [MEASUREMENTS.md](https://github.com/technobasant/data-stack-lab/blob/main/MEASUREMENTS.md#data-quality-nine-defects-two-policies), and CI re-runs the month and fails if one number moves.

## Nine defects, three layers

August was delivered clean and accepted, to give the checks a baseline. September's defects, one every three days:

| Defect | What it did | Caught by | Block | Quarantine |
|---|---|---|---|---|
| A file delivered twice | 6,274 rows for 3,113 events | nothing failed; deduplication absorbed it, a redelivery warning fired | promoted | promoted |
| Nulls in a key | 147 of 2,963 events with no account | `not_null` | held | 147 quarantined |
| A renamed column | `event_type` became `type` | the enforced contract | held | held |
| An upload cut at 40% | 1,709 rows never delivered | manifest, volume | held | held |
| Local time labelled UTC | all 2,992 event times shifted five hours ahead | event after its arrival | held | **87 bad rows promoted** |
| A new event type | 92 events of a legitimate new type | `accepted_values` | held | **92 good rows quarantined** |
| A platform goes silent | 613 iOS events never sent | per-platform share | held | held |
| Orphan keys | 59 events with an unknown account | `relationships` | held | 59 quarantined |
| A third arrives late | 1,040 events two days late | volume, in one run of two | **promoted** | held |
{: aria-label="Nine data defects, the check that caught each, and what each policy did" }

The checks sit in three layers. The batch model selects its columns by name under an enforced contract, so a renamed column fails the build before anything else runs. Row tests look for wrong values. Batch tests look at the day as a whole: its volume against the median of the last seven accepted days, each platform's share against its recent share, and each file's row count against the manifest the producer sent with it. No check fired on any of the twenty clean days.

## A unique test on raw events fails every day

The first version of the checks failed on every single day, clean ones included. Event delivery is at least once: on an ordinary day 0.8% of events arrived twice, some across midnight. A `unique` test on what arrived fired daily, and a check that fires daily is a check nobody reads.

The model now deduplicates first: the first delivery of each event wins, and events accepted on an earlier day are dropped. Uniqueness is tested on what is left, where a failure would mean the deduplication is broken. The duplicate file stopped being an incident. Deduplication absorbed it, and the only signal was a warning that redeliveries had jumped from under 1% to half the day, worth a look, not a stop.

## Missing rows leave nothing for a row test

The truncated upload delivered 1,145 perfectly valid rows. The silent platform delivered 2,613 perfectly valid rows. On the late day, 2,092 valid rows arrived and 1,040 were still on their way. Not one row test could fail, because every row that arrived was correct.

Three batch checks saw them, each for a different reason:

- **The manifest.** The producer declared how many rows each file held. The truncated file held 40% of them. This is the only check that knows what *should* have arrived, and it costs one number per file.
- **Per-platform share.** iOS stopping cut the day's volume by 19%, inside the 30% band. It moved iOS's own share from about 18% to zero. A total hides a loss in one group that the group's share shows.
- **Volume.** It caught the truncated upload easily. The late third was harder: 29.6% below one policy's baseline and 30.2% below the other's, because the two policies had accepted different earlier days. The band missed it by 12 rows in one run and caught it in the other.

That last result is the honest summary of fixed thresholds. Whatever band you pick, some real loss sits just inside it. A manifest from the producer, where one can be had, removes the guesswork.

## Block or quarantine

Under **block**, any failing check holds the whole day for a person. Under **quarantine**, rows that fail a row test are set aside and the rest of the day is promoted; contract and batch failures still hold the day.

| Over the month | Block | Quarantine |
|---|---:|---:|
| Bad rows promoted, of 3,198 | 0 | 87 |
| Good rows not promoted | 19,545 | 12,865 |
| Days held for a person | 8 | 5 |
{: aria-label="What blocking and quarantining let through and held back over a month" }

Quarantine kept 6,680 more good rows flowing and let 87 bad ones through. Those 87 were timestamp-shifted events that had already arrived more than five hours late, so the shift did not put them in the future, and the check that catches local time written as UTC could not see them.

Neither policy handled the new event type well. It was a legitimate product change. Blocking held a good day; quarantine set aside the 92 good rows of the new type. A rule check cannot tell a defect from a change. The fix is a contract process, so the new value is announced and added before it ships, not a looser check.

<div class="callout callout--note" markdown="1">
**Boundary.** Synthetic events with no weekly or seasonal pattern, so the volume and share bands see a flatter baseline than real traffic would, and the zero false alarms on clean days is optimistic. One defect per day, applied whole. A held day is never repaired and re-released in the harness; in real operation a person would do that. DuckDB and dbt Core on one machine.
</div>

## Checks for a daily delivery

- Ask the producer for a manifest per file, and compare row counts before anything else.
- Deduplicate first, then test uniqueness on the result.
- Row tests for wrong values: keys present, keys that exist, allowed values, times that make sense against arrival.
- Batch tests for missing rows: volume against recent accepted days, and the share of each group that can fail on its own (platform, region, source).
- Decide per check whether a failure holds the day or quarantines rows, and count both what gets through and what is held back.
- Treat new values as contract changes with a process, not as defects.

## Frequently asked questions

### What is the difference between data tests and data quality checks on volume?

Row tests (not null, unique, relationships, accepted values) find bad values in rows that arrived. They cannot see rows that never arrived. In a month of deliveries with nine defects, a truncated upload, a platform that stopped sending and a third of a day arriving late left no bad rows at all; only control totals against the producer's manifest, a volume band and a per-platform share caught them.

### Should bad data be blocked or quarantined?

It is a trade. Blocking the whole day on any failure let 0 of 3,198 bad rows through and held 19,545 good rows for a person. Quarantining only the failing rows let 87 bad rows through and held 12,865 good rows. Missing-data failures still have to hold the whole day under either policy.

### Why does a unique test on raw events fail every day?

Because event delivery is at least once. On an ordinary day 0.8% of events arrived twice, some across midnight. Deduplicate first, in the model, and test uniqueness on what is left; a test that fails every day is soon ignored.

The harness, the dbt checks and the results are in [data-stack-lab](https://github.com/technobasant/data-stack-lab/tree/main/quality), with the projects together in [the case study](/work/data-stack-lab/). Contracts between teams are the subject of [the data contracts post](/writing/json-schema-compatibility-data-contracts/). More on [data quality](/writing/tags/data-quality/).
