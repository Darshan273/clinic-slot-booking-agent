import httpx
from config import CALCOM_EVENT, CALCOM_KEY
from langchain_core.tools import tool
from model.model import check_availability as CheckAvailabilitySchema
from decouple import config
from datetime import datetime, time, timedelta, timezone
import dateutil.parser


CLINIC_TIMEZONE = "Asia/Kolkata"
CLINIC_TZINFO = timezone(timedelta(hours=5, minutes=30))


def _clinic_day_window(date: str) -> tuple[str, str, str]:
    """Return the local Cal.com query window for a clinic date."""
    try:
        parsed = dateutil.parser.parse(date)
    except Exception:
        parsed = datetime.now(CLINIC_TZINFO)

    clinic_date = parsed.date()
    start = datetime.combine(clinic_date, time.min, tzinfo=CLINIC_TZINFO)
    end = start + timedelta(days=1)
    return clinic_date.isoformat(), start.isoformat(), end.isoformat()


def _collect_slot_starts(value):
    starts = []

    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"time", "start", "startTime"} and isinstance(nested, str):
                starts.append(nested)
            else:
                starts.extend(_collect_slot_starts(nested))
        return starts

    if isinstance(value, list):
        for item in value:
            starts.extend(_collect_slot_starts(item))

    return starts


def _format_slots(response_json: dict, clean_date: str) -> dict:
    slots = []
    for slot_start in _collect_slot_starts(response_json):
        try:
            parsed = dateutil.parser.parse(slot_start)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=CLINIC_TZINFO)
            local_start = parsed.astimezone(CLINIC_TZINFO)
        except Exception:
            continue

        if local_start.date().isoformat() == clean_date:
            slots.append(local_start.strftime("%Y-%m-%d %I:%M %p"))

    unique_slots = sorted(set(slots), key=lambda item: datetime.strptime(item, "%Y-%m-%d %I:%M %p"))
    return {
        "date": clean_date,
        "timeZone": CLINIC_TIMEZONE,
        "available": bool(unique_slots),
        "available_slots": unique_slots,
        "message": (
            f"Available slots on {clean_date}: {', '.join(unique_slots)}"
            if unique_slots
            else f"No available slots on {clean_date}."
        ),
    }

@tool(description="check availability of a slot", args_schema=CheckAvailabilitySchema)
def check_availability(date: str):
    if not config("CALCOM_KEY"):
        return "cal.com api is not available"
    if not config("CALCOM_EVENT"):
        return "cal.com event is not available"
  
    url = "https://api.cal.com/v2/slots"

    clean_date, start_time, end_time = _clinic_day_window(date)

    params = {
        "eventTypeId": str(CALCOM_EVENT),
        "timeZone": CLINIC_TIMEZONE,
        "start": start_time,    
        "end": end_time,
    }

    headers = {
        "cal-api-version": "2024-09-04",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CALCOM_KEY}"
    }

    try:
        response = httpx.get(url, params=params, headers=headers)
        response.raise_for_status()
        return _format_slots(response.json(), clean_date)
    except Exception as e:
        error_msg = str(e)
        if 'response' in locals() and hasattr(response, 'text'):
            error_msg += f" - Response: {response.text}"
        return {"error": f"Failed to check availability: {error_msg}"}
        
