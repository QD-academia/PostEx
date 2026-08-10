from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from postex.enums import PosterSize, Severity
from postex.provenance import PROVENANCE_OBJECT_NAME, sha256_file


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    message: str
    location: str | None = None
    remediation: str | None = None


@dataclass
class PreflightReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(item.severity is Severity.ERROR for item in self.findings)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def require_pass(self) -> None:
        errors = [item.code for item in self.findings if item.severity is Severity.ERROR]
        if errors:
            raise RuntimeError("Preflight errors: " + ", ".join(errors))


REQUIRED_CHECKS = (
    "dimensions",
    "provenance_mark",
    "provenance_approval",
    "manifest",
    "overflow",
    "fonts",
    "effective_dpi",
    "minimum_font_size",
    "contrast",
    "safe_margin",
    "provenance_overlap",
    "evidence_coverage",
    "scientific_color_locks",
    "approvals",
    "final_release_approval",
    "artifacts",
    "output_hashes",
    "text_line_limits",
    "text_capacity",
    "text_collisions",
    "cjk_line_breaks",
)


def _minimum_body_font(poster_size: PosterSize) -> tuple[float, float]:
    """Return the print-size-specific body threshold in pixels and points."""

    points = 20.0 if poster_size is PosterSize.A1_LANDSCAPE else 28.0
    return points * 4.0 / 3.0, points


def _finding(code: str, severity: str, passed: bool, message: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "passed": passed,
        "message": message,
    }


def _line_count(element: dict[str, Any]) -> int:
    layout = element.get("textLayout")
    if isinstance(layout, dict):
        value = layout.get("lineCount")
        if isinstance(value, int):
            return value
    text = str(element.get("text", ""))
    return max(text.count("\n") + 1, 1)


def _maximum_lines(name: str) -> int | None:
    if name == "poster-title" or name == "central-takeaway-title":
        return 2
    if (
        name == "performance-strip-text"
        or name.endswith("-value")
        or name.endswith("-caption")
        or "evidence" in name
        or name in {"footer-source", "footer-status"}
    ):
        return 2 if name.endswith("-caption") else 1
    if name.endswith("-title"):
        return 1
    return None


def _bbox(element: dict[str, Any]) -> tuple[float, float, float, float] | None:
    raw = element.get("bbox")
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    try:
        return (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))
    except (TypeError, ValueError):
        return None


def _text_boxes_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    a = _bbox(left)
    b = _bbox(right)
    if a is None or b is None:
        return False
    horizontal = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    vertical = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return horizontal > 1.0 and vertical > 1.0


