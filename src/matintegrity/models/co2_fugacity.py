"""Pure-component CO2 fugacity provider backed by the optional CoolProp EOS."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec


class CoolPropCo2FugacityRequest(Contract):
    """Absolute CO2 partial pressure and temperature for a pure-component EOS state."""

    assessment_id: str = Field(min_length=1)
    temperature_K: Positive
    co2_partial_pressure_Pa: Positive
    backend: str = Field(default="HEOS", min_length=1)
    pure_component_approximation_reviewed: bool
    single_phase_gas_or_supercritical_reviewed: bool
    review_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class PureCo2FugacityHistory(Contract):
    """Exact-time sequence of independently specified pure-CO2 fugacity states."""

    schema_version: Literal["matintegrity.pure_co2_fugacity_history.v1"] = (
        "matintegrity.pure_co2_fugacity_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    time_s: tuple[Nonnegative, ...] = Field(min_length=1, max_length=20000)
    requests: tuple[CoolPropCo2FugacityRequest, ...] = Field(min_length=1, max_length=20000)
    history_clock_and_state_alignment_reviewed: bool
    maximum_point_evaluations: int = Field(default=20000, ge=1, le=20000)

    @model_validator(mode="after")
    def aligned_pure_history(self):
        if len(self.time_s) != len(self.requests):
            raise ValueError("one pure-CO2 fugacity request is required for every time point")
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("pure-CO2 fugacity history times must increase strictly")
        assessment_ids = [row.assessment_id for row in self.requests]
        if len(set(assessment_ids)) != len(assessment_ids):
            raise ValueError("pure-CO2 fugacity history assessment IDs must be unique")
        if len({row.backend for row in self.requests}) > 1:
            raise ValueError("one pure-CO2 fugacity history must use a single CoolProp backend")
        return self


class CoolPropCo2MixtureFugacityRequest(Contract):
    """CO2 component fugacity in a caller-specified gas-mixture PT state."""

    assessment_id: str = Field(min_length=1)
    temperature_K: Positive
    total_pressure_Pa: Positive
    components: tuple[str, ...] = Field(min_length=2)
    mole_fractions: tuple[float, ...] = Field(min_length=2)
    backend: str = Field(default="HEOS", min_length=1)
    mixture_composition_reviewed: bool
    mixture_eos_applicability_reviewed: bool
    single_phase_gas_or_supercritical_reviewed: bool
    review_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @field_validator("components")
    @classmethod
    def unique_component_names(cls, values):
        if any(not value.strip() for value in values) or len(values) != len(set(values)):
            raise ValueError("mixture component names must be nonblank and unique")
        co2_aliases = {"co2", "carbondioxide"}
        matches = [value for value in values if value.casefold() in co2_aliases]
        if len(matches) != 1:
            raise ValueError("mixture components must include exactly one CO2/CarbonDioxide component")
        if len({value.casefold() for value in values}) != len(values):
            raise ValueError("mixture component names cannot differ by case only")
        return values

    @model_validator(mode="after")
    def matching_normalized_composition(self):
        if len(self.components) != len(self.mole_fractions):
            raise ValueError("mixture component and mole-fraction counts must match")
        if any(value < 0.0 or value > 1.0 for value in self.mole_fractions):
            raise ValueError("mixture mole fractions must be between zero and one")
        if self.mole_fractions[_co2_component_index(self.components)] <= 0.0:
            raise ValueError("CO2 mole fraction must be positive")
        if abs(math.fsum(self.mole_fractions) - 1.0) > 1e-10:
            raise ValueError("mixture mole fractions must sum to one")
        if not self.assessment_id.strip() or not self.review_id.strip():
            raise ValueError("assessment_id and review_id cannot be blank")
        return self


class MixtureCo2FugacityHistory(Contract):
    """Exact-time sequence of caller-defined gas-mixture PT fugacity states."""

    schema_version: Literal["matintegrity.mixture_co2_fugacity_history.v1"] = (
        "matintegrity.mixture_co2_fugacity_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    time_s: tuple[Nonnegative, ...] = Field(min_length=1, max_length=20000)
    requests: tuple[CoolPropCo2MixtureFugacityRequest, ...] = Field(min_length=1, max_length=20000)
    history_clock_and_state_alignment_reviewed: bool
    maximum_point_evaluations: int = Field(default=20000, ge=1, le=20000)

    @model_validator(mode="after")
    def aligned_mixture_history(self):
        if len(self.time_s) != len(self.requests):
            raise ValueError("one mixture fugacity request is required for every time point")
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("mixture CO2 fugacity history times must increase strictly")
        if len({row.assessment_id for row in self.requests}) != len(self.requests):
            raise ValueError("mixture CO2 fugacity history assessment IDs must be unique")
        if len({row.backend for row in self.requests}) != 1:
            raise ValueError("one mixture CO2 fugacity history must use a single CoolProp backend")
        if len({row.components for row in self.requests}) != 1:
            raise ValueError("mixture components and their order must remain fixed over a history")
        return self


def _coolprop_phase_name(CoolProp, phase_index: int) -> str:
    phase_names = {
        int(CoolProp.iphase_liquid): "liquid",
        int(CoolProp.iphase_gas): "gas",
        int(CoolProp.iphase_twophase): "two_phase",
        int(CoolProp.iphase_supercritical): "supercritical",
        int(CoolProp.iphase_supercritical_gas): "supercritical_gas",
        int(CoolProp.iphase_supercritical_liquid): "supercritical_liquid",
        int(CoolProp.iphase_critical_point): "critical_point",
        int(CoolProp.iphase_unknown): "unknown",
        int(CoolProp.iphase_not_imposed): "not_imposed",
    }
    return phase_names.get(phase_index, "unrecognized")


def _supported_gas_phase(phase_name: str) -> bool:
    return phase_name in {"gas", "supercritical_gas", "supercritical"}


def _co2_component_index(components: tuple[str, ...]) -> int:
    return next(i for i, name in enumerate(components) if name.casefold() in {"co2", "carbondioxide"})


def _evaluate_pure_co2_state(x: CoolPropCo2FugacityRequest, CoolProp, state, pt_inputs) -> Calculation:
    """Evaluate one PT point using an existing, caller-isolated CoolProp state object."""
    try:
        state.update(pt_inputs, x.co2_partial_pressure_Pa, x.temperature_K)
    except ValueError as error:
        return Calculation(status="out_of_scope",values={"assessment_id":x.assessment_id,"reason":"CO2_state_outside_provider_numeric_support","provider_error":str(error)})
    phase_index = int(state.phase())
    phase_name = _coolprop_phase_name(CoolProp, phase_index)
    if not _supported_gas_phase(phase_name):
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "reason": "CO2_state_not_gas_or_supercritical",
                "coolprop_phase_index": phase_index,
                "coolprop_phase": phase_name,
            },
            notes=("Only gas, supercritical-gas or supercritical pure-CO2 states emit fugacity for this pathway.",),
        )

    phi = float(state.fugacity_coefficient(0))
    fugacity = float(state.fugacity(0))
    if not math.isfinite(phi) or phi <= 0.0 or not math.isfinite(fugacity) or fugacity <= 0.0:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "reason": "invalid_CO2_fugacity_output"},
            notes=("CoolProp did not return finite positive fugacity properties for this state.",),
        )

    configuration = {
        "provider_id": f"CoolProp:{x.backend}:CO2",
        "provider_revision": f"{CoolProp.__version__}:{CoolProp.__gitrevision__}",
        "backend": x.backend,
        "fluid": "CO2",
        "temperature_K": x.temperature_K,
        "co2_partial_pressure_Pa": x.co2_partial_pressure_Pa,
        "review_id": x.review_id,
        "pure_component_approximation_reviewed": x.pure_component_approximation_reviewed,
        "single_phase_gas_or_supercritical_reviewed": x.single_phase_gas_or_supercritical_reviewed,
    }
    configuration_digest = canonical_digest(configuration)
    record = {
        **configuration,
        "coolprop_phase_index": phase_index,
        "coolprop_phase": phase_name,
        "fugacity_coefficient": phi,
        "co2_fugacity_Pa": fugacity,
    }
    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "temperature_K": x.temperature_K,
            "co2_partial_pressure_Pa": x.co2_partial_pressure_Pa,
            "fugacity_coefficient": phi,
            "co2_fugacity_Pa": fugacity,
            "coolprop_phase_index": phase_index,
            "coolprop_phase": phase_name,
            "gas_fugacity_provider_id": configuration["provider_id"],
            "gas_fugacity_provider_revision": configuration["provider_revision"],
            "gas_fugacity_configuration_digest": configuration_digest,
            "gas_fugacity_record_digest": canonical_digest(record),
            "pure_component_approximation_reviewed": True,
            "single_phase_gas_or_supercritical_reviewed": True,
            "mixture_fugacity_computed": False,
        },
        notes=(
            "Pure-component CO2 EOS evaluated at caller-supplied absolute CO2 partial pressure.",
            "Mixture interaction effects, aqueous equilibrium, Henry coefficient, corrosion rate and integrity risk are not calculated.",
        ),
    )


def coolprop_co2_gas_fugacity(x: CoolPropCo2FugacityRequest) -> Calculation:
    """Calculate fugacity for pure CO2 at its partial pressure; never infer a mixture state."""
    missing = []
    if not x.pure_component_approximation_reviewed:
        missing.append("pure_component_approximation_reviewed")
    if not x.single_phase_gas_or_supercritical_reviewed:
        missing.append("single_phase_gas_or_supercritical_reviewed")
    if missing:
        return Calculation(
            status="needs_data",
            values={"assessment_id": x.assessment_id, "missing_reviews": missing},
            notes=(
                "CO2 fugacity is withheld until the declared pure-component and phase assumptions are reviewed.",
            ),
        )

    try:
        import CoolProp
        from CoolProp import PT_INPUTS, AbstractState
    except ImportError:
        return Calculation(
            status="needs_data",
            values={"assessment_id": x.assessment_id, "missing_dependency": "CoolProp"},
            notes=("Install the optional thermo dependency to evaluate this provider.",),
        )

    state = AbstractState(x.backend, "CO2")
    return _evaluate_pure_co2_state(x, CoolProp, state, PT_INPUTS)


def coolprop_pure_co2_fugacity_history(x: PureCo2FugacityHistory) -> Calculation:
    """Evaluate each caller-declared pure-CO2 EOS state at an exact time knot."""
    base = {
        "history_id": x.history_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "time_basis": x.time_basis,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
        "time_s": list(x.time_s),
        "point_count": len(x.requests),
        "provider_backend": x.requests[0].backend,
        "time_interpolation_performed": False,
    }
    if len(x.requests) > x.maximum_point_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "point_evaluation_budget_exceeded",
            "maximum_point_evaluations": x.maximum_point_evaluations,
        })
    if not x.history_clock_and_state_alignment_reviewed:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": ["history_clock_and_state_alignment_reviewed"],
        })

    rows = []
    # Reuse one mutable EOS state across the ordered history.  The requests
    # share a backend by contract; update() replaces PT state at each knot.
    state = None
    coolprop_module = None
    pt_inputs = None
    for index, (time_s, request) in enumerate(zip(x.time_s, x.requests, strict=True)):
        try:
            missing = []
            if not request.pure_component_approximation_reviewed:
                missing.append("pure_component_approximation_reviewed")
            if not request.single_phase_gas_or_supercritical_reviewed:
                missing.append("single_phase_gas_or_supercritical_reviewed")
            if missing:
                result = Calculation(
                    status="needs_data",
                    values={"assessment_id": request.assessment_id, "missing_reviews": missing},
                    notes=("CO2 fugacity is withheld until the declared pure-component and phase assumptions are reviewed.",),
                )
            else:
                if state is None:
                    try:
                        import CoolProp as coolprop_module
                        from CoolProp import PT_INPUTS as pt_inputs, AbstractState
                    except ImportError:
                        result = Calculation(
                            status="needs_data",
                            values={"assessment_id": request.assessment_id, "missing_dependency": "CoolProp"},
                            notes=("Install the optional thermo dependency to evaluate this provider.",),
                        )
                    else:
                        state = AbstractState(request.backend, "CO2")
                        result = _evaluate_pure_co2_state(request, coolprop_module, state, pt_inputs)
                else:
                    result = _evaluate_pure_co2_state(request, coolprop_module, state, pt_inputs)
        except (ArithmeticError, RuntimeError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "completed_sample_count": len(rows),
                "completed_time_s": [row["time_s"] for row in rows],
                "sample_results": rows,
                "failed_sample_index": index,
                "failed_sample_time_s": time_s,
                "failed_sample_id": request.assessment_id,
                "failed_sample_request_sha256": canonical_digest(request.model_dump(mode="json")),
                "provider_error_type": type(error).__name__,
            }, notes=("CoolProp failed at one requested state; the successfully computed prefix is retained.",))
        row = {
            "index": index,
            "time_s": time_s,
            "assessment_id": request.assessment_id,
            "request_sha256": canonical_digest(request.model_dump(mode="json")),
            "status": result.status,
            "values": result.values,
            "notes": list(result.notes),
        }
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "completed_sample_count": len(rows),
                "completed_time_s": [item["time_s"] for item in rows],
                "sample_results": rows,
                "failed_sample_index": index,
                "failed_sample_time_s": time_s,
                "failed_sample_id": request.assessment_id,
                "failed_sample_request_sha256": row["request_sha256"],
                "failed_sample_status": result.status,
                "failed_sample_values": result.values,
            }, notes=result.notes)
        rows.append(row)

    return Calculation(values=base | {
        "sample_results": rows,
        "assessment_ids": [row["assessment_id"] for row in rows],
        "temperature_K_history": [row["values"]["temperature_K"] for row in rows],
        "co2_partial_pressure_Pa_history": [row["values"]["co2_partial_pressure_Pa"] for row in rows],
        "fugacity_coefficient_history": [row["values"]["fugacity_coefficient"] for row in rows],
        "co2_fugacity_Pa_history": [row["values"]["co2_fugacity_Pa"] for row in rows],
        "provider_record_digests": [row["values"]["gas_fugacity_record_digest"] for row in rows],
        "all_points_computed": True,
        "mixture_interaction_modelled": False,
    }, notes=(
        "Each caller-supplied pure-CO2 PT state is evaluated independently by the selected CoolProp backend.",
        "No mixture interaction, aqueous equilibrium, Henry coefficient, gas inventory balance or corrosion response is inferred.",
        "Evaluation stops at the first failed state and preserves only the computed prefix.",
    ))


def _validate_pure_fugacity_history_context(request: PureCo2FugacityHistory, context: RunContext) -> None:
    if (request.asset_id, request.location_id, request.time_basis) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("pure-CO2 fugacity-history RunContext must match asset/location/time basis")


def co2_mixture_fugacity_history(x: MixtureCo2FugacityHistory) -> Calculation:
    """Evaluate ordered mixture PT states while reusing one CoolProp state object."""
    base = {
        "history_id": x.history_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "time_basis": x.time_basis,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
        "time_s": list(x.time_s),
        "point_count": len(x.requests),
        "provider_backend": x.requests[0].backend,
        "components": x.requests[0].components,
        "time_interpolation_performed": False,
    }
    if len(x.requests) > x.maximum_point_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "point_evaluation_budget_exceeded",
            "maximum_point_evaluations": x.maximum_point_evaluations,
        })
    if not x.history_clock_and_state_alignment_reviewed:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": ["history_clock_and_state_alignment_reviewed"],
        })

    rows = []
    state = None
    for index, (time_s, request) in enumerate(zip(x.time_s, x.requests, strict=True)):
        try:
            missing = [
                name for name, reviewed in (
                    ("mixture_composition_reviewed", request.mixture_composition_reviewed),
                    ("mixture_eos_applicability_reviewed", request.mixture_eos_applicability_reviewed),
                    ("single_phase_gas_or_supercritical_reviewed", request.single_phase_gas_or_supercritical_reviewed),
                ) if not reviewed
            ]
            if missing:
                result = Calculation(status="needs_data", values={
                    "assessment_id": request.assessment_id,
                    "missing_reviews": missing,
                }, notes=("Mixture fugacity is withheld until composition, EOS applicability and phase assumptions are reviewed.",))
            else:
                if state is None:
                    try:
                        from CoolProp import AbstractState
                    except ImportError:
                        result = Calculation(status="needs_data", values={
                            "assessment_id": request.assessment_id,
                            "missing_dependency": "CoolProp",
                        }, notes=("Install the optional thermo dependency to evaluate this provider.",))
                    else:
                        state = AbstractState(request.backend, "&".join(request.components))
                        result = _evaluate_co2_mixture_fugacity(request, _state=state)
                else:
                    result = _evaluate_co2_mixture_fugacity(request, _state=state)
        except (ArithmeticError, RuntimeError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "completed_sample_count": len(rows),
                "completed_time_s": [row["time_s"] for row in rows],
                "sample_results": rows,
                "failed_sample_index": index,
                "failed_sample_time_s": time_s,
                "failed_sample_id": request.assessment_id,
                "failed_sample_request_sha256": canonical_digest(request.model_dump(mode="json")),
                "provider_error_type": type(error).__name__,
            }, notes=("CoolProp failed at one requested mixture state; the successfully computed prefix is retained.",))
        row = {
            "index": index,
            "time_s": time_s,
            "assessment_id": request.assessment_id,
            "request_sha256": canonical_digest(request.model_dump(mode="json")),
            "status": result.status,
            "values": result.values,
            "notes": list(result.notes),
        }
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "completed_sample_count": len(rows),
                "completed_time_s": [item["time_s"] for item in rows],
                "sample_results": rows,
                "failed_sample_index": index,
                "failed_sample_time_s": time_s,
                "failed_sample_id": request.assessment_id,
                "failed_sample_request_sha256": row["request_sha256"],
                "failed_sample_status": result.status,
                "failed_sample_values": result.values,
            }, notes=result.notes)
        rows.append(row)

    return Calculation(values=base | {
        "sample_results": rows,
        "assessment_ids": [row["assessment_id"] for row in rows],
        "temperature_K_history": [row["values"]["temperature_K"] for row in rows],
        "total_pressure_Pa_history": [row["values"]["total_pressure_Pa"] for row in rows],
        "co2_partial_pressure_Pa_history": [row["values"]["co2_partial_pressure_Pa"] for row in rows],
        "fugacity_coefficient_history": [row["values"]["fugacity_coefficient"] for row in rows],
        "co2_fugacity_Pa_history": [row["values"]["co2_fugacity_Pa"] for row in rows],
        "provider_record_digests": [row["values"]["gas_fugacity_record_digest"] for row in rows],
        "all_points_computed": True,
        "mixture_interaction_modelled": True,
    }, notes=(
        "Each caller-supplied mixture PT state is evaluated at its exact time knot with a reused CoolProp state object.",
        "Mixture mole fractions may vary by knot; component identity/order and backend remain fixed. No temporal interpolation or ideal-mixture fallback is used.",
        "Evaluation stops at the first failed state and preserves the computed prefix; aqueous equilibrium and corrosion response are not inferred.",
    ))


def _validate_mixture_fugacity_history_context(request: MixtureCo2FugacityHistory, context: RunContext) -> None:
    if (request.asset_id, request.location_id, request.time_basis) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("mixture-CO2 fugacity-history RunContext must match asset/location/time basis")


def _evaluate_co2_mixture_fugacity(
    x: CoolPropCo2MixtureFugacityRequest,
    *,
    _state=None,
) -> Calculation:
    """Evaluate CO2 component fugacity in a reviewed, single-phase CoolProp gas mixture."""
    missing = [
        name
        for name, reviewed in (
            ("mixture_composition_reviewed", x.mixture_composition_reviewed),
            ("mixture_eos_applicability_reviewed", x.mixture_eos_applicability_reviewed),
            ("single_phase_gas_or_supercritical_reviewed", x.single_phase_gas_or_supercritical_reviewed),
        )
        if not reviewed
    ]
    if missing:
        return Calculation(
            status="needs_data",
            values={"assessment_id": x.assessment_id, "missing_reviews": missing},
            notes=(
                "Mixture fugacity is withheld until composition, EOS applicability and phase assumptions are reviewed.",
            ),
        )
    try:
        import CoolProp
        from CoolProp import PT_INPUTS, AbstractState
    except ImportError:
        return Calculation(
            status="needs_data",
            values={"assessment_id": x.assessment_id, "missing_dependency": "CoolProp"},
            notes=("Install the optional thermo dependency to evaluate this provider.",),
        )

    fluid_string = "&".join(x.components)
    try:
        state = _state if _state is not None else AbstractState(x.backend, fluid_string)
        state.set_mole_fractions(list(x.mole_fractions))
        state.update(PT_INPUTS, x.total_pressure_Pa, x.temperature_K)
        phase_index = int(state.phase())
        phase_name = _coolprop_phase_name(CoolProp, phase_index)
    except (ValueError, RuntimeError):
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "reason": "CoolProp_mixture_state_unavailable"},
            notes=(
                "The backend could not evaluate this composition/state; no fallback or ideal-mixture substitution is made.",
            ),
        )
    if not _supported_gas_phase(phase_name):
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "reason": "mixture_state_not_gas_or_supercritical",
                "coolprop_phase_index": phase_index,
                "coolprop_phase": phase_name,
            },
            notes=("Only gas, supercritical-gas or supercritical mixture states emit component fugacity.",),
        )

    co2_index = _co2_component_index(x.components)
    co2_mole_fraction = x.mole_fractions[co2_index]
    partial_pressure = co2_mole_fraction * x.total_pressure_Pa
    phi = float(state.fugacity_coefficient(co2_index))
    fugacity = float(state.fugacity(co2_index))
    if not math.isfinite(phi) or phi <= 0.0 or not math.isfinite(fugacity) or fugacity <= 0.0:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "reason": "invalid_CO2_mixture_fugacity_output"},
            notes=("CoolProp did not return finite positive component fugacity properties.",),
        )
    if not math.isclose(fugacity, phi * partial_pressure, rel_tol=1e-8, abs_tol=1e-10):
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "reason": "CO2_mixture_fugacity_identity_mismatch"},
            notes=(
                "CoolProp component fugacity did not match phi_i times the declared partial-pressure basis.",
            ),
        )

    configuration = {
        "provider_id": f"CoolProp:{x.backend}:{fluid_string}:CO2",
        "provider_revision": f"{CoolProp.__version__}:{CoolProp.__gitrevision__}",
        "backend": x.backend,
        "components": x.components,
        "mole_fractions": x.mole_fractions,
        "co2_component_index": co2_index,
        "temperature_K": x.temperature_K,
        "total_pressure_Pa": x.total_pressure_Pa,
        "review_id": x.review_id,
        "mixture_composition_reviewed": x.mixture_composition_reviewed,
        "mixture_eos_applicability_reviewed": x.mixture_eos_applicability_reviewed,
        "single_phase_gas_or_supercritical_reviewed": x.single_phase_gas_or_supercritical_reviewed,
    }
    configuration_digest = canonical_digest(configuration)
    record = {
        **configuration,
        "co2_partial_pressure_Pa": partial_pressure,
        "coolprop_phase_index": phase_index,
        "coolprop_phase": phase_name,
        "fugacity_coefficient": phi,
        "co2_fugacity_Pa": fugacity,
    }
    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "temperature_K": x.temperature_K,
            "total_pressure_Pa": x.total_pressure_Pa,
            "co2_partial_pressure_Pa": partial_pressure,
            "co2_mole_fraction": co2_mole_fraction,
            "fugacity_coefficient": phi,
            "co2_fugacity_Pa": fugacity,
            "coolprop_phase_index": phase_index,
            "coolprop_phase": phase_name,
            "gas_fugacity_provider_id": configuration["provider_id"],
            "gas_fugacity_provider_revision": configuration["provider_revision"],
            "gas_fugacity_configuration_digest": configuration_digest,
            "gas_fugacity_record_digest": canonical_digest(record),
            "mixture_composition_reviewed": True,
            "mixture_eos_applicability_reviewed": True,
            "single_phase_gas_or_supercritical_reviewed": True,
            "mixture_fugacity_computed": True,
        },
        notes=(
            "CO2 component fugacity is evaluated from the caller-specified CoolProp mixture EOS and total pressure.",
            "Result applicability depends on available binary interaction data and caller-reviewed composition/EOS suitability; no fallback model is used.",
            "Aqueous equilibrium, Henry coefficient, corrosion rate and integrity risk are not calculated.",
        ),
    )


def coolprop_co2_mixture_gas_fugacity(x: CoolPropCo2MixtureFugacityRequest) -> Calculation:
    """Evaluate one reviewed mixture state without exposing history state reuse controls."""
    return _evaluate_co2_mixture_fugacity(x)


def coolprop_co2_fugacity_to_carbonate_fields(values: dict[str, Any]) -> dict[str, Any]:
    """Map a computed provider result to the fixed-fugacity carbonate input field names."""
    required = (
        "co2_fugacity_Pa",
        "gas_fugacity_provider_id",
        "gas_fugacity_provider_revision",
        "gas_fugacity_configuration_digest",
        "gas_fugacity_record_digest",
    )
    if values.get("mixture_fugacity_computed") is not False:
        raise ValueError("provider result must explicitly identify the pure-component EOS approximation")
    if any(key not in values for key in required):
        raise ValueError("incomplete CoolProp CO2 fugacity result")
    if not values.get("pure_component_approximation_reviewed") or not values.get(
        "single_phase_gas_or_supercritical_reviewed"
    ):
        raise ValueError("required pure-component and phase reviews are absent")
    return {key: values[key] for key in required}


def coolprop_co2_fugacity_to_aquasoldb_fields(values: dict[str, Any]) -> dict[str, Any]:
    """Map a computed CO2 fugacity result to AquaSolDB's independent comparison inputs."""
    carbonate_fields = coolprop_co2_fugacity_to_carbonate_fields(values)
    if "temperature_K" not in values:
        raise ValueError("computed CoolProp CO2 fugacity result must include temperature_K")
    return {
        "co2_fugacity_Pa": carbonate_fields["co2_fugacity_Pa"],
        "fugacity_temperature_K": values["temperature_K"],
        "fugacity_provider_id": carbonate_fields["gas_fugacity_provider_id"],
        "fugacity_provider_revision": carbonate_fields["gas_fugacity_provider_revision"],
        "fugacity_configuration_digest": carbonate_fields["gas_fugacity_configuration_digest"],
        "fugacity_record_digest": carbonate_fields["gas_fugacity_record_digest"],
    }


