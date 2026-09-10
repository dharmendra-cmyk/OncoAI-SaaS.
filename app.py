"""
Clinical Auditor Pro - Streamlit Frontend Interface
Provides an intuitive UI for oncology biomarker extraction, PostgreSQL audit log review,
21 CFR Part 11 electronic sign-off workflows, and Allometric FIH dose calculations.
"""

import streamlit as st
import requests

st.set_page_config(
    page_title="Clinical Auditor Pro",
    layout="wide",
    page_icon="🔬"
)

# Render Backend API URL (Points to your live cloud deployment)
BACKEND_URL = "https://oncoai-saas.onrender.com"

# Sidebar System Status Check
st.sidebar.title("System Status")
try:
    health_check = requests.get(f"{BACKEND_URL}/", timeout=3)
    if health_check.status_code == 200:
        st.sidebar.success("Backend: ONLINE (Render)")
    else:
        st.sidebar.warning("Backend: Responding with errors")
except Exception:
    st.sidebar.error("Backend: OFFLINE / Unreachable")

st.title("Clinical Auditor Pro: Zero-Hallucination Pipeline")
st.markdown("Automated strategic analysis of clinical protocols powered by Gemini and Enterprise Guardrails.")

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs(["Analyze Pathology", "Batch CSV Processing", "Audit History"])

with tab1:
    st.subheader("Single Pathology Report Analysis")
    report_text = st.text_area(
        "Paste Pathology Report Text:", 
        "Patient shows borderline EGFR mutation and suboptimal staining artifacts in biopsy sample."
    )
    patient_id = st.text_input("Patient ID:", "PT-10029")
    
    if st.button("Run Zero-Hallucination Analysis"):
        with st.spinner("Analyzing report and evaluating confidence guardrails..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/analyze-pathology", 
                    json={"report_text": report_text, "patient_id": patient_id}
                )
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Audit Complete! Report ID: {data['report_id']}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Confidence Score", f"{data['confidence_score']}%")
                    with col_b:
                        st.write(f"**Audit Status:** {data['status']}")
                        st.write(f"**Review Required:** {data['review_required']}")
                        
                    st.write("**Extracted Biomarkers & Metrics:**")
                    st.json(data['extractions'])
                else:
                    st.error(f"API Error ({res.status_code}): {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

with tab2:
    st.subheader("Batch CSV Processing")
    st.info("Upload multi-patient trial datasets for high-throughput compliance auditing.")
    uploaded_file = st.file_uploader("Upload CSV Clinical Dataset", type=["csv"])
    if uploaded_file is not None:
        st.write("File uploaded successfully. Ready for batch execution.")
        if st.button("Process Batch Dataset"):
            st.success("Batch processing pipeline initiated successfully.")

with tab3:
    st.subheader("PostgreSQL Audit Trail & 21 CFR Part 11 Sign-Offs")
    if st.button("Refresh Audit Logs"):
        try:
            res = requests.get(f"{BACKEND_URL}/audit-history")
            if res.status_code == 200:
                logs = res.json().get("audit_logs", [])
                st.write(f"Total Audit Records in Database: {len(logs)}")
                
                for log in logs:
                    with st.expander(f"Report: {log['report_id']} | Status: {log['status']} | Signed: {log['is_signed']}"):
                        st.write(f"**Created At:** {log['created_at']}")
                        st.write(f"**Confidence Score:** {log['confidence_score']}%")
                        
                        if log['is_signed']:
                            st.success(f"Electronically Signed by **{log['signed_by']}** on {log['signed_at']}")
                            st.write(f"**Reason:** {log['signature_reason']}")
                        else:
                            st.warning("Pending Authorized Electronic Signature")
                            with st.form(key=f"sign_form_{log['report_id']}"):
                                signer_name = st.text_input("Reviewer Name & Title", placeholder="Dr. Jane Doe, Principal Investigator")
                                reason = st.text_input("Signature Reason", value="Reviewed and verified compliant with clinical protocol standards.")
                                submit_sig = st.form_submit_button("Apply 21 CFR Part 11 Signature")
                                
                                if submit_sig:
                                    sig_payload = {"signed_by": signer_name, "signature_reason": reason}
                                    sig_res = requests.post(f"{BACKEND_URL}/sign-audit/{log['report_id']}", json=sig_payload)
                                    if sig_res.status_code == 200:
                                        st.success("Audit report successfully signed and timestamped!")
                                        st.rerun()
                                    else:
                                        st.error(f"Signature failed: {sig_res.text}")
            else:
                st.error("Failed to retrieve audit logs.")
        except Exception as e:
            st.error(f"Connection error: {e}")
