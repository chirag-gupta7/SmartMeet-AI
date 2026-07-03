import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
import sys
import os

# Ensure the root of the project is in the path
sys.path.insert(0, os.getcwd())

from backend.app.services.llm_service import generate_action_reply, _memoized_generate_action_reply
from backend.app.services.elevenlabs_service import synthesize_speech, _memoized_synthesize_speech

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['HUGGINGFACE_API_KEY'] = 'fake-hf-key'
        self.app.config['ELEVENLABS_API_KEY'] = 'fake-eleven-key'
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Clear caches before each test
        _memoized_generate_action_reply.cache_clear()
        _memoized_synthesize_speech.cache_clear()

    def tearDown(self):
        self.ctx.pop()

    @patch('backend.app.services.llm_service.InferenceClient')
    def test_llm_caching(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat_completion.return_value.choices[0].message.content = '{"action": "general_response", "reply": "hi"}'

        # 10 calls with same text
        for _ in range(10):
            generate_action_reply("Hello")

        # InferenceClient should be initialized once
        self.assertEqual(mock_client_class.call_count, 1)
        # chat_completion should be called only once due to LRU cache
        self.assertEqual(mock_client.chat_completion.call_count, 1)

    @patch('backend.app.services.elevenlabs_service.ElevenLabs')
    def test_elevenlabs_caching(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        # 10 calls with same text
        for _ in range(10):
            synthesize_speech("Hello")

        # ElevenLabs should be initialized once
        self.assertEqual(mock_client_class.call_count, 1)
        # convert should be called only once due to LRU cache
        self.assertEqual(mock_client.text_to_speech.convert.call_count, 1)

if __name__ == '__main__':
    unittest.main()
