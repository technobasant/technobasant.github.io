---
title: "realtime-ml: a fraud model whose leakage, skew and label delay are measured"
seo_title: "realtime-ml — Real-Time Fraud Scoring with Point-in-Time Features"
hook: "Most real-time models fail before they are served: in a join that reads the future, a backfill that disagrees with the stream, labels that arrive weeks late"
description: "Open-source real-time fraud scoring on Kafka, Feast and MLflow, built to measure what leakage, skew, late labels and drift each cost, not just avoid them."
date: 2026-10-14
last_modified_at: 2026-10-14
kind: open-source
pillar: ai-systems
related: [evalproof, streaming-platform, dataset-registry]
order: 4
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "Generated payments (fixed seed): 874,446 transactions over 90 days, 0.80% fraud; a live stack of Kafka, Redis, Postgres, MLflow and Prometheus, one container per service"
problem: "A real-time model can pass every offline check and still fail: the training join reads the future, the backfill computes a feature differently from the stream, labels arrive weeks late, and the drift monitor fires on the calendar instead of the drift."
decision: "Build each failure on purpose next to the correct version — naive and point-in-time joins, SQL and stream features, mature and immature labels, four drift monitors — on generated data (fixed seed), and measure the difference instead of asserting it."
repo: "https://github.com/technobasant/realtime-ml"
flow: realtime-ml
cover:
  base: "/assets/images/editorial-realtime-ml-v1"
  width: 1600
  height: 900
  alt: "Slope chart: a naively joined fraud model falls from 0.746 AUC-PR on validation to 0.363 on the next two weeks, while the point-in-time model rises from 0.681 to 0.941"
  caption: "Only the training join differs, and the model that won validation scored 0.363 AUC-PR on the next two weeks against 0.941 for the one it beat."
  link: "/writing/realtime-ml-point-in-time-leakage/"
metrics: [rtml_leakage, rtml_cost_saved, rtml_parity, rtml_drift_psi]
stack: [Python, "Apache Kafka", Feast, Redis, DuckDB, LightGBM, MLflow, FastAPI, PostgreSQL, Prometheus, evalproof]
tags: [applied-ml, data-quality]
image: /assets/og/og-streaming.png
image_alt: "Kafka and streaming — real-time fraud scoring with measured leakage, skew and drift"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

