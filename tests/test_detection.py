
import pandas as pd

from evidentrace.validation import get_valid_df
from evidentrace.detection import run_all_rules


def make_event(event_id, timestamp, event, account="USER01",
               computer="LAB01", ip_address="192.168.10.10"):
    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "account": account,
        "computer": computer,
        "event": event,
        "ip_address": ip_address,
        "department_case": "CSE",
    }


def settings(**overrides):
    result = {
        "min_failures": 3,
        "window_minutes": 10,
        "require_success": True,
        "consecutive": False,
        "open_time": pd.Timestamp("08:00").time(),
        "close_time": pd.Timestamp("18:00").time(),
        "permitted_weekdays": [0, 1, 2, 3, 4],
        "holidays": [],
        "timezone": "Asia/Kolkata",
        "enable_ip_rule": True,
        "approved_network": "192.168.10.0/24",
    }
    result.update(overrides)
    return result


def detect(rows, **overrides):
    valid = get_valid_df(pd.DataFrame(rows))
    return run_all_rules(valid, settings(**overrides))


def repeated_failures():
    return [
        make_event("E1", "2026-10-12 10:00:00", "Failure"),
        make_event("E2", "2026-10-12 10:01:00", "Failure"),
        make_event("E3", "2026-10-12 10:02:00", "Failure"),
        make_event("E4", "2026-10-12 10:03:00", "Success"),
    ]


def rule_alerts(alerts, text):
    return [
        a for a in alerts
        if text.lower() in str(a.get("rule_label", "")).lower()
    ]


def test_repeated_failures_generate_alert():
    alerts = detect(repeated_failures())
    assert rule_alerts(alerts, "Repeated Failures")


def test_single_failure_does_not_generate_repeated_failure_alert():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", "Failure"),
        make_event("E2", "2026-10-12 10:01:00", "Success"),
    ]
    alerts = detect(rows)
    assert not rule_alerts(alerts, "Repeated Failures")


def test_successful_login_after_lab_hours_is_detected():
    rows = [
        make_event("E1", "2026-10-12 20:00:00", "Success")
    ]
    alerts = detect(rows)
    assert rule_alerts(alerts, "Outside Lab Hours")


def test_success_inside_lab_hours_is_not_after_hours():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", "Success")
    ]
    alerts = detect(rows)
    assert not rule_alerts(alerts, "Outside Lab Hours")


def test_ip_outside_approved_network_is_detected():
    rows = [
        make_event(
            "E1", "2026-10-12 10:00:00", "Success",
            ip_address="203.0.113.25",
        )
    ]
    alerts = detect(rows)
    assert rule_alerts(alerts, "Outside Approved Lab Network")


def test_ip_inside_approved_network_is_not_flagged():
    rows = [
        make_event(
            "E1", "2026-10-12 10:00:00", "Success",
            ip_address="192.168.10.25",
        )
    ]
    alerts = detect(rows)
    assert not rule_alerts(alerts, "Outside Approved Lab Network")


def test_alert_contains_evidence_event_ids():
    alerts = detect(repeated_failures())
    repeated = rule_alerts(alerts, "Repeated Failures")

    assert repeated
    assert set(repeated[0]["event_ids"]) == {"E1", "E2", "E3", "E4"}


def test_detection_is_independent_of_department():
    original = repeated_failures()
    changed = [
        {**row, "department_case": "Physics"}
        for row in original
    ]

    first = detect(original)
    second = detect(changed)

    def signature(alerts):
        return sorted(
            (
                a.get("rule_label"),
                a.get("priority"),
                a.get("account"),
                tuple(a.get("event_ids", [])),
            )
            for a in alerts
        )

    assert signature(first) == signature(second)
