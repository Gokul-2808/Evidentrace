"""



app.py — EvidenTrace: Explain Before You Alert



Main Streamlit application entry point.



"""



import datetime



import io
import hashlib

import json

import sqlite3

from pathlib import Path



import subprocess



import sys







import altair as alt



import pandas as pd



import streamlit as st







from evidentrace.detection import run_all_rules



from evidentrace.evidence import build_timeline



from evidentrace.ingestion import load_csv



from evidentrace.review import VALID_STATUSES, update_review_status



from evidentrace.scheduling import format_schedule_description



from evidentrace.validation import get_valid_df, validate







# ──────────────────────────────────────────────────────────────



# PAGE CONFIG



# ──────────────────────────────────────────────────────────────



st.set_page_config(



    page_title="EvidenTrace — Explain Before You Alert",



    page_icon="🔍",



    layout="wide",



    initial_sidebar_state="expanded",



)







# ──────────────────────────────────────────────────────────────



# GLOBAL CSS



# ──────────────────────────────────────────────────────────────



_CSS = """



<style>



@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');



* { font-family: 'Inter', sans-serif; }



[data-testid="stSidebar"] {



    background: #0D1220 !important;



    border-right: 1px solid #273244;



}



.metric-card {



    background: #111827;



    border: 1px solid #273244;



    border-radius: 10px;



    padding: 18px 20px;



    margin: 4px 0;



}



.metric-card .label {



    color: #A3AEC2; font-size: 0.78rem; font-weight: 500;



    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;



}



.metric-card .value {



    color: #F3F6FC; font-size: 2rem; font-weight: 700; line-height: 1;



}



.metric-card .sub { color: #A3AEC2; font-size: 0.78rem; margin-top: 4px; }



.section-header {



    color: #22D3C5; font-size: 0.75rem; font-weight: 600;



    text-transform: uppercase; letter-spacing: 0.08em;



    margin: 20px 0 8px 0; padding-bottom: 4px; border-bottom: 1px solid #273244;



}



.why-flagged {



    background: #161F2E; border: 1px solid #273244;



    border-left: 4px solid #22D3C5; border-radius: 8px;



    padding: 16px 18px; margin: 12px 0;



}



.why-flagged .title {



    color: #22D3C5; font-size: 0.75rem; font-weight: 600;



    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;



}



.why-flagged .body { color: #F3F6FC; font-size: 0.92rem; line-height: 1.6; }



.verify-box {



    background: #0D1220; border: 1px solid #273244;



    border-left: 4px solid #34D399; border-radius: 8px;



    padding: 14px 16px; margin: 10px 0;



}



.verify-box .title {



    color: #34D399; font-size: 0.75rem; font-weight: 600;



    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;



}



.verify-box .body { color: #A3AEC2; font-size: 0.88rem; }



.info-banner {



    background: #111827; border: 1px solid #273244;



    border-radius: 8px; padding: 24px; text-align: center; color: #A3AEC2;



}



.issue-chip {



    background: rgba(248,113,113,0.1); border: 1px solid #F87171;



    border-radius: 6px; padding: 8px 12px; margin: 4px 0;



}



.pill {



    display: inline-block; padding: 2px 10px;



    border-radius: 20px; font-size: 0.75rem; font-weight: 600;



}



.pill-high { background: rgba(248,113,113,0.15); color: #F87171; border: 1px solid #F87171; }



.pill-medium { background: rgba(251,191,36,0.15); color: #FBBF24; border: 1px solid #FBBF24; }



.pill-low { background: rgba(56,189,248,0.15); color: #38BDF8; border: 1px solid #38BDF8; }



.pill-open { background: rgba(163,174,194,0.15); color: #A3AEC2; border: 1px solid #A3AEC2; }



.pill-review { background: rgba(251,191,36,0.15); color: #FBBF24; border: 1px solid #FBBF24; }



.pill-resolved { background: rgba(52,211,153,0.15); color: #34D399; border: 1px solid #34D399; }



.pill-fp { background: rgba(56,189,248,0.15); color: #38BDF8; border: 1px solid #38BDF8; }



.stButton > button {



    background: #111827; border: 1px solid #273244;



    color: #F3F6FC; border-radius: 6px; font-size: 0.85rem; transition: all 0.2s;



}



.stButton > button:hover { border-color: #22D3C5; color: #22D3C5; }



.block-container { padding: 1.5rem 2rem; max-width: 1400px; }




/* Sidebar visual refresh only. App behavior and navigation values are unchanged. */
[data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin-bottom: .35rem; }
.et-brand { padding: 10px 2px 22px; margin-bottom: 12px; border-bottom: 1px solid #253148; }
.et-brand-row { display: flex; align-items: center; gap: 10px; margin-bottom: 7px; }
.et-brand-mark {
    width: 42px; height: 42px; flex: 0 0 42px; display: flex;
    align-items: center; justify-content: center; border-radius: 13px;
    color: #35E0D0; background: #12353C; border: 1px solid #24535A; font-size: 1.35rem;
}
.et-brand-name { color: #F4F7FF; font-size: 1.28rem; line-height: 1.15; font-weight: 750; letter-spacing: -.025em; }
.et-brand-tagline { padding-left: 2px; color: #35DCCB; font-size: .78rem; letter-spacing: .01em; }
.et-side-label { color: #35DCCB; font-size: .70rem; font-weight: 700; text-transform: uppercase; letter-spacing: .12em; margin: 18px 0 8px; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 5px; }
[data-testid="stSidebar"] [role="radiogroup"] > label {
    border: 1px solid transparent; border-radius: 10px; padding: 9px 10px !important;
    margin: 0 !important; background: transparent; transition: background 120ms ease, border-color 120ms ease;
}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover { background: #131D30; border-color: #253148; }
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) { background: #15343B; border-color: #24535A; }
[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] > label p { color: #D9E2F2; font-size: .91rem; font-weight: 500; }
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p { color: #FFFFFF; font-weight: 650; }
.et-dataset-card { background: #131D30; border: 1px solid #253148; border-radius: 12px; padding: 12px; margin: 7px 0 10px; }
.et-dataset-heading { display: flex; align-items: center; gap: 9px; color: #F4F7FF; font-size: .88rem; font-weight: 650; margin-bottom: 8px; }
.et-dataset-icon { display: inline-flex; width: 34px; height: 34px; align-items: center; justify-content: center; border-radius: 9px; background: #12353C; color: #35DCCB; font-size: 1.1rem; }
.et-dataset-name { color: #D9E2F2; font-size: .76rem; line-height: 1.4; overflow-wrap: anywhere; margin-bottom: 10px; }
.et-dataset-stats { display: flex; gap: 8px; flex-wrap: wrap; padding-top: 9px; border-top: 1px solid #29364B; color: #A3AEC2; font-size: .73rem; }
.et-dataset-stats strong { color: #FBBF24; font-weight: 700; }
.et-empty-dataset { color: #A3AEC2; font-size: .78rem; background: #111827; border: 1px dashed #334155; border-radius: 10px; padding: 12px; margin: 7px 0 10px; }
.et-footer { border-top: 1px solid #253148; margin-top: 20px; padding-top: 13px; color: #71819C; text-align: center; font-size: .70rem; line-height: 1.7; }
@media (max-width: 800px) { [data-testid="stSidebar"] [role="radiogroup"] > label { padding: 8px !important; } }

</style>



"""



