from app.services.command_processor import VoiceCommandProcessor


def test_get_weather_valid_location():
    processor = VoiceCommandProcessor()
    res = processor.get_weather("London")
    assert res["success"] is True
    assert "London" in res["user_message"] or "data" in res


def test_get_weather_invalid_characters_ssrf_attempt():
    processor = VoiceCommandProcessor()
    # SSRF / parameter injection attempts
    malicious_inputs = [
        "http://169.254.169.254/latest/meta-data/",
        "London&appid=evil_key",
        "New York\r\nHost: evil.com",
        "<script>alert(1)</script>",
        "London; drop table users;",
    ]
    for inp in malicious_inputs:
        res = processor.get_weather(inp)
        assert res["success"] is False
        assert res["error"] == "Invalid characters or length in location"


def test_get_weather_oversized_location():
    processor = VoiceCommandProcessor()
    long_location = "A" * 101
    res = processor.get_weather(long_location)
    assert res["success"] is False
    assert res["error"] == "Invalid characters or length in location"


def test_get_weather_empty_or_non_string():
    processor = VoiceCommandProcessor()
    for empty in ["", "   ", None, 123]:
        res = processor.get_weather(empty)
        assert res["success"] is False
        assert res["error"] == "Invalid location provided"
