---
title: "A warehouse alert is a state machine. Slack is only where it renders."
seo_title: "Slack alerts on lakehouse metrics: state, idempotency, Socket Mode"
description: "Slack alerts with Acknowledge and Resolve buttons on warehouse metrics: why the state and its write order come first, and where a receiver can actually live."
date: 2026-10-03 10:30:00 +0545
last_modified_at: 2026-10-03
type: essay
tags:
  - observability-slo
  - data-quality
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - alerting architecture
  - Slack interactivity
  - idempotent state transitions
  - data-quality monitoring
mentions:
  - Slack Socket Mode
  - Databricks Apps
  - Delta Lake
  - Lakebase Postgres
cover:
  base: "/assets/images/editorial-alert-state-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic: a scheduled detector and a Socket Mode receiver both write one alert-state row before Slack is called, with the lifecycle OK, ACTIVE, ACKNOWLEDGED, RESOLVED, CLOSED"
  caption: "Two processes, one transition function, one row per alert. Slack renders the state; it never holds it."
faq:
  - q: "Why can't a scheduled job handle Slack alert buttons on its own?"
    a: "Slack delivers a button click either to a public HTTPS Request URL or down a Socket Mode WebSocket, and expects an acknowledgement within 3 seconds. A cron job is not running at the moment of the click, so an alerting system with buttons needs a second, long-lived process to receive them."
  - q: "Should alert state be written before or after posting to Slack?"
    a: "Before. If the state write commits and Slack is down, the next run sees an ACTIVE alert with no message and posts it. If Slack is called first and the process dies before the state write, you have a message with buttons that point at state that does not exist, and a retry that posts it twice."
  - q: "How do you make Slack button clicks idempotent?"
    a: "Put the alert key and a state version in the button value. The handler compares the version with the stored row before transitioning. A stale click on a message someone already actioned gets an ephemeral reply instead of overwriting the newer state."
  - q: "Is Slack Socket Mode suitable for an internal alerting receiver?"
    a: "Yes, when the receiver cannot expose a public endpoint. Socket Mode opens an outbound WebSocket, so nothing arrives inbound. The costs are a long-lived connection to keep healthy and a process that runs, and is billed, continuously. Socket Mode apps cannot be listed in the public Slack Marketplace, which does not matter for an internal tool."
key_takeaways:
  - "A Slack alert with buttons needs two deployables: a scheduled, stateless detector and a long-lived receiver, because nothing in a cron job is listening when someone clicks."
  - "Every change to an alert, from a scheduled run, a click or an auto-resolve hours later, goes through one pure transition function and lands in one keyed row."
  - "Write state before calling Slack. The reverse order produces messages whose buttons point at state that does not exist, and duplicate posts on retry."
  - "The Slack message timestamp is state. Auto-resolve has no click to answer, so updating the original message requires the stored channel and ts."
  - "Noise control belongs in the state machine: consecutive breaches, cooldowns, acknowledgement, and a backfill that shows how often a rule would have fired before it is enabled."
---

A client asked for alerts on lakehouse metrics: freshness, row counts, data-quality ratios, the slow drifts that only exist once data has landed in tables. The request came with a picture of what they already used for service metrics, a Slack message with **Acknowledge**, **Resolve** and **Close** buttons, and one complaint about it. It fired so often that the critical alerts got lost.

The obvious design is a scheduled job that runs a query, compares the result with a threshold and posts to Slack. It works until the first person clicks a button. A cron job is not running at the moment of the click. It also misses the complaint: an alert that is just a query plus a post has no memory, so it cannot tell a new problem from the same problem reported for the fortieth time.

**Operating rule.** An alert is a state machine with an external user interface. Design the state, its key, and the order of writes first; the query is a parameter, and Slack is a renderer. Anything that can change an alert — a scheduled run, a click, an auto-resolve hours later — goes through one transition function and lands in one row.

This is a design I reviewed with a client and did not build or operate. The decisions are worth writing down because each one was forced by a platform fact, and the facts are checkable.

## The first click breaks the cron job

