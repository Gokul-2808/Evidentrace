
import pandas as pd

from evidentrace.validation import validate, get_valid_df


# ---------------------------------------------------------
# Helper: create a standard login record
# ---------------------------------------------------------

def make_row(
    event_id="E1",
    timestamp="2026-10-12 10:00:00",
    account="USER01",
    event="Success",
):
    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "account": account,
        "computer": "LAB01",
        "event": event,
        "ip_address": "192.168.10.10",
        "department_case": "CSE",
    }


# ---------------------------------------------------------
# Test 1: Valid row is retained
# ---------------------------------------------------------

def test_valid_row_is_retained():
    df = pd.DataFrame([make_row()])

    valid = get_valid_df(df)

    assert len(valid) == 1
    assert valid.iloc[0]["event_id"] == "E1"


# ---------------------------------------------------------
# Test 2: Missing account is excluded
# ---------------------------------------------------------

def test_missing_account_is_excluded():
    df = pd.DataFrame([
        make_row(account=None)
    ])

    valid = get_valid_df(df)

    assert valid.empty


# ---------------------------------------------------------
# Test 3: Missing timestamp is reported
# ---------------------------------------------------------

def test_missing_timestamp_is_reported():
    df = pd.DataFrame([
        make_row(timestamp=None)
    ])

    report = validate(df)

    assert report["missing_timestamps"] == 1


# ---------------------------------------------------------
# Test 4: Invalid timestamp is reported
# ---------------------------------------------------------

def test_invalid_timestamp_is_reported():
    df = pd.DataFrame([
        make_row(timestamp="not-a-date")
    ])

    report = validate(df)

    assert report["invalid_timestamps"] == 1


# ---------------------------------------------------------
# Test 5: Unknown login outcome is reported
# ---------------------------------------------------------

def test_unknown_outcome_is_reported():
    df = pd.DataFrame([
        make_row(event="Unknown")
    ])

    report = validate(df)

    assert report["unknown_outcomes"] == 1


# ---------------------------------------------------------
# Test 6: Duplicate event IDs are reported
# ---------------------------------------------------------

def test_duplicate_event_ids_are_reported():
    df = pd.DataFrame([
        make_row(event_id="E1"),
        make_row(
            event_id="E1",
            timestamp="2026-10-12 10:01:00",
        ),
    ])

    report = validate(df)

    # Current validator counts both rows involved
    # when an event ID occurs more than once.
    assert report["duplicate_event_ids"] == 2


# ---------------------------------------------------------
# Test 7: Valid rows are sorted by timestamp
# ---------------------------------------------------------

def test_valid_rows_are_sorted_by_timestamp():
    df = pd.DataFrame([
        make_row(
            event_id="E2",
            timestamp="2026-10-12 10:02:00",
        ),
        make_row(
            event_id="E1",
            timestamp="2026-10-12 10:00:00",
        ),
    ])

    valid = get_valid_df(df)

    timestamps = pd.to_datetime(valid["timestamp"])

    assert timestamps.is_monotonic_increasing
    assert valid.iloc[0]["event_id"] == "E1"


# ---------------------------------------------------------
# Test 8: Empty dataframe has zero rows
# ---------------------------------------------------------

def test_empty_dataframe_has_zero_rows():
    report = validate(pd.DataFrame())

    assert report["total_rows"] == 0
    assert report["valid_rows"] == 0
