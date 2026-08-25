#book slot tool

from datetime import datetime
import httpx
from langchain_core.tools import tool
from decouple import config
from config import CALCOM_EVENT, CALCOM_KEY
from model.model import create_booking
import dateutil.parser  

@tool(description="book slot", args_schema=create_booking)
def create_slot(start_time: str, name: str, email: str, reason: str):
    if not config("CALCOM_KEY"):
        return "cal.com api is not available"
    if not config("CALCOM_EVENT"):
        return "cal.com event is not available"

    url = "https://api.cal.com/v2/bookings"

    try:
        parsed_date = dateutil.parser.parse(start_time)
        if parsed_date.tzinfo is None:
            import datetime
            timezone_kolkata = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
            parsed_date = parsed_date.replace(tzinfo=timezone_kolkata)
        formatted_start = parsed_date.isoformat()
    except Exception:
        formatted_start = start_time

    payload = {
        "eventTypeId": int(CALCOM_EVENT),
        "start": formatted_start,
        "attendee": {
            "name": name,
            "email": email,
            "timeZone": "Asia/Kolkata",
            "language": "en"
        },
        "metadata": {
            "reason": reason
        }
    }

    headers = {
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CALCOM_KEY}"
    }

    try:
        response = httpx.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        error_msg = str(e)
        if 'response' in locals() and hasattr(response, 'text'):
            error_msg += f" - Response: {response.text}"
        return {"error": f"Failed to book slot: {error_msg}"}
