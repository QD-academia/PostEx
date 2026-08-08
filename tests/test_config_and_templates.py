import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from postex.config import load_mapping, load_project
from postex.enums import Language, PosterSize, ResearchType
from postex.templates import TemplateRegistry

ROOT = Path(__file__).resolve().parents[1]


class ConfigAndTemplateTests(unittest.TestCase):
    def test_bilingual_project_loads(self) -> None:
        project = load_project(ROOT / "examples" / "bioinformatics-project.yaml")
        self.assertIs(project.research_type, ResearchType.BIOINFORMATICS)
        self.assertIs(project.output_language, Language.CHINESE_SIMPLIFIED)
        self.assertEqual(project.branding["logo_mode"], "placeholder")
        self.assertEqual(project.branding["placeholders"][0]["role"], "institution")

    def test_no_logo_mode_loads(self) -> None:
        project = load_project(ROOT / "examples" / "observational-project.yaml")
        self.assertEqual(project.branding, {"logo_mode": "none"})

    def test_provided_logo_requires_asset_metadata(self) -> None:
        schema = json.loads((ROOT / "schemas" / "project.schema.json").read_text(encoding="utf-8"))
        project = load_mapping(ROOT / "examples" / "observational-project.yaml")
        project["branding"] = {
            "logo_mode": "provided",
            "logos": [
                {
                    "id": "institution-logo",
                    "role": "institution",
                    "path": "assets/branding/institution.svg",
                    "placement": "header-left",
                    "alt_text": "Institution logo",
                    "license": "Provided by project owner",
                }
            ],
        }
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(project)), [])

        project["branding"] = {"logo_mode": "provided"}
        self.assertTrue(list(validator.iter_errors(project)))

    def test_all_families_have_all_dimensions(self) -> None:
        registry = TemplateRegistry(ROOT / "assets" / "templates")
        self.assertEqual(
            registry.families(),
            ("bioinformatics-pipeline", "observational-cohort", "visual-results"),
        )
        expected = {
            PosterSize.A0_LANDSCAPE: (46.811, 33.110),
            PosterSize.A1_LANDSCAPE: (33.110, 23.386),
            PosterSize.INCH_36X48_LANDSCAPE: (48.0, 36.0),
        }
        for family in registry.families():
            for size, dimensions in expected.items():
                variant = registry.resolve(family, size)
                self.assertEqual((variant.width_in, variant.height_in), dimensions)
                if family == "bioinformatics-pipeline":
                    self.assertTrue(variant.asset.is_file())
                    self.assertTrue(variant.layout_spec and variant.layout_spec.is_file())
                    self.assertIsNotNone(variant.sha256)


if __name__ == "__main__":
    unittest.main()
