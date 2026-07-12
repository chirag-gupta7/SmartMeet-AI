import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from backend.app.services import llm_service


class TestLLMPerformance(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["HUGGINGFACE_API_KEY"] = "fake-key"
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Reset singleton state if it exists (for post-optimization tests)
        if hasattr(llm_service, "_client"):
            llm_service._client = None
        if hasattr(llm_service, "_last_api_key"):
            llm_service._last_api_key = None
        if hasattr(llm_service, "_get_llm_response_memoized"):
            llm_service._get_llm_response_memoized.cache_clear()

    def tearDown(self):
        self.ctx.pop()

    @patch("backend.app.services.llm_service.InferenceClient")
    def test_client_instantiation_count(self, mock_client_class):
        """
        Verify that InferenceClient is instantiated once (singleton pattern).
        """
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock the chat_completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        content = '{"action": "test", "reply": "hi"}'
        mock_response.choices[0].message.content = content
        mock_client.chat_completion.return_value = mock_response

        # Call the service multiple times
        llm_service.generate_action_reply("hello")
        llm_service.generate_action_reply("world")

        # After optimization, this should be 1.
        instantiation_count = mock_client_class.call_count
        self.assertEqual(
            instantiation_count,
            1,
            f"Expected 1 client instantiation, got {instantiation_count}"
        )

    @patch("backend.app.services.llm_service.InferenceClient")
    def test_memoization_impact(self, mock_client_class):
        """
        Verify that identical requests use the cache.
        """
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        content = '{"action": "test", "reply": "hi"}'
        mock_response.choices[0].message.content = content
        mock_client.chat_completion.return_value = mock_response

        # Same input twice
        llm_service.generate_action_reply("repeat me")
        llm_service.generate_action_reply("repeat me")

        # After optimization, chat_completion should be called only once.
        call_count = mock_client.chat_completion.call_count
        self.assertEqual(
            call_count,
            1,
            f"Expected 1 API call for identical requests, got {call_count}"
        )


if __name__ == "__main__":
    unittest.main()
