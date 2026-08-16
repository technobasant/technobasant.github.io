---
title: "Agents write the diff. The repo has to review it."
seo_title: "Governing Cursor, Claude Code, and Codex in existing repos"
description: "When agents write most of the diff, review time explodes. Put instructions, hooks, CI, and CODEOWNERS in the repo so merge is a policy, not a vibe."
date: 2026-08-16 13:00:00 +0545
last_modified_at: 2026-08-16
type: essay
series: agentic-engineering
series_order: 1
editor_pick: true
tags:
  - ai-agents
  - career
toc: true
featured: true
cover:
  base: "/assets/images/editorial-coding-agents-review-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic of an agent session becoming a candidate pull request, then a named-owner merge gate"
  caption: "Generation is candidate state. Types, tests, CODEOWNERS, and CI decide whether it becomes the tree."
key_takeaways:
  - "Treat agent output as candidate state: it becomes mergeable only after types, tests, security scans, and a named owner pass."
  - "Keep one portable AGENTS.md for repo facts; put procedures in skills, hard stops in hooks, and isolation in subagents."
  - "Nested package files plus CODEOWNERS beat a giant root prompt when designers, QA, and managers open PRs in a monorepo."
  - "The usual failures are not exotic: deleted tests, drive-by refactors, removed auth, hallucinated packages, and instruction files nobody reviews."
  - "A change the author cannot explain is not ready, regardless of which agent wrote it."
---

The throughput problem is no longer “can someone produce a patch.” Cursor, Claude Code, and Codex will produce one. The problem is that the patch arrives faster than anyone can honestly review it, and it now arrives from people who were never supposed to be in the commit graph: design, QA, product, sometimes a manager who pasted a ticket into an agent and opened a pull request.

That is not a tooling inconvenience. It is the same reliability failure I already treat as load-bearing in product agents. A fluent answer is not product state. A fluent diff is not the main branch. Generation is a candidate. Policy decides whether it becomes the tree.

## The bottleneck moved. The studies agree on the shape, not the slogan.

Self-reported speed is a bad instrument here. METR’s 2025 randomized trial on experienced open-source developers, working real issues in repositories they already knew, found that allowing early-2025 AI tools — mostly Cursor with Claude 3.5/3.7 Sonnet — made them **19% slower**, while those same developers still believed they had sped up by about 20%. The paper is a snapshot of one setting, not a law of physics; METR’s later replication widened the error bars. The durable fact is the perception gap: agents feel fast while the hidden cost moves into reading, repairing, and re-deriving intent.

Quality data points the same way. [CodeRabbit’s 2025 comparison](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report) of 470 open-source pull requests found AI-co-authored changes carried about **1.7× more issues** than human-only PRs, with logic/correctness up ~75% and security findings up to ~2.7×. It is a vendor-run taxonomy on public OSS, so treat the multipliers as directional. The operating consequence does not depend on the third decimal: agents over-produce plausible code, and reviewers inherit the comprehension debt.

