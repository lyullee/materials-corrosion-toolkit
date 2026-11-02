"""Synthetic caller-data example for the dynamic Cdl/Faradaic history API."""

from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.crevice_dynamic_double_layer_faradaic_history import (
    SOURCE_ID,
    CreviceDynamicDoubleLayerFaradaicHistoryRequest,
    DynamicDoubleLayerPolarizationBranch,
    solve_crevice_dynamic_double_layer_faradaic_history,
)


def evidence(digest: str, citation: str) -> Evidence:
    return Evidence(source_id=SOURCE_ID, origin="synthetic", citation=citation,
                    license_id="CC0-1.0", sha256=digest)


def build_request() -> CreviceDynamicDoubleLayerFaradaicHistoryRequest:
    time_s = (0.0, 0.01, 0.02)
    cell_ids = ("cell-0",)
    area = ((0.02,), (0.02,), (0.019,))
    reference = (0.0,)
    area_record = {"time_s": list(time_s), "cell_ids": list(cell_ids),
                   "active_area_m2_by_knot_and_cell": [list(row) for row in area],
                   "reference_potential_V_by_cell": list(reference)}
    current = ((1.0e-4,), (1.0e-4,), (8.0e-5,))
    current_record = {"time_s": list(time_s), "cell_ids": list(cell_ids),
                      "total_current_A_by_knot_and_cell": [list(row) for row in current]}
    cap_axis = (-0.5, 0.0, 0.5)
    cap_values = (10.0, 15.0, 12.0)
    cap_record = {"potential_axis_V": list(cap_axis),
                  "differential_capacitance_F_m2": list(cap_values)}
    eta = (-0.3, 0.0, 0.3)
    j = ((-0.12, 0.0, 0.12),)
    equilibrium = ((0.0,), (0.0,), (0.0,))
    branch_record = {"branch_id": "synthetic-anodic-cathodic-net",
                     "overpotential_axis_V": list(eta),
                     "signed_current_density_A_m2_by_cell_and_overpotential": [list(row) for row in j],
                     "equilibrium_potential_V_by_knot_and_cell": [list(row) for row in equilibrium]}
    branch_digest = canonical_digest(branch_record)
    branch = DynamicDoubleLayerPolarizationBranch(
        **branch_record, curve_sha256=branch_digest,
        evidence=(evidence(branch_digest, "Synthetic polarization table only"),),
    )
    cap_digest = canonical_digest(cap_record)
    area_digest = canonical_digest(area_record)
    current_digest = canonical_digest(current_record)
    return CreviceDynamicDoubleLayerFaradaicHistoryRequest(
        assessment_id="synthetic-cdl-history", time_s=time_s, cell_ids=cell_ids,
        initial_potential_V_by_cell=(0.0,), reference_potential_V_by_cell=reference,
        active_area_m2_by_knot_and_cell=area, active_area_record_sha256=area_digest,
        active_area_evidence=(evidence(area_digest, "Synthetic active-area schedule only"),),
        total_current_A_by_knot_and_cell=current, total_current_record_sha256=current_digest,
        total_current_evidence=(evidence(current_digest, "Synthetic total-current schedule only"),),
        differential_capacitance_potential_axis_V=cap_axis, differential_capacitance_F_m2=cap_values,
        differential_capacitance_curve_sha256=cap_digest,
        capacitance_evidence=(evidence(cap_digest, "Synthetic Cdl curve only"),),
        faradaic_branches=(branch,),
        curve_linearity_and_no_extrapolation_reviewed=True,
        current_sign_and_external_boundary_reviewed=True,
        lumped_cell_independence_and_no_ionic_transport_reviewed=True,
        parameter_applicability_reviewed=True, computation_budget_reviewed=True,
        computational_use_authorized=True,
    )


if __name__ == "__main__":
    result = solve_crevice_dynamic_double_layer_faradaic_history(build_request())
    print(result.model_dump(mode="json"))
