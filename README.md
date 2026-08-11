<p align="center">
  <img src="assets/brand/postex-logo-primary.svg" alt="PostEx™ — Let every study have its own visual identity." width="720">
</p>

<p align="center"><strong>Give every study its own visual identity.</strong></p>

<p align="center">
  Turn a paper, an inspiration palette, and a target conference into an editable,<br>
  evidence-linked academic poster.
</p>

<p align="center"><strong>Paper × Inspiration × Conference → Editable, traceable poster</strong></p>

<p align="center">
  <a href="#see-postex-in-action">See it in action</a> ·
  <a href="docs/gallery/index.html">Gallery</a> ·
  <a href="#built-in-palette-library">Explore 154 palettes</a> ·
  <a href="#conference-intelligence">Conference Intelligence</a> ·
  <a href="#quick-start">Quick start</a>
</p>

[![PostEx 0.5 launch demo: visual identity, Palette DNA, Conference Intelligence, and Trusted Export](docs/media/postex-launch-demo.gif)](#see-postex-in-action)

**Try the complete, no-API-key golden demo:**

```bash
git clone https://github.com/QD-academia/PostEx.git
cd PostEx
python -m pip install .
postex demo --output postex-demo
```

Open `postex-demo/index.html` to inspect the editable PPTX, poster preview, evidence report, preflight result, and artifact hashes. The command runs locally and makes no network request after installation.

PostEx™ is an open-source, agent-friendly academic-poster toolkit for Codex, Claude Code, and the command line. It combines three layers that are usually separated:

| Layer | What PostEx contributes |
|---|---|
| **Inspiration** | Images, named themes, institutions, cities, and built-in cards become role-based Palette DNA—not a simple color swap. |
| **Conference** | Year-specific packs keep official requirements separate from independent PostEx layout, canvas, and storytelling recommendations. |
| **Trust** | Evidence links, approvals, asset rights, preflight findings, and output hashes remain inspectable through Trusted Export. |

Version 0.5 alpha introduces **Conference Intelligence** foundations on top of v0.4 Trusted Export. Conference Packs supply verified requirements, independent PostEx recommendations, Palette DNA, canvas tokens, and machine-readable preflight rules without conference-specific renderer branches.

The reusable [launch animation](docs/media/postex-launch-demo.gif) and [1280×640 social preview](assets/brand/exports/postex-social-preview-1280x640.png) are generated from original PostEx branding and the CC0 AURORA-12 fixture; neither asset contains conference logos or third-party character art.

> Status: `0.5.0a1` foundation. Seven schema-validated Conference Packs are included: CVPR, AACR, ASCO, ESMO, RSNA, AHA Scientific Sessions, and ESC Congress 2026. The existing three template families remain production-renderable in A0, A1, and 36×48 landscape; arbitrary conference-native PPTX geometry is tracked as the next Canvas Engine milestone.

The approved **Poster Frame** identity is available as an editable SVG brand kit. See the [PostEx gallery](docs/gallery/index.html), [brand system](docs/brand.md), [30-day promotion plan](docs/promotion-plan.md), and [Genshin Study Identity campaign](docs/marketing/genshin-study-identity.md).

## Trusted Export

Trusted Export binds inputs, templates, palettes, licensed assets, approvals, and output hashes in `postex-manifest.json`. It records the PostEx version, project and source IDs, input hash, template and dimensions, Palette ID, asset/license references, approvals, Preflight result, and output hashes. The Manifest never hashes itself. Any ERROR blocks release; any WARNING keeps output draft-only.

## Conference Intelligence

A Conference Pack separates what the event publishes from what PostEx designs:

- **Official Requirement / Recommendation** records are edition-specific, source-bound, dated, and evaluated by the conference preflight validator.
- **PostEx Recommendation** records describe layout, storytelling, exact fallback canvas choices, and visual treatment. They are never represented as organizer policy.
- **Conference Palette DNA** is an independent PostEx interpretation. Golden packs bundle no conference logos or official templates and imply no endorsement.
- **Verification** is explicit. Unknown public requirements remain unknown; for example, AACR 2026's public e-poster rules are modeled while its unverified physical-board dimensions are not invented.

The registry contains the two original goldens plus a controlled medical batch:

```text
conferences/
├── registry.yaml
├── cvpr/{conference.yaml,editions/2026.yaml,palettes/2026.yaml}
├── aacr/{conference.yaml,editions/2026.yaml,palettes/2026.yaml}
├── asco/{conference.yaml,editions/2026.yaml,palettes/2026.yaml}
├── esmo/{conference.yaml,editions/2026.yaml,palettes/2026.yaml}
├── rsna/{conference.yaml,editions/2026.yaml,palettes/2026.yaml}
├── aha-scientific-sessions/{conference.yaml,editions/2026.yaml,palettes/2026.yaml}
└── esc-congress/{conference.yaml,editions/2026.yaml,palettes/2026.yaml}
```

ASCO and ESC have verified 2026 technical scopes. ESMO, RSNA, and AHA remain partially verified where public 2026 poster dimensions or upload details are pending; their exact PostEx canvases are visibly labeled as temporary recommendations.

See [Conference Intelligence architecture](docs/conference-intelligence.md) and the executable [v0.5 Epic/Issue plan](TASKS.md).

## Built-in palette library

PostEx 0.3 includes 154 source-grounded cards, displayed as: 50 ShanghaiRanking 2026 Chinese university emblems, 50 foreign university emblems selected from the 2026–2027 U.S. News Best Global Universities ranking, 35 Genshin characters grouped by Mondstadt, Liyue, Inazuma, Sumeru, Fontaine, Natlan, and Nod-Krai, then 19 Chinese city photographic cards. Each card combines source art with a six-role, poster-ready palette and machine-readable provenance.

[![All 154 built-in PostEx palette cards](assets/palettes/previews/all-palettes.webp)](assets/palettes/previews/all-palettes.webp)

### Genshin Study Identity

The 35-card Genshin collection supports a launch series built around a simple question: how can the same scientific evidence acquire seven distinct visual identities without placing character art inside the poster?

[![Thirty-five Genshin-inspired PostEx palette cards across seven regions](assets/palettes/previews/genshin-characters.webp)](assets/palettes/previews/genshin-characters.webp)

The first editorial sequence pairs the existing Paimon and Varka showcases with one planned identity from each catalog region: Albedo, Zhongli, Raiden Shogun, Nahida, Furina, Mavuika, and Columbina. Each study must be rendered and audited before its campaign status changes from `planned` to `ready`; the content registry is maintained in [`docs/marketing/genshin-study-identities.yaml`](docs/marketing/genshin-study-identities.yaml).

Genshin-inspired Palette DNA is an unofficial visual interpretation. Generated scientific posters do not embed character artwork by default, and no affiliation or endorsement is implied. Source art, rendered cards, named-theme provenance, and generated poster outputs retain separate rights records. See the [campaign playbook](docs/marketing/genshin-study-identity.md) and [asset licensing policy](docs/licensing.md).

Two enlarged examples show how the emblem and semantic palette work together:

[![Huazhong University of Science and Technology enlarged palette example](assets/palettes/examples/university-hust-example.webp)](assets/palettes/examples/university-hust-example.webp)

[![Tsinghua University enlarged palette example](assets/palettes/examples/university-tsinghua-example.webp)](assets/palettes/examples/university-tsinghua-example.webp)

See the [built-in palette documentation](docs/built-in-palettes.md) or audit a checkout with:

```bash
postex palette-catalog --root . --show-blockers
```

## See PostEx in action

### 1. Turn visual inspiration into Palette DNA

The primary visual direction on this page is a **Paimon-inspired cape-gradient Visual Signature**: midnight navy, layered cape blues, luminous ice blue, warm starlight gold, and a soft pearl canvas. No character artwork is bundled. PostEx translates the inspiration into an original, research-ready system of color roles, gradients, hierarchy, rhythm, cards, connectors, and emphasis.

![PostEx Palette Fusion Studio with three palette directions and three intelligent layout directions](docs/images/palette-fusion-studio.svg)

PostEx can build Palette DNA through several complementary routes:

- **Natural-language recognition:** descriptions such as *celestial, friendly, refined, airy* are parsed into temperature, luminance, saturation, contrast, visual rhythm, hierarchy, and component behavior.
- **User-image recognition:** region-aware CIELAB sampling identifies dominant, supporting, and accent colors from meaningful image regions; contrast repair and print simulation turn them into usable poster roles instead of simply averaging pixels.
- **Named-theme interpretation:** a theme is abstracted into visual characteristics and a rights-safe design language; source character or game artwork is not required or redistributed.
- **Brand and manual input:** institutional or user-supplied colors are mapped to semantic roles, completed with accessible neutrals, and checked for contrast, grayscale, color-vision, and print behavior.

Every route records provenance and produces role-based colors, usage ratios, component behavior, semantic locks, and three approval-ready expression levels: **Academic Safe**, **Balanced Fusion**, and **Visual Signature**. The Paimon-inspired Visual Signature is the hero direction here; the other two demonstrate how the same evidence plan can support quieter alternatives. Open the generated [Palette Studio HTML](examples/palette-fusion/outputs/palette/palette-studio.html), inspect the [fusion candidates](examples/palette-fusion/outputs/fusion/fusion-candidates.json), or read the [design rationale](examples/palette-fusion/outputs/fusion/design-rationale.html).

### 2. Fuse a fictional paper with a signature visual identity

The AURORA-12 golden example starts from a fully fictional, CC0 five-page manuscript. Its primary output is the Paimon-inspired Visual Signature below: evidence-linked, editable, print-aware, and approval-bound from Palette DNA through final rendering.

[![AURORA-12 fictional bioinformatics poster in the Paimon-inspired cape-gradient Visual Signature](examples/aurora-synthetic/output/paimon/aurora-synthetic-paimon-cape-gradient-visual-signature.png)](examples/aurora-synthetic/output/paimon/aurora-synthetic-paimon-cape-gradient-visual-signature.png)

The same approved evidence plan can also be expressed through PostEx Academic Safe or a user-image Balanced Fusion. These are supporting comparisons, not the lead identity:

[![Three AURORA-12 evidence-linked posters generated by PostEx](docs/images/aurora-three-palettes.png)](docs/images/aurora-three-palettes.png)

**Input:** [fictional manuscript PDF](examples/aurora-synthetic/AURORA-12-synthetic-manuscript.pdf) · **Research type:** synthetic bioinformatics benchmark · **Content mode:** traceable · **Primary output:** [Paimon-inspired PPTX](examples/aurora-synthetic/output/paimon/aurora-synthetic-paimon-cape-gradient-visual-signature.pptx) · **Supporting outputs:** [Academic Safe PPTX](examples/aurora-synthetic/output/default/aurora-synthetic-default-academic-safe.pptx) · [image-fusion PPTX](examples/aurora-synthetic/output/gate-image/aurora-synthetic-gate-image-balanced-fusion.pptx) · **Audit:** [evidence](examples/aurora-synthetic/evidence.json) · [approvals](examples/aurora-synthetic/approval-log.json)

### 3. Keep one design language across print sizes

The Paimon-inspired AURORA-12 design is rendered and preflighted independently in A0, A1, and 36×48-inch landscape formats rather than relying on blind page scaling. Typography, margins, cards, gradients, and figure density are adapted to each physical size while the Palette DNA remains recognizable.

![PostEx Bioinformatics Pipeline template family shown in A0, A1, and 36 by 48 inch variants](docs/images/template-family-preview.png)

### 4. Evaluate evidence structure across study types

Both panels below are generated from CC0 fictional studies: **AURORA-12** exercises a bioinformatics benchmark structure, while **LUMEN-24** exercises an observational cohort structure. They test must-keep facts, evidence anchors, source contracts, and interpretation boundaries—not just visual similarity—and share the Paimon-inspired design language used throughout this page.

![PostEx evaluation previews across bioinformatics and observational biomedical papers](docs/images/evidence-eval-preview.png)

Inspect the [AURORA-12 manuscript and evidence](examples/aurora-synthetic/) or the [LUMEN-24 fictional source and content plan](examples/homepage-fictional-evidence/).

### 5. Give one paper a knightly visual signature

What if a scientific poster could feel decisive, kinetic, and memorable—without sacrificing evidence discipline? This Varka-inspired case translates charcoal armor, wolf teal, Anemo cyan, ivory, and antique gold into a role-based **Visual Signature** with a clear results axis and restrained high-energy accents.

[![Varka visual source transformed into Palette DNA and an evidence-linked PostEx poster](docs/images/showcase/varka-showcase.webp)](docs/images/showcase/varka-poster.png)

PostEx does not paste character art into the poster or recolor scientific figures. It abstracts the reference into hierarchy, contrast, rhythm, component behavior, and semantic color roles; the source figures remain pixel-locked while the surrounding design becomes unmistakably its own.

**Route:** named-theme interpretation + region-aware image sampling · **Palette:** Visual Signature · **Structure:** Visual Journey · **Full view:** [poster PNG](docs/images/showcase/varka-poster.png) · **Reference:** [HoYoverse-hosted Varka illustration](docs/images/showcase/sources/varka-official-illustration.png)

### 6. Turn architecture into an intelligent poster system

The Temple of Heaven case starts with a real photograph, but the outcome is not a photo-themed template. PostEx recognizes glazed-tile blue, vermilion structure, gilded details, jade-painted eaves, and pale stone—then turns those observations into a print-safe **Balanced Fusion** and a calm, result-first reading path.

[![Temple of Heaven photograph transformed into Palette DNA and an evidence-linked PostEx poster](docs/images/showcase/tiantan-showcase.webp)](docs/images/showcase/tiantan-poster.png)

The building's ceremonial axis becomes information flow; tiered roofs become restrained header rhythm; white stone becomes breathing space. The reference image shapes the design language without appearing inside the scientific poster itself.

**Route:** user-image recognition + semantic interpretation · **Palette:** Balanced Fusion · **Structure:** Visual Journey · **Full view:** [poster PNG](docs/images/showcase/tiantan-poster.png) · **Reference:** [Hall of Prayer for Good Harvests photograph](docs/images/showcase/sources/tiantan-hall-of-prayer.jpg)

### 7. Turn an institutional emblem into a scientific identity

The Peking Union Medical College (北京协和医学院) case begins with an authorized institutional emblem rather than a photograph or character reference. PostEx maps PUMC green, archival ivory, restrained gold, sage support and clinical white into a disciplined **Balanced Fusion** that feels institutional without turning the poster into a branded letterhead.

[![Peking Union Medical College emblem transformed into Palette DNA and an evidence-linked PostEx poster](docs/images/showcase/pumc-showcase.webp)](docs/images/showcase/pumc-poster.png)

The emblem appears as the approved institutional mark while the extracted palette controls hierarchy, cards, metrics and emphasis. Scientific raster figures remain unchanged, and no affiliation or endorsement beyond the source study is implied.

**Route:** permission-recorded emblem + brand-role extraction · **Palette:** Balanced Fusion · **Structure:** Visual Journey · **Full view:** [poster PNG](docs/images/showcase/pumc-poster.png) · **Reference:** [authorized CAMS & PUMC emblem](docs/images/showcase/sources/pumc-emblem.png)

## Your study should not look like everyone else's

Give PostEx a paper and a visual idea—a mood, a place, an image, a brand, or a few colors. It returns traceable content, approval-ready Palette DNA, intelligent layout fusion, an editable PPTX, print output, and the evidence trail behind every major decision.

**If you want academic software to be both trustworthy and visually ambitious, [star PostEx on GitHub](https://github.com/QD-academia/PostEx).**

> **Alpha boundary:** all three template families and sizes now render through the shared production backend. Palette Fusion still requires explicit selection and approval of a structural direction; `postex create` scaffolds these gates but never decides them for the user.

## What makes PostEx different

- **Palette DNA:** natural language, user images, named themes, brand colors, or manual colors become role-based systems with usage ratios, component language, provenance, simulations, and semantic locks.
- **Intelligent fusion:** Hero Result, Visual Journey, and Editorial Story proposals respond to both content and palette character.
- **Explainable design:** every fusion proposal states why it chose its visual anchor, structure, emphasis, and guardrails.
- **User-owned decisions:** cloud upload, deletion, figure editing, palette application, poster structure, and semantic-color unlock are digest-bound approvals.
- **Evidence first:** claim IDs and numerical evidence survive rewriting, translation, and visual redesign.
- **Editable and print-aware:** PPTX is canonical; PDF, PNG, preflight, evidence, and rationale reports accompany delivery.
- **Trusted by construction:** file metadata, Manifest hashes, integrity checks, and final-release approval are enforced by the shared core and renderer.

PostEx v0.5 alpha retains the v0.4 production boundary while adding conference schemas, packs, palette/render tokens, and a standalone conference validator. Conference-native template geometry and the full 30-pack catalog are not yet production-complete.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install .

# No API key, cloud account, or office application required:
postex demo --output postex-demo
```

For development and your own projects:

```bash
pip install -e ".[dev]"

postex brief-questions
postex create path/to/paper.pdf --project-directory my-poster
postex validate examples/aurora-synthetic/project-paimon.yaml
postex palette-plan examples/palette-fusion/project.yaml
postex fusion-plan examples/palette-fusion/project.yaml
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

See [packaging and media assets](docs/packaging.md) for the slim-wheel boundary and the full palette curation library.

The two design commands create:

```text
examples/palette-fusion/outputs/fusion/
├── fusion-candidates.json
└── design-rationale.html
examples/palette-fusion/outputs/palette/
├── palette-candidates.json
└── palette-studio.html
```

The end-to-end renderer is exercised by the synthetic golden example:

```bash
postex generate examples/aurora-synthetic/project-paimon.yaml \
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
→ file metadata + integrity hashes
→ dimensions, fonts, overflow, DPI, contrast, margin, overlap, integrity, and evidence preflight
→ final release approval
→ Manifest, evidence, approval, diff, and design-rationale reports
```

Changing an approved proposal changes its digest and invalidates the approval. Locked copy, figures, regions, colors, layouts, or logos cannot be silently changed in later iterations.

## Repository map

```text
src/postex/              shared Python core
schemas/                 v0.1–v0.5 compatible JSON contracts
conferences/             registry plus year-specific Conference Packs
configs/                 defaults and provider examples
skills/                  Codex and Claude Code skill drafts
assets/templates/        three families × three print sizes
examples/palette-fusion/ runnable design-intelligence example
examples/aurora-synthetic/ CC0 fictional golden example and three poster variants
tests/                   unit and contract tests
evals/                   quality cases plus 3-family × 3-size Trusted Export goldens
docs/                    workflows, privacy, rendering, and design contracts
TASKS.md                 executable v0.5 GitHub-style Epic/Issue backlog
docker/                  container packaging
```

## Compatibility and limits

v0.1–v0.3 project files remain loadable. All three template families render through the shared core, but a structure candidate still requires approval before use. Raster scientific figures are never recolored automatically. Editable SVG figure variants require a separate scientific-color unlock. Core runnable examples remain independent of proprietary character artwork; the clearly attributed homepage showcase assets are governed separately and are not covered by the repository's Apache-2.0 license.

## Licensing

Python code and documentation are Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). Templates, examples, source papers, scientific figures, logos, character artwork, photographs, and homepage showcase assets have independent license records. See the [README image provenance](docs/images/README.md) before redistribution; never assume the code license covers bundled media.

See [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), and [CONTRIBUTING.md](CONTRIBUTING.md).
