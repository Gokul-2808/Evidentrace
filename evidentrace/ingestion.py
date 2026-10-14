
"""CSV loading and schema normalization for EvidenTrace."""

from io import BytesIO
from pathlib import Path

import pandas as pd


OFFICIAL_COLUMNS = {
    "event_id",
    "timestamp",
    "account",
    "computer",
    "event",
    "department_case",
}

SYNTHETIC_COLUMNS = {
    "event_id",
    "system_no",
    "ip_address",
    "roll_no",
    "department",
    "timestamp",
    "login_result",
}


def normalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Normalize supported CSV schemas to a common column structure."""
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    if OFFICIAL_COLUMNS.issubset(df.columns):
        schema = "official"
        rename_map = {}
    elif SYNTHETIC_COLUMNS.issubset(df.columns):
        schema = "synthetic"
        rename_map = {
            "system_no": "computer",
            "roll_no": "account",
            "department": "department_case",
            "login_result": "event",
        }
    else:
        # Accept partial schemas so validation can report missing columns.
        schema = "unknown"
        rename_map = {
            "system_no": "computer",
            "roll_no": "account",
            "department": "department_case",
            "login_result": "event",
        }

    df = df.rename(columns=rename_map)

    if "event" in df.columns:
        outcome_map = {
            "success": "Success",
            "successful": "Success",
            "failure": "Failure",
            "failed": "Failure",
            "fail": "Failure",
        }
        normalized = df["event"].astype("string").str.strip().str.lower()
        df["event"] = normalized.map(outcome_map).fillna(df["event"])

    return df, schema


def load_csv(source) -> tuple[pd.DataFrame, dict]:
    """Load a CSV path, bytes buffer, or uploaded file-like object."""
    try:
        if isinstance(source, (bytes, bytearray)):
            df = pd.read_csv(BytesIO(source))
        elif isinstance(source, (str, Path)):
            df = pd.read_csv(source)
        else:
            # Streamlit uploads and BytesIO objects are file-like.
            if hasattr(source, "seek"):
                source.seek(0)
            df = pd.read_csv(source)

        df, schema = normalize_columns(df)

        report = {
            "schema": schema,
            "rows_read": len(df),
            "columns_found": list(df.columns),
            "notes": [],
        }

        if schema == "unknown":
            report["notes"].append(
                "The CSV does not match either complete supported schema. "
                "Validation will identify missing required columns."
            )

        return df, report

    except pd.errors.EmptyDataError:
        return pd.DataFrame(), {
            "schema": "unknown",
            "rows_read": 0,
            "columns_found": [],
            "notes": ["The CSV file is empty or has no header."],
        }
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read CSV: {exc}") from exc
