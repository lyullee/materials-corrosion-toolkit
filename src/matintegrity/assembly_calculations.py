"""Explicit tube-layout, tube-inventory and elastic joint calculations."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class TubeLayout(Contract):
    tube_outer_diameter_m: Positive
    pitch_m: Positive
    layout: Literal["square", "triangular"]
    tube_count: int = Field(gt=0)
    tube_inner_diameter_m: Positive

    @model_validator(mode="after")
    def geometry(self):
        if (
            self.pitch_m <= self.tube_outer_diameter_m
            or self.tube_inner_diameter_m >= self.tube_outer_diameter_m
        ):
            raise ValueError("tube pitch/diameters must leave positive ligament and wall")
        return self


def tube_layout_geometry(request: TubeLayout) -> dict:
    cell = request.pitch_m**2 * (1.0 if request.layout == "square" else math.sqrt(3.0) / 2.0)
    metal = math.pi * request.tube_outer_diameter_m**2 / 4.0
    return dict(
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        ligament_m=request.pitch_m - request.tube_outer_diameter_m,
        ligament_fraction=(request.pitch_m - request.tube_outer_diameter_m) / request.pitch_m,
        ideal_lattice_void_fraction=(cell - metal) / cell,
        tube_side_flow_area_m2=request.tube_count * math.pi * request.tube_inner_diameter_m**2 / 4.0,
        basis="Infinite regular lattice void fraction; no shell/baffle clearance or pressure-drop model.",
    )


class TubeCondition(Contract):
    tube_id: str = Field(min_length=1)
    inner_diameter_m: Positive
    reference_wall_m: Positive
    minimum_wall_m: Nonnegative
    plugged: bool

    @model_validator(mode="after")
    def wall(self):
        if self.minimum_wall_m > self.reference_wall_m:
            raise ValueError("minimum wall exceeds declared reference wall")
        return self


def tube_bundle_inventory(tubes: tuple[TubeCondition, ...]) -> dict:
    if not tubes or len({tube.tube_id for tube in tubes}) != len(tubes):
        raise ValueError("bundle requires nonempty uniquely identified tubes")
    active = tuple(tube for tube in tubes if not tube.plugged)
    return dict(
        total_tube_count=len(tubes),
        active_tube_count=len(active),
        plugged_tube_count=len(tubes) - len(active),
        active_flow_area_m2=math.fsum(math.pi * tube.inner_diameter_m**2 / 4 for tube in active),
        wall_loss_fraction_by_tube={
            tube.tube_id: 1 - tube.minimum_wall_m / tube.reference_wall_m for tube in tubes
        },
        basis="Geometric inventory only; wall loss does not establish tube capacity or leakage.",
    )


class ElasticJointLoad(Contract):
    initial_bolt_force_N: Nonnegative
    bolt_stiffness_N_m: Positive
    clamped_stiffness_N_m: Positive
    external_separating_force_N: Nonnegative
    free_clamped_minus_bolt_expansion_m: float
    linear_contact_applicability_reviewed: bool


def elastic_joint_load(request: ElasticJointLoad) -> dict:
    if not request.linear_contact_applicability_reviewed:
        return dict(status="needs_data")
    kb, km = request.bolt_stiffness_N_m, request.clamped_stiffness_N_m
    scale = max(kb, km)
    denominator = kb / scale + km / scale
    bolt_share = (kb / scale) / denominator
    clamp_share = (km / scale) / denominator
    series_stiffness = min(kb, km) / (1.0 + min(kb, km) / max(kb, km))
    thermal = series_stiffness * request.free_clamped_minus_bolt_expansion_m
    preload = request.initial_bolt_force_N + thermal
    bolt = preload + bolt_share * request.external_separating_force_N
    clamp = preload - clamp_share * request.external_separating_force_N
    if not all(math.isfinite(value) for value in (thermal, preload, bolt, clamp)):
        return dict(status="out_of_scope", reason="Linear joint force exceeds finite numeric support")
    if preload < 0 or clamp < 0:
        return dict(
            status="out_of_scope",
            linear_contact_loss_predicted=True,
            unclipped_bolt_force_N=bolt,
            unclipped_clamp_force_N=clamp,
        )
    return dict(
        status="computed",
        bolt_force_N=bolt,
        clamp_force_N=clamp,
        thermal_preload_change_N=thermal,
        basis="Linear two-spring closed-contact model; no gasket nonlinearity, creep relaxation or acceptance.",
    )
