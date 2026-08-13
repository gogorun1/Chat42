import pytest

from app.services.llm_client import FakeLLMClient, LLMClient


def test_fake_llm_client_satisfies_protocol() -> None:
    client = FakeLLMClient(response="Bonjour")

    assert isinstance(client, LLMClient)


@pytest.mark.asyncio
async def test_fake_llm_client_generates_configured_response() -> None:
    client = FakeLLMClient(response="I visited the Garden.")

    response = await client.generate("Write today's diary.")

    assert response == "I visited the Garden."
    assert client.prompts == ["Write today's diary."]


@pytest.mark.asyncio
async def test_fake_llm_client_streams_configured_chunks() -> None:
    client = FakeLLMClient(chunks=["I was ", "in the Garden."])

    chunks = [chunk async for chunk in client.stream("Where were you?")]

    assert chunks == ["I was ", "in the Garden."]
    assert client.prompts == ["Where were you?"]
