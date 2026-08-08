from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from postex.approvals import canonical_digest
from postex.config import load_mapping, load_project
from postex.evidence import EvidenceRegistry
from postex.extractors import PdfExtractor
from postex.models import EvidenceRecord, PosterBlock, PosterModel, SourceLocator
from postex.preflight import run_artifact_preflight
from postex.renderers.pdf import LibreOfficePdfExporter, PowerPointPdfExporter
from postex.renderers.pptx import PptxRenderer
from postex.templates import TemplateRegistry


@dataclass(frozen=True)
class GenerationResult:
    pptx: Path
    pdf: Path
    png: Path
    evidence_report: Path
    preflight_report: Path
    extracted_document: Path


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def _approved_record(
    approval_log: dict[str, Any],
    *,
    subject: str,
    proposal_id: str,
    digest: str,
) -> dict[str, Any]:
    for record in approval_log.get("records", []):
        if (
            record.get("subject") == subject
            and record.get("proposal_id") == proposal_id
            and record.get("digest") == digest
            and record.get("decision") == "approved"
        ):
            return dict(record)
    raise RuntimeError(f"Missing current approval for {subject}/{proposal_id}/{digest}")


def _evidence_registry(
    source_id: str,
    content_plan: dict[str, Any],
    evidence_data: dict[str, Any],
) -> tuple[EvidenceRegistry, tuple[PosterBlock, ...]]:
    records = []
    for item in evidence_data["records"]:
        records.append(
            EvidenceRecord(
                evidence_id=str(item["evidence_id"]),
                claim_id=str(item.get("claim_id", item["evidence_id"])),
                locator=SourceLocator(
                    source_id=source_id,
                    kind="pdf",
                    page=item.get("page"),
                    section=item.get("section"),
                    figure=item.get("figure"),
                    table=item.get("table"),
                ),
                relation=str(item["relation"]),
            )
        )
    blocks = tuple(
        PosterBlock(
            block_id=str(item["block_id"]),
            role=str(item["role"]),
            text=str(item["text"]),
            evidence_ids=tuple(item.get("evidence", [])),
            synthesis=bool(item.get("synthesis", False)),
        )
        for item in content_plan["blocks"]
    )
    registry = EvidenceRegistry(records)
    registry.assert_covered(blocks)
    return registry, blocks


