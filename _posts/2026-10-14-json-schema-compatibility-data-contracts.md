---
title: "Removing an optional field breaks consumers. Adding one breaks history."
seo_title: "Data contract compatibility: BACKWARD and FORWARD on JSON Schema"
description: "Schema changes teams call safe still break someone. A JSON Schema contract checker, 51 labelled changes, an oracle, and no breaking change passed as safe."
date: 2026-10-14 09:25:00 +0545
last_modified_at: 2026-10-14
type: essay
pillar: data-platforms
series: reference-systems
series_order: 6
tags:
  - data-quality
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - data contracts
  - schema compatibility
  - JSON Schema evolution
  - data ownership
mentions:
  - JSON Schema
  - Apache Avro
  - OpenLineage
  - PostgreSQL
cover:
  base: "/assets/images/editorial-dataset-registry-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Table of eight schema changes teams call safe, each marked as breaking history or breaking consumers, beside the checker's score on 51 labelled changes: no breaking change called safe, two false alarms per direction"
  caption: "Widening breaks consumers; narrowing breaks history. The checker may over-report either, and must never under-report."
faq:
  - q: "Is removing an optional field from a JSON Schema contract a breaking change?"
    a: "For consumers, yes, if the object is open. Once the field is gone from properties, the name falls under additionalProperties, which accepts anything, so the producer may now write any value there and consumers built against the old type receive it. It breaks FORWARD compatibility, not BACKWARD."
  - q: "What is the difference between BACKWARD and FORWARD compatibility for JSON Schema?"
    a: "Defined on the sets of documents each version accepts: BACKWARD holds when every document valid under the old schema is valid under the new one, which protects history and replays. FORWARD holds when every document valid under the new schema is valid under the old one, which protects consumers built against the old contract. FULL requires both."
  - q: "Does adding a field with a default keep a JSON Schema change backward compatible?"
    a: "No. In JSON Schema, default is an annotation and validators do not fill it in, so a newly required field with a default still rejects every older document that lacks it. Avro's reader-side defaults have no equivalent in a JSON Schema validator."
  - q: "How accurate was the compatibility checker?"
    a: "On 51 hand-labelled changes it passed no breaking change as safe in BACKWARD, FORWARD or FULL mode, and flagged 2 safe changes per direction as breaking (96.1% accuracy), all from keywords it deliberately does not reason about. The labels were confirmed by an oracle that ran 8,092 probe documents through a real validator."
key_takeaways:
  - "Define compatibility on validity sets: BACKWARD protects history and replays, FORWARD protects consumers, and most real changes break exactly one of them."
  - "Widening breaks consumers and narrowing breaks history: an added enum value, integer to number and a removed optional field all break FORWARD."
  - "The checker passed no breaking change as safe on 51 labelled changes, at a cost of 2 false alarms per direction from regex, anyOf and multipleOf."
  - "Check the labels with an oracle that runs probe documents through a real validator, because labels written beside a checker share its blind spots."
  - "A conservative checker only works if a false alarm is cheap: ask the registered consumers rather than block, which requires knowing who owns and reads each dataset."
---

An orders contract has an optional `status` field that nobody downstream admits to reading. The producer removes it. No pipeline fails, nobody required it, and it looks like the safest change there is. Under the definition of compatibility I ended up using, it is breaking. The new contract says nothing about `status` any more, so the producer is free to write `"status": 42`, and every consumer that built a switch on the old enum receives it with the contract's blessing.

The reverse change looks just as harmless. Add an optional `channel` field to an open object, and the history you have already written can fail the new contract. The open object always accepted a field called `channel` with any value at all, and nothing says the old documents that carry one carry a string.

**Operating rule.** Define schema compatibility on the set of documents each version accepts, decide which direction your consumers need, and make the checker conservative: it may call a safe change breaking, and it must never call a breaking change safe. Then make a false alarm cheap, by turning it into a question for the teams it affects rather than a blocked deploy, and know who those teams are before you check anything.

