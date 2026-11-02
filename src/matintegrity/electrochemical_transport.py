"""Compose reviewed homogeneous reactions, ionic transport and electrode boundary kinetics."""

import math
from collections.abc import Callable

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, canonical_digest
from .models.competitive_solid_activity_iteration import CompetitiveSolidDaviesIteration
from .models.competitive_solid_bdot_iteration import CompetitiveSolidBdotIteration
from .models.competitive_solid_sit_iteration import CompetitiveSolidSITIteration
from .electrode_kinetics import ButlerVolmerReaction, electrode_reaction_flux, solve_electrode_mixed_potential
from .equilibrium_reactive_transport import EquilibriumReactiveTransport, solve_equilibrium_reactive_transport
from .multiphase_equilibrium_transport import (
    CompetitiveSolidEquilibriumTransport,
    solve_competitive_solid_equilibrium_transport,
)
from .reaction_network import MassActionNetwork, mass_action_callback
from .restricted_transport import RestrictedTransportRequest, solve_restricted_transport
from .scale_limited_electrochemistry import (
    ScaleLimitedSurfaceFlux,
    limit_species_production_branch_sets,
)


class ConcentrationKineticLaw(Contract):
    reference_concentration_mol_m3: dict[str, float]
    exchange_current_orders: dict[str, float]
    equilibrium_log_ratio_coefficients_V: dict[str, float]
    minimum_concentration_mol_m3: dict[str, float]
    maximum_concentration_mol_m3: dict[str, float]
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    concentration_law_reviewed: bool

    @model_validator(mode="after")
    def support(self):
        species = set(self.reference_concentration_mol_m3)
        if (
            not species
            or set(self.minimum_concentration_mol_m3) != species
            or set(self.maximum_concentration_mol_m3) != species
        ):
            raise ValueError("kinetic concentration reference and support must align")
        if not set(self.exchange_current_orders) | set(self.equilibrium_log_ratio_coefficients_V) <= species:
            raise ValueError("kinetic law contains undeclared concentration species")
        for name, reference in self.reference_concentration_mol_m3.items():
            low, high = self.minimum_concentration_mol_m3[name], self.maximum_concentration_mol_m3[name]
            if not 0 < low <= reference <= high:
                raise ValueError("kinetic concentration support must be positive and contain reference")
        return self