def _layout_typography_findings(layout_data: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [
        item
        for item in layout_data.get("elements", [])
        if isinstance(item, dict) and str(item.get("text", "")).strip()
    ]

    line_limit_failures: list[str] = []
    capacity_failures: list[str] = []
    orphan_lines: list[str] = []
    long_lines: list[str] = []
    cjk_break_failures: list[str] = []
    closing_punctuation = "，。；：！？）》】」』、"
    opening_punctuation = "（《【「『"
    line_length_exemptions = {
        "affiliations",
        "citation",
        "central-takeaway-subtitle",
        "footer-source",
        "footer-status",
    }

    for element in elements:
        name = str(element.get("name", "unnamed"))
        lines = _line_count(element)
        maximum = _maximum_lines(name)
        if maximum is not None and lines > maximum:
            line_limit_failures.append(f"{name} ({lines}>{maximum})")

        bbox = _bbox(element)
        try:
            font_size = float(element.get("resolvedFontSize", 0.0))
        except (TypeError, ValueError):
            font_size = 0.0
        if bbox is not None and font_size > 0 and lines * font_size * 0.92 > bbox[3] + 2.0:
            capacity_failures.append(name)

        text_layout = element.get("textLayout")
        rendered_lines = text_layout.get("lines", []) if isinstance(text_layout, dict) else []
        line_texts = [
            str(item.get("text", "")).strip()
            for item in rendered_lines
            if isinstance(item, dict) and str(item.get("text", "")).strip()
        ]
        if len(line_texts) > 1:
            last = line_texts[-1]
            if len(last) <= 8 and len(line_texts[-2]) >= 24:
                orphan_lines.append(name)
        for line in line_texts:
            has_cjk = any("\u2e80" <= char <= "\ufaff" for char in line)
            limit = 34 if has_cjk else 72
            if len(line) > limit and name not in line_length_exemptions and "evidence" not in name:
                long_lines.append(name)
            if has_cjk and (line[0] in closing_punctuation or line[-1] in opening_punctuation):
                cjk_break_failures.append(name)

    collision_pairs: list[str] = []
    for index, left in enumerate(elements):
        for right in elements[index + 1 :]:
            if _text_boxes_overlap(left, right):
                collision_pairs.append(f"{left.get('name', 'unnamed')} / {right.get('name', 'unnamed')}")

    return [
        _finding(
            "text_line_limits",
            "error",
            not line_limit_failures,
            "Text line limits are respected."
            if not line_limit_failures
            else "Excess line count: " + ", ".join(line_limit_failures[:8]),
        ),
        _finding(
            "text_capacity",
            "error",
            not capacity_failures,
            "Rendered line count fits every text box."
            if not capacity_failures
            else "Text boxes are too short for rendered lines: "
            + ", ".join(capacity_failures[:8]),
        ),
        _finding(
            "text_collisions",
            "error",
            not collision_pairs,
            "Text boxes do not overlap."
            if not collision_pairs
            else "Overlapping text boxes: " + ", ".join(collision_pairs[:8]),
        ),
        _finding(
            "orphan_lines",
            "warning",
            not orphan_lines,
            "No short orphan lines were detected."
            if not orphan_lines
            else "Short final lines: " + ", ".join(sorted(set(orphan_lines))[:8]),
        ),
        _finding(
            "text_line_length",
            "warning",
            not long_lines,
            "Text lines stay within scan-friendly length targets."
            if not long_lines
            else "Long rendered lines: " + ", ".join(sorted(set(long_lines))[:8]),
        ),
        _finding(
            "cjk_line_breaks",
            "warning",
            not cjk_break_failures,
            "CJK punctuation line breaks are valid."
            if not cjk_break_failures
            else "Invalid CJK punctuation breaks: "
            + ", ".join(sorted(set(cjk_break_failures))[:8]),
        ),
    ]


def _pptx_has_named_mark(pptx: Path, mark_text: str) -> bool:
    with zipfile.ZipFile(pptx) as archive:
        slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8", errors="replace")
    return PROVENANCE_OBJECT_NAME in slide_xml and mark_text in slide_xml


def _contrast_ratio(left: str, right: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    a, b = sorted((luminance(left), luminance(right)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _theme_contrast_finding(render_spec: dict[str, Any]) -> dict[str, Any]:
    theme = render_spec.get("theme", {})
    pairs = (
        ("ink/canvas", str(theme.get("ink", "#000000")), str(theme.get("canvas", "#FFFFFF"))),
        ("ink/panel", str(theme.get("ink", "#000000")), str(theme.get("panel", "#FFFFFF"))),
        ("white/primary", "#FFFFFF", str(theme.get("primary", "#000000"))),
    )
    ratios = {name: _contrast_ratio(left, right) for name, left, right in pairs}
    failed = [f"{name}={ratio:.2f}" for name, ratio in ratios.items() if ratio < 4.5]
    return _finding(
        "contrast",
        "error",
        not failed,
        "Primary text pairs meet WCAG 4.5:1."
        if not failed
        else "Insufficient contrast: " + ", ".join(failed),
    )


def _effective_dpi_finding(
    render_spec: dict[str, Any], expected_inches: tuple[float, float]
) -> dict[str, Any]:
    from PIL import Image

    failures: list[str] = []
    raster_count = 0
    for figure in render_spec.get("content", {}).get("figures", []):
        if not isinstance(figure, dict) or not figure.get("path"):
            continue
        path = Path(str(figure["path"]))
        if path.suffix.lower() == ".svg":
            continue
        if not path.is_file():
            failures.append(f"{path.name}: missing")
            continue
        raster_count += 1
        with Image.open(path) as image:
            display_width = expected_inches[0] * 0.32
            display_height = expected_inches[1] * 0.42
            dpi = min(image.width / display_width, image.height / display_height)
        if dpi < 150:
            failures.append(f"{path.name}: {dpi:.0f} DPI")
    message = (
        "All scientific figures are vector assets."
        if raster_count == 0 and not failures
        else "Raster figures meet the 150 effective-DPI draft threshold."
    )
    return _finding(
        "effective_dpi",
        "warning",
        not failures,
        message if not failures else "Low-resolution figure assets: " + ", ".join(failures),
    )


def _font_finding(layout_data: dict[str, Any]) -> dict[str, Any]:
    missing = []
    for element in layout_data.get("elements", []):
        if not isinstance(element, dict) or not str(element.get("text", "")).strip():
            continue
        style = element.get("resolvedTextStyle", {})
        if not isinstance(style, dict) or not str(style.get("typeface", "")).strip():
            missing.append(str(element.get("name", "unnamed")))
    return _finding(
        "fonts",
        "error",
        not missing,
        "Every text object resolves to an explicit or theme typeface."
        if not missing
        else "Unresolved fonts: " + ", ".join(missing[:8]),
    )


def _margin_and_mark_overlap_findings(
    layout_data: dict[str, Any], provenance: dict[str, Any]
) -> list[dict[str, Any]]:
    elements = [item for item in layout_data.get("elements", []) if isinstance(item, dict)]
    frame = layout_data.get("slide", {}).get("frame", {})
    width = float(frame.get("width", 0))
    height = float(frame.get("height", 0))
    margin = 24 * min(width / 4494, height / 3179)
    unsafe: list[str] = []
    for element in elements:
        if not str(element.get("text", "")).strip():
            continue
        box = _bbox(element)
        if box is None:
            continue
        if (
            box[0] < margin
            or box[1] < margin
            or box[0] + box[2] > width - margin
            or box[1] + box[3] > height - margin
        ):
            unsafe.append(str(element.get("name", "unnamed")))
    mark = next(
        (item for item in elements if item.get("name") == PROVENANCE_OBJECT_NAME), None
    )
    overlaps: list[str] = []
    if mark is not None:
        for element in elements:
            if element is mark or not str(element.get("text", "")).strip():
                continue
            if _text_boxes_overlap(mark, element):
                overlaps.append(str(element.get("name", "unnamed")))
    enabled = bool(provenance.get("enabled", True))
    return [
        _finding(
            "safe_margin",
            "error",
            not unsafe,
            "All text stays inside the 0.25-inch export safety margin."
            if not unsafe
            else "Text outside the safety margin: " + ", ".join(unsafe[:8]),
        ),
        _finding(
            "provenance_overlap",
            "error",
            not enabled or (mark is not None and not overlaps),
            "The provenance mark does not overlap poster content."
            if not overlaps
            else "Provenance overlaps: " + ", ".join(overlaps[:8]),
        ),
    ]


def run_artifact_preflight(
    *,
    project_id: str,
    poster_size: PosterSize,
    expected_inches: tuple[float, float],
    pptx: Path,
    pdf: Path,
    png: Path,
    layout: Path,
    evidence_coverage: float,
    approvals_current: bool,
    branding: dict[str, Any],
    provenance: dict[str, Any] | None = None,
    approval_log: dict[str, Any] | None = None,
    manifest: Path | None = None,
    render_spec: dict[str, Any] | None = None,
    expected_hashes: dict[str, dict[str, Any]] | None = None,
    output_files: dict[str, Path] | None = None,
    final_release_approved: bool = False,
    release_requested: bool = False,
) -> dict[str, Any]:
    """Run deterministic release checks over final single-slide poster artifacts."""

    from PIL import Image
    from pypdf import PdfReader

    findings: list[dict[str, Any]] = []
    provenance = provenance or {
        "enabled": True,
        "mark_text": "",
        "omission_approved": False,
    }
    approval_log = approval_log or {"records": []}
    render_spec = render_spec or {}
    expected_hashes = expected_hashes or {}
    output_files = output_files or {}
    artifacts = (pptx, pdf, png, layout)
    present = all(item.is_file() and item.stat().st_size > 0 for item in artifacts)
    findings.append(
        _finding(
            "artifacts",
            "error",
            present,
            "PPTX, PDF, PNG and layout JSON are present and non-empty.",
        )
    )
    if not present:
        return {
            "schema_version": "0.4",
            "project_id": project_id,
            "passed": False,
            "release_ready": False,
            "output_status": "draft",
            "findings": findings,
        }

    expected_px = tuple(round(value * 96) for value in expected_inches)
    expected_emu = tuple(value * 9525 for value in expected_px)
    expected_pt = tuple(value * 0.75 for value in expected_px)

    layout_data = json.loads(layout.read_text(encoding="utf-8"))
    frame = layout_data["slide"]["frame"]
    layout_size = (round(frame["width"]), round(frame["height"]))
    findings.append(
        _finding(
            "dimensions.layout",
            "error",
            layout_size == expected_px,
            f"Layout is {layout_size}; expected {expected_px} px.",
        )
    )

    primary_body_names = {
        "research-question",
        "datasets",
        "validation",
        "conclusion",
        "central-takeaway-title",
    }
    body_sizes = [
        float(element["resolvedFontSize"])
        for element in layout_data.get("elements", [])
        if element.get("text")
        and (
            str(element.get("name", "")) in primary_body_names
            or (
                str(element.get("name", "")).startswith("pipeline-")
                and str(element.get("name", "")).endswith("-text")
            )
        )
    ]
    minimum_body = min(body_sizes) if body_sizes else 0.0
    minimum_body_required, minimum_body_points = _minimum_body_font(poster_size)
    findings.append(
        _finding(
            "minimum_font_size",
            "error",
            minimum_body >= minimum_body_required,
            f"Minimum primary text is {minimum_body:.1f} px; required "
            f">={minimum_body_required:.1f} px ({minimum_body_points:.0f} pt) "
            f"for {poster_size.value}.",
        )
    )
    typography_findings = _layout_typography_findings(layout_data)
    findings.extend(typography_findings)
    overflow_ok = all(
        item["passed"]
        for item in typography_findings
        if item["code"] in {"text_line_limits", "text_capacity", "text_collisions"}
    )
    findings.append(
        _finding(
            "overflow",
            "error",
            overflow_ok,
            "Text capacity, line limits and collision checks pass.",
        )
    )
    findings.append(_font_finding(layout_data))

    with Image.open(png) as image:
        png_size = image.size
    findings.append(
        _finding(
            "dimensions.png",
            "error",
            png_size == expected_px,
            f"PNG is {png_size}; expected {expected_px} px.",
        )
    )

    pdf_reader = PdfReader(pdf)
    mark_text = str(provenance.get("mark_text", ""))
    mark_enabled = bool(provenance.get("enabled", True))
    named_mark = bool(mark_text) and _pptx_has_named_mark(pptx, mark_text)
    layout_mark = any(
        item.get("name") == PROVENANCE_OBJECT_NAME and item.get("text") == mark_text
        for item in layout_data.get("elements", [])
        if isinstance(item, dict)
    )
    pdf_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
    pdf_mark = bool(mark_text) and mark_text in pdf_text
    with Image.open(png) as image:
        png_mark = image.info.get("PostExProvenanceMark") == (
            "present" if mark_enabled else "omitted-with-approval"
        )
    visual_mark_ok = (named_mark and layout_mark and pdf_mark and png_mark) if mark_enabled else (
        not named_mark and not layout_mark and not pdf_mark and png_mark
    )
    findings.append(
        _finding(
            "provenance_mark",
            "error",
            visual_mark_ok,
            "The named provenance mark survives PPTX, PDF and PNG rendering."
            if mark_enabled
            else "The approved omission is absent visually while export metadata remains.",
        )
    )
    omission_ok = mark_enabled or bool(provenance.get("omission_approved", False))
    findings.append(
        _finding(
            "provenance_approval",
            "error",
            omission_ok,
            "Visual provenance is enabled or its exact omission digest is approved.",
        )
    )
    findings.extend(_margin_and_mark_overlap_findings(layout_data, provenance))
    findings.append(_theme_contrast_finding(render_spec))
    findings.append(_effective_dpi_finding(render_spec, expected_inches))

    if len(pdf_reader.pages) == 1:
        page = pdf_reader.pages[0]
        pdf_size = (float(page.mediabox.width), float(page.mediabox.height))
    else:
        pdf_size = (0.0, 0.0)
    pdf_ok = (
        len(pdf_reader.pages) == 1
        and abs(pdf_size[0] - expected_pt[0]) < 0.3
        and abs(pdf_size[1] - expected_pt[1]) < 0.3
    )
    findings.append(
        _finding(
            "dimensions.pdf",
            "error",
            pdf_ok,
            f"PDF has {len(pdf_reader.pages)} page at {pdf_size[0]:.2f}x{pdf_size[1]:.2f} pt.",
        )
    )

    manifest_ok = False
    manifest_data: dict[str, Any] = {}
    if manifest is not None and manifest.is_file() and manifest.stat().st_size > 0:
        try:
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_ok = (
                manifest_data.get("project_id") == project_id
                and manifest_data.get("source_id") == provenance.get("source_id")
                and "postex-manifest.json" not in manifest_data.get("outputs", {})
            )
        except (OSError, ValueError, TypeError):
            manifest_ok = False
    findings.append(
        _finding(
            "manifest",
            "error",
            manifest_ok,
            "postex-manifest.json is present, valid and does not hash itself.",
        )
    )

    figure_paths = {
        Path(str(item["path"])).name: Path(str(item["path"]))
        for item in render_spec.get("content", {}).get("figures", [])
        if isinstance(item, dict) and item.get("path")
    }
    lock_failures: list[str] = []
    locked_assets = [
        item
        for item in manifest_data.get("assets", [])
        if isinstance(item, dict) and item.get("pixel_locked")
    ]
    for item in locked_assets:
        path = figure_paths.get(Path(str(item.get("path", ""))).name)
        if path is None or not path.is_file() or sha256_file(path) != item.get("sha256"):
            lock_failures.append(str(item.get("id", "unnamed")))
    findings.append(
        _finding(
            "scientific_color_locks",
            "error",
            not figure_paths or (bool(locked_assets) and not lock_failures),
            "No scientific figures are embedded."
            if not figure_paths
            else "Scientific figure source hashes remain pixel-locked."
            if locked_assets and not lock_failures
            else "Scientific figure lock mismatch: " + ", ".join(lock_failures or ["none recorded"]),
        )
    )

    hashes_ok = True
    hash_failures: list[str] = []
    output_paths = {
        "pptx": pptx,
        "pdf": pdf,
        "png": png,
        "layout": layout,
    }
    output_paths.update(output_files)
    for name, expected in expected_hashes.items():
        path = output_paths.get(name)
        if path is None or not path.is_file() or sha256_file(path) != expected.get("sha256"):
            hashes_ok = False
            hash_failures.append(name)
    findings.append(
        _finding(
            "output_hashes",
            "error",
            hashes_ok,
            "Current output SHA-256 values match the manifest draft."
            if hashes_ok
            else "Output hash mismatch: " + ", ".join(hash_failures),
        )
    )

    final_severity = "error" if release_requested else "warning"
    findings.append(
        _finding(
            "final_release_approval",
            final_severity,
            final_release_approved,
            "The current Trusted Export release payload has final approval."
            if final_release_approved
            else "Final release approval is missing; output is draft-only.",
        )
    )

    with zipfile.ZipFile(pptx) as archive:
        presentation = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
        namespace = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        slide_size = presentation.find("p:sldSz", namespace)
        if slide_size is None:
            raise ValueError("PPTX presentation.xml does not declare p:sldSz")
        pptx_size = (
            int(slide_size.attrib["cx"]),
            int(slide_size.attrib["cy"]),
        )
    findings.append(
        _finding(
            "dimensions.pptx",
            "error",
            all(
                abs(actual - expected) <= 1
                for actual, expected in zip(pptx_size, expected_emu, strict=True)
            ),
            f"PPTX is {pptx_size}; expected {expected_emu} EMU.",
        )
    )

    findings.append(
        _finding(
            "evidence_coverage",
            "error",
            evidence_coverage == 1.0,
            f"Evidence coverage is {evidence_coverage:.3f}.",
        )
    )
    findings.append(
        _finding(
            "approvals",
            "error",
            approvals_current,
            "Deletion and palette approvals match current proposal digests.",
        )
    )

    logo_paths = [Path(str(item["path"])) for item in branding.get("logos", []) if item.get("path")]
    logo_ok = branding.get("logo_mode") != "provided" or (
        bool(logo_paths) and all(item.is_file() for item in logo_paths)
    )
    findings.append(
        _finding(
            "branding",
            "error",
            logo_ok,
            "Logo mode is valid and all supplied logo files exist.",
        )
    )

    errors = [item for item in findings if item["severity"] == "error" and not item["passed"]]
    warnings = [
        item for item in findings if item["severity"] == "warning" and not item["passed"]
    ]
    release_ready = not errors and not warnings
    return {
        "schema_version": "0.4",
        "project_id": project_id,
        "poster_size": poster_size.value,
        "passed": not errors,
        "release_ready": release_ready,
        "output_status": "release-ready" if release_ready else "draft",
        "expected_inches": list(expected_inches),
        "findings": findings,
    }
