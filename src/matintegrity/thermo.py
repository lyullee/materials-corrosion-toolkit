"""Optional thermodynamic provider; inputs and outputs use absolute SI quantities."""

from __future__ import annotations

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Positive, canonical_digest, check_finite


class ThermoRequest(Contract):
    fluid: str = Field(min_length=1)
    pressure_Pa: Positive
    temperature_K: Positive | None = None
    vapor_quality: float | None = Field(default=None, ge=0, le=1)
    backend: str = "HEOS"

    @model_validator(mode="after")
    def independent_pair(self):
        if (self.temperature_K is None) == (self.vapor_quality is None):
            raise ValueError("supply temperature or vapor quality, exactly one")
        return self


def fluid_state(request: ThermoRequest) -> dict:
    import CoolProp
    from CoolProp.CoolProp import PhaseSI, PropsSI

    key, value = (
        ("T", request.temperature_K) if request.temperature_K is not None else ("Q", request.vapor_quality)
    )
    fluid = f"{request.backend}::{request.fluid}"
    outputs = {
        name: float(PropsSI(symbol, "P", request.pressure_Pa, key, value, fluid))
        for name, symbol in [
            ("temperature_K", "T"),
            ("pressure_Pa", "P"),
            ("density_kg_m3", "Dmass"),
            ("specific_enthalpy_J_kg", "Hmass"),
            ("specific_entropy_J_kg_K", "Smass"),
        ]
    }
    result = dict(
        schema_version="matintegrity.fluid_state.v1",
        request=request.model_dump(mode="json"),
        properties=outputs,
        phase=PhaseSI("P", request.pressure_Pa, key, value, fluid),
        coolprop_version=CoolProp.__version__,
        coolprop_revision=CoolProp.__gitrevision__,
    )
    check_finite(result)
    return result


def boil_off_saturation_state_from_coolprop(*, fluid: str, pressure_Pa: float):
    """Return a pure-fluid HEOS saturation pair for bath calorimetry."""
    from CoolProp.CoolProp import get_fluid_param_string

    from .models.testmethods import SaturationCalorimetryState

    if not fluid or any(token in fluid for token in ("::", "&", "[", "]")):
        raise ValueError("a single pure-fluid name is required")
    if get_fluid_param_string(fluid, "pure").lower() != "true":
        raise ValueError("boil-off saturation provider supports pure fluids only")
    liquid = fluid_state(ThermoRequest(fluid=fluid, pressure_Pa=pressure_Pa, vapor_quality=0.0))
    vapor = fluid_state(ThermoRequest(fluid=fluid, pressure_Pa=pressure_Pa, vapor_quality=1.0))
    lp, vp = liquid["properties"], vapor["properties"]
    if abs(lp["temperature_K"] - vp["temperature_K"]) > 1e-8 * lp["temperature_K"]:
        raise ValueError("saturation pair temperature mismatch")
    values = dict(
        fluid_id=fluid,
        pressure_Pa=pressure_Pa,
        temperature_K=lp["temperature_K"],
        liquid_density_kg_m3=lp["density_kg_m3"],
        vapor_density_kg_m3=vp["density_kg_m3"],
        liquid_enthalpy_J_kg=lp["specific_enthalpy_J_kg"],
        vapor_enthalpy_J_kg=vp["specific_enthalpy_J_kg"],
        provider_id="CoolProp:HEOS",
        provider_version=liquid["coolprop_version"],
        provider_revision=liquid["coolprop_revision"],
    )
    digest = canonical_digest(values)
    return SaturationCalorimetryState(
        **values,
        provider_state_digest=digest,
        evidence=(
            Evidence(
                source_id="coolprop_saturation_pair",
                origin="model_prediction",
                citation="CoolProp HEOS P,Q=0 and P,Q=1 property evaluations",
                sha256=digest,
            ),
        ),
    )


