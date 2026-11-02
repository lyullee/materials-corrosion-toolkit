"""Crossland proportional stress blocks mapped to caller lives and Miner damage."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .multiaxial_crossland_proportional_screen import (
    CALIBRATION_SOURCE_ID as CROSSLAND_CALIBRATION_SOURCE_ID,
    MultiaxialCrosslandProportionalLimitScreen,
    evaluate_multiaxial_crossland_proportional_limit_screen,
)
from .registry import ModelSpec

MODEL_ID = "fatigue.crossland_proportional_miner_campaign"
CURVE_SOURCE_ID = "caller_crossland_parameter_constant_amplitude_life_curve"
PARAMETER_DEFINITION_ID = "crossland_1956_sqrtj2amplitude_plus_alpha_peak_hydrostatic.v1"


class CrosslandProportionalBlock(Contract):
    """One caller-counted block and its finite stress-path evaluation request."""

    block_id: str = Field(min_length=1)
    cycle_count: int = Field(ge=1, le=10**12)
    screen_request: MultiaxialCrosslandProportionalLimitScreen


class CrosslandProportionalMinerCampaign(Contract):
    """Compute same-condition bounded lives and linear Miner dose for blocks."""

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    parameter_definition_id: Literal[PARAMETER_DEFINITION_ID]
    life_curve_id: str = Field(min_length=1)
    curve_source_id: Literal[CURVE_SOURCE_ID]
    curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_evidence: Evidence
    curve_license_id: str = Field(min_length=1)
    condition_descriptor_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_hydrostatic_coefficient_alpha: Nonnegative
    parameter_points_Pa: tuple[Positive, ...] = Field(min_length=2, max_length=10000)
    cycles_to_failure: tuple[Positive, ...] = Field(min_length=2, max_length=10000)
    blocks: tuple[CrosslandProportionalBlock, ...] = Field(min_length=1, max_length=10000)
    miner_damage_threshold: Positive
    material_test_and_condition_reviewed: bool
    curve_rights_and_use_reviewed: bool
    cycle_decomposition_and_linear_miner_reviewed: bool

    @model_validator(mode="after")
    def validate_campaign(self):
        if self.curve_evidence.source_id != self.curve_source_id:
            raise ValueError("curve Evidence source ID must match the declared curve source")
        if self.curve_evidence.sha256 != self.curve_source_sha256:
            raise ValueError("curve Evidence digest must match the declared curve digest")
        if self.curve_evidence.license_id != self.curve_license_id:
            raise ValueError("curve Evidence reuse basis must match the declared license ID")
        if len(self.parameter_points_Pa) != len(self.cycles_to_failure):
            raise ValueError("parameter and cycle-life arrays must have equal lengths")
        if any(b <= a for a, b in zip(self.parameter_points_Pa, self.parameter_points_Pa[1:])):
            raise ValueError("curve parameter knots must strictly increase")
        if any(b >= a for a, b in zip(self.cycles_to_failure, self.cycles_to_failure[1:])):
            raise ValueError("cycles to failure must strictly decrease with increasing parameter")
        ids = [block.block_id for block in self.blocks]
        if len(set(ids)) != len(ids):
            raise ValueError("cycle block IDs must be unique")
        first = self.blocks[0].screen_request
        if first.calibration_source_id != CROSSLAND_CALIBRATION_SOURCE_ID:
            raise ValueError("block screen requests must use the registered Crossland caller calibration source")
        if first.hydrostatic_coefficient_alpha != self.curve_hydrostatic_coefficient_alpha:
            raise ValueError("life curve alpha must exactly match each block's Crossland parameter coefficient")
        for block in self.blocks:
            request = block.screen_request
            if request.calibration_material_condition_id != self.material_condition_id:
                raise ValueError("each block calibration condition must exactly match the campaign material condition")
            if (request.calibration_id != first.calibration_id
                    or request.calibration_source_id != first.calibration_source_id
                    or request.calibration_sha256 != first.calibration_sha256
                    or request.hydrostatic_coefficient_alpha != first.hydrostatic_coefficient_alpha
                    or request.caller_limit_beta_Pa != first.caller_limit_beta_Pa):
                raise ValueError("all blocks must share the exact Crossland coefficient, limit, and calibration lineage")
        return self


def _bounded_loglog(parameter: float, x: tuple[float, ...], y: tuple[float, ...]):
    if parameter < x[0] or parameter > x[-1]:
        return None
    for i, knot in enumerate(x):
        if parameter == knot:
            return y[i], i, 0.0, "exact_curve_knot"
    i = next(index for index in range(len(x) - 1) if x[index] < parameter < x[index + 1])
    fraction = (math.log(parameter) - math.log(x[i])) / (math.log(x[i + 1]) - math.log(x[i]))
    life = math.exp(math.log(y[i]) + fraction * (math.log(y[i + 1]) - math.log(y[i])))
    return life, i, fraction, "linear_log_parameter_log_cycles"


def evaluate_crossland_proportional_miner_campaign(
    request: CrosslandProportionalMinerCampaign,
) -> Calculation:
    """Evaluate each block, map its parameter to bounded life, and sum n/N."""
    curve_digest = canonical_digest({
        "life_curve_id": request.life_curve_id,
        "material_condition_id": request.material_condition_id,
        "parameter_definition_id": request.parameter_definition_id,
        "condition_descriptor_sha256": request.condition_descriptor_sha256,
        "hydrostatic_coefficient_alpha": request.curve_hydrostatic_coefficient_alpha,
        "source_id": request.curve_source_id,
        "source_sha256": request.curve_source_sha256,
        "license_id": request.curve_license_id,
        "parameter_points_Pa": request.parameter_points_Pa,
        "cycles_to_failure": request.cycles_to_failure,
    })
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "parameter_definition_id": request.parameter_definition_id,
        "crossland_calibration_id": request.blocks[0].screen_request.calibration_id,
        "crossland_calibration_sha256": request.blocks[0].screen_request.calibration_sha256,
        "life_curve_id": request.life_curve_id,
        "life_curve_source_id": request.curve_source_id,
        "life_curve_source_sha256": request.curve_source_sha256,
        "life_curve_license_id": request.curve_license_id,
        "condition_descriptor_sha256": request.condition_descriptor_sha256,
        "hydrostatic_coefficient_alpha": request.curve_hydrostatic_coefficient_alpha,
        "normalized_life_curve_sha256": curve_digest,
        "input_sha256": input_digest,
    }
    if not all((request.material_test_and_condition_reviewed, request.curve_rights_and_use_reviewed,
                request.cycle_decomposition_and_linear_miner_reviewed)):
        return Calculation(status="needs_data", values=base | {
            "reason": "material_test_rights_cycle_decomposition_and_linear_miner_reviews_required",
            "block_damage_ledger": None,
            "total_miner_damage": None,
            "repeat_units_to_damage_threshold": None,
        })

    ledger = []
    damages = []
    failed_blocks = []
    for block in request.blocks:
        screen = evaluate_multiaxial_crossland_proportional_limit_screen(block.screen_request)
        parameter = screen.values.get("crossland_parameter_Pa")
        row = {
            "block_id": block.block_id,
            "cycle_count": block.cycle_count,
            "screen_input_sha256": screen.values.get("input_sha256"),
            "screen_status": screen.status,
            "screen_reason": screen.values.get("reason"),
            "crossland_parameter_Pa": parameter,
            "crossland_limit_margin_Pa": screen.values.get("margin_to_caller_limit_Pa"),
        }
        if screen.status != "computed" or isinstance(parameter, bool) or not isinstance(parameter, (float, int)):
            row["life_mapping_status"] = screen.status if screen.status != "computed" else "out_of_scope"
            row["life_mapping_reason"] = "crossland_parameter_unavailable"
            ledger.append(row)
            failed_blocks.append(block.block_id)
            continue
        mapped = _bounded_loglog(float(parameter), request.parameter_points_Pa, request.cycles_to_failure)
        if mapped is None:
            row["life_mapping_status"] = "out_of_scope"
            row["life_mapping_reason"] = "crossland_parameter_outside_life_curve_support_no_extrapolation"
            row["curve_parameter_support_Pa"] = [request.parameter_points_Pa[0], request.parameter_points_Pa[-1]]
            ledger.append(row)
            failed_blocks.append(block.block_id)
            continue
        life, interval, fraction, mapping = mapped
        damage = block.cycle_count / life
        if not math.isfinite(damage) or damage < 0:
            row["life_mapping_status"] = "out_of_scope"
            row["life_mapping_reason"] = "block_damage_not_finite_nonnegative"
            ledger.append(row)
            failed_blocks.append(block.block_id)
            continue
        row.update({
            "life_mapping_status": "computed",
            "cycles_to_failure": life,
            "curve_interval_index": interval,
            "interpolation_fraction": fraction,
            "interpolation_method": mapping,
            "miner_damage": damage,
        })
        ledger.append(row)
        damages.append(damage)
    if failed_blocks:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "one_or_more_blocks_not_evaluable_complete_campaign_damage_withheld",
            "failed_block_ids": failed_blocks,
            "block_damage_ledger": ledger,
            "total_miner_damage": None,
            "repeat_units_to_damage_threshold": None,
        })
    total_damage = math.fsum(damages)
    repeat_units = request.miner_damage_threshold / total_damage if total_damage > 0 else math.inf
    if not math.isfinite(total_damage) or not math.isfinite(repeat_units):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "campaign_damage_or_threshold_repeat_count_not_finite",
            "block_damage_ledger": ledger,
            "total_miner_damage": None,
            "repeat_units_to_damage_threshold": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "block_damage_ledger": ledger,
        "total_miner_damage": total_damage,
        "miner_damage_threshold": request.miner_damage_threshold,
        "repeat_units_to_damage_threshold": repeat_units,
        "damage_semantics": "caller-declared block cycle counts and linear Miner sum; one repeat unit is the complete ordered block set",
        "limitations": [
            "Cycle counts and block definitions are caller supplied; no counting or cycle pairing is performed.",
            "The life curve is caller supplied and is interpolated only inside its support for the exact Crossland parameter definition and material condition.",
            "Linear Miner summation and threshold repetition are assumptions selected by the caller; order and interaction effects are not modeled.",
            "No extrapolation, probability, code acceptance, inspection interval, or qualified service life is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CrosslandProportionalMinerCampaign,
        evaluator=evaluate_crossland_proportional_miner_campaign,
        units={
            "block_damage_ledger[].crossland_parameter_Pa": "Pa",
            "block_damage_ledger[].cycles_to_failure": "cycle",
            "block_damage_ledger[].miner_damage": "1",
            "total_miner_damage": "1",
            "repeat_units_to_damage_threshold": "campaign_repeat",
        },
        assumptions=(
            "Each block is evaluated by the finite proportional Crossland screen and bounded same-condition caller life curve.",
            "Block damage is cycle_count divided by mapped life; complete campaign damage is a linear Miner sum.",
            "No cycle extraction, extrapolation, sequence correction, probability, acceptance, or qualification is inferred.",
        ),
        source_ids=(
            CROSSLAND_CALIBRATION_SOURCE_ID,
            "caller_crossland_parameter_constant_amplitude_life_curve",
            "crossland_1956_hydrostatic_pressure_torsional_fatigue_criterion",
        ),
        qualification="user_model",
    )]
