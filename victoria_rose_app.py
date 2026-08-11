import streamlit as st
import pandas as pd
import datetime
import hashlib
import sqlite3
from datetime import datetime as dt

AUDIT_DB = "audit_trail.db"

# --- Page Configuration ---
st.set_page_config(page_title="PV Intelligence Platform | Agentic Audit", layout="wide")

# --- Helper: Generate Hash ---
def generate_hash(data_string):
    """Creates a unique SHA-256 fingerprint for the data."""
    return hashlib.sha256(data_string.encode()).hexdigest()

# --- SQLite Audit Trail ---
def init_audit_db():
    conn = sqlite3.connect(AUDIT_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_hash TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

def log_to_audit_trail(filename, file_hash):
    """Record filename, file_hash, and current timestamp to audit_trail.db."""
    init_audit_db()
    conn = sqlite3.connect(AUDIT_DB)
    conn.execute(
        "INSERT INTO audit_logs (timestamp, filename, file_hash) VALUES (?, ?, ?)",
        (dt.now().strftime("%Y-%m-%d %H:%M:%S"), filename, file_hash),
    )
    conn.commit()
    conn.close()

def get_recent_audit_logs(limit=10):
    init_audit_db()
    conn = sqlite3.connect(AUDIT_DB)
    df = pd.read_sql(
        """
        SELECT timestamp, filename, file_hash
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        conn,
        params=(limit,),
    )
    conn.close()
    return df

# --- Mock Data Generation ---
def get_data():
    data = {
        'Signal_ID': ['SIG-001', 'SIG-002', 'SIG-003', 'SIG-004'],
        'Severity': ['High', 'Medium', 'High', 'Low'],
        'Patient_ID': ['P-101', 'P-102', 'P-103', 'P-104'],
        'Status': ['New', 'Under Review', 'New', 'Closed']
    }
    return pd.DataFrame(data)

# --- Autonomous Audit Agent ---
def run_autonomous_audit(df):
    st.sidebar.markdown("### 🤖 Agentic Audit Status")
    risks = df[(df['Severity'] == 'High') & (df['Status'] == 'New')]

    if not risks.empty:
        st.sidebar.error(f"⚠️ ALERT: {len(risks)} High-Severity Signals Unaddressed!")
    else:
        st.sidebar.success("✅ Audit Passed: All signals compliant.")

# --- Main App Execution ---
df = get_data()
st.title("Pharmacovigilance Intelligence Platform")
st.markdown("---")

run_autonomous_audit(df)

# ROI Metrics
st.markdown("### 📈 Impact Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Signals Processed", len(df))
col2.metric("High Priority Risks", len(df[df['Severity'] == 'High']))
col3.metric("Hours Saved", "9.3 hrs")
st.markdown("---")

# Data Table
st.dataframe(df, width="stretch")

# Compliance Export with Hashing
st.markdown("### Compliance Export")
csv_data = df.to_csv(index=False)
report_hash = generate_hash(csv_data)
export_filename = f"PV_Audit_{datetime.datetime.now().strftime('%Y%m%d')}.csv"

log_to_audit_trail(export_filename, report_hash)

st.write(f"**Document Fingerprint (SHA-256):** `{report_hash}`")
st.info("This unique fingerprint ensures the audit report has not been altered.")

st.download_button(
    label="Download Certified Audit Report (CSV)",
    data=csv_data.encode('utf-8'),
    file_name=export_filename,
    mime="text/csv"
)

# Audit trail — last 10 entries
st.markdown("---")
st.markdown("### Audit Trail (Last 10 Logs)")
recent_logs = get_recent_audit_logs(10)
if recent_logs.empty:
    st.info("No audit entries recorded yet.")
else:
    st.table(recent_logs)
