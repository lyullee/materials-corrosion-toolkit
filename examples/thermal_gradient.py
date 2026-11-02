"""Couple an authored transient temperature field to an elastic section screen."""

import copy
import json
from pathlib import Path

from matintegrity import bind_thermal_temperature_profile
from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.models.thermal_transient import ThroughWallThermalStress
from matintegrity.registry import default_registry


def main():
    examples = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))["models"]
    registry = default_registry()
    context = RunContext(
        asset_id="authored-wall",
        location_id="through-thickness-profile",
        time_basis="elapsed seconds from synthetic boundary change",
    )
    heat = registry.run_json(
        "thermal.transient_conduction_1d",
        json.dumps(examples["thermal.transient_conduction_1d"]),
        context,
    )
    stress_inputs = copy.deepcopy(examples["mechanics.through_wall_thermal_stress"])
    stress_inputs["position_m"] = heat.values["cell_centers_m"]
    synthetic_property_source = canonical_digest({"example": "synthetic thermal-stress properties v1"})
    stress_inputs["material_condition_id"] = "synthetic-example-condition-v1"
    stress_inputs["property_profile_evidence"] = [
        {
            "quantity": quantity,
            "provider_id": "matintegrity.synthetic.example",
            "provider_revision": "1",
            "record_id": f"synthetic-{quantity}-profile-v1",
            "source_sha256": synthetic_property_source,
            "evidence": [
                Evidence(
                    source_id="matintegrity.synthetic.example",
                    origin="synthetic",
                    citation="Synthetic values authored for the MatIntegrity wiring example; not material data.",
                    sha256=synthetic_property_source,
                    locator="examples/thermal_gradient.py",
                ).model_dump(mode="json")
            ],
        }
        for quantity in (
            "secant_thermal_expansion_1_K",
            "elastic_modulus_Pa",
            "poisson_ratio",
            "elastic_limit_Pa",
        )
    ]
    stress_request = ThroughWallThermalStress.model_validate(stress_inputs)
    stress_request = bind_thermal_temperature_profile(
        stress_request,
        heat,
        canonical_digest(heat.model_dump(mode="json")),
        len(heat.values["temperature_history_K"]) - 1,
        temperature_to_section_mapping_reviewed=True,
    )
    stress = registry.run("mechanics.through_wall_thermal_stress", stress_request, context)
    print(
        json.dumps(
            {
                "heat_status": heat.status,
                "stress_status": stress.status,
                "final_temperature_K": heat.values["temperature_history_K"][-1],
                "stress_Pa": stress.values["stress_Pa"],
                "mechanical_property_lineage": stress.values["mechanical_property_lineage"],
                "maximum_evaluated_elastic_limit_utilization": stress.values[
                    "maximum_evaluated_elastic_limit_utilization"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
