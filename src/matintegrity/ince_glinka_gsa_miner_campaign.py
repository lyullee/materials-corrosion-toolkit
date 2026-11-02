"""Aggregate caller-counted Ince–Glinka cycle groups with linear Miner damage."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .ince_glinka_gsa_curve_life import (
    InceGlinkaGSACurveLife,
    evaluate_ince_glinka_gsa_curve_life,
)
from .models.fatigue import MinerDamage, miner_damage
from .registry import ModelSpec


class InceGlinkaCycleGroup(Contract):
    """One caller-counted representative closed tensor cycle and its life curve."""

    cycle_group_id: str = Field(min_length=1)
    allocated_cycle_count: Positive
    life_request: InceGlinkaGSACurveLife


class InceGlinkaGSAMinerCampaign(Contract):
    """Map finite caller cycle groups to life, then sum their declared Miner fractions."""

    schema_version: Literal["matintegrity.ince_glinka_gsa_miner_campaign.v1"] = (
        "matintegrity.ince_glinka_gsa_miner_campaign.v1"
    )
    campaign_id: str = Field(min_length=1)
    cycle_groups: tuple[InceGlinkaCycleGroup, ...] = Field(min_length=1, max_length=10000)
    declared_damage_limit: Positive
    cycle_group_count_and_identity_reviewed: bool
    curve_and_material_consistency_reviewed: bool
    linear_miner_rule_reviewed: bool
    sequence_effects_excluded_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def consistent_groups(self):
        ids = [row.cycle_group_id for row in self.cycle_groups]
        if len(ids) != len(set(ids)):
            raise ValueError("cycle-group IDs must be unique")
        assessment_ids = [row.life_request.calculation.assessment_id for row in self.cycle_groups]
        if len(assessment_ids) != len(set(assessment_ids)):
            raise ValueError("each representative cycle calculation must have a unique assessment ID")
        first = self.cycle_groups[0].life_request
        calibration_identity = (
            first.calibration_id,
            first.calibration_material_condition_id,
            first.cycles_definition,
            canonical_digest([point.model_dump(mode="json") for point in first.curve_points]),
            first.calculation.material_condition_id,
            first.calculation.physical_scope_id,
            first.calculation.location_id,
        )
        for group in self.cycle_groups[1:]:
            request = group.life_request
            identity = (
                request.calibration_id,
                request.calibration_material_condition_id,
                request.cycles_definition,
                canonical_digest([point.model_dump(mode="json") for point in request.curve_points]),
                request.calculation.material_condition_id,
                request.calculation.physical_scope_id,
                request.calculation.location_id,
            )
            if identity != calibration_identity:
                raise ValueError("all cycle groups must share one curve, cycle definition, material condition and physical location")
        return self


def evaluate_ince_glinka_gsa_miner_campaign(
    request: InceGlinkaGSAMinerCampaign,
) -> Calculation:
    """Evaluate every declared cycle group and apply the existing Miner calculator."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    first = request.cycle_groups[0].life_request
    base = {
        "campaign_id": request.campaign_id,
        "input_sha256": input_digest,
        "calibration_id": first.calibration_id,
        "calibration_material_condition_id": first.calibration_material_condition_id,
        "cycles_definition": first.cycles_definition,
        "material_condition_id": first.calculation.material_condition_id,
        "physical_scope_id": first.calculation.physical_scope_id,
        "location_id": first.calculation.location_id,
        "cycle_group_count": len(request.cycle_groups),
        "cycle_counting_performed": False,
        "sequence_order_effects_modeled": False,
        "failure_probability_inferred": False,
    }
    reviews = {
        "cycle_group_count_and_identity_reviewed": request.cycle_group_count_and_identity_reviewed,
        "curve_and_material_consistency_reviewed": request.curve_and_material_consistency_reviewed,
        "linear_miner_rule_reviewed": request.linear_miner_rule_reviewed,
        "sequence_effects_excluded_reviewed": request.sequence_effects_excluded_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "completed_cycle_group_count": 0,
            "cycle_group_results": [],
            "total_miner_damage": None,
        })

    rows = []
    counts = []
    lives = []
    for index, group in enumerate(request.cycle_groups):
        life_result = evaluate_ince_glinka_gsa_curve_life(group.life_request)
        values = life_result.values
        row = {
            "cycle_group_id": group.cycle_group_id,
            "index": index,
            "allocated_cycle_count": group.allocated_cycle_count,
            "life_request_sha256": canonical_digest(group.life_request.model_dump(mode="json")),
            "life_result_sha256": canonical_digest(life_result.model_dump(mode="json")),
            "life_result": life_result.model_dump(mode="json"),
            "status": life_result.status,
        }
        if life_result.status != "computed":
            return Calculation(status=life_result.status, values=base | {
                "completed_cycle_group_count": len(rows),
                "cycle_group_results": rows + [row],
                "failed_cycle_group_id": group.cycle_group_id,
                "failed_cycle_group_index": index,
                "miner_result": None,
                "total_miner_damage": None,
                "prefix_policy": "total damage is withheld unless every caller cycle group maps to an in-support life",
            }, notes=(
                "No Miner sum is produced from a partial set of caller cycle groups.",
            ))
        life = values.get("cycles_to_failure")
        if isinstance(life, bool) or not isinstance(life, (int, float)) or not math.isfinite(life) or life <= 0:
            return Calculation(status="out_of_scope", values=base | {
                "completed_cycle_group_count": len(rows),
                "cycle_group_results": rows + [row],
                "failed_cycle_group_id": group.cycle_group_id,
                "failed_cycle_group_index": index,
                "reason": "life_curve_result_is_not_positive_finite",
                "miner_result": None,
                "total_miner_damage": None,
            })
        row["cycles_to_failure"] = float(life)
        row["miner_damage"] = group.allocated_cycle_count / float(life)
        rows.append(row)
        counts.append(group.allocated_cycle_count)
        lives.append(float(life))

    miner = miner_damage(MinerDamage(
        cycle_counts=counts,
        cycles_to_failure=lives,
        declared_damage_limit=request.declared_damage_limit,
    ))
    return Calculation(status=miner.status, values=base | {
        "completed_cycle_group_count": len(rows),
        "cycle_group_results": rows,
        "declared_damage_limit": request.declared_damage_limit,
        "miner_result": miner.model_dump(mode="json"),
        "total_miner_damage": miner.values.get("damage"),
        "damage_margin_to_caller_limit": miner.values.get("damage_margin"),
        "summation_basis": "existing_linear_miner_sum_over_complete_caller_counted_cycle_groups",
        "not_inferred": ["cycle_counts", "sequence_effects", "material_calibration", "failure_probability", "acceptance", "remaining_life"],
    }, notes=(
        "Each group reuses the existing finite-plane Ince–Glinka GSA calculation and caller-supplied monotone life curve; the existing Miner calculator sums caller cycle counts divided by those lives.",
        "Cycle extraction/count allocation and sequence effects are outside this API. The computed damage is conditional on the declared curve, repeated representative-cycle interpretation and linear Miner rule; it is not a probability or qualification result.",
    ) + miner.notes)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="fatigue.ince_glinka_gsa_miner_campaign",
        input_type=InceGlinkaGSAMinerCampaign,
        evaluator=evaluate_ince_glinka_gsa_miner_campaign,
        units={
            "cycle_groups[].allocated_cycle_count": "cycle",
            "cycle_group_results[].life_result.values.gsa_parameter": "1",
            "cycle_group_results[].cycles_to_failure": "cycle",
            "cycle_group_results[].miner_damage": "1",
            "total_miner_damage": "1",
        },
        assumptions=(
            "Each declared cycle group reuses the existing caller-input finite-plane Ince–Glinka parameter and caller-monotone GSA-to-life curve; no curve is fitted or extrapolated.",
            "Every group has an explicit caller-allocated cycle count. Only after every group has an in-support life does the existing Miner implementation sum damage fractions.",
            "Cycle counting, chronology, interaction or sequence effects, calibration transfer, probability and fatigue qualification are not inferred.",
        ),
        source_ids=("caller_ince_glinka_gsa_miner_campaign",),
        qualification="user_model",
    )]
