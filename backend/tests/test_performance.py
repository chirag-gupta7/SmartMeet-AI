import time
import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services.llm_service import generate_action_reply

class TestLLMPerformance(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["HUGGINGFACE_API_KEY"] = "fake-key"
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch("backend.app.services.llm_service.InferenceClient")
    def test_generate_action_reply_performance(self, mock_client_class):
        # Mocking the client and chat_completion
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Simulate a delay in the LLM response
        def slow_response(*args, **kwargs):
            time.sleep(0.5)
            # Mock response object structure
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message.content = '{"action": "weather", "reply": "It is sunny."}'
            return mock_resp

        mock_client.chat_completion.side_effect = slow_response

        # First call should take ~0.5s
        start_time = time.time()
        generate_action_reply("What is the weather?")
        duration1 = time.time() - start_time
        print(f"\nFirst call duration: {duration1:.4f}s")

        # Second call with same text should also take ~0.5s (before optimization)
        start_time = time.time()
        generate_action_reply("What is the weather?")
        duration2 = time.time() - start_time
        print(f"Second call duration: {duration2:.4f}s")

        self.assertGreaterEqual(duration1, 0.5)
        # Second call should be near-instant due to memoization
        self.assertLess(duration2, 0.1)

if __name__ == "__main__":
    unittest.main()
