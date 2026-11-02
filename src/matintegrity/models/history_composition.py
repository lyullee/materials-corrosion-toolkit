"""Registry adapters for typed creep and strain-life history calculations."""

from ..calibrated_condition_loss import (
    ConditionLossHistory,
    ConditionLossRateAssessment,
    evaluate_condition_loss_history,
    evaluate_condition_loss_rate,
)
from ..calibrated_damage_history import CalibratedDamageHistory, integrate_calibrated_damage
from ..contracts import Calculation
from ..creep_fatigue_campaign import CreepFatigueCampaign, evaluate_creep_fatigue_campaign
from ..creep_history import CreepHistoryRequest, integrate_creep_history
from ..fire_thermal_response import FireThermalResponse, evaluate_fire_thermal_response
from ..registry import ModelSpec
from ..strain_life_campaign import StrainLifeCampaign, evaluate_strain_life_campaign


def _evaluate(function, request):
    result = function(request)
    values = result.model_dump(mode="json")
    status = values.pop("status")
    notes = tuple(values.pop("notes"))
    return Calculation(status=status, values=values, notes=notes)


def _dict_evaluate(function, request):
    values = dict(function(request))
    status = values.pop("status")
    basis = values.pop("basis", values.pop("interpretation", None))
    return Calculation(status=status, values=values, notes=(basis,) if basis else ())


def specifications():
    return [
        ModelSpec(
            "degradation.calibrated_condition_loss_rate",
            ConditionLossRateAssessment,
            lambda x: _dict_evaluate(evaluate_condition_loss_rate, x),
            {"loss_rate_m_s": "m/s"},
            (
                "Explicit authorized material/mechanism-specific log-rate coefficients, native feature units and bounded support; no default biological or erosion-rate law.",
            ),
            ("calibrated_condition_loss_response",),
        ),
        ModelSpec(
            "degradation.calibrated_condition_loss_history",
            ConditionLossHistory,
            lambda x: _dict_evaluate(evaluate_condition_loss_history, x),
            {},
            (
                "Ordered piecewise-constant conditions mapped through one reviewed calibrated response and integrated without dropping unsupported intervals.",
            ),
            ("calibrated_condition_loss_response",),
        ),
        ModelSpec(
            "degradation.calibrated_damage_history",
            CalibratedDamageHistory,
            lambda x: _dict_evaluate(integrate_calibrated_damage, x),
            {"cumulative_loss_m": "m", "interval_loss_m": "m"},
            ("Explicit calibrated microbial or cavitation rate history; no indicator-to-rate inference.",),
            ("calibrated_damage_and_plane_life_composition",),
        ),
        ModelSpec(
            "thermal.fire_flux_response",
            FireThermalResponse,
            lambda x: _dict_evaluate(evaluate_fire_thermal_response, x),
            {},
            (
                "Reviewed net absorbed boundary flux composed with explicit multilayer transient conduction; no fire curve, ablation or intumescence law inferred.",
            ),
            ("fire_flux_conduction_composition",),
        ),
        ModelSpec(
            "structural.creep_fatigue_campaign",
            CreepFatigueCampaign,
            lambda x: _evaluate(evaluate_creep_fatigue_campaign, x),
            {},
            (
                "Compose same-history creep rupture-time fractions, fatigue cycle fractions and a caller-owned interaction envelope without substituting secondary strain for damage.",
            ),
            ("declared_creep_fatigue_campaign_composition",),
        ),
        ModelSpec(
            "creep.secondary_history",
            CreepHistoryRequest,
            lambda x: _evaluate(integrate_creep_history, x),
            {
                "interval_strain_increments": "1",
                "cumulative_strain_at_boundaries": "1",
                "secondary_creep_strain": "1",
                "linear_rupture_time_fraction": "1",
            },
            (
                "Ordered caller-calibrated secondary-creep history with separately reviewed rupture-time fractions inside explicit condition support.",
            ),
            ("declared_secondary_creep_history",),
        ),
        ModelSpec(
            "fatigue.strain_life_campaign",
            StrainLifeCampaign,
            lambda x: _evaluate(evaluate_strain_life_campaign, x),
            {"total_linear_damage": "1"},
            (
                "Explicit fully reversed, Morrow or SWT blocks with caller-reviewed linear cycle-fraction accumulation; constituent failures withhold the total.",
            ),
            ("declared_strain_life_block_accumulation",),
        ),
    ]
