---
title: "Agents read your definitions. Somebody has to own them."
seo_title: "Structuring knowledge for AI agents: owners, dates, disputes"
description: "Agents fail on stale or contradictory knowledge before they fail on reasoning. One concept per file, an owner, a date, a Disputed section, and generate the rest."
date: 2026-10-03 10:40:00 +0545
last_modified_at: 2026-10-03
type: essay
series: agentic-engineering
series_order: 3
tags:
  - ai-agents
  - rag
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - knowledge bases for AI agents
  - semantic layer
  - metric definitions
  - context engineering
mentions:
  - Claude Code
  - AGENTS.md
  - dbt Semantic Layer
  - MCP
cover:
  base: "/assets/images/editorial-agent-knowledge-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic mapping five kinds of agent knowledge to five homes: definitions to concept files, mappings to a semantic layer, conventions to rules, procedures to skills, and live state to a tool call"
  caption: "Five kinds of knowledge, five homes. The expensive mistake is storing all five as documents."
faq:
  - q: "Why does an AI agent give wrong metric numbers when the definitions are already documented?"
    a: "Usually for one of three reasons that have nothing to do with reasoning: it cannot find the definition inside one large file, it cannot tell a current definition from a stale one because nothing is dated or owned, or it finds two sources that disagree and silently picks one. Each needs a different fix: one concept per file, freshness metadata, and an explicit record of how a disagreement was resolved."
  - q: "What should a knowledge-base file for an agent contain?"
    a: "One concept, with aliases people actually use, an owner, a source of truth, a verified_on date and a status, then the definition, how to compute it including the filters that are easy to forget, the gotchas, and a Disputed section recording any conflict between sources and how it was resolved."
  - q: "What is a semantic layer for an agent, and why is the Never use column important?"
    a: "It is a short committed file that maps kinds of question to the table, grain and default filters that answer them. Listing the right table is not enough, because the agent will find a plausible wrong one in the catalog on its own. The Never use column names those tables and says why, which is the part a schema dump cannot express."
  - q: "Should an agent knowledge base include schemas and row counts?"
    a: "No. Anything that changes on its own, such as schemas, row counts, current thresholds or table freshness, should be generated at session start or returned by a tool call. A stale fact is worse than a missing one: a missing fact makes the agent ask, a stale fact makes it confidently wrong."
key_takeaways:
  - "Most wrong answers from data agents are knowledge failures, not reasoning failures: the definition was missing, stale, or contradicted by a second source."
  - "Five kinds of knowledge need five homes. Definitions go in owned, dated files; live state goes behind a tool call and never into a document."
  - "A Disputed section that records how a conflict was resolved is the most valuable part of a concept file, and the one that is almost always missing."
  - "A semantic layer earns its keep through the Never use column, because the agent will otherwise find a plausible wrong table on its own."
  - "Promote an invariant from prose to a tool only after the agent keeps violating it. Documentation asks; a tool enforces."
---

[Part one]({{ '/writing/coding-agents-repo-governance/' | relative_url }}) put the control plane for coding agents in the repository: a short `AGENTS.md`, skills, hooks, `CODEOWNERS`. [Part two]({{ '/writing/agents-in-a-real-repository/' | relative_url }}) measured it on this site's own gates. Both are about what an agent is allowed to *change*. This part is about what it is allowed to *believe*.

The brief on a recent advisory engagement was agents for metric validation and alerting over a data warehouse. The definitions already existed: in YAML dumps, wiki pages, dashboard descriptions, notebooks, and the heads of two people. The agents still produced numbers that did not match the dashboards, and the instinct in the room was to reach for a better model or a longer prompt. Neither would have helped. The agent was reasoning correctly from inputs that were missing, stale, or contradictory.

**Operating rule.** An agent's knowledge is a published dataset with a new consumer. It needs what any other published dataset needs before somebody reads it: one addressable unit per concept, a named owner, a date it was last verified, an explicit record of the conflicts it resolved, and — for anything that changes on its own — a generator instead of an author.

## Three ways a knowledge base fails an agent

