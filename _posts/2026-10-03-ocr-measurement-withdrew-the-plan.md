---
title: "The OCR plan said fix the photographs. Its first measurement withdrew it."
seo_title: "OCR accuracy on clinic records: measure the premise before the fix"
description: "An OCR plan blamed skewed, creased phone photos for lost accuracy. Its first step, a per-defect cost table and a deskew test, showed capture cost nothing."
date: 2026-10-03 09:00:00 +0545
last_modified_at: 2026-10-03
type: essay
tags:
  - applied-ml
  - data-quality
toc: true
featured: true
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - OCR evaluation
  - document information extraction
  - confounding in error analysis
mentions:
  - RapidOCR
  - PaddleOCR
  - ONNX Runtime
  - PostgreSQL
cover:
  base: "/assets/images/editorial-ocr-measurement-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic of a phone capture flowing through OCR, a parser and a scorer, with document type exposed as the confounder behind the apparent capture-defect cost"
  caption: "The defect looked expensive until document type was held constant. Then it cost three thousandths of an F1 point."
faq:
  - q: "Do skewed or creased phone photos hurt OCR accuracy on clinical documents?"
    a: "On this corpus, not measurably. Pages with perspective skew or creases looked better or worse only because defects cluster by document type. Within handwritten pages, skew scored 0.202 against 0.205, and a causal deskew test moved character yield by a net 5 characters in about 3,838."
  - q: "Why tune OCR extraction against F0.5 instead of F1?"
    a: "Because the errors are not priced equally. A missed row costs a clinician some typing beside the photograph; an invented row with a plausible name and number can be accepted into the record. F0.5 weights precision four times as heavily as recall, and wrong-value rate is tracked as its own metric because no F-score surfaces it."
  - q: "How do you tell whether the OCR or the parser is the bottleneck?"
    a: "Audit every missed truth row against its own page's OCR text. If most of the row's words are present, the parser dropped it and layout work can recover it. If they are absent, the recogniser never read it and no parser will. On handwritten diagnoses only 15% of missed rows were present at all."
  - q: "Does adding OCR workers make a document queue faster?"
    a: "Only if cores are free. With compare-and-set leases, scaling to three workers was safe, but six pages took 14.3 s with one worker and 16.7 s with three, because each ONNX Runtime session took every core it could see."
key_takeaways:
  - "A defect-cost table is only evidence once the confounder is held constant: some defect pages scored better only because those defects cluster on lab reports."
  - "Within handwritten pages, perspective skew cost 0.003 F1, and an applied deskew moved character yield by a net 5 characters out of about 3,838, so four image-quality work items were withdrawn."
  - "The real loss sat in document structure: printed forms filled in by hand scored 0.101 F1 against 0.543 for clean printed reports."
  - "Design the scorer before reading the output: separate boundary from content, report near-name matches apart, and give correct refusals and unscorable pages their own states."
  - "A missed row costs typing and a wrong value can reach a patient, so the one absolute target is never being silently wrong on a value."
---

The plan was sensible, and it was written down before any of it was built. Clinicians photograph paper records on a phone; the OCR pipeline turns each page into a draft a clinician reviews; accuracy on handwritten pages was poor. An audit of the corpus had found pages photographed at an angle, pages with a crease through the middle, a page shot sideways, and one with a keyboard in frame. The plan concluded that roughly 40% of the corpus carried a capture defect that cost measurable accuracy, and queued perspective correction, illumination normalisation, sharpening and binarisation to fix it.

Its first step was to build a per-defect cost table before doing any of that work. Built, the table said the defects cost approximately nothing. Four image-quality work items were withdrawn the same day, and the commit that withdrew them is the one I would show anyone joining the project.

**Operating rule.** A plan's premise is a hypothesis with a price on it. Measure the premise first, hold the obvious confounder constant, and when the number disagrees with the plan, withdraw the plan rather than reinterpret the number.

This is a records product I am building for small outpatient clinics in Nepal. The engine is RapidOCR on ONNX Runtime with PP-OCRv6 models, plus PP-OCRv5 models for Devanagari, which v6 does not cover. Nothing in this essay depends on the engine choice; it depends on how the measurement was set up.

## The scorer came before the output

The measurement was only possible because the scorer had been designed before anyone tuned against it, and most of its rules exist because a naive version of the metric would have rewarded the wrong behaviour.

**Boundary and content are scored separately.** Boundary is where the document sits in the photograph, scored by IoU and by how much of the true page a crop kept. Content is what the document says as structured clinical fields, scored by field-level matching. A pipeline can read every character and file it under the wrong heading, or crop perfectly and extract nothing. One aggregate number hides which of the two broke.

