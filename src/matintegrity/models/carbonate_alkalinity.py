"""Activity-based aqueous carbonate-only alkalinity speciation."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "chemistry.carbonate_alkalinity_speciation"
SOURCE_ID = "usgs_advanced_carbonate_speciation"
ACTIVITY_STANDARD_CONCENTRATION_MOL_L = 1.0


class CarbonateActivityConstants(Contract):
    activity_standard_state: Literal["molarity_1_mol_L"] = "molarity_1_mol_L"
    temperature_K: Positive
    K1_activity: Positive
    K2_activity: Positive
    Kw_activity: Positive
    gamma_h_plus: Positive
    gamma_hco3_minus: Positive
    gamma_co3_double_minus: Positive
    gamma_oh_minus: Positive
    constants_provider_id: str = Field(min_length=1)
    constants_provider_revision: str = Field(min_length=1)
    constants_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    constants_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CarbonateAlkalinitySpeciation(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    temperature_K: Positive
    ph_activity: float
    measured_total_alkalinity_mol_L: float
    expanded_total_alkalinity_uncertainty_mol_L: Nonnegative
    alkalinity_uncertainty_basis: str = Field(min_length=1)
    closure_absolute_tolerance_mol_L: Positive
    constants_temperature_tolerance_K: Nonnegative = 0.0
    constants: CarbonateActivityConstants
    measurement_provider_id: str = Field(min_length=1)
    measurement_provider_revision: str = Field(min_length=1)
    measurement_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    measurement_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    carbonate_only_alkalinity_basis_reviewed: bool
    ph_activity_scale_reviewed: bool
    equilibrium_constants_activity_basis_reviewed: bool
    activity_coefficients_reviewed: bool
    activity_standard_state_reviewed: bool = False
    aqueous_co2_star_definition_reviewed: bool
    temperature_and_provider_lineage_reviewed: bool
    alkalinity_measurement_units_and_uncertainty_reviewed: bool
    numerical_closure_tolerance_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


def _lineage(x: CarbonateAlkalinitySpeciation) -> dict[str, str]:
    return {
        "constants_provider_id": x.constants.constants_provider_id,
        "constants_provider_revision": x.constants.constants_provider_revision,
        "constants_configuration_digest": x.constants.constants_configuration_digest,
        "constants_record_digest": x.constants.constants_record_digest,
        "measurement_provider_id": x.measurement_provider_id,
        "measurement_provider_revision": x.measurement_provider_revision,
        "measurement_configuration_digest": x.measurement_configuration_digest,
        "measurement_record_digest": x.measurement_record_digest,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
    }


def _out_of_scope(x: CarbonateAlkalinitySpeciation, reason: str, **diagnostics) -> Calculation:
    return Calculation(
        status="out_of_scope",
        values={
            "assessment_id": x.assessment_id,
            "sample_id": x.sample_id,
            "out_of_scope_reason": reason,
            "diagnostics": diagnostics,
            **_lineage(x),
        },
        notes=(
            "The supplied carbonate-only activity model did not produce a finite physical aqueous closure.",
            "No gas-liquid equilibrium, gas pressure, missing species, corrosion rate, life, or acceptance is inferred.",
        ),
    )


def carbonate_alkalinity_speciation(x: CarbonateAlkalinitySpeciation) -> Calculation:
    """Solve the reviewed aqueous carbonate-only alkalinity balance in closed form."""

    review_fields = (
        "carbonate_only_alkalinity_basis_reviewed",
        "ph_activity_scale_reviewed",
        "equilibrium_constants_activity_basis_reviewed",
        "activity_coefficients_reviewed",
        "activity_standard_state_reviewed",
        "aqueous_co2_star_definition_reviewed",
        "temperature_and_provider_lineage_reviewed",
        "alkalinity_measurement_units_and_uncertainty_reviewed",
        "numerical_closure_tolerance_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "missing_reviews": missing_reviews,
                **_lineage(x),
            },
            notes=("All aqueous activity, measurement, lineage, and closure gates require review.",),
        )

    constants = x.constants
    if abs(constants.temperature_K - x.temperature_K) > x.constants_temperature_tolerance_K:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "missing_reviews": ["temperature_matched_equilibrium_constants"],
                **_lineage(x),
            },
            notes=(
                "Caller-supplied equilibrium constants and activity coefficients must match the sample temperature; no temperature extrapolation is performed.",
            ),
        )
    try:
        hydrogen_activity = 10.0 ** (-x.ph_activity)
        hydrogen_concentration = (
            hydrogen_activity / constants.gamma_h_plus * ACTIVITY_STANDARD_CONCENTRATION_MOL_L
        )
        hydroxide_concentration = (
            constants.Kw_activity
            / hydrogen_activity
            / constants.gamma_oh_minus
            * ACTIVITY_STANDARD_CONCENTRATION_MOL_L
        )
        carbonate_to_bicarbonate_ratio = (
            constants.K2_activity
            * constants.gamma_hco3_minus
            / (constants.gamma_co3_double_minus * hydrogen_activity)
        )
    except (OverflowError, ZeroDivisionError):
        return _out_of_scope(x, "nonfinite_primary_activity_state")

    primary_values = (
        hydrogen_activity,
        hydrogen_concentration,
        hydroxide_concentration,
        carbonate_to_bicarbonate_ratio,
    )
    if any(not math.isfinite(value) or value <= 0.0 for value in primary_values):
        return _out_of_scope(
            x,
            "nonfinite_primary_activity_state",
            hydrogen_activity=hydrogen_activity,
        )

    carbonate_alkalinity_numerator = (
        x.measured_total_alkalinity_mol_L - hydroxide_concentration + hydrogen_concentration
    )
    denominator = 1.0 + 2.0 * carbonate_to_bicarbonate_ratio
    if (
        not math.isfinite(carbonate_alkalinity_numerator)
        or carbonate_alkalinity_numerator < 0.0
        or not math.isfinite(denominator)
        or denominator <= 0.0
    ):
        return _out_of_scope(
            x,
            "nonphysical_carbonate_alkalinity_numerator",
            carbonate_alkalinity_numerator_mol_L=carbonate_alkalinity_numerator,
        )

    bicarbonate_concentration = carbonate_alkalinity_numerator / denominator
    carbonate_concentration = carbonate_to_bicarbonate_ratio * bicarbonate_concentration
    bicarbonate_activity = (
        constants.gamma_hco3_minus * bicarbonate_concentration / ACTIVITY_STANDARD_CONCENTRATION_MOL_L
    )
    aqueous_co2_star_concentration = (
        hydrogen_activity
        * bicarbonate_activity
        / constants.K1_activity
        * ACTIVITY_STANDARD_CONCENTRATION_MOL_L
    )
    reconstructed_alkalinity = (
        bicarbonate_concentration
        + 2.0 * carbonate_concentration
        + hydroxide_concentration
        - hydrogen_concentration
    )
    closure_residual = reconstructed_alkalinity - x.measured_total_alkalinity_mol_L
    bicarbonate_expanded_uncertainty = x.expanded_total_alkalinity_uncertainty_mol_L / denominator
    carbonate_expanded_uncertainty = carbonate_to_bicarbonate_ratio * bicarbonate_expanded_uncertainty
    aqueous_co2_star_expanded_uncertainty = (
        hydrogen_activity
        * constants.gamma_hco3_minus
        / constants.K1_activity
        * bicarbonate_expanded_uncertainty
    )
    derived_values = (
        bicarbonate_concentration,
        carbonate_concentration,
        bicarbonate_activity,
        aqueous_co2_star_concentration,
        reconstructed_alkalinity,
        closure_residual,
        bicarbonate_expanded_uncertainty,
        carbonate_expanded_uncertainty,
        aqueous_co2_star_expanded_uncertainty,
    )
    if any(not math.isfinite(value) for value in derived_values) or any(
        value < 0.0
        for value in (
            bicarbonate_concentration,
            carbonate_concentration,
            bicarbonate_activity,
            aqueous_co2_star_concentration,
        )
    ):
        return _out_of_scope(x, "nonfinite_or_negative_derived_species")
    if abs(closure_residual) > x.closure_absolute_tolerance_mol_L:
        return _out_of_scope(
            x,
            "alkalinity_closure_tolerance_exceeded",
            closure_residual_mol_L=closure_residual,
            closure_absolute_tolerance_mol_L=x.closure_absolute_tolerance_mol_L,
        )

    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "sample_id": x.sample_id,
            "temperature_K": x.temperature_K,
            "activity_standard_state": constants.activity_standard_state,
            "activity_standard_state_reviewed": x.activity_standard_state_reviewed,
            "ph_activity": x.ph_activity,
            "measured_total_alkalinity_mol_L": x.measured_total_alkalinity_mol_L,
            "expanded_total_alkalinity_uncertainty_mol_L": (x.expanded_total_alkalinity_uncertainty_mol_L),
            "bicarbonate_expanded_uncertainty_mol_L": bicarbonate_expanded_uncertainty,
            "carbonate_expanded_uncertainty_mol_L": carbonate_expanded_uncertainty,
            "aqueous_co2_star_expanded_uncertainty_mol_L": aqueous_co2_star_expanded_uncertainty,
            "expanded_uncertainty_scope": "exact_linear_propagation_of_total_alkalinity_only",
            "uncertainty_basis": x.alkalinity_uncertainty_basis,
            "hydrogen_activity": hydrogen_activity,
            "hydrogen_concentration_mol_L": hydrogen_concentration,
            "hydroxide_concentration_mol_L": hydroxide_concentration,
            "carbonate_to_bicarbonate_ratio": carbonate_to_bicarbonate_ratio,
            "bicarbonate_concentration_mol_L": bicarbonate_concentration,
            "carbonate_concentration_mol_L": carbonate_concentration,
            "bicarbonate_activity": bicarbonate_activity,
            "aqueous_co2_star_concentration_mol_L": aqueous_co2_star_concentration,
            "reconstructed_total_alkalinity_mol_L": reconstructed_alkalinity,
            "alkalinity_closure_residual_mol_L": closure_residual,
            "closure_absolute_tolerance_mol_L": x.closure_absolute_tolerance_mol_L,
            "activity_constants": {
                "activity_standard_state": constants.activity_standard_state,
                "temperature_K": constants.temperature_K,
                "K1_activity": constants.K1_activity,
                "K2_activity": constants.K2_activity,
                "Kw_activity": constants.Kw_activity,
                "gamma_h_plus": constants.gamma_h_plus,
                "gamma_hco3_minus": constants.gamma_hco3_minus,
                "gamma_co3_double_minus": constants.gamma_co3_double_minus,
                "gamma_oh_minus": constants.gamma_oh_minus,
            },
            "gas_liquid_equilibrium_evaluated": False,
            "gas_pressure_evaluated": False,
            **_lineage(x),
        },
        notes=(
            "The result uses only the exact caller-supplied aqueous carbonate-only alkalinity and activity definitions.",
            "Aqueous CO2* is returned; no Henry relation, gas-liquid equilibrium, or gas pressure is evaluated.",
            "Expanded alkalinity uncertainty is propagated exactly through the linear species relations while pH, equilibrium constants, and activity coefficients are held fixed; no probability is assigned.",
            "No activity model, pH or constant uncertainty propagation, corrosion rate, remaining life, or acceptance is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("carbonate alkalinity sample asset and location must match run context")

    return [
        ModelSpec(
            MODEL_ID,
            CarbonateAlkalinitySpeciation,
            carbonate_alkalinity_speciation,
            {
                "temperature_K": "K",
                "activity_standard_state": "1",
                "activity_standard_state_reviewed": "1",
                "ph_activity": "1",
                "measured_total_alkalinity_mol_L": "mol/L",
                "expanded_total_alkalinity_uncertainty_mol_L": "mol/L",
                "hydrogen_activity": "1",
                "hydrogen_concentration_mol_L": "mol/L",
                "hydroxide_concentration_mol_L": "mol/L",
                "carbonate_to_bicarbonate_ratio": "1",
                "bicarbonate_concentration_mol_L": "mol/L",
                "carbonate_concentration_mol_L": "mol/L",
                "bicarbonate_activity": "1",
                "aqueous_co2_star_concentration_mol_L": "mol/L",
                "bicarbonate_expanded_uncertainty_mol_L": "mol/L",
                "carbonate_expanded_uncertainty_mol_L": "mol/L",
                "aqueous_co2_star_expanded_uncertainty_mol_L": "mol/L",
                "reconstructed_total_alkalinity_mol_L": "mol/L",
                "alkalinity_closure_residual_mol_L": "mol/L",
                "gas_liquid_equilibrium_evaluated": "1",
                "gas_pressure_evaluated": "1",
            },
            (
                "Aqueous carbonate-only alkalinity balance with caller activity-based K1, K2, Kw and activity coefficients.",
                "The activity standard state is fixed to 1 mol/L and requires explicit caller review; molality-standard coefficients are not directly accepted.",
                "No additional alkalinity species, gas-liquid equilibrium, gas pressure, corrosion rate, life, or acceptance is included.",
            ),
            (SOURCE_ID,),
            context_validator=same_identity,
        )
    ]
