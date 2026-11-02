"""Fixed-geometry transport followed by explicit local single-solid equilibrium.

This is a declared operator split, not a simultaneous general geochemical solver.
Each cell keeps its own immobile solid inventory and may use a digest-pinned
caller activity-coefficient callback at transport and phase-projection states.
"""

from collections.abc import Callable

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Positive, canonical_digest
from .restricted_transport import RestrictedTransportRequest, solve_restricted_transport
from .single_solid_equilibrium import SingleSolidEquilibrium, evaluate_single_solid_equilibrium
from .transport_potential import reconstruct_transport_potential


class EquilibriumReactiveTransport(Contract):
    campaign_id: str = Field(min_length=1)
    transport: RestrictedTransportRequest
    initial_cell_equilibria: tuple[SingleSolidEquilibrium, ...] = Field(min_length=2)
    uniform_temperature_K: Positive
    maximum_phase_projection_count: int = Field(default=20000, ge=2, le=200000)
    initial_equilibrium_projection_reviewed: bool
    instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed: bool
    fixed_geometry_and_immobile_solid_basis_reviewed: bool

    @model_validator(mode="after")
    def phase_grid(self):
        model = self.transport
        if model.cell_count * len(model.output_times_s) > self.maximum_phase_projection_count:
            raise ValueError("phase projection record budget exceeded; reduce cells or splitting boundaries")
        if len(self.initial_cell_equilibria) != model.cell_count:
            raise ValueError("one initial phase record is required per transport cell")
        if model.activity_provider_id is not None and not model.activity_chemical_potential_and_tracer_diffusivity_reviewed:
            raise ValueError("nonideal activity transport requires the declared chemical-potential review")
        if (
            model.migration_temperature_K is not None
            and model.migration_temperature_K != self.uniform_temperature_K
        ):
            raise ValueError("transport and phase temperatures must match")
        if len({row.equilibrium_id for row in self.initial_cell_equilibria}) != model.cell_count:
            raise ValueError("initial cell phase records require unique equilibrium IDs")
        if len({row.solid_species_id for row in self.initial_cell_equilibria}) != 1:
            raise ValueError("the split solver supports one common declared solid species")
        phase_signatures = set()
        for phase in self.initial_cell_equilibria:
            signature = phase.model_dump(
                mode="json", exclude={"equilibrium_id", "initial_solid_moles_per_solution_volume_mol_m3"}
            )
            for row in signature["aqueous_species"]:
                row.pop("initial_concentration_mol_m3")
                row.pop("activity_coefficient")
            phase_signatures.add(canonical_digest(signature))
        if len(phase_signatures) != 1:
            raise ValueError("cells must share one phase law, standard state and calibration basis")
        lookup = {name: index for index, name in enumerate(model.species_ids)}
        for cell, phase in enumerate(self.initial_cell_equilibria):
            if phase.temperature_K != self.uniform_temperature_K:
                raise ValueError("every phase record must use the common temperature")
            for row in phase.aqueous_species:
                if model.activity_provider_id is None and row.activity_coefficient != 1.0:
                    raise ValueError("nonideal phase activity coefficients require a declared provider")
                if row.species_id not in lookup:
                    raise ValueError("phase species is absent from transport species order")
                index = lookup[row.species_id]
                if row.initial_concentration_mol_m3 != model.initial_concentration_mol_m3[index][cell]:
                    raise ValueError("initial phase and transport concentrations must agree exactly")
                if model.charge_numbers is not None and row.charge_number != model.charge_numbers[index]:
                    raise ValueError("phase and transport species charges differ")
        return self


