"""Build synthetic dependence inputs; no leakage/dependence calculation is run."""

from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.gasket_correlated_uncertainty import (
    GasketLeakageCorrelatedScenario, GasketLeakageCorrelatedScenarioEnvelope,
    GasketLeakageWeightedScenarioMoments,
)
from matintegrity.models.gasket_leakage_calibration import GasketLeakageCalibrationMap, GasketLeakageCalibrationRow
from matintegrity.models.gasket_finite_scenario_dependence import GasketFiniteScenarioDependence

calibration = GasketLeakageCalibrationMap(
    differential_pressure_Pa=(0.0, 2e6),
    rows=(GasketLeakageCalibrationRow(contact_pressure_Pa=0.0, molar_leak_flux_by_delta_pressure_mol_s_m2=(0.0, 1e-8)),
          GasketLeakageCalibrationRow(contact_pressure_Pa=2e6, molar_leak_flux_by_delta_pressure_mol_s_m2=(0.0, 1e-9))),
)
scenarios = tuple(GasketLeakageCorrelatedScenario(
    scenario_id=name, node_contact_pressure_Pa=(pressure,), common_differential_pressure_Pa=delta,
    node_area_m2=(area,), calibration_flux_by_contact_pressure_and_delta=((0.0, 1e-8), (0.0, 1e-9)),
) for name, pressure, delta, area in (
    ("synthetic-A", 0.5e6, 0.5e6, 0.01),
    ("synthetic-B", 1.5e6, 1.0e6, 0.012),
    ("synthetic-C", 1.0e6, 1.5e6, 0.011),
))
scenario_digest = canonical_digest([row.model_dump(mode="json") for row in scenarios])
rights = Evidence(source_id="synthetic-rights", origin="synthetic", citation="Fabricated API values only.", license_id="synthetic-fixture-MIT")
envelope = GasketLeakageCorrelatedScenarioEnvelope(
    assessment_id="synthetic-dependence", asset_id="synthetic-asset", joint_id="synthetic-joint",
    physical_scope_id="synthetic-surface", time_s=0.0, node_ids=("node-A",), calibration=calibration,
    calibration_provider_id="synthetic-calibration", calibration_provider_revision="fixture-1",
    calibration_record_sha256="a" * 64, scenario_provider_id="synthetic-scenarios",
    scenario_provider_revision="fixture-1", scenario_set_sha256=scenario_digest, scenarios=scenarios,
    evidence=(Evidence(source_id="synthetic-calibration", origin="synthetic", citation="Synthetic calibration grid.", sha256="a" * 64),
              Evidence(source_id="synthetic-scenarios", origin="synthetic", citation="Synthetic joint scenario rows.", sha256=scenario_digest)),
    usage_rights_evidence=(rights,), usage_license_id="synthetic-fixture-MIT",
    joint_scenario_correlation_reviewed=True, scenario_coverage_and_bounds_reviewed=True,
    calibration_and_joint_match_reviewed=True, area_partition_and_units_reviewed=True,
    usage_rights_reviewed=True, computational_use_authorized=True,
)
weighted = GasketLeakageWeightedScenarioMoments(
    scenario_envelope=envelope, scenario_weights=(0.25, 0.5, 0.25), weight_semantics="user_declared_weight",
    weight_provider_id="synthetic-weights", weight_provider_revision="fixture-1", weight_record_sha256="b" * 64,
    weight_evidence=Evidence(source_id="synthetic-weights", origin="synthetic", citation="Synthetic scenario weights.", sha256="b" * 64),
    weight_usage_rights_evidence=(rights,), weight_usage_license_id="synthetic-fixture-MIT",
    weight_meaning_reviewed=True, weight_usage_rights_reviewed=True, weight_computational_use_authorized=True,
)
request = GasketFiniteScenarioDependence(
    weighted_scenarios=weighted, selected_node_ids=("node-A",),
    finite_set_dependence_and_variable_units_reviewed=True,
    descriptive_covariance_not_causal_or_population_inference_reviewed=True,
)

if __name__ == "__main__":
    print(request.model_dump_json(indent=2))
