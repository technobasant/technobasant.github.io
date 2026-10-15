---
title: "evalproof: LLM evaluation as measurement, gated on what the data can show"
seo_title: "evalproof — Open-Source LLM Evaluation with Judge Calibration and Significance-Gated CI"
hook: "An LLM judge's pass rate is a biased estimate, and a few-point drop on a small suite is mostly noise"
description: "Open-source LLM evaluation: calibrate the judge against gold labels, compare runs on paired cases, and fail CI only on regressions the data can actually show."
date: 2026-10-14
last_modified_at: 2026-10-15
kind: open-source
pillar: ai-systems
related: [governed-agent, realtime-ml, retrieval-bench]
order: 2
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "An 83-question support-assistant suite on local models; a 60-ticket offline suite that CI runs on every commit"
problem: "LLM features ship on a judge model's pass rate and a 'fail if it dropped by X' gate. The judge has error rates of its own, and a few-point delta on a few dozen cases is mostly noise, so the gate either blocks harmless changes or gets loosened until it catches nothing."
decision: "Treat the judge as an instrument to calibrate, compare runs on paired cases with exact tests, and fail only when a drop is both beyond tolerance and significant, with latency and cost budgets on their own exit code."
repo: "https://github.com/technobasant/evalproof"
live_url: "https://evalproof.streamlit.app"
flow: evalproof
cover:
  base: "/assets/images/editorial-evalproof-v1"
  width: 1600
  height: 900
  alt: "Grid of 83 eval cases: 71 unchanged, 8 worse and 4 better after a prompt change, beside three gates — a delta gate that fails it, a paired gate that warns at p = 0.39, and a latency budget that fails it"
  caption: "Twelve of 83 cases changed verdict, too few to separate a 4.8-point drop from noise, so the paired gate warned while the latency budget failed the change."
  link: "/writing/eval-score-drop-twelve-answers/"
metrics: [evalproof_noise_gate, evalproof_latency_p95, evalproof_gold_errors, evalproof_pairwise_flips]
stack: [Python, numpy, Pydantic, httpx, Ollama, "Qwen3", "GitHub Actions", uv]
tags: [applied-ml, ai-agents]
image: /assets/og/og-agents.png
image_alt: "LLM evaluation as measurement — evalproof, open source"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Most LLM evaluation I have seen reports one number: the share of outputs a judge model marked as passing. A release gate then compares that number between two runs and fails if it dropped by more than a few points. Both halves of that are measurement problems presented as engineering ones.

The judge is a classifier. If it passes bad answers at a false-positive rate and good answers at a true-positive rate, its pass rate converges to a weighted mix of the two, not to the true rate — the same classify-and-count bias I worked through in [the prevalence post](/writing/count-prevalence-not-classifications/). And a pass-rate delta on 60 or 80 cases is dominated by a handful of flipped verdicts: two flips out of sixty move a score by 3.3 points.

