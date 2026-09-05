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


def test_set_timer_security_validation():
    processor = VoiceCommandProcessor()
    # Test duration exceeding max limit (1440 minutes / 24 hours)
    res = processor.set_timer(1441)
    assert res["success"] is False
    assert "exceeds maximum allowed limit" in res["error"]

    # Test invalid label length or non-string
    res = processor.set_timer(10, label="L" * 101)
    assert res["success"] is False
    assert res["error"] == "Invalid timer label"

    res = processor.set_timer(10, label=12345)
    assert res["success"] is False
    assert res["error"] == "Invalid timer label"


def test_set_reminder_security_validation():
    processor = VoiceCommandProcessor()
    # Test empty or non-string inputs
    for invalid in ["", "   ", None, 123]:
        res = processor.set_reminder(invalid, "tomorrow")
        assert res["success"] is False
        assert res["error"] == "Invalid reminder parameters."

        res = processor.set_reminder("Call mom", invalid)
        assert res["success"] is False
        assert res["error"] == "Invalid reminder parameters."

    # Test oversized inputs
    res = processor.set_reminder("A" * 501, "tomorrow")
    assert res["success"] is False
    assert "exceed maximum allowed length" in res["error"]


def test_web_search_security_validation():
    processor = VoiceCommandProcessor()
    for invalid in ["", "   ", None, 123]:
        res = processor.web_search(invalid)
        assert res["success"] is False
        assert res["error"] == "Invalid search query."

    res = processor.web_search("Q" * 501)
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]


def test_translate_text_security_validation():
    processor = VoiceCommandProcessor()
    for invalid in ["", "   ", None, 123]:
        res = processor.translate_text(invalid, "French")
        assert res["success"] is False
        assert res["error"] == "Invalid translation input."

        res = processor.translate_text("Hello", invalid)
        assert res["success"] is False
        assert res["error"] == "Invalid translation input."

    res = processor.translate_text("T" * 5001, "French")
    assert res["success"] is False
    assert res["error"] == "Translation input exceeds length limits."


def test_calculate_security_validation():
    processor = VoiceCommandProcessor()
    for invalid in ["", "   ", None, 123]:
        res = processor.calculate(invalid)
        assert res["success"] is False
        assert res["error"] == "Invalid expression"

    res = processor.calculate("1 + " * 200)
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]