def cavitation_inputs_from_coolprop(
    *,
    fluid: str,
    temperature_K: float,
    local_static_pressure_Pa: float,
    characteristic_velocity_m_s: float,
    local_pressure_definition: str,
    velocity_definition: str,
    backend: str = "HEOS",
) -> dict:
    """Build cavitation-margin inputs from a saturated-liquid CoolProp state."""
    import CoolProp
    from CoolProp.CoolProp import PropsSI

    if temperature_K <= 0 or local_static_pressure_Pa <= 0 or characteristic_velocity_m_s <= 0:
        raise ValueError("temperature, absolute pressure and characteristic velocity must be positive")
    if not fluid or not local_pressure_definition or not velocity_definition:
        raise ValueError("fluid and hydraulic quantity definitions are required")
    provider_fluid = f"{backend}::{fluid}"
    vapor_pressure = float(PropsSI("P", "T", temperature_K, "Q", 0, provider_fluid))
    liquid_density = float(PropsSI("Dmass", "T", temperature_K, "Q", 0, provider_fluid))
    provider_state = {
        "provider": "CoolProp",
        "version": CoolProp.__version__,
        "revision": CoolProp.__gitrevision__,
        "backend": backend,
        "fluid": fluid,
        "temperature_K": temperature_K,
        "saturation_quality": 0,
        "vapor_pressure_Pa": vapor_pressure,
        "saturated_liquid_density_kg_m3": liquid_density,
    }
    check_finite(provider_state)
    return {
        "fluid_id": fluid,
        "temperature_K": temperature_K,
        "pressure_basis": "absolute",
        "local_static_pressure_Pa": local_static_pressure_Pa,
        "vapor_pressure_Pa": vapor_pressure,
        "liquid_density_kg_m3": liquid_density,
        "characteristic_velocity_m_s": characteristic_velocity_m_s,
        "property_provider_id": f"CoolProp:{backend}",
        "property_provider_version": f"{CoolProp.__version__}:{CoolProp.__gitrevision__}",
        "property_state_digest": canonical_digest(provider_state),
        "local_pressure_definition": local_pressure_definition,
        "velocity_definition": velocity_definition,
        "absolute_pressure_reviewed": True,
        "thermodynamic_state_reviewed": True,
    }


def cavitation_history_inputs_from_coolprop(
    *,
    history_id: str,
    asset_id: str,
    location_id: str,
    clock_id: str,
    history_origin: str,
    hydraulic_source_digest: str,
    fluid: str,
    sample_ids: list[str],
    time_s: list[float],
    temperature_K: list[float],
    local_static_pressure_Pa: list[float],
    characteristic_velocity_m_s: list[float],
    sample_valid: list[bool],
    local_pressure_definition: str,
    velocity_definition: str,
    backend: str = "HEOS",
) -> dict:
    """Build aligned cavitation-history inputs from CoolProp saturation states."""
    import CoolProp
    from CoolProp.CoolProp import PropsSI

    count = len(sample_ids)
    vectors = (
        time_s,
        temperature_K,
        local_static_pressure_Pa,
        characteristic_velocity_m_s,
        sample_valid,
    )
    if count < 2 or any(len(vector) != count for vector in vectors):
        raise ValueError("at least two aligned cavitation-history samples are required")
    if not history_id or not fluid or not local_pressure_definition or not velocity_definition:
        raise ValueError("history, fluid and hydraulic quantity definitions are required")
    provider_fluid = f"{backend}::{fluid}"
    provider_states = []
    vapor_pressures = []
    liquid_densities = []
    for sample_id, temperature in zip(sample_ids, temperature_K, strict=True):
        vapor_pressure = float(PropsSI("P", "T", temperature, "Q", 0, provider_fluid))
        liquid_density = float(PropsSI("Dmass", "T", temperature, "Q", 0, provider_fluid))
        state = {
            "sample_id": sample_id,
            "provider": "CoolProp",
            "version": CoolProp.__version__,
            "revision": CoolProp.__gitrevision__,
            "backend": backend,
            "fluid": fluid,
            "temperature_K": temperature,
            "saturation_quality": 0,
            "vapor_pressure_Pa": vapor_pressure,
            "saturated_liquid_density_kg_m3": liquid_density,
        }
        check_finite(state)
        provider_states.append(state)
        vapor_pressures.append(vapor_pressure)
        liquid_densities.append(liquid_density)
    return {
        "history_id": history_id,
        "asset_id": asset_id,
        "location_id": location_id,
        "clock_id": clock_id,
        "history_origin": history_origin,
        "hydraulic_source_digest": hydraulic_source_digest,
        "fluid_id": fluid,
        "pressure_basis": "absolute",
        "sample_ids": sample_ids,
        "time_s": time_s,
        "local_static_pressure_Pa": local_static_pressure_Pa,
        "temperature_K": temperature_K,
        "vapor_pressure_Pa": vapor_pressures,
        "liquid_density_kg_m3": liquid_densities,
        "characteristic_velocity_m_s": characteristic_velocity_m_s,
        "sample_valid": sample_valid,
        "property_provider_id": f"CoolProp:{backend}",
        "property_provider_version": f"{CoolProp.__version__}:{CoolProp.__gitrevision__}",
        "property_state_digests": [canonical_digest(state) for state in provider_states],
        "property_history_digest": canonical_digest(provider_states),
        "local_pressure_definition": local_pressure_definition,
        "velocity_definition": velocity_definition,
        "interpolation": "linear",
        "absolute_pressure_reviewed": True,
        "thermodynamic_state_reviewed": True,
    }


