import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.heat_exchanger_geometry import (
    HeatExchangerGeometryAssessment,
    heat_exchanger_geometry_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def payload(**updates):
    value = {
        "assessment_id": "geometry-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "exchanger_id": "exchanger-1",
        "shell_geometry_id": "shell-geometry-1",
        "shell_material_condition_id": "shell-condition-1",
        "shell_inside_diameter_m": 1.0,
        "shell_length_m": 5.0,
        "tube_layout": {
            "bundle_id": "bundle-1",
            "coordinate_frame_id": "bundle-frame",
            "coordinate_unit_token": "m",
            "coordinate_component_order": ("x", "y"),
            "tube_ordering_definition": "authored row-major tube IDs",
            "tube_count": 100,
            "layout_pattern_descriptor": "triangular-pattern",
            "pitch_m": 0.03,
            "tube_outer_diameter_m": 0.02,
            "tube_wall_thickness_m": 0.001,
            "tube_length_m": 5.0,
            "coordinate_array_shape": (100, 2),
            "coordinate_payload_digest": DIGEST_A,
            "evidence": (EVIDENCE,),
        },
        "tubesheets": (
            {
                "tubesheet_id": "tubesheet-1",
                "axial_coordinate_m": 0.0,
                "outer_diameter_m": 1.1,
                "thickness_m": 0.1,
                "tube_hole_count": 100,
                "material_condition_id": "tubesheet-condition-1",
                "record_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "baffles": (
            {
                "baffle_id": "baffle-1",
                "axial_coordinate_m": 1.0,
                "baffle_type_descriptor": "segmental",
                "outer_diameter_m": 0.98,
                "thickness_m": 0.01,
                "cut_or_open_fraction": 0.25,
                "record_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "provider_id": "geometry-provider",
        "provider_version": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "provider_input_digest": DIGEST_C,
        "provider_result_digest": DIGEST_D,
        "qualification_evidence": (
            {
                "evidence_record_id": "evidence-1",
                "physical_specimen_id": "specimen-1",
                "source_group_id": "source-1",
                "partition": "qualification",
                "metric_id": "tube-coordinate",
                "unit_token": "m",
                "observed_value": 0.1,
                "provider_value": 0.101,
                "expanded_uncertainty": 0.002,
                "method_id": "metrology-1",
                "provider_id": "geometry-provider",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_D,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "shell_geometry_id": "shell-geometry-1",
                "shell_material_condition_id": "shell-condition-1",
                "supported_layout_pattern_descriptors": ("triangular-pattern",),
                "supported_baffle_type_descriptors": ("segmental",),
                "minimum_shell_inside_diameter_m": 0.5,
                "maximum_shell_inside_diameter_m": 2.0,
                "minimum_shell_length_m": 1.0,
                "maximum_shell_length_m": 10.0,
                "minimum_tube_count": 10,
                "maximum_tube_count": 500,
                "minimum_baffle_count": 1,
                "maximum_baffle_count": 20,
                "metric_support": (
                    {
                        "metric_id": "tube-coordinate",
                        "unit_token": "m",
                        "maximum_absolute_difference": 0.005,
                        "minimum_record_count": 1,
                        "support_basis": "authored metrology support",
                    },
                ),
                "minimum_source_group_count": 1,
                "provider_id": "geometry-provider",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "qualification_basis": "authored provider qualification",
                "evidence": (EVIDENCE,),
            },
        ),
        "exchanger_shell_bundle_and_coordinate_frame_reviewed": True,
        "tube_layout_shape_order_units_and_digest_reviewed": True,
        "tubesheet_and_baffle_geometry_reviewed": True,
        "material_condition_and_geometry_units_reviewed": True,
        "provider_revision_configuration_input_and_result_reviewed": True,
        "qualification_specimens_partitions_and_uncertainty_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return HeatExchangerGeometryAssessment(**value)


def test_reviewed_geometry_is_within_provider_support():
    result = heat_exchanger_geometry_evidence(payload())
    assert result.status == "computed"
    assert result.values["declared_geometry_outcome"] == "within_support"
    assert result.values["tube_count"] == 100


def test_geometry_or_metrology_outside_support_is_visible():
    base = payload(shell_inside_diameter_m=3.0)
    evidence = base.qualification_evidence[0].model_copy(update={"provider_value": 0.2})
    result = heat_exchanger_geometry_evidence(base.model_copy(update={"qualification_evidence": (evidence,)}))
    assert result.status == "out_of_scope"
    assert result.values["outside_geometry_support_reasons"] == ["shell_inside_diameter"]
    assert result.values["outside_support_evidence_ids"] == ["evidence-1"]


def test_unit_mismatch_or_missing_review_needs_data():
    base = payload()
    evidence = base.qualification_evidence[0].model_copy(update={"unit_token": "mm"})
    assert (
        heat_exchanger_geometry_evidence(
            base.model_copy(update={"qualification_evidence": (evidence,)})
        ).status
        == "needs_data"
    )
    assert (
        heat_exchanger_geometry_evidence(
            payload(tube_layout_shape_order_units_and_digest_reviewed=False)
        ).status
        == "needs_data"
    )


def test_coordinate_shape_and_context_identity_are_strict():
    base = payload()
    with pytest.raises(ValueError, match="tube_count by two"):
        HeatExchangerGeometryAssessment(
            **base.model_dump(exclude={"tube_layout"}),
            tube_layout=base.tube_layout.model_copy(update={"coordinate_array_shape": (99, 2)}),
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.heat_exchanger_geometry_evidence",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
