"""Iterate cylindrical BV recession and caller scale kinetics/diffusion inventory."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_diffusion_limited_scale_growth import (
    WetCo2CylindricalDiffusionLimitedScaleGrowth,
    WetCo2DiffusionLimitedBulkKnot,
    WetCo2DiffusionLimitedSolidReactant,
    evaluate_wet_co2_cylindrical_diffusion_limited_scale_growth,
)
from .wet_co2_cylindrical_multilayer_transport import (
    WetCo2CylindricalMultilayerTransportResistance,
    evaluate_wet_co2_cylindrical_multilayer_transport_resistance,
)
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalGeometryKnot,
    WetCo2CylindricalScaleGeometryHistory,
    WetCo2ScalePhaseLineInventory,
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)
from .wet_co2_cylindrical_spatial_mixed_potential import (
    MODEL_ID as SPATIAL_MODEL_ID,
    WetCo2CylindricalSpatialMixedPotential,
    evaluate_wet_co2_cylindrical_spatial_mixed_potential,
)
from .wet_co2_cylindrical_wall_saturation_scale_kinetics import (
    WetCo2CylindricalWallSaturationScaleKinetics,
    evaluate_wet_co2_cylindrical_wall_saturation_scale_kinetics,
)

MODEL_ID = "integration.wet_co2_cylindrical_scale_recession_feedback"
SOURCE_ID = "bounded_feedback_of_caller_scale_kinetics_diffusion_supply_and_bv_recession"


class WetCo2CylindricalPhaseGrowthCampaign(Contract):
    """Caller stoichiometry, open bulk knots and review gates for one scale phase."""

    solid_id: str = Field(min_length=1, max_length=160)
    reactant_stoichiometry: tuple[WetCo2DiffusionLimitedSolidReactant, ...] = Field(min_length=1, max_length=64)
    stoichiometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stoichiometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    bulk_history: tuple[WetCo2DiffusionLimitedBulkKnot, ...] = Field(min_length=2, max_length=2000)
    precipitation_flux_area_basis_reviewed: bool
    left_held_interval_flux_reviewed: bool
    stoichiometry_and_phase_identity_reviewed: bool

    @model_validator(mode="after")
    def bind_inventory_campaign(self):
        rows = [row.model_dump(mode="json") for row in self.reactant_stoichiometry]
        if canonical_digest(rows) != self.stoichiometry_record_sha256:
            raise ValueError("growth stoichiometry digest must bind ordered reactant coefficients")
        if not any(row.sha256 == self.stoichiometry_record_sha256 and row.license_id
                   for row in self.stoichiometry_evidence):
            raise ValueError("licensed Evidence must pin the precipitation reactant stoichiometry")
        if len({row.species_id for row in self.reactant_stoichiometry}) != len(self.reactant_stoichiometry):
            raise ValueError("growth stoichiometry species IDs must be unique")
        if not self.bulk_history or self.bulk_history[0].time_s != 0.0:
            raise ValueError("bulk history must begin at time zero")
        if any(b.time_s <= a.time_s for a, b in zip(self.bulk_history, self.bulk_history[1:])):
            raise ValueError("bulk history knots must be strictly increasing")
        return self


class WetCo2CylindricalScaleRecessionFeedback(Contract):
    """Outer exact-knot Picard loop over BV wall loss and phase-specific scale growth."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_scale_recession_feedback.v1"] = (
        "matintegrity.wet_co2_cylindrical_scale_recession_feedback.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    spatial_request: WetCo2CylindricalSpatialMixedPotential
    phase_saturation_kinetics_requests: dict[str, WetCo2CylindricalWallSaturationScaleKinetics] = Field(min_length=1, max_length=32)
    multilayer_transport_request: WetCo2CylindricalMultilayerTransportResistance
    phase_growth_campaigns: dict[str, WetCo2CylindricalPhaseGrowthCampaign] = Field(min_length=1, max_length=32)
    maximum_feedback_iterations: int = Field(default=20, ge=1, le=60)
    relaxation_factor: float = Field(default=0.5, gt=0.0, le=1.0)
    absolute_radius_tolerance_m: Positive = Field(default=1e-9)
    relative_radius_tolerance: float = Field(default=1e-7, gt=0.0, le=1e-2)
    absolute_phase_inventory_tolerance_mol_m: Positive = Field(default=1e-12)
    relative_phase_inventory_tolerance: float = Field(default=1e-8, gt=0.0, le=1e-2)
    absolute_wall_element_tolerance_mol_m: Positive = Field(default=1e-12)
    relative_wall_element_tolerance: float = Field(default=1e-8, gt=0.0, le=1e-2)
    maximum_feedback_work_units: int = Field(default=30_000_000, ge=10_000, le=300_000_000)
    scale_kinetics_and_transport_are_separate_reviewed_paths: bool
    saturation_standard_state_and_phase_selection_reviewed: bool
    diffusion_limited_reactant_supply_mapping_reviewed: bool
    reaction_stoichiometry_and_phase_formula_reviewed: bool
    alloy_release_and_scale_volume_geometry_reviewed: bool
    no_unmodeled_aqueous_precipitation_sink_claim_reviewed: bool
    no_inter_knot_or_qualification_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_composed_inputs_and_budget(self):
        spatial = self.spatial_request
        if spatial.geometry_trial_mode:
            raise ValueError("input spatial request must be the ordinary base request")
        geometry = spatial.geometry
        phase_ids = {row.phase_id for row in geometry.phases}
        if set(self.phase_saturation_kinetics_requests) != phase_ids:
            raise ValueError("supply exactly one wall-saturation/kinetics request per declared scale phase")
        if set(self.phase_growth_campaigns) != phase_ids:
            raise ValueError("supply exactly one diffusion-limited growth campaign per declared scale phase")
        if geometry.history[0].time_s != 0.0 or geometry.history[0].wall_recession_m != 0.0:
            raise ValueError("geometry must start at time zero with zero initial metal recession")
        geometry_result = evaluate_wet_co2_cylindrical_scale_geometry_history(geometry)
        if geometry_result.status != "computed":
            raise ValueError("caller seed geometry must be inside the cylindrical geometry support")
        times = tuple(float(row["time_s"]) for row in geometry_result.values["history"])
        species_ids = {row.species_id for row in spatial.species}
        for phase_id, saturation in self.phase_saturation_kinetics_requests.items():
            if saturation.candidate_solid_id != phase_id:
                raise ValueError("wall-saturation request key must match its selected solid phase")
            if saturation.transport_request.geometry != geometry:
                raise ValueError("saturation transport geometry must exactly match the spatial seed geometry")
            if {row.species_id for row in saturation.transport_request.species} != species_ids:
                raise ValueError("saturation transport species identities must match the spatial species set")
            if tuple(row.time_s for row in saturation.transport_request.knots) != tuple(row.time_s for row in spatial.knots):
                raise ValueError("saturation transport and BV solver must use the same exact time knots")
            phase = next(row for row in geometry.phases if row.phase_id == phase_id)
            if not math.isclose(saturation.kinetics_request.scale_molar_volume_m3_mol,
                                phase.molar_volume_m3_mol, rel_tol=1e-10, abs_tol=1e-15):
                raise ValueError("kinetic and geometry phase molar volumes differ")
            growth = self.phase_growth_campaigns[phase_id]
            if growth.solid_id != phase_id:
                raise ValueError("growth campaign key and phase ID differ")
            sat_terms = {row.species_id: row.exponent for row in saturation.activity_product_terms}
            growth_terms = {row.species_id: row.moles_consumed_per_mole_solid for row in growth.reactant_stoichiometry}
            if sat_terms != growth_terms:
                raise ValueError("diffusion-limited reactant stoichiometry must match the selected phase dissolution formula")
            if tuple(row.time_s for row in growth.bulk_history) != times:
                raise ValueError("every phase bulk history must match all exact geometry knots")
            if set(growth_terms) - species_ids:
                raise ValueError("growth reactants must be declared in spatial aqueous species")
        if self.multilayer_transport_request.geometry != geometry:
            raise ValueError("multilayer transport geometry must exactly match the spatial seed geometry")
        if self.multilayer_transport_request.species_ids and not set(self.multilayer_transport_request.species_ids) <= species_ids:
            raise ValueError("multilayer transport species must be present in the spatial species set")
        radial_count = len(spatial.initial_species[0].cell_concentrations_mol_m3)
        spatial_work = radial_count * sum(len(row.species_boundaries) for row in spatial.knots)
        saturation_work = sum(
            len(row.transport_request.initial_species[0].cell_concentrations_mol_m3)
            * sum(len(knot.species_boundaries) for knot in row.transport_request.knots)
            for row in self.phase_saturation_kinetics_requests.values()
        )
        transport_work = len(times) * max(1, len(geometry.phases)) * max(1, len(species_ids))
        estimate = self.maximum_feedback_iterations * (spatial_work + saturation_work + transport_work)
        if estimate > self.maximum_feedback_work_units:
            raise ValueError("nested finite-volume and phase work estimate exceeds the declared feedback budget")
        return self


def _geometry_with_inventory_and_steel(
    source: WetCo2CylindricalScaleGeometryHistory,
    steel_inner_radius_m_by_knot: tuple[float, ...],
    inventories_mol_m_by_phase: dict[str, tuple[float, ...]],
    *,
    iteration: int,
) -> WetCo2CylindricalScaleGeometryHistory:
    if len(steel_inner_radius_m_by_knot) != len(source.history):
        raise ValueError("steel-radius path must align with exact geometry knots")
    if set(inventories_mol_m_by_phase) != {row.phase_id for row in source.phases}:
        raise ValueError("phase inventories must include every declared scale phase")
    knots = []
    previous_recession = -math.inf
    for index, old in enumerate(source.history):
        recession = steel_inner_radius_m_by_knot[index] - source.initial_inner_radius_m
        if not math.isfinite(recession) or recession < -1e-12 or recession < previous_recession - 1e-12:
            raise ValueError("metal recession must remain finite, nonnegative and nondecreasing")
        previous_recession = recession
        phase_rows = []
        for phase in source.phases:
            values = inventories_mol_m_by_phase[phase.phase_id]
            if len(values) != len(source.history):
                raise ValueError("every phase inventory history must align with exact geometry knots")
            value = float(values[index])
            if not math.isfinite(value) or value < -1e-12:
                raise ValueError("phase inventory must remain finite and nonnegative")
            phase_rows.append(WetCo2ScalePhaseLineInventory(
                phase_id=phase.phase_id,
                moles_per_axial_metre_mol_m=max(0.0, value),
            ))
        knots.append(WetCo2CylindricalGeometryKnot(
            time_s=old.time_s,
            wall_recession_m=max(0.0, recession),
            phase_inventories=tuple(phase_rows),
        ))
    knot_tuple = tuple(knots)
    history_digest = canonical_digest([row.model_dump(mode="json") for row in knot_tuple])
    provider_id = f"{MODEL_ID}.iterated_geometry"
    evidence = Evidence(
        source_id=provider_id,
        origin="model_prediction",
        citation=(
            f"Computed iteration geometry for {MODEL_ID}; source geometry record "
            f"{source.history_provider_id}@{source.history_provider_revision} "
            f"sha256={source.history_record_sha256}; iteration={iteration}; upstream terms retained."
        ),
        license_id=source.history_evidence.license_id,
        sha256=history_digest,
    )
    payload = source.model_dump(mode="python")
    payload.update({
        "history": knot_tuple,
        "history_record_sha256": history_digest,
        "history_provider_id": provider_id,
        "history_provider_revision": "bounded-feedback-v1",
        "history_evidence": evidence,
    })
    return WetCo2CylindricalScaleGeometryHistory.model_validate(payload)


def _retarget_spatial_request(
    source: WetCo2CylindricalSpatialMixedPotential,
    geometry: WetCo2CylindricalScaleGeometryHistory,
    fixed_point_sha256: str,
    *,
    trial: bool,
    wall_abs_tolerance: float,
    wall_rel_tolerance: float,
) -> WetCo2CylindricalSpatialMixedPotential:
    payload = source.model_dump(mode="python")
    payload.update({
        "geometry": geometry,
        "geometry_sha256": canonical_digest(geometry.model_dump(mode="json")),
        "geometry_trial_mode": trial,
        "fixed_point_input_sha256": fixed_point_sha256 if trial else None,
        "trial_geometry_closure_exemption_reviewed": trial,
        "inventory_absolute_tolerance_mol_m": wall_abs_tolerance,
        "inventory_relative_tolerance": wall_rel_tolerance,
    })
    return WetCo2CylindricalSpatialMixedPotential.model_validate(payload)


def _retarget_saturation_request(
    source: WetCo2CylindricalWallSaturationScaleKinetics,
    geometry: WetCo2CylindricalScaleGeometryHistory,
) -> WetCo2CylindricalWallSaturationScaleKinetics:
    payload = source.model_dump(mode="python")
    transport = source.transport_request.model_dump(mode="python")
    transport.update({
        "geometry": geometry,
        "geometry_sha256": canonical_digest(geometry.model_dump(mode="json")),
    })
    payload.update({
        "transport_request": transport,
        "transport_request_sha256": canonical_digest(transport),
    })
    return WetCo2CylindricalWallSaturationScaleKinetics.model_validate(payload)


def _retarget_multilayer_request(
    source: WetCo2CylindricalMultilayerTransportResistance,
    geometry: WetCo2CylindricalScaleGeometryHistory,
) -> WetCo2CylindricalMultilayerTransportResistance:
    payload = source.model_dump(mode="python")
    payload.update({
        "geometry": geometry,
        "geometry_sha256": canonical_digest(geometry.model_dump(mode="json")),
    })
    return WetCo2CylindricalMultilayerTransportResistance.model_validate(payload)


def _growth_request(
    campaign: WetCo2CylindricalPhaseGrowthCampaign,
    geometry_result: Calculation,
    transport_result: Calculation,
    saturation_result: Calculation,
    *,
    assessment_id: str,
) -> WetCo2CylindricalDiffusionLimitedScaleGrowth:
    return WetCo2CylindricalDiffusionLimitedScaleGrowth.model_validate({
        "assessment_id": assessment_id,
        "solid_id": campaign.solid_id,
        "geometry_result": geometry_result.model_dump(mode="json"),
        "multilayer_transport_result": transport_result.model_dump(mode="json"),
        "saturation_scale_kinetics_result": saturation_result.model_dump(mode="json"),
        "reactant_stoichiometry": [row.model_dump(mode="json") for row in campaign.reactant_stoichiometry],
        "stoichiometry_record_sha256": campaign.stoichiometry_record_sha256,
        "stoichiometry_evidence": [row.model_dump(mode="json") for row in campaign.stoichiometry_evidence],
        "bulk_history": [row.model_dump(mode="json") for row in campaign.bulk_history],
        "precipitation_flux_area_basis_reviewed": campaign.precipitation_flux_area_basis_reviewed,
        "left_held_interval_flux_reviewed": campaign.left_held_interval_flux_reviewed,
        "stoichiometry_and_phase_identity_reviewed": campaign.stoichiometry_and_phase_identity_reviewed,
    })


def _phase_volume_per_length(geometry: WetCo2CylindricalScaleGeometryHistory, knot_index: int) -> float:
    phase_inventory = {row.phase_id: row.moles_per_axial_metre_mol_m
                       for row in geometry.history[knot_index].phase_inventories}
    return math.fsum(phase_inventory[phase.phase_id] * phase.molar_volume_m3_mol for phase in geometry.phases)


def _inventory_convergence(
    current: dict[str, tuple[float, ...]],
    target: dict[str, tuple[float, ...]],
    *,
    abs_tol: float,
    rel_tol: float,
) -> tuple[float, float, dict[str, list[float]]]:
    ratio = 0.0
    tolerance_max = 0.0
    residuals: dict[str, list[float]] = {}
    for phase_id in current:
        residuals[phase_id] = []
        for left, right in zip(current[phase_id], target[phase_id], strict=True):
            delta = float(right) - float(left)
            tol = abs_tol + rel_tol * max(abs(float(left)), abs(float(right)), 1e-30)
            ratio = max(ratio, abs(delta) / max(tol, 1e-300))
            tolerance_max = max(tolerance_max, tol)
            residuals[phase_id].append(delta)
    return ratio, tolerance_max, residuals


def _wall_element_residual_ratio(
    spatial_values: dict,
    *,
    abs_tol: float,
    rel_tol: float,
) -> tuple[float, float]:
    residuals = spatial_values.get("wall_element_balance_residual_mol_m_by_element", {})
    scales = spatial_values.get("wall_element_inventory_scale_mol_m", {})
    if not isinstance(residuals, dict) or not residuals or set(residuals) != set(scales):
        raise ValueError("trial spatial result lacks aligned wall-element residual and scale arrays")
    ratio = 0.0
    largest_tolerance = 0.0
    nknots = len(spatial_values.get("time_s", []))
    for element, values in residuals.items():
        if len(values) != nknots or len(scales[element]) != nknots:
            raise ValueError("wall-element residuals and scales must align with every exact knot")
        for residual, scale in zip(values, scales[element], strict=True):
            residual = float(residual)
            scale = abs(float(scale))
            if not math.isfinite(residual) or not math.isfinite(scale):
                raise ValueError("wall-element residuals and inventory scales must be finite")
            tolerance = abs_tol + rel_tol * scale
            ratio = max(ratio, abs(residual) / max(tolerance, 1e-300))
            largest_tolerance = max(largest_tolerance, tolerance)
    return ratio, largest_tolerance


def evaluate_wet_co2_cylindrical_scale_recession_feedback(
    request: WetCo2CylindricalScaleRecessionFeedback,
) -> Calculation:
    """Alternate spatial BV, wall saturation kinetics, diffusion cap and cylinder update."""
    source_geometry = request.spatial_request.geometry
    source_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "spatial_model_id": SPATIAL_MODEL_ID,
        "input_sha256": source_digest,
        "asset_id": source_geometry.asset_id,
        "location_id": source_geometry.location_id,
        "time_basis_id": source_geometry.time_basis_id,
        "time_s": [float(row.time_s) for row in source_geometry.history],
        "phase_ids": [row.phase_id for row in source_geometry.phases],
        "iteration_method": "bounded_relaxed_operator_split_bv_scale_transport_geometry.v1",
        "scale_kinetics_transport": "separate_caller_transient_transport_and_wall_activity_paths",
    }
    review_fields = {
        "scale_kinetics_and_transport_are_separate_reviewed_paths": request.scale_kinetics_and_transport_are_separate_reviewed_paths,
        "saturation_standard_state_and_phase_selection_reviewed": request.saturation_standard_state_and_phase_selection_reviewed,
        "diffusion_limited_reactant_supply_mapping_reviewed": request.diffusion_limited_reactant_supply_mapping_reviewed,
        "reaction_stoichiometry_and_phase_formula_reviewed": request.reaction_stoichiometry_and_phase_formula_reviewed,
        "alloy_release_and_scale_volume_geometry_reviewed": request.alloy_release_and_scale_volume_geometry_reviewed,
        "no_unmodeled_aqueous_precipitation_sink_claim_reviewed": request.no_unmodeled_aqueous_precipitation_sink_claim_reviewed,
        "no_inter_knot_or_qualification_claim_reviewed": request.no_inter_knot_or_qualification_claim_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, value in review_fields.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "reason": "caller_review_gates_incomplete", "missing_reviews": missing,
        })

    seed_geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(source_geometry)
    if seed_geometry.status != "computed":
        return Calculation(status=seed_geometry.status, values=base | {
            "reason": "seed_geometry_not_computed", "geometry_result": seed_geometry.model_dump(mode="json"),
        })
    steel_guess = tuple(float(row["steel_inner_radius_m"]) for row in seed_geometry.values["history"])
    inventory_guess = {
        phase.phase_id: tuple(
            next(item.moles_per_axial_metre_mol_m for item in knot.phase_inventories
                 if item.phase_id == phase.phase_id)
            for knot in source_geometry.history
        ) for phase in source_geometry.phases
    }
    iteration_history = []
    converged = False
    last_state = None
    radius_residual_norm = math.inf
    radius_tolerance = 0.0
    scale_residual_ratio = math.inf
    scale_tolerance_max = 0.0
    wall_residual_ratio = math.inf
    wall_tolerance_max = 0.0

    for iteration in range(request.maximum_feedback_iterations):
        try:
            geometry = _geometry_with_inventory_and_steel(
                source_geometry, steel_guess, inventory_guess, iteration=iteration,
            )
            geometry_result = evaluate_wet_co2_cylindrical_scale_geometry_history(geometry)
            if geometry_result.status != "computed":
                raise ValueError(f"trial geometry failed: {geometry_result.values.get('reason')}")
            geometry_sha = canonical_digest(geometry.model_dump(mode="json"))
            iteration_digest = canonical_digest({
                "controller_model_id": MODEL_ID,
                "controller_input_sha256": source_digest,
                "iteration_index": iteration,
                "steel_inner_radius_m_by_knot": list(steel_guess),
                "phase_inventory_mol_m_by_phase": {key: list(value) for key, value in inventory_guess.items()},
                "geometry_sha256": geometry_sha,
            })
            trial_spatial_request = _retarget_spatial_request(
                request.spatial_request, geometry, iteration_digest,
                trial=True,
                wall_abs_tolerance=request.absolute_wall_element_tolerance_mol_m,
                wall_rel_tolerance=request.relative_wall_element_tolerance,
            )
            spatial_trial = evaluate_wet_co2_cylindrical_spatial_mixed_potential(trial_spatial_request)
            if spatial_trial.status != "computed":
                return Calculation(status=spatial_trial.status, values=base | {
                    "reason": "spatial_bv_trial_did_not_compute",
                    "iteration_index": iteration,
                    "trial_values": spatial_trial.values,
                    "iteration_prefix": iteration_history,
                })
            if spatial_trial.values.get("fixed_point_input_sha256") != iteration_digest:
                raise ValueError("spatial result fixed-point digest differs from current geometry trial")

            phase_saturation_results = {}
            for phase_id, saturation_source in request.phase_saturation_kinetics_requests.items():
                saturation_request = _retarget_saturation_request(saturation_source, geometry)
                saturation_result = evaluate_wet_co2_cylindrical_wall_saturation_scale_kinetics(saturation_request)
                if saturation_result.status != "computed":
                    return Calculation(status=saturation_result.status, values=base | {
                        "reason": "phase_saturation_kinetics_did_not_compute",
                        "iteration_index": iteration,
                        "phase_id": phase_id,
                        "saturation_values": saturation_result.values,
                        "iteration_prefix": iteration_history,
                    })
                phase_saturation_results[phase_id] = saturation_result

            multilayer_request = _retarget_multilayer_request(request.multilayer_transport_request, geometry)
            multilayer_result = evaluate_wet_co2_cylindrical_multilayer_transport_resistance(multilayer_request)
            if multilayer_result.status != "computed":
                return Calculation(status=multilayer_result.status, values=base | {
                    "reason": "multilayer_diffusion_supply_calculation_did_not_compute",
                    "iteration_index": iteration,
                    "transport_values": multilayer_result.values,
                    "iteration_prefix": iteration_history,
                })

            phase_growth_results = {}
            inventory_target: dict[str, tuple[float, ...]] = {}
            times = tuple(float(row.time_s) for row in source_geometry.history)
            for phase_id, campaign in request.phase_growth_campaigns.items():
                growth_request = _growth_request(
                    campaign, geometry_result, multilayer_result,
                    phase_saturation_results[phase_id],
                    assessment_id=f"{request.assessment_id}:{phase_id}:{iteration}",
                )
                growth_result = evaluate_wet_co2_cylindrical_diffusion_limited_scale_growth(growth_request)
                if growth_result.status != "computed":
                    return Calculation(status=growth_result.status, values=base | {
                        "reason": "diffusion_limited_phase_inventory_update_did_not_compute",
                        "iteration_index": iteration,
                        "phase_id": phase_id,
                        "growth_values": growth_result.values,
                        "iteration_prefix": iteration_history,
                    })
                rows = growth_result.values.get("history", [])
                if tuple(float(row["time_s"]) for row in rows) != times:
                    raise ValueError(f"{phase_id}: growth inventory history lost exact geometry-knot alignment")
                inventory_target[phase_id] = tuple(
                    float(row["diffusion_limited_phase_inventory_mol_m"]) for row in rows
                )
                if any(not math.isfinite(value) or value < -request.absolute_phase_inventory_tolerance_mol_m
                       for value in inventory_target[phase_id]):
                    raise ValueError(f"{phase_id}: nonfinite or negative computed phase inventory")
                phase_growth_results[phase_id] = {
                    "request_sha256": canonical_digest(growth_request.model_dump(mode="json")),
                    "result": growth_result,
                }

            spatial_values = spatial_trial.values
            bore_target = tuple(float(value) for value in spatial_values["target_bore_radius_m_by_knot"])
            if len(bore_target) != len(times):
                raise ValueError("spatial metal-release target radius does not align with geometry knots")
            steel_target = []
            for index, radius in enumerate(bore_target):
                current_scale_volume = _phase_volume_per_length(geometry, index)
                steel_sq = radius * radius + current_scale_volume / math.pi
                if not math.isfinite(steel_sq) or steel_sq <= 0.0:
                    raise ValueError("BV release target and current phase volume imply invalid steel radius")
                steel_target.append(math.sqrt(steel_sq))
            steel_target_tuple = tuple(steel_target)
            if any(b < a - 1e-12 for a, b in zip(steel_target_tuple, steel_target_tuple[1:])):
                raise ValueError("BV target steel-surface history violates nondecreasing metal recession")
            radius_residual_norm = max(abs(a - b) for a, b in zip(steel_guess, steel_target_tuple, strict=True))
            radius_scale = max(1e-30, *(abs(value) for value in (*steel_guess, *steel_target_tuple)))
            radius_tolerance = request.absolute_radius_tolerance_m + request.relative_radius_tolerance * radius_scale
            scale_residual_ratio, scale_tolerance_max, scale_residuals = _inventory_convergence(
                inventory_guess, inventory_target,
                abs_tol=request.absolute_phase_inventory_tolerance_mol_m,
                rel_tol=request.relative_phase_inventory_tolerance,
            )
            wall_residual_ratio, wall_tolerance_max = _wall_element_residual_ratio(
                spatial_values,
                abs_tol=request.absolute_wall_element_tolerance_mol_m,
                rel_tol=request.relative_wall_element_tolerance,
            )
            iteration_history.append({
                "iteration_index": iteration,
                "fixed_point_input_sha256": iteration_digest,
                "geometry_sha256": geometry_sha,
                "spatial_trial_result_sha256": canonical_digest(spatial_trial.model_dump(mode="json")),
                "multilayer_transport_result_sha256": canonical_digest(multilayer_result.model_dump(mode="json")),
                "phase_saturation_result_sha256": {
                    key: canonical_digest(value.model_dump(mode="json"))
                    for key, value in phase_saturation_results.items()
                },
                "phase_growth_result_sha256": {
                    key: value["result"].values.get("input_sha256")
                    for key, value in phase_growth_results.items()
                },
                "steel_inner_radius_input_m_by_knot": list(steel_guess),
                "steel_inner_radius_target_m_by_knot": list(steel_target_tuple),
                "phase_inventory_residual_mol_m_by_phase": scale_residuals,
                "radius_residual_norm_m": radius_residual_norm,
                "radius_tolerance_m": radius_tolerance,
                "phase_inventory_residual_norm_ratio": scale_residual_ratio,
                "phase_inventory_tolerance_max_mol_m": scale_tolerance_max,
                "wall_element_residual_norm_ratio": wall_residual_ratio,
                "wall_element_tolerance_max_mol_m": wall_tolerance_max,
            })
            last_state = {
                "geometry": geometry,
                "geometry_result": geometry_result,
                "spatial_request": trial_spatial_request,
                "spatial_result": spatial_trial,
                "multilayer_request": multilayer_request,
                "multilayer_result": multilayer_result,
                "saturation_requests": {
                    phase_id: _retarget_saturation_request(source, geometry)
                    for phase_id, source in request.phase_saturation_kinetics_requests.items()
                },
                "saturation_results": phase_saturation_results,
                "growth_results": phase_growth_results,
                "steel_target": steel_target_tuple,
                "inventory_target": inventory_target,
            }
            if (radius_residual_norm <= radius_tolerance
                    and scale_residual_ratio <= 1.0
                    and wall_residual_ratio <= 1.0):
                converged = True
                break
            if iteration + 1 >= request.maximum_feedback_iterations:
                break

            steel_next = tuple(
                current + request.relaxation_factor * (target - current)
                for current, target in zip(steel_guess, steel_target_tuple, strict=True)
            )
            inventory_next = {
                phase_id: tuple(
                    current + request.relaxation_factor * (target - current)
                    for current, target in zip(inventory_guess[phase_id], inventory_target[phase_id], strict=True)
                )
                for phase_id in inventory_guess
            }
            _geometry_with_inventory_and_steel(
                source_geometry, steel_next, inventory_next, iteration=iteration + 1,
            )
            steel_guess = steel_next
            inventory_guess = inventory_next
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "feedback_iteration_failed_closed",
                "iteration_index": iteration,
                "detail": str(exc),
                "iteration_prefix": iteration_history,
            })

    if not converged or last_state is None:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "scale_recession_feedback_iteration_did_not_converge",
            "converged": False,
            "iteration_count": len(iteration_history),
            "final_radius_residual_norm_m": radius_residual_norm,
            "final_radius_tolerance_m": radius_tolerance,
            "final_phase_inventory_residual_norm_ratio": scale_residual_ratio,
            "final_wall_element_residual_norm_ratio": wall_residual_ratio,
            "iteration_history": iteration_history,
            "qualification": "nonconverged operator-split iterations are diagnostics only",
        })

    # Final strict BV calculation on the converged trial geometry. This re-enables
    # element-to-wall geometry closure; the phase inventories remain those of the
    # converged diffusion-limited histories recorded on the same exact knots.
    fixed_final_digest = canonical_digest({
        "controller_input_sha256": source_digest,
        "final_geometry_sha256": canonical_digest(last_state["geometry"].model_dump(mode="json")),
        "iteration_history_sha256": canonical_digest(iteration_history),
        "strict_final_solve": True,
    })
    strict_spatial_request = _retarget_spatial_request(
        request.spatial_request,
        last_state["geometry"],
        fixed_final_digest,
        trial=False,
        wall_abs_tolerance=request.absolute_wall_element_tolerance_mol_m,
        wall_rel_tolerance=request.relative_wall_element_tolerance,
    )
    strict_spatial = evaluate_wet_co2_cylindrical_spatial_mixed_potential(strict_spatial_request)
    if strict_spatial.status != "computed":
        return Calculation(status=strict_spatial.status, values=base | {
            "reason": "final_strict_spatial_wall_geometry_closure_failed",
            "strict_spatial_values": strict_spatial.values,
            "iteration_history": iteration_history,
        })

    final_radius_target = tuple(float(value) for value in strict_spatial.values["target_bore_radius_m_by_knot"])
    current_geometry_rows = last_state["geometry_result"].values["history"]
    final_steel_target = []
    for index, radius in enumerate(final_radius_target):
        steel_sq = radius * radius + _phase_volume_per_length(last_state["geometry"], index) / math.pi
        final_steel_target.append(math.sqrt(steel_sq))
    final_steel_residual = max(abs(a - b) for a, b in zip(
        (float(row["steel_inner_radius_m"]) for row in current_geometry_rows),
        final_steel_target, strict=True,
    ))
    final_radius_tol = request.absolute_radius_tolerance_m + request.relative_radius_tolerance * max(
        1e-30, *(abs(value) for row in current_geometry_rows for value in [float(row["steel_inner_radius_m"])]),
        *(abs(value) for value in final_steel_target),
    )
    if final_steel_residual > final_radius_tol:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "final_strict_solve_left_radius_fixed_point_tolerance",
            "final_radius_residual_norm_m": final_steel_residual,
            "final_radius_tolerance_m": final_radius_tol,
            "iteration_history": iteration_history,
        })

    final_inventory_residuals = {}
    for phase_id, growth_data in last_state["growth_results"].items():
        growth_rows = growth_data["result"].values["history"]
        geometry_inventory = [
            next(row.moles_per_axial_metre_mol_m for row in knot.phase_inventories if row.phase_id == phase_id)
            for knot in last_state["geometry"].history
        ]
        final_inventory_residuals[phase_id] = [
            float(growth_row["diffusion_limited_phase_inventory_mol_m"]) - float(current)
            for growth_row, current in zip(growth_rows, geometry_inventory, strict=True)
        ]

    final_geometry_volume_residuals = []
    for row in current_geometry_rows:
        steel = float(row["steel_inner_radius_m"])
        bore = float(row["bore_radius_m"])
        scale_volume = float(row["scale_volume_per_axial_metre_m2"])
        final_geometry_volume_residuals.append(math.pi * (steel * steel - bore * bore) - scale_volume)

    return Calculation(status="computed", values=base | {
        "input_sha256": source_digest,
        "converged": True,
        "iteration_count": len(iteration_history),
        "iteration_history": iteration_history,
        "final_geometry_sha256": canonical_digest(last_state["geometry"].model_dump(mode="json")),
        "final_geometry_history": current_geometry_rows,
        "final_phase_inventory_mol_m_by_phase": {
            phase_id: list(values) for phase_id, values in inventory_guess.items()
        },
        "final_phase_inventory_fixed_point_residual_mol_m_by_phase": final_inventory_residuals,
        "final_phase_saturation_results": {
            phase_id: result.model_dump(mode="json")
            for phase_id, result in last_state["saturation_results"].items()
        },
        "final_multilayer_transport_result": last_state["multilayer_result"].model_dump(mode="json"),
        "final_phase_growth_results": {
            phase_id: row["result"].model_dump(mode="json")
            for phase_id, row in last_state["growth_results"].items()
        },
        "final_strict_spatial_request_sha256": canonical_digest(strict_spatial_request.model_dump(mode="json")),
        "final_strict_spatial_result_sha256": canonical_digest(strict_spatial.model_dump(mode="json")),
        "final_strict_spatial_result": strict_spatial.values,
        "final_steel_radius_fixed_point_residual_m": final_steel_residual,
        "final_steel_radius_tolerance_m": final_radius_tol,
        "geometry_volume_closure_residual_m2_by_knot": final_geometry_volume_residuals,
        "coupling_scope": "iterated_bv_recession_plus_activity_kinetics_limited_cylindrical_scale_inventory",
        "aqueous_scale_sink_feedback": False,
        "scale_elemental_inventory_from_solid_formula": {
            phase_id: {
                element: [
                    float(inventory) * float(solid.elemental_composition.get(element, 0.0))
                    for inventory in inventory_guess[phase_id]
                ]
                for element in request.phase_saturation_kinetics_requests[phase_id].solid_elemental_composition
            }
            for phase_id, solid in request.phase_saturation_kinetics_requests.items()
        },
        "qualification": "bounded caller-calibrated operator-split model; no independent experimental or field qualification",
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalScaleRecessionFeedback,
        evaluator=evaluate_wet_co2_cylindrical_scale_recession_feedback,
        units={
            "time_s[]": "s",
            "final_geometry_history[].bore_radius_m": "m",
            "final_phase_inventory_mol_m_by_phase.*[]": "mol/m",
            "final_phase_inventory_fixed_point_residual_mol_m_by_phase.*[]": "mol/m",
            "final_steel_radius_fixed_point_residual_m": "m",
            "geometry_volume_closure_residual_m2_by_knot[]": "m^2",
        },
        assumptions=(
            "Every outer iteration recalculates spatial BV transport, phase saturation and wall kinetics, multilayer cylindrical diffusion supply, phase inventory and common wall geometry.",
            "Phase kinetic and diffusion paths use caller-declared, independently reviewed transport inputs on identical exact geometry knots.",
            "Precipitation/dissolution inventory uses left-held flux and the corresponding left-knot cylinder area; scale inventory is not added as an aqueous reaction sink in the BV transport solve.",
            "The outer relaxed iteration is bounded and followed by a final strict metal wall geometry closure solve; no contraction or uniqueness guarantee is claimed.",
            "All phase selection, activity, solubility, kinetic coefficients, reactant supply mapping, alloy composition and cylindrical assumptions are caller supplied.",
        ),
        source_ids=(
            SOURCE_ID,
            "independent_transient_cylindrical_finite_volume_electrochemical_inventory",
            "caller_cylindrical_transient_species_history_for_wall_saturation",
            "caller_wet_co2_wall_saturation_scale_kinetics_result",
            "caller_cylindrical_phase_solution_diffusivity_records",
            "cylindrical_multilayer_radial_diffusion_resistance",
            "independent_cylindrical_annular_scale_inventory_volume_closure",
        ),
        qualification="user_model",
    ),)
