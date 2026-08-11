# PostEx packaging and media assets

PostEx separates the installable runtime from the repository's editorial media library.

## Core wheel

The wheel contains:

- Python runtime and schemas;
- Conference Packs and machine-readable provenance;
- production PPTX templates;
- palette catalog metadata and extracted Palette DNA;
- the lightweight, fictional AURORA-12 golden demo.

It intentionally excludes palette-card renders, source images, cutouts, incoming assets, and preview contact sheets. Those files support curation, rights review, documentation, and campaign production; they are not required to run the core CLI.

## Repository media library

The full Git checkout retains the curated media under `assets/palettes/`. Each asset remains governed by `rights.yaml`, `ATTRIBUTION.md`, and the release-blocker audit. Excluding media from a wheel does not change its license or redistribution status.

Use the full repository when you need to:

- audit all 154 card sources and rights records;
- rebuild cutouts, cards, or contact sheets;
- author social campaigns and gallery material;
- contribute or review a new inspiration collection.

```bash
postex palette-catalog --root . --show-blockers
```

## Golden demo contract

`postex demo` copies a deterministic, fully fictional CC0 example to a new local directory. It performs no network request and requires no API key. The command emits an editable PPTX, PNG preview, evidence report, preflight report, HTML index, and a SHA-256 manifest. It is a product tour, not a claim that a new poster was generated live.

## Future split

If user demand justifies downloadable high-resolution inspiration media, publish it as separately versioned release assets with checksums and a rights manifest. Do not silently download third-party artwork during normal CLI execution.
