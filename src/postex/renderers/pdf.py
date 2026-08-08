from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from postex.errors import ConfigurationError
from postex.renderers.base import RenderResult


class PowerPointPdfExporter:
    name = "powerpoint"

    def export_pdf(self, pptx: Path, output: Path) -> RenderResult:
        if sys.platform != "darwin" or shutil.which("osascript") is None:
            raise ConfigurationError("PowerPoint PDF export is available only on macOS")
        pptx = pptx.resolve()
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        script = (
            'tell application "Microsoft PowerPoint"\n'
            f'open POSIX file "{pptx}"\n'
            "set activePresentation to active presentation\n"
            f'save activePresentation in POSIX file "{output}" as save as PDF\n'
            "close activePresentation saving no\n"
            "end tell"
        )
        completed = subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0 or not output.is_file():
            raise RuntimeError(
                "PowerPoint PDF export failed: " + (completed.stderr or completed.stdout).strip()
            )
        return RenderResult(output, self.name)


class LibreOfficePdfExporter:
    name = "libreoffice"

    def __init__(self, executable: str | Path | None = None) -> None:
        self.executable = str(
            executable or shutil.which("soffice") or shutil.which("libreoffice") or ""
        )

    def export_pdf(self, pptx: Path, output: Path) -> RenderResult:
        if not self.executable:
            raise ConfigurationError("LibreOffice was not found")
        pptx = pptx.resolve()
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="postex-pdf-") as temporary:
            profile = (Path(temporary) / "profile").resolve()
            profile.mkdir()
            completed = subprocess.run(
                [
                    self.executable,
                    "--headless",
                    f"-env:UserInstallation={profile.as_uri()}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    temporary,
                    str(pptx),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            converted = Path(temporary) / f"{pptx.stem}.pdf"
            if completed.returncode != 0 or not converted.is_file():
                raise RuntimeError(
                    "LibreOffice PDF export failed: "
                    + (completed.stderr or completed.stdout).strip()
                )
            shutil.move(converted, output)
        return RenderResult(
            output,
            self.name,
            ("LibreOffice fallback may produce small typography differences",),
        )
