"""Synthetic cycle-domain request/provider only; no calculation is executed."""

from matintegrity.adaptive_cycle_block_damage import (
    AdaptiveCycleBlockDamageRequest,
    CycleBlockLawParameter,
    IntegerCycleDamageBlock,
)
from matintegrity.contracts import Evidence

request = AdaptiveCycleBlockDamageRequest(
    analysis_id="synthetic-cycle-ode", physical_scope_id="synthetic-point",
    material_condition_id="synthetic-material", cycle_count_basis_id="synthetic-full-cycles",
    provider_id="synthetic-cycle-law", provider_revision="fixture-1",
    provider_configuration_sha256="a" * 64, calibration_sha256="b" * 64,
    state_variable_ids=("synthetic_memory",), state_units=("1",),
    initial_state=(0.0,), minimum_state=(0.0,), maximum_state=(10.0,),
    blocks=(IntegerCycleDamageBlock(
        block_id="block-A", cycle_population_id="synthetic-population",
        loading_state_id="synthetic-load-A", cycle_count=100, source_sha256="c" * 64,
        parameters=(CycleBlockLawParameter(parameter_id="memory_source", value=0.001, unit="1/cycle"),),
    ),),
    initial_step_cycles=1.0, minimum_step_cycles=1e-6, maximum_step_cycles=10.0,
    state_absolute_tolerance=(1e-10,), state_relative_tolerance=1e-6,
    damage_absolute_tolerance=1e-12, damage_relative_tolerance=1e-6,
    ordered_integer_blocks_and_cycle_count_basis_reviewed=True,
    state_law_and_nonnegative_damage_rate_reviewed=True,
    initialization_bounds_and_event_meaning_reviewed=True,
    deterministic_repeat_evaluation_reviewed=True,
    adaptive_controls_and_local_error_meaning_reviewed=True,
    material_calibration_and_usage_rights_reviewed=True, computational_use_authorized=True,
    evidence=(Evidence(source_id="synthetic-cycle-law", origin="synthetic",
        citation="Fabricated numerical API fixture, not a material fatigue law.",
        license_id="synthetic-fixture-MIT", sha256="b" * 64),),
)


def synthetic_provider(local_cycle_coordinate, state, block):
    source = block.parameters[0].value
    return {"state_derivative_per_cycle": (source - 0.01 * state[0],),
            "damage_rate_per_cycle": 1e-6 * (1.0 + state[0])}


synthetic_provider.provider_id = "synthetic-cycle-law"
synthetic_provider.revision = "fixture-1"
synthetic_provider.configuration_sha256 = "a" * 64
synthetic_provider.calibration_sha256 = "b" * 64
synthetic_provider.state_variable_ids = ("synthetic_memory",)
synthetic_provider.state_units = ("1",)
synthetic_provider.cycle_count_basis_id = "synthetic-full-cycles"
synthetic_provider.damage_unit = "1"

if __name__ == "__main__":
    print(request.model_dump_json(indent=2))
