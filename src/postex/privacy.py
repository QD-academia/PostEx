from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from postex.approvals import ApprovalGate, ApprovalRecord, canonical_digest
from postex.enums import ApprovalSubject

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


@dataclass(frozen=True)
class CloudDisclosure:
    provider: str
    document_label: str
    fields: tuple[str, ...]
    excluded: tuple[str, ...]
    estimated_text_length: int
    content_digest: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "document_label": self.document_label,
            "fields": list(self.fields),
            "excluded": list(self.excluded),
            "estimated_text_length": self.estimated_text_length,
            "content_digest": self.content_digest,
        }


@dataclass(frozen=True)
class ApprovedCloudPayload:
    provider: str
    content: dict[str, str]
    disclosure_digest: str


class PrivacyGate:
    def __init__(self) -> None:
        self.approvals = ApprovalGate(ApprovalSubject.CLOUD_UPLOAD)

    @staticmethod
    def redact(text: str) -> str:
        return EMAIL.sub("[redacted-email]", text)

    def disclose(
        self, provider: str, document_label: str, content: dict[str, str]
    ) -> CloudDisclosure:
        redacted = {name: self.redact(value) for name, value in content.items()}
        disclosure = CloudDisclosure(
            provider=provider,
            document_label=document_label,
            fields=tuple(sorted(redacted)),
            excluded=("author_email_addresses", "embedded_file_metadata", "raw_supplements"),
            estimated_text_length=sum(len(value) for value in redacted.values()),
            content_digest=canonical_digest(redacted),
        )
        self.approvals.propose(document_label, disclosure.as_payload())
        return disclosure

    def approve(self, actor: str) -> ApprovalRecord:
        return self.approvals.decide(True, actor)

    def build_payload(self, provider: str, content: dict[str, str]) -> ApprovedCloudPayload:
        approval = self.approvals.require_approved()
        proposal = self.approvals.proposal
        assert proposal is not None
        if proposal.payload["provider"] != provider:
            raise ValueError("Provider differs from the approved disclosure")
        redacted = {name: self.redact(value) for name, value in content.items()}
        if tuple(sorted(redacted)) != tuple(proposal.payload["fields"]):
            raise ValueError("Fields differ from the approved disclosure")
        if (
            sum(len(value) for value in redacted.values())
            != proposal.payload["estimated_text_length"]
        ):
            raise ValueError("Content length changed; create a new disclosure")
        if canonical_digest(redacted) != proposal.payload["content_digest"]:
            raise ValueError("Content changed; create a new disclosure")
        return ApprovedCloudPayload(provider, redacted, approval.digest)
