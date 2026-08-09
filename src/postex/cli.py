from __future__ import annotations

import argparse
import json
from pathlib import Path

from postex.brief import BRIEF_QUESTIONS, poster_brief_from_mapping
from postex.config import load_mapping, load_project
from postex.fusion import ContentSignals, FusionEngine
from postex.generation import generate_project
from postex.palette import (
    Palette,
    PaletteStudio,
    palette_dna_from_mapping,
    render_palette_studio_html,
)
from postex.palette_catalog import load_palette_catalog
from postex.rationale import build_design_rationale, render_design_rationale_html
from postex.research import PROFILES
from postex.templates import TemplateRegistry
from postex.workflow import PosterWorkflow


def _default_templates() -> Path:
    packaged = Path(__file__).resolve().parent / "assets" / "templates"
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[2] / "assets" / "templates"


def command_validate(path: str) -> int:
    config = load_project(path)
    print(json.dumps(config.as_dict(), default=str, ensure_ascii=False, indent=2))
    return 0


def command_plan(path: str) -> int:
    config = load_project(path)
    profile = PROFILES[config.research_type]
    result = {
        "project_id": config.project_id,
        "research_type": config.research_type.value,
        "sections": profile.required_sections,
        "preferred_visuals": profile.preferred_visuals,
        "template": f"{config.template_family}/{config.poster_size.value}",
        "branding": config.branding,
        "poster_brief": config.poster_brief,
        "fusion": config.fusion,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_brief_questions() -> int:
    print(json.dumps({"questions": list(BRIEF_QUESTIONS)}, ensure_ascii=False, indent=2))
    return 0


def _project_artifact(path: Path, raw: dict, key: str) -> Path:
    try:
        relative = raw["artifacts"][key]
    except KeyError as exc:
        raise ValueError(f"Project does not declare artifacts.{key}") from exc
    return (path.parent / str(relative)).resolve()


def command_fusion_plan(path: str, output: str | None) -> int:
    project_path = Path(path).resolve()
    raw = load_mapping(project_path)
    brief = poster_brief_from_mapping(
        load_mapping(_project_artifact(project_path, raw, "poster_brief"))
    )
    palette = palette_dna_from_mapping(
        load_mapping(_project_artifact(project_path, raw, "palette_dna"))
    )
    signal_data = raw.get("fusion", {}).get("content_signals", {})
    signals = ContentSignals(
        hero_claim_id=str(signal_data.get("hero_claim_id", "claim:hero")),
        main_visual_id=str(signal_data["main_visual_id"])
        if signal_data.get("main_visual_id")
        else None,
        figure_count=int(signal_data.get("figure_count", 0)),
        table_count=int(signal_data.get("table_count", 0)),
        methods_complexity=str(signal_data.get("methods_complexity", "medium")),
    )
    candidates = FusionEngine().propose(brief, palette, signals)
    out = Path(output).resolve() if output else (project_path.parent / "outputs" / "fusion")
    out.mkdir(parents=True, exist_ok=True)
    plan_path = out / "fusion-candidates.json"
    plan_path.write_text(
        json.dumps(
            {"schema_version": "0.2", "candidates": [item.as_payload() for item in candidates]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    recommended = next(item for item in candidates if item.recommended)
    rationale_path = render_design_rationale_html(
        build_design_rationale(brief, palette, recommended), out / "design-rationale.html"
    )
    print(
        json.dumps(
            {
                "fusion_candidates": str(plan_path),
                "design_rationale": str(rationale_path),
                "recommended": recommended.candidate_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_palette_plan(path: str, output: str | None) -> int:
    project_path = Path(path).resolve()
    raw = load_mapping(project_path)
    seed = palette_dna_from_mapping(
        load_mapping(_project_artifact(project_path, raw, "palette_dna"))
    )
    candidates = PaletteStudio().propose(seed)
    out = Path(output).resolve() if output else (project_path.parent / "outputs" / "palette")
    out.mkdir(parents=True, exist_ok=True)
    plan_path = out / "palette-candidates.json"
    payload = {
        "schema_version": "0.2",
        "candidates": [item.as_payload() for item in candidates],
    }
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preview_path = render_palette_studio_html(candidates, out / "palette-studio.html")
    print(
        json.dumps(
            {
                "palette_candidates": str(plan_path),
                "palette_studio": str(preview_path),
                "recommended": candidates[1].palette.palette_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_workflow_demo() -> int:
    workflow = PosterWorkflow()
    stages = [workflow.stage.value]
    workflow.request_cloud("openai", "fictional-study.pdf", {"abstract": "Example"})
    stages.append(workflow.stage.value)
    workflow.approve_cloud("demo-user")
    stages.append(workflow.stage.value)
    workflow.propose_deletions("deletions-v1", ["source:discussion:3"])
    stages.append(workflow.stage.value)
    workflow.approve_deletions("demo-user")
    workflow.palette.preview("palette-v1", Palette(("#0B3954", "#087E8B", "#FF5A5F"), "fictional"))
    stages.append(workflow.stage.value)
    workflow.approve_palette("demo-user")
    stages.append(workflow.stage.value)
    print(json.dumps({"stages": stages}, indent=2))
    return 0


def command_templates(root: str) -> int:
    registry = TemplateRegistry(root)
    print(json.dumps({"families": registry.families()}, indent=2))
    return 0


def command_palette_catalog(root: str, show_blockers: bool) -> int:
    catalog = load_palette_catalog(root)
    payload = catalog.summary()
    if show_blockers:
        payload["blockers"] = catalog.release_blockers()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["blocked"] == 0 else 1


def command_generate(
    path: str,
    *,
    templates_root: str,
    artifact_workspace: str,
    output: str | None,
    pdf_exporter: str,
    office_executable: str | None,
) -> int:
    result = generate_project(
        path,
        templates_root=templates_root,
        artifact_workspace=artifact_workspace,
        output_directory=output,
        pdf_exporter=pdf_exporter,
        office_executable=office_executable,
    )
    print(
        json.dumps(
            {
                "pptx": str(result.pptx),
                "pdf": str(result.pdf),
                "png": str(result.png),
                "evidence_report": str(result.evidence_report),
                "preflight_report": str(result.preflight_report),
                "extracted_document": str(result.extracted_document),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="postex")
    parser.add_argument("--version", action="version", version="postex 0.3.0a2")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Load and validate project configuration")
    validate.add_argument("project")
    plan = sub.add_parser("plan", help="Show the domain-aware poster plan")
    plan.add_argument("project")
    sub.add_parser("workflow-demo", help="Run a local approval-state demonstration")
    sub.add_parser("brief-questions", help="Print the v0.2 pre-generation interview")
    fusion = sub.add_parser("fusion-plan", help="Create three Palette Fusion structure candidates")
    fusion.add_argument("project")
    fusion.add_argument("--output")
    palettes = sub.add_parser("palette-plan", help="Create three named Palette Studio candidates")
    palettes.add_argument("project")
    palettes.add_argument("--output")
    catalog = sub.add_parser(
        "palette-catalog",
        help="Audit built-in palette selections, cutouts and redistribution rights",
    )
    catalog.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    catalog.add_argument("--show-blockers", action="store_true")
    templates = sub.add_parser("templates", help="List official template families")
    templates.add_argument("--root", default=str(_default_templates()))
    generate = sub.add_parser(
        "generate",
        help="Run local extraction, approved rendering, PDF export and preflight",
    )
    generate.add_argument("project")
    generate.add_argument("--templates-root", default=str(_default_templates()))
    generate.add_argument("--artifact-workspace", required=True)
    generate.add_argument("--output")
    generate.add_argument(
        "--pdf-exporter",
        choices=("powerpoint", "libreoffice"),
        default="libreoffice",
    )
    generate.add_argument("--office-executable")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate":
        return command_validate(args.project)
    if args.command == "plan":
        return command_plan(args.project)
    if args.command == "workflow-demo":
        return command_workflow_demo()
    if args.command == "brief-questions":
        return command_brief_questions()
    if args.command == "fusion-plan":
        return command_fusion_plan(args.project, args.output)
    if args.command == "palette-plan":
        return command_palette_plan(args.project, args.output)
    if args.command == "palette-catalog":
        return command_palette_catalog(args.root, args.show_blockers)
    if args.command == "templates":
        return command_templates(args.root)
    if args.command == "generate":
        return command_generate(
            args.project,
            templates_root=args.templates_root,
            artifact_workspace=args.artifact_workspace,
            output=args.output,
            pdf_exporter=args.pdf_exporter,
            office_executable=args.office_executable,
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