def winterization_inputs_from_coolprop(
    *,
    case_id: str,
    fluid: str,
    pressure_Pa_abs: float,
    inventory_mass_kg: float,
    initial_bulk_temperature_K: float,
    minimum_allowable_temperature_K: float,
    time_s: list[float],
    interval_ambient_temperature_K: list[float],
    interval_heat_loss_conductance_W_K: list[float],
    interval_heat_tracing_power_W: list[float],
    property_evaluation_temperature_K: list[float],
    backend: str = "HEOS",
) -> dict:
    """Create winterization inputs from reviewed, single-phase CoolProp states."""
    import CoolProp
    from CoolProp.CoolProp import PhaseSI, PropsSI

    interval_count = len(time_s) - 1
    interval_vectors = (
        interval_ambient_temperature_K,
        interval_heat_loss_conductance_W_K,
        interval_heat_tracing_power_W,
        property_evaluation_temperature_K,
    )
    if not case_id or not fluid or not backend:
        raise ValueError("case, fluid and backend identifiers are required")
    if pressure_Pa_abs <= 0 or inventory_mass_kg <= 0:
        raise ValueError("absolute pressure and inventory mass must be positive")
    if interval_count < 1 or any(len(values) != interval_count for values in interval_vectors):
        raise ValueError("one ambient, conductance, heat input and property state per interval required")

    provider_fluid = f"{backend}::{fluid}"
    states = []
    heat_capacities = []
    phases = []
    for index, temperature in enumerate(property_evaluation_temperature_K):
        heat_capacity = float(PropsSI("Cpmass", "T", temperature, "P", pressure_Pa_abs, provider_fluid))
        phase = str(PhaseSI("T", temperature, "P", pressure_Pa_abs, provider_fluid))
        if heat_capacity <= 0 or phase in {"twophase", "unknown"}:
            raise ValueError("winterization property states must have positive heat capacity and one phase")
        state = {
            "interval_index": index,
            "provider": "CoolProp",
            "version": CoolProp.__version__,
            "revision": CoolProp.__gitrevision__,
            "backend": backend,
            "fluid": fluid,
            "pressure_Pa_abs": pressure_Pa_abs,
            "temperature_K": temperature,
            "phase": phase,
            "effective_isobaric_heat_capacity_J_kg_K": heat_capacity,
        }
        check_finite(state)
        states.append(state)
        heat_capacities.append(heat_capacity)
        phases.append(phase)

    return {
        "case_id": case_id,
        "fluid_id": fluid,
        "pressure_Pa_abs": pressure_Pa_abs,
        "inventory_mass_kg": inventory_mass_kg,
        "initial_bulk_temperature_K": initial_bulk_temperature_K,
        "minimum_allowable_temperature_K": minimum_allowable_temperature_K,
        "time_s": time_s,
        "interval_ambient_temperature_K": interval_ambient_temperature_K,
        "interval_heat_loss_conductance_W_K": interval_heat_loss_conductance_W_K,
        "interval_heat_tracing_power_W": interval_heat_tracing_power_W,
        "interval_effective_isobaric_heat_capacity_J_kg_K": heat_capacities,
        "property_evaluation_temperature_K": property_evaluation_temperature_K,
        "property_phase": phases,
        "property_provider_id": f"CoolProp:{backend}",
        "property_provider_version": f"{CoolProp.__version__}:{CoolProp.__gitrevision__}",
        "property_history_digest": canonical_digest(states),
        "inventory_and_mixing_reviewed": True,
        "conductance_history_reviewed": True,
        "heat_tracing_history_reviewed": True,
        "property_states_reviewed": True,
        "minimum_temperature_reviewed": True,
    }


