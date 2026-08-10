from __future__ import annotations

import json
from typing import Any

from postex.approvals import ApprovalRecord
from postex.errors import ConfigurationError
from postex.privacy import ApprovedCloudPayload
from postex.providers.base import (
    ProviderRequest,
    ProviderResponse,
    verify_upload_approval,
)


class OpenAIProvider:
    name = "openai"

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
                from openai import AsyncOpenAI
            except ImportError as exc:
                raise ConfigurationError("Install PostEx with the 'openai' extra") from exc
            client = AsyncOpenAI()
        dynamic_client: Any = client
        response = await dynamic_client.responses.create(
            model=request.model,
            instructions=request.system,
            input=request.prompt + "\n\n" + json.dumps(payload.content, ensure_ascii=False),
            max_output_tokens=request.max_output_tokens,
        )
        return ProviderResponse(
            text=response.output_text,
            provider=self.name,
            model=request.model,
            request_id=getattr(response, "id", None),
        )
