from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from postex.enums import ContentMode, PosterEmphasis


@dataclass(frozen=True)
class PosterBrief:
    """User-owned intent gathered before content planning or visual design."""

    audience: tuple[str, ...]
    takeaway: str
    visual_tone: tuple[str, ...]
    palette_source: str
    logo_treatment: str
    emphasis: PosterEmphasis = PosterEmphasis.BALANCED
    conference: str | None = None
    must_keep: tuple[str, ...] = ()
    figure_edit_permission: str = "ask"
    content_mode: ContentMode = ContentMode.TRACEABLE
    allow_network_palette_sources: bool = False
    allow_cloud_manuscript_processing: bool = False

    def validate(self) -> None:
        if not self.audience:
            raise ValueError("Poster brief needs at least one audience")
        if not self.takeaway.strip():
            raise ValueError("Poster brief needs a one-sentence takeaway")
        if not self.visual_tone:
            raise ValueError("Poster brief needs at least one visual tone")
        if self.logo_treatment not in {"none", "placeholder", "provided"}:
            raise ValueError("logo_treatment must be none, placeholder, or provided")
        if self.figure_edit_permission not in {"never", "ask", "crop", "split", "recompose"}:
            raise ValueError("Unknown figure_edit_permission")

    def as_payload(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["emphasis"] = self.emphasis.value
        payload["content_mode"] = self.content_mode.value
        return payload


def poster_brief_from_mapping(data: dict[str, Any]) -> PosterBrief:
    brief = PosterBrief(
        audience=tuple(str(item) for item in data.get("audience", ())),
        takeaway=str(data.get("takeaway", "")),
        visual_tone=tuple(str(item) for item in data.get("visual_tone", ())),
        palette_source=str(data.get("palette_source", "default")),
        logo_treatment=str(data.get("logo_treatment", "none")),
        emphasis=PosterEmphasis(data.get("emphasis", "balanced")),
        conference=str(data["conference"]) if data.get("conference") else None,
        must_keep=tuple(str(item) for item in data.get("must_keep", ())),
        figure_edit_permission=str(data.get("figure_edit_permission", "ask")),
        content_mode=ContentMode(data.get("content_mode", "traceable")),
        allow_network_palette_sources=bool(data.get("allow_network_palette_sources", False)),
        allow_cloud_manuscript_processing=bool(
            data.get("allow_cloud_manuscript_processing", False)
        ),
    )
    brief.validate()
    return brief


BRIEF_QUESTIONS = (
    "Who will view the poster and at what conference or setting?",
    "What single sentence should a visitor remember?",
    "Should methods, results, impact, or a balanced story dominate?",
    "Which figures, tables, numbers, or claims must remain?",
    "May PostEx crop, split, or recompose composite figures after approval?",
    "Should logos be omitted, retained as labeled placeholders, or supplied now?",
    "What image, theme, brand, colors, or mood should inspire the palette?",
    "May PostEx use network palette sources or cloud manuscript processing?",
)
