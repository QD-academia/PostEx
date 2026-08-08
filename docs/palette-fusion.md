# Palette Fusion

Palette Fusion combines scientific story signals with a role-based visual system. A palette is not approved merely because its colors look attractive; it must specify how those colors and moods affect hierarchy, components, flow, and scientific semantics.

## Palette DNA contract

Required roles are `canvas`, `primary`, `secondary`, `highlight`, `accent`, and `text`. Ratios total approximately 1.0. Additional roles may represent surfaces, muted content, or approved positive/negative semantics.

Source types are `default`, `image`, `theme`, `brand`, and `manual`. Store a reference and rights note. A named theme does not grant permission to redistribute character art, logos, fonts, or screenshots.

## Fusion directions

- Hero Result makes an approved claim the dominant visual anchor.
- Visual Journey organizes process, figures, and evidence as a readable sequence.
- Editorial Story uses asymmetric hierarchy and editorial pacing to foreground meaning.

Each candidate binds to a Poster Brief digest, Palette DNA ID, and hero claim. The candidate records normalized layout weights, component language, rationale, and recommendation status. Selection requires approval.

## Palette Studio choices

- Academic Safe reduces saturation and ornament for maximum conference formality.
- Balanced Fusion preserves the approved inspiration and is the default recommendation.
- Visual Signature strengthens color expression and component character.

All three retain the same scientific semantic locks and intended use ratios.

## CLI

```bash
postex palette-plan examples/palette-fusion/project.yaml
postex fusion-plan examples/palette-fusion/project.yaml
```

This emits machine-readable candidates and a self-contained HTML rationale. Renderer integration must consume an approved candidate and map palette roles rather than positional color-array indices.
