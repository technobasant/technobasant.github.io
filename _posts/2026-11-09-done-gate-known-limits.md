---
title: "A gate's known limits are its next tests"
seo_title: "Catching coding agents that weaken tests: greenproof 0.4.0"
description: "greenproof 0.4.0 set out to close the limits its own docs listed. Of 744 tamper probes none passes, and honest changes blocked fell from 35 to 18."
date: 2026-11-09 01:19:00 +0545
last_modified_at: 2026-11-09
type: essay
pillar: ai-systems
series: agentic-engineering
series_order: 5
tags:
  - ai-agents
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - AI coding agents
  - test tampering
  - reward hacking
  - adversarial testing
  - definition of done
  - known limitations
mentions:
  - greenproof
  - Claude Code
  - Codex CLI
  - Cursor
  - OpenCode
  - pytest
key_takeaways:
  - "A gate that documents its blind spots has written down the ways past it. greenproof 0.4.0 treated its own known-limits list as the backlog: a probe for each limit before any fix, the tamper and the honest edit beside it."
  - "Of 60 tamper probes aimed at the documented limits, 0.3.1 handled 49 as expected and let 6 through with no finding. 0.4.0 handles 59 and warns on the last. Of all 744 tamper probes, none passes."
  - "The honest side was harder. Of 50 honest edits the limits said would be blocked, 0.3.1 handled 20 correctly and 0.4.0 handles 32. Over all 502 honest probes, false blocks fell from 35 to 18."
  - "On 698 real commits that touched tests, blocks fell from 75 to 66 and false blocks from 21 to 12. Pairing a renamed test with its old self cleared five of the nine false blocks that went away."
  - "Checking this article's examples against the build found a bug the probes had missed: an `npm ci` step in the same job hid a narrowed npm workspace selection. It was fixed before the release, and an example is a probe too."
cover:
  base: "/assets/images/editorial-done-gate-limits-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic: the known limits of greenproof 0.3.1 become probes, each a tamper and an honest edit, run against 0.3.1 and 0.4.0; tamper probes handled as expected go from 49 to 59 of 60, honest ones from 20 to 32 of 50, and false blocks on 698 real commits from 21 to 12"
  caption: "Each documented limit became a probe before any code changed, and both builds ran every probe."
faq:
  - q: "How do you test whether a test-tampering detector can be bypassed?"
    a: "Write edits whose only purpose is to get past it and keep each one as a probe with the verdict it must get, next to the honest edit that looks most like it. Run every probe against the previous release as well as the new build, and replay real commit history, because a rule loosened to clear a false block can reopen a tamper it used to catch. greenproof keeps 1,246 such probes and a harness that runs them against any build."
  - q: "Should a test gate for coding agents publish its known limitations?"
    a: "Yes. Anything in the repository is readable by an agent working in it, so a limit kept out of the docs is not hidden from the agent, only from the people deciding whether to trust the gate. The protection is elsewhere: the gate reads its policy from the base revision, CI runs the same check where the agent's local edits do not count, and the list of limits becomes the next round of probes."
  - q: "What does greenproof 0.4.0 still miss?"
    a: "One tamper probe of 744 only warns: a `-k smoke` that a Makefile adds through `$(if $(CI),...)`, because make functions are not evaluated. A policy script is judged by the kinds of check it runs, not how many times, so removing a second pytest run or swapping one lint tool for another passes. A matcher is only recognised as the top-level operand of an equality. SPEC.md lists the rest under Known limits (0.4.0)."
  - q: "How often does greenproof 0.4.0 block an honest change to tests?"
    a: "On 698 commits that touched tests in click, httpx, zustand and cobra, it blocked 66: 46 correctly, 8 ambiguously and 12 wrongly, against 21 wrong blocks on 0.3.1. The remaining false blocks are mostly checks moved into a helper or loop it does not credit, several exact checks merged into one larger equality, and tests moved to another file and rewritten at once."
---

[The last post](/writing/done-gate-for-coding-agents/) ended on a list. greenproof's SPEC.md had a section called "Known limits (0.3.0)" that named the edits the gate could not see: an expected value replaced by `mock.ANY`, a row dropped from a table a loop checks, a tolerance loosened through a variable, a test script that quietly stopped running `pytest`. I wrote that list because a gate that hides its blind spots asks to be trusted for things it does not do.

