# Genshin Study Identity campaign

**Series promise:** One paper. Seven regions. Seven visual identities.<br>
**Role in PostEx growth:** visual discovery for Palette DNA, followed by product proof through editable output, conference context, and Trusted Export.

The campaign uses Genshin-inspired color systems as an entry point to explain a more general PostEx capability: visual inspiration can shape hierarchy, rhythm, cards, emphasis, and layout behavior without changing scientific evidence or placing source artwork inside the academic poster.

The machine-readable editorial registry is [`genshin-study-identities.yaml`](genshin-study-identities.yaml). It is the source of truth for status, required artifacts, rights boundaries, identity names, and links.

## Campaign truth boundary

Every public post must distinguish among three things:

1. **Source inspiration:** a named theme or separately governed source asset.
2. **Palette DNA:** original PostEx color roles, ratios, component behavior, and design interpretation.
3. **Generated poster:** an evidence-linked scientific artifact that does not embed character art by default.

Use the exact public notice:

> Genshin-inspired Palette DNA is an unofficial visual interpretation. Generated scientific posters do not embed character artwork by default, and no affiliation or endorsement is implied.

Do not use “official,” “collaboration,” “partnership,” or “Genshin template.” Do not place a game logo in a generated poster. Do not imply that naming a theme grants redistribution rights to character media.

## Status discipline

An identity is not a campaign deliverable merely because its palette card exists.

| Status | Meaning | Public use |
|---|---|---|
| `planned` | Card and palette are selected; poster work has not started | Roadmap only |
| `rendering` | Poster artifacts are being generated | Builder update with limitations |
| `review` | Visual, evidence, preflight, or rights review remains | Preview only; no “ready” claim |
| `ready` | Required artifacts and reviews are complete | Launch content may be prepared |
| `published` | Channel copy, links, and rights notice were verified | Public campaign asset |

The registry requires a PNG, editable PPTX, palette reference, evidence record, preflight report, rights review, and human visual review before `ready`.

## Launch identities

### Existing proof

| Identity | Current role | Proof |
|---|---|---|
| Paimon / Celestial Starlight | Primary hero identity | [Poster PNG](../../examples/aurora-synthetic/output/paimon/aurora-synthetic-paimon-cape-gradient-visual-signature.png) · [Editable PPTX](../../examples/aurora-synthetic/output/paimon/aurora-synthetic-paimon-cape-gradient-visual-signature.pptx) |
| Varka / Wolf Teal | Documentation showcase pending campaign PPTX | [Showcase](../images/showcase/varka-showcase.webp) · [Poster](../images/showcase/varka-poster.png) |

### Seven Regions, One Paper queue

| Region | Identity | Editorial lens | Suggested domains |
|---|---|---|---|
| Mondstadt | Albedo / Chalk Mineral | precise methods and mineral neutrals | chemistry, materials science |
| Liyue | Zhongli / Geo Archive | archival, stable, longitudinal | earth and environmental science |
| Inazuma | Raiden Shogun / Electro Violet | controlled contrast and performance | AI, CS, engineering |
| Sumeru | Nahida / Verdant Wisdom | connected biological evidence | biology, medicine, ecology |
| Fontaine | Furina / Cerulean Theatre | layered visual staging | computer vision, medical imaging |
| Natlan | Mavuika / Solar Ember | momentum and intervention | energy, engineering, trials |
| Nod-Krai | Columbina / Lunar Nocturne | complex signals and high-dimensional evidence | genomics, neuroscience |

These seven entries remain `planned` until their audited poster artifacts exist.

## Production workflow

Run the same fictional source and evidence plan through every identity so the visual comparison remains fair.

```text
lock source paper and evidence plan
→ select catalog Palette DNA
→ generate three expression candidates
→ approve one structural direction
→ render editable PPTX, PDF, and PNG
→ run evidence, typography, contrast, integrity, and conference preflight
→ complete rights and human visual review
→ prepare comparison crop and channel copy
→ verify every link and publish
```

Scientific raster figures remain pixel-locked. Palette application must not recolor heatmaps, legends, microscopy, clinical images, or other semantic scientific colors unless a separate, explicit approval permits the edit.

## Content package for each identity

Each published identity should ship as a reusable set:

- 1280×1600 vertical carousel cover
- 1280×640 link/social preview
- 1920×1080 comparison frame
- 8–20 second transformation clip
- palette card and six-role breakdown
- full poster PNG
- editable PPTX link
- short evidence/preflight proof
- alt text
- public rights notice
- one primary call to action

Recommended carousel order:

1. Same paper, new visual identity.
2. Source inspiration and palette card.
3. Six Palette DNA roles.
4. Component and hierarchy behavior.
5. Full scientific poster.
6. Evidence/preflight proof.
7. Try, request, or contribute.

## Messaging

### Primary headline

> Same paper. Same evidence. A completely different visual identity.

### Seven-region headline

> One paper. Seven regions. Seven visual identities.

### Explanatory line

> PostEx translates inspiration into Palette DNA, hierarchy, rhythm, and component behavior—not a character image pasted onto a poster.

### Calls to action

- **Discovery:** Which identity should render next?
- **Trial:** Pick a palette and inspect the editable poster.
- **Conference:** Choose the conference that should constrain the next identity.
- **Contribution:** Add the evidence or verification needed to move one identity to `ready`.

## Channel adaptations

| Channel | Format | Conversation prompt |
|---|---|---|
| X | short clip + four-image thread | Which identity fits this study? |
| LinkedIn | carousel + trust explanation | Can visual ambition and evidence discipline coexist? |
| Xiaohongshu | vertical carousel | 同一篇论文，你会选哪种视觉身份？ |
| Bilibili | 3–6 minute build walkthrough | 色卡如何影响布局，而不是只换颜色？ |
| Zhihu | long-form technical case | 如何把角色灵感转成可审计的学术设计语言？ |
| GitHub Discussions | poll + artifact links | Vote on the next audited identity |

Do not copy identical promotional text across communities. Lead with a useful transformation or design lesson and follow the current rules of the destination community.

## Four-week release sequence

1. **Week 1:** Paimon hero case and the distinction between inspiration, Palette DNA, and poster output.
2. **Week 2:** Varka documentation case and the editable-PPTX gap required for campaign readiness.
3. **Week 3:** First fully audited regional identity, selected from user votes and domain fit.
4. **Week 4:** Two- or three-identity comparison; announce the next regional production queue.

Do not render all seven merely to fill the calendar. Each identity should answer a real product or research-domain question and pass the same audit boundary.

## References

- [Built-in palette documentation](../built-in-palettes.md)
- [Palette Fusion architecture](../palette-fusion.md)
- [Asset licensing](../licensing.md)
- [Showcase rights records](../images/showcase/README.md)
- [Palette rights manifest](../../assets/palettes/rights.yaml)