st.markdown(_CSS, unsafe_allow_html=True)







# ──────────────────────────────────────────────────────────────



# SESSION STATE



# ──────────────────────────────────────────────────────────────







def _init_state():



    defaults = {



        "raw_df": None,



        "valid_df": None,



        "ingest_report": None,



        "validation_report": None,



        "alerts": [],



        "filename": None,



        "settings": {



            "min_failures": 3,



            "window_minutes": 10,



            "require_success": True,



            "consecutive": False,



            "open_time": datetime.time(8, 0),



            "close_time": datetime.time(18, 0),



            "permitted_weekdays": [0, 1, 2, 3, 4],



            "holidays": [],



            "timezone": "UTC",



            "enable_ip_rule": False,



            "approved_network": "192.168.10.0/24",



        },



        "selected_alert_id": None,



        "test_results": None,



    }



    for k, v in defaults.items():



        if k not in st.session_state:



            st.session_state[k] = v











_init_state()







# ──────────────────────────────────────────────────────────────



# HELPERS



# ──────────────────────────────────────────────────────────────







# SQLite database is stored beside app.py. Keep it in the project folder.

DATABASE_PATH = Path(__file__).resolve().parent / "evidentrace.db"

LEGACY_REVIEW_STORE_PATH = Path(__file__).resolve().parent / "review_statuses.json"





def _db_connect():

    """Open the local SQLite database and ensure the required tables exist."""

    conn = sqlite3.connect(str(DATABASE_PATH), timeout=10)

    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("""

        CREATE TABLE IF NOT EXISTS review_statuses (

            storage_key TEXT PRIMARY KEY,

            status TEXT NOT NULL,

            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

        )

    """)

    conn.execute("""

        CREATE TABLE IF NOT EXISTS app_settings (

            setting_key TEXT PRIMARY KEY,

            setting_value TEXT NOT NULL,

            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

        )

    """)

    conn.commit()

    return conn





def _read_review_store():

    """Read all review statuses from SQLite, importing the old JSON file once."""

    try:

        with _db_connect() as conn:

            rows = conn.execute("SELECT storage_key, status FROM review_statuses").fetchall()

            saved = dict(rows)

            # Migrate existing JSON statuses so the user's current reviews are not lost.

            if not saved and LEGACY_REVIEW_STORE_PATH.exists():

                try:

                    legacy = json.loads(LEGACY_REVIEW_STORE_PATH.read_text(encoding="utf-8"))

                    if isinstance(legacy, dict):

                        for key, status in legacy.items():

                            if status in VALID_STATUSES:

                                conn.execute(

                                    "INSERT OR REPLACE INTO review_statuses(storage_key, status, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",

                                    (str(key), str(status)),

                                )

                        conn.commit()

                        saved = {

                            str(key): str(status)

                            for key, status in legacy.items()

                            if status in VALID_STATUSES

                        }

                except (OSError, json.JSONDecodeError):

                    pass

            return saved

    except sqlite3.Error as exc:

        st.error(f"Could not read SQLite review statuses: {exc}")

        return {}





def _write_review_store(data):

    """Persist review statuses in SQLite instead of session-only memory."""

    try:

        with _db_connect() as conn:

            for key, status in data.items():

                if status in VALID_STATUSES:

                    conn.execute(

                        "INSERT INTO review_statuses(storage_key, status, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "

                        "ON CONFLICT(storage_key) DO UPDATE SET status=excluded.status, updated_at=CURRENT_TIMESTAMP",

                        (str(key), str(status)),

                    )

        return True

    except sqlite3.Error as exc:

        st.error(f"Could not save review status to SQLite: {exc}")

        return False





def _save_settings_store(settings):

    """Save current rule and schedule settings in SQLite."""

    try:

        serializable = dict(settings)

        for key in ("open_time", "close_time"):

            value = serializable.get(key)

            if isinstance(value, datetime.time):

                serializable[key] = value.strftime("%H:%M:%S")

        with _db_connect() as conn:

            conn.execute(

                "INSERT INTO app_settings(setting_key, setting_value, updated_at) VALUES ('rules', ?, CURRENT_TIMESTAMP) "

                "ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value, updated_at=CURRENT_TIMESTAMP",

                (json.dumps(serializable, ensure_ascii=False),),

            )

        return True

    except (sqlite3.Error, TypeError, ValueError) as exc:

        st.error(f"Could not save settings to SQLite: {exc}")

        return False





def _restore_settings_store():

    """Restore persisted rules and schedule, keeping safe defaults for invalid data."""

    try:

        with _db_connect() as conn:

            row = conn.execute(

                "SELECT setting_value FROM app_settings WHERE setting_key='rules'"

            ).fetchone()

        if not row:

            return

        saved = json.loads(row[0])

        if not isinstance(saved, dict):

            return

        for key in ("open_time", "close_time"):

            value = saved.get(key)

            if isinstance(value, str):

                saved[key] = datetime.time.fromisoformat(value)

        st.session_state.settings.update(saved)

    except (sqlite3.Error, json.JSONDecodeError, ValueError, TypeError) as exc:

        st.warning(f"Saved settings could not be restored; using current defaults. Details: {exc}")



def _review_store_key(alert):

    dataset = st.session_state.get("filename") or "dataset"

    return f"{dataset}::{alert.get('alert_id', '')}"



