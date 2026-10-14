
"""Evidence timeline generation for EvidenTrace."""

import pandas as pd


def build_timeline(alert: dict) -> list[dict]:
    """Build a readable timeline from the alert's supporting event IDs.

    The detection engine places actual supporting event IDs in each alert.
    This function creates a timeline from the evidence stored in the alert.
    """
    event_ids = alert.get("event_ids", [])

    if not event_ids:
        return []

    timestamps = alert.get("evidence_timestamps", [])
    outcomes = alert.get("evidence_outcomes", [])

    timeline = []

    for index, event_id in enumerate(event_ids):
        timestamp = (
            timestamps[index]
            if index < len(timestamps)
            else None
        )
        outcome = (
            outcomes[index]
            if index < len(outcomes)
            else "Supporting event"
        )

        timeline.append({
            "Event ID": str(event_id),
            "Timestamp": (
                str(timestamp) if timestamp is not None else "See login records"
            ),
            "Event": str(outcome),
            "Evidence": (
                "This event contributed to the detection rule."
            ),
        })

    return timeline
