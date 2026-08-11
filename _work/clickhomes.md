---
title: "ClickHomes: a real-estate data spine"
hook: "PostgreSQL for truth, ClickHouse for speed, RESO as the only door in"
description: "A real-estate platform I build outside work: PostgreSQL for truth, ClickHouse for speed, a mandatory RESO pipeline, and 90+ versioned SQL migrations."
kind: production
order: 5
featured: false
role: "Founder & sole engineer — built on nights and weekends"
org: "ClickHomes (personal project)"
period: "2024 – present"
team: "One person"
scale: "Dual PostgreSQL / ClickHouse schema, 90+ versioned SQL migrations, running on Docker on a single VPS"
stack: [PostgreSQL, ClickHouse, Python, FastAPI, Pydantic, Celery, SQLAlchemy, Docker, Next.js]
metrics: [clickhomes_migrations]
tags: [postgres, clickhouse, ai-agents]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
live_url: "https://clickhomes.ai"
---

## Context

ClickHomes is a real-estate platform I build outside work, on nights and weekends. It is a personal project. I mention that up front because everything below only makes sense once you know that the engineering budget is my evenings and the operations budget is zero.

The domain problem is real, though, and it is a data problem before it is anything else. Real-estate listing data arrives from MLS feeds through the RESO standard — a defined schema for properties, members, offices, media and open houses. The feeds are large, they update constantly, and they are *someone else's* schema: field names, enumerations and nullability are decided by the source and change without asking. On top of that feed a platform needs two very different things at once. Transactional operations — saved searches, leads, agent activity, scoring — where constraints matter and the working set is small. And analytics — market statistics, price history, inventory trends over the full listing history — where scans are wide and the working set is everything.

Those two workloads want opposite physical designs. The interesting engineering here is what happens when you take that seriously instead of pretending one database can be both.

The second piece is the AI layer. The platform generates lead summaries, valuation checks and activity briefings, and one early decision shaped everything after it: those outputs are not chat. They are written into PostgreSQL as structured records with a versioned contract, so they can be queried, audited and joined to the operational data they describe.

## Constraints

**One person, in the evenings.** Every design decision is filtered through "will I understand this in three months, at eleven at night, after not touching it for a while." That eliminates a lot of clever architecture.

**No on-call, ever.** There is nobody to page. The system has to fail safe rather than fail loud: a broken load must stop and leave the last good state intact, because the alternative is a partially written gold table I discover a week later.

**A single VPS running Docker, at a fixed monthly cost.** No managed database, no managed queue, no managed anything. Both databases share a host, and disk is the resource that runs out first.

**The source schema is not mine.** RESO field definitions, enumerations and nullability come from the feed. When a provider changes something I find out because my transformer rejects rows, not because anyone told me. Updates also arrive as a mix of full and incremental payloads, so every load path must be idempotent — the same record will be presented many times and I cannot assume it changed.

**No meaningful business metrics, and I will not invent any.** The credible numbers here are engineering numbers: schema, migrations, invariants, failure behavior. Anything else would be decoration.

**Everything has to be re-runnable from a documented command,** not from memory. The runbook is written for a version of me who has forgotten how this works, because that version shows up regularly.

## Architecture

The core invariant is that there is exactly one way into the gold tables. No job, script or console session writes them directly.

```text
        MLS / RESO feed (someone else's schema)
                        |
                        v
        +-------------------------------+
        |  Connector                    |   auth, paging, watermark
        |  raw payload preserved        |
        +-------------------------------+
                        |
                        v
        +-------------------------------+
        |  Transformer                  |   RESO field mapping,
        |  Pydantic model per entity    |   enum normalization,
        |  reject -> quarantine         |   type coercion
        +-------------------------------+
                        |
                        v
        +-------------------------------+
        |  Gold Loader                  |   idempotent upsert on
        |  Pydantic validation again    |   (listing key, source ts)
        |  transactional per batch      |
        +-------------------------------+
                        |
            +-----------+------------+
            v                        v
     PostgreSQL (OLTP)        ClickHouse (OLAP)
     users, agents, leads,    listings history,
     lead scoring history,    market statistics,
     saved searches, event    price / inventory
     + behavioral tables,     trends — wide scans
     agent output records     over full history
            ^
            |
     +---------------------------+
     |  Agent layer              |   structured JSON contract,
     |  lead summaries           |   schema_version per row,
     |  valuation validation     |   deterministic fallback,
     |  activity briefings       |   written, not just displayed
     +---------------------------+

     Celery runs the ETL jobs on a schedule.
     90+ versioned SQL migrations cover both schemas.
     NO RAW BYPASS: nothing writes gold except the Gold Loader.
```

