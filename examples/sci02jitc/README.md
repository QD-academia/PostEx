# SCI02JITC shared-core golden example

This separately licensed example is the release acceptance case for the shared `postex` Python core. It starts from `SCI02JITC.pdf` and produces an editable A0 PPTX, print PDF, PNG preview, locally extracted page text, evidence report, and preflight report.

The project uses the approved PostEx default palette and an editable institution-logo placeholder. Manuscript text remains local; no OpenAI or Anthropic request is made.

## Rebuild

Initialize an Artifact Tool workspace with the Codex Presentations skill, then run:

```bash
postex generate examples/sci02jitc/project.yaml \
  --artifact-workspace /absolute/path/to/artifact-workspace \
  --office-executable /absolute/path/to/soffice
```

The command performs:

1. local PDF extraction and source SHA-256 verification;
2. current palette- and deletion-approval digest verification;
3. claim-to-evidence coverage validation;
4. rendering through the official `bioinformatics-pipeline/a0-landscape` contract;
5. editable PPTX and PNG generation;
6. LibreOffice PDF export;
7. physical-dimension, typography, evidence, approval, and branding preflight.

## Acceptance result

- Evidence coverage: 100% across eight poster blocks.
- PPTX, PDF, PNG, and layout dimensions verified as A0 landscape.
- Primary body text: at least 28 pt.
- Scientific source images embedded without recoloring.
- Artifact Tool and LibreOffice renders visually reviewed.
- PowerPoint overflow test: passed.

See `ASSET_LICENSES.md` before redistributing the paper, figures, or generated poster.
