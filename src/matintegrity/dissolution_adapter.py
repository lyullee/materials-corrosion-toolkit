"""Explicit reviewed mapping from one coupled reaction-current history to uniform metal loss."""

import math
from typing import Any
from typing import Literal

from pydantic import Field

from .contracts import Contract, Positive, canonical_digest
from .metal_dissolution import PartialMetalDissolutionHistory, integrate_partial_metal_dissolution


class DissolutionSelection(Contract):
    history_id: str = Field(min_length=1)
    surface_reaction_id: str = Field(min_length=1)
    metal_species_id: str = Field(min_length=1)
    electron_count: int = Field(gt=0)
    metal_moles_per_reaction_extent: Positive = 1.0
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    dissolution_current_efficiency: float = Field(gt=0, le=1)
    selected_reaction_is_dissolution_only_reviewed: bool
    uniform_recession_and_output_clock_resolution_reviewed: bool
    current_component: Literal["reaction_net_dissolution_only", "gross_anodic"] = (
        "reaction_net_dissolution_only"
    )


class NetMetalBoundarySelection(Contract):
    metal_species_id: str = Field(min_length=1)
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    boundary_species_is_one_metal_atom_per_mole_reviewed: bool
    all_tip_metal_flux_is_dissolution_or_redeposition_reviewed: bool
    fixed_surface_area_and_uniform_change_reviewed: bool


class WallMetalLossSelection(Contract):
    selection_id: str = Field(min_length=1)
    metal_species_id: str = Field(min_length=1)
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    reference_cross_section_m2: Positive
    boundary_species_is_one_metal_atom_per_mole_reviewed: bool
    wall_flux_is_signed_dissolution_or_redeposition_reviewed: bool
    reactive_wall_and_reference_areas_reviewed: bool
    area_average_recession_interpretation_reviewed: bool
    cellwise_recession_interpretation_reviewed: bool = False


class CoupledWallMetalLossRequest(Contract):
    coupled_result: dict[str, Any]
    coupled_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selection: WallMetalLossSelection


