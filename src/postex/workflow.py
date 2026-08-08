from __future__ import annotations

from postex.approvals import ApprovalGate
from postex.brief import PosterBrief
from postex.enums import ApprovalSubject, WorkflowStage
from postex.errors import InvalidTransition
from postex.figures import FigureEdit, FigureEditGate
from postex.fusion import FusionCandidate, FusionGate, HeroResultGate
from postex.palette import PaletteGate
from postex.privacy import PrivacyGate


class PosterWorkflow:
    """Minimal orchestration contract for the three mandatory approvals."""

    def __init__(self) -> None:
        self.stage = WorkflowStage.LOCAL_READY
        self.privacy = PrivacyGate()
        self.deletions = ApprovalGate(ApprovalSubject.CONTENT_DELETION)
        self.palette = PaletteGate()

    def request_cloud(self, provider: str, label: str, content: dict[str, str]) -> None:
        self._require(WorkflowStage.LOCAL_READY)
        self.privacy.disclose(provider, label, content)
        self.stage = WorkflowStage.AWAITING_UPLOAD_APPROVAL

    def approve_cloud(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_UPLOAD_APPROVAL)
        self.privacy.approve(actor)
        self.stage = WorkflowStage.CLOUD_READY

    def propose_deletions(self, proposal_id: str, source_ids: list[str]) -> None:
        self._require(WorkflowStage.CLOUD_READY)
        self.deletions.propose(proposal_id, {"source_ids": sorted(source_ids)})
        self.stage = WorkflowStage.AWAITING_DELETION_APPROVAL

    def approve_deletions(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_DELETION_APPROVAL)
        self.deletions.decide(True, actor)
        self.stage = WorkflowStage.AWAITING_PALETTE_APPROVAL

    def approve_palette(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_PALETTE_APPROVAL)
        self.palette.approve(actor)
        self.stage = WorkflowStage.READY_TO_RENDER

    def mark_rendered(self) -> None:
        self._require(WorkflowStage.READY_TO_RENDER)
        self.stage = WorkflowStage.RENDERED

    def mark_preflight_passed(self) -> None:
        self._require(WorkflowStage.RENDERED)
        self.stage = WorkflowStage.PREFLIGHT_PASSED

    def _require(self, expected: WorkflowStage) -> None:
        if self.stage is not expected:
            raise InvalidTransition(f"Expected {expected.value}, got {self.stage.value}")


class PaletteFusionWorkflow:
    """v0.2 design workflow; keep the v0.1 workflow available for compatibility."""

    def __init__(self) -> None:
        self.stage = WorkflowStage.LOCAL_READY
        self.brief: PosterBrief | None = None
        self.hero = HeroResultGate()
        self.deletions = ApprovalGate(ApprovalSubject.CONTENT_DELETION)
        self.figures = FigureEditGate()
        self.palette = PaletteGate()
        self.fusion = FusionGate()

    def accept_brief(self, brief: PosterBrief) -> None:
        self._require(WorkflowStage.LOCAL_READY)
        brief.validate()
        self.brief = brief
        self.stage = WorkflowStage.BRIEF_READY

    def propose_hero(self, claim_id: str, summary: str, evidence_ids: list[str]) -> None:
        self._require(WorkflowStage.BRIEF_READY)
        self.hero.propose(claim_id, summary, evidence_ids)
        self.stage = WorkflowStage.AWAITING_HERO_APPROVAL

    def approve_hero(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_HERO_APPROVAL)
        self.hero.approve(actor)
        self.stage = WorkflowStage.AWAITING_DELETION_APPROVAL

    def propose_deletions(self, proposal_id: str, source_ids: list[str]) -> None:
        self._require(WorkflowStage.AWAITING_DELETION_APPROVAL)
        self.deletions.propose(proposal_id, {"source_ids": sorted(source_ids)})

    def approve_deletions(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_DELETION_APPROVAL)
        self.deletions.decide(True, actor)
        self.stage = WorkflowStage.AWAITING_FIGURE_APPROVAL

    def propose_figure_edits(self, proposal_id: str, edits: tuple[FigureEdit, ...]) -> None:
        self._require(WorkflowStage.AWAITING_FIGURE_APPROVAL)
        self.figures.propose(proposal_id, edits)

    def approve_figure_edits(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_FIGURE_APPROVAL)
        self.figures.approve(actor)
        self.stage = WorkflowStage.AWAITING_PALETTE_APPROVAL

    def approve_palette(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_PALETTE_APPROVAL)
        self.palette.approve(actor)
        self.stage = WorkflowStage.AWAITING_STRUCTURE_APPROVAL

    def preview_structure(self, candidate: FusionCandidate) -> None:
        self._require(WorkflowStage.AWAITING_STRUCTURE_APPROVAL)
        self.fusion.preview(candidate)

    def approve_structure(self, actor: str) -> None:
        self._require(WorkflowStage.AWAITING_STRUCTURE_APPROVAL)
        self.fusion.approve(actor)
        self.stage = WorkflowStage.READY_TO_RENDER

    def _require(self, expected: WorkflowStage) -> None:
        if self.stage is not expected:
            raise InvalidTransition(f"Expected {expected.value}, got {self.stage.value}")
