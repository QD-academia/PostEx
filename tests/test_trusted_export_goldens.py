import json
import unittest
import zipfile
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from PIL import Image
from pypdf import PdfReader

from postex.enums import PosterSize
from postex.preflight import run_artifact_preflight
from postex.provenance import PROVENANCE_OBJECT_NAME, sha256_file

ROOT = Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "evals" / "goldens" / "trusted-export"
FAMILIES = ("bioinformatics-pipeline", "observational-cohort", "visual-results")
SIZES = ("a0-landscape", "a1-landscape", "36x48-landscape")


def _golden(family: str, size: str) -> tuple[Path, dict, dict, dict]:
    root = GOLDENS / family / size
    manifest = json.loads((root / "postex-manifest.json").read_text(encoding="utf-8"))
    preflight = json.loads((root / "preflight-report.json").read_text(encoding="utf-8"))
    render_spec = json.loads((root / "render-spec.json").read_text(encoding="utf-8"))
    return root, manifest, preflight, render_spec


class TrustedExportGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_schema = json.loads(
            (ROOT / "schemas" / "postex-manifest.schema.json").read_text(encoding="utf-8")
        )
        cls.preflight_schema = json.loads(
            (ROOT / "schemas" / "preflight-report.schema.json").read_text(encoding="utf-8")
        )
        cls.project_schema = json.loads(
            (ROOT / "schemas" / "project.schema.json").read_text(encoding="utf-8")
        )

    def test_nine_goldens_are_complete_and_release_ready(self) -> None:
        for family in FAMILIES:
            for size in SIZES:
                with self.subTest(family=family, size=size):
                    root, manifest, preflight, _ = _golden(family, size)
                    Draft202012Validator(self.manifest_schema).validate(manifest)
                    Draft202012Validator(self.preflight_schema).validate(preflight)
                    project = yaml.safe_load(
                        (root / "golden-project.yaml").read_text(encoding="utf-8")
                    )
                    Draft202012Validator(self.project_schema).validate(project)
                    self.assertTrue(preflight["passed"])
                    self.assertTrue(preflight["release_ready"])
                    self.assertEqual(preflight["output_status"], "release-ready")
                    self.assertFalse(
                        [item for item in preflight["findings"] if not item["passed"]]
                    )
                    self.assertEqual(manifest["template"]["family"], family)
                    self.assertEqual(manifest["template"]["size"], size)
                    self.assertNotIn("postex-manifest.json", manifest["outputs"])
                    for output in manifest["outputs"].values():
                        path = root / output["path"]
                        self.assertTrue(path.is_file())
                        self.assertEqual(sha256_file(path), output["sha256"])

    def test_watermark_survives_all_three_formats(self) -> None:
        root, manifest, _, _ = _golden("bioinformatics-pipeline", "a0-landscape")
        mark = manifest["provenance"]["mark_text"]
        pptx = next(root.glob("*.pptx"))
        pdf = next(root.glob("*.pdf"))
        png = next(root.glob("*.png"))
        with zipfile.ZipFile(pptx) as archive:
            slide = archive.read("ppt/slides/slide1.xml").decode("utf-8")
            core = archive.read("docProps/core.xml").decode("utf-8")
        self.assertIn(PROVENANCE_OBJECT_NAME, slide)
        self.assertIn(mark, slide)
        self.assertIn(manifest["source_id"], core)
        reader = PdfReader(pdf)
        self.assertIn(mark, "\n".join(page.extract_text() or "" for page in reader.pages))
        self.assertIn(manifest["source_id"], str(reader.metadata.get("/Subject", "")))
        with Image.open(png) as image:
            self.assertEqual(image.info["PostExSourceId"], manifest["source_id"])
            self.assertEqual(image.info["PostExProvenanceMark"], "present")

    def test_scientific_source_assets_remain_hash_locked(self) -> None:
        _, manifest, _, _ = _golden("bioinformatics-pipeline", "a0-landscape")
        fixture = ROOT / "examples" / "aurora-synthetic"
        locked = [item for item in manifest["assets"] if item.get("pixel_locked")]
        self.assertEqual(len(locked), 4)
        for item in locked:
            self.assertEqual(sha256_file(fixture / item["path"]), item["sha256"])

    def test_warning_is_draft_and_release_request_turns_missing_approval_into_error(self) -> None:
        root, manifest, _, render_spec = _golden(
            "bioinformatics-pipeline", "a0-landscape"
        )
        render_spec = json.loads(json.dumps(render_spec))
        fixture = ROOT / "examples" / "aurora-synthetic"
        for figure in render_spec["content"]["figures"]:
            figure["path"] = str(fixture / figure["path"])
        paths = {name: root / item["path"] for name, item in manifest["outputs"].items()}
        common = {
            "project_id": manifest["project_id"],
            "poster_size": PosterSize.A0_LANDSCAPE,
            "expected_inches": (
                manifest["template"]["width_in"],
                manifest["template"]["height_in"],
            ),
            "pptx": paths["pptx"],
            "pdf": paths["pdf"],
            "png": paths["png"],
            "layout": paths["layout"],
            "evidence_coverage": 1.0,
            "approvals_current": True,
            "branding": render_spec["branding"],
            "provenance": manifest["provenance"],
            "manifest": root / "postex-manifest.json",
            "render_spec": render_spec,
            "expected_hashes": {
                name: manifest["outputs"][name]
                for name in ("pptx", "pdf", "png", "layout")
            },
            "final_release_approved": False,
        }
        draft = run_artifact_preflight(**common, release_requested=False)
        self.assertTrue(draft["passed"])
        self.assertFalse(draft["release_ready"])
        self.assertEqual(draft["output_status"], "draft")
        blocked = run_artifact_preflight(**common, release_requested=True)
        self.assertFalse(blocked["passed"])
        self.assertFalse(blocked["release_ready"])

    def test_template_assets_have_no_placeholders(self) -> None:
        for family in FAMILIES:
            metadata = yaml.safe_load(
                (ROOT / "assets" / "templates" / family / "template.yaml").read_text(
                    encoding="utf-8"
                )
            )
            for size in SIZES:
                root = ROOT / "assets" / "templates" / family / size
                with self.subTest(family=family, size=size):
                    self.assertFalse((root / "PLACEHOLDER.md").exists())
                    for filename in (
                        "template.pptx",
                        "template.png",
                        "template-spec.json",
                        "template.layout.json",
                        "template.inspect.ndjson",
                    ):
                        self.assertTrue((root / filename).is_file())
                    self.assertEqual(
                        sha256_file(root / "template.pptx"),
                        metadata["variants"][size]["sha256"],
                    )


if __name__ == "__main__":
    unittest.main()
