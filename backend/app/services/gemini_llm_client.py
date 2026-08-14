from collections.abc import AsyncIterator
from typing import Any


class GeminiLLMClient:
    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    async def generate(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text or ""

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        response = await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=prompt,
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text
