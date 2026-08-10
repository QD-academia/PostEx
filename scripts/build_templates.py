#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "assets" / "templates"
RUNNER = ROOT / "src" / "postex" / "renderers" / "artifact_renderer.mjs"

VARIANTS = {
    "a0-landscape": (46.811, 33.110),
    "a1-landscape": (33.110, 23.386),
    "36x48-landscape": (48.0, 36.0),
}


def _figure(label: str) -> dict[str, str]:
    return {
        "placeholder": label,
        "alt": f"Editable {label.lower()} placeholder",
        "caption": f"{label.title()} caption",
        "source": "Evidence/source locator",
    }


def _base_content() -> dict:
    return {
        "title": "Evidence-traceable academic poster title",
        "authors": "Author names",
        "affiliations": "Institutions and collaborating centers",
        "citation": "Journal or conference · DOI",
        "header_metrics": [
            {"value": "N", "label": "primary observations"},
            {"value": "N", "label": "analysis samples"},
            {"value": "N", "label": "validation units"},
        ],
        "question_heading": "Research question",
        "question": "State the scientific question in two concise sentences.",
        "question_evidence": "Evidence: source page or section",
        "pipeline_heading": "Study workflow",
        "pipeline_steps": ["Source population", "Analysis set", "Primary model", "Validation"],
        "dataset_kicker": "DATA FOUNDATION",
        "datasets": "Discovery set\nPrimary analysis\nValidation set\nSensitivity analysis",
        "dataset_evidence": "Evidence: methods and dataset table",
        "figure_one_heading": "Design and data flow",
        "takeaway": "Place the single most important result here",
        "takeaway_subtitle": "Explain what the result means for the audience",
        "takeaway_evidence": "Evidence: result section and figure",
        "figure_two_heading": "Primary result",
        "validation_heading": "Robustness and validation",
        "validation": "• Primary adjusted result\n• External validation\n• Negative findings\n• Interpretation boundary",
        "validation_evidence": "Evidence: result pages",
        "performance_summary": "Primary estimate · uncertainty · validation",
        "biology_heading": "Supporting evidence",
        "biology_metrics": [
            {"value": "Effect", "label": "primary estimate"},
            {"value": "95% CI", "label": "uncertainty"},
            {"value": "P", "label": "robustness"},
        ],
        "biology_evidence": "Evidence: supporting analysis",
        "validation_visual_heading": "Sensitivity analysis",
        "conclusion_heading": "Conclusion",
        "conclusion": "State the supported conclusion and retain the most important limitation.",
        "conclusion_evidence": "Evidence: discussion and conclusion",
        "footer_source": "Source citation · content mode · asset license",
        "footer_status": "Approvals current · scientific colors locked",
        "figures": [_figure("scientific figure") for _ in range(4)],
    }


def family_content(family: str) -> dict:
    content = _base_content()
    if family == "bioinformatics-pipeline":
        content.update(
            {
                "title": "Evidence-traceable bioinformatics poster title",
                "question_heading": "Biological question",
                "pipeline_heading": "Analysis pipeline",
                "pipeline_steps": [
                    "Input biomarkers or features",
                    "Feature selection",
                    "Model construction",
                    "Independent validation",
                ],
                "figure_one_heading": "From features to signature",
                "biology_heading": "Biological interpretation",
                "validation_visual_heading": "Orthogonal validation",
            }
        )
    elif family == "observational-cohort":
        content.update(
            {
                "title": "Transparent observational cohort poster title",
                "header_metrics": [
                    {"value": "N", "label": "eligible participants"},
                    {"value": "N", "label": "outcome events"},
                    {"value": "N", "label": "sensitivity models"},
                ],
                "question_heading": "Clinical question",
                "pipeline_heading": "Cohort construction",
                "pipeline_steps": [
                    "Define source population",
                    "Apply eligibility criteria",
                    "Specify exposure and outcome",
                    "Fit adjusted models",
                ],
                "dataset_kicker": "COHORT ACCOUNTING",
                "figure_one_heading": "Eligibility and follow-up",
                "figure_two_heading": "Adjusted primary outcome",
                "validation_heading": "Bias and sensitivity checks",
                "biology_heading": "Effect estimates",
                "validation_visual_heading": "Subgroups and robustness",
                "conclusion_heading": "Interpretation and limitations",
                "figures": [
                    _figure("cohort flow diagram"),
                    _figure("adjusted outcome plot"),
                    _figure("baseline characteristics visual"),
                    _figure("sensitivity analysis plot"),
                ],
            }
        )
    elif family == "visual-results":
        content.update(
            {
                "title": "Result-first visual research poster title",
                "question_heading": "One-sentence question",
                "pipeline_heading": "Methods at a glance",
                "pipeline_steps": [
                    "Study design",
                    "Primary measurement",
                    "Analysis strategy",
                    "Validation boundary",
                ],
                "dataset_kicker": "ESSENTIAL CONTEXT",
                "figure_one_heading": "How the result was produced",
                "takeaway": "Lead with the decisive visual result",
                "takeaway_subtitle": "Keep the interpretation adjacent to its evidence",
                "figure_two_heading": "Hero result",
                "validation_heading": "What changes the conclusion",
                "biology_heading": "Three result anchors",
                "validation_visual_heading": "Supporting result",
                "conclusion_heading": "Why this result matters",
                "figures": [
                    _figure("methods summary"),
                    _figure("hero result"),
                    _figure("supporting result"),
                    _figure("validation result"),
                ],
            }
        )
    else:
        raise ValueError(f"Unknown family: {family}")
    return content