**Near-name matches count, and are always reported apart.** OCR on handwriting misreads a character or two of a name. Counting that as both a miss and an invention charges one error twice and hides that the pipeline found the right row. So a prediction within a normalised edit distance of 0.25 of an unclaimed truth row, with no equally close rival, matches — and every section reports `found_by_near_name` beside `found`, so a tolerance-assisted score is never quoted as an exact one.

**A correct refusal is not a zero.** Some pages carry no patient result at all — the back page of a lab report with the laboratory's interpretation key, for instance. A pipeline that emits nothing there is right. Scored naively, that page is F1 0.0 for giving the right answer, which teaches anyone tuning against the metric to invent results on exactly the pages where inventing them is most dangerous. Those records are marked `correct_refusal`, counted, and kept out of the mean.

**A page the scorer cannot see is not a page with nothing on it.** The first version of the refusal rule was too generous: a hand-drawn charting sheet whose only content belonged to no scored section came back as a correct refusal. It is now `unscorable`, listed with the sections responsible, and reported as a coverage gap in the suite rather than a pass.

A sketch of those states, simplified from the evaluation module. The names in the example are invented.

```python
# Simplified sketch, not the repository code. Example strings are invented.
NEAR_NAME_MAX = 0.25  # normalised edit distance

def classify_page(truth_rows, predicted_rows, scored_sections):
    if not truth_rows and not predicted_rows:
        if page_has_content_outside(scored_sections):
            return "unscorable"        # a gap in the suite, reported as one
        return "correct_refusal"       # counted, kept out of the mean
    return "scored"

def match(pred, unclaimed_truth):
    exact = [t for t in unclaimed_truth if norm(t) == norm(pred)]
    if exact:
        return exact[0], "found"
    close = sorted(unclaimed_truth, key=lambda t: ned(norm(t), norm(pred)))
    if close and ned(norm(close[0]), norm(pred)) <= NEAR_NAME_MAX \
            and not tied(close, pred):
        return close[0], "found_by_near_name"   # e.g. "Tab Exampline" vs "Tab Exarnpline"
    return None, "spurious"
```
{: data-file="scorer_sketch.py" }

Two further rules shaped what could be quoted. The objective is F0.5, not F1, because the two error types do not cost the same: a missed row costs a clinician some typing with the photograph beside them, while an invented row with a plausible name and value can be accepted into the record. And a number may only be quoted with its denominator. When content labels grew from 19 pages to 48, micro-F1 *fell* from 0.479 to 0.257 while true positives rose from 26 to 92. Extraction had not got worse; the denominator had become honest.

The scorer also caught itself once. Classifying the remaining narrative "fabrications" showed that 23% of them were the same truth text cut at a different sentence boundary — one radiology finding labelled as one row and extracted as two, so the second sentence, correctly read, scored as an invention. Those are now reported in their own `resegmented` column. A rule that "improved precision" by suppressing correctly-read prose would otherwise have scored as a win.

## What the cost table actually said

The table compares mean F1 of pages carrying each capture attribute against pages without it, over the 97 pages with full content labels.

| Attribute | Pages | F1 with | F1 without | Gap |
|---|---:|---:|---:|---:|
| perspective skew | 39 | 0.392 | 0.358 | −0.034 |
| glare | 18 | 0.447 | 0.354 | −0.093 |
| mixed orientation | 10 | 0.624 | 0.342 | −0.281 |
| rotated 90° | 6 | 0.369 | 0.372 | +0.002 |
| partial page | 37 | 0.367 | 0.374 | +0.007 |
| creased | 27 | 0.327 | 0.389 | +0.062 |

Several gaps are negative: pages *with* the defect scored better. That is not a discovery about glare. It is confounding. Nine of the ten mixed-orientation pages are lab reports, and lab reports score well for reasons that have nothing to do with orientation. Defects are not spread evenly across the corpus; they cluster on the documents people photograph in particular ways.

Hold document type constant and the effect disappears:

```text
within handwritten pages only      F1 with defect    F1 without
perspective_skew                   0.202 (n=13)      0.205 (n=26)
creased                            0.205 (n=12)      0.204 (n=27)
```

Correlation still cannot settle a causal claim, so the correction was applied and measured. Hough-line deskew on six skewed handwritten pages, detected angles of 1.9° to 10.0°, then re-OCR and compare character yield: −3, +8, +14, 0, −6 and −8 characters. A net +5 across roughly 3,838 characters, with no consistent direction. That is noise.

