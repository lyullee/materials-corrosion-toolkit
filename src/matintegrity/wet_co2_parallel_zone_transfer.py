"""Aggregate wet-CO2 transfer across disjoint zones with distinct local states."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_parallel_zone_transfer"
SOURCE_ID = "caller_disjoint_wet_co2_transfer_zones"


class WetCo2ParallelTransferZone(Contract):
    """One disjoint wetted interface region with its own transfer state."""

    zone_id: str = Field(min_length=1)
    flow_region: Literal["stratified_layer", "slug_body", "slug_film", "annular_film", "other"]
    interfacial_area_m2: float = Field(gt=0)
    temperature_K: float = Field(gt=0)
    gas_co2_fugacity_Pa: float = Field(ge=0)
    liquid_co2star_concentration_mol_m3: float = Field(ge=0)
    henry_concentration_over_fugacity_mol_m3_Pa: float = Field(gt=0)
    gas_film_coefficient_mol_m2_s_Pa: float = Field(gt=0)
    liquid_film_coefficient_m_s: float = Field(gt=0)
    state_provider_id: str = Field(min_length=1)
    state_provider_revision: str = Field(min_length=1)
    state_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    state_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    local_zone_support_reviewed: bool

    @model_validator(mode="after")
    def finite_and_evidenced(self):
        numeric = (
            self.interfacial_area_m2, self.temperature_K, self.gas_co2_fugacity_Pa,
            self.liquid_co2star_concentration_mol_m3,
            self.henry_concentration_over_fugacity_mol_m3_Pa,
            self.gas_film_coefficient_mol_m2_s_Pa, self.liquid_film_coefficient_m_s,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("zone conditions and coefficients must be finite")
        if self.state_provider_id not in {row.source_id for row in self.evidence}:
            raise ValueError("zone Evidence must identify the state provider")
        return self


class WetCo2ParallelTransferRequest(Contract):
    """Sum local two-film fluxes over caller-declared disjoint wetted zones."""

    schema_version: Literal["matintegrity.wet_co2_parallel_zone_transfer.v1"] = (
        "matintegrity.wet_co2_parallel_zone_transfer.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    total_interfacial_area_m2: float = Field(gt=0)
    zones: tuple[WetCo2ParallelTransferZone, ...] = Field(min_length=1, max_length=1000)
    zone_areas_partition_one_interface_reviewed: bool
    local_states_and_coefficients_comparable_reviewed: bool
    no_cross_zone_exchange_or_shared_depletion_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def area_partition(self):
        if not math.isfinite(self.total_interfacial_area_m2):
            raise ValueError("total interface area must be finite")
        ids = [zone.zone_id for zone in self.zones]
        if len(set(ids)) != len(ids):
            raise ValueError("zone IDs must be unique")
        try:
            area_sum = math.fsum(zone.interfacial_area_m2 for zone in self.zones)
        except OverflowError as exc:
            raise ValueError("sum of zone areas exceeds finite numeric support") from exc
        if not math.isfinite(area_sum):
            raise ValueError("sum of zone areas exceeds finite numeric support")
        if not math.isclose(area_sum, self.total_interfacial_area_m2, rel_tol=1e-10, abs_tol=1e-14):
            raise ValueError("disjoint zone areas must sum to the declared total interface area")
        return self


def _overall_liquid_coefficient(gas_k: float, henry: float, liquid_k: float) -> float | None:
    log_gas_h = math.log(gas_k) + math.log(henry)
    log_ratio = math.log(liquid_k) - log_gas_h
    if log_ratio >= 0.0:
        log_result = log_gas_h - math.log1p(math.exp(-log_ratio))
    else:
        log_result = math.log(liquid_k) - math.log1p(math.exp(log_ratio))
    if log_result > math.log(sys.float_info.max):
        return None
    result = math.exp(log_result)
    return result if math.isfinite(result) and result > 0.0 else None


def evaluate_wet_co2_parallel_zone_transfer(request: WetCo2ParallelTransferRequest) -> Calculation:
    """Sum signed zone transfer rates without homogenizing local driving forces."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "input_sha256": input_sha,
        "total_interfacial_area_m2": request.total_interfacial_area_m2,
        "zone_count": len(request.zones),
    }
    reviews = (
        "zone_areas_partition_one_interface_reviewed",
        "local_states_and_coefficients_comparable_reviewed",
        "no_cross_zone_exchange_or_shared_depletion_reviewed",
        "calculation_use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    missing.extend(
        f"zone[{zone.zone_id}].local_zone_support_reviewed"
        for zone in request.zones if not zone.local_zone_support_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing, "zone_ledger": [],
        })

    ledger: list[dict] = []
    rates: list[float] = []
    for zone in request.zones:
        henry = zone.henry_concentration_over_fugacity_mol_m3_Pa
        overall_k = _overall_liquid_coefficient(
            zone.gas_film_coefficient_mol_m2_s_Pa,
            henry,
            zone.liquid_film_coefficient_m_s,
        )
        equilibrium_c = henry * zone.gas_co2_fugacity_Pa
        if overall_k is None or not math.isfinite(equilibrium_c):
            return Calculation(status="out_of_scope", values=base | {
                "zone_ledger": ledger, "failed_zone_id": zone.zone_id,
                "failure_reason": "zone equilibrium or overall coefficient outside finite support",
            })
        driving_force = equilibrium_c - zone.liquid_co2star_concentration_mol_m3
        flux = overall_k * driving_force
        rate = zone.interfacial_area_m2 * flux
        if not all(math.isfinite(value) for value in (driving_force, flux, rate)):
            return Calculation(status="out_of_scope", values=base | {
                "zone_ledger": ledger, "failed_zone_id": zone.zone_id,
                "failure_reason": "zone flux or transfer rate exceeds finite support",
            })
        rates.append(rate)
        ledger.append({
            "zone_id": zone.zone_id,
            "flow_region": zone.flow_region,
            "interfacial_area_m2": zone.interfacial_area_m2,
            "area_fraction": zone.interfacial_area_m2 / request.total_interfacial_area_m2,
            "temperature_K": zone.temperature_K,
            "gas_co2_fugacity_Pa": zone.gas_co2_fugacity_Pa,
            "liquid_co2star_concentration_mol_m3": zone.liquid_co2star_concentration_mol_m3,
            "equilibrium_co2star_concentration_mol_m3": equilibrium_c,
            "overall_liquid_basis_coefficient_m_s": overall_k,
            "signed_gas_to_liquid_flux_mol_m2_s": flux,
            "signed_transfer_rate_mol_s": rate,
            "state_provider_id": zone.state_provider_id,
            "state_provider_revision": zone.state_provider_revision,
            "state_configuration_sha256": zone.state_configuration_sha256,
            "state_result_sha256": zone.state_result_sha256,
            "zone_input_sha256": canonical_digest(zone.model_dump(mode="json")),
            "evidence": [row.model_dump(mode="json") for row in zone.evidence],
        })
    try:
        total_rate = math.fsum(rates)
    except OverflowError:
        return Calculation(status="out_of_scope", values=base | {
            "zone_ledger": ledger,
            "failure_reason": "sum of parallel zone transfer rates exceeds finite support",
        })
    average_flux = total_rate / request.total_interfacial_area_m2
    if not math.isfinite(total_rate) or not math.isfinite(average_flux):
        return Calculation(status="out_of_scope", values=base | {
            "zone_ledger": ledger,
            "failure_reason": "sum of parallel zone transfer rates exceeds finite support",
        })
    return Calculation(values=base | {
        "status": "computed",
        "zone_ledger": ledger,
        "signed_total_gas_to_liquid_transfer_rate_mol_s": total_rate,
        "area_weighted_signed_gas_to_liquid_flux_mol_m2_s": average_flux,
        "transfer_sign_convention": "positive denotes net transfer from gas into liquid; individual zones may have opposite signs",
        "aggregation": "sum of independent local flux times disjoint interfacial area",
        "interpretation_boundary": "Steady instantaneous parallel-zone mass transfer under caller-declared local states. It does not update coupled zone inventories or chemistry.",
        "not_inferred": [
            "flow-regime transitions, area fractions or local wetting",
            "cross-zone liquid/gas mixing and shared-reservoir depletion",
            "time integration, carbonate speciation, reaction or surface-scale feedback",
            "corrosion rate, localized attack, metal loss, life or risk",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2ParallelTransferRequest,
        evaluator=evaluate_wet_co2_parallel_zone_transfer,
        units={
            "total_interfacial_area_m2": "m2",
            "signed_total_gas_to_liquid_transfer_rate_mol_s": "mol/s",
            "area_weighted_signed_gas_to_liquid_flux_mol_m2_s": "mol/(m2 s)",
            "zone_ledger[].signed_transfer_rate_mol_s": "mol/s",
            "zone_ledger[].signed_gas_to_liquid_flux_mol_m2_s": "mol/(m2 s)",
        },
        assumptions=(
            "Each caller-declared interface zone has one representative gas and liquid state and local two-film coefficients.",
            "Zone areas form a disjoint partition of the declared total interface area.",
            "Zones do not exchange mass or deplete shared reservoirs during this instantaneous calculation.",
            "Local states and coefficients are simultaneously comparable and applicable to the zone conditions.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
