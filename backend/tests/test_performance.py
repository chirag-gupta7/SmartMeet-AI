import time
import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.llm_service import generate_action_reply
from app.services.elevenlabs_service import synthesize_speech

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['HUGGINGFACE_API_KEY'] = 'fake_hf_key'
        self.app.config['ELEVENLABS_API_KEY'] = 'fake_el_key'
        self.app.config['ELEVENLABS_VOICE_ID'] = 'fake_voice_id'
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('app.services.llm_service.InferenceClient')
    def test_llm_performance(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat_completion.return_value.choices[0].message.content = '{"action": "test", "reply": "hello"}'

        # Repeated calls with same input
        for _ in range(3):
            generate_action_reply("hello")

        # Verify caching
        self.assertEqual(mock_client_class.call_count, 1)
        self.assertEqual(mock_client.chat_completion.call_count, 1)

        # Call with different input
        generate_action_reply("world")
        self.assertEqual(mock_client.chat_completion.call_count, 2)

    @patch('app.services.elevenlabs_service.ElevenLabs')
    def test_tts_performance(self, mock_el_class):
        mock_client = MagicMock()
        mock_el_class.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = [b"audio", b"data"]

        # Repeated calls with same input
        for _ in range(3):
            synthesize_speech("hello")

        # Verify caching
        self.assertEqual(mock_el_class.call_count, 1)
        self.assertEqual(mock_client.text_to_speech.convert.call_count, 1)

        # Call with different input
        synthesize_speech("world")
        self.assertEqual(mock_client.text_to_speech.convert.call_count, 2)

if __name__ == '__main__':
    unittest.main()