def insulation_condensation_inputs_from_coolprop(
    *,
    assessment_id: str,
    asset_id: str,
    location_id: str,
    insulation_system_id: str,
    outer_surface_location_definition: str,
    clock_id: str,
    time_s: list[float],
    outer_surface_temperature_K: list[float],
    ambient_dry_bulb_temperature_K: list[float],
    ambient_relative_humidity_fraction: list[float],
    ambient_pressure_Pa_abs: list[float],
    weather_barrier_state_id: list[str],
    barrier_states_allowing_external_moisture: list[str],
    temperature_measurement_uncertainty_K: float,
    dew_point_uncertainty_K: float,
    evidence: list[Evidence],
) -> dict:
    """Build reviewed condensation-exposure inputs from CoolProp humid-air dew points."""
    import CoolProp
    from CoolProp.HumidAirProp import HAPropsSI

    count = len(time_s) - 1
    vectors = (
        outer_surface_temperature_K,
        ambient_dry_bulb_temperature_K,
        ambient_relative_humidity_fraction,
        ambient_pressure_Pa_abs,
        weather_barrier_state_id,
    )
    if count < 1 or any(len(vector) != count for vector in vectors):
        raise ValueError("one aligned surface, ambient and barrier state is required per interval")
    if time_s[0] < 0:
        raise ValueError("condensation elapsed time cannot be negative")
    if any(end <= start for start, end in zip(time_s, time_s[1:], strict=False)):
        raise ValueError("condensation time knots must strictly increase")
    if any(temperature <= 0 for temperature in outer_surface_temperature_K):
        raise ValueError("outer-surface temperatures must be positive absolute values")
    if any(temperature <= 0 for temperature in ambient_dry_bulb_temperature_K):
        raise ValueError("ambient dry-bulb temperatures must be positive absolute values")
    if any(not 0 < pressure for pressure in ambient_pressure_Pa_abs):
        raise ValueError("humid-air pressure must be positive and absolute")
    if any(not 0 < humidity <= 1 for humidity in ambient_relative_humidity_fraction):
        raise ValueError("dew-point calculation requires relative humidity above zero and at most one")
    if temperature_measurement_uncertainty_K < 0 or dew_point_uncertainty_K < 0:
        raise ValueError("temperature uncertainties cannot be negative")
    if not evidence:
        raise ValueError("source evidence is required")

    states = []
    intervals = []
    for index in range(count):
        dew_point = float(
            HAPropsSI(
                "D",
                "T",
                ambient_dry_bulb_temperature_K[index],
                "P",
                ambient_pressure_Pa_abs[index],
                "R",
                ambient_relative_humidity_fraction[index],
            )
        )
        state = {
            "interval_index": index,
            "provider": "CoolProp.HAPropsSI",
            "version": CoolProp.__version__,
            "revision": CoolProp.__gitrevision__,
            "ambient_dry_bulb_temperature_K": ambient_dry_bulb_temperature_K[index],
            "ambient_relative_humidity_fraction": ambient_relative_humidity_fraction[index],
            "ambient_pressure_Pa_abs": ambient_pressure_Pa_abs[index],
            "ambient_dew_point_temperature_K": dew_point,
        }
        check_finite(state)
        states.append(state)
        intervals.append(
            {
                "interval_id": f"{assessment_id}:interval:{index}",
                "start_time_s": time_s[index],
                "end_time_s": time_s[index + 1],
                "outer_surface_temperature_K": outer_surface_temperature_K[index],
                "ambient_dew_point_temperature_K": dew_point,
                "weather_barrier_state_id": weather_barrier_state_id[index],
                "record_valid": True,
                "invalid_basis": None,
                "evidence": tuple(evidence),
            }
        )
    return {
        "assessment_id": assessment_id,
        "asset_id": asset_id,
        "location_id": location_id,
        "insulation_system_id": insulation_system_id,
        "outer_surface_location_definition": outer_surface_location_definition,
        "dew_point_definition": (
            f"CoolProp.HAPropsSI:{CoolProp.__version__}:{CoolProp.__gitrevision__}:"
            "dew point from dry-bulb temperature, absolute pressure and relative humidity"
        ),
        "dew_point_provider_state_digest": canonical_digest(states),
        "clock_id": clock_id,
        "horizon_start_s": time_s[0],
        "horizon_end_s": time_s[-1],
        "intervals": tuple(intervals),
        "barrier_states_allowing_external_moisture": tuple(barrier_states_allowing_external_moisture),
        "temperature_measurement_uncertainty_K": temperature_measurement_uncertainty_K,
        "dew_point_uncertainty_K": dew_point_uncertainty_K,
        "temperature_and_dew_point_units_reviewed": True,
        "surface_location_reviewed": True,
        "clock_and_coverage_reviewed": True,
        "weather_barrier_mapping_reviewed": True,
        "uncertainty_basis_reviewed": True,
        "evidence": tuple(evidence),
    }


