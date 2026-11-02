"""Compose explicit carbonate boundaries, electrolyte chemistry, transport and selected metal loss."""

from collections.abc import Callable

import numpy as np
from pydantic import Field

from .carbonate_transport_adapter import CarbonateTransportBoundary
from .contracts import Contract, canonical_digest
from .dissolution_adapter import (
    CoupledWallMetalLossRequest,
    DissolutionSelection,
    WallMetalLossSelection,
    coupled_result_metal_loss,
    coupled_wall_metal_loss,
)
from .electrochemical_transport import ElectrochemicalTransport, solve_electrochemical_transport
from .equilibrium_reactive_transport import EquilibriumReactiveTransport


class Co2CorrosionCampaign(Contract):
    campaign_id: str = Field(min_length=1)
    carbonate_boundary: CarbonateTransportBoundary
    electrochemistry: ElectrochemicalTransport
    dissolution: DissolutionSelection
    wall_metal_loss_selection: WallMetalLossSelection | None = None
    phase_transport: EquilibriumReactiveTransport | None = None
    carbonate_species_boundary_and_mechanism_reviewed: bool
    time_varying_boundary_is_separately_qualified_reviewed: bool = False


def evaluate_co2_corrosion_campaign(
    request: Co2CorrosionCampaign,
    *,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
) -> dict:
    base = dict(
        campaign_id=request.campaign_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status="needs_data",
        electrochemical_result=None,
        metal_loss_result=None,
        metal_loss_scope=(
            "selected_tip_reaction_only"
            if request.wall_metal_loss_selection is None
            else "selected_tip_reaction_and_reviewed_wall_species_ledger"
        ),
        lateral_wall_loss_aggregation_included=False,
    )
    if not request.carbonate_species_boundary_and_mechanism_reviewed:
        return base
    boundary = request.carbonate_boundary
    model = request.electrochemistry
    if (
        model.transport.mouth_concentration_history_mol_m3 is not None
        and not request.time_varying_boundary_is_separately_qualified_reviewed
    ):
        return base | dict(
            reason="Time-varying boundary qualification is separate from the initial carbonate-equilibrium record"
        )
    concentrations = dict(
        zip(model.transport.species_ids, model.transport.mouth_concentration_mol_m3, strict=True)
    )
    for species, value in zip(boundary.species_ids, boundary.concentration_mol_m3, strict=True):
        if species not in concentrations or concentrations[species] != value:
            raise ValueError(
                "explicit carbonate boundary concentrations must match the transport mouth exactly"
            )
    if (
        request.phase_transport is not None
        and request.phase_transport.uniform_temperature_K != boundary.temperature_K
    ):
        raise ValueError("carbonate and phase-coupling temperatures differ")
    if model.transport.migration_temperature_K != boundary.temperature_K:
        raise ValueError("carbonate equilibrium and transport temperature differ")
    reactions = {row.reaction_id: row for row in model.surface_reactions}
    selected = reactions.get(request.dissolution.surface_reaction_id)
    if selected is None or selected.electron_count != request.dissolution.electron_count:
        raise ValueError("selected dissolution reaction/electron count differs from the coupled model")
    if (
        request.dissolution.metal_species_id not in selected.stoichiometric_species_coefficients
        or selected.stoichiometric_species_coefficients[request.dissolution.metal_species_id] <= 0
    ):
        raise ValueError("selected metal species must be explicitly produced by the dissolution reaction")
    if (
        selected.stoichiometric_species_coefficients[request.dissolution.metal_species_id]
        != request.dissolution.metal_moles_per_reaction_extent
    ):
        raise ValueError("selected metal production coefficient differs from the dissolution mapping")
    if request.wall_metal_loss_selection is not None:
        if not model.wall_surface_reactions:
            raise ValueError("wall metal-loss selection requires explicit wall surface reactions")
        wall_species = {
            species
            for reaction in model.wall_surface_reactions
            for species in reaction.stoichiometric_species_coefficients
        }
        if request.wall_metal_loss_selection.metal_species_id not in wall_species:
            raise ValueError("selected wall metal species is absent from every wall reaction")
        if (
            model.transport.reference_cross_section_m2
            != request.wall_metal_loss_selection.reference_cross_section_m2
        ):
            raise ValueError("wall metal-loss reference cross section differs from the transport geometry")
    result = solve_electrochemical_transport(
        model,
        wall_surface_flux=wall_surface_flux,
        activity_coefficients=activity_coefficients,
        phase_transport=request.phase_transport,
        axial_advection_velocity=axial_advection_velocity,
    )
    base["electrochemical_result"] = result
    if result["status"] != "computed":
        return base | dict(status=result["status"])
    loss = coupled_result_metal_loss(result, request.dissolution)
    wall_loss = None
    if request.wall_metal_loss_selection is not None:
        wall_loss = coupled_wall_metal_loss(
            CoupledWallMetalLossRequest(
                coupled_result=result,
                coupled_result_sha256=canonical_digest(result),
                selection=request.wall_metal_loss_selection,
            )
        )
        if wall_loss["status"] != "computed":
            return base | dict(
                status=wall_loss["status"],
                metal_loss_result=loss,
                wall_metal_loss_result=wall_loss,
                metal_loss_results={"tip": loss, "wall": wall_loss},
            )
    return base | dict(
        status=loss["loss"]["status"],
        metal_loss_result=loss,
        wall_metal_loss_result=wall_loss,
        metal_loss_results={"tip": loss, **({"wall": wall_loss} if wall_loss is not None else {})},
        lateral_wall_loss_aggregation_included=wall_loss is not None,
        basis="Explicit reviewed carbonate-boundary electrochemical transport and dissolution-current mapping. Fixed geometry and caller-calibrated chemistry, with optional explicit ideal single-solid phase splitting and digest-pinned layered-scale diffusion current limiting when separately reviewed; no evolving scale coverage, competing phases, precipitation kinetics, moving surface, automatic parameter calibration or acceptance.",
    )
