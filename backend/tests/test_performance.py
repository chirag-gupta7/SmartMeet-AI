import unittest
from unittest.mock import patch, MagicMock
from backend.app import create_app
import time

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['ELEVENLABS_API_KEY'] = 'fake_key'
        self.app.config['HUGGINGFACE_API_KEY'] = 'fake_key'
        self.ctx = self.app.app_context()
        self.ctx.push()

        # We need to import these here to ensure they use the app context we just pushed
        from backend.app.services.elevenlabs_service import _get_cached_client, _memoized_synthesize
        _get_cached_client.cache_clear()
        _memoized_synthesize.cache_clear()

    def tearDown(self):
        self.ctx.pop()

    @patch('backend.app.services.elevenlabs_service.ElevenLabs')
    def test_elevenlabs_client_caching(self, mock_elevenlabs):
        from backend.app.services.elevenlabs_service import _get_client as get_eleven_client

        # Measure time for multiple client initializations
        start_time = time.time()
        for _ in range(100):
            client = get_eleven_client()
        end_time = time.time()
        duration = end_time - start_time
        print(f"\nElevenLabs client init time (100 iterations) AFTER OPTIMIZATION: {duration:.4f}s")

        # Check if they are the same object
        client1 = get_eleven_client()
        client2 = get_eleven_client()
        self.assertIs(client1, client2)

        # The client should have been instantiated exactly once
        self.assertEqual(mock_elevenlabs.call_count, 1)

    @patch('backend.app.services.elevenlabs_service.ElevenLabs')
    def test_synthesize_speech_memoization(self, mock_elevenlabs):
        from backend.app.services.elevenlabs_service import synthesize_speech

        # Setup mock
        mock_instance = mock_elevenlabs.return_value
        mock_instance.text_to_speech.convert.return_value = [b"audio_data"]

        text = "Hello world"

        # First call - should call the API
        start_time = time.time()
        res1 = synthesize_speech(text)
        duration1 = time.time() - start_time

        # Second call - should be cached
        start_time = time.time()
        res2 = synthesize_speech(text)
        duration2 = time.time() - start_time

        print(f"\nFirst synthesize call: {duration1:.4f}s")
        print(f"Second synthesize call (cached): {duration2:.4f}s")

        self.assertIsNotNone(res1)
        self.assertEqual(res1, res2)
        self.assertLess(duration2, duration1)
        # API should only be called once
        self.assertEqual(mock_instance.text_to_speech.convert.call_count, 1)

if __name__ == '__main__':
    unittest.main()
