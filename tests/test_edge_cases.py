
from datetime import time

import pandas as pd
import pytest

from evidentrace.ingestion import load_csv
from evidentrace.validation import validate, get_valid_df
from evidentrace.detection import run_all_rules


# ---------------------------------------------------------
# Shared test data and settings
# ---------------------------------------------------------

def make_event(event_id, timestamp, account="USER01",
               computer="LAB01", event="Success",
               ip_address="192.168.10.10",
               department_case="CSE"):

    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "account": account,
        "computer": computer,
        "event": event,
        "ip_address": ip_address,
        "department_case": department_case,
    }


def make_settings(**overrides):
    settings = {
        "min_failures": 3,
        "window_minutes": 10,
        "require_success": True,
        "consecutive": False,
        "open_time": time(8, 0),
        "close_time": time(18, 0),
        "permitted_weekdays": [0, 1, 2, 3, 4],
        "holidays": [],
        "timezone": "Asia/Kolkata",
        "enable_ip_rule": True,
        "approved_network": "192.168.10.0/24",
    }
    settings.update(overrides)
    return settings


def run_detection(rows, **settings_overrides):
    df = pd.DataFrame(rows)
    valid = get_valid_df(df)
    alerts = run_all_rules(valid, make_settings(**settings_overrides))
    return valid, alerts


def repeated_failure_sequence(start="2026-10-12 10:00:00"):
    times = pd.date_range(start=start, periods=4, freq="2min")
    return [
        make_event("E1", str(times[0]), event="Failure"),
        make_event("E2", str(times[1]), event="Failure"),
        make_event("E3", str(times[2]), event="Failure"),
        make_event("E4", str(times[3]), event="Success"),
    ]


def repeated_failure_alerts(alerts):
    return [
        alert for alert in alerts
        if "Repeated Failures" in str(alert.get("rule_label", ""))
    ]


# =========================================================
# 1. EMPTY CSV
# =========================================================

def test_01_empty_csv():
    df = pd.DataFrame()
    report = validate(df)

    assert report["total_rows"] == 0
    assert report["valid_rows"] == 0


# =========================================================
# 2. MISSING REQUIRED COLUMNS
# =========================================================

def test_02_missing_required_columns():
    df = pd.DataFrame({
        "event_id": ["E1"],
        "timestamp": ["2026-10-12 10:00:00"],
    })

    report = validate(df)

    assert report["valid_rows"] == 0
    assert report["missing_columns"]


# =========================================================
# 3. MISSING ACCOUNT
# =========================================================

def test_03_missing_account():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", account=None)
    ]

    valid, _ = run_detection(rows)

    assert valid.empty


# =========================================================
# 4. MISSING TIMESTAMP
# =========================================================

def test_04_missing_timestamp():
    df = pd.DataFrame([
        make_event("E1", None)
    ])

    report = validate(df)

    assert report["missing_timestamps"] >= 1


# =========================================================
# 5. INVALID TIMESTAMP
# =========================================================

def test_05_invalid_timestamp():
    df = pd.DataFrame([
        make_event("E1", "not-a-valid-date")
    ])

    report = validate(df)

    assert report["invalid_timestamps"] >= 1


# =========================================================
# 6. UNKNOWN LOGIN OUTCOME
# =========================================================

def test_06_unknown_login_outcome():
    df = pd.DataFrame([
        make_event("E1", "2026-10-12 10:00:00", event="Unknown")
    ])

    report = validate(df)

    assert report["unknown_outcomes"] >= 1


# =========================================================
# 7. UNSORTED ROWS
# =========================================================

def test_07_unsorted_rows():
    rows = repeated_failure_sequence()
    rows.reverse()

    valid, alerts = run_detection(rows)

    timestamps = pd.to_datetime(valid["timestamp"])

    assert timestamps.is_monotonic_increasing
    assert repeated_failure_alerts(alerts)


# =========================================================
# 8. DUPLICATE EVENT IDS
# =========================================================

