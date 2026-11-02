"""Illustrate the double-layer charge API with synthetic values only.

The numbers below are an API-shape example, not measured values, a steel
capacitance curve, model calibration or validation evidence.
"""

from __future__ import annotations

import json

from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.crevice_double_layer_charge_history import (
    SOURCE_ID,
    CreviceDoubleLayerChargeHistoryRequest,
    evaluate_crevice_double_layer_charge_history,
)


def build_synthetic_request() -> CreviceDoubleLayerChargeHistoryRequest:
    time_s = (0.0, 2.0)
    cell_ids = ("cell-001",)
    potentials = ((0.0,), (0.1,))
    areas = ((0.01,), (0.01,))
    reference = (0.0,)
    potential_axis = (-0.2, 0.2)
    capacitance = (20.0, 30.0)  # F/m²; synthetic teaching values
    curve = {
        "potential_axis_V": list(potential_axis),
        "differential_capacitance_F_m2": list(capacitance),
    }
    area_record = {
        "cell_ids": list(cell_ids),
        "time_s": list(time_s),
        "active_area_m2_by_knot_and_cell": [list(row) for row in areas],
        "reference_potential_V_by_cell": list(reference),
    }
    citation = "Synthetic instructional values in this project example; not experimental evidence."
    return CreviceDoubleLayerChargeHistoryRequest(
        assessment_id="synthetic-double-layer-example",
        time_s=time_s,
        cell_ids=cell_ids,
        potential_V_by_knot_and_cell=potentials,
        active_area_m2_by_knot_and_cell=areas,
        reference_potential_V_by_cell=reference,
        differential_capacitance_curve_sha256=canonical_digest(curve),
        potential_axis_V=potential_axis,
        differential_capacitance_F_m2=capacitance,
        curve_evidence=(Evidence(
            source_id=SOURCE_ID,
            origin="synthetic",
            citation=citation,
            license_id="MIT",
            sha256=canonical_digest(curve),
        ),),
        area_record_sha256=canonical_digest(area_record),
        area_evidence=(Evidence(
            source_id=SOURCE_ID,
            origin="synthetic",
            citation=citation,
            license_id="MIT",
            sha256=canonical_digest(area_record),
        ),),
        tabulated_differential_capacitance_reviewed=True,
        active_area_and_potential_alignment_reviewed=True,
        linear_charge_interpolation_between_knots_reviewed=True,
        double_layer_only_interpretation_reviewed=True,
        computation_budget_reviewed=True,
    )


if __name__ == "__main__":
    result = evaluate_crevice_double_layer_charge_history(build_synthetic_request())
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
