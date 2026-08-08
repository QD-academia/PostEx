import unittest
from pathlib import Path

from postex.generation import _portable_render_spec


class PortableGenerationReportTests(unittest.TestCase):
    def test_absolute_asset_paths_are_removed(self) -> None:
        repository = Path("/workspace/postex")
        project = repository / "examples" / "fixture"
        spec = {
            "template": {
                "asset": str(repository / "assets" / "templates" / "family" / "template.pptx")
            },
            "branding": {"logos": [{"path": str(project / "assets" / "logo.svg")}]},
            "content": {
                "figures": [{"path": str(project / "assets" / "figures" / "figure.svg")}]
            },
        }

        portable = _portable_render_spec(
            spec, project_base=project, repository_root=repository
        )

        self.assertEqual(
            portable["template"]["asset"],
            "assets/templates/family/template.pptx",
        )
        self.assertEqual(portable["branding"]["logos"][0]["path"], "assets/logo.svg")
        self.assertEqual(
            portable["content"]["figures"][0]["path"],
            "assets/figures/figure.svg",
        )
        self.assertTrue(str(spec["template"]["asset"]).startswith("/workspace"))


if __name__ == "__main__":
    unittest.main()
