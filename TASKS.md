# PostEx v0.5 — Conference Intelligence delivery plan

This backlog is written as GitHub-style Epics and Issues. A checked item is implemented in the current branch; unchecked items are not implied to exist.

## Epic CI-A — Contracts and registry (P0)

- [x] **CI-001 — Split conference contracts.** Add Draft 2020-12 schemas for identity, edition, rule, palette set, and registry. Acceptance: official rules require provenance and PostEx rules cannot masquerade as official.
- [x] **CI-002 — Establish editioned storage.** Add registry plus `<conference>/editions/<year>` and `<conference>/palettes/<year>` paths. Acceptance: no annual file overwrites a stable identity file.
- [x] **CI-003 — Implement safe registry loader.** Validate referenced files, reject path escape, duplicate IDs/modes, cross-file identity mismatch, missing provenance, and invalid Palette DNA.
- [x] **CI-004 — Add two golden packs.** CVPR 2026 is verified for the declared main-poster scope; AACR 2026 is partially verified for the public e-poster PDF scope and preserves physical-poster gaps.
- [ ] **CI-005 — Add registry audit CLI.** `postex conference list/show/audit` must expose verification, source freshness, rights, and unverified fields.
- [ ] **CI-006 — Add source freshness policy.** Define annual review windows, moved-page detection, edition deprecation, and non-destructive supersession.

## Epic CI-B — Conference Canvas Engine (P1)

- [x] **CI-010 — Define exact/range/unspecified canvas facts.** Keep official canvas and PostEx fallback canvas separate.
- [x] **CI-011 — Emit generic renderer tokens.** Map Conference Palette DNA and canvas metadata into the existing render-spec vocabulary without conference ID branches.
- [ ] **CI-012 — Generate arbitrary native PPTX geometry.** Support exact conference dimensions independently of the current A0/A1/36×48 template assets.
- [ ] **CI-013 — Add range-aware canvas selection.** Choose a reviewed exact canvas inside an official range and display the basis to the user.
- [ ] **CI-014 — Add user override contract.** Preserve custom canvas choices while emitting an official-difference finding.
- [ ] **CI-015 — Validate PDF/PPTX dimension parity.** Acceptance: native PPTX, exported PDF, render spec, and Manifest agree within declared tolerance.
- [ ] **CI-016 — Add geometry regression fixtures.** Cover 2:1, 3:2, 4:3, portrait, and organizer-unspecified cases.

## Epic CI-C — Conference Preflight (P1)

- [x] **CI-020 — Implement declarative rule model.** Support equality, membership, numeric bounds, range, presence, absence, conditional presence, tolerance, origin, level, and source reference.
- [x] **CI-021 — Implement normalized snapshot validator.** Required failures block compliance; organizer recommendations and PostEx guidance remain distinguishable.
- [ ] **CI-022 — Build artifact snapshot adapters.** Derive conference facts from PPTX, PDF, PNG, layout inspection, project settings, and submission metadata.
- [ ] **CI-023 — Add PDF crop/bleed checks.** Detect media/crop/trim boxes and extraneous whitespace where technically measurable.
- [ ] **CI-024 — Merge with Trusted Export Preflight.** Include Conference Pack ID, edition verification, rule results, and source references in report and Manifest.
- [ ] **CI-025 — Add unsupported-rule behavior.** Unknown operators or unavailable facts must fail closed for required rules and remain explicit for advisory rules.
- [ ] **CI-026 — Add human-readable conference report.** Group Official Required, Official Recommended, and PostEx Recommendation with source links.

## Epic CI-D — Research Archetypes (P1/P2)

- [ ] **CI-030 — Define archetype schema.** Record evidence blocks, priority, optionality, layout weights, and compatible research types.
- [ ] **CI-031 — Clinical Trial archetype.** Cohort flow, endpoints, safety, effect estimates, and clinical implication.
- [ ] **CI-032 — Observational Study archetype.** Population, exposure, outcome, association, subgroup, and limitations.
- [ ] **CI-033 — Computational Biology archetype.** Biological question, data, pipeline, validation, and discovery.
- [ ] **CI-034 — Computer Vision archetype.** Problem, architecture, qualitative result, benchmark, and ablation.
- [ ] **CI-035 — Environmental Study archetype.** Study area, spatial/temporal evidence, uncertainty, and implication.
- [ ] **CI-036 — Implement Conference × Archetype resolver.** Produce a recommendation with traceable inputs; never predict acceptance probability.

## Epic CI-E — Curated 30-pack catalog (P2)

- [x] **CI-040 — Medicine batch:** ASCO, AACR, ESMO, RSNA, AHA Scientific Sessions, ESC Congress. Partial editions retain explicit public-source gaps and must be refreshed when organizer instructions appear.
- [ ] **CI-041 — Biology batch:** SfN, ASCB, ASM Microbe, ASHG, ISMB, Plant Biology.
- [ ] **CI-042 — Environment batch:** AGU Annual Meeting, EGU General Assembly, ESA Annual Meeting, SETAC, AMS Annual Meeting, Ocean Sciences Meeting.
- [ ] **CI-043 — Computer Science batch:** CVPR, SIGGRAPH, CHI, SIGCOMM, KDD, IEEE VIS.
- [ ] **CI-044 — Artificial Intelligence batch:** NeurIPS, ICML, ICLR, AAAI, ACL, EMNLP.
- [ ] **CI-045 — Enforce multi-label taxonomy.** Cross-disciplinary conferences remain one object referenced by multiple domains.
- [ ] **CI-046 — Require pack review evidence.** Each edition needs official sources, access date, explicit gaps, rights review, schema tests, validator pass/fail fixture, and maintainer sign-off.
- [ ] **CI-047 — Add visual review fixture per pack.** One golden card and one low-resolution poster preview per pack; no organizer marks unless licensed.

Catalog completion means 30 unique conference objects, not 30 hard-coded templates. Packs land in reviewed batches after CI-A through CI-C stabilize.

## Epic CI-F — Product surfaces (P2)

- [ ] **CI-050 — Add project create flow.** Choose conference, edition, presentation, palette mode, and detected archetype.
- [ ] **CI-051 — Add catalog/detail UI contract.** Filter by domain/topic/year/verification and show official versus PostEx labels.
- [ ] **CI-052 — Add conference-card view model.** Include Palette DNA preview, canvas status, verification, and rights notice.
- [ ] **CI-053 — Add stale-edition warning.** Never silently select an older edition for a newer event year.
- [ ] **CI-054 — Add user-supplied official template path.** Preserve rights, checksum, logo proportions, and non-endorsement state.

## Epic CI-G — Quality and release (continuous)

- [x] **CI-060 — Add schema/loader/validator unit tests.** Cover both goldens, renderer token mapping, required failures, and conditional rules.
- [ ] **CI-061 — Add malformed-pack tests.** Duplicate IDs, missing provenance, bad rights, path traversal, invalid ratios, identity mismatch, and false verified state.
- [ ] **CI-062 — Add integrated export goldens.** CVPR native canvas and AACR e-poster PDF through PPTX/PDF/PNG/Manifest/Preflight.
- [ ] **CI-063 — Add cross-platform export matrix.** PowerPoint and LibreOffice on supported operating systems.
- [ ] **CI-064 — Add accessibility checks.** Contrast, grayscale, CVD simulations, minimum type, reading distance, and alt-text expectations.
- [ ] **CI-065 — Add release gate.** Full tests, repository audit, Ruff, strict mypy, schema audit, source freshness, rights review, and visual regression must pass.
