"""Caller-parameterized reduced-time Prony history for a gasket temperature path."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..gasket_relaxation import GasketViscoelasticHistoryRequest, evaluate_gasket_viscoelastic_history
from ..registry import ModelSpec

MODEL_ID = "fabrication.gasket_prony_temperature_shift_history"
SOURCE_ID = "caller_gasket_prony_time_temperature_shift_parameters"
R_GAS = 8.31446261815324


class GasketPronyTemperatureShiftLaw(Contract):
    """Evidence-bound caller shift law for reference-temperature Prony times."""

    law_id: str = Field(min_length=1)
    law: Literal["arrhenius", "wlf"]
    reference_temperature_K: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    activation_energy_J_mol: float | None = Field(default=None, ge=0)
    wlf_c1: Positive | None = None
    wlf_c2_K: Positive | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    parameter_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    calibration_and_shift_form_reviewed: bool

    @model_validator(mode="after")
    def validate_shift_parameters(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("temperature support must be ordered")
        if not self.minimum_temperature_K <= self.reference_temperature_K <= self.maximum_temperature_K:
            raise ValueError("reference temperature must lie inside shift-law support")
        if self.evidence.source_id != SOURCE_ID or self.evidence.sha256 != self.parameter_sha256:
            raise ValueError("shift-law Evidence must match the declared caller source and parameter digest")
        if self.law == "arrhenius":
            if self.activation_energy_J_mol is None or self.wlf_c1 is not None or self.wlf_c2_K is not None:
                raise ValueError("Arrhenius shift requires only activation energy")
        elif self.activation_energy_J_mol is not None or self.wlf_c1 is None or self.wlf_c2_K is None:
            raise ValueError("WLF shift requires C1 and C2 only")
        return self


class GasketTemperatureShiftedPronyHistory(Contract):
    """Isothermal Prony response in caller-defined reduced time with a variable actual temperature path."""

    schema_version: Literal["matintegrity.gasket_prony_temperature_shift_history.v1"] = (
        "matintegrity.gasket_prony_temperature_shift_history.v1"
    )
    base_history: GasketViscoelasticHistoryRequest
    shift_law: GasketPronyTemperatureShiftLaw
    interval_temperature_K: tuple[Positive, ...] = Field(min_length=1)
    interval_temperature_piecewise_constant_reviewed: bool

    @model_validator(mode="after")
    def validate_alignment(self):
        if len(self.interval_temperature_K) != len(self.base_history.elapsed_time_s) - 1:
            raise ValueError("one temperature is required for each elapsed-time interval")
        if self.base_history.material.temperature_K != self.shift_law.reference_temperature_K:
            raise ValueError("Prony branch parameters must be declared at the shift-law reference temperature")
        if any(not math.isfinite(value) for value in self.interval_temperature_K):
            raise ValueError("interval temperatures must be finite")
        return self


def _log_shift_factor(law: GasketPronyTemperatureShiftLaw, temperature_K: float) -> float | None:
    if temperature_K < law.minimum_temperature_K or temperature_K > law.maximum_temperature_K:
        return None
    if law.law == "arrhenius":
        assert law.activation_energy_J_mol is not None
        value = law.activation_energy_J_mol / R_GAS * (
            1.0 / temperature_K - 1.0 / law.reference_temperature_K
        )
    else:
        assert law.wlf_c1 is not None and law.wlf_c2_K is not None
        delta = temperature_K - law.reference_temperature_K
        denominator = law.wlf_c2_K + delta
        if denominator <= 0.0:
            return None
        value = -math.log(10.0) * law.wlf_c1 * delta / denominator
    return value if math.isfinite(value) else None


def evaluate_gasket_temperature_shifted_prony_history(
    request: GasketTemperatureShiftedPronyHistory,
) -> Calculation:
    law = request.shift_law
    base = request.base_history
    base_values = {
        "model_id": MODEL_ID,
        "request_sha256": canonical_digest(request.model_dump(mode="json")),
        "shift_law_id": law.law_id,
        "shift_law": law.law,
        "reference_temperature_K": law.reference_temperature_K,
        "interval_temperature_K": list(request.interval_temperature_K),
    }
    if not (law.calibration_and_shift_form_reviewed and request.interval_temperature_piecewise_constant_reviewed):
        return Calculation(status="needs_data", values=base_values | {"reason": "required temperature-shift reviews are missing"})

    reduced_times = [0.0]
    ledger = []
    for index, temperature in enumerate(request.interval_temperature_K):
        log_a = _log_shift_factor(law, temperature)
        if log_a is None:
            return Calculation(status="out_of_scope", values=base_values | {
                "failed_interval_index": index,
                "reason": "temperature is outside shift-law support or its formula domain",
                "temperature_shift_history": ledger,
                "reduced_time_s": reduced_times,
            })
        if abs(log_a) > 700.0:
            return Calculation(status="out_of_scope", values=base_values | {
                "failed_interval_index": index,
                "reason": "temperature shift factor exceeds finite representable support",
                "temperature_shift_history": ledger,
                "reduced_time_s": reduced_times,
            })
        factor = math.exp(log_a)
        actual_dt = base.elapsed_time_s[index + 1] - base.elapsed_time_s[index]
        reduced_dt = actual_dt / factor
        next_time = reduced_times[-1] + reduced_dt
        if not all(math.isfinite(value) for value in (factor, reduced_dt, next_time)) or reduced_dt <= 0.0:
            return Calculation(status="out_of_scope", values=base_values | {
                "failed_interval_index": index,
                "reason": "reduced-time increment exceeds finite positive support",
                "temperature_shift_history": ledger,
                "reduced_time_s": reduced_times,
            })
        reduced_times.append(next_time)
        ledger.append({
            "interval_index": index,
            "actual_start_time_s": base.elapsed_time_s[index],
            "actual_end_time_s": base.elapsed_time_s[index + 1],
            "temperature_K": temperature,
            "log_shift_factor": log_a,
            "shift_factor": factor,
            "reduced_interval_time_s": reduced_dt,
        })

    reduced_request = base.model_copy(update={"elapsed_time_s": tuple(reduced_times)})
    response = evaluate_gasket_viscoelastic_history(reduced_request)
    response_history = response.get("response_history")
    if response_history is not None:
        for index, row in enumerate(response_history):
            if index < len(base.elapsed_time_s):
                row["reduced_elapsed_time_s"] = row["elapsed_time_s"]
                row["elapsed_time_s"] = base.elapsed_time_s[index]
                row["temperature_K"] = (
                    law.reference_temperature_K if index == 0 else request.interval_temperature_K[index - 1]
                )
    values = base_values | {
        "status": response.get("status", "out_of_scope"),
        "constitutive_response_history": response_history,
        "temperature_shift_history": ledger,
        "reduced_time_s": reduced_times,
        "material_condition_id": base.material.material_condition_id,
        "source_group_id": base.material.source_group_id,
        "physical_specimen_id": base.material.physical_specimen_id,
        "limitations": [
            "Only Prony relaxation times shift with temperature; equilibrium modulus and branch moduli remain at the reference-condition values.",
            "Temperature is caller-declared piecewise constant within each interval; no heat-transfer solve or within-interval temperature interpolation is done.",
            "Arrhenius and WLF parameters, support, reference condition, shift direction and thermorheological simplicity are caller responsibilities and require calibration review.",
            "No contact separation mechanics, flange equilibrium, leakage, seal acceptance or material qualification is inferred.",
        ],
    }
    if response.get("reason"):
        values["reason"] = response["reason"]
    return Calculation(status=values["status"], values=values)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=GasketTemperatureShiftedPronyHistory,
        evaluator=evaluate_gasket_temperature_shifted_prony_history,
        units={
            "reference_temperature_K": "K",
            "interval_temperature_K[]": "K",
            "reduced_time_s[]": "s",
            "temperature_shift_history[].shift_factor": "1",
            "temperature_shift_history[].reduced_interval_time_s": "s",
            "constitutive_response_history[].total_compressive_stress_Pa": "Pa",
            "constitutive_response_history[].compressive_force_N": "N",
        },
        assumptions=(
            "A caller-calibrated, thermorheologically simple time-temperature shift modifies the Prony relaxation clock while other material parameters remain at the reference condition.",
            "The existing exact piecewise-linear strain/generalized-Maxwell solver is reused in reduced time; actual interval temperatures are piecewise constant caller inputs.",
            "This is an isothermal-equivalent constitutive screening history, not a thermally coupled joint or seal qualification model.",
        ),
        source_ids=(SOURCE_ID, "caller_gasket_prony_constitutive_response", "arrhenius_reduced_time_prony_shift", "wlf_reduced_time_prony_shift"),
        qualification="user_model",
    )]
