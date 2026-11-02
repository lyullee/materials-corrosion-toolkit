"""Forward observation mappings for reviewed hydrogen release histories."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..hydrogen_exports import FARADAY_C_MOL_ELECTRONS
from ..registry import ModelSpec


class HydrogenDetectorObservation(Contract):
    """Map a signed atomic-hydrogen flow to one reviewed ideal detector signal."""

    schema_version: Literal["matintegrity.hydrogen_detector_observation.v1"] = (
        "matintegrity.hydrogen_detector_observation.v1"
    )
    observation_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    elapsed_time_origin_id: str = Field(min_length=1)
    source_model_id: str = Field(min_length=1)
    source_model_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_surface_id: str = Field(min_length=1)
    source_flow_basis: str = Field(min_length=1)
    detector_calibration_id: str = Field(min_length=1)
    detector_kind: Literal["electrochemical_current", "mass_normalized_tds"]
    elapsed_time_s: list[Nonnegative] = Field(min_length=2, max_length=100_000)
    outward_hydrogen_atoms_mol_s: list[float]
    current_sign_for_outward_hydrogen: Literal[-1, 1] | None = None
    electron_mol_per_hydrogen_atom_mol: Positive | None = None
    current_efficiency: float | None = Field(default=None, gt=0, le=1)
    background_current_A: float | None = None
    sample_mass_kg: Positive | None = None
    hydrogen_atomic_molar_mass_kg_mol: Positive | None = None
    source_surface_mapping_reviewed: bool = False
    detector_response_mapping_reviewed: bool = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_detector_contract(self):
        if self.elapsed_time_s[0] != 0 or any(
            right <= left
            for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("elapsed times must start at zero and strictly increase")
        if len(self.outward_hydrogen_atoms_mol_s) != len(self.elapsed_time_s):
            raise ValueError("the signed hydrogen-flow history must match every time knot")
        electrochemical = (
            self.current_sign_for_outward_hydrogen,
            self.electron_mol_per_hydrogen_atom_mol,
            self.current_efficiency,
        )
        thermal = (self.sample_mass_kg, self.hydrogen_atomic_molar_mass_kg_mol)
        if self.detector_kind == "electrochemical_current":
            if not all(value is not None for value in electrochemical) or any(
                value is not None for value in thermal
            ):
                raise ValueError(
                    "electrochemical observation requires only sign, electron stoichiometry and efficiency"
                )
        elif any(value is not None for value in electrochemical) or not all(
            value is not None for value in thermal
        ):
            raise ValueError(
                "mass-normalized TDS observation requires only sample mass and atomic molar mass"
            )
        if self.detector_kind != "electrochemical_current" and self.background_current_A is not None:
            raise ValueError("background current is only meaningful for electrochemical observation")
        return self


def detector_observation(x: HydrogenDetectorObservation) -> Calculation:
    """Apply an instantaneous reviewed Faraday or mass-normalized observation identity."""
    if not x.source_surface_mapping_reviewed or not x.detector_response_mapping_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "The transport surface mapping and detector-response mapping both require explicit review.",
            ),
        )
    flow = x.outward_hydrogen_atoms_mol_s
    cumulative = [0.0]
    for index in range(1, len(flow)):
        duration = x.elapsed_time_s[index] - x.elapsed_time_s[index - 1]
        cumulative.append(cumulative[-1] + 0.5 * (flow[index - 1] + flow[index]) * duration)
    values = {
        "observation_id": x.observation_id,
        "material_condition_id": x.material_condition_id,
        "specimen_id": x.specimen_id,
        "elapsed_time_origin_id": x.elapsed_time_origin_id,
        "source_model_id": x.source_model_id,
        "source_model_result_digest": x.source_model_result_digest,
        "source_surface_id": x.source_surface_id,
        "detector_calibration_id": x.detector_calibration_id,
        "elapsed_time_s": x.elapsed_time_s,
        "outward_hydrogen_atoms_mol_s": flow,
        "cumulative_outward_hydrogen_atoms_mol": cumulative,
        "observation_contract_digest": canonical_digest(x.model_dump(mode="json")),
    }
    if x.detector_kind == "electrochemical_current":
        equivalent = [
            x.current_sign_for_outward_hydrogen
            * rate
            * FARADAY_C_MOL_ELECTRONS
            * x.electron_mol_per_hydrogen_atom_mol
            / x.current_efficiency
            for rate in flow
        ]
        background = 0.0 if x.background_current_A is None else x.background_current_A
        values.update(
            electrochemical_equivalent_current_A=equivalent,
            predicted_current_A=[value + background for value in equivalent],
            background_current_A=background,
        )
    else:
        values["predicted_hydrogen_mass_ppm_per_sample_mass_per_s"] = [
            rate * x.hydrogen_atomic_molar_mass_kg_mol / x.sample_mass_kg * 1e6 for rate in flow
        ]
    return Calculation(
        values=values,
        notes=(
            "The input and cumulative release count moles of hydrogen atoms; outward flow and its ideal detector response remain signed and are never clipped.",
            "This is an instantaneous algebraic observation mapping. It does not infer a transport boundary from a signal or represent detector lag, line volume, pumping, recombination, adsorption, noise or calibration uncertainty.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_detector_observation",
            HydrogenDetectorObservation,
            detector_observation,
            {
                "elapsed_time_s": "s",
                "outward_hydrogen_atoms_mol_s": "mol/s",
                "cumulative_outward_hydrogen_atoms_mol": "mol",
                "electrochemical_equivalent_current_A": "A",
                "predicted_current_A": "A",
                "background_current_A": "A",
                "predicted_hydrogen_mass_ppm_per_sample_mass_per_s": "ppm/s",
            },
            (
                "Instantaneous reviewed Faraday or sample-mass observation identity for a signed hydrogen-atom release history; detector dynamics and transport inversion are excluded.",
            ),
            ("si_defining_constants", "hydrogen_detector_observation_derivation"),
        )
    ]