def test_08_duplicate_event_ids():
    df = pd.DataFrame([
        make_event("E1", "2026-10-12 10:00:00"),
        make_event("E1", "2026-10-12 10:01:00"),
    ])

    report = validate(df)

    assert report["duplicate_event_ids"] >= 1


# =========================================================
# 9. FAILURES BELOW THRESHOLD
# =========================================================

def test_09_failures_below_threshold():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", event="Failure"),
        make_event("E2", "2026-10-12 10:01:00", event="Failure"),
        make_event("E3", "2026-10-12 10:02:00", event="Success"),
    ]

    _, alerts = run_detection(rows)

    assert not repeated_failure_alerts(alerts)


# =========================================================
# 10. FAILURES EXACTLY AT THRESHOLD
# =========================================================

def test_10_failures_exactly_at_threshold():
    _, alerts = run_detection(repeated_failure_sequence())

    assert repeated_failure_alerts(alerts)


# =========================================================
# 11. SUCCESS WITHOUT PREVIOUS FAILURES
# =========================================================

def test_11_success_without_failures():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", event="Success")
    ]

    _, alerts = run_detection(rows)

    assert not repeated_failure_alerts(alerts)


# =========================================================
# 12. FAILURES WITHOUT SUBSEQUENT SUCCESS
# =========================================================

def test_12_failures_without_success():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", event="Failure"),
        make_event("E2", "2026-10-12 10:01:00", event="Failure"),
        make_event("E3", "2026-10-12 10:02:00", event="Failure"),
    ]

    _, alerts = run_detection(rows)

    assert not repeated_failure_alerts(alerts)


# =========================================================
# 13. SUCCESS OUTSIDE THE TIME WINDOW
# =========================================================

def test_13_success_outside_window():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", event="Failure"),
        make_event("E2", "2026-10-12 10:01:00", event="Failure"),
        make_event("E3", "2026-10-12 10:02:00", event="Failure"),
        make_event("E4", "2026-10-12 10:20:00", event="Success"),
    ]

    _, alerts = run_detection(rows)

    assert not repeated_failure_alerts(alerts)


# =========================================================
# 14. SUCCESS EXACTLY AT WINDOW BOUNDARY
# =========================================================

def test_14_success_at_window_boundary():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", event="Failure"),
        make_event("E2", "2026-10-12 10:05:00", event="Failure"),
        make_event("E3", "2026-10-12 10:10:00", event="Failure"),
        make_event("E4", "2026-10-12 10:10:00", event="Success"),
    ]

    _, alerts = run_detection(rows, window_minutes=10)

    assert repeated_failure_alerts(alerts)


# =========================================================
# 15. SEQUENCE CROSSING MIDNIGHT
# =========================================================

def test_15_sequence_crossing_midnight():
    rows = [
        make_event("E1", "2026-10-12 23:50:00", event="Failure"),
        make_event("E2", "2026-10-12 23:53:00", event="Failure"),
        make_event("E3", "2026-10-12 23:56:00", event="Failure"),
        make_event("E4", "2026-10-13 00:00:00", event="Success"),
    ]

    _, alerts = run_detection(rows, window_minutes=15)

    assert repeated_failure_alerts(alerts)


# =========================================================
# 16. NEW SEQUENCE AFTER SUCCESS
# =========================================================

def test_16_new_sequence_after_success():
    rows = [
        make_event("E1", "2026-10-12 10:00:00", event="Failure"),
        make_event("E2", "2026-10-12 10:01:00", event="Failure"),
        make_event("E3", "2026-10-12 10:02:00", event="Failure"),
        make_event("E4", "2026-10-12 10:03:00", event="Success"),
        make_event("E5", "2026-10-12 10:04:00", event="Failure"),
        make_event("E6", "2026-10-12 10:05:00", event="Failure"),
        make_event("E7", "2026-10-12 10:06:00", event="Failure"),
        make_event("E8", "2026-10-12 10:07:00", event="Success"),
    ]

    _, alerts = run_detection(rows)

    assert len(repeated_failure_alerts(alerts)) == 2


