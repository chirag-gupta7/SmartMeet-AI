from datetime import datetime, timedelta, timezone as dt_timezone
from functools import lru_cache
import logging
import re
from zoneinfo import ZoneInfo
from dateutil import parser
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

DEFAULT_TIMEZONE = "UTC"

# BOLT OPTIMIZATION: Pre-compile regex patterns at module level to eliminate
# dynamic pattern compilation overhead on every natural language date parse.
_TIME_RANGE_PATTERNS = [
    re.compile(
        r"(\d{1,2}):(\d{2})\s*(am|pm)?\s*(?:to|until|till|-)\s*"
        r"(\d{1,2}):(\d{2})\s*(am|pm)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d{1,2})\s*(am|pm)\s*(?:to|until|till|-)\s*(\d{1,2})\s*(am|pm)",
        re.IGNORECASE,
    ),
    re.compile(
        r"from\s*(\d{1,2}):(\d{2})\s*(am|pm)?\s*(?:to|until|till|-)\s*"
        r"(\d{1,2}):(\d{2})\s*(am|pm)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"from\s*(\d{1,2})\s*(am|pm)\s*(?:to|until|till|-)\s*"
        r"(\d{1,2})\s*(am|pm)",
        re.IGNORECASE,
    ),
]

_TIME_PATTERNS = [
    re.compile(r"(\d{1,2}):(\d{2})\s*(am|pm)", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s*(am|pm)", re.IGNORECASE),
    re.compile(r"at\s*(\d{1,2}):(\d{2})", re.IGNORECASE),
    re.compile(r"at\s*(\d{1,2})\s*(am|pm)", re.IGNORECASE),
    re.compile(r"(\d{1,2}):(\d{2})", re.IGNORECASE),
]

_ALL_DAY_PATTERN = re.compile(r"\b(all[- ]?day|full[- ]?day)\b", re.IGNORECASE)
_DIGIT_PATTERN = re.compile(r"\d")
_MONTH_PATTERN = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b",
    re.IGNORECASE,
)
_NEXT_WEEKDAY_PATTERNS = [
    ("monday", re.compile(r"next\s+monday", re.IGNORECASE), 7),
    ("tuesday", re.compile(r"next\s+tuesday", re.IGNORECASE), 8),
    ("wednesday", re.compile(r"next\s+wednesday", re.IGNORECASE), 9),
    ("thursday", re.compile(r"next\s+thursday", re.IGNORECASE), 10),
    ("friday", re.compile(r"next\s+friday", re.IGNORECASE), 11),
    ("saturday", re.compile(r"next\s+saturday", re.IGNORECASE), 12),
    ("sunday", re.compile(r"next\s+sunday", re.IGNORECASE), 13),
]
_THIS_WEEKEND_PATTERN = re.compile(r"this\s+weekend", re.IGNORECASE)


def _fallback_utc():
    """
    Return a UTC zone even when no IANA database is installed
    (e.g. bare Windows hosts); datetime.timezone.utc needs no data files.
    """
    try:
        return ZoneInfo(DEFAULT_TIMEZONE)
    except Exception:
        return dt_timezone.utc


# BOLT OPTIMIZATION: Memoize timezone resolution to prevent repeated ZoneInfo
# instantiation and exception handling for identical timezone names.
@lru_cache(maxsize=64)
def resolve_timezone(timezone_name=None):
    """
    Resolve an IANA timezone name (e.g. "Asia/Kolkata") to a ZoneInfo,
    falling back to UTC when the name is missing or unknown. Memoized
    with lru_cache to eliminate ZoneInfo instantiation overhead.
    """
    if not timezone_name:
        return _fallback_utc()
    try:
        return ZoneInfo(str(timezone_name))
    except Exception as exc:  # invalid/unknown IANA name or missing tz db
        logger.warning(
            "Unknown timezone %r (%s); falling back to %s",
            timezone_name,
            exc,
            DEFAULT_TIMEZONE,
        )
        return _fallback_utc()


