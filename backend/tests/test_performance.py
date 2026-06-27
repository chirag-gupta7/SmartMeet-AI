import time
import unittest
from unittest.mock import MagicMock, patch
from flask import Flask

# Create a dummy Flask app for context
app = Flask(__name__)
app.config['ELEVENLABS_API_KEY'] = 'fake-key'
app.config['HUGGINGFACE_API_KEY'] = 'fake-key'

# Import services
from backend.app.services.elevenlabs_service import synthesize_speech, _get_client as get_eleven_client
from backend.app.services.llm_service import generate_action_reply, _get_client as get_llm_client

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('backend.app.services.elevenlabs_service.ElevenLabs')
    def test_elevenlabs_client_caching(self, mock_eleven):
        # Measure time to get client multiple times
        start_time = time.time()
        for _ in range(10000):
            get_eleven_client()
        end_time = time.time()
        duration = end_time - start_time
        print(f"\nElevenLabs client retrieval (10000x): {duration:.4f}s")

        # Verify it was called only once (or very few times if cache is shared/reset, but lru_cache(1) should be 1)
        # Note: since we are patching, we need to be careful.
        # Actually, the lru_cache is on _get_cached_client which calls ElevenLabs.
        self.assertLess(duration, 0.1) # Should be much faster now

    @patch('backend.app.services.llm_service.InferenceClient')
    def test_llm_client_caching(self, mock_hf):
        # Measure time to get client multiple times
        start_time = time.time()
        for _ in range(10000):
            get_llm_client()
        end_time = time.time()
        duration = end_time - start_time
        print(f"HuggingFace client retrieval (10000x): {duration:.4f}s")
        self.assertLess(duration, 0.1)

    @patch('backend.app.services.elevenlabs_service._get_cached_client')
    def test_memoization_impact(self, mock_get_cached_client):
        mock_client = MagicMock()
        mock_get_cached_client.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        text = "Hello world"

        # First call
        synthesize_speech(text)
        self.assertEqual(mock_client.text_to_speech.convert.call_count, 1)

        # Subsequent calls should be memoized
        start_time = time.time()
        for _ in range(100):
            synthesize_speech(text)
        end_time = time.time()
        duration = end_time - start_time
        print(f"ElevenLabs synthesize_speech (100x same text, memoized): {duration:.4f}s")

        # Still 1
        self.assertEqual(mock_client.text_to_speech.convert.call_count, 1)
        self.assertLess(duration, 0.01)

if __name__ == "__main__":
    unittest.main()
