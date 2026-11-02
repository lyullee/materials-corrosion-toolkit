from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .electrode_kinetics import ButlerVolmerReaction, electrode_reaction_flux
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_finite_inventory_electrode_mixed_potential"
TRANSFER_SOURCE_ID = "caller_cylindrical_liquid_transfer_capacity_history"
GEOMETRY_SOURCE_ID = "caller_cylindrical_geometry_result"
KINETICS_SOURCE_ID = "caller_calibrated_butler_volmer_branch_set"
INVENTORY_SOURCE_ID = "caller_finite_bulk_wall_liquid_inventories"
EXCHANGE_SOURCE_ID = "caller_interval_external_liquid_sources_sinks"
METHOD_SOURCE_ID = "finite_reservoir_species_limited_mixed_potential_ledger"
FARADAY_C_MOL = 96485.33212


class WetCo2LumpedElectrochemicalSpecies(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    charge_number: int = Field(ge=-8, le=8)
    elemental_composition: dict[str, Positive]


class WetCo2LumpedElectrochemicalInitialInventory(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    bulk_inventory_mol: Nonnegative
    wall_inventory_mol: Nonnegative
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_initial_record(self):
        payload = {"species_id": self.species_id, "bulk_inventory_mol": self.bulk_inventory_mol,
                   "wall_inventory_mol": self.wall_inventory_mol}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("initial inventory digest must bind species and both compartment stocks")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each initial finite-liquid inventory")
        return self


class WetCo2LumpedElectrochemicalVolumeKnot(Contract):
    time_s: Nonnegative
    bulk_volume_m3: Positive
    wall_volume_m3: Positive


class WetCo2LumpedElectrochemicalReaction(Contract):
    kinetics: ButlerVolmerReaction
    metal_element_release_mol_per_extent: dict[str, Nonnegative] = Field(default_factory=dict)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_kinetics_evidence(self):
        if not any(row.sha256 == self.kinetics.calibration_sha256 and row.license_id
                   for row in self.evidence):
            raise ValueError("licensed Evidence must pin the electrode branch calibration")
        return self


class WetCo2LumpedElectrochemicalInterval(Contract):
    start_time_s: Nonnegative
    end_time_s: Positive
    reactions: tuple[WetCo2LumpedElectrochemicalReaction, ...] = Field(min_length=2, max_length=64)

    @model_validator(mode="after")
    def validate_interval_reactions(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("electrochemical interval must have positive duration")
        ids = [row.kinetics.reaction_id for row in self.reactions]
        if len(ids) != len(set(ids)):
            raise ValueError("reaction IDs must be unique within each interval")
        return self


class WetCo2LumpedElectrochemicalExternalExchange(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    start_time_s: Nonnegative
    end_time_s: Positive
    bulk_inventory_change_mol: float
    wall_inventory_change_mol: float
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_exchange(self):
        payload = {"species_id": self.species_id, "start_time_s": self.start_time_s,
                   "end_time_s": self.end_time_s, "bulk_inventory_change_mol": self.bulk_inventory_change_mol,
                   "wall_inventory_change_mol": self.wall_inventory_change_mol}
        if self.end_time_s <= self.start_time_s or not all(math.isfinite(value) for value in (
            self.bulk_inventory_change_mol, self.wall_inventory_change_mol
        )):
            raise ValueError("external exchange must be finite and cover a positive interval")
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("external exchange digest must bind the species, interval and changes")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each external compartment exchange")
        return self


class WetCo2FiniteInventoryElectrodeMixedPotential(Contract):
    """Transient finite-reservoir electrode coupling with branch supply limits and common potential."""

    schema_version: Literal["matintegrity.wet_co2_finite_inventory_electrode_mixed_potential.v1"] = (
        "matintegrity.wet_co2_finite_inventory_electrode_mixed_potential.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    geometry_result: Calculation
    transfer_capacity_results: dict[str, Calculation] = Field(min_length=2, max_length=32)
    species: tuple[WetCo2LumpedElectrochemicalSpecies, ...] = Field(min_length=2, max_length=32)
    initial_inventories: tuple[WetCo2LumpedElectrochemicalInitialInventory, ...] = Field(min_length=2, max_length=32)
    volume_history: tuple[WetCo2LumpedElectrochemicalVolumeKnot, ...] = Field(min_length=2, max_length=5000)
    intervals: tuple[WetCo2LumpedElectrochemicalInterval, ...] = Field(min_length=1, max_length=4999)
    external_exchanges: tuple[WetCo2LumpedElectrochemicalExternalExchange, ...] = Field(min_length=2, max_length=159968)
    potential_absolute_tolerance_V: Positive = 1e-10
    current_absolute_tolerance_A_m2: Positive = 1e-8
    inventory_absolute_tolerance_mol: Positive = 1e-12
    inventory_relative_tolerance: Positive = Field(default=1e-8, le=1e-2)
    maximum_bisection_iterations: int = Field(default=200, ge=10, le=500)
    finite_reservoir_and_current_area_reviewed: bool
    reaction_formula_charge_and_direction_reviewed: bool
    well_mixed_bulk_and_wall_compartments_reviewed: bool

    @model_validator(mode="after")
    def validate_exact_cross_model_contracts(self):
        if self.geometry_result.status != "computed" or self.geometry_result.values.get("model_id") != "degradation.wet_co2_cylindrical_scale_geometry_history":
            raise ValueError("computed cylindrical geometry result is required")
        geometry_digest = canonical_digest(self.geometry_result.model_dump(mode="json"))
        times = tuple(float(row["time_s"]) for row in self.geometry_result.values.get("history", []))
        if tuple(row.time_s for row in self.volume_history) != times:
            raise ValueError("compartment volumes must use exact geometry knots")
        if len(self.intervals) != len(times) - 1 or tuple(row.start_time_s for row in self.intervals) != times[:-1] or tuple(
            row.end_time_s for row in self.intervals
        ) != times[1:]:
            raise ValueError("electrode intervals must cover each adjacent geometry knot exactly")
        species_ids = {row.species_id for row in self.species}
        if len(species_ids) != len(self.species) or species_ids != set(self.transfer_capacity_results):
            raise ValueError("unique species IDs must exactly match transfer capacity result keys")
        if {row.species_id for row in self.initial_inventories} != species_ids or len(self.initial_inventories) != len(species_ids):
            raise ValueError("initial inventories must include each and only each species exactly once")
        formulas = {row.species_id: row.elemental_composition for row in self.species}
        charges = {row.species_id: row.charge_number for row in self.species}
        for species_id, result in self.transfer_capacity_results.items():
            if result.status != "computed" or result.values.get("model_id") != "integration.wet_co2_cylindrical_liquid_transfer_capacity_history":
                raise ValueError("each species must have a computed cylindrical transfer-capacity history")
            if result.values.get("assessment_id") != self.assessment_id or result.values.get("asset_id") != self.geometry_result.values.get("asset_id") or result.values.get("location_id") != self.geometry_result.values.get("location_id"):
                raise ValueError("transfer-capacity scope must match the geometry/electrode request")
            if result.values.get("species_id") != species_id or result.values.get("geometry_result_sha256") != geometry_digest:
                raise ValueError("each transfer-capacity history must bind its species and the exact geometry result")
            if tuple(float(row["time_s"]) for row in result.values.get("history", [])) != times:
                raise ValueError("transfer-capacity histories must use exact geometry knots")
        expected_exchange = {(species_id, left, right) for species_id in species_ids
                             for left, right in zip(times[:-1], times[1:], strict=True)}
        actual_exchange = {(row.species_id, row.start_time_s, row.end_time_s) for row in self.external_exchanges}
        if actual_exchange != expected_exchange or len(actual_exchange) != len(self.external_exchanges):
            raise ValueError("external exchanges must cover every species and every exact interval once")
        for interval in self.intervals:
            if len({row.kinetics.temperature_K for row in interval.reactions}) != 1:
                raise ValueError("all simultaneous electrode branches in an interval must share one temperature")
            low = max(row.kinetics.equilibrium_potential_V + row.kinetics.minimum_overpotential_V
                      for row in interval.reactions)
            high = min(row.kinetics.equilibrium_potential_V + row.kinetics.maximum_overpotential_V
                       for row in interval.reactions)
            if low >= high:
                raise ValueError("interval reactions have no common reviewed potential support")
            for branch in interval.reactions:
                reaction = branch.kinetics
                if not reaction.calibration_and_reaction_direction_reviewed:
                    raise ValueError("each electrode reaction direction/calibration must be reviewed")
                if not set(reaction.stoichiometric_species_coefficients) <= species_ids:
                    raise ValueError("electrode stoichiometry references a species without a finite reservoir")
                charge_delta = math.fsum(charges[key] * value for key, value in reaction.stoichiometric_species_coefficients.items())
                if not math.isclose(charge_delta, reaction.electron_count, rel_tol=1e-10, abs_tol=1e-10):
                    raise ValueError("reaction aqueous charge change must equal electron count in anodic direction")
                elements = set(branch.metal_element_release_mol_per_extent) | set().union(*(
                    set(formulas[key]) for key in reaction.stoichiometric_species_coefficients
                ))
                for element in elements:
                    aqueous = math.fsum(value * formulas[key].get(element, 0.0)
                                        for key, value in reaction.stoichiometric_species_coefficients.items())
                    released = branch.metal_element_release_mol_per_extent.get(element, 0.0)
                    if not math.isclose(aqueous, released, rel_tol=1e-10, abs_tol=1e-10):
                        raise ValueError(f"reaction element balance does not close for {element}")
        return self


def _at_potential(interval: WetCo2LumpedElectrochemicalInterval, potential: float,
                  concentrations: dict[str, float], wall_inventory: dict[str, float],
                  transfer_rate: dict[str, float], area: float, dt: float) -> tuple[float, dict, dict]:
    raw = {}
    for row in interval.reactions:
        result = electrode_reaction_flux(row.kinetics, potential)
        if result.get("status") != "computed":
            raise ValueError("a Butler-Volmer branch left its caller calibration support")
        raw[row.kinetics.reaction_id] = result
    branch_demand: dict[tuple[str, str, str], float] = {}
    for row in interval.reactions:
        reaction = row.kinetics
        result = raw[reaction.reaction_id]
        anodic_extent = result["gross_anodic_current_density_A_m2"] / (reaction.electron_count * FARADAY_C_MOL)
        cathodic_extent = result["gross_cathodic_current_density_A_m2"] / (reaction.electron_count * FARADAY_C_MOL)
        for species_id, coefficient in reaction.stoichiometric_species_coefficients.items():
            if coefficient < 0.0:
                branch_demand[(reaction.reaction_id, "anodic", species_id)] = abs(coefficient) * anodic_extent
            elif coefficient > 0.0:
                branch_demand[(reaction.reaction_id, "cathodic", species_id)] = coefficient * cathodic_extent
    total_demand: dict[tuple[str, str], float] = {}
    for (reaction_id, branch_name, species_id), demand in branch_demand.items():
        key = (branch_name, species_id)
        total_demand[key] = total_demand.get(key, 0.0) + demand
    available_rate = {}
    for species_id in wall_inventory:
        # The transient inventory can be consumed from existing wall stock; inward transfer adds to that stock.
        available_rate[species_id] = max(0.0, wall_inventory[species_id] / (area * dt))
    factors = {}
    for key, demand in total_demand.items():
        branch_name, species_id = key
        factors[key] = 1.0 if demand <= available_rate[species_id] or demand == 0.0 else available_rate[species_id] / demand
    adjusted = {}
    for row in interval.reactions:
        reaction = row.kinetics
        raw_row = raw[reaction.reaction_id]
        anodic_factor = min((factors.get(("anodic", sid), 1.0)
                             for sid, coefficient in reaction.stoichiometric_species_coefficients.items()
                             if coefficient < 0.0), default=1.0)
        cathodic_factor = min((factors.get(("cathodic", sid), 1.0)
                               for sid, coefficient in reaction.stoichiometric_species_coefficients.items()
                               if coefficient > 0.0), default=1.0)
        anodic_current = raw_row["gross_anodic_current_density_A_m2"] * anodic_factor
        cathodic_current = raw_row["gross_cathodic_current_density_A_m2"] * cathodic_factor
        net_current = anodic_current - cathodic_current
        signed_extent = net_current / (reaction.electron_count * FARADAY_C_MOL)
        species_flux = {species_id: coefficient * signed_extent
                        for species_id, coefficient in reaction.stoichiometric_species_coefficients.items()}
        adjusted[reaction.reaction_id] = {
            "signed_current_density_A_m2": net_current,
            "anodic_current_density_A_m2": anodic_current,
            "cathodic_current_density_A_m2": cathodic_current,
            "signed_extent_mol_m2_s": signed_extent,
            "anodic_supply_factor": anodic_factor,
            "cathodic_supply_factor": cathodic_factor,
            "species_flux_mol_m2_s": species_flux,
            "metal_element_release_mol_m2_s": {
                element: amount * signed_extent
                for element, amount in row.metal_element_release_mol_per_extent.items()
            },
        }
    current = math.fsum(row["signed_current_density_A_m2"] for row in adjusted.values())
    return current, adjusted, {"branch_species_demand_mol_m2_s": {f"{branch}|{species}": value for (branch, species), value in total_demand.items()},
                               "available_wall_supply_mol_m2_s": available_rate}


def evaluate_wet_co2_finite_inventory_electrode_mixed_potential(
    request: WetCo2FiniteInventoryElectrodeMixedPotential,
) -> Calculation:
    """Solve interval mixed potentials while finite liquid species inventories evolve."""
    geometry_rows = request.geometry_result.values["history"]
    geometry_digest = canonical_digest(request.geometry_result.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry_result.values.get("asset_id"),
        "location_id": request.geometry_result.values.get("location_id"),
        "model_id": MODEL_ID,
        "geometry_result_sha256": geometry_digest,
        "transfer_capacity_result_sha256": {
            key: canonical_digest(value.model_dump(mode="json"))
            for key, value in request.transfer_capacity_results.items()
        },
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "source_ids": [TRANSFER_SOURCE_ID, GEOMETRY_SOURCE_ID, KINETICS_SOURCE_ID,
                       INVENTORY_SOURCE_ID, EXCHANGE_SOURCE_ID, METHOD_SOURCE_ID],
    }
    missing = [name for name in (
        "finite_reservoir_and_current_area_reviewed", "reaction_formula_charge_and_direction_reviewed",
        "well_mixed_bulk_and_wall_compartments_reviewed",
    ) if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"reason": "finite_electrode_coupling_review_required", "missing_reviews": missing})
    species = {row.species_id: row for row in request.species}
    bulk = {row.species_id: row.bulk_inventory_mol for row in request.initial_inventories}
    wall = {row.species_id: row.wall_inventory_mol for row in request.initial_inventories}
    initial_total = {key: bulk[key] + wall[key] for key in species}
    initial_state = []
    interval_rows = []
    current_ledger = {key: 0.0 for key in species}
    cumulative_ext_bulk = {key: 0.0 for key in species}
    cumulative_ext_wall = {key: 0.0 for key in species}
    cumulative_transfer = {key: 0.0 for key in species}
    cumulative_reaction = {key: 0.0 for key in species}
    area = []
    for row in geometry_rows:
        area.append(float(row["bore_wetted_perimeter_m"]) * float(request.geometry_result.values["segment_length_m"]))
    for index, interval in enumerate(request.intervals):
        dt = interval.end_time_s - interval.start_time_s
        geometry_area = area[index]
        if not math.isfinite(geometry_area) or geometry_area <= 0.0:
            return Calculation(status="out_of_scope", values=base | {"reason": "electrode_area_outside_finite_support", "failed_interval_index": index})
        volume = request.volume_history[index]
        concentrations_bulk = {key: bulk[key] / volume.bulk_volume_m3 for key in species}
        concentrations_wall = {key: wall[key] / volume.wall_volume_m3 for key in species}
        exchange_rows = {(row.species_id): row for row in request.external_exchanges
                         if row.start_time_s == interval.start_time_s and row.end_time_s == interval.end_time_s}
        transfer_rates = {}
        for species_id, transfer_result in request.transfer_capacity_results.items():
            conductance = float(transfer_result.values["history"][index]["segment_transfer_conductance_m3_s"])
            transfer_rates[species_id] = conductance * (concentrations_bulk[species_id] - concentrations_wall[species_id])
        # Pre-electrode wall stock after external changes and interval transfer defines a hard maximum sink budget.
        pre_reaction_wall = {}
        for key in species:
            ext = exchange_rows[key]
            pre_reaction_wall[key] = wall[key] + ext.wall_inventory_change_mol + transfer_rates[key] * dt
            bulk_candidate = bulk[key] + ext.bulk_inventory_change_mol - transfer_rates[key] * dt
            if pre_reaction_wall[key] < -request.inventory_absolute_tolerance_mol or bulk_candidate < -request.inventory_absolute_tolerance_mol:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "bulk_or_wall_inventory_depleted_before_electrode_closure",
                    "failed_interval_index": index,
                    "species_id": key,
                    "bulk_inventory_candidate_mol": bulk_candidate,
                    "wall_inventory_candidate_mol": pre_reaction_wall[key],
                    "completed_prefix_interval_count": len(interval_rows),
                })
            pre_reaction_wall[key] = max(0.0, pre_reaction_wall[key])
        low = max(row.kinetics.equilibrium_potential_V + row.kinetics.minimum_overpotential_V
                  for row in interval.reactions)
        high = min(row.kinetics.equilibrium_potential_V + row.kinetics.maximum_overpotential_V
                   for row in interval.reactions)

        def evaluate_potential(potential: float):
            return _at_potential(interval, potential, concentrations_wall, pre_reaction_wall,
                                 transfer_rates, geometry_area, dt)

        try:
            low_current = evaluate_potential(low)[0]
            high_current = evaluate_potential(high)[0]
            if low_current == 0.0:
                potential = low
            elif high_current == 0.0:
                potential = high
            elif low_current * high_current > 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "no_zero_current_potential_in_common_caller_calibration_interval",
                    "failed_interval_index": index,
                    "completed_prefix_interval_count": len(interval_rows),
                    "low_current_density_A_m2": low_current,
                    "high_current_density_A_m2": high_current,
                })
            else:
                left, right = low, high
                potential = 0.5 * (left + right)
                for _iteration in range(request.maximum_bisection_iterations):
                    potential = 0.5 * (left + right)
                    current, _, _ = evaluate_potential(potential)
                    if abs(current) <= request.current_absolute_tolerance_A_m2:
                        break
                    if low_current * current > 0.0:
                        left = potential
                        low_current = current
                    else:
                        right = potential
                        high_current = current
                else:
                    return Calculation(status="out_of_scope", values=base | {
                        "reason": "mixed_potential_bisection_iteration_budget_exhausted",
                        "failed_interval_index": index,
                        "completed_prefix_interval_count": len(interval_rows),
                    })
            total_current, reaction_rows, supply = evaluate_potential(potential)
        except (ValueError, ArithmeticError, OverflowError, KeyError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_inventory_electrode_state_left_supported_domain",
                "failed_interval_index": index,
                "completed_prefix_interval_count": len(interval_rows),
                "detail": str(exc),
            })
        reaction_change = {key: 0.0 for key in species}
        element_release = {}
        for row in interval.reactions:
            reaction = row.kinetics
            result = reaction_rows[reaction.reaction_id]
            for species_id, flux in result["species_flux_mol_m2_s"].items():
                reaction_change[species_id] += flux * geometry_area * dt
            for element_id, flux in result["metal_element_release_mol_m2_s"].items():
                element_release[element_id] = element_release.get(element_id, 0.0) + flux * geometry_area * dt
        next_bulk, next_wall, closure_rows = {}, {}, {}
        for key in species:
            ext = exchange_rows[key]
            transfer_amount = transfer_rates[key] * dt
            next_bulk[key] = bulk[key] + ext.bulk_inventory_change_mol - transfer_amount
            next_wall[key] = wall[key] + ext.wall_inventory_change_mol + transfer_amount + reaction_change[key]
            if next_bulk[key] < -request.inventory_absolute_tolerance_mol or next_wall[key] < -request.inventory_absolute_tolerance_mol:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "electrode_reaction_depletes_finite_species_inventory",
                    "failed_interval_index": index,
                    "species_id": key,
                    "bulk_inventory_candidate_mol": next_bulk[key],
                    "wall_inventory_candidate_mol": next_wall[key],
                    "completed_prefix_interval_count": len(interval_rows),
                })
            next_bulk[key] = max(0.0, next_bulk[key])
            next_wall[key] = max(0.0, next_wall[key])
            external_total = ext.bulk_inventory_change_mol + ext.wall_inventory_change_mol
            total_change = next_bulk[key] + next_wall[key] - bulk[key] - wall[key]
            residual = total_change - external_total - reaction_change[key]
            scale = max(abs(next_bulk[key] + next_wall[key]), abs(bulk[key] + wall[key]),
                        abs(external_total), abs(reaction_change[key]), 1e-30)
            allowed = request.inventory_absolute_tolerance_mol + request.inventory_relative_tolerance * scale
            if abs(residual) > allowed:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "finite_species_transfer_reaction_inventory_closure_failed",
                    "failed_interval_index": index,
                    "species_id": key,
                    "closure_residual_mol": residual,
                    "allowed_residual_mol": allowed,
                    "completed_prefix_interval_count": len(interval_rows),
                })
            closure_rows[key] = {
                "bulk_inventory_start_mol": bulk[key],
                "wall_inventory_start_mol": wall[key],
                "bulk_inventory_end_mol": next_bulk[key],
                "wall_inventory_end_mol": next_wall[key],
                "bulk_concentration_start_mol_m3": concentrations_bulk[key],
                "wall_concentration_start_mol_m3": concentrations_wall[key],
                "transfer_mol": transfer_amount,
                "external_bulk_change_mol": ext.bulk_inventory_change_mol,
                "external_wall_change_mol": ext.wall_inventory_change_mol,
                "electrode_reaction_change_mol": reaction_change[key],
                "inventory_closure_residual_mol": residual,
            }
            current_ledger[key] += total_change
            cumulative_ext_bulk[key] += ext.bulk_inventory_change_mol
            cumulative_ext_wall[key] += ext.wall_inventory_change_mol
            cumulative_transfer[key] += transfer_amount
            cumulative_reaction[key] += reaction_change[key]
        interval_rows.append({
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": dt,
            "metal_minus_solution_mixed_potential_V": potential,
            "net_current_density_A_m2": total_current,
            "segment_inner_wetted_area_m2": geometry_area,
            "reaction_branches": reaction_rows,
            "species_branch_supply_limits": supply,
            "species_inventory_closure": closure_rows,
            "metal_element_release_mol_by_element": element_release,
            "reaction_and_transfer_sign_convention": "anodic reaction stoichiometry follows caller coefficients; liquid transfer positive bulk_to_wall",
        })
        bulk, wall = next_bulk, next_wall
    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(interval_rows),
        "final_bulk_inventory_mol_by_species": bulk,
        "final_wall_inventory_mol_by_species": wall,
        "cumulative_bulk_to_wall_transfer_mol_by_species": cumulative_transfer,
        "cumulative_electrode_reaction_change_mol_by_species": cumulative_reaction,
        "cumulative_external_bulk_change_mol_by_species": cumulative_ext_bulk,
        "cumulative_external_wall_change_mol_by_species": cumulative_ext_wall,
        "history": interval_rows,
        "limitations": [
            "A well-mixed finite bulk compartment and a well-mixed finite wall-liquid compartment represent each species; radial concentration profiles are not resolved.",
            "The common potential is solved independently on each exact interval using caller-calibrated Butler-Volmer branches; parameters are held constant over that interval.",
            "The branch supply cap uses finite wall inventory after caller exchange and liquid transfer; it is an interval-averaged stock limit, not a diffusion-layer PDE.",
            "The model couples liquid transfer, electrode current and finite inventories but does not include scale-layer diffusion/reaction, aqueous speciation, activity, gas chemistry, or scale growth/adhesion.",
            "All fluid, geometry, stoichiometry, electrode calibration and external inventory changes are caller-owned; no corrosion qualification or life prediction follows.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2FiniteInventoryElectrodeMixedPotential,
        evaluator=evaluate_wet_co2_finite_inventory_electrode_mixed_potential,
        units={
            "history[].metal_minus_solution_mixed_potential_V": "V",
            "history[].net_current_density_A_m2": "A/m^2",
            "history[].segment_inner_wetted_area_m2": "m^2",
            "history[].species_inventory_closure.*.transfer_mol": "mol",
            "history[].species_inventory_closure.*.electrode_reaction_change_mol": "mol",
            "history[].metal_element_release_mol_by_element.*": "mol",
        },
        assumptions=(
            "The caller defines a common calibrated electrode potential interval at every exact geometry interval.",
            "Branch currents are limited by species-resolved finite wall stock and are solved at zero net current.",
            "Per-species bulk/wall inventory updates include segment transfer, caller external exchange and electrode reaction stoichiometry.",
        ),
        source_ids=(TRANSFER_SOURCE_ID, GEOMETRY_SOURCE_ID, KINETICS_SOURCE_ID,
                    INVENTORY_SOURCE_ID, EXCHANGE_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]



