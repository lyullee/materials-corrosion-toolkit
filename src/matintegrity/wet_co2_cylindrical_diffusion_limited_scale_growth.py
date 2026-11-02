from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_cylindrical_diffusion_limited_scale_growth"
SATURATION_SOURCE_ID = "caller_wet_co2_wall_saturation_scale_kinetics_result"
TRANSPORT_SOURCE_ID = "caller_wet_co2_cylindrical_multilayer_transport_result"
GEOMETRY_SOURCE_ID = "caller_wet_co2_cylindrical_geometry_result"
STOICHIOMETRY_SOURCE_ID = "caller_balanced_solid_precipitation_consumption_stoichiometry"
FARADAY_C_MOL = 96485.33212


class WetCo2DiffusionLimitedSolidReactant(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    moles_consumed_per_mole_solid: Positive


class WetCo2DiffusionLimitedBulkSpecies(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    concentration_mol_m3: Nonnegative


class WetCo2DiffusionLimitedBulkKnot(Contract):
    time_s: Nonnegative
    concentrations: tuple[WetCo2DiffusionLimitedBulkSpecies, ...] = Field(min_length=1, max_length=64)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_bulk_record(self):
        payload = {"time_s": self.time_s,
                   "concentrations": [row.model_dump(mode="json") for row in self.concentrations]}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("bulk concentration digest must bind exact time and species records")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each bulk concentration record")
        ids = [row.species_id for row in self.concentrations]
        if len(ids) != len(set(ids)):
            raise ValueError("bulk concentration species IDs must be unique")
        return self


class WetCo2CylindricalDiffusionLimitedScaleGrowth(Contract):
    """Limit one caller-selected solid's precipitation rate by aqueous species supply."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_diffusion_limited_scale_growth.v1"] = (
        "matintegrity.wet_co2_cylindrical_diffusion_limited_scale_growth.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    solid_id: str = Field(min_length=1, max_length=160)
    geometry_result: Calculation
    multilayer_transport_result: Calculation
    saturation_scale_kinetics_result: Calculation
    reactant_stoichiometry: tuple[WetCo2DiffusionLimitedSolidReactant, ...] = Field(min_length=1, max_length=64)
    stoichiometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stoichiometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    bulk_history: tuple[WetCo2DiffusionLimitedBulkKnot, ...] = Field(min_length=2, max_length=5000)
    precipitation_flux_area_basis_reviewed: bool
    left_held_interval_flux_reviewed: bool
    stoichiometry_and_phase_identity_reviewed: bool

    @model_validator(mode="after")
    def bind_stoich_and_results(self):
        payload = [row.model_dump(mode="json") for row in self.reactant_stoichiometry]
        if canonical_digest(payload) != self.stoichiometry_record_sha256:
            raise ValueError("stoichiometry digest must bind the ordered phase-reactant coefficients")
        if not any(row.sha256 == self.stoichiometry_record_sha256 and row.license_id
                   for row in self.stoichiometry_evidence):
            raise ValueError("licensed Evidence must pin the caller-selected balanced solid stoichiometry")
        if len({row.species_id for row in self.reactant_stoichiometry}) != len(self.reactant_stoichiometry):
            raise ValueError("solid reactant species IDs must be unique")
        if self.geometry_result.values.get("model_id") != "degradation.wet_co2_cylindrical_scale_geometry_history":
            raise ValueError("geometry input must come from the cylindrical geometry model")
        if self.multilayer_transport_result.values.get("model_id") != "integration.wet_co2_cylindrical_multilayer_transport_resistance":
            raise ValueError("transport input must come from the cylindrical multilayer resistance model")
        if self.saturation_scale_kinetics_result.values.get("model_id") != "integration.wet_co2_cylindrical_wall_saturation_scale_kinetics":
            raise ValueError("saturation input must come from the cylindrical wall saturation kinetics adapter")
        if any(result.status != "computed" for result in (
            self.geometry_result, self.multilayer_transport_result, self.saturation_scale_kinetics_result
        )):
            raise ValueError("geometry, multilayer transport and saturation kinetics inputs must all be computed")
        times = tuple(float(row["time_s"]) for row in self.geometry_result.values.get("history", []))
        if times != tuple(row.time_s for row in self.bulk_history):
            raise ValueError("bulk concentration records must match every exact geometry knot")
        if tuple(float(row["time_s"]) for row in self.multilayer_transport_result.values.get("history", [])) != times:
            raise ValueError("multilayer transport result knots must exactly match geometry")
        saturation = self.saturation_scale_kinetics_result.values
        saturation_times = tuple(float(row["time_s"]) for row in saturation.get("saturation_history", []))
        kinetics = saturation.get("surface_scale_kinetics", {}).get("values", {}).get("scale_history", [])
        kinetics_times = tuple(float(row["time_s"]) for row in kinetics)
        if saturation_times != times or kinetics_times != times:
            raise ValueError("saturation and kinetics knots must exactly match the geometry history")
        return self


def _upstream_sha(result: Calculation) -> str:
    return canonical_digest(result.model_dump(mode="json"))


def evaluate_wet_co2_cylindrical_diffusion_limited_scale_growth(
    request: WetCo2CylindricalDiffusionLimitedScaleGrowth,
) -> Calculation:
    """Cap the selected caller precipitation flux by every limiting reactant's transport supply."""
    geometry = request.geometry_result.values
    transport = request.multilayer_transport_result.values
    saturation = request.saturation_scale_kinetics_result.values
    request_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": geometry.get("asset_id"),
        "location_id": geometry.get("location_id"),
        "model_id": MODEL_ID,
        "solid_id": request.solid_id,
        "input_sha256": request_digest,
        "geometry_result_sha256": _upstream_sha(request.geometry_result),
        "transport_result_sha256": _upstream_sha(request.multilayer_transport_result),
        "saturation_kinetics_result_sha256": _upstream_sha(request.saturation_scale_kinetics_result),
        "stoichiometry_record_sha256": request.stoichiometry_record_sha256,
        "source_ids": [GEOMETRY_SOURCE_ID, TRANSPORT_SOURCE_ID, SATURATION_SOURCE_ID, STOICHIOMETRY_SOURCE_ID],
    }
    missing_reviews = [name for name in (
        "precipitation_flux_area_basis_reviewed", "left_held_interval_flux_reviewed",
        "stoichiometry_and_phase_identity_reviewed",
    ) if not getattr(request, name)]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "reason": "surface_area_interval_and_phase_stoichiometry_reviews_required",
            "missing_reviews": missing_reviews,
        })
    if saturation.get("candidate_solid_id") != request.solid_id:
        return Calculation(status="needs_data", values=base | {
            "reason": "selected_solid_does_not_match_saturation_kinetics_result",
            "upstream_candidate_solid_id": saturation.get("candidate_solid_id"),
        })
    geometry_digest_from_transport = saturation.get("transport_geometry_result_sha256")
    transport_geometry_digest = transport.get("geometry_result_sha256")
    geometry_input_digest = _upstream_sha(request.geometry_result)
    if geometry_digest_from_transport != geometry_input_digest or transport_geometry_digest != geometry_input_digest:
        return Calculation(status="needs_data", values=base | {
            "reason": "geometry_result_lineage_does_not_match_transport_and_saturation_inputs",
            "saturation_geometry_sha256": geometry_digest_from_transport,
            "multilayer_geometry_sha256": transport_geometry_digest,
        })

    geometry_rows = geometry.get("history", [])
    transport_rows = transport.get("history", [])
    saturation_rows = saturation.get("saturation_history", [])
    kinetic_rows = saturation.get("surface_scale_kinetics", {}).get("values", {}).get("scale_history", [])
    stoich = {row.species_id: row.moles_consumed_per_mole_solid for row in request.reactant_stoichiometry}
    bulk_rows = [{row.species_id: row.concentration_mol_m3 for row in knot.concentrations}
                 for knot in request.bulk_history]
    state_rows = []
    cumulative_mol_per_m = 0.0
    starting_inventory = float(geometry_rows[0].get("phase_inventory_mol_m_by_phase", {}).get(request.solid_id, 0.0))
    cumulative_mol_per_m = starting_inventory
    for index, (geom, transport_row, sat_row, kinetic_row) in enumerate(zip(
        geometry_rows, transport_rows, saturation_rows, kinetic_rows, strict=True
    )):
        scale_species = transport_row.get("species_transport", {})
        wall_concentrations = sat_row.get("wall_adjacent_cell_concentration_mol_m3_by_species", {})
        available_limits = {}
        for species_id, coefficient in stoich.items():
            if species_id not in scale_species or species_id not in wall_concentrations or species_id not in bulk_rows[index]:
                return Calculation(status="needs_data", values=base | {
                    "reason": "stoichiometric_reactant_missing_from_bulk_wall_or_multilayer_transport",
                    "failed_knot_index": index,
                    "species_id": species_id,
                })
            k = float(scale_species[species_id]["inner_area_mass_transfer_coefficient_m_s"])
            driving = bulk_rows[index][species_id] - float(wall_concentrations[species_id])
            supply = max(0.0, k * driving)
            available_limits[species_id] = {
                "bulk_concentration_mol_m3": bulk_rows[index][species_id],
                "wall_concentration_mol_m3": float(wall_concentrations[species_id]),
                "mass_transfer_coefficient_m_s": k,
                "inward_supply_flux_mol_m2_s": supply,
                "solid_equivalent_precipitation_limit_mol_m2_s": supply / coefficient,
            }
        kinetic_precip = float(kinetic_row["precipitation_flux_mol_m2_s"])
        kinetic_dissolve = float(kinetic_row["dissolution_flux_mol_m2_s"])
        if not all(math.isfinite(value) and value >= 0.0 for value in (kinetic_precip, kinetic_dissolve)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "kinetics_flux_outside_finite_nonnegative_support",
                "failed_knot_index": index,
            })
        transport_cap = min((row["solid_equivalent_precipitation_limit_mol_m2_s"]
                             for row in available_limits.values()), default=0.0)
        limited_precip = min(kinetic_precip, transport_cap)
        net_flux = limited_precip - kinetic_dissolve
        radius = float(geom["bore_radius_m"])
        interval_moles_per_m = 0.0
        inventory_at_knot = cumulative_mol_per_m
        if index < len(geometry_rows) - 1:
            dt = float(geometry_rows[index + 1]["time_s"]) - float(geom["time_s"])
            interval_moles_per_m = net_flux * (2.0 * math.pi * radius) * dt
            if not math.isfinite(interval_moles_per_m):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "left_held_phase_inventory_increment_outside_finite_support",
                    "failed_knot_index": index,
                })
            cumulative_mol_per_m += interval_moles_per_m
            if cumulative_mol_per_m < -1e-12:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "dissolution_depletes_selected_phase_inventory",
                    "failed_interval_index": index,
                    "phase_inventory_mol_m": cumulative_mol_per_m,
                })
            cumulative_mol_per_m = max(0.0, cumulative_mol_per_m)
        geometry_inventory = float(geom.get("phase_inventory_mol_m_by_phase", {}).get(request.solid_id, 0.0))
        state_rows.append({
            "time_s": float(geom["time_s"]),
            "bore_radius_m": radius,
            "kinetic_precipitation_flux_mol_m2_s": kinetic_precip,
            "diffusion_limited_precipitation_flux_mol_m2_s": limited_precip,
            "dissolution_flux_mol_m2_s": kinetic_dissolve,
            "net_phase_flux_mol_m2_s": net_flux,
            "species_transport_limits": available_limits,
            "interval_left_held_net_phase_increment_mol_m": interval_moles_per_m,
            "diffusion_limited_phase_inventory_mol_m": inventory_at_knot,
            "geometry_phase_inventory_mol_m": geometry_inventory,
            "inventory_difference_from_geometry_mol_m": inventory_at_knot - geometry_inventory,
        })
    return Calculation(values=base | {
        "status": "computed",
        "knot_count": len(state_rows),
        "inventory_integration": "left_held_knot_flux_times_inner_wetted_area_per_axial_metre.v1",
        "history": state_rows,
        "limitations": [
            "A single caller-selected neutral solid and caller-declared aqueous consumption stoichiometry are used; phase selection and reaction balancing are not inferred.",
            "Precipitation is capped by min_i[k_i max(C_bulk,i - C_wall,i, 0)/nu_i]; dissolution uses the caller kinetics flux unchanged.",
            "Kinetics flux is assumed to use the instantaneous inner wetted-area basis after explicit caller review.",
            "Left-held fluxes and the left-knot bore circumference integrate phase inventory per axial metre; no within-interval feedback or adaptive time integration is performed.",
            "The output is a diagnostic ledger on the supplied geometry. It does not update transport, saturation, scale thickness, or geometry and does not establish field corrosion performance.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalDiffusionLimitedScaleGrowth,
        evaluator=evaluate_wet_co2_cylindrical_diffusion_limited_scale_growth,
        units={
            "history[].kinetic_precipitation_flux_mol_m2_s": "mol/m^2/s",
            "history[].diffusion_limited_precipitation_flux_mol_m2_s": "mol/m^2/s",
            "history[].dissolution_flux_mol_m2_s": "mol/m^2/s",
            "history[].species_transport_limits.*.mass_transfer_coefficient_m_s": "m/s",
            "history[].species_transport_limits.*.inward_supply_flux_mol_m2_s": "mol/m^2/s",
            "history[].interval_left_held_net_phase_increment_mol_m": "mol/m",
            "history[].diffusion_limited_phase_inventory_mol_m": "mol/m",
        },
        assumptions=(
            "The precipitation rate is limited by the least available reactant flux among caller-declared solid reactants.",
            "All input histories share exact geometry knots and matching geometry-result lineage.",
            "Interval rates are held at the left knot and multiplied by the inner wetted area per axial metre.",
        ),
        source_ids=(GEOMETRY_SOURCE_ID, TRANSPORT_SOURCE_ID, SATURATION_SOURCE_ID, STOICHIOMETRY_SOURCE_ID),
        qualification="user_model",
    )]



