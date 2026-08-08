# AURORA-12 synthetic golden example

AURORA-12 is a fully fictional, rights-safe manuscript fixture for PostEx. Every person, institution, cohort, feature, endpoint and result was authored for software evaluation. It is not a real study and must not be cited as biomedical evidence.

The source of truth is `manuscript.yaml`. Build the five-page manuscript with:

```bash
python scripts/build_fictional_manuscript.py \
  examples/aurora-synthetic/manuscript.yaml \
  examples/aurora-synthetic/AURORA-12-synthetic-manuscript.pdf
```

The example includes:

- a traceable poster brief and content plan;
- evidence records anchored to manuscript pages and figures;
- approval-gated hero, deletion, palette and structure proposals;
- three poster palettes: PostEx default, user-image fusion and a rights-safe Paimon-inspired cape-gradient theme;
- four original SVG figures;
- an editable logo placeholder;
- no cloud upload, external data, DOI or third-party artwork.

Final poster outputs are generated only after the proposal digests recorded in this directory have explicit approval.

## Generate the three palette variants

Initialize an Artifact Tool workspace, then run the variants sequentially:

```bash
postex generate examples/aurora-synthetic/project-default.yaml \
  --artifact-workspace /path/to/artifact-workspace \
  --office-executable /path/to/soffice
postex generate examples/aurora-synthetic/project-gate-image.yaml \
  --artifact-workspace /path/to/artifact-workspace \
  --office-executable /path/to/soffice
postex generate examples/aurora-synthetic/project-paimon.yaml \
  --artifact-workspace /path/to/artifact-workspace \
  --office-executable /path/to/soffice
```

Each output directory contains editable PPTX, print PDF, PNG preview, portable render diagnostics, an evidence report, and a preflight report. LibreOffice was used as the reproducible PDF-export fallback for the committed artifacts.

| Variant | Palette behavior | Output |
|---|---|---|
| Academic Safe | PostEx default teal, gold and neutral system | `output/default/` |
| Balanced Fusion | User-image-derived teal, sky blue and restrained coral; source image omitted | `output/gate-image/` |
| Visual Signature | Paimon-inspired midnight-navy-to-pale-blue cape gradient with starlight-gold accents | `output/paimon/` |

The Paimon-inspired variant uses separately generated editable SVG copies only after the approved scientific-color unlock. It does not include Paimon artwork, screenshots, logos, fonts, or game assets.

## Generate the Paimon-inspired size family

The homepage size comparison is generated from the same fictional evidence plan and Palette DNA with size-specific layout and preflight rules:

```bash
postex generate examples/aurora-synthetic/project-paimon.yaml \
  --artifact-workspace /path/to/artifact-workspace \
  --office-executable /path/to/soffice
postex generate examples/aurora-synthetic/project-paimon-a1.yaml \
  --artifact-workspace /path/to/artifact-workspace \
  --office-executable /path/to/soffice
postex generate examples/aurora-synthetic/project-paimon-36x48.yaml \
  --artifact-workspace /path/to/artifact-workspace \
  --office-executable /path/to/soffice
```

The generated artifacts are stored in `output/paimon/`, `output/paimon-a1/`, and `output/paimon-36x48/`.