def parse_natural_language_datetime(text, timezone_name=None):
    """
    Parse natural language datetime expressions relative to the given
    IANA timezone (defaults to UTC). Returns a dictionary with the parsing
    results including success status, extracted timezone-aware date/time,
    and whether it's an all-day event.
    """
    original_text = text
    text = text.lower().strip()
    tzinfo_obj = resolve_timezone(timezone_name)
    now = datetime.now(tzinfo_obj)
    is_all_day = False
    day_signal_found = False

    # Check for "all day" markers using pre-compiled regex
    if _ALL_DAY_PATTERN.search(text):
        is_all_day = True

    # Day/date detection - enhanced with pre-compiled patterns
    # NOTE: "day after tomorrow" must be checked before "tomorrow", otherwise
    # the substring match claims it and the event lands one day early.
    if "day after tomorrow" in text:
        day_signal_found = True
        base_date = now + timedelta(days=2)
    elif "tomorrow" in text:
        day_signal_found = True
        base_date = now + timedelta(days=1)
    elif "today" in text:
        day_signal_found = True
        base_date = now
    else:
        matched_next_day = False
        for _, pattern, target_offset in _NEXT_WEEKDAY_PATTERNS:
            if pattern.search(text):
                day_signal_found = True
                days_ahead = (target_offset - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                base_date = now + timedelta(days=days_ahead)
                matched_next_day = True
                break

        if not matched_next_day:
            if _THIS_WEEKEND_PATTERN.search(text):
                day_signal_found = True
                days_ahead = (5 - now.weekday()) % 7
                base_date = now + timedelta(days=days_ahead)
            elif "next week" in text:
                day_signal_found = True
                base_date = now + timedelta(weeks=1)
            elif "next month" in text:
                day_signal_found = True
                base_date = now + relativedelta(months=1)
            else:
                try:
                    base_date = parser.parse(text, fuzzy=True)
                    if base_date.tzinfo is None:
                        base_date = base_date.replace(tzinfo=tzinfo_obj)
                    if _DIGIT_PATTERN.search(text) or _MONTH_PATTERN.search(
                        text
                    ):
                        day_signal_found = True
                except Exception as e:
                    logger.warning(f"Failed to parse date with dateutil: {e}")
                    base_date = now

    # Time detection with pre-compiled patterns
    time_found = False
    end_datetime = None

    for pattern in _TIME_RANGE_PATTERNS:
        match = pattern.search(text)
        if match:
            time_found = True
            groups = match.groups()

            if len(groups) == 6:
                start_hour = int(groups[0])
                start_minute = int(groups[1])
                start_ampm = groups[2]

                end_hour = int(groups[3])
                end_minute = int(groups[4])
                end_ampm = groups[5]

                if start_ampm and start_ampm.lower() == "pm" and (
                    start_hour != 12
                ):
                    start_hour += 12
                elif start_ampm and start_ampm.lower() == "am" and (
                    start_hour == 12
                ):
                    start_hour = 0

                if end_ampm and end_ampm.lower() == "pm" and end_hour != 12:
                    end_hour += 12
                elif end_ampm and end_ampm.lower() == "am" and end_hour == 12:
                    end_hour = 0

            elif len(groups) == 4:
                start_hour = int(groups[0])
                start_minute = 0
                start_ampm = groups[1]

                end_hour = int(groups[2])
                end_minute = 0
                end_ampm = groups[3]

                if start_ampm and start_ampm.lower() == "pm" and (
                    start_hour != 12
                ):
                    start_hour += 12
                elif start_ampm and start_ampm.lower() == "am" and (
                    start_hour == 12
                ):
                    start_hour = 0

                if end_ampm and end_ampm.lower() == "pm" and end_hour != 12:
                    end_hour += 12
                elif end_ampm and end_ampm.lower() == "am" and end_hour == 12:
                    end_hour = 0

            base_date = base_date.replace(
                hour=start_hour, minute=start_minute, second=0, microsecond=0
            )
            end_datetime = base_date.replace(
                hour=end_hour, minute=end_minute, second=0, microsecond=0
            )

            if end_datetime < base_date:
                end_datetime += timedelta(days=1)

            break

    if not time_found:
        for pattern in _TIME_PATTERNS:
            match = pattern.search(text)
            if match:
                time_found = True
                groups = match.groups()

                if len(groups) == 3:
                    hour = int(groups[0])
                    minute = int(groups[1])
                    ampm = groups[2]

                    if ampm and ampm.lower() == "pm" and hour != 12:
                        hour += 12
                    elif ampm and ampm.lower() == "am" and hour == 12:
                        hour = 0

                elif len(groups) == 2:
                    if groups[1] in ["am", "pm"]:
                        hour = int(groups[0])
                        minute = 0
                        ampm = groups[1]

                        if ampm.lower() == "pm" and hour != 12:
                            hour += 12
                        elif ampm.lower() == "am" and hour == 12:
                            hour = 0
                    else:
                        hour = int(groups[0])
                        minute = int(groups[1])

                base_date = base_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                end_datetime = base_date + timedelta(hours=1)
                break

    day_keywords = [
        "tomorrow",
        "today",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "next week",
        "weekend",
    ]

    if not time_found and not is_all_day:
        if any(keyword in text.lower() for keyword in day_keywords):
            is_all_day = True
            base_date = base_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_datetime = None

    if not time_found and not day_signal_found and not any(
        keyword in text.lower() for keyword in day_keywords
    ):
        err_msg = (
            f"Could not find any date or time information in: "
            f"'{original_text}'"
        )
        return {
            "success": False,
            "error": err_msg,
        }

    result = {
        "success": True,
        "is_all_day": is_all_day,
        "timezone": getattr(tzinfo_obj, "key", DEFAULT_TIMEZONE),
    }

    if is_all_day:
        result["start_date"] = base_date.date()
    else:
        result["start_datetime"] = base_date
        if end_datetime:
            result["end_datetime"] = end_datetime

    return result
