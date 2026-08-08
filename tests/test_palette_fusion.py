import json
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from postex.approvals import canonical_digest
from postex.brief import poster_brief_from_mapping
from postex.enums import WorkflowStage
from postex.errors import LockViolation
from postex.figures import FigureEdit
from postex.fusion import ContentSignals, FusionEngine
from postex.locks import DesignLock, LockRegistry
from postex.palette import PaletteStudio, palette_dna_from_mapping, render_palette_studio_html
from postex.rationale import build_design_rationale, render_design_rationale_html
from postex.workflow import PaletteFusionWorkflow

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "palette-fusion"


class PaletteFusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.brief_data = yaml.safe_load(
            (EXAMPLE / "poster-brief.yaml").read_text(encoding="utf-8")
        )
        self.palette_data = yaml.safe_load(
            (EXAMPLE / "palette-dna.yaml").read_text(encoding="utf-8")
        )
        self.brief = poster_brief_from_mapping(self.brief_data)
        self.palette = palette_dna_from_mapping(self.palette_data)

    def test_v02_example_contracts_validate(self) -> None:
        for filename, schema_name in (
            ("poster-brief.yaml", "poster-brief.schema.json"),
            ("palette-dna.yaml", "palette-dna.schema.json"),
            ("design-locks.json", "design-locks.schema.json"),
        ):
            path = EXAMPLE / filename
            data = (
                json.loads(path.read_text(encoding="utf-8"))
                if path.suffix == ".json"
                else yaml.safe_load(path.read_text(encoding="utf-8"))
            )
            schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            self.assertEqual(list(Draft202012Validator(schema).iter_errors(data)), [])

    def test_fusion_engine_returns_three_distinct_directions(self) -> None:
        candidates = FusionEngine().propose(
            self.brief,
            self.palette,
            ContentSignals("claim:external-validation", figure_count=5, methods_complexity="high"),
        )
        self.assertEqual(len(candidates), 3)
        self.assertEqual(len({item.direction for item in candidates}), 3)
        self.assertEqual(sum(item.recommended for item in candidates), 1)
        self.assertTrue(
            all(
                item.brief_digest == canonical_digest(self.brief.as_payload())
                for item in candidates
            )
        )

        schema = json.loads(
            (ROOT / "schemas" / "fusion-proposal.schema.json").read_text(encoding="utf-8")
        )
        payload = {
            "schema_version": "0.2",
            "candidates": [item.as_payload() for item in candidates],
        }
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(payload)), [])

    def test_palette_studio_returns_three_expression_levels(self) -> None:
        candidates = PaletteStudio().propose(self.palette)
        self.assertEqual(
            [item.variant for item in candidates],
            ["academic-safe", "balanced-fusion", "visual-signature"],
        )
        self.assertEqual(
            len({tuple(color.hex for color in item.palette.colors) for item in candidates}), 3
        )
        self.assertTrue(
            all(
                abs(sum(color.ratio for color in item.palette.colors) - 1.0) < 0.001
                for item in candidates
            )
        )
        payload = {
            "schema_version": "0.2",
            "candidates": [item.as_payload() for item in candidates],
        }
        studio_schema = json.loads(
            (ROOT / "schemas" / "palette-studio.schema.json").read_text(encoding="utf-8")
        )
        dna_schema = json.loads(
            (ROOT / "schemas" / "palette-dna.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(Draft202012Validator(studio_schema).iter_errors(payload)), [])
        for item in payload["candidates"]:
            self.assertEqual(
                list(Draft202012Validator(dna_schema).iter_errors(item["palette"])), []
            )
        with tempfile.TemporaryDirectory() as tmp:
            preview = render_palette_studio_html(candidates, Path(tmp) / "palette-studio.html")
            text = preview.read_text(encoding="utf-8")
            self.assertIn("Academic Safe", text)
            self.assertIn("Balanced Fusion", text)
            self.assertIn("Visual Signature", text)

    def test_design_rationale_is_self_contained_html(self) -> None:
        candidate = FusionEngine().propose(self.brief, self.palette, ContentSignals("claim:hero"))[
            0
        ]
        report = build_design_rationale(self.brief, self.palette, candidate)
        with tempfile.TemporaryDirectory() as tmp:
            path = render_design_rationale_html(report, Path(tmp) / "rationale.html")
            text = path.read_text(encoding="utf-8")
            self.assertIn("Palette DNA", text)
            self.assertIn("Scientific guardrails", text)
            self.assertNotIn("<script", text.lower())

    def test_design_locks_block_mutation(self) -> None:
        registry = LockRegistry((DesignLock("claim:hero", "copy", "sha256:" + "0" * 64, "owner"),))
        with self.assertRaises(LockViolation):
            registry.require_mutable(("claim:hero", "figure:2"))
        registry.require_mutable(("figure:2",))

    def test_v02_approval_sequence_reaches_render_gate(self) -> None:
        workflow = PaletteFusionWorkflow()
        workflow.accept_brief(self.brief)
        workflow.propose_hero("claim:hero", "Validated result", ["evidence:1"])
        workflow.approve_hero("owner")
        workflow.propose_deletions("delete:v1", ["source:discussion:4"])
        workflow.approve_deletions("owner")
        workflow.propose_figure_edits(
            "figures:v1", (FigureEdit("figure:2", "split", ("A", "C"), "Preserve relevant panels"),)
        )
        workflow.approve_figure_edits("owner")
        workflow.palette.preview(self.palette.palette_id, self.palette)
        workflow.approve_palette("owner")
        candidate = FusionEngine().propose(self.brief, self.palette, ContentSignals("claim:hero"))[
            0
        ]
        workflow.preview_structure(candidate)
        workflow.approve_structure("owner")
        self.assertIs(workflow.stage, WorkflowStage.READY_TO_RENDER)


if __name__ == "__main__":
    unittest.main()