I built this into [dataset-registry](https://github.com/technobasant/dataset-registry), a data-ownership registry with a Go API, PostgreSQL 18 and a Next.js UI, populated with an online retailer's orders, payments and dbt models, a standard e-commerce scenario. Its compatibility checker was measured against 51 hand-labelled schema changes. Every figure below is in the repository's [MEASUREMENTS.md](https://github.com/technobasant/dataset-registry/blob/main/MEASUREMENTS.md), and the system around the checker is described in [the case study](/work/dataset-registry/).

## Compatible with what?

The words come from schema registries: BACKWARD, FORWARD, FULL. Their intuitions come mostly from Avro, where a reader resolves a writer's schema, skips fields it does not know and fills in defaults for fields it expects. A JSON Schema validator does none of that. It takes one document and one schema and says yes or no. So I kept the names and pinned their meaning to the only thing a validator has, the set of documents each version accepts. Write V(s) for the set of documents schema *s* accepts.

| Mode | Holds when | Protects |
|---|---|---|
| BACKWARD | V(old) ⊆ V(new) | Readers of history: everything already written still validates, so replays and backfills work |
| FORWARD | V(new) ⊆ V(old) | Consumers: everything written from now on still satisfies the contract they built against |
| FULL | Both | Both |
{: aria-label="Compatibility modes defined on the sets of documents each schema version accepts" }

The registry defaults to FORWARD, because it exists for consumers. They built against the old contract, and they will receive data written under the new one. Datasets that are replayed or backfilled from history can ask for BACKWARD or FULL.

One rule then handles open and closed objects without a table of special cases. A field that is absent from `properties` takes the schema of `additionalProperties`. For an open object that schema accepts anything, and for a closed one (`additionalProperties: false`) it accepts nothing. "Add a field" stops being its own kind of change. It becomes "the schema at this name went from anything to a string", and that comparison is the same one the checker makes everywhere else.

## The changes people call safe

Most changes break exactly one direction. These are the ones that surprise people, all with labels taken from the labelled set:

| Change | Breaks history (BACKWARD) | Breaks consumers (FORWARD) | Why |
|---|---|---|---|
| Optional field removed, open object | no | **yes** | The name is now unconstrained, so new documents may carry any value there |
| Optional field added, open object | **yes** | no | Older documents could already carry that name, with another type |
| Optional field added, closed object | no | **yes** | Consumers validating the closed old contract reject the new field |
| Required → optional | no | **yes** | Consumers relying on the field can find it missing |
| Integer → number | no | **yes** | Consumers expecting integers receive 12.5 |
| Enum value added | no | **yes** | A consumer with a closed set of cases receives a value it has never seen |
| Nullable added | no | **yes** | Consumers that never saw `null` now receive it |
| Required field added, with a `default` | **yes** | no | Validators do not fill defaults, so history without the field fails |
| Field renamed | **yes** | **yes** | A rename is a removal plus an addition |
{: aria-label="Schema changes commonly treated as safe, and the direction each one breaks" }

The pattern under the table is short. Widening breaks consumers and narrowing breaks history. A change that lets the producer write something the old contract forbade is a FORWARD problem. A change that rejects something the old contract allowed is a BACKWARD problem. Most of what the checker does is bookkeeping of which of those two happened, at every path in the schema.

Two rows deserve a second look. The `default` row catches anyone who learned schema evolution on Avro, where a reader-side default makes a new required field safe. In JSON Schema, `default` is an annotation. Adding a required field with a default still rejects every older document that lacks it.

The open-object addition is the strictest label in the set, and I kept it strict on purpose. In practice most histories do not contain a stray `channel` field. The checker cannot know that, because the old contract allowed one, and a checker that guesses about history is not a checker. The strictness also costs nothing in the default mode. The change only breaks BACKWARD, so under FORWARD it publishes at once.

## Checking the labels, not just the checker

A checker and a set of labels written by the same person share blind spots. If I misread what `additionalProperties` does to a removed field, I would write the wrong rule and the matching wrong label, and the test would pass. So the labels are checked by something that does not use my reasoning at all.

The oracle generates probe documents from both schemas. It starts from an exemplar that has every declared field, then sets each field to values of every JSON type, to the enum values, examples and the edges of each bound, drops fields one at a time, and adds an undeclared one. It validates every probe against both versions with a real JSON Schema validator. A document that the old version accepts and the new one rejects is a *witness*: concrete proof that BACKWARD breaks. The reverse proves FORWARD breaks.

Across 8,092 probes the oracle agreed with **51 of 51** labels in both directions. The agreement is not symmetric, though, and the difference matters. For every "breaking" label the oracle produced a document that proves it. For every "safe" label it only failed to find one. That is evidence, not proof, and I would not describe it as more.

## Wrong in one direction only

With the labels checked, the checker's score:

| Mode | Breaking, flagged | Safe, flagged (false alarm) | Safe, passed | Breaking, passed (false negative) | Accuracy |
|---|---:|---:|---:|---:|---:|
| BACKWARD | 29 | 2 | 20 | **0** | 96.1% |
| FORWARD | 27 | 2 | 22 | **0** | 96.1% |
| FULL | 47 | 0 | 4 | **0** | 100% |
{: aria-label="Compatibility checker against 51 labelled schema changes, by mode" }

**No breaking change passed as safe** in any mode. That is the one property the rest of the registry depends on. A unit test runs every labelled case and fails if it ever stops holding, so a later change to the checker that introduces a false negative fails CI.

**The four false alarms are the ones I designed in.** A widened and a narrowed regular expression, an added `anyOf` branch, and an added `multipleOf` are each flagged as breaking in both directions, and each truly breaks only one. The checker does not compare regular expressions for containment. Deciding whether one pattern accepts everything another does is expensive even for textbook regular expressions, and JSON Schema patterns are ECMA-262 regexes with backreferences and lookarounds on top. It does not reason about `anyOf`, `oneOf`, `$ref`, `patternProperties` or `multipleOf` either. When any of those differ between versions, the answer is "breaking, both ways", with a reason that says so.

Measured against safe changes rather than against all 51, the over-reporting rate is 2 of 24 under FORWARD and 2 of 22 under BACKWARD: roughly one safe change in eleven or twelve gets flagged.

**FULL's 100% is not a better checker.** 47 of the 51 changes break *some* direction, so under FULL the conservative answer happens to be right for the four cases it over-reports in the other modes. Accuracy here is a property of the case mix as much as of the checker, which is why I report the matrix rather than a single figure.

A comparison takes 17 µs at the median (64 µs at p95). That is cheap enough to run on every proposed version without anyone noticing.

<div class="callout callout--note" markdown="1">
**Boundary.** I wrote the labelled set alongside the checker. It tests the rules the checker claims to implement. It is not a sample of real-world schema changes, and I have not measured one. A real corpus would contain far more `$ref` and `oneOf`, which this checker always calls breaking, so its false-alarm rate on real contracts would be higher than 2 in 51 — by an amount I do not know. The oracle proves breaking labels and only supports safe ones. Avro and Protobuf contracts are not supported at all.
</div>

## A false alarm has to be cheap

A conservative checker is only half a design. The other half is what a "breaking" verdict does, because that decides what a false alarm costs.

If the verdict blocks the change, every false alarm teaches a team to route around the registry. They create a new topic, a `_v2` table, a column nobody removes, and the contract slowly stops describing what is actually produced. Sometimes a breaking change is the right change. What goes wrong is that the people it breaks find out from an incident.

In dataset-registry a compatible change publishes at once. A breaking change creates a pending version and a change request, and every consumer registered at that moment gets a review. Each one reads the checker's report — what changed, at which path, which direction it breaks and why — and acknowledges or rejects it. A rejection has to carry a reason, and one rejection closes the request. The owner can publish only once every consumer has acknowledged. An admin cannot acknowledge on a team's behalf, and every transition lands in an append-only audit log that database triggers protect.

Seen that way, the checker's lean follows from the costs. A false alarm costs each affected consumer one report to read and one click. A false negative costs whatever the incident costs. I would rather pay the first cost many times over than the second once.

The design has a failure mode of its own, and it is on the repository's limits list rather than hidden. A consumer that never answers blocks the owner indefinitely, because there is no expiry or escalation yet. Consumers that register after a request opens are not asked about it.

## Ownership comes before the checker

The checker answers "does this change break someone?" The workflow needs "whom?", and the checker cannot answer that.

So the registry's first rule is not about schemas at all. **Nobody can depend on a dataset that nobody owns.** Lineage arrives as OpenLineage run events from the pipelines that move data, and any dataset that appears in lineage without an owner is recorded as unowned. It is real and something writes it, but there is no one to ask about it. Registering as a consumer of an unowned dataset is refused until a team claims it.

Without that rule, the acknowledgement workflow has a hole exactly where it matters. A breaking change to a table that nobody owns, read by teams that never declared it, is the change that turns into an incident. The registry handles a change with no registered consumers honestly: the request starts approved because nobody declared a dependency, and the audit log records that the change was breaking. The rule's job is to make "nobody declared a dependency" a fact about the world rather than a gap in the bookkeeping.

## What I would put in any contract checker

- The compatibility modes defined on validity sets, written down next to the code, with the protected party named for each.
- Both directions reported for every change, then a verdict under the dataset's mode, with a reason a consumer can read.
- Keywords the checker cannot reason about treated as breaking in both directions, and the resulting over-reporting measured rather than assumed.
- A labelled set with a test that fails on any false negative, and labels checked by an oracle that runs probe documents through a real validator.
- FORWARD as the default when the registry exists for consumers; BACKWARD or FULL for datasets that are replayed from history.
- A breaking verdict that becomes a question to registered consumers, not a block.
- No dependency on a dataset that nobody owns.
{: .checklist }

## Frequently asked questions

### Is removing an optional field from a JSON Schema contract a breaking change?

For consumers, yes, if the object is open. Once the field is gone from `properties`, the name falls under `additionalProperties`, which accepts anything, so the producer may now write any value there and consumers built against the old type receive it. It breaks FORWARD compatibility, not BACKWARD.

### What is the difference between BACKWARD and FORWARD compatibility for JSON Schema?

Defined on the sets of documents each version accepts: BACKWARD holds when every document valid under the old schema is valid under the new one, which protects history and replays. FORWARD holds when every document valid under the new schema is valid under the old one, which protects consumers built against the old contract. FULL requires both.

### Does adding a field with a default keep a JSON Schema change backward compatible?

No. In JSON Schema, `default` is an annotation and validators do not fill it in, so a newly required field with a default still rejects every older document that lacks it. Avro's reader-side defaults have no equivalent in a JSON Schema validator.

### How accurate was the compatibility checker?

On 51 hand-labelled changes it passed no breaking change as safe in BACKWARD, FORWARD or FULL mode, and flagged 2 safe changes per direction as breaking (96.1% accuracy), all from keywords it deliberately does not reason about. The labels were confirmed by an oracle that ran 8,092 probe documents through a real validator.
