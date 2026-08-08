#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def normalize(value: str) -> str:
    return "".join(value.lower().replace(",", "").split())


def main() -> int:
    errors: list[str] = []
    results: list[dict] = []
    dois: set[str] = set()
    real_papers = 0

    for path in sorted(CASES.glob("*.json")):
        case = load(path)
        required = (
            "case_id",
            "license",
            "research_type",
            "facts",
            "expected_sections",
            "forbidden",
        )
        missing = [key for key in required if key not in case]
        if missing:
            errors.append(f"{path.name}: missing {missing}")
            continue
        if not case.get("fictional", False):
            real_papers += 1
            doi = str(case.get("doi", ""))
            if not doi or doi in dois:
                errors.append(f"{path.name}: missing or duplicate DOI")
            dois.add(doi)
            if not case.get("source_url") or not case.get("human_review"):
                errors.append(f"{path.name}: missing source URL or human review")

        claim_ids = [str(item["claim_id"]) for item in case["facts"]]
        if len(claim_ids) != len(set(claim_ids)):
            errors.append(f"{path.name}: duplicate claim IDs")

        candidate_status = "fixture-only"
        candidate_value = case.get("candidate")
        if candidate_value:
            candidate_path = (path.parent / str(candidate_value)).resolve()
            candidate = load(candidate_path)
            combined = normalize(
                "\n".join(str(block.get("text", "")) for block in candidate["blocks"])
            )
            absent = [
                item["claim_id"]
                for item in case["facts"]
                if normalize(str(item["required_text"])) not in combined
            ]
            roles = {str(block["role"]) for block in candidate["blocks"]}
            missing_roles = set(case["expected_sections"]) - roles
            forbidden = [
                phrase for phrase in case["forbidden"] if normalize(str(phrase)) in combined
            ]
            if absent or missing_roles or forbidden:
                errors.append(
                    f"{path.name}: absent facts={absent}, "
                    f"missing roles={sorted(missing_roles)}, forbidden={forbidden}"
                )
                candidate_status = "failed"
            else:
                candidate_status = "passed"

        results.append(
            {
                "case_id": case["case_id"],
                "research_type": case["research_type"],
                "license": case["license"],
                "candidate_status": candidate_status,
                "human_review_status": case.get("human_review", {}).get(
                    "visual_status", "not-applicable"
                ),
            }
        )

    if not 5 <= real_papers <= 10:
        errors.append(f"Expected 5-10 real-paper cases, found {real_papers}")

    report = {
        "schema_version": "0.1",
        "passed": not errors,
        "real_paper_cases": real_papers,
        "total_cases": len(results),
        "errors": errors,
        "results": results,
    }
    target = ROOT / "evals" / "report.json"
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"passed={report['passed']} real_papers={real_papers} "
        f"total_cases={len(results)} errors={len(errors)}"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
