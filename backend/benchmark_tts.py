import time
import base64
from unittest.mock import MagicMock, patch
from flask import Flask
from app.services.elevenlabs_service import synthesize_speech, _synthesize_speech_memoized

def benchmark():
    app = Flask(__name__)
    app.config["ELEVENLABS_API_KEY"] = "fake-key"
    app.config["ELEVENLABS_VOICE_ID"] = "fake-voice"

    with app.app_context():
        # Clear cache before starting
        _synthesize_speech_memoized.cache_clear()

        # Mocking ElevenLabs client and its convert method
        mock_client = MagicMock()
        mock_audio_stream = [b"audio", b"data"]
        mock_client.text_to_speech.convert.return_value = mock_audio_stream

        with patch("app.services.elevenlabs_service.ElevenLabs", return_value=mock_client) as mock_init:
            text = "Hello world"

            print(f"--- Benchmarking TTS for: '{text}' ---")

            # First call (should initialize client and call API)
            start_time = time.time()
            res1 = synthesize_speech(text)
            duration1 = time.time() - start_time
            print(f"First call duration: {duration1:.6f}s")

            # Second call (should be cached, no client init, no API call)
            start_time = time.time()
            res2 = synthesize_speech(text)
            duration2 = time.time() - start_time
            print(f"Second call (cached) duration: {duration2:.6f}s")

            # Third call with different text (should call API but NOT re-init client)
            text2 = "Goodbye world"
            start_time = time.time()
            res3 = synthesize_speech(text2)
            duration3 = time.time() - start_time
            print(f"Third call (new text) duration: {duration3:.6f}s")

            # Assertions to verify behavior
            assert res1 == res2
            assert res1 == base64.b64encode(b"audiodata").decode("utf-8")
            assert mock_init.call_count == 1, f"ElevenLabs should be initialized once, but was called {mock_init.call_count} times"
            assert mock_client.text_to_speech.convert.call_count == 2, f"API should be called twice (once for each unique text), but was called {mock_client.text_to_speech.convert.call_count} times"

            if duration2 < duration1:
                print("\n✅ Performance Improvement Verified: Cached call was faster!")
                print(f"Speedup: {duration1 / duration2:.2f}x")
            else:
                print("\n❌ Cached call was not significantly faster. Check implementation.")

if __name__ == "__main__":
    benchmark()
