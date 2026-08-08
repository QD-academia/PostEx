# Preflight contract

Preflight emits structured findings with `info`, `warning`, or `error` severity.

Required checks cover dimensions, overflow, font availability, image resolution, minimum font size, contrast, evidence coverage, scientific-color locks, approvals, and PDF renderer match. Errors block release. Warnings require explicit acknowledgement and remain in the report.

PowerPoint is the preferred PDF exporter because PPTX is the editable canonical artifact. LibreOffice is the fallback and must be identified in the report. PNG is a preview, not a printable source.

