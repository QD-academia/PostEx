# PostEx v0.2 Product Requirements

## 1. Product definition

PostEx v0.2 is an evidence-linked visual-storytelling system for academic conference posters. It turns PDF, LaTeX/Overleaf, YAML, or JSON research material plus a visual inspiration into an editable PPTX, print PDF, PNG preview, evidence report, preflight report, approval log, and explainable design rationale.

The defining capability is **Palette Fusion**: a role-based visual system and the scientific story jointly influence layout, hierarchy, components, figure treatment, and emphasis. The result must look like a distinct visual identity, not a template with substituted colors.

## 2. Product promise

> From scientific evidence to a visual identity.

1. Understand the research before styling it.
2. Turn image, theme, brand, manual colors, or mood language into Palette DNA.
3. Produce three structurally different design directions.
4. Explain and obtain approval for consequential transformations.
5. Preserve evidence, editability, accessibility, and print safety.

## 3. Scope

- Research profiles: bioinformatics and observational biomedical studies.
- Languages: Chinese and English input/output.
- Sizes: A0, A1, and 36×48-inch landscape.
- Interfaces: shared Python core, CLI, Codex Skill, Claude Code Skill.
- Providers: provider-neutral OpenAI and Anthropic adapters plus local-only operation.
- Canonical artifact: editable PPTX, followed by PDF and PNG exports.

## 4. Functional requirements

### FR-1 Poster Brief

Before content planning or design, record audience, presentation setting, one-sentence takeaway, emphasis, must-keep content, figure-edit permission, logo treatment, visual tone, palette source, content mode, and network/cloud permissions. The user may request recommendations, but the resulting brief must be explicit and reviewable.

### FR-2 Palette DNA

Each palette declares:

- six to ten role-based colors;
- intended usage ratios;
- source type and provenance;
- mood labels;
- card, corner, connector, ornament, gradient, and border behavior;
- semantic color locks;
- poster, color-vision-deficiency, grayscale, and print simulations.

Users can lock colors and request natural-language changes. A palette change invalidates palette and downstream structure approval.

### FR-3 Intelligent fusion

Generate exactly three initial directions:

- `hero-result`: one approved result dominates the hierarchy;
- `visual-journey`: process and evidence sequence organize the page;
- `editorial-story`: asymmetric, magazine-like storytelling emphasizes meaning and impact.

Directions must differ in hierarchy, space allocation, flow, and component behavior even in grayscale. The engine records layout weights, component rules, hero claim, brief digest, palette ID, and rationale.

### FR-4 Hero-result approval

Show the proposed headline result, summary, and evidence IDs. Do not use it as the visual anchor until the exact proposal digest is approved.

### FR-5 Figure intelligence

Detect composite panels and propose crop, split, recomposition, or caption compression. Preserve panel labels and scientific meaning. Do not execute figure edits before approval. Warn about low resolution, small labels, unreadable legends, and raster-only limitations.

### FR-6 Design locks and conversational revision

Allow users to lock copy, figures, regions, palette colors, layout, or logos. Natural-language revision requests are translated into structured mutations. A mutation targeting a lock must fail visibly. Record version differences and downstream approval invalidation.

### FR-7 Explainable design

Generate machine-readable rationale and a self-contained HTML report describing palette origin, use ratios, chosen hero, structural direction, component behavior, protected scientific semantics, must-keep items, and relevant approvals.

### FR-8 Trust and privacy

Parse locally first. Before any cloud request containing manuscript content, disclose provider, fields, exclusions, estimated length, and digest. Do not upload without explicit approval. Treat manuscript text as untrusted data rather than executable instructions.

### FR-9 Content deletion and evidence

Propose deletions with source IDs and reasons. Do not omit content before approval. Every factual poster block must resolve to a stable evidence locator or be visibly marked as synthesis. Preserve numerical values, sample sizes, intervals, effects, units, and significance.

### FR-10 Branding

Ask whether to omit logos, keep labeled editable placeholders, or use supplied assets. Preserve proportions, provenance, accessibility text, and license information. Never invent, reconstruct, or silently recolor an institutional logo.

### FR-11 Rendering and preflight

Render editable PPTX first. Prefer PowerPoint PDF export and document LibreOffice fallback. Check dimensions, typography, overflow, contrast, image resolution, evidence coverage, approvals, branding, semantic locks, and exporter consistency. Add 3 m, 2 m, 1 m, color-vision-deficiency, grayscale, and print simulations as the preflight implementation matures.

## 5. Non-goals for v0.2

- Arbitrary unannotated PPTX import.
- Full desktop WYSIWYG editing or real-time collaboration.
- Automatic raster scientific-figure recoloring.
- Unapproved manuscript upload, deletion, crop, or semantic-color changes.
- Scientific truth validation or clinical decision support.
- Redistribution of third-party character, brand, logo, font, paper, or figure assets without rights.

## 6. Acceptance criteria

- All public JSON/YAML examples validate against schemas.
- Palette DNA rejects invalid colors, missing roles, duplicate roles, and ratios outside tolerance.
- A fusion run returns three unique directions and exactly one recommendation.
- Every candidate binds to the current Poster Brief digest and Palette DNA ID.
- Hero, deletion, figure-edit, palette, and structure approvals are digest-bound.
- Locked elements cannot be mutated silently.
- The HTML rationale is self-contained and includes palette, structure, and scientific guardrails.
- v0.1 configuration and golden rendering remain operational.
- Unit, repository, Skill, and evaluation checks pass.

## 7. Quality targets

- 100% factual claim-to-evidence coverage in `traceable` mode.
- 100% preserved numerical meaning in evaluation cases.
- Three directions remain structurally distinguishable in grayscale.
- Title and takeaway pass 3 m/2 m simulation; key results pass 1 m simulation.
- No overflow, unacknowledged preflight error, stale approval, or silent lock violation.
- At least twelve licensed real-paper evaluations across both launch profiles before beta.

## 8. Release stages

1. `0.2.0a1`: domain models, contracts, CLI fusion plan, rationale, locks, and Skill workflow.
2. `0.2.0a2`: visual Palette Studio previews and role-aware renderer integration.
3. `0.2.0b1`: figure panel detection, revision diffs, and distance simulations.
4. `0.2.0`: two complete research families, cross-platform export checks, print samples, privacy review, and Skill forward tests.
