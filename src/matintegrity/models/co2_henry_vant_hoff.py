"""Caller-parameterized temperature correction for aqueous CO2 Henry solubility."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "chemistry.co2_henry_vant_hoff_temperature_correction"
SOURCE_ID = "caller_co2_henry_vant_hoff_thermochemistry"
METHOD_SOURCE_ID = "idaes_van_t_hoff_equilibrium_constant"
GAS_CONSTANT_SOURCE_ID = "nist_molar_gas_constant"
R_J_MOL_K = 8.31446261815324


class Co2HenryTemperatureReference(Contract):
    """One source-pinned Henry solubility datum and dissolution thermochemistry."""

    coefficient_mol_L_Pa: Positive
    coefficient_convention: Literal[
        "aqueous_CO2star_concentration_over_gas_fugacity_mol_L_Pa"
    ]
    reference_temperature_K: Positive
    dissolution_enthalpy_J_mol: float
    dissolution_heat_capacity_change_J_mol_K: float | None = None
    minimum_supported_temperature_K: Positive
    maximum_supported_temperature_K: Positive
    solvent_composition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    enthalpy_sign_convention: Literal["positive_for_endothermic_dissolution"]
    evidence: Evidence

    @model_validator(mode="after")
    def validate_reference(self):
        if not math.isfinite(self.dissolution_enthalpy_J_mol):
            raise ValueError("dissolution enthalpy must be finite")
        if self.dissolution_heat_capacity_change_J_mol_K is not None and not math.isfinite(
            self.dissolution_heat_capacity_change_J_mol_K
        ):
            raise ValueError("dissolution heat-capacity change must be finite")
        if self.minimum_supported_temperature_K >= self.maximum_supported_temperature_K:
            raise ValueError("temperature support must be strictly increasing")
        if not (
            self.minimum_supported_temperature_K
            <= self.reference_temperature_K
            <= self.maximum_supported_temperature_K
        ):
            raise ValueError("reference temperature must lie inside the declared thermochemical support")
        if self.evidence.source_id != self.provider_id or self.evidence.sha256 != self.record_sha256:
            raise ValueError("provider identity and record digest must match the attached Evidence")
        return self


class Co2HenryTemperatureCorrectionRequest(Contract):
    assessment_id: str = Field(min_length=1)
    target_temperature_K: Positive
    sample_solvent_composition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference: Co2HenryTemperatureReference
    henry_coefficient_convention_reviewed: bool
    solvent_composition_match_reviewed: bool
    constant_heat_capacity_correction_reviewed: bool = False
    thermochemical_support_reviewed: bool
    maximum_absolute_log_temperature_factor: Positive = Field(default=40.0, le=100.0)
    review_id: str = Field(min_length=1)


def co2_henry_vant_hoff_temperature_correction(
    request: Co2HenryTemperatureCorrectionRequest,
) -> Calculation:
    """Correct Henry solubility using caller dissolution enthalpy and optional delta Cp.

    The log correction integrates d(ln K)/dT = DeltaH(T)/(R*T**2), with
    constant DeltaH or linearly varying DeltaH from a constant heat-capacity
    change. No thermochemical parameters are selected or extrapolated here.
    """
    ref = request.reference
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "reference_temperature_K": ref.reference_temperature_K,
        "target_temperature_K": request.target_temperature_K,
        "reference_coefficient_mol_L_Pa": ref.coefficient_mol_L_Pa,
        "reference_record_sha256": ref.record_sha256,
        "provider_id": ref.provider_id,
        "provider_revision": ref.provider_revision,
        "provider_configuration_sha256": ref.provider_configuration_sha256,
        "solvent_composition_sha256": ref.solvent_composition_sha256,
        "temperature_support_K": [ref.minimum_supported_temperature_K, ref.maximum_supported_temperature_K],
        "dissolution_enthalpy_J_mol": ref.dissolution_enthalpy_J_mol,
        "dissolution_heat_capacity_change_J_mol_K": ref.dissolution_heat_capacity_change_J_mol_K,
        "enthalpy_sign_convention": ref.enthalpy_sign_convention,
        "review_id": request.review_id,
    }
    if request.sample_solvent_composition_sha256 != ref.solvent_composition_sha256:
        return Calculation(
            status="out_of_scope",
            values=base | {"reason": "solvent_composition_digest_mismatch"},
            notes=("A Henry coefficient cannot be transferred to a different declared solvent composition.",),
        )
    if not (
        ref.minimum_supported_temperature_K
        <= request.target_temperature_K
        <= ref.maximum_supported_temperature_K
    ):
        return Calculation(
            status="out_of_scope",
            values=base | {"reason": "target_temperature_outside_source_support"},
            notes=("No temperature extrapolation is performed beyond the explicit source support.",),
        )
    missing_reviews = [
        name
        for name, reviewed in (
            ("henry_coefficient_convention_reviewed", request.henry_coefficient_convention_reviewed),
            ("solvent_composition_match_reviewed", request.solvent_composition_match_reviewed),
            ("thermochemical_support_reviewed", request.thermochemical_support_reviewed),
            (
                "constant_heat_capacity_correction_reviewed",
                request.constant_heat_capacity_correction_reviewed
                or ref.dissolution_heat_capacity_change_J_mol_K is None,
            ),
        )
        if not reviewed
    ]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing_reviews},
            notes=("The caller must review the Henry convention, solvent match, and thermochemical support.",),
        )

    t0 = ref.reference_temperature_K
    t = request.target_temperature_K
    delta_h = ref.dissolution_enthalpy_J_mol
    log_factor = delta_h / R_J_MOL_K * (1.0 / t0 - 1.0 / t)
    delta_cp = ref.dissolution_heat_capacity_change_J_mol_K
    if delta_cp is not None:
        log_factor += delta_cp / R_J_MOL_K * (math.log(t / t0) + t0 / t - 1.0)
    if not math.isfinite(log_factor) or abs(log_factor) > request.maximum_absolute_log_temperature_factor:
        return Calculation(
            status="out_of_scope",
            values=base
            | {
                "log_temperature_factor": log_factor if math.isfinite(log_factor) else None,
                "reason": "temperature_factor_exceeds_declared_bound",
            },
            notes=("The exponential correction exceeds the caller-declared numerical bound.",),
        )

    try:
        factor = math.exp(log_factor)
        coefficient = ref.coefficient_mol_L_Pa * factor
    except OverflowError:
        factor = math.inf
        coefficient = math.inf
    if not math.isfinite(factor) or not math.isfinite(coefficient) or factor <= 0.0 or coefficient <= 0.0:
        return Calculation(
            status="out_of_scope",
            values=base | {"log_temperature_factor": log_factor, "reason": "corrected_coefficient_not_representable"},
            notes=("The corrected coefficient is not representable as a finite positive binary64 value.",),
        )

    result = {
        **base,
        "delta_log_coefficient": log_factor,
        "temperature_factor": factor,
        "coefficient_mol_L_Pa": coefficient,
        "coefficient_convention": ref.coefficient_convention,
        "source_id": SOURCE_ID,
        "method_source_id": METHOD_SOURCE_ID,
        "gas_constant_source_id": GAS_CONSTANT_SOURCE_ID,
        "input_record_digest": canonical_digest(request.model_dump(mode="json")),
        "result_digest": canonical_digest(
            {
                "assessment_id": request.assessment_id,
                "target_temperature_K": t,
                "coefficient_mol_L_Pa": coefficient,
                "reference_record_sha256": ref.record_sha256,
                "model_id": MODEL_ID,
            }
        ),
    }
    return Calculation(
        status="computed",
        values=result,
        notes=(
            "The output is a caller-parameterized temperature correction to CO2* solubility coefficient only.",
            "No gas fugacity, electrolyte activity, carbonate speciation, corrosion rate, or material response is calculated.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            Co2HenryTemperatureCorrectionRequest,
            co2_henry_vant_hoff_temperature_correction,
            {
                "reference_temperature_K": "K",
                "target_temperature_K": "K",
                "coefficient_mol_L_Pa": "mol/L/Pa",
                "temperature_factor": "1",
                "delta_log_coefficient": "1",
            },
            (
                "The caller supplies a Henry solubility coefficient, dissolution enthalpy, optional constant heat-capacity change, solvent identity, thermochemical support and source lineage.",
                "The integrated van't Hoff form uses a positive enthalpy for endothermic dissolution and no extrapolation outside the declared temperature interval.",
                "This calculator does not infer the source parameters or calculate gas fugacity, aqueous speciation, corrosion kinetics, or engineering acceptance.",
            ),
            (SOURCE_ID, METHOD_SOURCE_ID, GAS_CONSTANT_SOURCE_ID),
        )
    ]
