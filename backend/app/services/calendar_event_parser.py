import os
import logging
import re
from datetime import datetime, timedelta, timezone
from googleapiclient.errors import HttpError

from .datetime_parser import parse_natural_language_datetime, resolve_timezone

logger = logging.getLogger(__name__)

# BOLT OPTIMIZATION: Module-level pre-compiled regexes avoid repeated compilation
# overhead on every manual event parse attempt.
_SUMMARY_MATCH_PATTERN = re.compile(
    r"(?:schedule|create|add)\s+(?:a\s+)?(.+?)"
    r"(?:\s+(?:on|at|for|from)\s+.*|$)",
    re.IGNORECASE,
)
_SUMMARY_CLEAN_PATTERN = re.compile(
    r"(?:tomorrow|today|next week|next month|at \d{1,2}(?::\d{2})?\s*"
    r"(?:am|pm)?|on \w+ \d{1,2}(?:st|nd|rd|th)?|\d{1,2}(?::\d{2})?\s*"
    r"(?:am|pm)?).*",
    re.IGNORECASE,
)


def create_event_manual_parse(conversation_text, get_calendar_service, timezone_name=None):
    """
    Manually parses conversation text to create a calendar event.
    This is a fallback if quickAdd fails.
    Returns a structured dictionary with success status and event details.

    ``timezone_name`` is the user's IANA timezone (e.g. "Asia/Kolkata");
    relative dates/times are interpreted in it and the Google payload is
    sent with a UTC-converted dateTime plus the user's timezone label.
    """
    logger.info(f"Attempting manual parse for event: {conversation_text}")
    summary = "Untitled Event"
    
    # Simple regex to find common patterns for event summary
    # Using pre-compiled regex patterns for optimal performance
    summary_match = _SUMMARY_MATCH_PATTERN.search(conversation_text)
    if summary_match:
        summary = summary_match.group(1).strip()
        # Clean up summary if it contains time/date phrases that were part of the summary extraction
        # This is a heuristic and might need further refinement based on user input patterns
        summary = _SUMMARY_CLEAN_PATTERN.sub('', summary).strip()
        if not summary: # Fallback if regex removed everything
            summary = "New Event"
    else:
        # If no clear summary found, use the whole text or a default
        summary = conversation_text.split(' for ')[0].strip() if ' for ' in conversation_text else "New Event"
        if len(summary) > 100: # Prevent very long summaries
            summary = summary[:100] + "..."

    # Try to parse date/time from the text using the enhanced function,
    # interpreted in the user's timezone.
    datetime_result = parse_natural_language_datetime(conversation_text, timezone_name)
    
    if not datetime_result.get('success', True):  # Default to True if 'success' key isn't present
        logger.warning(f"Failed to parse date/time information: {datetime_result.get('error', 'Unknown error')}")
        return {
            'success': False, 
            'error': 'Could not understand the date and time for this event',
            'message': f"❌ Could not understand when this event should be scheduled. Please try again with a clearer date and time."
        }
    
    # Create the event
    try:
        service = get_calendar_service()
        
        if datetime_result.get('is_all_day', False):
            # Create all-day event
            start_date = datetime_result.get('start_date')
            event = {
                'summary': summary,
                'start': {
                    'date': start_date.strftime('%Y-%m-%d'),
                },
                'end': {
                    'date': (start_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                },
                'description': conversation_text
            }
            
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            
            date_str = start_date.strftime('%B %d, %Y')
            
            result = {
                'success': True,
                'event': {
                    'id': created_event.get('id'),
                    'summary': summary,
                    'htmlLink': created_event.get('htmlLink', ''),
                    'date': date_str,
                    'is_all_day': True
                },
                'message': f"✅ All-day event created: '{summary}' on {date_str}"
            }
            
            return result
        else:
            # Create timed event
            start_time = datetime_result.get('start_datetime')

            # If end time is specified in the datetime_result, use it
            # Otherwise default to 1 hour after start time
            if 'end_datetime' in datetime_result:
                end_time = datetime_result.get('end_datetime')
            else:
                end_time = start_time + timedelta(hours=1)

            tz = resolve_timezone(timezone_name)
            tz_name = getattr(tz, 'key', 'UTC')

            # Guard against naive datetimes slipping through: interpret
            # them in the user's timezone rather than the server's.
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=tz)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=tz)

            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.astimezone(timezone.utc).isoformat(),
                    'timeZone': tz_name,
                },
                'end': {
                    'dateTime': end_time.astimezone(timezone.utc).isoformat(),
                    'timeZone': tz_name,
                },
                'description': conversation_text
            }
            
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            
            # Create response dictionary
            date_str = start_time.strftime('%B %d, %Y')
            start_str = start_time.strftime('%I:%M %p')
            end_str = end_time.strftime('%I:%M %p')
            
            result = {
                'success': True,
                'event': {
                    'id': created_event.get('id'),
                    'summary': summary,
                    'htmlLink': created_event.get('htmlLink', ''),
                    'date': date_str,
                    'start_time': start_str,
                    'end_time': end_str,
                    'is_all_day': False
                },
                'message': f"✅ Event created: '{summary}' on {date_str} from {start_str} to {end_str}"
            }
            
            return result
        
    except Exception as e:
        logger.error(f"Error in manual event parsing: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': f"❌ Failed to create event: {str(e)}"
        }
