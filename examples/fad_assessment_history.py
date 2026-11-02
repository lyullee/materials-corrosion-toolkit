"""Synthetic-only example of a digest-pinned FAD time-history assessment.

All numbers and source receipts below are illustrative synthetic values. They are
not experimental measurements, provider predictions, calibration data, or a
qualified FAD curve.
"""

from __future__ import annotations

import json

from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.fad_history import (
    FADAssessmentHistoryKnot,
    FADAssessmentHistoryRequest,
    FADHistoryProviderReceipt,
    evaluate_failure_assessment_history,
)
from matintegrity.models.fad import FailureAssessmentCurve


def synthetic_evidence(label: str, digest: str | None = None) -> Evidence:
    return Evidence(
        source_id=f"synthetic_fad_demo:{label}",
        origin="synthetic",
        citation=f"Illustrative synthetic example value only ({label}); not experimental or qualified data.",
        license_id="MIT",
        sha256=digest or canonical_digest({"synthetic_demo_label": label}),
    )


scope = dict(
    asset_id="synthetic-asset",
    location_id="synthetic-location",
    physical_scope_id="synthetic-crack-scope",
    clock_id="synthetic-seconds-v1",
    material_condition_id="synthetic-material-state",
    geometry_basis_id="synthetic-fixed-geometry-v1",
    load_history_id="synthetic-two-knot-load-history-v1",
)

curve = FailureAssessmentCurve(
    curve_id="synthetic-nonincreasing-support-example",
    assessment_basis_id="synthetic-illustration-only",
    load_ratio=(0.0, 0.5, 1.0, 1.2),
    allowable_toughness_ratio=(1.0, 0.9, 0.7, 0.0),
    validity_description="Synthetic monotone curve used only to demonstrate request and output shape.",
    evidence=(synthetic_evidence("curve-boundary"),),
)


def make_receipt(quantity: str, time_s: float, value: float) -> FADHistoryProviderReceipt:
    payload = {"scope": scope, "quantity": quantity, "time_s": time_s, "synthetic_value": value}
    result_sha256 = canonical_digest(payload)
    return FADHistoryProviderReceipt(
        quantity=quantity,
        **scope,
        time_s=time_s,
        provider_id="synthetic-demo-provider",
        result_id=f"synthetic-{quantity}-{time_s:g}",
        result_sha256=result_sha256,
        evidence=(synthetic_evidence(f"{quantity}-{time_s:g}", result_sha256),),
    )


def make_knot(time_s: float, *, k_pa_sqrt_m: float, toughness_pa_sqrt_m: float,
              stress_pa: float, strength_pa: float) -> FADAssessmentHistoryKnot:
    values = {
        "effective_mode_i_stress_intensity": k_pa_sqrt_m,
        "fracture_resistance": toughness_pa_sqrt_m,
        "reference_stress": stress_pa,
        "normalizing_strength": strength_pa,
    }
    return FADAssessmentHistoryKnot(
        time_s=time_s,
        effective_stress_intensity_Pa_sqrt_m=k_pa_sqrt_m,
        fracture_resistance_Pa_sqrt_m=toughness_pa_sqrt_m,
        reference_stress_Pa=stress_pa,
        normalizing_strength_Pa=strength_pa,
        provider_receipts=tuple(
            make_receipt(quantity, time_s, value) for quantity, value in values.items()
        ),
    )


request = FADAssessmentHistoryRequest(
    assessment_id="synthetic-fad-assessment",
    **scope,
    curve=curve,
    curve_sha256=canonical_digest(curve.model_dump(mode="json")),
    knots=(
        make_knot(
            0.0,
            k_pa_sqrt_m=40.0e6,
            toughness_pa_sqrt_m=100.0e6,
            stress_pa=200.0e6,
            strength_pa=400.0e6,
        ),
        make_knot(
            3600.0,
            k_pa_sqrt_m=110.0e6,
            toughness_pa_sqrt_m=100.0e6,
            stress_pa=300.0e6,
            strength_pa=400.0e6,
        ),
    ),
    linear_elastic_k_solution_reviewed=True,
    reference_stress_solution_reviewed=True,
    toughness_and_strength_applicability_reviewed=True,
    load_history_and_combination_reviewed=True,
    geometry_and_material_scope_reviewed=True,
    curve_applicability_reviewed=True,
)

calculation = evaluate_failure_assessment_history(request)

if __name__ == "__main__":
    print(json.dumps(calculation.model_dump(mode="json"), indent=2, ensure_ascii=False))
