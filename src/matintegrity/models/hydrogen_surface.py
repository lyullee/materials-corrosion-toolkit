"""Reviewed gas driver to reduced hydrogen surface-reaction capacities."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .hydrogen import R_J_mol_K


class ThermallyActivatedSurfaceFlux(Contract):
    """One reviewed Arrhenius limiting surface-flux parameterization."""

    rate_id: str = Field(min_length=1)
    pre_exponential_capacity_flux_mol_m2_s: Positive
    activation_energy_J_mol: Nonnegative
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HydrogenDissociativeSurfaceRates(Contract):
    """Create boundary histories without inferring fugacity or surface parameters."""

    boundary_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    hydrogen_species_id: str = Field(min_length=1)
    gas_state_provider_id: str = Field(min_length=1)
    elapsed_time_origin_id: str = Field(min_length=1)
    elapsed_time_s: list[Nonnegative] = Field(min_length=2, max_length=4096)
    temperature_K: list[Positive]
    hydrogen_gas_driver_Pa: list[Nonnegative]
    gas_driver_kind: Literal["fugacity", "ideal_gas_partial_pressure_approximation"]
    reference_fugacity_Pa: Positive
    supported_temperature_K: tuple[Positive, Positive]
    supported_hydrogen_gas_driver_Pa: tuple[Nonnegative, Positive]
    absorption: ThermallyActivatedSurfaceFlux
    desorption: ThermallyActivatedSurfaceFlux
    temperature_history_reviewed: bool = False
    gas_driver_history_reviewed: bool = False
    surface_parameterizations_reviewed: bool = False
    lattice_surface_state_mapping_reviewed: bool = False
    ideal_gas_approximation_reviewed: bool = False

    @model_validator(mode="after")
    def aligned_inputs(self):
        if self.elapsed_time_s[0] != 0 or any(
            right <= left
            for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("elapsed times must start at zero and strictly increase")
        count = len(self.elapsed_time_s)
        if len(self.temperature_K) != count or len(self.hydrogen_gas_driver_Pa) != count:
            raise ValueError("temperature and gas-driver histories must match every elapsed-time knot")
        if self.supported_temperature_K[1] <= self.supported_temperature_K[0]:
            raise ValueError("supported temperature interval must have positive width")
        if self.supported_hydrogen_gas_driver_Pa[1] <= self.supported_hydrogen_gas_driver_Pa[0]:
            raise ValueError("supported gas-driver interval must have positive width")
        if self.absorption.rate_id == self.desorption.rate_id:
            raise ValueError("absorption and desorption rate identities must differ")
        if self.gas_driver_kind == "fugacity" and self.ideal_gas_approximation_reviewed:
            raise ValueError("an ideal-gas review flag is not applicable to supplied fugacity")
        return self


def _log_capacity(law: ThermallyActivatedSurfaceFlux, temperature_K: float) -> float:
    return math.log(law.pre_exponential_capacity_flux_mol_m2_s) - law.activation_energy_J_mol / (
        R_J_mol_K * temperature_K
    )


def dissociative_surface_rates(x: HydrogenDissociativeSurfaceRates) -> Calculation:
    """Evaluate a reviewed reduced reversible surface law at aligned history knots."""
    reviews = (
        x.temperature_history_reviewed,
        x.gas_driver_history_reviewed,
        x.surface_parameterizations_reviewed,
        x.lattice_surface_state_mapping_reviewed,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Temperature, gas driver, both surface laws and the mapping to lattice-surface occupancy require explicit review.",
            ),
        )
    if (
        x.gas_driver_kind == "ideal_gas_partial_pressure_approximation"
        and not x.ideal_gas_approximation_reviewed
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Treating hydrogen partial pressure as fugacity requires an explicit ideal-gas approximation review.",
            ),
        )
    t_min, t_max = x.supported_temperature_K
    f_min, f_max = x.supported_hydrogen_gas_driver_Pa
    if any(temperature < t_min or temperature > t_max for temperature in x.temperature_K):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Temperature history exceeds the declared support of the surface parameters.",),
        )
    if any(driver < f_min or driver > f_max for driver in x.hydrogen_gas_driver_Pa):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Hydrogen gas-driver history exceeds the declared support of the surface parameters.",),
        )

    log_absorption_base = [_log_capacity(x.absorption, value) for value in x.temperature_K]
    log_desorption = [_log_capacity(x.desorption, value) for value in x.temperature_K]
    log_absorption = [
        (None if driver == 0 else base + 0.5 * math.log(driver / x.reference_fugacity_Pa))
        for base, driver in zip(log_absorption_base, x.hydrogen_gas_driver_Pa, strict=True)
    ]
    lower = math.log(math.ulp(0.0))
    upper = math.log(float.fromhex("0x1.fffffffffffffp+1023"))
    requested_positive_logs = [value for value in log_absorption if value is not None] + log_desorption
    if any(not math.isfinite(value) or value < lower or value > upper for value in requested_positive_logs):
        return Calculation(
            status="out_of_scope",
            values={
                "log_absorption_capacity_flux_mol_m2_s": log_absorption,
                "log_desorption_capacity_flux_mol_m2_s": log_desorption,
            },
            notes=(
                "A positive requested surface capacity is outside floating-point range; it is not clipped. Exact zero absorption is retained only for an exact zero gas driver.",
            ),
        )
    absorption = [0.0 if value is None else math.exp(value) for value in log_absorption]
    desorption = [math.exp(value) for value in log_desorption]
    equilibrium_occupancy = [
        inward / (inward + outward) for inward, outward in zip(absorption, desorption, strict=True)
    ]
    evidence = [item.model_dump(mode="json") for law in (x.absorption, x.desorption) for item in law.evidence]
    boundary_fields = {
        "kind": "dissociative_surface_reaction",
        "absorption_capacity_flux_mol_m2_s": absorption,
        "desorption_capacity_flux_mol_m2_s": desorption,
        "evidence": evidence,
    }
    return Calculation(
        values={
            "boundary_id": x.boundary_id,
            "material_condition_id": x.material_condition_id,
            "reference_lattice_id": x.reference_lattice_id,
            "surface_condition_id": x.surface_condition_id,
            "hydrogen_species_id": x.hydrogen_species_id,
            "gas_state_provider_id": x.gas_state_provider_id,
            "elapsed_time_origin_id": x.elapsed_time_origin_id,
            "elapsed_time_s": x.elapsed_time_s,
            "temperature_K": x.temperature_K,
            "hydrogen_gas_driver_Pa": x.hydrogen_gas_driver_Pa,
            "gas_driver_kind": x.gas_driver_kind,
            "absorption_capacity_flux_mol_m2_s": absorption,
            "desorption_capacity_flux_mol_m2_s": desorption,
            "log_absorption_capacity_flux_mol_m2_s": log_absorption,
            "log_desorption_capacity_flux_mol_m2_s": log_desorption,
            "zero_occupancy_inward_capacity_flux_mol_m2_s": absorption,
            "unit_occupancy_outward_capacity_flux_mol_m2_s": desorption,
            "zero_net_surface_occupancy": equilibrium_occupancy,
            "absorption_parameter_digest": canonical_digest(x.absorption.model_dump(mode="json")),
            "desorption_parameter_digest": canonical_digest(x.desorption.model_dump(mode="json")),
            "boundary_contract_fields": boundary_fields,
            "boundary_history_digest": canonical_digest(boundary_fields),
        },
        notes=(
            "The reduced law is J_in=J_abs*(1-theta_surface)-J_des*theta_surface. J_abs follows a caller-reviewed Arrhenius capacity times sqrt(f_H2/f_ref); J_des follows a caller-reviewed Arrhenius capacity.",
            "Zero-net surface occupancy is a diagnostic of this reduced boundary law, not a bulk solubility, Langmuir coverage, measured equilibrium concentration or service limit.",
            "Fugacity is supplied by the caller or partial pressure is used only after an explicit ideal-gas review. CoolProp is not used as a hydrogen fugacity provider.",
            "Surface contamination, oxide evolution, site blocking, electrochemical charging, multiple surface states, uncertainty, detector response and fracture effects are not modelled.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_dissociative_surface_rates",
            HydrogenDissociativeSurfaceRates,
            dissociative_surface_rates,
            {
                "elapsed_time_s": "s",
                "temperature_K": "K",
                "hydrogen_gas_driver_Pa": "Pa",
                "absorption_capacity_flux_mol_m2_s": "mol/(m^2*s)",
                "desorption_capacity_flux_mol_m2_s": "mol/(m^2*s)",
                "log_absorption_capacity_flux_mol_m2_s": "ln(numerical flux in mol/(m^2*s))",
                "log_desorption_capacity_flux_mol_m2_s": "ln(numerical flux in mol/(m^2*s))",
                "zero_net_surface_occupancy": "1",
            },
            (
                "Reviewed hydrogen fugacity, or explicitly reviewed ideal-gas partial-pressure approximation, and two effective Arrhenius surface-capacity laws over declared temperature and gas-driver support.",
            ),
            (
                "hydrogen_reduced_surface_reaction_derivation",
                "iupac_fugacity_definition",
            ),
        )
    ]
