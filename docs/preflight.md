# Preflight contract

Preflight emits structured findings with `info`, `warning`, or `error` severity.

Required checks cover provenance presence or approved omission, page dimensions, font resolution, text overflow and collisions, effective DPI, contrast, safety margins, provenance overlap, evidence coverage, scientific-color locks, current approvals, output completeness, and SHA-256 integrity.

`ERROR` blocks release-ready output. A failed `WARNING` does not destroy artifacts, but forces `output_status: draft`; warnings cannot be acknowledged into a release-ready state. Final release requires a digest-bound `final_release` approval for the exact project, template, size, Palette ID, provenance setting, and source ID.

Preflight reads the draft `postex-manifest.json`, verifies core output hashes, then generation writes the final Preflight state and report hash into the Manifest. The Manifest intentionally excludes its own hash.

Primary poster text must be at least 28 pt for A0 and 36×48-inch outputs. A1 uses a 20 pt threshold because its independently composed canvas is smaller and intended for a shorter viewing distance; it is not accepted by blindly scaling an A0 PDF.

PowerPoint is the preferred PDF exporter because PPTX is the editable canonical artifact. LibreOffice is the fallback and must be identified in the report. PNG is a preview, not a printable source.
