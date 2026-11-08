---
title: "Agents say done. Something outside them has to check."
seo_title: "Stop hooks for Claude Code, Codex CLI, Cursor and OpenCode"
description: "A stop hook for Claude Code, Codex CLI, Cursor and OpenCode that runs the repo's checks and flags weakened tests. On 698 real commits it blocked 75, 21 wrongly."
date: 2026-11-08 01:00:00 +0545
last_modified_at: 2026-11-08
type: essay
pillar: ai-systems
series: agentic-engineering
series_order: 4
tags:
  - ai-agents
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - AI coding agents
  - definition of done
  - agent stop hooks
  - Claude Code hooks
  - test tampering
  - reward hacking
  - adversarial testing
mentions:
  - Claude Code
  - Codex CLI
  - Cursor
  - OpenCode
  - greenproof
key_takeaways:
  - "An agent's report that the tests pass is a claim. The gate has to run the project's own checks itself when the agent tries to stop, with its policy read from the base revision so the change cannot weaken the gate that judges it."
  - "Replayed over 698 human commits that touched tests, the static rules blocked 75: 45 correctly, 9 ambiguously and 21 wrongly."
  - "A benchmark written alongside the rules passed 107 of 107 and missed most of the attack surface. Of 684 tamper probes written to get past the gate, 455 got through 0.2.0, and 438 of those left the tests alone and changed which tests run or whether a failure counts. None get through 0.3.0."
  - "Claude Code, Codex, Cursor and OpenCode each return a block differently, and the OpenCode and Codex failures that mattered only appeared when the real tools ran."
  - "A hook only advises: the agent can edit it, and a hook that cannot start lets the agent stop. The same check in CI, with its rules read from the base branch, is where the gate holds."
cover:
  base: "/assets/images/editorial-done-gate-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic: Claude Code, Codex CLI, Cursor and OpenCode each hand their stop to one greenproof check, which runs the repo's own commands with its policy read from the base revision and ends in pass, block (tests.skipped at line 6) or release (the same tree twice)"
  caption: "The agent's report is a claim. The check that decides runs outside it, at the moment it tries to stop."
faq:
  - q: "How do you stop a coding agent from skipping or deleting failing tests?"
    a: "Check its work outside the agent, when it tries to stop. A stop hook runs the project's own test, lint and type commands, reads the gate's policy from the base revision so the change cannot weaken it, and inspects the diff for removed, skipped or loosened tests. A block goes back to the agent as its next input, and CI runs the same check as the authority."
  - q: "Do Codex CLI, Cursor and OpenCode have stop hooks like Claude Code?"
    a: "Yes. Claude Code has a Stop hook in .claude/settings.json, Codex CLI a Stop hook in .codex/hooks.json and Cursor a stop hook in .cursor/hooks.json. OpenCode 2.x has no command hooks, but a plugin in .opencode/plugins/ can run on the session's idle hook. They answer differently: Claude Code blocks with exit code 2 and a message on stderr, Codex with a JSON decision, Cursor with a follow-up message, and an OpenCode plugin with a synthetic message that continues the same run."
  - q: "How often does a test-weakening gate block honest changes?"
    a: "Replayed over 698 human commits that touched tests in click, httpx, zustand and cobra, greenproof 0.3.0's static rules blocked 75. Read against each diff, 45 blocks were correct, 9 ambiguous and 21 false. The most common false blocks were a test renamed and edited in the same commit and checks moved into a helper or a loop, five of each, then several exact checks merged into one larger equality. The rules were calibrated on those commits, so expect more false blocks on other projects."
  - q: "How do you test a test-tampering detector?"
    a: "Write edits whose only purpose is to get past it, and keep each one as a probe with the verdict it must get. greenproof's 1,134 probes are one-edit changes to small fixtures, 684 tampers and 450 honest edits, with a harness that runs them against any build. Run them against the previous release as well as the new one, honest edits included, because loosening a rule to clear a false block can reopen a tamper it used to catch. Probes written by the same project show which classes of tampering are closed. They are not a detection rate."
