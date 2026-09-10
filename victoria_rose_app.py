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

