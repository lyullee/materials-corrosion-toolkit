"""Conservative ledger for caller-supplied competing solid reaction rates."""

from __future__ import annotations

import math
import sys

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec


class KineticAqueousSpeciesDefinition(Contract):
    species_id: str = Field(min_length=1)
    charge_number: int
    elemental_composition: dict[str, int]
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def valid_composition(self):
        if not self.elemental_composition or any(value < 0 for value in self.elemental_composition.values()):
            raise ValueError("aqueous species require explicit nonnegative elemental composition")
        if not any(self.elemental_composition.values()):
            raise ValueError("aqueous species elemental composition cannot be all zero")
        return self


class KineticAqueousSpecies(KineticAqueousSpeciesDefinition):
    initial_concentration_mol_m3: Nonnegative


class KineticSolidReaction(Contract):
    solid_species_id: str = Field(min_length=1)
    precipitation_stoichiometry: dict[str, Positive]
    solid_elemental_composition: dict[str, int]
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class KineticSolidPhase(KineticSolidReaction):
    initial_solid_moles_per_solution_volume_mol_m3: Nonnegative


def validate_neutral_solid_reaction_network(aqueous_species, candidate_solid_phases) -> None:
    species = {row.species_id: row for row in aqueous_species}
    phases = {row.solid_species_id: row for row in candidate_solid_phases}
    if len(species) != len(aqueous_species) or len(phases) != len(candidate_solid_phases):
        raise ValueError("aqueous species and solid phase IDs must be unique")
    if set(species) & set(phases):
        raise ValueError("aqueous and solid species identifiers must be distinct")
    for phase in candidate_solid_phases:
        if not phase.solid_elemental_composition or any(value < 0 for value in phase.solid_elemental_composition.values()):
            raise ValueError("each solid requires explicit nonnegative elemental composition")
        if not any(phase.solid_elemental_composition.values()):
            raise ValueError("solid composition cannot be all zero")
        if not phase.precipitation_stoichiometry or not set(phase.precipitation_stoichiometry) <= set(species):
            raise ValueError("each solid reaction must reference declared aqueous species")
        charge = math.fsum(species[key].charge_number * value for key, value in phase.precipitation_stoichiometry.items())
        if not math.isfinite(charge) or not math.isclose(charge, 0.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("each reaction to a neutral solid must conserve charge")
        elements = set(phase.solid_elemental_composition)
        for species_id in phase.precipitation_stoichiometry:
            elements.update(species[species_id].elemental_composition)
        for element in elements:
            aqueous = math.fsum(
                species[species_id].elemental_composition.get(element, 0) * coefficient
                for species_id, coefficient in phase.precipitation_stoichiometry.items()
            )
            solid = phase.solid_elemental_composition.get(element, 0)
            if not math.isfinite(aqueous) or not math.isclose(aqueous, solid, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("each solid reaction must conserve every declared element")


class CompetingSolidKineticInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    phase_extent_rate_mol_m3_s: dict[str, float]

    @model_validator(mode="after")
    def ordered_interval_and_rates(self):
        if not math.isfinite(self.start_time_s) or not math.isfinite(self.end_time_s) or self.end_time_s <= self.start_time_s:
            raise ValueError("kinetic interval must have finite positive duration")
        if any(not math.isfinite(value) for value in self.phase_extent_rate_mol_m3_s.values()):
            raise ValueError("caller-supplied phase rates must be finite")
        return self


class CompetingSolidKineticLedger(Contract):
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    kinetic_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: Positive
    kinetic_parameter_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    aqueous_species: tuple[KineticAqueousSpecies, ...] = Field(min_length=1, max_length=64)
    candidate_solid_phases: tuple[KineticSolidPhase, ...] = Field(min_length=2, max_length=16)
    intervals: tuple[CompetingSolidKineticInterval, ...] = Field(min_length=1, max_length=5000)
    absolute_balance_tolerance_mol_m3: Positive = 1e-10
    relative_balance_tolerance: float = Field(default=1e-9, gt=0, le=0.01)
    phase_stoichiometry_and_solution_volume_reviewed: bool
    caller_rate_law_units_temperature_and_support_reviewed: bool
    dissolution_then_precipitation_split_order_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_reaction_network_and_history(self):
        validate_neutral_solid_reaction_network(self.aqueous_species, self.candidate_solid_phases)
        species = {row.species_id: row for row in self.aqueous_species}
        phases = {row.solid_species_id: row for row in self.candidate_solid_phases}
        phase_ids = set(phases)
        interval_ids = [row.interval_id for row in self.intervals]
        if len(set(interval_ids)) != len(interval_ids):
            raise ValueError("kinetic interval IDs must be unique")
        if self.intervals[0].start_time_s != 0:
            raise ValueError("kinetic history must begin at zero seconds")
        for index, interval in enumerate(self.intervals):
            if set(interval.phase_extent_rate_mol_m3_s) != phase_ids:
                raise ValueError("each interval must supply exactly one signed rate for every candidate phase")
            if index and interval.start_time_s != self.intervals[index - 1].end_time_s:
                raise ValueError("kinetic intervals must be contiguous and ordered without gaps or overlap")
        return self


class SolidSaturationRateLaw(Contract):
    """Caller-calibrated precipitation and dissolution law for one neutral phase."""

    solid_species_id: str = Field(min_length=1)
    precipitation_rate_constant_mol_m3_s: Nonnegative
    precipitation_order: Positive = Field(le=8.0)
    dissolution_rate_constant_mol_m3_s: Nonnegative
    dissolution_order: Positive = Field(le=8.0)
    rate_constant_reference_temperature_K: Positive | None = None
    minimum_valid_temperature_K: Positive | None = None
    maximum_valid_temperature_K: Positive | None = None
    precipitation_activation_energy_J_mol: Nonnegative | None = None
    dissolution_activation_energy_J_mol: Nonnegative | None = None
    arrhenius_parameter_applicability_reviewed: bool = False
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_arrhenius_parameters(self):
        activation_energies = (
            self.precipitation_activation_energy_J_mol,
            self.dissolution_activation_energy_J_mol,
        )
        has_activation_energy = any(value is not None for value in activation_energies)
        has_temperature_support = (
            self.minimum_valid_temperature_K is not None
            and self.maximum_valid_temperature_K is not None
        )
        complete_arrhenius_parameters = (
            self.rate_constant_reference_temperature_K is not None and has_temperature_support
        )
        if has_activation_energy != complete_arrhenius_parameters:
            raise ValueError("Arrhenius parameters require activation energy, reference temperature and valid temperature limits")
        if (self.minimum_valid_temperature_K is None) != (self.maximum_valid_temperature_K is None):
            raise ValueError("both lower and upper valid temperatures must be supplied together")
        if not has_activation_energy and any((
            self.rate_constant_reference_temperature_K is not None,
            self.minimum_valid_temperature_K is not None,
            self.maximum_valid_temperature_K is not None,
        )):
            raise ValueError("reference temperature and valid limits are only used with activation energy")
        if has_temperature_support:
            if self.maximum_valid_temperature_K < self.minimum_valid_temperature_K:
                raise ValueError("valid temperature support must be ordered")
            if self.rate_constant_reference_temperature_K is not None and not (
                self.minimum_valid_temperature_K
                <= self.rate_constant_reference_temperature_K
                <= self.maximum_valid_temperature_K
            ):
                raise ValueError("reference temperature must lie within the declared valid support")
        if has_activation_energy and not self.arrhenius_parameter_applicability_reviewed:
            raise ValueError("Arrhenius temperature dependence requires explicit applicability review")
        if not has_activation_energy and self.arrhenius_parameter_applicability_reviewed:
            raise ValueError("Arrhenius applicability review requires at least one activation energy")
        return self


class CompetingSolidSaturationInterval(Contract):
    """Interval-constant, caller-supplied saturation ratios for candidate phases."""

    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    temperature_K: Positive | None = None
    saturation_ratio_by_phase: dict[str, Nonnegative]

    @model_validator(mode="after")
    def finite_positive_duration(self):
        if not math.isfinite(self.start_time_s) or not math.isfinite(self.end_time_s) or self.end_time_s <= self.start_time_s:
            raise ValueError("saturation interval must have finite positive duration")
        return self


class CompetingSolidSaturationKinetics(Contract):
    """Map caller saturation histories to phase rates, then apply the conservative ledger."""

    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    kinetic_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: Positive
    kinetic_parameter_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    aqueous_species: tuple[KineticAqueousSpecies, ...] = Field(min_length=1, max_length=64)
    candidate_solid_phases: tuple[KineticSolidPhase, ...] = Field(min_length=2, max_length=16)
    phase_rate_laws: tuple[SolidSaturationRateLaw, ...] = Field(min_length=2, max_length=16)
    intervals: tuple[CompetingSolidSaturationInterval, ...] = Field(min_length=1, max_length=5000)
    absolute_balance_tolerance_mol_m3: Positive = 1e-10
    relative_balance_tolerance: float = Field(default=1e-9, gt=0, le=0.01)
    phase_stoichiometry_and_solution_volume_reviewed: bool
    saturation_ratio_and_standard_state_reviewed: bool
    caller_rate_law_units_temperature_and_support_reviewed: bool
    dissolution_then_precipitation_split_order_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_phase_laws_and_clock(self):
        validate_neutral_solid_reaction_network(self.aqueous_species, self.candidate_solid_phases)
        phases = {row.solid_species_id for row in self.candidate_solid_phases}
        law_ids = [row.solid_species_id for row in self.phase_rate_laws]
        if len(set(law_ids)) != len(law_ids) or set(law_ids) != phases:
            raise ValueError("exactly one caller kinetic law is required for every candidate solid phase")
        interval_ids = [row.interval_id for row in self.intervals]
        if len(set(interval_ids)) != len(interval_ids) or self.intervals[0].start_time_s != 0:
            raise ValueError("saturation intervals require unique IDs and must begin at zero")
        for index, interval in enumerate(self.intervals):
            if set(interval.saturation_ratio_by_phase) != phases:
                raise ValueError("each interval must supply a saturation ratio for every candidate phase")
            if index and interval.start_time_s != self.intervals[index - 1].end_time_s:
                raise ValueError("saturation intervals must be contiguous and ordered")
        return self


def _derive_solid_saturation_rate(
    law: SolidSaturationRateLaw,
    saturation_ratio: float,
    *,
    temperature_K: float,
) -> dict:
    """Evaluate one explicitly caller-calibrated, interval-constant phase rate."""
    if not math.isfinite(saturation_ratio) or saturation_ratio < 0:
        raise ValueError("saturation ratio must be finite and nonnegative")
    if not math.isfinite(temperature_K) or temperature_K <= 0:
        raise ValueError("kinetic temperature must be finite and positive")
    if law.minimum_valid_temperature_K is not None and not (
        float(law.minimum_valid_temperature_K) <= temperature_K <= float(law.maximum_valid_temperature_K)
    ):
        raise ArithmeticError(f"Temperature for {law.solid_species_id} is outside its declared kinetic support")

    def adjusted_constant(reference_rate: float, activation_energy: float | None) -> float:
        if activation_energy is None or reference_rate == 0.0:
            return reference_rate
        reference_temperature = float(law.rate_constant_reference_temperature_K)
        log_ratio = -activation_energy / 8.31446261815324 * (
            1.0 / temperature_K - 1.0 / reference_temperature
        )
        log_rate = math.log(reference_rate) + log_ratio
        if log_rate > math.log(sys.float_info.max):
            raise ArithmeticError(f"Arrhenius rate constant for {law.solid_species_id} exceeds numeric support")
        try:
            adjusted = math.exp(log_rate)
        except OverflowError as error:
            raise ArithmeticError(
                f"Arrhenius rate constant for {law.solid_species_id} exceeds numeric support"
            ) from error
        if adjusted == 0.0:
            raise ArithmeticError(
                f"Arrhenius rate constant for {law.solid_species_id} underflows binary64 support"
            )
        return adjusted

    precipitation_constant = adjusted_constant(
        float(law.precipitation_rate_constant_mol_m3_s),
        law.precipitation_activation_energy_J_mol,
    )
    dissolution_constant = adjusted_constant(
        float(law.dissolution_rate_constant_mol_m3_s),
        law.dissolution_activation_energy_J_mol,
    )
    if saturation_ratio > 1.0:
        driving = saturation_ratio - 1.0
        rate = precipitation_constant * driving**law.precipitation_order
        direction = "precipitation"
    elif saturation_ratio < 1.0:
        driving = 1.0 - saturation_ratio
        rate = -dissolution_constant * driving**law.dissolution_order
        direction = "dissolution"
    else:
        driving, rate, direction = 0.0, 0.0, "equilibrium_threshold"
    if not math.isfinite(rate):
        raise ArithmeticError(f"rate law for {law.solid_species_id} exceeded finite numeric support")
    return {
        "saturation_ratio": saturation_ratio,
        "absolute_driving_distance": driving,
        "signed_extent_rate_mol_m3_s": rate,
        "selected_direction": direction,
        "rate_law_temperature_K": temperature_K,
        "rate_constant_reference_temperature_K": law.rate_constant_reference_temperature_K,
        "minimum_valid_temperature_K": law.minimum_valid_temperature_K,
        "maximum_valid_temperature_K": law.maximum_valid_temperature_K,
        "effective_precipitation_rate_constant_mol_m3_s": precipitation_constant,
        "effective_dissolution_rate_constant_mol_m3_s": dissolution_constant,
        "arrhenius_parameter_applicability_reviewed": law.arrhenius_parameter_applicability_reviewed,
    }


def evaluate_competing_solid_saturation_kinetics(request: CompetingSolidSaturationKinetics) -> Calculation:
    """Convert caller saturation ratios into bounded signed extent rates and ledger them.

    For each interval and phase, supersaturation drives the caller's precipitation
    power law and undersaturation drives its dissolution power law. The saturation
    ratio is held constant only over its declared interval; it is not computed from
    the aqueous state and does not trigger phase discovery or nucleation.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "kinetic_configuration_sha256": request.kinetic_configuration_sha256,
        "kinetic_parameter_source_sha256": request.kinetic_parameter_source_sha256,
        "input_sha256": digest,
        "temperature_K": request.temperature_K,
        "phase_rate_law_source_sha256": {law.solid_species_id: law.source_sha256 for law in request.phase_rate_laws},
    }
    reviews = {
        "phase_stoichiometry_and_solution_volume_reviewed": request.phase_stoichiometry_and_solution_volume_reviewed,
        "saturation_ratio_and_standard_state_reviewed": request.saturation_ratio_and_standard_state_reviewed,
        "caller_rate_law_units_temperature_and_support_reviewed": request.caller_rate_law_units_temperature_and_support_reviewed,
        "dissolution_then_precipitation_split_order_reviewed": request.dissolution_then_precipitation_split_order_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    laws = {law.solid_species_id: law for law in request.phase_rate_laws}
    phases = [phase.solid_species_id for phase in request.candidate_solid_phases]
    derived_intervals = []
    derived_history = []
    try:
        for interval in request.intervals:
            rates: dict[str, float] = {}
            diagnostics: dict[str, dict[str, float | str | bool | None]] = {}
            interval_temperature = (
                float(interval.temperature_K)
                if interval.temperature_K is not None
                else float(request.temperature_K)
            )
            for phase_id in phases:
                saturation = float(interval.saturation_ratio_by_phase[phase_id])
                row = _derive_solid_saturation_rate(
                    laws[phase_id], saturation, temperature_K=interval_temperature
                )
                rates[phase_id] = row["signed_extent_rate_mol_m3_s"]
                diagnostics[phase_id] = row
            derived_intervals.append(CompetingSolidKineticInterval(
                interval_id=interval.interval_id,
                start_time_s=interval.start_time_s,
                end_time_s=interval.end_time_s,
                phase_extent_rate_mol_m3_s=rates,
            ))
            derived_history.append({
                "interval_id": interval.interval_id,
                "start_time_s": interval.start_time_s,
                "end_time_s": interval.end_time_s,
                "temperature_K": interval_temperature,
                "phase_rate_diagnostics": diagnostics,
            })
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": str(error),
            "computed_rate_prefix": derived_history,
        })

    ledger_request = CompetingSolidKineticLedger(
        assessment_id=request.assessment_id,
        physical_scope_id=request.physical_scope_id,
        provider_id=request.provider_id,
        provider_revision=request.provider_revision,
        kinetic_configuration_sha256=request.kinetic_configuration_sha256,
        temperature_K=request.temperature_K,
        kinetic_parameter_source_sha256=request.kinetic_parameter_source_sha256,
        aqueous_species=request.aqueous_species,
        candidate_solid_phases=request.candidate_solid_phases,
        intervals=tuple(derived_intervals),
        absolute_balance_tolerance_mol_m3=request.absolute_balance_tolerance_mol_m3,
        relative_balance_tolerance=request.relative_balance_tolerance,
        phase_stoichiometry_and_solution_volume_reviewed=request.phase_stoichiometry_and_solution_volume_reviewed,
        caller_rate_law_units_temperature_and_support_reviewed=request.caller_rate_law_units_temperature_and_support_reviewed,
        dissolution_then_precipitation_split_order_reviewed=request.dissolution_then_precipitation_split_order_reviewed,
        computational_use_authorized=request.computational_use_authorized,
    )
    ledger = evaluate_competing_solid_kinetic_ledger(ledger_request)
    return Calculation(
        status=ledger.status,
        values=base | {
            "derived_rate_history": derived_history,
            "kinetic_ledger": ledger.values,
            "rate_basis": "caller_supplied_interval_constant_saturation_ratio_and_phase_specific_power_laws",
        },
        notes=(
            "The API evaluates user-supplied saturation-driven rate coefficients and orders, then applies the existing conservative multi-phase inventory ledger.",
            "It does not calculate saturation from composition, solve aqueous equilibrium, discover phases, predict nucleation, or provide material/process qualification.",
        ),
    )


def evaluate_competing_solid_kinetic_ledger(request: CompetingSolidKineticLedger) -> Calculation:
    """Apply signed caller rates with a fixed dissolution-then-precipitation split.

    Positive extent precipitates a solid and consumes its declared aqueous reactants;
    negative extent dissolves the same phase and is limited by its current inventory.
    Simultaneous positive requests share one proportional aqueous-resource limiter.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "kinetic_configuration_sha256": request.kinetic_configuration_sha256,
        "kinetic_parameter_source_sha256": request.kinetic_parameter_source_sha256,
        "temperature_K": request.temperature_K,
        "input_sha256": digest,
        "aqueous_species_source_sha256": {row.species_id: row.source_sha256 for row in request.aqueous_species},
        "solid_phase_source_sha256": {row.solid_species_id: row.source_sha256 for row in request.candidate_solid_phases},
    }
    reviews = {
        "phase_stoichiometry_and_solution_volume_reviewed": request.phase_stoichiometry_and_solution_volume_reviewed,
        "caller_rate_law_units_temperature_and_support_reviewed": request.caller_rate_law_units_temperature_and_support_reviewed,
        "dissolution_then_precipitation_split_order_reviewed": request.dissolution_then_precipitation_split_order_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    species = request.aqueous_species
    phases = request.candidate_solid_phases
    species_index = {row.species_id: i for i, row in enumerate(species)}
    phase_index = {row.solid_species_id: j for j, row in enumerate(phases)}
    concentrations = [float(row.initial_concentration_mol_m3) for row in species]
    solids = [float(row.initial_solid_moles_per_solution_volume_mol_m3) for row in phases]
    stoich = [[0.0 for _ in phases] for _ in species]
    for j, phase in enumerate(phases):
        for species_id, coefficient in phase.precipitation_stoichiometry.items():
            stoich[species_index[species_id]][j] = float(coefficient)
    elements = sorted(
        set().union(
            *(set(row.elemental_composition) for row in species),
            *(set(phase.solid_elemental_composition) for phase in phases),
        )
    )

    def conserved_totals(aqueous, solid_amounts):
        totals = {
            element: math.fsum(
                row.elemental_composition.get(element, 0) * aqueous[i]
                for i, row in enumerate(species)
            )
            + math.fsum(
                phase.solid_elemental_composition.get(element, 0) * solid_amounts[j]
                for j, phase in enumerate(phases)
            )
            for element in elements
        }
        charge = math.fsum(row.charge_number * aqueous[i] for i, row in enumerate(species))
        return totals, charge

    initial_elements, initial_charge = conserved_totals(concentrations, solids)
    history = [{
        "time_s": 0.0,
        "aqueous_concentration_mol_m3": {row.species_id: concentrations[i] for i, row in enumerate(species)},
        "solid_inventory_mol_m3": {phase.solid_species_id: solids[j] for j, phase in enumerate(phases)},
        "cumulative_applied_extent_mol_m3": {phase.solid_species_id: 0.0 for phase in phases},
    }]
    cumulative_extents = [0.0 for _ in phases]
    max_element_residual = 0.0
    max_charge_residual = 0.0

    try:
        for interval in request.intervals:
            dt = interval.end_time_s - interval.start_time_s
            requested = [
                float(interval.phase_extent_rate_mol_m3_s[phase.solid_species_id]) * dt
                for phase in phases
            ]
            if any(not math.isfinite(value) for value in requested):
                raise ArithmeticError("requested kinetic extent exceeded finite numeric range")

            applied = [0.0 for _ in phases]
            # The reviewed operator split dissolves existing phase inventory first.
            for j, value in enumerate(requested):
                if value < 0:
                    applied[j] = max(value, -solids[j])
            dissolved_species = [
                concentrations[i] - math.fsum(stoich[i][j] * applied[j] for j in range(len(phases)))
                for i in range(len(species))
            ]
            if any(not math.isfinite(value) or value < 0 for value in dissolved_species):
                raise ArithmeticError("dissolution update produced an invalid aqueous inventory")
            dissolved_solids = [solids[j] + applied[j] for j in range(len(phases))]
            if any(not math.isfinite(value) or value < 0 for value in dissolved_solids):
                raise ArithmeticError("dissolution update exceeded solid inventory")

            precipitation_requested = [max(value, 0.0) for value in requested]
            demand = [
                math.fsum(stoich[i][j] * precipitation_requested[j] for j in range(len(phases)))
                for i in range(len(species))
            ]
            resource_factors = [
                dissolved_species[i] / demand[i]
                for i in range(len(species))
                if demand[i] > 0
            ]
            precipitation_factor = min(1.0, min(resource_factors, default=1.0))
            if not math.isfinite(precipitation_factor) or precipitation_factor < 0:
                raise ArithmeticError("precipitation resource factor is invalid")
            if precipitation_factor < 1.0:
                precipitation_factor = math.nextafter(precipitation_factor, 0.0)
            for j, value in enumerate(precipitation_requested):
                applied[j] += value * precipitation_factor
            final_concentrations = [
                dissolved_species[i] - math.fsum(stoich[i][j] * max(requested[j], 0.0) * precipitation_factor for j in range(len(phases)))
                for i in range(len(species))
            ]
            final_solids = [solids[j] + applied[j] for j in range(len(phases))]
            if any(not math.isfinite(value) or value < 0 for value in final_concentrations + final_solids):
                raise ArithmeticError("limited interval update produced negative or nonfinite inventories")

            element_totals, charge_total = conserved_totals(final_concentrations, final_solids)
            element_residuals = {key: element_totals[key] - initial_elements[key] for key in elements}
            element_limits = {
                key: request.absolute_balance_tolerance_mol_m3
                + request.relative_balance_tolerance * max(abs(element_totals[key]), abs(initial_elements[key]))
                for key in elements
            }
            charge_residual = charge_total - initial_charge
            charge_limit = request.absolute_balance_tolerance_mol_m3 + request.relative_balance_tolerance * max(
                abs(charge_total), abs(initial_charge)
            )
            if any(abs(element_residuals[key]) > element_limits[key] for key in elements) or abs(charge_residual) > charge_limit:
                raise ArithmeticError("element or charge balance exceeded declared tolerance")
            max_element_residual = max(max_element_residual, *(abs(value) for value in element_residuals.values()))
            max_charge_residual = max(max_charge_residual, abs(charge_residual))
            concentrations, solids = final_concentrations, final_solids
            cumulative_extents = [cumulative_extents[j] + applied[j] for j in range(len(phases))]
            history.append({
                "time_s": interval.end_time_s,
                "interval_id": interval.interval_id,
                "requested_extent_mol_m3": {phase.solid_species_id: requested[j] for j, phase in enumerate(phases)},
                "applied_extent_mol_m3": {phase.solid_species_id: applied[j] for j, phase in enumerate(phases)},
                "dissolution_extent_mol_m3": {phase.solid_species_id: min(applied[j], 0.0) for j, phase in enumerate(phases)},
                "precipitation_extent_mol_m3": {phase.solid_species_id: max(applied[j], 0.0) for j, phase in enumerate(phases)},
                "common_precipitation_resource_factor": precipitation_factor,
                "element_balance_residual_mol_m3": element_residuals,
                "charge_balance_residual_mol_charge_m3": charge_residual,
                "aqueous_concentration_mol_m3": {row.species_id: concentrations[i] for i, row in enumerate(species)},
                "solid_inventory_mol_m3": {phase.solid_species_id: solids[j] for j, phase in enumerate(phases)},
                "cumulative_applied_extent_mol_m3": {phase.solid_species_id: cumulative_extents[j] for j, phase in enumerate(phases)},
            })
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": str(error),
            "computed_prefix": history,
            "maximum_element_balance_residual_mol_m3": max_element_residual,
            "maximum_charge_balance_residual_mol_charge_m3": max_charge_residual,
        })
    return Calculation(values=base | {
        "species_ids": [row.species_id for row in species],
        "solid_phase_ids": [phase.solid_species_id for phase in phases],
        "final_aqueous_concentration_mol_m3": {row.species_id: concentrations[i] for i, row in enumerate(species)},
        "final_solid_inventory_mol_m3": {phase.solid_species_id: solids[j] for j, phase in enumerate(phases)},
        "history": history,
        "maximum_element_balance_residual_mol_m3": max_element_residual,
        "maximum_charge_balance_residual_mol_charge_m3": max_charge_residual,
        "precipitation_update_basis": "One common resource factor preserves caller relative rates across all simultaneous requested precipitation reactions after the explicitly reviewed dissolution-first split.",
        "scope": "Caller rates are applied, not predicted. No saturation/equilibrium solve, nucleation, rate-law fitting, activity iteration, spatial transport, corrosion rate or protective-scale effect is inferred.",
    })


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "chemistry.competitive_solid_kinetic_ledger",
            CompetingSolidKineticLedger,
            evaluate_competing_solid_kinetic_ledger,
            {
                "intervals[].start_time_s": "s",
                "intervals[].end_time_s": "s",
                "intervals[].temperature_K": "K",
                "intervals[].phase_extent_rate_mol_m3_s": "mol/m3/s",
                "history[].aqueous_concentration_mol_m3": "mol/m3",
                "history[].solid_inventory_mol_m3": "mol/m3",
            },
            (
                "Apply caller-supplied signed phase extent rates sequentially with explicit solid-inventory and common aqueous-reactant limits; verify elemental and charge ledgers.",
                "No saturation-derived rate, thermodynamic phase selection, speciation or kinetic law is inferred.",
            ),
            ("caller_rate_competitive_solid_mass_balance_ledger",),
            qualification="user_model",
        ),
        ModelSpec(
            "chemistry.competitive_solid_saturation_kinetics",
            CompetingSolidSaturationKinetics,
            evaluate_competing_solid_saturation_kinetics,
            {
                "temperature_K": "K",
                "intervals[].start_time_s": "s",
                "intervals[].end_time_s": "s",
                "intervals[].saturation_ratio_by_phase": "1",
                "phase_rate_laws[].rate_constant_reference_temperature_K": "K",
                "phase_rate_laws[].minimum_valid_temperature_K": "K",
                "phase_rate_laws[].maximum_valid_temperature_K": "K",
                "phase_rate_laws[].precipitation_activation_energy_J_mol": "J/mol",
                "phase_rate_laws[].dissolution_activation_energy_J_mol": "J/mol",
                "derived_rate_history[].phase_rate_diagnostics[].rate_law_temperature_K": "K",
                "derived_rate_history[].phase_rate_diagnostics[].effective_precipitation_rate_constant_mol_m3_s": "mol/m3/s",
                "derived_rate_history[].phase_rate_diagnostics[].effective_dissolution_rate_constant_mol_m3_s": "mol/m3/s",
                "derived_rate_history[].phase_rate_diagnostics[].signed_extent_rate_mol_m3_s": "mol/m3/s",
                "kinetic_ledger.history[].solid_inventory_mol_m3": "mol/m3",
            },
            (
                "Map caller-reviewed interval saturation ratios to per-phase precipitation or dissolution power-law rates, then apply the existing elemental/charge-conserving solid inventory limiter.",
                "Saturation ratios, phase identity, rate coefficients, reaction orders, units, temperature range and applicability remain caller supplied; chemistry and equilibrium are not inferred.",
            ),
            ("caller_competing_solid_saturation_rate_law", "arrhenius_kinetics"),
            qualification="user_model",
        ),
    ]