---

A coding agent told to make the tests pass will usually make the tests pass. Most of the time it does that by fixing the code. Sometimes it skips the failing test, deletes it, loosens the assertion until it holds, or changes the expected value to whatever the code now returns. Then it reports that all tests pass, and the report is true. The suite is green. It just no longer checks what it was written to protect. Research on coding agents calls this reward hacking: the agent satisfies the check it is graded on instead of the goal the check stands for.

I wanted that report treated as a claim, not a fact. The obvious time to check it is the moment the agent tries to stop, and every coding agent I use now has a stop hook there. Each one exposes it differently, though, and two of the failures that mattered only showed up when the real tools ran.

**Operating rule.** Check an agent's "done" outside the agent, when it stops. Run the project's own commands, read the gate's rules from the base revision so the change cannot edit its own judge, and name each weakened test with a rule, a file and a line. Let an agent that stops twice on the same tree go, so it can tell you why. Keep the same check in CI, because that is the only place it cannot be edited around.

The tool is [greenproof](https://github.com/technobasant/greenproof), an open-source definition-of-done gate I wrote for this. Version 0.2.0 added a plugin for Claude Code, Codex CLI and Cursor and a plugin file for OpenCode 2.x. [Version 0.3.0](https://github.com/technobasant/greenproof/releases/tag/v0.3.0) rewrote most of the rules after a week of trying to break them, and [0.3.1](https://github.com/technobasant/greenproof/releases/tag/v0.3.1), released on 8 November 2026, fixes a hang when the check is interrupted. It uses only the Python standard library and makes no model calls. Every number and agent run below is recorded in the repository's [MEASUREMENTS.md](https://github.com/technobasant/greenproof/blob/main/MEASUREMENTS.md), with the raw results and the commands to reproduce them. [The first post in this series](/writing/coding-agents-repo-governance/) argued that the repository has to review what agents write; this is the part of that review a machine can do before the agent hands over.

## What "done" has to measure

The check has three parts, and each one closes a gap that the agent's own report leaves open.

1. **It runs the commands itself.** The lint, type, test and build commands named in `.greenproof.toml` run now, on the candidate tree. A stale run, or one that never happened, cannot be reported as green.
2. **It reads its policy from the base revision.** The commands and rules come from the commit the work started from. An agent that edits `.greenproof.toml` in the same change to drop the test command is reported for it, under `policy.changed`, not obeyed.
3. **It reads the diff for weakening.** Removed, skipped, focused and loosened tests, expected values changed while the code stayed the same, new suppression comments, and edits to runner or CI configuration each have a rule id.

Not every rule blocks. Deleting, skipping, focusing or weakening a test, editing the policy, and narrowing the test runner or CI do. A changed expected value, a new suppression comment, a test that mocks the function it asserts on, and production code that special-cases a literal from the tests only warn, because honest work does all of them. The gate is a diff heuristic and a command runner, not a proof that the code is correct.

This is what an agent gets back when it adds a skip marker to a test:

```text
greenproof: not done.
  BLOCK tests.skipped  tests/test_shop.py:6  `@pytest.mark.skip` added to test_refund
Fix the code, not the check. Do not delete, skip or weaken tests, or edit CI or test
configuration to get green. If the requirement itself changed, stop and tell the user
which test and why. Never run `greenproof accept`; accepting a finding is the user's call.
```

The message is short on purpose, because it lands in the agent's context. The last line matters as much as the finding. Accepting a finding is a maintainer's decision, made with a `/greenproof accept` comment on the pull request, and the agent is told it is not its call.

## What it costs on commits nobody gamed

A gate that blocks honest work gets switched off, so the first number I wanted was how often it blocks commits that were not trying to cheat. `bench/replay.py` takes up to 200 recent commits that touch a test file in a project, commits each parent as the base, applies the commit and runs the static checks. These are human commits on maintained projects, not agent output.

| Project | Commits | Blocked, 0.2.0 | Blocked, 0.3.0 | Rate, 0.3.0 |
|---|---:|---:|---:|---:|
| pallets/click | 132 | 8 | 8 | 6.1% |
| encode/httpx | 200 | 30 | 30 | 15.0% |
| pmndrs/zustand | 166 | 9 | 13 | 7.8% |
| spf13/cobra | 200 | 23 | 24 | 12.0% |
{: aria-label="greenproof 0.2.0 and 0.3.0 static checks replayed over 698 test-touching commits in four open-source projects" }

That is 75 blocks in 698 commits on 0.3.0, against 70 on 0.2.0. I read every block against its diff, with a model's help, and committed each verdict and its reason so anyone can check them. Forty-five were correct: the commit really did remove or weaken checking, usually on purpose, for example by deleting a feature together with its tests. Nine were ambiguous. Twenty-one were false, because the checking was still there in another form. On 0.2.0 the static check took a median of 258 to 390 ms per commit. I did not time 0.3.0 again, because the machine was loaded when I measured it.

0.3.0 added five blocks and cleared none. Four are zustand workflow steps that rewrite test files before the tests run, which 0.2.0 did not read: two turn tests into `it.skip`, which is correct to block, one strips `@ts-expect-error` lines for an older TypeScript, which is ambiguous, and one edits a rewrite that was already there and is read as a new one, which is false.

The false blocks have a shape. Assertions moved into a helper or a loop count as one check, so a Go test that now calls a helper looks weaker than it is. Several exact checks merged into one larger equality lower the count while the test gets stronger. A test renamed and edited in the same commit pairs with nothing, so it reads as one test removed and another added. Those are the limits of counting assertions in syntax trees and lines, and MEASUREMENTS.md lists each one by commit hash. The rules were calibrated on these same commits, so on a project they have not seen, expect more than 21 false blocks in 698.

## What the benchmark missed

Before 0.2.0 shipped, all 107 benchmark cases were met: every tamper caught and no legitimate change blocked. The same project wrote the cases and the rules, so that showed the rules did what their author expected. It said nothing about an edit written to get past them.

So for 0.3.0 I tried to break it. Over several review rounds, agents were asked for tampers the rules let through and honest edits they blocked, and reviewers who had not seen my cases wrote more. Each finding became a probe: one edit to a small fixture, with the verdict it must get. The repository keeps 1,134 of them, with a harness that runs them against any greenproof build.

| | 0.2.0 | 0.3.0 |
|---|---:|---:|
| Tamper probes that pass with no finding | 455 of 684 | 0 of 684 |
| Honest probes blocked | 87 of 450 | 2 of 450 |
| Benchmark tampers caught, controls blocked | 67 of 67, 0 of 40 | 67 of 67, 0 of 40 |
{: aria-label="greenproof 0.2.0 and 0.3.0 against 1,134 adversarial probes and the 107-case benchmark" }

Of the 455 tampers that got through 0.2.0, 438 never touched a test. They changed which tests run, or whether a failure counts. `PYTEST_ADDOPTS` with a `-k` filter in a workflow's `env`. A dash in tox's `commands = -pytest`, which tells tox to ignore the exit code. `jest --changedSince=origin/main`, which runs only the tests related to files changed since that branch. A `GNUmakefile` that includes the `Makefile` and redefines `test` with `-k "not integration"`; GNU make reads it first. An `exit 0` at the end of a local script the workflow calls. 0.3.0 reads tox and nox sessions, Makefile includes and conditionals, monorepo package filters, test-selection settings and environment variables, and CI steps through composite actions, scripts and `bash -c`.

Three things from those rounds changed how I test the gate. Loosening a rule to clear a false block reopened tampers it used to catch, so from then on every round ran against the previous build and 0.2.0, honest probes as well as tampers. A gate that runs past its hook timeout lets the agent stop, so a slow parse is a bypass, and the readers work within budgets instead of truncating silently. And one agent fixing rules rewrote the probes' expected verdicts to match its code. Probes are now never edited to fit. The probes still come from the same project. They show which classes of tampering are closed, not how often tampering in the wild gets caught, and SPEC.md lists the limits that are still open. [The next post](/writing/done-gate-known-limits/) turns that list into probes and closes most of it in 0.4.0.

## Stop hooks in Claude Code, Codex, Cursor and OpenCode

All four agents let a hook run when the agent tries to finish. What the hook can send back differs, and that decides how a block reaches the model.

| Agent | Where the gate runs | How a block reaches the model | How the gate lets go |
|---|---|---|---|
| Claude Code | `Stop` hook in `.claude/settings.json` | Exit code 2, with the message on stderr | `{"continue": false}` and a note for the user |
| Codex CLI | `Stop` hook in `.codex/hooks.json`, once the user trusts it with `/hooks` | `{"decision": "block", "reason": ...}` | `{"continue": false}` and a note |
| Cursor | `stop` hook in `.cursor/hooks.json` | `{"followup_message": ...}`, sent as the next prompt | An empty answer |
| OpenCode 2.x | A plugin in `.opencode/plugins/`, on the session's idle hook | A synthetic message, the next user input in the same run | A console warning |
{: aria-label="How Claude Code, Codex CLI, Cursor and OpenCode return a block and a release from a stop hook" }

`greenproof init` writes those files. For Claude Code, the stop hook is one command entry in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uvx greenproof@0.3.1 check --hook claude",
            "timeout": 960
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact|fork",
        "hooks": [
          {
            "type": "command",
            "command": "uvx greenproof@0.3.1 session-start --hook claude"
          }
        ]
      }
    ]
  }
}
```
{: data-file=".claude/settings.json" }

The timeout comes from the policy: the per-command timeout times the number of commands, here 900 seconds for one test command, plus a minute, capped at an hour. The command is pinned through `uvx` because greenproof was not on the PATH when `init` ran. The `SessionStart` hook records where the session began, so the gate judges the session's work against that point, and tells the agent which commands will run. The plugin installs the same two hooks without touching the repository: `claude plugin marketplace add technobasant/greenproof`, then `claude plugin install greenproof@greenproof`. Codex CLI takes the same marketplace with `codex plugin marketplace add technobasant/greenproof`, then `codex plugin add greenproof@greenproof`.

Every row shares one design problem: a block must never become a trap. An agent that cannot fix something, because the requirement changed or the suite was red before it started, has to be able to stop and say so. greenproof keeps a little state per worktree in the git directory. If the agent stops again with exactly the tree it was blocked on, it is released: it was told, and chose not to change anything. A session that keeps failing is released on its eighth consecutive failed stop.

In the Claude Code run that is what happened. Asked to add `@pytest.mark.skip` to a test, the agent was blocked with `tests.skipped`. It stopped, said why, and asked the user what to do. It did not revert the skip, and it did not try to accept the finding. Its next stop, on the same tree, was released.

Codex CLI, asked to change a business rule and skip the test that then failed, refused the skip on its own: it read the rules `greenproof init` adds to AGENTS.md, changed the code and left the test failing. The stop hook blocked because the test command failed. The next stop, on the same tree, was released, and the agent's last message named the assertion that conflicted with the request and said it would not skip or weaken the test.

Installing the gate twice raised a subtler problem. A user can have both the plugin and the project hooks that `greenproof init` writes, and Claude Code runs both for one stop, in parallel; it does not deduplicate plugin hooks against settings hooks. Claude Code and Codex also let one hook's `continue: false` override every other hook's block. Without coordination, the second hook would find the first one's block, apply the same-tree rule and release, and every block would become a release. greenproof now takes a lock in the git directory and records each stop's decision against a fingerprint of the hook's input, so the second hook replays the first one's decision. In a real Claude Code run with both installed, both copies blocked the first stop with the same finding and both released the second: one decision per stop, delivered twice.

## What only a real run showed

The tests for each adapter were written against each vendor's documented format, and they passed. Two failures still waited for the real CLIs.

**OpenCode never told the plugin a session had started.** OpenCode has no command hooks, so greenproof ships a JavaScript plugin. Its first version wrote the session marker, the base the work is judged against, when it saw a `session.created` event. I ran OpenCode 2.2.1 for real against a fake OpenAI-compatible model server. The harness plays the misbehaving agent itself: it edits the tree between two messages, and the fake model never calls a tool. Five of six checks passed. The idle hook fired, the synthetic message reached the model as its next input, the user-level plugin directory loaded, and two copies of the plugin in one process continued a stop only once. The session-start check saw zero calls.

The cause is in OpenCode's plugin adapter. `ctx.event.subscribe` returns an async iterator that only starts listening on its first `next()`, and OpenCode publishes `session.created` before the plugin's loop gets there. Nothing replays it. No test against the documented event list could have caught that, because the event is documented and real; it just arrives before anyone can hear it. 2.x has no session-start hook either. The fix runs session start from the `prompt` session hook, on the first prompt the plugin sees for a top-level session: `startup` when the session has no earlier assistant message, `resume` when it does. The rerun passed seven of seven, including a `--continue` run in a new process that sent `resume` for the same session.

**Codex's sandbox would not let the agent run the gate.** The stop hook worked in the Codex run above. But the AGENTS.md section greenproof writes tells agents to run `greenproof check` themselves before saying a task is done, and inside Codex's `workspace-write` sandbox that failed with exit code 4. greenproof snapshots the candidate tree into git objects, and the sandbox denies writes under `.git`. The fix keeps the snapshot in a temporary object store that borrows the repository's objects through git's alternates. It skips the revert check, which the stop hook still runs outside the sandbox, and says so in the report. A test reproduces the failure on macOS with a `sandbox-exec` profile that denies writes to the git directory.

Cursor is the one adapter I have not run end to end yet. Tests written against Cursor's documented hook format cover its input and output, and that is all I claim for it.

<div class="callout callout--note" markdown="1">
**Boundary.** Hooks are advisory. The agent shares your shell: it can edit the hook files and greenproof's state under the git directory, or run the check and ignore it. Every supported agent treats a hook that cannot start as a non-blocking error, so without `greenproof` or `uv` on the agent's PATH there is no gate. The replay numbers are static checks on human commits, not agent sessions, and the probes were written by the project they test. The end-to-end runs are single scenarios that show the wiring works, not rates.
</div>

## Where the gate actually holds

The hook gives the agent the verdict while it can still act on it, which is when fixing the code is cheapest. Otherwise the skip gets explained, or missed, in review. But the hook is not a security boundary, for the same reason [a prompt is not tenant isolation](/writing/prompt-is-not-tenant-isolation/): it sits where the thing it constrains can reach it. The gate holds in CI, where the same `greenproof check` runs on every pull request with its policy read from the base branch, and nothing the agent edited on a local machine counts. `greenproof init --ci github` writes that workflow, and there is a GitHub Action for teams that prefer one.

That split is the useful decision for anyone [running agents in a real repository](/writing/agents-in-a-real-repository/). Put the check in the agent's stop hook for speed and in CI for authority, and make both read the rules from where the change cannot reach them. Expect honest changes to be blocked, about one in ten on the history I measured. Most of those blocks are right, because the change really did remove checking; about one in thirty-three changes is blocked wrongly. Give a maintainer a recorded way to accept them. An agent will report done either way. The point is that the report stops being the evidence.
