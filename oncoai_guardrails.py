"""
OncoAI Zero-Hallucination Guardrail Engine.

Validates LLM-extracted biomarkers against verbatim PDF citations and maps
verified driver mutations to NCCN-aligned therapy class hints for downstream
clinical decision support (human-in-the-loop required).
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, Final, Mapping, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REQUIRES_HUMAN_VERIFICATION = "REQUIRES_HUMAN_VERIFICATION"


class CitationMetadata(BaseModel):
    """Verifiable span tied to a PDF page."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    page_num: int = Field(..., ge=1, description="1-based page index in source PDF text")
    extracted_text: str = Field(..., min_length=1)
    context_before: Optional[str] = Field(
        default=None,
        description="Optional leading context window stored by the extractor",
    )
    context_after: Optional[str] = Field(
        default=None,
        description="Optional trailing context window stored by the extractor",
    )

    @field_validator("extracted_text")
    @classmethod
    def _non_blank_extracted(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("extracted_text must contain non-whitespace characters")
        return value


class BiomarkerExtraction(BaseModel):
    """Structured biomarker / genomic finding from an LLM pipeline."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    biomarker_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    raw_value: Optional[str] = None
    driver_mutation_key: Optional[str] = Field(
        default=None,
        description="Normalized key into VERIFIED_DRIVER_THERAPY_MAP when matched",
    )
    citation: CitationMetadata
    llm_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class GuardrailResult(BaseModel):
    """Output of citation + therapy mapping guardrails for one extraction."""

    model_config = ConfigDict(frozen=True)

    status: VerificationStatus
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    biomarker: BiomarkerExtraction
    citation_verified: bool
    therapy_class: Optional[str] = None
    flags: Tuple[str, ...] = Field(default_factory=tuple)
    notes: Tuple[str, ...] = Field(default_factory=tuple)


# Immutable NCCN-aligned therapy class hints for verified actionable drivers.
# Keys are canonical display strings produced after normalization.
VERIFIED_DRIVER_THERAPY_MAP: Final[Mapping[str, str]] = {
    "EGFR Exon 19 Deletion": "TKIs / Osimertinib",
    "EGFR L858R": "TKIs / Osimertinib",
    "ALK Rearrangement": "ALK inhibitors / Alectinib",
    "ROS1 Rearrangement": "ROS1 inhibitors / Entrectinib",
    "KRAS G12C": "KRAS G12C inhibitors / Sotorasib",
    "BRAF V600E": "BRAF/MEK inhibitors / Dabrafenib + Trametinib",
    "MET Exon 14 Skipping": "MET inhibitors / Capmatinib",
    "RET Fusion": "RET inhibitors / Selpercatinib",
    "NTRK Fusion": "TRK inhibitors / Larotrectinib",
    "PD-L1 positive": "Immunotherapy / Pembrolizumab (TPS ≥1%)",
    "PD-L1 high": "Immunotherapy / Pembrolizumab (TPS ≥50%)",
    "HER2 Exon 20 Insertion": "Antibody-drug conjugates / Trastuzumab deruxtecan",
}


_DRIVER_ALIASES: Final[Mapping[str, str]] = {
    "egfr exon 19 del": "EGFR Exon 19 Deletion",
    "egfr exon 19 deletion": "EGFR Exon 19 Deletion",
    "exon 19 deletion": "EGFR Exon 19 Deletion",
    "egfr l858r": "EGFR L858R",
    "alk fusion": "ALK Rearrangement",
    "alk rearrangement": "ALK Rearrangement",
    "kras g12c mutation": "KRAS G12C",
    "kras g12c": "KRAS G12C",
    "pd-l1 ≥50%": "PD-L1 high",
    "pd-l1 tps ≥50%": "PD-L1 high",
    "pd-l1 positive": "PD-L1 positive",
    "pdl1 positive": "PD-L1 positive",
}


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _split_pdf_pages(source_pdf_text: str) -> list:
    if "\f" in source_pdf_text:
        return source_pdf_text.split("\f")
    if re.search(r"\[PAGE\s+\d+\]", source_pdf_text, flags=re.IGNORECASE):
        parts = re.split(r"\[PAGE\s+\d+\]", source_pdf_text, flags=re.IGNORECASE)
        return [p for p in parts if p.strip()]
    return [source_pdf_text]


def _page_text(source_pdf_text: str, page_num: int) -> str:
    pages = _split_pdf_pages(source_pdf_text)
    if 1 <= page_num <= len(pages):
        return pages[page_num - 1]
    return source_pdf_text


def validate_verbatim_citation(
    extracted_text: str,
    source_pdf_text: str,
    page_num: int,
) -> bool:
    """
    Return True iff ``extracted_text`` appears verbatim in the PDF text for ``page_num``.

    Matching is byte-for-character on the page slice after stripping outer whitespace
    only on the query string; internal whitespace must match the source exactly.
    A secondary check allows a single collapsed-whitespace variant when the PDF
    layer inserted inconsistent line breaks (still deterministic).
    """
    if not extracted_text or not source_pdf_text:
        return False

    page = _page_text(source_pdf_text, page_num)
    if extracted_text in page:
        return True

    collapsed_query = _normalize_whitespace(extracted_text)
    if collapsed_query in _normalize_whitespace(page):
        return True

    return False


def _resolve_driver_key(display_name: str, raw_value: Optional[str]) -> Optional[str]:
    candidates = [display_name]
    if raw_value:
        candidates.append(raw_value)
    for candidate in candidates:
        canonical = candidate.strip()
        if canonical in VERIFIED_DRIVER_THERAPY_MAP:
            return canonical
        alias_key = _normalize_whitespace(candidate).lower()
        if alias_key in _DRIVER_ALIASES:
            return _DRIVER_ALIASES[alias_key]
    return None


def _score_confidence(
    *,
    citation_ok: bool,
    driver_key: Optional[str],
    llm_confidence: Optional[float],
) -> float:
    score = 0.35
    if citation_ok:
        score += 0.45
    if driver_key and driver_key in VERIFIED_DRIVER_THERAPY_MAP:
        score += 0.15
    if llm_confidence is not None:
        score = min(1.0, score * 0.7 + llm_confidence * 0.3)
    return round(min(1.0, max(0.0, score)), 3)


def process_and_guardrail_extraction(
    raw_llm_json: Dict[str, Any],
    source_pdf_text: str,
) -> GuardrailResult:
    """
    Parse LLM JSON, validate verbatim citation, map drivers to therapy classes,
    and flag any mismatch as REQUIRES_HUMAN_VERIFICATION.
    """
    biomarker = BiomarkerExtraction.model_validate(raw_llm_json)

    citation_ok = validate_verbatim_citation(
        biomarker.citation.extracted_text,
        source_pdf_text,
        biomarker.citation.page_num,
    )

    driver_key = biomarker.driver_mutation_key or _resolve_driver_key(
        biomarker.display_name,
        biomarker.raw_value,
    )

    flags: list[str] = []
    notes: list[str] = []

    if not citation_ok:
        flags.append("CITATION_NOT_VERBATIM")
        notes.append(
            f"Extracted span not found verbatim on page {biomarker.citation.page_num}."
        )

    therapy_class: Optional[str] = None
    if driver_key:
        therapy_class = VERIFIED_DRIVER_THERAPY_MAP.get(driver_key)
        if therapy_class is None:
            flags.append("UNKNOWN_DRIVER_KEY")
            notes.append(f"Driver key {driver_key!r} is not in therapy map.")
    else:
        flags.append("DRIVER_NOT_MAPPED")
        notes.append("No NCCN-aligned driver key could be resolved.")

    status = (
        VerificationStatus.VERIFIED
        if citation_ok and not flags
        else VerificationStatus.REQUIRES_HUMAN_VERIFICATION
    )

    if citation_ok and flags:
        # Citation holds but therapy mapping uncertain — still human review.
        status = VerificationStatus.REQUIRES_HUMAN_VERIFICATION

    confidence = _score_confidence(
        citation_ok=citation_ok,
        driver_key=driver_key if therapy_class else None,
        llm_confidence=biomarker.llm_confidence,
    )

    if status is VerificationStatus.REQUIRES_HUMAN_VERIFICATION:
        confidence = min(confidence, 0.79)

    enriched = biomarker.model_copy(
        update={"driver_mutation_key": driver_key or biomarker.driver_mutation_key}
    )

    return GuardrailResult(
        status=status,
        confidence_score=confidence,
        biomarker=enriched,
        citation_verified=citation_ok,
        therapy_class=therapy_class,
        flags=tuple(flags),
        notes=tuple(notes),
    )


if __name__ == "__main__":
    sample_pdf = (
        "[PAGE 1]\n"
        "Molecular profiling: EGFR Exon 19 Deletion detected.\n"
        "PD-L1 TPS 60% (positive).\n"
        "\f"
        "[PAGE 2]\n"
        "Recommendation: consider osimertinib per NCCN.\n"
    )

    verified_payload = {
        "biomarker_id": "bm-001",
        "display_name": "EGFR Exon 19 Deletion",
        "raw_value": "Exon 19 deletion",
        "llm_confidence": 0.92,
        "citation": {
            "page_num": 1,
            "extracted_text": "EGFR Exon 19 Deletion detected",
        },
    }

    verified_result = process_and_guardrail_extraction(verified_payload, sample_pdf)
    assert verified_result.status is VerificationStatus.VERIFIED
    assert verified_result.citation_verified is True
    assert verified_result.therapy_class == "TKIs / Osimertinib"
    print("PASS verified extraction:", verified_result.model_dump_json(indent=2))

    hallucinated_payload = {
        "biomarker_id": "bm-002",
        "display_name": "KRAS G12C",
        "driver_mutation_key": "KRAS G12C",
        "citation": {
            "page_num": 1,
            "extracted_text": "KRAS G12C mutation present",
        },
    }

    hallucinated_result = process_and_guardrail_extraction(
        hallucinated_payload, sample_pdf
    )
    assert hallucinated_result.status is VerificationStatus.REQUIRES_HUMAN_VERIFICATION
    assert "CITATION_NOT_VERBATIM" in hallucinated_result.flags
    print("PASS hallucination flagged:", hallucinated_result.model_dump_json(indent=2))

    print("All oncoai_guardrails self-tests passed.")