def coolprop_co2_mixture_fugacity_to_carbonate_fields(values: dict[str, Any]) -> dict[str, Any]:
    """Map reviewed CO2 mixture component fugacity and provider lineage to carbonate inputs."""
    required = (
        "co2_fugacity_Pa",
        "gas_fugacity_provider_id",
        "gas_fugacity_provider_revision",
        "gas_fugacity_configuration_digest",
        "gas_fugacity_record_digest",
    )
    if values.get("mixture_fugacity_computed") is not True:
        raise ValueError("provider result must explicitly identify mixture component fugacity")
    if any(key not in values for key in required):
        raise ValueError("incomplete CoolProp CO2 mixture fugacity result")
    if not all(
        values.get(key)
        for key in (
            "mixture_composition_reviewed",
            "mixture_eos_applicability_reviewed",
            "single_phase_gas_or_supercritical_reviewed",
        )
    ):
        raise ValueError("required mixture composition, EOS and phase reviews are absent")
    return {key: values[key] for key in required}


def coolprop_co2_mixture_fugacity_to_aquasoldb_fields(values: dict[str, Any]) -> dict[str, Any]:
    """Map reviewed mixture fugacity to the AquaSolDB independent comparison field names."""
    carbonate_fields = coolprop_co2_mixture_fugacity_to_carbonate_fields(values)
    if "temperature_K" not in values:
        raise ValueError("computed CoolProp CO2 mixture fugacity result must include temperature_K")
    return {
        "co2_fugacity_Pa": carbonate_fields["co2_fugacity_Pa"],
        "fugacity_temperature_K": values["temperature_K"],
        "fugacity_provider_id": carbonate_fields["gas_fugacity_provider_id"],
        "fugacity_provider_revision": carbonate_fields["gas_fugacity_provider_revision"],
        "fugacity_configuration_digest": carbonate_fields["gas_fugacity_configuration_digest"],
        "fugacity_record_digest": carbonate_fields["gas_fugacity_record_digest"],
    }