def _run_analysis():

    """Run all detection rules on current valid_df and restore saved review statuses."""

    df = st.session_state.valid_df

    if df is None or df.empty:

        st.session_state.alerts = []

        return



    old_statuses = {a["alert_id"]: a.get("review_status", "Open") for a in st.session_state.alerts}

    saved_statuses = _read_review_store()

    alerts = run_all_rules(df, st.session_state.settings)

    for alert in alerts:

        saved = saved_statuses.get(_review_store_key(alert))

        if saved in VALID_STATUSES:

            alert["review_status"] = saved

        elif alert["alert_id"] in old_statuses:

            alert["review_status"] = old_statuses[alert["alert_id"]]

    st.session_state.alerts = alerts





# Load persisted rules/schedule once at startup, after session defaults exist.

_restore_settings_store()





def _load_file(content: bytes, fname: str):



    """Ingest, validate, analyse uploaded data."""



    df_raw, ingest = load_csv(io.BytesIO(content))



    ingest["filename"] = fname



    val = validate(df_raw)



    valid = get_valid_df(df_raw)



    st.session_state.raw_df = df_raw



    st.session_state.valid_df = valid



    st.session_state.ingest_report = ingest



    st.session_state.validation_report = val



    st.session_state.filename = fname



    st.session_state.alerts = []



    st.session_state.selected_alert_id = None



    _run_analysis()











def _ts(ts) -> str:



    return ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, pd.Timestamp) else str(ts)











def _priority_pill(p: str) -> str:



    cls = {"High": "pill-high", "Medium": "pill-medium", "Low": "pill-low"}.get(p, "pill-low")



    return f'<span class="pill {cls}">{p}</span>'











def _status_pill(s: str) -> str:



    cls = {



        "Open": "pill-open",



        "Under Review": "pill-review",



        "Resolved": "pill-resolved",



        "False Positive": "pill-fp",



    }.get(s, "pill-open")



    return f'<span class="pill {cls}">{s}</span>'











def _mcard(col, label: str, value: str, sub: str = "", color: str = "#F3F6FC"):



    col.markdown(



        f'<div class="metric-card">'



        f'<div class="label">{label}</div>'



        f'<div class="value" style="color:{color};">{value}</div>'



        f'<div class="sub">{sub}</div>'



        f"</div>",



        unsafe_allow_html=True,



    )











# ──────────────────────────────────────────────────────────────