class ElectrochemicalTransport(Contract):
    campaign_id: str = Field(min_length=1)
    transport: RestrictedTransportRequest
    network: MassActionNetwork
    surface_reactions: tuple[ButlerVolmerReaction, ...] = Field(min_length=1)
    wall_surface_reactions: tuple[ButlerVolmerReaction, ...] = ()
    wall_surface_composition_and_reference_reviewed: bool = False
    equipotential_wall_and_metal_potential_reviewed: bool = False
    homogeneous_reaction_activity_correction_reviewed: bool = False
    metal_potential_V: float
    common_potential_reference_id: str = Field(min_length=1)
    surface_composition_and_reference_reviewed: bool
    free_corrosion_zero_current_reviewed: bool = False
    concentration_laws: dict[str, ConcentrationKineticLaw] = Field(default_factory=dict)
    scale_limited_surface_flux: ScaleLimitedSurfaceFlux | None = None
    additional_scale_limited_surface_fluxes: tuple[ScaleLimitedSurfaceFlux, ...] = ()

    @model_validator(mode="after")
    def compatible_components(self):
        if self.transport.species_ids != self.network.species_ids:
            raise ValueError("transport and reaction network species order must match exactly")
        if self.transport.charge_numbers != self.network.charge_numbers:
            raise ValueError("transport and homogeneous-network charge vectors must match")
        if self.transport.reaction_configuration_sha256 != canonical_digest(
            self.network.model_dump(mode="json")
        ):
            raise ValueError("transport homogeneous-network digest differs")
        surface_configuration = [row.model_dump(mode="json") for row in self.surface_reactions]
        if self.concentration_laws:
            surface_configuration = dict(
                reactions=surface_configuration,
                concentration_laws={
                    key: value.model_dump(mode="json") for key, value in self.concentration_laws.items()
                },
            )
        if self.transport.tip_surface_configuration_sha256 != canonical_digest(surface_configuration):
            raise ValueError("transport surface-reaction digest differs")
        wall_configuration = [row.model_dump(mode="json") for row in self.wall_surface_reactions]
        if self.wall_surface_reactions:
            wall_laws = {
                key: value.model_dump(mode="json")
                for key, value in self.concentration_laws.items()
                if key in {row.reaction_id for row in self.wall_surface_reactions}
            }
            if wall_laws:
                wall_configuration = dict(reactions=wall_configuration, concentration_laws=wall_laws)
            if self.transport.wall_surface_configuration_sha256 != canonical_digest(wall_configuration):
                raise ValueError("transport wall-reaction digest differs")
            if not (
                self.transport.wall_area_per_volume_m2_m3 is not None
                and self.transport.wall_surface_provider_id
                and self.transport.wall_surface_flux_basis_reviewed
                and self.wall_surface_composition_and_reference_reviewed
                and self.equipotential_wall_and_metal_potential_reviewed
            ):
                raise ValueError("wall kinetics require reviewed wall basis, geometry and equipotential assumption")
        if self.transport.prescribed_potential_V is None and self.transport.poisson_permittivity_F_m is None:
            raise ValueError("electrode coupling requires an explicit solution-potential model")
        if self.homogeneous_reaction_activity_correction_reviewed and not (
            self.transport.activity_provider_id
            and self.transport.activity_configuration_sha256
            and self.transport.activity_chemical_potential_and_tracer_diffusivity_reviewed
        ):
            raise ValueError(
                "reviewed reaction activity correction requires a digest-pinned transport activity provider"
            )
        all_reactions = (*self.surface_reactions, *self.wall_surface_reactions)
        if len({row.reaction_id for row in all_reactions}) != len(all_reactions):
            raise ValueError("surface reaction IDs must be unique")
        species = set(self.transport.species_ids)
        charges = dict(zip(self.network.species_ids, self.network.charge_numbers, strict=True))
        for row in all_reactions:
            if set(row.stoichiometric_species_coefficients) <= species:
                produced_charge = math.fsum(
                    charges[name] * coefficient
                    for name, coefficient in row.stoichiometric_species_coefficients.items()
                )
                if not math.isclose(produced_charge, float(row.electron_count), rel_tol=1e-10, abs_tol=1e-10):
                    raise ValueError(
                        "anodic surface stoichiometry must generate ionic charge equal to released electron count"
                    )
        if self.transport.migration_temperature_K is not None and any(
            row.temperature_K != self.transport.migration_temperature_K for row in all_reactions
        ):
            raise ValueError("surface reaction and transport migration temperatures must match")
        if not set(self.concentration_laws) <= {row.reaction_id for row in all_reactions}:
            raise ValueError("concentration law refers to unknown reaction")
        if any(
            not set(law.reference_concentration_mol_m3) <= species for law in self.concentration_laws.values()
        ):
            raise ValueError("concentration law refers to unknown species")
        if any(not set(row.stoichiometric_species_coefficients) <= species for row in all_reactions):
            raise ValueError("surface reaction references species absent from transport")
        scale_bindings = _scale_bindings(self)
        binding_keys = [(row.application_location, row.transported_species_id) for row in scale_bindings]
        if len(binding_keys) != len(set(binding_keys)):
            raise ValueError("scale limiter bindings must be unique by boundary and transported species")
        for location in {key[0] for key in binding_keys}:
            location_bindings = [row for row in scale_bindings if row.application_location == location]
            if len(location_bindings) > 1:
                area_basis_ids = {row.surface_area_basis_id for row in location_bindings}
                if None in area_basis_ids or len(area_basis_ids) != 1:
                    raise ValueError("multiple scale bounds at one electrode boundary require one shared explicit surface-area basis ID")
        for binding in scale_bindings:
            bounded_reactions = self.surface_reactions if binding.application_location == "tip" else self.wall_surface_reactions
            producing_ids = {
                row.reaction_id for row in bounded_reactions
                if row.stoichiometric_species_coefficients.get(binding.transported_species_id, 0.0) != 0
            }
            if producing_ids != set(binding.limited_reaction_ids):
                raise ValueError("scale limiter must cover every reaction branch producing its selected species at the selected boundary")
            if not producing_ids:
                raise ValueError("scale limiter has no producing reaction at the selected boundary")
        return self