A list like that is also a set of instructions. It tells anyone who wants the suite green without fixing the code exactly which edits will get through, and a coding agent working in the repository can read SPEC.md as easily as I can. I don't have evidence that an agent has ever read it for that. I didn't want to find out, so [greenproof 0.4.0](https://github.com/technobasant/greenproof/releases/tag/v0.4.0), released on 9 November 2026, set out to close the list.

**Operating rule.** Treat a gate's known-limits list as its backlog. Before changing any code, write a probe for each limit: the tamper it lets through, and the honest edit that looks most like it. Run every probe against the old build and the new one, replay real history, and publish the limits that are left.

## Probes before fixes

The 0.3.0 list had about forty items in six groups: Python tests, test identity, Go, Rust and JS tests, Makefiles, test-runner configuration and selection, and shell scripts and CI. For each one I wrote probes from the text of the limit alone, before any fix existed. A probe is one edit to a small fixture repository with the verdict it must get. A `TAMPER-` probe is the nearest weakening, and it has to be caught. A `HONEST-` probe is the change the limit wrongly blocks, and it should pass once the limit is closed. There are 110 of them in `bench/probes/spec_040_*.py`, next to the 1,134 from the earlier rounds, and the same harness runs them against any build.

Run against 0.3.1 first, they measured the list:

| Probes aimed at the 0.3.0 limits | 0.3.1 | 0.4.0 |
|---|---:|---:|
| Tamper, handled as expected | 49 of 60 | 59 of 60 |
| Tamper, passed with no finding | 6 | 0 |
| Honest, handled as expected | 20 of 50 | 32 of 50 |
{: aria-label="greenproof 0.3.1 and 0.4.0 against the 110 probes written from the 0.3.0 known limits" }

The six tampers that got through 0.3.1 cleanly were all outside the test files. A deleted root Makefile, so the targets the policy runs went with it. A `-k` filter built by a command substitution. A long script that dropped its test line. `nx run-many` swapped for `nx affected`, and two npm workspace selections narrowed in CI. The other limits mostly produced a warning where a block was due. A warning reaches the agent, but the agent can still stop.

## Four edits 0.3.1 let through

Each of these is a scratch repository with one commit of tests and one commit of tampering, checked with `greenproof check --base HEAD~1 --checks static`. 0.3.1 passes all four.

An expected value replaced by a matcher. `ANY` compares equal to everything, so the assertion still runs and can no longer fail:

```python
from unittest.mock import ANY

def test_add():
    assert add(1, 1) == ANY      # was: == 2
```

```text
BLOCK tests.weakened  tests/test_calc.py:6  test test_add checks less than at the base:
      exact check on `add(1, 1)` loosened to `add(1, 1) == ANY`
```

The matchers it knows are `ANY`, dirty-equals, callee, testfixtures `Comparison`, a class in the file or the test tree whose `__eq__` never reads the other operand, and a function that returns one of those, followed three calls deep.

A row dropped from a table. One assertion in a loop over three cases became one assertion over two. 0.3.1 counted assertions, and there was still one:

```python
def test_add():
    for a, b, want in [(1, 1, 2), (2, 2, 4)]:    # was: ..., (-1, 1, 0)
        assert add(a, b) == want
```

```text
BLOCK tests.weakened  tests/test_calc.py:4  test test_add checks less than at the base:
      table rows reduced from 3 to 2
```

0.4.0 counts distinct rows of a literal list or tuple, whether a loop or `parametrize` reads it. Fewer rows block unless every base row is still among the candidate's rows or a new test's. Rows count toward the check total too, so unrolling a three-row loop into two explicit asserts blocks as well.

A tolerance moved into a name. `pytest.approx` with a literal tolerance was already read. A name was not:

```python
TOL = 0.5

def test_add():
    assert add(0.1, 0.2) == pytest.approx(0.3, abs=TOL)   # was: pytest.approx(0.3)
```

```text
BLOCK tests.weakened  tests/test_calc.py:8  test test_add checks less than at the base:
      exact check on `add(0.1, 0.2)` against 0.3 loosened to a tolerance of 0.5
      (1% of the expected value or more)
```

A module-level number is resolved first, so `TOL = 1e-9` still passes. A name it cannot resolve is read as an unbounded tolerance and blocks.

A test script that stopped running the tests. The policy's test command is `sh scripts/test.sh`, and the script kept its lint line:

```sh
set -e
ruff check .
# pytest        <- removed
```

```text
BLOCK runner.tampered  scripts/test.sh  scripts/test.sh: it changed and it no longer runs
      `pytest` (`sh scripts/test.sh` runs it)
```

0.3.1 blocked a script that lost every check, not one that lost a kind of check while others remained. 0.4.0 compares the kinds of check a policy script runs, reads the scripts it calls into it (four levels deep, 64 files and 1 MiB per file), and follows a script that a Makefile recipe runs.

## The honest side was harder

Closing a tamper is a matter of reading one more construct. Closing a false block means letting an edit through, and every edit let through is one an agent can use. Several fixes went in and came back out for that reason.

The largest single cause of false blocks in real history was a test renamed while its body changed. 0.3.1 saw a test removed and a different one added, and blocked it. 0.4.0 pairs the two when the match is unique and the bodies share most of their tokens: 0.6 in the same file, 0.75 across files, and only for bodies of at least 10 tokens. A paired test then goes through the weakening comparison, so a rename that also drops a check still blocks, now with the reason:

```text
BLOCK tests.weakened  tests/test_calc.py:4  test test_add_integers checks less than at the
      base: checks dropped from 4 to 3
```

The thresholds came from the replayed commits and were then checked against the probes. Below them, or on a tie, a rename stays a removal and blocks.

Go was the case where letting an edit through needed the most care. Go table tests often replace separate `if got != want` checks with a loop over a slice of cases, and 0.3.1 blocked that because the line count of checks dropped. 0.4.0 credits the loop with its rows times the checks in its body, but only for checks that read the row, and only when every number and string from the removed checks is still in the file. The first version credited any loop over the table. A probe then showed what that allowed. Go rejects an unused loop variable, so the obvious tamper discards it:

```go
for _, c := range cases {
	_ = c
	if got := Add(1, 1); got != 2 {
		t.Errorf("x")
	}
}
```

That loop runs the same fixed check three times and earns three rows of credit. A row that is only assigned to `_`, printed or logged now counts as unread, and that loop blocks.

One fix was reverted outright. An edit to an existing `sed -i` rewrite of the tests had always blocked. A work package made a plain name swap only warn, and the fix rounds took that back: it stays a block, as in 0.3.1. That decision costs one false block in the replayed history, in zustand.

## What real history said

The probes come from the same project as the rules, so they show which classes of edit are closed, not a detection rate. The check on that is replaying human commits that nobody gamed: the same 698 test-touching and 394 runner-touching commits of click, httpx, zustand and cobra as last time, on both builds.

| | 0.3.1 | 0.4.0 |
|---|---:|---:|
| Tamper probes: blocked, warned, passed | 687, 50, 7 of 744 | 693, 51, 0 of 744 |
| Honest probes blocked that should not be | 35 of 502 | 18 of 502 |
| Test-touching commits blocked | 75 of 698 | 66 of 698 |
| Of those, false blocks | 21 | 12 |
| Runner-touching commits blocked | 18 of 394 | 19 of 394 |
{: aria-label="greenproof 0.3.1 and 0.4.0 on the full probe set and on replayed commit history" }

Ten blocks cleared and one is new. Nine of the ten were false on 0.3.1: five renamed tests now paired, three Go checks moved into a helper or a literal table loop, and exact checks merged into one equality against a `QueryParams(...)` value in httpx. The new block is httpx `5b5f6d8e1`, which renames `test_url` to `test_complete_url` and drops a `copy_with(scheme=..., port=None)` check that no other test makes. 0.3.1 only said the test was replaced. 0.4.0 says what it lost, and the block is correct.

Read against each diff, the 66 blocks are 46 correct, 12 false and 8 ambiguous. About one honest change in sixty is still blocked wrongly on this history. The rules were tuned on these commits, so expect more on yours.

## The bug the article found

The changelog says `npm test` becoming `npm test -w web` in a workflow blocks: npm ran every workspace before and now runs one. The unit tests agreed. For this article I built the example in a scratch repository with the workflow most projects actually have, `npm ci` and then `npm test`, and the 0.4.0 build passed it.

The cause was one word. The rules treat a script named `ci` as a test task, which is right for `npm run ci`. `npm ci` is npm's clean install, but it matched too, so the job seemed to contain an npm test run over every workspace, and the narrowed step beside it never counted as narrowing. The fix reads npm's own command first: `ci`, `install` and the other subcommands that install or publish are not test runs. Four tests now cover `npm ci` in the same step, in a step of its own, and beside a widened selection. The probes and replays were run again on the fixed build before the release.

No probe had an `npm ci` step beside a narrowed selection. The probes were written from the limits list, and this was not on it. Two probes now do. On 0.3.1 the narrowed run passes, on 0.4.0 it blocks, and the honest widening passes on both. They are in the totals above but not in the first table, which counts only the probes written blind from the list. An example in an article is a claim about what the tool does, so it gets run like one.

## What is still open

SPEC.md has a "Known limits (0.4.0)" section now. The parts most likely to matter:

- **One tamper still only warns.** A `-k smoke` that a Makefile adds through `$(if $(CI),-k smoke,)` runs fewer tests in CI only. Make functions are not evaluated, so the gate sees a computed argument and warns.
- **Kinds, not counts.** A policy script that runs `pytest` twice and loses one run passes, and so does swapping `ruff` for `mypy`, because the lint tools count as one kind. A call to a script that cannot be read, past the depth, file or size limits or missing, might run anything, so that script is not judged by kind at all.
- **Top-level matchers only.** `== ANY` blocks. `== (ANY, 2)` does not, and neither does a matcher class with an inherited or metaclass `__eq__`.
- **Literal tables only.** Row counts apply to a list or tuple bound once and never changed. A table built by `range`, a comprehension or a call falls back to plain counts and warns when the base's table could be read.
- **The 12 false blocks.** Go checks in a helper or loop that 0.4.0 still does not credit, exact checks merged into one larger equality, tests moved to another file and rewritten at once, and the `sed -i` edit above.

The list is shorter than 0.3.0's, and it is still a map. I am keeping it public for the reason I wrote it. An agent in the repository can read everything in the repository, so leaving a limit out of the docs hides it from the people deciding whether to trust the gate, not from the agent. What protects the gate is that its policy comes from the base revision and CI runs the same check where local edits do not count. Each limit in the list is the first probe of the next round.

## The same gate, in two other places

The shape is not specific to tests. [The AI platform architecture](/work/ai-platform-architecture/) ships every prompt, model and semantic-layer change through a [paired evaluation gate](https://github.com/technobasant/ai-platform-architecture/blob/main/decisions/0008-release-gate.md): a drop that is significant on a McNemar test fails, one that is not warns with the sample size needed, and an isolation leak fails outright. [evalproof](/writing/eval-score-drop-twelve-answers/) is the measurement behind that, and [governed-agent](/writing/agent-measured-by-what-it-publishes/) applies it to an agent's writes: nothing it produces becomes state until a schema, a policy and a grounding check pass.

All three split block from warn on purpose and publish what they measured, including how often they are wrong. A gate that blocks too much gets switched off, and one that hides its misses gets trusted for things it does not check. Both failures are the operator's to prevent, with numbers. The rest of [this series](/writing/agents-in-a-real-repository/) is about where those gates go in a repository that agents write to; [the governance post](/writing/coding-agents-repo-governance/) explains why the repository has to review what agents write, and [the knowledge post](/writing/knowledge-for-agents-needs-owners-and-dates/) covers the definitions they read.

## Upgrading

```bash
pipx install --force greenproof==0.4.0     # or: uvx greenproof@0.4.0 check
greenproof check --base origin/main
```

The Claude Code, Codex and Cursor plugins and `greenproof init` pick up the new version through the installed command. OpenCode users can pin [`opencode-greenproof@0.4.0`](https://www.npmjs.com/package/opencode-greenproof) in `opencode.json`. Every number above, with the raw per-probe and per-commit results and the commands to reproduce them, is in the repository's [MEASUREMENTS.md](https://github.com/technobasant/greenproof/blob/main/MEASUREMENTS.md), and the full list of changes is in the [0.4.0 changelog](https://github.com/technobasant/greenproof/blob/main/CHANGELOG.md).
