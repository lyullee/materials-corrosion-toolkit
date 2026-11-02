"""Declared synthetic coupon uncertainty; no experimental uncertainty calibration."""

import json

from matintegrity.registry import default_registry
from matintegrity.sensitivity import (
    SobolRequest,
    analyze_sobol_evaluations,
    create_sobol_design,
    evaluate_sobol_design,
    registry_sensitivity_evaluator,
)

EVIDENCE = {
    "source_id": "authored-demo",
    "origin": "synthetic",
    "citation": "Authored example ranges; not fitted material uncertainty",
}
REQUEST = dict(
    analysis_id="synthetic-coupon-sobol",
    context=dict(
        asset_id="synthetic-coupon",
        location_id="exposed-surface",
        time_basis="fixed 86400-second coupon exposure",
    ),
    evaluator_id="corrosion.coupon_loss",
    evaluator_revision="1.0.0",
    evaluator_configuration=dict(
        model_id="corrosion.coupon_loss",
        base_inputs=dict(density_kg_m3=7800.0, duration_s=86400.0),
        bindings=[
            dict(parameter_name="mass", input_field="mass_loss_kg", input_unit="kg"),
            dict(parameter_name="area", input_field="exposed_area_m2", input_unit="m^2"),
        ],
    ),
    parameters=[
        dict(name="mass", unit="mg", family="uniform", lower=1.0, upper=3.0, evidence=[EVIDENCE]),
        dict(name="area", unit="cm^2", family="uniform", lower=1.0, upper=2.0, evidence=[EVIDENCE]),
    ],
    quantities=[dict(name="mean_penetration_m", unit="micrometer"), dict(name="rate_m_s", unit="mm/year")],
    sample_powers=[5, 7, 9],
    scrambles=4,
    seed=2026,
    independence_declared=True,
    deterministic_response_declared=True,
)


if __name__ == "__main__":
    request = SobolRequest.model_validate_json(json.dumps(REQUEST))
    design = create_sobol_design(request)
    response = registry_sensitivity_evaluator(default_registry(), request)
    evaluations = evaluate_sobol_design(design, response)
    report = analyze_sobol_evaluations(design, evaluations)
    print(
        json.dumps(
            dict(
                status=report.status,
                precision_status=report.precision_status,
                parameters=report.parameter_names,
                quantities=[
                    dict(
                        name=q.name,
                        response_unit=q.response_unit,
                        first_order=q.levels[-1].first_order,
                        total_order=q.levels[-1].total_order,
                        precision_criteria_satisfied=q.precision_criteria_satisfied,
                    )
                    for q in report.quantities
                ],
                diagnostics=report.diagnostics,
            ),
            indent=2,
        )
    )