# =========================================================
# 17. LOGIN EXACTLY AT OPENING TIME
# =========================================================

def test_17_login_at_opening_time():
    rows = [
        make_event("E1", "2026-10-12 08:00:00", event="Success")
    ]

    _, alerts = run_detection(rows)

    after_hours = [
        a for a in alerts
        if "Outside Lab Hours" in str(a.get("rule_label", ""))
    ]

    assert not after_hours


# =========================================================
# 18. LOGIN EXACTLY AT CLOSING TIME
# =========================================================

def test_18_login_at_closing_time():
    rows = [
        make_event("E1", "2026-10-12 18:00:00", event="Success")
    ]

    _, alerts = run_detection(rows)

    after_hours = [
        a for a in alerts
        if "Outside Lab Hours" in str(a.get("rule_label", ""))
    ]

    # Closing time is treated as outside permitted hours.
    assert after_hours


# =========================================================
# 19. WEEKEND AND HOLIDAY
# =========================================================

def test_19_weekend_and_holiday():
    rows = [
        make_event("E1", "2026-10-10 10:00:00", event="Success"),
        make_event("E2", "2026-10-12 10:00:00", event="Success"),
    ]

    _, alerts = run_detection(
        rows,
        holidays=["2026-10-12"],
    )

    after_hours = [
        a for a in alerts
        if "Outside Lab Hours" in str(a.get("rule_label", ""))
    ]

    # Saturday is outside permitted weekdays; Monday is a configured holiday.
    assert len(after_hours) >= 2


# =========================================================
# 20. OVERNIGHT LAB SCHEDULE
# =========================================================

def test_20_overnight_schedule():
    rows = [
        make_event("E1", "2026-10-12 23:00:00", event="Success"),
        make_event("E2", "2026-10-13 02:00:00", event="Success"),
    ]

    _, alerts = run_detection(
        rows,
        open_time=time(22, 0),
        close_time=time(6, 0),
    )

    after_hours = [
        a for a in alerts
        if "Outside Lab Hours" in str(a.get("rule_label", ""))
    ]

    # Both times fall within the overnight time window.
    assert not after_hours


# =========================================================
# 21. IP ADDRESS AT CIDR BOUNDARIES
# =========================================================

def test_21_ip_network_boundaries():
    rows = [
        make_event(
            "E1", "2026-10-12 10:00:00",
            ip_address="192.168.10.0",
        ),
        make_event(
            "E2", "2026-10-12 10:01:00",
            ip_address="192.168.10.255",
        ),
    ]

    _, alerts = run_detection(rows)

    outside_network = [
        a for a in alerts
        if "Outside Approved Lab Network"
        in str(a.get("rule_label", ""))
    ]

    # Both are inside the /24 network as represented by CIDR.
    # Network and broadcast addresses are not host-usable addresses,
    # but are still within the CIDR range.
    assert not outside_network


# =========================================================
# 22. IP ADDRESS OUTSIDE APPROVED NETWORK
# =========================================================

def test_22_ip_outside_approved_network():
    rows = [
        make_event(
            "E1", "2026-10-12 10:00:00",
            ip_address="203.0.113.25",
        )
    ]

    _, alerts = run_detection(rows)

    outside_network = [
        a for a in alerts
        if "Outside Approved Lab Network"
        in str(a.get("rule_label", ""))
    ]

    assert outside_network


# =========================================================
# 23. DEPARTMENT MUST NOT CHANGE DETECTION
# =========================================================

def test_23_department_does_not_change_detection():
    original = repeated_failure_sequence()

    changed_department = [
        {**row, "department_case": "Physics"}
        for row in original
    ]

    _, alerts_cse = run_detection(original)
    _, alerts_physics = run_detection(changed_department)

    def signature(alerts):
        return sorted(
            (
                alert.get("rule"),
                alert.get("rule_label"),
                alert.get("priority"),
                alert.get("account"),
                tuple(alert.get("event_ids", [])),
            )
            for alert in alerts
        )

    assert signature(alerts_cse) == signature(alerts_physics)
