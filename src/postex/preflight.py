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
