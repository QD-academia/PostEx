from __future__ import annotations

from dataclasses import dataclass

from postex.approvals import ApprovalGate, ApprovalRecord, Proposal
from postex.enums import ApprovalSubject


@dataclass(frozen=True)
class DeletionItem:
    source_id: str
    reason: str
    impact: str


class DeletionGate:
    def __init__(self) -> None:
        self.approvals = ApprovalGate(ApprovalSubject.CONTENT_DELETION)

    def propose(self, proposal_id: str, items: tuple[DeletionItem, ...]) -> Proposal:
        return self.approvals.propose(
            proposal_id,
            {
                "items": [
                    {"source_id": item.source_id, "reason": item.reason, "impact": item.impact}
                    for item in items
                ]
            },
        )

    def approve(self, actor: str) -> ApprovalRecord:
        return self.approvals.decide(True, actor)

    def require_application_approval(self) -> ApprovalRecord:
        return self.approvals.require_approved()