<div class="callout callout--gotcha" markdown="1">
**The confounder was in the plan's own evidence.** The original claim quoted the absolute F1 of pages carrying each defect — 0.377 for skewed pages, 0.315 for creased ones — with no comparison group. Low scores on defect pages looked like a defect cost. The within-type cut shows they were mostly the handwritten pages scoring low with or without a crease. Any per-attribute table over a corpus with mixed document types needs that cut before it is allowed to justify work.
</div>

So perspective correction, illumination, sharpening and binarisation were withdrawn for want of evidence. Each can be reopened by a causal test showing a gain on the pages that carry the defect. Three narrower capture items were kept because each had evidence independent of the table: resolving rotation *direction* rather than only the axis (an upside-down page scored 0.000), suppressing background objects so the recogniser stops reading furniture as clinical text, and diagnosing one page that lost an entire left column.

## Where the accuracy actually went

The same table, cut by page class rather than by defect, named the real blockers:

| Page class | Pages | Mean F1 |
|---|---:|---:|
| clean printed report | 29 | 0.543 |
| printed form, not handwritten | 29 | 0.425 |
| handwritten, not a form | 19 | 0.313 |
| printed form filled in by hand | 20 | 0.101 |

Two independent, compounding factors, and neither is image quality. A printed form costs −0.118 F1 on its own and −0.212 in combination with handwriting, across 49 pages. A form is printed labels with handwritten or stamped values, so extracting it is a label-to-value pairing problem: a geometry problem, not a pixel one. Handwriting costs −0.280 and is bound by the recogniser.

The second instrument separated those two. For every missed truth row, I checked whether at least four words in five of that row appeared anywhere in the page's OCR text. Present means the recogniser read it and the parser dropped it. Absent means no parser, vocabulary or layout model would ever reach it.

| Section | Missed rows present in the OCR text |
|---|---:|
| impression | 91% |
| findings | 73% |
| results | 69% |
| medicines | 36% |
| vitals | 35% |
| advice | 25% |
| complaints | 22% |
| diagnoses | 15% |

For printed results and findings, most of what is missed was read and then lost in assembly: layout work recovers it. For handwritten diagnoses, 85% of misses were never recognised. The ceiling there is the photograph and the recogniser, and tuning parsers against it is work spent on the wrong layer.

Two "obvious" fixes for that ceiling were also measured rather than assumed. A quantised vision-language OCR model, run as an optional sidecar on the class of 2-vCPU box this deploys to, took about 7.2 s per page against roughly 1.5 s for the existing engine in the same bench. It did not fix the handwritten field that motivated the test, and it returns no per-line confidence, which is how a doubtful value reaches a clinician flagged. It ships off. And gating extracted results on the recogniser's own confidence did nothing useful:

```text
min confidence   precision   recall
none             0.864       0.571
0.90             0.865       0.545
0.99             0.864       0.441
```

Precision is flat across the whole range while recall falls by almost a quarter. The false positives are not shaky reads; they are confident ones — rows from a second document in the same frame, section judgements, labelling conventions. The gate was implemented, measured and removed, because a knob that only spends recall is worse than no knob.

## Targets per document class, and one that is absolute

The original request was 99% accuracy. On printed lab reports the pipeline now reads result rows at **0.870 precision and 0.590 recall, and gets the value itself right 95.8% of the time**. Record type is detected correctly on every labelled page; the finer document-kind taxonomy, which decides which readers a page is allowed to run, is right on 29% — up from 14% when it was first measured, with no new wrong labels, because a wrong confident kind reaches a clinician with the same authority as a right one. The narrative and handwritten sections are nowhere near those numbers, and the cost table explains why.

A single 99% across all document types is not reachable on this corpus, and I would rather say so now than discover it in month three. So the commitment became a target per class:

| Target | Document class | Why |
|---|---|---|
| ≥ 99% value accuracy on matched rows | printed lab reports | already at 95.8% |
| ≥ 95% precision, ≥ 90% recall | printed lab and typed reports | needs layout and noise work |
| ≥ 90% precision, ≥ 60% recall | printed narrative reports | needs layout work |
| ≥ 85% precision, best-effort recall | handwritten cards | capped by recognition |
| 100% | never silently wrong on a value | the clinical requirement |

The last row is the one that is not negotiable. A missing row costs thirty seconds of typing; a wrong one costs a patient. The audit found three confidently-wrong cases — a qualitative urine attribute filled with another attribute's value, a Fahrenheit temperature that would have been filed as Celsius, and lab analytes filed as bedside vitals — and no F-score had surfaced any of them. Wrong-value rate is now tracked as its own first-class metric beside F0.5.