# SIDEBAR
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div class="et-brand">'
        '<div class="et-brand-row">'
        '<div class="et-brand-mark">⌕</div>'
        '<div class="et-brand-name">EvidenTrace</div>'
        '</div>'
        '<div class="et-brand-tagline">Explain Before You Alert</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Preserve original radio navigation labels so routing remains unchanged.
    page = st.radio(
        "Nav",
        [
            "🏠 Security Overview",
            "🚨 Alert Investigation",
            "🔎 Login Explorer",
            "⚙️ Rules & Lab Schedule",
            "🧪 Data Quality & QA",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<div class="et-side-label">Dataset</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        upload_signature = (uploaded.name, hashlib.sha256(file_bytes).hexdigest())
        if st.session_state.get("_last_upload_signature") != upload_signature:
            _load_file(file_bytes, uploaded.name)
            st.session_state._last_upload_signature = upload_signature

    if st.session_state.filename:
        n = len(st.session_state.raw_df) if st.session_state.raw_df is not None else 0
        a = len(st.session_state.alerts)
        st.markdown(
            '<div class="et-dataset-card">'
            '<div class="et-dataset-heading"><span class="et-dataset-icon">▦</span>'
            '<span>Current dataset</span></div>'
            f'<div class="et-dataset-name">✓ {st.session_state.filename}</div>'
            f'<div class="et-dataset-stats"><span>{n:,} rows</span><span>·</span>'
            f'<span><strong>{a:,}</strong> alerts</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="et-empty-dataset">No dataset loaded yet.<br>'
            '<span style="color:#71819C;">Upload a CSV to begin analysis.</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="et-footer">EvidenTrace v1.0 · EvidentX<br>CyberHack ENG-02</div>',
        unsafe_allow_html=True,
    )


# PAGE 1: SECURITY OVERVIEW



# ──────────────────────────────────────────────────────────────







if page == "🏠 Security Overview":



    st.markdown("## Security Overview")



    st.markdown(



        '<div style="color:#A3AEC2;font-size:0.9rem;margin-bottom:20px;">'



        "Lab access analysis dashboard — <em>Explain Before You Alert</em></div>",



        unsafe_allow_html=True,



    )







    if st.session_state.raw_df is None:



        st.markdown(



            '<div class="info-banner">'



            '<div style="font-size:3rem;">📂</div>'



            '<div style="font-size:1.1rem;color:#F3F6FC;margin:8px 0;">Upload a CSV to begin analysis</div>'



            "<div>Use the sidebar uploader or load a sample below.</div>"



            "</div>",



            unsafe_allow_html=True,



        )



        c1, c2 = st.columns(2)



        with c1:



            if st.button("📋 Load Official Sample", use_container_width=True):



                try:



                    with open("sample_data/sample_official.csv", "rb") as f:



                        _load_file(f.read(), "sample_official.csv")



                    st.rerun()



                except FileNotFoundError:



                    st.error("Sample file not found.")



        with c2:



            if st.button("🧪 Load Synthetic Sample", use_container_width=True):



                try:



                    with open("sample_data/sample_synthetic.csv", "rb") as f:



                        _load_file(f.read(), "sample_synthetic.csv")



                    st.rerun()



                except FileNotFoundError:



                    st.error("Sample file not found.")



        st.stop()







    raw = st.session_state.raw_df



    valid = st.session_state.valid_df



    val = st.session_state.validation_report



    alerts = st.session_state.alerts







    tot = len(raw)



    vld = len(valid) if valid is not None else 0



    na = len(alerts)



    nq = len(val.get("issues", []))







    m1, m2, m3, m4 = st.columns(4)



    _mcard(m1, "Total Events", f"{tot:,}", "All rows received")



    _mcard(m2, "Valid Events", f"{vld:,}", "Used in detection", "#34D399")



    _mcard(m3, "Review Alerts", f"{na:,}", "Require administrator review",



           "#F87171" if na > 0 else "#34D399")



    _mcard(m4, "Data Quality Issues", f"{nq:,}", "Validation findings",



           "#FBBF24" if nq > 0 else "#34D399")







    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)







    ch1, ch2 = st.columns([2, 1])



    with ch1:



        st.markdown('<div class="section-header">Login Activity Timeline</div>', unsafe_allow_html=True)



        if valid is not None and not valid.empty and "timestamp" in valid.columns:



            tl = valid.copy()



            tl["hour"] = tl["timestamp"].dt.floor("h")



            timeline = tl.groupby(["hour", "event"]).size().reset_index(name="count")



            chart = (



                alt.Chart(timeline)



                .mark_area(opacity=0.7, interpolate="monotone")



                .encode(



                    x=alt.X("hour:T", title="Time",



                            axis=alt.Axis(format="%b %d %H:%M", labelColor="#A3AEC2", titleColor="#A3AEC2")),



                    y=alt.Y("count:Q", title="Events",



                            axis=alt.Axis(labelColor="#A3AEC2", titleColor="#A3AEC2")),



                    color=alt.Color(



                        "event:N",



                        scale=alt.Scale(domain=["Success", "Failure"], range=["#22D3C5", "#F87171"]),



                        legend=alt.Legend(labelColor="#A3AEC2"),



                    ),



                    tooltip=["hour:T", "event:N", "count:Q"],



                )



                .properties(height=200)



                .configure_view(strokeWidth=0, fill="#111827")



                .configure_axis(gridColor="#1E2D40")



                .configure(background="#111827")



            )



            st.altair_chart(chart, use_container_width=True)



        else:



            st.info("No valid timestamped events to chart.")







    with ch2:



        st.markdown('<div class="section-header">Alert Distribution</div>', unsafe_allow_html=True)



        if alerts:



            rc2 = {}



            for a in alerts:



                rc2[a.get("rule_label", "?")] = rc2.get(a.get("rule_label", "?"), 0) + 1



            rdf = pd.DataFrame(list(rc2.items()), columns=["Rule", "Count"])



            pie = (



                alt.Chart(rdf)



                .mark_arc(innerRadius=40)



                .encode(



                    theta=alt.Theta("Count:Q"),



                    color=alt.Color(



                        "Rule:N",



                        scale=alt.Scale(range=["#F87171", "#FBBF24", "#38BDF8", "#22D3C5"]),



                        legend=alt.Legend(labelColor="#A3AEC2"),



                    ),



                    tooltip=["Rule:N", "Count:Q"],



                )



                .properties(height=200)



                .configure_view(strokeWidth=0)



                .configure(background="#111827")



            )



            st.altair_chart(pie, use_container_width=True)



        else:



            st.markdown(



                '<div style="color:#34D399;text-align:center;padding:40px;font-size:0.9rem;">'



                "✓ No alerts generated</div>",



                unsafe_allow_html=True,



            )







    if valid is not None and not valid.empty and "event" in valid.columns:



        st.markdown('<div class="section-header">Login Outcome Summary</div>', unsafe_allow_html=True)



        sc = int((valid["event"] == "Success").sum())



        fc = int((valid["event"] == "Failure").sum())



        tv = sc + fc



        s1, s2, s3 = st.columns(3)



        _mcard(s1, "Successful Logins", f"{sc:,}",



               f"{sc/tv*100:.1f}% of valid events" if tv else "", "#34D399")



        _mcard(s2, "Failed Logins", f"{fc:,}",



               f"{fc/tv*100:.1f}% of valid events" if tv else "", "#F87171")



        ratio = fc / sc if sc > 0 else float("inf")



        _mcard(s3, "Failure:Success Ratio", f"{ratio:.2f}", "Higher values may warrant attention")







    st.markdown('<div class="section-header">Recent Alerts</div>', unsafe_allow_html=True)



    if alerts:



        rows = [



            {



                "Alert ID": a.get("alert_id"),



                "Rule": a.get("rule_label"),



                "Priority": a.get("priority"),



                "Account": a.get("account"),



                "Computer": a.get("computer"),



                "Time": _ts(a.get("ts_start")),



                "Status": a.get("review_status"),



            }



            for a in alerts[:10]



        ]



        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)



    else:



        st.markdown(



            '<div style="color:#34D399;font-size:0.9rem;padding:12px;background:#111827;'



            'border-radius:8px;border:1px solid #273244;">✓ No alerts generated.</div>',



            unsafe_allow_html=True,



        )







# ──────────────────────────────────────────────────────────────



# PAGE 2: ALERT INVESTIGATION



# ──────────────────────────────────────────────────────────────







