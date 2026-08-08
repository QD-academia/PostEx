# Preflight contract

Preflight emits structured findings with `info`, `warning`, or `error` severity.

Required checks cover dimensions, overflow, font availability, image resolution, minimum font size, contrast, evidence coverage, scientific-color locks, approvals, and PDF renderer match. Errors block release. Warnings require explicit acknowledgement and remain in the report.

Primary poster text must be at least 28 pt for A0 and 36×48-inch outputs. A1 uses a 20 pt threshold because its independently composed canvas is smaller and intended for a shorter viewing distance; it is not accepted by blindly scaling an A0 PDF.

PowerPoint is the preferred PDF exporter because PPTX is the editable canonical artifact. LibreOffice is the fallback and must be identified in the report. PNG is a preview, not a printable source.