def gas_pressure_decay_inputs_from_coolprop(
    *,
    fluid: str,
    rigid_volume_m3: float,
    initial_absolute_pressure_Pa: float,
    final_absolute_pressure_Pa: float,
    initial_temperature_K: float,
    final_temperature_K: float,
    duration_s: float,
    reference_pressure_Pa: float,
    reference_temperature_K: float,
    backend: str = "HEOS",
) -> dict:
    """Build pressure-decay inputs with endpoint compressibility from CoolProp."""
    import CoolProp
    from CoolProp.CoolProp import PhaseSI, PropsSI

    scalars = (
        rigid_volume_m3,
        initial_absolute_pressure_Pa,
        final_absolute_pressure_Pa,
        initial_temperature_K,
        final_temperature_K,
        duration_s,
        reference_pressure_Pa,
        reference_temperature_K,
    )
    if any(value <= 0 for value in scalars):
        raise ValueError("volume, absolute states, duration and reference state must be positive")
    if not fluid or not backend:
        raise ValueError("fluid and CoolProp backend identifiers are required")
    provider_fluid = f"{backend}::{fluid}"
    states = []
    factors = []
    for state_id, pressure, temperature in (
        ("initial", initial_absolute_pressure_Pa, initial_temperature_K),
        ("final", final_absolute_pressure_Pa, final_temperature_K),
        ("reference", reference_pressure_Pa, reference_temperature_K),
    ):
        factor = float(PropsSI("Z", "P", pressure, "T", temperature, provider_fluid))
        phase = str(PhaseSI("P", pressure, "T", temperature, provider_fluid))
        if factor <= 0 or phase in {"twophase", "unknown"}:
            raise ValueError("pressure-decay property states require positive Z and a resolved single phase")
        state = {
            "state_id": state_id,
            "provider": "CoolProp",
            "version": CoolProp.__version__,
            "revision": CoolProp.__gitrevision__,
            "backend": backend,
            "fluid": fluid,
            "absolute_pressure_Pa": pressure,
            "temperature_K": temperature,
            "phase": phase,
            "compressibility_factor": factor,
        }
        check_finite(state)
        states.append(state)
        factors.append(factor)
    return {
        "rigid_volume_m3": rigid_volume_m3,
        "initial_absolute_pressure_Pa": initial_absolute_pressure_Pa,
        "final_absolute_pressure_Pa": final_absolute_pressure_Pa,
        "initial_temperature_K": initial_temperature_K,
        "final_temperature_K": final_temperature_K,
        "initial_compressibility_factor": factors[0],
        "final_compressibility_factor": factors[1],
        "duration_s": duration_s,
        "reference_pressure_Pa": reference_pressure_Pa,
        "reference_temperature_K": reference_temperature_K,
        "reference_compressibility_factor": factors[2],
        "fluid_id": fluid,
        "property_provider_id": f"CoolProp:{backend}",
        "property_provider_version": f"{CoolProp.__version__}:{CoolProp.__gitrevision__}",
        "property_state_digest": canonical_digest(states),
        "absolute_pressure_temperature_and_phase_reviewed": True,
    }
