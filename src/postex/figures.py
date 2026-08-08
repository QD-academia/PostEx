from __future__ import annotations

from dataclasses import asdict, dataclass

from postex.approvals import ApprovalGate, ApprovalRecord, Proposal
from postex.enums import ApprovalSubject


@dataclass(frozen=True)
class FigureEdit:
    figure_id: str
    operation: str
    panels: tuple[str, ...]
    reason: str
    preserves_labels: bool = True


class FigureEditGate:
    def __init__(self) -> None:
        self.approvals = ApprovalGate(ApprovalSubject.FIGURE_EDIT)

    def propose(self, proposal_id: str, edits: tuple[FigureEdit, ...]) -> Proposal:
        allowed = {"crop", "split", "recompose", "caption-compress"}
        if any(edit.operation not in allowed for edit in edits):
            raise ValueError("Unknown figure edit operation")
        return self.approvals.propose(proposal_id, {"edits": [asdict(edit) for edit in edits]})

    def approve(self, actor: str) -> ApprovalRecord:
        return self.approvals.decide(True, actor)