def coupled_wall_metal_loss(request: CoupledWallMetalLossRequest) -> dict:
    """Map a signed integrated wall-species ledger to total mass and area-average recession."""
    result = request.coupled_result
    selection = request.selection
    result_digest = canonical_digest(result)
    base = dict(
        status="needs_data",
        coupled_result_sha256=result_digest,
        selection_sha256=canonical_digest(selection.model_dump(mode="json")),
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        wall_metal_loss=None,
        wall_transfer_basis="solver_integrated_signed_species_ledger",
        current_efficiency_factor_applied=False,
    )
    if result_digest != request.coupled_result_sha256:
        raise ValueError("coupled result digest differs from the caller-pinned value")
    if not (
        selection.boundary_species_is_one_metal_atom_per_mole_reviewed
        and selection.wall_flux_is_signed_dissolution_or_redeposition_reviewed
        and selection.reactive_wall_and_reference_areas_reviewed
        and selection.area_average_recession_interpretation_reviewed
    ):
        return base
    # Accept registry AssessmentResult values, direct solver composition, or campaign nesting.
    payload = result.get("values", result)
    if not isinstance(payload, dict):
        return base | dict(status="needs_data", reason="Coupled result values must be an object")
    coupled = payload.get("electrochemical_result", payload)
    if not isinstance(coupled, dict):
        return base | dict(status="needs_data", reason="Coupled electrochemical result must be an object")
    if coupled.get("status") != "computed":
        return base | dict(status=coupled.get("status", "needs_data"), reason="Coupled electrochemical calculation is incomplete")
    transport = coupled.get("transport_result")
    if not isinstance(transport, dict) or transport.get("status") != "computed":
        return base | dict(status="needs_data", reason="A complete transport result is required")
    species = transport.get("species_ids")
    if (
        not isinstance(species, list)
        or any(not isinstance(item, str) for item in species)
        or len(set(species)) != len(species)
    ):
        return base | dict(status="needs_data", reason="Unique transport species order is required")
    if selection.metal_species_id not in species:
        return base | dict(status="out_of_scope", reason="Selected metal species is absent from transport")
    if transport.get("reference_cross_section_m2") != selection.reference_cross_section_m2:
        return base | dict(status="out_of_scope", reason="Reviewed reference cross section differs from transport")
    area_ratio = transport.get("wall_area_over_reference_area")
    if isinstance(area_ratio, bool) or not isinstance(area_ratio, (int, float)) or not math.isfinite(area_ratio) or area_ratio <= 0:
        return base | dict(status="needs_data", reason="Transport result lacks positive reactive wall area")
    time = transport.get("elapsed_time_s")
    ledger = transport.get("cumulative_wall_inward_mol_m2")
    if (
        not isinstance(time, list)
        or len(time) < 2
        or not isinstance(ledger, list)
        or len(time) != len(ledger)
        or any(not isinstance(row, list) or len(row) != len(species) for row in ledger)
    ):
        return base | dict(status="needs_data", reason="Wall-species ledger does not align with the output clock")
    index = species.index(selection.metal_species_id)
    physical_wall_area = area_ratio * selection.reference_cross_section_m2
    if not math.isfinite(physical_wall_area) or physical_wall_area <= 0:
        return base | dict(status="out_of_scope", reason="Reactive wall area exceeds numeric range")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in time
    ) or time[0] != 0 or any(right <= left for left, right in zip(time[:-1], time[1:], strict=True)):
        return base | dict(status="needs_data", reason="Finite strictly increasing output times are required")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for row in ledger
        for value in row
    ):
        return base | dict(status="out_of_scope", reason="Wall species ledger contains a nonfinite or nonnumeric value")
    rows = []
    for elapsed, values in zip(time, ledger, strict=True):
        amount_per_reference_area = values[index]
        total_amount = amount_per_reference_area * selection.reference_cross_section_m2
        mass = total_amount * selection.metal_molar_mass_kg_mol
        volume = mass / selection.metal_density_kg_m3
        mean_recession = volume / physical_wall_area
        if not all(math.isfinite(value) for value in (amount_per_reference_area, total_amount, mass, volume, mean_recession)):
            return base | dict(status="out_of_scope", reason="Wall metal-loss conversion exceeded numeric range")
        rows.append(
            dict(
                elapsed_time_s=elapsed,
                net_metal_amount_per_reference_area_mol_m2=amount_per_reference_area,
                net_metal_amount_mol=total_amount,
                net_mass_loss_kg=mass,
                net_volume_change_m3=volume,
                signed_area_average_recession_m=mean_recession,
            )
        )
    cellwise_history = None
    if selection.cellwise_recession_interpretation_reviewed:
        cell_ledger = transport.get("cumulative_wall_inward_by_cell_mol_m2")
        area_density = transport.get("wall_area_per_volume_m2_m3")
        widths = transport.get("cell_widths_m")
        cell_cross_sections = transport.get("cell_cross_section_m2")
        reference_area = transport.get("reference_cross_section_m2")
        if (
            not isinstance(cell_ledger, list)
            or not isinstance(area_density, list)
            or not isinstance(widths, list)
            or len(area_density) < 1
            or len(widths) != len(area_density)
            or len(cell_ledger) != len(time)
            or any(
                not isinstance(row, list)
                or len(row) != len(species)
                or any(not isinstance(species_row, list) or len(species_row) != len(area_density) for species_row in row)
                for row in cell_ledger
            )
        ):
            return base | dict(
                status="needs_data",
                reason="Cell-resolved wall ledger, geometry and species ordering are required for local recession",
            )
        if cell_cross_sections is None:
            if reference_area is not None:
                return base | dict(status="needs_data", reason="Variable-area cell cross sections are required")
            cell_wall_area_ratio = [density * width for density, width in zip(area_density, widths, strict=True)]
        else:
            if (
                not isinstance(cell_cross_sections, list)
                or len(cell_cross_sections) != len(area_density)
                or reference_area != selection.reference_cross_section_m2
            ):
                return base | dict(status="out_of_scope", reason="Cell and reference areas do not match the reviewed selection")
            cell_wall_area_ratio = [
                density * width * cross_section / reference_area
                for density, width, cross_section in zip(area_density, widths, cell_cross_sections, strict=True)
            ]
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
            for value in cell_wall_area_ratio
        ) or not math.isclose(math.fsum(cell_wall_area_ratio), area_ratio, rel_tol=1e-8, abs_tol=1e-12):
            return base | dict(status="out_of_scope", reason="Cell reactive wall areas do not reconcile with total wall area")
        cellwise_history = []
        for elapsed, by_species in zip(time, cell_ledger, strict=True):
            cells = []
            for cell_index, amount_per_reference_area in enumerate(by_species[index]):
                amount = amount_per_reference_area * selection.reference_cross_section_m2
                mass = amount * selection.metal_molar_mass_kg_mol
                volume = mass / selection.metal_density_kg_m3
                recession = (
                    amount_per_reference_area
                    * selection.metal_molar_mass_kg_mol
                    / selection.metal_density_kg_m3
                    / cell_wall_area_ratio[cell_index]
                )
                if not all(math.isfinite(value) for value in (amount_per_reference_area, amount, mass, volume, recession)):
                    return base | dict(status="out_of_scope", reason="Cellwise wall-metal conversion exceeded numeric range")
                cells.append(
                    dict(
                        cell_index=cell_index,
                        net_metal_amount_per_reference_area_mol_m2=amount_per_reference_area,
                        net_metal_amount_mol=amount,
                        net_mass_loss_kg=mass,
                        net_volume_change_m3=volume,
                        reactive_wall_area_over_reference_area=cell_wall_area_ratio[cell_index],
                        signed_local_cell_average_recession_m=recession,
                    )
                )
            cellwise_history.append(dict(elapsed_time_s=elapsed, cells=cells))
    return base | dict(
        status="computed",
        wall_metal_loss=dict(
            metal_species_id=selection.metal_species_id,
            transfer_basis="solver_integrated_signed_species_ledger",
            current_efficiency_factor_applied=False,
            elapsed_time_s=time,
            reference_cross_section_m2=selection.reference_cross_section_m2,
            reactive_wall_area_over_reference_area=area_ratio,
            reactive_wall_area_m2=physical_wall_area,
            history=rows,
            cellwise_history=cellwise_history,
            interpretation="Signed wall uptake is positive metal loss and negative uptake is redeposition. Recession is an area-average material-volume balance over the caller-reviewed reactive wall area; it is not a local thickness field, corrosion rate qualification, capacity, acceptance, remaining-life or failure-probability result.",
        ),
    )


