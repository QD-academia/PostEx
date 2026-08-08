from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from postex.approvals import ApprovalRecord
from postex.enums import ApprovalDecision, ApprovalSubject
from postex.errors import ApprovalRequired
from postex.privacy import ApprovedCloudPayload


@dataclass(frozen=True)
class ProviderRequest:
    model: str
    system: str
    prompt: str
    max_output_tokens: int = 4096


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    provider: str
    model: str
    request_id: str | None = None


def verify_upload_approval(payload: ApprovedCloudPayload, approval: ApprovalRecord) -> None:
    if (
        approval.subject is not ApprovalSubject.CLOUD_UPLOAD
        or approval.decision is not ApprovalDecision.APPROVED
        or approval.digest != payload.disclosure_digest
    ):
        raise ApprovalRequired("Provider call lacks matching cloud-upload approval")


class Provider(Protocol):
    name: str

    async def complete(
        self,
        request: ProviderRequest,
        payload: ApprovedCloudPayload,
        approval: ApprovalRecord,
    ) -> ProviderResponse: ...
