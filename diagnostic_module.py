# diagnostic_module.py
import numpy as np
from typing import Dict, Any

class DiagnosticPredictor:
    def __init__(self):
        # Weighted coefficients for early-onset signal calibration
        self.weights = {
            "cfdna_conc": 0.25,
            "fragmentomics": 0.30,
            "methylation": 0.35,
            "mutation_burden": 0.10
        }

    def compute_risk_score(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        score = 0.0
        confidence = 0.95
        attributions = {}

        if payload.get("liquid_data"):
            liq = payload["liquid_data"]
            # Normalize and weigh liquid markers
            cfdna_score = min(liq.get("cfdna_concentration_ng_ml", 0.0) / 50.0, 1.0)
            frag_score = liq.get("fragmentomics_score", 0.0)
            meth_score = liq.get("methylation_signature_score", 0.0)
            
            mutations = liq.get("mutations", [])
            mutation_score = min(len(mutations) * 0.2, 1.0)

            score = (
                (cfdna_score * self.weights["cfdna_conc"]) +
                (frag_score * self.weights["fragmentomics"]) +
                (meth_score * self.weights["methylation"]) +
                (mutation_score * self.weights["mutation_burden"])
            )

            attributions = {
                "cfdn_a_contribution": cfdna_score * self.weights["cfdna_conc"],
                "fragmentomics_contribution": frag_score * self.weights["fragmentomics"],
                "methylation_contribution": meth_score * self.weights["methylation"],
                "somatic_mutation_count": len(mutations)
            }
        
        # Binary classification mapping with thresholding
        malignancy_probability = float(1.0 / (1.0 + np.exp(-10 * (score - 0.5))))
        
        return {
            "malignancy_probability": round(malignancy_probability, 4),
            "risk_tier": "HIGH" if malignancy_probability > 0.7 else ("MODERATE" if malignancy_probability > 0.4 else "LOW"),
            "feature_attributions": attributions,
            "model_confidence": confidence
        }
