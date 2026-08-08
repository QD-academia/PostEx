from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from postex.enums import ContentMode, Language, PosterSize, ResearchType


@dataclass(frozen=True)
class SourceLocator:
    source_id: str
    kind: str
    page: int | None = None
    section: str | None = None
    figure: str | None = None
    table: str | None = None
    json_pointer: str | None = None


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    claim_id: str
    locator: SourceLocator
    relation: str
    excerpt_hash: str | None = None


@dataclass(frozen=True)
class PosterBlock:
    block_id: str
    role: str
    text: str
    evidence_ids: tuple[str, ...] = ()
    synthesis: bool = False


@dataclass(frozen=True)
class PosterModel:
    project_id: str
    title: str
    language: Language
    blocks: tuple[PosterBlock, ...]
    template_family: str
    size: PosterSize
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectConfig:
    schema_version: str
    project_id: str
    title: str
    research_type: ResearchType
    input_language: Language
    output_language: Language
    content_mode: ContentMode
    template_family: str
    poster_size: PosterSize
    provider: str
    model: str
    networking: bool = False
    branding: dict[str, Any] = field(default_factory=lambda: {"logo_mode": "none"})
    source: dict[str, Any] = field(default_factory=dict)
    poster_brief: dict[str, Any] = field(default_factory=dict)
    palette: dict[str, Any] = field(default_factory=dict)
    fusion: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
