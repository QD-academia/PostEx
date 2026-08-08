from __future__ import annotations

import json

from postex.approvals import ApprovalRecord
from postex.errors import ConfigurationError
from postex.privacy import ApprovedCloudPayload
from postex.providers.base import (
    ProviderRequest,
    ProviderResponse,
    verify_upload_approval,
)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, client: object | None = None) -> None:
        self._client = client

    async def complete(
        self,
        request: ProviderRequest,
        payload: ApprovedCloudPayload,
        approval: ApprovalRecord,
    ) -> ProviderResponse:
        verify_upload_approval(payload, approval)
        client = self._client
        if client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError as exc:
                raise ConfigurationError("Install PostEx with the 'anthropic' extra") from exc
            client = AsyncAnthropic()
        response = await client.messages.create(  # type: ignore[attr-defined]
            model=request.model,
            system=request.system,
            max_tokens=request.max_output_tokens,
            messages=[
                {
                    "role": "user",
                    "content": request.prompt
                    + "\n\n"
                    + json.dumps(payload.content, ensure_ascii=False),
                }
            ],
        )
        text = "".join(getattr(block, "text", "") for block in response.content)
        return ProviderResponse(
            text=text,
            provider=self.name,
            model=request.model,
            request_id=getattr(response, "id", None),
        )
