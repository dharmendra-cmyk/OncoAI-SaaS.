"""
Clinical Auditor Pro - Streamlit Frontend Interface
"""

import streamlit as st
import requests

st.set_page_config(
    page_title="Clinical Auditor Pro",
    layout="wide",
    page_icon="🔬"
)

BACKEND_URL = "https://oncoai-saas.onrender.com"

st.sidebar.title("System Status")
try:
    res = requests.get(f"{BACKEND_URL}/", timeout=2)
    if res.status_code == 200:
        st.sidebar.success("Backend: ONLINE (Render)")
    else:
        st.sidebar.warning("Backend: Error")
except Exception:
    st.sidebar.error("Backend: Unreachable")

st.title("Clinical Auditor Pro: Zero-Hallucination Pipeline")

tab1, tab2, tab3 = st.tabs(["Analyze Pathology", "Batch CSV Processing", "Audit History"])

with tab1:
    st.subheader("Single Pathology Report Analysis")
    report_text = st.text_area(
        "Paste Pathology Report Text:", 
        "Patient shows borderline EGFR mutation and suboptimal staining artifacts in biopsy sample."
    )
    patient_id = st.text_input("Patient ID:", "PT-10029")
    
    if st.button("Run Zero-Hallucination Analysis"):
        with st.spinner("Analyzing report..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/analyze-pathology", 
                    json={"report_text": report_text, "patient_id": patient_id},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Audit Complete! Report ID: {data.get('report_id')}")
                    st.json(data)
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

with tab2:
    st.subheader("Batch CSV Processing")
    st.info("Upload multi-patient trial datasets for high-throughput compliance auditing.")

with tab3:
    st.subheader("PostgreSQL Audit Trail")
    if st.button("Refresh Logs"):
        try:
            res = requests.get(f"{BACKEND_URL}/audit-history", timeout=5)
            if res.status_code == 200:
                st.json(res.json())
            else:
                st.error("Failed to load logs.")
        except Exception as e:
            st.error(f"Error: {e}")
