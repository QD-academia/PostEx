from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from postex.errors import ConfigurationError
from postex.models import PosterModel
from postex.renderers.base import RenderResult


class PptxRenderer:
    """Render an official PostEx layout through the editable Artifact Tool backend."""

    name = "artifact-tool"

    def __init__(
        self,
        *,
        node: str | Path | None = None,
        workspace: str | Path | None = None,
    ) -> None:
        self.node = str(node or os.environ.get("POSTEX_NODE") or shutil.which("node") or "")
        configured_workspace = workspace or os.environ.get("POSTEX_ARTIFACT_WORKSPACE")
        self.workspace = Path(configured_workspace).resolve() if configured_workspace else None

    def render_pptx(self, poster: PosterModel, template: Path, output: Path) -> RenderResult:
        if not template.is_file():
            raise FileNotFoundError(template)
        spec_value = poster.metadata.get("render_spec")
        if not spec_value:
            raise ConfigurationError("Poster metadata must include render_spec")
        spec = Path(str(spec_value)).resolve()
        if not spec.is_file():
            raise FileNotFoundError(spec)
        if not self.node:
            raise ConfigurationError("Node.js was not found; set POSTEX_NODE")
        if self.workspace is None or not (self.workspace / "node_modules").exists():
            raise ConfigurationError(
                "Artifact Tool workspace was not found; set POSTEX_ARTIFACT_WORKSPACE "
                "to a workspace initialized by setup_artifact_tool_workspace.mjs"
            )

        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        source_runner = Path(__file__).with_name("artifact_renderer.mjs")
        runner = self.workspace / "postex-artifact-renderer.mjs"
        shutil.copy2(source_runner, runner)
        completed = subprocess.run(
            [self.node, str(runner), "--spec", str(spec), "--output", str(output)],
            cwd=self.workspace,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"Artifact Tool rendering failed: {detail}")
        if not output.is_file():
            raise RuntimeError(f"Renderer did not create {output}")
        return RenderResult(output, self.name)