def build_spec(family: str, width_in: float, height_in: float, size: str) -> dict:
    return {
        "schema_version": "0.4",
        "canvas": {"width": round(width_in * 96), "height": round(height_in * 96)},
        "template": {"family": family, "size": size},
        "theme": {
            "ink": "#102A43",
            "primary": "#0F5F73",
            "secondary": "#2C8C99",
            "accent": "#E8B44C",
            "canvas": "#F6F8FA",
            "panel": "#FFFFFF",
            "neutral": "#D9E2EC",
        },
        "typography": {
            "language": "en",
            "latin_font_family": "Arial",
            "cjk_font_family": "Noto Sans CJK SC",
        },
        "branding": {
            "logo_mode": "placeholder",
            "placeholders": [
                {
                    "id": "institution-logo",
                    "role": "institution",
                    "placement": "header-right",
                    "label": "Institution logo",
                }
            ],
        },
        "provenance": {
            "enabled": True,
            "source_id": "PX-00000000",
            "mark_text": "Made with PostEx™ · PX-00000000",
            "object_name": "POSTEX_PROVENANCE_MARK",
        },
        "content": family_content(family),
        "sources": [
            "PostEx official template asset; CC BY 4.0",
            "No third-party logo or scientific figure is embedded",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-workspace", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument(
        "--family",
        action="append",
        choices=("bioinformatics-pipeline", "observational-cohort", "visual-results"),
    )
    args = parser.parse_args()
    workspace = Path(args.artifact_workspace).resolve()
    if not (workspace / "node_modules").exists():
        raise SystemExit("Artifact Tool workspace is not initialized")
    workspace_runner = workspace / "postex-template-renderer.mjs"
    shutil.copy2(RUNNER, workspace_runner)
    families = args.family or [
        "bioinformatics-pipeline",
        "observational-cohort",
        "visual-results",
    ]

    for family in families:
        family_root = TEMPLATES / family
        metadata_path = family_root / "template.yaml"
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        for size, dimensions in VARIANTS.items():
            target = family_root / size
            target.mkdir(parents=True, exist_ok=True)
            spec_path = target / "template-spec.json"
            spec_path.write_text(
                json.dumps(
                    build_spec(family, dimensions[0], dimensions[1], size),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            output = target / "template.pptx"
            completed = subprocess.run(
                [
                    args.node,
                    str(workspace_runner),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(output),
                ],
                cwd=workspace,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout).strip()
                raise RuntimeError(f"{family}/{size} failed: {detail}")
            digest = hashlib.sha256(output.read_bytes()).hexdigest()
            variant = metadata["variants"][size]
            variant["layout_spec"] = f"{size}/template-spec.json"
            variant["sha256"] = digest
            print(f"created {output.relative_to(ROOT)}")
        metadata_path.write_text(
            yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