def _scale_bindings(request: ElectrochemicalTransport) -> tuple[ScaleLimitedSurfaceFlux, ...]:
    return tuple(
        binding
        for binding in (request.scale_limited_surface_flux, *request.additional_scale_limited_surface_fluxes)
        if binding is not None
    )


class _SurfaceSupportError(ValueError):
    pass


def _apply_scale_limiters(bindings, reactions, reaction_results):
    return limit_species_production_branch_sets(tuple(bindings), reactions, reaction_results)


def _scale_limited_mixed_potential(reactions, limiters, stats=None):
    """Find zero net current after applying every reviewed species-flux cap."""
    low = max(row.equilibrium_potential_V + row.minimum_overpotential_V for row in reactions)
    high = min(row.equilibrium_potential_V + row.maximum_overpotential_V for row in reactions)
    if low >= high:
        raise _SurfaceSupportError("surface reactions have no common reviewed potential interval")

    def net_current(potential):
        evaluated = {}
        for row in reactions:
            result = electrode_reaction_flux(row, potential)
            if result["status"] != "computed":
                raise _SurfaceSupportError("scale-limited mixed-potential reaction left reviewed support")
            evaluated[row.reaction_id] = result
        evaluated, diagnostics = _apply_scale_limiters(limiters, reactions, evaluated)
        if stats is not None:
            for item_stats, item in zip(stats, diagnostics, strict=True):
                item_stats["reaction_evaluation_count"] += 1
                item_stats["limited_evaluation_count"] += int(item["productive_partial_current_scaling_factor"] < 1.0)
                item_stats["minimum_productive_partial_current_scaling_factor"] = min(
                    item_stats["minimum_productive_partial_current_scaling_factor"], item["productive_partial_current_scaling_factor"]
                )
                item_stats["maximum_unlimited_gross_species_production_mol_m2_s"] = max(
                    item_stats["maximum_unlimited_gross_species_production_mol_m2_s"], item["unlimited_gross_species_production_mol_m2_s"]
                )
        return math.fsum(row["signed_current_density_A_m2"] for row in evaluated.values())

    f_low = net_current(low)
    f_high = net_current(high)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if (f_low < 0) == (f_high < 0):
        raise _SurfaceSupportError("scale-limited zero-current potential is not bracketed inside reviewed support")
    for _ in range(120):
        mid = low + 0.5 * (high - low)
        f_mid = net_current(mid)
        if f_mid == 0 or high - low <= 1e-12:
            return mid
        if (f_low < 0) == (f_mid < 0):
            low, f_low = mid, f_mid
        else:
            high, f_high = mid, f_mid
    raise _SurfaceSupportError("scale-limited mixed-potential solve did not converge")


