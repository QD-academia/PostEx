from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from postex.enums import ApprovalDecision, ApprovalSubject
from postex.errors import ApprovalRequired


def canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Proposal:
    subject: ApprovalSubject
    proposal_id: str
    payload: dict[str, Any]
    digest: str

    @classmethod
    def create(
        cls, subject: ApprovalSubject, proposal_id: str, payload: dict[str, Any]
    ) -> Proposal:
        return cls(subject, proposal_id, payload, canonical_digest(payload))


@dataclass(frozen=True)
class ApprovalRecord:
    subject: ApprovalSubject
    proposal_id: str
    digest: str
    decision: ApprovalDecision
    actor: str
    decided_at: str


class ApprovalGate:
    """Keep only the current proposal and bind decisions to its digest."""

    def __init__(self, subject: ApprovalSubject) -> None:
        self.subject = subject
        self.proposal: Proposal | None = None
        self.record: ApprovalRecord | None = None

    def propose(self, proposal_id: str, payload: dict[str, Any]) -> Proposal:
        self.proposal = Proposal.create(self.subject, proposal_id, payload)
        self.record = None
        return self.proposal

    def decide(self, approved: bool, actor: str) -> ApprovalRecord:
        if self.proposal is None:
            raise ApprovalRequired(f"No {self.subject.value} proposal exists")
        decision = ApprovalDecision.APPROVED if approved else ApprovalDecision.REJECTED
        self.record = ApprovalRecord(
            subject=self.subject,
            proposal_id=self.proposal.proposal_id,
            digest=self.proposal.digest,
            decision=decision,
            actor=actor,
            decided_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.record

    def revoke(self, actor: str) -> ApprovalRecord:
        self.require_approved()
        assert self.proposal is not None
        self.record = ApprovalRecord(
            subject=self.subject,
            proposal_id=self.proposal.proposal_id,
            digest=self.proposal.digest,
            decision=ApprovalDecision.REVOKED,
            actor=actor,
            decided_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.record

    def require_approved(self) -> ApprovalRecord:
        if (
            self.proposal is None
            or self.record is None
            or self.record.decision is not ApprovalDecision.APPROVED
            or self.record.digest != self.proposal.digest
        ):
            raise ApprovalRequired(f"Current {self.subject.value} proposal is not approved")
        return self.record
