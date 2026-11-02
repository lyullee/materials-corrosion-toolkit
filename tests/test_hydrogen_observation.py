import json

import pytest

from matintegrity.adapters import hydrogen_observation_inputs_from_transport_result
from matintegrity.contracts import AssessmentResult, RunContext, canonical_digest
from matintegrity.hydrogen_exports import FARADAY_C_MOL_ELECTRONS
from matintegrity.models.hydrogen_observation import (
    HydrogenDetectorObservation,
    detector_observation,
)
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-test",
    "origin": "synthetic",
    "citation": "Authored detector-observation identity test",
}


def inputs(kind="electrochemical_current"):
    base = {
        "observation_id": "obs-a",
        "material_condition_id": "state-a",
        "specimen_id": "specimen-a",
        "elapsed_time_origin_id": "release-start",
        "source_model_id": "authored.synthetic_flow",
        "source_model_result_digest": "a" * 64,
        "source_surface_id": "exit",
        "source_flow_basis": "authored signed atomic flow",
        "detector_calibration_id": "calibration-a",
        "detector_kind": kind,
        "elapsed_time_s": [0.0, 2.0, 5.0],
        "outward_hydrogen_atoms_mol_s": [1e-9, -2e-9, 3e-9],
        "source_surface_mapping_reviewed": True,
        "detector_response_mapping_reviewed": True,
        "evidence": [EVIDENCE],
    }
    if kind == "electrochemical_current":
        base.update(
            current_sign_for_outward_hydrogen=-1,
            electron_mol_per_hydrogen_atom_mol=1.0,
            current_efficiency=0.5,
            background_current_A=2e-6,
        )
    else:
        base.update(sample_mass_kg=0.002, hydrogen_atomic_molar_mass_kg_mol=0.001)
    return base


def calculate(payload):
    return detector_observation(HydrogenDetectorObservation.model_validate_json(json.dumps(payload)))


def assessment(model_id, inputs_, values, *, status="computed"):
    return AssessmentResult(
        model_id=model_id,
        model_version="1.0.0",
        status=status,
        inputs=inputs_,
        values=values,
        units={},
        assumptions=("authored adapter fixture",),
        notes=(),
        context=RunContext(asset_id="asset-a", location_id="location-a", time_basis="elapsed"),
        input_digest="b" * 64,
        source_ids=("authored",),
        qualification="engineering_screening",
        runtime={"matintegrity": "test"},
    )


def test_electrochemical_forward_identity_preserves_sign_and_background():
    result = calculate(inputs())
    equivalent = [-rate * FARADAY_C_MOL_ELECTRONS / 0.5 for rate in [1e-9, -2e-9, 3e-9]]
    assert result.status == "computed"
    assert result.values["electrochemical_equivalent_current_A"] == pytest.approx(equivalent)
    assert result.values["predicted_current_A"] == pytest.approx([value + 2e-6 for value in equivalent])
    assert result.values["cumulative_outward_hydrogen_atoms_mol"] == pytest.approx([0.0, -1e-9, 0.5e-9])


def test_mass_normalized_tds_identity_preserves_negative_release_rate():
    result = calculate(inputs("mass_normalized_tds"))
    assert result.values["predicted_hydrogen_mass_ppm_per_sample_mass_per_s"] == pytest.approx(
        [5e-4, -1e-3, 1.5e-3]
    )
    assert "predicted_current_A" not in result.values


def test_review_gates_return_needs_data_without_partial_prediction():
    payload = inputs()
    payload["source_surface_mapping_reviewed"] = False
    result = calculate(payload)
    assert result.status == "needs_data" and result.values == {}


@pytest.mark.parametrize(
    "change,message",
    [
        ({"elapsed_time_s": [0.0, 0.0, 1.0]}, "strictly increase"),
        ({"outward_hydrogen_atoms_mol_s": [1.0, 2.0]}, "match every time knot"),
        ({"sample_mass_kg": 1.0}, "electrochemical observation requires only"),
        ({"current_efficiency": 0.0}, "greater than 0"),
    ],
)
def test_invalid_clock_alignment_or_detector_parameter_mix_is_refused(change, message):
    payload = inputs()
    payload.update(change)
    with pytest.raises(ValueError, match=message):
        HydrogenDetectorObservation.model_validate_json(json.dumps(payload))


