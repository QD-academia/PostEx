# Changelog

All notable changes follow Keep a Changelog. Versions use Semantic Versioning.

## [Unreleased]

## [0.5.0a1] - 2026-08-10

### Added

- Conference Intelligence schemas for stable conference identity, annual editions, preflight rules, Conference Palette DNA, and registry discovery.
- Schema-validated 2026 Conference Packs for CVPR, AACR, ASCO, ESMO, RSNA, AHA Scientific Sessions, and ESC Congress.
- Explicit Official Requirement, Official Recommendation, and PostEx Recommendation origins with source-bound provenance and verification gaps.
- Declarative conference preflight operators for equality, membership, numeric limits, ranges, presence, absence, and conditional presence.
- Generic Conference Pack to Palette DNA/renderer context adapter with no conference-specific renderer branches.
- GitHub-style Epic/Issue backlog for the 30-pack catalog, Research Archetypes, Conference Canvas Engine, integrated Preflight, and regression testing.

### Changed

- Project schema and package version now accept the v0.5 Conference Intelligence selection contract while retaining v0.1-v0.4 compatibility.
- Palette DNA accepts rights-safe `conference-inspired` sources.
- Conference canvas contracts distinguish exact, bounded, and unspecified official geometry from temporary PostEx canvas recommendations.

### Verification

- ASCO and ESC Congress have verified public 2026 poster/ePoster technical scopes.
- AACR, ESMO, RSNA, and AHA preserve named unverified fields rather than importing prior-year or third-party dimensions.
- 48 tests and 18 subtests pass together with Ruff, strict mypy, repository audit, and diff checks.

## [0.4.0a1] - 2026-08-10

### Added

- Trusted Export provenance label with stable `PX-XXXXXXXX` source IDs and the independent PPTX object `POSTEX_PROVENANCE_MARK`.
- `postex-manifest.json`, JSON Schema, file metadata, input/output SHA-256 records, asset/license references, approvals, and Preflight state.
- Release checks for provenance, omission approval, dimensions, fonts, overflow, effective DPI, contrast, safety margins, mark overlap, integrity, and hashes.
- Approval-gated `postex create <source>` scaffolding.
- Production assets and release-ready goldens for three template families across A0, A1, and 36×48 landscape.

### Changed

- WARNING findings now force draft status; ERROR findings block release-ready output.
- Missing provenance fields in v0.3 and earlier projects default to the visual source mark being enabled.
- Codex and Claude Code Skills now delegate Trusted Export rules to the shared `postex` core.

## [0.3.0a1] - 2026-08-08

### Added

- Built-in 104-palette catalog: 19 Chinese city landmarks, ShanghaiRanking 2026 Top50 university emblems, and 35 Genshin character palettes across seven regions.
- Transparent source-art presentation, six-role palette extraction, 900×1240 WebP card rendering, catalog contact sheets, and redistribution-rights release audit.
- CC0 fictional LUMEN-24 observational fixture and homepage evidence preview.
- Production-rendered Paimon-inspired AURORA-12 examples for A1 and 36×48-inch formats.

### Changed

- Reframed the repository homepage around Paimon-inspired Palette Fusion, with detailed natural-language, user-image, named-theme, brand, and manual palette routes.
- Replaced the homepage size and study-type illustrations with generated fictional-paper examples.
- Scaled A1 typography with the poster geometry and applied a size-appropriate preflight threshold.

## [0.2.0a2] - 2026-08-08

### Added

- Fully fictional CC0 AURORA-12 manuscript fixture with stable evidence IDs, approval records, editable figures, and three production-rendered poster variants.
- Approval-bound palette roles, component behavior, and native stepped-gradient support in the Bioinformatics Pipeline renderer.
- Explicit scientific-color unlock for separately generated editable SVG variants.
- Portable public generation reports that omit machine-specific absolute paths.

### Changed

- Replaced the former real-paper golden example with the rights-safe AURORA-12 synthetic benchmark.
- Updated the landing page and evaluation suite around reproducible three-palette comparison.
- Refined the Paimon-inspired Visual Signature into a cape-gradient system without redistributing character artwork.

## [0.2.0a1] - 2026-08-07

### Added

- Poster Brief model, canonical interview, schema, CLI command, and example.
- Palette DNA roles, usage ratios, moods, component behavior, provenance, semantic locks, and validation.
- Three Palette Studio expression levels with machine-readable and self-contained HTML previews.
- Deterministic Hero Result, Visual Journey, and Editorial Story fusion candidates with a recommendation.
- Digest-bound hero-result, figure-edit, and poster-structure approval subjects.
- Design locks for copy, figures, regions, palette colors, layouts, and logos.
- Self-contained HTML design-rationale report.
- `postex fusion-plan` and a rights-safe named-theme example.
- v0.2 Codex and Claude Code Skill workflows.

### Changed

- Product positioning now centers on evidence-linked Palette Fusion and visual identity.
- v0.1 configurations, approvals, and renderer remain compatible.

## [0.1.0a1] - 2026-08-06

### Added

- Shared Python core, CLI, OpenAI/Anthropic provider boundaries, privacy and deletion approvals, evidence tracing, preflight, and Codex/Claude Skills.
- Logo interview, local PDF extraction, Artifact Tool PPTX rendering, PowerPoint/LibreOffice PDF export, and three-size Bioinformatics Pipeline family.
- Reproducible golden-example workflow and licensed evaluation suite.
