
"""Data validation for EvidenTrace login-event records."""

import ipaddress

import pandas as pd


REQUIRED_COLUMNS = [
    "event_id",
    "timestamp",
    "account",
    "computer",
    "event",
]

VALID_OUTCOMES = {"Success", "Failure"}


def validate(df: pd.DataFrame) -> dict:
    """Return a data-quality report without modifying the input."""
    df = df.copy()
    issues = []

    def add_issue(issue_type, description, count=1):
        issues.append({
            "type": issue_type,
            "description": description,
            "count": int(count),
        })

    if df.empty:
        add_issue("empty_csv", "The dataset contains no rows.", 0)

    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]

    if missing_columns:
        add_issue(
            "missing_columns",
            "Missing required columns: " + ", ".join(missing_columns),
            len(missing_columns),
        )

    if "event_id" in df.columns:
        missing_ids = df["event_id"].isna() | (
            df["event_id"].astype("string").str.strip() == ""
        )
        if missing_ids.any():
            add_issue(
                "missing_event_id",
                "Some rows do not have an event ID.",
                missing_ids.sum(),
            )

        duplicate_ids = (
            df["event_id"].notna()
            & df["event_id"].duplicated(keep=False)
        )
        duplicate_count = int(duplicate_ids.sum())

        if duplicate_count:
            add_issue(
                "duplicate_event_ids",
                "Duplicate event IDs were found. All rows sharing a "
                "duplicate ID are flagged.",
                duplicate_count,
            )
    else:
        duplicate_count = 0

    if "timestamp" in df.columns:
        original_ts = df["timestamp"]
        missing_ts = original_ts.isna() | (
            original_ts.astype("string").str.strip() == ""
        )
        parsed_ts = pd.to_datetime(original_ts, errors="coerce")

        invalid_ts = ~missing_ts & parsed_ts.isna()

        if missing_ts.any():
            add_issue(
                "missing_timestamp",
                "Some rows have missing timestamps.",
                missing_ts.sum(),
            )

        if invalid_ts.any():
            add_issue(
                "invalid_timestamp_format",
                "Some timestamps could not be parsed.",
                invalid_ts.sum(),
            )

        df["timestamp"] = parsed_ts
        missing_timestamp_count = int(missing_ts.sum())
        invalid_timestamp_count = int(invalid_ts.sum())
    else:
        missing_timestamp_count = 0
        invalid_timestamp_count = 0

    if "event" in df.columns:
        normalized_outcomes = (
            df["event"].astype("string").str.strip().str.lower()
        )
        unknown = (
            df["event"].notna()
            & ~normalized_outcomes.isin(
                {"success", "failure", "successful", "failed", "fail"}
            )
        )

        if unknown.any():
            add_issue(
                "unknown_login_outcome",
                "Some login outcomes are not recognized as Success "
                "or Failure.",
                unknown.sum(),
            )

        missing_outcomes = df["event"].isna() | (
            df["event"].astype("string").str.strip() == ""
        )

        if missing_outcomes.any():
            add_issue(
                "unknown_login_outcome",
                "Some rows have missing login outcomes.",
                missing_outcomes.sum(),
            )

        normalized_map = {
            "success": "Success",
            "successful": "Success",
            "failure": "Failure",
            "failed": "Failure",
            "fail": "Failure",
        }
        df["event"] = normalized_outcomes.map(normalized_map)

        unknown_outcome_count = int(
            (unknown | missing_outcomes).sum()
        )
    else:
        unknown_outcome_count = 0

    invalid_ip_count = 0

    if "ip_address" in df.columns:
        def is_invalid_ip(value):
            if pd.isna(value) or not str(value).strip():
                return False
            try:
                ipaddress.ip_address(str(value).strip())
                return False
            except ValueError:
                return True

        invalid_ip_mask = df["ip_address"].apply(is_invalid_ip)
        invalid_ip_count = int(invalid_ip_mask.sum())

        if invalid_ip_count:
            add_issue(
                "invalid_ip_address",
                "Some non-empty IP addresses are invalid.",
                invalid_ip_count,
            )

    # Required identifiers for detection must be present.
    missing_identity_count = 0

    for col in ("account", "computer"):
        if col in df.columns:
            missing_identity = df[col].isna() | (
                df[col].astype("string").str.strip() == ""
            )
            missing_identity_count += int(missing_identity.sum())

    # Rows are usable only when required columns and values are valid.
    valid_mask = pd.Series(True, index=df.index)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            valid_mask[:] = False
            break

    if all(col in df.columns for col in REQUIRED_COLUMNS):
        valid_mask &= df["event_id"].notna()
        valid_mask &= df["event_id"].astype("string").str.strip().ne("")
        valid_mask &= df["account"].notna()
        valid_mask &= df["account"].astype("string").str.strip().ne("")
        valid_mask &= df["computer"].notna()
        valid_mask &= df["computer"].astype("string").str.strip().ne("")
        valid_mask &= df["timestamp"].notna()
        valid_mask &= df["event"].isin(VALID_OUTCOMES)

    valid_rows = int(valid_mask.sum())
    invalid_rows = int(len(df) - valid_rows)

    return {
        "total_rows": int(len(df)),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "duplicate_event_ids": duplicate_count,
        "missing_timestamps": missing_timestamp_count,
        "invalid_timestamps": invalid_timestamp_count,
        "unknown_outcomes": unknown_outcome_count,
        "invalid_ip_addresses": invalid_ip_count,
        "missing_identity_values": missing_identity_count,
        "missing_columns": missing_columns,
        "issues": issues,
    }


def get_valid_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return normalized rows suitable for the detection engine."""
    df = df.copy()

    if df.empty or any(
        col not in df.columns for col in REQUIRED_COLUMNS
    ):
        return pd.DataFrame(columns=df.columns)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce"
    )

    df["event_id"] = df["event_id"].astype("string").str.strip()
    df["account"] = df["account"].astype("string").str.strip()
    df["computer"] = df["computer"].astype("string").str.strip()

    outcome_map = {
        "success": "Success",
        "successful": "Success",
        "failure": "Failure",
        "failed": "Failure",
        "fail": "Failure",
    }

    normalized = df["event"].astype("string").str.strip().str.lower()
    df["event"] = normalized.map(outcome_map)

    mask = (
        df["event_id"].notna()
        & df["event_id"].ne("")
        & df["account"].notna()
        & df["account"].ne("")
        & df["computer"].notna()
        & df["computer"].ne("")
        & df["timestamp"].notna()
        & df["event"].isin(VALID_OUTCOMES)
    )

    if "ip_address" in df.columns:
        # Invalid IP addresses are reported separately. They do not
        # invalidate otherwise usable login records.
        pass

    return (
        df.loc[mask]
        .sort_values("timestamp", kind="stable")
        .reset_index(drop=True)
    )
