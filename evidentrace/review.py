
"""Human review workflow for EvidenTrace alerts."""

VALID_STATUSES = [
    "Open",
    "Under Review",
    "Resolved",
    "False Positive",
]


def update_review_status(
    alerts: list[dict],
    alert_id: str,
    new_status: str,
) -> list[dict]:
    """Update an alert's review status without changing other alerts."""
    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid review status: {new_status}. "
            f"Choose one of {VALID_STATUSES}."
        )

    updated_alerts = []

    for alert in alerts:
        updated = alert.copy()

        if updated.get("alert_id") == alert_id:
            updated["review_status"] = new_status

        updated_alerts.append(updated)

    return updated_alerts
