"""Verify ideal hydrogen detector identities and a planar transport adapter."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.adapters import hydrogen_observation_inputs_from_transport_result
from matintegrity.contracts import AssessmentResult, RunContext
from matintegrity.hydrogen_exports import FARADAY_C_MOL_ELECTRONS
from matintegrity.models.hydrogen_observation import (
    HydrogenDetectorObservation,
    detector_observation,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ({"source_id": "authored", "origin": "synthetic", "citation": "Authored identity"},)


def evaluate(values):
    return detector_observation(HydrogenDetectorObservation.model_validate(values))


def main():
    common = dict(
        observation_id="authored-observation",
        material_condition_id="authored-state",
        specimen_id="authored-specimen",
        elapsed_time_origin_id="authored-clock",
        source_model_id="authored.flow",
        source_model_result_digest="a" * 64,
        source_surface_id="authored-surface",
        source_flow_basis="authored signed atomic flow",
        detector_calibration_id="authored-calibration",
        elapsed_time_s=[0.0, 2.0, 5.0],
        outward_hydrogen_atoms_mol_s=[1e-9, -2e-9, 3e-9],
        source_surface_mapping_reviewed=True,
        detector_response_mapping_reviewed=True,
        evidence=EVIDENCE,
    )
    electrochemical = evaluate(
        HydrogenDetectorObservation(
            **common,
            detector_kind="electrochemical_current",
            current_sign_for_outward_hydrogen=-1,
            electron_mol_per_hydrogen_atom_mol=2.0,
            current_efficiency=0.8,
            background_current_A=3e-7,
        ).model_dump()
    )
    expected_equivalent = [
        -rate * FARADAY_C_MOL_ELECTRONS * 2.0 / 0.8 for rate in common["outward_hydrogen_atoms_mol_s"]
    ]
    current_error = max(
        abs(actual - expected)
        for actual, expected in zip(
            electrochemical.values["electrochemical_equivalent_current_A"],
            expected_equivalent,
            strict=True,
        )
    )
    thermal = evaluate(
        HydrogenDetectorObservation(
            **common,
            detector_kind="mass_normalized_tds",
            sample_mass_kg=0.002,
            hydrogen_atomic_molar_mass_kg_mol=0.001,
        ).model_dump()
    )
    expected_ppm = [rate * 0.001 / 0.002 * 1e6 for rate in common["outward_hydrogen_atoms_mol_s"]]
    ppm_error = max(
        abs(actual - expected)
        for actual, expected in zip(
            thermal.values["predicted_hydrogen_mass_ppm_per_sample_mass_per_s"],
            expected_ppm,
            strict=True,
        )
    )
    transport = AssessmentResult(
        model_id="transport.hydrogen_slab_kinetic",
        model_version="1.0.0",
        status="computed",
        inputs={
            "material_condition_id": "authored-state",
            "left_boundary": {"boundary_id": "entry"},
            "right_boundary": {"boundary_id": "exit"},
        },
        values={
            "elapsed_time_origin_id": "authored-clock",
            "elapsed_time_s": [0.0, 2.0, 5.0],
            "left_inward_flux_mol_m2_s": [0.0, 0.0, 0.0],
            "right_inward_flux_mol_m2_s": [-4e-9, 8e-9, -12e-9],
        },
        units={},
        assumptions=("authored adapter fixture",),
        notes=(),
        context=RunContext(asset_id="authored-asset", location_id="exit", time_basis="elapsed"),
        input_digest="b" * 64,
        source_ids=("authored",),
        qualification="engineering_screening",
        runtime={"matintegrity": "validation"},
    )
    adapted = hydrogen_observation_inputs_from_transport_result(
        transport,
        observation_id="adapted-observation",
        specimen_id="authored-specimen",
        surface_role="right",
        detector_calibration_id="authored-calibration",
        detector_kind="mass_normalized_tds",
        evidence=EVIDENCE,
        source_surface_mapping_reviewed=True,
        detector_response_mapping_reviewed=True,
        planar_surface_area_m2=0.25,
        planar_surface_area_basis="authored area",
        sample_mass_kg=0.002,
        hydrogen_atomic_molar_mass_kg_mol=0.001,
    )
    expected_flow = [1e-9, -2e-9, 3e-9]
    adapter_error = max(
        abs(actual - expected)
        for actual, expected in zip(adapted["outward_hydrogen_atoms_mol_s"], expected_flow, strict=True)
    )
    errors = {
        "faraday_current_absolute_A": current_error,
        "mass_normalized_tds_absolute_ppm_per_s": ppm_error,
        "planar_flux_to_flow_absolute_mol_per_s": adapter_error,
    }
    if max(errors.values()) > 1e-15:
        raise AssertionError(errors)
    record = {
        "schema_version": "matintegrity.validation.hydrogen_detector_observation.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Authored algebraic identity and adapter verification; not detector calibration, "
            "experimental validation or inverse transport identification."
        ),
        "absolute_errors": errors,
        "faraday_constant_C_mol_electrons": FARADAY_C_MOL_ELECTRONS,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/hydrogen_observation.py").read_bytes()
        ).hexdigest(),
        "adapter_source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/adapters.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/hydrogen_detector_observation_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
