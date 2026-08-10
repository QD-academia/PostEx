import tempfile
import unittest
from pathlib import Path

import yaml

from postex.cli import build_parser
from postex.scaffold import create_project_scaffold


class CreateCommandTests(unittest.TestCase):
    def test_parser_accepts_create_shortcut(self) -> None:
        args = build_parser().parse_args(["create", "paper.pdf"])
        self.assertEqual(args.command, "create")
        self.assertEqual(args.template_family, "bioinformatics-pipeline")

    def test_create_scaffold_keeps_all_approval_gates_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "paper.pdf"
            source.write_bytes(b"%PDF-1.4\nfixture")
            project_path = create_project_scaffold(
                source, project_directory=root / "project", project_id="trusted-demo"
            )
            project = yaml.safe_load(project_path.read_text(encoding="utf-8"))
            approvals = yaml.safe_load(
                (project_path.parent / "approval-log.json").read_text(encoding="utf-8")
            )
            self.assertTrue(project["provenance"]["enabled"])
            self.assertTrue(project["palette"]["require_approval"])
            self.assertTrue(project["fusion"]["require_structure_approval"])
            self.assertFalse(project["output"]["release_ready"])
            self.assertEqual(approvals["records"], [])
            self.assertIn("final_release", approvals["required_before_release"])
            self.assertIn("content_deletion", approvals["required_before_render"])


if __name__ == "__main__":
    unittest.main()