def solve_equilibrium_reactive_transport(
    request: EquilibriumReactiveTransport,
    reaction: Callable[[float, np.ndarray], np.ndarray],
    *,
    tip_surface_flux: Callable[[float, np.ndarray, float | None], np.ndarray] | None = None,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
) -> dict:
    base = dict(
        campaign_id=request.campaign_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        steps=[],
        initial_projection=None,
        activity_provider_id=request.transport.activity_provider_id,
        activity_configuration_sha256=request.transport.activity_configuration_sha256,
    )
    if not (
        request.initial_equilibrium_projection_reviewed
        and request.instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed
        and request.fixed_geometry_and_immobile_solid_basis_reviewed
    ):
        return base
    original = request.transport
    if original.activity_provider_id is not None:
        if activity_coefficients is None:
            return base | dict(reason="Declared nonideal activity provider callback is unavailable")
        if getattr(activity_coefficients, "configuration_sha256", None) != original.activity_configuration_sha256:
            raise ValueError("phase activity callback must carry the digest pinned by the transport request")
    elif activity_coefficients is not None:
        raise ValueError("an activity callback requires a provider identity and configuration digest")
    if not original.geometry_diffusion_reaction_basis_reviewed:
        return base
    if (
        original.cell_cross_section_m2 is not None
        and not original.variable_area_one_dimensional_reduction_reviewed
    ):
        return base
    if (
        original.mouth_concentration_history_mol_m3 is not None
        and not original.mouth_history_interpolation_reviewed
    ):
        return base
    if original.prescribed_potential_V is not None and not original.prescribed_field_migration_reviewed:
        return base
    if original.poisson_permittivity_F_m is not None and not original.poisson_boundary_and_charge_reviewed:
        return base
    if original.tip_surface_provider_id is not None and (
        tip_surface_flux is None or not original.tip_surface_flux_basis_reviewed
    ):
        return base
    if original.wall_surface_provider_id is not None and (
        wall_surface_flux is None or not original.wall_surface_flux_basis_reviewed
    ):
        return base
    count = original.cell_count
    lookup = {name: index for index, name in enumerate(original.species_ids)}
    widths = np.asarray(
        original.cell_widths_m if original.cell_widths_m is not None else (original.length_m / count,) * count
    )
    areas = (
        np.asarray(original.cell_cross_section_m2) / original.reference_cross_section_m2
        if original.cell_cross_section_m2 is not None
        else np.ones(count)
    )
    volumes = areas * widths
    if not np.isfinite(volumes).all() or np.any(volumes <= 0):
        return base | dict(status="out_of_scope", reason="Cell volume normalization exceeds numeric range")
    wall_area_over_reference_area = None
    if original.wall_area_per_volume_m2_m3 is not None:
        wall_area_over_reference_area = float(
            np.sum(np.asarray(original.wall_area_per_volume_m2_m3) * volumes)
        )
        if not np.isfinite(wall_area_over_reference_area) or wall_area_over_reference_area <= 0:
            return base | dict(status="out_of_scope", reason="Reactive wall area normalization exceeds numeric range")
    current = np.asarray(original.initial_concentration_mol_m3, dtype=float)
    initial_inventory = (current * volumes).sum(axis=1)
    solid = np.asarray(
        [phase.initial_solid_moles_per_solution_volume_mol_m3 for phase in request.initial_cell_equilibria],
        dtype=float,
    )
    accumulated_phase = np.zeros(len(lookup))
    accumulated_transport = np.zeros(len(lookup))
    ledger_keys = (
        "cumulative_mouth_inward_mol_m2",
        "cumulative_tip_inward_mol_m2",
        "cumulative_homogeneous_source_mol_m2",
        "cumulative_wall_inward_mol_m2",
    )
    separate_ledgers = {key: np.zeros(len(lookup)) for key in ledger_keys}
    ledger_histories = {key: [np.zeros(len(lookup)).tolist()] for key in ledger_keys}
    wall_cell_ledger = np.zeros((len(lookup), count))
    wall_cell_history = [wall_cell_ledger.tolist()]
    advection_velocity_history = []

    def mouth_at(time_s):
        if original.mouth_concentration_history_mol_m3 is None:
            return np.asarray(original.mouth_concentration_mol_m3, dtype=float)
        history = np.asarray(original.mouth_concentration_history_mol_m3, dtype=float)
        return np.asarray(
            [
                np.interp(time_s, original.output_times_s, history[:, species_index])
                for species_index in range(history.shape[1])
            ],
            dtype=float,
        )

    def project(concentrations, solid_inventory, stage_id, time_s):
        updated = concentrations.copy()
        updated_solid = solid_inventory.copy()
        phase_amounts = np.zeros(len(lookup))
        records = []
        phase_gamma = None
        if activity_coefficients is not None:
            complete_state = np.column_stack((mouth_at(time_s), concentrations))
            complete_state.setflags(write=False)
            try:
                phase_gamma = np.asarray(activity_coefficients(time_s, complete_state), dtype=float)
            except (ArithmeticError, OverflowError, ValueError, RuntimeError) as error:
                return None, None, None, [dict(status="out_of_scope", reason=f"Activity provider failed: {error}")]
            if (
                phase_gamma.shape != complete_state.shape
                or not np.isfinite(phase_gamma).all()
                or np.any(phase_gamma <= 0)
            ):
                return None, None, None, [dict(status="out_of_scope", reason="Activity provider must return finite positive species-by-mouth-and-cell coefficients")]
            phase_gamma = phase_gamma[:, 1:]
        for cell, template in enumerate(request.initial_cell_equilibria):
            payload = template.model_dump(mode="python")
            payload["equilibrium_id"] = f"{template.equilibrium_id}:{stage_id}"
            payload["initial_solid_moles_per_solution_volume_mol_m3"] = float(solid_inventory[cell])
            for row in payload["aqueous_species"]:
                row["initial_concentration_mol_m3"] = float(concentrations[lookup[row["species_id"]], cell])
                species_index = lookup[row["species_id"]]
                if phase_gamma is not None:
                    supplied_gamma = float(phase_gamma[species_index, cell])
                    if stage_id == "initial" and not np.isclose(
                        row["activity_coefficient"], supplied_gamma, rtol=1e-12, atol=0.0
                    ):
                        return None, None, None, [dict(status="out_of_scope", reason="Initial phase gamma differs from the pinned activity provider")]
                    row["activity_coefficient"] = supplied_gamma
            result = evaluate_single_solid_equilibrium(SingleSolidEquilibrium.model_validate(payload))
            records.append(result)
            if result["status"] != "computed":
                return None, None, None, records
            updated_solid[cell] = result["final_solid_moles_per_solution_volume_mol_m3"]
            extent = result["reaction_extent_mol_m3"]
            for row in template.aqueous_species:
                index = lookup[row.species_id]
                updated[index, cell] = result["final_aqueous_concentration_mol_m3"][row.species_id]
                phase_amounts[index] -= row.stoichiometric_moles_per_solid_mole * extent * volumes[cell]
        return updated, updated_solid, phase_amounts, records

    current, solid, phase_amounts, records = project(
        current, solid, "initial", original.output_times_s[0]
    )
    base["initial_projection"] = records
    if current is None:
        return base | dict(status="out_of_scope", reason="Initial phase projection is incomplete")
    accumulated_phase += phase_amounts
    fields = [current.tolist()]
    solid_history = [solid.tolist()]
    phase_history = [accumulated_phase.tolist()]
    transport_history = [accumulated_transport.tolist()]
    clocks = original.output_times_s

    def shifted(callback, offset):
        if callback is None:
            return None

        def evaluate(time, *arguments):
            return callback(time + offset, *arguments)

        digest = getattr(callback, "configuration_sha256", None)
        if digest is not None:
            evaluate.configuration_sha256 = digest
        return evaluate

    for index, (start, end) in enumerate(zip(clocks[:-1], clocks[1:], strict=True)):
        payload = original.model_dump(mode="python")
        payload.update(
            simulation_id=f"{original.simulation_id}:split:{index}",
            initial_concentration_mol_m3=tuple(tuple(float(value) for value in row) for row in current),
            output_times_s=(0.0, end - start),
        )
        if original.mouth_concentration_history_mol_m3 is not None:
            payload["mouth_concentration_mol_m3"] = original.mouth_concentration_history_mol_m3[index]
            payload["mouth_concentration_history_mol_m3"] = original.mouth_concentration_history_mol_m3[
                index : index + 2
            ]
        segment = RestrictedTransportRequest.model_validate(payload)
        result = solve_restricted_transport(
            segment,
            shifted(reaction, start),
            tip_surface_flux=shifted(tip_surface_flux, start),
            wall_surface_flux=shifted(wall_surface_flux, start),
            axial_advection_velocity=shifted(axial_advection_velocity, start),
            activity_coefficients=shifted(activity_coefficients, start),
        )
        record = dict(
            interval_index=index,
            start_s=start,
            end_s=end,
            transport_before_phase=result,
            phase_projection=None,
        )
        base["steps"].append(record)
        if result["status"] != "computed":
            return base | dict(status=result["status"], reason="Transport split interval did not complete")
        interval_velocity = result.get("axial_advection_velocity_history_m_s")
        if interval_velocity is not None:
            if not advection_velocity_history:
                advection_velocity_history.append(interval_velocity[0])
            advection_velocity_history.append(interval_velocity[-1])
        transported = np.asarray(result["concentration_mol_m3"][-1])
        current, solid, phase_amounts, records = project(transported, solid, f"step:{index}", end)
        record["phase_projection"] = records
        if current is None:
            return base | dict(status="out_of_scope", reason="Local phase projection did not complete")
        accumulated_phase += phase_amounts
        for key in ledger_keys:
            increment = np.asarray(result[key][-1])
            accumulated_transport += increment
            separate_ledgers[key] += increment
            ledger_histories[key].append(separate_ledgers[key].tolist())
        cell_increment = np.asarray(result["cumulative_wall_inward_by_cell_mol_m2"][-1])
        if cell_increment.shape != wall_cell_ledger.shape or not np.isfinite(cell_increment).all():
            return base | dict(
                status="out_of_scope", reason="Cell-resolved wall ledger does not align across split transport intervals"
            )
        wall_cell_ledger += cell_increment
        wall_cell_history.append(wall_cell_ledger.tolist())
        fields.append(current.tolist())
        solid_history.append(solid.tolist())
        phase_history.append(accumulated_phase.tolist())
        transport_history.append(accumulated_transport.tolist())
    inventory = (np.asarray(fields) * volumes).sum(axis=2)
    phase_history = np.asarray(phase_history)
    transport_history = np.asarray(transport_history)
    residual = inventory - initial_inventory - phase_history - transport_history
    scale = np.abs(inventory) + np.abs(initial_inventory) + np.abs(phase_history) + np.abs(transport_history)
    tolerance = original.inventory_absolute_tolerance_mol_m2 + original.inventory_relative_tolerance * scale
    if not (np.isfinite(residual).all() and np.isfinite(tolerance).all()):
        return base | dict(status="out_of_scope", reason="Split inventory balance exceeds numeric range")
    try:
        potential_fields = [reconstruct_transport_potential(original, np.asarray(frame)) for frame in fields]
    except (ValueError, ArithmeticError) as error:
        return base | dict(status="out_of_scope", reason=str(error))
    potentials = [frame.tolist() for frame in potential_fields] if potential_fields[0] is not None else None
    tip_ratio = (
        original.face_cross_section_m2[-1] / original.reference_cross_section_m2
        if original.face_cross_section_m2 is not None
        else 1.0
    )
    within = bool(np.all(np.abs(residual) <= tolerance))
    return base | dict(
        status="computed" if within else "out_of_scope",
        elapsed_time_s=list(clocks),
        species_ids=list(original.species_ids),
        concentration_after_phase_mol_m3=fields,
        concentration_mol_m3=fields,
        solution_potential_V=potentials,
        inventory_per_unit_area_mol_m2=inventory.tolist(),
        initial_aqueous_inventory_before_phase_mol_m2=initial_inventory.tolist(),
        phase_order="initial_projection_then_transport_then_local_equilibrium",
        output_state_basis="after_local_phase_projection_at_each_declared_boundary",
        tip_area_over_reference_area=tip_ratio,
        **ledger_histories,
        solid_moles_per_solution_volume_mol_m3=solid_history,
        cumulative_phase_aqueous_source_per_reference_area_mol_m2=phase_history.tolist(),
        cumulative_transport_source_per_reference_area_mol_m2=transport_history.tolist(),
        aqueous_inventory_balance_residual_mol_m2=residual.tolist(),
        inventory_balance_within_declared_tolerance=within,
        reference_cross_section_m2=original.reference_cross_section_m2,
        wall_area_over_reference_area=wall_area_over_reference_area,
        cumulative_wall_inward_by_cell_mol_m2=wall_cell_history,
        axial_advection_velocity_history_m_s=advection_velocity_history or None,
        basis="Initial phase projection, then transport followed by local ideal-activity single-solid equilibrium at each declared output-clock boundary. Fixed geometry and immobile solid; no simultaneous-speciation solve, splitting-error bound, precipitation kinetics, scale protection or failure probability.",
    )
