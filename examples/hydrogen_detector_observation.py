"""Project an authored hydrogen-release history to ideal detector signals."""

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-synthetic",
    "origin": "synthetic",
    "citation": "Authored detector-observation demonstration",
    "license_id": "MIT",
}

request = {
    "observation_id": "synthetic-permeation-observation",
    "material_condition_id": "synthetic-state",
    "specimen_id": "synthetic-membrane",
    "elapsed_time_origin_id": "synthetic-release-start",
    "source_model_id": "authored.synthetic_flow",
    "source_model_result_digest": "a" * 64,
    "source_surface_id": "exit-face",
    "source_flow_basis": "authored signed hydrogen-atom flow demonstration",
    "detector_calibration_id": "synthetic-faraday-mapping",
    "detector_kind": "electrochemical_current",
    "elapsed_time_s": [0.0, 5.0, 10.0],
    "outward_hydrogen_atoms_mol_s": [0.0, 2e-10, 4e-10],
    "current_sign_for_outward_hydrogen": 1,
    "electron_mol_per_hydrogen_atom_mol": 1.0,
    "current_efficiency": 0.9,
    "background_current_A": 1e-7,
    "source_surface_mapping_reviewed": True,
    "detector_response_mapping_reviewed": True,
    "evidence": [EVIDENCE],
}

result = default_registry().run_json(
    "transport.hydrogen_detector_observation",
    __import__("json").dumps(request),
    RunContext(
        asset_id="synthetic-asset",
        location_id="exit-face",
        time_basis="elapsed from synthetic release start",
    ),
)
print(result.model_dump_json(indent=2))
