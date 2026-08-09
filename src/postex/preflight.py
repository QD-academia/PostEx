from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from postex.enums import PosterSize, Severity


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
    "overflow",
    "fonts",
    "image_resolution",
    "minimum_font_size",
    "contrast",
    "evidence_coverage",
    "scientific_color_locks",
    "approvals",
    "renderer_match",
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
) -> dict[str, Any]:
    """Run deterministic release checks over final single-slide poster artifacts."""

    from PIL import Image
    from pypdf import PdfReader

    findings: list[dict[str, Any]] = []
    artifacts = (pptx, pdf, png, layout)
    present = all(item.is_file() and item.stat().st_size > 0 for item in artifacts)
    findings.append(
        _finding(
            "artifacts",
            "error",
            present,
            "PPTX, PDF, PNG and layout JSON are present.",
        )
    )
    if not present:
        return {
            "schema_version": "0.1",
            "project_id": project_id,
            "passed": False,
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
    findings.extend(_layout_typography_findings(layout_data))

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

    with zipfile.ZipFile(pptx) as archive:
        presentation = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
        namespace = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        slide_size = presentation.find("p:sldSz", namespace)
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
    return {
        "schema_version": "0.1",
        "project_id": project_id,
        "poster_size": poster_size.value,
        "passed": not errors,
        "expected_inches": list(expected_inches),
        "findings": findings,
    }
