"""Optional CoolProp adapter for pure-water saturated-vapor fugacity at a wall temperature."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

PROVIDER_ID = "thermo.coolprop_pure_water_saturated_vapor_fugacity"
SOURCE_ID = "coolprop_pure_water_saturated_vapor_state"
STATE_PROVIDER_ID = "thermo.coolprop_pure_water_single_phase_state"
STATE_SOURCE_ID = "coolprop_pure_water_single_phase_state"


class CoolPropPureWaterSaturationFugacityRequest(Contract):
    """Typed request for a pure-water saturation state, separate from gas-mixture water fugacity."""

    wall_temperature_K: float = Field(gt=0)
    backend: str = Field(default="HEOS", min_length=1)
    caller_absolute_bound_Pa: float = Field(ge=0)
    pure_water_condensate_phase_applicability_reviewed: bool

    @model_validator(mode="after")
    def finite_values(self):
        if not all(math.isfinite(value) for value in (self.wall_temperature_K, self.caller_absolute_bound_Pa)):
            raise ValueError("temperature and caller absolute bound must be finite")
        if not self.pure_water_condensate_phase_applicability_reviewed:
            raise ValueError("explicit applicability review is required before using pure-water saturation")
        return self


class CoolPropPureWaterSinglePhaseStateRequest(Contract):
    """Caller-reviewed pure-water P-T state request for a declared single phase."""

    temperature_K: float = Field(gt=0)
    pressure_Pa: float = Field(gt=0)
    backend: str = Field(default="HEOS", min_length=1)
    expected_phase: Literal[
        "liquid", "gas", "supercritical_liquid", "supercritical_gas", "supercritical"
    ]
    pure_water_and_phase_applicability_reviewed: bool

    @model_validator(mode="after")
    def finite_and_reviewed(self):
        if not all(math.isfinite(value) for value in (self.temperature_K, self.pressure_Pa)):
            raise ValueError("temperature and absolute pressure must be finite")
        if not self.pure_water_and_phase_applicability_reviewed:
            raise ValueError("pure-water composition and phase applicability review is required")
        return self


def pure_water_single_phase_state_from_coolprop(
    request: CoolPropPureWaterSinglePhaseStateRequest,
) -> dict[str, Any]:
    """Return a digest-pinned single-phase water state from optional CoolProp.

    The caller declares the expected phase. Two-phase states are rejected, and
    this routine does not infer a brine, glycol, mixture, or corrosion model.
    """
    try:
        import CoolProp
        import CoolProp.CoolProp as CP
    except ImportError as exc:
        raise RuntimeError(
            "CoolProp is optional and required for this property call; install a compatible CoolProp build"
        ) from exc

    try:
        state = CP.AbstractState(request.backend, "Water")
        state.update(CP.PT_INPUTS, request.pressure_Pa, request.temperature_K)
        phase = state.phase()
        phases = CP.phases
        allowed_phases = {
            "liquid": {phases.iphase_liquid},
            "gas": {phases.iphase_gas},
            "supercritical_liquid": {phases.iphase_supercritical_liquid},
            "supercritical_gas": {phases.iphase_supercritical_gas},
            "supercritical": {phases.iphase_supercritical},
        }[request.expected_phase]
        if phase not in allowed_phases:
            if phase == phases.iphase_twophase:
                raise ValueError("CoolProp returned a two-phase state; this API accepts single-phase states only")
            raise ValueError(
                f"CoolProp phase {phase!r} does not match caller-declared {request.expected_phase!r} phase"
            )
        values = {
            "density_kg_m3": float(state.rhomass()),
            "specific_enthalpy_J_kg": float(state.hmass()),
            "specific_heat_capacity_cp_J_kg_K": float(state.cpmass()),
            "dynamic_viscosity_Pa_s": float(state.viscosity()),
            "thermal_conductivity_W_m_K": float(state.conductivity()),
            "speed_of_sound_m_s": float(state.speed_sound()),
            "compressibility_factor": float(state.compressibility_factor()),
        }
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"CoolProp backend {request.backend!r} could not provide the requested pure-water P-T state"
        ) from exc

    if any(not math.isfinite(value) for value in values.values()):
        raise RuntimeError("CoolProp returned a nonfinite pure-water property")
    if any(values[key] <= 0.0 for key in (
        "density_kg_m3", "specific_heat_capacity_cp_J_kg_K", "dynamic_viscosity_Pa_s",
        "thermal_conductivity_W_m_K", "speed_of_sound_m_s", "compressibility_factor",
    )):
        raise RuntimeError("CoolProp returned a nonpositive property outside supported numerical state")

    version = str(CoolProp.__version__)
    revision = str(getattr(CoolProp, "__gitrevision__", "unknown"))
    configuration = {
        "provider": "CoolProp.AbstractState",
        "backend": request.backend,
        "fluid": "Water",
        "input_pair": "PT_INPUTS",
        "temperature_K": request.temperature_K,
        "pressure_Pa": request.pressure_Pa,
        "expected_phase": request.expected_phase,
        "returned_phase_code": int(phase),
        "version": version,
        "revision": revision,
    }
    config_sha = canonical_digest(configuration)
    result_sha = canonical_digest({"configuration_sha256": config_sha, **values})
    provider_id = f"CoolProp:{request.backend}::Water.single_phase_state"
    evidence = Evidence(
        source_id=provider_id,
        origin="model_prediction",
        citation=(
            f"CoolProp {version} ({revision}), {request.backend} backend, pure Water P-T state; "
            f"caller-declared {request.expected_phase} phase"
        ),
        license_id="MIT",
        sha256=result_sha,
    )
    return {
        **values,
        "expected_phase": request.expected_phase,
        "coolprop_phase_code": int(phase),
        "water_property_provider_id": provider_id,
        "water_property_provider_revision": f"{version}:{revision}",
        "water_configuration_sha256": config_sha,
        "water_result_sha256": result_sha,
        "water_provider_evidence": evidence,
        "provider_model_id": STATE_PROVIDER_ID,
        "source_id": STATE_SOURCE_ID,
    }


def evaluate_pure_water_single_phase_state(
    request: CoolPropPureWaterSinglePhaseStateRequest,
) -> Calculation:
    """Registry envelope for the caller-phase-reviewed property state."""
    values = pure_water_single_phase_state_from_coolprop(request)
    values["water_provider_evidence"] = values["water_provider_evidence"].model_dump(mode="json")
    return Calculation(values={"status": "computed", **values})


def pure_water_saturated_vapor_fugacity_from_coolprop(
    request: CoolPropPureWaterSaturationFugacityRequest,
) -> dict[str, Any]:
    """Return a provenance-pinned pure-water saturation fugacity record.

    This adapter deliberately does not calculate gas-side water fugacity, CO2
    fugacity, Henry data, brine/MEG water activity, or a condensation rate.
    CoolProp is imported only when this function is called.
    """
    wall_temperature_K = request.wall_temperature_K
    backend = request.backend
    caller_absolute_bound_Pa = request.caller_absolute_bound_Pa

    # Optional dependency remains lazy; no module-level CoolProp import.
    try:
        import CoolProp
        import CoolProp.CoolProp as CP
    except ImportError as exc:
        raise RuntimeError(
            "CoolProp is optional and required for this property call; install a compatible CoolProp build"
        ) from exc

    fluid = "Water"
    provider_id = f"CoolProp:{backend}::Water.saturated_vapor_fugacity"
    try:
        state = CP.AbstractState(backend, fluid)
        triple_temperature_K = float(state.Ttriple())
        critical_temperature_K = float(state.T_critical())
        if not triple_temperature_K < wall_temperature_K < critical_temperature_K:
            raise ValueError(
                "pure-water vapor saturation is supported only strictly between triple and critical temperatures"
            )
        state.update(CP.QT_INPUTS, 1.0, wall_temperature_K)
        saturation_pressure_Pa = float(state.p())
        # QT identifies the saturated-vapor density, while CoolProp 8 rejects
        # fugacity on its two-phase state object. Evaluate the same vapor
        # density and temperature on the explicitly known gas branch.
        saturated_vapor_density_mol_m3 = float(state.rhomolar())
        state.specify_phase(CP.iphase_gas)
        state.update(CP.DmolarT_INPUTS, saturated_vapor_density_mol_m3, wall_temperature_K)
        vapor_fugacity_coefficient = float(state.fugacity_coefficient(0))
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"CoolProp backend {backend!r} could not provide pure-water saturation vapor fugacity"
        ) from exc

    if (
        not math.isfinite(saturation_pressure_Pa)
        or saturation_pressure_Pa <= 0.0
        or not math.isfinite(vapor_fugacity_coefficient)
        or vapor_fugacity_coefficient <= 0.0
    ):
        raise RuntimeError("CoolProp returned a nonpositive or nonfinite saturation state")
    saturated_vapor_fugacity_Pa = saturation_pressure_Pa * vapor_fugacity_coefficient
    if not math.isfinite(saturated_vapor_fugacity_Pa) or saturated_vapor_fugacity_Pa <= 0.0:
        raise RuntimeError("saturated-vapor fugacity exceeds finite positive numeric support")

    version = str(CoolProp.__version__)
    revision = str(getattr(CoolProp, "__gitrevision__", "unknown"))
    configuration = {
        "provider": "CoolProp.AbstractState",
        "backend": backend,
        "fluid": fluid,
        "input_pair": "QT_INPUTS",
        "fugacity_evaluation_pair": "DmolarT_INPUTS_at_QT_saturated_vapor_density",
        "fugacity_phase": "gas",
        "quality": 1.0,
        "wall_temperature_K": wall_temperature_K,
        "property": "pure-water saturated-vapor fugacity = saturation pressure * vapor fugacity coefficient",
        "version": version,
        "revision": revision,
        "caller_absolute_bound_Pa": caller_absolute_bound_Pa,
    }
    result = {
        "saturation_pressure_Pa": saturation_pressure_Pa,
        "saturated_vapor_fugacity_coefficient": vapor_fugacity_coefficient,
        "saturated_vapor_fugacity_Pa": saturated_vapor_fugacity_Pa,
        "triple_temperature_K": triple_temperature_K,
        "critical_temperature_K": critical_temperature_K,
        "caller_absolute_bound_Pa": caller_absolute_bound_Pa,
    }
    config_sha = canonical_digest(configuration)
    result_sha = canonical_digest({"configuration_sha256": config_sha, **result})
    evidence = Evidence(
        source_id=provider_id,
        origin="model_prediction",
        citation=f"CoolProp {version} ({revision}), {backend} backend, pure Water saturated vapor state at caller wall temperature",
        license_id="MIT",
        sha256=result_sha,
    )
    return {
        "condensate_water_equilibrium_fugacity_at_wall_Pa": saturated_vapor_fugacity_Pa,
        "wall_equilibrium_fugacity_absolute_bound_Pa": caller_absolute_bound_Pa,
        "water_property_provider_id": provider_id,
        "water_property_provider_revision": f"{version}:{revision}",
        "water_configuration_sha256": config_sha,
        "water_result_sha256": result_sha,
        "water_provider_evidence": evidence,
        "provider_model_id": PROVIDER_ID,
        "source_id": SOURCE_ID,
        "water_property_details": result | {
            "provider_id": provider_id,
            "provider_version": version,
            "provider_revision": revision,
            "configuration_sha256": config_sha,
            "result_sha256": result_sha,
            "standard_state": "pure-water saturated vapor fugacity from CoolProp EOS",
            "mixture_or_solution_activity_included": False,
        },
    }


def evaluate_pure_water_saturation_fugacity(request: CoolPropPureWaterSaturationFugacityRequest) -> Calculation:
    """Registry adapter returning the provider record in the common result envelope."""
    values = pure_water_saturated_vapor_fugacity_from_coolprop(request)
    values["water_provider_evidence"] = values["water_provider_evidence"].model_dump(mode="json")
    return Calculation(values={"status": "computed", **values})


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=PROVIDER_ID,
        input_type=CoolPropPureWaterSaturationFugacityRequest,
        evaluator=evaluate_pure_water_saturation_fugacity,
        units={
            "wall_temperature_K": "K",
            "saturation_pressure_Pa": "Pa",
            "saturated_vapor_fugacity_Pa": "Pa",
            "caller_absolute_bound_Pa": "Pa",
        },
        assumptions=(
            "Pure-water saturated vapor is evaluated at the caller wall temperature using the requested CoolProp backend.",
            "Returned fugacity coefficient and pressure use the CoolProp provider convention and pinned runtime revision.",
            "The output is not gas-mixture water fugacity, brine/MEG water activity, condensate inventory or corrosion rate.",
            "Caller-declared bounds and phase applicability review are required and are not inferred by the provider.",
        ),
        source_ids=(SOURCE_ID, "coolprop_high_level", "coolprop_low_level_fugacity"),
        qualification="engineering_screening",
    ), ModelSpec(
        model_id=STATE_PROVIDER_ID,
        input_type=CoolPropPureWaterSinglePhaseStateRequest,
        evaluator=evaluate_pure_water_single_phase_state,
        units={
            "temperature_K": "K",
            "pressure_Pa": "Pa",
            "density_kg_m3": "kg/m^3",
            "specific_enthalpy_J_kg": "J/kg",
            "specific_heat_capacity_cp_J_kg_K": "J/kg/K",
            "dynamic_viscosity_Pa_s": "Pa*s",
            "thermal_conductivity_W_m_K": "W/m/K",
            "speed_of_sound_m_s": "m/s",
            "compressibility_factor": "1",
        },
        assumptions=(
            "Pure water is evaluated at the caller absolute-pressure/temperature state with the selected CoolProp backend.",
            "The caller-declared phase must match a single-phase CoolProp state; two-phase states are rejected.",
            "Provider outputs are pinned by CoolProp version/revision and request/result digests.",
            "The state is not a brine, glycol or gas-mixture property, and it is not a corrosion or acceptance model.",
            "Caller phase/composition applicability is required and is not inferred by this provider.",
        ),
        source_ids=(STATE_SOURCE_ID, "coolprop_high_level", "coolprop_abstract_state_single_phase_properties"),
        qualification="engineering_screening",
    )]
