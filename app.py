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

st.title("Clinical Auditor Pro")
st.markdown("### Enterprise Oncology Biomarker Extraction & Compliance Suite (21 CFR Part 11)")

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs(["Pathology Analysis", "Audit Logs & E-Signatures", "Allometric FIH Dosing"])

with tab1:
    st.subheader("Zero-Hallucination Biomarker Extraction")
    report_text = st.text_area(
        "Paste Pathology Report Text:", 
        "Patient shows borderline EGFR mutation and suboptimal staining artifacts in biopsy sample."
    )
    patient_id = st.text_input("Patient ID:", "PT-10029")
    
    if st.button("Run Audit Analysis"):
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
                        
                    st.write("**Extracted Biomarkers & Metrics:**")
                    st.json(data['extractions'])
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

with tab2:
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

with tab3:
    st.subheader("First-in-Human (FIH) Allometric Scaling Calculator")
    col1, col2 = st.columns(2)
    
    with col1:
        compound = st.text_input("Compound Name", "Onco-Inhibitor Alpha")
        noael = st.number_input("Animal NOAEL (mg/kg)", value=50.0)
    with col2:
        species = st.selectbox("Animal Species", ["mouse", "rat", "dog", "monkey"])
        human_wt = st.number_input("Assumed Human Weight (kg)", value=60.0)
        
    if st.button("Calculate FIH Starting Dose"):
        payload = {
            "compound_name": compound,
            "animal_noael_mg_kg": noael,
            "animal_species": species,
            "human_weight_kg": human_wt
        }
        try:
            res = requests.post(f"{BACKEND_URL}/calculate-fih-dose", json=payload)
            if res.status_code == 200:
                fih_data = res.json()
                st.success("Allometric Scaling Calculation Complete (FDA Guidance)")
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.metric("Conservative FIH Starting Dose (1/10th HED)", f"{fih_data['conservative_fih_dose_mg_1_10th']} mg")
                with col_res2:
                    st.metric("Max Recommended Starting Dose", f"{fih_data['recommended_maximum_starting_dose_mg']} mg")
                    
                st.write(f"**Human Equivalent Dose (HED):** {fih_data['human_equivalent_dose_hed_mg_kg']} mg/kg")
                st.info(fih_data['compliance_note'])
            else:
                st.error(f"Error: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")
