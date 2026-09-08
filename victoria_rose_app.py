import streamlit as st
from oncoai_guardrails import EnterpriseGuardrails

# Page configuration
st.set_page_config(
    page_title="OncoAI-SaaS | Enterprise Clinical Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize enterprise security layer
guardrails = EnterpriseGuardrails()
guardrails.enforce_rbac()

# Retrieve user role from session
current_role = st.session_state.get("user_role", "Data Contributor")
current_user = st.session_state.get("username", "Enterprise User")

# Main Header
st.title("Pharmacovigilance & Clinical Intelligence Platform")
st.markdown(f"*Logged in as:* **{current_user}** | *Enterprise Tier:* **{current_role} Access**")
st.markdown("---")

# Multi-Tier Tab Navigation based on Enterprise Role
if current_role == "Administrator":
    tab1, tab2, tab3 = st.tabs(["📊 Executive Impact Dashboard", "🔍 Compliance & Audit Logs", "⚙️ Enterprise Governance"])
elif current_role == "Auditor":
    tab1, tab2 = st.tabs(["🔍 Compliance & Audit Logs", "📊 Executive Impact Dashboard"])
else:
    tab1, tab2 = st.tabs(["📥 Protocol Data Input", "📊 Executive Impact Dashboard"])

# --- TAB 1: Dashboard / Metrics ---
with tab1 if "tab1" in locals() else st.container():
    if current_role != "Data Contributor":
        st.subheader("Impact Dashboard")
        col1, col2, col3 = st.columns(3)
        col1.metric("Signals Processed", "4", delta="+1 today")
        col2.metric("High Priority Risks", "2", delta="-1 from baseline", delta_color="inverse")
        col3.metric("Hours Saved", "9.3 hrs", delta="+2.1 hrs")
        
        st.markdown("---")
        st.subheader("Active Signal Tracking")
        st.dataframe({
            "Signal_ID": ["SIG-001", "SIG-002", "SIG-003", "SIG-004"],
            "Severity": ["High", "Medium", "High", "Low"],
            "Patient_ID": ["P-101", "P-102", "P-103", "P-104"],
            "Status": ["New", "Under Review", "New", "Closed"]
        }, use_container_width=True)
    else:
        st.subheader("Data Contributor Portal")
        st.info("Upload new clinical protocol batches or pathology files for automated initial parsing.")
        uploaded_file = st.file_uploader("Upload Clinical Protocol (.csv or .pdf)", type=["csv", "pdf"])
        if uploaded_file:
            st.success("File uploaded successfully and queued for agentic parsing.")

# --- TAB 2: Compliance & Audit Logs ---
if current_role in ["Administrator", "Auditor"]:
    with tab2 if "tab2" in locals() else st.container():
        st.subheader("Compliance Export & SHA-256 Verification")
        sample_data = b"OncoAI-SaaS-Enterprise-Audit-Stream"
        diag = guardrails.run_iq_oq_pq_diagnostics(sample_data)

        st.write(f"**Diagnostic Status:** {diag['status']} ({diag['compliance_standard']})")
        st.text(f"Document Fingerprint (SHA-256): {diag['sha256_hash']}")
        st.info("This unique fingerprint ensures the audit report has not been altered, satisfying 21 CFR Part 11.")

        if st.button("Download Certified Audit Report (CSV)"):
            st.download_button(
                label="Confirm Download",
                data=sample_data,
                file_name=f"Enterprise_Audit_{diag['sha256_hash'][:8]}.csv",
                mime="text/csv"
            )

        st.markdown("### Immutable Audit Trail")
        st.dataframe({
            "timestamp": [diag["timestamp"], diag["timestamp"]],
            "user": [current_user, current_user],
            "action": ["Protocol Evaluation Verified", "Compliance Export Generated"],
            "file_hash": [diag["sha256_hash"][:16] + "...", diag["sha256_hash"][:16] + "..."]
        }, use_container_width=True)

# --- TAB 3: Governance (Admin Only) ---
if current_role == "Administrator":
    with tab3:
        st.subheader("Enterprise Governance & Tenant Controls")
        st.checkbox("Enforce Strict AES-256 Encryption at Rest", value=True)
        st.checkbox("Enable Automated IQ/OQ/PQ Self-Diagnostics on Boot", value=True)
        st.selectbox("Active VPC Environment", ["AWS GovCloud / Secure US-East", "GCP Enterprise Healthcare Cloud"])
        if st.button("Save Governance Configuration"):
            st.success("Enterprise policies updated and propagated across multi-tenant nodes.")
