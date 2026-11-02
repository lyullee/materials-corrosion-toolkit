"""Unexecuted adapter example using an externally reviewed assessment receipt."""

from matintegrity.contracts import AssessmentResult, Evidence, RunContext
from matintegrity.ti12mo5zr_remaining_thickness import (
    RemainingThicknessRequest,
    build_remaining_thickness_history,
)


def adapt_reviewed_result(
    assessment: AssessmentResult,
    expected_input_digest: str,
    expected_result_digest: str,
    expected_mass_balance_digest: str,
    matching_context: RunContext,
    reviewed_baseline_thickness_m: float,
):
    request = RemainingThicknessRequest(
        assessment=assessment,
        expected_assessment_input_digest=expected_input_digest,
        expected_assessment_result_digest=expected_result_digest,
        expected_mass_balance_result_digest=expected_mass_balance_digest,
        expected_run_context=matching_context,
        baseline_thickness_m=reviewed_baseline_thickness_m,
        baseline_thickness_evidence=Evidence(
            source_id="caller-baseline-thickness",
            origin="measured",
            citation="Replace with the reviewed inspection record and measurement basis.",
        ),
        uniform_area_basis_authorized=True,
        density_material_applicability_authorized=True,
        computational_use_authorized=True,
        local_only_authorized=True,
    )
    return build_remaining_thickness_history(request)


# This file is documentation only; no assessment is supplied or evaluated here.
