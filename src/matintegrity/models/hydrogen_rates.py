"""Reviewed thermal rate histories for independent hydrogen-trap kinetics."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .hydrogen import R_J_mol_K

BOLTZMANN_J_K = 1.380649e-23
PLANCK_J_S = 6.62607015e-34


class ThermallyActivatedFrequency(Contract):
    frequency_id: str = Field(min_length=1)
    kind: Literal["arrhenius", "transition_state"]
    pre_exponential_frequency_per_s: Positive | None = None
    activation_energy_J_mol: Nonnegative | None = None
    activation_enthalpy_J_mol: float | None = None
    activation_entropy_J_mol_K: float | None = None
    transmission_coefficient: float | None = Field(default=None, gt=0, le=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def parameterization(self):
        arrhenius = (
            self.pre_exponential_frequency_per_s is not None,
            self.activation_energy_J_mol is not None,
        )
        transition_state = (
            self.activation_enthalpy_J_mol is not None,
            self.activation_entropy_J_mol_K is not None,
            self.transmission_coefficient is not None,
        )
        if self.kind == "arrhenius" and not (all(arrhenius) and not any(transition_state)):
            raise ValueError("Arrhenius frequency requires only prefactor and activation energy")
        if self.kind == "transition_state" and not (all(transition_state) and not any(arrhenius)):
            raise ValueError(
                "transition-state frequency requires only activation enthalpy, entropy and transmission coefficient"
            )
        return self


class HydrogenTrapThermalRates(Contract):
    trap_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    energy_reference_id: str = Field(min_length=1)
    elapsed_time_origin_id: str = Field(min_length=1)
    elapsed_time_s: list[Nonnegative] = Field(min_length=2, max_length=4096)
    temperature_K: list[Positive]
    supported_temperature_K: tuple[Positive, Positive]
    capture: ThermallyActivatedFrequency
    release: ThermallyActivatedFrequency
    temperature_history_reviewed: bool = False
    frequency_parameterizations_reviewed: bool = False
    common_energy_reference_reviewed: bool = False

    @model_validator(mode="after")
    def aligned_history(self):
        if self.elapsed_time_s[0] != 0 or any(
            right <= left
            for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("elapsed times must start at zero and strictly increase")
        if len(self.temperature_K) != len(self.elapsed_time_s):
            raise ValueError("temperature history must match every elapsed-time knot")
        if self.supported_temperature_K[1] <= self.supported_temperature_K[0]:
            raise ValueError("supported temperature interval must have positive width")
        if self.capture.frequency_id == self.release.frequency_id:
            raise ValueError("capture and release frequency identities must differ")
        return self


def _log_frequency(law: ThermallyActivatedFrequency, temperature_K: float) -> float:
    if law.kind == "arrhenius":
        return math.log(law.pre_exponential_frequency_per_s) - law.activation_energy_J_mol / (
            R_J_mol_K * temperature_K
        )
    return (
        math.log(law.transmission_coefficient)
        + math.log(BOLTZMANN_J_K / PLANCK_J_S)
        + math.log(temperature_K)
        + law.activation_entropy_J_mol_K / R_J_mol_K
        - law.activation_enthalpy_J_mol / (R_J_mol_K * temperature_K)
    )


def thermal_trap_rates(x: HydrogenTrapThermalRates) -> Calculation:
    """Evaluate reviewed Arrhenius or transition-state capture and release frequencies."""
    if not all(
        (
            x.temperature_history_reviewed,
            x.frequency_parameterizations_reviewed,
            x.common_energy_reference_reviewed,
        )
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Temperature history, both frequency parameterizations and their common energy reference require explicit review.",
            ),
        )
    minimum, maximum = x.supported_temperature_K
    if any(temperature < minimum or temperature > maximum for temperature in x.temperature_K):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Temperature history exceeds the declared support of the rate parameters.",),
        )
    log_capture = [_log_frequency(x.capture, temperature) for temperature in x.temperature_K]
    log_release = [_log_frequency(x.release, temperature) for temperature in x.temperature_K]
    lower = math.log(math.ulp(0.0))
    upper = math.log(float.fromhex("0x1.fffffffffffffp+1023"))
    if any(
        not math.isfinite(value) or value < lower or value > upper for value in (*log_capture, *log_release)
    ):
        return Calculation(
            status="out_of_scope",
            values={"log_capture_frequency_per_s": log_capture, "log_release_frequency_per_s": log_release},
            notes=(
                "A requested frequency is outside representable positive floating-point range; it is not replaced by zero, infinity or an irreversible trap.",
            ),
        )
    capture = [math.exp(value) for value in log_capture]
    release = [math.exp(value) for value in log_release]
    effective_ratio_energy = [
        -R_J_mol_K * temperature * (log_r - log_c)
        for temperature, log_c, log_r in zip(x.temperature_K, log_capture, log_release, strict=True)
    ]
    evidence = [item.model_dump(mode="json") for law in (x.capture, x.release) for item in law.evidence]
    rate_fields = {
        "rate_model": "independent_frequencies",
        "capture_frequency_per_s": capture,
        "release_frequency_per_s": release,
        "independent_rate_histories_reviewed": True,
        "rate_evidence": evidence,
    }
    return Calculation(
        values={
            "trap_id": x.trap_id,
            "material_condition_id": x.material_condition_id,
            "reference_lattice_id": x.reference_lattice_id,
            "energy_reference_id": x.energy_reference_id,
            "elapsed_time_origin_id": x.elapsed_time_origin_id,
            "elapsed_time_s": x.elapsed_time_s,
            "temperature_K": x.temperature_K,
            "capture_frequency_per_s": capture,
            "release_frequency_per_s": release,
            "log_capture_frequency_per_s": log_capture,
            "log_release_frequency_per_s": log_release,
            "effective_rate_ratio_energy_J_mol": effective_ratio_energy,
            "capture_parameter_digest": canonical_digest(x.capture.model_dump(mode="json")),
            "release_parameter_digest": canonical_digest(x.release.model_dump(mode="json")),
            "independent_rate_contract_fields": rate_fields,
            "independent_rate_history_digest": canonical_digest(rate_fields),
            "constant_basis": {
                "molar_gas_constant_J_mol_K": R_J_mol_K,
                "boltzmann_constant_J_K": BOLTZMANN_J_K,
                "planck_constant_J_s": PLANCK_J_S,
                "si_constants_exact": True,
            },
        },
        notes=(
            "Arrhenius uses A*exp(-Ea/(R*T)); transition-state mode uses transmission*(k_B*T/h)*exp(activation_entropy/R)*exp(-activation_enthalpy/(R*T)). Parameters are effective caller-reviewed quantities for one declared material condition and temperature support.",
            "Log-frequency outputs are natural logarithms of the numerical frequency expressed in s^-1; they are retained for numerical diagnostics and are not separate physical observables.",
            "The effective rate-ratio energy is -R*T*ln(release/capture), a diagnostic of the supplied rates rather than an inferred trap binding energy. The returned contract fields still require a matching population and initial occupancy in the transport model.",
            "No pressure/current-to-surface conversion, atomistic prefactor inference, multi-path mechanism selection, parameter fitting, uncertainty propagation, experimental qualification or fracture effect is performed.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_trap_thermal_rates",
            HydrogenTrapThermalRates,
            thermal_trap_rates,
            {
                "elapsed_time_s": "s",
                "temperature_K": "K",
                "capture_frequency_per_s": "1/s",
                "release_frequency_per_s": "1/s",
                "log_capture_frequency_per_s": "ln(numerical frequency in 1/s)",
                "log_release_frequency_per_s": "ln(numerical frequency in 1/s)",
                "effective_rate_ratio_energy_J_mol": "J/mol",
            },
            (
                "Reviewed single-path Arrhenius or transition-state frequency parameters, one common energy reference, a supported absolute-temperature interval and an aligned elapsed-time history.",
            ),
            (
                "arrhenius_frequency_history_derivation",
                "eyring_transition_state",
                "hydrogen_thermal_rate_contract",
            ),
        )
    ]
