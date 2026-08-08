from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from postex.approvals import ApprovalGate, ApprovalRecord, Proposal, canonical_digest
from postex.brief import PosterBrief
from postex.enums import ApprovalSubject, PosterEmphasis, StructureDirection
from postex.palette import PaletteDNA


@dataclass(frozen=True)
class ContentSignals:
    hero_claim_id: str
    main_visual_id: str | None = None
    figure_count: int = 0
    table_count: int = 0
    methods_complexity: str = "medium"


@dataclass(frozen=True)
class FusionCandidate:
    candidate_id: str
    direction: StructureDirection
    palette_id: str
    brief_digest: str
    hero_claim_id: str
    layout_weights: dict[str, float]
    component_style: dict[str, str]
    rationale: tuple[str, ...]
    recommended: bool = False

    def as_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["direction"] = self.direction.value
        payload["rationale"] = list(self.rationale)
        return payload


class FusionEngine:
    """Create structurally distinct directions from content intent and Palette DNA."""

    _BASE_WEIGHTS = {
        StructureDirection.HERO_RESULT: {
            "hero": 0.42,
            "methods": 0.18,
            "results": 0.28,
            "impact": 0.12,
        },
        StructureDirection.VISUAL_JOURNEY: {
            "hero": 0.20,
            "methods": 0.32,
            "results": 0.34,
            "impact": 0.14,
        },
        StructureDirection.EDITORIAL_STORY: {
            "hero": 0.30,
            "methods": 0.16,
            "results": 0.26,
            "impact": 0.28,
        },
    }

    def propose(
        self,
        brief: PosterBrief,
        palette: PaletteDNA,
        signals: ContentSignals,
    ) -> tuple[FusionCandidate, ...]:
        brief.validate()
        palette.validate()
        brief_digest = canonical_digest(brief.as_payload())
        recommended_direction = self._recommended_direction(brief, signals)
        candidates = []
        for direction in StructureDirection:
            weights = dict(self._BASE_WEIGHTS[direction])
            self._apply_emphasis(weights, brief.emphasis)
            style = self._component_style(direction, palette)
            rationale = self._rationale(direction, brief, palette, signals)
            candidates.append(
                FusionCandidate(
                    candidate_id=f"{palette.palette_id}-{direction.value}",
                    direction=direction,
                    palette_id=palette.palette_id,
                    brief_digest=brief_digest,
                    hero_claim_id=signals.hero_claim_id,
                    layout_weights=weights,
                    component_style=style,
                    rationale=rationale,
                    recommended=direction is recommended_direction,
                )
            )
        return tuple(candidates)

    @staticmethod
    def _recommended_direction(brief: PosterBrief, signals: ContentSignals) -> StructureDirection:
        if brief.emphasis is PosterEmphasis.METHODS or signals.methods_complexity == "high":
            return StructureDirection.VISUAL_JOURNEY
        if brief.emphasis is PosterEmphasis.IMPACT:
            return StructureDirection.EDITORIAL_STORY
        return StructureDirection.HERO_RESULT

    @staticmethod
    def _apply_emphasis(weights: dict[str, float], emphasis: PosterEmphasis) -> None:
        target = {
            PosterEmphasis.METHODS: "methods",
            PosterEmphasis.RESULTS: "results",
            PosterEmphasis.IMPACT: "impact",
        }.get(emphasis)
        if target is None:
            return
        for key in weights:
            weights[key] *= 0.9
        weights[target] += 0.1
        total = sum(weights.values())
        for key in weights:
            weights[key] = round(weights[key] / total, 3)

    @staticmethod
    def _component_style(direction: StructureDirection, palette: PaletteDNA) -> dict[str, str]:
        defaults = {
            StructureDirection.HERO_RESULT: {
                "cards": "anchored",
                "flow": "focused",
                "ornament": "minimal",
            },
            StructureDirection.VISUAL_JOURNEY: {
                "cards": "connected",
                "flow": "directional",
                "ornament": "rhythmic",
            },
            StructureDirection.EDITORIAL_STORY: {
                "cards": "layered",
                "flow": "asymmetric",
                "ornament": "expressive",
            },
        }[direction]
        return {**defaults, **palette.component_style}

    @staticmethod
    def _rationale(
        direction: StructureDirection,
        brief: PosterBrief,
        palette: PaletteDNA,
        signals: ContentSignals,
    ) -> tuple[str, ...]:
        return (
            f"Use {signals.hero_claim_id} as the approved visual anchor.",
            f"Translate the {', '.join(palette.moods) or 'balanced'} palette mood into {direction.value} composition.",
            f"Prioritize {brief.emphasis.value} while preserving every must-keep item.",
            "Keep scientific semantic colors locked unless separately approved.",
        )


class HeroResultGate:
    def __init__(self) -> None:
        self.approvals = ApprovalGate(ApprovalSubject.HERO_RESULT)

    def propose(self, claim_id: str, summary: str, evidence_ids: list[str]) -> Proposal:
        return self.approvals.propose(
            claim_id, {"summary": summary, "evidence_ids": sorted(evidence_ids)}
        )

    def approve(self, actor: str) -> ApprovalRecord:
        return self.approvals.decide(True, actor)


class FusionGate:
    def __init__(self) -> None:
        self.approvals = ApprovalGate(ApprovalSubject.POSTER_STRUCTURE)

    def preview(self, candidate: FusionCandidate) -> Proposal:
        return self.approvals.propose(candidate.candidate_id, candidate.as_payload())

    def approve(self, actor: str) -> ApprovalRecord:
        return self.approvals.decide(True, actor)
