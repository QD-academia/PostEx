from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from postex import __version__
from postex.provenance import ProvenancePolicy, sha256_file

MANIFEST_FILENAME = "postex-manifest.json"


def _portable(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.name


def asset_references(
    *, project: dict[str, Any], render_content: dict[str, Any], base: Path
) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    declared = project.get("materials", [])
    if isinstance(declared, list):
        for item in declared:
            if isinstance(item, dict):
                references.append(dict(item))
    branding = project.get("branding", {})
    if isinstance(branding, dict):
        for logo in branding.get("logos", []):
            if not isinstance(logo, dict) or not logo.get("path"):
                continue
            path = (base / str(logo["path"])).resolve()
            references.append(
                {
                    "id": str(logo.get("id", path.stem)),
                    "kind": "logo",
                    "path": _portable(path, base),
                    "sha256": sha256_file(path) if path.is_file() else None,
                    "license_ref": str(logo.get("license", "not-provided")),
                }
            )
    for figure in render_content.get("figures", []):
        if not isinstance(figure, dict) or not figure.get("path"):
            continue
        path = (base / str(figure["path"])).resolve()
        references.append(
            {
                "id": str(figure.get("id", path.stem)),
                "kind": "scientific_figure",
                "path": _portable(path, base),
                "sha256": sha256_file(path) if path.is_file() else None,
                "license_ref": str(figure.get("license", "source-manuscript")),
                "pixel_locked": True,
            }
        )
    return references


def output_hashes(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "path": path.name,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for name, path in sorted(paths.items())
        if path.is_file() and path.name != MANIFEST_FILENAME
    }


def build_manifest(
    *,
    project_id: str,
    input_path: Path,
    input_sha256: str,
    template: dict[str, Any],
    palette_id: str,
    palette_source: str,
    assets: list[dict[str, Any]],
    approval_log: dict[str, Any],
    provenance: ProvenancePolicy,
    outputs: dict[str, dict[str, Any]],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    approvals = [
        dict(record)
        for record in approval_log.get("records", [])
        if isinstance(record, dict)
    ]
    return {
        "schema_version": "0.4",
        "postex_version": __version__,
        "project_id": project_id,
        "source_id": provenance.source_id,
        "input": {
            "path": input_path.name,
            "sha256": input_sha256,
        },
        "template": template,
        "palette": {"palette_id": palette_id, "source": palette_source},
        "assets": assets,
        "approvals": approvals,
        "provenance": provenance.as_dict(),
        "preflight": preflight,
        "outputs": outputs,
    }


def write_manifest(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
