from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .models.surface_scale_kinetics import (
    CallerSurfaceScaleKinetics,
    SurfaceScaleKineticInterval,
    caller_surface_scale_kinetics,
)
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalScaleGeometryHistory,
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)
from .wet_co2_cylindrical_finite_liquid_transfer_inventory import (
    WetCo2CylindricalFiniteLiquidTransferInventory,
)
from .wet_co2_cylindrical_scale_kinetics_geometry import (
    WetCo2CylindricalScaleKineticsGeometryHandoff,
    evaluate_wet_co2_cylindrical_scale_kinetics_geometry_handoff,
)
from .wet_co2_cylindrical_wall_saturation_scale_kinetics import (
    WetCo2CylindricalActivityProductTerm,
    WetCo2CylindricalPhaseActivityKnot,
)
from .wet_co2_cylindrical_transient_transport import WetCo2TransientSpecies

MODEL_ID = "integration.wet_co2_finite_inventory_saturation_scale_geometry"
FINITE_INVENTORY_SOURCE_ID = "caller_cylindrical_finite_liquid_inventory_results"
ACTIVITY_SOURCE_ID = "caller_finite_inventory_wall_activity_and_ksp_records"
KINETICS_SOURCE_ID = "caller_surface_scale_kinetics_configuration"
GEOMETRY_SOURCE_ID = "caller_cylindrical_scale_geometry_seed"
CLOSURE_SOURCE_ID = "finite_liquid_to_solid_reaction_stoichiometric_closure"


