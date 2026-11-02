import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.gasket_joint import GasketJointAssessment, gasket_joint_evidence, specifications
from matintegrity.registry import ModelRegistry, default_registry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def payload(**updates):
    value = {
        "assessment_id": "gasket-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "joint_id": "joint-1",
        "physical_scope_id": "scope-1",
        "flange_geometry_id": "flange-1",
        "flange_material_condition_id": "flange-material-1",
        "gasket_material_condition_id": "gasket-material-1",
        "gasket_lot_id": "gasket-lot-1",
        "bolt_material_condition_id": "bolt-material-1",
        "bolt_lot_id": "bolt-lot-1",
        "medium_id": "medium-1",
        "pressure_basis": "absolute",
        "operating_pressure_Pa": 1.0e6,
        "operating_temperature_K": 350.0,
        "bolt_preloads": tuple(
            {
                "bolt_id": f"bolt-{index}",
                "preload_value": value,
                "preload_unit_token": "custom-force",
                "measurement_method_id": "direct-preload-method",
                "expanded_uncertainty": 2.0,
                "provider_id": "assembly-provider",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            }
            for index, value in enumerate((100.0, 102.0), start=1)
        ),
        "seating_result": {
            "result_id": "seating-1",
            "metric_id": "seating-metric",
            "metric_definition": "authored seating metric",
            "reported_value": 50.0,
            "unit_token": "custom-seating-unit",
            "expanded_uncertainty": 2.0,
            "provider_id": "seating-provider",
            "provider_version": "1",
            "provider_state_digest": DIGEST_A,
            "provider_configuration_digest": DIGEST_B,
            "input_digest": DIGEST_A,
            "result_digest": DIGEST_B,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
        "relaxation_observations": (
            {
                "observation_id": "relaxation-1",
                "elapsed_time_s": 3600.0,
                "physical_specimen_id": "specimen-1",
                "source_group_id": "source-1",
                "partition": "application",
                "metric_id": "retained-preload",
                "metric_definition": "authored retained preload fraction",
                "reported_value": 0.9,
                "unit_token": "fraction",
                "expanded_uncertainty": 0.03,
                "method_id": "relaxation-method",
                "provider_id": "laboratory-1",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "flange_geometry_id": "flange-1",
                "flange_material_condition_id": "flange-material-1",
                "gasket_material_condition_id": "gasket-material-1",
                "bolt_material_condition_id": "bolt-material-1",
                "medium_id": "medium-1",
                "pressure_basis": "absolute",
                "minimum_pressure_Pa": 0.0,
                "maximum_pressure_Pa": 2.0e6,
                "minimum_temperature_K": 300.0,
                "maximum_temperature_K": 400.0,
                "preload_unit_token": "custom-force",
                "minimum_individual_preload_value": 90.0,
                "maximum_individual_preload_value": 110.0,
                "maximum_preload_coefficient_of_variation": 0.05,
                "seating_metric_support": {
                    "metric_id": "seating-metric",
                    "metric_definition": "authored seating metric",
                    "unit_token": "custom-seating-unit",
                    "minimum_supported_value": 40.0,
                    "maximum_supported_value": 60.0,
                    "maximum_supported_expanded_uncertainty": 5.0,
                    "minimum_record_count": 1,
                    "support_basis": "authored support",
                },
                "relaxation_metric_support": {
                    "metric_id": "retained-preload",
                    "metric_definition": "authored retained preload fraction",
                    "unit_token": "fraction",
                    "minimum_supported_value": 0.8,
                    "maximum_supported_value": 1.0,
                    "maximum_supported_expanded_uncertainty": 0.05,
                    "minimum_record_count": 1,
                    "support_basis": "authored support",
                },
                "qualification_evidence": (
                    {
                        "evidence_record_id": "qualification-1",
                        "physical_specimen_id": "specimen-q1",
                        "source_group_id": "source-q1",
                        "partition": "qualification",
                        "supported_metric_ids": ("seating-metric", "retained-preload"),
                        "provider_id": "qualification-provider",
                        "provider_version": "1",
                        "provider_state_digest": DIGEST_A,
                        "result_digest": DIGEST_B,
                        "record_valid": True,
                        "supports_declared_envelope": True,
                        "evidence": (EVIDENCE,),
                    },
                ),
                "minimum_source_group_count": 1,
                "qualification_basis": "authored qualification",
                "evidence": (EVIDENCE,),
            },
        ),
        "flange_gasket_bolt_material_and_lot_reviewed": True,
        "medium_pressure_basis_and_temperature_reviewed": True,
        "preload_method_units_uncertainty_and_bolt_identity_reviewed": True,
        "seating_provider_revision_configuration_and_digests_reviewed": True,
        "relaxation_clock_metrics_units_and_uncertainty_reviewed": True,
        "qualification_specimens_partitions_and_source_groups_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return GasketJointAssessment(**value)


def test_supported_joint_computes_direct_preload_statistics():
    result = gasket_joint_evidence(payload())
    assert result.status == "computed"
    assert result.values["preload_mean"] == pytest.approx(101.0)
    assert result.values["declared_evidence_outcome"] == "within_support"


def test_single_seating_result_cannot_satisfy_multiple_required_records():
    value = payload()
    envelope = value.candidate_envelopes[0]
    support = envelope.seating_metric_support.model_copy(update={"minimum_record_count": 2})
    candidate = envelope.model_copy(update={"seating_metric_support": support})
    result = gasket_joint_evidence(value.model_copy(update={"candidate_envelopes": (candidate,)}))
    assert result.status == "needs_data"
    assert result.values["seating_result_count"] == 1
    assert result.values["required_seating_result_count"] == 2


def test_default_registry_python_json_preserves_gasket_evidence():
    registry = default_registry()
    value = payload()
    context = RunContext(asset_id=value.asset_id, location_id=value.location_id, time_basis="synthetic")
    direct = registry.run("fabrication.gasket_joint_evidence", value, context)
    assert direct.status == "computed" and direct.model_version == "1.0.1"
    assert (
        direct.model_dump()
        == registry.run_json(
            "fabrication.gasket_joint_evidence", value.model_dump_json(), context
        ).model_dump()
    )


def test_scatter_or_relaxation_outside_support_is_visible():
    base = payload()
    bolt = base.bolt_preloads[1].model_copy(update={"preload_value": 130.0})
    relaxation = base.relaxation_observations[0].model_copy(update={"reported_value": 0.5})
    result = gasket_joint_evidence(
        base.model_copy(
            update={
                "bolt_preloads": (base.bolt_preloads[0], bolt),
                "relaxation_observations": (relaxation,),
            }
        )
    )
    assert result.status == "out_of_scope"
    assert "individual_preload" in result.values["outside_support_reasons"]
    assert result.values["outside_support_relaxation_observation_ids"] == ["relaxation-1"]


def test_unit_or_review_gap_needs_data():
    base = payload()
    bolt = base.bolt_preloads[0].model_copy(update={"preload_unit_token": "other"})
    assert (
        gasket_joint_evidence(base.model_copy(update={"bolt_preloads": (bolt, base.bolt_preloads[1])})).status
        == "needs_data"
    )
    assert (
        gasket_joint_evidence(payload(relaxation_clock_metrics_units_and_uncertainty_reviewed=False)).status
        == "needs_data"
    )


def test_duplicate_bolt_and_context_identity_are_strict():
    base = payload()
    with pytest.raises(ValueError, match="bolt IDs"):
        GasketJointAssessment(
            **base.model_dump(exclude={"bolt_preloads"}),
            bolt_preloads=(base.bolt_preloads[0], base.bolt_preloads[0]),
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.gasket_joint_evidence",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
