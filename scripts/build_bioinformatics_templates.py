#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "assets" / "templates" / "bioinformatics-pipeline"
RUNNER = ROOT / "src" / "postex" / "renderers" / "artifact_renderer.mjs"

VARIANTS = {
    "a0-landscape": (46.811, 33.110),
    "a1-landscape": (33.110, 23.386),
    "36x48-landscape": (48.0, 36.0),
}


def placeholder_content() -> dict:
    figure = {
        "placeholder": "SCIENTIFIC FIGURE",
        "alt": "Editable scientific figure placeholder",
        "caption": "Figure caption",
        "source": "Evidence/source locator",
    }
    return {
        "title": "Evidence-traceable bioinformatics poster title",
        "authors": "Author names",
        "affiliations": "Institutions and collaborating centers",
        "citation": "Journal or conference · DOI",
        "header_metrics": [
            {"value": "N", "label": "signature features"},
            {"value": "N", "label": "discovery samples"},
            {"value": "N", "label": "validation cohorts"},
        ],
        "question_heading": "Research question",
        "question": "State the biological or clinical question in two concise sentences.",
        "question_evidence": "Evidence: source page or section",
        "pipeline_heading": "Analysis pipeline",
        "pipeline_steps": [
            "Input biomarkers or features",
            "Feature selection",
            "Model construction",
            "Independent validation",
        ],
        "dataset_kicker": "DATA FOUNDATION",
        "datasets": "Discovery cohort\nTraining and test split\nExternal validation\nOrthogonal validation",
        "dataset_evidence": "Evidence: methods and dataset table",
        "figure_one_heading": "From features to signature",
        "takeaway": "Place the single most important result here",
        "takeaway_subtitle": "Explain what the result means for the audience",
        "takeaway_evidence": "Evidence: result section and figure",
        "figure_two_heading": "Primary performance",
        "validation_heading": "Independent and external validation",
        "validation": "• Primary adjusted result\n• External validation\n• Negative or inconsistent findings\n• Interpretation boundary",
        "validation_evidence": "Evidence: result pages",
        "performance_strip": "Primary performance statistic or calibrated model comparison",
        "biology_heading": "Biological interpretation",
        "biology_metrics": [
            {"value": "Effect", "label": "program or pathway"},
            {"value": "Effect", "label": "program or pathway"},
            {"value": "Effect", "label": "program or pathway"},
        ],
        "biology_evidence": "Evidence: biological analysis",
        "validation_visual_heading": "Orthogonal validation",
        "conclusion_heading": "Conclusion",
        "conclusion": "State the supported conclusion and retain the most important limitation.",
        "conclusion_evidence": "Evidence: discussion and conclusion",
        "footer_source": "Source citation · content mode · asset license",
        "footer_status": "Approval status · scientific colors locked",
        "figures": [dict(figure) for _ in range(4)],
    }


def build_spec(width_in: float, height_in: float, size: str) -> dict:
    return {
        "schema_version": "0.1",
        "canvas": {
            "width": round(width_in * 96),
            "height": round(height_in * 96),
        },
        "template": {"family": "bioinformatics-pipeline", "size": size},
        "theme": {
            "ink": "#102A43",
            "primary": "#0F5F73",
            "secondary": "#2C8C99",
            "accent": "#E8B44C",
            "canvas": "#F6F8FA",
            "panel": "#FFFFFF",
            "neutral": "#D9E2EC",
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
        "content": placeholder_content(),
        "sources": [
            "PostEx official template asset; CC BY 4.0",
            "No third-party logo or scientific figure is embedded",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-workspace", required=True)
    parser.add_argument("--node", default=shutil.which("node"))
    args = parser.parse_args()
    if not args.node:
        raise SystemExit("Node.js was not found")
    workspace = Path(args.artifact_workspace).resolve()
    if not (workspace / "node_modules").exists():
        raise SystemExit("Artifact Tool workspace is not initialized")
    workspace_runner = workspace / "postex-template-renderer.mjs"
    shutil.copy2(RUNNER, workspace_runner)

    for size, dimensions in VARIANTS.items():
        target = FAMILY / size
        target.mkdir(parents=True, exist_ok=True)
        spec_path = target / "template-spec.json"
        spec_path.write_text(
            json.dumps(
                build_spec(dimensions[0], dimensions[1], size),
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
            raise RuntimeError(f"{size} failed: " + (completed.stderr or completed.stdout).strip())
        print(f"created {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
