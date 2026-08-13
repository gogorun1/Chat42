from unittest.mock import AsyncMock, Mock

import pytest

from app.services.gemini_llm_client import GeminiLLMClient


@pytest.mark.asyncio
async def test_generate_returns_gemini_text() -> None:
    sdk_client = Mock()
    sdk_client.aio.models.generate_content = AsyncMock(
        return_value=Mock(text="Moulinette was in the Garden.")
    )
    client = GeminiLLMClient(sdk_client, model="gemini-test")

    result = await client.generate("Write a diary.")

    assert result == "Moulinette was in the Garden."
    sdk_client.aio.models.generate_content.assert_awaited_once_with(
        model="gemini-test",
        contents="Write a diary.",
    )


@pytest.mark.asyncio
async def test_stream_yields_only_text_chunks() -> None:
    async def response_stream():
        for text in ["I was ", None, "in the Garden."]:
            yield Mock(text=text)

    sdk_client = Mock()
    sdk_client.aio.models.generate_content_stream = AsyncMock(
        return_value=response_stream()
    )
    client = GeminiLLMClient(sdk_client, model="gemini-test")

    chunks = [chunk async for chunk in client.stream("Where were you?")]

    assert chunks == ["I was ", "in the Garden."]
    sdk_client.aio.models.generate_content_stream.assert_awaited_once_with(
        model="gemini-test",
        contents="Where were you?",
    )
