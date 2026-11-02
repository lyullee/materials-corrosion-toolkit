from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_cylindrical_finite_liquid_transfer_inventory"
TRANSFER_SOURCE_ID = "caller_cylindrical_liquid_transfer_capacity_history"
GEOMETRY_SOURCE_ID = "caller_cylindrical_geometry_history"
HYDRAULICS_SOURCE_ID = "caller_cylindrical_hydraulics_history"
CONCENTRATION_SOURCE_ID = "caller_bulk_wall_liquid_concentration_records"
EXCHANGE_SOURCE_ID = "caller_bulk_wall_external_inventory_exchange_records"
METHOD_SOURCE_ID = "finite_two_compartment_liquid_transfer_balance"


class WetCo2CylindricalLiquidConcentrationKnot(Contract):
    time_s: Nonnegative
    species_id: str = Field(min_length=1, max_length=160)
    bulk_concentration_mol_m3: Nonnegative
    wall_concentration_mol_m3: Nonnegative
    bulk_liquid_volume_m3: Positive
    wall_liquid_volume_m3: Positive
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_concentration_state(self):
        payload = {
            "time_s": self.time_s,
            "species_id": self.species_id,
            "bulk_concentration_mol_m3": self.bulk_concentration_mol_m3,
            "wall_concentration_mol_m3": self.wall_concentration_mol_m3,
            "bulk_liquid_volume_m3": self.bulk_liquid_volume_m3,
            "wall_liquid_volume_m3": self.wall_liquid_volume_m3,
        }
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("concentration record digest must bind exact knot, concentrations and compartment volumes")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each bulk/wall concentration state")
        return self


