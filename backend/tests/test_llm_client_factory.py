from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from app.services.llm_client_factory import get_llm_client


class LLMClientFactoryTests(TestCase):
    def setUp(self) -> None:
        get_llm_client.cache_clear()

    def tearDown(self) -> None:
        get_llm_client.cache_clear()

    @patch("app.services.llm_client_factory.get_settings")
    @patch("app.services.llm_client_factory.genai.Client")
    def test_builds_and_caches_gemini_client(self, sdk_client, get_settings) -> None:
        get_settings.return_value = SimpleNamespace(
            gemini_api_key="test-key",
            gemini_model="gemini-test",
        )
        sdk = Mock()
        sdk_client.return_value = sdk

        first = get_llm_client()
        second = get_llm_client()

        self.assertIs(first, second)
        self.assertIs(first._client, sdk)
        self.assertEqual(first._model, "gemini-test")
        sdk_client.assert_called_once_with(api_key="test-key")

    @patch("app.services.llm_client_factory.get_settings")
    def test_rejects_missing_api_key(self, get_settings) -> None:
        get_settings.return_value = SimpleNamespace(
            gemini_api_key="",
            gemini_model="gemini-test",
        )

        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
            get_llm_client()
