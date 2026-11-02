"""Compose reviewed creep histories, fatigue blocks and caller interaction curves."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, canonical_digest
from .creep_fatigue_interaction import (
    CreepFatigueInteractionEnvelope,
    CreepFatigueInteractionPoint,
    CreepFatigueInteractionResult,
    evaluate_creep_fatigue_interaction,
)
from .creep_history import CreepHistoryRequest, CreepHistoryResult, integrate_creep_history
from .strain_life_campaign import StrainLifeCampaign, StrainLifeCampaignResult, evaluate_strain_life_campaign


class CreepFatigueCampaign(Contract):
    campaign_id: str = Field(min_length=1)
    creep_history: CreepHistoryRequest
    fatigue_history: StrainLifeCampaign
    envelope: CreepFatigueInteractionEnvelope
    interaction_temperature_K: float = Field(gt=0)
    creep_fraction_definition: str = Field(min_length=1)
    fatigue_fraction_definition: str = Field(min_length=1)
    common_exposure_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    histories_and_interaction_basis_reviewed: bool

    @model_validator(mode="after")
    def common_material(self):
        materials = {
            self.creep_history.material_condition_id,
            self.fatigue_history.material_condition_id,
            self.envelope.material_condition_id,
        }
        if len(materials) != 1:
            raise ValueError("creep, fatigue and interaction envelope must share material condition")
        if self.fatigue_history.history_sha256 != self.common_exposure_history_sha256:
            raise ValueError("fatigue history must reference the common exposure history")
        if (
            self.creep_history.exposure_history_sha256 is not None
            and self.creep_history.exposure_history_sha256 != self.common_exposure_history_sha256
        ):
            raise ValueError("creep history references a different exposure history")
        if (
            self.creep_fraction_definition != self.envelope.creep_damage_definition
            or self.fatigue_fraction_definition != self.envelope.fatigue_damage_definition
        ):
            raise ValueError("campaign damage definitions must match the interaction curve")
        return self


class CreepFatigueCampaignResult(Contract):
    schema_version: Literal["matintegrity.creep_fatigue_campaign.v1"] = (
        "matintegrity.creep_fatigue_campaign.v1"
    )
    campaign_id: str
    input_sha256: str
    status: Literal["computed", "needs_data", "out_of_scope"]
    creep_result: CreepHistoryResult | None
    fatigue_result: StrainLifeCampaignResult | None
    interaction_result: CreepFatigueInteractionResult | None
    notes: tuple[str, ...]


def evaluate_creep_fatigue_campaign(request: CreepFatigueCampaign) -> CreepFatigueCampaignResult:
    """Keep strain, rupture fractions and fatigue fractions separate until an explicit envelope comparison."""
    base = dict(
        campaign_id=request.campaign_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        creep_result=None,
        fatigue_result=None,
        interaction_result=None,
    )
    if not request.histories_and_interaction_basis_reviewed:
        return CreepFatigueCampaignResult(
            **base,
            status="needs_data",
            notes=("Common exposure and interaction definitions require review.",),
        )
    if request.creep_history.exposure_history_sha256 is None:
        return CreepFatigueCampaignResult(
            **base,
            status="needs_data",
            notes=("Creep history must explicitly bind the common exposure history digest.",),
        )
    unsupported = [
        row.interval_id
        for row in request.creep_history.intervals
        if not request.envelope.applicable_temperature_min_K
        <= row.temperature_K
        <= request.envelope.applicable_temperature_max_K
    ]
    if unsupported:
        return CreepFatigueCampaignResult(
            **base,
            status="out_of_scope",
            notes=(
                "Creep intervals exceed interaction-envelope temperature support: " + ", ".join(unsupported),
            ),
        )
    creep = integrate_creep_history(request.creep_history)
    fatigue = evaluate_strain_life_campaign(request.fatigue_history)
    base.update(creep_result=creep, fatigue_result=fatigue)
    statuses = {creep.status, fatigue.status}
    if statuses != {"computed"}:
        status = "needs_data" if "needs_data" in statuses else "out_of_scope"
        return CreepFatigueCampaignResult(
            **base,
            status=status,
            notes=("Interaction withheld because a constituent history was incomplete or unsupported.",),
        )
    if creep.linear_rupture_time_fraction is None or fatigue.total_linear_damage is None:
        return CreepFatigueCampaignResult(
            **base,
            status="needs_data",
            notes=(
                "Both reviewed rupture-time and fatigue-cycle fractions are required for this interaction basis.",
            ),
        )
    point = CreepFatigueInteractionPoint(
        point_id=request.campaign_id,
        material_condition_id=request.envelope.material_condition_id,
        creep_damage_definition=request.creep_fraction_definition,
        fatigue_damage_definition=request.fatigue_fraction_definition,
        creep_damage=creep.linear_rupture_time_fraction,
        fatigue_damage=fatigue.total_linear_damage,
        temperature_K=request.interaction_temperature_K,
        exposure_history_sha256=request.common_exposure_history_sha256,
        damage_inputs_reviewed=True,
    )
    interaction = evaluate_creep_fatigue_interaction(point, request.envelope)
    base["interaction_result"] = interaction
    return CreepFatigueCampaignResult(
        **base,
        status=interaction.status,
        notes=(
            "The caller-owned interaction curve combines the two declared damage measures; secondary creep strain remains a separate output.",
        ),
    )
