
"""Explainable security detection rules for EvidenTrace."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import ipaddress

import pandas as pd


def _parse_timestamp(value, timezone_name="UTC"):
    """Convert a timestamp into the configured timezone."""
    ts = pd.Timestamp(value)

    if pd.isna(ts):
        return None

    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")

    if ts.tzinfo is None:
        return ts.tz_localize(tz)

    return ts.tz_convert(tz)


def _in_permitted_hours(ts, settings):
    """Return whether a timestamp is inside permitted lab hours."""
    open_time = settings.get("open_time", time(8, 0))
    close_time = settings.get("close_time", time(18, 0))
    permitted_days = settings.get("permitted_weekdays", [0, 1, 2, 3, 4])
    holidays = set(settings.get("holidays", []))

    day = ts.dayofweek
    date_string = ts.date().isoformat()
    current_time = ts.time().replace(tzinfo=None)

    if date_string in holidays:
        return False

    # A normal schedule, such as 08:00–18:00.
    if open_time < close_time:
        return (
            day in permitted_days
            and open_time <= current_time < close_time
        )

    # Overnight schedule, such as 20:00–06:00.
    if open_time > close_time:
        if current_time >= open_time:
            return day in permitted_days
        if current_time < close_time:
            previous_day = (day - 1) % 7
            previous_date = (ts.date() - timedelta(days=1)).isoformat()
            return (
                previous_day in permitted_days
                and previous_date not in holidays
            )

    # Equal opening and closing times are treated as no permitted hours.
    return False


def _base_alert(alert_id, rule, rule_label, priority, account, computer,
                ts_start, ts_end, event_ids, explanation,
                verification_step, priority_rationale):
    """Create a consistent alert dictionary for the interface."""
    elapsed = ts_end - ts_start

    return {
        "alert_id": alert_id,
        "rule": rule,
        "rule_label": rule_label,
        "priority": priority,
        "account": account,
        "computer": computer,
        "ts_start": ts_start,
        "ts_end": ts_end,
        "elapsed": str(elapsed),
        "event_ids": event_ids,
        "explanation": explanation,
        "verification_step": verification_step,
        "priority_rationale": priority_rationale,
        "review_status": "Open",
    }


def detect_repeated_failures(df, settings):
    """Detect repeated failures followed by success within a time window."""
    if df is None or df.empty:
        return []

    min_failures = int(settings.get("min_failures", 3))
    window_minutes = int(settings.get("window_minutes", 10))
    require_success = bool(settings.get("require_success", True))
    consecutive = bool(settings.get("consecutive", False))
    timezone_name = settings.get("timezone", "UTC")

    work = df.copy()

    required = {"timestamp", "event", "account", "computer", "event_id"}
    if not required.issubset(work.columns):
        return []

    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    work = work.dropna(subset=["timestamp", "account", "computer", "event"])
    work = work.sort_values("timestamp", kind="stable")

    alerts = []
    sequence_number = 1

    for (account, computer), group in work.groupby(
        ["account", "computer"], dropna=True, sort=False
    ):
        group = group.reset_index(drop=True)

        failures = []

        for _, row in group.iterrows():
            event = str(row["event"]).strip().lower()
            ts = _parse_timestamp(row["timestamp"], timezone_name)

            if ts is None:
                continue

            if event == "failure":
                failures.append(row)

                # Keep only failures inside the active detection window.
                cutoff = ts - pd.Timedelta(minutes=window_minutes)
                failures = [
                    f for f in failures
                    if _parse_timestamp(f["timestamp"], timezone_name) >= cutoff
                ]

            elif event == "success":
                if len(failures) >= min_failures:
                    first_ts = _parse_timestamp(
                        failures[0]["timestamp"], timezone_name
                    )
                    last_failure_ts = _parse_timestamp(
                        failures[-1]["timestamp"], timezone_name
                    )

                    if (
                        ts - first_ts <= pd.Timedelta(minutes=window_minutes)
                        and (not consecutive or len(failures) == min_failures)
                    ):
                        failure_rows = failures[-min_failures:]
                        event_ids = [
                            str(f["event_id"]) for f in failure_rows
                        ] + [str(row["event_id"])]

                        priority = (
                            "High" if len(failures) >= min_failures + 2
                            else "Medium"
                        )

                        alerts.append(_base_alert(
                            alert_id=f"ET-RF-{sequence_number:04d}",
                            rule="repeated_failures",
                            rule_label="Repeated Failures → Success",
                            priority=priority,
                            account=str(account),
                            computer=str(computer),
                            ts_start=first_ts,
                            ts_end=ts,
                            event_ids=event_ids,
                            explanation=(
                                f"{len(failures)} failed login attempt(s) "
                                f"were observed before a successful login "
                                f"for account {account} on computer "
                                f"{computer}, within {window_minutes} "
                                f"minutes. This is a review signal, not "
                                f"proof of unauthorized access."
                            ),
                            verification_step=(
                                "Confirm the account owner, verify whether "
                                "the failed attempts were expected, and "
                                "check the associated lab access records."
                            ),
                            priority_rationale=(
                                "High priority reflects a greater number "
                                "of failed attempts; it is not a finding "
                                "of confirmed compromise."
                            ),
                        ))

                        sequence_number += 1

                # A success ends the preceding failure sequence.
                failures = []

    return alerts


def detect_after_hours(df, settings):
    """Flag successful logins outside configured lab hours."""
    if df is None or df.empty:
        return []

    required = {"timestamp", "event", "account", "computer", "event_id"}
    if not required.issubset(df.columns):
        return []

    timezone_name = settings.get("timezone", "UTC")
    work = df.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    work = work.dropna(subset=["timestamp", "event"])

    alerts = []

    for _, row in work.iterrows():
        if str(row["event"]).strip().lower() != "success":
            continue

        ts = _parse_timestamp(row["timestamp"], timezone_name)

        if ts is None or _in_permitted_hours(ts, settings):
            continue

        local_ts = ts
        alert_id = f"ET-AH-{len(alerts) + 1:04d}"

        alerts.append(_base_alert(
            alert_id=alert_id,
            rule="after_hours",
            rule_label="Successful Login Outside Lab Hours",
            priority="Medium",
            account=str(row["account"]),
            computer=str(row["computer"]),
            ts_start=local_ts,
            ts_end=local_ts,
            event_ids=[str(row["event_id"])],
            explanation=(
                f"A successful login occurred at {local_ts.strftime('%Y-%m-%d %H:%M:%S %Z')} "
                f"outside the configured permitted lab schedule. "
                f"Verify whether the access was authorized."
            ),
            verification_step=(
                "Check the approved lab schedule, holiday calendar, "
                "and any documented exception for this login."
            ),
            priority_rationale=(
                "Medium priority indicates a schedule exception requiring "
                "human review, not confirmed misuse."
            ),
        ))

    return alerts


def detect_ip_boundary(df, settings):
    """Flag events outside an optional approved network."""
    if not settings.get("enable_ip_rule", False):
        return []

    if df is None or df.empty or "ip_address" not in df.columns:
        return []

    try:
        network = ipaddress.ip_network(
            settings.get("approved_network", "192.168.10.0/24"),
            strict=False,
        )
    except ValueError:
        return []

    required = {"timestamp", "account", "computer", "event_id"}
    if not required.issubset(df.columns):
        return []

    alerts = []

    for _, row in df.iterrows():
        value = row.get("ip_address")

        if pd.isna(value) or not str(value).strip():
            continue

        try:
            address = ipaddress.ip_address(str(value).strip())
        except ValueError:
            # Invalid addresses belong in the validation report.
            continue

        if address.version != network.version or address in network:
            continue

        ts = _parse_timestamp(
            row["timestamp"], settings.get("timezone", "UTC")
        )
        if ts is None:
            continue

        alerts.append(_base_alert(
            alert_id=f"ET-IP-{len(alerts) + 1:04d}",
            rule="ip_boundary",
            rule_label="IP Outside Approved Lab Network",
            priority="Medium",
            account=str(row["account"]),
            computer=str(row["computer"]),
            ts_start=ts,
            ts_end=ts,
            event_ids=[str(row["event_id"])],
            explanation=(
                f"Event {row['event_id']} used IP address {address}, "
                f"which is outside the configured approved network "
                f"{network}. This may have a legitimate explanation."
            ),
            verification_step=(
                "Confirm the source IP, approved network configuration, "
                "and whether an authorized VPN or network change applies."
            ),
            priority_rationale=(
                "Medium priority indicates a network-boundary exception "
                "that requires administrator verification."
            ),
        ))

    return alerts


def run_all_rules(df, settings):
    """Run enabled rules and return alerts in timestamp order."""
    if df is None or df.empty:
        return []

    alerts = []
    alerts.extend(detect_repeated_failures(df, settings))
    alerts.extend(detect_after_hours(df, settings))
    alerts.extend(detect_ip_boundary(df, settings))

    alerts.sort(key=lambda alert: alert["ts_start"])

    return alerts
