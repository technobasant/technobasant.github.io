---
title: "The data platform is part of the product"
seo_title: "Why the data platform belongs inside the product boundary"
description: "A practical operating model for reliable data and AI products: consumer-facing promises, typed decisions, idempotency, provenance, and repair."
date: 2026-08-11 10:00:00 +0545
last_modified_at: 2026-08-11 16:00:00 +0545
type: essay
tags: [ai-agents, data-quality]
toc: true
level: advanced
cover:
  base: "/assets/images/editorial-data-platform-ai-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Abstract event streams passing through governed data layers into a product decision surface"
  caption: "A reliable product boundary carries contracts, provenance, and recovery paths across every layer."
key_takeaways:
  - "Define reliability from the consumer's decision window: what must be queryable, how fresh it must be, and who can repair it."
  - "Persist automated decisions as typed, validated records with provenance before another workflow is allowed to act on them."
  - "Design idempotency, replay, rejection, and human review before launch; a correction path is part of the product interface."
---

I used to draw data platforms underneath the product: neat boxes for ingestion, storage, transformation, and serving, with the “real” application sitting safely above them. The diagram was tidy and the boundary was wrong.

A user does not experience those boxes. They experience one answer. If a source arrives late, a transformation accepts an impossible value, a cache serves an old projection, and an AI workflow confidently acts on it, every individual service can be green while the product is wrong.

That changed the question I ask in design reviews. I no longer begin with, “What should process this data?” I begin with, “What promise is the product making, and how will we repair that promise when one layer lies?”

This is the operating model I now use. It is intentionally independent of any employer architecture or vendor stack.

## Start with the decision window, not the job

“The pipeline runs every hour” is a schedule, not a reliability promise. The consumer cares whether the expected fact is queryable before a decision becomes stale.

For each product-facing dataset or endpoint, I write down five things:

1. **The fact:** the smallest record the consumer actually needs.
2. **The clock:** event time, processing time, or the time a decision must be made.
3. **The tolerance:** how late, incomplete, or approximate the fact may be.
4. **The failure state:** what the product shows when the promise cannot be met.
5. **The repair owner:** who can replay, correct, or suppress the result safely.

That short contract changes the implementation. Freshness becomes a property of a published fact rather than a scheduler. Quarantine becomes a visible state instead of a forgotten dead-letter queue. A backfill becomes part of the interface, because a correction that never reaches the product is not a correction.

I also separate *availability* from *fitness*. A service can answer every request and still serve a stale or semantically invalid record. For data products, I want at least these signals beside ordinary uptime:

| Signal | Question it answers |
|---|---|
| Freshness | Is the newest expected fact available inside its decision window? |
| Completeness | Did the expected population arrive, not merely some records? |
| Validity | Do values satisfy the contract at the publication boundary? |
| Decision latency | How long from source event to a product action? |
| Repair time | How long from detection to a corrected product state? |

## Make the boundary a record, not a feeling

Whenever automated output can change another workflow, I persist a decision record before I persist the effect. The record needs enough information to explain what happened without reconstructing it from logs scattered across services.

This small standard-library example is deliberately runnable. It validates confidence, requires source references, fixes the set of allowed outcomes, and emits a JSON-ready record. The type hints help the editor; the runtime checks protect the boundary.

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal

