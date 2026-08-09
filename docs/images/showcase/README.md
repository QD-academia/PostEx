# Homepage showcase asset record

These assets support three documentation demonstrations of PostEx Palette Fusion. They are documentation media, not inputs to the runnable golden example, and they are not covered by the repository's Apache-2.0 license.

## Varka showcase

- Promotional composition: `varka-showcase.webp`
- Reference illustration: `sources/varka-official-illustration.png`
- Source URL: <https://act-upload.hoyoverse.com/event-ugc-hoyowiki/2026/01/24/35428890/0339ed759f5a3c6648d0b0706ac2ba16_3965272301952436796.png>
- Context page: <https://wiki.hoyolab.com/pc/genshin/entry/9342>
- Official character-content page carrying a “Repost allowed” notice: <https://www.hoyolab.com/article/43858177>
- Retrieved: 2026-08-08
- SHA-256: `83fc675e2a5db0ec928e2927969e063b407185493faafbca8ddf2033269cb727`
- Rights: Varka and Genshin Impact visual properties © HoYoverse. Used here as an attributed, non-commercial, unofficial workflow demonstration. No affiliation or endorsement is implied. Remove the illustration and derived showcase if the rights holder requests it.
- Transformation: cropped within a rounded documentation card and combined with explanatory typography, palette-role swatches, and an independently generated poster preview. The character artwork is not embedded in the poster.

## Temple of Heaven showcase

- Promotional composition: `tiantan-showcase.webp`
- Reference photograph: `sources/tiantan-hall-of-prayer.jpg`
- Title: *Temple of heaven, Beijing, China — panoramio (2) (cropped)*
- Photographer: Haluk Comertel
- Source: <https://commons.wikimedia.org/wiki/File:Temple_of_heaven,Beijing,China_-_panoramio_(2)_(cropped).jpg>
- License: [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/)
- Retrieved: 2026-08-08
- SHA-256: `60ac0f2f045af3983ae5ccd4cc326813520385ad16d03d8fd211d8f4b16f7dbf`
- Transformation: cropped to emphasize the upper roof tiers, then combined with explanatory typography, palette-role swatches, and an independently generated poster preview.

## Peking Union Medical College showcase

- Promotional composition: `pumc-showcase.webp`
- Reference emblem: `sources/pumc-emblem.png`
- Institution: Chinese Academy of Medical Sciences & Peking Union Medical College (中国医学科学院·北京协和医学院)
- Source: supplied by the user for the associated academic-poster project
- Permission record: the user confirmed full permission for this academic-poster and public showcase use on 2026-08-08
- SHA-256: `4abc7919388ccc5ca9b795c1d47647366005f6f42f536f12921edff0c143ab20`
- Rights: the emblem remains a third-party institutional mark and is not relicensed under Apache-2.0. No affiliation or endorsement is implied.
- Transformation: transparent pixels outside the circular mark were normalized; internal emblem pixels and proportions were preserved. The emblem is combined with explanatory typography, role-based swatches and an independently rendered poster preview.

## Poster previews

All three poster previews derive from Zhang et al., “A signature for pan-cancer prognosis based on neutrophil extracellular traps,” *Journal for ImmunoTherapy of Cancer* (2022), DOI `10.1136/jitc-2021-004210`. The article and displayed scientific figures are available under CC BY-NC 4.0. Scientific raster figures were not recolored.

- `varka-poster.png` SHA-256: `1251290eadfa10a1f5e19f5c397f1b674c93edc4b4b6b175cd62834652ccb434`
- `tiantan-poster.png` SHA-256: `a8d76995b77f47421f72ddf45ae083d6a9f076cece68ea42c354f521839b5f65`
- `pumc-poster.png` SHA-256: `75d405402339507e1b3acf507a5011e0e38280ad70baf3509ae5663731c4bd28`

The promotional compositions are rebuilt deterministically with `scripts/build_showcase_assets.py`.
