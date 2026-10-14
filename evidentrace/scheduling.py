
"""Lab schedule utilities for EvidenTrace."""

from datetime import time


def format_schedule_description(settings: dict) -> str:
    """Return a readable description of permitted lab days and hours."""
    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    permitted = settings.get("permitted_weekdays", [0, 1, 2, 3, 4])
    day_labels = [
        weekdays[day]
        for day in permitted
        if isinstance(day, int) and 0 <= day < 7
    ]

    open_time = settings.get("open_time", time(8, 0))
    close_time = settings.get("close_time", time(18, 0))
    timezone = settings.get("timezone", "UTC")
    holidays = settings.get("holidays", [])

    if not day_labels:
        days_text = "No permitted weekdays"
    else:
        days_text = ", ".join(day_labels)

    if open_time == close_time:
        hours_text = "No permitted hours"
    elif open_time < close_time:
        hours_text = f"{open_time.strftime('%H:%M')}–{close_time.strftime('%H:%M')}"
    else:
        hours_text = (
            f"{open_time.strftime('%H:%M')}–"
            f"{close_time.strftime('%H:%M')} (overnight)"
        )

    return (
        f"{days_text}; {hours_text}; timezone {timezone}; "
        f"{len(holidays)} holiday(s) configured"
    )