elif page == "🚨 Alert Investigation":



    st.markdown("## Alert Investigation")



    st.markdown(



        '<div style="color:#A3AEC2;font-size:0.9rem;margin-bottom:16px;">'



        "Review every alert with full evidence and explanation before acting.</div>",



        unsafe_allow_html=True,



    )







    if st.session_state.raw_df is None:



        st.info("Upload a dataset from the sidebar to begin.")



        st.stop()







    alerts = st.session_state.alerts



    if not alerts:



        st.markdown(



            '<div class="info-banner"><div style="font-size:2.5rem;">✅</div>'



            '<div style="font-size:1rem;color:#34D399;margin:8px 0;">No alerts generated</div>'



            "<div>No findings with current settings and dataset.</div></div>",



            unsafe_allow_html=True,



        )



        st.stop()







    with st.expander("🔽 Filters", expanded=False):



        fc1, fc2, fc3, fc4 = st.columns(4)



        f_rule = fc1.selectbox("Rule", ["All"] + sorted({a.get("rule_label", "?") for a in alerts}))



        f_pri = fc2.selectbox("Priority", ["All", "High", "Medium", "Low"])



        f_stat = fc3.selectbox("Status", ["All"] + VALID_STATUSES)



        f_comp = fc4.selectbox("Computer", ["All"] + sorted({a.get("computer", "?") for a in alerts}))







    def _filt(a):



        if f_rule != "All" and a.get("rule_label") != f_rule:



            return False



        if f_pri != "All" and a.get("priority") != f_pri:



            return False



        if f_stat != "All" and a.get("review_status") != f_stat:



            return False



        if f_comp != "All" and a.get("computer") != f_comp:



            return False



        return True







    filtered = [a for a in alerts if _filt(a)]



    if not filtered:



        st.warning("No alerts match the current filters.")



        st.stop()





    # Explicit selector lets the reviewer open any alert, not only the first.

    available_alert_ids = [str(item["alert_id"]) for item in filtered]

    current_alert_id = st.session_state.get("selected_alert_id")

    if current_alert_id not in available_alert_ids:

        current_alert_id = available_alert_ids[0]

        st.session_state.selected_alert_id = current_alert_id



    default_alert_index = available_alert_ids.index(str(current_alert_id))

    chosen_alert_id = st.selectbox(

        "Select an alert to investigate",

        options=available_alert_ids,

        index=default_alert_index,

        format_func=lambda alert_id: next(

            (

                f"{item.get('alert_id', '?')} · {item.get('rule_label', 'Alert')} · "

                f"{item.get('account', '?')} @ {item.get('computer', '?')} · "

                f"{_ts(item.get('ts_start'))}"

                for item in filtered

                if str(item.get("alert_id")) == str(alert_id)

            ),

            str(alert_id),

        ),

        key="investigation_alert_picker",

    )

    st.session_state.selected_alert_id = chosen_alert_id









    lc, dc = st.columns([1, 2])



    with lc:



        st.markdown(



            f'<div style="font-size:0.8rem;color:#A3AEC2;margin-bottom:8px;">{len(filtered)} alert(s)</div>',



            unsafe_allow_html=True,



        )



        for a in filtered:



            aid = a["alert_id"]



            ts_s = _ts(a.get("ts_start"))



            label = (



                f"**{a.get('rule_label','?')}**  \n"



                f"{a.get('account','?')} @ {a.get('computer','?')}  \n"



                f"{ts_s} · {a.get('priority','?')}"



            )



            if st.button(label, key=f"ab_{aid}", use_container_width=True):



                st.session_state.selected_alert_id = aid



                st.rerun()







    with dc:



        sid = st.session_state.get("selected_alert_id")

        a = next((x for x in filtered if str(x["alert_id"]) == str(sid)), filtered[0])

        st.session_state.selected_alert_id = a["alert_id"]







        st.markdown(f"### {a.get('rule_label', 'Alert')}")



        st.markdown(



            f"{_priority_pill(a.get('priority','?'))} {_status_pill(a.get('review_status','?'))}",



            unsafe_allow_html=True,



        )



        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)







        i1, i2, i3 = st.columns(3)



        i1.markdown(f"**Alert ID**  \n`{a.get('alert_id','?')}`")



        i2.markdown(f"**Account**  \n{a.get('account','—')}")



        i3.markdown(f"**Computer**  \n{a.get('computer','—')}")







        i4, i5, i6 = st.columns(3)



        i4.markdown(f"**Start**  \n{_ts(a.get('ts_start'))}")



        i5.markdown(f"**End**  \n{_ts(a.get('ts_end'))}")



        i6.markdown(f"**Elapsed**  \n{a.get('elapsed','—')}")







        if a.get("ip_address"):



            st.markdown(f"**IP Address:** `{a.get('ip_address')}`")







        eids = a.get("event_ids", [])



        if eids:



            st.markdown(f"**Supporting Event IDs:** `{', '.join(str(e) for e in eids)}`")







        # Resolve supporting event IDs against the normalized, validated records.

        # This avoids displaying a default failure count when the detector did not

        # attach that optional field to the alert.

        _evidence_ids = a.get("event_ids", []) or []

        if isinstance(_evidence_ids, str):

            _evidence_ids = [x.strip() for x in _evidence_ids.split(",") if x.strip()]

        _valid_for_evidence = st.session_state.valid_df

        _alert_evidence_df = pd.DataFrame()

        if (

            _valid_for_evidence is not None

            and not _valid_for_evidence.empty

            and "event_id" in _valid_for_evidence.columns

            and _evidence_ids

        ):

            _alert_evidence_df = _valid_for_evidence[

                _valid_for_evidence["event_id"].astype(str).isin(

                    [str(x) for x in _evidence_ids]

                )

            ].copy()



        if a.get("rule") == "repeated_failures":

            _observed_failures = 0

            if not _alert_evidence_df.empty and "event" in _alert_evidence_df.columns:

                _observed_failures = int(

                    _alert_evidence_df["event"].astype(str).str.strip().str.lower()

                    .isin(["failure", "failed", "fail", "denied"])

                    .sum()

                )

            _reported_failures = a.get("failure_count")

            try:

                _reported_failures = int(_reported_failures) if _reported_failures is not None else 0

            except (TypeError, ValueError):

                _reported_failures = 0

            _failure_count = max(_observed_failures, _reported_failures)

            _threshold = int(a.get("threshold", st.session_state.settings.get("min_failures", 3)))

            _window = int(a.get("window_minutes", st.session_state.settings.get("window_minutes", 10)))

            st.markdown(

                f"**Matched Rule:** {_failure_count} failed login(s) ≥ threshold "

                f"({_threshold}) within {_window} min"

            )



        elif a.get("rule") == "after_hours":



            ot, ct = a.get("open_time"), a.get("close_time")



            if ot and ct:



                st.markdown(f"**Matched Rule:** Outside {ot.strftime('%H:%M')}–{ct.strftime('%H:%M')}")







        # WHY WAS THIS FLAGGED?



        expl = a.get("explanation", "No explanation available.")



        st.markdown(



            f'<div class="why-flagged">'



            f'<div class="title">🔍 WHY WAS THIS FLAGGED?</div>'



            f'<div class="body">{expl}</div>'



            f"</div>",



            unsafe_allow_html=True,



        )



        st.markdown(



            f'<div style="font-size:0.82rem;color:#A3AEC2;margin:-4px 0 8px 0;">'



            f"<b>Priority rationale:</b> {a.get('priority_rationale','')}</div>",



            unsafe_allow_html=True,



        )







        st.markdown('<div class="section-header">Evidence Timeline</div>', unsafe_allow_html=True)



        # Prefer source records for the timeline so timestamps, outcomes, and

        # computer/account fields are real dataset values rather than placeholders.

        _timeline_ids = a.get("event_ids", []) or []

        if isinstance(_timeline_ids, str):

            _timeline_ids = [x.strip() for x in _timeline_ids.split(",") if x.strip()]



        _timeline_df = pd.DataFrame()

        _source_df = st.session_state.valid_df

        if (

            _source_df is not None

            and not _source_df.empty

            and "event_id" in _source_df.columns

            and _timeline_ids

        ):

            _timeline_df = _source_df[

                _source_df["event_id"].astype(str).isin([str(x) for x in _timeline_ids])

            ].copy()



        if not _timeline_df.empty:

            if "timestamp" in _timeline_df.columns:

                _timeline_df["timestamp"] = pd.to_datetime(

                    _timeline_df["timestamp"], errors="coerce"

                )

                _timeline_df = _timeline_df.sort_values(

                    "timestamp", na_position="last"

                )

                _timeline_df["Timestamp"] = _timeline_df["timestamp"].map(

                    lambda value: value.strftime("%Y-%m-%d %H:%M:%S")

                    if pd.notna(value) else "Invalid timestamp"

                )

            else:

                _timeline_df["Timestamp"] = "Not available"



            _timeline_view = pd.DataFrame({

                "Event ID": _timeline_df.get("event_id", pd.Series(index=_timeline_df.index, dtype="object")).astype(str),

                "Timestamp": _timeline_df["Timestamp"],

                "Event": _timeline_df.get("event", pd.Series("Unknown", index=_timeline_df.index)).astype(str),

                "Computer": _timeline_df.get("computer", pd.Series("Unknown", index=_timeline_df.index)).astype(str),

                "Account": _timeline_df.get("account", pd.Series("Unknown", index=_timeline_df.index)).astype(str),

                "IP Address": _timeline_df.get("ip_address", pd.Series("Not available", index=_timeline_df.index)).fillna("Not available").astype(str),

                "Evidence": ["Supporting event for this detection rule."] * len(_timeline_df),

            })

            st.dataframe(_timeline_view, use_container_width=True, hide_index=True)

        else:

            # Keep compatibility with the existing evidence helper as a fallback.

            tl = build_timeline(a)

            if tl:

                st.dataframe(pd.DataFrame(tl), use_container_width=True, hide_index=True)

            else:

                st.info("No supporting login records were found for this alert.")







        step = a.get("verification_step", "No recommendation available.")



        st.markdown(



            f'<div class="verify-box">'



            f'<div class="title">✅ RECOMMENDED VERIFICATION STEP</div>'



            f'<div class="body">{step}</div>'



            f"</div>",



            unsafe_allow_html=True,



        )







        st.markdown('<div class="section-header">Review Status</div>', unsafe_allow_html=True)

        current_status = a.get("review_status", "Open")

        status_options = list(VALID_STATUSES)



        # Explicit form: choose a status, then submit it with the Save button.

        with st.form(key=f"review_status_form_{a['alert_id']}"):

            selected_status = st.selectbox(

                "Choose review status",

                options=status_options,

                index=(status_options.index(current_status) if current_status in status_options else 0),

                key=f"review_status_picker_{a['alert_id']}",

            )

            submitted = st.form_submit_button(

                "Save review status", type="primary", use_container_width=True

            )



        if submitted:

            st.session_state.alerts = update_review_status(

                st.session_state.alerts, a["alert_id"], selected_status

            )

            saved_store = _read_review_store()

            updated_alert = next(

                (item for item in st.session_state.alerts

                 if str(item.get("alert_id")) == str(a.get("alert_id"))),

                None,

            )

            if updated_alert is not None:

                saved_store[_review_store_key(updated_alert)] = selected_status

                if _write_review_store(saved_store):

                    st.success(f"Review status saved: {selected_status}")

            st.rerun()



        latest_status = next(

            (item.get("review_status", "Open") for item in st.session_state.alerts

             if str(item.get("alert_id")) == str(a.get("alert_id"))),

            current_status,

        )

        st.markdown(

            f'<div style="font-size:0.8rem;color:#A3AEC2;margin-top:4px;">'

            f"Current status: {_status_pill(latest_status)} <em>(saved locally)</em></div>",

            unsafe_allow_html=True,

        )





