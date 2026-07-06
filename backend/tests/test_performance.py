import unittest
from unittest.mock import MagicMock, patch
import time
from flask import Flask
from backend.app.services.llm_service import generate_action_reply, _get_client
from backend.app.services.elevenlabs_service import synthesize_speech, _get_client as _get_eleven_client

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['HUGGINGFACE_API_KEY'] = 'fake_hf_key'
        self.app.config['ELEVENLABS_API_KEY'] = 'fake_eleven_key'
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('backend.app.services.llm_service.InferenceClient')
    def test_llm_client_instantiation_and_memoization(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat_completion.return_value.choices[0].message.content = '{"action": "weather", "reply": "Sunny"}'

        # Test multiple calls
        for _ in range(5):
            generate_action_reply("What is the weather?")

        print(f"\nLLM Client init count: {mock_client_class.call_count}")
        print(f"LLM API call count: {mock_client.chat_completion.call_count}")

    @patch('backend.app.services.elevenlabs_service.ElevenLabs')
    def test_elevenlabs_client_instantiation_and_memoization(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = [b"audio_data"]

        # Test multiple calls
        for _ in range(5):
            synthesize_speech("Hello world")

        print(f"\nElevenLabs Client init count: {mock_client_class.call_count}")
        print(f"ElevenLabs API call count: {mock_client.text_to_speech.convert.call_count}")

if __name__ == "__main__":
    unittest.main()