def coupled_net_metal_boundary_change(result: dict, selection: NetMetalBoundarySelection) -> dict:
    """Map signed solver-integrated boundary amount to net metal loss without absolute values."""
    if result.get("status") != "computed" or result.get("transport_result", {}).get("status") != "computed":
        raise ValueError("complete coupled transport result required")
    if not (
        selection.boundary_species_is_one_metal_atom_per_mole_reviewed
        and selection.all_tip_metal_flux_is_dissolution_or_redeposition_reviewed
        and selection.fixed_surface_area_and_uniform_change_reviewed
    ):
        raise ValueError("metal species, complete boundary flux meaning and fixed-area change require review")
    species = result.get("species_ids")
    if species is None or len(set(species)) != len(species) or selection.metal_species_id not in species:
        raise ValueError("selected metal species is absent or result order is ambiguous")
    index = species.index(selection.metal_species_id)
    transport = result["transport_result"]
    rows = transport.get("cumulative_tip_inward_mol_m2")
    clock = transport.get("elapsed_time_s")
    if not rows or clock is None or len(rows) != len(clock) or any(len(row) != len(species) for row in rows):
        raise ValueError("integrated boundary amounts must align with species and output clock")
    area_ratio = transport.get("tip_area_over_reference_area", 1.0)
    if isinstance(area_ratio, bool) or not math.isfinite(area_ratio) or area_ratio <= 0:
        raise ValueError("tip-to-reference area ratio must be finite and positive")
    if (
        transport.get("reference_cross_section_m2") is not None
        and "tip_area_over_reference_area" not in transport
    ):
        raise ValueError("variable-area transport must declare its tip-to-reference area ratio")
    reference_amounts = [float(row[index]) for row in rows]
    amounts = [value / area_ratio for value in reference_amounts]
    if not all(math.isfinite(value) for value in amounts):
        raise ValueError("integrated metal boundary amounts must be finite")
    mass = [value * selection.metal_molar_mass_kg_mol for value in amounts]
    recession = [value / selection.metal_density_kg_m3 for value in mass]
    if not all(math.isfinite(value) for value in mass + recession):
        return dict(
            status="out_of_scope",
            reason="Metal mass/recession exceeds numeric range",
            provider_result_sha256=canonical_digest(result),
            selection_sha256=canonical_digest(selection.model_dump(mode="json")),
        )
    return dict(
        status="computed",
        provider_result_sha256=canonical_digest(result),
        selection_sha256=canonical_digest(selection.model_dump(mode="json")),
        elapsed_time_s=clock,
        tip_area_over_reference_area=area_ratio,
        cumulative_metal_per_reference_area_mol_m2=reference_amounts,
        net_metal_loss_mol_m2=amounts,
        metal_loss_area_basis="local_tip_surface_area",
        net_mass_loss_kg_m2=mass,
        net_uniform_recession_m=recession,
        interpretation="Signed metal transfer into solution is positive loss; negative values represent net deposition. Uses the solver-integrated tip flux converted from fixed reference area to local tip area; not resampled current trapezoids. No moving geometry or alloy selective dissolution is inferred.",
    )