class WetCo2FiniteLiquidWallExchange(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    start_time_s: Nonnegative
    end_time_s: Positive
    nonreaction_wall_inventory_change_mol: float
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_wall_exchange_record(self):
        if self.end_time_s <= self.start_time_s or not math.isfinite(self.nonreaction_wall_inventory_change_mol):
            raise ValueError("wall external exchange interval/value must be finite and positive-duration")
        payload = {"species_id": self.species_id, "start_time_s": self.start_time_s,
                   "end_time_s": self.end_time_s,
                   "nonreaction_wall_inventory_change_mol": self.nonreaction_wall_inventory_change_mol}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("wall exchange digest must bind species, interval and nonreaction change")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin every nonreaction wall inventory exchange")
        return self


class WetCo2FiniteInventorySaturationScaleGeometry(Contract):
    """Bridge finite liquid wall concentrations to caller scale kinetics and exact cylindrical phase geometry."""

    schema_version: Literal["matintegrity.wet_co2_finite_inventory_saturation_scale_geometry.v1"] = (
        "matintegrity.wet_co2_finite_inventory_saturation_scale_geometry.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    solid_id: str = Field(min_length=1, max_length=160)
    geometry_seed: WetCo2CylindricalScaleGeometryHistory
    geometry_result: Calculation
    finite_liquid_inventory_results: dict[str, Calculation] = Field(min_length=1, max_length=64)
    aqueous_species: tuple[WetCo2TransientSpecies, ...] = Field(min_length=1, max_length=64)
    solid_elemental_composition: dict[str, Positive]
    activity_product_terms: tuple[WetCo2CylindricalActivityProductTerm, ...] = Field(min_length=1, max_length=32)
    phase_activity_history: tuple[WetCo2CylindricalPhaseActivityKnot, ...] = Field(min_length=2, max_length=5000)
    kinetics_template: CallerSurfaceScaleKinetics
    nonreaction_wall_exchanges: tuple[WetCo2FiniteLiquidWallExchange, ...] = Field(min_length=1, max_length=32000)
    layer_order_steel_to_bore: tuple[str, ...] = Field(min_length=1, max_length=1)
    concentration_inventory_abs_tolerance_mol: Positive = 1e-10
    concentration_inventory_relative_tolerance: Positive = Field(default=1e-8, le=1e-2)
    geometry_kinetic_inventory_abs_tolerance_mol: Positive = 1e-10
    geometry_kinetic_inventory_relative_tolerance: Positive = Field(default=1e-6, le=1e-2)
    precipitation_area_basis_and_reaction_closure_reviewed: bool
    wall_activity_standard_state_and_phase_reviewed: bool
    saturation_interpolation_reviewed: bool = False
    geometry_layer_and_segment_area_reviewed: bool

    @model_validator(mode="after")
    def bind_exact_phase_and_clock(self):
        if set(self.geometry_seed.phase_ids if hasattr(self.geometry_seed, "phase_ids") else
               [row.phase_id for row in self.geometry_seed.phases]) != {self.solid_id}:
            raise ValueError("this bounded bridge requires a single selected solid phase in the cylindrical geometry seed")
        if self.layer_order_steel_to_bore != (self.solid_id,):
            raise ValueError("single-phase layer order must exactly identify the selected solid")
        if self.geometry_result.status != "computed" or self.geometry_result.values.get("input_sha256") != canonical_digest(
            self.geometry_seed.model_dump(mode="json")
        ):
            raise ValueError("computed geometry result must bind the supplied geometry seed")
        if self.geometry_result.values.get("assessment_id") != self.assessment_id:
            raise ValueError("geometry and bridge assessment IDs must match")
        times = tuple(row.time_s for row in self.geometry_seed.history)
        if tuple(row.time_s for row in self.phase_activity_history) != times:
            raise ValueError("activity and Ksp records must match every geometry knot exactly")
        if tuple(row.start_time_s for row in self.kinetics_template.intervals) != times[:-1] or tuple(
            row.end_time_s for row in self.kinetics_template.intervals
        ) != times[1:]:
            raise ValueError("caller kinetics intervals must cover every exact geometry interval")
        if self.kinetics_template.assessment_id != self.assessment_id or self.kinetics_template.scale_phase_id != self.solid_id:
            raise ValueError("kinetics template assessment/phase must match the bridge")
        if not math.isclose(self.kinetics_template.scale_molar_volume_m3_mol,
                            self.geometry_seed.phases[0].molar_volume_m3_mol,
                            rel_tol=1e-10, abs_tol=1e-15):
            raise ValueError("kinetics and geometry phase molar volumes must match")
        if set(self.finite_liquid_inventory_results) != {row.species_id for row in self.activity_product_terms}:
            raise ValueError("provide one finite-liquid inventory result for each selected-solid dissolution product species")
        species_by_id = {row.species_id: row for row in self.aqueous_species}
        if set(species_by_id) != set(self.finite_liquid_inventory_results):
            raise ValueError("aqueous formulas, finite liquid results and activity products must cover the same species")
        if len(species_by_id) != len(self.aqueous_species):
            raise ValueError("aqueous species IDs must be unique")
        terms = {row.species_id: row.exponent for row in self.activity_product_terms}
        if len(terms) != len(self.activity_product_terms):
            raise ValueError("activity product terms must be unique by species")
        if not self.solid_elemental_composition:
            raise ValueError("selected solid needs an explicit elemental formula")
        charge = math.fsum(species_by_id[key].charge_number * exponent for key, exponent in terms.items())
        if not math.isclose(charge, 0.0, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("selected neutral solid dissolution products must be charge balanced")
        elements = set(self.solid_elemental_composition) | set().union(*(
            set(species_by_id[key].elemental_composition) for key in terms
        ))
        for element in elements:
            product = math.fsum(exponent * species_by_id[key].elemental_composition.get(element, 0.0)
                                for key, exponent in terms.items())
            if not math.isclose(product, self.solid_elemental_composition.get(element, 0.0),
                                rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError(f"selected solid formula is not balanced by dissolution products for {element}")
        for species_id, result in self.finite_liquid_inventory_results.items():
            if result.status != "computed" or result.values.get("model_id") != "integration.wet_co2_cylindrical_finite_liquid_transfer_inventory":
                raise ValueError("each species input must be a computed finite cylindrical liquid inventory result")
            if result.values.get("species_id") != species_id or result.values.get("assessment_id") != self.assessment_id:
                raise ValueError("finite inventory species and assessment IDs must match the request map")
            if result.values.get("geometry_result_sha256") != canonical_digest(self.geometry_result.model_dump(mode="json")):
                raise ValueError("all finite inventories must use the exact supplied cylindrical geometry result")
            if tuple(float(row["time_s"]) for row in result.values.get("history", [])) != times:
                raise ValueError("finite inventory results must match every geometry knot exactly")
        expected_exchange = {(species_id, left, right) for species_id in terms
                             for left, right in zip(times[:-1], times[1:], strict=True)}
        actual_exchange = {(row.species_id, row.start_time_s, row.end_time_s)
                           for row in self.nonreaction_wall_exchanges}
        if actual_exchange != expected_exchange or len(actual_exchange) != len(self.nonreaction_wall_exchanges):
            raise ValueError("nonreaction wall exchange must contain one exact interval record per species")
        for knot in self.phase_activity_history:
            if knot.equilibrium_solid_id != self.solid_id or set(knot.activity_coefficients) != set(terms):
                raise ValueError("activity/Ksp records must bind the selected solid and exactly its product species")
        return self


def _saturation_ratio(knot: WetCo2CylindricalPhaseActivityKnot,
                      concentrations_mol_m3: dict[str, float],
                      terms: tuple[WetCo2CylindricalActivityProductTerm, ...]) -> float:
    log10_iap = 0.0
    for term in terms:
        concentration_mol_l = concentrations_mol_m3[term.species_id] / 1000.0
        if concentration_mol_l <= 0.0:
            return 0.0
        gamma = knot.activity_coefficients[term.species_id]
        log10_iap += term.exponent * (math.log10(gamma) + math.log10(concentration_mol_l))
    log10_ratio = log10_iap - knot.log10_solubility_product
    if not math.isfinite(log10_ratio) or log10_ratio > 300.0:
        raise ArithmeticError("finite-inventory saturation ratio exceeds supported logarithmic range")
    return 10.0 ** log10_ratio if log10_ratio > -320.0 else 0.0


def evaluate_wet_co2_finite_inventory_saturation_scale_geometry(
    request: WetCo2FiniteInventorySaturationScaleGeometry,
) -> Calculation:
    """Derive wall saturation, execute caller scale kinetics, close liquid reaction exchange and map cylindrical geometry."""
    geometry_digest = canonical_digest(request.geometry_result.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry_seed.asset_id,
        "location_id": request.geometry_seed.location_id,
        "model_id": MODEL_ID,
        "geometry_result_sha256": geometry_digest,
        "finite_inventory_result_sha256": {
            key: canonical_digest(value.model_dump(mode="json"))
            for key, value in request.finite_liquid_inventory_results.items()
        },
        "kinetics_template_sha256": canonical_digest(request.kinetics_template.model_dump(mode="json")),
        "source_ids": [FINITE_INVENTORY_SOURCE_ID, ACTIVITY_SOURCE_ID, KINETICS_SOURCE_ID,
                       GEOMETRY_SOURCE_ID, CLOSURE_SOURCE_ID],
    }
    missing = [name for name in (
        "precipitation_area_basis_and_reaction_closure_reviewed",
        "wall_activity_standard_state_and_phase_reviewed",
        "geometry_layer_and_segment_area_reviewed",
    ) if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "reason": "wall_activity_scale_area_and_reaction_closure_reviews_required",
            "missing_reviews": missing,
        })
    times = tuple(row.time_s for row in request.geometry_seed.history)
    wall_concentrations = []
    bulk_concentrations = [
        {species_id: float(result.values["history"][index]["bulk_concentration_mol_m3"])
         for species_id, result in request.finite_liquid_inventory_results.items()}
        for index in range(len(times))
    ]
    for knot_index, time_s in enumerate(times):
        wall_concentrations.append({species_id: float(result.values["history"][knot_index]["wall_concentration_mol_m3"])
                                    for species_id, result in request.finite_liquid_inventory_results.items()})
    saturation_rows = []
    ratios = []
    try:
        for knot, concentrations in zip(request.phase_activity_history, wall_concentrations, strict=True):
            ratio = _saturation_ratio(knot, concentrations, request.activity_product_terms)
            ratios.append(ratio)
            saturation_rows.append({
                "time_s": knot.time_s,
                "temperature_K": knot.temperature_K,
                "solid_id": request.solid_id,
                "wall_concentration_mol_m3_by_species": concentrations,
                "bulk_concentration_mol_m3_by_species": bulk_concentrations[len(saturation_rows)],
                "activity_coefficients": knot.activity_coefficients,
                "log10_solubility_product": knot.log10_solubility_product,
                "saturation_ratio": ratio,
                "activity_record_sha256": knot.activity_record_sha256,
                "equilibrium_record_sha256": knot.equilibrium_record_sha256,
            })
    except (ArithmeticError, KeyError, ValueError) as exc:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_inventory_wall_saturation_calculation_outside_support",
            "detail": str(exc),
        })
    varying = any(left != right for left, right in zip(ratios[:-1], ratios[1:], strict=True))
    if varying and not request.saturation_interpolation_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "computed_knot_saturation_variation_requires_linear_path_review",
            "saturation_history": saturation_rows,
        })
    template = request.kinetics_template.model_dump(mode="json")
    interval_rows = []
    for index, interval in enumerate(request.kinetics_template.intervals):
        payload = interval.model_dump(mode="json")
        payload["saturation_ratio"] = ratios[index]
        payload["saturation_ratio_end"] = ratios[index + 1] if ratios[index] != ratios[index + 1] else None
        payload["temperature_K"] = request.phase_activity_history[index].temperature_K
        interval_rows.append(payload)
    template["intervals"] = interval_rows
    actual_varies = any(row["saturation_ratio_end"] is not None for row in interval_rows)
    template["linearly_varying_saturation_reviewed"] = bool(actual_varies and request.saturation_interpolation_reviewed)
    try:
        bound_kinetics = CallerSurfaceScaleKinetics.model_validate(template)
    except ValueError as exc:
        return Calculation(status="needs_data", values=base | {
            "reason": "finite_inventory_saturation_did_not_bind_to_caller_kinetics_contract",
            "detail": str(exc),
            "saturation_history": saturation_rows,
        })
    kinetics = caller_surface_scale_kinetics(bound_kinetics)
    if kinetics.status != "computed":
        return Calculation(status=kinetics.status, values=base | {
            "reason": "caller_surface_scale_kinetics_not_computed",
            "kinetics_result": kinetics.model_dump(mode="json"),
            "saturation_history": saturation_rows,
        })
    scale_rows = kinetics.values["scale_history"]
    kinetic_history = Calculation(values={
        "assessment_id": request.assessment_id,
        "model_id": "integration.wet_co2_finite_inventory_scale_kinetics_history",
        "scale_history": scale_rows,
    })
    geometry_handoff = WetCo2CylindricalScaleKineticsGeometryHandoff(
        assessment_id=request.assessment_id,
        geometry=request.geometry_seed,
        phase_kinetics_results={request.solid_id: kinetic_history},
        layer_order_steel_to_bore=(request.solid_id,),
        exact_knot_mapping_reviewed=True,
        dense_contiguous_layers_reviewed=True,
    )
    moving_geometry = evaluate_wet_co2_cylindrical_scale_kinetics_geometry_handoff(geometry_handoff)
    if moving_geometry.status != "computed":
        return Calculation(status=moving_geometry.status, values=base | {
            "reason": "kinetic_thickness_to_cylindrical_geometry_handoff_not_computed",
            "geometry_handoff_result": moving_geometry.model_dump(mode="json"),
            "scale_kinetics_result": kinetics.model_dump(mode="json"),
            "saturation_history": saturation_rows,
        })

    geometry_history = moving_geometry.values["history"]
    seed_initial = float(request.geometry_seed.history[0].phase_inventories[0].moles_per_axial_metre_mol_m)
    mapped_initial = float(geometry_history[0]["phase_inventory_mol_m_by_phase"][request.solid_id])
    initial_residual = mapped_initial - seed_initial
    initial_allowed = request.geometry_kinetic_inventory_abs_tolerance_mol + request.geometry_kinetic_inventory_relative_tolerance * max(abs(mapped_initial), abs(seed_initial), 1e-30)
    if abs(initial_residual) > initial_allowed:
        return Calculation(status="out_of_scope", values=base | {"reason": "initial_scale_kinetics_thickness_does_not_match_seed_phase_inventory", "initial_geometry_phase_inventory_mol_m": seed_initial, "kinetic_initial_phase_inventory_mol_m": mapped_initial, "closure_residual_mol_m": initial_residual, "allowed_residual_mol_m": initial_allowed})
    external_map = {(row.species_id, row.start_time_s): row.nonreaction_wall_inventory_change_mol
                    for row in request.nonreaction_wall_exchanges}
    exchange_closure = []
    species_terms = {row.species_id: row.exponent for row in request.activity_product_terms}
    intervals = scale_rows[1:]
    for index, interval in enumerate(intervals):
        start_time = times[index]
        row0 = geometry_history[index]
        row1 = geometry_history[index + 1]
        area = float(row0["bore_wetted_perimeter_m"]) * request.geometry_seed.segment_length_m
        phase_inventory_delta_mol = (
            float(row1["phase_inventory_mol_m_by_phase"][request.solid_id])
            - float(row0["phase_inventory_mol_m_by_phase"][request.solid_id])
        ) * request.geometry_seed.segment_length_m
        kinetic_net_mol_m2 = float(interval["precipitated_mol_m2"]) - float(interval["dissolved_mol_m2"])
        kinetic_phase_delta_mol = kinetic_net_mol_m2 * area
        geometry_kinetic_residual = phase_inventory_delta_mol - kinetic_phase_delta_mol
        geometry_scale = max(abs(phase_inventory_delta_mol), abs(kinetic_phase_delta_mol), 1e-30)
        geometry_allowed = request.geometry_kinetic_inventory_abs_tolerance_mol + request.geometry_kinetic_inventory_relative_tolerance * geometry_scale
        if abs(geometry_kinetic_residual) > geometry_allowed:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "cylindrical_phase_inventory_does_not_close_to_areal_kinetics_extent",
                "failed_interval_index": index,
                "geometry_phase_delta_mol": phase_inventory_delta_mol,
                "kinetic_areal_extent_times_segment_area_mol": kinetic_phase_delta_mol,
                "closure_residual_mol": geometry_kinetic_residual,
                "allowed_residual_mol": geometry_allowed,
            })
        per_species = {}
        for species_id, coefficient in species_terms.items():
            finite_row = request.finite_liquid_inventory_results[species_id].values["history"][index]
            total_wall_external = float(finite_row["external_wall_inventory_change_mol"])
            nonreaction = external_map[(species_id, start_time)]
            phase_reaction = coefficient * (
                float(interval["dissolved_mol_m2"]) - float(interval["precipitated_mol_m2"])
            ) * area
            expected_wall_external = nonreaction + phase_reaction
            residual = total_wall_external - expected_wall_external
            scale = max(abs(total_wall_external), abs(expected_wall_external), 1e-30)
            allowed = request.concentration_inventory_abs_tolerance_mol + request.concentration_inventory_relative_tolerance * scale
            per_species[species_id] = {
                "finite_inventory_external_wall_change_mol": total_wall_external,
                "caller_nonreaction_wall_change_mol": nonreaction,
                "kinetic_precipitation_wall_consumption_mol": -coefficient * float(interval["precipitated_mol_m2"]) * area,
                "kinetic_dissolution_wall_release_mol": coefficient * float(interval["dissolved_mol_m2"]) * area,
                "expected_total_wall_change_mol": expected_wall_external,
                "closure_residual_mol": residual,
                "allowed_residual_mol": allowed,
            }
            if abs(residual) > allowed:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "finite_wall_liquid_inventory_does_not_close_with_phase_kinetics",
                    "failed_interval_index": index,
                    "species_id": species_id,
                    "species_closure": per_species[species_id],
                })
        exchange_closure.append({
            "start_time_s": start_time,
            "end_time_s": times[index + 1],
            "selected_phase_area_m2": area,
            "kinetic_net_phase_change_mol": kinetic_phase_delta_mol,
            "geometry_phase_change_mol": phase_inventory_delta_mol,
            "geometry_kinetics_closure_residual_mol": geometry_kinetic_residual,
            "wall_liquid_species_closure": per_species,
        })
    return Calculation(values=base | {
        "status": "computed",
        "selected_solid_id": request.solid_id,
        "saturation_history": saturation_rows,
        "scale_kinetics_result": kinetics.model_dump(mode="json"),
        "moving_cylindrical_geometry_result": moving_geometry.model_dump(mode="json"),
        "finite_liquid_phase_exchange_closure": exchange_closure,
        "closure_method": "caller_surface_kinetics_to_annular_phase_inventory_and_finite_wall_liquid_exchange.v1",
        "limitations": [
            "Saturation is derived from caller wall-compartment concentrations, activity coefficients, Ksp records and an explicitly selected neutral solid.",
            "The existing caller scale-kinetics law supplies precipitation/dissolution; no kinetic parameter is inferred.",
            "All finite-liquid species balances must already include the reaction wall exchange; this adapter checks that external ledger against nonreaction exchange plus kinetics-derived reaction moles.",
            "Single solid layer, dense axisymmetric annulus, full inner wetted-area reference, caller layer/area mapping and exact knots are assumed.",
            "Both annular geometry phase inventory and each aqueous species wall-exchange ledger must close within declared tolerances; mismatches fail closed.",
            "No automatic phase discovery, competing phase selection, transient geometry feedback, gas chemistry, corrosion prediction or qualification is performed.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2FiniteInventorySaturationScaleGeometry,
        evaluator=evaluate_wet_co2_finite_inventory_saturation_scale_geometry,
        units={
            "saturation_history[].wall_concentration_mol_m3_by_species.*": "mol/m^3",
            "saturation_history[].saturation_ratio": "1",
            "finite_liquid_phase_exchange_closure[].selected_phase_area_m2": "m^2",
            "finite_liquid_phase_exchange_closure[].kinetic_net_phase_change_mol": "mol",
            "finite_liquid_phase_exchange_closure[].geometry_phase_change_mol": "mol",
            "finite_liquid_phase_exchange_closure[].wall_liquid_species_closure.*.closure_residual_mol": "mol",
        },
        assumptions=(
            "Wall activities use molarity standard state, caller activity coefficients and a caller log10 Ksp at each exact time knot.",
            "One caller-selected neutral solid and its explicit aqueous dissolution-product stoichiometry are used.",
            "Caller finite-liquid inventory results include both nonreaction wall exchange and the selected solid's reaction exchange; this module verifies the decomposition.",
            "Scale kinetics are mapped to a single dense annular phase and checked against exact cylindrical phase inventory changes.",
        ),
        source_ids=(FINITE_INVENTORY_SOURCE_ID, ACTIVITY_SOURCE_ID, KINETICS_SOURCE_ID,
                    GEOMETRY_SOURCE_ID, CLOSURE_SOURCE_ID),
        qualification="user_model",
    )]




