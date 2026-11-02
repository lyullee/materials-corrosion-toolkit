"""Two-electrode galvanic coupling with a finite caller-owned series resistance."""

from __future__ import annotations

import math
from itertools import product
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .galvanic_coupling import (
    GalvanicElectrodeEvidence,
    GalvanicEnvironment,
    PartialDissolutionObservation,
)


class ResistanceComponent(Contract):
    component_id: str = Field(min_length=1)
    component_kind: Literal["electrolyte", "contact", "lead", "caller_other"]
    resistance_ohm: Nonnegative
    basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ResistiveGalvanicConnection(Contract):
    connection_id: str = Field(min_length=1)
    components: tuple[ResistanceComponent, ...] = Field(min_length=1)
    declared_total_series_resistance_ohm: Positive
    component_sum_tolerance_ohm: Nonnegative = 1e-12
    connection_reviewed: bool

    @model_validator(mode="after")
    def unique_components(self):
        identities = [item.component_id for item in self.components]
        if len(identities) != len(set(identities)):
            raise ValueError("resistance component identities must be unique")
        return self


class ResistiveGalvanicCoupling(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    environment: GalvanicEnvironment
    electrodes: tuple[GalvanicElectrodeEvidence, GalvanicElectrodeEvidence]
    connection: ResistiveGalvanicConnection
    partial_dissolution_observations: tuple[PartialDissolutionObservation, ...] = ()
    solver_id: Literal["matintegrity.two_electrode_piecewise_resistive_balance.v1"]
    solver_revision: str = Field(min_length=1)
    quasi_steady_reviewed: bool
    condition_compatibility_reviewed: bool
    common_reference_reviewed: bool
    anodic_positive_net_current_reviewed: bool
    caller_reviewed: bool
    absolute_current_balance_tolerance_A: Nonnegative = 1e-12
    absolute_voltage_balance_tolerance_V: Nonnegative = 1e-12
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_evidence(self):
        electrode_ids = [item.electrode_id for item in self.electrodes]
        if len(set(electrode_ids)) != 2:
            raise ValueError("resistive coupling requires two distinct electrode identities")
        if self.electrodes[0].polarization_curve.curve_id == self.electrodes[1].polarization_curve.curve_id:
            raise ValueError("resistive coupling requires distinct polarization curve identities")
        observation_ids = [item.observation_id for item in self.partial_dissolution_observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("partial dissolution observation identities must be unique")
        if any(item.electrode_id not in electrode_ids for item in self.partial_dissolution_observations):
            raise ValueError("partial dissolution observations must reference a coupled electrode")
        return self


def _segment_coefficients(electrode: GalvanicElectrodeEvidence) -> list[tuple[float, float, float, float]]:
    curve = electrode.polarization_curve
    segments = []
    for index in range(len(curve.potential_V) - 1):
        left, right = curve.potential_V[index : index + 2]
        current_left, current_right = curve.signed_net_current_density_A_m2[index : index + 2]
        density_slope = (current_right - current_left) / (right - left)
        density_intercept = current_left - density_slope * left
        segments.append(
            (
                left,
                right,
                electrode.exposed_area_m2 * density_slope,
                electrode.exposed_area_m2 * density_intercept,
            )
        )
    return segments


def resistive_galvanic_coupling(x: ResistiveGalvanicCoupling) -> Calculation:
    """Solve all piecewise-linear two-electrode equilibria without curve extrapolation."""
    input_digest = canonical_digest(x.model_dump(mode="json"))
    resistance = x.connection.declared_total_series_resistance_ohm
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "environment_id": x.environment.environment_id,
        "solver_id": x.solver_id,
        "solver_revision": x.solver_revision,
        "input_digest": input_digest,
        "declared_total_series_resistance_ohm": resistance,
        "equilibria": [],
        "electrode_interface_potential_V": None,
        "signed_net_electrode_current_A": None,
        "series_voltage_drop_V": None,
        "partial_dissolution_observations": [
            item.model_dump(mode="json") for item in x.partial_dissolution_observations
        ],
    }
    notes = (
        "The two interface potentials may differ by the signed net current times the declared series resistance; no curve is extrapolated.",
        "Signed net external electrode current is distinct from partial dissolution current and is not converted to metal loss or corrosion rate.",
        "The algebraic quasi-steady solution does not establish dynamic stability, acceptance, remaining life, or failure probability.",
    )

    def result(
        status: Literal["computed", "needs_data", "out_of_scope"], reason: str, **values: object
    ) -> Calculation:
        return Calculation(status=status, values=base | {"reason": reason} | values, notes=notes)

    reviews = {
        "caller_reviewed": x.caller_reviewed,
        "quasi_steady_reviewed": x.quasi_steady_reviewed,
        "condition_compatibility_reviewed": x.condition_compatibility_reviewed,
        "common_reference_reviewed": x.common_reference_reviewed,
        "anodic_positive_net_current_reviewed": x.anodic_positive_net_current_reviewed,
        "connection_reviewed": x.connection.connection_reviewed,
        "curve_support_reviewed": all(item.curve_support_reviewed for item in x.electrodes),
    }
    unreviewed = [name for name, reviewed in reviews.items() if not reviewed]
    if unreviewed:
        return result("needs_data", "unreviewed_applicability", unreviewed=unreviewed)

    component_sum = math.fsum(item.resistance_ohm for item in x.connection.components)
    if abs(component_sum - resistance) > x.connection.component_sum_tolerance_ohm:
        return result(
            "needs_data",
            "resistance_component_sum_mismatch",
            component_sum_ohm=component_sum,
            component_sum_residual_ohm=component_sum - resistance,
        )

    expected_condition = (
        x.environment.electrolyte_id,
        x.environment.reference_electrode_id,
        x.environment.temperature_K,
    )
    for electrode in x.electrodes:
        curve = electrode.polarization_curve
        if curve.current_convention != "anodic_positive_net":
            return result("needs_data", "unreviewed_current_convention", electrode_id=electrode.electrode_id)
        observed_condition = (
            curve.electrolyte_id,
            curve.reference_electrode_id,
            curve.temperature_K,
        )
        if any(value is None for value in observed_condition):
            return result("needs_data", "missing_curve_environment", electrode_id=electrode.electrode_id)
        if observed_condition != expected_condition:
            return result("out_of_scope", "curve_environment_mismatch", electrode_id=electrode.electrode_id)

    candidates: list[dict[str, object]] = []
    nonunique_segment_pairs: list[list[int]] = []
    segment_sets = [_segment_coefficients(item) for item in x.electrodes]
    for (first_index, first), (second_index, second) in product(
        enumerate(segment_sets[0]), enumerate(segment_sets[1])
    ):
        first_left, first_right, first_slope, first_intercept = first
        second_left, second_right, second_slope, second_intercept = second
        matrix = np.asarray(
            [
                [first_slope, second_slope],
                [1.0 + resistance * first_slope, -1.0],
            ],
            dtype=float,
        )
        target = np.asarray(
            [
                -first_intercept - second_intercept,
                -resistance * first_intercept,
            ],
            dtype=float,
        )
        augmented = np.column_stack((matrix, target))
        rank = int(np.linalg.matrix_rank(matrix))
        if rank < 2:
            if int(np.linalg.matrix_rank(augmented)) == rank:
                nonunique_segment_pairs.append([first_index, second_index])
            continue
        first_potential, second_potential = np.linalg.solve(matrix, target)
        potential_scale = max(
            1.0,
            abs(first_left),
            abs(first_right),
            abs(second_left),
            abs(second_right),
        )
        support_tolerance = 64 * np.finfo(float).eps * potential_scale
        if not (
            first_left - support_tolerance <= first_potential <= first_right + support_tolerance
            and second_left - support_tolerance <= second_potential <= second_right + support_tolerance
        ):
            continue
        first_potential = float(min(max(first_potential, first_left), first_right))
        second_potential = float(min(max(second_potential, second_left), second_right))
        first_current = float(first_slope * first_potential + first_intercept)
        second_current = float(second_slope * second_potential + second_intercept)
        current_residual = float(first_current + second_current)
        voltage_residual = float(first_potential - second_potential + resistance * first_current)
        if not all(
            math.isfinite(value)
            for value in (
                first_potential,
                second_potential,
                first_current,
                second_current,
                current_residual,
                voltage_residual,
            )
        ):
            return result("out_of_scope", "equilibrium_not_numerically_representable")
        candidate = {
            "electrode_ids": [item.electrode_id for item in x.electrodes],
            "electrode_interface_potential_V": [first_potential, second_potential],
            "signed_net_electrode_current_A": [first_current, second_current],
            "series_voltage_drop_V": resistance * first_current,
            "current_balance_residual_A": current_residual,
            "voltage_balance_residual_V": voltage_residual,
            "support_segment_indices": [first_index, second_index],
        }
        duplicate = any(
            max(
                abs(first_potential - existing["electrode_interface_potential_V"][0]),
                abs(second_potential - existing["electrode_interface_potential_V"][1]),
            )
            <= support_tolerance
            for existing in candidates
        )
        if not duplicate:
            candidates.append(candidate)

    details = {
        "equilibria": candidates,
        "nonunique_segment_pairs": nonunique_segment_pairs,
        "resistance_components": [item.model_dump(mode="json") for item in x.connection.components],
        "curve_provenance": [
            {
                "electrode_id": item.electrode_id,
                "curve_id": item.polarization_curve.curve_id,
                "provider_id": item.curve_provider_id,
                "provider_revision": item.curve_provider_revision,
                "input_digest": item.curve_input_digest,
                "result_digest": item.curve_result_digest,
                "support_V": [
                    item.polarization_curve.potential_V[0],
                    item.polarization_curve.potential_V[-1],
                ],
            }
            for item in x.electrodes
        ],
    }
    if nonunique_segment_pairs:
        return result("needs_data", "nonunique_continuous_equilibrium", **details)
    if not candidates:
        return result("out_of_scope", "no_equilibrium_within_both_curve_supports", **details)
    if len(candidates) > 1:
        return result("needs_data", "multiple_piecewise_equilibria", **details)
    equilibrium = candidates[0]
    if (
        abs(equilibrium["current_balance_residual_A"]) > x.absolute_current_balance_tolerance_A
        or abs(equilibrium["voltage_balance_residual_V"]) > x.absolute_voltage_balance_tolerance_V
    ):
        return result("needs_data", "balance_residual_exceeds_tolerance", **details)
    return result(
        "computed",
        "unique_two_electrode_resistive_equilibrium",
        **details,
        electrode_interface_potential_V=equilibrium["electrode_interface_potential_V"],
        signed_net_electrode_current_A=equilibrium["signed_net_electrode_current_A"],
        series_voltage_drop_V=equilibrium["series_voltage_drop_V"],
        current_meaning="signed_net_external_current_not_partial_dissolution",
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "degradation.galvanic_resistive_coupling",
            ResistiveGalvanicCoupling,
            resistive_galvanic_coupling,
            {
                "electrode_interface_potential_V": "V",
                "signed_net_electrode_current_A": "A",
                "series_voltage_drop_V": "V",
                "declared_total_series_resistance_ohm": "ohm",
            },
            (
                "Exactly two reviewed signed net polarization curves share one environment and reference electrode; every root is bounded by both supplied curve supports.",
                "Caller-owned electrolyte, contact and lead resistance components sum to the finite declared series resistance used in the voltage balance.",
                "No current-to-loss conversion, corrosion rate, acceptance, life, stability claim, or failure probability is produced.",
            ),
            ("authored_two_electrode_resistive_galvanic_balance",),
        )
    ]
