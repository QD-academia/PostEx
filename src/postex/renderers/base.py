from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from postex.models import PosterModel


@dataclass(frozen=True)
class RenderResult:
    artifact: Path
    renderer: str
    warnings: tuple[str, ...] = ()


class PosterRenderer(Protocol):
    def render_pptx(self, poster: PosterModel, template: Path, output: Path) -> RenderResult: ...


class PdfExporter(Protocol):
    def export_pdf(self, pptx: Path, output: Path) -> RenderResult: ...