**Connector** talks to the feed: authentication, paging, checkpointing. It preserves the raw payload before anything interprets it, because if my mapping is wrong I want the original bytes to re-derive from.

**Transformer** is where RESO becomes my model — field mapping, enum normalization, type coercion, a Pydantic model per entity. Rows that fail validation go to quarantine with the reason attached rather than being dropped: you can fix what you kept.

**Gold Loader** validates again — yes, a second time — and performs an idempotent upsert keyed on the listing key plus the source timestamp. The second validation exists because the loader is the last boundary before data becomes durable, and a boundary you can bypass is not a boundary.

**PostgreSQL** holds everything transactional: users, agents, leads, saved searches, event and behavioral tables, lead scoring history, and the agent output records. **ClickHouse** holds listing history, market statistics and trend aggregates — the queries that scan a lot and mutate nothing.

**The agent layer** writes into PostgreSQL through a structured JSON contract carrying a `schema_version`. Every agent-produced record is a row you can query and audit. If the model call fails or the output does not validate, a deterministic fallback record is written instead and flagged as such. Nothing is silently absent.

**90+ SQL migrations** cover both schemas, versioned and applied in order. That number is not a boast; it is partly a symptom, and I say what of below.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost us |
|---|---|---|---|
| Two databases: PostgreSQL for OLTP, ClickHouse for OLAP | One PostgreSQL, with a columnar extension or careful indexing for the analytics | Market-statistics queries scan the full listing history. That is column-store work. Keeping it out of the transactional database means a heavy analytical query cannot stall a user request, which is the failure I most wanted to make structurally impossible. | Two schemas, two migration tracks, and no cross-store joins — every one becomes an application-level join I have to write and keep correct. A meaningful share of those 90+ migrations exists because one logical change touches two stores. |
| Mandatory pipeline: Connector → Transformer → Gold Loader, no raw bypass | Let some jobs write gold directly when the shape is simple | One code path means one place where RESO mapping and validation live. The moment a second path exists, validation drifts, and the drift is invisible until the data is wrong. | Onboarding a new feed is slower, and a one-field fix still requires a transformer change and a migration. There is a real temptation, at midnight, to just write the row. The rule exists precisely because I know I would. |
| Pydantic models at every load boundary, not only at the API edge | Validate once, at the edge | Bad rows are cheap to reject and expensive to un-write. Validating where data becomes durable is the only validation that actually protects the store. | Python-side validation costs CPU on bulk loads, which puts a ceiling on ingest throughput. I have not needed to raise it, but it is the first thing that would have to change if volume grew. |
| Agent output persisted as versioned structured records with fallbacks | Render model output in the UI and keep nothing | Lead summaries and valuation checks become part of the operational record: auditable, joinable, re-runnable. An answer nobody can review is an answer nobody should trust. | Every prompt change becomes a schema question. I version the contract and keep old readers working, which means carrying compatibility code for shapes I no longer produce. |
| Celery for ETL scheduling | Airflow | On a single VPS, Airflow's footprint is larger than the pipelines it would schedule, and Celery is already in the stack for background work. | No DAG-level lineage and no backfill UI. Re-run and backfill are documented runbook commands, and if the runbook is stale I am the one who suffers. The decision I am least sure about. |
| Explicit TTL on ClickHouse system log tables | Leave the defaults | On a disk-constrained host, ClickHouse's own query and part logs grew faster than the actual data. Left alone they would have filled the disk before the listings did. | A recurring chore that must be re-checked after every ClickHouse upgrade, because defaults come back. It is on the runbook for that reason. |
| Idempotent upsert keyed on (listing key, source timestamp) | Insert-and-deduplicate later | Feeds re-present the same record constantly, and a mix of full and incremental payloads means "did this change" is not answerable at read time. Idempotence at write time makes replay safe and a crashed job harmless. | It requires the source timestamp to be trustworthy. Where a provider's is not, I fall back to a content hash — slower, and a second path I had to build. |