class WetCo2CylindricalExternalLiquidExchange(Contract):
    start_time_s: Nonnegative
    end_time_s: Positive
    bulk_inventory_change_mol: float
    wall_inventory_change_mol: float
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_external_exchange(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("external inventory exchange interval must have positive duration")
        if not all(math.isfinite(value) for value in (self.bulk_inventory_change_mol, self.wall_inventory_change_mol)):
            raise ValueError("external inventory changes must be finite signed quantities")
        payload = {
            "start_time_s": self.start_time_s,
            "end_time_s": self.end_time_s,
            "bulk_inventory_change_mol": self.bulk_inventory_change_mol,
            "wall_inventory_change_mol": self.wall_inventory_change_mol,
        }
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("external exchange digest must bind its interval and compartment changes")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each bulk/wall external exchange record")
        return self


class WetCo2CylindricalFiniteLiquidTransferInventory(Contract):
    """Convert segment transfer conductance to signed molar exchange and close finite liquid inventories."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_finite_liquid_transfer_inventory.v1"] = (
        "matintegrity.wet_co2_cylindrical_finite_liquid_transfer_inventory.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    species_id: str = Field(min_length=1, max_length=160)
    geometry_result: Calculation
    hydraulics_result: Calculation
    transfer_capacity_result: Calculation
    concentration_history: tuple[WetCo2CylindricalLiquidConcentrationKnot, ...] = Field(min_length=2, max_length=5000)
    external_exchange_history: tuple[WetCo2CylindricalExternalLiquidExchange, ...] = Field(min_length=1, max_length=4999)
    absolute_inventory_tolerance_mol: Positive = 1e-12
    relative_inventory_tolerance: Positive = Field(default=1e-8, le=1e-2)

    @model_validator(mode="after")
    def bind_results_and_clocks(self):
        for result, model_id in (
            (self.geometry_result, "degradation.wet_co2_cylindrical_scale_geometry_history"),
            (self.hydraulics_result, "integration.wet_co2_cylindrical_steady_hydraulics"),
            (self.transfer_capacity_result, "integration.wet_co2_cylindrical_liquid_transfer_capacity_history"),
        ):
            if result.status != "computed" or result.values.get("model_id") != model_id:
                raise ValueError(f"computed upstream result from {model_id} is required")
        geometry_digest = canonical_digest(self.geometry_result.model_dump(mode="json"))
        if self.hydraulics_result.values.get("geometry_result_sha256") != geometry_digest:
            raise ValueError("hydraulic result must use the supplied exact geometry result")
        if self.transfer_capacity_result.values.get("geometry_result_sha256") != geometry_digest:
            raise ValueError("transfer-capacity result must use the supplied exact geometry result")
        if self.transfer_capacity_result.values.get("hydraulics_result_sha256") != canonical_digest(
            self.hydraulics_result.model_dump(mode="json")
        ):
            raise ValueError("transfer-capacity result must use the supplied exact hydraulics result")
        if self.transfer_capacity_result.values.get("species_id") != self.species_id:
            raise ValueError("transfer capacity and finite inventory species IDs must match")
        times = tuple(float(row["time_s"]) for row in self.geometry_result.values.get("history", []))
        if tuple(float(row["time_s"]) for row in self.hydraulics_result.values.get("history", [])) != times:
            raise ValueError("geometry and hydraulics knots must match exactly")
        if tuple(float(row["time_s"]) for row in self.transfer_capacity_result.values.get("history", [])) != times:
            raise ValueError("geometry and transfer-capacity knots must match exactly")
        if tuple(row.time_s for row in self.concentration_history) != times:
            raise ValueError("bulk/wall concentration records must match all geometry knots exactly")
        expected_intervals = tuple(zip(times[:-1], times[1:], strict=True))
        actual_intervals = tuple((row.start_time_s, row.end_time_s) for row in self.external_exchange_history)
        if actual_intervals != expected_intervals:
            raise ValueError("external exchange records must span every adjacent geometry-knot interval exactly")
        if any(row.species_id != self.species_id for row in self.concentration_history):
            raise ValueError("all finite-liquid concentration records must use the selected species ID")
        if self.geometry_result.values.get("assessment_id") != self.assessment_id:
            raise ValueError("geometry and finite-transfer assessment IDs must match")
        if self.hydraulics_result.values.get("assessment_id") != self.assessment_id or self.transfer_capacity_result.values.get("assessment_id") != self.assessment_id:
            raise ValueError("geometry and finite-transfer assessment IDs must match")
        if (self.hydraulics_result.values.get("asset_id") != self.geometry_result.values.get("asset_id")
                or self.transfer_capacity_result.values.get("asset_id") != self.geometry_result.values.get("asset_id")):
            raise ValueError("geometry, hydraulics and transfer-capacity asset scopes must match")
        return self


def evaluate_wet_co2_cylindrical_finite_liquid_transfer_inventory(
    request: WetCo2CylindricalFiniteLiquidTransferInventory,
) -> Calculation:
    """Integrate signed transfer and enforce finite inventory/closure at every exact knot."""
    geometry_digest = canonical_digest(request.geometry_result.model_dump(mode="json"))
    hydraulics_digest = canonical_digest(request.hydraulics_result.model_dump(mode="json"))
    transfer_digest = canonical_digest(request.transfer_capacity_result.model_dump(mode="json"))
    transfer_rows = request.transfer_capacity_result.values["history"]
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry_result.values.get("asset_id"),
        "location_id": request.geometry_result.values.get("location_id"),
        "model_id": MODEL_ID,
        "species_id": request.species_id,
        "geometry_result_sha256": geometry_digest,
        "hydraulics_result_sha256": hydraulics_digest,
        "transfer_capacity_result_sha256": transfer_digest,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "source_ids": [TRANSFER_SOURCE_ID, GEOMETRY_SOURCE_ID, HYDRAULICS_SOURCE_ID,
                       CONCENTRATION_SOURCE_ID, EXCHANGE_SOURCE_ID, METHOD_SOURCE_ID],
    }
    concentration = request.concentration_history
    exchange = request.external_exchange_history
    first = concentration[0]
    bulk_initial = first.bulk_concentration_mol_m3 * first.bulk_liquid_volume_m3
    wall_initial = first.wall_concentration_mol_m3 * first.wall_liquid_volume_m3
    bulk_inventory = bulk_initial
    wall_inventory = wall_initial
    cumulative_external_bulk = 0.0
    cumulative_external_wall = 0.0
    cumulative_transfer = 0.0
    rows = []
    total_initial = bulk_initial + wall_initial
    for index, (transfer, state) in enumerate(zip(transfer_rows, concentration, strict=True)):
        bulk_measured = state.bulk_concentration_mol_m3 * state.bulk_liquid_volume_m3
        wall_measured = state.wall_concentration_mol_m3 * state.wall_liquid_volume_m3
        bulk_at_knot = bulk_inventory
        wall_at_knot = wall_inventory
        residuals = {
            "bulk_residual_mol": bulk_inventory - bulk_measured,
            "wall_residual_mol": wall_inventory - wall_measured,
        }
        if index > 0:
            for key, residual in residuals.items():
                observed = bulk_measured if key.startswith("bulk") else wall_measured
                allowed = request.absolute_inventory_tolerance_mol + request.relative_inventory_tolerance * max(
                    abs(observed), abs(bulk_inventory if key.startswith("bulk") else wall_inventory)
                )
                if abs(residual) > allowed:
                    return Calculation(status="needs_data", values=base | {
                        "reason": "caller_concentration_history_does_not_match_finite_inventory_state",
                        "failed_knot_index": index,
                        "time_s": state.time_s,
                        "inventory_residuals_mol": residuals,
                        "allowed_residual_mol": allowed,
                        "completed_prefix_knot_count": len(rows),
                    })
        conductance = float(transfer["segment_transfer_conductance_m3_s"])
        driving = state.bulk_concentration_mol_m3 - state.wall_concentration_mol_m3
        transfer_rate = conductance * driving
        interval_amount = 0.0
        external_bulk = 0.0
        external_wall = 0.0
        if index < len(transfer_rows) - 1:
            interval = exchange[index]
            dt = interval.end_time_s - interval.start_time_s
            interval_amount = transfer_rate * dt
            external_bulk = interval.bulk_inventory_change_mol
            external_wall = interval.wall_inventory_change_mol
            next_bulk = bulk_inventory + external_bulk - interval_amount
            next_wall = wall_inventory + external_wall + interval_amount
            if not all(math.isfinite(value) for value in (interval_amount, next_bulk, next_wall)):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "finite_inventory_transfer_update_outside_numeric_support",
                    "failed_interval_index": index,
                    "completed_prefix_knot_count": len(rows),
                })
            if next_bulk < -request.absolute_inventory_tolerance_mol or next_wall < -request.absolute_inventory_tolerance_mol:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "finite_liquid_inventory_depleted_by_transfer_or_external_exchange",
                    "failed_interval_index": index,
                    "bulk_inventory_candidate_mol": next_bulk,
                    "wall_inventory_candidate_mol": next_wall,
                    "completed_prefix_knot_count": len(rows),
                })
            bulk_inventory = max(0.0, next_bulk)
            wall_inventory = max(0.0, next_wall)
            cumulative_external_bulk += external_bulk
            cumulative_external_wall += external_wall
            cumulative_transfer += interval_amount
        total_inventory = bulk_inventory + wall_inventory if index == len(transfer_rows) - 1 else next_bulk + next_wall
        closure = total_inventory - total_initial - cumulative_external_bulk - cumulative_external_wall
        closure_scale = max(abs(total_inventory), abs(total_initial),
                            abs(cumulative_external_bulk), abs(cumulative_external_wall), 1e-30)
        allowed_closure = request.absolute_inventory_tolerance_mol + request.relative_inventory_tolerance * closure_scale
        if abs(closure) > allowed_closure:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "bulk_wall_transfer_inventory_closure_exceeded_tolerance",
                "failed_knot_index": index,
                "closure_residual_mol": closure,
                "allowed_closure_residual_mol": allowed_closure,
                "completed_prefix_knot_count": len(rows),
            })
        rows.append({
            "time_s": state.time_s,
            "species_id": request.species_id,
            "bulk_concentration_mol_m3": state.bulk_concentration_mol_m3,
            "wall_concentration_mol_m3": state.wall_concentration_mol_m3,
            "bulk_liquid_volume_m3": state.bulk_liquid_volume_m3,
            "wall_liquid_volume_m3": state.wall_liquid_volume_m3,
            "segment_transfer_conductance_m3_s": conductance,
            "signed_bulk_to_wall_transfer_rate_mol_s": transfer_rate,
            "left_held_interval_transfer_mol": interval_amount,
            "external_bulk_inventory_change_mol": external_bulk,
            "external_wall_inventory_change_mol": external_wall,
            "bulk_inventory_at_knot_mol": bulk_at_knot,
            "wall_inventory_at_knot_mol": wall_at_knot,
            "bulk_inventory_after_interval_mol": (bulk_inventory if index == len(transfer_rows) - 1 else next_bulk),
            "wall_inventory_after_interval_mol": (wall_inventory if index == len(transfer_rows) - 1 else next_wall),

            "inventory_closure_residual_mol": closure,
            "concentration_state_residual_mol": residuals,
            "bulk_record_sha256": state.record_sha256,
            "external_exchange_record_sha256": exchange[index].record_sha256 if index < len(exchange) else None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "knot_count": len(rows),
        "initial_bulk_inventory_mol": bulk_initial,
        "initial_wall_inventory_mol": wall_initial,
        "cumulative_signed_bulk_to_wall_transfer_mol": cumulative_transfer,
        "cumulative_external_bulk_inventory_change_mol": cumulative_external_bulk,
        "cumulative_external_wall_inventory_change_mol": cumulative_external_wall,
        "final_bulk_inventory_mol": bulk_inventory,
        "final_wall_inventory_mol": wall_inventory,
        "history": rows,
        "transfer_sign_convention": "positive_bulk_to_wall",
        "integration": "left_held_conductance_and_concentration_difference_on_exact_knots.v1",
        "limitations": [
            "The model only converts the supplied segment transfer conductance and caller bulk/wall concentrations into a finite inventory exchange.",
            "No concentration is generated from chemistry, equilibrium, reaction, gas-liquid transfer or corrosion; caller external inventory changes account for all non-transfer sources/sinks.",
            "Bulk and wall compartments are each well mixed at caller-specified volumes; volume changes do not imply additional transfer or dilution terms beyond caller concentrations/exchange records.",
            "Transfer conductance and concentration difference are held at each left knot through the following interval.",
            "Depletion, knot-state inconsistency and mass-balance residual violations fail closed; no extrapolation occurs.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalFiniteLiquidTransferInventory,
        evaluator=evaluate_wet_co2_cylindrical_finite_liquid_transfer_inventory,
        units={
            "history[].bulk_concentration_mol_m3": "mol/m^3",
            "history[].wall_concentration_mol_m3": "mol/m^3",
            "history[].segment_transfer_conductance_m3_s": "m^3/s",
            "history[].signed_bulk_to_wall_transfer_rate_mol_s": "mol/s",
            "history[].left_held_interval_transfer_mol": "mol",
            "history[].bulk_inventory_mol": "mol",
            "history[].wall_inventory_mol": "mol",
            "history[].inventory_closure_residual_mol": "mol",
        },
        assumptions=(
            "The transfer exposure result supplies a whole-segment conductance on the cylindrical wetted-area basis.",
            "One well-mixed bulk reservoir and one well-mixed wall-liquid reservoir are tracked for a single declared species.",
            "Exact-knot caller concentrations, liquid volumes, and external inventory changes close the finite two-reservoir balance.",
        ),
        source_ids=(TRANSFER_SOURCE_ID, GEOMETRY_SOURCE_ID, HYDRAULICS_SOURCE_ID,
                    CONCENTRATION_SOURCE_ID, EXCHANGE_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]


