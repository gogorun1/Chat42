from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    async def generate(self, prompt: str) -> str: ...

    def stream(self, prompt: str) -> AsyncIterator[str]: ...


class FakeLLMClient:
    def __init__(
        self,
        response: str = "",
        chunks: list[str] | None = None,
    ) -> None:
        self.response = response
        self.chunks = chunks or []
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        self.prompts.append(prompt)
        for chunk in self.chunks:
            yield chunk