The useful move is to stop saying "the agent got it wrong" and ask which of three things happened, because each has a different fix.

**It could not find the definition.** An agent does not read a knowledge base end to end. In Claude Code, for example, a skill's name and description are loaded into context up front and its body [loads only when it is used](https://code.claude.com/docs/en/skills). That is what makes skills cheap, and it is also why a single 4,000-line metrics file is useless: either it all loads and buries the one line that mattered, or none of it does. The long-context evidence points the same way. [*Lost in the Middle*](https://arxiv.org/abs/2307.03172) found models use information best at the start and end of a long input and markedly worse in the middle; Chroma's [context-rot report](https://www.trychroma.com/research/context-rot) found reliability falling with input length even on simple tasks, and worse with distractors present.

**It found the definition and could not tell whether it was current.** A definition with no date and no owner is indistinguishable from one that was correct two reorganisations ago. The agent treats both as fact.

**It found two definitions that disagree.** This is the expensive one. If a dashboard says an active customer is someone who ordered in the last 28 days and a YAML file says 30, the agent picks one, does not mention the other, and returns a number that is defensible from its inputs and wrong for the reader. The second definition is exactly the kind of distractor that degrades long-context performance — except it is not noise, it is a plausible answer.

The common cause is a category error. **A YAML dump is structured for a parser, not for a retriever.** Machine-parseable and agent-usable are different properties.

## Five kinds of knowledge, five different homes

The most common mistake I see is storing everything as documents. The knowledge an agent needs for data work comes in five kinds, and they decay at different rates for different reasons.

| Kind of knowledge | Where it lives | Who owns it | How it goes stale | What generates it |
|---|---|---|---|---|
| Definitions — what a metric or entity means | One concept file each, reached through a skill | The team that answers for the number | Rarely, and on purpose: a redefinition | Nothing. Authored, reviewed like code |
| Mappings — which table answers which question | A semantic-layer file | The data platform team | With schema and model changes | Partly: the catalog says what exists, a person says what to use |
| Conventions — how queries are written here | A rule, always loaded | The repository's owners | Slowly | Nothing. Authored |
| Procedures — how to investigate an alert | A skill, loaded on demand | Whoever runs the procedure | When the procedure changes | Nothing. Authored |
| Live state — current values, row counts, freshness | A tool call. Never a document | The system itself | Continuously | The warehouse, at query time |

Two failures account for most bad knowledge bases, and they are mirror images. **Live state written down as documentation** — a schema snapshot, a "current threshold", a row count — is stale by the time anyone reads it. **Definitions left as tribal knowledge** are the most stable and most valuable things to write down, and the ones most often missing, because everybody already knows them.

## One concept, one file, and a section for the argument

Every definition gets its own file, with front matter an agent and a hook can both read. The example below is illustrative — a retail domain I made up, not anyone's real schema.

```markdown
---
id: active-customer
aliases: [active customers, actives, AC28]
owner: commercial-analytics
source_of_truth: analytics.fct_orders
verified_on: 2026-09-15
status: current        # current | deprecated | disputed
---

# Active customer

## Definition
A customer with at least one completed order in the window.
Counted distinct on customer_id, never on order_id.

## How to compute
Table: analytics.fct_orders (one row per order)
Filter: status = 'completed' AND is_test_account = false. Always.
Window: rolling 28 days, inclusive of today.

## Gotchas
- orders_raw also has customer_id, but before identity merge. Never join on it.
- Test accounts were not flagged before the migration; comparisons across
  that date are invalid.

## Disputed
The executive dashboard used 30 days; analytics uses 28.
Resolved 2026-09-15: 28 is canonical, the dashboard is being corrected.
If a number does not match the dashboard, this is usually why. Say so.

## Related
net-revenue · customer
```
{: data-file="knowledge/metrics/active-customer.md" }

Each part prevents a specific failure. `aliases` is how the file gets found when somebody asks for "actives" instead of "active customer". `source_of_truth` stops the agent choosing a plausible-looking table. `verified_on` and `status` let it tell current from stale. The filter line prevents the most expensive class of error — silently wrong numbers, which are expensive precisely because nothing errors. Gotchas stop it repeating a trap that already cost somebody an afternoon.

**`## Disputed` is the section that earns the file.** Contradictions between sources are the main reason an agent's number does not match a dashboard, and an undocumented resolution gets re-litigated every quarter. Writing down the decision, its date, and what is being corrected turns a silent disagreement into one the agent can explain. The instruction that goes with it is simple: if a file says `status: disputed`, surface the dispute and never quietly pick a side.

A one-line-per-concept `INDEX.md` sits on top and goes into the skill body, so the agent sees the routing table without loading the base.

## The semantic layer is mostly a "Never use" column

An agent given only DDL knows what exists. It cannot know that one table is the deduplicated fact and its neighbour is pre-dedup and double-counts. That knowledge is not in the schema, so it has to be written down — and it is the one thing a catalog cannot generate for you. The idea is not new: the [dbt Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl) exists to define a metric once so that every consumer gets the same answer. An agent is one more consumer.

The version an agent needs is about a page long, and its most important column is the one that says what not to touch. Again illustrative:

| If asked about | Use | Grain | Never use |
|---|---|---|---|
| Orders, active customers | `analytics.fct_orders` | one row per order | `orders_raw` — pre-dedup, double-counts retries |
| Customer attributes | `analytics.dim_customer` | one row per customer version | `crm_accounts` — sales-owned, lags a day |
| Refunds | `analytics.fct_refunds` | one row per refund line | `payments_events` — includes reversed attempts |
| Margin | Ask a person. Not modelled here. | | |
{: aria-label="Illustrative semantic-layer routing table with a Never use column" }

Listing the right table only helps if the agent does not independently discover a wrong one that looks right. It will — catalogs are full of tables with good names and bad semantics. The "Never use" column closes that door, and a final row that says "ask a person" is as useful as any of the others: it is a defined answer for a question the warehouse cannot answer.

The two artefacts have different jobs. DDL from a live tool tells the agent what exists and is always current. The semantic layer from a committed file tells it what to use and changes only when someone decides it should. A committed DDL dump is the worst of both: large, stale immediately, and silent about which of its tables are traps.

There is also a useful completeness test hiding here. Once the semantic layer and the concept files exist, most metric questions reduce to three inputs: **source** (which table, from the routing file), **calculation** (which metric, from the concept file) and **processing** (window, filters, grain). If a real question cannot be expressed as those three inputs, the knowledge base is missing something — almost always a definition or a routing rule.

## If it changes on its own, generate it

The rule that governs everything else: **if a fact changes without anybody deciding to change it, do not write it down.** A stale fact is worse than a missing one. A missing fact makes the agent ask. A stale fact makes it confidently wrong.

So consolidation ends by splitting what was written into two piles. Definitions, business rules, gotchas, disputes and table routing are authored and committed. Column lists, row counts, cardinalities, partition inventories and table freshness are generated — by a tool call, or by a hook that runs when a session starts.

`verified_on` is only useful if something reads it. An illustrative session-start hook that makes staleness visible before it produces a wrong number:

```bash
#!/usr/bin/env bash
# SessionStart hook: list knowledge files not verified in 90 days.
cutoff=$(date -v-90d +%Y-%m-%d 2>/dev/null || date -d '90 days ago' +%Y-%m-%d)
grep -rl '^verified_on:' knowledge/ | while read -r f; do
  d=$(grep -m1 '^verified_on:' "$f" | awk '{print $2}')
  [ "$d" \< "$cutoff" ] && echo "stale: $f (verified $d)"
done
exit 0
```
{: data-file=".claude/hooks/knowledge-freshness.sh" }

It does not fix anything. It moves the discovery of a stale definition from "a number in a meeting was wrong" to "the session opened with a warning", which is the same move a freshness check makes for a published table.

## The ladder: rules, skills, agents, tools

The order in which these get built matters as much as their content, and each step should be triggered by evidence rather than ambition.

```text
tribal knowledge → written definitions → indexed knowledge base
    → wired into a skill → invariants promoted into tools
```

Rules come first because they bound behaviour on every request. Skills come next, for the procedures that repeat. Agents come after that — an agent with no skills has to be told how to do the job every time. Tools come last, and only for a reason: an invariant keeps getting violated, an audit trail is needed, or "read-only" has to be enforced rather than requested.

That last step is where this connects to [part two]({{ '/writing/agents-in-a-real-repository/' | relative_url }}). A rule in a context file shapes what an agent attempts; it does not constrain what it does. If the agent keeps forgetting to exclude test accounts after a week of use, the fix is not a sterner sentence in the concept file. It is a query tool that applies the filter itself. **Documentation asks; a tool enforces.**

Maintenance follows the same logic. At the end of a working session, every correction gets routed to the layer it belongs in: a wrong definition to its concept file, a repeated wrong table to the semantic layer, a violated rule to a hook. And deletion is part of the job. Skill descriptions and tool schemas cost context on every request, so a skill that never fires, a definition nobody has asked about in six months, or a rule a hook already enforces is not harmless clutter. It is a distractor.

<div class="callout callout--note" markdown="1">
**Boundary.** This is an operating model, not a measurement. It comes from one advisory engagement over a data warehouse plus the way this site's own repository is run. I have not measured answer accuracy before and after restructuring a knowledge base, and I would not quote a figure for it without a fixed question set and a scorer written before the run. The external evidence cited — long-context degradation and distractor sensitivity — supports the *direction* of the argument, not any particular size of effect. Every schema, table and metric shown here is invented for illustration.
</div>

## This is data governance with a different consumer

None of the structure above is specific to language models. It is what a data platform already does for a published table: [ownership before consumption]({{ '/about/' | relative_url }}), a freshness expectation, a contract that says what the table promises and what it does not. The agent is simply a consumer that cannot walk over to someone's desk and ask which of two numbers is right.

That is also why the boundary matters in the other direction. In [governed AI delivery]({{ '/work/governed-ai-delivery/' | relative_url }}) the rule is that model output only becomes state after validation and provenance. The rule here is the mirror image: a definition only becomes something an agent may rely on after it has an owner, a date and a recorded resolution of its disputes. Input and output both cross a boundary, or neither is trustworthy.

## Frequently asked questions

### Why does an AI agent give wrong metric numbers when the definitions are already documented?

Usually for one of three reasons that have nothing to do with reasoning: it cannot find the definition inside one large file, it cannot tell a current definition from a stale one because nothing is dated or owned, or it finds two sources that disagree and silently picks one. Each needs a different fix: one concept per file, freshness metadata, and an explicit record of how a disagreement was resolved.

### What should a knowledge-base file for an agent contain?

One concept, with aliases people actually use, an owner, a source of truth, a `verified_on` date and a status, then the definition, how to compute it including the filters that are easy to forget, the gotchas, and a `## Disputed` section recording any conflict between sources and how it was resolved.

### What is a semantic layer for an agent, and why is the Never use column important?

It is a short committed file that maps kinds of question to the table, grain and default filters that answer them. Listing the right table is not enough, because the agent will find a plausible wrong one in the catalog on its own. The "Never use" column names those tables and says why, which is the part a schema dump cannot express.

### Should an agent knowledge base include schemas and row counts?

No. Anything that changes on its own — schemas, row counts, current thresholds, table freshness — should be generated at session start or returned by a tool call. A stale fact is worse than a missing one: a missing fact makes the agent ask, a stale fact makes it confidently wrong.

The repository decides what an agent may merge; the knowledge base decides what it may believe. Both are policy, and both belong under review. Part one is the [control plane for coding agents]({{ '/writing/coding-agents-repo-governance/' | relative_url }}), part two is [the gates that enforce it]({{ '/writing/agents-in-a-real-repository/' | relative_url }}), and the rest of the writing on [AI agents in production]({{ '/writing/tags/ai-agents/' | relative_url }}) and [retrieval]({{ '/writing/tags/rag/' | relative_url }}) follows the same rule.