The same rule governs what may become a committable field at all. Even after the scorer stopped penalising re-segmented sentences, narrative sections ran at 0.253 precision — about three inventions for every real row — so a readability filter refuses rows the recogniser could not read before they can be routed into a typed field. Refused text still appears in a read-only panel beside the draft. Refusing to assert a row has never meant discarding it.

## The queue got the same treatment

OCR runs at 2.9 to 5.8 seconds per page uncached on the development machine, so a 17-page checkup packet is 50 to 100 seconds of worker time. Jobs live in Postgres rather than in a request-scoped background task, so an interpreter restart mid-page cannot silently lose a document. The claim is a compare-and-set decided by affected row count:

```python
won = db.execute(
    update(OcrJob)
    .where(
        OcrJob.id == job_id,
        OcrJob.attempts < settings.ocr_max_attempts,
        or_(
            OcrJob.status == "queued",
            # a lapsed claim means the previous worker died mid-page
            and_(OcrJob.status == "processing", OcrJob.claim_expires_at < now),
        ),
    )
    .values(status="processing", attempts=OcrJob.attempts + 1,
            claimed_at=now, claim_expires_at=deadline)
)
if won.rowcount != 1:
    continue  # another worker took it between the select and the update
```
{: data-file="backend/app/services.py" }

The obvious alternative, `SELECT … FOR UPDATE SKIP LOCKED`, is silently ignored by SQLite in development, which let two runners win the same job. Expressed as a guarded `UPDATE`, the claim is correct on both databases with no dialect-specific locking, and a page abandoned by a crashed worker is recovered when its lease expires.

The plan's next assumption was that more workers would mean faster packets. Measured: three workers did claim three pages concurrently with one attempt each, so scaling was safe. It was not faster. Six text-heavy pages drained in 14.3 s with one worker, 16.7 s with three at four threads each, and 17.1 s with three at three. ONNX Runtime keeps its own intra-op thread pool and ignores `OMP_NUM_THREADS`, so every worker took every core it could see. The numbers went into the compose file's comments so nobody rediscovers them, and the real fix — setting intra-op threads to cores divided by workers — became its own work item.

<div class="callout callout--note" markdown="1">
**Boundary.** The corpus is 198 real clinic captures. Every page carries a coarse classification; 97 carry full field-level content labels, chosen by format family so each family is represented, labelled with model pre-labelling and human review. All figures here are development-set numbers measured on my machine while tuning; the project's own rule is that only a held-out, human-verified split may be quoted as accuracy, so read them as diagnostics. Per-class groups are 19 to 29 pages: a difference of 0.003 F1 is noise, and the six-page deskew test rules out a large, consistent effect, not a small one. The examples in the code sketch are invented. No patient text, value, name or image appears in this essay. This is engineering measurement, not clinical validation.
</div>

## Frequently asked questions

### Do skewed or creased phone photos hurt OCR accuracy on clinical documents?

On this corpus, not measurably. Pages with perspective skew or creases looked better or worse only because defects cluster by document type. Within handwritten pages, skew scored 0.202 against 0.205, and a causal deskew test moved character yield by a net 5 characters in about 3,838.

### Why tune OCR extraction against F0.5 instead of F1?

Because the errors are not priced equally. A missed row costs a clinician some typing beside the photograph; an invented row with a plausible name and number can be accepted into the record. F0.5 weights precision four times as heavily as recall, and wrong-value rate is tracked as its own metric because no F-score surfaces it.

### How do you tell whether the OCR or the parser is the bottleneck?

Audit every missed truth row against its own page's OCR text. If most of the row's words are present, the parser dropped it and layout work can recover it. If they are absent, the recogniser never read it and no parser will. On handwritten diagnoses only 15% of missed rows were present at all.

### Does adding OCR workers make a document queue faster?

Only if cores are free. With compare-and-set leases, scaling to three workers was safe, but six pages took 14.3 s with one worker and 16.7 s with three, because each ONNX Runtime session took every core it could see.

The habit worth keeping is small: when a plan names a cause, its first step should be the table that could prove it wrong, cut by the variable most likely to be hiding behind it. The same discipline — a candidate is not a record until it passes a schema, a scorer and a person — runs through [governed AI delivery](/work/governed-ai-delivery/). More on [applied ML and evaluation](/writing/tags/applied-ml/) and on [data quality and contracts](/writing/tags/data-quality/).