def assemble_electrochemical_transport(
    *,
    campaign_id: str,
    network: MassActionNetwork,
    transport_parameters: dict,
    surface_reactions: tuple[ButlerVolmerReaction, ...],
    surface_provider_id: str,
    metal_potential_V: float,
    common_potential_reference_id: str,
    surface_composition_and_reference_reviewed: bool,
    concentration_laws: dict[str, ConcentrationKineticLaw] | None = None,
    free_corrosion_zero_current_reviewed: bool = False,
    wall_surface_reactions: tuple[ButlerVolmerReaction, ...] = (),
    wall_surface_provider_id: str | None = None,
    wall_surface_composition_and_reference_reviewed: bool = False,
    equipotential_wall_and_metal_potential_reviewed: bool = False,
    homogeneous_reaction_activity_correction_reviewed: bool = False,
    scale_limited_surface_flux: ScaleLimitedSurfaceFlux | None = None,
    additional_scale_limited_surface_fluxes: tuple[ScaleLimitedSurfaceFlux, ...] = (),
) -> ElectrochemicalTransport:
    """Bind known component identities/digests; require all physical fields and review flags from caller."""
    laws = {} if concentration_laws is None else dict(concentration_laws)
    configuration = [row.model_dump(mode="json") for row in surface_reactions]
    if laws:
        configuration = dict(
            reactions=configuration,
            concentration_laws={name: law.model_dump(mode="json") for name, law in laws.items()},
        )
    bindings = dict(
        species_ids=network.species_ids,
        charge_numbers=network.charge_numbers,
        reaction_provider_id=network.network_id,
        reaction_configuration_sha256=canonical_digest(network.model_dump(mode="json")),
        tip_surface_provider_id=surface_provider_id,
        tip_surface_configuration_sha256=canonical_digest(configuration),
    )
    if wall_surface_reactions:
        wall_configuration = [row.model_dump(mode="json") for row in wall_surface_reactions]
        wall_laws = {
            name: law.model_dump(mode="json")
            for name, law in laws.items()
            if name in {row.reaction_id for row in wall_surface_reactions}
        }
        if wall_laws:
            wall_configuration = dict(reactions=wall_configuration, concentration_laws=wall_laws)
        bindings.update(
            wall_surface_provider_id=wall_surface_provider_id or f"electrochemical-wall:{campaign_id}",
            wall_surface_configuration_sha256=canonical_digest(wall_configuration),
        )
    parameters = dict(transport_parameters)
    for name, value in bindings.items():
        if name in parameters and parameters[name] != value:
            raise ValueError(f"caller transport field {name} conflicts with the selected component")
        parameters[name] = value
    transport = RestrictedTransportRequest.model_validate(parameters)
    return ElectrochemicalTransport(
        campaign_id=campaign_id,
        transport=transport,
        network=network,
        surface_reactions=surface_reactions,
        metal_potential_V=metal_potential_V,
        common_potential_reference_id=common_potential_reference_id,
        surface_composition_and_reference_reviewed=surface_composition_and_reference_reviewed,
        free_corrosion_zero_current_reviewed=free_corrosion_zero_current_reviewed,
        concentration_laws=laws,
        wall_surface_reactions=wall_surface_reactions,
        wall_surface_composition_and_reference_reviewed=wall_surface_composition_and_reference_reviewed,
        equipotential_wall_and_metal_potential_reviewed=equipotential_wall_and_metal_potential_reviewed,
        homogeneous_reaction_activity_correction_reviewed=homogeneous_reaction_activity_correction_reviewed,
        scale_limited_surface_flux=scale_limited_surface_flux,
        additional_scale_limited_surface_fluxes=additional_scale_limited_surface_fluxes,
    )


