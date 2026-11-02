"""Evidence-bound adapter for dynamic node results from ``lh2dt_models``.

The upstream package is optional. This module consumes its public result
objects by attribute inspection and does not import or copy upstream code.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from .registry import ModelSpec

MODEL_ID = "integration.lh2dt_dynamic_network_node_state_history"
SOURCE_ID = "lyullee_lh2dt_dynamic_network_public_result_contract"
UPSTREAM_REPOSITORY = "lyullee/lh2dt_models"


class LH2DTNodeThermoPoint(Contract):
    """One caller-mapped thermodynamic node state at an accepted time point."""

    time_s: Nonnegative
    pressure_Pa: Positive
    temperature_K: Positive
    density_kg_m3: Positive
    specific_enthalpy_J_kg: float
    specific_internal_energy_J_kg: float
    specific_entropy_J_kgK: float
    quality: float | None = Field(default=None, ge=0.0, le=1.0)
    phase: str = Field(min_length=1)
    node_mass_flow_kg_s: float
    pressure_solver_success: bool
    junction_conservation_success: bool

    @model_validator(mode="after")
    def finite_state(self):
        for name in (
            "specific_enthalpy_J_kg",
            "specific_internal_energy_J_kg",
            "specific_entropy_J_kgK",
            "node_mass_flow_kg_s",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not math.isfinite(value):
                raise ValueError(f"{name} must be finite numeric data")
        return self


class LH2DTNodeStateHistory(Contract):
    """Pinned upstream run and an explicitly mapped node-state time series."""

    schema_version: Literal["matintegrity.lh2dt_node_state_history.v1"] = (
        "matintegrity.lh2dt_node_state_history.v1"
    )
    model_id: Literal["integration.lh2dt_dynamic_network_node_state_history"] = MODEL_ID
    upstream_repository: Literal["lyullee/lh2dt_models"] = UPSTREAM_REPOSITORY
    upstream_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    upstream_package_version: str = Field(min_length=1)
    source_run_id: str = Field(min_length=1)
    upstream_result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    upstream_configuration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    node_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    points: tuple[LH2DTNodeThermoPoint, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    node_to_physical_asset_mapping_reviewed: bool
    fluid_and_material_scope_reviewed: bool
    upstream_convergence_reviewed: bool

    @model_validator(mode="after")
    def ordered_history(self):
        times = [point.time_s for point in self.points]
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("node-state timestamps must be strictly increasing")
        return self


def adapt_lh2dt_dynamic_network_steps(
    steps: Iterable[object],
    *,
    upstream_revision: str,
    upstream_package_version: str,
    source_run_id: str,
    upstream_result_sha256: str,
    upstream_configuration_sha256: str,
    node_id: str,
    asset_id: str,
    location_id: str,
    material_condition_id: str,
    clock_id: str,
    evidence: tuple[Evidence, ...],
    node_to_physical_asset_mapping_reviewed: bool,
    fluid_and_material_scope_reviewed: bool,
    upstream_convergence_reviewed: bool,
) -> LH2DTNodeStateHistory:
    """Translate public ``DynamicNetworkStepResult``-like objects to a contract.

    Attribute names match the upstream public result object. The adapter does
    not infer material-wall temperature, chemistry, phase-specific composition,
    corrosion rate, or a physical location from a network node name.
    """
    points: list[LH2DTNodeThermoPoint] = []
    for index, step in enumerate(steps):
        try:
            state = step.thermo_states[node_id]
            solution = step.network_solution
            points.append(
                LH2DTNodeThermoPoint(
                    time_s=step.time_s,
                    pressure_Pa=state.pressure_Pa,
                    temperature_K=state.temperature_K,
                    density_kg_m3=state.density_kg_m3,
                    specific_enthalpy_J_kg=state.specific_enthalpy_J_kg,
                    specific_internal_energy_J_kg=state.specific_internal_energy_J_kg,
                    specific_entropy_J_kgK=state.specific_entropy_J_kgK,
                    quality=state.quality,
                    phase=state.phase,
                    node_mass_flow_kg_s=step.node_mass_flow_kg_s[node_id],
                    pressure_solver_success=solution.pressure_solver_success,
                    junction_conservation_success=solution.junction_conservation_success,
                )
            )
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"upstream step {index} lacks the required node thermodynamic/convergence fields"
            ) from exc

    return LH2DTNodeStateHistory(
        upstream_revision=upstream_revision,
        upstream_package_version=upstream_package_version,
        source_run_id=source_run_id,
        upstream_result_sha256=upstream_result_sha256,
        upstream_configuration_sha256=upstream_configuration_sha256,
        node_id=node_id,
        asset_id=asset_id,
        location_id=location_id,
        material_condition_id=material_condition_id,
        clock_id=clock_id,
        points=tuple(points),
        evidence=evidence,
        node_to_physical_asset_mapping_reviewed=node_to_physical_asset_mapping_reviewed,
        fluid_and_material_scope_reviewed=fluid_and_material_scope_reviewed,
        upstream_convergence_reviewed=upstream_convergence_reviewed,
    )


def evaluate_lh2dt_dynamic_network_node_state_history(
    request: LH2DTNodeStateHistory,
) -> Calculation:
    """Return only reviewed, upstream-converged node thermodynamic history."""
    missing = [
        name
        for name, reviewed in (
            ("node_to_physical_asset_mapping", request.node_to_physical_asset_mapping_reviewed),
            ("fluid_and_material_scope", request.fluid_and_material_scope_reviewed),
            ("upstream_convergence", request.upstream_convergence_reviewed),
        )
        if not reviewed
    ]
    if missing:
        return Calculation(
            status="needs_data",
            values={"source_run_id": request.source_run_id, "missing_reviews": missing},
            notes=("The mapped node history is withheld until all lineage and applicability reviews are complete.",),
        )
    failed = [
        index
        for index, point in enumerate(request.points)
        if not point.pressure_solver_success or not point.junction_conservation_success
    ]
    if failed:
        return Calculation(
            status="needs_data",
            values={"source_run_id": request.source_run_id, "failed_point_indices": failed},
            notes=("No thermodynamic exposure history is released when an upstream step lacks solver/conservation success.",),
        )
    return Calculation(
        values={
            "source_run_id": request.source_run_id,
            "upstream_repository": request.upstream_repository,
            "upstream_revision": request.upstream_revision,
            "upstream_package_version": request.upstream_package_version,
            "upstream_result_sha256": request.upstream_result_sha256,
            "upstream_configuration_sha256": request.upstream_configuration_sha256,
            "node_id": request.node_id,
            "asset_id": request.asset_id,
            "location_id": request.location_id,
            "material_condition_id": request.material_condition_id,
            "clock_id": request.clock_id,
            "point_count": len(request.points),
            "points": [point.model_dump(mode="json") for point in request.points],
            "calculation_source_id": SOURCE_ID,
        },
        notes=(
            "The adapter preserves bulk-fluid node states only; it does not infer wall conditions or material response.",
            "A successfully transferred process state is not a corrosion, hydrogen-attack, embrittlement, damage, life, or acceptance result.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            MODEL_ID,
            LH2DTNodeStateHistory,
            evaluate_lh2dt_dynamic_network_node_state_history,
            {"point_count": "1", "pressure_Pa": "Pa", "temperature_K": "K"},
            (
                "The upstream result revision, run result, and configuration digests are caller-pinned.",
                "Node-to-asset and fluid/material applicability mappings are explicitly reviewed by the caller.",
                "The result contains bulk-fluid states and does not represent material-wall conditions.",
            ),
            (SOURCE_ID,),
        )
    ]