def specifications():
    return [
        ModelSpec(
            "thermo.co2_mixture_fugacity_history",
            MixtureCo2FugacityHistory,
            co2_mixture_fugacity_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "time_basis": "1",
                "time_s[]": "s",
                "temperature_K_history[]": "K",
                "total_pressure_Pa_history[]": "Pa",
                "co2_partial_pressure_Pa_history[]": "Pa",
                "fugacity_coefficient_history[]": "1",
                "co2_fugacity_Pa_history[]": "Pa",
                "point_count": "count",
            },
            (
                "Evaluate ordered caller-specified gas-mixture CO2 component fugacity at exact PT time knots with CoolProp.",
                "Component identity/order and backend are fixed; mole fractions may vary at each knot and the provider state object is reused.",
                "No ideal-mixture fallback, temporal interpolation, aqueous equilibrium, Henry coefficient or corrosion response is inferred.",
            ),
            ("coolprop_low_level_fugacity",),
            qualification="engineering_screening",
            context_validator=_validate_mixture_fugacity_history_context,
        ),
        ModelSpec(
            "thermo.co2_pure_fugacity_history",
            PureCo2FugacityHistory,
            coolprop_pure_co2_fugacity_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "time_basis": "1",
                "time_s[]": "s",
                "temperature_K_history[]": "K",
                "co2_partial_pressure_Pa_history[]": "Pa",
                "fugacity_coefficient_history[]": "1",
                "co2_fugacity_Pa_history[]": "Pa",
                "point_count": "count",
            },
            (
                "Evaluate ordered caller-supplied pure-CO2 PT requests with the selected optional CoolProp backend at exact time points.",
                "Preserve provider lineage and stop on the first failed point with a computed prefix; no mixture interactions or temporal interpolation are inferred.",
                "Aqueous equilibrium, Henry solubility, corrosion rate, structural life and acceptance are outside the model.",
            ),
            ("coolprop_low_level_fugacity",),
            qualification="engineering_screening",
            context_validator=_validate_pure_fugacity_history_context,
        ),
        ModelSpec(
            "thermo.co2_fugacity_coolprop",
            CoolPropCo2FugacityRequest,
            coolprop_co2_gas_fugacity,
            {
                "temperature_K": "K",
                "co2_partial_pressure_Pa": "Pa",
                "fugacity_coefficient": "1",
                "co2_fugacity_Pa": "Pa",
                "coolprop_phase_index": "1",
                "gas_fugacity_configuration_digest": "1",
                "gas_fugacity_record_digest": "1",
                "mixture_fugacity_computed": "1",
            },
            (
                "CoolProp pure-component CO2 EOS is evaluated at caller-supplied absolute CO2 partial pressure.",
                "Caller review is required for single-phase gas/supercritical use and the pure-component approximation to a mixture.",
                "Mixture fugacity, aqueous chemistry, corrosion rate and structural risk are outside this model.",
            ),
            ("coolprop_low_level_fugacity",),
        ),
        ModelSpec(
            "thermo.co2_mixture_fugacity_coolprop",
            CoolPropCo2MixtureFugacityRequest,
            coolprop_co2_mixture_gas_fugacity,
            {
                "temperature_K": "K",
                "total_pressure_Pa": "Pa",
                "co2_partial_pressure_Pa": "Pa",
                "co2_mole_fraction": "1",
                "fugacity_coefficient": "1",
                "co2_fugacity_Pa": "Pa",
                "coolprop_phase_index": "1",
                "gas_fugacity_configuration_digest": "1",
                "gas_fugacity_record_digest": "1",
                "mixture_fugacity_computed": "1",
            },
            (
                "CoolProp's caller-configured mixture EOS evaluates the CO2 component fugacity at total pressure and normalized gas mole fractions.",
                "Caller review is required for composition, available binary interaction parameters, EOS applicability and single-phase gas/supercritical conditions.",
                "No ideal-mixture fallback, aqueous equilibrium, Henry coefficient, corrosion rate or structural risk is inferred.",
            ),
            ("coolprop_low_level_fugacity",),
        ),
    ]