# ──────────────────────────────────────────────────────────────



# PAGE 3: LOGIN EXPLORER



# ──────────────────────────────────────────────────────────────







elif page == "🔎 Login Explorer":



    st.markdown("## Login Explorer")



    st.markdown(



        '<div style="color:#A3AEC2;font-size:0.9rem;margin-bottom:16px;">'



        "Browse, search, and filter original event records.</div>",



        unsafe_allow_html=True,



    )







    if st.session_state.raw_df is None:



        st.info("Upload a dataset from the sidebar to begin.")



        st.stop()







    df = (



        st.session_state.valid_df.copy()



        if st.session_state.valid_df is not None



        else pd.DataFrame()



    )



    if df.empty:



        st.warning("No valid events available after validation.")



        st.stop()







    fc1, fc2, fc3 = st.columns(3)



    s_eid = fc1.text_input("🔍 Search Event ID", placeholder="e.g. EVT001")



    out_opts = (



        ["All"] + sorted(df["event"].dropna().unique().tolist())



        if "event" in df.columns



        else ["All"]



    )



    f_out = fc2.selectbox("Login Outcome", out_opts)



    comps = (



        ["All"] + sorted(df["computer"].dropna().unique().tolist())



        if "computer" in df.columns



        else ["All"]



    )



    f_comp = fc3.selectbox("Computer", comps)







    fc4, fc5 = st.columns(2)



    accs = (



        ["All"] + sorted(df["account"].dropna().unique().tolist())



        if "account" in df.columns



        else ["All"]



    )



    f_acc = fc4.selectbox("Account", accs)



    ips = (



        ["All"] + sorted(df["ip_address"].dropna().unique().tolist())



        if "ip_address" in df.columns and df["ip_address"].notna().any()



        else ["All"]



    )



    f_ip = fc5.selectbox("IP Address", ips)







    if "timestamp" in df.columns and df["timestamp"].notna().any():



        mn, mx = df["timestamp"].min(), df["timestamp"].max()



        d1, d2 = st.columns(2)



        sd = d1.date_input("From", value=mn.date(), min_value=mn.date(), max_value=mx.date())



        ed = d2.date_input("To", value=mx.date(), min_value=mn.date(), max_value=mx.date())



        df = df[(df["timestamp"].dt.date >= sd) & (df["timestamp"].dt.date <= ed)]







    if s_eid and "event_id" in df.columns:



        df = df[df["event_id"].astype(str).str.contains(s_eid, case=False, na=False)]



    if f_out != "All" and "event" in df.columns:



        df = df[df["event"] == f_out]



    if f_comp != "All" and "computer" in df.columns:



        df = df[df["computer"] == f_comp]



    if f_acc != "All" and "account" in df.columns:



        df = df[df["account"] == f_acc]



    if f_ip != "All" and "ip_address" in df.columns:



        df = df[df["ip_address"] == f_ip]







    st.markdown(



        f'<div style="font-size:0.8rem;color:#A3AEC2;margin-bottom:8px;">{len(df):,} events</div>',



        unsafe_allow_html=True,



    )



    dcols = [



        c for c in ["event_id", "timestamp", "account", "computer", "event", "ip_address", "department_case"]



        if c in df.columns



    ]



    st.dataframe(df[dcols], use_container_width=True, hide_index=True)







    st.markdown('<div class="section-header">Event Detail</div>', unsafe_allow_html=True)



    if "event_id" in df.columns and len(df) > 0:



        sel = st.selectbox("Select event", df["event_id"].dropna().unique().tolist())



        if sel:



            row = df[df["event_id"] == sel].iloc[0]



            rc1, rc2 = st.columns(2)



            for col in dcols[:4]:



                if col in row:



                    rc1.markdown(f"**{col}:** `{row[col]}`")



            for col in dcols[4:]:



                if col in row:



                    rc2.markdown(f"**{col}:** `{row[col]}`")



            related = [



                a for a in st.session_state.alerts



                if str(sel) in [str(e) for e in a.get("event_ids", [])]



            ]



            if related:



                st.markdown(



                    f'<div style="color:#FBBF24;font-size:0.85rem;">⚠️ Referenced in '



                    f'{len(related)} alert(s): {", ".join(a["alert_id"] for a in related)}</div>',



                    unsafe_allow_html=True,



                )







