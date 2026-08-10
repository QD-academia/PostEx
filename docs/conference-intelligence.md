# Conference Intelligence architecture

## Contract

A Conference Pack is a joined, read-only view of three editioned data files and one stable identity file. The registry is the only discovery surface.

```text
conferences/
  registry.yaml
  <conference-id>/
    conference.yaml
    editions/<year>.yaml
    palettes/<year>.yaml
```

The layers deliberately answer different questions:

| Layer | Question | Authority |
|---|---|---|
| Conference identity | What event is this? | Organizer identity metadata |
| Conference edition | What did the event publish for this year? | Official, source-bound facts |
| Preflight rule | How can an artifact fact be evaluated? | Official or explicitly PostEx |
| Palette set | How should PostEx express the setting visually? | Independent PostEx design |
| Registry | Which file versions form a loadable pack? | PostEx release metadata |

## Official versus PostEx

An official rule requires all of the following:

- `origin: official`;
- `level: required` or `recommended`;
- a `provenance_ref` resolving inside the same edition;
- an access date and official URL;
- an evidence summary and locator.

A PostEx rule uses `origin: postex` and `level: postex`. It may define a practical exact canvas when the organizer publishes only a range, but the edition must preserve the official range and state that the exact value is not official.

AACR 2026 demonstrates this boundary. The public 2026 instructions verify the companion e-poster requirement, PDF size guidance, file-size limit, cropping rule, and social-media opt-out marker. They do not establish the physical poster-board dimensions in the sources reviewed for this pack. The pack therefore lists physical canvas and print specification under `unverified_fields` and uses a clearly labeled 36×24-inch PostEx e-poster canvas.

## Verification states

- `verified`: the declared scope is fully checked and `unverified_fields` is empty.
- `partially-verified`: the declared scope is usable but named gaps remain.
- `community`: contributed data has not completed maintainer verification.
- `outdated`: a newer edition or changed official source supersedes the pack.

Verification applies to a declared scope, not to every possible presentation mode at an event.

## Rights

Golden packs are metadata and original design systems. They bundle no organizer logos or official templates, do not recolor or reconstruct marks, and do not imply endorsement. Official template support, when later added, must be separately licensed and referenced through Trusted Export rights records.

## Renderer interface

`ConferencePack.render_context()` selects a presentation and a reviewed Palette DNA mode. It emits only:

- physical canvas dimensions and orientation;
- existing renderer theme roles;
- generic component behavior;
- a layout recommendation profile;
- trace metadata identifying the pack, presentation, and Palette ID.

`apply_conference_render_context()` merges those values into a normal render spec. The renderer does not know that a palette came from CVPR, AACR, or any future pack.

This P0/P1 adapter does not yet synthesize arbitrary native PPTX templates. The Canvas Engine issue in `TASKS.md` owns geometry generation, template constraints, overrides, and end-to-end export.

## Preflight interface

`ConferencePreflightValidator` consumes a normalized mapping such as:

```yaml
canvas: {width_in: 84, height_in: 42, orientation: landscape}
export: {format: pdf, effective_dpi: 150, has_bleed: false}
layout: {column_count: 4}
typography: {minimum_body_font_pt: 30}
```

Rules use stable dotted paths and generic operators: `equals`, `one_of`, `minimum`, `maximum`, `between`, `present`, `absent`, and `present_if`. Required failures make conference compliance fail; recommendation findings remain separately inspectable. The next integration milestone will derive this snapshot from PPTX/PDF/PNG inspection and merge findings into Trusted Export Preflight and Manifest records.

## Adding a pack

1. Add or reuse `<conference-id>/conference.yaml`.
2. Add an immutable annual edition and palette file.
3. Cite only official organizer sources for official rules.
4. Mark unknown public fields explicitly.
5. Record rights and ensure no logo/template assets are accidentally bundled.
6. Add the pack to `registry.yaml`.
7. Run `pytest`, repository checks, lint, and strict type checking.

Do not copy a prior-year edition forward as verified or turn prose design advice into a required rule. The first medical expansion intentionally includes partial ESMO, RSNA, and AHA editions so source gaps remain visible while their identity, rights, Palette DNA, and PostEx recommendation layers are usable.

## Current medical batch

| Pack | Verification scope |
|---|---|
| AACR 2026 | Public companion e-poster PDF requirements verified; physical board dimensions unverified |
| ASCO 2026 | Regular and Trials in Progress canvas and poster-content restrictions verified |
| ESMO 2026 | Meeting identity verified; detailed public presenter specification pending |
| RSNA 2026 | Presenter-resource availability verified; 2026 hardcopy and digital specifications pending |
| AHA Scientific Sessions 2026 | Mandatory online e-poster and language verified; board and upload specifications pending |
| ESC Congress 2026 | Moderated ePoster PDF, 16:9, typography, image, logo, QR, video, commentary, and zoom-zone rules verified |