Outcome = Literal["approve", "reject", "needs_review"]
ALLOWED_OUTCOMES = {"approve", "reject", "needs_review"}


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    subject_id: str
    outcome: Outcome
    confidence: float
    policy_version: str
    source_refs: tuple[str, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.subject_id.strip():
            raise ValueError("subject_id must not be blank")
        if self.outcome not in ALLOWED_OUTCOMES:
            raise ValueError(f"unsupported outcome: {self.outcome}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.policy_version.strip():
            raise ValueError("policy_version must not be blank")
        if not self.source_refs or any(not ref.strip() for ref in self.source_refs):
            raise ValueError("at least one non-blank source reference is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must include a timezone")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_refs"] = list(self.source_refs)
        payload["created_at"] = self.created_at.isoformat()
        return payload


record = DecisionRecord(
    subject_id="case-1042",
    outcome="needs_review",
    confidence=0.71,
    policy_version="risk-policy-2026-08",
    source_refs=("snapshot:6b8f", "rule:missing-history"),
    created_at=datetime.now(UTC),
)

print(record.outcome)
print(record.to_dict()["policy_version"])
```
{: data-file="contracts/decision_record.py" }

Running the file should produce the outcome and policy version:

```console
$ python3 contracts/decision_record.py
needs_review
risk-policy-2026-08
```

The database should defend the same boundary. Application validation gives a useful error close to the producer; database constraints protect every write path, including scripts and future services.

```sql
CREATE TABLE decision_records (
    decision_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    idempotency_key  text        NOT NULL UNIQUE,
    subject_id       text        NOT NULL CHECK (btrim(subject_id) <> ''),
    outcome          text        NOT NULL
                     CHECK (outcome IN ('approve', 'reject', 'needs_review')),
    confidence       numeric(5,4) NOT NULL
                     CHECK (confidence BETWEEN 0 AND 1),
    policy_version   text        NOT NULL CHECK (btrim(policy_version) <> ''),
    source_refs      jsonb       NOT NULL
                     CHECK (jsonb_typeof(source_refs) = 'array'
                            AND jsonb_array_length(source_refs) > 0),
    created_at       timestamptz NOT NULL,
    recorded_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX decision_records_subject_time_idx
    ON decision_records (subject_id, created_at DESC);
```
{: data-file="migrations/001_decision_records.sql" }

Notice what is absent: a raw prompt as the only evidence, a free-form verdict, and an overwritten “current answer.” Those make a demo easy and a correction almost impossible.

## Keep truth separate from projections

Product reads often need a shape that the source of truth should not have. A low-latency endpoint may want one precomputed row per subject; an audit may need the full history; an analyst may need a columnar projection. Those are different read paths, not competing definitions of truth.

I use three layers of responsibility:

- **Source records** preserve the facts received from producers, including event time and a stable source identifier.
- **Decision records** preserve what a policy or model concluded, the version that concluded it, and the evidence it used.
- **Projections** arrange those facts for a particular read path and may be rebuilt.

The third layer is disposable by design. If a projection is corrupted or its model changes, I should be able to rebuild it from the first two layers without inventing history. That repair path is more valuable than choosing a fashionable serving engine.

This distinction also makes corrections honest. A new policy should append a new decision; it should not mutate the old one until the audit trail agrees with the present. The product can point to the active decision while the history explains how it got there.

## Treat AI as an unreliable producer

AI does not need a separate philosophy of reliability. It needs the same producer boundary as any source we do not fully control, with stricter attention to provenance and evaluation.

I model the workflow as explicit states:

```text
proposed -> validated -> applied
    |           |
    |           +-> needs_review
    +--------------> rejected
```
{: data-file="docs/decision-state-machine.txt" }

“Proposed” is important. Model output has not become a product fact merely because inference returned successfully. It still has to pass structural validation, policy checks, evidence requirements, and—where the consequence justifies it—human review.

Confidence is not a universal truth meter either. A threshold only has meaning against an evaluated task, versioned data, and a defined cost for false approval versus false rejection. If those are missing, `0.93` is decoration.

For every automated decision, I want to answer:

- Which model, policy, and tool versions ran?
- Which source records were visible?
- Which checks passed, failed, or were skipped?
- Was a human review required, and who completed it?
- Can the effect be reversed without deleting the original record?

If the system cannot answer those questions, it is not ready to make a consequential change unattended.

## Design replay and idempotency before launch

Retries happen everywhere: queues redeliver, clients time out after a successful write, operators replay a date range, and backfills overlap live traffic. “Exactly once” is often a property claimed by one component while the business effect crosses several.

I prefer an idempotency key derived from the stable inputs to the decision, such as:

```python
from hashlib import sha256


def decision_key(
    subject_id: str,
    policy_version: str,
    source_snapshot: str,
) -> str:
    canonical = "\x1f".join((subject_id, policy_version, source_snapshot))
    return sha256(canonical.encode("utf-8")).hexdigest()
```
{: data-file="contracts/idempotency.py" }

The write path then treats a duplicate as a known result, not a second decision:

```sql
INSERT INTO decision_records (
    idempotency_key,
    subject_id,
    outcome,
    confidence,
    policy_version,
    source_refs,
    created_at
)
VALUES (
    :idempotency_key,
    :subject_id,
    :outcome,
    :confidence,
    :policy_version,
    CAST(:source_refs AS jsonb),
    :created_at
)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING decision_id;
```
{: data-file="queries/insert_decision.sql" }

There is a trade-off: the key encodes what I consider the identity of a decision. Changing that definition is a contract change. I document it and version the policy rather than hiding it in a helper function.

Replay needs a product rule too. When a corrected source record produces a different outcome, does the system apply it automatically, open a review, or leave the prior effect in place? That answer depends on consequence, not throughput. The platform can provide the mechanism; the product must own the policy.

## Review the seams as one operating model

End-to-end ownership does not mean one person builds every service. It means the seams share one definition of correctness and one repair story.

This is the checklist I use before a data-backed or AI-assisted workflow ships:

- [ ] The consumer-facing fact and decision window are written down.
- [ ] Missing, late, duplicate, malformed, and contradictory inputs have named states.
- [ ] Automated output crosses typed validation before it can create an effect.
- [ ] The decision record includes policy version, evidence references, and time.
- [ ] The write path is idempotent under retry and replay.
- [ ] Projections can be rebuilt without rewriting source or decision history.
- [ ] Alerts point to a safe action, not merely a dashboard.
- [ ] A corrected decision can reach the product without erasing the old one.
- [ ] A human can stop or review the workflow when the consequence demands it.

The principle underneath all of this is modest: the platform is part of the product because it decides which facts the product may trust. Once that is explicit, architecture discussions get less theatrical. The useful questions become concrete: What is the promise? Where is it recorded? How does it fail? Who can repair it? And can they do so while the rest of the system keeps moving?