# ──────────────────────────────────────────────────────────────



# PAGE 4: RULES & LAB SCHEDULE



# ──────────────────────────────────────────────────────────────







elif page == "⚙️ Rules & Lab Schedule":



    st.markdown("## Rules & Lab Schedule")



    st.markdown(



        '<div style="color:#A3AEC2;font-size:0.9rem;margin-bottom:16px;">'



        "Configure detection thresholds, lab schedule, and optional IP network.</div>",



        unsafe_allow_html=True,



    )







    s = st.session_state.settings







    st.markdown('<div class="section-header">Rule 1 — Repeated Failures → Success</div>', unsafe_allow_html=True)



    r1, r2 = st.columns(2)



    min_f = r1.number_input("Minimum failed attempts", 1, 20, int(s.get("min_failures", 3)))



    win_m = r1.number_input("Time window (minutes)", 1, 120, int(s.get("window_minutes", 10)))



    req_s = r2.checkbox("Require success following failures", bool(s.get("require_success", True)))



    consec = r2.checkbox("Require consecutive failures (no intervening events)", bool(s.get("consecutive", False)))







    st.markdown('<div class="section-header">Lab Schedule (Rule 2 — After-Hours Access)</div>', unsafe_allow_html=True)



    sc1, sc2, sc3 = st.columns(3)



    ot = sc1.time_input("Opening time (inclusive)", s.get("open_time", datetime.time(8, 0)))



    ct = sc1.time_input("Closing time (exclusive)", s.get("close_time", datetime.time(18, 0)))



    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]



    sel_days = sc2.multiselect(



        "Permitted weekdays",



        list(range(7)),



        s.get("permitted_weekdays", [0, 1, 2, 3, 4]),



        format_func=lambda x: day_names[x],



    )



    tz_opts = ["UTC", "Asia/Kolkata", "Europe/London", "US/Eastern", "US/Pacific", "Australia/Sydney"]



    cur_tz = s.get("timezone", "UTC")



    tz = sc3.selectbox("Timezone", tz_opts, index=tz_opts.index(cur_tz) if cur_tz in tz_opts else 0)



    hol_text = sc3.text_area("Holidays (YYYY-MM-DD, one per line)", "\n".join(s.get("holidays", [])), height=80)







    st.markdown('<div class="section-header">Rule 3 (Optional) — IP Network Boundary</div>', unsafe_allow_html=True)



    en_ip = st.checkbox("Enable IP network boundary rule", bool(s.get("enable_ip_rule", False)))



    apn = st.text_input("Approved IPv4/IPv6 CIDR network", s.get("approved_network", "192.168.10.0/24"), disabled=not en_ip)



    if en_ip and apn:



        import ipaddress as _ipmod



        try:



            _ipmod.ip_network(apn, strict=False)



            st.markdown(f'<div style="color:#34D399;font-size:0.83rem;">✓ Valid network: {apn}</div>', unsafe_allow_html=True)



        except ValueError:



            st.error("Invalid CIDR notation. Example: 192.168.10.0/24")







    def _parse_hols(text):



        valid = []



        for l in text.strip().splitlines():



            l = l.strip()



            if l:



                try:



                    datetime.date.fromisoformat(l)



                    valid.append(l)



                except ValueError:



                    pass



        return valid







    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)



    ac1, ac2, ac3 = st.columns(3)







    if ac1.button("💾 Save & Reanalyse", use_container_width=True, type="primary"):



        st.session_state.settings.update({



            "min_failures": int(min_f),



            "window_minutes": int(win_m),



            "require_success": req_s,



            "consecutive": consec,



            "open_time": ot,



            "close_time": ct,



            "permitted_weekdays": sel_days,



            "holidays": _parse_hols(hol_text),



            "timezone": tz,



            "enable_ip_rule": en_ip,



            "approved_network": apn,



        })



        settings_saved = _save_settings_store(st.session_state.settings)

        _run_analysis()



        if settings_saved:

            st.success(f"Settings saved to SQLite. {len(st.session_state.alerts)} alert(s) generated.")

        else:

            st.warning(f"Settings applied for this session. {len(st.session_state.alerts)} alert(s) generated, but persistence failed.")







    if ac2.button("↩️ Reset to Defaults", use_container_width=True):



        st.session_state.settings = {



            "min_failures": 3, "window_minutes": 10, "require_success": True,



            "consecutive": False, "open_time": datetime.time(8, 0), "close_time": datetime.time(18, 0),



            "permitted_weekdays": [0, 1, 2, 3, 4], "holidays": [], "timezone": "UTC",



            "enable_ip_rule": False, "approved_network": "192.168.10.0/24",



        }



        _save_settings_store(st.session_state.settings)

        _run_analysis()



        st.success("Settings reset to defaults and saved to SQLite.")



        st.rerun()







    if ac3.button("🔄 Reanalyse Only", use_container_width=True):



        _run_analysis()



        st.success(f"Reanalysed. {len(st.session_state.alerts)} alert(s) generated.")







    st.markdown('<div class="section-header">Current Schedule Summary</div>', unsafe_allow_html=True)



    st.markdown(



        f'<div style="font-size:0.9rem;color:#F3F6FC;background:#111827;'



        f'border:1px solid #273244;border-radius:8px;padding:12px 16px;">'



        f"<b>Lab hours:</b> {s.get('open_time')} – {s.get('close_time')} "



        f"(opening inclusive, closing exclusive)<br>"



        f"<b>Timezone:</b> {s.get('timezone','UTC')}<br>"



        f"<b>Schedule:</b> {format_schedule_description(s)}<br>"



        f"<b>Holidays:</b> {len(s.get('holidays', []))} configured"



        f"</div>",



        unsafe_allow_html=True,



    )







