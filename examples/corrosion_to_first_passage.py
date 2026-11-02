"""Compose reviewed model-output rate scenarios into a conditional first-passage event."""

from matintegrity import evaluate
from matintegrity.adapters import probability_event
from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.corrosion import (
    CorrosionRateModelOutputWallLossScenario,
    CorrosionRateProjectionRow,
    corrosion_model_output_to_first_passage_inputs,
)

source_sha256 = "c" * 64
evidence = Evidence(
    source_id="synthetic-corrosion-model",
    origin="model_prediction",
    citation="Synthetic corrosion scenario fixture",
    license_id="MIT",
    sha256=source_sha256,
)
scenario = CorrosionRateModelOutputWallLossScenario(
    rows=[
        CorrosionRateProjectionRow(
            scenario_id="rate-low",
            source_dataset_id="synthetic-corrosion-model",
            source_group_id="synthetic-run-1",
            source_record_id="row-1",
            source_archive_sha256=source_sha256,
            source_role="simulated_model_output",
            rate_m_s=0.5e-10,
            evidence=(evidence,),
        ),
        CorrosionRateProjectionRow(
            scenario_id="rate-high",
            source_dataset_id="synthetic-corrosion-model",
            source_group_id="synthetic-run-1",
            source_record_id="row-2",
            source_archive_sha256=source_sha256,
            source_role="simulated_model_output",
            rate_m_s=1.0e-10,
            evidence=(evidence,),
        ),
    ],
    current_thickness_m=0.01,
    required_thickness_m=0.008,
    horizon_s=50e6,
    material_state_compatibility_reviewed=True,
    material_state_review_id="review:material",
    condition_transferability_reviewed=True,
    condition_transfer_review_id="review:condition-transfer",
    linear_loss_model_reviewed=True,
    linear_loss_model_review_id="review:constant-rate-loss",
    scenario_weights=[0.25, 0.75],
    weight_meaning="caller_declared_scenario_weight",
    scenario_set_id="synthetic-rate-distribution",
)

first_passage_input = corrosion_model_output_to_first_passage_inputs(
    scenario,
    forecast_id="synthetic-first-passage",
    asset_id="asset-1",
    location_id="cml-1",
    physical_scope_id="circuit-1/cml-1",
    physical_location_id="cml-1",
    time_basis="elapsed seconds",
    assessment_time_s=0.0,
    conditioning="survived above the reviewed minimum thickness at assessment",
    event_id="minimum-thickness-first-crossing",
    event_definition="first crossing of the caller-reviewed required thickness",
    distribution_definition_id="reviewed-two-rate-distribution",
    sample_design_id="synthetic-design-1",
    candidate_horizon_end_s=[10e6, 20e6, 30e6, 50e6],
    current_thickness_at_assessment_review_id="review:assessment-thickness",
    samples_conditioned_on_survival_to_assessment=True,
    constant_nonnegative_loss_model_reviewed=True,
    joint_sample_distribution_reviewed=True,
    required_thickness_basis_reviewed=True,
    candidate_horizons_reviewed=True,
    review_reference_ids={
        "samples_conditioned_on_survival_to_assessment": "review:survival-conditioning",
        "constant_nonnegative_loss_model_reviewed": "review:rate-law",
        "joint_sample_distribution_reviewed": "review:joint-distribution",
        "required_thickness_basis_reviewed": "review:threshold",
        "candidate_horizons_reviewed": "review:time-grid",
    },
)
context = RunContext(asset_id="asset-1", location_id="cml-1", time_basis="elapsed seconds")
forecast = evaluate(
    "reliability.sampled_linear_thickness_first_passage",
    first_passage_input.model_dump(mode="json"),
    context,
)

# EventProbability is created only from the reviewed first-passage calculation.
event = probability_event(
    forecast,
    event_id="minimum-thickness-first-crossing",
    physical_scope_id="circuit-1/cml-1",
    failure_mode="caller-defined-thickness-threshold-crossing",
    horizon_start_s=0.0,
    horizon_end_s=50e6,
    conditioning="survived above the reviewed minimum thickness at assessment",
)
print(forecast.values["forecast_points"])
print(event.model_dump(mode="json"))
