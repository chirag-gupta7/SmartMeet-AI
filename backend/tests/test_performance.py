import time
import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
import sys
import os

# Add the parent directory to sys.path to import from backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.elevenlabs_service import synthesize_speech
from app.services.llm_service import generate_action_reply

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['ELEVENLABS_API_KEY'] = 'fake_key'
        self.app.config['ELEVENLABS_VOICE_ID'] = 'fake_voice'
        self.app.config['HUGGINGFACE_API_KEY'] = 'fake_hf_key'

    @patch('app.services.elevenlabs_service.ElevenLabs')
    def test_synthesize_speech_performance(self, mock_elevenlabs):
        # Mock the client and its behavior
        mock_client = MagicMock()
        mock_elevenlabs.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = [b"audio", b"data"]

        with self.app.app_context():
            # Warm up / First call
            start_time = time.time()
            res1 = synthesize_speech("Hello world")
            first_duration = time.time() - start_time

            # Second call with same text
            start_time = time.time()
            res2 = synthesize_speech("Hello world")
            second_duration = time.time() - start_time

            print(f"\nTTS - First call duration: {first_duration:.6f}s")
            print(f"TTS - Second call duration: {second_duration:.6f}s")

            self.assertEqual(res1, res2)

    @patch('app.services.llm_service.InferenceClient')
    def test_llm_performance(self, mock_inference_client):
        # Mock the client and its behavior
        mock_client = MagicMock()
        mock_inference_client.return_value = mock_client

        # Mock response structure
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"action": "weather", "reply": "It is sunny."}'
        mock_client.chat_completion.return_value = mock_response

        with self.app.app_context():
            # First call
            start_time = time.time()
            res1 = generate_action_reply("What is the weather?")
            first_duration = time.time() - start_time

            # Second call with same text
            start_time = time.time()
            res2 = generate_action_reply("What is the weather?")
            second_duration = time.time() - start_time

            print(f"\nLLM - First call duration: {first_duration:.6f}s")
            print(f"LLM - Second call duration: {second_duration:.6f}s")

            self.assertEqual(res1, res2)

if __name__ == '__main__':
    unittest.main()