## Results

The published number is the honest one: **90+ versioned SQL migrations** across the dual PostgreSQL and ClickHouse schema, counted from the migration files in the repository. I chose it as the headline because it is the only figure on this project that is externally checkable and that actually says something — it describes a schema evolved deliberately over time rather than reshaped by hand.

Beyond that, what this project demonstrates is structural rather than numeric, and I would rather say so than dress it up. The **no-raw-bypass invariant holds**: every row in a gold table went through Connector → Transformer → Gold Loader and was validated by a Pydantic model twice, so there is exactly one place to look when a field is wrong. **Loads are idempotent and replay is safe** — a crashed worker, a re-presented full payload and a manual re-run of yesterday's batch all converge to the same state, which is what makes a system operable by someone asleep most of the time it runs. And **agent output is durable and auditable**: every model-generated summary, valuation check and briefing is a row with a schema version and, where the model path failed, an explicit fallback marker.

There are no user or traffic numbers on this page. This is a personal project, and those numbers would not mean anything.

## Running it

**SLOs, adjusted for reality.** There is no availability SLO here in the sense a company would write one, and claiming otherwise would be dishonest. The contract I hold myself to has three parts: a failed load never leaves a partially written gold table; quarantine is reviewed on a schedule rather than when something breaks; and disk headroom never drops below a threshold that gives me a week to react.

**On-call shape: none.** Nobody gets paged. That absence is a design input, not a gap — it is why every job is transactional per batch, why every load is idempotent, and why the system is built to stop rather than struggle on. A pipeline that halts on a bad batch and waits for me is correct here. One that tries to be clever at 2am while I am asleep is not.

**Three failure modes, and what the runbook says:**

*Feed schema drift.* A provider changes an enumeration or a field's nullability and the transformer starts rejecting rows. Symptom: quarantine volume rising while the job still reports success — the right behavior, and the reason quarantine volume is monitored rather than a table I remember to look at. Runbook: read the reason codes to identify the field, update the Pydantic model and mapping, add a migration if the target column changes, then replay the quarantined batch. Replay is safe because the load is idempotent, which is the whole point of having made it so.

*Disk pressure from ClickHouse system logs.* Symptom: free space falling with no corresponding growth in listing data — a distinctive shape once you know to look for it. Runbook: check the system log tables *first*, before touching data retention. Apply or repair the TTL, drop the accumulated partitions, verify the TTL survived the last upgrade. Shrinking real data to reclaim space that logs are consuming is a mistake you only make once.

*A Celery worker dies mid-batch.* Symptom: a job that never reports completion and a watermark that has not advanced. Runbook: do nothing clever. Confirm the batch was transactional, then re-run it from the last checkpoint; the idempotent upsert makes the re-run a no-op for anything that already landed. What to guard against is my own instinct to start repairing rows by hand, which has never once been the right move.

## What I'd do differently

**I built the re-run and backfill path after the first production load, not before.** For the first few weeks, "how do I reload last Tuesday" was answered by writing a script each time. That is how you end up with three slightly different reload scripts and no confidence in any of them. Backfill is part of the pipeline, not an operational afterthought, and next time I will write it before the first row lands.

**Two databases on one host is a false economy, and I knew it when I did it.** The logical separation is right and I would make that call again. Putting both on a single VPS undermines much of the benefit: a heavy ClickHouse merge still competes with PostgreSQL for page cache and disk I/O, so the isolation is architectural rather than physical. Either the hosts should be separate, or I should have stayed on one store longer and split when the pain was real. I split early and paid for it with complexity I could not yet cash in.

**90+ migrations is partly a symptom.** A good share are consumer-visible schema changes that a view layer should have absorbed. If the gold tables had sat behind stable views from the start, most of those migrations would have been internal and invisible to the application. Instead the application reads the physical schema, so every physical change is a coordinated one. That is the design decision on this project I would most like back.