def solve_electrochemical_transport(
    request: ElectrochemicalTransport,
    *,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
    phase_transport: EquilibriumReactiveTransport | CompetitiveSolidEquilibriumTransport | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
) -> dict:
    base = dict(
        campaign_id=request.campaign_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status="needs_data",
        transport_result=None,
        network_configuration_sha256=canonical_digest(request.network.model_dump(mode="json")),
        surface_configuration_sha256=request.transport.tip_surface_configuration_sha256,
        species_ids=request.transport.species_ids,
        common_potential_reference_id=request.common_potential_reference_id,
        current_convention="anodic_positive_A_per_m2",
        concentration_unit="mol/m3",
        homogeneous_reaction_rate_basis=(
            "gamma_corrected_effective_concentration"
            if request.homogeneous_reaction_activity_correction_reviewed
            else "concentration"
        ),
    )
    if request.homogeneous_reaction_activity_correction_reviewed:
        if activity_coefficients is None:
            return base | dict(reason="Reviewed homogeneous-reaction activity provider callback is unavailable")
        expected_provider = request.transport.activity_provider_id
        expected_configuration = request.transport.activity_configuration_sha256
        if getattr(activity_coefficients, "provider_id", None) != expected_provider:
            raise ValueError("reaction activity provider identity differs from the pinned transport provider")
        if getattr(activity_coefficients, "configuration_sha256", None) != expected_configuration:
            raise ValueError("reaction activity provider configuration digest differs from the pinned transport digest")
        base["homogeneous_reaction_activity_lineage"] = {
            "provider_id": expected_provider,
            "provider_revision": getattr(activity_coefficients, "provider_revision", None),
            "configuration_sha256": expected_configuration,
            "correction_basis": "rate constants remain caller-calibrated concentration-basis constants; species concentrations are multiplied by supplied gamma",
            "reviewed": True,
        }
    scale_bindings = _scale_bindings(request)
    scale_limiter_stats = [{
            "scale_transport_result_sha256": limiter.scale_transport_result_sha256,
            "scale_state_id": limiter.scale_state_id,
            "transported_species_id": limiter.transported_species_id,
            "surface_area_basis_id": limiter.surface_area_basis_id,
            "application_location": limiter.application_location,
            "caller_flux_limit_mol_m2_s": limiter.flux_limit_mol_m2_s,
            "scale_transport_assessment_id": limiter.scale_transport_result.values.get("assessment_id"),
            "scale_physical_scope_id": limiter.physical_scope_id,
            "reaction_evaluation_count": 0,
            "limited_evaluation_count": 0,
            "minimum_productive_partial_current_scaling_factor": 1.0,
            "maximum_unlimited_gross_species_production_mol_m2_s": 0.0,
        } for limiter in scale_bindings]
    if scale_limiter_stats:
        # Preserve the original single-binding result field for existing callers.
        base["scale_limiter_diagnostics"] = scale_limiter_stats[0]
        base["scale_limiter_diagnostics_by_species"] = scale_limiter_stats
    if phase_transport is not None:
        if phase_transport.transport != request.transport:
            raise ValueError(
                "phase-coupling transport request must match the electrochemical transport exactly"
            )
        base["phase_transport_input_sha256"] = canonical_digest(phase_transport.model_dump(mode="json"))
        base["phase_transport_lineage"] = {
            "adapter_type": (
                (
                    "competitive_solid_davies_operator_split"
                    if isinstance(phase_transport.initial_cell_equilibria[0], CompetitiveSolidDaviesIteration)
                    else "competitive_solid_sit_operator_split"
                    if isinstance(phase_transport.initial_cell_equilibria[0], CompetitiveSolidSITIteration)
                    else "competitive_solid_bdot_operator_split"
                )
                if isinstance(phase_transport, CompetitiveSolidEquilibriumTransport)
                else "single_solid_equilibrium_operator_split"
            ),
            "campaign_id": phase_transport.campaign_id,
            "physical_scope_id": getattr(phase_transport, "physical_scope_id", None),
            "request_sha256": base["phase_transport_input_sha256"],
            "transport_request_sha256": canonical_digest(phase_transport.transport.model_dump(mode="json")),
            "activity_provider_id": phase_transport.transport.activity_provider_id,
            "activity_configuration_sha256": phase_transport.transport.activity_configuration_sha256,
        }
        if isinstance(phase_transport, CompetitiveSolidEquilibriumTransport):
            base["phase_transport_lineage"].update({
                "phase_ids": [row.solid_species_id for row in phase_transport.initial_cell_equilibria[0].equilibrium.candidate_solid_phases],
                "phase_activity_model": (
                    "Davies"
                    if isinstance(phase_transport.initial_cell_equilibria[0], CompetitiveSolidDaviesIteration)
                    else "SIT"
                    if isinstance(phase_transport.initial_cell_equilibria[0], CompetitiveSolidSITIteration)
                    else "B-dot"
                ),
                "uniform_temperature_K": phase_transport.uniform_temperature_K,
                "initial_equilibrium_projection_reviewed": phase_transport.initial_equilibrium_projection_reviewed,
                "instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed": phase_transport.instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed,
                "fixed_geometry_and_immobile_solid_basis_reviewed": phase_transport.fixed_geometry_and_immobile_solid_basis_reviewed,
                "transport_activity_to_phase_davies_mapping_reviewed": phase_transport.transport_activity_to_phase_davies_mapping_reviewed,
            })
        base["input_sha256"] = canonical_digest(
            {
                "electrochemistry": request.model_dump(mode="json"),
                "phase_transport": phase_transport.model_dump(mode="json"),
            }
        )
        if request.network.elemental_composition is None:
            return base | dict(reason="Phase coupling requires explicit network elemental composition")
        for phase in phase_transport.initial_cell_equilibria:
            aqueous_species = (
                phase.equilibrium.aqueous_species
                if isinstance(phase_transport, CompetitiveSolidEquilibriumTransport)
                else phase.aqueous_species
            )
            for row in aqueous_species:
                network_elements = {
                    name: value
                    for name, value in request.network.elemental_composition[row.species_id].items()
                    if value
                }
                phase_elements = {name: value for name, value in row.elemental_composition.items() if value}
                if network_elements != phase_elements:
                    raise ValueError("phase and network species elemental compositions differ")
    if not request.surface_composition_and_reference_reviewed:
        return base
    scale_limiter_review_gaps = []
    for limiter in scale_bindings:
        required_reviews = {
            "complete_species_production_branch_set_reviewed": limiter.complete_species_production_branch_set_reviewed,
            "diffusion_bound_and_surface_area_basis_reviewed": limiter.diffusion_bound_and_surface_area_basis_reviewed,
            "scale_state_constant_over_transport_horizon_reviewed": limiter.scale_state_constant_over_transport_horizon_reviewed,
            "metal_potential_and_solution_reference_compatible_reviewed": limiter.metal_potential_and_solution_reference_compatible_reviewed,
            "electrochemical_and_scale_physical_scope_match_reviewed": limiter.electrochemical_and_scale_physical_scope_match_reviewed,
        }
        missing_reviews = [name for name, reviewed in required_reviews.items() if not reviewed]
        if missing_reviews:
            scale_limiter_review_gaps.append({
                "application_location": limiter.application_location,
                "transported_species_id": limiter.transported_species_id,
                "missing_review_count": len(missing_reviews),
                "missing_reviews": missing_reviews,
            })
    if scale_limiter_review_gaps:
        return base | {"status": "needs_data", "scale_limiter_review_gaps": scale_limiter_review_gaps}
    if any(not law.concentration_law_reviewed for law in request.concentration_laws.values()):
        return base
    if not request.network.concentration_activity_approximation_and_rates_reviewed or any(
        not row.calibration_and_reaction_direction_reviewed for row in request.surface_reactions
    ):
        return base
    source = mass_action_callback(
        request.network,
        activity_coefficients=(
            activity_coefficients if request.homogeneous_reaction_activity_correction_reviewed else None
        ),
    )
    lookup = {species: i for i, species in enumerate(request.transport.species_ids)}

    def surface_for(reactions, time, concentrations, solution_potential, location, diagnostics=False):
        if solution_potential is None:
            raise _SurfaceSupportError("solution potential unavailable")
        flux = np.zeros(len(lookup))
        local_reactions = []
        for row in reactions:
            law = request.concentration_laws.get(row.reaction_id)
            if law is None:
                local_reactions.append(row)
                continue
            ratios = {}
            for species, reference in law.reference_concentration_mol_m3.items():
                value = float(concentrations[lookup[species]])
                if (
                    not law.minimum_concentration_mol_m3[species]
                    <= value
                    <= law.maximum_concentration_mol_m3[species]
                ):
                    raise _SurfaceSupportError("Surface concentration left kinetic calibration support")
                ratios[species] = math.log(value / reference)
            try:
                multiplier = math.exp(
                    math.fsum(
                        order * ratios[species] for species, order in law.exchange_current_orders.items()
                    )
                )
            except OverflowError as error:
                raise _SurfaceSupportError(
                    "Concentration kinetic multiplier exceeds numeric range"
                ) from error
            payload = row.model_dump(mode="python")
            payload["exchange_current_density_A_m2"] *= multiplier
            payload["equilibrium_potential_V"] += math.fsum(
                coefficient * ratios[species]
                for species, coefficient in law.equilibrium_log_ratio_coefficients_V.items()
            )
            local_reactions.append(ButlerVolmerReaction.model_validate(payload))
        local_reactions = tuple(local_reactions)
        delta = request.metal_potential_V - solution_potential
        active_limiters = tuple(
            binding for binding in scale_bindings if binding.application_location == location
        )
        active_stats = [
            stats for binding, stats in zip(scale_bindings, scale_limiter_stats, strict=True)
            if binding.application_location == location
        ]
        if request.free_corrosion_zero_current_reviewed:
            if not active_limiters:
                mixed = solve_electrode_mixed_potential(local_reactions)
                if mixed["status"] != "computed":
                    raise _SurfaceSupportError("Free-corrosion mixed potential is not supported or identifiable")
                delta = mixed["metal_minus_solution_potential_V"]
            else:
                delta = _scale_limited_mixed_potential(local_reactions, active_limiters, active_stats)
        partial_currents = {}
        anodic_currents = {}
        cathodic_currents = {}
        reaction_results = {}
        for row in local_reactions:
            result = electrode_reaction_flux(row, delta)
            if result["status"] != "computed":
                raise _SurfaceSupportError(f"surface reaction {row.reaction_id} exceeds reviewed support")
            reaction_results[row.reaction_id] = result
        scale_limit_diagnostics = []
        if active_limiters:
            try:
                reaction_results, scale_limit_diagnostics = _apply_scale_limiters(
                    active_limiters, local_reactions, reaction_results
                )
            except (ArithmeticError, KeyError, ValueError) as error:
                raise _SurfaceSupportError("scale-limited electrochemical boundary is unsupported") from error
            for item_stats, item in zip(active_stats, scale_limit_diagnostics, strict=True):
                item_stats["reaction_evaluation_count"] += 1
                item_stats["limited_evaluation_count"] += int(item["productive_partial_current_scaling_factor"] < 1.0)
                item_stats["minimum_productive_partial_current_scaling_factor"] = min(
                    item_stats["minimum_productive_partial_current_scaling_factor"],
                    item["productive_partial_current_scaling_factor"],
                )
                item_stats["maximum_unlimited_gross_species_production_mol_m2_s"] = max(
                    item_stats["maximum_unlimited_gross_species_production_mol_m2_s"],
                    item["unlimited_gross_species_production_mol_m2_s"],
                )
        for row in local_reactions:
            result = reaction_results[row.reaction_id]
            partial_currents[row.reaction_id] = result["signed_current_density_A_m2"]
            anodic_currents[row.reaction_id] = result["gross_anodic_current_density_A_m2"]
            cathodic_currents[row.reaction_id] = result["gross_cathodic_current_density_A_m2"]
            for species, value in result["inward_species_flux_mol_m2_s"].items():
                flux[lookup[species]] += value
        if diagnostics:
            details = dict(
                metal_minus_solution_potential_V=delta,
                partial_signed_current_A_m2=partial_currents,
                gross_anodic_current_A_m2=anodic_currents,
                gross_cathodic_current_A_m2=cathodic_currents,
                net_current_A_m2=math.fsum(partial_currents.values()),
            )
            if scale_limit_diagnostics:
                details["scale_transport_flux_limits"] = scale_limit_diagnostics
                if len(scale_limit_diagnostics) == 1:
                    details["scale_transport_flux_limit"] = scale_limit_diagnostics[0]
            return details
        return flux

    def surface(time, concentrations, solution_potential, diagnostics=False):
        return surface_for(request.surface_reactions, time, concentrations, solution_potential, "tip", diagnostics)

    built_in_wall = bool(request.wall_surface_reactions)
    if built_in_wall and wall_surface_flux is not None:
        raise ValueError("supply either built-in wall kinetics or an external wall callback, not both")
    if built_in_wall:
        if not request.wall_surface_composition_and_reference_reviewed or not request.equipotential_wall_and_metal_potential_reviewed:
            return base
        wall_reaction_ids = {row.reaction_id for row in request.wall_surface_reactions}
        if any(
            not law.concentration_law_reviewed
            for key, law in request.concentration_laws.items()
            if key in wall_reaction_ids
        ):
            return base
        if any(not row.calibration_and_reaction_direction_reviewed for row in request.wall_surface_reactions):
            return base

        def wall_surface_flux(time, concentrations, potentials):
            values = np.asarray(concentrations, dtype=float)
            phi = None if potentials is None else np.asarray(potentials, dtype=float)
            if values.shape != (len(lookup), request.transport.cell_count):
                raise _SurfaceSupportError("wall kinetic concentration array must be species by cell")
            if phi is None or phi.shape != (request.transport.cell_count,):
                raise _SurfaceSupportError("wall kinetics require one local solution potential per cell")
            flux = np.zeros_like(values)
            for cell in range(request.transport.cell_count):
                flux[:, cell] = surface_for(
                    request.wall_surface_reactions, time, values[:, cell], phi[cell], "wall"
                )
            return flux

        wall_surface_flux.configuration_sha256 = request.transport.wall_surface_configuration_sha256

    try:
        if phase_transport is None:
            result = solve_restricted_transport(
                request.transport,
                source,
                surface,
                wall_surface_flux=wall_surface_flux,
                activity_coefficients=activity_coefficients,
                axial_advection_velocity=axial_advection_velocity,
            )
        elif isinstance(phase_transport, CompetitiveSolidEquilibriumTransport):
            result = solve_competitive_solid_equilibrium_transport(
                phase_transport,
                source,
                tip_surface_flux=surface,
                wall_surface_flux=wall_surface_flux,
                axial_advection_velocity=axial_advection_velocity,
                activity_coefficients=activity_coefficients,
            )
        else:
            result = solve_equilibrium_reactive_transport(
                phase_transport,
                source,
                tip_surface_flux=surface,
                wall_surface_flux=wall_surface_flux,
                axial_advection_velocity=axial_advection_velocity,
                activity_coefficients=activity_coefficients,
            )
    except _SurfaceSupportError as error:
        return base | dict(status="out_of_scope", reason=str(error))
    surface_history = None
    if result["status"] == "computed":
        surface_history = []
        try:
            for time, concentrations, potentials in zip(
                result["elapsed_time_s"],
                result["concentration_mol_m3"],
                result["solution_potential_V"],
                strict=True,
            ):
                surface_history.append(
                    surface(time, np.asarray(concentrations)[:, -1], potentials[-1], diagnostics=True)
                )
        except _SurfaceSupportError as error:
            return base | dict(status="out_of_scope", reason=str(error), transport_result=result)
    return base | dict(
        status=result["status"],
        transport_result=result,
        surface_history=surface_history,
        surface_history_basis=(
            "Output-knot diagnostic re-evaluated at the concentrations and solution potentials returned by the transport/phase operator; it is not the solver-integrated boundary-flux history."
        ) if surface_history is not None else None,
        basis="Caller-calibrated reaction network with imposed-potential or reviewed zero-current boundary. Concentration laws and optional Poisson closure are explicit inputs; optional single-solid or caller-declared competing neutral-solid equilibrium projection is operator-split at transport output knots. A digest-pinned layered-scale diffusion upper bound may cap gross production of a selected species by scaling every selected producer partial-current branch while retaining reaction stoichiometry. Evolving scale state/coverage, phase kinetics, moving geometry and chemistry calibration remain separate models.",
    )
