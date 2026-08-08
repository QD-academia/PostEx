#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"
OUTPUT = ROOT / "evals" / "previews"
RUNNER = ROOT / "src" / "postex" / "renderers" / "artifact_renderer.mjs"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def facts(case: dict) -> list[dict]:
    return list(case.get("facts", []))


def metric_value(item: dict) -> str:
    value = str(item["required_text"])
    tokens = re.findall(r"(?:[A-Za-z]{1,4}=)?\d[\d.,]*|[A-Za-z][A-Za-z0-9]*", value)
    return (tokens[0] if tokens else "FACT")[:10].rstrip(",.")


def render_content(case: dict) -> dict:
    case_facts = facts(case)
    metric_items = [
        {
            "value": metric_value(item),
            "label": str(item["claim_id"]).replace("-", " ")[:18],
        }
        for item in case_facts[:3]
    ]
    while len(metric_items) < 3:
        metric_items.append({"value": "—", "label": "source fact"})
    sections = [
        str(value).replace("_", " ").title() for value in case.get("expected_sections", [])[:4]
    ]
    while len(sections) < 4:
        sections.append("Evidence review")
    fact_lines = "\n".join(
        f"• {item['claim_id'].replace('-', ' ')}: {item['required_text']}" for item in case_facts
    )
    placeholder = {
        "placeholder": "SOURCE FIGURE SLOT",
        "alt": "Evaluation-only source figure placeholder",
        "caption": "Source figure selected during full-paper generation",
        "source": f"Source: {case['doi']}",
    }
    return {
        "title": case["title"],
        "authors": "Source-grounded PostEx evaluation fixture",
        "affiliations": f"{case['research_type'].title()} profile · {case['license']}",
        "citation": f"DOI {case['doi']}",
        "header_metrics": metric_items,
        "question_heading": "Communication objective",
        "question": "Present the paper's design, central evidence and interpretation boundary in a traceable conference-poster format.",
        "question_evidence": f"Evidence fixture: {case['doi']}",
        "pipeline_heading": "Required evidence structure",
        "pipeline_steps": sections,
        "dataset_kicker": "SOURCE CONTRACT",
        "datasets": f"Input: full paper\nLicense: {case['license']}\nProfile: {case['research_type']}\nClaims checked: {len(case_facts)}",
        "dataset_evidence": case["source_url"],
        "figure_one_heading": "Methods and source evidence",
        "takeaway": str(case_facts[0]["required_text"]) if case_facts else case["title"],
        "takeaway_subtitle": "Key facts remain bound to the source and study design",
        "takeaway_evidence": f"Evidence fixture: {case['doi']}",
        "figure_two_heading": "Primary evidence",
        "validation_heading": "Required factual anchors",
        "validation": fact_lines or "• No numerical fixture claims",
        "validation_evidence": f"Ground-truth case: {case['case_id']}",
        "performance_strip": "No unsupported numerical or causal expansion permitted",
        "biology_heading": "Fact checks",
        "biology_metrics": metric_items,
        "biology_evidence": "Machine-checkable evaluation fixture",
        "validation_visual_heading": "Independent evidence slot",
        "conclusion_heading": "Interpretation boundary",
        "conclusion": "Interpret findings only within the source study design, population, methods and reported uncertainty.",
        "conclusion_evidence": f"Source and license: {case['doi']} · {case['license']}",
        "footer_source": f"{case['title']} · {case['license']}",
        "footer_status": "Evaluation preview · not a release poster",
        "figures": [dict(placeholder) for _ in range(4)],
    }


def build_spec(case: dict) -> dict:
    return {
        "schema_version": "0.1",
        "canvas": {"width": 4494, "height": 3179},
        "template": {
            "family": "bioinformatics-pipeline",
            "size": "a0-landscape",
        },
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
        "content": render_content(case),
        "sources": [case["source_url"], f"License: {case['license']}"],
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
    runner = workspace / "postex-eval-renderer.mjs"
    shutil.copy2(RUNNER, runner)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    rendered = 0
    for path in sorted(CASES.glob("*.json")):
        case = load(path)
        if case.get("fictional", False) and not case.get("render_preview", False):
            continue
        target = OUTPUT / case["case_id"]
        target.mkdir(parents=True, exist_ok=True)
        spec = target / "preview-spec.json"
        spec.write_text(
            json.dumps(build_spec(case), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        output = target / f"{case['case_id']}.pptx"
        completed = subprocess.run(
            [
                args.node,
                str(runner),
                "--spec",
                str(spec),
                "--output",
                str(output),
            ],
            cwd=workspace,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"{case['case_id']}: " + (completed.stderr or completed.stdout).strip()
            )
        rendered += 1
        print(f"rendered {case['case_id']}")
    print(f"rendered_evaluation_previews={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
