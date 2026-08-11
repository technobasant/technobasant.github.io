---
title: "Making model output into records you can audit"
hook: "The boundary I put between a language model and anything a product depends on"
description: "How I ship AI features that other workflows can rely on: typed outputs, provenance, evaluation before rollout, and a fallback that is a real path rather than an apology."
kind: practice
order: 2
featured: true
role: "Senior Data Engineer"
org: "UXCam"
period: "2024 – present"
team: "Global team, working US and EU hours"
scale: "Described at the level the product is publicly an analytics tool. No prompts, architecture, model choices, vendor terms or usage figures."
stack: [Python, Pydantic, LangGraph, LangChain, CrewAI, "Google-ADK", MCP, Milvus, MLflow, PostgreSQL]
tags: [ai-agents, data-quality, rag]
image: /assets/og/og-agents.png
image_alt: "AI agents in production — Basant Bhattarai"
---

## What this page is

The same rule as the [platform page](/work/data-platform-practice/): the method, not the deployment. No prompts, no model selection, no vendor arrangements, no usage numbers. What follows is the design position I hold, which is portable and arguable — and I would rather be argued with than believed.

## Context

Almost every hard problem in shipping an AI feature turns out to be a data-engineering problem wearing a costume. Getting a plausible answer out of a model is the easy part and has been for a while. The difficulty is that a product cannot depend on prose. It depends on records: typed, queryable, attributable, and correctable when wrong.

So the interesting question is never "what did the model say." It is **what is allowed to become state**, and under what conditions.

## Constraints I design against

- **Non-determinism is permanent.** The same input can produce a different output tomorrow. Any design that assumes stability is already broken.
- **Confident wrongness is the default failure mode.** A model does not signal uncertainty by going quiet. It signals it by being fluent and incorrect, which is the hardest failure to catch downstream.
- **Provenance is not optional.** If an automated judgment influenced something a person acted on, I need to reconstruct later which version produced it and on what input.
- **Latency and cost per call are user-visible in a way a batch job never is.**

## The method

### A typed boundary, and nothing crosses it untyped

Model output is parsed into a declared schema before it goes anywhere. Validation failure is a handled outcome with its own path, not an exception that surfaces to a user. In practice this means a validated object, versioned, with the raw response retained for inspection.

The trade-off: schemas constrain what the feature can express, and loosening one later is a migration. I take that cost deliberately — an unconstrained output is a liability that grows with adoption.

### Separate what is generated from what is true

Generated content lands in its own columns, or its own tables, clearly marked and never silently merged into a field a human authored. Anyone reading the record — or querying it in two years — can tell which is which.

This one is not negotiable. Losing the distinction is unrecoverable, because after the merge there is no query that separates them again.

### Provenance on every generated record

Input reference, schema version, timestamp, and which pipeline produced it. Enough to answer "why does this say that" without guessing, and enough to re-derive or invalidate a cohort when something upstream turns out to have been wrong.

### Evaluate before rollout, and keep the set

A held-out set with expected outcomes, run before a change ships. Tracing so a regression is attributable rather than mysterious. The set grows every time something surprises me in production — that is what makes it valuable, and it is why deleting it is expensive.

The trade-off: maintaining an evaluation set is ongoing work that never feels urgent. It is the first thing to rot and the last thing you want rotten.

### A fallback that is a real path

If validation fails or confidence is low, the feature degrades to something honest and useful — the underlying data, an explicit "not available", a queue for review. Never a guess presented as an answer, and never a blank space that reads as a bug.

### Retrieval is a data problem

For retrieval-augmented features: chunking, metadata filters and index choice determine quality far more than prompt wording does. A vector store also needs a retention and compaction policy on day one, for the same reason any other store does — without one it becomes a landfill that is expensive to query and impossible to reason about.

## What I would do differently

**Build the evaluation set before the first version, not after the first regression.** I know why it happened — early on the feature is changing so fast that fixing the target feels premature. That reasoning is wrong, and it costs more than it saves.

**Decide the human-review path at design time.** Retrofitting review onto a feature that assumed full automation is significantly harder than designing for it and then not needing it.

**Say no to more of them.** The most useful judgment I have developed here is which problems should not have a model in the loop at all. A deterministic rule that is right every time beats a generated answer that is right most of the time, and it is cheaper to operate.
