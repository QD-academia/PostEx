#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import yaml

from postex.approvals import canonical_digest
from postex.generation import generate_project
from postex.provenance import source_short_id

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "aurora-synthetic"
GOLDENS = ROOT / "evals" / "goldens" / "trusted-export"
SOURCE_SHA256 = "ddd3aad8b3ed4ba3a82beabf6172b6830d22b2ced40345cfd4cf743ca400e2a5"
FAMILIES = ("bioinformatics-pipeline", "observational-cohort", "visual-results")
SIZES = ("a0-landscape", "a1-landscape", "36x48-landscape")


def _identifier(family: str, size: str) -> str:
    family_code = {
        "bioinformatics-pipeline": "bio",
        "observational-cohort": "cohort",
        "visual-results": "visual",
    }[family]
    size_code = {"a0-landscape": "a0", "a1-landscape": "a1", "36x48-landscape": "36x48"}[size]
    return f"trusted-{family_code}-{size_code}"


def _final_approval(project_id: str, family: str, size: str) -> dict[str, str]:
    short_id = source_short_id(project_id, SOURCE_SHA256)
    payload = {
        "project_id": project_id,
        "template_family": family,
        "poster_size": size,
        "palette_id": "default-academic-safe",
        "provenance_enabled": True,
        "source_id": short_id,
    }
    return {
        "subject": "final_release",
        "proposal_id": f"release-{project_id}-{family}-{size}",
        "digest": canonical_digest(payload),
        "decision": "approved",
        "actor": "PostEx golden-fixture maintainer",
        "decided_at": "2026-08-10T12:00:00-04:00",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-workspace", required=True)
    parser.add_argument("--office-executable", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--family", choices=FAMILIES)
    parser.add_argument("--size", choices=SIZES)
    args = parser.parse_args()
    os.environ["POSTEX_NODE"] = args.node
    base = yaml.safe_load((FIXTURE / "project-default.yaml").read_text(encoding="utf-8"))
    approval_base = json.loads((FIXTURE / "approval-log.json").read_text(encoding="utf-8"))

    families = (args.family,) if args.family else FAMILIES
    sizes = (args.size,) if args.size else SIZES
    for family in families:
        for size in sizes:
            project_id = _identifier(family, size)
            target = GOLDENS / family / size
            target.mkdir(parents=True, exist_ok=True)
            project = json.loads(json.dumps(base))
            project["schema_version"] = "0.4"
            project["project_id"] = project_id
            project["title"] = f"AURORA-12 Trusted Export · {family} · {size}"
            project["research_type"] = (
                "observational" if family == "observational-cohort" else "bioinformatics"
            )
            project["template"] = {"family": family, "size": size}
            project["provenance"] = {"enabled": True}
            project["materials"] = [
                {
                    "id": "aurora-12-fixture",
                    "kind": "source-manuscript",
                    "license_ref": "CC0-1.0",
                }
            ]
            project["output"] = {
                "directory": str(target),
                "formats": ["pptx", "pdf", "png", "evidence", "preflight", "manifest"],
                "release_ready": True,
            }
            approval = json.loads(json.dumps(approval_base))
            approval["schema_version"] = "0.4"
            approval["records"].append(_final_approval(project_id, family, size))
            with tempfile.NamedTemporaryFile(
                mode="w", suffix="-approval.json", dir=FIXTURE, encoding="utf-8", delete=False
            ) as approval_file:
                json.dump(approval, approval_file, ensure_ascii=False, indent=2)
                approval_path = Path(approval_file.name)
            project["artifacts"]["approval_log"] = approval_path.name
            with tempfile.NamedTemporaryFile(
                mode="w", suffix="-project.yaml", dir=FIXTURE, encoding="utf-8", delete=False
            ) as project_file:
                yaml.safe_dump(project, project_file, sort_keys=False, allow_unicode=True)
                project_path = Path(project_file.name)
            try:
                result = generate_project(
                    project_path,
                    templates_root=ROOT / "assets" / "templates",
                    artifact_workspace=args.artifact_workspace,
                    output_directory=target,
                    pdf_exporter="libreoffice",
                    office_executable=args.office_executable,
                )
                portable = json.loads(json.dumps(project))
                portable["output"]["directory"] = "."
                portable["source"]["path"] = os.path.relpath(
                    FIXTURE / str(project["source"]["path"]), target
                )
                for key, value in portable["artifacts"].items():
                    if key == "approval_log":
                        continue
                    portable["artifacts"][key] = os.path.relpath(FIXTURE / str(value), target)
                portable["artifacts"]["approval_log"] = "approval-log.json"
                (target / "approval-log.json").write_text(
                    json.dumps(approval, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                (target / "golden-project.yaml").write_text(
                    yaml.safe_dump(portable, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                print(f"verified {family}/{size}: {result.manifest.relative_to(ROOT)}")
            finally:
                project_path.unlink(missing_ok=True)
                approval_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