def _normalize_render_content(
    base: Path, content: dict[str, Any], branding: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = json.loads(json.dumps(content))
    for figure in normalized.get("figures", []):
        figure["path"] = str(_resolve(base, str(figure["path"])))

    normalized_branding = json.loads(json.dumps(branding))
    for logo in normalized_branding.get("logos", []):
        logo["path"] = str(_resolve(base, str(logo["path"])))
    return normalized, normalized_branding


def _relative_path(value: str, base: Path) -> str:
    path = Path(value)
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.name


def _portable_render_spec(
    render_spec: dict[str, Any], *, project_base: Path, repository_root: Path
) -> dict[str, Any]:
    """Remove machine-specific absolute paths from the persisted render report."""

    portable = json.loads(json.dumps(render_spec))
    portable["template"]["asset"] = _relative_path(
        str(portable["template"]["asset"]), repository_root
    )
    for figure in portable.get("content", {}).get("figures", []):
        if figure.get("path"):
            figure["path"] = _relative_path(str(figure["path"]), project_base)
    for logo in portable.get("branding", {}).get("logos", []):
        if logo.get("path"):
            logo["path"] = _relative_path(str(logo["path"]), project_base)
    return portable


def generate_project(
    project_path: str | Path,
    *,
    templates_root: str | Path,
    artifact_workspace: str | Path,
    output_directory: str | Path | None = None,
    pdf_exporter: str = "libreoffice",
    office_executable: str | Path | None = None,
) -> GenerationResult:
    project_file = Path(project_path).resolve()
    base = project_file.parent
    raw = load_mapping(project_file)
    config = load_project(project_file)
    artifacts = raw.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("Project configuration requires an artifacts object")

    source_path = _resolve(base, str(raw["source"]["path"]))
    extracted = PdfExtractor().extract(source_path)
    expected_hash = raw["source"].get("sha256")
    if expected_hash and extracted.sha256 != expected_hash:
        raise RuntimeError("Source PDF digest differs from project configuration")

    content_plan_path = _resolve(base, str(artifacts["content_plan"]))
    evidence_path = _resolve(base, str(artifacts["evidence"]))
    deletion_path = _resolve(base, str(artifacts["deletion_proposal"]))
    palettes_path = _resolve(base, str(artifacts["palette_proposals"]))
    approvals_path = _resolve(base, str(artifacts["approval_log"]))
    render_content_path = _resolve(base, str(artifacts["render_content"]))

    content_plan = _load_json(content_plan_path)
    evidence_data = _load_json(evidence_path)
    deletion = _load_json(deletion_path)
    palettes = _load_json(palettes_path)
    approval_log = _load_json(approvals_path)
    render_content = _load_json(render_content_path)

    selected_palette = str(raw.get("palette", {}).get("selected", "default"))
    palette = next(
        (
            item
            for item in palettes.get("proposals", [])
            if item.get("palette_id") == selected_palette
        ),
        None,
    )
    if palette is None:
        raise ValueError(f"Unknown palette: {selected_palette}")
    palette_payload = {
        "colors": list(palette["colors"]),
        "source": palette["source"],
        "semantic_colors_locked": bool(palette["semantic_colors_locked"]),
        "simulations": list(palette["simulations"]),
    }
    if "roles" in palette:
        palette_payload["roles"] = dict(sorted(palette["roles"].items()))
    for field in (
        "ratios",
        "mood",
        "component_behavior",
        "gradient_stops",
        "design_guardrails",
    ):
        if field in palette:
            value = palette[field]
            palette_payload[field] = dict(sorted(value.items())) if isinstance(value, dict) else value
    if canonical_digest(palette_payload) != palette["digest"]:
        raise RuntimeError("Palette proposal digest does not match its current payload")
    _approved_record(
        approval_log,
        subject="palette_application",
        proposal_id=selected_palette,
        digest=str(palette["digest"]),
    )
    _approved_record(
        approval_log,
        subject="content_deletion",
        proposal_id=str(deletion["proposal_id"]),
        digest=str(deletion["digest"]),
    )

    figure_variant_root = raw.get("palette", {}).get("figure_variant_root")
    if figure_variant_root:
        figure_proposal_path = _resolve(base, str(artifacts["figure_color_proposal"]))
        figure_proposal = _load_json(figure_proposal_path)
        _approved_record(
            approval_log,
            subject="scientific_color_unlock",
            proposal_id=str(figure_proposal["proposal_id"]),
            digest=str(figure_proposal["digest"]),
        )
        variant_root = Path(str(figure_variant_root))
        render_content = json.loads(json.dumps(render_content))
        for figure in render_content.get("figures", []):
            figure["path"] = str(variant_root / Path(str(figure["path"])).name)

    registry, blocks = _evidence_registry(source_path.name, content_plan, evidence_data)
    coverage = registry.coverage(blocks)
    if coverage != 1.0:
        raise RuntimeError(f"Evidence coverage is {coverage:.3f}, expected 1.0")

    output = (
        Path(output_directory).resolve()
        if output_directory
        else _resolve(base, str(raw["output"]["directory"]))
    )
    output.mkdir(parents=True, exist_ok=True)

    variant = TemplateRegistry(templates_root).resolve(config.template_family, config.poster_size)
    if not variant.asset.is_file():
        raise FileNotFoundError(variant.asset)

    content, branding = _normalize_render_content(base, render_content, config.branding)
    colors = list(palette["colors"])
    if len(colors) < 6:
        raise ValueError("A PostEx palette needs at least six colors")
    roles = palette.get(
        "roles",
        {
            "text": colors[0],
            "primary": colors[1],
            "secondary": colors[2],
            "highlight": colors[3],
            "canvas": colors[4],
            "accent": "#D9E2EC" if colors[5].upper() == "#FFFFFF" else colors[5],
        },
    )
    required_roles = {"text", "primary", "secondary", "highlight", "canvas", "accent"}
    missing_roles = required_roles.difference(roles)
    if missing_roles:
        raise ValueError(f"Palette is missing roles: {', '.join(sorted(missing_roles))}")
    source_records = [source_path.name]
    source_doi = str(evidence_data.get("source_doi", "")).strip()
    if source_doi:
        source_records.append(source_doi)
    source_records.extend(
        [
            f"palette approval {palette['digest']}",
            f"deletion approval {deletion['digest']}",
        ]
    )
    render_spec = {
        "schema_version": "0.1",
        "canvas": {
            "width": round(variant.width_in * 96),
            "height": round(variant.height_in * 96),
        },
        "template": {
            "family": variant.family,
            "size": variant.size.value,
            "asset": str(variant.asset),
        },
        "theme": {
            "ink": roles["text"],
            "primary": roles["primary"],
            "secondary": roles["secondary"],
            "accent": roles["highlight"],
            "canvas": roles["canvas"],
            "panel": "#FFFFFF",
            "neutral": roles.get("neutral", roles["accent"]),
            "gradient_stops": list(palette.get("gradient_stops", [])),
            "component_behavior": dict(palette.get("component_behavior", {})),
        },
        "branding": branding,
        "content": content,
        "sources": source_records,
    }
    render_spec_path = output / "render-spec.json"
    render_spec_path.write_text(
        json.dumps(render_spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    poster = PosterModel(
        project_id=config.project_id,
        title=config.title,
        language=config.output_language,
        blocks=blocks,
        template_family=config.template_family,
        size=config.poster_size,
        metadata={"render_spec": str(render_spec_path)},
    )
    stem = f"{config.project_id}-{selected_palette}"
    pptx_path = output / f"{stem}.pptx"
    renderer = PptxRenderer(workspace=artifact_workspace)
    renderer.render_pptx(poster, variant.asset, pptx_path)
    repository_root = Path(templates_root).resolve().parents[1]
    render_spec_path.write_text(
        json.dumps(
            _portable_render_spec(
                render_spec,
                project_base=base,
                repository_root=repository_root,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    pdf_path = output / f"{stem}.pdf"
    if pdf_exporter == "powerpoint":
        PowerPointPdfExporter().export_pdf(pptx_path, pdf_path)
    elif pdf_exporter == "libreoffice":
        LibreOfficePdfExporter(office_executable).export_pdf(pptx_path, pdf_path)
    else:
        raise ValueError(f"Unknown PDF exporter: {pdf_exporter}")

    png_path = output / f"{stem}.png"
    layout_path = output / f"{stem}.layout.json"
    extracted_path = output / "extracted-document.json"
    extracted_data = extracted.as_dict()
    extracted_data["source"] = source_path.name
    extracted_path.write_text(
        json.dumps(extracted_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    evidence_report = output / "evidence-report.json"
    evidence_report.write_text(
        json.dumps(
            {
                **evidence_data,
                "coverage": coverage,
                "covered_blocks": len(blocks),
                "total_blocks": len(blocks),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = run_artifact_preflight(
        project_id=config.project_id,
        poster_size=config.poster_size,
        expected_inches=(variant.width_in, variant.height_in),
        pptx=pptx_path,
        pdf=pdf_path,
        png=png_path,
        layout=layout_path,
        evidence_coverage=coverage,
        approvals_current=True,
        branding=branding,
    )
    preflight_path = output / "preflight-report.json"
    preflight_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not report["passed"]:
        failed = [
            item["code"]
            for item in report["findings"]
            if item["severity"] == "error" and not item["passed"]
        ]
        raise RuntimeError("Preflight failed: " + ", ".join(failed))
    return GenerationResult(
        pptx=pptx_path,
        pdf=pdf_path,
        png=png_path,
        evidence_report=evidence_report,
        preflight_report=preflight_path,
        extracted_document=extracted_path,
    )
