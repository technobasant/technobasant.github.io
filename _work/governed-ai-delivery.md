---
title: "Turning model output into product state you can audit"
hook: "A governed analytics workflow with typed state, provenance, evaluation, review, and an honest fallback path."
description: "How I designed AI-assisted analytics around typed records, source evidence, evaluation, human review, and measurable workflow outcomes."
kind: practice
order: 2
featured: true
role: "Senior Data Engineer"
org: "UXCam"
period: "2024 – present"
team: "Global team, working US and EU hours"
scale: "AI features in a production analytics product"
problem: "Useful model responses were not enough: downstream workflows needed records that could be validated, traced, reviewed, corrected, and safely withheld."
decision: "Treat generation as a candidate state, then require schema validation, provenance, evaluation, and a review or fallback decision before publication."
flow: ai
metrics: [professional_analytics_delivery, professional_manual_effort]
stack: [Python, Pydantic, LangGraph, LangChain, CrewAI, "Google-ADK", MCP, Milvus, MLflow, PostgreSQL]
tags: [ai-agents, data-quality, rag]
image: /assets/og/og-agents.png
image_alt: "AI agents in production — Basant Bhattarai"
---

## Context

The product goal was not a chat demo. It was a faster analytics workflow that people could use without losing the evidence and reviewability they expected from the underlying data platform.

A model can return fluent prose, but a product workflow needs durable records: typed, queryable, attributable, and correctable. The central design question became **what is allowed to become state**, under which policy, and what happens when the system cannot justify an answer.

## My role

I designed the data and state boundary around the AI workflow: structured outputs, provenance, evaluation, retrieval metadata, publication rules, and the path from automated candidate to human-reviewed result. I worked across platform and product concerns rather than treating the model invocation as the feature.

## Constraints

- **Non-determinism is permanent.** The same input can produce a different candidate after a model or prompt change.
- **Confident wrongness is the dangerous failure.** A fluent answer can pass superficial review while contradicting source data.
- **Analytical claims need evidence.** Every result must retain enough source context to explain and re-evaluate it.
- **Latency and cost are user-visible.** Tool loops and retrieval choices are product decisions, not invisible infrastructure.
- **Automation needs a stopping rule.** Some cases should go to review or return underlying data rather than generate another guess.

## Architecture and state boundary

The workflow separates four states: source context, generated candidate, validated record, and published result. Generation never writes directly into a human-authored field. A schema and policy version travel with the record, along with source references, timestamps, and the path that produced it.

Validation failure is an expected outcome. The system can retry a bounded transformation, present the underlying data, mark the result unavailable, or queue it for review. Each path is explicit; none silently converts uncertainty into success.

Retrieval follows the same data-engineering discipline: versioned documents, metadata filters, known retention, and evaluation against held-out questions. Prompt changes cannot compensate for missing provenance or a polluted index.

## Decisions and rejected alternatives

| Decision | Alternative rejected | Why | Cost accepted |
|---|---|---|---|
| Parse every candidate into a versioned schema | Store free-form model prose as the result | Downstream code gets a stable contract | Schema changes become migrations |
| Keep generated and human-authored state separate | Merge into one canonical field | Origin and correction history remain recoverable | Consumers handle explicit state |
| Attach source references and pipeline versions | Keep only the final answer | Claims can be inspected and cohorts re-evaluated | More storage and metadata |
| Evaluate before rollout and after surprises | Rely on prompt review and spot checks | Regressions become measurable and attributable | Evaluation sets need maintenance |
| Design review and fallback before automation | Add human review after failures appear | The product stays useful when confidence is low | Some cases complete more slowly |
{: .case-decisions aria-label="Governed AI decisions and rejected alternatives" }

## Outcomes

The workflow improved analytics delivery time by **{{ site.data.metrics.professional_analytics_delivery.value }}** and reduced analyst manual effort by **{{ site.data.metrics.professional_manual_effort.value }}**. Those gains matter because the controls remained part of the path: typed output, source evidence, evaluation, review, and fallback were not removed to make the number look better.

The system also established a reusable operating pattern for AI features: generated content is candidate state; policy decides whether it becomes product state.

## Failure and recovery

If parsing fails, the raw candidate and validation reason remain inspectable. If evidence is missing or the policy threshold is not met, the workflow does not publish. If a model, prompt, or source changes, the versioned provenance supports cohort re-evaluation instead of manual guesswork.

Recovery therefore means more than retrying an API call. It means restoring a defensible record or declining to create one.

## Reflection

I would build the evaluation set before the first release. Early feature churn makes a stable test set feel premature; in practice, that is when its baseline is most valuable.

I would also decide the human-review path during product design, not after implementation. Retrofitting review into a workflow that assumed full automation is much harder than designing the decision point and using it selectively.

The most important judgment is still when not to use a model. A deterministic rule that is right every time is cheaper, faster, and easier to operate.