Slack delivers an interaction payload either to a public HTTPS Request URL or down a [Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode) WebSocket, and the app must [acknowledge it within 3 seconds](https://docs.slack.dev/interactivity/handling-user-interaction). Either way, something has to be running when the click arrives. That single fact turns one job into two deployables:

```text
DETECTOR  (scheduled, stateless)          RECEIVER  (long-lived)
  load config                               hold an outbound WebSocket to Slack
  compute the window                        on click: ack within 3 s
  query source tables  ← only reader        transition → write state
  evaluate → transition                     chat.update the original message
  write state, append history               never reads source tables
  post or update Slack
            \                                  /
             └──── one config, one state store, one lifecycle module ────┘
```

The split is also a permission boundary. The detector is the only component that reads source data, so it holds `SELECT` on the source schemas and write access only to its own state and history tables. The receiver never reads source data at all. Both import the same lifecycle module, so a status change looks identical whether a person or the scheduler caused it.

## Where the receiver can live

The client's platform was Databricks, and the obvious home for a small always-on process there is a [Databricks App](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts). The obvious way to use one does not work.

| Option | Why it fails, or survives | What it would have cost |
| --- | --- | --- |
| App as the Slack Request URL | [Apps cannot be made public](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/permissions); anonymous access and SSO bypass are not supported. Slack's unauthenticated POST meets a sign-in page, not the route. | A relay in front of the App, which is a second public service and defeats the reason for using the App. |
| Continuous serverless job as the listener | Serverless compute has a [7-day maximum runtime](https://docs.databricks.com/aws/en/compute/serverless/limitations); longer runs are terminated and not retried. | A listener that dies weekly, plus the supervisor you would have to build to restart it. |
| Function with a public URL (the fallback) | Works. No idle cost, stateless, public HTTPS by default. | A second platform, warehouse OAuth secrets stored and rotated in another account, a public inbound surface, and the state machine packaged twice. |
| **App holding a Socket Mode connection** (chosen) | Socket Mode is outbound: the app calls `apps.connections.open` and Slack pushes payloads down the connection it already holds. The auth proxy is never in the request path. | An App is [billed while it is running](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts), so this is standing cost; the exact figure was an open question at review. And a long-lived connection to keep healthy across redeploys. |
{: aria-label="Options considered for hosting the Slack interaction receiver" }

Socket Mode was the answer because it inverts the direction of the connection, not because it is newer. The constraint was "nothing may arrive inbound", and a receiver that dials out satisfies it by construction. The App also brings its own service principal, which is already the identity it needs to write alert state, so there is no credential to copy into another cloud. The trade-offs are the ones you accept with any stateful process: WebSockets drop, redeploys interrupt the connection briefly, and if egress is restricted, Slack's WebSocket domain has to be allowlisted. Socket Mode apps are also [not allowed in the public Slack Marketplace](https://docs.slack.dev/apis/events-api/using-socket-mode), which does not matter for an internal tool.

The function stayed in the design as a documented fallback, for the case where the standing cost turns out to be material. Keeping the receiver thin — ack, transition, update — is what makes that swap a deployment change rather than a rewrite.

## The state is the product

The lifecycle has five states, and most of the rules exist to keep two of them apart.

```text
              breach × consecutive_breaches
     OK ─────────────────────────────────────► ACTIVE
      ▲                                         │   │
      │                             [Acknowledge]   │ [Close]
      │                                         ▼   │
      │                                  ACKNOWLEDGED
      │                                         │   │
      │        healthy × recovery_runs          │   │ [Close]
      │   ┌─────────────────────────────────────┘   │
      │   │   (auto-resolve, from ACTIVE or ACKED)  │
      │   ▼                                         ▼
      └── RESOLVED ──[breach again]──► ACTIVE      CLOSED
                                                    │
                                     [healthy first, then may re-fire]
                                                    ▼
                                                    OK
```

The rules that need to be written down, because they are where the bugs live:

- **Acknowledged still evaluates.** Acknowledgement suppresses notification, not measurement.
- **Resolved re-fires** on the next breach as a new instance with a new message.
- **Closed does not re-fire** until the metric has been healthy again. That is the whole difference between Resolve and Close, and the reason to have both.
- **A manual transition wins** over an automatic one in the same run.
- **Illegal transitions are rejected and logged**, never quietly coerced into the nearest legal state.

The lifecycle is a pure function, `(prior_state, evaluation, config) → (new_state, action)`, with no I/O. That makes it exhaustively testable without a warehouse or a Slack workspace, which matters because it is the code most likely to be wrong. The state it produces lives in a small mutable table, one row per alert instance, with an append-only history beside it:

```sql
CREATE TABLE ops.alert_state (
  alert_id              STRING    NOT NULL,  -- stable id from config; never reused
  group_key             STRING    NOT NULL,  -- '' when the alert has no group_by
  status                STRING    NOT NULL,  -- OK | ACTIVE | ACKNOWLEDGED | RESOLVED | CLOSED
  state_version         BIGINT    NOT NULL,  -- bumped on every transition; carried by buttons
  consecutive_breaches  INT       NOT NULL,
  consecutive_healthy   INT       NOT NULL,
  current_value         DOUBLE,
  comparison_value      DOUBLE,
  first_breached_at     TIMESTAMP,
  last_notified_at      TIMESTAMP,              -- cooldown is computed from this
  slack_channel_id      STRING,                 -- needed to edit the message later
  slack_message_ts      STRING,
  acked_by              STRING,
  updated_at            TIMESTAMP NOT NULL
);
-- Logical key: (alert_id, group_key). Every MERGE names both columns explicitly.
```
{: data-file="alert_state.sql (sketch)" }

`group_by` is what makes the key two columns: an alert grouped by region is one independently tracked instance per region, each with its own lifecycle and its own message. Every merge names both key columns, because a loose predicate turns a single-row update into a table scan and a contention source.

The `state_version` column is what makes a click idempotent. Each button carries `alert_id|group_key|state_version`. If the version on the click no longer matches the row — someone else resolved it a minute ago — the handler answers that person privately instead of overwriting a newer state with an older intention. It is the same move as deduplicating on an idempotency key when an [agent's tool call can be delivered twice](/writing/agent-tools-on-the-users-machine/): a side effect against an external party has to be safe to receive twice.

## Write the state before you call Slack

The order of the last two steps in a run decides whether an outage loses alerts.

```text
tick
 ├─ compute the window (wall clock, aligned)
 ├─ query current and comparison windows      ── timeout, row cap
 ├─ evaluate → breached | healthy | error
 ├─ transition(prior, result) → new state + action
 ├─ MERGE alert_state; INSERT alert_history    ◄── commit here
 └─ action: post | update | suppress | digest  ◄── Slack, after the commit
       └─ on post: store channel + ts in alert_state

Slack down?  state is committed; next tick finds ACTIVE with no ts → posts it.
Reversed?    message exists, process dies before MERGE → buttons point at
             a state that does not exist; the retry posts a second message.
```

With state first, a Slack outage delays a notification and loses nothing. With Slack first, the failure produces the worst artefact an alerting system can have: a message nobody can resolve.

The receiver has the same rule with one more constraint: the 3-second acknowledgement. It acknowledges first, then writes state, then edits the message. It never blocks the acknowledgement on a database read.

That edit is also why the message timestamp is state rather than a log detail. Slack offers two ways to change a message after a click. A `response_url` can be used [up to five times within 30 minutes](https://docs.slack.dev/interactivity/handling-user-interaction) of the click; [`chat.update`](https://docs.slack.dev/reference/methods/chat.update) works on messages the app itself posted, given the channel and `ts`. Auto-resolve happens hours later, from the scheduled side, with no click to hang a `response_url` on. So the detector needs the stored channel and `ts`, and `chat.update` is the primary path.

Where the row lives was the one decision left deliberately reversible:

| Store | For | Against |
| --- | --- | --- |
| Delta table | No new infrastructure; queryable beside everything else. | Optimistic concurrency: a concurrent operation that adds files your operation read raises `ConcurrentAppendException`. [Row-level concurrency](https://docs.databricks.com/aws/en/optimizations/isolation/row-level-concurrency) needs Runtime 14.3 LTS or above, deletion vectors, and an unpartitioned table. |
| Lakebase Postgres | Row updates with ordinary transactional semantics. | Scale-to-zero means a cold resume, [typically a few hundred milliseconds](https://developers.databricks.com/docs/lakebase/configuration), with session context reset — a slice of the 3-second budget if the handler queried it before acknowledging. |
{: aria-label="Alert state store options" }

At tens of alerts, one scheduled writer and occasional clicks, contention is rare and a bounded retry absorbs it. Paying for a database to serve a handful of row updates an hour is the wrong trade. So the recommendation was a Delta table behind a store interface, with the Postgres implementation designed in and switched on only if write conflicts appear in the logs. My own research notes had worried that the cold resume would land inside the acknowledgement budget. The documented figure says it is a fraction of it — and the acknowledge-first rule makes it irrelevant either way.

## Time and noise belong to the state machine too

Most false alerts in systems like this come from time, not thresholds. A scheduler is not a clock: runs slip. So a window is computed from wall-clock time and aligned to its own size, never as "now minus the schedule interval". With a 15-minute window and a 5-minute offset, a run at 08:07 evaluates `[07:45, 08:00)`, and a run that slips to 08:11 evaluates exactly the same window. The offset has to exceed real ingestion lag, because a partially loaded window looks identical to a collapse. All arithmetic is in UTC, so an hourly schedule is not skipped or doubled twice a year. A metric with a weekly rhythm compares with the same window last week, not the previous one, or Monday morning alarms against Sunday night forever.

The client's stated pain was volume, so noise control is requirements, not polish, and each mechanism is a field in the state:

- **Consecutive breaches** before an alert fires — the cheapest defence against a transient spike.
- **A cooldown** inside which an active alert updates state but stays quiet.
- **Acknowledgement suppresses** re-notification once someone owns the problem.
- **Low-severity digests**: one scheduled summary instead of many messages.
- **Auto-resolve** after a run of healthy evaluations, so the channel reflects reality.
- **Backfill before enable.** The same evaluation code runs over historical windows and reports how often a proposed rule *would have* fired. A rule that would have paged every day of the last month does not get switched on.

Alert definitions are config, reviewed in a pull request, with structured filters rendered as parameterised SQL. An illustrative definition, with an invented table:

```yaml
id: orders_per_hour_by_region      # stable; the dedupe key
severity: P3
source: { catalog: analytics, schema: sales, table: orders }
metric:
  expression: count(*)
  timestamp_column: created_at
  group_by: [region]
window: { size: 1h, offset: 15m, compare_to: same_time_last_week }
condition: { type: delta_pct, operator: lt, value: -30, consecutive_breaches: 2 }
notify: { channel: "#data-alerts", cooldown: 2h, auto_resolve: true, digest: true }
```
{: data-file="config/alerts/orders_per_hour_by_region.yaml (illustrative)" }

A model may help write that file at design time. It does not write SQL inside a scheduled run at three in the morning. Non-determinism is the one property an alerting path cannot have.

The chart that goes with each alert is a smaller example of checking a platform fact before designing around it. Slack's old `files.upload` method lost access for new apps on 16 May 2024 and was [sunset on 12 November 2025](https://docs.slack.dev/changelog/2024-04-a-better-way-to-upload-files-is-here-to-stay); uploads now go through `files.getUploadURLExternal`, a direct POST of the bytes, and `files.completeUploadExternal`. My research notes had an earlier date. It made no difference to a new build, but it is why every date in this essay was re-checked against the source. One detail does change behaviour: completing an upload without a channel leaves the file [hosted but private](https://docs.slack.dev/messaging/working-with-files), shared nowhere, which looks exactly like a broken image.

<div class="callout callout--note" markdown="1">
**Boundary.** This is a design I wrote and reviewed with a client; it was not built while I was involved, and I have not operated it. There are no measured numbers here. The platform behaviour — the 3-second acknowledgement, `response_url` limits, Socket Mode, the App access model, the serverless runtime cap, row-level concurrency, Lakebase resume, the `files.upload` sunset — is cited to vendor documentation as of October 2026. The table names and the alert definition are illustrative, not the client's.
</div>

## What I would check before writing code

Three answers change the build, and none of them is about code. The standing cost of an always-on receiver decides between the App and the function. The real ingestion lag on the target tables sets the window offset, and an offset chosen by guess is a false alert waiting for a slow day. And the question of who may acknowledge and close decides whether the receiver needs an authorisation check of its own on top of Slack membership.

Everything else follows from the first decision. Once the alert is a row with a key, a version and a lifecycle, the transport is replaceable, the noise rules have somewhere to live, and an outage delays a message instead of losing one.

## Frequently asked questions

### Why can't a scheduled job handle Slack alert buttons on its own?

Slack delivers a button click either to a public HTTPS Request URL or down a Socket Mode WebSocket, and expects an acknowledgement within 3 seconds. A cron job is not running at the moment of the click, so an alerting system with buttons needs a second, long-lived process to receive them.

### Should alert state be written before or after posting to Slack?

Before. If the state write commits and Slack is down, the next run sees an ACTIVE alert with no message and posts it. If Slack is called first and the process dies before the state write, you have a message with buttons that point at state that does not exist, and a retry that posts it twice.

### How do you make Slack button clicks idempotent?

Put the alert key and a state version in the button value. The handler compares the version with the stored row before transitioning. A stale click on a message someone already actioned gets an ephemeral reply instead of overwriting the newer state.

### Is Slack Socket Mode suitable for an internal alerting receiver?

Yes, when the receiver cannot expose a public endpoint. Socket Mode opens an outbound WebSocket, so nothing arrives inbound. The costs are a long-lived connection to keep healthy and a process that runs, and is billed, continuously. Socket Mode apps cannot be listed in the public Slack Marketplace, which does not matter for an internal tool.

The same discipline — state and idempotency before transport — runs through [running agent tools on a user's machine](/writing/agent-tools-on-the-users-machine/). More on what to measure and what should page someone in [Observability & SLOs](/writing/tags/observability-slo/).
