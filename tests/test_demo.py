import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from postex.cli import main
from postex.demo import create_golden_demo


class GoldenDemoTests(unittest.TestCase):
    def test_demo_materializes_editable_and_auditable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "demo"
            result = create_golden_demo(output)
            self.assertFalse(result["api_key_required"])
            for name in (
                "index.html",
                "poster.pptx",
                "poster.png",
                "evidence-report.json",
                "preflight-report.json",
                "demo-manifest.json",
            ):
                self.assertTrue((output / name).is_file(), name)
            manifest = json.loads((output / "demo-manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["network_access"])
            self.assertEqual(
                set(manifest["artifacts"]),
                {
                    "index.html",
                    "poster.pptx",
                    "poster.png",
                    "evidence-report.json",
                    "preflight-report.json",
                },
            )

    def test_demo_refuses_to_overwrite_nonempty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "demo"
            output.mkdir()
            (output / "keep.txt").write_text("user data", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                create_golden_demo(output)

    def test_cli_demo_uses_default_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "demo"
            with mock.patch("sys.argv", ["postex", "demo", "--output", str(output)]):
                self.assertEqual(main(), 0)
            self.assertTrue((output / "poster.pptx").is_file())


if __name__ == "__main__":
    unittest.main()