def dissolution_history_from_coupled_result(
    result: dict, selection: DissolutionSelection
) -> PartialMetalDissolutionHistory:
    if result.get("status") != "computed" or result.get("transport_result", {}).get("status") != "computed":
        raise ValueError("only a complete coupled transport result can provide a dissolution history")
    if (
        not selection.selected_reaction_is_dissolution_only_reviewed
        or not selection.uniform_recession_and_output_clock_resolution_reviewed
    ):
        raise ValueError(
            "reaction interpretation, uniform recession and output-clock resolution require review"
        )
    clock = result["transport_result"]["elapsed_time_s"]
    rows = result.get("surface_history")
    if rows is None or len(rows) != len(clock):
        raise ValueError("surface current history must align exactly with the output clock")
    currents = []
    for row in rows:
        key = (
            "gross_anodic_current_A_m2"
            if selection.current_component == "gross_anodic"
            else "partial_signed_current_A_m2"
        )
        mapping = row.get(key, {})
        if selection.surface_reaction_id not in mapping:
            raise ValueError("selected surface reaction is absent from a result row")
        value = mapping[selection.surface_reaction_id]
        if isinstance(value, bool) or not math.isfinite(value) or value < 0:
            raise ValueError(
                "dissolution history requires finite nonnegative selected current; no clipping or absolute-value conversion"
            )
        currents.append(float(value))
    return PartialMetalDissolutionHistory(
        history_id=selection.history_id,
        metal_species_id=selection.metal_species_id,
        surface_reaction_id=selection.surface_reaction_id,
        provider_result_sha256=canonical_digest(result),
        elapsed_time_s=tuple(float(value) for value in clock),
        partial_anodic_current_A_m2=tuple(currents),
        electron_count=selection.electron_count,
        metal_moles_per_reaction_extent=selection.metal_moles_per_reaction_extent,
        metal_molar_mass_kg_mol=selection.metal_molar_mass_kg_mol,
        metal_density_kg_m3=selection.metal_density_kg_m3,
        dissolution_current_efficiency=selection.dissolution_current_efficiency,
        partial_current_and_uniform_recession_reviewed=True,
    )


def coupled_result_metal_loss(result: dict, selection: DissolutionSelection) -> dict:
    history = dissolution_history_from_coupled_result(result, selection)
    return dict(
        history=history.model_dump(mode="json"),
        loss=integrate_partial_metal_dissolution(history),
        current_component=selection.current_component,
        interpretation="Gross anodic removal excludes cathodic redeposition and is not automatically net dimensional recession."
        if selection.current_component == "gross_anodic"
        else "Caller-reviewed dissolution-only reaction current.",
    )
