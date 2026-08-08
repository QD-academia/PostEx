# Evaluations

The suite contains six separately licensed real-paper cases plus one CC0 fictional case. The real cases cover bioinformatics workflows, RNA-seq tool comparison, pan-cancer prognosis, case-cohort prognosis, and left-truncated survival analysis.

The rubric blocks a candidate when a numerical claim is unsupported, evidence coverage is incomplete, a required approval is missing, scientific conclusions are expanded, or a preflight error remains.

Run:

```bash
python scripts/run_evals.py
```

Each case records its DOI, source URL, asset license, required facts, expected poster roles, forbidden conclusion expansions, and a human-review checklist. The SCI02JITC golden case is connected to an actual evidence-linked content plan and release artifact. All six real-paper cases also have an A0 evaluation-only PPTX/PNG preview under `evals/previews`; these stress-test title length, fact density, minimum typography, logo placement, and layout stability without pretending to be full-paper release posters. Source PDFs are not redistributed for the five non-golden cases.