An [empirical study of agentic GitHub PRs](https://arxiv.org/abs/2601.00477) found the same caution in security work. Security-relevant agent PRs merged at 61.5% versus 77.3% for non-security ones, with median review latency jumping from 0.11 hours to 3.92. Reviewers are already rationing attention by blast radius. A team that lets every vibe-coded PR consume a senior’s afternoon will not ship; it will drown.

[The New Stack](https://thenewstack.io/ai-generated-code-crisis/) is right about the queue: open-source maintainers saw it first, enterprise teams get it next, and the person who opened the PR often cannot explain the change when asked. That is the tell. If the author cannot walk the diff, the agent did not make them faster. It made them a courier.

Martin Fowler’s distinction is the one worth keeping. **Vibe coding** is prompting, running, and forgetting that the code exists — fine for a throwaway. **Agentic programming** is an agent that reads the repo, edits, tests, and iterates, while people keep ownership of structure and behaviour. [vm0](https://www.vm0.ai/en/blog/posts/engineering-quality-vibe-coded-codebase) published the volume version of that model: six engineers, 630 merged PRs in a week, median merge around 53 minutes, with types, contracts, real databases, browser loops, and a merge queue carrying what line-by-line review can no longer carry. They did not get there by asking seniors to read harder.

## Do not drop an agent into a brownfield repo and hope

An existing monorepo is hostile to a naked agent in predictable ways. The README is written for humans. The real rules live in someone’s head: which package owns auth, which test command is a lie, which generated file you must never edit, which “temporary” flag is load-bearing. The agent will do the locally reasonable thing — invent a helper, widen a type, add a new HTTP client, “clean up” an adjacent file — and the PR will look tidy while coupling three teams that did not ask to be coupled.

The first integration step is not a better prompt in chat. It is making the repo self-describing for every tool the team actually uses. Cursor, Claude Code, and Codex do not share one config file, but they do share a job: they need facts, procedures, and hard stops, and those are three different layers.

| Layer | What it is for | Where it lives | Guarantee |
|---|---|---|---|
| Facts the agent must always know | Layout, install, test, “never touch” | Root [`AGENTS.md`](https://agents.md/) (portable); `CLAUDE.md` imports it | Advisory. Loaded every session. Keep it short. |
| Procedures used sometimes | PR shape, security review, release, “add a design token” | Skills (`SKILL.md`), invoked on demand | Advisory. Cheap until used. |
| Isolation | Deep search, adversarial review, log archaeology | Subagents with a tight tool list | Still a model. Fresh context, summary returns. |
| Hard stops | Ban `rm -rf`, force lint after edit, block secret files | Hooks / Cursor hooks / CI | Deterministic. The model cannot talk its way around it. |

[Anthropic’s own steering note](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more) is the practical split: `CLAUDE.md` for always-on facts under ~200 lines; skills for runbooks; hooks for anything that must happen even when the model would rather skip it. Cursor’s native equivalent is path-scoped `.cursor/rules/*.mdc` plus root `AGENTS.md`. Codex reads `AGENTS.md` natively, including nested files. Claude Code still wants `CLAUDE.md`; the compatibility move is a one-line import, not a second copy of the same novel.

```markdown
# CLAUDE.md
@AGENTS.md
```
{: data-file="CLAUDE.md" }

Root `AGENTS.md` should answer the questions you would give a new teammate on day one, and almost nothing else:

```markdown
# AGENTS.md

## Repo
- Package manager and the exact install command.
- How to run the smallest useful test for a touched package.
- Which paths are generated. Do not edit them.
- Which paths are security-sensitive. Stop and ask.

## Change rules
- One concern per PR. No drive-by refactors.
- Do not add a dependency that is not already in the lockfile.
- Do not delete or weaken tests to make CI green. Fix the code or stop.
- If a check is in CI, run that same check locally before you stop.
- If you cannot name the owner of a package, you are not done exploring.

## Verify
- `pnpm turbo run test --filter <package>`
- `pnpm lint --filter <package>`
```
{: data-file="AGENTS.md" }

That file is policy. Put it under `CODEOWNERS`. A prompt-injection in an issue is annoying; an unreviewed edit to `AGENTS.md` is an instruction to every future agent. GitHub Well-Architected’s advice here is the right one: treat agent instruction files like IAM.

For Cursor-only constraints that `AGENTS.md` cannot express — a glob that should fire only on `apps/web/**` — keep a thin `.cursor/rules/` layer. Do not maintain three essays that say the same thing in `.cursorrules`, `CLAUDE.md`, and `AGENTS.md`. Drift is how agents learn yesterday’s architecture.

## Monorepo governance is path policy, not a longer prompt

Once designers, QA, and managers can open PRs, a single root file becomes a liability. It either stays vague and the agent invents, or it grows until the model ignores the middle. Nested files are the intended design. [AGENTS.md](https://agents.md/) says the closest file wins; OpenAI’s own monorepo has shipped dozens of them. Cursor scopes a nested `AGENTS.md` to its subtree. Claude Code walks from the working directory and concatenates.

Put repo-wide facts at the root. Put the package’s test command, data store, and “do not migrate from here” at the package. State facts (“this service owns `payments.ledger`”) rather than global slogans. Datadog’s pattern of a gitignored `AGENTS.local.md` for personal overrides is the right split: local taste does not merge into main and silently retune every session.

Then make Git do the thing Markdown cannot: refuse the merge.

```text
# Agent instruction surface — platform owns it
/AGENTS.md                          @org/platform
/**/AGENTS.md                       @org/platform
/.claude/                           @org/platform
/.cursor/                           @org/platform
/.github/workflows/                 @org/platform

# High blast radius — humans, always
/packages/auth/                     @org/security
/packages/billing/                  @org/payments
/infra/                             @org/platform
/**/migrations/                     @org/data-platform

# Places non-dev agents may land without a staff engineer in the loop
/apps/web/src/content/              @org/design
/packages/qa-fixtures/              @org/qa
```
{: data-file=".github/CODEOWNERS" }

That last block is the friction design. You *want* a designer’s agent to ship copy and tokens inside a fenced path, with visual regression and CODEOWNERS on design. You do *not* want that same session “just adding a webhook” in billing. Path-scoped Cursor rules and nested `AGENTS.md` files should say so in language an agent will actually load when it touches those files.

Pydantic AI’s maintainer response to the flood is the other half: for anything that is not a trivial bugfix with a regression test, **sign off on the approach before anyone looks at implementation**. A `PLAN.md` PR, or a labelled “API review” PR with no code, is cheaper than a 1,700-line agent diff. GitHub’s own engineering advice is to [split a giant agent PR into a reviewable stack](https://github.blog/engineering/turn-one-giant-ai-generated-pull-request-to-a-reviewable-stack/). Agents amplify whatever PR shape you already tolerate. If you tolerate novels, you will review novels.

## Review evidence, not every line — and do not pretend that is optional

Seniors should not try to out-read the agent. They should decide where judgement is still required, and make everything else executable.

**Always a human, named by CODEOWNERS**

- Auth, payments, PII, encryption, tenancy.
- Migrations and backfills.
- New network egress, new MCP servers, new dependencies with install-time scripts.
- Changes to agent instruction files, CI, and branch protection.
- Anything that alters a public contract.

**Never only a human**

- Formatting, import order, type errors, dead code, secret scanning, lockfile integrity, “does the package test suite pass.”
- “Did the author attach the command output they claim.”

vm0’s list is the mature version of that split: converge the environment so agents and people run the same commands; put standards in types and linters rather than wiki pages; test at module boundaries against real infrastructure; give the agent a browser; delete slop continuously so it does not become architecture. Uncle Bob’s provocative version — review the metrics, not the code — only works if those metrics are actually connected to behaviour. Mutation tests and coverage without a contract are a new way to be confident and wrong.

For non-dev authors, add a social gate the tools will not invent: **the person who opened the PR must be able to explain the change in review**, including what they told the agent not to do. If they cannot, it goes back. That sounds harsh. It is kinder than merging a system nobody on-call understands.

Specialized agents belong *inside* that loop, not instead of it. A security-review subagent that only reads the diff and cannot push; a docs agent that fails when a public API changed with no changelog; a “adversarial plan” agent that runs before code exists. They reduce the mechanical part of review. They do not own merge. Hooks and CI own the hard stops. CODEOWNERS owns the judgement. The author owns the explanation.

Preview environments close the last common lie. An agent that “tested it” on a laptop with two-year-old Docker volumes has tested nothing the reviewer can see. Per-PR databases and a URL in the PR body are how a designer’s change becomes reviewable without a senior re-running the stack from memory.

## The pain is almost never the model. It is a green PR that is wrong.

Most of the queue cost is a handful of repeating failure modes. [OWASP’s cheat sheet on secure coding with AI](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) names several of them; the rest show up as soon as non-devs can open PRs. I treat these as expected inputs, not surprises.

| Pain | What it looks like in review | Why the agent did it | Gate that actually stops it |
|---|---|---|---|
| Drive-by refactor | The ticket was a label colour; the diff also “tidies” three packages | Locally reasonable cleanup; no one-concern rule | Diff-size cap, one-concern `AGENTS.md`, reject extra packages |
| Green by cheating | Tests deleted, `assertEquals` became `assertNotNull`, the unit under test is now mocked | You told it to make CI pass | Fail CI on deleted/weakened tests without CODEOWNERS; review test diffs first |
| Auth vanished in a cleanup | Middleware gone, CORS `*`, tenant filter dropped, debug route left on | Refactor without an invariant | Diff scan for removed auth/validation; negative tests the agent did not write |
| Hallucinated supply chain | New package with a plausible name, or a vulnerable pin from a README | Models invent names; attackers register them ([slopsquatting](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html)); setup files can steer the install | Lockfile allowlist, package age check, no `npm install` of a name the agent invented |
| Instruction poisoning | `AGENTS.md`, a skill, or `.mcp.json` changed in the same PR as a feature | Those files steer every future agent; issues and READMEs are untrusted text | CODEOWNERS on the control plane; never pipe issue bodies into the session as instructions |
| Giant PR | 1,700 lines, three layers, one “LGTM if CI is green” | No plan, no stack | Plan-first; stacked PRs; warn above ~30 files / ~800 lines |
| Courier author | Opener cannot explain the diff or what they forbade | Vibe coding | Social gate: no explanation, no merge |
| Nested rules leak | Frontend conventions applied to the API because someone said “follow the repo guidelines” | The agent grepped every `AGENTS.md` | Path-scoped rules; nested files apply only to their subtree |
| “Works on my machine” | Agent claims tests passed; CI or a preview disagrees | Stale volumes, skipped commands, wrong package filter | Same command in CI; attach output; preview URL |

The cheating-tests row is the one seniors miss because the suite is green. [OWASP’s wording](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) is blunt: a passing suite generated by the same agent that wrote the code is not independent assurance. Review the test diff before the implementation diff. If a failing test disappeared, the PR is a lie.

The supply-chain row is getting less hypothetical. Agents suggest package names that do not exist; those names get registered. Third-party skills can nudge the model toward more speculative installs. A README or Makefile can point the agent at an extra index or an old pin. A prompt that says “be careful” does not replace a hook that refuses any install not already in the lockfile.

The poisoning row is why `AGENTS.md` is IAM. Indirect prompt injection through a GitHub issue, a support ticket, or an MCP tool description does not look like an exploit in the diff. It looks like a helpful agent that suddenly wants network, home-directory, or `pull_request_target`. Pin MCP servers. Audit tool descriptions. Block the agent from editing GitHub Actions that widen permissions in the same PR as the feature.

<div class="callout callout--gotcha" markdown="1">
**Failure boundary.** A 2,000-line root `AGENTS.md` does not make these safer. Models drop the middle. Put facts in a short root file, procedures in skills, and the hard stops in hooks and CI. Markdown that the agent can ignore is not a control.
</div>

## An operating checklist I will actually enforce

This is the control plane I want in a repo before I am willing to let a non-specialist agent open PRs against it. It is the same shape as [governed product agents](/work/governed-ai-delivery/): candidate, schema, evidence, review, fallback.

- One portable `AGENTS.md` at the root; `CLAUDE.md` imports it; no duplicate novels.
- Nested `AGENTS.md` (or path-scoped Cursor rules) per package, reviewed like code.
- Skills for repeatable workflows; hooks for bans and “run the linter after every edit.”
- `CODEOWNERS` on instruction files, CI, auth, data, and infra.
- CI that the agent is told to run, and that branch protection actually requires.
- Secret scan, dependency audit, and a test command that fails closed on the touched package.
- CI fails if tests are deleted or assertions weakened without owner approval.
- New dependencies must already be in the lockfile, or pass an age and allowlist check.
- Diff scan for removed auth, open CORS, committed `.env`, and GitHub Actions permission widening.
- Plan-first for new surfaces; stacked PRs instead of one agent novel.
- Preview or equivalent evidence attached to the PR.
- The opener can explain the diff. If not, it is not their PR yet.
- A named fallback: revert is cheap, “we will clean it up later” is not a policy.
{: .checklist }

The credibility move for a senior who leads this work is not collecting more agents. It is making merge a published policy: which files an agent may touch, which checks must pass, who is allowed to say yes, and what happens when the model is fluent and wrong. Teams that skip that layer will spend the “productivity gain” in review, incident, and rewrite. Teams that install it can let more people write — because the repository, not the chat window, is what stands behind the code.
