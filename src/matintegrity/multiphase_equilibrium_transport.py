"""Fixed-geometry transport with cell-local Davies, SIT or B-dot solid projections."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Positive, canonical_digest
from .models.competitive_solid_bdot_iteration import (
    CompetitiveSolidBdotIteration,
    competitive_solid_bdot_self_consistent_equilibrium,
)
from .models.competitive_solid_activity_iteration import (
    CompetitiveSolidDaviesIteration,
    competitive_solid_davies_self_consistent_equilibrium,
)
from .models.competitive_solid_sit_iteration import (
    CompetitiveSolidSITIteration,
    competitive_solid_sit_self_consistent_equilibrium,
)
from .restricted_transport import RestrictedTransportRequest, solve_restricted_transport
from .transport_potential import reconstruct_transport_potential


class CompetitiveSolidEquilibriumTransport(Contract):
    """Operator-split 1D transport and local nonideal solid equilibria.

    Each output interval is transported at fixed geometry, then every cell is
    projected to its caller-defined competitive neutral-solid equilibrium.
    """

    campaign_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    transport: RestrictedTransportRequest
    initial_cell_equilibria: tuple[CompetitiveSolidDaviesIteration | CompetitiveSolidSITIteration | CompetitiveSolidBdotIteration, ...] = Field(min_length=2)
    uniform_temperature_K: Positive
    transport_activity_adapter_configuration_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
        description="Reviewed transport callback configuration digest, including adapter settings; phase parameter digest remains independently preserved in each phase request.",
    )
    maximum_phase_projection_count: int = Field(default=20000, ge=2, le=200000)
    initial_equilibrium_projection_reviewed: bool
    instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed: bool
    fixed_geometry_and_immobile_solid_basis_reviewed: bool
    transport_activity_to_phase_davies_mapping_reviewed: bool = Field(
        description="Legacy field name; review that transport activity and the selected Davies, SIT or B-dot phase model use compatible standard states and parameter bases."
    )

    @model_validator(mode="after")
    def aligned_transport_and_phase_cells(self):
        model = self.transport
        if model.cell_count != len(self.initial_cell_equilibria):
            raise ValueError("one initial competitive-solid equilibrium is required per transport cell")
        if model.cell_count * len(model.output_times_s) > self.maximum_phase_projection_count:
            raise ValueError("phase projection budget exceeded; reduce cells or output-clock boundaries")
        phase_count = len(self.initial_cell_equilibria[0].equilibrium.candidate_solid_phases)
        if model.cell_count * len(model.output_times_s) * (len(model.species_ids) + phase_count) > 5_000_000:
            raise ValueError("phase projection species/phase record budget exceeded")
        if model.charge_numbers is None:
            raise ValueError("multiphase activity/phase transport requires declared charges for the complete species order")
        templates = self.initial_cell_equilibria
        if len({row.equilibrium.equilibrium_id for row in templates}) != model.cell_count:
            raise ValueError("each cell equilibrium requires a unique equilibrium ID")
        phase_ids = tuple(row.solid_species_id for row in templates[0].equilibrium.candidate_solid_phases)
        if any(tuple(row.solid_species_id for row in item.equilibrium.candidate_solid_phases) != phase_ids for item in templates):
            raise ValueError("all cells must use the same ordered competing solid phase set")
        lookup = {name: index for index, name in enumerate(model.species_ids)}
        signatures = set()
        for cell, item in enumerate(templates):
            phase = item.equilibrium
            phase_species_ids = {row.species_id for row in phase.aqueous_species}
            if phase_species_ids != set(model.species_ids):
                raise ValueError("every transport species must occur in the complete phase/charge inventory")
            if phase.temperature_K != self.uniform_temperature_K:
                raise ValueError("all phase equilibrium temperatures must match the transport temperature")
            for species in phase.aqueous_species:
                if species.species_id not in lookup:
                    raise ValueError("every phase species must occur in transport species order")
                index = lookup[species.species_id]
                if species.initial_concentration_mol_m3 != model.initial_concentration_mol_m3[index][cell]:
                    raise ValueError("initial transport and phase concentrations must match exactly")
                if model.charge_numbers is not None and species.charge_number != model.charge_numbers[index]:
                    raise ValueError("phase and transport charge numbers differ")
                if model.activity_provider_id is None and species.activity_coefficient != 1.0:
                    raise ValueError("nonideal transport activity requires an explicit activity provider")
            payload = item.model_dump(mode="json")
            eq = payload["equilibrium"]
            eq.pop("equilibrium_id")
            for species in eq["aqueous_species"]:
                species.pop("initial_concentration_mol_m3")
                species.pop("activity_coefficient")
            for solid in eq["candidate_solid_phases"]:
                solid.pop("initial_solid_moles_per_solution_volume_mol_m3")
            signatures.add(canonical_digest(payload))
        if len(signatures) != 1:
            raise ValueError("cells must share phase laws, Ksp data, provider configuration and review basis")
        phase_template = templates[0]
        if model.activity_provider_id is None:
            raise ValueError("transport must declare an activity provider aligned with the phase activity model")
        if isinstance(phase_template, CompetitiveSolidDaviesIteration):
            phase_provider_id = phase_template.davies_A_provider_id
            phase_configuration_sha256 = phase_template.davies_A_configuration_digest
            phase_activity_model = "Davies"
        elif isinstance(phase_template, CompetitiveSolidSITIteration):
            phase_provider_id = phase_template.provider_id
            phase_configuration_sha256 = phase_template.configuration_sha256
            phase_activity_model = "SIT"
        else:
            phase_provider_id = phase_template.provider_id
            phase_configuration_sha256 = phase_template.configuration_sha256
            phase_activity_model = "B-dot"
        if (
            model.activity_provider_id != phase_provider_id
            or model.activity_configuration_sha256 != (
                self.transport_activity_adapter_configuration_sha256
                or phase_configuration_sha256
            )
        ):
            raise ValueError(f"transport activity provider identity and digest must match the reviewed {phase_activity_model} transport configuration")
        if not self.transport_activity_to_phase_davies_mapping_reviewed:
            raise ValueError("mapping the transport activity callback to the phase activity model requires explicit review")
        if model.migration_temperature_K is not None and model.migration_temperature_K != self.uniform_temperature_K:
            raise ValueError("transport migration and phase temperatures must match")
        if model.activity_provider_id is not None and not model.activity_chemical_potential_and_tracer_diffusivity_reviewed:
            raise ValueError("nonideal transport activity requires its chemical-potential review")
        return self


def bind_competitive_solid_transport_activity(
    request: CompetitiveSolidEquilibriumTransport,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray],
) -> CompetitiveSolidEquilibriumTransport:
    """Return a revalidated request pinned to a reviewed runtime adapter.

    The caller retains responsibility for standard-state and physical mapping.
    This helper does not execute the callback or an equilibrium calculation.
    """
    provider = getattr(activity_coefficients, "provider_id", None)
    digest = getattr(activity_coefficients, "configuration_sha256", None)
    if provider != request.transport.activity_provider_id:
        raise ValueError("activity adapter provider differs from the phase transport provider")
    if not isinstance(digest, str):
        raise ValueError("activity adapter must expose a configuration digest")
    phase = request.initial_cell_equilibria[0]
    phase_digest = (
        phase.davies_A_configuration_digest
        if isinstance(phase, CompetitiveSolidDaviesIteration)
        else phase.configuration_sha256
    )
    if getattr(activity_coefficients, "phase_parameter_configuration_sha256", None) != phase_digest:
        raise ValueError("activity adapter must identify the unchanged phase parameter configuration")
    payload = request.model_dump(mode="python")
    payload["transport"]["activity_configuration_sha256"] = digest
    payload["transport_activity_adapter_configuration_sha256"] = digest
    return CompetitiveSolidEquilibriumTransport.model_validate(payload, strict=True)


def solve_competitive_solid_equilibrium_transport(
    request: CompetitiveSolidEquilibriumTransport,
    reaction: Callable[[float, np.ndarray], np.ndarray],
    *,
    tip_surface_flux: Callable[[float, np.ndarray, float | None], np.ndarray] | None = None,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
) -> dict:
    """Transport between output knots, then update all declared solid phases per cell."""
    original = request.transport
    count = original.cell_count
    species_count = len(original.species_ids)
    phase_ids = [row.solid_species_id for row in request.initial_cell_equilibria[0].equilibrium.candidate_solid_phases]
    base = {
        "campaign_id": request.campaign_id,
        "physical_scope_id": request.physical_scope_id,
        "status": "needs_data",
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "activity_provider_id": original.activity_provider_id,
        "activity_configuration_sha256": original.activity_configuration_sha256,
        "transport_activity_adapter_configuration_sha256": request.transport_activity_adapter_configuration_sha256,
        "phase_parameter_configuration_sha256": (
            request.initial_cell_equilibria[0].davies_A_configuration_digest
            if isinstance(request.initial_cell_equilibria[0], CompetitiveSolidDaviesIteration)
            else request.initial_cell_equilibria[0].configuration_sha256
        ),
        "phase_ids": phase_ids,
        "steps": [],
        "initial_phase_projection": None,
        "phase_activity_model": (
            "Davies" if isinstance(request.initial_cell_equilibria[0], CompetitiveSolidDaviesIteration)
            else "SIT" if isinstance(request.initial_cell_equilibria[0], CompetitiveSolidSITIteration)
            else "B-dot"
        ),
    }
    if not (
        request.initial_equilibrium_projection_reviewed
        and request.instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed
        and request.fixed_geometry_and_immobile_solid_basis_reviewed
        and request.transport_activity_to_phase_davies_mapping_reviewed
    ):
        return base
    if original.activity_provider_id is not None:
        if activity_coefficients is None:
            return base | {"reason": "Declared transport activity callback is unavailable"}
        if getattr(activity_coefficients, "configuration_sha256", None) != original.activity_configuration_sha256:
            raise ValueError("transport activity callback digest does not match the request")
        if getattr(activity_coefficients, "provider_id", None) != original.activity_provider_id:
            raise ValueError("transport activity callback provider does not match the request")
        if request.transport_activity_adapter_configuration_sha256 is not None:
            phase = request.initial_cell_equilibria[0]
            expected = {
                "phase_parameter_configuration_sha256": base["phase_parameter_configuration_sha256"],
                "species_ids": tuple(original.species_ids),
                "temperature_K": float(request.uniform_temperature_K),
            }
            if not isinstance(phase, CompetitiveSolidDaviesIteration):
                expected["provider_revision"] = phase.provider_revision
                expected["water_mass_per_solution_volume_kg_L"] = phase.water_mass_per_solution_volume_kg_L
                expected["debye_huckel_A_at_temperature"] = phase.debye_huckel_A_at_temperature
                expected["record_sha256"] = (
                    phase.record_sha256 if isinstance(phase, CompetitiveSolidSITIteration)
                    else phase.parameter_record_sha256
                )
                if isinstance(phase, CompetitiveSolidSITIteration):
                    expected["sit_interaction_parameter_sha256"] = canonical_digest(
                        [row.model_dump(mode="json") for row in phase.interactions]
                    )
                else:
                    expected["debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom"] = phase.debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom
                    expected["parameter_sha256"] = canonical_digest(
                        [row.model_dump(mode="json") for row in phase.species_parameters]
                    )
            for name, value in expected.items():
                if getattr(activity_coefficients, name, None) != value:
                    raise ValueError(f"transport activity callback {name} differs from the phase mapping")
    elif activity_coefficients is not None:
        raise ValueError("an activity callback requires a provider identity and digest")
    if not original.geometry_diffusion_reaction_basis_reviewed:
        return base
    if original.cell_cross_section_m2 is not None and not original.variable_area_one_dimensional_reduction_reviewed:
        return base
    if original.mouth_concentration_history_mol_m3 is not None and not original.mouth_history_interpolation_reviewed:
        return base
    if original.prescribed_potential_V is not None and not original.prescribed_field_migration_reviewed:
        return base
    if original.poisson_permittivity_F_m is not None and not original.poisson_boundary_and_charge_reviewed:
        return base
    if original.tip_surface_provider_id is not None and (tip_surface_flux is None or not original.tip_surface_flux_basis_reviewed):
        return base
    if original.wall_surface_provider_id is not None and (wall_surface_flux is None or not original.wall_surface_flux_basis_reviewed):
        return base

    lookup = {name: index for index, name in enumerate(original.species_ids)}
    widths = np.asarray(original.cell_widths_m or (original.length_m / count,) * count, dtype=float)
    areas = (
        np.asarray(original.cell_cross_section_m2, dtype=float) / original.reference_cross_section_m2
        if original.cell_cross_section_m2 is not None else np.ones(count)
    )
    volumes = areas * widths
    if not np.isfinite(volumes).all() or np.any(volumes <= 0):
        return base | {"status": "out_of_scope", "reason": "cell-volume normalization is nonfinite or nonpositive"}
    current = np.asarray(original.initial_concentration_mol_m3, dtype=float)
    initial_inventory = (current * volumes).sum(axis=1)
    solid = np.asarray([
        [phase.initial_solid_moles_per_solution_volume_mol_m3 for phase in cell.equilibrium.candidate_solid_phases]
        for cell in request.initial_cell_equilibria
    ], dtype=float)
    phase_source = np.zeros(species_count)
    transport_source = np.zeros(species_count)
    ledger_keys = (
        "cumulative_mouth_inward_mol_m2", "cumulative_tip_inward_mol_m2",
        "cumulative_homogeneous_source_mol_m2", "cumulative_wall_inward_mol_m2",
    )
    ledger_total = {key: np.zeros(species_count) for key in ledger_keys}
    ledger_history = {key: [np.zeros(species_count).tolist()] for key in ledger_keys}
    wall_cell_total = np.zeros((species_count, count))
    wall_cell_history = [wall_cell_total.tolist()]
    velocity_history = []

    def prefix_result(status: str, reason: str, extra: dict | None = None):
        payload = {
            "status": status,
            "reason": reason,
            "computed_time_s": list(original.output_times_s[:len(fields)]),
            "computed_step_count": len(fields) - 1,
            "concentration_computed_prefix_mol_m3": fields,
            "solid_inventory_computed_prefix_mol_m3_by_cell": solid_history,
            "cumulative_phase_source_computed_prefix_mol_m2": phase_history,
            "cumulative_transport_source_computed_prefix_mol_m2": transport_history,
            "transport_source_histories_computed_prefix": ledger_history,
            "cumulative_wall_inward_by_cell_computed_prefix_mol_m2": wall_cell_history,
            "computed_steps": base["steps"][:len(fields) - 1],
            "partial_step": base["steps"][len(fields) - 1] if len(base["steps"]) >= len(fields) else None,
        }
        return base | payload | (extra or {})

    def project(concentration, solid_inventory, stage):
        new_concentration = concentration.copy()
        new_solid = solid_inventory.copy()
        source = np.zeros(species_count)
        records = []
        for cell, template in enumerate(request.initial_cell_equilibria):
            payload = template.model_dump(mode="python")
            payload["equilibrium"]["equilibrium_id"] = f"{template.equilibrium.equilibrium_id}:{stage}"
            for row in payload["equilibrium"]["aqueous_species"]:
                row["initial_concentration_mol_m3"] = float(concentration[lookup[row["species_id"]], cell])
            for j, phase in enumerate(payload["equilibrium"]["candidate_solid_phases"]):
                phase["initial_solid_moles_per_solution_volume_mol_m3"] = float(solid_inventory[cell, j])
            if isinstance(template, CompetitiveSolidDaviesIteration):
                local = CompetitiveSolidDaviesIteration.model_validate(payload)
                result = competitive_solid_davies_self_consistent_equilibrium(local)
            elif isinstance(template, CompetitiveSolidSITIteration):
                local = CompetitiveSolidSITIteration.model_validate(payload)
                result = competitive_solid_sit_self_consistent_equilibrium(local)
            else:
                local = CompetitiveSolidBdotIteration.model_validate(payload)
                result = competitive_solid_bdot_self_consistent_equilibrium(local)
            records.append(result.model_dump(mode="json"))
            if result.status != "computed":
                return None, None, None, records
            for row in template.equilibrium.aqueous_species:
                new_concentration[lookup[row.species_id], cell] = result.values["final_aqueous_concentration_mol_m3"][row.species_id]
            phases = {row["solid_species_id"]: row for row in result.values["solid_phase_results"]}
            for j, phase_template in enumerate(template.equilibrium.candidate_solid_phases):
                solved_phase = phases[phase_template.solid_species_id]
                extent = solved_phase["reaction_extent_mol_m3"]
                new_solid[cell, j] = solved_phase["final_solid_moles_per_solution_volume_mol_m3"]
                for species_id, coefficient in phase_template.precipitation_stoichiometry.items():
                    source[lookup[species_id]] -= coefficient * extent * volumes[cell]
        return new_concentration, new_solid, source, records

    current, solid, initial_source, records = project(current, solid, "initial")
    base["initial_phase_projection"] = records
    if current is None:
        return base | {"status": "out_of_scope", "reason": "initial competitive phase projection did not complete"}
    phase_source += initial_source
    fields = [current.tolist()]
    solid_history = [solid.tolist()]
    phase_history = [phase_source.tolist()]
    transport_history = [transport_source.tolist()]
    potential_history = []
    try:
        initial_potential = reconstruct_transport_potential(original, current)
        if initial_potential is not None:
            potential_history.append(initial_potential.tolist())
    except (ValueError, ArithmeticError) as error:
        return base | {"status": "out_of_scope", "reason": str(error)}

    def shifted(callback, offset):
        if callback is None:
            return None
        def evaluate(time, *args):
            return callback(time + offset, *args)
        digest = getattr(callback, "configuration_sha256", None)
        if digest is not None:
            evaluate.configuration_sha256 = digest
        return evaluate

    for index, (start, end) in enumerate(zip(original.output_times_s[:-1], original.output_times_s[1:], strict=True)):
        payload = original.model_dump(mode="python")
        payload.update(
            simulation_id=f"{original.simulation_id}:competitive-solid-split:{index}",
            initial_concentration_mol_m3=tuple(tuple(float(value) for value in row) for row in current),
            output_times_s=(0.0, end - start),
        )
        if original.mouth_concentration_history_mol_m3 is not None:
            payload["mouth_concentration_mol_m3"] = original.mouth_concentration_history_mol_m3[index]
            payload["mouth_concentration_history_mol_m3"] = original.mouth_concentration_history_mol_m3[index:index + 2]
        segment = RestrictedTransportRequest.model_validate(payload)
        solved_transport = solve_restricted_transport(
            segment,
            shifted(reaction, start),
            tip_surface_flux=shifted(tip_surface_flux, start),
            wall_surface_flux=shifted(wall_surface_flux, start),
            axial_advection_velocity=shifted(axial_advection_velocity, start),
            activity_coefficients=shifted(activity_coefficients, start),
        )
        step = {"interval_index": index, "start_s": start, "end_s": end, "transport": solved_transport, "phase_projection": None}
        base["steps"].append(step)
        if solved_transport["status"] != "computed":
            return prefix_result(solved_transport["status"], "transport interval did not complete")
        interval_velocity = solved_transport.get("axial_advection_velocity_history_m_s")
        if interval_velocity is not None:
            if not velocity_history:
                velocity_history.append(interval_velocity[0])
            velocity_history.append(interval_velocity[-1])
        transported = np.asarray(solved_transport["concentration_mol_m3"][-1], dtype=float)
        projected, projected_solid, increment, records = project(transported, solid, f"step:{index}")
        step["phase_projection"] = records
        if projected is None:
            return prefix_result("out_of_scope", "local competitive phase projection did not complete")
        next_ledgers = {}
        next_transport_source = transport_source.copy()
        for key in ledger_keys:
            value = np.asarray(solved_transport[key][-1], dtype=float)
            if value.shape != (species_count,) or not np.isfinite(value).all():
                return prefix_result("out_of_scope", f"transport source ledger {key} is invalid")
            next_ledgers[key] = ledger_total[key] + value
            next_transport_source += value
        wall_increment = np.zeros_like(wall_cell_total)
        if "cumulative_wall_inward_by_cell_mol_m2" in solved_transport:
            wall_increment = np.asarray(solved_transport["cumulative_wall_inward_by_cell_mol_m2"][-1], dtype=float)
            if wall_increment.shape != wall_cell_total.shape or not np.isfinite(wall_increment).all():
                return prefix_result("out_of_scope", "cell-resolved wall source ledger shape mismatch")
        # Commit only after phase projection and every source ledger validate.
        current = projected
        solid = projected_solid
        phase_source += increment
        transport_source = next_transport_source
        for key in ledger_keys:
            ledger_total[key] = next_ledgers[key]
            ledger_history[key].append(ledger_total[key].tolist())
        wall_cell_total += wall_increment
        wall_cell_history.append(wall_cell_total.tolist())
        fields.append(current.tolist())
        solid_history.append(solid.tolist())
        phase_history.append(phase_source.tolist())
        transport_history.append(transport_source.tolist())
        try:
            potential = reconstruct_transport_potential(original, current)
            if potential is not None:
                potential_history.append(potential.tolist())
        except (ValueError, ArithmeticError) as error:
            return prefix_result("out_of_scope", str(error))

    inventory = (np.asarray(fields) * volumes).sum(axis=2)
    phase_history_array = np.asarray(phase_history)
    transport_history_array = np.asarray(transport_history)
    residual = inventory - initial_inventory - phase_history_array - transport_history_array
    scale = np.abs(inventory) + np.abs(initial_inventory) + np.abs(phase_history_array) + np.abs(transport_history_array)
    tolerance = original.inventory_absolute_tolerance_mol_m2 + original.inventory_relative_tolerance * scale
    if not np.isfinite(residual).all() or not np.isfinite(tolerance).all():
        return prefix_result("out_of_scope", "inventory balance exceeds numeric range")
    within = bool(np.all(np.abs(residual) <= tolerance))
    if not within:
        return prefix_result(
            "out_of_scope",
            "aqueous inventory balance exceeds the declared transport tolerance",
            {"final_inventory_balance_residual_mol_m2": residual.tolist()},
        )
    return base | {
        "status": "computed" if within else "out_of_scope",
        "elapsed_time_s": list(original.output_times_s),
        "species_ids": list(original.species_ids),
        "concentration_after_phase_mol_m3": fields,
        "concentration_mol_m3": fields,
        "solution_potential_V": potential_history if potential_history else None,
        "solid_species_ids": phase_ids,
        "solid_moles_per_solution_volume_mol_m3": solid_history,
        "initial_aqueous_inventory_before_phase_per_species_mol_m2": initial_inventory.tolist(),
        "cumulative_phase_aqueous_source_per_reference_area_mol_m2": phase_history_array.tolist(),
        "cumulative_transport_source_per_reference_area_mol_m2": transport_history_array.tolist(),
        "aqueous_inventory_balance_residual_mol_m2": residual.tolist(),
        "inventory_balance_within_declared_tolerance": within,
        "axial_advection_velocity_history_m_s": velocity_history or None,
        **ledger_history,
        "cumulative_wall_inward_by_cell_mol_m2": wall_cell_history,
        "basis": "Competitive caller-declared Davies, SIT or extended Debye-Huckel B-dot neutral-solid equilibrium is projected per cell initially and after each fixed-geometry transport interval; no simultaneous transport/phase solve, kinetics or moving geometry is inferred.",
    }
