from __future__ import annotations

from .issues import ValidationIssue


CAUSAL_TERMS = ("导致", "造成", "使得", "引发", "驱动", "改变")
UNIVERSAL_TERMS = ("所有人", "任何人", "必然", "永久", "证明了", "彻底")
EXPERIMENTAL_DESIGNS = {"experiment", "quasi_experiment"}


def validate_evidence_language(item: dict) -> list[ValidationIssue]:
    evidence_id = str(item.get("id") or "")
    claim = str(item.get("claim_zh") or "")
    design = str(item.get("study_design") or "")
    strength = str(item.get("claim_strength") or "")
    issues: list[ValidationIssue] = []

    if design not in EXPERIMENTAL_DESIGNS and any(term in claim for term in CAUSAL_TERMS):
        issues.append(
            ValidationIssue(
                severity="error",
                code="causal_wording_for_nonexperimental_design",
                message=(
                    f"{design or 'unknown design'} cannot support causal wording "
                    "without an explicit design justification"
                ),
                item_id=evidence_id,
                location="claim_zh",
            )
        )

    if any(term in claim for term in UNIVERSAL_TERMS):
        issues.append(
            ValidationIssue(
                severity="error",
                code="universal_generalization",
                message="Claim generalizes beyond the reported sample or time boundary",
                item_id=evidence_id,
                location="claim_zh",
            )
        )

    if strength == "not_supported" and "显著" in claim and "不显著" not in claim:
        issues.append(
            ValidationIssue(
                severity="error",
                code="significance_mismatch",
                message="Unsupported evidence cannot be described as statistically significant",
                item_id=evidence_id,
                location="claim_zh",
            )
        )

    return issues