def test_planar_adapter_converts_named_inward_flux_to_outward_flow():
    transport = assessment(
        "transport.hydrogen_slab_kinetic",
        {
            "material_condition_id": "state-a",
            "left_boundary": {"boundary_id": "entry"},
            "right_boundary": {"boundary_id": "exit"},
        },
        {
            "elapsed_time_origin_id": "clock-a",
            "elapsed_time_s": [0.0, 1.0],
            "left_inward_flux_mol_m2_s": [2.0, 3.0],
            "right_inward_flux_mol_m2_s": [-4.0, -5.0],
        },
    )
    adapted = hydrogen_observation_inputs_from_transport_result(
        transport,
        observation_id="obs-a",
        specimen_id="specimen-a",
        surface_role="right",
        detector_calibration_id="cal-a",
        detector_kind="electrochemical_current",
        evidence=(EVIDENCE,),
        source_surface_mapping_reviewed=True,
        detector_response_mapping_reviewed=True,
        planar_surface_area_m2=0.25,
        planar_surface_area_basis="reviewed exposed membrane area",
        current_sign_for_outward_hydrogen=1,
        electron_mol_per_hydrogen_atom_mol=1.0,
        current_efficiency=1.0,
    )
    assert adapted["source_surface_id"] == "exit"
    assert adapted["outward_hydrogen_atoms_mol_s"] == [1.0, 1.25]
    assert adapted["source_model_result_digest"] == canonical_digest(transport.model_dump(mode="json"))
    assert calculate(adapted).status == "computed"


def test_cylinder_adapter_uses_integrated_surface_flow_without_extra_area():
    transport = assessment(
        "transport.hydrogen_finite_cylinder_kinetic",
        {
            "material_condition_id": "state-a",
            "curved_surface_boundary": {"boundary_id": "wall"},
            "lower_end_boundary": {"boundary_id": "bottom"},
            "upper_end_boundary": {"boundary_id": "top"},
        },
        {
            "elapsed_time_origin_id": "clock-a",
            "elapsed_time_s": [0.0, 1.0],
            "inward_surface_flow_mol_s": {
                "curved_surface": [-1e-9, -2e-9],
                "lower_end": [0.0, 0.0],
                "upper_end": [0.0, 0.0],
            },
        },
    )
    adapted = hydrogen_observation_inputs_from_transport_result(
        transport,
        observation_id="obs-a",
        specimen_id="specimen-a",
        surface_role="curved_surface",
        detector_calibration_id="cal-a",
        detector_kind="mass_normalized_tds",
        evidence=(EVIDENCE,),
        source_surface_mapping_reviewed=True,
        detector_response_mapping_reviewed=True,
        sample_mass_kg=0.002,
        hydrogen_atomic_molar_mass_kg_mol=0.001,
    )
    assert adapted["source_surface_id"] == "wall"
    assert adapted["outward_hydrogen_atoms_mol_s"] == [1e-9, 2e-9]


def test_adapter_rejects_missing_planar_area_noncomputed_and_unrelated_models():
    planar = assessment(
        "transport.hydrogen_slab_kinetic",
        {"material_condition_id": "state-a"},
        {},
    )
    common = dict(
        observation_id="obs-a",
        specimen_id="specimen-a",
        surface_role="right",
        detector_calibration_id="cal-a",
        detector_kind="electrochemical_current",
        evidence=(EVIDENCE,),
        source_surface_mapping_reviewed=True,
        detector_response_mapping_reviewed=True,
    )
    with pytest.raises(ValueError, match="positive reviewed physical surface area"):
        hydrogen_observation_inputs_from_transport_result(planar, **common)
    unrelated = assessment("corrosion.uniform_loss", {}, {})
    with pytest.raises(ValueError, match="only hydrogen slab"):
        hydrogen_observation_inputs_from_transport_result(unrelated, **common)


def test_registry_exposes_and_runs_detector_observation():
    registry = default_registry()
    assert "transport.hydrogen_detector_observation" in registry.list_models()
    result = registry.run_json(
        "transport.hydrogen_detector_observation",
        json.dumps(inputs()),
        RunContext(asset_id="asset-a", location_id="exit", time_basis="release-start"),
    )
    assert result.status == "computed"
    assert result.values["source_surface_id"] == "exit"