[evalproof](https://github.com/technobasant/evalproof) is the measurement layer I built for that: how much a judge's verdict is worth, and whether a difference between two runs is real. It is deliberately narrow. Broad frameworks such as promptfoo, DeepEval, Ragas and Inspect run evaluations; evalproof's run file is plain JSON, so it can sit beside them and do the statistics.

## Constraints

Local-first, so results are reproducible and free to re-run: Ollama is the default provider, with Anthropic and OpenAI optional over plain HTTP and no vendor SDK. Every model call is cached by content, and each run records the dataset hash, seed, Ollama version and model digests. The statistics use numpy and the standard library only, small enough to read and to test against hand-worked values. Everything was measured on one Apple M5 with 24 GB of RAM, with `qwen3:1.7b` as the system under test and `qwen3:8b` as the judge.

## Architecture

A suite is one YAML file: a JSONL golden set, the system under test, scorers, an optional judge, calibration settings and a gate. `evalproof run` produces a self-describing run file with every case's output, latency, tokens and scores. Three commands read run files:

- **calibrate** measures the judge against gold labels — confusion matrix, TPR, FPR, Cohen's κ — and reports the raw pass rate beside two corrected estimates, adjusted classify-and-count and prediction-powered inference, each with an interval.
- **compare** pairs two runs by case id and tests the difference: exact McNemar for pass/fail, a paired bootstrap for continuous scores.
- **pairwise** asks the judge to choose between two answers in both orders and reports order-dependent verdicts as ties.

The gate turns a comparison into an exit code: 0 pass (possibly with warnings), 1 quality regression, 3 budget breach, 4 cannot gate, 2 usage error. A composite GitHub Action runs it and writes the report to the job summary.

## In the code

This is the decision behind the headline result. For a pass/fail metric `mc.p_value` is the exact McNemar test on the cases whose verdict changed, so a drop fails only when it is both beyond `max_drop` and significant; the 4.8-point drop on 83 cases took the warning branch, and the latency budget failed the change with its own exit code.

```python
def decide(cmp: Comparison, gate: GateConfig) -> GateDecision:
    # …
    exit_code = EXIT_PASS
    drop_big = mc.delta <= -gate.max_drop
    significant = mc.p_value < gate.alpha
    if drop_big and significant:
        # …
        exit_code = EXIT_REGRESSION
    elif drop_big:
        warnings.append(
            f"{gate.metric} dropped {mc.delta:+.3f}, beyond the {gate.max_drop:.3f} threshold, but "
            f"p={mc.p_value:.3f} ≥ α={gate.alpha}: not distinguishable from noise "
            f"at n={mc.n_paired}. "
            "Add cases before trusting either direction."
        )
    # …
    if (
        gate.max_p95_latency_ms is not None
        and cmp.candidate.p95_latency_ms > gate.max_p95_latency_ms
    ):
        # …
        exit_code = exit_code or EXIT_BUDGET
    # …
    status = "fail" if exit_code else ("warn" if warnings else "pass")
```
{: data-file="src/evalproof/gate.py" }

The full function, including the checks that refuse to gate with exit 4, is in [src/evalproof/gate.py](https://github.com/technobasant/evalproof/blob/main/src/evalproof/gate.py).

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Fail only when a drop is beyond `max_drop` **and** significant | Fail on any drop beyond a tolerance | On small suites most few-point drops are noise, and a gate that fails on noise gets switched off | A real but small regression on a small suite passes with a warning; the only fix is more cases |
| Paired tests on case ids | Compare two pass rates or their intervals | Only cases whose verdict changed carry evidence; pairing uses exactly those | Runs over different datasets cannot be compared at all — exit 4 |
| Treat the judge as a classifier and calibrate it | Trust its pass rate | Its count is biased by its own error rates, and the bias moves with the true rate | Someone has to label a sample, and with 30 labels the corrected intervals were 1.6 to 2.2 times as wide |
| Gate one metric, report the rest | Gate every metric | Several metrics at α = 0.05 each inflate false failures | A regression in an ungated metric is only reported |
| Pointwise verdicts gate; pairwise is a diagnostic | Gate on pairwise preference | Measured: 42.2% of pairwise verdicts flipped with answer order, with a strong length preference | Pairwise sensitivity is given up for gating |
| Local models and a content-addressed cache | Hosted APIs by default | Reproducible, tied to a model digest, free to re-run | Small local models are weaker judges than hosted ones |

## Results

The worked example is a support assistant for a fictional product: 83 questions, 9 of them unanswerable from its facts. The change under test swaps a grounded system prompt for one that always gives "a complete answer".

**The quality drop was not distinguishable from noise.** The judge's pass rate fell 4.8 points, from 8 answers getting worse and 4 getting better while 71 kept their verdict. Exact McNemar gives {{ site.data.metrics.evalproof_noise_gate.value }}, so the gate passed the change with a warning naming the sample size. A delta-only gate with a three-point tolerance would have failed it. The arithmetic of the same test shows why: on 83 cases, no drop smaller than six net cases can reach significance.

**The latency regression was real.** Mean answer length went from 19 to 77 tokens, and p95 latency went {{ site.data.metrics.evalproof_latency_p95.value }}. With a 2,500 ms budget the gate exits 3 and still prints the quality warning.

**The judge was good; the gold was worse than it looked.** Against the regex answer key the 8B judge scored TPR 92.6%, FPR 6.7% and κ 0.78. Of 13 disagreements between them, read by hand, the key was wrong 7 times and the judge 4 — the key could see that the right fact was present but not that a wrong one was absent. Corrected on those cases, the key lands within about a point of the raw judge.

**Pairwise judging preferred the worse prompt.** {{ site.data.metrics.evalproof_pairwise_flips.value }} of pairwise verdicts flipped with the order of the answers. Of the consistent ones, the judge preferred the lower-scoring candidate 42 to 6, mostly where both answers were right and the candidate's was about five times longer.

**It reproduces.** With the cache off, 20 re-run cases gave 20 identical outputs, verdicts and judge reasons. A warm-cache re-run took 0.05 s instead of 363 s. CI runs an offline ticket router on every commit and asserts the gate's exit codes: 1 for a real regression of 11 tickets worse and none better, 0 for 2 worse out of 60.

The analysis behind the gate's design is in [The eval score fell 4.8 points. Twelve answers decided whether it meant anything.](/writing/eval-score-drop-twelve-answers/), and every table is in [MEASUREMENTS.md](https://github.com/technobasant/evalproof/blob/main/MEASUREMENTS.md).

## What the measurements refused to show

**That calibration helps at this size.** Over 200 random gold samples of 30 labels, both corrections removed the judge's 3.6–4.8-point offset on average, but their intervals were far wider than the raw rate's, which already covered the truth every time. Calibration earns its keep on large suites, where the raw interval is narrow and the bias dominates.

**That the gate can see a 4.8-point regression.** Taking this run's rates as the truth, a seeded simulation caught it 13% of the time at 83 cases and needed about 520 cases for an 80% chance. The gate is honest about that rather than sensitive.

**Anything about other models or domains.** One machine, two small local models, one fictional domain, 83 cases, and a judge with thinking disabled. The numbers describe this setup; the method is what transfers.

The first CI runs also caught one of my own bugs: the Wilson interval's lower bound at zero passes came out as 2.8e-17 on x86_64 Linux and 0.0 on arm64 macOS, a subtraction of two equal quantities rounding differently by platform. Version 0.1.1 pins the boundaries exactly.

## What I'd do differently

**Label with people, not a regex.** The answer key was written before any model output was seen and never changed, which kept it honest, but it was wrong more often than the judge. Calibration is only as good as its labels; a real deployment should calibrate against human review.

**Stratify the gold sample.** Five of the answer key's seven errors were on the nine unanswerable questions, where telling an abstention from an invention matters most, and a uniform sample of 30 holds only about three of them. Per-tag sampling and per-tag calibration are first on the roadmap.

**Measure a reasoning judge.** The judge ran without thinking to keep runs fast and deterministic. Whether a reasoning judge earns its latency against the same answer key is the next measurement worth making.
