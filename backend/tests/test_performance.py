import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services import llm_service, elevenlabs_service

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['HUGGINGFACE_API_KEY'] = 'fake-hf-key'
        self.app.config['ELEVENLABS_API_KEY'] = 'fake-eleven-key'

        # Reset singletons
        llm_service._client = None
        llm_service._last_api_key = None
        llm_service._get_llm_response_memoized.cache_clear()

        elevenlabs_service._client = None
        elevenlabs_service._last_api_key = None
        elevenlabs_service._synthesize_speech_memoized.cache_clear()

    @patch('app.services.llm_service.InferenceClient')
    def test_llm_client_singleton(self, mock_client):
        # Mock the chat_completion return value
        mock_instance = mock_client.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"action": "test", "reply": "test"}'
        mock_instance.chat_completion.return_value = mock_response

        with self.app.app_context():
            # Call multiple times with same text (triggers cache)
            for _ in range(5):
                llm_service.generate_action_reply("test")

            # Client should be instantiated once
            print(f"\nLLM Client instantiations (same text): {mock_client.call_count}")
            self.assertEqual(mock_client.call_count, 1)

            # API call should happen once (due to memoization)
            self.assertEqual(mock_instance.chat_completion.call_count, 1)

            # Call with different text (triggers new API call but same client)
            llm_service.generate_action_reply("different test")
            print(f"LLM Client instantiations (different text): {mock_client.call_count}")
            self.assertEqual(mock_client.call_count, 1)
            self.assertEqual(mock_instance.chat_completion.call_count, 2)

    @patch('app.services.elevenlabs_service.ElevenLabs')
    def test_elevenlabs_client_singleton(self, mock_client):
        # Mock the convert method
        mock_instance = mock_client.return_value
        mock_instance.text_to_speech.convert.return_value = [b"audio"]

        with self.app.app_context():
            # Call multiple times with same text
            for _ in range(5):
                elevenlabs_service.synthesize_speech("test")

            # Client should be instantiated once
            print(f"ElevenLabs Client instantiations (same text): {mock_client.call_count}")
            self.assertEqual(mock_client.call_count, 1)

            # API call should happen once
            self.assertEqual(mock_instance.text_to_speech.convert.call_count, 1)

            # Call with different text
            elevenlabs_service.synthesize_speech("different test")
            print(f"ElevenLabs Client instantiations (different text): {mock_client.call_count}")
            self.assertEqual(mock_client.call_count, 1)
            self.assertEqual(mock_instance.text_to_speech.convert.call_count, 2)

    @patch('app.services.llm_service.InferenceClient')
    def test_llm_client_reinit_on_key_change(self, mock_client):
        mock_instance = mock_client.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"action": "test", "reply": "test"}'
        mock_instance.chat_completion.return_value = mock_response

        with self.app.app_context():
            llm_service.generate_action_reply("test")
            self.assertEqual(mock_client.call_count, 1)

            # Change API key
            self.app.config['HUGGINGFACE_API_KEY'] = 'new-fake-hf-key'
            llm_service.generate_action_reply("test")

            # Should re-initialize client
            print(f"LLM Client instantiations (key change): {mock_client.call_count}")
            self.assertEqual(mock_client.call_count, 2)

if __name__ == '__main__':
    unittest.main()
