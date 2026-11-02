from __future__ import annotations

import math
from typing import Literal

from pydantic import Field

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalGeometryKnot,
    WetCo2CylindricalScaleGeometryHistory,
    WetCo2ScalePhaseLineInventory,
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)
from .wet_co2_cylindrical_transient_transport import (
    WetCo2CylindricalTransientTransport,
    evaluate_wet_co2_cylindrical_transient_transport,
)
from .wet_co2_cylindrical_multilayer_transport import (
    WetCo2CylindricalMultilayerTransportResistance,
    evaluate_wet_co2_cylindrical_multilayer_transport_resistance,
)
from .wet_co2_cylindrical_wall_saturation_scale_kinetics import (
    WetCo2CylindricalWallSaturationScaleKinetics,
    evaluate_wet_co2_cylindrical_wall_saturation_scale_kinetics,
)
from .wet_co2_cylindrical_diffusion_limited_scale_growth import (
    WetCo2CylindricalDiffusionLimitedScaleGrowth,
    evaluate_wet_co2_cylindrical_diffusion_limited_scale_growth,
)

MODEL_ID = "integration.wet_co2_cylindrical_coupled_scale_geometry_replay"
GEOMETRY_SOURCE_ID = "caller_cylindrical_geometry_iteration_seed"
COUPLING_SOURCE_ID = "bounded_picard_replay_of_caller_transport_saturation_and_scale_growth"


