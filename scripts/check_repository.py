#!/usr/bin/env python3
"""Check repository contracts without network or office applications."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "README.md",
    "PRD.md",
    "ARCHITECTURE.md",
    "pyproject.toml",
    "LICENSE",
    "NOTICE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "configs",
    "schemas",
    "schemas/postex-manifest.schema.json",
    "src/postex",
    "assets/templates",
    "assets/palettes/catalog.yaml",
    "assets/palettes/rights.yaml",
    "examples",
    "tests",
    "evals",
    "docs",
    "docker",
    "skills/codex/postex/SKILL.md",
    "skills/claude-code/postex/SKILL.md",
    "examples/palette-fusion/project.yaml",
    "examples/palette-fusion/poster-brief.yaml",
    "examples/palette-fusion/palette-dna.yaml",
    "docs/releases/v0.4.0a1.md",
    "evals/goldens/trusted-export",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"missing: {relative}")

    schemas = {}
    for path in sorted((ROOT / "schemas").glob("*.json")):
        try:
            schema = load_json(path)
            Draft202012Validator.check_schema(schema)
            schemas[path.name] = schema
        except Exception as exc:  # validation tool should collect all failures
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    project_validator = Draft202012Validator(schemas["project.schema.json"])
    project_examples = sorted((ROOT / "examples").rglob("*project.yaml"))
    for path in project_examples:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for issue in project_validator.iter_errors(data):
            errors.append(f"{path.relative_to(ROOT)}: {issue.message}")

    fusion_example = ROOT / "examples" / "palette-fusion"
    for filename, schema_name in (
        ("poster-brief.yaml", "poster-brief.schema.json"),
        ("palette-dna.yaml", "palette-dna.schema.json"),
        ("design-locks.json", "design-locks.schema.json"),
    ):
        path = fusion_example / filename
        try:
            data = (
                load_json(path)
                if path.suffix == ".json"
                else yaml.safe_load(path.read_text(encoding="utf-8"))
            )
            for issue in Draft202012Validator(schemas[schema_name]).iter_errors(data):
                errors.append(f"{path.relative_to(ROOT)}: {issue.message}")
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    palette_output = fusion_example / "outputs" / "palette" / "palette-candidates.json"
    if palette_output.exists():
        data = load_json(palette_output)
        for issue in Draft202012Validator(schemas["palette-studio.schema.json"]).iter_errors(data):
            errors.append(f"{palette_output.relative_to(ROOT)}: {issue.message}")
        dna_validator = Draft202012Validator(schemas["palette-dna.schema.json"])
        for index, candidate in enumerate(data.get("candidates", [])):
            for issue in dna_validator.iter_errors(candidate.get("palette", {})):
                errors.append(
                    f"{palette_output.relative_to(ROOT)} candidate {index}: {issue.message}"
                )

    template_validator = Draft202012Validator(schemas["template.schema.json"])
    families = ("bioinformatics-pipeline", "observational-cohort", "visual-results")
    sizes = ("a0-landscape", "a1-landscape", "36x48-landscape")
    for family in families:
        metadata = ROOT / "assets" / "templates" / family / "template.yaml"
        data = yaml.safe_load(metadata.read_text(encoding="utf-8"))
        for issue in template_validator.iter_errors(data):
            errors.append(f"{metadata.relative_to(ROOT)}: {issue.message}")
        for size in sizes:
            placeholder = metadata.parent / size / "PLACEHOLDER.md"
            asset = metadata.parent / data["variants"][size]["asset"]
            if placeholder.exists():
                errors.append(f"unfinished template placeholder: {family}/{size}")
            for filename in (
                asset.name,
                "template.png",
                "template-spec.json",
                "template.layout.json",
                "template.inspect.ndjson",
            ):
                if not (metadata.parent / size / filename).is_file():
                    errors.append(f"missing template asset: {family}/{size}/{filename}")

    manifest_validator = Draft202012Validator(schemas["postex-manifest.schema.json"])
    preflight_validator = Draft202012Validator(schemas["preflight-report.schema.json"])
    golden_root = ROOT / "evals" / "goldens" / "trusted-export"
    golden_count = 0
    for family in families:
        for size in sizes:
            directory = golden_root / family / size
            manifest_path = directory / "postex-manifest.json"
            preflight_path = directory / "preflight-report.json"
            if not manifest_path.is_file() or not preflight_path.is_file():
                errors.append(f"missing Trusted Export golden: {family}/{size}")
                continue
            golden_count += 1
            manifest = load_json(manifest_path)
            preflight = load_json(preflight_path)
            for issue in manifest_validator.iter_errors(manifest):
                errors.append(f"{manifest_path.relative_to(ROOT)}: {issue.message}")
            for issue in preflight_validator.iter_errors(preflight):
                errors.append(f"{preflight_path.relative_to(ROOT)}: {issue.message}")
            if not preflight.get("release_ready"):
                errors.append(f"golden is not release-ready: {family}/{size}")

    for path in (
        ROOT / "skills" / "codex" / "postex" / "SKILL.md",
        ROOT / "skills" / "claude-code" / "postex" / "SKILL.md",
    ):
        text = path.read_text(encoding="utf-8")
        if "[TODO" in text or not text.startswith("---\nname: postex\ndescription:"):
            errors.append(f"invalid skill draft: {path.relative_to(ROOT)}")

    if errors:
        print("Repository check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Repository check passed: required files, {len(schemas)} schemas, "
        f"{len(project_examples)} project examples, 3 template families, "
        f"9 production template assets, {golden_count} Trusted Export goldens, "
        "Palette Fusion contracts, and 2 skill drafts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
