# PostEx

**Let every study have its own visual identity.**

PostEx is an open-source, agent-friendly academic-poster toolkit for Codex, Claude Code, and the command line. Version 0.2 introduces **Palette Fusion**: it combines evidence-linked scientific content with an image, theme, brand, manual palette, or visual mood to create structurally distinct poster directions—not merely recolored templates.

> Status: `0.2.0a1`. Palette DNA, Poster Brief, three-direction fusion planning, figure-edit approval, design locks, and explainable HTML rationale are runnable. The production renderer remains the v0.1 Bioinformatics Pipeline family while Palette Fusion rendering integration is developed.

## What makes PostEx different

- **Palette DNA:** role-based colors, usage ratios, moods, component language, simulations, and semantic locks.
- **Intelligent fusion:** Hero Result, Visual Journey, and Editorial Story proposals respond to both content and palette character.
- **Explainable design:** every fusion proposal states why it chose its visual anchor, structure, emphasis, and guardrails.
- **User-owned decisions:** cloud upload, deletion, figure editing, palette application, poster structure, and semantic-color unlock are digest-bound approvals.
- **Evidence first:** claim IDs and numerical evidence survive rewriting, translation, and visual redesign.
- **Editable and print-aware:** PPTX is canonical; PDF, PNG, preflight, evidence, and rationale reports accompany delivery.

PostEx v0.2 still prioritizes bioinformatics and observational biomedical research, Chinese/English input and output, and A0, A1, and 36×48-inch landscape posters.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

postex brief-questions
postex validate examples/palette-fusion/project.yaml
postex palette-plan examples/palette-fusion/project.yaml
postex fusion-plan examples/palette-fusion/project.yaml
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

The two design commands create:

```text
examples/palette-fusion/outputs/fusion/
├── fusion-candidates.json
└── design-rationale.html
examples/palette-fusion/outputs/palette/
├── palette-candidates.json
└── palette-studio.html
```

The legacy end-to-end renderer remains available:

```bash
postex generate examples/sci02jitc/project.yaml \
  --artifact-workspace /path/to/initialized/artifact-tool-workspace \
  --office-executable /path/to/soffice
```

## Palette Fusion workflow

```text
local inspect
→ Poster Brief and logo decision
→ evidence-linked content plan
→ hero-result approval
→ deletion and figure-edit approvals
→ three Palette DNA previews
→ palette approval
→ three structural fusion directions
→ structure approval
→ PPTX/PDF/PNG render
→ distance, accessibility, print, and evidence preflight
→ evidence, approval, diff, and design-rationale reports
```

Changing an approved proposal changes its digest and invalidates the approval. Locked copy, figures, regions, colors, layouts, or logos cannot be silently changed in later iterations.

## Repository map

```text
src/postex/              shared Python core
schemas/                 v0.1-compatible and v0.2 JSON contracts
configs/                 defaults and provider examples
skills/                  Codex and Claude Code skill drafts
assets/templates/        three families × three print sizes
examples/palette-fusion/ runnable design-intelligence example
examples/sci02jitc/      licensed real-paper golden example
tests/                   unit and contract tests
evals/                   quality cases and rubric
docs/                    workflows, privacy, rendering, and design contracts
docker/                  container packaging
```

## Compatibility and limits

v0.1 project files remain loadable. The v0.2 alpha generates fusion plans and rationale through the shared Python core; it does not yet promise that all three fusion directions can be rendered by every template family. Raster scientific figures are never recolored automatically. Named-theme examples include no proprietary character artwork or third-party brand assets.

## Licensing

Python code and documentation are Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). Templates and examples have independent license records. Never assume the code license covers source papers, figures, logos, fonts, character artwork, or palette reference images.

See [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), and [CONTRIBUTING.md](CONTRIBUTING.md).