class WetCo2CylindricalCoupledScaleGeometryReplay(Contract):
    """Bounded explicit replay of geometry-dependent caller wet-CO2 submodels."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_coupled_scale_geometry_replay.v1"] = (
        "matintegrity.wet_co2_cylindrical_coupled_scale_geometry_replay.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    geometry_seed: WetCo2CylindricalScaleGeometryHistory
    transient_transport_template: WetCo2CylindricalTransientTransport
    multilayer_transport_template: WetCo2CylindricalMultilayerTransportResistance
    saturation_kinetics_template: WetCo2CylindricalWallSaturationScaleKinetics
    diffusion_limited_growth_template: WetCo2CylindricalDiffusionLimitedScaleGrowth
    selected_solid_id: str = Field(min_length=1, max_length=160)
    inventory_absolute_tolerance_mol_m: Positive = 1e-10
    inventory_relative_tolerance: Positive = Field(default=1e-6, le=1e-2)
    maximum_iterations: int = Field(default=12, ge=1, le=50)
    iteration_budget_verified: bool
    result_lineage_and_area_basis_reviewed: bool

    def validate_template_identity(self):
        if self.selected_solid_id not in {row.phase_id for row in self.geometry_seed.phases}:
            raise ValueError("selected solid must be a declared phase in the geometry seed")
        for request in (self.transient_transport_template, self.multilayer_transport_template):
            if request.geometry.asset_id != self.geometry_seed.asset_id or request.geometry.location_id != self.geometry_seed.location_id:
                raise ValueError("transport templates must share the geometry seed asset and location")
        if self.saturation_kinetics_template.candidate_solid_id != self.selected_solid_id:
            raise ValueError("selected solid must match the saturation/kinetics template")
        if self.diffusion_limited_growth_template.solid_id != self.selected_solid_id:
            raise ValueError("selected solid must match the growth ledger template")
        return self


def _geometry_with_inventories(
    geometry: WetCo2CylindricalScaleGeometryHistory,
    phase_inventories_by_knot: list[dict[str, float]],
    iteration: int,
) -> WetCo2CylindricalScaleGeometryHistory:
    rows = []
    phase_ids = [row.phase_id for row in geometry.phases]
    for knot, inventories in zip(geometry.history, phase_inventories_by_knot, strict=True):
        rows.append(WetCo2CylindricalGeometryKnot(
            time_s=knot.time_s,
            wall_recession_m=knot.wall_recession_m,
            phase_inventories=tuple(WetCo2ScalePhaseLineInventory(
                phase_id=phase_id,
                moles_per_axial_metre_mol_m=inventories[phase_id],
            ) for phase_id in phase_ids),
        ))
    row_payload = [row.model_dump(mode="json") for row in rows]
    row_digest = canonical_digest(row_payload)
    prior_license = geometry.history_evidence.license_id
    payload = geometry.model_dump(mode="json")
    payload.update({
        "history": row_payload,
        "history_provider_id": MODEL_ID,
        "history_provider_revision": f"bounded_picard_iteration_{iteration}",
        "history_record_sha256": row_digest,
        "history_evidence": Evidence(
            source_id=MODEL_ID,
            origin="model_prediction",
            citation="Derived geometry inventory iterate from the caller's coupled wet-CO2 replay inputs.",
            license_id=prior_license,
            sha256=row_digest,
        ).model_dump(mode="json"),
    })
    return WetCo2CylindricalScaleGeometryHistory.model_validate(payload)


def _rebind_transient(
    request: WetCo2CylindricalTransientTransport,
    geometry: WetCo2CylindricalScaleGeometryHistory,
) -> WetCo2CylindricalTransientTransport:
    payload = request.model_dump(mode="json")
    payload["geometry"] = geometry.model_dump(mode="json")
    payload["geometry_sha256"] = canonical_digest(geometry.model_dump(mode="json"))
    return WetCo2CylindricalTransientTransport.model_validate(payload)


def _rebind_multilayer(
    request: WetCo2CylindricalMultilayerTransportResistance,
    geometry: WetCo2CylindricalScaleGeometryHistory,
) -> WetCo2CylindricalMultilayerTransportResistance:
    payload = request.model_dump(mode="json")
    payload["geometry"] = geometry.model_dump(mode="json")
    payload["geometry_sha256"] = canonical_digest(geometry.model_dump(mode="json"))
    return WetCo2CylindricalMultilayerTransportResistance.model_validate(payload)


def _rebind_saturation(
    request: WetCo2CylindricalWallSaturationScaleKinetics,
    transport: WetCo2CylindricalTransientTransport,
) -> WetCo2CylindricalWallSaturationScaleKinetics:
    payload = request.model_dump(mode="json")
    payload["transport_request"] = transport.model_dump(mode="json")
    payload["transport_request_sha256"] = canonical_digest(transport.model_dump(mode="json"))
    return WetCo2CylindricalWallSaturationScaleKinetics.model_validate(payload)


def _rebind_growth(
    request: WetCo2CylindricalDiffusionLimitedScaleGrowth,
    geometry_result: Calculation,
    transport_result: Calculation,
    saturation_result: Calculation,
) -> WetCo2CylindricalDiffusionLimitedScaleGrowth:
    payload = request.model_dump(mode="json")
    payload["geometry_result"] = geometry_result.model_dump(mode="json")
    payload["multilayer_transport_result"] = transport_result.model_dump(mode="json")
    payload["saturation_scale_kinetics_result"] = saturation_result.model_dump(mode="json")
    return WetCo2CylindricalDiffusionLimitedScaleGrowth.model_validate(payload)


def _inventory_rows(geometry: WetCo2CylindricalScaleGeometryHistory) -> list[dict[str, float]]:
    return [{row.phase_id: row.moles_per_axial_metre_mol_m for row in knot.phase_inventories}
            for knot in geometry.history]


def evaluate_wet_co2_cylindrical_coupled_scale_geometry_replay(
    request: WetCo2CylindricalCoupledScaleGeometryReplay,
) -> Calculation:
    """Iterate transport and scale-growth submodels, committing only tolerance-converged geometry."""
    request.validate_template_identity()
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry_seed.asset_id,
        "location_id": request.geometry_seed.location_id,
        "model_id": MODEL_ID,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "geometry_seed_sha256": canonical_digest(request.geometry_seed.model_dump(mode="json")),
        "selected_solid_id": request.selected_solid_id,
        "source_ids": [GEOMETRY_SOURCE_ID, COUPLING_SOURCE_ID],
    }
    if not request.iteration_budget_verified or not request.result_lineage_and_area_basis_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "iteration_budget_lineage_and_growth_area_review_required",
        })
    current = request.geometry_seed
    seed_inventories = _inventory_rows(current)
    iteration_summaries = []
    last_ledger = None
    last_geometry_result = None
    committed_prefix = 0
    final_candidate = None
    for iteration in range(1, request.maximum_iterations + 1):
        geometry_result = evaluate_wet_co2_cylindrical_scale_geometry_history(current)
        if geometry_result.status != "computed":
            return Calculation(status=geometry_result.status, values=base | {
                "reason": "geometry_replay_iteration_not_computed",
                "failed_iteration": iteration,
                "committed_prefix_knot_count": committed_prefix,
                "last_attempted_geometry_result_sha256": canonical_digest(last_geometry_result.model_dump(mode="json")) if last_geometry_result else None,
                "geometry_result": geometry_result.model_dump(mode="json"),
                "iteration_summaries": iteration_summaries,
            })
        try:
            transient_request = _rebind_transient(request.transient_transport_template, current)
            multilayer_request = _rebind_multilayer(request.multilayer_transport_template, current)
            saturation_request = _rebind_saturation(request.saturation_kinetics_template, transient_request)
            transient_result = evaluate_wet_co2_cylindrical_transient_transport(transient_request)
            multilayer_result = evaluate_wet_co2_cylindrical_multilayer_transport_resistance(multilayer_request)
            saturation_result = evaluate_wet_co2_cylindrical_wall_saturation_scale_kinetics(saturation_request)
            if any(result.status != "computed" for result in (transient_result, multilayer_result, saturation_result)):
                failed = next(result for result in (transient_result, multilayer_result, saturation_result)
                              if result.status != "computed")
                return Calculation(status=failed.status, values=base | {
                    "reason": "nested_transport_or_saturation_iteration_not_computed",
                    "failed_iteration": iteration,
                    "committed_prefix_knot_count": committed_prefix,
                    "last_attempted_geometry_result_sha256": canonical_digest(last_geometry_result.model_dump(mode="json")) if last_geometry_result else None,
                    "nested_result": failed.model_dump(mode="json"),
                    "iteration_summaries": iteration_summaries,
                })
            growth_request = _rebind_growth(request.diffusion_limited_growth_template,
                                           geometry_result, multilayer_result, saturation_result)
            ledger = evaluate_wet_co2_cylindrical_diffusion_limited_scale_growth(growth_request)
            if ledger.status != "computed":
                return Calculation(status=ledger.status, values=base | {
                    "reason": "diffusion_limited_growth_ledger_iteration_not_computed",
                    "failed_iteration": iteration,
                    "committed_prefix_knot_count": committed_prefix,
                    "last_attempted_geometry_result_sha256": canonical_digest(last_geometry_result.model_dump(mode="json")) if last_geometry_result else None,
                    "growth_ledger": ledger.model_dump(mode="json"),
                    "iteration_summaries": iteration_summaries,
                })
        except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
            return Calculation(status="needs_data", values=base | {
                "reason": "replay_input_rebinding_failed_closed",
                "failed_iteration": iteration,
                "detail": str(exc),
                "committed_prefix_knot_count": committed_prefix,
                "iteration_summaries": iteration_summaries,
            })
        ledger_rows = ledger.values["history"]
        candidate_rows = _inventory_rows(current)
        current_rows = _inventory_rows(current)
        selected = request.selected_solid_id
        residuals = []
        for index, row in enumerate(ledger_rows):
            candidate_rows[index][selected] = float(row["diffusion_limited_phase_inventory_mol_m"])
            old_value = current_rows[index][selected]
            new_value = candidate_rows[index][selected]
            difference = new_value - old_value
            allowed = request.inventory_absolute_tolerance_mol_m + request.inventory_relative_tolerance * max(abs(new_value), abs(old_value))
            residuals.append({
                "time_s": float(row["time_s"]),
                "previous_inventory_mol_m": old_value,
                "candidate_inventory_mol_m": new_value,
                "residual_mol_m": difference,
                "allowed_residual_mol_m": allowed,
                "converged": abs(difference) <= allowed,
            })
        prefix = 0
        for row in residuals:
            if not row["converged"]:
                break
            prefix += 1
        committed_prefix = prefix
        candidate = _geometry_with_inventories(current, candidate_rows, iteration)
        iteration_summaries.append({
            "iteration": iteration,
            "geometry_result_sha256": canonical_digest(geometry_result.model_dump(mode="json")),
            "transport_result_sha256": canonical_digest(transient_result.model_dump(mode="json")),
            "multilayer_transport_result_sha256": canonical_digest(multilayer_result.model_dump(mode="json")),
            "saturation_result_sha256": canonical_digest(saturation_result.model_dump(mode="json")),
            "growth_ledger_sha256": canonical_digest(ledger.model_dump(mode="json")),
            "converged_prefix_knot_count": prefix,
            "maximum_inventory_residual_mol_m": max((abs(row["residual_mol_m"]) for row in residuals), default=0.0),
        })
        last_ledger = ledger
        last_geometry_result = geometry_result
        final_candidate = candidate
        if prefix == len(residuals):
            return Calculation(values=base | {
                "status": "computed",
                "converged": True,
                "iteration_count": iteration,
                "converged_geometry": candidate.model_dump(mode="json"),
                "converged_geometry_sha256": canonical_digest(candidate.model_dump(mode="json")),
                "geometry_result_sha256": canonical_digest(geometry_result.model_dump(mode="json")),
                "last_transport_result_sha256": canonical_digest(transient_result.model_dump(mode="json")),
                "last_multilayer_transport_result_sha256": canonical_digest(multilayer_result.model_dump(mode="json")),
                "last_saturation_result_sha256": canonical_digest(saturation_result.model_dump(mode="json")),
                "growth_ledger": ledger.model_dump(mode="json"),
                "iteration_summaries": iteration_summaries,
                "committed_prefix_knot_count": len(residuals),
                "limitations": [
                    "This is bounded Picard replay of explicit caller models, not a monolithic solver or a validated corrosion model.",
                    "Only one caller-selected solid inventory is updated; other phase histories and wall recession remain fixed from the geometry seed.",
                    "Transient species transport, multilayer steady resistance, saturation, caller kinetics and growth ledger are rerun in sequence; within-iteration feedback is absent.",
                    "The iteration commits only when every exact-knot solid-inventory residual satisfies the declared absolute-plus-relative tolerance.",
                    "Only converged states are returned as committed; there is no extrapolation, automatic speciation, phase discovery, or material qualification.",
                ],
            })
        current = candidate
    return Calculation(status="needs_data", values=base | {
        "reason": "maximum_replay_iterations_reached_without_full_convergence",
        "converged": False,
        "maximum_iterations": request.maximum_iterations,
        "committed_prefix_knot_count": committed_prefix,
        "committed_prefix_inventory_rows": (last_ledger.values.get("history", [])[:committed_prefix]
                                             if last_ledger is not None else []),
        "last_geometry_result_sha256": canonical_digest(last_geometry_result.model_dump(mode="json")) if last_geometry_result else None,
        "uncommitted_candidate_geometry_sha256": canonical_digest(final_candidate.model_dump(mode="json")) if final_candidate else None,
        "iteration_summaries": iteration_summaries,
        "limitations": [
            "No unconverged candidate geometry is committed or suitable for downstream calculation.",
            "Any committed prefix is diagnostic and must be explicitly reviewed before reuse; no full assessment result exists.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalCoupledScaleGeometryReplay,
        evaluator=evaluate_wet_co2_cylindrical_coupled_scale_geometry_replay,
        units={
            "inventory_absolute_tolerance_mol_m": "mol/m",
            "iteration_summaries[].maximum_inventory_residual_mol_m": "mol/m",
        },
        assumptions=(
            "The caller supplies all state, thermodynamic, kinetics, stoichiometry, transport and diffusivity records.",
            "Only the selected solid's per-axial-metre inventory is iterated; wall recession and other phase inventories are fixed.",
            "Exact-knot geometry, transport, saturation, and flux-limited growth are replayed until all inventory knots meet tolerance or budget ends.",
        ),
        source_ids=(GEOMETRY_SOURCE_ID, COUPLING_SOURCE_ID),
        runtime_dependency_names=("scipy",),
        qualification="user_model",
    )]



