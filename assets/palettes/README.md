# Built-in palette catalog

PostEx v0.3 reserves 154 stable palette IDs, displayed in this order: the 2026
ShanghaiRanking Top 50 Chinese universities, 50 foreign universities selected from
the 2026–2027 U.S. News Best Global Universities ranking, 35 Genshin character
inspirations grouped into seven regions, and 19 Chinese city photographic cards.

City cards retain the approved photograph inside a transparent rounded frame instead
of forcing neural background removal. Their photo-specific extractor excludes
near-black and near-white pixels before building the six-role Palette DNA.

Each card expects a transparent PNG at `cutouts/<id>.png` and an extracted Palette
DNA seed at `extracted/<id>.json`. `catalog.yaml` is the selection manifest;
`rights.yaml` is the release gate. A missing rights record always means `pending`.

Third-party images are not covered by the PostEx Apache-2.0 license. Do not add an
official character artwork, university emblem, photograph, screenshot, font, or
other protected asset to a public release unless the corresponding rights record
documents the source, license or permission, attribution, modification, and
redistribution terms.

