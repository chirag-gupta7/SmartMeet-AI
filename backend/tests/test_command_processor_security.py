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


def test_create_calendar_event_empty_or_non_string():
    processor = VoiceCommandProcessor()
    for empty in ["", "   ", None, 123]:
        res = processor.create_calendar_event(empty)
        assert res["success"] is False
        assert res["error"] == "Invalid event text provided"


def test_create_calendar_event_oversized():
    processor = VoiceCommandProcessor()
    long_event = "A" * 10001
    res = processor.create_calendar_event(long_event)
    assert res["success"] is False
    assert res["error"] == (
        "Event text exceeds maximum allowed length of 10000 characters."
    )


def test_set_timer_oversized_duration():
    processor = VoiceCommandProcessor()
    res = processor.set_timer(1441)
    assert res["success"] is False
    assert res["error"] == "Duration exceeds maximum limit of 1440 minutes"


def test_set_timer_invalid_duration_types_and_bounds():
    processor = VoiceCommandProcessor()
    invalid_inputs = [-1, 0, "abc", None, [], {}]
    for inp in invalid_inputs:
        res = processor.set_timer(inp)
        assert res["success"] is False


def test_set_timer_oversized_label():
    processor = VoiceCommandProcessor()
    long_label = "A" * 101
    res = processor.set_timer(10, label=long_label)
    assert res["success"] is False
    assert res["error"] == "Timer label exceeds 100 characters"


def test_set_timer_valid():
    processor = VoiceCommandProcessor()
    res = processor.set_timer(5, label="Quick Break")
    assert res["success"] is True
    assert res["data"]["duration"] == 5
    assert res["data"]["label"] == "Quick Break"


def test_set_reminder_validation():
    processor = VoiceCommandProcessor()

    # Empty text
    res = processor.set_reminder("", "tomorrow")
    assert res["success"] is False
    assert res["error"] == "Invalid reminder text provided"

    # Oversized text
    res = processor.set_reminder("A" * 1001, "tomorrow")
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]

    # Empty when
    res = processor.set_reminder("buy milk", "")
    assert res["success"] is False
    assert res["error"] == "Invalid reminder time provided"

    # Oversized when
    res = processor.set_reminder("buy milk", "B" * 256)
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]


def test_calculate_validation():
    processor = VoiceCommandProcessor()
    for invalid in ["", "   ", None, 123]:
        res = processor.calculate(invalid)
        assert res["success"] is False
        assert res["error"] == "Invalid expression provided"

    long_expr = "1+" * 251
    res = processor.calculate(long_expr)
    assert res["success"] is False
    assert res["error"] == "Expression is too long"


def test_web_search_validation():
    processor = VoiceCommandProcessor()

    # Empty query
    res = processor.web_search("   ")
    assert res["success"] is False
    assert res["error"] == "Invalid search query provided"

    # Oversized query
    res = processor.web_search("Q" * 501)
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]


def test_translate_text_validation():
    processor = VoiceCommandProcessor()

    # Empty text
    res = processor.translate_text("")
    assert res["success"] is False
    assert res["error"] == "Invalid text provided for translation"

    # Oversized text
    res = processor.translate_text("T" * 5001)
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]

    # Oversized target language
    res = processor.translate_text("hello", target_language="L" * 101)
    assert res["success"] is False
    assert "exceeds maximum allowed length" in res["error"]


def test_get_upcoming_events_validation():
    processor = VoiceCommandProcessor()
    for invalid_days in ["invalid", None, [7]]:
        res = processor.get_upcoming_events(invalid_days)
        assert res["success"] is False
        assert res["error"] == "Invalid days parameter provided"

    for out_of_range in [0, -5, 366, 1000]:
        res = processor.get_upcoming_events(out_of_range)
        assert res["success"] is False
        assert res["error"] == "Days parameter out of allowed range"
