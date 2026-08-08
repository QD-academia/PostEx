from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from postex.errors import ConfigurationError


@dataclass(frozen=True)
class ExtractedPage:
    page: int
    text: str
    width_pt: float
    height_pt: float


@dataclass(frozen=True)
class ExtractedDocument:
    source: Path
    sha256: str
    pages: tuple[ExtractedPage, ...]
    metadata: dict[str, Any]

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source),
            "sha256": self.sha256,
            "metadata": self.metadata,
            "pages": [asdict(page) for page in self.pages],
        }


class PdfExtractor:
    """Local-only PDF text and page-geometry extraction."""

    def extract(self, source: str | Path) -> ExtractedDocument:
        path = Path(source).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()

        try:
            import fitz
        except ImportError:
            return self._extract_with_pypdf(path, digest)

        document = fitz.open(path)
        pages = tuple(
            ExtractedPage(
                page=index + 1,
                text=page.get_text("text").strip(),
                width_pt=float(page.rect.width),
                height_pt=float(page.rect.height),
            )
            for index, page in enumerate(document)
        )
        metadata = {
            key: value
            for key, value in (document.metadata or {}).items()
            if value not in (None, "")
        }
        document.close()
        return ExtractedDocument(path, digest, pages, metadata)

    @staticmethod
    def _extract_with_pypdf(path: Path, digest: str) -> ExtractedDocument:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ConfigurationError(
                "PDF extraction requires PyMuPDF or pypdf; install PostEx with the 'render' extra"
            ) from exc

        reader = PdfReader(path)
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            box = page.mediabox
            pages.append(
                ExtractedPage(
                    page=index,
                    text=(page.extract_text() or "").strip(),
                    width_pt=float(box.width),
                    height_pt=float(box.height),
                )
            )
        metadata = {
            str(key).lstrip("/"): str(value)
            for key, value in (reader.metadata or {}).items()
            if value not in (None, "")
        }
        return ExtractedDocument(path, digest, tuple(pages), metadata)
