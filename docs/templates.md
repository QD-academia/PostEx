# PostEx™ official template contract

v0.4 accepts official pre-annotated templates through the shared renderer. Each family contains `template.yaml` and three independently rendered and reviewed variants:

| Variant | Width | Height |
|---|---:|---:|
| A0 landscape | 46.811 in | 33.110 in |
| A1 landscape | 33.110 in | 23.386 in |
| 36×48 landscape | 48 in | 36 in |

The three production families are Bioinformatics Pipeline, Observational Cohort, and Visual Results. Every size includes an actual `.pptx`, `.png`, render spec, layout inspection, and object inspection. A production `.pptx` declares role-tagged content and logo placeholders, minimum font sizes, asset license, checksum, and renderer fixtures.

Every generated poster uses an independent `POSTEX_PROVENANCE_MARK` object unless an exact omission approval is current. Template fixtures use `PX-00000000`; project exports replace it with a deterministic source ID.

Do not create one master file and scale it blindly. Review font sizes, margins, captions, chart detail, geometry, and print output for each size. Reject macro-enabled or unlicensed files.

## Logo slots

Before layout, collect one of three branding decisions:

1. `none`: remove logo slots without leaving accidental gaps.
2. `placeholder`: retain labeled, editable slots with an explicit role and position.
3. `provided`: replace each matching slot with a user-supplied SVG or transparent PNG.

Supported roles are institution, laboratory, funder, conference, and other. Preserve each supplied logo's aspect ratio, do not recolor it without approval, and record its source and license. Preflight warns about insufficient resolution, opaque backgrounds, cropping, missing alternative text, or unknown provenance. PostEx must never invent an institutional logo.
