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


def test_create_calendar_event_oversized_text():
    processor = VoiceCommandProcessor()
    long_event = "A" * 10001
    res = processor.create_calendar_event(long_event)
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]


def test_create_calendar_event_empty_or_invalid():
    processor = VoiceCommandProcessor()
    for empty in ["", "   ", None, 123]:
        res = processor.create_calendar_event(empty)
        assert res["success"] is False
        assert res["error"] == "Event text is required."


def test_calculate_validation_and_length_limit():
    processor = VoiceCommandProcessor()
    # Invalid / empty
    for invalid in ["", "   ", None, 12345]:
        res = processor.calculate(invalid)
        assert res["success"] is False
        assert res["error"] == "Expression must be a non-empty string."

    # Oversized
    oversized = "1+" * 251  # 502 chars
    res = processor.calculate(oversized)
    assert res["success"] is False
    assert "exceeds maximum length" in res["error"]


def test_set_timer_duration_limits():
    processor = VoiceCommandProcessor()
    # Invalid / non-positive / boolean / too large
    invalid_durations = [0, -10, 1441, True, False, "invalid"]
    for dur in invalid_durations:
        res = processor.set_timer(dur)
        assert res["success"] is False

    # Valid duration
    res = processor.set_timer(5)
    assert res["success"] is True


def test_set_reminder_validation():
    processor = VoiceCommandProcessor()
    # Empty or non-string
    res = processor.set_reminder("", "tomorrow")
    assert res["success"] is False
    res = processor.set_reminder("buy milk", None)
    assert res["success"] is False

    # Oversized
    res = processor.set_reminder("A" * 1001, "tomorrow")
    assert res["success"] is False


def test_web_search_and_translate_validation():
    processor = VoiceCommandProcessor()
    # Search invalid/oversized
    assert processor.web_search("")["success"] is False
    assert processor.web_search("A" * 501)["success"] is False

    # Translate invalid/oversized
    assert processor.translate_text("", "Spanish")["success"] is False
    assert processor.translate_text("hello", "A" * 51)["success"] is False