[realtime-ml](https://github.com/technobasant/realtime-ml) scores payments for an online homewares retailer, a standard e-commerce scenario, as they happen. Payments flow through Kafka into a stream processor that keeps window features — card counts per device in the last hour, purchases per customer in the last day — in Feast's online store. A FastAPI service scores each payment with the champion model, runs the challenger in shadow, and logs both. A gate promotes the challenger only on a statistically significant, paired improvement, and a monitor exports drift signals to Prometheus.

None of that is unusual, and none of it was the point. The ways a model like this goes wrong mostly happen before it is served, and they are quiet: the offline numbers look fine. So each failure is built here on purpose, beside the correct version, and the difference between them is the measurement. The finding I did not expect is written up in [Validation picked the fraud model that had read the future](/writing/realtime-ml-point-in-time-leakage/).

## Constraints

The data is generated, from a fixed-seed generator: 8,000 customers, 90 days, card-testing bursts, account takeovers, lone anomalies, and chargebacks that arrive after a lognormal delay with a median of seven days — 15% of frauds are never reported at all. That makes every absolute score a property of the generator. The comparisons are the findings: the same rows, the same model, one thing changed.

The live stack is Kafka 4.3.1 in KRaft mode, Redis, Postgres, an MLflow server and Prometheus, each a container on one Docker VM of 8 CPUs and 11.7 GiB. All containers share one host, so latency figures contain no real network hops. Kafka runs one broker and one partition, because the log's guarantees are not what is under test.

## Architecture

The offline side writes every window feature into Feast from SQL window functions in DuckDB, joins it point-in-time for training, trains LightGBM, and registers champion and challenger in MLflow. The online side recomputes the same features in a per-entity state machine over the Kafka stream and pushes them into Redis, where the API reads them at scoring time. Every prediction, with the features it was served, lands in a Postgres log that feeds the gate and the drift monitor.

Two implementations of each feature is deliberate. A single shared function would hide skew instead of testing for it; two implementations with a parity test make skew a measured quantity.

## In the code

This is the decision behind the leakage result. Both training sets are built from the same rows; the point-in-time join asks Feast for each payment's features one millisecond before that payment, while the naive one hands every row the entity's latest state as of a single pull date, and that one difference is 0.941 against 0.363 AUC-PR on the two weeks that followed.

```python
# A transaction is scored before its own event reaches the feature pipeline. Offline, the
# same thing is expressed by asking for features one millisecond before the event.
SCORE_OFFSET = pd.Timedelta(milliseconds=1)
# …
def pit_join(store: FeatureStore, rows: pd.DataFrame) -> pd.DataFrame:
    """Point-in-time features for ``rows``, through Feast's historical retrieval."""
    ent = rows[["txn_id", "customer_id", "device_id"]].copy()
    ent["event_timestamp"] = rows["ts"] - SCORE_OFFSET
    feats = store.get_historical_features(entity_df=ent, features=FEATURE_REFS).to_df()
    feats = feats.drop(columns=["customer_id", "device_id", "event_timestamp"])
    out = rows.merge(feats, on="txn_id", how="left", validate="one_to_one")
    return out.sort_values("ts").reset_index(drop=True)


def naive(rows: pd.DataFrame, tables: dict[str, pd.DataFrame], as_of: pd.Timestamp) -> pd.DataFrame:
    return naive_join(rows, tables, as_of).sort_values("ts").reset_index(drop=True)
```
{: data-file="src/rtml/dataset.py" }

The full file, including the label view a model is allowed to see at training time, is [src/rtml/dataset.py](https://github.com/technobasant/realtime-ml/blob/main/src/rtml/dataset.py).

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Train with features as of 1 ms before each transaction | Join each entity's latest row | The latest row includes the rest of the fraud burst and the transaction's own chargeback | The honest model *looks* worse on validation, scored with the labels known on the day |
| Every window feature written twice, SQL and stream | One shared feature function | Two implementations make skew measurable | Twice the feature code, and a parity test to maintain |
| Score with the state after the entity's previous event; no TTL on feature views | Re-expire windows at read time | Feast applies a view's TTL offline but not on Redis reads, which would build skew into the store | A customer quiet for three days still shows that day's one-hour count; the model is told the window's age instead |
| Train on rows at least 14 days old | Train on everything with the labels known on the day | Immature labels ruined the threshold | 31% fewer training rows than using everything |
| Promote only on a significant paired saving within a 2 ms p99 | Promote the higher number | Shadow traffic is paired; the higher number promotes noise | An improvement smaller than this one would have to wait for chargebacks to mature before it clears the bar |
| Hour-matched PSI, calendar-trending features excluded | PSI against the training distribution, all features | The textbook recipe fired on evenings and on the calendar | No label-free monitor caught the tactics drift; that is reported, not tuned away |

## Results

On the two weeks after training, with true labels, the champion reached AUC-PR 0.941 and recall 0.954 at precision 0.668, flagging 1.2% of payments and saving 82.5% of fraud cost against approving everything. A hand-written rule saved 20.7%.

The leakage measurement is the one that changed how I would review a training pipeline. With features joined naively, the model scored 0.746 on validation against 0.681 for the point-in-time join — and then 0.363 against 0.941 on the following two weeks. Every naive training row took its customer features from a row timestamped after the transaction.

The SQL backfill and the stream state machine agreed on 100% of 68,273 replayed rows. A planted defect changed 16.84% of one feature and was caught at the feature level, while AUC-PR, flag rate and cost saving were unchanged to three decimals — a model-level parity check would have passed it. On the running stack, 99.905% of 9,500 live requests were served exactly the point-in-time features; all nine disagreements were stream lag at replay speed.

Scoring took a server-side p50 of 0.54–0.73 ms and a p99 of 3.5–4.3 ms at 25, 50 and 100 requests per second, with no errors. Offline, the gate promoted the device-feature model at a saving of $0.109 per transaction (95% CI 0.085 to 0.137) over 68,016 paired shadow transactions, and refused a reseeded copy, an underfit model, and an oversized one that beat only the weaker champion. Live, it promoted the same model and the API was serving it 6.1 seconds later.

## What the measurements refused to show

**Drift monitoring does not work well here, and that is the finding.** When fraudsters slowed down and stayed closer to normal, recall fell 3 to 9 points. Feature PSI never fired on that change, and neither did score PSI: fraud is 0.8% of traffic, and when it changes tactics the population barely moves. The flag rate caught all five drifts in a median 48 hours at a threshold that also fired on 17.2% of drift-free windows. Recall on the chargebacks that had arrived tracked the real damage and was about 300 hours late.

**The client-side latency tail is not explained.** Inside the API, p99 stayed under 5 ms. The client saw p99 of up to 257 ms at 100 requests per second over the same requests. Moving the Kafka producer off the replay's event loop removed the largest cause; at least one more remains between the two timers.

**Calibration is good on average and wrong where it matters.** The expected calibration error is 0.002 because nearly every score is near zero and correct. In the top 1% the model is consistently under-confident — a score of 0.42 was fraud 67% of the time — because it learned P(chargeback), and 17% of frauds in its training window were never reported.

## What I'd do differently

**Monitor the flagged slice, not the population.** Every label-free monitor here watched all traffic, where a tactics change in 0.8% of it is invisible. The next step on the roadmap is to watch the decisions the model makes rather than the traffic it sees, and to recalibrate on matured labels.

**Partition the stream from the start.** One Kafka partition kept the parity measurement clean and left the processor unable to scale out. Customer, device and customer-device state have to stay together, and that partitioning scheme does not exist yet.

**Measure parity at real speed.** Replaying a day in seven minutes puts a card-testing burst's attempts closer together than the stream's lag, which is where every disagreement came from. The real-speed figure would be smaller; it is unmeasured, so it is not claimed.

Every number above comes from the repository's [MEASUREMENTS.md](https://github.com/technobasant/realtime-ml/blob/main/MEASUREMENTS.md), which has the seeds, the environment and the command behind each table.
