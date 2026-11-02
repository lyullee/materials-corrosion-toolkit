"""Fixed-geometry transport with cellwise caller-supplied multiphase kinetics."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest
from .multiphase_kinetic_ledger import (
    CompetingSolidKineticInterval,
    CompetingSolidKineticLedger,
    SolidSaturationRateLaw,
    _derive_solid_saturation_rate,
    KineticAqueousSpecies,
    KineticAqueousSpeciesDefinition,
    KineticSolidPhase,
    KineticSolidReaction,
    evaluate_competing_solid_kinetic_ledger,
    validate_neutral_solid_reaction_network,
)
from .restricted_transport import RestrictedTransportRequest, solve_restricted_transport
from .transport_potential import reconstruct_transport_potential


class CellwiseCompetingSolidRateInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    phase_extent_rate_mol_m3_s_by_cell: dict[str, tuple[float, ...]]

    @model_validator(mode="after")
    def finite_ordered_rates(self):
        if not math.isfinite(self.start_time_s) or not math.isfinite(self.end_time_s):
            raise ValueError("kinetic interval bounds must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("kinetic interval must have positive duration")
        if any(not math.isfinite(value) for values in self.phase_extent_rate_mol_m3_s_by_cell.values() for value in values):
            raise ValueError("caller-supplied cell rates must be finite")
        return self


class CompetingSolidKineticTransport(Contract):
    campaign_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    transport: RestrictedTransportRequest
    aqueous_species: tuple[KineticAqueousSpeciesDefinition, ...] = Field(min_length=1, max_length=64)
    candidate_solid_phases: tuple[KineticSolidReaction, ...] = Field(min_length=2, max_length=16)
    initial_solid_inventory_mol_m3_by_phase: dict[str, tuple[Nonnegative, ...]]
    kinetic_intervals: tuple[CellwiseCompetingSolidRateInterval, ...] = Field(default=(), max_length=5000)
    phase_rate_laws: tuple[SolidSaturationRateLaw, ...] = Field(default=(), max_length=16)
    saturation_ratio_provider_id: str | None = None
    saturation_ratio_provider_revision: str | None = None
    saturation_ratio_provider_configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    saturation_activity_standard_state: str | None = None
    saturation_ratio_and_standard_state_reviewed: bool = False
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    kinetic_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_parameter_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: Positive
    absolute_balance_tolerance_mol_m3: Positive = 1e-10
    relative_balance_tolerance: float = Field(default=1e-9, gt=0, le=0.01)
    phase_stoichiometry_and_solution_volume_reviewed: bool
    caller_rate_law_units_temperature_and_support_reviewed: bool
    transport_then_kinetics_split_order_reviewed: bool
    computational_use_authorized: bool
    maximum_kinetic_cell_updates: int = Field(default=100000, ge=1, le=500000)

    @model_validator(mode="after")
    def aligned_grid_and_network(self):
        transport = self.transport
        species_ids = tuple(row.species_id for row in self.aqueous_species)
        phase_ids = {row.solid_species_id for row in self.candidate_solid_phases}
        if len(set(species_ids)) != len(species_ids):
            raise ValueError("kinetic aqueous species IDs must be unique")
        validate_neutral_solid_reaction_network(self.aqueous_species, self.candidate_solid_phases)
        if species_ids != transport.species_ids:
            raise ValueError("kinetic species order must exactly match transport species order")
        if transport.charge_numbers is not None and tuple(row.charge_number for row in self.aqueous_species) != transport.charge_numbers:
            raise ValueError("kinetic species charges must match transport charges")
        if transport.migration_temperature_K is not None and transport.migration_temperature_K != self.temperature_K:
            raise ValueError("kinetic and transport migration temperatures must match")
        if set(self.initial_solid_inventory_mol_m3_by_phase) != phase_ids:
            raise ValueError("initial solid inventory must cover exactly the declared phases")
        for phase_id, cell_values in self.initial_solid_inventory_mol_m3_by_phase.items():
            if len(cell_values) != transport.cell_count:
                raise ValueError(f"initial solid inventory for {phase_id} must cover every transport cell")
        direct_rate_mode = bool(self.kinetic_intervals)
        saturation_rate_mode = bool(self.phase_rate_laws)
        if direct_rate_mode == saturation_rate_mode:
            raise ValueError("supply either explicit kinetic intervals or phase rate laws with a saturation provider")
        if direct_rate_mode:
            if any((self.saturation_ratio_provider_id, self.saturation_ratio_provider_revision,
                    self.saturation_ratio_provider_configuration_sha256)):
                raise ValueError("explicit-rate mode must not declare a saturation provider")
            interval_ids = [row.interval_id for row in self.kinetic_intervals]
            if len(self.kinetic_intervals) != len(transport.output_times_s) - 1 or len(set(interval_ids)) != len(interval_ids):
                raise ValueError("explicit kinetic intervals must uniquely match the transport clock")
            for index, interval in enumerate(self.kinetic_intervals):
                if interval.start_time_s != transport.output_times_s[index] or interval.end_time_s != transport.output_times_s[index + 1]:
                    raise ValueError("kinetic intervals must exactly match adjacent transport output-clock knots")
                if set(interval.phase_extent_rate_mol_m3_s_by_cell) != phase_ids:
                    raise ValueError("every interval must provide all and only the declared solid phases")
                if any(len(values) != transport.cell_count for values in interval.phase_extent_rate_mol_m3_s_by_cell.values()):
                    raise ValueError("each phase rate vector must contain one rate per transport cell")
        else:
            law_ids = [law.solid_species_id for law in self.phase_rate_laws]
            if len(set(law_ids)) != len(law_ids) or set(law_ids) != phase_ids:
                raise ValueError("saturation mode requires exactly one rate law for every declared phase")
            if not all((self.saturation_ratio_provider_id, self.saturation_ratio_provider_revision,
                        self.saturation_ratio_provider_configuration_sha256,
                        self.saturation_activity_standard_state)):
                raise ValueError("saturation mode requires provider identity, revision, configuration digest and activity standard state")
            if not self.saturation_ratio_and_standard_state_reviewed:
                raise ValueError("saturation output and standard-state mapping require explicit review")
        updates = transport.cell_count * (len(transport.output_times_s) - 1)
        if updates > self.maximum_kinetic_cell_updates:
            raise ValueError("kinetic cell-update budget exceeded; reduce cells or time intervals")
        if updates * (len(self.aqueous_species) + len(self.candidate_solid_phases) + 1) > 5_000_000:
            raise ValueError("kinetic species/phase record budget exceeded; reduce grid, intervals or network size")
        return self


def _shift_callback(callback, global_start_s: float):
    if callback is None:
        return None

    def shifted(local_time_s, *args):
        return callback(float(local_time_s) + global_start_s, *args)

    digest = getattr(callback, "configuration_sha256", None)
    if digest is not None:
        shifted.configuration_sha256 = digest
    return shifted


def solve_competing_solid_kinetic_transport(
    campaign: CompetingSolidKineticTransport,
    *,
    reaction: Callable[[float, np.ndarray], np.ndarray],
    tip_surface_flux: Callable[[float, np.ndarray, float | None], np.ndarray] | None = None,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
    saturation_ratios: Callable[[float, int, np.ndarray, dict[str, float]], dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Run transport, then apply a local multiphase rate ledger at each output knot.

    Rates may be supplied directly as constant interval values or derived from
    saturation ratios returned by a caller callback after interval transport,
    using that interval's right-knot aqueous state and the committed solid
    inventory. The resulting rate is applied as an explicit transport-then-
    kinetics operator split. No sub-interval saturation/rate update or
    simultaneous equilibrium is inferred.
    """
    original = campaign.transport
    campaign_digest = canonical_digest(campaign.model_dump(mode="json"))
    base: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "physical_scope_id": campaign.physical_scope_id,
        "status": "needs_data",
        "input_sha256": campaign_digest,
        "provider_id": campaign.provider_id,
        "provider_revision": campaign.provider_revision,
        "kinetic_configuration_sha256": campaign.kinetic_configuration_sha256,
        "kinetic_parameter_source_sha256": campaign.kinetic_parameter_source_sha256,
        "saturation_ratio_provider_id": campaign.saturation_ratio_provider_id,
        "saturation_ratio_provider_revision": campaign.saturation_ratio_provider_revision,
        "saturation_ratio_provider_configuration_sha256": campaign.saturation_ratio_provider_configuration_sha256,
        "saturation_activity_provider_lineage": (
            getattr(saturation_ratios, "activity_provider_lineage", None)
            if saturation_ratios is not None else None
        ),
        "saturation_activity_provider_lineage_sha256": (
            getattr(saturation_ratios, "activity_provider_lineage_sha256", None)
            if saturation_ratios is not None else None
        ),
        "aqueous_species_source_sha256": {row.species_id: row.source_sha256 for row in campaign.aqueous_species},
        "solid_phase_source_sha256": {row.solid_species_id: row.source_sha256 for row in campaign.candidate_solid_phases},
        "steps": [],
    }
    reviews = {
        "phase_stoichiometry_and_solution_volume_reviewed": campaign.phase_stoichiometry_and_solution_volume_reviewed,
        "caller_rate_law_units_temperature_and_support_reviewed": campaign.caller_rate_law_units_temperature_and_support_reviewed,
        "transport_then_kinetics_split_order_reviewed": campaign.transport_then_kinetics_split_order_reviewed,
        "computational_use_authorized": campaign.computational_use_authorized,
    }
    saturation_mode = not campaign.kinetic_intervals
    if saturation_mode:
        reviews["saturation_ratio_and_standard_state_reviewed"] = campaign.saturation_ratio_and_standard_state_reviewed
    if not all(reviews.values()):
        return base | {"missing_reviews": [name for name, accepted in reviews.items() if not accepted]}
    if original.activity_provider_id is not None:
        if activity_coefficients is None:
            return base | {"reason": "Declared transport activity provider callback is unavailable"}
        if getattr(activity_coefficients, "configuration_sha256", None) != original.activity_configuration_sha256:
            raise ValueError("activity callback configuration digest differs from the transport request")
    elif activity_coefficients is not None:
        raise ValueError("an activity callback requires a provider identity and configuration digest")
    if saturation_mode:
        if saturation_ratios is None:
            return base | {"reason": "Declared saturation-ratio provider callback is unavailable"}
        if getattr(saturation_ratios, "configuration_sha256", None) != campaign.saturation_ratio_provider_configuration_sha256:
            raise ValueError("saturation callback configuration digest differs from the campaign contract")
        callback_provider_id = getattr(saturation_ratios, "provider_id", campaign.saturation_ratio_provider_id)
        callback_provider_revision = getattr(saturation_ratios, "provider_revision", campaign.saturation_ratio_provider_revision)
        if callback_provider_id != campaign.saturation_ratio_provider_id:
            raise ValueError("saturation callback provider ID differs from the campaign contract")
        if callback_provider_revision != campaign.saturation_ratio_provider_revision:
            raise ValueError("saturation callback revision differs from the campaign contract")
        callback_temperature = getattr(saturation_ratios, "temperature_K", None)
        if callback_temperature != campaign.temperature_K:
            raise ValueError("saturation callback temperature differs from the kinetic campaign temperature")
        callback_standard_state = getattr(saturation_ratios, "activity_standard_state", None)
        if callback_standard_state != campaign.saturation_activity_standard_state:
            raise ValueError("saturation callback activity standard state differs from the campaign contract")
    elif saturation_ratios is not None:
        raise ValueError("a saturation callback requires saturation-derived kinetic mode")

    count = original.cell_count
    species_count = len(campaign.aqueous_species)
    phase_ids = [row.solid_species_id for row in campaign.candidate_solid_phases]
    phase_index = {phase_id: index for index, phase_id in enumerate(phase_ids)}
    widths = np.asarray(original.cell_widths_m or (original.length_m / count,) * count, dtype=float)
    area_ratio = (
        np.asarray(original.cell_cross_section_m2, dtype=float) / float(original.reference_cross_section_m2)
        if original.cell_cross_section_m2 is not None
        else np.ones(count)
    )
    cell_volume_per_reference_area = area_ratio * widths
    if not np.isfinite(cell_volume_per_reference_area).all() or np.any(cell_volume_per_reference_area <= 0):
        return base | {"status": "out_of_scope", "reason": "Cell-volume normalization exceeds numeric range"}

    current = np.asarray(original.initial_concentration_mol_m3, dtype=float)
    if current.shape != (species_count, count) or not np.isfinite(current).all():
        return base | {"status": "out_of_scope", "reason": "Initial aqueous field does not match the declared grid"}
    initial_inventory = current @ cell_volume_per_reference_area
    solid = np.asarray(
        [campaign.initial_solid_inventory_mol_m3_by_phase[phase_id] for phase_id in phase_ids], dtype=float
    )
    fields = [current.tolist()]
    solid_history = [{phase_id: solid[index].tolist() for index, phase_id in enumerate(phase_ids)}]
    cumulative_phase_source = np.zeros(species_count)
    cumulative_transport_source = np.zeros(species_count)
    phase_source_history = [cumulative_phase_source.tolist()]
    transport_source_history = [cumulative_transport_source.tolist()]
    ledger_keys = (
        "cumulative_mouth_inward_mol_m2",
        "cumulative_tip_inward_mol_m2",
        "cumulative_homogeneous_source_mol_m2",
        "cumulative_wall_inward_mol_m2",
    )
    transport_ledgers = {key: np.zeros(species_count) for key in ledger_keys}
    transport_ledger_history = {key: [np.zeros(species_count).tolist()] for key in ledger_keys}
    wall_cell_ledger = np.zeros((species_count, count))
    wall_cell_history = [wall_cell_ledger.tolist()]
    velocity_history = []

    def prefix_result(status: str, reason: str, extra: dict[str, Any] | None = None):
        payload = {
            "status": status,
            "reason": reason,
            "computed_time_s": list(original.output_times_s[: len(fields)]),
            "computed_step_count": len(fields) - 1,
            "concentration_computed_prefix_mol_m3": fields,
            "solid_inventory_computed_prefix_mol_m3_by_phase": solid_history,
            "cumulative_kinetic_source_computed_prefix_mol_m2": phase_source_history,
            "cumulative_transport_source_computed_prefix_mol_m2": transport_source_history,
            "transport_source_histories_computed_prefix": transport_ledger_history,
            "cumulative_wall_inward_by_cell_computed_prefix_mol_m2": wall_cell_history,
            "computed_steps": base["steps"][: len(fields) - 1],
            "partial_step": base["steps"][len(fields) - 1] if len(base["steps"]) >= len(fields) else None,
        }
        return base | payload | (extra or {})

    for interval_index, (start, end) in enumerate(zip(original.output_times_s[:-1], original.output_times_s[1:], strict=True)):
        if saturation_mode:
            interval_id = f"saturation-{interval_index:04d}"
            interval = None
        else:
            interval = campaign.kinetic_intervals[interval_index]
            interval_id = interval.interval_id
        transport_payload = original.model_dump(mode="python")
        transport_payload.update(
            simulation_id=f"{original.simulation_id}:multiphase:{interval_index}",
            initial_concentration_mol_m3=tuple(tuple(float(value) for value in row) for row in current),
            output_times_s=(0.0, float(end - start)),
        )
        if original.mouth_concentration_history_mol_m3 is not None:
            transport_payload["mouth_concentration_mol_m3"] = original.mouth_concentration_history_mol_m3[interval_index]
            transport_payload["mouth_concentration_history_mol_m3"] = original.mouth_concentration_history_mol_m3[
                interval_index : interval_index + 2
            ]
        segment = RestrictedTransportRequest.model_validate(transport_payload)
        transport_result = solve_restricted_transport(
            segment,
            _shift_callback(reaction, start),
            tip_surface_flux=_shift_callback(tip_surface_flux, start),
            wall_surface_flux=_shift_callback(wall_surface_flux, start),
            activity_coefficients=_shift_callback(activity_coefficients, start),
            axial_advection_velocity=_shift_callback(axial_advection_velocity, start),
        )
        step: dict[str, Any] = {
            "interval_id": interval_id,
            "start_time_s": start,
            "end_time_s": end,
            "transport": transport_result,
            "cellwise_kinetics": [],
        }
        base["steps"].append(step)
        if transport_result["status"] != "computed":
            return prefix_result(transport_result["status"], "Transport interval did not complete")

        interval_velocity = transport_result.get("axial_advection_velocity_history_m_s")
        before_kinetics = np.asarray(transport_result["concentration_mol_m3"][-1], dtype=float)
        if saturation_mode:
            law_by_phase = {law.solid_species_id: law for law in campaign.phase_rate_laws}
            rates_by_phase = {phase_id: [] for phase_id in phase_ids}
            saturation_by_cell = []
            try:
                for cell in range(count):
                    local_solid = {phase_id: float(solid[phase_index[phase_id], cell]) for phase_id in phase_ids}
                    raw_ratios = saturation_ratios(float(end), cell, before_kinetics[:, cell].copy(), local_solid)
                    if not isinstance(raw_ratios, dict) or set(raw_ratios) != set(phase_ids):
                        raise ValueError("saturation callback must return one ratio for every declared phase")
                    cell_ratios = {}
                    for phase_id in phase_ids:
                        raw_ratio = raw_ratios[phase_id]
                        if isinstance(raw_ratio, (bool, str, bytes)) or not isinstance(raw_ratio, (int, float, np.number)):
                            raise ValueError(f"saturation ratio for {phase_id} must be a numeric scalar")
                        ratio = float(raw_ratio)
                        diagnostics = _derive_solid_saturation_rate(
                            law_by_phase[phase_id], ratio, temperature_K=float(campaign.temperature_K)
                        )
                        rates_by_phase[phase_id].append(diagnostics["signed_extent_rate_mol_m3_s"])
                        cell_ratios[phase_id] = diagnostics
                    saturation_by_cell.append(cell_ratios)
            except Exception as error:
                return prefix_result("out_of_scope", f"Saturation-rate provider failed after transport: {error}",
                                     {"failed_interval_index": interval_index,
                                      "computed_saturation_prefix_by_cell": saturation_by_cell})
            interval = CellwiseCompetingSolidRateInterval(
                interval_id=interval_id,
                start_time_s=float(start),
                end_time_s=float(end),
                phase_extent_rate_mol_m3_s_by_cell={key: tuple(value) for key, value in rates_by_phase.items()},
            )
            step["saturation_rate_diagnostics_by_cell"] = saturation_by_cell
        updated_concentrations = before_kinetics.copy()
        updated_solid = solid.copy()
        interval_species_source = np.zeros(species_count)
        for cell in range(count):
            aqueous_rows = tuple(
                KineticAqueousSpecies(
                    **row.model_dump(mode="python"),
                    initial_concentration_mol_m3=float(before_kinetics[species_index, cell]),
                )
                for species_index, row in enumerate(campaign.aqueous_species)
            )
            phase_rows = tuple(
                KineticSolidPhase(
                    **phase.model_dump(mode="python"),
                    initial_solid_moles_per_solution_volume_mol_m3=float(solid[phase_index[phase.solid_species_id], cell]),
                )
                for phase in campaign.candidate_solid_phases
            )
            cell_interval = CompetingSolidKineticInterval(
                interval_id=interval.interval_id,
                start_time_s=0.0,
                end_time_s=float(end - start),
                phase_extent_rate_mol_m3_s={
                    phase_id: float(interval.phase_extent_rate_mol_m3_s_by_cell[phase_id][cell])
                    for phase_id in phase_ids
                },
            )
            ledger = CompetingSolidKineticLedger(
                assessment_id=f"{campaign.campaign_id}:{interval.interval_id}:cell:{cell}",
                physical_scope_id=f"{campaign.physical_scope_id}:cell:{cell}",
                provider_id=campaign.provider_id,
                provider_revision=campaign.provider_revision,
                kinetic_configuration_sha256=campaign.kinetic_configuration_sha256,
                temperature_K=campaign.temperature_K,
                kinetic_parameter_source_sha256=campaign.kinetic_parameter_source_sha256,
                aqueous_species=aqueous_rows,
                candidate_solid_phases=phase_rows,
                intervals=(cell_interval,),
                absolute_balance_tolerance_mol_m3=campaign.absolute_balance_tolerance_mol_m3,
                relative_balance_tolerance=campaign.relative_balance_tolerance,
                phase_stoichiometry_and_solution_volume_reviewed=campaign.phase_stoichiometry_and_solution_volume_reviewed,
                caller_rate_law_units_temperature_and_support_reviewed=campaign.caller_rate_law_units_temperature_and_support_reviewed,
                dissolution_then_precipitation_split_order_reviewed=campaign.transport_then_kinetics_split_order_reviewed,
                computational_use_authorized=campaign.computational_use_authorized,
            )
            calculation = evaluate_competing_solid_kinetic_ledger(ledger)
            if calculation.status != "computed":
                step["failed_cell"] = cell
                step["failed_kinetic_calculation"] = calculation.model_dump(mode="json")
                return prefix_result(
                    calculation.status,
                    "Cellwise kinetic ledger did not complete; earlier cells in this interval are retained as an uncommitted prefix",
                    {
                        "failed_cell": cell,
                        "failed_interval_transported_concentration_mol_m3": before_kinetics.tolist(),
                    },
                )
            values = calculation.values
            step["cellwise_kinetics"].append(values)
            for species_index, species in enumerate(campaign.aqueous_species):
                updated_concentrations[species_index, cell] = values["final_aqueous_concentration_mol_m3"][species.species_id]
                interval_species_source[species_index] += (
                    updated_concentrations[species_index, cell] - before_kinetics[species_index, cell]
                ) * cell_volume_per_reference_area[cell]
            for phase_id in phase_ids:
                updated_solid[phase_index[phase_id], cell] = values["final_solid_inventory_mol_m3"][phase_id]

        next_transport_ledgers = {}
        next_cumulative_transport_source = cumulative_transport_source.copy()
        for key in ledger_keys:
            increment = np.asarray(transport_result[key][-1], dtype=float)
            if increment.shape != (species_count,) or not np.isfinite(increment).all():
                return prefix_result(
                    "out_of_scope",
                    f"Transport ledger {key} is invalid",
                    {"interval_kinetic_results": step["cellwise_kinetics"]},
                )
            next_transport_ledgers[key] = transport_ledgers[key] + increment
            next_cumulative_transport_source += increment
        wall_increment = np.asarray(transport_result["cumulative_wall_inward_by_cell_mol_m2"][-1], dtype=float)
        if wall_increment.shape != wall_cell_ledger.shape or not np.isfinite(wall_increment).all():
            return prefix_result(
                "out_of_scope",
                "Cellwise wall ledger does not match the transport grid",
                {"interval_kinetic_results": step["cellwise_kinetics"]},
            )

        # Commit only after every cell and transport ledger for this interval succeeds.
        current = updated_concentrations
        solid = updated_solid
        cumulative_phase_source += interval_species_source
        for key in ledger_keys:
            transport_ledgers[key] = next_transport_ledgers[key]
            transport_ledger_history[key].append(transport_ledgers[key].tolist())
        cumulative_transport_source = next_cumulative_transport_source
        wall_cell_ledger += wall_increment
        fields.append(current.tolist())
        solid_history.append({phase_id: solid[index].tolist() for index, phase_id in enumerate(phase_ids)})
        phase_source_history.append(cumulative_phase_source.tolist())
        wall_cell_history.append(wall_cell_ledger.tolist())
        transport_source_history.append(cumulative_transport_source.tolist())
        if interval_velocity is not None:
            if not velocity_history:
                velocity_history.append(interval_velocity[0])
            velocity_history.append(interval_velocity[-1])

    inventory = np.asarray(fields) @ cell_volume_per_reference_area
    phase_source = np.asarray(phase_source_history)
    transport_source = np.asarray(transport_source_history)
    residual = inventory - initial_inventory[None, :] - phase_source - transport_source
    scale = np.abs(inventory) + np.abs(initial_inventory[None, :]) + np.abs(phase_source) + np.abs(transport_source)
    tolerance = original.inventory_absolute_tolerance_mol_m2 + original.inventory_relative_tolerance * scale
    if not np.isfinite(residual).all() or not np.isfinite(tolerance).all():
        return prefix_result("out_of_scope", "Campaign inventory balance exceeds numeric range")
    try:
        potential_fields = [reconstruct_transport_potential(original, np.asarray(frame)) for frame in fields]
    except (ValueError, ArithmeticError) as error:
        return prefix_result("out_of_scope", str(error))
    potentials = [frame.tolist() for frame in potential_fields] if potential_fields[0] is not None else None
    within = bool(np.all(np.abs(residual) <= tolerance))
    return base | {
        "status": "computed" if within else "out_of_scope",
        "physical_scope_id": campaign.physical_scope_id,
        "elapsed_time_s": list(original.output_times_s),
        "species_ids": list(original.species_ids),
        "solid_phase_ids": phase_ids,
        "concentration_mol_m3": fields,
        "concentration_after_kinetics_mol_m3": fields,
        "solid_inventory_mol_m3_by_phase": solid_history,
        "cumulative_kinetic_aqueous_source_per_reference_area_mol_m2": phase_source.tolist(),
        "cumulative_transport_source_per_reference_area_mol_m2": transport_source.tolist(),
        "aqueous_inventory_per_reference_area_mol_m2": inventory.tolist(),
        "initial_aqueous_inventory_per_reference_area_mol_m2": initial_inventory.tolist(),
        "aqueous_inventory_balance_residual_mol_m2": residual.tolist(),
        "inventory_balance_within_declared_tolerance": within,
        "solution_potential_V": potentials,
        "reference_cross_section_m2": original.reference_cross_section_m2,
        "cumulative_wall_inward_by_cell_mol_m2": wall_cell_history,
        "transport_source_histories": {key: value for key, value in transport_ledger_history.items()},
        "axial_advection_velocity_history_m_s": velocity_history or None,
        "operator_split_basis": "Each fixed-geometry transport interval is solved, then phase rates are applied independently in each cell. In saturation mode, the callback is evaluated from the post-transport right-knot aqueous state and current solid inventory; the endpoint-derived rate is applied over the just-completed interval duration.",
        "scope": "Saturation mode uses caller-provided saturation outputs and phase-specific power-law parameters; it does not calculate chemical speciation or equilibrium, infer nucleation, evolve protective morphology, move boundaries, or solve simultaneous flow/transport/kinetics. Qualification and failure probability are not inferred.",
    }
