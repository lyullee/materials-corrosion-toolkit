"""Bounded gas-film water condensation/evaporation and wall-film inventory history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_gas_film_condensation_transfer_history"
TRANSFER_SOURCE_ID = "caller_wet_co2_gas_film_water_transfer_parameters"
SATURATION_SOURCE_ID = "caller_wet_co2_wall_water_saturation_fugacity"
ALGORITHM_SOURCE_ID = "finite_gas_film_fugacity_driven_condensation_inventory"
WATER_MOLAR_MASS_KG_MOL = 0.01801528
MAX_INTERVALS = 100_000


class WetCo2GasFilmCondensationInterval(Contract):
    """One piecewise-constant local water-transfer state over an exact interval."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    bulk_water_vapor_fugacity_Pa: float = Field(ge=0)
    wall_saturation_water_fugacity_Pa: float = Field(gt=0)
    gas_film_molar_transfer_coefficient_mol_m2_s_Pa: float = Field(ge=0)
    liquid_water_density_kg_m3: float = Field(gt=0)
    transfer_provider_id: str = Field(min_length=1)
    transfer_provider_revision: str = Field(min_length=1)
    transfer_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transfer_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    saturation_provider_id: str = Field(min_length=1)
    saturation_provider_revision: str = Field(min_length=1)
    saturation_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    saturation_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    density_record_id: str = Field(min_length=1)
    density_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    interval_state_basis_and_units_reviewed: bool

    @model_validator(mode="after")
    def finite_and_provenance(self):
        values = (
            self.start_time_s,
            self.end_time_s,
            self.bulk_water_vapor_fugacity_Pa,
            self.wall_saturation_water_fugacity_Pa,
            self.gas_film_molar_transfer_coefficient_mol_m2_s_Pa,
            self.liquid_water_density_kg_m3,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("all interval inputs must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must be later than its start")
        ids = {item.source_id for item in self.evidence}
        if not {self.transfer_provider_id, self.saturation_provider_id, self.density_record_id}.issubset(ids):
            raise ValueError("Evidence must identify transfer, saturation, and density inputs")
        digest_pairs = {
            (item.source_id, item.sha256) for item in self.evidence
        }
        if (self.density_record_id, self.density_record_sha256) not in digest_pairs:
            raise ValueError("density record digest must match its Evidence")
        return self


class WetCo2GasFilmCondensationHistoryRequest(Contract):
    """Local fixed-patch film inventory driven by caller gas/wall fugacity states."""

    schema_version: Literal["matintegrity.wet_co2_gas_film_condensation_transfer_history.v1"] = (
        "matintegrity.wet_co2_gas_film_condensation_transfer_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    wall_patch_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    initial_water_areal_inventory_kg_m2: float = Field(ge=0)
    intervals: tuple[WetCo2GasFilmCondensationInterval, ...] = Field(min_length=1, max_length=MAX_INTERVALS)
    exact_gas_and_wall_state_alignment_reviewed: bool
    fugacity_reference_and_gas_film_coefficient_units_reviewed: bool
    fixed_patch_no_lateral_exchange_and_uniform_film_reviewed: bool
    pure_water_saturation_applicability_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def ordered_history(self):
        if not math.isfinite(self.initial_water_areal_inventory_kg_m2):
            raise ValueError("initial inventory must be finite")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at time zero")
        if any(left.end_time_s != right.start_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("intervals must be contiguous exact knots")
        return self


def evaluate_wet_co2_gas_film_condensation_history(
    request: WetCo2GasFilmCondensationHistoryRequest,
) -> Calculation:
    """Integrate signed fugacity-driven water transfer, limiting evaporation at dryout."""
    request_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "wall_patch_id": request.wall_patch_id,
        "condition_id": request.condition_id,
        "input_sha256": request_sha,
        "initial_water_areal_inventory_kg_m2": request.initial_water_areal_inventory_kg_m2,
        "water_molar_mass_kg_mol": WATER_MOLAR_MASS_KG_MOL,
    }
    review_fields = (
        "exact_gas_and_wall_state_alignment_reviewed",
        "fugacity_reference_and_gas_film_coefficient_units_reviewed",
        "fixed_patch_no_lateral_exchange_and_uniform_film_reviewed",
        "pure_water_saturation_applicability_reviewed",
        "calculation_use_authorized",
    )
    missing = [name for name in review_fields if not getattr(request, name)]
    missing.extend(
        f"interval[{i}].interval_state_basis_and_units_reviewed"
        for i, interval in enumerate(request.intervals)
        if not interval.interval_state_basis_and_units_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "inventory_history": [],
            "interval_ledger": [],
        })

    inventory = request.initial_water_areal_inventory_kg_m2
    history = [{
        "time_s": 0.0,
        "water_areal_inventory_kg_m2": inventory,
        "uniform_equivalent_film_thickness_m": inventory / request.intervals[0].liquid_water_density_kg_m3,
        "origin": "caller_initial_inventory",
    }]
    ledger: list[dict] = []
    total_condensed = 0.0
    total_evaporated = 0.0
    unmet_evaporation = 0.0

    for index, interval in enumerate(request.intervals):
        dt = interval.end_time_s - interval.start_time_s
        fugacity_difference = interval.bulk_water_vapor_fugacity_Pa - interval.wall_saturation_water_fugacity_Pa
        requested_molar_flux = interval.gas_film_molar_transfer_coefficient_mol_m2_s_Pa * fugacity_difference
        requested_mass_flux = requested_molar_flux * WATER_MOLAR_MASS_KG_MOL
        requested_mass_transfer = requested_mass_flux * dt
        if not all(math.isfinite(value) for value in (requested_molar_flux, requested_mass_flux, requested_mass_transfer)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "inventory_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "fugacity-driven transfer exceeds finite numeric support",
            })
        admitted_transfer = max(requested_mass_transfer, -inventory)
        unmet = max(0.0, -requested_mass_transfer - inventory)
        inventory_end = inventory + admitted_transfer
        density = interval.liquid_water_density_kg_m3
        thickness_start = inventory / density
        thickness_end = inventory_end / density
        if not all(math.isfinite(value) for value in (inventory_end, thickness_start, thickness_end)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "inventory_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "film inventory or thickness exceeds finite numeric support",
            })
        condensed = max(0.0, admitted_transfer)
        evaporated = max(0.0, -admitted_transfer)
        total_condensed += condensed
        total_evaporated += evaporated
        unmet_evaporation += unmet
        residual = inventory_end - inventory - admitted_transfer
        ledger.append({
            "interval_index": index,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": dt,
            "bulk_water_vapor_fugacity_Pa": interval.bulk_water_vapor_fugacity_Pa,
            "wall_saturation_water_fugacity_Pa": interval.wall_saturation_water_fugacity_Pa,
            "fugacity_driving_force_Pa": fugacity_difference,
            "requested_molar_flux_mol_m2_s": requested_molar_flux,
            "requested_mass_flux_kg_m2_s": requested_mass_flux,
            "requested_mass_transfer_kg_m2": requested_mass_transfer,
            "admitted_mass_transfer_kg_m2": admitted_transfer,
            "condensation_added_kg_m2": condensed,
            "evaporation_removed_kg_m2": evaporated,
            "evaporation_unmet_after_dryout_kg_m2": unmet,
            "inventory_start_kg_m2": inventory,
            "inventory_end_kg_m2": inventory_end,
            "equivalent_film_thickness_start_m": thickness_start,
            "equivalent_film_thickness_end_m": thickness_end,
            "inventory_balance_residual_kg_m2": residual,
            "transfer_provider_id": interval.transfer_provider_id,
            "transfer_provider_revision": interval.transfer_provider_revision,
            "transfer_configuration_sha256": interval.transfer_configuration_sha256,
            "transfer_result_sha256": interval.transfer_result_sha256,
            "saturation_provider_id": interval.saturation_provider_id,
            "saturation_provider_revision": interval.saturation_provider_revision,
            "saturation_configuration_sha256": interval.saturation_configuration_sha256,
            "saturation_result_sha256": interval.saturation_result_sha256,
            "density_record_id": interval.density_record_id,
            "density_record_sha256": interval.density_record_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
            "evidence": [row.model_dump(mode="json") for row in interval.evidence],
        })
        inventory = inventory_end
        history.append({
            "time_s": interval.end_time_s,
            "water_areal_inventory_kg_m2": inventory,
            "uniform_equivalent_film_thickness_m": thickness_end,
            "origin": "integrated_caller_gas_film_fugacity_transfer",
        })

    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(ledger),
        "final_water_areal_inventory_kg_m2": inventory,
        "final_uniform_equivalent_film_thickness_m": history[-1]["uniform_equivalent_film_thickness_m"],
        "cumulative_condensation_kg_m2": total_condensed,
        "cumulative_evaporation_kg_m2": total_evaporated,
        "cumulative_evaporation_unmet_after_dryout_kg_m2": unmet_evaporation,
        "inventory_history": history,
        "interval_ledger": ledger,
        "limitations": [
            "The gas-film coefficient and both fugacity states are caller supplied; no hydrodynamic or thermodynamic provider is executed.",
            "Wall saturation is represented by caller pure-water equilibrium fugacity; brine or MEG water activity is not included.",
            "The gas is an undepleted reservoir over each interval; wall temperature and transfer conditions are piecewise constant.",
            "No latent-heat balance, wall conduction, droplet nucleation, drainage, lateral film flow, corrosion chemistry, or acceptance decision is computed.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2GasFilmCondensationHistoryRequest,
        evaluator=evaluate_wet_co2_gas_film_condensation_history,
        units={
            "final_water_areal_inventory_kg_m2": "kg/m^2",
            "final_uniform_equivalent_film_thickness_m": "m",
            "cumulative_condensation_kg_m2": "kg/m^2",
            "cumulative_evaporation_kg_m2": "kg/m^2",
            "cumulative_evaporation_unmet_after_dryout_kg_m2": "kg/m^2",
            "interval_ledger[].requested_molar_flux_mol_m2_s": "mol/(m^2*s)",
            "interval_ledger[].requested_mass_flux_kg_m2_s": "kg/(m^2*s)",
            "interval_ledger[].inventory_balance_residual_kg_m2": "kg/m^2",
        },
        assumptions=(
            "Gas-film molar flux follows a caller-supplied linear fugacity driving-force law on each interval.",
            "Condensation adds to a fixed wall-patch water areal inventory; evaporation cannot remove more liquid than is present.",
            "Equivalent film thickness uses caller liquid density and assumes a spatially uniform film on the declared patch.",
        ),
        source_ids=(TRANSFER_SOURCE_ID, SATURATION_SOURCE_ID, ALGORITHM_SOURCE_ID),
    )]
