"""Screen water condensation potential and CO2-star state for wet-gas wall conditions."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_condensate_state"
SOURCE_ID = "caller_wet_gas_wall_condensate_thermo_state"


class WetCo2CondensateStateRequest(Contract):
    """One aligned gas/wall state with caller-supplied water and CO2 property outputs."""

    schema_version: Literal["matintegrity.wet_co2_condensate_state.v1"] = (
        "matintegrity.wet_co2_condensate_state.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    bulk_gas_temperature_K: float = Field(gt=0)
    inner_wall_temperature_K: float = Field(gt=0)
    gas_total_pressure_Pa: float = Field(gt=0)
    water_vapor_fugacity_Pa: float = Field(ge=0)
    water_vapor_fugacity_absolute_bound_Pa: float = Field(ge=0)
    condensate_water_equilibrium_fugacity_at_wall_Pa: float = Field(gt=0)
    wall_equilibrium_fugacity_absolute_bound_Pa: float = Field(ge=0)
    co2_gas_fugacity_Pa: float = Field(ge=0)
    co2_fugacity_absolute_bound_Pa: float = Field(ge=0)
    co2star_henry_concentration_over_fugacity_mol_m3_Pa: float = Field(gt=0)
    henry_absolute_bound_mol_m3_Pa: float = Field(ge=0)
    water_property_provider_id: str = Field(min_length=1)
    water_property_provider_revision: str = Field(min_length=1)
    water_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    water_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    co2_property_provider_id: str = Field(min_length=1)
    co2_property_provider_revision: str = Field(min_length=1)
    co2_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    co2_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    henry_record_id: str = Field(min_length=1)
    henry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    gas_wall_state_time_alignment_reviewed: bool
    water_phase_standard_state_and_solution_match_reviewed: bool
    co2_fugacity_and_henry_convention_reviewed: bool
    bound_interpretation_is_deterministic_not_probability_reviewed: bool
    thermodynamic_use_authorized: bool

    @model_validator(mode="after")
    def validate_properties_and_provenance(self):
        numeric = (
            self.time_s, self.bulk_gas_temperature_K, self.inner_wall_temperature_K,
            self.gas_total_pressure_Pa, self.water_vapor_fugacity_Pa,
            self.water_vapor_fugacity_absolute_bound_Pa,
            self.condensate_water_equilibrium_fugacity_at_wall_Pa,
            self.wall_equilibrium_fugacity_absolute_bound_Pa,
            self.co2_gas_fugacity_Pa, self.co2_fugacity_absolute_bound_Pa,
            self.co2star_henry_concentration_over_fugacity_mol_m3_Pa,
            self.henry_absolute_bound_mol_m3_Pa,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("all state and property values must be finite")
        if self.water_vapor_fugacity_Pa > self.gas_total_pressure_Pa + self.water_vapor_fugacity_absolute_bound_Pa:
            raise ValueError("water vapor fugacity cannot exceed total pressure beyond its declared bound")
        if self.co2_gas_fugacity_Pa > self.gas_total_pressure_Pa + self.co2_fugacity_absolute_bound_Pa:
            raise ValueError("CO2 fugacity cannot exceed total pressure beyond its declared bound")
        required = {self.water_property_provider_id, self.co2_property_provider_id, self.henry_record_id}
        evidence_sources = {row.source_id for row in self.evidence}
        if not required.issubset(evidence_sources):
            raise ValueError("Evidence must identify water, CO2 and Henry property records")
        if not any(row.source_id == self.henry_record_id and row.sha256 == self.henry_record_sha256 for row in self.evidence):
            raise ValueError("Henry record digest must match its Evidence record")
        return self


def evaluate_wet_co2_condensate_state(request: WetCo2CondensateStateRequest) -> Calculation:
    """Compare local water vapor potential with wall equilibrium and map incipient-liquid CO2star."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "time_s": request.time_s,
        "input_sha256": input_sha,
        "bulk_gas_temperature_K": request.bulk_gas_temperature_K,
        "inner_wall_temperature_K": request.inner_wall_temperature_K,
        "gas_total_pressure_Pa": request.gas_total_pressure_Pa,
        "water_property_provider_id": request.water_property_provider_id,
        "water_property_provider_revision": request.water_property_provider_revision,
        "water_configuration_sha256": request.water_configuration_sha256,
        "water_result_sha256": request.water_result_sha256,
        "co2_property_provider_id": request.co2_property_provider_id,
        "co2_property_provider_revision": request.co2_property_provider_revision,
        "co2_configuration_sha256": request.co2_configuration_sha256,
        "co2_result_sha256": request.co2_result_sha256,
        "henry_record_id": request.henry_record_id,
        "henry_record_sha256": request.henry_record_sha256,
        "uncertainty_interpretation": "caller-supplied deterministic absolute bounds; not probability intervals",
    }
    reviews = (
        "gas_wall_state_time_alignment_reviewed",
        "water_phase_standard_state_and_solution_match_reviewed",
        "co2_fugacity_and_henry_convention_reviewed",
        "bound_interpretation_is_deterministic_not_probability_reviewed",
        "thermodynamic_use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    water_low = max(0.0, request.water_vapor_fugacity_Pa - request.water_vapor_fugacity_absolute_bound_Pa)
    water_high = request.water_vapor_fugacity_Pa + request.water_vapor_fugacity_absolute_bound_Pa
    equilibrium_low = max(
        0.0,
        request.condensate_water_equilibrium_fugacity_at_wall_Pa
        - request.wall_equilibrium_fugacity_absolute_bound_Pa,
    )
    equilibrium_high = (
        request.condensate_water_equilibrium_fugacity_at_wall_Pa
        + request.wall_equilibrium_fugacity_absolute_bound_Pa
    )
    if not all(math.isfinite(value) for value in (water_high, equilibrium_high)) or equilibrium_low <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "failure_reason": "water fugacity bounds exceed finite support or include a zero wall equilibrium value",
        })
    ratio = request.water_vapor_fugacity_Pa / request.condensate_water_equilibrium_fugacity_at_wall_Pa
    ratio_low = water_low / equilibrium_high
    ratio_high = water_high / equilibrium_low
    if not all(math.isfinite(value) for value in (ratio, ratio_low, ratio_high)):
        return Calculation(status="out_of_scope", values=base | {
            "failure_reason": "water fugacity ratio exceeds finite numeric support",
        })
    if ratio_low > 1.0:
        condensation_state = "condensation_potential_supported_within_bounds"
    elif ratio_high < 1.0:
        condensation_state = "no_condensation_potential_indicated_within_bounds"
    else:
        condensation_state = "condensation_potential_indeterminate_within_bounds"

    co2_low = max(0.0, request.co2_gas_fugacity_Pa - request.co2_fugacity_absolute_bound_Pa)
    co2_high = request.co2_gas_fugacity_Pa + request.co2_fugacity_absolute_bound_Pa
    henry_low = max(
        0.0,
        request.co2star_henry_concentration_over_fugacity_mol_m3_Pa
        - request.henry_absolute_bound_mol_m3_Pa,
    )
    henry_high = (
        request.co2star_henry_concentration_over_fugacity_mol_m3_Pa
        + request.henry_absolute_bound_mol_m3_Pa
    )
    co2star_low = co2_low * henry_low
    co2star_high = co2_high * henry_high
    if not all(math.isfinite(value) for value in (co2_high, henry_high, co2star_low, co2star_high)):
        return Calculation(status="out_of_scope", values=base | {
            "condensation_potential_state": condensation_state,
            "water_fugacity_ratio": ratio,
            "water_fugacity_ratio_bounds": [ratio_low, ratio_high],
            "failure_reason": "incipient-condensate CO2star state exceeds finite numeric support",
        })

    return Calculation(values=base | {
        "status": "computed",
        "water_vapor_fugacity_Pa": request.water_vapor_fugacity_Pa,
        "wall_condensate_water_equilibrium_fugacity_Pa": request.condensate_water_equilibrium_fugacity_at_wall_Pa,
        "water_fugacity_ratio": ratio,
        "water_fugacity_ratio_bounds": [ratio_low, ratio_high],
        "condensation_potential_state": condensation_state,
        "co2_gas_fugacity_Pa": request.co2_gas_fugacity_Pa,
        "co2_gas_fugacity_bounds_Pa": [co2_low, co2_high],
        "co2star_henry_concentration_over_fugacity_mol_m3_Pa": request.co2star_henry_concentration_over_fugacity_mol_m3_Pa,
        "incipient_condensate_equilibrium_co2star_concentration_mol_m3": request.co2star_henry_concentration_over_fugacity_mol_m3_Pa * request.co2_gas_fugacity_Pa,
        "incipient_condensate_equilibrium_co2star_bounds_mol_m3": [co2star_low, co2star_high],
        "liquid_inventory_or_condensation_rate_computed": False,
        "interpretation_boundary": "A local thermodynamic condensation-potential screen and Henry-law neutral CO2star state for an incipient aqueous phase, conditional on caller-supplied property outputs.",
        "not_inferred": [
            "condensed water mass, condensation rate, droplet thickness, coverage or retention time",
            "liquid electrolyte composition, pH, alkalinity or carbonate speciation",
            "gas-liquid boundary layer dynamics or cross-zone condensate transport",
            "corrosion rate, localized wall loss, acceptance or risk probability",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CondensateStateRequest,
        evaluator=evaluate_wet_co2_condensate_state,
        units={
            "time_s": "s", "bulk_gas_temperature_K": "K", "inner_wall_temperature_K": "K",
            "water_fugacity_ratio": "1", "water_fugacity_ratio_bounds": "1",
            "incipient_condensate_equilibrium_co2star_concentration_mol_m3": "mol/m3",
            "incipient_condensate_equilibrium_co2star_bounds_mol_m3": "mol/m3",
        },
        assumptions=(
            "Water fugacity and wall equilibrium fugacity are provider-supplied on one compatible fugacity/standard-state basis.",
            "Henry coefficient maps CO2 gas fugacity to neutral dissolved CO2star for the incipient liquid composition and wall temperature.",
            "Absolute bounds are deterministic caller-declared intervals and are not statistical confidence intervals.",
            "Condensation potential indicates thermodynamic possibility only; no water amount or corrosion response is inferred.",
        ),
        source_ids=(SOURCE_ID, "seiersten_top_of_line_corrosion_condensation"),
        qualification="user_model",
    )]
