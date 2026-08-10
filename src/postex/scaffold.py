from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from postex.approvals import canonical_digest
from postex.provenance import sha256_file


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (normalized or "postex-project")[:64].rstrip("-")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_project_scaffold(
    source: str | Path,
    *,
    project_directory: str | Path | None = None,
    project_id: str | None = None,
    title: str | None = None,
    research_type: str = "bioinformatics",
    template_family: str = "bioinformatics-pipeline",
    poster_size: str = "a0-landscape",
) -> Path:
    """Create a local, approval-gated project without copying or uploading the source."""

    source_path = Path(source).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    identifier = _slug(project_id or source_path.stem)
    target = (
        Path(project_directory).resolve()
        if project_directory
        else (Path.cwd() / f"{identifier}-postex").resolve()
    )
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Project directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)

    palette_payload = {
        "colors": ["#102A43", "#0F5F73", "#2C8C99", "#E8B44C", "#F6F8FA", "#D9E2EC"],
        "source": "PostEx default biomedical design system; approval required",
        "semantic_colors_locked": True,
        "simulations": ["poster", "deuteranopia", "protanopia", "grayscale", "print"],
        "roles": {
            "text": "#102A43",
            "primary": "#0F5F73",
            "secondary": "#2C8C99",
            "highlight": "#E8B44C",
            "canvas": "#F6F8FA",
            "accent": "#D9E2EC",
        },
    }
    palette = {
        "palette_id": "default-academic-safe",
        "status": "pending",
        "digest": canonical_digest(palette_payload),
        **palette_payload,
    }
    deletion_payload: dict[str, list[Any]] = {"items": [], "figure_plan": []}
    deletion = {
        "schema_version": "0.4",
        "proposal_id": "initial-content-deletion",
        "status": "pending",
        "digest": canonical_digest(deletion_payload),
        **deletion_payload,
    }
    source_relative = os.path.relpath(source_path, target)
    source_type = source_path.suffix.lower().lstrip(".") or "pdf"
    source_type = "latex" if source_type in {"tex", "latex"} else source_type
    project = {
        "schema_version": "0.4",
        "project_id": identifier,
        "title": title or source_path.stem.replace("-", " ").replace("_", " "),
        "research_type": research_type,
        "input_language": "en",
        "output_language": "en",
        "content_mode": "traceable",
        "source": {
            "type": source_type,
            "path": source_relative,
            "published": False,
            "sha256": sha256_file(source_path),
        },
        "provider": {"name": "local-only", "model": "none"},
        "template": {"family": template_family, "size": poster_size},
        "branding": {"logo_mode": "none"},
        "privacy": {
            "require_cloud_upload_approval": True,
            "allow_network_palette_sources": False,
        },
        "palette": {
            "selected": "default-academic-safe",
            "require_approval": True,
            "lock_scientific_figure_colors": True,
        },
        "fusion": {
            "require_structure_approval": True,
            "content_signals": {"hero_claim_id": "pending", "methods_complexity": "medium"},
        },
        "provenance": {"enabled": True},
        "artifacts": {
            "content_plan": "content-plan.json",
            "evidence": "evidence.json",
            "deletion_proposal": "deletion-proposal.json",
            "palette_proposals": "palette-proposals.json",
            "approval_log": "approval-log.json",
            "render_content": "render-content.json",
            "poster_brief": "poster-brief.yaml",
            "palette_dna": "palette-dna.yaml",
        },
        "output": {
            "directory": "output",
            "formats": ["pptx", "pdf", "png", "evidence", "preflight", "manifest"],
            "release_ready": False,
        },
    }
    (target / "project.yaml").write_text(
        yaml.safe_dump(project, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    _write_json(target / "content-plan.json", {"schema_version": "0.4", "blocks": []})
    _write_json(target / "evidence.json", {"schema_version": "0.4", "records": []})
    _write_json(target / "deletion-proposal.json", deletion)
    _write_json(
        target / "palette-proposals.json",
        {
            "schema_version": "0.4",
            "approval_required": True,
            "scientific_figure_colors_locked": True,
            "proposals": [palette],
        },
    )
    _write_json(
        target / "approval-log.json",
        {
            "schema_version": "0.4",
            "records": [],
            "required_before_render": [
                "content_deletion",
                "palette_application",
                "poster_structure",
            ],
            "required_before_release": ["final_release"],
        },
    )
    _write_json(target / "render-content.json", {"status": "awaiting_content_plan"})
    (target / "poster-brief.yaml").write_text(
        yaml.safe_dump(
            {
                "audience": [],
                "takeaway": "",
                "visual_tone": [],
                "palette_source": "default",
                "logo_treatment": "none",
                "figure_edit_permission": "ask",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (target / "palette-dna.yaml").write_text(
        yaml.safe_dump({"status": "pending_palette_fusion", **palette}, sort_keys=False),
        encoding="utf-8",
    )
    return target / "project.yaml"
