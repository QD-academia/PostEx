# Evaluations

The suite contains five separately licensed real-paper cases plus two CC0 fictional cases. The real cases cover bioinformatics workflows, RNA-seq tool comparison, case-cohort prognosis, and left-truncated survival analysis. The fictional cases include the fully rendered AURORA-12 golden example.

The rubric blocks a candidate when a numerical claim is unsupported, evidence coverage is incomplete, a required approval is missing, scientific conclusions are expanded, or a preflight error remains.

Run:

```bash
python scripts/run_evals.py
```

Real-paper cases record DOI, source URL, asset license, required facts, expected poster roles, forbidden conclusion expansions, and a human-review checklist. AURORA-12 is connected to an actual evidence-linked content plan, fictional source PDF, and release artifacts. Five real-paper cases plus AURORA-12 have A0 evaluation previews under `evals/previews`; these stress-test title length, fact density, minimum typography, logo placement, and layout stability without pretending that real-paper previews are full-paper release posters. Real-paper PDFs are not redistributed.
