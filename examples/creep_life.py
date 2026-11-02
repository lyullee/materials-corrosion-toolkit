"""Synthetic specimen fitting, portable model and period-event conversion."""

import json
import math

from matintegrity import evaluate
from matintegrity.adapters import probability_event
from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.creep import CreepLifeModel


def inputs():
    stress = [s for s in (1e8, 1.5e8, 2e8, 2.5e8) for _ in range(4)]
    residual = [-0.2, -0.07, 0.07, 0.2] * 4
    return dict(
        material_condition_id="synthetic-material-state",
        stress_basis="constant_true_stress",
        temperature_basis="nominal_specified",
        family="stress_only",
        specimen_id=[f"synthetic-{i}" for i in range(len(stress))],
        initial_stress_Pa=stress,
        temperature_K=[1000.0] * len(stress),
        endpoint_time_s=[
            1e6 * (s / 1.5e8) ** -4 * math.exp(e) for s, e in zip(stress, residual, strict=True)
        ],
        right_censored=[False] * len(stress),
        temperature_tolerance_K=0.0,
        independent_specimens_confirmed=True,
        common_mechanism_and_condition_confirmed=True,
        evidence=(
            Evidence(
                source_id="synthetic",
                origin="synthetic",
                citation="Analytical synthetic power-law specimens",
                license_id="MIT",
            ),
        ),
    )


def main():
    context = RunContext(
        asset_id="synthetic",
        location_id="gauge",
        time_basis="seconds since fresh material at unchanged conditions",
    )
    fitted = evaluate("creep.lognormal_life_fit", inputs(), context)
    model = CreepLifeModel.model_validate_json(json.dumps(fitted.values["model"]))
    predicted = evaluate(
        "creep.conditional_life",
        dict(
            model=model,
            material_condition_id="synthetic-material-state",
            stress_basis="constant_true_stress",
            temperature_basis="nominal_specified",
            initial_stress_Pa=1.5e8,
            temperature_K=1000.0,
            current_age_s=1e5,
            horizon_s=9e5,
            maximum_time_extrapolation_factor=1.0,
            constant_conditions_since_fresh_material_confirmed=True,
            applicability_reviewed=True,
        ),
        context,
    )
    event = probability_event(
        predicted,
        event_id="rupture",
        physical_scope_id="gauge",
        failure_mode="constant-condition creep rupture",
        horizon_start_s=1e5,
        horizon_end_s=1e6,
        conditioning="Survived to age 100000 s; unchanged synthetic conditions",
    )
    print(json.dumps(event.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
