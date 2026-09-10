import streamlit as st
import requests

st.set_page_config(
    page_title="Clinical Auditor Pro",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 Clinical Auditor Pro: Zero-Hallucination Pipeline")
st.markdown("Automated strategic analysis of clinical protocols powered by Gemini and Enterprise Guardrails.")

# Live API Endpoint on Render
API_BASE_URL = "https://oncoai-saas.onrender.com"

# Sidebar for Navigation / Status
st.sidebar.header("System Status")
try:
    health_res = requests.get(f"{API_BASE_URL}/")
    if health_res.status_code == 200:
        st.sidebar.success("Backend: ONLINE (Render)")
    else:
        st.sidebar.warning("Backend: Degraded")
except Exception:
    st.sidebar.error("Backend: OFFLINE")

# Main Interface Tabs
tab1, tab2 = st.tabs(["📊 Analyze Pathology", "📜 Audit History"])

with tab1:
    st.subheader("Pathology Report Analysis")
    report_input = st.text_area(
        "Paste Pathology Report Text:",
        placeholder="Enter patient biomarker findings, mutation status, and clinical notes here...",
        height=150
    )

    if st.button("Run Zero-Hallucination Analysis", type="primary"):
        if not report_input.strip():
            st.warning("Please enter valid report text before running analysis.")
        else:
            with st.spinner("Processing through Gemini & enterprise guardrails..."):
                try:
                    payload = {"report_text": report_input}
                    response = requests.post(f"{API_BASE_URL}/api/v1/analyze-pathology", json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Analysis Successful! Saved under Report ID: **{result.get('report_id')}**")
                        
                        # Display Metrics
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Status", result.get("status"))
                        col2.metric("Confidence Score", f"{result.get('confidence_score', 0.0) * 100:.1f}%")
                        col3.metric("Review Required", str(result.get("review_required")))

                        st.subheader("Extracted Biomarkers & Audit Details")
                        st.json(result)
                    else:
                        st.error(f"API Error ({response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {str(e)}")

with tab2:
    st.subheader("Recent Database Audit Logs")
    if st.button("Refresh Audit History"):
        try:
            history_res = requests.get(f"{API_BASE_URL}/api/v1/audit-history")
            if history_res.status_code == 200:
                history_data = history_res.json()
                if history_data:
                    for audit in history_data:
                        with st.expander(f"Report ID: {audit['report_id']} | Date: {audit['created_at']} | Status: {audit['status']}"):
                            st.write(f"**Overall Confidence:** {audit['overall_confidence']}")
                            st.write(f"**Review Required:** {audit['review_required']}")
                            st.write("**Extractions:**")
                            st.json(audit['extractions'])
                else:
                    st.info("No audit logs found yet.")
            else:
                st.error("Could not fetch audit history.")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