# ──────────────────────────────────────────────────────────────



# PAGE 5: DATA QUALITY & QA



# ──────────────────────────────────────────────────────────────







elif page == "🧪 Data Quality & QA":



    st.markdown("## Data Quality & QA")



    st.markdown(



        '<div style="color:#A3AEC2;font-size:0.9rem;margin-bottom:16px;">'



        "Validation results for the current dataset and automated test suite status.</div>",



        unsafe_allow_html=True,



    )







    st.markdown('<div class="section-header">Dataset Validation</div>', unsafe_allow_html=True)







    if st.session_state.raw_df is None:



        st.info("Upload a dataset to see quality results.")



    else:



        raw = st.session_state.raw_df



        val = st.session_state.validation_report



        ingest = st.session_state.ingest_report







        q1, q2, q3, q4 = st.columns(4)



        _mcard(q1, "Total Rows", f"{len(raw):,}")



        _mcard(q2, "Valid Rows", f"{val.get('valid_rows',0):,}", color="#34D399")



        _mcard(q3, "Excluded / Invalid", f"{val.get('invalid_rows',0):,}",



               color="#F87171" if val.get("invalid_rows", 0) > 0 else "#34D399")



        _mcard(q4, "Schema Detected", ingest.get("schema", "?").upper())







        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)



        q5, q6, q7, q8 = st.columns(4)







        def _warn(v):



            return "#FBBF24" if v > 0 else "#34D399"







        _mcard(q5, "Duplicate Event IDs", f"{val.get('duplicate_event_ids',0):,}",



               color=_warn(val.get("duplicate_event_ids", 0)))



        _mcard(q6, "Missing Timestamps", f"{val.get('missing_timestamps',0):,}",



               color=_warn(val.get("missing_timestamps", 0)))



        _mcard(q7, "Invalid Timestamps", f"{val.get('invalid_timestamps',0):,}",



               color="#F87171" if val.get("invalid_timestamps", 0) > 0 else "#34D399")



        _mcard(q8, "Unknown Outcomes", f"{val.get('unknown_outcomes',0):,}",



               color=_warn(val.get("unknown_outcomes", 0)))







        issues = val.get("issues", [])



        if issues:



            st.markdown('<div class="section-header">Validation Issues</div>', unsafe_allow_html=True)



            icons = {



                "empty_csv": "❌", "missing_columns": "🚫", "duplicate_event_ids": "⚠️",



                "missing_timestamp": "⏱️", "invalid_timestamp_format": "❌",



                "unknown_login_outcome": "❓", "invalid_ip_address": "🌐", "missing_event_id": "🔑",



            }



            for iss in issues:



                ico = icons.get(iss["type"], "ℹ️")



                st.markdown(



                    f'<div class="issue-chip">{ico} <b>{iss["type"].replace("_"," ").title()}</b>: '



                    f'{iss["description"]}</div>',



                    unsafe_allow_html=True,



                )



        else:



            st.markdown(



                '<div style="color:#34D399;font-size:0.9rem;padding:12px;background:#111827;'



                'border-radius:8px;border:1px solid #273244;">✓ No validation issues. Dataset is clean.</div>',



                unsafe_allow_html=True,



            )







        for n in ingest.get("notes", []):



            st.markdown(



                f'<div style="font-size:0.85rem;color:#A3AEC2;padding:4px 0;">ℹ️ {n}</div>',



                unsafe_allow_html=True,



            )







    st.markdown(



        '<div class="section-header">Automated Test Suite (23 Edge Cases)</div>',



        unsafe_allow_html=True,



    )







    tc1, tc2 = st.columns([1, 3])



    with tc1:



        if st.button("▶️ Run Tests Now", use_container_width=True):



            with st.spinner("Running pytest..."):



                try:



                    res = subprocess.run(



                        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--no-header", "-q"],



                        capture_output=True,



                        text=True,



                        cwd=".",



                        timeout=60,



                    )



                    st.session_state.test_results = {



                        "stdout": res.stdout,



                        "stderr": res.stderr,



                        "returncode": res.returncode,



                    }



                except Exception as exc:



                    st.session_state.test_results = {"stdout": "", "stderr": str(exc), "returncode": -1}







    tr = st.session_state.test_results



    if tr:



        rc = tr.get("returncode", -1)



        col = "#34D399" if rc == 0 else "#F87171"



        sym = "✅" if rc == 0 else "❌"



        msg = "All tests passed" if rc == 0 else "Some tests failed"



        st.markdown(



            f'<div style="color:{col};font-size:0.9rem;font-weight:600;">{sym} {msg} (exit code {rc})</div>',



            unsafe_allow_html=True,



        )



        output = (tr.get("stdout", "") + tr.get("stderr", "")).strip()



        st.code(output or "(no output)", language="text")



    else:



        st.markdown(



            '<div style="color:#A3AEC2;font-size:0.85rem;">Click <b>Run Tests Now</b> to execute the '



            "23 edge-case tests, or run <code>python -m pytest tests/ -v</code> in a terminal.</div>",



            unsafe_allow_html=True,



        )







    st.markdown(



        '<div style="margin-top:12px;font-size:0.8rem;color:#3B4563;">'



        "Review statuses and rule settings are saved locally in evidentrace.db (SQLite).</div>",



        unsafe_allow_html=True,



    )